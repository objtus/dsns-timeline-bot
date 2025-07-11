# 分散SNS関連年表bot 運用・開発ガイドライン

## 概要
このガイドラインは、systemd自動化設定後の分散SNS関連年表botの運用・開発方法を説明します。

## システム構成

### 自動化コンポーネント
- **dsns-timeline-bot-main.service**: main.py常駐サービス
- **dsns-bot-data-update.timer**: データ更新タイマー（毎日03:00）
- **dsns-bot-backup.timer**: バックアップタイマー（毎日04:00）

### 仮想環境
- **.venv/**: Python仮想環境（systemdサービスで使用）
- **venv/**: 古い仮想環境（削除可能）

## 日常運用

### サービス状態確認
```bash
# メインサービスの状態確認
sudo systemctl status dsns-timeline-bot-main

# タイマーの状態確認
sudo systemctl list-timers dsns-bot-*

# 全サービスの状態確認
sudo systemctl status dsns-timeline-bot-main dsns-bot-data-update.service dsns-bot-backup.service
```

### ログ監視
```bash
# リアルタイムログ確認
sudo journalctl -u dsns-timeline-bot-main -f

# 最新100行のログ確認
sudo journalctl -u dsns-timeline-bot-main -n 100

# エラーログのみ確認
sudo journalctl -u dsns-timeline-bot-main -p err

# 今日のログ確認
sudo journalctl -u dsns-timeline-bot-main --since today

# 特定時間のログ確認
sudo journalctl -u dsns-timeline-bot-main --since "2025-07-04 10:00:00"
```

### サービス制御
```bash
# サービス開始
sudo systemctl start dsns-timeline-bot-main

# サービス停止
sudo systemctl stop dsns-timeline-bot-main

# サービス再起動
sudo systemctl restart dsns-timeline-bot-main

# サービス有効化（自動起動設定）
sudo systemctl enable dsns-timeline-bot-main

# サービス無効化（自動起動解除）
sudo systemctl disable dsns-timeline-bot-main
```

## 開発ワークフロー

### 1. 通常のコード修正
```bash
# 1. コードを修正
vim main.py  # または任意のエディタ

# 2. サービスを再起動（新しいコードで自動起動）
sudo systemctl restart dsns-timeline-bot-main

# 3. 状態確認
sudo systemctl status dsns-timeline-bot-main

# 4. ログ確認（必要に応じて）
sudo journalctl -u dsns-timeline-bot-main -n 20
```

### 2. デバッグが必要な場合
```bash
# 1. サービスを停止
sudo systemctl stop dsns-timeline-bot-main

# 2. 手動で実行（ログを直接確認）
cd /home/objtus/dsns_timeline_bot
source .venv/bin/activate
python main.py

# 3. デバッグ完了後、サービスを再開
sudo systemctl start dsns-timeline-bot-main
```

### 3. 依存関係の更新
```bash
# 1. サービスを停止
sudo systemctl stop dsns-timeline-bot-main

# 2. 仮想環境で依存関係を更新
cd /home/objtus/dsns_timeline_bot
source .venv/bin/activate
pip install -r requirements.txt

# 3. サービスを再開
sudo systemctl start dsns-timeline-bot-main
```

### 4. 環境変数の変更
```bash
# 1. .envファイルを編集
vim .env

# 2. サービスを再起動（環境変数を再読み込み）
sudo systemctl restart dsns-timeline-bot-main
```

## トラブルシューティング

### サービスが起動しない場合
```bash
# 1. 詳細なエラー情報を確認
sudo systemctl status dsns-timeline-bot-main -l

# 2. ログを詳細確認
sudo journalctl -u dsns-timeline-bot-main -n 50

# 3. 手動で起動テスト
cd /home/objtus/dsns_timeline_bot
source .venv/bin/activate
python main.py
```

### 仮想環境の問題
```bash
# 仮想環境のPythonパスを確認
ls -la .venv/bin/python

# 仮想環境を再作成（必要に応じて）
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 権限の問題
```bash
# ファイルの権限を確認
ls -la /home/objtus/dsns_timeline_bot/

# 必要に応じて権限を修正
chmod +x scripts/start_bot.sh
```

## 定期メンテナンス

### データベースバックアップ確認
```bash
# バックアップファイルの確認
ls -la data/backups/

# バックアップタイマーの手動実行
sudo systemctl start dsns-bot-backup.service
```

### データ更新確認
```bash
# データ更新タイマーの手動実行
sudo systemctl start dsns-bot-data-update.service

# 更新ログの確認
sudo journalctl -u dsns-bot-data-update.service -n 50
```

### ログローテーション
```bash
# 古いログファイルの確認
ls -la logs/

# 必要に応じてログファイルを削除
rm logs/old_log_file.log
```

## セキュリティ

### サービス設定の確認
```bash
# systemdサービスの設定確認
sudo systemctl cat dsns-timeline-bot-main

# セキュリティ設定の確認
sudo systemctl show dsns-timeline-bot-main | grep -E "(Protect|Private|NoNewPrivileges)"
```

### 環境変数の保護
```bash
# .envファイルの権限確認
ls -la .env

# 必要に応じて権限を制限
chmod 600 .env
```

## パフォーマンス監視

### リソース使用量確認
```bash
# プロセスの確認
ps aux | grep main.py

# メモリ使用量確認
free -h

# ディスク使用量確認
df -h
```

### データベースサイズ確認
```bash
# SQLiteデータベースのサイズ確認
ls -lh data/timeline.db

# データベースの統計情報確認
sqlite3 data/timeline.db "SELECT COUNT(*) FROM timeline_events;"
```

## 緊急時対応

### サービスが応答しない場合
```bash
# 1. 強制停止
sudo systemctl stop dsns-timeline-bot-main

# 2. プロセスを確認
ps aux | grep main.py

# 3. 必要に応じて強制終了
sudo pkill -f main.py

# 4. サービスを再開
sudo systemctl start dsns-timeline-bot-main
```

### システム再起動後の確認
```bash
# 1. サービスの状態確認
sudo systemctl status dsns-timeline-bot-main

# 2. 自動起動が有効になっているか確認
sudo systemctl is-enabled dsns-timeline-bot-main

# 3. 必要に応じて手動開始
sudo systemctl start dsns-timeline-bot-main
```

## 開発環境のセットアップ

### 新規開発者の環境構築
```bash
# 1. リポジトリをクローン
git clone <repository_url>
cd dsns_timeline_bot

# 2. 仮想環境を作成
python3 -m venv .venv
source .venv/bin/activate

# 3. 依存関係をインストール
pip install -r requirements.txt

# 4. 環境変数を設定
cp .env.example .env
vim .env  # 必要な設定値を入力

# 5. データベースを初期化
python database.py

# 6. テスト実行
python test_components.py
```

### 開発用の手動実行
```bash
# 開発中は手動で実行（デバッグしやすい）
source .venv/bin/activate
python main.py

# または、特定のテストを実行
python test_scheduled_posting.py
```

## ベストプラクティス

### コード修正時
1. **小さな変更**: `restart`で再起動
2. **大きな変更**: `stop`して手動実行でテスト
3. **依存関係変更**: 仮想環境を更新してから再起動

### ログ管理
1. **定期的なログ確認**: エラーがないかチェック
2. **ログローテーション**: 古いログファイルの削除
3. **ログ分析**: パフォーマンス問題の早期発見

### バックアップ
1. **定期的なバックアップ確認**: 自動バックアップの動作確認
2. **手動バックアップ**: 重要な変更前の手動バックアップ
3. **バックアップテスト**: 復元テストの実施

### セキュリティ
1. **環境変数の保護**: .envファイルの権限制限
2. **定期的な更新**: 依存関係のセキュリティ更新
3. **アクセス制御**: 不要なアクセスの制限

## 参考資料

- **PROJECT_MAP.md**: プロジェクト全体の概要
- **mipa_guide.md**: MiPAライブラリの詳細ガイド
- **scripts/**: 各種設定スクリプト
- **systemd設定ファイル**: /etc/systemd/system/dsns-*

---

このガイドラインに従うことで、安全で効率的な運用・開発が可能になります。 