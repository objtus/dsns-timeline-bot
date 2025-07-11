#!/bin/bash
# 高度なsystemd設定例

echo "=== 高度なsystemd設定例 ==="
echo

# 例1: 失敗通知サービス
echo "【例1】失敗通知サービス"
cat <<'EOF'
# /etc/systemd/system/notify-failure@.service
[Unit]
Description=Failure notification for %i
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"text":"DSNS Bot service %i failed!"}' \
  https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
User=nobody

[Install]
WantedBy=multi-user.target
EOF
echo

# 例2: ヘルスチェックサービス
echo "【例2】ヘルスチェックサービス"
cat <<'EOF'
# /etc/systemd/system/dsns-bot-health.service
[Unit]
Description=DSNS Bot Health Check
After=dsns-timeline-bot.service

[Service]
Type=oneshot
WorkingDirectory=/home/objtus/dsns_timeline_bot
ExecStart=/usr/bin/python3 -c "
import sqlite3
import sys
try:
    conn = sqlite3.connect('data/timeline.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM timeline_events')
    count = cursor.fetchone()[0]
    print(f'Database has {count} events')
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f'Health check failed: {e}')
    sys.exit(1)
"
User=objtus

[Install]
WantedBy=multi-user.target
EOF
echo

# 例3: ログローテーション設定
echo "【例3】ログローテーション設定"
cat <<'EOF'
# /etc/systemd/system/dsns-bot-logrotate.service
[Unit]
Description=DSNS Bot Log Rotation
After=network.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c '
cd /home/objtus/dsns_timeline_bot/logs
if [ -f dsns_bot.log ]; then
    mv dsns_bot.log dsns_bot.log.$(date +%Y%m%d)
    gzip dsns_bot.log.$(date +%Y%m%d)
fi
# 30日以上古いログを削除
find . -name "dsns_bot.log.*.gz" -mtime +30 -delete
'
User=objtus

[Install]
WantedBy=multi-user.target
EOF
echo

# 例4: バックアップサービス
echo "【例4】バックアップサービス"
cat <<'EOF'
# /etc/systemd/system/dsns-bot-backup.service
[Unit]
Description=DSNS Bot Database Backup
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/home/objtus/dsns_timeline_bot
ExecStart=/bin/bash -c '
BACKUP_DIR="/home/objtus/backups/dsns-bot"
mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y%m%d_%H%M%S)
cp data/timeline.db "$BACKUP_DIR/timeline_$DATE.db"
# 7日以上古いバックアップを削除
find "$BACKUP_DIR" -name "timeline_*.db" -mtime +7 -delete
echo "Backup completed: timeline_$DATE.db"
'
User=objtus

[Install]
WantedBy=multi-user.target
EOF
echo

# 例5: 複合タイマー（複数サービス）
echo "【例5】複合タイマー（複数サービス）"
cat <<'EOF'
# /etc/systemd/system/dsns-bot-daily.timer
[Unit]
Description=DSNS Bot Daily Tasks Timer

[Timer]
OnCalendar=*-*-* 00:01:00
Persistent=true

[Install]
WantedBy=timers.target

# /etc/systemd/system/dsns-bot-daily.service
[Unit]
Description=DSNS Bot Daily Tasks
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/home/objtus/dsns_timeline_bot
ExecStart=/usr/bin/python3 scripts/health_check.py
ExecStart=/usr/bin/systemctl start dsns-bot-health.service
ExecStart=/usr/bin/systemctl start dsns-bot-logrotate.service
User=objtus

[Install]
WantedBy=multi-user.target
EOF
echo

# 例6: 条件付き実行（ネットワーク確認）
echo "【例6】条件付き実行（ネットワーク確認）"
cat <<'EOF'
# /etc/systemd/system/dsns-bot-network-check.service
[Unit]
Description=DSNS Bot Network Check
After=network-online.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c '
if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
    echo "Network is up"
    systemctl start dsns-timeline-bot.service
else
    echo "Network is down"
    exit 1
fi
'
User=objtus

[Install]
WantedBy=multi-user.target
EOF
echo

# 例7: 監視・メトリクス収集
echo "【例7】監視・メトリクス収集"
cat <<'EOF'
# /etc/systemd/system/dsns-bot-metrics.service
[Unit]
Description=DSNS Bot Metrics Collection
After=dsns-timeline-bot.service

[Service]
Type=oneshot
WorkingDirectory=/home/objtus/dsns_timeline_bot
ExecStart=/usr/bin/python3 -c "
import sqlite3
import json
import time
from datetime import datetime

try:
    conn = sqlite3.connect('data/timeline.db')
    cursor = conn.cursor()
    
    # データベース統計
    cursor.execute('SELECT COUNT(*) FROM timeline_events')
    event_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM update_history')
    update_count = cursor.fetchone()[0]
    
    # メトリクスをJSONファイルに保存
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'event_count': event_count,
        'update_count': update_count,
        'service_status': 'running'
    }
    
    with open('logs/metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    conn.close()
    print('Metrics collected successfully')
    
except Exception as e:
    print(f'Metrics collection failed: {e}')
    exit(1)
"
User=objtus

[Install]
WantedBy=multi-user.target
EOF
echo

# 例8: 開発・本番環境切り替え
echo "【例8】開発・本番環境切り替え"
cat <<'EOF'
# 開発環境用
# /etc/systemd/system/dsns-timeline-bot-dev.service
[Unit]
Description=DSNS Timeline Bot (Development)
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/home/objtus/dsns_timeline_bot
ExecStart=/home/objtus/dsns_timeline_bot/.venv/bin/python scripts/health_check.py
User=objtus
Environment=DEBUG_MODE=true
Environment=DRY_RUN_MODE=true

[Install]
WantedBy=multi-user.target

# 本番環境用
# /etc/systemd/system/dsns-timeline-bot-prod.service
[Unit]
Description=DSNS Timeline Bot (Production)
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/home/objtus/dsns_timeline_bot
ExecStart=/home/objtus/dsns_timeline_bot/.venv/bin/python scripts/health_check.py
User=objtus
Environment=DEBUG_MODE=false
Environment=DRY_RUN_MODE=false

[Install]
WantedBy=multi-user.target
EOF
echo 