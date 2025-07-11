"""
アラート機能ユーティリティ

異常検知、アラート送信、通知管理などの
アラート機能を提供します。
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """アラートの重要度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    """アラート情報"""
    alert_id: str
    severity: AlertSeverity
    title: str
    message: str
    component: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class AlertManager:
    """アラート管理クラス"""
    
    def __init__(self):
        """アラートマネージャーの初期化"""
        self.alerts: Dict[str, Alert] = {}
        self.notifiers: List[Callable] = []
        self.alert_history: List[Alert] = []
        self.max_history = 1000
        self.rate_limit = {}  # レート制限管理
    
    def add_notifier(self, notifier: Callable) -> None:
        """
        通知機能を追加
        
        Args:
            notifier: 通知関数（Alertオブジェクトを受け取る）
        """
        self.notifiers.append(notifier)
    
    async def send_alert(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        component: str,
        metadata: Optional[Dict[str, Any]] = None,
        alert_id: Optional[str] = None
    ) -> str:
        """
        アラートを送信
        
        Args:
            severity: 重要度
            title: アラートタイトル
            message: アラートメッセージ
            component: コンポーネント名
            metadata: 追加メタデータ
            alert_id: アラートID（自動生成される）
            
        Returns:
            str: アラートID
        """
        # レート制限チェック
        if not self._check_rate_limit(component, severity):
            logger.debug(f"レート制限によりアラートをスキップ: {component} - {severity}")
            return ""
        
        # アラートID生成
        if alert_id is None:
            alert_id = f"{component}_{severity.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # アラート作成
        alert = Alert(
            alert_id=alert_id,
            severity=severity,
            title=title,
            message=message,
            component=component,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # アラートを保存
        self.alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # 履歴サイズ制限
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)
        
        # 通知送信
        await self._send_notifications(alert)
        
        logger.info(f"アラート送信: {alert_id} - {severity.value} - {title}")
        return alert_id
    
    def resolve_alert(self, alert_id: str) -> bool:
        """
        アラートを解決済みにマーク
        
        Args:
            alert_id: アラートID
            
        Returns:
            bool: 解決成功時True
        """
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            logger.info(f"アラート解決: {alert_id}")
            return True
        return False
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """
        アクティブなアラートを取得
        
        Args:
            severity: 重要度フィルタ
            
        Returns:
            List[Alert]: アクティブなアラートリスト
        """
        active_alerts = [
            alert for alert in self.alerts.values()
            if not alert.resolved
        ]
        
        if severity:
            active_alerts = [
                alert for alert in active_alerts
                if alert.severity == severity
            ]
        
        return sorted(active_alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """
        アラート統計を取得
        
        Returns:
            Dict: アラート統計
        """
        total_alerts = len(self.alerts)
        active_alerts = len([a for a in self.alerts.values() if not a.resolved])
        resolved_alerts = total_alerts - active_alerts
        
        severity_counts = {}
        for severity in AlertSeverity:
            severity_counts[severity.value] = len([
                a for a in self.alerts.values()
                if a.severity == severity and not a.resolved
            ])
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'resolved_alerts': resolved_alerts,
            'severity_distribution': severity_counts,
            'history_size': len(self.alert_history),
        }
    
    def _check_rate_limit(self, component: str, severity: AlertSeverity) -> bool:
        """
        レート制限チェック
        
        Args:
            component: コンポーネント名
            severity: 重要度
            
        Returns:
            bool: 送信可能時True
        """
        key = f"{component}_{severity.value}"
        now = datetime.now()
        
        if key not in self.rate_limit:
            self.rate_limit[key] = []
        
        # 1時間以内のアラートをカウント
        recent_alerts = [
            time for time in self.rate_limit[key]
            if now - time < timedelta(hours=1)
        ]
        
        # 重要度に応じた制限
        limits = {
            AlertSeverity.INFO: 10,
            AlertSeverity.WARNING: 5,
            AlertSeverity.ERROR: 3,
            AlertSeverity.CRITICAL: 1,
        }
        
        if len(recent_alerts) >= limits[severity]:
            return False
        
        # 現在時刻を追加
        self.rate_limit[key].append(now)
        
        # 古いエントリを削除
        self.rate_limit[key] = [
            time for time in self.rate_limit[key]
            if now - time < timedelta(hours=1)
        ]
        
        return True
    
    async def _send_notifications(self, alert: Alert) -> None:
        """
        通知を送信
        
        Args:
            alert: 送信するアラート
        """
        for notifier in self.notifiers:
            try:
                await notifier(alert)
            except Exception as e:
                logger.error(f"通知送信エラー: {e}")

