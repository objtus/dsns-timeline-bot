"""
ステータス監視機能専用ハンドラー
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from config import Config
from database import TimelineDatabase as Database
from data_service import TimelineDataService as DataService
from bot_client import BotClient
from dsnstypes import StatusInfo, StatusSystemInfo, StatusDatabaseInfo
from exceptions import StatusHandlerError, DatabaseError, ConfigError
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)

class StatusHandler(BaseHandler):
    """ステータス監視機能専用ハンドラー"""
    
    def __init__(self, config: Config, database: Database, data_service: DataService, bot_client: Optional[BotClient] = None):
        """
        ステータスハンドラーの初期化
        
        Args:
            config: 設定オブジェクト
            database: データベースオブジェクト
            data_service: データサービスオブジェクト
            bot_client: ボットクライアントオブジェクト
            
        Raises:
            StatusHandlerError: 初期化エラー時
        """
        try:
            super().__init__(config, database, data_service, bot_client)
            logger.info("StatusHandler初期化完了")
        except Exception as e:
            logger.error(f"StatusHandler初期化エラー: {e}")
            raise StatusHandlerError(f"StatusHandler初期化失敗: {e}")
    
    async def handle(self, note, command) -> str:
        """
        ステータス監視要求を処理
        
        Args:
            note: Misskeyのnoteオブジェクト
            command: パースされたコマンド辞書（type='status'等）
            
        Returns:
            str: ステータス情報メッセージ
            
        Raises:
            StatusHandlerError: 処理エラー時
        """
        try:
            logger.info("ステータス監視処理開始")
            
            # サブコマンドの判定
            sub_command = command.get('sub_command')
            
            if sub_command == 'server':
                return await self._handle_server_status()
            elif sub_command == 'bot':
                return await self._handle_bot_status()
            elif sub_command == 'timeline':
                return await self._handle_timeline_status()
            else:
                # デフォルト: 基本ステータス
                return await self._handle_basic_status()
                
        except Exception as e:
            logger.error(f"ステータス監視処理エラー: {e}")
            raise StatusHandlerError(f"ステータス監視処理失敗: {e}")
    
    async def _handle_basic_status(self) -> str:
        """基本ステータス表示"""
        try:
            status = self._get_bot_status()
            
            status_message = f"""🤖 分散SNS年表bot ステータス

🔗 接続状態: {'✅ 接続中' if status.get('is_connected', False) else '❌ 切断中'}
⏰ 稼働時間: {status.get('uptime', 'N/A')}
📊 処理メッセージ数: {status.get('message_count', 0):,}件
❌ エラー数: {status.get('error_count', 0)}件
📈 エラー率: {status.get('error_rate', 0.0):.1%}
📚 データベース: {status.get('database_events', 0):,}件のイベント
⚡ 平均応答時間: {status.get('avg_response_time', 'N/A')}
💾 メモリ使用量: {status.get('memory_usage', 'N/A')}
📊 処理成功率: {status.get('success_rate', 0.0):.1f}%

設定: {'🔧 ドライラン' if status.get('dry_run_mode', False) else '🚀 本番'}モード

💡 詳細情報: 「ステータス サーバー」「ステータス ボット」「ステータス 年表」で個別詳細を確認できます"""
            
            logger.info("基本ステータス情報生成完了")
            return status_message
            
        except Exception as e:
            logger.error(f"基本ステータス処理エラー: {e}")
            raise StatusHandlerError(f"基本ステータス処理失敗: {e}")
    
    async def _handle_server_status(self) -> str:
        """サーバー詳細ステータス表示"""
        try:
            status = self._get_bot_status()
            
            server_message = f"""🖥️ サーバー詳細ステータス

💻 システム情報:
  • 稼働時間: {status.get('uptime', 'N/A')}
  • メモリ使用量: {status.get('memory_usage', 'N/A')}
  • CPU使用率: {status.get('cpu_usage', 'N/A')}
  • ディスク使用量: {status.get('disk_usage', 'N/A')}

