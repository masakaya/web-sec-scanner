"""セキュリティスキャナー実行モジュール。

このモジュールはDockerコンテナを使用してWebアプリケーションの
セキュリティスキャンを実行する機能を提供する。
"""
# ruff: noqa: D400, D415, S603, S607

from datetime import datetime
import json
from pathlib import Path
import subprocess
from urllib.parse import urlparse

from prefect import task
from prefect.logging import get_run_logger
import yaml

from .config import ScanConfig


def _create_timestamped_report_dir(config: ScanConfig) -> tuple[Path, str]:
    """タイムスタンプ付きのレポートディレクトリを作成する。

    Args:
        config: スキャン設定

    Returns:
        (レポートディレクトリのパス, タイムスタンプ文字列)

    """
    logger = get_run_logger()

    # タイムスタンプを生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ディレクトリ名のプレフィックスを決定（automationは"fast"に変更）
    dir_prefix = "fast" if config.scan_type == "automation" else config.scan_type
    report_subdir = config.report_dir / f"{dir_prefix}-{timestamp}"

    # ディレクトリを作成
    report_subdir.mkdir(parents=True, exist_ok=True)
    report_subdir.chmod(0o777)

    logger.info(f"Timestamped report directory created: {report_subdir}")

    return report_subdir, timestamp


@task(name="setup-directories", description="ディレクトリセットアップ")
def setup_directories(config: ScanConfig) -> None:
    """スキャンに必要なディレクトリを作成する。

    Args:
        config: スキャン設定

    """
    logger = get_run_logger()

    config.report_dir.mkdir(parents=True, exist_ok=True)
    # Dockerコンテナからの書き込みを可能にするため777に設定
    config.report_dir.chmod(0o777)
    logger.info(f"Report directory created: {config.report_dir}")

    # 設定ディレクトリも作成（認証スクリプト用）
    config_dir = config.report_dir.parent / "scanner-config"
    config_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Config directory created: {config_dir}")


def load_scan_presets(config_file: Path) -> dict:
    """設定プリセットファイルを読み込む。

    Args:
        config_file: 設定ファイルのパス

    Returns:
        設定プリセットの辞書

    Raises:
        FileNotFoundError: 設定ファイルが存在しない場合
        json.JSONDecodeError: JSONファイルの形式が不正な場合

    """
    logger = get_run_logger()

    if not config_file.exists():
        msg = f"Configuration file not found: {config_file}"
        raise FileNotFoundError(msg)

    logger.info(f"Loading scan presets from: {config_file}")

    with open(config_file) as f:
        presets = json.load(f)

    logger.info("✓ Scan presets loaded successfully")
    return presets


