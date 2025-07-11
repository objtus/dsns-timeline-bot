#!/usr/bin/env python3
"""
リンクパース処理のテスト
"""

import re
import html

def test_link_parsing():
    """リンクパース処理をテスト"""
    
    # テスト用のHTML（複数リンクを含む例）
    test_html = '''<li class="event">
  <a href="https://example1.com">リンク1</a>の後に
  <a href="https://example2.com">リンク2</a>があります。
  さらに<a href="https://example3.com">リンク3</a>も。
</li>'''

    print('=== 元のHTML ===')
    print(test_html)

    # 現在の実装をテスト
    content = test_html

    # 1. liタグの内容のみを抽出
    li_match = re.search(r'<li[^>]*>(.*?)</li>', content, re.DOTALL)
    if li_match:
        content = li_match.group(1)
    else:
        content = content

    print('\n=== liタグ抽出後 ===')
    print(content)

    # 2. 改行コードとタブを空白に変換（HTMLの構造由来の改行を除去）
    content = re.sub(r'[\r\n\t]+', ' ', content)

    # 3. 複数の空白を単一に変換
    content = re.sub(r'\s{2,}', ' ', content)

    print('\n=== 空白処理後 ===')
    print(content)

    # 4. HTMLリンクを保持しつつテキスト抽出
    # <a>タグをテンポラリ形式に変換
    content = re.sub(r'<a\s+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', 
                    r'LINKSTART\1LINKMIDDLE\2LINKEND', content, flags=re.IGNORECASE)

    print('\n=== リンク変換後 ===')
    print(content)

    # 5. 他のHTMLタグは通常通り処理
    # <span class="str">を太字に変換
    content = re.sub(r'<span\s+class=["\']str["\'][^>]*>([^<]+)</span>', 
                    r'**\1**', content, flags=re.IGNORECASE)

    # 6. <br>タグを改行に変換
    content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)

    # 7. 残りのHTMLタグを削除
    content = re.sub(r'<[^>]+>', '', content)

    print('\n=== HTMLタグ削除後 ===')
    print(content)

    # 8. テンポラリ形式をMarkdownリンクに変換
    content = re.sub(r'LINKSTART([^L]+)LINKMIDDLE([^L]+)LINKEND', 
                    r'[\2](\1)', content)

    print('\n=== 最終結果 ===')
    print(content)

    # 9. HTMLエンティティをデコード
    content = html.unescape(content)

    # 10. 前後の空白を除去
    content = content.strip()

    print('\n=== 最終処理後 ===')
    print(content)
    
    # テスト結果の検証
    assert '[' in content, "Markdownリンクが含まれていません"
    assert '](' in content, "正しいMarkdownリンク形式ではありません"
    assert content.count('[') == content.count(']'), "リンクの括弧が一致しません"
    assert content.count('(') == content.count(')'), "リンクの括弧が一致しません"

if __name__ == "__main__":
    test_link_parsing()
    print(f"\n=== テスト完了 ===") 