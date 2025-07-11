"""
分散SNS関連年表bot - メインボットアプリケーション

このモジュールは分散SNS関連年表botのメインエントリーポイントとして機能し、
以下の主要な責任を担います：

## 主要機能
- **ボットライフサイクル管理**: 初期化、開始、終了、シャットダウンの統合管理
- **コンポーネント統合**: Config、Database、DataService、CommandRouter、BotClientの統合
- **エラーハンドリング**: 全体的なエラー処理とログ管理
- **シグナル処理**: SIGINT/SIGTERMによる正常終了の実装
- **ヘルスモニタリング**: ボット状態の監視と統計情報の提供

## アーキテクチャ概要
- **DSNSTimelineBot**: メインクラス。全コンポーネントの統合管理
- **初期化フロー**: Config → Database → DataService → CommandRouter → BotClient
- **実行フロー**: start_bot() → run_forever() → shutdown_bot()
- **テストモード**: BotClient未初期化時の自動フォールバック機能

## 依存関係
- **外部ライブラリ**: mipa (Misskeyボットライブラリ)
- **内部モジュール**: config, database, data_service, command_router, bot_client
- **標準ライブラリ**: asyncio, logging, signal, sys, datetime, pathlib

## 運用特性
- **非同期処理**: 全体的にasyncioベースの非同期実行
- **エラー耐性**: 各段階でのエラーハンドリングとフォールバック機能
- **ログ管理**: 詳細なログ出力とファイル・コンソール両方への出力
- **設定管理**: 設定ファイルの動的読み込みと検証

## 開発・デバッグ機能
- **ドライランモード**: 実際の投稿なしでのテスト実行
- **テストループ**: BotClientなしでの基本機能テスト
- **詳細ログ**: デバッグレベルの詳細ログ出力
- **統計情報**: メッセージ数、エラー数、稼働時間などの統計

## セキュリティ・運用考慮事項
- **トークン管理**: Misskey APIトークンの安全な管理
- **接続管理**: WebSocket接続の適切な開始・終了
- **リソース管理**: データベース接続やファイルハンドルの適切な解放
- **監視機能**: ハートビート監視と異常検出
"""

import asyncio
import logging
import signal
import sys
import traceback
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

# MiPA（Misskeyボットライブラリ）
try:
    from mipa.ext.commands.bot import Bot
    print("✅ MiPA インポート成功")
except ImportError as e:
    print("❌ MiPAライブラリが見つかりません。以下のコマンドでインストールしてください:")
    print("pip install mipa")
    print(f"詳細エラー: {e}")
    sys.exit(1)

# 内部モジュール
try:
    from config import Config
    from database import TimelineDatabase
    from data_service import TimelineDataService
    print("✅ 内部モジュール インポート成功")
except ImportError as e:
    print(f"❌ 内部モジュールインポートエラー: {e}")
    print("現在のディレクトリにconfig.py, database.py等があることを確認してください")
    sys.exit(1)

logger = logging.getLogger(__name__)

