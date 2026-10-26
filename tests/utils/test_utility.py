"""utilityモジュールのユニットテスト。"""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.utility import find_project_root, get_report_dir


class TestFindProjectRoot:
    """find_project_root関数のテストクラス。"""

    def test_find_project_root_with_pyproject_toml(self, tmp_path):
        """pyproject.tomlが存在する場合、プロジェクトルートを見つけることをテスト。"""
        # プロジェクト構造を作成
        project_root = tmp_path / "my_project"
        project_root.mkdir()
        (project_root / "pyproject.toml").touch()

        sub_dir = project_root / "src" / "scanner"
        sub_dir.mkdir(parents=True)

        # サブディレクトリから検索
        found_root = find_project_root(start_path=sub_dir)

        assert found_root == project_root

    def test_find_project_root_with_git(self, tmp_path):
        """`.git`が存在する場合、プロジェクトルートを見つけることをテスト。"""
        # プロジェクト構造を作成
        project_root = tmp_path / "my_project"
        project_root.mkdir()
        git_dir = project_root / ".git"
        git_dir.mkdir()

        sub_dir = project_root / "src" / "utils"
        sub_dir.mkdir(parents=True)

        # サブディレクトリから検索
        found_root = find_project_root(start_path=sub_dir)

        assert found_root == project_root

    def test_find_project_root_with_custom_markers(self, tmp_path):
        """カスタムマーカーでプロジェクトルートを見つけることをテスト。"""
        # プロジェクト構造を作成
        project_root = tmp_path / "my_project"
        project_root.mkdir()
        (project_root / "setup.py").touch()

        sub_dir = project_root / "tests"
        sub_dir.mkdir()

        # カスタムマーカーで検索
        found_root = find_project_root(markers=("setup.py",), start_path=sub_dir)

        assert found_root == project_root

    def test_find_project_root_no_marker_found(self, tmp_path):
        """マーカーが見つからない場合、開始パスを返すことをテスト。"""
        # マーカーなしのディレクトリ構造を作成
        some_dir = tmp_path / "random_dir" / "nested"
        some_dir.mkdir(parents=True)

        # マーカーが見つからない場合、開始パスを返す
        found_root = find_project_root(start_path=some_dir)

        assert found_root == some_dir

    def test_find_project_root_multiple_markers(self, tmp_path):
        """複数のマーカーのいずれかが存在する場合、プロジェクトルートを見つけることをテスト。"""
        # プロジェクト構造を作成
        project_root = tmp_path / "my_project"
        project_root.mkdir()
        # 複数のマーカーのうち1つだけ作成
        git_dir = project_root / ".git"
        git_dir.mkdir()
        # pyproject.tomlは作成しない

        sub_dir = project_root / "src"
        sub_dir.mkdir()

        # デフォルトマーカー（pyproject.toml と .git）で検索
        found_root = find_project_root(start_path=sub_dir)

        assert found_root == project_root

    def test_find_project_root_from_current_directory(self, tmp_path, monkeypatch):
        """start_pathが指定されていない場合、カレントディレクトリから検索することをテスト。"""
        # プロジェクト構造を作成
        project_root = tmp_path / "my_project"
        project_root.mkdir()
        (project_root / "pyproject.toml").touch()

        # カレントディレクトリを変更
        monkeypatch.chdir(project_root)

        # start_pathなしで検索
        found_root = find_project_root()

        assert found_root == project_root

    def test_find_project_root_at_root_level(self, tmp_path):
        """プロジェクトルート自体で検索した場合をテスト。"""
        # プロジェクト構造を作成
        project_root = tmp_path / "my_project"
        project_root.mkdir()
        (project_root / "pyproject.toml").touch()

        # プロジェクトルートから検索
        found_root = find_project_root(start_path=project_root)

        assert found_root == project_root


class TestGetReportDir:
    """get_report_dir関数のテストクラス。"""

    def test_get_report_dir_default_name(self, tmp_path, monkeypatch):
        """デフォルトのレポートディレクトリ名でパスを取得することをテスト。"""
        # プロジェクト構造を作成
        project_root = tmp_path / "my_project"
        project_root.mkdir()
        (project_root / "pyproject.toml").touch()

        # カレントディレクトリを変更
        monkeypatch.chdir(project_root)

        # レポートディレクトリパスを取得
        report_dir = get_report_dir()

        assert report_dir == project_root / "report"
        assert report_dir.parent == project_root

    def test_get_report_dir_custom_name(self, tmp_path, monkeypatch):
        """カスタムレポートディレクトリ名でパスを取得することをテスト。"""
        # プロジェクト構造を作成
        project_root = tmp_path / "my_project"
        project_root.mkdir()
        (project_root / "pyproject.toml").touch()

        # カレントディレクトリを変更
        monkeypatch.chdir(project_root)

        # カスタム名でレポートディレクトリパスを取得
        report_dir = get_report_dir(base_name="scan_results")

        assert report_dir == project_root / "scan_results"
        assert report_dir.name == "scan_results"

    def test_get_report_dir_returns_path_object(self, tmp_path, monkeypatch):
        """Pathオブジェクトを返すことをテスト。"""
        # プロジェクト構造を作成
        project_root = tmp_path / "my_project"
        project_root.mkdir()
        (project_root / ".git").mkdir()

        # カレントディレクトリを変更
        monkeypatch.chdir(project_root)

        # レポートディレクトリパスを取得
        report_dir = get_report_dir()

        assert isinstance(report_dir, Path)

    def test_get_report_dir_nested_project(self, tmp_path, monkeypatch):
        """ネストされたディレクトリ構造でも正しく動作することをテスト。"""
        # プロジェクト構造を作成
        project_root = tmp_path / "workspace" / "my_project"
        project_root.mkdir(parents=True)
        (project_root / "pyproject.toml").touch()

        sub_dir = project_root / "src" / "scanner"
        sub_dir.mkdir(parents=True)

        # サブディレクトリから実行
        monkeypatch.chdir(sub_dir)

        # レポートディレクトリパスを取得
        report_dir = get_report_dir()

        # プロジェクトルート配下のreportディレクトリを指すはず
        assert report_dir == project_root / "report"
