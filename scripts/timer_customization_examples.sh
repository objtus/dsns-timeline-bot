#!/bin/bash
# systemdタイマーファイルのカスタマイズ例

echo "=== systemdタイマーファイルのカスタマイズ例 ==="
echo

# 例1: 基本的な定期実行
echo "【例1】基本的な定期実行（1日2回）"
cat <<'EOF'
[Unit]
Description=DSNS Timeline Bot 定期実行タイマー

[Timer]
OnCalendar=*-*-* 00:01,12:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
echo

# 例2: より細かい時刻制御
echo "【例2】より細かい時刻制御"
cat <<'EOF'
[Unit]
Description=DSNS Timeline Bot 定期実行タイマー

[Timer]
# 毎日00:01と12:00に実行
OnCalendar=*-*-* 00:01:00
OnCalendar=*-*-* 12:00:00
# 月曜日のみ追加実行
OnCalendar=Mon *-*-* 09:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF
echo

# 例3: 間隔ベースの実行
echo "【例3】間隔ベースの実行"
cat <<'EOF'
[Unit]
Description=DSNS Timeline Bot 定期実行タイマー

[Timer]
# 6時間ごとに実行
OnBootSec=1min
OnUnitActiveSec=6h
Persistent=true

[Install]
WantedBy=timers.target
EOF
echo

# 例4: 複雑なスケジュール
echo "【例4】複雑なスケジュール"
cat <<'EOF'
[Unit]
Description=DSNS Timeline Bot 定期実行タイマー

[Timer]
# 平日のみ実行
OnCalendar=Mon..Fri *-*-* 00:01:00
OnCalendar=Mon..Fri *-*-* 12:00:00
# 土日は1回のみ
OnCalendar=Sat,Sun *-*-* 10:00:00
Persistent=true
# ランダム遅延（0-300秒）
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF
echo

# 例5: 失敗時の再実行
echo "【例5】失敗時の再実行"
cat <<'EOF'
[Unit]
Description=DSNS Timeline Bot 定期実行タイマー

[Timer]
OnCalendar=*-*-* 00:01,12:00
Persistent=true
# 失敗時の再実行設定
OnFailure=notify-failure@%n.service

[Install]
WantedBy=timers.target
EOF
echo

# 例6: 条件付き実行
echo "【例6】条件付き実行（他のサービスが起動している場合のみ）"
cat <<'EOF'
[Unit]
Description=DSNS Timeline Bot 定期実行タイマー
Requires=network-online.target
After=network-online.target

[Timer]
OnCalendar=*-*-* 00:01,12:00
Persistent=true
# ネットワークが利用可能な場合のみ実行
Unit=dsns-timeline-bot.service

[Install]
WantedBy=timers.target
EOF
echo

# 例7: 月次・週次実行
echo "【例7】月次・週次実行"
cat <<'EOF'
[Unit]
Description=DSNS Timeline Bot 定期実行タイマー

[Timer]
# 毎日00:01と12:00
OnCalendar=*-*-* 00:01:00
OnCalendar=*-*-* 12:00:00
# 毎週月曜日の09:00にデータ更新
OnCalendar=Mon *-*-* 09:00:00
# 毎月1日の03:00に完全バックアップ
OnCalendar=*-*-01 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
echo

# 例8: 開発・テスト用
echo "【例8】開発・テスト用（頻繁な実行）"
cat <<'EOF'
[Unit]
Description=DSNS Timeline Bot 開発用タイマー

[Timer]
# 5分ごとに実行（テスト用）
OnBootSec=1min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
EOF
echo 