def _detect_docker_network(target_url: str) -> str | None:
    """ターゲットURLからDockerネットワークを自動検出する。

    Args:
        target_url: スキャン対象のURL

    Returns:
        検出されたDockerネットワーク名、または検出できない場合はNone

    """
    logger = get_run_logger()

    # URLからホスト名を抽出
    parsed = urlparse(target_url)
    hostname = parsed.hostname

    # localhost、IPアドレス、または外部ドメインの場合はネットワーク不要
    if not hostname:
        return None

    if hostname in ("localhost", "127.0.0.1") or "." in hostname:
        # localhostまたはFQDN（外部サービス）の場合
        logger.info(f"Target is {hostname}, no Docker network needed")
        return None

    try:
        # docker psでコンテナ名またはホスト名からネットワークを検出
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                f"name={hostname}",
                "--format",
                "{{.Networks}}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0 and result.stdout.strip():
            network = result.stdout.strip()
            logger.info(f"Auto-detected Docker network: {network}")
            return network

        # プロジェクト名からデフォルトネットワークを推測
        project_root = Path.cwd()
        project_name = project_root.name
        default_network = f"{project_name}_default"

        # デフォルトネットワークが存在するか確認
        result = subprocess.run(
            ["docker", "network", "ls", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
            check=False,
        )

        if default_network in result.stdout:
            logger.info(f"Using default project network: {default_network}")
            return default_network

        logger.warning(f"Could not detect Docker network for {hostname}")
        return None

    except Exception as e:
        logger.warning(f"Failed to detect Docker network: {e}")
        return None


def _create_automation_config(
    config: ScanConfig,
    report_subdir: Path,
    timestamp: str,
    scan_presets: dict | None = None,
) -> Path:
    """Automation Framework用のYAML設定ファイルを作成する。

    Args:
        config: スキャン設定
        report_subdir: タイムスタンプ付きレポートディレクトリ
        timestamp: タイムスタンプ文字列
        scan_presets: 設定プリセット（オプション）

    Returns:
        作成された設定ファイルのパス

    """
    logger = get_run_logger()

    config_dir = config.report_dir.parent / "scanner-config"
    config_dir.mkdir(parents=True, exist_ok=True)

    automation_config = {
        "env": {
            "contexts": [
                {
                    "name": "Target Application",
                    "urls": [config.target_url],
                    "includePaths": [f"{config.target_url}.*"],
                }
            ],
            "parameters": {
                "failOnError": False,
                "failOnWarning": False,
                "progressToStdout": True,
            },
        },
        "jobs": [],
    }

    # 認証設定の追加
    if config.username:
        auth_config = {
            "parameters": {
                "loginUrl": config.login_url,
                "usernameField": config.username_field,
                "passwordField": config.password_field,
            }
        }

        if config.logged_in_indicator:
            auth_config["verification"] = {
                "method": "response",
                "loggedInRegex": config.logged_in_indicator,
            }
            if config.logged_out_indicator:
                auth_config["verification"]["loggedOutRegex"] = (
                    config.logged_out_indicator
                )

        automation_config["env"]["contexts"][0]["authentication"] = auth_config
        automation_config["env"]["contexts"][0]["users"] = [
            {
                "name": config.username,
                "credentials": {
                    "username": config.username,
                    "password": config.password,
                },
            }
        ]
        automation_config["env"]["contexts"][0]["sessionManagement"] = {
            "method": config.session_method,
            "parameters": {},
        }

    # Spiderジョブ（プリセット設定があればマージ）
    spider_params = {
        "maxDuration": config.max_duration,
        "maxDepth": config.max_depth,
        "maxChildren": config.max_children,
    }
    if scan_presets and "spider_config" in scan_presets:
        spider_params.update(scan_presets["spider_config"])

    automation_config["jobs"].append(
        {
            "type": "spider",
            "parameters": spider_params,
        }
    )

    # AJAX Spiderジョブ（有効な場合、プリセット設定があればマージ）
    if config.ajax_spider:
        ajax_spider_params = {
            "maxDuration": config.max_duration,
            "maxCrawlDepth": config.max_depth,
            "numberOfBrowsers": 2,
        }
        if scan_presets and "ajax_spider_config" in scan_presets:
            ajax_spider_params.update(scan_presets["ajax_spider_config"])

        automation_config["jobs"].append(
            {
                "type": "spiderAjax",
                "parameters": ajax_spider_params,
            }
        )

    # Passive Scan待機（プリセット設定があればマージ）
    passive_scan_wait_params = {"maxDuration": 5}
    if scan_presets and "passive_scan_config" in scan_presets:
        passive_scan_wait_params.update(scan_presets["passive_scan_config"])

    automation_config["jobs"].append(
        {"type": "passiveScan-wait", "parameters": passive_scan_wait_params}
    )

    # Active Scan（プリセット設定があればマージ）
    active_scan_params = {
        "policy": "Default Policy",
        "maxScanDurationInMins": config.max_duration,
        "threadPerHost": 10,  # ホストごとのスレッド数（高速化）
        "hostsPerScan": 5,    # 並列スキャンするホスト数（高速化）
    }
    if scan_presets and "active_scan_config" in scan_presets:
        active_scan_params.update(scan_presets["active_scan_config"])

    automation_config["jobs"].append(
        {
            "type": "activeScan",
            "parameters": active_scan_params,
        }
    )

    # 最終Passive Scan待機
    automation_config["jobs"].append(
        {"type": "passiveScan-wait", "parameters": passive_scan_wait_params}
    )

    # レポート生成（タイムスタンプディレクトリ内に出力）
    # Dockerコンテナ内のパス: /scanner/wrk/{scan_type}-{timestamp}/
    report_subdir_name = report_subdir.name
    for template, ext in [
        ("traditional-html", "html"),
        ("traditional-json", "json"),
        ("traditional-xml", "xml"),
    ]:
        automation_config["jobs"].append(
            {
                "type": "report",
                "parameters": {
                    "template": template,
                    "reportDir": f"/scanner/wrk/{report_subdir_name}",
                    "reportFile": f"scan-report.{ext}",
                    "reportTitle": "Security Scanning Report",
                    "reportDescription": f"Target: {config.target_url}",
                },
            }
        )

    # YAML設定ファイルを保存
    config_file = config_dir / "automation-config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(automation_config, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Automation config created: {config_file}")
    return config_file


