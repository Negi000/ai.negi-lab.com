#!/usr/bin/env python3
"""
楽天アフィリエイトリンク修正バッチ

古い形式（アフィリエイト報酬が発生しない）:
  https://search.rakuten.co.jp/search/mall/{keyword}/?scid={AFFILIATE_ID}

新しい形式（正しいアフィリエイトリンク）:
  https://hb.afl.rakuten.co.jp/hgc/{AFFILIATE_ID}/?pc={URLエンコードした楽天URL}&m={URLエンコードした楽天URL}

使い方:
  python fix_rakuten_links.py           # ドライラン（変更内容を表示するだけ）
  python fix_rakuten_links.py --apply   # 実際に変更を適用
"""

import re
import sys
from pathlib import Path
from urllib.parse import quote, unquote

# 設定
RAKUTEN_AFFILIATE_ID = "5000cbfd.5f52567b.5000cbff.924460a4"
CONTENT_DIR = Path(__file__).parent / "content" / "posts"

# 古い形式のパターン
# https://search.rakuten.co.jp/search/mall/{keyword}/?scid={AFFILIATE_ID}
OLD_PATTERN = re.compile(
    r'https://search\.rakuten\.co\.jp/search/mall/([^/?]+)(?:/\?|\?)scid=' + re.escape(RAKUTEN_AFFILIATE_ID),
    re.IGNORECASE
)


def convert_to_new_format(match: re.Match) -> str:
    """古い形式のURLを新しい形式に変換"""
    encoded_keyword = match.group(1)
    
    # 楽天検索ページのURL（末尾スラッシュなし）
    search_url = f"https://search.rakuten.co.jp/search/mall/{encoded_keyword}/"
    
    # URLエンコード
    encoded_url = quote(search_url, safe='')
    
    # 新しいアフィリエイトリンク
    new_url = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_AFFILIATE_ID}/?pc={encoded_url}&m={encoded_url}"
    
    return new_url


def process_file(file_path: Path, apply: bool = False) -> tuple[int, list[str]]:
    """
    ファイル内の楽天リンクを処理
    
    Returns:
        (修正件数, 変更内容のリスト)
    """
    content = file_path.read_text(encoding='utf-8')
    
    # マッチを検索
    matches = list(OLD_PATTERN.finditer(content))
    
    if not matches:
        return 0, []
    
    changes = []
    new_content = content
    
    # 後ろからマッチを処理（位置がずれないように）
    for match in reversed(matches):
        old_url = match.group(0)
        new_url = convert_to_new_format(match)
        
        # キーワードをデコードして表示用に
        keyword = unquote(match.group(1))
        changes.insert(0, f"  キーワード: {keyword}")
        changes.insert(1, f"    旧: {old_url[:80]}...")
        changes.insert(2, f"    新: {new_url[:80]}...")
        
        new_content = new_content[:match.start()] + new_url + new_content[match.end():]
    
    if apply and new_content != content:
        file_path.write_text(new_content, encoding='utf-8')
    
    return len(matches), changes


def main():
    apply = '--apply' in sys.argv
    
    if apply:
        print("=" * 60)
        print("楽天アフィリエイトリンク修正バッチ（適用モード）")
        print("=" * 60)
    else:
        print("=" * 60)
        print("楽天アフィリエイトリンク修正バッチ（ドライランモード）")
        print("実際に変更を適用するには --apply オプションを付けてください")
        print("=" * 60)
    
    print()
    
    if not CONTENT_DIR.exists():
        print(f"エラー: ディレクトリが見つかりません: {CONTENT_DIR}")
        return 1
    
    # .mdファイルを検索
    md_files = list(CONTENT_DIR.glob("*.md"))
    print(f"対象ファイル数: {len(md_files)}")
    print()
    
    total_fixes = 0
    fixed_files = 0
    
    for file_path in sorted(md_files):
        count, changes = process_file(file_path, apply=apply)
        
        if count > 0:
            fixed_files += 1
            total_fixes += count
            
            status = "修正済み" if apply else "修正予定"
            print(f"[{status}] {file_path.name} ({count}件)")
            for change in changes:
                print(change)
            print()
    
    print("-" * 60)
    print(f"合計: {fixed_files}ファイル / {total_fixes}件のリンク")
    
    if not apply and total_fixes > 0:
        print()
        print("変更を適用するには以下を実行してください:")
        print("  python fix_rakuten_links.py --apply")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
