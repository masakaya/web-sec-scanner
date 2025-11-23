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

これらの設定ファイルは、CLIの`--config-file`オプションで指定できます（実装予定）。

```bash
# 高速スキャンの設定を使用
uv run python -m scanner.main automation https://example.com \
  --config-file resources/config/fast-scan.json

# 徹底的なスキャンの設定を使用
uv run python -m scanner.main automation https://example.com \
  --config-file resources/config/thorough-scan.json \
  --username admin --password secret
```

## 設定のカスタマイズ

必要に応じて、これらのファイルをコピーして独自の設定を作成できます：

```bash
cp resources/config/fast-scan.json resources/config/my-custom-scan.json
# my-custom-scan.jsonを編集
```

## 設定項目の説明

### spider_config
- `maxDuration`: 最大実行時間（分）
- `maxDepth`: クロール深度
- `maxChildren`: ノードあたりの最大子要素数
- `acceptCookies`: Cookie受け入れ
- `parseComments`: HTMLコメント解析
- `parseGit`: .gitディレクトリ解析
- `parseRobotsTxt`: robots.txt解析
- `parseSitemapXml`: sitemap.xml解析
- `postForm`: POSTフォーム送信
- `processForm`: フォーム処理

### ajax_spider_config
- `maxDuration`: 最大実行時間（分）
- `maxCrawlDepth`: クロール深度
- `numberOfBrowsers`: 並列ブラウザ数
- `clickDefaultElems`: デフォルト要素クリック
- `randomInputs`: ランダム入力生成

### active_scan_config
- `policy`: スキャンポリシー
- `maxRuleDurationInMins`: ルールあたりの最大実行時間
- `maxScanDurationInMins`: スキャン全体の最大実行時間
- `threadPerHost`: ホストあたりのスレッド数
- `handleAntiCSRFTokens`: CSRFトークン処理

### passive_scan_config
- `maxDuration`: 最大待機時間（分）

### sqliplugin_config
- `enabled`: SQLインジェクションスキャナーを有効化（デフォルト: true）
- `attackStrength`: 攻撃強度 (`LOW`, `MEDIUM`, `HIGH`, `INSANE`)
- `alertThreshold`: アラート閾値 (`OFF`, `LOW`, `MEDIUM`, `HIGH`)
