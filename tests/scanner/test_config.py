"""ScanConfigモデルのユニットテスト。"""

# ruff: noqa: S106, S105, S108

from pathlib import Path

from pydantic import ValidationError
import pytest

from src.scanner.config import ScanConfig


class TestScanConfig:
    """ScanConfigモデルのテストクラス。"""

    def test_valid_baseline_config(self):
        """ベースラインスキャンの有効な設定をテスト。"""
        config = ScanConfig(
            scan_type="baseline",
            target_url="http://example.com",
        )
        assert config.scan_type == "baseline"
        assert config.target_url == "http://example.com"
        assert config.auth_type == "none"
        assert config.ajax_spider is False
        assert config.max_duration == 30

    def test_valid_full_scan_with_auth(self):
        """認証付きフルスキャンの有効な設定をテスト。"""
        config = ScanConfig(
            scan_type="full",
            target_url="https://example.com",
            username="admin",
            password="secret",
            auth_type="form",
            login_url="https://example.com/login",
            logged_in_indicator="Logout",
        )
        assert config.scan_type == "full"
        assert config.username == "admin"
        assert config.password == "secret"
        assert config.auth_type == "form"
        assert config.login_url == "https://example.com/login"

    def test_invalid_url_without_protocol(self):
        """プロトコルなしのURLで検証エラーが発生することをテスト。"""
        with pytest.raises(ValidationError) as exc_info:
            ScanConfig(
                scan_type="baseline",
                target_url="example.com",  # http:// or https:// なし
            )
        errors = exc_info.value.errors()
        assert any("target_url must start with http://" in str(e) for e in errors)

    def test_auth_requires_credentials(self):
        """認証タイプが'none'以外の場合、認証情報が必要なことをテスト。"""
        with pytest.raises(ValidationError) as exc_info:
            ScanConfig(
                scan_type="full",
                target_url="http://example.com",
                auth_type="form",
                # username と password が不足
            )
        errors = exc_info.value.errors()
        assert any("username and password are required" in str(e) for e in errors)

    def test_auth_with_valid_credentials(self):
        """認証情報が提供されている場合は検証が成功することをテスト。"""
        config = ScanConfig(
            scan_type="full",
            target_url="http://example.com",
            auth_type="basic",
            username="user",
            password="pass",
        )
        assert config.auth_type == "basic"
        assert config.username == "user"
        assert config.password == "pass"

    def test_positive_numeric_values(self):
        """正の数値検証をテスト。"""
        with pytest.raises(ValidationError):
            ScanConfig(
                scan_type="baseline",
                target_url="http://example.com",
                max_duration=0,  # 0以下は無効
            )

        with pytest.raises(ValidationError):
            ScanConfig(
                scan_type="baseline",
                target_url="http://example.com",
                max_depth=-1,  # 負の値は無効
            )

    def test_default_values(self):
        """デフォルト値が正しく設定されることをテスト。"""
        config = ScanConfig(
            scan_type="api",
            target_url="http://api.example.com",
        )
        assert config.auth_type == "none"
        assert config.username_field == "username"
        assert config.password_field == "password"
        assert config.session_method == "cookie"
        assert config.ajax_spider is False
        assert config.max_duration == 30
        assert config.max_depth == 10
        assert config.max_children == 20

    def test_report_dir_default(self):
        """レポートディレクトリのデフォルト値をテスト。"""
        config = ScanConfig(
            scan_type="baseline",
            target_url="http://example.com",
        )
        assert isinstance(config.report_dir, Path)
        assert config.report_dir.name == "report"

    def test_custom_report_dir(self):
        """カスタムレポートディレクトリの設定をテスト。"""
        custom_dir = Path("/tmp/custom_reports")
        config = ScanConfig(
            scan_type="baseline",
            target_url="http://example.com",
            report_dir=custom_dir,
        )
        assert config.report_dir == custom_dir

    def test_all_scan_types(self):
        """すべてのスキャンタイプが受け入れられることをテスト。"""
        for scan_type in ["baseline", "full", "api", "automation"]:
            config = ScanConfig(
                scan_type=scan_type,
                target_url="http://example.com",
            )
            assert config.scan_type == scan_type

    def test_invalid_scan_type(self):
        """無効なスキャンタイプで検証エラーが発生することをテスト。"""
        with pytest.raises(ValidationError):
            ScanConfig(
                scan_type="invalid",  # type: ignore
                target_url="http://example.com",
            )

    def test_ajax_spider_option(self):
        """AJAXスパイダーオプションの設定をテスト。"""
        config = ScanConfig(
            scan_type="full",
            target_url="http://example.com",
            ajax_spider=True,
        )
        assert config.ajax_spider is True

    def test_network_name_option(self):
        """Dockerネットワーク名の設定をテスト。"""
        config = ScanConfig(
            scan_type="automation",
            target_url="http://example.com",
            network_name="webgoat_default",
        )
        assert config.network_name == "webgoat_default"
