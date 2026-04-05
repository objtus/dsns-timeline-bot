#!/usr/bin/env python3
"""
LLMコメント機能のテストスクリプト
"""

import asyncio
import logging
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_llm_commentary():
    """LLMコメント機能をテスト"""
    try:
        from config import Config
        from database import TimelineDatabase
        from data_service import TimelineDataService
        from llm_service import LLMService
        from llm_commentary import LLMCommentaryService
        from bot_client import BotClient
        
        logger.info("=== LLMコメント機能テスト開始 ===")
        
        # 初期化
        config = Config()
        database = TimelineDatabase(config.database_path)
        data_service = TimelineDataService(config, database)
        llm_service = LLMService(config)
        bot_client = BotClient(config)
        commentary_service = LLMCommentaryService(config, database, data_service, llm_service)
        
        logger.info("✅ 初期化完了")
        
        # BotClient接続
        await bot_client.connect()
        logger.info("✅ BotClient接続開始")
        
        # 接続完了を待機（最大10秒）
        for i in range(10):
            await asyncio.sleep(1)
            if bot_client.is_connected:
                logger.info("✅ BotClient接続完了")
                break
        else:
            logger.warning("BotClient接続タイムアウト（継続します）")
        
        # 今日のイベントを取得
        now = datetime.now()
        message = data_service.get_today_events_message(now.date())
        
        if not message:
            logger.error("今日のイベントが取得できませんでした")
            return
        
        logger.info(f"今日のイベント取得: {len(message)}文字")
        
        # テスト投稿を作成（home公開範囲）
        logger.info("テスト用年表投稿を作成中...")
        note_id = await bot_client.send_note(
            message + "\n\n(LLMコメントテスト用投稿)",
            visibility='home'
        )
        
        if not note_id:
            logger.error("テスト投稿の作成に失敗しました")
            await bot_client.disconnect()
            return
        
        logger.info(f"✅ テスト投稿作成完了: note_id={note_id}")
        
        # BotClientに投稿IDを設定
        bot_client.last_posted_note_id = note_id
        
        # 少し待機
        logger.info("5秒待機...")
        await asyncio.sleep(5)
        
        # LLMコメントを生成して投稿
        logger.info("LLMコメント生成・投稿開始...")
        success = await commentary_service.post_commentary(bot_client)
        
        if success:
            logger.info("✅✅✅ LLMコメントテスト成功！ ✅✅✅")
        else:
            logger.error("❌ LLMコメントテスト失敗")
        
        # 切断
        await bot_client.disconnect()
        logger.info("✅ BotClient切断完了")
        
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_llm_commentary())