class DiscordNotifier:
    """Discord通知機能"""
    
    def __init__(self, webhook_url: str):
        """
        Discord通知機能の初期化
        
        Args:
            webhook_url: Discord Webhook URL
        """
        self.webhook_url = webhook_url
    
    async def __call__(self, alert: Alert) -> None:
        """
        アラートをDiscordに送信
        
        Args:
            alert: 送信するアラート
        """
        try:
            import aiohttp
            
            # 重要度に応じた色
            colors = {
                AlertSeverity.INFO: 0x00ff00,      # 緑
                AlertSeverity.WARNING: 0xffff00,   # 黄
                AlertSeverity.ERROR: 0xff8000,     # オレンジ
                AlertSeverity.CRITICAL: 0xff0000,  # 赤
            }
            
            embed = {
                "title": alert.title,
                "description": alert.message,
                "color": colors[alert.severity],
                "fields": [
                    {
                        "name": "コンポーネント",
                        "value": alert.component,
                        "inline": True
                    },
                    {
                        "name": "重要度",
                        "value": alert.severity.value.upper(),
                        "inline": True
                    },
                    {
                        "name": "時刻",
                        "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "inline": True
                    }
                ],
                "timestamp": alert.timestamp.isoformat()
            }
            
            if alert.metadata:
                metadata_str = "\n".join([f"{k}: {v}" for k, v in alert.metadata.items()])
                embed["fields"].append({
                    "name": "詳細情報",
                    "value": metadata_str[:1024],  # Discord制限
                    "inline": False
                })
            
            payload = {
                "embeds": [embed]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status != 204:
                        logger.error(f"Discord通知エラー: {response.status}")
                        
        except Exception as e:
            logger.error(f"Discord通知送信エラー: {e}")

class EmailNotifier:
    """メール通知機能"""
    
    def __init__(self, smtp_config: Dict[str, str]):
        """
        メール通知機能の初期化
        
        Args:
            smtp_config: SMTP設定
        """
        self.smtp_config = smtp_config
    
    async def __call__(self, alert: Alert) -> None:
        """
        アラートをメールで送信
        
        Args:
            alert: 送信するアラート
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # メール作成
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['from']
            msg['To'] = self.smtp_config['to']
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            # 本文作成
            body = f"""
アラート詳細:
- タイトル: {alert.title}
- メッセージ: {alert.message}
- コンポーネント: {alert.component}
- 重要度: {alert.severity.value}
- 時刻: {alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")}

詳細情報:
{alert.metadata or "なし"}
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # メール送信
            with smtplib.SMTP(self.smtp_config['host'], int(self.smtp_config['port'])) as server:
                if self.smtp_config.get('use_tls'):
                    server.starttls()
                
                if 'username' in self.smtp_config:
                    server.login(self.smtp_config['username'], self.smtp_config['password'])
                
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"メール通知送信エラー: {e}")

class LogNotifier:
    """ログ通知機能"""
    
    def __init__(self, log_level: str = "WARNING"):
        """
        ログ通知機能の初期化
        
        Args:
            log_level: ログレベル
        """
        self.log_level = getattr(logging, log_level.upper(), logging.WARNING)
    
    async def __call__(self, alert: Alert) -> None:
        """
        アラートをログに出力
        
        Args:
            alert: 出力するアラート
        """
        log_message = f"ALERT [{alert.severity.value.upper()}] {alert.component}: {alert.title} - {alert.message}"
        
        if self.log_level == logging.CRITICAL:
            logger.critical(log_message)
        elif self.log_level == logging.ERROR:
            logger.error(log_message)
        elif self.log_level == logging.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)

# グローバルインスタンス
alert_manager = AlertManager()

# デフォルト通知機能を追加
alert_manager.add_notifier(LogNotifier()) 