def _build_docker_command(config: ScanConfig, scan_command: list) -> list:
    """Docker実行コマンドを構築する。

    Args:
        config: スキャン設定
        scan_command: スキャナーコマンド

    Returns:
        完全なDockerコマンド

    """
    logger = get_run_logger()

    # ユーザーIDとグループIDを取得
    uid = subprocess.check_output(["id", "-u"]).decode().strip()
    gid = subprocess.check_output(["id", "-g"]).decode().strip()

    # スキャンタイプに応じてマウントパスを決定
    # baseline/full/apiスキャンは /zap/wrk を使用
    # automationスキャンは /scanner/wrk を使用
    if scan_command[0] in ["zap-baseline.py", "zap-full-scan.py", "zap-api-scan.py"]:
        mount_path = "/zap/wrk"
    else:
        mount_path = "/scanner/wrk"

    cmd = [
        "docker",
        "run",
        "--rm",
        "--user",
        f"{uid}:{gid}",
        "-v",
        f"{config.report_dir.absolute()}:{mount_path}:rw",
    ]

    # Dockerネットワーク指定（自動検出または手動指定）
    network_name = config.network_name
    if not network_name:
        network_name = _detect_docker_network(config.target_url)

    if network_name:
        cmd.extend(["--network", network_name])
        logger.info(f"Using Docker network: {network_name}")
    else:
        logger.info("No Docker network specified, using default networking")

    # 設定ディレクトリのマウント（automation用およびフックスクリプト用）
    config_dir = config.report_dir.parent / "scanner-config"
    if config_dir.exists():
        cmd.extend(["-v", f"{config_dir.absolute()}:/scanner/config:ro"])
        # フックスクリプトが存在する場合は環境変数で指定
        hook_file = config_dir / "zap_hooks.py"
        if hook_file.exists():
            cmd.extend(["-e", "ZAP_HOOKS=/scanner/config/zap_hooks.py"])

    # 言語設定
    cmd.extend(["-e", f"LC_ALL={config.language}.UTF-8"])

    # スキャナーイメージとコマンド
    cmd.append("ghcr.io/zaproxy/zaproxy:stable")
    cmd.extend(scan_command)

    return cmd


