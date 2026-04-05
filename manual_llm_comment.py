#!/usr/bin/env python3
"""
手動でLLMコメントを投稿するスクリプト
"""

import asyncio
import logging
import sys
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def manual_llm_comment(note_id: str):
    """指定されたnote_idに対してLLMコメントを投稿"""
    try:
        from config import Config
        from database import TimelineDatabase
        from data_service import TimelineDataService
        from llm_service import LLMService
        from llm_commentary import LLMCommentaryService
        from bot_client import BotClient
        
        logger.info("=== 手動LLMコメント投稿開始 ===")
        logger.info(f"元投稿ID: {note_id}")
        
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
        
        # note_idを設定
        bot_client.last_posted_note_id = note_id
        
        # LLMコメント生成・投稿
        logger.info("LLMコメント生成・投稿開始...")
        success = await commentary_service.post_commentary(bot_client)
        
        if success:
            logger.info("✅✅✅ 手動LLMコメント投稿成功！ ✅✅✅")
        else:
            logger.error("❌ 手動LLMコメント投稿失敗")
        
        # 切断
        await bot_client.disconnect()
        logger.info("✅ BotClient切断完了")
        
        return success
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使用方法: python3 manual_llm_comment.py <note_id>")
        print("例: python3 manual_llm_comment.py ain5g8e4y8vf4ty7")
        sys.exit(1)
    
    note_id = sys.argv[1]
    success = asyncio.run(manual_llm_comment(note_id))
    sys.exit(0 if success else 1)
