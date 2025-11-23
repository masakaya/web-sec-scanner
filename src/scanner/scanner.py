"""セキュリティスキャナー実行モジュール。

このモジュールはDockerコンテナを使用してWebアプリケーションの
セキュリティスキャンを実行する機能を提供する。
"""
# ruff: noqa: D400, D415, S603, S607

from datetime import datetime
import json
from pathlib import Path
import subprocess
from typing import Any
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

    # ディレクトリ名のプレフィックスを決定
    if config.config_file:
        # 設定ファイル名から名前を抽出（例：fast-scan.json → fast, thorough-scan.json → thorough）
        dir_prefix = config.config_file.stem.replace("-scan", "")
    else:
        # 設定ファイルが指定されていない場合、スキャンタイプから決定
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


def load_scan_presets(config_file: Path) -> dict[str, Any]:
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
        presets: dict[str, Any] = json.load(f)

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
    scan_presets: dict[str, Any] | None = None,
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

    automation_config: dict[str, Any] = {
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

    # 認証設定の追加（Browser-based Authentication）
    if config.username and config.auth_type != "bearer":
        # Browser-based認証を使用（Authentication Helper AddOn）
        auth_config = {
            "method": "browser",
            "parameters": {
                "loginPageUrl": config.login_url,
                "loginPageWait": 5,
                "browserId": "firefox-headless",
            },
        }

        # 検証方法（autodetect推奨）
        if config.logged_in_indicator or config.logged_out_indicator:
            verification_config: dict[str, Any] = {"method": "response"}
            if config.logged_in_indicator:
                verification_config["loggedInRegex"] = config.logged_in_indicator
            if config.logged_out_indicator:
                verification_config["loggedOutRegex"] = config.logged_out_indicator
            automation_config["env"]["contexts"][0]["verification"] = (
                verification_config
            )
        else:
            # autodetectを使用
            automation_config["env"]["contexts"][0]["verification"] = {
                "method": "autodetect"
            }

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

        # セッション管理（autodetect推奨）
        automation_config["env"]["contexts"][0]["sessionManagement"] = {
            "method": "autodetect",
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

    # Active Scan Policy（sqliplugin設定があれば適用）
    if scan_presets and "sqliplugin_config" in scan_presets:
        sqliplugin_config = scan_presets["sqliplugin_config"]
        if sqliplugin_config.get("enabled", True):
            policy_params = {
                "defaultStrength": sqliplugin_config.get("attackStrength", "MEDIUM"),
                "defaultThreshold": sqliplugin_config.get("alertThreshold", "MEDIUM"),
                "rules": [
                    {
                        "id": 40018,  # SQL Injection - MySQL
                        "name": "SQL Injection - MySQL",
                        "threshold": sqliplugin_config.get("alertThreshold", "MEDIUM"),
                        "strength": sqliplugin_config.get("attackStrength", "MEDIUM"),
                    }
                ],
            }
            automation_config["jobs"].append(
                {
                    "type": "activeScan-policy",
                    "parameters": policy_params,
                }
            )

    # Active Scan（設定の優先順位: プリセット < CLI引数/config）
    active_scan_params = {}

    # プリセット設定を先に適用（低優先度）
    if scan_presets and "active_scan_config" in scan_presets:
        active_scan_params.update(scan_presets["active_scan_config"])

    # CLI/config設定で上書き（高優先度）
    active_scan_params.update(
        {
            "policy": active_scan_params.get("policy", "Default Policy"),
            "maxScanDurationInMins": config.max_duration,
            "threadPerHost": config.thread_per_host,  # ホストごとのスレッド数（高速化）
        }
    )

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

    # 設定ディレクトリのマウント（automation用）
    config_dir = config.report_dir.parent / "scanner-config"
    if config_dir.exists():
        cmd.extend(["-v", f"{config_dir.absolute()}:/scanner/config:ro"])

    # 言語設定
    cmd.extend(["-e", f"LC_ALL={config.language}.UTF-8"])

    # Bearer認証の環境変数設定
    if config.auth_type == "bearer" and config.auth_token:
        token_prefix = (
            config.token_prefix if config.token_prefix.lower() != "none" else ""
        )
        token_value = f"{token_prefix} {config.auth_token}".strip()
        cmd.extend(["-e", f"ZAP_AUTH_HEADER_VALUE={token_value}"])
        cmd.extend(["-e", f"ZAP_AUTH_HEADER={config.auth_header}"])
        logger.info(
            f"Using ZAP environment variable authentication: {config.auth_header}"
        )

    # スキャナーイメージ
    cmd.append("ghcr.io/zaproxy/zaproxy:stable")

    # スキャンコマンド
    cmd.extend(scan_command)

    # AddOnのインストール（zap.shの後に追加）
    if config.addons:
        for addon in config.addons:
            cmd.extend(["-addoninstall", addon])
        logger.info(f"Installing ZAP AddOns: {', '.join(config.addons)}")

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

    if config.ajax_spider:
        scan_cmd.append("-j")

    # スキャナー設定オプション
    scanner_opts = [
        f"-config view.locale={config.language}",
        f"-config spider.maxDuration={config.max_duration}",
        f"-config spider.maxDepth={config.max_depth}",
        f"-config spider.maxChildren={config.max_children}",
        f"-config scanner.threadPerHost={config.thread_per_host}",  # ホストごとのスレッド数（高速化）
        f"-config scanner.hostsPerScan={config.hosts_per_scan}",  # 並列スキャンするホスト数（高速化）
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