class DSNSTimelineBot:
    """
    分散SNS関連年表ボットのメインクラス
    
    MiPAを使用してMisskeyボットとして動作し、
    年表データの取得・投稿・ユーザーとの対話を管理
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """分散SNS関連年表ボットの初期化を行います。
        
        Args:
            config_path (Optional[str]): 設定ファイルのパス。
                Noneの場合はデフォルトの設定ファイルを使用。
        """
        self.config = None
        self.database = None
        self.data_service = None
        self.command_router = None
        self.bot_client = None
        
        # ボット状態管理
        self.is_running = False
        self.startup_time = None
        self.last_heartbeat = None
        self.message_count = 0
        self.error_count = 0
        
        # シャットダウンフラグ
        self.shutdown_requested = False
        
        # 初期化実行
        self._init_components(config_path)
    
    def _init_components(self, config_path: Optional[str] = None):
        """ボットコンポーネントの初期化を行います。"""
        try:
            logger.info("=== DSNS Timeline Bot 初期化開始 ===")
            
            # 設定読み込み
            self.config = Config(config_path)
            logger.info("✅ 設定読み込み完了")
            
            # データベース初期化
            self.database = TimelineDatabase(self.config.database_path)
            logger.info("✅ データベース初期化完了")
            
            # データサービス初期化
            self.data_service = TimelineDataService(self.config, self.database)
            logger.info("✅ データサービス初期化完了")
            
            # BotClient初期化
            try:
                from bot_client import BotClient
                self.bot_client = BotClient(self.config)
                logger.info("✅ BotClient初期化完了")
                
            except Exception as e:
                logger.error(f"BotClient初期化失敗: {e}")
                logger.debug(traceback.format_exc())
                self.bot_client = None
                logger.warning("ボットクライアントなしで続行（テスト用）")
            
            # CommandRouter初期化
            from command_router import CommandRouter
            self.command_router = CommandRouter(
                self.config, self.database, self.data_service, self.bot_client
            )
            logger.info("✅ CommandRouter初期化完了")
            
            # BotClientにCommandRouterを設定
            if self.bot_client:
                self.bot_client.set_command_router(self.command_router)
            
            logger.info("=== 初期化完了 ===")
            
        except Exception as e:
            logger.critical(f"初期化エラー: {e}")
            logger.debug(traceback.format_exc())
            sys.exit(1)
    
    async def start_bot(self):
        """ボットの非同期開始処理を実行します。"""
        try:
            if self.is_running:
                logger.warning("ボットは既に実行中です")
                return
            
            self.startup_time = datetime.now()
            self.is_running = True
            
            logger.info("=== ボット開始 ===")
            
            # データサービスの初期化（非同期部分）
            if self.data_service and hasattr(self.data_service, '__aenter__'):
                await self.data_service.__aenter__()
            
            # 初期ヘルスチェック
            await self._initial_health_check()
            
            # BotClient経由で接続
            if self.bot_client:
                logger.info("BotClient経由でMisskeyインスタンスへ接続中...")
                
                try:
                    # 起動時刻を BotClient に設定（起動通知用）
                    self.bot_client.startup_time = self.startup_time
                    
                    # BotClient経由で接続
                    await self.bot_client.connect()
                    
                except Exception as connect_error:
                    logger.error(f"BotClient接続エラー: {connect_error}")
                    logger.debug(traceback.format_exc())
                    
                    # 接続エラーの種類に応じた処理
                    if "timeout" in str(connect_error).lower():
                        logger.warning("接続タイムアウト - ネットワーク環境を確認してください")
                    elif "cancelled" in str(connect_error).lower():
                        logger.warning("接続が中断されました - 再起動を試してください")
                    elif "token" in str(connect_error).lower():
                        logger.error("トークンエラー - 設定を確認してください")
                    else:
                        logger.error("不明な接続エラー")
                    
                    # 接続エラーでもボットは継続実行（定期投稿機能は有効）
                    logger.warning("BotClient接続に失敗しましたが、定期投稿機能は継続します")
                    # テストモードは実行せず、メインループに進む
            else:
                logger.warning("BotClientが未初期化のため接続をスキップ")
                await self._test_main_loop()

        except Exception as e:
            logger.critical(f"ボット開始エラー: {e}")
            logger.debug(traceback.format_exc())
            await self.shutdown_bot()
            raise
    
    async def _initial_health_check(self):
        """ボット開始時の初期ヘルスチェックを実行します。"""
        try:
            logger.info("初期ヘルスチェック実行中...")
            
            # データサービスのヘルスチェック
            if self.data_service and hasattr(self.data_service, 'health_check'):
                health = await self.data_service.health_check()
                
                if health.get('status') == 'healthy':
                    logger.info("✅ ヘルスチェック完了")
                elif health.get('status') == 'degraded':
                    logger.warning(f"⚠️ 一部機能に問題: {health.get('failed_checks', [])}")
                else:
                    logger.error(f"❌ ヘルスチェック失敗: {health}")
            else:
                logger.warning("データサービスのヘルスチェック機能が利用できません")
                
            # データベース統計表示
            if self.database:
                stats = self.database.get_statistics()
                logger.info(f"データベース統計: {stats['total_events']}件のイベント")
            else:
                logger.warning("データベースが未初期化")
            
        except Exception as e:
            logger.error(f"ヘルスチェックエラー: {e}")
    
    async def _test_main_loop(self):
        """ボットクライアントなしでのテスト用メインループです。"""
        logger.info("🔧 テストモード: ボットクライアントなしで実行中")
        
        # 今日のイベントをログ出力してテスト
        if self.command_router and 'today' in self.command_router.handlers:
            try:
                from datetime import date
                test_note = type('TestNote', (), {'text': '今日のイベント教えて'})()
                message = await self.command_router.handlers['today'].handle(test_note, {'type': 'today'})
                logger.info(f"📅 今日のイベント（テスト）:\n{message}")
            except Exception as e:
                logger.error(f"今日のイベント取得エラー: {e}")
        
        # 短時間でテスト終了
        await asyncio.sleep(5)
        logger.info("🔧 テストモード終了")
        self.shutdown_requested = True

    def _get_bot_status(self) -> Dict[str, Any]:
        """ボットの現在のステータス情報を取得します。"""
        uptime = datetime.now() - self.startup_time if self.startup_time else timedelta(0)
        stats = self.database.get_statistics() if self.database else {'total_events': 0}
        
        return {
            'uptime': str(uptime).split('.')[0],  # 秒以下を除去
            'message_count': self.message_count,
            'error_count': self.error_count,
            'last_heartbeat': self.last_heartbeat.strftime('%H:%M:%S') if self.last_heartbeat else 'N/A',
            'database_events': stats['total_events'],
            'startup_time': self.startup_time.isoformat() if self.startup_time else None,
        }
   
    async def shutdown_bot(self):
        """ボットの正常終了処理を実行します。"""
        if not self.is_running:
            return
        
        logger.info("=== ボット終了処理開始 ===")
        self.shutdown_requested = True
        
        try:
            # データサービス終了
            if self.data_service and hasattr(self.data_service, '__aexit__'):
                try:
                    await self.data_service.__aexit__(None, None, None)
                    logger.info("✅ データサービス終了完了")
                except Exception as e:
                    logger.error(f"データサービス終了エラー: {e}")
            
            # BotClient終了
            if self.bot_client:
                try:
                    await self.bot_client.disconnect()
                    logger.info("✅ BotClient終了完了")
                except Exception as e:
                    logger.error(f"BotClient終了エラー: {e}")
            
            self.is_running = False
            logger.info("✅ ボット終了完了")
            
        except Exception as e:
            logger.error(f"終了処理エラー: {e}")
            logger.debug(traceback.format_exc())
    
    async def run_forever(self):
        """ボットの無限実行ループを開始します。"""
        try:
            await self.start_bot()
            
            # シグナルハンドラー設定
            def signal_handler(signum, frame):
                logger.info(f"シグナル受信: {signum}")
                self.shutdown_requested = True
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # systemd環境での動作確認
            logger.info("✅ ボット開始完了 - systemdサービスとして動作中")
            
            # メインループ
            while not self.shutdown_requested:
                await asyncio.sleep(1)
                
                # 定期的なハートビートチェック
                if self.last_heartbeat:
                    time_since_heartbeat = datetime.now() - self.last_heartbeat
                    if time_since_heartbeat > timedelta(minutes=10):
                        logger.warning(f"ハートビート遅延: {time_since_heartbeat}")
                
                # 定期投稿チェック（1分ごと）
                if self.command_router and 'today' in self.command_router.handlers:
                    try:
                        today_handler = self.command_router.handlers['today']
                        if hasattr(today_handler, 'post_scheduled_today_event'):
                            # 定期投稿チェック実行（デバッグログ追加）
                            logger.debug("定期投稿チェック実行中...")
                            result = await today_handler.post_scheduled_today_event()
                            if result:
                                logger.info("✅ 定期投稿実行完了")
                            else:
                                logger.debug("定期投稿タイミングではありません")
                    except Exception as e:
                        logger.error(f"定期投稿チェックエラー: {e}")
                else:
                    logger.warning("定期投稿チェック: command_routerまたはtodayハンドラーが利用できません")
            
        except KeyboardInterrupt:
            logger.info("キーボード割り込み受信")
        except asyncio.CancelledError:
            logger.info("タスクがキャンセルされました")
        except Exception as e:
            logger.critical(f"メインループエラー: {e}")
            logger.debug(traceback.format_exc())
        finally:
            await self.shutdown_bot()


async def main():
    """メインエントリーポイント関数です。"""
    print("🤖 分散SNS関連年表bot 起動中...")
    
    try:
        bot = DSNSTimelineBot()
        await bot.run_forever()
    except Exception as e:
        logger.critical(f"ボット実行エラー: {e}")
        sys.exit(1)


# CLI実行用
if __name__ == "__main__":
    # ログディレクトリ作成
    Path("logs").mkdir(exist_ok=True)
    
    # 詳細なログ設定
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # ルートロガーの設定をクリア
    logging.getLogger().handlers.clear()
    
    # ログハンドラーを設定
    handlers = []
    
    # ファイルハンドラー
    try:
        file_handler = logging.FileHandler('logs/bot.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)
        print(f"✅ ログファイル設定完了: logs/bot.log")
    except Exception as e:
        print(f"❌ ログファイル設定エラー: {e}")
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # ルートロガー設定
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=handlers,
        format=log_format
    )
    
    # 特定のロガーのレベル調整
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
    # asyncioの未クローズセッション警告を抑制
    import warnings
    warnings.filterwarnings("ignore", message="Unclosed client session")
    warnings.filterwarnings("ignore", message="Unclosed connector")
    warnings.filterwarnings("ignore", message=".*Unclosed.*")
    warnings.filterwarnings("ignore", message=".*client session.*")
    warnings.filterwarnings("ignore", message=".*connector.*")
    
    # asyncioの警告レベルを調整
    logging.getLogger('asyncio').setLevel(logging.ERROR)
    
    # aiohttpの警告も抑制
    logging.getLogger('aiohttp').setLevel(logging.ERROR)
    logging.getLogger('aiohttp.client').setLevel(logging.ERROR)
    
    # イベントループ終了時のセッションクリーンアップを設定
    import atexit
    import asyncio
    
    def cleanup_sessions():
        """イベントループ終了時にセッションをクリーンアップ"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 非同期でセッションクリーンアップを実行
                async def async_cleanup():
                    try:
                        from mipa.http import HTTPSession
                        if hasattr(HTTPSession, 'close_session'):
                            await HTTPSession.close_session()
                    except Exception:
                        pass
                
                # 新しいタスクとして実行
                asyncio.create_task(async_cleanup())
        except Exception:
            pass
    
    atexit.register(cleanup_sessions)
    
    print(f"🔧 ログ設定完了: レベル=DEBUG, ハンドラー数={len(handlers)}")
    
    # メイン実行
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 ボットを終了します...")
    except Exception as e:
        print(f"❌ 致命的エラー: {e}")
        logging.exception("致命的エラーの詳細:")
        sys.exit(1)