#!/usr/bin/env python3
"""
修正したリンクパース処理のテスト
"""

import re
import html

def test_fixed_link_parsing():
    """修正したリンクパース処理をテスト"""
    
    # 実際のデータで問題が発生していたHTML例
    test_html = '''<li class="event">
  <a href="https://web.archive.org/web/20211109130335/https://twitter.com/taqueshix/status/641699062576648192">LSD を 0.008mg 筋肉注射</a>され、
  <a href="https://web.archive.org/web/20211002190210/https://twitter.com/chocoramastudio/status/1124282979662983168">その様子を 3 時間録音した後 30 分に編集したものが放送</a>された。
  さらに<a href="https://www.sogetsu.or.jp/about/artcenter/">草月アートセンター</a>や
  <a href="http://www.cmn.hs.h.kyoto-u.ac.jp/CMN20/PDF/otani_article.pdf">シネマ57 の定例会</a>などで上映されている。
</li>'''

    print('=== 修正前の問題のあるHTML ===')
    print(test_html)

    # 修正した実装をテスト
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

    # 8. 修正されたテンポラリ形式をMarkdownリンクに変換
    content = re.sub(r'LINKSTART(.*?)LINKMIDDLE(.*?)LINKEND', 
                    r'[\2](\1)', content)

    print('\n=== 修正後の最終結果 ===')
    print(content)

    # 9. HTMLエンティティをデコード
    content = html.unescape(content)

    # 10. 前後の空白を除去
    content = content.strip()

    print('\n=== 最終処理後 ===')
    print(content)
    
    # リンクの詳細分析
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    print(f"\n=== 抽出されたリンク ===")
    print(f"リンク数: {len(links)}")
    for i, (text, url) in enumerate(links):
        print(f"  {i+1}. [{text}]({url})")
    
    # テスト結果の検証
    assert len(links) > 0, "リンクが抽出されていません"
    assert all('http' in url for _, url in links), "無効なURLが含まれています"

def compare_old_vs_new():
    """修正前後の比較テスト"""
    
    # 問題があった実際のデータ例
    problematic_text = '''LINKSTARThttps://web.archive.org/web/20211109130335/https://twitter.com/taqueshix/status/641699062576648192LINKMIDDLELSD を 0.008mg 筋肉注射LINKENDされ、[その様子を 3 時間録音した後 30 分に編集したものが放送](https://web.archive.org/web/20211002190210/https://twitter.com/chocoramastudio/status/1124282979662983168)された。'''
    
    print("=== 修正前後の比較 ===")
    print(f"問題のあるテキスト: {problematic_text}")
    
    # 修正前の正規表現（問題あり）
    old_result = re.sub(r'LINKSTART([^L]+)LINKMIDDLE([^L]+)LINKEND', 
                       r'[\2](\1)', problematic_text)
    print(f"\n修正前の結果: {old_result}")
    
    # 修正後の正規表現
    new_result = re.sub(r'LINKSTART(.*?)LINKMIDDLE(.*?)LINKEND', 
                       r'[\2](\1)', problematic_text)
    print(f"\n修正後の結果: {new_result}")
    
    # 結果の比較
    old_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', old_result)
    new_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', new_result)
    
    print(f"\n修正前のリンク数: {len(old_links)}")
    print(f"修正後のリンク数: {len(new_links)}")
    
    if len(new_links) > len(old_links):
        print("✅ 修正成功: より多くのリンクが正しく変換されました")
    else:
        print("❌ 修正失敗: リンク数に改善がありません")

if __name__ == "__main__":
    print("修正したリンクパース処理のテスト...")
    test_fixed_link_parsing()
    
    print("\n" + "="*50)
    compare_old_vs_new() 