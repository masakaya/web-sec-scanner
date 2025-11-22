"""セキュリティスキャナー実行モジュール。

このモジュールはDockerコンテナを使用してWebアプリケーションの
セキュリティスキャンを実行する機能を提供する。
"""
# ruff: noqa: D400, D415, S603, S607

from datetime import datetime
import json
from pathlib import Path
import subprocess

from prefect import task
from prefect.logging import get_run_logger
import yaml

from .config import ScanConfig


@task(name="setup-directories", description="ディレクトリセットアップ")
def setup_directories(config: ScanConfig) -> None:
    """スキャンに必要なディレクトリを作成する。

    Args:
        config: スキャン設定

    """
    logger = get_run_logger()

    config.report_dir.mkdir(parents=True, exist_ok=True)
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


def _create_automation_config(
    config: ScanConfig, scan_presets: dict | None = None
) -> Path:
    """Automation Framework用のYAML設定ファイルを作成する。

    Args:
        config: スキャン設定
        scan_presets: 設定プリセット（オプション）

    Returns:
        作成された設定ファイルのパス

    """
    logger = get_run_logger()

    config_dir = config.report_dir.parent / "scanner-config"
    config_dir.mkdir(parents=True, exist_ok=True)

    # タイムスタンプ
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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

    # レポート生成
    report_file = f"scan-report-{config.scan_type}-{timestamp}"
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
                    "reportDir": "/scanner/wrk",
                    "reportFile": f"{report_file}.{ext}",
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
    # ユーザーIDとグループIDを取得
    uid = subprocess.check_output(["id", "-u"]).decode().strip()
    gid = subprocess.check_output(["id", "-g"]).decode().strip()

    cmd = [
        "docker",
        "run",
        "--rm",
        "--user",
        f"{uid}:{gid}",
        "-v",
        f"{config.report_dir.absolute()}:/scanner/wrk:rw",
    ]

    # Dockerネットワーク指定
    if config.network_name:
        cmd.extend(["--network", config.network_name])

    # 設定ディレクトリのマウント（automation用）
    config_dir = config.report_dir.parent / "scanner-config"
    if config_dir.exists():
        cmd.extend(["-v", f"{config_dir.absolute()}:/scanner/config:ro"])

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

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_base = f"scan-report-{config.scan_type}-{timestamp}"

    scan_cmd = [
        "zap-baseline.py",
        "-t",
        config.target_url,
        "-r",
        f"{report_base}.html",
        "-J",
        f"{report_base}.json",
        "-w",
        f"{report_base}.xml",
        "-l",
        "INFO",
        "-config",
        f"view.locale={config.language}",
    ]

    docker_cmd = _build_docker_command(config, scan_cmd)
    logger.info(f"Executing: {' '.join(docker_cmd)}")

    result = subprocess.run(docker_cmd)
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

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_base = f"scan-report-{config.scan_type}-{timestamp}"

    scan_cmd = [
        "zap-full-scan.py",
        "-t",
        config.target_url,
        "-r",
        f"{report_base}.html",
        "-J",
        f"{report_base}.json",
        "-w",
        f"{report_base}.xml",
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
    ]

    scan_cmd.extend(["-z", " ".join(scanner_opts)])

    docker_cmd = _build_docker_command(config, scan_cmd)
    logger.info(f"Executing: {' '.join(docker_cmd)}")

    result = subprocess.run(docker_cmd)
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

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_base = f"scan-report-{config.scan_type}-{timestamp}"

    scan_cmd = [
        "zap-api-scan.py",
        "-t",
        config.target_url,
        "-r",
        f"{report_base}.html",
        "-J",
        f"{report_base}.json",
        "-w",
        f"{report_base}.xml",
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
    return result.returncode


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

    # 設定プリセットを読み込み
    scan_presets = None
    if config.config_file:
        scan_presets = load_scan_presets(config.config_file)

    # Automation設定ファイルを作成
    _ = _create_automation_config(config, scan_presets)

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
    return result.returncode
