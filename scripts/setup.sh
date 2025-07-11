#!/bin/bash
# 分散SNS関連年表bot systemdサービス・タイマー自動生成スクリプト

SERVICE_NAME="dsns-timeline-bot"
WORKDIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="/usr/bin/python3"
USER="$(whoami)"

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
TIMER_FILE="/etc/systemd/system/${SERVICE_NAME}.timer"

cat <<EOF | sudo tee "$SERVICE_FILE"
[Unit]
Description=DSNS Timeline Bot 定期データ更新・投稿
After=network.target

[Service]
Type=oneshot
WorkingDirectory=${WORKDIR}
ExecStart=${PYTHON} ${WORKDIR}/scripts/health_check.py
User=${USER}

[Install]
WantedBy=multi-user.target
EOF

cat <<EOF | sudo tee "$TIMER_FILE"
[Unit]
Description=DSNS Timeline Bot 定期実行タイマー

[Timer]
OnCalendar=*-*-* 00:01,12:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "systemdサービス・タイマーを作成しました:"
echo "  $SERVICE_FILE"
echo "  $TIMER_FILE"
echo "有効化・起動するには以下を実行してください:"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable --now ${SERVICE_NAME}.timer"
