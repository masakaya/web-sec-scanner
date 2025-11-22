#!/bin/bash
# ローカルでreviewdogを使ってmypyの結果を確認する

set -e

echo "🔍 mypyで型チェック中..."

# reviewdogがインストールされているか確認
if ! command -v reviewdog &> /dev/null; then
    echo "⚠️  reviewdogがインストールされていません。"
    echo ""
    echo "インストール方法:"
    echo "  macOS: brew install reviewdog"
    echo "  Linux: https://github.com/reviewdog/reviewdog#installation"
    echo ""
    echo "または、通常のmypyチェックを実行します..."
    uv run mypy .
    exit 0
fi

# mypyの結果をreviewdogで表示
echo "📝 reviewdogで結果を表示します..."
uv run mypy . --show-column-numbers --no-error-summary 2>&1 | \
    reviewdog -f=mypy -reporter=local -level=error

echo ""
echo "✅ チェック完了！"
echo ""
echo "💡 ヒント:"
echo "  - 型アノテーション追加: docs/MYPY.md 参照"
echo "  - 厳格モード: poe typecheck-strict"
