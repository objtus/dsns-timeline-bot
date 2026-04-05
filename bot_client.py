"""
MiPA WebSocketクライアント専用管理

WebSocket接続、再接続、メッセージ受信処理を担当
"""

import asyncio
import logging
import traceback
from datetime import datetime
from typing import Optional, Any

from constants import (
    MessageLimits, Visibility, ErrorMessages, 
    SuccessMessages, DefaultValues
)
from exceptions import BotClientError, NetworkError, MessageLimitError, ConfigError
from dsnstypes import VisibilityType

# MiPA（Misskeyボットライブラリ）
try:
    from mipa.ext.commands.bot import Bot
except ImportError as e:
    logging.error(f"MiPAライブラリが見つかりません: {e}")
    raise

logger = logging.getLogger(__name__)

class SessionManager:
    """統一されたセッション管理クラス"""
    
    def __init__(self, mipa_bot):
        """
        セッション管理の初期化
        
        Args:
            mipa_bot: MiPAボットインスタンス
        """
        self.mipa_bot = mipa_bot
        self._sessions_to_close = []
    
    async def close_all_sessions(self):
        """全てのセッションを適切に閉じる"""
        logger.info("セッション管理: 全セッションの切断開始")
        
        # 1. MiPA APIセッション（最優先）
        await self._close_mipa_api_session()
        
        # 2. MiPAクライアントセッション
        await self._close_mipa_client_session()
        
        # 3. WebSocket接続
        await self._close_websocket_session()
        
        # 4. その他のセッション
        await self._close_other_sessions()
        
        logger.info("セッション管理: 全セッションの切断完了")
    
    async def _close_mipa_api_session(self):
        """MiPA APIセッションを閉じる"""
        try:
            if hasattr(self.mipa_bot, 'core') and self.mipa_bot.core:
                if hasattr(self.mipa_bot.core, 'close_session'):
                    await self.mipa_bot.core.close_session()
                    logger.info("セッション管理: MiPA APIセッション切断完了")
                else:
                    logger.debug("セッション管理: MiPA core.close_session()メソッドが利用できません")
            else:
                logger.debug("セッション管理: MiPA coreが利用できません")
        except Exception as e:
            logger.warning(f"セッション管理: MiPA APIセッション切断エラー（無視）: {e}")
    
    async def _close_mipa_client_session(self):
        """MiPAクライアントセッションを閉じる"""
        try:
            if hasattr(self.mipa_bot, 'client') and self.mipa_bot.client:
                if hasattr(self.mipa_bot.client, 'session') and self.mipa_bot.client.session:
                    if not self.mipa_bot.client.session.closed:
                        await self.mipa_bot.client.session.close()
                        logger.info("セッション管理: MiPAクライアントセッション切断完了")
                    else:
                        logger.debug("セッション管理: MiPAクライアントセッションは既に閉じられています")
                else:
                    logger.debug("セッション管理: MiPAクライアントセッションが利用できません")
            else:
                logger.debug("セッション管理: MiPAクライアントが利用できません")
        except Exception as e:
            logger.warning(f"セッション管理: MiPAクライアントセッション切断エラー（無視）: {e}")
    
    async def _close_websocket_session(self):
        """WebSocketセッションを閉じる"""
        try:
            if hasattr(self.mipa_bot, 'ws') and self.mipa_bot.ws:
                if hasattr(self.mipa_bot.ws, 'closed'):
                    if not self.mipa_bot.ws.closed:
                        await self.mipa_bot.ws.close()
                        logger.info("セッション管理: WebSocketセッション切断完了")
                    else:
                        logger.debug("セッション管理: WebSocketセッションは既に閉じられています")
                else:
                    # closed属性がない場合は直接close()を試行
                    try:
                        await self.mipa_bot.ws.close()
                        logger.info("セッション管理: WebSocketセッション切断完了（直接呼び出し）")
                    except Exception as direct_close_error:
                        logger.debug(f"セッション管理: WebSocket直接切断エラー（無視）: {direct_close_error}")
            else:
                logger.debug("セッション管理: WebSocketセッションが利用できません")
        except Exception as e:
            logger.warning(f"セッション管理: WebSocketセッション切断エラー（無視）: {e}")
    
    async def _close_other_sessions(self):
        """その他のセッションを閉じる"""
        # 必要に応じて追加のセッション管理を実装
        pass

