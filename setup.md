# HEIC to JPG Converter - セットアップガイド

## 必要な準備

### 1. Google Drive API の設定
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成または既存プロジェクトを選択
3. Google Drive API を有効化
4. 認証情報を作成（OAuth 2.0 クライアント ID）
5. デスクトップアプリケーション用の認証情報をダウンロード
6. ダウンロードしたファイルを`credentials.json`として保存

### 2. 環境設定
```bash
# 依存関係をインストール
pip install -r requirements.txt

# 環境変数ファイルをコピー（必要に応じて）
copy .env.example .env
```

## 使用方法

### 基本的な使用方法
```bash
# 全てのHEICファイルを変換
python heic2jpg.py

# 出力ディレクトリを指定
python heic2jpg.py --output blog_images

# 画質とサイズを指定
python heic2jpg.py --quality 90 --max-width 1600 --max-height 900

# 特定のフォルダのみ処理
python heic2jpg.py --folder-id "YOUR_FOLDER_ID"
```

### オプション
- `--output, -o`: 出力ディレクトリ（デフォルト: converted）
- `--quality, -q`: JPG画質 1-100（デフォルト: 85）
- `--max-width`: 最大幅（デフォルト: 1920）
- `--max-height`: 最大高さ（デフォルト: 1080）
- `--folder-id`: 処理するGoogle Driveフォルダの ID
- `--credentials`: 認証情報ファイルのパス

## 初回実行時の認証
初回実行時にブラウザが開き、Google アカウントでの認証が必要です。
認証後、`token.json`ファイルが作成され、次回からは自動的に認証されます。

## テストの実行

### テスト環境の準備
```bash
# テスト用依存関係をインストール（requirements.txtに含まれています）
pip install pytest pytest-mock pytest-cov
```

### テストの実行方法

#### Windows環境
```bash
# 全てのテストを実行
python test_runner.py

# ユニットテストのみ実行
python test_runner.py --type unit

# 統合テストのみ実行
python test_runner.py --type integration

# カバレッジ付きでテスト実行
python test_runner.py --type coverage

# 詳細出力
python test_runner.py --verbose
```

#### Linux/Mac環境（Makefileを使用）
```bash
# 全てのテストを実行
make test

# ユニットテストのみ実行
make test-unit

# 統合テストのみ実行
make test-integration

# カバレッジ付きでテスト実行
make test-coverage

# テスト後のクリーンアップ
make clean
```

#### 直接pytestを使用
```bash
# 全てのテストを実行
pytest

# ユニットテストのみ実行
pytest -m "not integration"

# 統合テストのみ実行
pytest -m integration

# カバレッジ付きでテスト実行
pytest --cov=heic2jpg --cov-report=html
```

### テストの種類
- **ユニットテスト**: 個別の関数やクラスの動作をテスト
- **統合テスト**: Google Drive APIとの連携をモックでテスト
- **画像変換テスト**: HEIC→JPG変換機能の詳細テスト