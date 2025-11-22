# Renovate 自動依存関係更新

このプロジェクトでは [Renovate](https://docs.renovatebot.com/) を使用して、依存関係を自動的に最新に保ちます。

## 📋 概要

Renovate は依存関係の更新を自動的に検出し、Pull Request を作成します。

### 主な機能

- ✅ **自動依存関係更新**: `pyproject.toml` と `uv.lock` の依存関係を自動更新
- ✅ **セキュリティアラート対応**: 脆弱性のある依存関係を優先的に更新
- ✅ **自動マージ**: マイナー・パッチ更新は自動マージ（設定可能）
- ✅ **定期実行**: 毎週末に自動チェック
- ⚠️ **Python バージョン固定**: Python 本体のバージョンは更新しない

---

## 🔧 設定

### `.github/renovate.json`

Renovate の設定ファイルです。

**主な設定:**

```json
{
  "schedule": ["every weekend"],
  "timezone": "Asia/Tokyo",
  "automerge": true,  // マイナー・パッチは自動マージ
  "lockFileMaintenance": {
    "enabled": true  // ロックファイルの定期メンテナンス
  }
}
```

### `.github/workflows/renovate.yml`

GitHub Actions でセルフホスト型 Renovate を実行します。

**実行タイミング:**
- 毎週土曜日 3:00 JST（自動）
- 手動実行可能（workflow_dispatch）
- renovate.json 変更時

---

## 🚀 使い方

### 手動実行

1. GitHub の **Actions** タブを開く
2. **Renovate** ワークフローを選択
3. **Run workflow** をクリック

### PR の確認

Renovate が作成した PR を確認：

```bash
# ラベルでフィルタリング
gh pr list --label "dependencies"

# Renovate PR を表示
gh pr list --label "renovate"
```

---

## 📊 更新ポリシー

### 自動マージされる更新

以下は自動的にマージされます（設定で変更可能）：

- ✅ **開発依存関係**のマイナー・パッチ更新
  - mypy, ruff, pytest など
- ✅ **ロックファイル**のメンテナンス更新

### 手動レビューが必要な更新

以下は手動レビューが必要です：

- ⚠️ **メジャーバージョン**更新（破壊的変更の可能性）
- ⚠️ **本番依存関係**の更新
- ⚠️ **セキュリティ関連**の更新

---

## 🔒 Python バージョンの固定

Python 本体のバージョンは**更新されません**。

`renovate.json` で以下のように設定されています：

```json
{
  "packageRules": [
    {
      "matchPackageNames": ["python"],
      "enabled": false
    }
  ]
}
```

Python バージョンを更新する場合は、手動で `pyproject.toml` を編集してください。

---

## 🎯 カスタマイズ

### 自動マージを無効化

自動マージを無効にする場合：

```json
{
  "packageRules": [
    {
      "matchUpdateTypes": ["minor", "patch"],
      "automerge": false
    }
  ]
}
```

### スケジュール変更

更新チェックのスケジュールを変更：

```json
{
  "schedule": [
    "after 10pm every weekday",
    "before 5am every weekday",
    "every weekend"
  ]
}
```

### PR 数の制限

同時に作成される PR の数を制限：

```json
{
  "prConcurrentLimit": 5,
  "prHourlyLimit": 2
}
```

---

## 🐛 トラブルシューティング

### Renovate が動作しない

1. **GitHub Token の確認**
   - `GITHUB_TOKEN` に必要な権限があるか確認
   - または `RENOVATE_TOKEN` を設定

2. **ワークフローの実行履歴を確認**
   ```bash
   gh run list --workflow=renovate.yml
   ```

3. **ログレベルを上げて実行**
   - 手動実行時に `debug` または `trace` を選択

### PR が自動マージされない

1. **ブランチ保護ルール**を確認
2. **Status checks** が通っているか確認
3. `automerge` 設定を確認

---

## 📚 参考リンク

- [Renovate 公式ドキュメント](https://docs.renovatebot.com/)
- [Configuration Options](https://docs.renovatebot.com/configuration-options/)
- [Python Support](https://docs.renovatebot.com/modules/manager/pep621/)
- [GitHub Action](https://github.com/renovatebot/github-action)

---

## 💡 ベストプラクティス

1. **定期的な確認**: 週次で Renovate の PR を確認
2. **テストの充実**: 自動マージ前に CI が通ることを確認
3. **段階的な更新**: メジャー更新は慎重にレビュー
4. **ロックファイル**: `uv.lock` を必ずコミットに含める
5. **セキュリティ優先**: 脆弱性のある依存関係は最優先で対応
