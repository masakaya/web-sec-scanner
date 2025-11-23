# スキャン設定ファイル

このディレクトリには、セキュリティスキャンの詳細設定ファイルが含まれています。

## 設定ファイル一覧

### fast-scan.json
高速スキャン用の設定。短時間で基本的な脆弱性をチェックします。

- **スパイダー**: 5分、深度5、子要素10
- **アクティブスキャン**: 10分、スレッド2
- **パッシブスキャン**: 2分
- **推奨用途**: 開発中の頻繁なチェック、CIパイプライン

### thorough-scan.json
徹底的なスキャン用の設定。詳細な脆弱性検査を実行します。

- **スパイダー**: 60分、深度20、子要素50
- **AJAXスパイダー**: 60分、深度20、ブラウザ4つ
- **アクティブスキャン**: 120分、スレッド8
- **パッシブスキャン**: 15分
- **推奨用途**: 本番前の最終チェック、定期的なセキュリティ監査

## 使用方法

### 基本的な使用例

```bash
# 高速スキャンの設定を使用
uv run python -m src.scanner.main automation https://example.com \
  --config-file resources/config/fast-scan.json

# 徹底的なスキャンの設定を使用
uv run python -m src.scanner.main automation https://example.com \
  --config-file resources/config/thorough-scan.json
```

### 認証が必要なアプリケーションのスキャン

```bash
# フォーム認証の場合
uv run python -m src.scanner.main automation https://example.com/app \
  --username admin \
  --password secret \
  --auth-type form \
  --login-url https://example.com/login \
  --logged-in-indicator "ログアウト" \
  --config-file resources/config/fast-scan.json

# Basic認証の場合
uv run python -m src.scanner.main automation https://example.com/api \
  --username admin \
  --password secret \
  --auth-type basic \
  --config-file resources/config/thorough-scan.json
```

### Dockerコンテナのスキャン

```bash
# Dockerネットワークを自動検出してスキャン
uv run python -m src.scanner.main automation http://app-container:8080 \
  --config-file resources/config/fast-scan.json

# ネットワークを明示的に指定
uv run python -m src.scanner.main automation http://app-container:8080 \
  --network my-network \
  --config-file resources/config/fast-scan.json
```

### スキャン時間の制限

```bash
# 最大10分でスキャンを終了
uv run python -m src.scanner.main automation https://example.com \
  --config-file resources/config/fast-scan.json \
  --max-duration 10
```

## レポート出力

スキャン完了後、以下のファイルが自動生成されます：

### レポートディレクトリ構造

```
reports/
└── YYYYMMDD_HHMMSS_<scan-type>/
    ├── scan-report.html      # ZAPデフォルトレポート
    ├── scan-report.json      # JSON形式の詳細レポート
    └── security-report.html  # カスタムHTMLレポート（推奨）
```

### カスタムHTMLレポートの特徴

- **セキュリティスコア**: 100点満点で脆弱性の深刻度を数値化
  - High検出: -10点
  - Medium検出: -3点
  - Low検出: -1点

- **6段階グレード評価**:
  - A: 80-100点 (緑) - 優秀
  - B: 60-79点 (青) - 良好
  - C: 40-59点 (黄) - 要注意
  - D: 20-39点 (オレンジ) - 危険
  - E: 1-19点 (赤) - 重大
  - F: 0点 (赤) - 最悪

- **詳細な脆弱性情報**:
  - 脆弱性の種類と深刻度
  - 影響を受けるURL一覧
  - 攻撃手法と証拠
  - 推奨される対策方法
  - 参考リンク

## 設定のカスタマイズ

必要に応じて、これらのファイルをコピーして独自の設定を作成できます：

```bash
# カスタム設定ファイルを作成
cp resources/config/fast-scan.json resources/config/my-custom-scan.json

# my-custom-scan.jsonを編集して使用
uv run python -m src.scanner.main automation https://example.com \
  --config-file resources/config/my-custom-scan.json
```

## 設定項目の説明

### spider_config
Webアプリケーションのページを探索するための設定。

- `maxDuration`: 最大実行時間（分）
- `maxDepth`: クロール深度（0から始まるリンクの階層）
- `maxChildren`: ノードあたりの最大子要素数
- `acceptCookies`: Cookie受け入れ
- `parseComments`: HTMLコメント内のURLを解析
- `parseGit`: .gitディレクトリの解析（Git情報漏洩チェック）
- `parseRobotsTxt`: robots.txtの解析
- `parseSitemapXml`: sitemap.xmlの解析
- `postForm`: POSTフォームの送信
- `processForm`: フォームの処理

### ajax_spider_config
JavaScriptで動的に生成されるコンテンツを探索するための設定。

- `maxDuration`: 最大実行時間（分）
- `maxCrawlDepth`: クロール深度
- `numberOfBrowsers`: 並列実行するブラウザ数
- `clickDefaultElems`: デフォルト要素のクリック
- `randomInputs`: ランダム入力の生成

### active_scan_config
脆弱性を積極的に検査するための設定。

- `policy`: スキャンポリシー（`Default Policy`など）
- `maxRuleDurationInMins`: 1つのルールあたりの最大実行時間
- `maxScanDurationInMins`: スキャン全体の最大実行時間
- `threadPerHost`: ホストあたりのスレッド数（並列度）
- `handleAntiCSRFTokens`: CSRFトークンの自動処理

### passive_scan_config
通信内容を監視して脆弱性を検出するための設定。

- `maxDuration`: 最大待機時間（分）

### sqliplugin_config
SQLインジェクションスキャナーの設定。

- `enabled`: SQLインジェクションスキャナーを有効化（デフォルト: true）
- `attackStrength`: 攻撃強度
  - `LOW`: 低（軽量なペイロードのみ）
  - `MEDIUM`: 中（標準的なペイロード）
  - `HIGH`: 高（多数のペイロード）
  - `INSANE`: 最高（すべてのペイロード、時間がかかる）
- `alertThreshold`: アラート閾値
  - `OFF`: アラートなし
  - `LOW`: 低い信頼度でもアラート
  - `MEDIUM`: 中程度の信頼度でアラート
  - `HIGH`: 高い信頼度のみアラート

## ベストプラクティス

### 開発環境での使用
- `fast-scan.json` を使用して頻繁にスキャン
- CIパイプラインに組み込んで自動チェック
- セキュリティスコアがB（60点）以上を維持

### ステージング環境での使用
- `thorough-scan.json` を使用して詳細チェック
- 本番デプロイ前の最終確認
- セキュリティスコアがA（80点）以上を目標

### 本番環境での使用
- 定期的に `thorough-scan.json` でスキャン
- 認証情報は環境変数から読み込み
- スキャン結果を保存してトレンド分析

## トラブルシューティング

### スキャンが途中で停止する
- `--max-duration` オプションで時間制限を調整
- 設定ファイルの各 `maxDuration` 値を増やす

### Dockerコンテナにアクセスできない
- `--network` オプションでネットワークを明示的に指定
- コンテナ名が正しいか確認（`docker ps` で確認）

### 認証がうまくいかない
- `--logged-in-indicator` の文字列が正しいか確認
- ログイン後のページに表示される特徴的な文字列を指定
- ブラウザで実際にログインして確認

### レポートが生成されない
- スキャンが正常に完了したか確認
- `reports/` ディレクトリの権限を確認
- ログファイルでエラーメッセージを確認
