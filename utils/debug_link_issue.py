#!/usr/bin/env python3
"""
リンク変換問題の詳細調査
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database import TimelineDatabase
import re

def debug_link_issue():
    """問題のあるリンクを詳細調査"""
    
    config = Config()
    database = TimelineDatabase(config.database_path)
    
    # 2008年07月02日のidenti.caイベントを検索
    with database._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT *, rowid FROM timeline_events 
            WHERE month = 7 AND day = 2 AND year = 2008
            ORDER BY rowid
        ''')
        rows = cursor.fetchall()
    
    print(f"2008年07月02日のイベント数: {len(rows)}")
    
    for i, row in enumerate(rows):
        print(f"\n=== イベント {i+1} ===")
        # print(f"ID: {row['id']}")
        print(f"年: {row['year']}")
        print(f"月: {row['month']}")
        print(f"日: {row['day']}")
        print(f"内容: {row['content']}")
        
        # LINKSTART...LINKMIDDLE...LINKENDの出現回数をカウント
        link_pattern_count = row['content'].count('LINKSTART')
        print(f"LINKSTART出現回数: {link_pattern_count}")
        
        # 正規Markdownリンクの数をカウント
        markdown_link_count = row['content'].count('[')
        print(f"Markdownリンク数: {markdown_link_count}")
        
        # 問題のある部分を特定
        if 'LINKSTART' in row['content']:
            print("⚠️ 未変換のリンクパターンが検出されました")
            
            # 正規表現でLINKSTART...LINKMIDDLE...LINKENDを検索
            pattern = r'LINKSTART(.*?)LINKMIDDLE(.*?)LINKEND'
            matches = re.findall(pattern, row['content'])
            
            print(f"未変換リンク数: {len(matches)}")
            for j, (url, text) in enumerate(matches):
                print(f"  未変換リンク {j+1}:")
                print(f"    URL: {url}")
                print(f"    テキスト: {text}")
                print(f"    期待されるMarkdown: [{text}]({url})")

    with database._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(timeline_events);")
        columns = cursor.fetchall()
        print("カラム一覧:")
        for col in columns:
            print(col)

def convert_links_in_db():
    config = Config()
    database = TimelineDatabase(config.database_path)
    update_count = 0

    with database._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, content FROM timeline_events")
        rows = cursor.fetchall()

        for row in rows:
            rowid = row['rowid']
            content = row['content']
            # 変換前にパターンが含まれているかチェック
            if 'LINKSTART' in content:
                # 正規表現でMarkdownリンクに変換
                new_content = re.sub(
                    r'LINKSTART(.*?)LINKMIDDLE(.*?)LINKEND',
                    r'[\2](\1)',
                    content
                )
                if new_content != content:
                    cursor.execute(
                        "UPDATE timeline_events SET content = ? WHERE rowid = ?",
                        (new_content, rowid)
                    )
                    update_count += 1

        conn.commit()
    print(f"変換・更新したレコード数: {update_count}")

if __name__ == "__main__":
    debug_link_issue()
    convert_links_in_db() 