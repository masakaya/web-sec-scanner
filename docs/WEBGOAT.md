# WebGoat テスト環境

このプロジェクトには、Webアプリケーションのセキュリティテストを学習・実践するための **WebGoat** 環境が含まれています。

## 📋 概要

WebGoatは、OWASPが提供する意図的に脆弱性を含んだWebアプリケーションで、セキュリティテストの学習と実践に最適な環境です。

### 含まれるコンポーネント

- **WebGoat**: セキュリティ脆弱性の学習用Webアプリケーション（ポート8080）
- **WebWolf**: WebGoatの補助ツール（ポート9090）

---

## 🚀 クイックスタート

### 前提条件

- Docker
- Docker Compose

### 起動方法

```bash
# WebGoat環境を起動
poe webgoat-start

# または、docker composeコマンドで直接起動
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
poe webgoat-start
# または
docker compose up -d

# 環境を停止
poe webgoat-stop
# または
docker compose down

# ログを確認
poe webgoat-logs
# または
docker compose logs -f webgoat

# 環境を再起動
poe webgoat-restart
# または
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

## 📚 WebGoatの使い方

### レッスン構成

WebGoatには以下のようなセキュリティトピックが含まれています：

1. **一般的な脆弱性**
   - SQL Injection
   - Cross-Site Scripting (XSS)
   - Cross-Site Request Forgery (CSRF)
   - Path Traversal
   - Authentication Bypass

2. **アクセス制御**
   - Broken Access Control
   - Insecure Direct Object References

3. **認証とセッション管理**
   - Session Management
   - Authentication Flaws
   - JWT Tokens

4. **その他**
   - XML External Entities (XXE)
   - Insecure Deserialization
   - Server-Side Request Forgery (SSRF)

### 学習の進め方

1. **レッスンを選択**: 左側のメニューから学習したいトピックを選択
2. **説明を読む**: 各レッスンには脆弱性の説明が含まれています
3. **課題に挑戦**: 実際に脆弱性を突いて課題をクリア
4. **解答を確認**: 詰まった場合はヒントや解答を参照可能

---

## 🔧 設定

### ポート設定

デフォルトのポート設定は以下の通りです：

- WebGoat: `8080`
- WebWolf: `9090`

ポートを変更する場合は、`compose.yml` を編集してください：

```yaml
services:
  webgoat:
    ports:
      - "カスタムポート:8080"
      - "カスタムポート:9090"
```

### 環境変数

`compose.yml` で以下の環境変数を設定できます：

- `WEBGOAT_HOST`: WebGoatのホスト（デフォルト: 0.0.0.0）
- `WEBGOAT_PORT`: WebGoatのポート（デフォルト: 8080）
- `WEBWOLF_HOST`: WebWolfのホスト（デフォルト: 0.0.0.0）
- `WEBWOLF_PORT`: WebWolfのポート（デフォルト: 9090）

---

## 🎯 このプロジェクトでの活用方法

このWebGoat環境は、開発中のWebセキュリティスキャナーのテスト対象として使用できます：

1. **スキャナーの開発**: WebGoatの既知の脆弱性に対してスキャナーをテスト
2. **検出精度の確認**: 正しく脆弱性を検出できるか検証
3. **誤検知の削減**: 正常な機能を脆弱性として誤検知しないか確認
4. **パフォーマンステスト**: スキャン速度や負荷テストの実施

### スキャン例

```python
# 将来的な実装例
from scanner import WebSecScanner

scanner = WebSecScanner(target="http://localhost:8080/WebGoat")
results = scanner.scan()
print(f"Found {len(results)} vulnerabilities")
```

---

## ⚠️ 重要な注意事項

### セキュリティ警告

- **ローカル環境のみで使用**: WebGoatは意図的に脆弱なので、インターネットに公開しないでください
- **本番環境で使用禁止**: 絶対に本番環境やアクセス可能なネットワークで起動しないでください
- **学習目的のみ**: WebGoatは教育目的専用です

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
- [WebGoatドキュメント](https://github.com/WebGoat/WebGoat/wiki)

---

## 📝 ライセンス

WebGoatはOWASPプロジェクトで、教育目的で自由に使用できます。詳細は[WebGoatのライセンス](https://github.com/WebGoat/WebGoat/blob/main/LICENSE)を参照してください。