@task(name="run-baseline-scan", description="ベースラインスキャン実行")
def run_baseline_scan(config: ScanConfig) -> int:
    """ベースラインスキャンを実行する。

    Args:
        config: スキャン設定

    Returns:
        終了コード

    """
    logger = get_run_logger()
    logger.info("Running Baseline Scan...")

    # タイムスタンプ付きディレクトリを作成
    report_subdir, timestamp = _create_timestamped_report_dir(config)
    report_subdir_name = report_subdir.name

    scan_cmd = [
        "zap-baseline.py",
        "-t",
        config.target_url,
        "-r",
        f"{report_subdir_name}/scan-report.html",
        "-J",
        f"{report_subdir_name}/scan-report.json",
        "-w",
        f"{report_subdir_name}/scan-report.xml",
        "-l",
        "INFO",
        "-config",
        f"view.locale={config.language}",
    ]

    docker_cmd = _build_docker_command(config, scan_cmd)
    logger.info(f"Executing: {' '.join(docker_cmd)}")

    result = subprocess.run(docker_cmd)

    # JSONレポートのエンコーディングを修正
    if result.returncode in (0, 2):  # 成功または警告付き成功
        _fix_json_encoding(report_subdir)

    return result.returncode


@task(name="run-full-scan", description="フルスキャン実行")
def run_full_scan(config: ScanConfig) -> int:
    """フルスキャンを実行する。

    Args:
        config: スキャン設定

    Returns:
        終了コード

    """
    logger = get_run_logger()
    logger.info("Running Full Scan...")

    # タイムスタンプ付きディレクトリを作成
    report_subdir, timestamp = _create_timestamped_report_dir(config)
    report_subdir_name = report_subdir.name

    # 設定ディレクトリを取得
    config_dir = config.report_dir.parent / "scanner-config"

    # 認証フックスクリプトを作成
    hook_script = _create_auth_hook_script(config, config_dir)

    scan_cmd = [
        "zap-full-scan.py",
        "-t",
        config.target_url,
        "-r",
        f"{report_subdir_name}/scan-report.html",
        "-J",
        f"{report_subdir_name}/scan-report.json",
        "-w",
        f"{report_subdir_name}/scan-report.xml",
        "-l",
        "INFO",
        "-d",
        "-m",
        str(config.max_duration),
        "-T",
        "120",
    ]

    # 認証が有効な場合はログに記録
    if hook_script:
        logger.info(f"Using authentication hook script for user: {config.username}")

    if config.ajax_spider:
        scan_cmd.append("-j")

    # スキャナー設定オプション
    scanner_opts = [
        f"-config view.locale={config.language}",
        f"-config spider.maxDuration={config.max_duration}",
        f"-config spider.maxDepth={config.max_depth}",
        f"-config spider.maxChildren={config.max_children}",
        "-config scanner.threadPerHost=10",  # ホストごとのスレッド数（高速化）
        "-config scanner.hostsPerScan=5",    # 並列スキャンするホスト数（高速化）
    ]

    scan_cmd.extend(["-z", " ".join(scanner_opts)])

    docker_cmd = _build_docker_command(config, scan_cmd)
    logger.info(f"Executing: {' '.join(docker_cmd)}")

    result = subprocess.run(docker_cmd)

    # JSONレポートのエンコーディングを修正
    if result.returncode in (0, 2):  # 成功または警告付き成功
        _fix_json_encoding(report_subdir)

    return result.returncode


@task(name="run-api-scan", description="APIスキャン実行")
def run_api_scan(config: ScanConfig) -> int:
    """APIスキャンを実行する。

    Args:
        config: スキャン設定

    Returns:
        終了コード

    """
    logger = get_run_logger()
    logger.info("Running API Scan...")

    # タイムスタンプ付きディレクトリを作成
    report_subdir, timestamp = _create_timestamped_report_dir(config)
    report_subdir_name = report_subdir.name

    scan_cmd = [
        "zap-api-scan.py",
        "-t",
        config.target_url,
        "-r",
        f"{report_subdir_name}/scan-report.html",
        "-J",
        f"{report_subdir_name}/scan-report.json",
        "-w",
        f"{report_subdir_name}/scan-report.xml",
        "-l",
        "INFO",
        "-f",
        "openapi",
        "-config",
        f"view.locale={config.language}",
    ]

    docker_cmd = _build_docker_command(config, scan_cmd)
    logger.info(f"Executing: {' '.join(docker_cmd)}")

    result = subprocess.run(docker_cmd)

    # JSONレポートのエンコーディングを修正
    if result.returncode in (0, 2):  # 成功または警告付き成功
        _fix_json_encoding(report_subdir)

    return result.returncode


