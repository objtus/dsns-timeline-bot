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
        
        # 接続状態管理
        self.is_connected = False
        self.last_heartbeat: Optional[datetime] = None
        self.connection_count = 0
        self.note_count = 0
        self.startup_time: Optional[datetime] = None
        self.mipa_task = None  # MiPAバックグラウンドタスク
        
        logger.info("BotClient初期化完了")
    
    def set_command_router(self, router):
        """
        CommandRouterを設定
        
        Args:
            router: CommandRouterインスタンス
        """
        self.command_router = router
        logger.info("CommandRouter設定完了")
    
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
            
            # MiPAのstart()をバックグラウンドタスクで実行
            loop = asyncio.get_running_loop()
            self.mipa_task = loop.create_task(self.mipa_bot.start(ws_url, token))
            logger.info("MiPA start()をバックグラウンドで実行開始")
            # すぐにreturnし、メインループへ制御を返す
            
        except Exception as e:
            logger.error(f"WebSocket接続エラー: {e}")
            logger.debug(traceback.format_exc())
            raise NetworkError(f"WebSocket接続に失敗しました: {e}", url=ws_url)
    
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
        
        # 統一された投稿処理を使用
        return await self._create_note(
            message=message,
            visibility=visibility,
            reply_id=note.id,
            context="リプライ"
        )
    
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
                          reply_id: Optional[str] = None, context: str = "投稿") -> bool:
        """
        統一されたノート作成処理
        
        Args:
            message: 投稿メッセージ
            visibility: 公開範囲
            reply_id: リプライ先のノートID（指定時はリプライ投稿）
            context: 投稿コンテキスト（ログ用）
            
        Returns:
            bool: 投稿成功時True
        """
        try:
            if self.config.dry_run_mode:
                logger.info(f"🔧 [ドライラン] {context} ({visibility}): {message[:100]}...")
                return True
            
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
            
            # 投稿パラメータを構築
            if reply_id:
                await self.mipa_bot.client.note.action.create(
                    text=message,
                    visibility=visibility,
                    reply_id=reply_id
                )
            else:
                await self.mipa_bot.client.note.action.create(
                    text=message,
                    visibility=visibility
                )
            logger.info(f"✅ {context}完了 ({visibility})")
            return True
            
        except Exception as e:
            logger.error(f"{context}エラー: {e}")
            logger.debug(traceback.format_exc())
            
            # エラーが文字数制限によるものかチェック
            if "maxLength" in str(e) or str(MessageLimits.MAX_LENGTH) in str(e):
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
                
                # セッション切断処理
                try:
                    # MiPAの正しいセッション管理: API.core.close_sessionを使用
                    if hasattr(self.mipa_bot, 'core') and self.mipa_bot.core:
                        await self.mipa_bot.core.close_session() # type: ignore
                        logger.info("MiPA APIセッション切断完了")
                    
                    # フォールバック: グローバルHTTPSession
                    try:
                        from mipa.http import HTTPSession
                        if hasattr(HTTPSession, 'close_session'):
                            await HTTPSession.close_session()
                            logger.info("MiPAグローバルHTTPSession切断完了")
                    except Exception:
                        pass  # グローバルセッションは失敗しても問題なし
                        
                except Exception as e:
                    logger.error(f"セッション切断エラー: {e}")
            
            # MiPAバックグラウンドタスクのキャンセル
            if self.mipa_task:
                logger.info("MiPAバックグラウンドタスクをキャンセルします")
                self.mipa_task.cancel()
                try:
                    await self.mipa_task
                except asyncio.CancelledError:
                    logger.info("MiPAタスクのキャンセル完了")
                except Exception as e:
                    logger.error(f"MiPAタスクキャンセル時エラー: {e}")
            
            self.is_connected = False
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
            await self._connect_channel()
            logger.info("✅ ボット再接続完了")
            
        except Exception as e:
            logger.error(f"再接続エラー: {e}")
            logger.debug(traceback.format_exc())
    
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
            
            # text属性の安全な取得
            note_text = getattr(actual_note, 'text', '')
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
            if "connection" in str(error).lower():
                logger.warning("接続エラーが発生しました")
            elif "timeout" in str(error).lower():
                logger.warning("タイムアウトエラーが発生しました")
            else:
                logger.warning("不明なエラーが発生しました")
                
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