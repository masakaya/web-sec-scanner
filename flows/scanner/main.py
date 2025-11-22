"""メインセキュリティスキャンフロー。

このモジュールはWebアプリケーションに対してセキュリティスキャンを
実行するためのPrefectフローを提供する。
"""

import argparse
import sys
from pathlib import Path
from typing import Literal, Optional

from prefect import flow, task
from prefect.logging import get_run_logger

from .config import ScanConfig


@task(name="parse-arguments", description="コマンドライン引数を解析")
def parse_arguments_task() -> argparse.Namespace:
    """コマンドライン引数をPrefectタスクとして解析する。

    Returns:
        解析されたコマンドライン引数

    Raises:
        SystemExit: 引数の解析に失敗した場合
    """
    parser = argparse.ArgumentParser(
        description="Web Security Scanner with Prefect",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple baseline scan
  %(prog)s baseline http://example.com

  # Full scan with form authentication
  %(prog)s full http://example.com \\
    --username admin --password secret \\
    --auth-type form --login-url http://example.com/login \\
    --logged-in-indicator "Logout" --ajax-spider

  # API scan
  %(prog)s api http://api.example.com

  # Automation framework scan with custom settings
  %(prog)s automation http://example.com \\
    --max-duration 60 --max-depth 15 --network webgoat_default
        """,
    )

    # 必須引数
    parser.add_argument(
        "scan_type",
        choices=["baseline", "full", "api", "automation"],
        help="Type of scan to perform",
    )
    parser.add_argument("target_url", help="Target URL to scan")

    # 認証オプション
    auth_group = parser.add_argument_group("authentication options")
    auth_group.add_argument("--username", help="Username for authentication")
    auth_group.add_argument("--password", help="Password for authentication")
    auth_group.add_argument(
        "--auth-type",
        choices=["none", "form", "json", "basic"],
        default="none",
        help="Authentication type (default: none)",
    )
    auth_group.add_argument("--login-url", help="Login endpoint URL")
    auth_group.add_argument(
        "--username-field", default="username", help="Username field name"
    )
    auth_group.add_argument(
        "--password-field", default="password", help="Password field name"
    )
    auth_group.add_argument(
        "--logged-in-indicator", help="Regex to detect logged-in state"
    )
    auth_group.add_argument(
        "--logged-out-indicator", help="Regex to detect logged-out state"
    )
    auth_group.add_argument(
        "--session-method",
        choices=["cookie", "http"],
        default="cookie",
        help="Session management method (default: cookie)",
    )

    # スキャンオプション
    scan_group = parser.add_argument_group("scan options")
    scan_group.add_argument(
        "--ajax-spider",
        action="store_true",
        help="Enable AJAX Spider for JavaScript-heavy sites",
    )
    scan_group.add_argument(
        "--max-duration",
        type=int,
        default=30,
        help="Maximum scan duration in minutes (default: 30)",
    )
    scan_group.add_argument(
        "--max-depth", type=int, default=10, help="Maximum crawl depth (default: 10)"
    )
    scan_group.add_argument(
        "--max-children",
        type=int,
        default=20,
        help="Maximum children per node (default: 20)",
    )
    scan_group.add_argument("--network", dest="network_name", help="Docker network name")
    scan_group.add_argument(
        "--report-dir",
        type=Path,
        help="Directory to save reports (default: ./report)",
    )

    args = parser.parse_args()
    return args


@task(name="validate-config", description="スキャン設定の検証")
def validate_scan_config(args: argparse.Namespace) -> ScanConfig:
    """コマンドライン引数からスキャン設定を検証して作成する。

    Args:
        args: 解析されたコマンドライン引数

    Returns:
        検証済みのScanConfigオブジェクト

    Raises:
        ValidationError: 設定の検証に失敗した場合
    """
    logger = get_run_logger()

    logger.info("Validating scan configuration...")
    config = ScanConfig(
        scan_type=args.scan_type,
        target_url=args.target_url,
        username=args.username,
        password=args.password,
        auth_type=args.auth_type,
        login_url=args.login_url,
        username_field=args.username_field,
        password_field=args.password_field,
        logged_in_indicator=args.logged_in_indicator,
        logged_out_indicator=args.logged_out_indicator,
        session_method=args.session_method,
        ajax_spider=args.ajax_spider,
        max_duration=args.max_duration,
        max_depth=args.max_depth,
        max_children=args.max_children,
        network_name=args.network_name,
        report_dir=args.report_dir or Path.cwd() / "report",
    )

    logger.info("✓ Configuration validated successfully")
    logger.info(f"Scan Type: {config.scan_type}")
    logger.info(f"Target URL: {config.target_url}")
    logger.info(f"Authentication: {config.auth_type}")
    logger.info(f"AJAX Spider: {config.ajax_spider}")
    logger.info(f"Max Duration: {config.max_duration} minutes")

    return config


@flow(name="check-security-scan-option", description="セキュリティスキャンオプションのチェックと検証")
def check_security_scan_option() -> ScanConfig:
    """コマンドライン引数からセキュリティスキャンオプションをチェック・検証する。

    このフローはコマンドライン引数を解析して検証し、
    セキュリティスキャンで使用可能なScanConfigオブジェクトを作成する。

    Returns:
        検証済みのScanConfigオブジェクト

    Raises:
        ValidationError: 設定の検証に失敗した場合
        SystemExit: 引数の解析に失敗した場合
    """
    logger = get_run_logger()

    logger.info("Checking security scan options from command line arguments...")

    # コマンドライン引数を解析
    args = parse_arguments_task()

    # 設定を検証
    config = validate_scan_config(args)

    logger.info("✓ Security scan options validated successfully")

    return config


@flow(name="security-scan", description="セキュリティスキャンを実行")
def security_scan_flow(config: ScanConfig) -> dict:
    """セキュリティスキャンをPrefectフローとして実行する。

    Args:
        config: 検証済みのスキャン設定

    Returns:
        スキャン結果とレポートパスを含む辞書
    """
    logger = get_run_logger()

    logger.info("Starting security scan...")
    logger.info(f"Scan Type: {config.scan_type}")
    logger.info(f"Target URL: {config.target_url}")
    logger.info(f"Authentication: {config.auth_type}")

    # TODO: 実際のスキャンロジックを実装
    logger.warning("⚠ Scan logic not yet implemented")

    return {
        "status": "pending",
        "config": config.model_dump(),
        "message": "Flow structure created successfully",
    }


if __name__ == "__main__":
    try:
        # スキャンオプションをチェック・検証（内部で引数を解析）
        config = check_security_scan_option()

        # セキュリティスキャンフローを実行
        result = security_scan_flow(config)

        print(f"\n{'='*60}")
        print("Scan Result:")
        print(f"{'='*60}")
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        print(f"{'='*60}\n")

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nScan interrupted by user")
        sys.exit(130)
    except SystemExit:
        # argparseからのSystemExitを再送出（使用方法は既に出力済み）
        raise
    except Exception as e:
        # 検証エラーのエラーメッセージを出力
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
