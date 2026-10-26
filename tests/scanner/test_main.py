"""メインスキャンフローのユニットテスト。"""

# ruff: noqa: S106, S105, S108

import argparse
from pathlib import Path

from src.scanner.config import ScanConfig
from src.scanner.main import security_scan_flow, validate_scan_config


class TestValidateScanConfig:
    """validate_scan_configタスクのテストクラス。"""

    def test_validate_baseline_config(self):
        """ベースラインスキャン設定の検証をテスト。"""
        args = argparse.Namespace(
            scan_type="baseline",
            target_url="http://example.com",
            username=None,
            password=None,
            auth_type="none",
            login_url=None,
            username_field="username",
            password_field="password",
            logged_in_indicator=None,
            logged_out_indicator=None,
            session_method="cookie",
            auth_token=None,
            auth_header="Authorization",
            token_prefix="Bearer",
            ajax_spider=False,
            max_duration=30,
            max_depth=10,
            max_children=20,
            thread_per_host=10,
            hosts_per_scan=5,
            network_name=None,
            language="ja_JP",
            config_file=None,
            addons=None,
            report_dir=None,
        )

        config = validate_scan_config(args)

        assert isinstance(config, ScanConfig)
        assert config.scan_type == "baseline"
        assert config.target_url == "http://example.com"
        assert config.auth_type == "none"

    def test_validate_config_with_auth(self):
        """認証付き設定の検証をテスト。"""
        args = argparse.Namespace(
            scan_type="full",
            target_url="https://example.com",
            username="admin",
            password="secret",
            auth_type="form",
            login_url="https://example.com/login",
            username_field="username",
            password_field="password",
            logged_in_indicator="Logout",
            logged_out_indicator=None,
            session_method="cookie",
            auth_token=None,
            auth_header="Authorization",
            token_prefix="Bearer",
            ajax_spider=True,
            max_duration=60,
            max_depth=15,
            max_children=30,
            thread_per_host=10,
            hosts_per_scan=5,
            network_name="test_network",
            language="ja_JP",
            config_file=None,
            addons=None,
            report_dir=Path("/tmp/reports"),
        )

        config = validate_scan_config(args)

        assert config.scan_type == "full"
        assert config.username == "admin"
        assert config.password == "secret"
        assert config.auth_type == "form"
        assert config.ajax_spider is True
        assert config.max_duration == 60
        assert config.network_name == "test_network"

    def test_validate_config_with_custom_report_dir(self):
        """カスタムレポートディレクトリの検証をテスト。"""
        custom_dir = Path("/tmp/custom_reports")
        args = argparse.Namespace(
            scan_type="api",
            target_url="http://api.example.com",
            username=None,
            password=None,
            auth_type="none",
            login_url=None,
            username_field="username",
            password_field="password",
            logged_in_indicator=None,
            logged_out_indicator=None,
            session_method="cookie",
            auth_token=None,
            auth_header="Authorization",
            token_prefix="Bearer",
            ajax_spider=False,
            max_duration=30,
            max_depth=10,
            max_children=20,
            thread_per_host=10,
            hosts_per_scan=5,
            network_name=None,
            language="ja_JP",
            config_file=None,
            addons=None,
            report_dir=custom_dir,
        )

        config = validate_scan_config(args)

        assert config.report_dir == custom_dir

    def test_validate_config_default_report_dir(self):
        """デフォルトレポートディレクトリの検証をテスト。"""
        args = argparse.Namespace(
            scan_type="baseline",
            target_url="http://example.com",
            username=None,
            password=None,
            auth_type="none",
            login_url=None,
            username_field="username",
            password_field="password",
            logged_in_indicator=None,
            logged_out_indicator=None,
            session_method="cookie",
            auth_token=None,
            auth_header="Authorization",
            token_prefix="Bearer",
            ajax_spider=False,
            max_duration=30,
            max_depth=10,
            max_children=20,
            thread_per_host=10,
            hosts_per_scan=5,
            network_name=None,
            language="ja_JP",
            config_file=None,
            addons=None,
            report_dir=None,
        )

        config = validate_scan_config(args)

        assert config.report_dir == Path.cwd() / "report"


class TestSecurityScanFlow:
    """security_scan_flowフローのテストクラス。"""

    def test_security_scan_flow_returns_pending_status(self):
        """スキャンフローが実行ステータスを返すことをテスト。"""
        config = ScanConfig(
            scan_type="baseline",
            target_url="http://example.com",
        )

        result = security_scan_flow(config)

        assert isinstance(result, dict)
        assert result["status"] in ["completed", "failed"]
        assert "config" in result
        assert "exit_code" in result
        assert "report_dir" in result

    def test_security_scan_flow_includes_config(self):
        """スキャンフローの結果に設定が含まれることをテスト。"""
        config = ScanConfig(
            scan_type="full",
            target_url="https://example.com",
            username="admin",
            password="secret",
            auth_type="form",
            login_url="https://example.com/login",
        )

        result = security_scan_flow(config)

        assert result["config"]["scan_type"] == "full"
        assert result["config"]["target_url"] == "https://example.com"
        assert result["config"]["auth_type"] == "form"

    def test_security_scan_flow_with_ajax_spider(self):
        """AJAXスパイダー有効時のスキャンフローをテスト。"""
        config = ScanConfig(
            scan_type="automation",
            target_url="http://example.com",
            ajax_spider=True,
        )

        result = security_scan_flow(config)

        assert result["config"]["ajax_spider"] is True

    def test_security_scan_flow_with_network(self):
        """ネットワーク設定時のスキャンフローをテスト。"""
        config = ScanConfig(
            scan_type="automation",
            target_url="http://webgoat:8080",
            network_name="webgoat_default",
        )

        result = security_scan_flow(config)

        assert result["config"]["network_name"] == "webgoat_default"
