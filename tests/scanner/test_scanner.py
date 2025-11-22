"""Tests for scanner.scanner module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.scanner.config import ScanConfig
from src.scanner.scanner import (
    _create_timestamped_report_dir,
    _detect_docker_network,
    _fix_json_encoding,
    load_scan_presets,
    setup_directories,
)


@pytest.fixture
def scan_config(tmp_path):
    """Create a test ScanConfig."""
    return ScanConfig(
        scan_type="automation",
        target_url="http://test.example.com",
        report_dir=tmp_path / "report",
    )


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    with patch("src.scanner.scanner.get_run_logger") as mock:
        yield mock.return_value


class TestCreateTimestampedReportDir:
    """Tests for _create_timestamped_report_dir function."""

    def test_creates_directory_with_timestamp(self, scan_config, mock_logger):
        """Test that timestamped directory is created."""
        report_subdir, timestamp = _create_timestamped_report_dir(scan_config)

        assert report_subdir.exists()
        assert report_subdir.is_dir()
        assert report_subdir.name.startswith("fast-")
        assert len(timestamp) == 15  # YYYYMMDD_HHMMSS

    def test_directory_has_correct_permissions(self, scan_config, mock_logger):
        """Test that directory has 777 permissions."""
        report_subdir, _ = _create_timestamped_report_dir(scan_config)

        # Check permissions (0o777)
        assert oct(report_subdir.stat().st_mode & 0o777) == oct(0o777)

    def test_directory_name_includes_scan_type(self, scan_config, mock_logger):
        """Test that directory name includes scan type (automation -> fast)."""
        report_subdir, _ = _create_timestamped_report_dir(scan_config)

        # automationスキャンはディレクトリ名に"fast"を使用
        expected_prefix = "fast" if scan_config.scan_type == "automation" else scan_config.scan_type
        assert expected_prefix in report_subdir.name


class TestDetectDockerNetwork:
    """Tests for _detect_docker_network function."""

    def test_localhost_returns_none(self, mock_logger):
        """Test that localhost URLs return None."""
        result = _detect_docker_network("http://localhost:8080/test")
        assert result is None

    def test_ip_address_returns_none(self, mock_logger):
        """Test that IP addresses return None."""
        result = _detect_docker_network("http://127.0.0.1:8080/test")
        assert result is None

    def test_fqdn_returns_none(self, mock_logger):
        """Test that FQDN (external domains) return None."""
        result = _detect_docker_network("https://example.com/test")
        assert result is None

    @patch("src.scanner.scanner.subprocess.run")
    def test_container_name_detects_network(self, mock_run, mock_logger):
        """Test that container names trigger network detection."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="test-network\n"
        )

        result = _detect_docker_network("http://webgoat:8080/test")

        assert result == "test-network"
        mock_run.assert_called_once()


class TestFixJsonEncoding:
    """Tests for _fix_json_encoding function."""

    def test_fixes_unicode_escapes(self, tmp_path, mock_logger):
        """Test that Unicode escapes are converted to UTF-8."""
        # Create a test JSON file with Unicode escapes
        test_dir = tmp_path / "test-report"
        test_dir.mkdir()

        test_data = {
            "test": "\\u30C8\\u30FC\\u30AF\\u30F3",  # トークン in escaped form
            "name": "Test",
        }

        json_file = test_dir / "test.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=True)

        # Run the fix
        _fix_json_encoding(test_dir)

        # Verify the fix
        with open(json_file, encoding="utf-8") as f:
            fixed_data = json.load(f)

        assert fixed_data["test"] == "\\u30C8\\u30FC\\u30AF\\u30F3"

    def test_handles_empty_directory(self, tmp_path, mock_logger):
        """Test that empty directories are handled gracefully."""
        test_dir = tmp_path / "empty"
        test_dir.mkdir()

        # Should not raise an exception
        _fix_json_encoding(test_dir)

    def test_handles_errors_gracefully(self, tmp_path, mock_logger):
        """Test that errors are handled gracefully."""
        # Non-existent directory should not raise
        _fix_json_encoding(tmp_path / "nonexistent")


class TestLoadScanPresets:
    """Tests for load_scan_presets function."""

    def test_loads_valid_json(self, tmp_path, mock_logger):
        """Test loading valid JSON preset file."""
        preset_file = tmp_path / "preset.json"
        preset_data = {
            "spider_config": {"maxDuration": 10},
            "active_scan_config": {"threadPerHost": 4},
        }

        with open(preset_file, "w") as f:
            json.dump(preset_data, f)

        result = load_scan_presets(preset_file)

        assert result == preset_data
        assert result["spider_config"]["maxDuration"] == 10

    def test_raises_error_for_nonexistent_file(self, tmp_path, mock_logger):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            load_scan_presets(tmp_path / "nonexistent.json")

    def test_raises_error_for_invalid_json(self, tmp_path, mock_logger):
        """Test that JSONDecodeError is raised for invalid JSON."""
        preset_file = tmp_path / "invalid.json"
        with open(preset_file, "w") as f:
            f.write("invalid json content")

        with pytest.raises(json.JSONDecodeError):
            load_scan_presets(preset_file)


class TestSetupDirectories:
    """Tests for setup_directories task."""

    def test_creates_report_directory(self, scan_config, mock_logger):
        """Test that report directory is created."""
        setup_directories(scan_config)

        assert scan_config.report_dir.exists()
        assert scan_config.report_dir.is_dir()

    def test_creates_config_directory(self, scan_config, mock_logger):
        """Test that scanner-config directory is created."""
        setup_directories(scan_config)

        config_dir = scan_config.report_dir.parent / "scanner-config"
        assert config_dir.exists()
        assert config_dir.is_dir()

    def test_report_directory_has_correct_permissions(
        self, scan_config, mock_logger
    ):
        """Test that report directory has 777 permissions."""
        setup_directories(scan_config)

        # Check permissions (0o777)
        assert oct(scan_config.report_dir.stat().st_mode & 0o777) == oct(
            0o777
        )
