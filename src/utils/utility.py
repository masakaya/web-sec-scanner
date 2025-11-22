"""ユーティリティ関数モジュール。

プロジェクトルート検出やファイルパス解決などの共通機能を提供する。
"""
# ruff: noqa: D400, D415

from pathlib import Path


def find_project_root(
    markers: tuple[str, ...] = ("pyproject.toml", ".git"),
    start_path: Path | None = None,
) -> Path:
    """プロジェクトルートディレクトリを探す。

    指定されたマーカーファイル/ディレクトリを持つ親ディレクトリを探す。
    見つからない場合は、開始パスを返す。

    Args:
        markers: プロジェクトルートを示すファイル/ディレクトリ名のタプル
        start_path: 検索開始パス（Noneの場合はカレントディレクトリ）

    Returns:
        プロジェクトルートのPath

    Examples:
        >>> root = find_project_root()
        >>> root = find_project_root(markers=("pyproject.toml",))
        >>> root = find_project_root(start_path=Path("/path/to/subdir"))

    """
    current = start_path or Path.cwd()

    # 現在のディレクトリから親を辿ってマーカーを探す
    for parent in [current, *current.parents]:
        if any((parent / marker).exists() for marker in markers):
            return parent

    # 見つからない場合は開始パスを返す
    return current


def get_report_dir(base_name: str = "report") -> Path:
    """レポート出力ディレクトリのパスを取得する。

    プロジェクトルート配下にレポートディレクトリを作成して返す。

    Args:
        base_name: レポートディレクトリの名前（デフォルト: "report"）

    Returns:
        レポートディレクトリのPath

    """
    project_root = find_project_root()
    report_dir = project_root / base_name
    return report_dir
