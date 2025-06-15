# HEIC to JPG Converter

Google DriveからHEICファイルをダウンロードしてJPGに変換するPythonツールです。ブログ用の画像最適化に特化しています。

## 特徴

- Google Drive APIを使用してHEICファイルを自動検索・ダウンロード
- 高品質なJPG変換（品質・サイズ調整可能）
- バッチ処理対応
- 重複変換の自動スキップ
- 圧縮率レポート機能
- 環境変数による設定管理

## インストール

### 前提条件
- Python 3.7以上
- Google Drive APIアクセス権限

### セットアップ

1. **リポジトリのクローン**
```bash
git clone <repository-url>
cd heic2jpg
```

2. **依存関係のインストール**
```bash
pip install -r requirements.txt
```

3. **Google Drive API設定**
   - [Google Cloud Console](https://console.cloud.google.com/)でプロジェクト作成
   - Google Drive APIを有効化
   - OAuth 2.0認証情報をダウンロード
   - `credentials.json`として保存

4. **環境変数設定（オプション）**
```bash
# .env ファイルを作成
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json
DEFAULT_QUALITY=85
DEFAULT_MAX_WIDTH=1920
DEFAULT_MAX_HEIGHT=1080
DEFAULT_OUTPUT_DIR=converted
```

## 使用方法

### 基本的な使用方法

```bash
# 全てのHEICファイルを変換
python heic2jpg.py

# 出力ディレクトリを指定
python heic2jpg.py --output blog_images

# 画質とサイズをカスタマイズ
python heic2jpg.py --quality 90 --max-width 1600 --max-height 900

# 特定のフォルダのみ処理
python heic2jpg.py --folder-id "YOUR_GOOGLE_DRIVE_FOLDER_ID"
```

### コマンドラインオプション

| オプション | 短縮形 | デフォルト値 | 説明 |
|-----------|--------|-------------|------|
| `--output` | `-o` | `converted` | 出力ディレクトリ |
| `--quality` | `-q` | `85` | JPG画質 (1-100) |
| `--max-width` | - | `1920` | 最大幅（ピクセル） |
| `--max-height` | - | `1080` | 最大高さ（ピクセル） |
| `--folder-id` | - | なし | 処理するGoogle DriveフォルダID |
| `--credentials` | - | `credentials.json` | 認証情報ファイルパス |

### 初回認証

初回実行時はブラウザが開き、Googleアカウントでの認証が必要です。認証後、`token.json`が作成され、以降は自動認証されます。

## テスト

### テスト実行

```bash
# 全テスト実行
python test_runner.py

# ユニットテストのみ
python test_runner.py --type unit

# 統合テストのみ
python test_runner.py --type integration

# カバレッジ付き実行
python test_runner.py --type coverage

# Makefileを使用（Linux/Mac）
make test
make test-unit
make test-integration
make test-coverage
```

### 直接pytest使用

```bash
pytest                           # 全テスト
pytest -m "not integration"     # ユニットテストのみ
pytest -m integration           # 統合テストのみ
pytest --cov=heic2jpg --cov-report=html  # カバレッジ付き
```

## 開発

### プロジェクト構造

```
heic2jpg/
├── heic2jpg.py          # メインモジュール
├── requirements.txt     # 依存関係
├── test_runner.py       # テストランナー
├── pytest.ini          # pytest設定
├── Makefile            # ビルドツール（Linux/Mac）
└── tests/              # テストファイル
    ├── conftest.py     # テスト設定
    ├── test_config.py  # 設定テスト
    ├── test_converter.py  # 変換機能テスト
    ├── test_image_conversion.py  # 画像変換テスト
    └── test_integration.py  # 統合テスト
```

### 環境変数

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `GOOGLE_CREDENTIALS_FILE` | `credentials.json` | Google API認証ファイル |
| `GOOGLE_TOKEN_FILE` | `token.json` | アクセストークンファイル |
| `DEFAULT_QUALITY` | `85` | デフォルトJPG品質 |
| `DEFAULT_MAX_WIDTH` | `1920` | デフォルト最大幅 |
| `DEFAULT_MAX_HEIGHT` | `1080` | デフォルト最大高さ |
| `DEFAULT_OUTPUT_DIR` | `converted` | デフォルト出力ディレクトリ |

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## トラブルシューティング

### よくある問題

1. **認証エラー**
   - `credentials.json`が正しい場所にあることを確認
   - Google Cloud ConsoleでDrive APIが有効化されていることを確認

2. **HEIC変換エラー**
   - `pillow-heif`パッケージが正しくインストールされていることを確認
   - システムにlibheifライブラリがインストールされていることを確認

3. **メモリエラー**
   - 大きなファイルの場合、`--max-width`と`--max-height`を小さくしてください

詳細なセットアップ手順は`setup.md`を参照してください。