🌐 ネットワーク情報:
  • 接続状態: {'✅ 接続中' if status.get('is_connected', False) else '❌ 切断中'}
  • 接続回数: {status.get('connection_count', 0)}回
  • 最終接続: {status.get('last_connection', 'N/A')}
  • 平均応答時間: {status.get('avg_response_time', 'N/A')}

⚙️ 設定情報:
  • デバッグモード: {'✅ 有効' if status.get('debug_mode', False) else '❌ 無効'}
  • ドライランモード: {'✅ 有効' if status.get('dry_run_mode', False) else '❌ 無効'}
  • ログレベル: {status.get('log_level', 'N/A')}"""
            
            logger.info("サーバー詳細ステータス情報生成完了")
            return server_message
            
        except Exception as e:
            logger.error(f"サーバーステータス処理エラー: {e}")
            raise StatusHandlerError(f"サーバーステータス処理失敗: {e}")
    
    async def _handle_bot_status(self) -> str:
        """ボット詳細ステータス表示"""
        try:
            status = self._get_bot_status()
            
            bot_message = f"""🤖 ボット詳細ステータス

📊 処理統計:
  • 処理メッセージ数: {status.get('message_count', 0):,}件
  • エラー数: {status.get('error_count', 0)}件
  • エラー率: {status.get('error_rate', 0.0):.1%}
  • 処理成功率: {status.get('success_rate', 0.0):.1f}%
  • 最終処理時刻: {status.get('last_command_time', 'N/A')}

🔧 ハンドラー情報:
  • 登録ハンドラー数: {status.get('handlers_count', 0)}個
  • 利用可能ハンドラー: {status.get('available_handlers', 'N/A')}
  • 最終ハートビート: {status.get('last_heartbeat', 'N/A')}

📈 パフォーマンス:
  • 平均応答時間: {status.get('avg_response_time', 'N/A')}
  • 最大応答時間: {status.get('max_response_time', 'N/A')}
  • 最小応答時間: {status.get('min_response_time', 'N/A')}"""
            
            logger.info("ボット詳細ステータス情報生成完了")
            return bot_message
            
        except Exception as e:
            logger.error(f"ボットステータス処理エラー: {e}")
            raise StatusHandlerError(f"ボットステータス処理失敗: {e}")
    
    async def _handle_timeline_status(self) -> str:
        """年表詳細ステータス表示"""
        try:
            status = self._get_bot_status()
            
            timeline_message = f"""📚 年表詳細ステータス

🗄️ データベース情報:
  • 総イベント数: {status.get('database_events', 0):,}件
  • データベースサイズ: {status.get('database_size', 'N/A')}
  • 最終更新: {status.get('last_data_update', 'N/A')}
  • 更新結果: {status.get('last_update_result', 'N/A')}

📅 データ範囲:
  • 最古のイベント: {status.get('oldest_event', 'N/A')}
  • 最新のイベント: {status.get('newest_event', 'N/A')}
  • 年代別分布: {status.get('decade_distribution', 'N/A')}

