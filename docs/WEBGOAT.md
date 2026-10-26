# WebGoat テスト環境

このプロジェクトには、セキュリティ診断レポート出力のサンプルとして使用する **WebGoat** 環境が含まれています。

## 📋 概要

WebGoatは、OWASPが提供する意図的に脆弱性を含んだWebアプリケーションです。
このプロジェクトでは、セキュリティ診断ツールでスキャンを実行し、レポートを生成するためのテスト対象として使用します。

### 含まれるコンポーネント

- **WebGoat**: セキュリティ脆弱性を含むWebアプリケーション（ポート8080）
- **WebWolf**: WebGoatの補助ツール（ポート9090）

---

## 🚀 クイックスタート

### 前提条件

- Docker
- Docker Compose

### 起動方法

```bash
# WebGoat環境を起動
docker compose up -d
```

### アクセス方法

WebGoat環境が起動したら、以下のURLにアクセスできます：

- **WebGoat**: http://localhost:8080/WebGoat
- **WebWolf**: http://localhost:9090/WebWolf

### 初回ログイン

1. WebGoat（http://localhost:8080/WebGoat）にアクセス
2. 「Register new user」をクリック
3. ユーザー名とパスワードを設定してアカウント作成
4. 作成したアカウントでログイン

---

## 🛠️ 管理コマンド

### Docker Compose操作

```bash
# 環境を起動
docker compose up -d

# 環境を停止
docker compose down

# ログを確認
docker compose logs -f webgoat

# 環境を再起動
docker compose restart

# 環境を完全削除（データも削除）
docker compose down -v
```

### コンテナの状態確認

```bash
# コンテナの状態を確認
docker compose ps

# リソース使用状況を確認
docker stats webgoat
```

---

## 🎯 このプロジェクトでの活用方法

WebGoat環境は、セキュリティ診断レポート出力ツールの開発とテストに使用します：

1. **スキャンの実行**: WebGoatに対してセキュリティ診断ツールでスキャンを実行
2. **レポート生成**: スキャン結果からレポートを生成
3. **レポート形式のテスト**: 様々なレポート形式（HTML, JSON, XMLなど）の出力テスト
4. **サンプルレポート作成**: ドキュメント用のサンプルレポートを生成

---

## ⚠️ 重要な注意事項

### セキュリティ警告

- **ローカル環境のみで使用**: WebGoatは意図的に脆弱なので、インターネットに公開しないでください
- **本番環境で使用禁止**: 絶対に本番環境やアクセス可能なネットワークで起動しないでください
- **テスト目的のみ**: WebGoatはセキュリティ診断レポート出力のテスト目的専用です

### ファイアウォール設定

ローカルマシンのファイアウォールで、以下のポートへの外部アクセスをブロックしてください：

- 8080（WebGoat）
- 9090（WebWolf）

### データの永続性

デフォルトでは、コンテナを削除してもデータは保持されます。完全にデータを削除する場合は：

```bash
docker compose down -v
```

---

## 🐛 トラブルシューティング

### コンテナが起動しない

```bash
# ログを確認
docker compose logs webgoat

# ポートが使用されているか確認
lsof -i :8080
lsof -i :9090

# コンテナを完全削除して再起動
docker compose down -v
docker compose up -d
```

### アクセスできない

1. コンテナが起動しているか確認:
   ```bash
   docker compose ps
   ```

2. ブラウザのキャッシュをクリア

3. 正しいURLにアクセスしているか確認:
   - http://localhost:8080/WebGoat（末尾の`/WebGoat`が必要）

### パフォーマンスが悪い

WebGoatはJavaアプリケーションで、メモリを多く使用します。Docker Desktopの設定でメモリを増やしてください（推奨: 4GB以上）。

---

## 📚 参考リンク

- [WebGoat公式サイト](https://owasp.org/www-project-webgoat/)
- [WebGoat GitHub](https://github.com/WebGoat/WebGoat)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

---

## 📝 ライセンス

WebGoatはOWASPプロジェクトで、教育目的で自由に使用できます。詳細は[WebGoatのライセンス](https://github.com/WebGoat/WebGoat/blob/main/LICENSE)を参照してください。
