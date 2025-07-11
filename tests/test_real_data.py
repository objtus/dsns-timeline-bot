#!/usr/bin/env python3
"""
実際のデータベースから複数リンクを含むイベントをテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database import TimelineDatabase
import re

def find_events_with_multiple_links():
    """複数リンクを含むイベントを検索"""
    
    config = Config()
    database = TimelineDatabase(config.database_path)
    
    # データベースから全イベントを取得
    with database._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM timeline_events ORDER BY year, month, day')
        rows = cursor.fetchall()
    
    print(f"総イベント数: {len(rows)}")
    
    # 複数リンクを含むイベントを検索
    multiple_link_events = []
    
    for row in rows:
        content = row['content']
        # Markdownリンクの数をカウント
        link_count = content.count('[')
        
        if link_count > 1:
            multiple_link_events.append({
                'year': row['year'],
                'month': row['month'],
                'day': row['day'],
                'content': content,
                'link_count': link_count
            })
    
    print(f"複数リンクを含むイベント数: {len(multiple_link_events)}")
    
    # 最初の5件を詳細表示
    for i, event in enumerate(multiple_link_events[:5]):
        print(f"\n=== イベント {i+1} ===")
        print(f"日付: {event['year']}年{event['month']:02d}月{event['day']:02d}日")
        print(f"リンク数: {event['link_count']}")
        print(f"内容: {event['content']}")
        
        # リンクの詳細分析
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', event['content'])
        print(f"抽出されたリンク:")
        for j, (text, url) in enumerate(links):
            print(f"  {j+1}. [{text}]({url})")
    
    return multiple_link_events

def test_link_parsing_with_real_data():
    """実際のデータでリンクパース処理をテスト"""
    
    config = Config()
    database = TimelineDatabase(config.database_path)
    
    # 複数リンクを含むイベントを1件取得
    with database._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM timeline_events 
            WHERE content LIKE '%[%]%' 
            AND (LENGTH(content) - LENGTH(REPLACE(content, '[', ''))) > 1
            LIMIT 1
        ''')
        row = cursor.fetchone()
    
    if not row:
        print("複数リンクを含むイベントが見つかりませんでした")
        return
    
    print("=== 実際のデータでのテスト ===")
    print(f"日付: {row['year']}年{row['month']:02d}月{row['day']:02d}日")
    print(f"HTML: {row['html_content'][:200]}...")
    print(f"処理済み内容: {row['content']}")
    
    # リンクの詳細分析
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', row['content'])
    print(f"抽出されたリンク数: {len(links)}")
    for i, (text, url) in enumerate(links):
        print(f"  {i+1}. [{text}]({url})")

if __name__ == "__main__":
    print("複数リンクを含むイベントの検索...")
    events = find_events_with_multiple_links()
    
    if events:
        print(f"\n実際のデータでのリンクパース処理テスト...")
        test_link_parsing_with_real_data()
    else:
        print("複数リンクを含むイベントが見つかりませんでした") 