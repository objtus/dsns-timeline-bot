#!/usr/bin/env python3
"""
データベース内の未変換リンクをMarkdown形式に変換
"""

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database import TimelineDatabase

def convert_links_in_db():
    config = Config()
    database = TimelineDatabase(config.database_path)
    update_count = 0

    with database._get_connection() as conn:
        cursor = conn.cursor()
        
        # まず、未変換のリンクを含むレコードを特定
        print("未変換リンクを含むレコードを検索中...")
        cursor.execute("SELECT rowid, content FROM timeline_events WHERE content LIKE '%LINKSTART%'")
        rows = cursor.fetchall()
        
        print(f"未変換リンクを含むレコード数: {len(rows)}")
        
        for row in rows:
            rowid = row[0]
            content = row[1]
            
            print(f"変換対象レコード (rowid: {rowid}): {content[:100]}...")
            
            # 正規表現でMarkdownリンクに変換
            new_content = re.sub(
                r'LINKSTART(.*?)LINKMIDDLE(.*?)LINKEND',
                r'[\2](\1)',
                content
            )
            
            if new_content != content:
                # 変換後の内容が既存のレコードと重複しないかチェック
                cursor.execute("""
                    SELECT COUNT(*) FROM timeline_events 
                    WHERE year = (SELECT year FROM timeline_events WHERE rowid = ?)
                    AND month = (SELECT month FROM timeline_events WHERE rowid = ?)
                    AND day = (SELECT day FROM timeline_events WHERE rowid = ?)
                    AND content = ?
                    AND rowid != ?
                """, (rowid, rowid, rowid, new_content, rowid))
                
                duplicate_count = cursor.fetchone()[0]
                
                if duplicate_count == 0:
                    # 重複がなければ更新
                    cursor.execute(
                        "UPDATE timeline_events SET content = ? WHERE rowid = ?",
                        (new_content, rowid)
                    )
                    update_count += 1
                    print(f"変換完了 (rowid: {rowid})")
                else:
                    # 重複がある場合は削除（既に変換済みのレコードが存在する）
                    cursor.execute("DELETE FROM timeline_events WHERE rowid = ?", (rowid,))
                    print(f"重複のため削除 (rowid: {rowid})")

        conn.commit()
    
    print(f"変換・更新したレコード数: {update_count}")
    print("データベース修正完了")

if __name__ == "__main__":
    convert_links_in_db()