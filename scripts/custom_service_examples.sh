#!/bin/bash
# systemdサービスファイルのカスタマイズ例

SERVICE_NAME="dsns-timeline-bot"
WORKDIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== systemdサービスファイルのカスタマイズ例 ==="
echo

# 例1: 仮想環境を使用する場合
echo "【例1】Python仮想環境を使用"
cat <<'EOF'
[Unit]
Description=DSNS Timeline Bot 定期データ更新・投稿
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/home/objtus/dsns_timeline_bot
ExecStart=/home/objtus/dsns_timeline_bot/.venv/bin/python /home/objtus/dsns_timeline_bot/scripts/health_check.py
User=objtus
Group=objtus

# 環境変数の設定
Environment=PATH=/home/objtus/dsns_timeline_bot/.venv/bin
Environment=PYTHONPATH=/home/objtus/dsns_timeline_bot

[Install]
WantedBy=multi-user.target
EOF
echo

# 例2: ログ管理を強化
echo "【例2】ログ管理を強化"
cat <<'EOF'
[Unit]
Description=DSNS Timeline Bot 定期データ更新・投稿
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/home/objtus/dsns_timeline_bot
ExecStart=/usr/bin/python3 /home/objtus/dsns_timeline_bot/scripts/health_check.py
User=objtus

# ログ設定
StandardOutput=journal
StandardError=journal
SyslogIdentifier=dsns-bot

# タイムアウト設定
TimeoutStartSec=300
TimeoutStopSec=60

# リスタート設定（失敗時）
Restart=no
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
echo

# 例3: セキュリティ強化
echo "【例3】セキュリティ強化"
cat <<'EOF'
[Unit]
Description=DSNS Timeline Bot 定期データ更新・投稿
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/home/objtus/dsns_timeline_bot
ExecStart=/usr/bin/python3 /home/objtus/dsns_timeline_bot/scripts/health_check.py
User=objtus

# セキュリティ設定
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/objtus/dsns_timeline_bot/data /home/objtus/dsns_timeline_bot/logs
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
EOF
echo

# 例4: 依存関係と順序制御
echo "【例4】依存関係と順序制御"
cat <<'EOF'
[Unit]
Description=DSNS Timeline Bot 定期データ更新・投稿
After=network.target postgresql.service
Requires=network.target
Wants=postgresql.service

[Service]
Type=oneshot
WorkingDirectory=/home/objtus/dsns_timeline_bot
ExecStart=/usr/bin/python3 /home/objtus/dsns_timeline_bot/scripts/health_check.py
User=objtus

# 失敗時の処理
OnFailure=notify-failure@%n.service

[Install]
WantedBy=multi-user.target
EOF
echo

# 例5: 複数実行と並列制御
echo "【例5】複数実行と並列制御"
cat <<'EOF'
[Unit]
Description=DSNS Timeline Bot 定期データ更新・投稿
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/home/objtus/dsns_timeline_bot
ExecStart=/usr/bin/python3 /home/objtus/dsns_timeline_bot/scripts/health_check.py
User=objtus

# 並列実行制御
StartLimitInterval=300
StartLimitBurst=3

# 重複実行防止
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
echo 