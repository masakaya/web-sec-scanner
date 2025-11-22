# Ruff統合ガイド：シームレスな開発環境

このプロジェクトでは、Ruffによる自動チェック・修正システムを導入しています。

## 📋 目次

1. [Ruffの挙動](#ruffの挙動)
2. [開発環境での統合](#開発環境での統合)
3. [コマンドラインでの使用](#コマンドラインでの使用)
4. [CI/CDでの自動化](#cicdでの自動化)

---

## 🔍 Ruffの挙動

### 自動修正可能な問題

以下のような問題は `ruff check --fix` で自動的に修正されます：

- ✅ 未使用のインポート削除 (F401)
- ✅ インポートの並び替え (I001)
- ✅ f-stringへの変換 (UP032)
- ✅ 古い構文の更新 (UP系)
- ✅ その他多数（詳細は `ruff.toml` 参照）

### 手動修正が必要な問題

以下のような問題は自動修正できません：

- ❌ 命名規則違反 (N802, N801など)
- ❌ bare exceptの使用 (E722)
- ❌ 未定義の変数 (F821)
- ❌ 複雑度が高すぎる関数 (C901)

### 安全でない修正

一部の問題は `--unsafe-fixes` で修正可能ですが、コードの意味が変わる可能性があります：

- ⚠️ ネストしたif文の結合 (SIM102)
- ⚠️ try-except-passの置き換え (SIM105)

---

## 💻 開発環境での統合

### VSCode

1. **Ruff拡張機能をインストール**
   ```bash
   code --install-extension charliermarsh.ruff
   ```

2. **プロジェクトの設定ファイルを確認**
   - `.vscode/settings.json` が既に設定済み
   - `ruff.toml` の設定が自動的に適用されます

3. **保存時の動作**
   - ファイル保存時（Ctrl+S / Cmd+S）に自動的に：
     - コードフォーマット実行
     - 自動修正可能な問題を修正
     - インポートを整理

4. **リアルタイム表示**
   - エディタ内でルール違反を波線で表示
   - ホバーで詳細説明とドキュメントリンクを表示

### PyCharm / IntelliJ IDEA

1. **Ruffプラグインをインストール**
   - Settings → Plugins → "Ruff" を検索してインストール

2. **設定**
   - Settings → Tools → Ruff
   - "Run ruff on save" を有効化
   - "Use ruff formatter" を有効化

3. **プロジェクト設定が自動適用**
   - `ruff.toml` が自動的に検出されます

### Vim / Neovim

```lua
-- LSP設定例（nvim-lspconfig使用）
require('lspconfig').ruff_lsp.setup {
  init_options = {
    settings = {
      -- ruff.tomlが自動的に検出されます
    }
  }
}
```

---

## 🚀 コマンドラインでの使用

### 基本コマンド

```bash
# チェックのみ（問題を表示）
poe lint

# チェック＋自動修正
poe lint-fix

# フォーマット
poe format

# 安全でない修正も実行
poe lint-unsafe

# または直接ruff実行
uv run ruff check .
```

### プロジェクト独自のショートカット

```bash
# チェックのみ
poe lint

# フォーマット
poe format
```

### ワークフロー例

```bash
# 1. 開発中：保存時にIDEが自動修正

# 2. コミット前：手動で全体チェック
poe lint-fix
poe format

# 3. コミット
git add .
git commit -m "feat: 新機能追加"
```

---

## 🤖 CI/CDでの自動化

### GitHub Actions + reviewdog

`.github/workflows/ruff.yml` が設定済みです。

#### 動作

1. **プッシュ/PR時に自動実行**
   - main, develop ブランチへのプッシュ
   - Pull Request作成時

2. **reviewdogによる自動レビュー**
   - **PRの該当行に直接コメント**を投稿
   - 自動修正可能/不可能を明示
   - ドキュメントリンクを自動添付
   - GitHub Checksとして統合

3. **実行内容**
   - Ruffチェック + reviewdog連携
   - **自動フォーマット＋コミット**（PR時のみ）
     - `ruff format .` を自動実行
     - フォーマット変更を自動コミット
     - github-actions[bot] がコミット
   - すべてのPRに対応

4. **成果物**
   - PRの各行にインラインコメント（reviewdog）
     - Ruff: コード品質の問題

#### reviewdogの利点

- ✅ **該当箇所に直接コメント** - コードレビューのように表示
- ✅ **自動修正の提案** - fixableなものは修正方法を提示
- ✅ **GitHub Checks統合** - PRのステータスに反映
- ✅ **差分のみチェック** - 変更した部分だけレビュー

> **注意:**
> - 型チェック（mypy）は別のワークフロー（`.github/workflows/mypy.yml`）で実行されます
> - テストは別のワークフロー（`.github/workflows/test.yml`）で実行されます
> - いずれも手動実行可能です

#### ローカルでreviewdogを使う

```bash
# reviewdogのインストール（初回のみ）
# macOS
brew install reviewdog

# Linux
# https://github.com/reviewdog/reviewdog#installation

# ローカルでreviewdog実行（Ruff）
poe review-local
# または
./.github/scripts/ruff-review.sh

# ローカルでreviewdog実行（mypy）
poe typecheck-review
# または
./.github/scripts/mypy-review.sh

# または直接実行
# Ruff
uv run ruff check . --output-format=json | \
  reviewdog -f=ruff -reporter=local -level=warning

# mypy
uv run mypy . --show-column-numbers --no-error-summary | \
  reviewdog -f=mypy -reporter=local -level=error
```

#### GitHub Actions形式の出力を確認

```bash
uv run ruff check . --output-format=github
```

---

## 🔧 カスタマイズ

### ルールの調整

`ruff.toml` を編集：

```toml
[lint]
# 追加のルールを有効化
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM", "S"]  # "S" を追加

# 特定のルールを無視
ignore = [
    "E501",  # 行の長さ制限
    "N802",  # 関数名の命名規則（キャメルケースを許可したい場合）
]
```

### ファイル別の設定

```toml
[lint.per-file-ignores]
# テストファイルでは特定のルールを無視
"tests/**/*.py" = [
    "S101",  # assertの使用を許可
    "PLR2004",  # マジックナンバーを許可
]

# スクリプトファイル
"scripts/**/*.py" = [
    "T201",  # print文の使用を許可
]
```

---

## 📚 参考リンク

- [Ruff公式ドキュメント](https://docs.astral.sh/ruff/)
- [全ルール一覧](https://docs.astral.sh/ruff/rules/)
- [ruff.toml設定リファレンス](https://docs.astral.sh/ruff/configuration/)
- [VSCode拡張機能](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)

---

## 💡 ベストプラクティス

1. **IDE統合を最優先**
   - 保存時に自動修正されるため、最もシームレス
   - リアルタイムフィードバックで学習効果も高い

2. **コミット前にチェック**
   - `poe lint-fix` を実行
   - `poe check` で全チェック実行

3. **CIで品質を保証**
   - GitHub Actionsが自動チェック
   - reviewdogがPRに自動コメント

4. **チーム全体で同じ設定を共有**
   - `ruff.toml` をGitで管理
   - VSCode設定（`.vscode/`）も共有
   - 全員が同じルールでチェック

5. **段階的な導入**
   - 最初は自動修正可能な問題のみ対応
   - 徐々に厳しいルールを追加
   - チームで合意を取りながら進める