def _fix_json_encoding(report_dir: Path) -> None:
    """JSONレポートのUnicodeエスケープをUTF-8に変換する。

    Args:
        report_dir: レポートディレクトリ

    """
    logger = get_run_logger()

    try:
        json_files = list(report_dir.glob("*.json"))
        if not json_files:
            return

        for json_file in json_files:
            try:
                # JSONファイルを読み込み
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)

                # 一時ファイルに書き込み
                temp_file = json_file.with_suffix(".json.tmp")
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                # 元のファイルを削除して一時ファイルをリネーム
                json_file.unlink()
                temp_file.rename(json_file)

                logger.info(f"Fixed JSON encoding: {json_file.name}")

            except Exception as e:
                logger.warning(f"Failed to fix {json_file.name}: {e}")
                # 一時ファイルがあれば削除
                temp_file = json_file.with_suffix(".json.tmp")
                if temp_file.exists():
                    temp_file.unlink()

    except Exception as e:
        logger.warning(f"Failed to fix JSON encoding: {e}")


def _create_auth_hook_script(config: ScanConfig, config_dir: Path) -> Path | None:
    """認証設定用のZAPフックスクリプトを生成する。

    Args:
        config: スキャン設定
        config_dir: 設定ファイル保存先ディレクトリ

    Returns:
        生成したフックスクリプトのパス、認証なしの場合はNone

    """
    if config.auth_type == "none":
        return None

    logger = get_run_logger()

    # ベースURLを取得
    parsed_url = urlparse(config.target_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    # URL エンコードされたログインリクエストデータを生成
    # 例: username={%username%}&password={%password%} -> username%3D%7B%25username%25%7D%26password%3D%7B%25password%25%7D
    import urllib.parse
    login_data = f"{config.username_field}={{%username%}}&{config.password_field}={{%password%}}"
    encoded_login_data = urllib.parse.quote(login_data, safe='')

    # ログイン判定用の正規表現（\Qと\Eでリテラル文字列として扱う）
    logged_in_regex = f"\\\\Q{config.logged_in_indicator}\\\\E" if config.logged_in_indicator else ""
    logged_out_regex = f"\\\\Q{config.logged_out_indicator}\\\\E" if config.logged_out_indicator else ""

    # ZAPフックスクリプト（Python）
    hook_script = f'''"""ZAP authentication hook script."""

def zap_tuned(zap):
    """ZAPチューニング後に認証を設定する。

    Args:
        zap: ZAPv2 APIインスタンス
    """
    print("Setting up authentication via ZAP API...")

    # コンテキストを作成
    context_name = "scan-context"
    context_id = zap.context.new_context(context_name)
    print(f"Created context: {{context_name}} (ID: {{context_id}})")

    # コンテキストにターゲットURLを追加
    zap.context.include_in_context(context_name, "{base_url}/.*")
    print(f"Added URL pattern to context: {base_url}/.*")

    # Form-based認証を設定
    auth_method = "formBasedAuthentication"
    auth_params = (
        f"loginUrl={config.login_url}&"
        f"loginRequestData={encoded_login_data}"
    )

    zap.authentication.set_authentication_method(
        contextid=context_id,
        authmethodname=auth_method,
        authmethodconfigparams=auth_params
    )
    print(f"Set authentication method: {{auth_method}}")

    # ログイン判定の設定
    if "{logged_in_regex}":
        zap.authentication.set_logged_in_indicator(
            contextid=context_id,
            loggedinindicatorregex="{logged_in_regex}"
        )
        print(f"Set logged-in indicator: {config.logged_in_indicator}")

    if "{logged_out_regex}":
        zap.authentication.set_logged_out_indicator(
            contextid=context_id,
            loggedoutindicatorregex="{logged_out_regex}"
        )
        print(f"Set logged-out indicator: {config.logged_out_indicator}")

    # ユーザーを作成
    user_name = "{config.username}"
    user_id = zap.users.new_user(context_id, user_name)
    print(f"Created user: {{user_name}} (ID: {{user_id}})")

    # ユーザーの認証情報を設定
    credentials = f"{config.username_field}={config.username}&{config.password_field}={config.password}"
    zap.users.set_authentication_credentials(
        contextid=context_id,
        userid=user_id,
        authcredentialsconfigparams=credentials
    )
    print(f"Set authentication credentials for user: {{user_name}}")

    # ユーザーを有効化
    zap.users.set_user_enabled(context_id, user_id, True)
    print(f"Enabled user: {{user_name}}")

    # 強制ユーザーモードを有効化（このユーザーでスキャン）
    zap.forcedUser.set_forced_user(context_id, user_id)
    zap.forcedUser.set_forced_user_mode_enabled(True)
    print(f"Enabled forced user mode for: {{user_name}}")

    # スパイダーとアクティブスキャンでこのコンテキストを使用するように設定
    zap.context.set_context_in_scope(context_name, True)
    print(f"Set context in scope: {{context_name}}")

    print("Authentication setup completed successfully!")
'''

    # zap_spiderフックも追加（スパイダーをユーザーとして実行）
    hook_script += f'''

def zap_spider(zap, target):
    """スパイダーをユーザーとして実行する。

    Args:
        zap: ZAPv2 APIインスタンス
        target: ターゲットURL
    """
    print("Overriding spider to use authenticated user...")

    # コンテキストとユーザーIDを取得
    context_id = "1"
    user_id = "0"

    # 認証済みユーザーとしてスパイダーを実行
    scan_id = zap.spider.scan_as_user(context_id, user_id, target, recurse=True)
    print(f"Started spider as user (scan ID: {{scan_id}})")

    # スパイダーの完了を待つ
    import time
    while int(zap.spider.status(scan_id)) < 100:
        print(f"Spider progress: {{zap.spider.status(scan_id)}}%")
        time.sleep(5)

    print("Spider completed as authenticated user")
'''

    # フックスクリプトを保存
    hook_file = config_dir / "zap_hooks.py"
    with open(hook_file, "w", encoding="utf-8") as f:
        f.write(hook_script)

    logger.info(f"Authentication hook script created: {hook_file}")

    return hook_file


@task(name="run-automation-scan", description="Automationフレームワークスキャン実行")
def run_automation_scan(config: ScanConfig) -> int:
    """Automation Frameworkスキャンを実行する。

    Args:
        config: スキャン設定

    Returns:
        終了コード

    """
    logger = get_run_logger()
    logger.info("Running Automation Framework...")

    # タイムスタンプ付きディレクトリを作成
    report_subdir, timestamp = _create_timestamped_report_dir(config)

    # 設定プリセットを読み込み
    scan_presets = None
    if config.config_file:
        scan_presets = load_scan_presets(config.config_file)

    # Automation設定ファイルを作成
    _ = _create_automation_config(config, report_subdir, timestamp, scan_presets)

    scan_cmd = [
        "zap.sh",
        "-cmd",
        "-autorun",
        "/scanner/config/automation-config.yaml",
        "-config",
        f"view.locale={config.language}",
    ]

    docker_cmd = _build_docker_command(config, scan_cmd)
    logger.info(f"Executing: {' '.join(docker_cmd)}")

    result = subprocess.run(docker_cmd)

    # JSONレポートのエンコーディングを修正
    if result.returncode in (0, 2):  # 成功または警告付き成功
        _fix_json_encoding(report_subdir)

    return result.returncode
