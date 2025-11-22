# Juice Shop Bearer/JWT認証テストガイド

OWASP Juice ShopでBearer/JWT認証のセキュリティスキャンをテストする手順です。

## 🚀 クイックスタート

### 1. Juice Shopを起動

```bash
docker compose up -d juice-shop
```

起動確認:
```bash
curl http://localhost:3000/api/version
```

### 2. JWTトークンを取得（自動）

ヘルパースクリプトを使用:
```bash
./scripts/get-juice-shop-token.sh
```

このスクリプトは自動的に:
- Juice Shopの起動を確認
- ログインしてJWTトークンを取得
- トークンの詳細を表示
- スキャン実行コマンド例を提示

### 3. スキャンを実行

スクリプトが出力したコマンドをコピーして実行。

---

## 📋 手動での手順

ヘルパースクリプトが使えない場合の手動手順です。

### ステップ1: Juice Shopにアクセス

ブラウザで http://localhost:3000 を開く

### ステップ2: アカウントを作成（初回のみ）

1. 右上の「Account」→「Login」をクリック
2. 「Not yet a customer?」をクリック
3. アカウント情報を入力:
   - Email: `test@example.com`
   - Password: `Test@1234`
   - Security Question: 任意
4. 「Register」をクリック

### ステップ3: JWTトークンを取得

#### 方法A: curlを使用（推奨）

```bash
# ログインAPIを叩く
curl -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@1234"}' \
  | jq -r '.authentication.token'
```

#### 方法B: ブラウザの開発者ツールを使用

1. ブラウザでログイン
2. 開発者ツールを開く（F12）
3. 「Application」→「Local Storage」→「http://localhost:3000」
4. `token` の値をコピー

### ステップ4: スキャンを実行

取得したトークンを使用してスキャン:

```bash
# 環境変数にトークンを保存
export JWT_TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

# fullスキャン実行
PYTHONPATH=src uv run python -m scanner.main full http://juice-shop:3000 \
  --auth-type bearer \
  --auth-token "$JWT_TOKEN" \
  --network web-sec-scanner_default \
  --ajax-spider \
  --max-duration 10
```

---

## 🔍 テスト内容

### Juice Shopの特徴

- **フレームワーク**: Angular (SPA)
- **認証方式**: JWT (Bearer トークン)
- **APIエンドポイント**: `/rest/*`, `/api/*`
- **脆弱性**: 100以上のOWASP Top 10脆弱性

### 認証付きでアクセスできるエンドポイント例

```bash
# ユーザーのバスケット情報
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:3000/rest/basket/1

# ユーザー情報
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:3000/rest/user/whoami

# 注文履歴
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:3000/rest/order-history
```

---

## 🎯 スキャンタイプ別の実行例

### 1. 高速スキャン (Automation Framework)

```bash
PYTHONPATH=src uv run python -m scanner.main automation http://juice-shop:3000 \
  --auth-type bearer \
  --auth-token "$JWT_TOKEN" \
  --network web-sec-scanner_default \
  --config-file resources/config/fast-scan.json \
  --max-duration 5
```

### 2. フルスキャン (推奨)

```bash
PYTHONPATH=src uv run python -m scanner.main full http://juice-shop:3000 \
  --auth-type bearer \
  --auth-token "$JWT_TOKEN" \
  --network web-sec-scanner_default \
  --ajax-spider \
  --max-duration 15 \
  --thread-per-host 15
```

### 3. APIスキャン

```bash
PYTHONPATH=src uv run python -m scanner.main api http://juice-shop:3000 \
  --auth-type bearer \
  --auth-token "$JWT_TOKEN" \
  --network web-sec-scanner_default \
  --max-duration 10
```

---

## ⚠️ トラブルシューティング

### トークンの有効期限切れ

JWTトークンは一定時間で期限切れになります。エラーが出たら再取得:

```bash
./scripts/get-juice-shop-token.sh
```

### ログインできない

デフォルトの `admin@juice-sh.op / admin123` は動作しない場合があります:

1. ブラウザで新しいアカウントを作成
2. 作成したアカウントでスクリプトを実行:
   ```bash
   ./scripts/get-juice-shop-token.sh your-email@example.com your-password
   ```

### Juice Shopが起動しない

```bash
# コンテナを再起動
docker compose restart juice-shop

# ログを確認
docker compose logs juice-shop

# 完全に削除して再起動
docker compose down juice-shop
docker compose up -d juice-shop
```

### ネットワークエラー

スキャナーとJuice Shopが同じDockerネットワークにいることを確認:

```bash
# ネットワーク名を確認
docker network ls | grep web-sec-scanner

# コンテナがネットワークに接続されているか確認
docker network inspect web-sec-scanner_default
```

---

## 📊 期待される結果

### スキャンで検出される主な脆弱性例

- SQL Injection
- XSS (Cross-Site Scripting)
- Broken Authentication
- JWT Token Manipulation
- CSRF (Cross-Site Request Forgery)
- Security Misconfiguration
- XXE (XML External Entities)
- Path Traversal

### レポートの確認

スキャン完了後、`report/` ディレクトリに以下が生成されます:
- `scan-report.html` - HTMLレポート
- `scan-report.json` - JSON形式の詳細データ
- `scan-report.xml` - XML形式のレポート

```bash
# HTMLレポートをブラウザで開く
xdg-open report/*/scan-report.html  # Linux
open report/*/scan-report.html      # macOS
```

---

## 🔗 参考リンク

- [OWASP Juice Shop公式サイト](https://owasp.org/www-project-juice-shop/)
- [Juice Shop GitHub](https://github.com/juice-shop/juice-shop)
- [Juice Shop Challenge Guide](https://pwning.owasp-juice.shop/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

---

## 💡 Tips

### トークンの内容を確認

```bash
# JWTをデコード（jq必須）
echo "$JWT_TOKEN" | cut -d. -f2 | base64 -d | jq '.'
```

### 複数ユーザーでテスト

```bash
# ユーザー1のトークン
TOKEN1=$(./scripts/get-juice-shop-token.sh user1@test.com password1)

# ユーザー2のトークン
TOKEN2=$(./scripts/get-juice-shop-token.sh user2@test.com password2)

# それぞれでスキャン実行
```

### 認証なしとの比較

```bash
# 認証なしでスキャン
PYTHONPATH=src uv run python -m scanner.main full http://juice-shop:3000 \
  --network web-sec-scanner_default \
  --max-duration 10

# 認証ありでスキャン
PYTHONPATH=src uv run python -m scanner.main full http://juice-shop:3000 \
  --auth-type bearer \
  --auth-token "$JWT_TOKEN" \
  --network web-sec-scanner_default \
  --max-duration 10

# 検出された脆弱性の差を比較
```
