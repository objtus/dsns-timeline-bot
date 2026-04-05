# 接続最適化設定ガイド

## 概要

このドキュメントは、DSNS Timeline Botの接続安定性を向上させるための設定について説明します。

## 新しく追加された設定項目

### 接続監視設定

以下の環境変数を`.env`ファイルに追加することで、接続監視の動作をカスタマイズできます：

```bash
# 接続状態監視間隔（秒）
CONNECTION_HEALTH_CHECK_INTERVAL=300

# ハートビートタイムアウト（秒）
HEARTBEAT_TIMEOUT_SECONDS=600

# 最大接続失敗回数
MAX_CONNECTION_FAILURES=10

# 接続復旧時の遅延（秒）
CONNECTION_RECOVERY_DELAY=30
```

### 設定値の説明

#### CONNECTION_HEALTH_CHECK_INTERVAL
- **デフォルト**: 300秒（5分）
- **説明**: 接続状態をチェックする間隔
- **推奨値**: 300-600秒（5-10分）
- **注意**: 短すぎると負荷が高く、長すぎると問題の検出が遅れる

#### HEARTBEAT_TIMEOUT_SECONDS
- **デフォルト**: 600秒（10分）
- **説明**: ハートビートが受信されない場合のタイムアウト時間
- **推奨値**: 600-1200秒（10-20分）
- **注意**: Misskeyサーバーの設定に合わせて調整

#### MAX_CONNECTION_FAILURES
- **デフォルト**: 10回
- **説明**: 自動復旧を試行する最大回数
- **推奨値**: 5-15回
- **注意**: 少なすぎると復旧機会が減り、多すぎると無限ループの可能性

#### CONNECTION_RECOVERY_DELAY
- **デフォルト**: 30秒
- **説明**: 接続復旧試行間の遅延時間
- **推奨値**: 30-60秒
- **注意**: 短すぎるとサーバーに負荷がかかり、長すぎると復旧が遅れる

## 実装された改善点

### 1. 接続状態監視の強化
- WebSocket接続の詳細状態チェック
- ping/pongによる接続生存確認
- MiPAクライアントセッション状態の監視

### 2. 再接続処理の改善
- 既存接続の適切なクリーンアップ
- 接続復旧後の状態確認
- 失敗回数の適切な管理

### 3. 監視ロジックの最適化
- 連続失敗回数による段階的な復旧
- 不要な復旧試行の回避
- より詳細なログ出力

## 使用方法

### 1. 環境変数の設定
`.env`ファイルに必要な設定を追加：

```bash
# 既存の設定に加えて
CONNECTION_HEALTH_CHECK_INTERVAL=300
HEARTBEAT_TIMEOUT_SECONDS=600
MAX_CONNECTION_FAILURES=10
CONNECTION_RECOVERY_DELAY=30
```

### 2. サービスの再起動
設定変更後はサービスを再起動：

```bash
sudo systemctl restart dsns-timeline-bot-main.service
```

### 3. ログの監視
接続状態の監視：

```bash
# 接続監視ログの確認
journalctl -u dsns-timeline-bot-main.service | grep -E "接続|ハートビート|復旧"

# リアルタイム監視
journalctl -u dsns-timeline-bot-main.service -f
```

## トラブルシューティング

### 接続が頻繁に切れる場合
1. `HEARTBEAT_TIMEOUT_SECONDS`を長くする
2. `CONNECTION_HEALTH_CHECK_INTERVAL`を短くする
3. ネットワーク環境の確認

### 復旧が遅い場合
1. `CONNECTION_RECOVERY_DELAY`を短くする
2. `MAX_CONNECTION_FAILURES`を増やす
3. サーバーの負荷状況を確認

### ログが多すぎる場合
1. `CONNECTION_HEALTH_CHECK_INTERVAL`を長くする
2. ログレベルの調整
3. 不要な監視項目の無効化

## 今後の改善予定

1. **自動設定最適化**: 接続状況に応じた動的な設定調整
2. **メトリクス収集**: 接続品質の統計情報収集
3. **アラート機能**: 接続問題の自動通知
4. **負荷分散**: 複数サーバーへの接続分散
