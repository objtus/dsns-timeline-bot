#!/usr/bin/env python3
"""
LLMコメント生成テストスクリプト（投稿なし）

プロンプトを調整しながら、生成される文章を確認できます。
"""

import sys
import asyncio
import logging
from datetime import datetime, date
from typing import Optional

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_llm_generation(target_date: Optional[date] = None, show_prompt: bool = True):
    """LLMコメント生成をテスト（投稿なし）"""
    try:
        from config import Config
        from database import TimelineDatabase
        from data_service import TimelineDataService
        from llm_service import LLMService
        from llm_commentary import LLMCommentaryService
        
        # 初期化
        config = Config()
        database = TimelineDatabase(config.database_path)
        data_service = TimelineDataService(config, database)
        llm_service = LLMService(config)
        commentary_service = LLMCommentaryService(config, database, data_service, llm_service)
        
        # 対象日の設定
        if target_date is None:
            target_date = datetime.now()
        elif isinstance(target_date, date):
            target_date = datetime.combine(target_date, datetime.min.time())
        
        month = target_date.month
        day = target_date.day
        
        print("=" * 80)
        print(f"LLMコメント生成テスト: {month}月{day}日")
        print("=" * 80)
        print()
        
        # イベント取得
        events = database.get_events_by_date(month, day)
        
        if not events:
            print(f"❌ {month}月{day}日のイベントが見つかりません")
            return None
        
        print(f"📅 イベント数: {len(events)}件")
        print()
        
        # イベント一覧を表示
        print("📋 イベント一覧:")
        print("-" * 80)
        for i, event in enumerate(events, 1):
            print(f"{i}. {event.year}年: {event.content[:100]}...")
        print()
        
        # プロンプトを構築して表示
        if show_prompt:
            import re
            
            # イベントテキストを構築（commentary_service内と同じロジック）
            event_texts = []
            for event in events:
                year = getattr(event, 'year', '????')
                content = getattr(event, 'content', '')
                content = content.strip() if content else ''
                # Markdown形式のURL除去
                content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
                if content:
                    event_texts.append(f"{year}年: {content}")
            
            events_summary = "\n".join(event_texts)
            prompt = f"""今日（{month}月{day}日）の分散SNS関連年表のできごとを読んで、感想を述べてください。

【今日のできごと】
{events_summary}

以下の観点で200-500文字程度で感想を述べてください：
- これらのできごとの歴史的意義や面白さ
- 分散SNSの発展への影響
- 個人的な驚きや発見

感想："""
            
            print("📄 LLMに送信されるプロンプト:")
            print("=" * 80)
            print(prompt)
            print("=" * 80)
            print(f"📊 プロンプト文字数: {len(prompt)}文字")
            print()
        
        # コメント生成
        logger.info("LLMコメント生成開始...")
        start_time = datetime.now()
        
        commentary = await commentary_service.generate_commentary(target_date)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if commentary:
            print("✅ 生成成功！")
            print(f"⏱️  生成時間: {duration:.1f}秒")
            print(f"📝 文字数: {len(commentary)}文字")
            print()
            print("=" * 80)
            print("生成されたコメント:")
            print("=" * 80)
            print(commentary)
            print("=" * 80)
            print()
            
            # ハッシュタグ付きバージョンも表示
            commentary_with_hashtag = f"{commentary}\n\n#今日はなんの日LLM感想"
            print("📝 ハッシュタグ付きバージョン（実際の投稿）:")
            print("=" * 80)
            print(commentary_with_hashtag)
            print("=" * 80)
            print(f"📊 合計文字数: {len(commentary_with_hashtag)}文字")
            print()
            
            return commentary
        else:
            print("❌ 生成失敗")
            return None
            
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LLMコメント生成テスト（投稿なし）')
    parser.add_argument('--date', type=str, help='対象日付（MM/DD形式、例: 02/14）')
    parser.add_argument('--hide-prompt', action='store_true', help='プロンプトを非表示にする')
    parser.add_argument('--count', type=int, default=1, help='生成回数（デフォルト: 1）')
    
    args = parser.parse_args()
    
    # 日付の解析
    target_date = None
    if args.date:
        try:
            month, day = map(int, args.date.split('/'))
            year = datetime.now().year
            target_date = date(year, month, day)
        except Exception as e:
            print(f"❌ 日付の形式が正しくありません: {args.date}")
            print("正しい形式: MM/DD（例: 02/14）")
            sys.exit(1)
    
    # 非同期実行
    async def run_tests():
        # 複数回生成
        for i in range(args.count):
            if args.count > 1:
                print()
                print(f"{'=' * 80}")
                print(f"第{i+1}回目の生成")
                print(f"{'=' * 80}")
                print()
            
            commentary = await test_llm_generation(target_date, show_prompt=not args.hide_prompt)
            
            if commentary is None:
                sys.exit(1)
            
            if i < args.count - 1:
                print("\n\n")
    
    asyncio.run(run_tests())

if __name__ == '__main__':
    main()
