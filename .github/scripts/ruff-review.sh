#!/bin/bash
# ローカルでreviewdogを使ってRuffの結果を確認する

set -e

echo "🔍 Ruffでコードをチェック中..."

# reviewdogがインストールされているか確認
if ! command -v reviewdog &> /dev/null; then
    echo "⚠️  reviewdogがインストールされていません。"
    echo ""
    echo "インストール方法:"
    echo "  macOS: brew install reviewdog"
    echo "  Linux: https://github.com/reviewdog/reviewdog#installation"
    echo ""
    echo "または、通常のRuffチェックを実行します..."
    uv run ruff check .
    exit 0
fi

# Ruffの結果をreviewdogで表示
echo "📝 reviewdogで結果を表示します..."
uv run ruff check . --output-format=json | \
    reviewdog -f=ruff -reporter=local -level=warning

echo ""
echo "✅ チェック完了！"
echo ""
echo "💡 ヒント:"
echo "  - 自動修正: uv run ruff check --fix ."
echo "  - レポート生成: uv run review"
