#!/bin/bash
# main.py常駐用systemdサービス設定スクリプト（仮想環境対応）

SERVICE_NAME="dsns-timeline-bot-main"
WORKDIR="$(cd "$(dirname "$0")/.." && pwd)"
USER="$(whoami)"

# 仮想環境のPythonパスを自動検出
if [ -f "${WORKDIR}/.venv/bin/python" ]; then
    PYTHON="${WORKDIR}/.venv/bin/python"
    echo "✅ 仮想環境を検出: $PYTHON"
elif [ -f "${WORKDIR}/venv/bin/python" ]; then
    PYTHON="${WORKDIR}/venv/bin/python"
    echo "✅ 仮想環境を検出: $PYTHON"
else
    PYTHON="/usr/bin/python3"
    echo "⚠️  仮想環境が見つかりません。グローバルPythonを使用: $PYTHON"
fi

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "=== main.py常駐用systemdサービス設定（仮想環境対応） ==="
echo "作業ディレクトリ: $WORKDIR"
echo "Pythonパス: $PYTHON"
echo "ユーザー: $USER"
echo

# サービスファイル作成
cat <<EOF | sudo tee "$SERVICE_FILE"
[Unit]
Description=DSNS Timeline Bot Main Service (常駐型)
After=network.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${WORKDIR}
ExecStart=${PYTHON} ${WORKDIR}/main.py
User=${USER}
Group=${USER}

# 環境変数設定（仮想環境対応）
Environment=PATH=${WORKDIR}/.venv/bin:${WORKDIR}/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=${WORKDIR}
Environment=VIRTUAL_ENV=${WORKDIR}/.venv

# ログ設定
StandardOutput=journal
StandardError=journal
SyslogIdentifier=dsns-bot-main

# 再起動設定
Restart=always
RestartSec=10
StartLimitInterval=300
StartLimitBurst=3

# タイムアウト設定
TimeoutStartSec=300
TimeoutStopSec=60

# セキュリティ設定
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${WORKDIR}/data ${WORKDIR}/logs
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
EOF

echo "✅ サービスファイルを作成しました: $SERVICE_FILE"
echo

# 仮想環境の依存関係確認
echo "=== 依存関係確認 ==="
if [ -f "${WORKDIR}/requirements.txt" ]; then
    echo "requirements.txtを確認中..."
    if ${PYTHON} -c "import mipa" 2>/dev/null; then
        echo "✅ mipaライブラリ: OK"
    else
        echo "❌ mipaライブラリ: 見つかりません"
        echo "仮想環境で以下を実行してください:"
        echo "  pip install -r requirements.txt"
    fi
else
    echo "⚠️  requirements.txtが見つかりません"
fi
echo

# サービス有効化・起動
echo "=== サービス有効化・起動 ==="
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service
sudo systemctl start ${SERVICE_NAME}.service

echo
echo "=== 設定完了 ==="
echo "サービス名: $SERVICE_NAME"
echo "Pythonパス: $PYTHON"
echo "状態確認: sudo systemctl status $SERVICE_NAME"
echo "ログ確認: sudo journalctl -u $SERVICE_NAME -f"
echo "停止: sudo systemctl stop $SERVICE_NAME"
echo "開始: sudo systemctl start $SERVICE_NAME"
echo "再起動: sudo systemctl restart $SERVICE_NAME"
echo "無効化: sudo systemctl disable $SERVICE_NAME" 