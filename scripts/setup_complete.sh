#!/bin/bash
# DSNS Timeline Bot 完全自動化設定スクリプト

echo "=== DSNS Timeline Bot 完全自動化設定 ==="
echo "このスクリプトは以下を設定します："
echo "1. main.py常駐サービス（メンション応答 + 定期投稿）"
echo "2. データ更新・バックアップタイマー（オプション）"
echo

# 設定確認
read -p "続行しますか？ (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "設定をキャンセルしました"
    exit 0
fi

echo
echo "=== 1. main.py常駐サービス設定 ==="
chmod +x scripts/setup_main_service.sh
./scripts/setup_main_service.sh

echo
echo "=== 2. データ更新・バックアップタイマー設定（オプション） ==="
read -p "データ更新・バックアップタイマーも設定しますか？ (y/N): " setup_timer

if [[ $setup_timer =~ ^[Yy]$ ]]; then
    echo "データ更新・バックアップタイマーを設定します..."
    
    # データ更新タイマー
    cat <<EOF | sudo tee /etc/systemd/system/dsns-bot-data-update.timer
[Unit]
Description=DSNS Bot Data Update Timer
Requires=network-online.target
After=network-online.target

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
RandomizedDelaySec=1800

[Install]
WantedBy=timers.target
EOF

    cat <<EOF | sudo tee /etc/systemd/system/dsns-bot-data-update.service
[Unit]
Description=DSNS Bot Data Update Service
After=network.target

[Service]
Type=oneshot
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 -c "
import asyncio
from data_service import TimelineDataService
from config import Config
from database import TimelineDatabase

async def update_data():
    try:
        config = Config()
        database = TimelineDatabase(config.database_path)
        data_service = TimelineDataService(config, database)
        await data_service.__aenter__()
        await data_service.update_timeline_data()
        await data_service.__aexit__(None, None, None)
        print('Data update completed successfully')
    except Exception as e:
        print(f'Data update failed: {e}')
        exit(1)

asyncio.run(update_data())
"
User=$(whoami)

[Install]
WantedBy=multi-user.target
EOF

    # バックアップタイマー
    cat <<EOF | sudo tee /etc/systemd/system/dsns-bot-backup.timer
[Unit]
Description=DSNS Bot Backup Timer

[Timer]
OnCalendar=*-*-* 04:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

    cat <<EOF | sudo tee /etc/systemd/system/dsns-bot-backup.service
[Unit]
Description=DSNS Bot Backup Service
After=network.target

[Service]
Type=oneshot
WorkingDirectory=$(pwd)
ExecStart=/bin/bash -c '
BACKUP_DIR="/home/$(whoami)/backups/dsns-bot"
mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y%m%d_%H%M%S)
cp data/timeline.db "$BACKUP_DIR/timeline_$DATE.db"
find "$BACKUP_DIR" -name "timeline_*.db" -mtime +7 -delete
echo "Backup completed: timeline_$DATE.db"
'
User=$(whoami)

[Install]
WantedBy=multi-user.target
EOF

    # タイマー有効化
    sudo systemctl daemon-reload
    sudo systemctl enable dsns-bot-data-update.timer
    sudo systemctl enable dsns-bot-backup.timer
    sudo systemctl start dsns-bot-data-update.timer
    sudo systemctl start dsns-bot-backup.timer
    
    echo "✅ データ更新・バックアップタイマーを設定しました"
else
    echo "データ更新・バックアップタイマーの設定をスキップしました"
fi

echo
echo "=== 設定完了 ==="
echo
echo "📋 設定されたサービス一覧："
echo "1. dsns-timeline-bot-main.service (main.py常駐)"
echo "   - メンション応答"
echo "   - 定期投稿（00:01, 12:00）"
echo "   - 自動再起動対応"
echo

if [[ $setup_timer =~ ^[Yy]$ ]]; then
    echo "2. dsns-bot-data-update.timer (データ更新)"
    echo "   - 毎日03:00にデータ更新"
    echo "3. dsns-bot-backup.timer (バックアップ)"
    echo "   - 毎日04:00にDBバックアップ"
    echo
fi

echo "🔧 管理コマンド："
echo "状態確認: sudo systemctl status dsns-timeline-bot-main"
echo "ログ確認: sudo journalctl -u dsns-timeline-bot-main -f"
echo "再起動: sudo systemctl restart dsns-timeline-bot-main"
echo "停止: sudo systemctl stop dsns-timeline-bot-main"
echo "開始: sudo systemctl start dsns-timeline-bot-main"
echo

if [[ $setup_timer =~ ^[Yy]$ ]]; then
    echo "📅 タイマー状態確認："
    echo "sudo systemctl list-timers dsns-bot-*"
    echo
fi

echo "🎉 設定完了！Raspberry Pi再起動後も自動で動作します。" 