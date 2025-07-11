# 分散SNS関連年表bot

「分散SNS関連年表」サイトの「今日はなんの日？」機能を自動化して定期投稿するMisskeyボットです。

## 🚀 機能

- **定期投稿**: 1日2回（00:01, 12:00）の自動投稿
- **対話機能**: メンションによる日付指定、検索、ヘルプ表示
- **カテゴリ複合フィルタ**: 複数カテゴリ指定・除外条件付きフィルタリング
- **カテゴリ統計・分析**: カテゴリ分布・共起カテゴリ分析
- **年代別統計**: 年代別のイベント統計と代表的なイベント表示
- **年代＋カテゴリ複合**: 年代別＋カテゴリ複合条件での検索
- **ステータス監視**: システム状態の階層化表示
- **自動運用**: systemdによる24時間無人運用

## 📁 プロジェクト構造

```
dsns_timeline_bot/
├── main.py                 # メインアプリケーション
├── bot_client.py          # MiPA WebSocket管理
├── command_router.py      # コマンド解析・ルーティング
├── data_service.py        # データ取得・更新
├── database.py           # SQLite操作
├── config.py             # 設定管理
├── constants.py          # 定数管理
├── exceptions.py         # 例外クラス
├── dsnstypes.py          # 型定義
├── summary_manager.py    # 年代別概要管理
├── handlers/             # 応答処理群
│   ├── base_handler.py   # 共通基底クラス
│   ├── today_handler.py  # 今日のイベント処理
│   ├── date_handler.py   # 特定日付処理
│   ├── search_handler.py # 検索機能
│   ├── help_handler.py   # ヘルプ表示
│   ├── status_handler.py # ステータス監視機能
│   └── decade_handler.py # 年代別統計機能
├── tests/                # テストファイル群
├── utils/                # ユーティリティ
├── scripts/              # 運用スクリプト群
├── data/                 # データディレクトリ
│   ├── timeline.db       # SQLiteデータベース
│   └── summaries/        # 年代別概要ファイル
├── logs/                 # ログ出力ディレクトリ
├── docs/                 # ドキュメント
├── pytest.ini           # pytest設定
└── requirements.txt      # Python依存関係
```

## 🛠️ セットアップ

### 1. 環境変数設定

```bash
# .envファイルを作成
cp .env.example .env
# 必要に応じて設定値を編集
```

### 2. 依存関係インストール

```bash
# 仮想環境作成
python -m venv .venv
source .venv/bin/activate

# 依存関係インストール（テスト用も含む）
pip install -r requirements.txt
```

### 3. データベース初期化

```bash
# データベース初期化
python utils/rebuild_db.py
```

### 4. systemdサービス設定

```bash
# 自動化設定スクリプト実行
sudo bash scripts/setup_complete.sh
```

## 🚀 起動

### 手動起動

```bash
python main.py
```

### systemdサービス起動

```bash
# サービス開始
sudo systemctl start dsns-timeline-bot-main

# 状態確認
sudo systemctl status dsns-timeline-bot-main

# ログ確認
sudo journalctl -u dsns-timeline-bot-main -f
```

## 📚 ドキュメント

- [プロジェクト概要](docs/PROJECT_MAP.md)
- [開発ガイド](docs/DEVELOPMENT_GUIDE.md)
- [リファクタリング詳細](docs/REFACTORING_DOCUMENTATION.md)
- [MiPA運用ガイド](docs/mipa_guide.md)

## 🧪 テスト

```bash
# 全テスト実行
PYTHONPATH=. python -m pytest tests/

# 特定テスト実行
PYTHONPATH=. python -m pytest tests/test_refactoring_final.py

# リファクタリング統合テスト
PYTHONPATH=. python tests/test_refactoring_final.py
```

## 🔧 運用

### 日常運用

```bash
# サービス状態確認
sudo systemctl status dsns-timeline-bot-main

# ログ確認（リアルタイム）
sudo journalctl -u dsns-timeline-bot-main -f

# サービス再起動（コード修正後）
sudo systemctl restart dsns-timeline-bot-main
```

### 開発ワークフロー

```bash
# 1. コード修正
vim main.py

# 2. テスト実行
PYTHONPATH=. python -m pytest tests/

# 3. サービス再起動
sudo systemctl restart dsns-timeline-bot-main

# 4. デバッグが必要な場合
sudo systemctl stop dsns-timeline-bot-main
python main.py  # 手動実行
```

## 📊 対応コマンド

- **今日のイベント**: "今日"、"きょう"、"today"
- **特定日付**: "5月1日"、"05月01日"
- **検索**: "検索 キーワード"
- **ヘルプ**: "ヘルプ"、"使い方"
- **ステータス**: "ステータス"、"status"（基本・サーバー・ボット・年表）
- **年代別統計**: "2000年代"、"90年代 代表"、"1990年から1999年 概要"
- **カテゴリ機能**:
  - `カテゴリ dsns+tech` → dsnsかつtechカテゴリのイベント一覧
  - `カテゴリ dsns+tech-meme` → dsns・techだがmeme以外のイベント
  - `カテゴリ一覧` → 利用可能なカテゴリ一覧を表示
  - `カテゴリ統計` → 年代別・年別のカテゴリ分布
  - `カテゴリ分析 dsns` → dsnsと組み合わせられるカテゴリの統計
- **複合検索**: `検索 SNS カテゴリ dsns+tech` → キーワード＋複数カテゴリで絞り込み
- **年代＋カテゴリ**: `2000年代 カテゴリ web+tech` → 2000年代のweb・techカテゴリのイベント

## 🔍 主要カテゴリ

- **d-sns**: 分散SNS関連
- **sns**: ソーシャルネットワーク
- **web**: Web技術
- **network**: ネットワーク技術
- **web3**: Web3技術
- **hacker**: ハッカー文化・セキュリティ
- **tech**: 技術全般
- **culture**: 文化・コミュニティ
- **law**: 法律・規制
- **BBS**: 掲示板システム
- **site**: サイト・サービス
- **P2P**: P2P技術
- **crypto**: 暗号技術・暗号通貨
- **book**: 書籍・文献
- **incident**: 事件・事故
- **metaverse**: メタバース
- **meme**: ミーム・文化現象
- **pol**: 政治
- **art**: アート
- **flame**: 炎上・論争
- **tool**: ツール

## 🔗 関連リンク

- **データソース**: https://yuinoid.neocities.org/txt/my_dsns_timeline
- **参考bot**: @dsns_today_event@tanoshii.site

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。 