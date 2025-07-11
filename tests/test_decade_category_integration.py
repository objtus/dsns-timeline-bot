#!/usr/bin/env python3
"""
年代別＋カテゴリ複合機能の統合テスト

フェーズ3の実装をテストするための包括的なテスト
"""

import asyncio
import logging
import sys
import os
import pytest
from pathlib import Path
from typing import Dict, Any

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from database import TimelineDatabase, TimelineEvent
from data_service import TimelineDataService
from command_router import CommandRouter
from handlers.decade_handler import DecadeHandler
from bot_client import BotClient

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockNote:
    """テスト用のMock Noteクラス"""
    def __init__(self, text: str):
        self.text = text

class MockBotClient(BotClient):
    """テスト用のMock BotClientクラス"""
    def __init__(self):
        super().__init__(None)  # 親クラスの初期化
        self.is_connected = True
        self.uptime = 3600.0
        self.message_count = 100
        self.error_count = 5

@pytest.mark.asyncio
async def test_decade_category_integration():
    """年代別＋カテゴリ複合機能の統合テスト"""
    print("🧪 年代別＋カテゴリ複合機能の統合テスト開始")
    
    try:
        # 設定初期化
        config = Config()
        
        # テスト用データベース初期化
        test_db_path = Path("test_decade_category.db")
        if test_db_path.exists():
            test_db_path.unlink()
        
        database = TimelineDatabase(test_db_path)
        
        # テストデータ投入
        test_events = [
            TimelineEvent(1995, 1, 15, "1995年: 分散SNSの黎明期", "dsns tech"),
            TimelineEvent(1995, 3, 20, "1995年: Web技術の発展", "web tech"),
            TimelineEvent(1996, 2, 10, "1996年: 暗号技術の進歩", "crypto tech"),
            TimelineEvent(1996, 5, 25, "1996年: ハッカー文化の台頭", "hacker culture"),
            TimelineEvent(1997, 8, 12, "1997年: P2P技術の誕生", "p2p tech"),
            TimelineEvent(1997, 11, 30, "1997年: メタバースの概念", "metaverse tech"),
            TimelineEvent(1998, 4, 18, "1998年: 炎上事件の発生", "flame incident"),
            TimelineEvent(1998, 7, 22, "1998年: ミーム文化の広がり", "meme culture"),
            TimelineEvent(1999, 1, 5, "1999年: 法律改正", "law"),
            TimelineEvent(1999, 12, 31, "1999年: 世紀末の技術革新", "tech"),
            
            TimelineEvent(2000, 2, 14, "2000年: Web2.0の始まり", "web tech"),
            TimelineEvent(2000, 6, 8, "2000年: ソーシャルネットワーク", "sns web"),
            TimelineEvent(2001, 3, 15, "2001年: セキュリティ事件", "hacker incident"),
            TimelineEvent(2001, 9, 11, "2001年: ネットワーク技術", "network tech"),
            TimelineEvent(2002, 5, 20, "2002年: 暗号通貨の概念", "crypto"),
            TimelineEvent(2002, 8, 30, "2002年: 分散システム", "dsns tech"),
            TimelineEvent(2003, 1, 10, "2003年: 掲示板システム", "bbs site"),
            TimelineEvent(2003, 7, 25, "2003年: アートとテクノロジー", "art tech"),
            TimelineEvent(2004, 4, 12, "2004年: 政治とネット", "pol web"),
            TimelineEvent(2004, 11, 8, "2004年: ツール開発", "tool tech"),
        ]
        
        for event in test_events:
            database.add_event(event)
        
        print(f"✅ テストデータ投入完了: {len(test_events)}件")
        
        # データサービス初期化
        data_service = TimelineDataService(config, database)
        
        # ボットクライアント初期化（Mock）
        bot_client = MockBotClient()
        
        # 年代別ハンドラー初期化
        decade_handler = DecadeHandler(config, database, data_service, bot_client)
        
        # コマンドルーター初期化
        command_router = CommandRouter(config, database, data_service, bot_client)
        
        # テストケース実行
        test_cases = [
            {
                "name": "1990年代の統計（カテゴリなし）",
                "command": "1990年代 統計",
                "expected_contains": ["1990年代の統計情報", "総イベント数: 10件"]
            },
            {
                "name": "1990年代の統計（dsns+tech）",
                "command": "1990年代 カテゴリ dsns+tech 統計",
                "expected_contains": ["1990年代の統計情報（カテゴリ: dsns, tech）", "総イベント数: 1件"]
            },
            {
                "name": "1990年代の統計（tech-meme）",
                "command": "1990年代 カテゴリ tech-meme 統計",
                "expected_contains": ["1990年代の統計情報（カテゴリ: tech, 除外: meme）", "総イベント数: 6件"]
            },
            {
                "name": "2000年代の代表（カテゴリなし）",
                "command": "2000年代 代表",
                "expected_contains": ["2000年代の主要な出来事"]
            },
            {
                "name": "2000年代の代表（web+tech）",
                "command": "2000年代 カテゴリ web+tech 代表",
                "expected_contains": ["2000年代の主要な出来事（カテゴリ: web, tech）"]
            },
            {
                "name": "1990年代の概要（カテゴリなし）",
                "command": "1990年代 概要",
                "expected_contains": ["1990年代"]
            },
            {
                "name": "1990年代の概要（dsns）",
                "command": "1990年代 カテゴリ dsns 概要",
                "expected_contains": ["**カテゴリフィルタ**: dsns"]
            },
            {
                "name": "存在しないカテゴリ",
                "command": "1990年代 カテゴリ nonexistent 統計",
                "expected_contains": ["イベントは見つかりませんでした"]
            },
            {
                "name": "複雑な除外条件",
                "command": "1990年代 カテゴリ tech-meme+incident 統計",
                "expected_contains": ["1990年代の統計情報（カテゴリ: tech, 除外: meme, incident）"]
            }
        ]
        
        passed = 0
        failed = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 テストケース {i}: {test_case['name']}")
            print(f"   コマンド: {test_case['command']}")
            
            try:
                # コマンド解析
                command = command_router.parse_command(test_case['command'])
                if not command:
                    print(f"   ❌ コマンド解析失敗")
                    failed += 1
                    continue
                
                print(f"   解析結果: {command['type']} - {command.get('sub_type')} - カテゴリ={command.get('categories')} - 除外={command.get('exclude_categories')}")
                
                # ハンドラー実行
                mock_note = MockNote(test_case['command'])
                result = await decade_handler.handle(mock_note, command)
                
                print(f"   結果: {len(result)}文字")
                print(f"   内容: {result}")
                
                # 期待値チェック
                all_expected_found = True
                for expected in test_case['expected_contains']:
                    if expected not in result:
                        print(f"   ❌ 期待値 '{expected}' が見つかりません")
                        all_expected_found = False
                
                if all_expected_found:
                    print(f"   ✅ テスト成功")
                    passed += 1
                else:
                    print(f"   ❌ テスト失敗")
                    failed += 1
                    
            except Exception as e:
                print(f"   ❌ テスト実行エラー: {e}")
                failed += 1
        
        # データベース機能の直接テスト
        print(f"\n🔍 データベース機能の直接テスト")
        
        # 年代別＋カテゴリ検索テスト
        events = database.get_events_by_decade_and_categories(1995, 1999, ["dsns", "tech"])
        print(f"   1990年代 dsns+tech: {len(events)}件")
        
        events = database.get_events_by_decade_and_categories(1995, 1999, ["tech"], ["meme"])
        print(f"   1990年代 tech-meme: {len(events)}件")
        
        # 年代別カテゴリ統計テスト
        stats = database.get_decade_category_statistics(1995, 1999)
        print(f"   1990年代カテゴリ統計: {stats['total_events']}件, {stats['unique_categories']}カテゴリ")
        
        # 結果サマリー
        print(f"\n📊 テスト結果サマリー")
        print(f"   成功: {passed}件")
        print(f"   失敗: {failed}件")
        print(f"   成功率: {passed/(passed+failed)*100:.1f}%")
        
        if failed == 0:
            print(f"\n🎉 全てのテストが成功しました！")
            return True
        else:
            print(f"\n⚠️  {failed}件のテストが失敗しました")
            return False
            
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        return False
    finally:
        # テスト用データベース削除
        if test_db_path.exists():
            test_db_path.unlink()
        print(f"🧹 テスト用データベース削除完了")

if __name__ == "__main__":
    success = asyncio.run(test_decade_category_integration())
    sys.exit(0 if success else 1) 