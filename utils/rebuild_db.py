#!/usr/bin/env python3
"""
データベース再構築スクリプト
"""

import asyncio
import logging
from data_service import TimelineDataService
from config import Config
from database import TimelineDatabase

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def rebuild_database():
    """データベースを再構築"""
    try:
        print("=== データベース再構築開始 ===")
        
        # 設定とデータベース初期化
        config = Config()
        database = TimelineDatabase(config.database_path)
        
        # データサービスでデータ更新
        async with TimelineDataService(config, database) as service:
            print("データ取得・更新中...")
            result = await service.update_timeline_data()
            
            print(f"更新完了:")
            print(f"  新規追加: {result.get('new_count', result.get('added', 0))}件")
            print(f"  更新: {result.get('updated_count', result.get('updated', 0))}件")
            print(f"  総件数: {result.get('total_count', result.get('total', 0))}件")
            
            # ヘルスチェック
            health = await service.health_check()
            print(f"ヘルスチェック: {health['status']}")
            
        print("=== データベース再構築完了 ===")
        
    except Exception as e:
        logger.error(f"データベース再構築エラー: {e}")
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    asyncio.run(rebuild_database()) 