🔗 データソース:
  • 年表URL: {status.get('timeline_url', 'N/A')}
  • 最終取得: {status.get('last_fetch_time', 'N/A')}
  • 取得結果: {status.get('last_fetch_result', 'N/A')}"""
            
            logger.info("年表詳細ステータス情報生成完了")
            return timeline_message
            
        except Exception as e:
            logger.error(f"年表ステータス処理エラー: {e}")
            raise StatusHandlerError(f"年表ステータス処理失敗: {e}")
    
    def _get_bot_status(self) -> StatusInfo:
        """
        ボットの現在のステータス情報を取得
        
        Returns:
            StatusInfo: ステータス情報
            
        Raises:
            StatusHandlerError: ステータス取得エラー時
        """
        try:
            # データベース統計
            stats = self.database.get_statistics() if self.database else {'total_events': 0}
            
            # BotClientの状態情報を取得
            bot_client_status = {}
            if self.bot_client:
                try:
                    bot_client_status = self.bot_client.get_client_status()
                    logger.debug(f"BotClient状態: {bot_client_status}")
                except Exception as e:
                    logger.warning(f"BotClient状態取得エラー: {e}")
            else:
                logger.warning("BotClientが設定されていません")
            
            # CommandRouterの状態情報を取得（bot_client経由）
            router_status = {}
            if self.bot_client and self.bot_client.command_router:
                try:
                    router_status = self.bot_client.command_router.get_router_status()
                    logger.debug(f"CommandRouter状態: {router_status}")
                except Exception as e:
                    logger.warning(f"CommandRouter状態取得エラー: {e}")
            else:
                logger.warning("CommandRouterが設定されていません")
            
            # 処理成功率の計算
            message_count = router_status.get('command_count', 0)
            error_count = router_status.get('error_count', 0)
            success_rate = 0.0
            if message_count > 0:
                success_rate = max(0.0, min(100.0, ((message_count - error_count) / message_count) * 100))
            
            # デバッグ: 計算過程をログ出力
            logger.debug(f"処理成功率計算: message_count={message_count}, error_count={error_count}, success_rate={success_rate}")
            
            # システム情報の取得
            system_info = self._get_system_info()
            
            # データベース詳細情報の取得
            db_details = self._get_database_details()
            
            final_status = StatusInfo(
                # 基本情報
                uptime=bot_client_status.get('uptime', 'N/A'),
                message_count=message_count,
                error_count=error_count,
                database_events=stats['total_events'],
                startup_time=bot_client_status.get('startup_time'),
                is_connected=bot_client_status.get('is_connected', False),
                error_rate=router_status.get('error_rate', 0.0),
                dry_run_mode=bot_client_status.get('dry_run_mode', False),
                avg_response_time=bot_client_status.get('avg_response_time', 'N/A'),
                memory_usage=bot_client_status.get('memory_usage', 'N/A'),
                success_rate=success_rate,
                
                # サーバー情報
                cpu_usage=system_info.get('cpu_usage', 'N/A'),
                disk_usage=system_info.get('disk_usage', 'N/A'),
                connection_count=bot_client_status.get('connection_count', 0),
                last_connection=bot_client_status.get('last_connection', 'N/A') if bot_client_status.get('last_connection') else 'N/A',
                debug_mode=bot_client_status.get('debug_mode', False),
                log_level=self.config.log_level if hasattr(self.config, 'log_level') else 'N/A',
                
                # ボット情報
                last_command_time=router_status.get('last_command_time', 'N/A'),
                handlers_count=router_status.get('handlers_count', 0),
                available_handlers=router_status.get('available_handlers', 'N/A'),
                last_heartbeat=bot_client_status.get('last_heartbeat', 'N/A'),
                max_response_time=bot_client_status.get('max_response_time', 'N/A'),
                min_response_time=bot_client_status.get('min_response_time', 'N/A'),
                
                # 年表情報
                database_size=db_details.get('database_size', 'N/A'),
                last_data_update=db_details.get('last_data_update', 'N/A'),
                last_update_result=db_details.get('last_update_result', 'N/A'),
                oldest_event=db_details.get('oldest_event', 'N/A'),
                newest_event=db_details.get('newest_event', 'N/A'),
                decade_distribution=db_details.get('decade_distribution', 'N/A'),
                timeline_url=self.config.timeline_url if hasattr(self.config, 'timeline_url') else 'N/A',
                last_fetch_time=db_details.get('last_fetch_time', 'N/A'),
                last_fetch_result=db_details.get('last_fetch_result', 'N/A'),
            )
            
            logger.debug(f"最終ステータス: {final_status}")
            return final_status
            
        except Exception as e:
            logger.error(f"ステータス取得エラー: {e}")
            raise StatusHandlerError(f"ステータス取得失敗: {e}")
    
    def _get_system_info(self) -> StatusSystemInfo:
        """
        システム情報を取得
        
        Returns:
            SystemInfo: システム情報
            
        Raises:
            StatusHandlerError: システム情報取得エラー時
        """
        try:
            import psutil
            import os
            
            # CPU使用率
            cpu_usage = f"{psutil.cpu_percent(interval=1):.1f}%"
            
            # メモリ使用量
            memory = psutil.virtual_memory()
            memory_usage = f"{memory.percent:.1f}% ({memory.used // (1024**3):.1f}GB / {memory.total // (1024**3):.1f}GB)"
            
            # ディスク使用量
            disk = psutil.disk_usage('/')
            disk_usage = f"{disk.percent:.1f}% ({disk.used // (1024**3):.1f}GB / {disk.total // (1024**3):.1f}GB)"
            
            return StatusSystemInfo(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
            )
            
        except ImportError:
            logger.warning("psutilがインストールされていません。システム情報を取得できません。")
            return StatusSystemInfo(
                cpu_usage='N/A (psutil未インストール)',
                memory_usage='N/A (psutil未インストール)',
                disk_usage='N/A (psutil未インストール)',
            )
        except Exception as e:
            logger.error(f"システム情報取得エラー: {e}")
            raise StatusHandlerError(f"システム情報取得失敗: {e}")
    
    def _get_database_details(self) -> StatusDatabaseInfo:
        """
        データベース詳細情報を取得
        
        Returns:
            DatabaseInfo: データベース情報
            
        Raises:
            StatusHandlerError: データベース情報取得エラー時
        """
        try:
            if not self.database:
                return StatusDatabaseInfo(
                    database_size='N/A',
                    last_data_update='N/A',
                    last_update_result='N/A',
                    oldest_event='N/A',
                    newest_event='N/A',
                    decade_distribution='N/A',
                    last_fetch_time='N/A',
                    last_fetch_result='N/A',
                )
            
            # データベースサイズ
            db_path = self.config.database_path if hasattr(self.config, 'database_path') else None
            database_size = 'N/A'
            if db_path and db_path.exists():
                size_bytes = db_path.stat().st_size
                if size_bytes > 1024**3:
                    database_size = f"{size_bytes / (1024**3):.1f}GB"
                elif size_bytes > 1024**2:
                    database_size = f"{size_bytes / (1024**2):.1f}MB"
                else:
                    database_size = f"{size_bytes / 1024:.1f}KB"
            
            # データ範囲情報
            oldest_event = self.database.get_oldest_event() if hasattr(self.database, 'get_oldest_event') else 'N/A'
            newest_event = self.database.get_newest_event() if hasattr(self.database, 'get_newest_event') else 'N/A'
            decade_distribution = self.database.get_decade_distribution() if hasattr(self.database, 'get_decade_distribution') else 'N/A'
            
            # 更新履歴情報
            update_history = self.database.get_last_update_info() if hasattr(self.database, 'get_last_update_info') else {}
            last_data_update = update_history.get('last_update', 'N/A')
            last_update_result = update_history.get('result', 'N/A')
            last_fetch_time = update_history.get('last_fetch', 'N/A')
            last_fetch_result = update_history.get('fetch_result', 'N/A')
            
            return StatusDatabaseInfo(
                database_size=database_size,
                last_data_update=last_data_update,
                last_update_result=last_update_result,
                oldest_event=oldest_event,
                newest_event=newest_event,
                decade_distribution=decade_distribution,
                last_fetch_time=last_fetch_time,
                last_fetch_result=last_fetch_result,
            )
            
        except Exception as e:
            logger.error(f"データベース詳細情報取得エラー: {e}")
            raise StatusHandlerError(f"データベース詳細情報取得失敗: {e}")