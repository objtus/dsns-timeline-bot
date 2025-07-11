#!/usr/bin/env python3
"""
定期投稿の公開範囲変更テストスクリプト
"""

import asyncio
import os
import pytest
from datetime import datetime
from config import Config
from database import TimelineDatabase
from data_service import TimelineDataService
from handlers.today_handler import TodayHandler
from bot_client import BotClient

@pytest.mark.asyncio
@pytest.mark.parametrize("visibility", ['public', 'home', 'followers', 'specified'])
async def test_visibility_change(visibility: str):
    """公開範囲変更のテスト"""
    print(f"=== 定期投稿公開範囲変更テスト ({visibility}) ===")
    
    # テスト用の環境変数を設定
    test_time = datetime.now()
    test_post_time = f"{test_time.hour:02d}:{(test_time.minute + 1) % 60:02d}"
    
    os.environ['POST_TIMES'] = test_post_time
    os.environ['SCHEDULED_POST_VISIBILITY'] = visibility
    os.environ['DRY_RUN_MODE'] = 'true'
    
    print(f"テスト投稿時刻: {test_post_time}")
    print(f"テスト公開範囲: {visibility}")
    
    try:
        # コンポーネント初期化
        config = Config()
        database = TimelineDatabase(config.database_path)
        data_service = TimelineDataService(config, database)
        bot_client = BotClient(config)
        handler = TodayHandler(config, database, data_service, bot_client)
        
        print(f"設定確認 - 投稿時刻: {config.post_times}")
        print(f"設定確認 - 公開範囲: {config.scheduled_post_visibility}")
        
        # 定期投稿実行
        success = await handler.post_scheduled_today_event()
        
        print(f"定期投稿テスト結果: {success}")
        
        # クリーンアップ
        await bot_client.disconnect()
        
        assert success, f"公開範囲 {visibility} での定期投稿が失敗しました"
        
    except Exception as e:
        print(f"テストエラー: {e}")
        pytest.fail(f"公開範囲 {visibility} でのテストが例外で失敗: {e}")

@pytest.mark.asyncio
async def test_all_visibilities():
    """全公開範囲をテスト"""
    visibilities = ['public', 'home', 'followers', 'specified']
    results = {}
    
    for visibility in visibilities:
        print(f"\n{'='*50}")
        try:
            await test_visibility_change(visibility)
            results[visibility] = True
        except Exception as e:
            print(f"公開範囲 {visibility} でエラー: {e}")
            results[visibility] = False
        print(f"{'='*50}")
    
    # 結果サマリー
    print(f"\n{'='*60}")
    print("📊 公開範囲テスト結果サマリー")
    print(f"{'='*60}")
    
    for visibility, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{status}: {visibility}")
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    print(f"\n総合結果: {success_count}/{total_count} 公開範囲で成功")
    
    if success_count == total_count:
        print("🎉 全公開範囲でテスト成功！定期投稿機能は正常に動作します。")
    else:
        print("⚠️  一部の公開範囲でテストが失敗しました。")
    
    assert success_count == total_count, f"{success_count}/{total_count} の公開範囲でテストが失敗しました"

if __name__ == "__main__":
    asyncio.run(test_all_visibilities()) 