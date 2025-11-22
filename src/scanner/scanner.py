"""OWASP ZAP スキャナー実行モジュール。

このモジュールはOWASP ZAPを使用してWebアプリケーションの
セキュリティスキャンを実行する機能を提供する。
"""
# ruff: noqa: D400, D415, S603, S607

from datetime import datetime
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
    config_dir = config.report_dir.parent / "zap-config"
    config_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Config directory created: {config_dir}")


def _create_automation_config(config: ScanConfig) -> Path:
    """ZAP Automation Framework用のYAML設定ファイルを作成する。

    Args:
        config: スキャン設定

    Returns:
        作成された設定ファイルのパス

    """
    logger = get_run_logger()

    config_dir = config.report_dir.parent / "zap-config"
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

    # Spiderジョブ
    automation_config["jobs"].append(
        {
            "type": "spider",
            "parameters": {
                "maxDuration": config.max_duration,
                "maxDepth": config.max_depth,
                "maxChildren": config.max_children,
            },
        }
    )

    # AJAX Spiderジョブ（有効な場合）
    if config.ajax_spider:
        automation_config["jobs"].append(
            {
                "type": "spiderAjax",
                "parameters": {
                    "maxDuration": config.max_duration,
                    "maxCrawlDepth": config.max_depth,
                    "numberOfBrowsers": 2,
                },
            }
        )

    # Passive Scan待機
    automation_config["jobs"].append(
        {"type": "passiveScan-wait", "parameters": {"maxDuration": 5}}
    )

    # Active Scan
    automation_config["jobs"].append(
        {
            "type": "activeScan",
            "parameters": {
                "policy": "Default Policy",
                "maxScanDurationInMins": config.max_duration,
            },
        }
    )

    # 最終Passive Scan待機
    automation_config["jobs"].append(
        {"type": "passiveScan-wait", "parameters": {"maxDuration": 5}}
    )

    # レポート生成
    report_file = f"zap-report-{config.scan_type}-{timestamp}"
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
                    "reportDir": "/zap/wrk",
                    "reportFile": f"{report_file}.{ext}",
                    "reportTitle": "ZAP Security Scanning Report",
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
        scan_command: ZAPスキャンコマンド

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
        f"{config.report_dir.absolute()}:/zap/wrk:rw",
    ]

    # Dockerネットワーク指定
    if config.network_name:
        cmd.extend(["--network", config.network_name])

    # 設定ディレクトリのマウント（automation用）
    config_dir = config.report_dir.parent / "zap-config"
    if config_dir.exists():
        cmd.extend(["-v", f"{config_dir.absolute()}:/zap/config:ro"])

    # 言語設定
    cmd.extend(["-e", f"LC_ALL={config.language}.UTF-8"])

    # ZAPイメージとコマンド
    cmd.append("ghcr.io/zaproxy/zaproxy:stable")
    cmd.extend(scan_command)

    return cmd


@task(name="run-baseline-scan", description="ベースラインスキャン実行")
def run_baseline_scan(config: ScanConfig) -> int:
    """ZAPベースラインスキャンを実行する。

    Args:
        config: スキャン設定

    Returns:
        終了コード

    """
    logger = get_run_logger()
    logger.info("Running ZAP Baseline Scan...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_base = f"zap-report-{config.scan_type}-{timestamp}"

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
    """ZAPフルスキャンを実行する。

    Args:
        config: スキャン設定

    Returns:
        終了コード

    """
    logger = get_run_logger()
    logger.info("Running ZAP Full Scan...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_base = f"zap-report-{config.scan_type}-{timestamp}"

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

    # ZAP設定オプション
    zap_opts = [
        f"-config view.locale={config.language}",
        f"-config spider.maxDuration={config.max_duration}",
        f"-config spider.maxDepth={config.max_depth}",
        f"-config spider.maxChildren={config.max_children}",
    ]

    scan_cmd.extend(["-z", " ".join(zap_opts)])

    docker_cmd = _build_docker_command(config, scan_cmd)
    logger.info(f"Executing: {' '.join(docker_cmd)}")

    result = subprocess.run(docker_cmd)
    return result.returncode


@task(name="run-api-scan", description="APIスキャン実行")
def run_api_scan(config: ScanConfig) -> int:
    """ZAP APIスキャンを実行する。

    Args:
        config: スキャン設定

    Returns:
        終了コード

    """
    logger = get_run_logger()
    logger.info("Running ZAP API Scan...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_base = f"zap-report-{config.scan_type}-{timestamp}"

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
    """ZAP Automation Frameworkスキャンを実行する。

    Args:
        config: スキャン設定

    Returns:
        終了コード

    """
    logger = get_run_logger()
    logger.info("Running ZAP Automation Framework...")

    # Automation設定ファイルを作成
    _ = _create_automation_config(config)

    scan_cmd = [
        "zap.sh",
        "-cmd",
        "-autorun",
        "/zap/config/automation-config.yaml",
        "-config",
        f"view.locale={config.language}",
    ]

    docker_cmd = _build_docker_command(config, scan_cmd)
    logger.info(f"Executing: {' '.join(docker_cmd)}")

    result = subprocess.run(docker_cmd)
    return result.returncode