class BotClient:
    """MiPA WebSocketクライアント専用管理"""
    
    def __init__(self, config):
        """
        ボットクライアント初期化
        
        Args:
            config: 設定オブジェクト
        """
        self.config = config
        self.mipa_bot = None
        self.command_router = None
        self.session_manager = None  # セッション管理
        
        # 接続状態管理
        self.is_connected = False
        self.last_heartbeat: Optional[datetime] = None
        self.connection_count = 0
        self.note_count = 0
        self.startup_time: Optional[datetime] = None
        self.mipa_task = None  # MiPAバックグラウンドタスク
        self.last_posted_note_id: Optional[str] = None  # 最後の投稿ID（LLMコメント用）
        
        # 接続監視の強化
        self.last_connection_attempt: Optional[datetime] = None
        self.connection_failure_count = 0
        self.max_connection_failures = getattr(config, 'max_connection_failures', 5)
        self.connection_health_check_interval = getattr(config, 'connection_health_check_interval', 300)
        self.heartbeat_timeout_seconds = getattr(config, 'heartbeat_timeout_seconds', 600)
        self.last_health_check: Optional[datetime] = None
        
        logger.info("BotClient初期化完了")
    
    def set_command_router(self, router):
        """
        CommandRouterを設定
        
        Args:
            router: CommandRouterインスタンス
        """
        self.command_router = router
        logger.info("CommandRouter設定完了")
    
    async def check_connection_health(self):
        """
        接続状態のヘルスチェック（強化版）
        
        Returns:
            bool: 接続が正常な場合True
        """
        try:
            if not self.mipa_bot:
                logger.warning("⚠️ MiPAボットが初期化されていません")
                return False
            
            # 最後のハートビートからの経過時間をチェック
            if self.last_heartbeat:
                time_since_heartbeat = (datetime.now() - self.last_heartbeat).total_seconds()
                if time_since_heartbeat > self.heartbeat_timeout_seconds:  # 10分以上ハートビートがない
                    logger.warning(f"⚠️ ハートビートが{time_since_heartbeat:.0f}秒間受信されていません")
                    return False
            
            # WebSocket接続状態をチェック
            if hasattr(self.mipa_bot, 'ws') and self.mipa_bot.ws:
                # WebSocketオブジェクトの属性をデバッグ出力
                ws_attrs = [attr for attr in dir(self.mipa_bot.ws) if not attr.startswith('_')]
                logger.debug(f"WebSocketオブジェクトの属性: {ws_attrs}")
                
                # MiPAのWebSocketオブジェクト（ClientWebSocketResponse）の正しい属性を使用
                if hasattr(self.mipa_bot.ws, 'closed'):
                    if self.mipa_bot.ws.closed:
                        logger.warning("⚠️ WebSocket接続が切断されています")
                        return False
                elif hasattr(self.mipa_bot.ws, 'open'):
                    if not self.mipa_bot.ws.open:
                        logger.warning("⚠️ WebSocket接続が切断されています")
                        return False
                else:
                    # どちらの属性も存在しない場合は、pingで接続確認
                    logger.debug("WebSocket接続状態をpingで確認します")
                
                # 接続の生存確認（ping）
                try:
                    if hasattr(self.mipa_bot.ws, 'ping') and callable(getattr(self.mipa_bot.ws, 'ping')):
                        try:
                            await asyncio.wait_for(self.mipa_bot.ws.ping(), timeout=5.0)
                            logger.debug("✅ WebSocket ping成功")
                        except asyncio.TimeoutError:
                            logger.warning("⚠️ WebSocket pingタイムアウト")
                            return False
                        except Exception as ping_error:
                            logger.warning(f"⚠️ WebSocket pingエラー: {ping_error}")
                            return False
                    else:
                        logger.debug("WebSocket ping機能が利用できません")
                            
                except Exception as ws_check_error:
                    logger.warning(f"⚠️ WebSocket状態チェックエラー: {ws_check_error}")
                    return False
            
            # MiPAボットの内部状態チェック（セッション管理を使用）
            if self.session_manager:
                try:
                    # セッション状態をチェック
                    if hasattr(self.mipa_bot, 'client') and self.mipa_bot.client:
                        if hasattr(self.mipa_bot.client, 'session') and self.mipa_bot.client.session:
                            if self.mipa_bot.client.session.closed:
                                logger.warning("⚠️ MiPAクライアントセッションが閉じられています")
                                return False
                except Exception as client_check_error:
                    logger.warning(f"⚠️ MiPAクライアント状態チェックエラー: {client_check_error}")
                    return False
            else:
                logger.debug("セッション管理が初期化されていないため、セッション状態チェックをスキップ")
            
            logger.debug("✅ 接続状態は正常です")
            return True
            
        except Exception as e:
            logger.error(f"接続状態チェックエラー: {e}")
            return False
    
    async def attempt_reconnection(self):
        """
        手動再接続の試行（強化版）
        
        Returns:
            bool: 再接続成功時True
        """
        try:
            logger.info("🔄 手動再接続を試行します")
            
            # 接続失敗回数をチェック
            if self.connection_failure_count >= self.max_connection_failures:
                logger.error(f"❌ 接続失敗回数が上限({self.max_connection_failures}回)に達しました")
                logger.error("手動での復旧が必要です")
                return False
            
            # 既存の接続を適切に切断
            await self._cleanup_existing_connection()
            
            # 接続状態をリセット
            self.is_connected = False
            self.last_heartbeat = None
            
            # 新しい接続を試行
            await self.connect()
            
            # 接続成功を確認
            await asyncio.sleep(5)  # 接続安定化のため5秒待機
            
            if await self.check_connection_health():
                logger.info("✅ 再接続が成功しました")
                self.connection_failure_count = 0  # 失敗回数をリセット
                return True
            else:
                logger.warning("⚠️ 再接続後の接続状態チェックに失敗")
                return False
            
        except Exception as e:
            self.connection_failure_count += 1
            logger.error(f"❌ 手動再接続に失敗しました (失敗回数: {self.connection_failure_count}/{self.max_connection_failures}): {e}")
            return False
    
    async def _cleanup_existing_connection(self):
        """既存の接続を適切にクリーンアップ（disconnect()メソッドを使用）"""
        await self.disconnect()
    
    async def connect(self):
        """
        WebSocket接続処理
        
        Raises:
            ValueError: 接続設定が不正な場合
            ConnectionError: WebSocket接続に失敗した場合
        """
        try:
            logger.info("WebSocket接続開始")
            
            # 設定確認
            if not hasattr(self.config, 'misskey_token') or not self.config.misskey_token:
                raise ConfigError("MISSKEY_TOKEN が設定されていません")
            
            # WebSocket URL構築
            host = self._get_misskey_host()
            ws_url = f"wss://{host}/streaming"
            token = self.config.misskey_token
            
            logger.info(f"接続先: {ws_url}")
            logger.info(f"トークン長: {len(token)}文字")
            
            # カスタムボットクラス作成
            self.mipa_bot = DSNSMiPABot(self)
            
            # セッション管理を初期化
            self.session_manager = SessionManager(self.mipa_bot)
            logger.info("セッション管理を初期化しました")
            
            # MiPAのstart()をバックグラウンドタスクで実行
            loop = asyncio.get_running_loop()
            self.mipa_task = loop.create_task(self.mipa_bot.start(ws_url, token))
            logger.info("MiPA start()をバックグラウンドで実行開始")
            
            # 接続状態監視タスクを開始
            self._start_connection_monitor(loop)
            
            # すぐにreturnし、メインループへ制御を返す
            
        except Exception as e:
            logger.error(f"WebSocket接続エラー: {e}")
            logger.debug(traceback.format_exc())
            raise NetworkError(f"WebSocket接続に失敗しました: {e}", url=ws_url)
    
    def _start_connection_monitor(self, loop):
        """接続状態監視タスクを開始"""
        try:
            monitor_task = loop.create_task(self._connection_monitor_loop())
            logger.info("接続状態監視タスクを開始しました")
        except Exception as e:
            logger.error(f"接続状態監視タスクの開始に失敗: {e}")
    
    async def _connection_monitor_loop(self):
        """接続状態監視ループ（強化版）"""
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        while True:
            try:
                await asyncio.sleep(self.connection_health_check_interval)
                
                # 接続状態をチェック
                is_healthy = await self.check_connection_health()
                
                if is_healthy:
                    consecutive_failures = 0  # 連続失敗回数をリセット
                    logger.debug("✅ 接続状態監視: 正常")
                else:
                    consecutive_failures += 1
                    logger.warning(f"⚠️ 接続状態に問題を検出しました (連続失敗: {consecutive_failures}/{max_consecutive_failures})")
                    
                    # 連続失敗回数が上限に達した場合のみ自動復旧を試行
                    if consecutive_failures >= max_consecutive_failures:
                        if self.connection_failure_count < self.max_connection_failures:
                            logger.info("🔄 連続失敗による自動復旧を試行します")
                            recovery_success = await self.attempt_reconnection()
                            
                            if recovery_success:
                                consecutive_failures = 0  # 復旧成功時はリセット
                                logger.info("✅ 自動復旧が成功しました")
                            else:
                                logger.warning("⚠️ 自動復旧に失敗しました")
                        else:
                            logger.critical("🚨 自動復旧の上限に達しました。手動での復旧が必要です。")
                            # システム管理者への通知を検討
                            break
                    else:
                        logger.info(f"⚠️ 連続失敗回数が少ないため、自動復旧は見送ります ({consecutive_failures}/{max_consecutive_failures})")
                
                # ヘルスチェック時刻を更新
                self.last_health_check = datetime.now()
                
            except asyncio.CancelledError:
                logger.info("接続状態監視タスクがキャンセルされました")
                break
            except Exception as e:
                logger.error(f"接続状態監視エラー: {e}")
                consecutive_failures += 1
                
                # エラーの詳細をログ出力
                if "object has no attribute" in str(e):
                    logger.warning("⚠️ WebSocketオブジェクトの属性エラーが発生しています")
                    logger.warning("MiPAライブラリのバージョン互換性を確認してください")
                    logger.warning("MiPAガイド: https://mipa.akarinext.org を参照してください")
                elif "connection" in str(e).lower():
                    logger.warning("⚠️ 接続エラーが発生しています")
                elif "timeout" in str(e).lower():
                    logger.warning("⚠️ タイムアウトエラーが発生しています")
                
                await asyncio.sleep(60)  # エラー時は1分待機
    
    def _get_misskey_host(self) -> str:
        """Misskeyホスト名を取得"""
        if hasattr(self.config, 'misskey_host') and self.config.misskey_host:
            return self.config.misskey_host
        elif hasattr(self.config, 'misskey_url') and self.config.misskey_url:
            # https://misskey.io から misskey.io を抽出
            return self.config.misskey_url.replace('https://', '').replace('http://', '').rstrip('/')
        else:
            raise ConfigError("Misskey host configuration not found")
    
    async def send_reply(self, note, message: str):
        """
        リプライ送信（元の投稿の公開範囲に合わせる）
        
        Args:
            note: リプライ対象のnoteオブジェクト
            message: 送信メッセージ
        """
        # 元の投稿の公開範囲を取得
        visibility = self._get_note_visibility(note)
        logger.debug(f"元の投稿の公開範囲: {visibility}")
        
        # まずリプライを試行
        try:
            if self.config.dry_run_mode:
                logger.info(f"🔧 [ドライラン] リプライ ({visibility}): {message[:100]}...")
                return True
            
            if not self.mipa_bot:
                logger.error("MiPA botインスタンスが初期化されていません")
                return False
            
            # 文字数制限チェック
            if len(message) > MessageLimits.MAX_LENGTH:
                logger.warning(f"メッセージが長すぎます: {len(message)}文字")
                message = message[:MessageLimits.TRUNCATE_LENGTH] + "..."
            
            # リプライとして送信
            await self.mipa_bot.client.note.action.create(
                text=message,
                visibility=visibility,
                reply_id=note.id
            )
            logger.info(f"✅ リプライ送信完了: {len(message)}文字")
            return True
            
        except Exception as e:
            error_str = str(e)
            
            # DMへのリプライエラーの場合は新規DMにフォールバック
            if "CANNOT_REPLY_TO_AN_INVISIBLE_NOTE" in error_str or "invisible Note" in error_str:
                logger.warning("DMへのリプライは不可 → 新規DMとして送信")
                return await self._send_dm(note, message)
            
            # その他のエラー
            logger.error(f"リプライエラー: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    async def _send_dm(self, note, message: str) -> bool:
        """
        DM送信（specified visibility用）
        
        Args:
            note: 元のnoteオブジェクト
            message: 送信メッセージ
            
        Returns:
            bool: 送信成功時True
        """
        try:
            if self.config.dry_run_mode:
                logger.info(f"🔧 [ドライラン] DM送信 (specified): {message[:100]}...")
                return True
            
            if not self.mipa_bot:
                logger.error("MiPA botインスタンスが初期化されていません")
                return False
            
            # 送信先ユーザーIDを取得（複数の方法を試行）
            user_id = None
            if hasattr(note, 'user_id'):
                user_id = note.user_id
            elif hasattr(note, 'user') and hasattr(note.user, 'id'):
                user_id = note.user.id
            
            if not user_id:
                logger.error(f"送信先ユーザーIDが取得できません: note type={type(note).__name__}")
                return False
            
            logger.info(f"DM送信先: user_id={user_id}")
            
            # 文字数制限チェック
            if len(message) > MessageLimits.MAX_LENGTH:
                logger.warning(f"メッセージが長すぎます: {len(message)}文字")
                message = message[:MessageLimits.TRUNCATE_LENGTH] + "..."
            
            # DMとして送信（reply_idなし、visible_user_ids指定）
            await self.mipa_bot.client.note.action.create(
                text=message,
                visibility='specified',
                visible_user_ids=[user_id]
            )
            logger.info(f"✅ DM送信完了 (specified)")
            return True
            
        except Exception as e:
            logger.error(f"DM送信エラー: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def _get_note_visibility(self, note) -> VisibilityType:
        """
        ノートの公開範囲を取得
        
        Args:
            note: Misskeyのnoteオブジェクト
            
        Returns:
            VisibilityType: 公開範囲
        """
        try:
            # 公開範囲の取得を試行
            if hasattr(note, 'visibility'):
                visibility = note.visibility
                logger.debug(f"ノートから公開範囲を取得: {visibility}")
                
                # 有効な公開範囲かチェック
                if Visibility.is_valid(visibility):
                    return visibility
                else:
                    logger.warning(f"無効な公開範囲: {visibility}, デフォルトで{Visibility.PUBLIC}を使用")
                    return Visibility.PUBLIC
            
            # 代替方法: 公開範囲の属性を確認
            if hasattr(note, 'local_only') and note.local_only:
                logger.debug("ローカルのみ投稿として検出")
                return Visibility.HOME
            
            # デフォルトはパブリック
            logger.debug("公開範囲が不明なため、デフォルトでpublicを使用")
            return Visibility.PUBLIC
            
        except Exception as e:
            logger.warning(f"公開範囲取得エラー: {e}, デフォルトでpublicを使用")
            return Visibility.PUBLIC
    
    async def _create_note(self, message: str, visibility: VisibilityType = Visibility.PUBLIC, 
                          reply_id: Optional[str] = None, context: str = "投稿") -> Optional[str]:
        """
        統一されたノート作成処理
        
        Args:
            message: 投稿メッセージ
            visibility: 公開範囲
            reply_id: リプライ先のノートID（指定時はリプライ投稿）
            context: 投稿コンテキスト（ログ用）
            
        Returns:
            Optional[str]: 投稿成功時はnote ID、失敗時はNone
        """
        try:
            if self.config.dry_run_mode:
                logger.info(f"🔧 [ドライラン] {context} ({visibility}): {message[:100]}...")
                return "dry_run_note_id"
            
            if not self.mipa_bot:
                raise BotClientError("MiPAボットが初期化されていません")
            
            # メッセージ長チェック（統一処理）
            original_length = len(message)
            if original_length > MessageLimits.MAX_LENGTH:
                logger.warning(f"メッセージが長すぎます: {original_length}文字 -> {MessageLimits.MAX_LENGTH}文字に制限")
                message = message[:MessageLimits.TRUNCATE_LENGTH] + "..."
                # メッセージ長制限エラーを記録
                raise MessageLimitError(
                    f"メッセージが長すぎます: {original_length}文字",
                    current_length=original_length,
                    max_length=MessageLimits.MAX_LENGTH
                )
            
            # 投稿パラメータを構築してAPIを呼び出し
            if reply_id:
                created_note = await self.mipa_bot.client.note.action.create(
                    text=message,
                    visibility=visibility,
                    reply_id=reply_id
                )
            else:
                created_note = await self.mipa_bot.client.note.action.create(
                    text=message,
                    visibility=visibility
                )
            
            # note IDを取得
            note_id = None
            if created_note:
                note_id = getattr(created_note, 'id', None) or (created_note.get('id') if isinstance(created_note, dict) else None)
            
            if note_id:
                logger.info(f"✅ {context}完了 ({visibility}): note_id={note_id}")
                # 定期投稿の場合は最後の投稿IDとして保存
                if context == "定期投稿":
                    self.last_posted_note_id = note_id
                    logger.info(f"最後の投稿ID保存: {note_id}")
                return note_id
            else:
                logger.warning(f"{context}完了したが、note IDが取得できませんでした")
                return None
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"{context}エラー: {e}")
            logger.debug(traceback.format_exc())
            
            # エラーが文字数制限によるものかチェック
            if "maxLength" in error_str or str(MessageLimits.MAX_LENGTH) in error_str:
                logger.warning("文字数制限エラーを検出しました")
                # 短縮版メッセージを送信
                if self.mipa_bot:
                    try:
                        # コンテキストに応じた短縮版メッセージ
                        if "定期投稿" in context or "今日のイベント" in context:
                            short_message = "今日のイベントが多すぎるため、一部のみ表示します。\n\n" + message[:MessageLimits.SHORT_MESSAGE_LENGTH] + "..."
                        elif "検索" in context:
                            short_message = "検索結果が多すぎるため、一部のみ表示します。\n\n" + message[:MessageLimits.SHORT_MESSAGE_LENGTH] + "..."
                        else:
                            short_message = "内容が多すぎるため、一部のみ表示します。\n\n" + message[:MessageLimits.SHORT_MESSAGE_LENGTH] + "..."
                        
                        if reply_id:
                            await self.mipa_bot.client.note.action.create(
                                text=short_message,
                                visibility=visibility,
                                reply_id=reply_id
                            )
                        else:
                            await self.mipa_bot.client.note.action.create(
                                text=short_message,
                                visibility=visibility
                            )
                        logger.info(f"✅ 短縮版{context}完了")
                        return True
                    except Exception as retry_error:
                        logger.error(f"短縮版{context}も失敗: {retry_error}")
                        return False
                else:
                    logger.error("MiPAボットが初期化されていないため、短縮版投稿をスキップ")
                    return False
            else:
                logger.error(f"その他のエラーのため、{context}をスキップ")
                return False
    
    async def send_note(self, message: str, visibility: VisibilityType = Visibility.PUBLIC):
        """
        ノート投稿（定期投稿用）
        
        Args:
            message: 投稿メッセージ
            visibility: 公開範囲 ('public', 'home', 'followers', 'specified')
        """
        return await self._create_note(message, visibility, context="定期投稿")
    
    async def disconnect(self):
        """WebSocket切断処理"""
        try:
            if self.mipa_bot:
                logger.info("BotClient切断処理開始")
                
                # MiPAボットの切断処理
                try:
                    if hasattr(self.mipa_bot, 'disconnect'):
                        await self.mipa_bot.disconnect() # type: ignore
                        logger.info("MiPAボット切断完了")
                    elif hasattr(self.mipa_bot, 'stop'):
                        await self.mipa_bot.stop() # type: ignore
                        logger.info("MiPAボット停止完了")
                except Exception as e:
                    # WebSocketNotConnectedエラーは正常な場合もある
                    if "WebSocketNotConnected" in str(e) or "not connected" in str(e).lower():
                        logger.info("WebSocketは既に切断済み")
                    else:
                        logger.error(f"ボット切断エラー: {e}")
                
                # 統一されたセッション管理を使用
                if self.session_manager:
                    await self.session_manager.close_all_sessions()
                else:
                    logger.warning("セッション管理が初期化されていません")
            
            # MiPAバックグラウンドタスクのキャンセル
            if self.mipa_task:
                logger.info("MiPAバックグラウンドタスクをキャンセルします")
                self.mipa_task.cancel()
                try:
                    await asyncio.wait_for(self.mipa_task, timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning("MiPAタスクのキャンセルがタイムアウトしました")
                except asyncio.CancelledError:
                    logger.info("MiPAタスクのキャンセル完了")
                except Exception as e:
                    logger.error(f"MiPAタスクキャンセル時エラー: {e}")
            
            # 接続状態をリセット
            self.mipa_bot = None
            self.mipa_task = None
            self.is_connected = False
            self.last_heartbeat = None
            
            logger.info("✅ 切断処理完了")
            
        except Exception as e:
            logger.error(f"切断処理エラー: {e}")
            logger.debug(traceback.format_exc())
    
    def get_client_status(self):
        """
        クライアント状態情報を取得
        
        Returns:
            Dict: 状態情報
        """
        # 稼働時間の計算
        uptime = 'N/A'
        if self.startup_time:
            from datetime import datetime
            uptime_delta = datetime.now() - self.startup_time
            uptime = str(uptime_delta).split('.')[0]  # 秒以下を除去
        
        # 応答時間の計算（簡易版）
        avg_response_time = 'N/A'
        max_response_time = 'N/A'
        min_response_time = 'N/A'
        
        # メモリ使用量の取得
        memory_usage = 'N/A'
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_usage = f"{memory_info.rss / (1024**2):.1f}MB"
        except:
            pass
        
        return {
            'client_type': 'mipa_websocket',
            'is_connected': self.is_connected,
            'connection_count': self.connection_count,
            'note_count': self.note_count,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'has_router': self.command_router is not None,
            'dry_run_mode': getattr(self.config, 'dry_run_mode', False),
            'debug_mode': getattr(self.config, 'debug_mode', False),
            'uptime': uptime,
            'startup_time': self.startup_time.isoformat() if self.startup_time else None,
            'avg_response_time': avg_response_time,
            'max_response_time': max_response_time,
            'min_response_time': min_response_time,
            'memory_usage': memory_usage,
            'last_connection': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
        }


class DSNSMiPABot(Bot):
    """
    DSNS Timeline Bot用のカスタムMiPAボット
    
    親BotClientインスタンスと連携してイベント処理を実行
    """
    
    def __init__(self, parent_client: BotClient):
        """
        カスタムボット初期化
        
        Args:
            parent_client: 親BotClientインスタンス
        """
        super().__init__()
        self.parent = parent_client
        
    async def _connect_channel(self):
        """ストリーミングチャンネルに接続"""
        try:
            # メンション通知を受信するためにmainチャンネルのみ接続
            await self.router.connect_channel(['main'])
            logger.info("✅ mainチャンネル接続完了（メンション通知受信用）")
            
        except Exception as e:
            logger.error(f"❌ mainチャンネル接続エラー: {e}")
            # フォールバック: 辞書形式で接続を試行
            try:
                await self.router.connect_channel({'main': None})
                logger.info("✅ mainチャンネル接続完了（フォールバック）")
            except Exception as fallback_error:
                logger.error(f"❌ mainチャンネル接続失敗（フォールバック）: {fallback_error}")
                raise
    
    async def on_ready(self, ws):
        """ボット準備完了時"""
        try:
            # 接続状態を更新
            self.parent.is_connected = True
            self.parent.connection_count += 1
            self.parent.startup_time = datetime.now()
            
            # ボット情報をログ出力
            bot_info = await self.client.get_me()
            logger.info(f"🚀 ボット準備完了: {bot_info.username}")
            logger.info(f"🆔 ボットID: {bot_info.id}")
            
            # メンション通知用チャンネルに接続
            await self._connect_channel()
            
            logger.info(f"✅ ボット完全接続完了: {bot_info.username}")
            
        except Exception as e:
            logger.error(f"ボット準備完了エラー: {e}")
            logger.debug(traceback.format_exc())
    
    async def on_reconnect(self, ws):
        """再接続時"""
        try:
            logger.info("🔄 ボット再接続開始")
            
            # 接続状態を更新
            self.parent.connection_count += 1
            self.parent.last_connection_attempt = datetime.now()
            
            # 再接続の原因を分析
            if self.parent.last_heartbeat:
                time_since_heartbeat = (datetime.now() - self.parent.last_heartbeat).total_seconds()
                logger.info(f"📊 最後のハートビートから{time_since_heartbeat:.0f}秒経過")
            
            # チャンネル再接続
            await self._connect_channel()
            
            # 接続状態を更新
            self.parent.is_connected = True
            self.parent.last_heartbeat = datetime.now()
            
            logger.info("✅ ボット再接続完了")
            
        except Exception as e:
            logger.error(f"再接続エラー: {e}")
            logger.debug(traceback.format_exc())
            
            # 接続失敗を記録
            self.parent.connection_failure_count += 1
            logger.error(f"❌ 再接続失敗 (失敗回数: {self.parent.connection_failure_count}/{self.parent.max_connection_failures})")
            
            # 失敗回数が上限に達した場合の警告
            if self.parent.connection_failure_count >= self.parent.max_connection_failures:
                logger.critical("🚨 再接続失敗回数が上限に達しました。手動での復旧が必要です。")
    
    async def on_note(self, note):
        """ノート受信時（通常の投稿）"""
        try:
            self.parent.note_count += 1
            self.parent.last_heartbeat = datetime.now()
            
            # デバッグ: ノート受信をログ出力
            logger.debug(f"📝 ノート受信: {getattr(note, 'id', 'unknown_id')}")
            
            # メンションが含まれているかチェック
            if hasattr(note, 'mentions') and note.mentions:
                logger.debug(f"🔍 メンション検出: {note.mentions}")
                await self._handle_mention(note)
            else:
                logger.debug("📝 メンションなしのノート")
                
        except Exception as e:
            logger.error(f"ノート処理エラー: {e}")
            logger.debug(traceback.format_exc())
    
    async def on_reply(self, note):
        """リプライ受信時"""
        try:
            self.parent.note_count += 1
            self.parent.last_heartbeat = datetime.now()
            
            # デバッグ: リプライ受信をログ出力
            logger.debug(f"💬 リプライ受信: {getattr(note, 'id', 'unknown_id')}")
            
            # リプライの場合はメンション処理を実行（リプライ先がボットかどうかは_handle_mentionでチェック）
            await self._handle_mention(note)
            
        except Exception as e:
            logger.error(f"リプライ処理エラー: {e}")
            logger.debug(traceback.format_exc())
    
    async def on_mention(self, notice):
        """メンション受信時（通知オブジェクト）"""
        try:
            self.parent.note_count += 1
            self.parent.last_heartbeat = datetime.now()
            
            # デバッグ: メンション受信をログ出力
            logger.debug(f"🎯 メンション受信: {getattr(notice, 'id', 'unknown_id')}")
            
            # メンション処理を実行
            await self._handle_mention(notice)
            
        except Exception as e:
            logger.error(f"メンション処理エラー: {e}")
            logger.debug(traceback.format_exc())
    
    async def _handle_mention(self, note):
        """メンション処理"""
        try:
            # NotificationNote対応: 実ノートを抽出
            actual_note = note.note if hasattr(note, 'note') and note.note else note
            logger.debug(f"🔍 メンション処理開始: note_id={getattr(actual_note, 'id', 'unknown')}")

            # ボット自身のメンションを除外
            bot_info = await self.client.get_me()
            logger.debug(f"🤖 ボットID: {bot_info.id}, ノートユーザーID: {getattr(actual_note, 'user_id', 'unknown')}")
            
            if actual_note.user_id == bot_info.id:
                logger.debug("🚫 ボット自身の投稿をスキップ")
                return

            # ユーザー情報を取得
            user_info = await self.client.user.action.get(user_id=actual_note.user_id)
            visibility = getattr(actual_note, 'visibility', 'unknown')
            
            # text属性の取得（MiPAのNote内部構造に対応）
            note_text = None
            # 方法1: 通常のtext属性
            if hasattr(actual_note, 'text') and actual_note.text:
                note_text = actual_note.text
            # 方法2: raw_noteから取得
            elif hasattr(actual_note, '_Note__raw_note'):
                raw_note = actual_note._Note__raw_note
                if isinstance(raw_note, dict):
                    note_text = raw_note.get('text', '')
            
            if note_text:
                preview = note_text[:50] + "..." if len(note_text) > 50 else note_text
            else:
                preview = "(テキストなし)"
            
            logger.info(f"💬 ノート受信: @{user_info.username} ({visibility}) - {preview}")

            # メンション検出（IDで比較）
            is_mention = False
            if hasattr(actual_note, 'mentions') and actual_note.mentions:
                logger.debug(f"🔍 メンションリスト: {actual_note.mentions}")
                for mention in actual_note.mentions:
                    logger.debug(f"🔍 メンション比較: {mention} == {bot_info.id}")
                    if mention == bot_info.id:
                        is_mention = True
                        break
            
            # リプライの場合は、リプライ先がボットかどうかもチェック
            if not is_mention and hasattr(actual_note, 'reply') and actual_note.reply:
                logger.debug(f"🔍 リプライ先チェック: {getattr(actual_note.reply, 'user_id', 'unknown')} == {bot_info.id}")
                if getattr(actual_note.reply, 'user_id', None) == bot_info.id:
                    is_mention = True
                    logger.debug("🎯 リプライによるメンション検出")
            
            if is_mention:
                logger.info(f"🎯 メンション検出: @{user_info.username}")
                # CommandRouterでコマンド処理
                if self.parent.command_router:
                    try:
                        result_message = await self.parent.command_router.route_message(actual_note, bot_info.username)
                        # リプライを送信
                        await self.parent.send_reply(actual_note, result_message)
                        logger.info(f"✅ リプライ送信完了: {len(result_message)}文字")
                    except Exception as route_error:
                        logger.error(f"コマンド処理エラー: {route_error}")
                        # エラー時のフォールバックメッセージ
                        error_message = "申し訳ございません。処理中にエラーが発生しました。"
                        await self.parent.send_reply(actual_note, error_message)
                else:
                    logger.warning("CommandRouterが設定されていません")
                    # CommandRouterがない場合のフォールバック
                    fallback_message = "申し訳ございません。現在コマンド処理が利用できません。"
                    await self.parent.send_reply(actual_note, fallback_message)
            else:
                logger.debug("❌ ボットへのメンションが見つかりませんでした")

            logger.info(f"✅ メンション処理完了: @{user_info.username}")

        except Exception as e:
            logger.error(f"メンション処理エラー: {e}")
            logger.debug(traceback.format_exc())
    
    async def on_error(self, error):
        """エラー発生時"""
        try:
            logger.error(f"WebSocketエラー: {error}")
            
            # エラー内容に応じた処理
            error_str = str(error).lower()
            
            if "connection" in error_str:
                logger.warning("🔌 接続エラーが発生しました")
                self.parent.connection_failure_count += 1
            elif "timeout" in error_str:
                logger.warning("⏰ タイムアウトエラーが発生しました")
                self.parent.connection_failure_count += 1
            elif "websocket" in error_str:
                logger.warning("🌐 WebSocketエラーが発生しました")
                self.parent.connection_failure_count += 1
            elif "ssl" in error_str:
                logger.warning("🔒 SSL/TLSエラーが発生しました")
                self.parent.connection_failure_count += 1
            else:
                logger.warning("❓ 不明なエラーが発生しました")
                self.parent.connection_failure_count += 1
            
            # 接続失敗回数の警告
            if self.parent.connection_failure_count >= self.parent.max_connection_failures:
                logger.critical("🚨 WebSocketエラーが多発しています。接続状態を確認してください。")
            
            # エラーの詳細情報をログ出力
            logger.debug(f"エラー詳細: {type(error).__name__}: {error}")
            logger.debug(f"現在の接続失敗回数: {self.parent.connection_failure_count}")
                
        except Exception as e:
            logger.error(f"エラーハンドリングエラー: {e}")
            logger.debug(traceback.format_exc())
    
    async def _send_startup_notification(self):
        """起動通知送信（オプション）"""
        try:
            if hasattr(self.parent.config, 'send_startup_notification') and self.parent.config.send_startup_notification:
                message = "🚀 DSNS Timeline Bot が起動しました"
                await self.parent.send_note(message, 'home')
                logger.info("起動通知を送信しました")
        except Exception as e:
            logger.error(f"起動通知送信エラー: {e}")


async def test_bot_client():
    """BotClientのテスト用関数"""
    logger.info("BotClientテスト開始")
    # テスト実装は省略
    logger.info("BotClientテスト完了")