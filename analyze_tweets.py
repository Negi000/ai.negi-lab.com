#!/usr/bin/env python3
"""X Analytics CSV 詳細分析スクリプト"""
import csv
import re
from collections import Counter, defaultdict
from statistics import mean, median
from datetime import datetime

CSV_PATH = r'c:\Users\vocal\Downloads\account_analytics_content_2026-01-22_2026-02-18.csv'

# Read CSV
rows = []
with open(CSV_PATH, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

print(f'=== 基本統計 ===')
print(f'総ツイート数: {len(rows)}')

# Parse metrics
for r in rows:
    r['imp'] = int(r['インプレッション数'])
    r['likes'] = int(r['いいね'])
    r['eng'] = int(r['エンゲージメント'])
    r['bm'] = int(r['ブックマーク'])
    r['rt'] = int(r['リポスト'])
    r['reply_count'] = int(r['返信'])
    r['profile'] = int(r['プロフィールへのアクセス数'])
    r['detail'] = int(r['詳細のクリック数'])
    r['url_click'] = int(r['URLのクリック数'])
    r['hashtag_click'] = int(r['ハッシュタグのクリック数'])
    r['text'] = r['ポスト本文']
    r['date'] = r['日付']
    r['follow'] = int(r['新しいフォロー'])
    r['share'] = int(r['共有された回数\\'])
    # Engagement rate
    r['eng_rate'] = (r['eng'] / r['imp'] * 100) if r['imp'] > 0 else 0

# Classify tweet types: Main (has hashtags/↓) vs Reply (has t.co URL, shorter)
main_tweets = []
reply_tweets = []
for r in rows:
    if '#' in r['text'] and '↓' in r['text']:
        main_tweets.append(r)
    elif 'https://t.co/' in r['text'] and '#' not in r['text']:
        reply_tweets.append(r)
    elif '#' in r['text']:
        main_tweets.append(r)
    else:
        reply_tweets.append(r)

print(f'メインツイート: {len(main_tweets)}')
print(f'リプライツイート: {len(reply_tweets)}')

# Overall stats
all_imps = [r['imp'] for r in rows]
main_imps = [r['imp'] for r in main_tweets]
reply_imps = [r['imp'] for r in reply_tweets]
print(f'\n=== インプレッション ===')
print(f'全体: 平均={mean(all_imps):.1f}, 中央値={median(all_imps)}, 最高={max(all_imps)}, 最低={min(all_imps)}, 合計={sum(all_imps)}')
print(f'メイン: 平均={mean(main_imps):.1f}, 中央値={median(main_imps)}, 最高={max(main_imps)}')
print(f'リプライ: 平均={mean(reply_imps):.1f}, 中央値={median(reply_imps)}, 最高={max(reply_imps)}')

# Engagement rate
print(f'\n=== エンゲージメント ===')
main_eng = [r['eng'] for r in main_tweets]
reply_eng = [r['eng'] for r in reply_tweets]
main_likes = [r['likes'] for r in main_tweets]
reply_likes = [r['likes'] for r in reply_tweets]
main_eng_rates = [r['eng_rate'] for r in main_tweets]
reply_eng_rates = [r['eng_rate'] for r in reply_tweets]
print(f'メイン: 平均エンゲージ={mean(main_eng):.1f}, 平均いいね={mean(main_likes):.2f}, 平均ER={mean(main_eng_rates):.2f}%')
print(f'リプライ: 平均エンゲージ={mean(reply_eng):.1f}, 平均いいね={mean(reply_likes):.2f}, 平均ER={mean(reply_eng_rates):.2f}%')

# URL clicks
main_url = [r['url_click'] for r in main_tweets]
reply_url = [r['url_click'] for r in reply_tweets]
reply_url_nonzero = sum(1 for r in reply_tweets if r['url_click'] > 0)
print(f'\n=== URLクリック ===')
print(f'メイン: 合計={sum(main_url)}, 平均={mean(main_url):.2f}')
print(f'リプライ: 合計={sum(reply_url)}, 平均={mean(reply_url):.2f}')
print(f'URLクリック>0のリプライ: {reply_url_nonzero} / {len(reply_tweets)}')

# Top 15 by impressions
print(f'\n=== インプレッション TOP15 ===')
sorted_rows = sorted(rows, key=lambda x: x['imp'], reverse=True)
for i, r in enumerate(sorted_rows[:15]):
    text_short = r['text'][:60].replace('\n', ' ')
    ttype = 'M' if r in main_tweets else 'R'
    print(f'{i+1:>2}. [{ttype}] imp={r["imp"]:>4} like={r["likes"]} eng={r["eng"]:>2} url={r["url_click"]} bm={r["bm"]} | {text_short}')

# Bottom 15 by impressions (main only)
print(f'\n=== インプレッション WORST15 (メインのみ) ===')
sorted_main = sorted(main_tweets, key=lambda x: x['imp'])
for i, r in enumerate(sorted_main[:15]):
    text_short = r['text'][:60].replace('\n', ' ')
    print(f'{i+1:>2}. imp={r["imp"]:>4} like={r["likes"]} eng={r["eng"]:>2} url={r["url_click"]} | {text_short}')

# Hashtag analysis
print(f'\n=== ハッシュタグ分析 ===')
hashtag_perf = defaultdict(list)
for r in main_tweets:
    tags = re.findall(r'#\S+', r['text'])
    for tag in tags:
        hashtag_perf[tag].append(r['imp'])
print('ハッシュタグ別平均インプレッション (使用回数5以上):')
for tag, imps in sorted(hashtag_perf.items(), key=lambda x: mean(x[1]) if len(x[1]) >= 5 else 0, reverse=True):
    if len(imps) >= 5:
        print(f'  {tag}: 平均={mean(imps):.0f}, 使用={len(imps)}回')

# Hook pattern analysis
print(f'\n=== フックパターン分析 ===')
hook_patterns = defaultdict(list)
for r in main_tweets:
    # Extract first line as hook
    first_line = r['text'].split('\n')[0].strip()
    # Normalize: remove emojis and specific product names for pattern matching
    hook_patterns[first_line].append(r)

# Find repeated hooks
print('同一フック使用回数 (2回以上):')
repeated = [(hook, tweets) for hook, tweets in hook_patterns.items() if len(tweets) >= 2]
repeated.sort(key=lambda x: len(x[1]), reverse=True)
for hook, tweets in repeated[:15]:
    avg_imp = mean([t['imp'] for t in tweets])
    hook_short = hook[:55]
    print(f'  [{len(tweets):>2}回] 平均imp={avg_imp:>5.0f} | {hook_short}')

# Time analysis (hour of day)
print(f'\n=== 時間帯別分析 ===')
hour_data = defaultdict(list)
for r in rows:
    try:
        dt = datetime.strptime(r['date'], '%Y-%m-%d %H:%M %z')
        hour_data[dt.hour].append(r['imp'])
    except:
        pass
for h in sorted(hour_data.keys()):
    imps = hour_data[h]
    print(f'  {h:>2}時: 平均imp={mean(imps):>6.1f}, ツイート数={len(imps):>3}')

# Day of week analysis
print(f'\n=== 曜日別分析 ===')
dow_names = ['月', '火', '水', '木', '金', '土', '日']
dow_data = defaultdict(list)
for r in rows:
    try:
        dt = datetime.strptime(r['date'], '%Y-%m-%d %H:%M %z')
        dow_data[dt.weekday()].append(r['imp'])
    except:
        pass
for d in sorted(dow_data.keys()):
    imps = dow_data[d]
    print(f'  {dow_names[d]}曜: 平均imp={mean(imps):>6.1f}, ツイート数={len(imps):>3}')

# Period comparison: old vs new format
print(f'\n=== 期間比較 (フォーマット変更前後) ===')
old_tweets = [r for r in main_tweets if r['date'] < '2026-02-10']
new_tweets = [r for r in main_tweets if r['date'] >= '2026-02-10']
if old_tweets:
    print(f'旧フォーマット (~Feb 9): {len(old_tweets)}件, 平均imp={mean([r["imp"] for r in old_tweets]):.1f}, 平均eng={mean([r["eng"] for r in old_tweets]):.1f}')
if new_tweets:
    print(f'新フォーマット (Feb 10~): {len(new_tweets)}件, 平均imp={mean([r["imp"] for r in new_tweets]):.1f}, 平均eng={mean([r["eng"] for r in new_tweets]):.1f}')

# Follow generation
print(f'\n=== フォロー獲得 ===')
total_follows = sum(r['follow'] for r in rows)
follow_tweets = [(r, r['follow']) for r in rows if r['follow'] > 0]
print(f'合計新規フォロー: {total_follows}')
print(f'フォロー獲得ツイート数: {len(follow_tweets)}')
for r, f in sorted(follow_tweets, key=lambda x: x[1], reverse=True)[:10]:
    text_short = r['text'][:50].replace('\n', ' ')
    print(f'  +{f}フォロー, imp={r["imp"]} | {text_short}')

# Bookmark analysis
print(f'\n=== ブックマーク分析 ===')
bm_tweets = [(r, r['bm']) for r in rows if r['bm'] > 0]
print(f'ブックマークされたツイート: {len(bm_tweets)}件')
for r, b in sorted(bm_tweets, key=lambda x: x[1], reverse=True)[:10]:
    text_short = r['text'][:50].replace('\n', ' ')
    print(f'  bm={b}, imp={r["imp"]} | {text_short}')

# Content length analysis
print(f'\n=== 文字数分析 ===')
main_lens = [len(r['text']) for r in main_tweets]
reply_lens = [len(r['text']) for r in reply_tweets]
print(f'メイン: 平均={mean(main_lens):.0f}文字, 中央値={median(main_lens)}文字, 最長={max(main_lens)}文字')
print(f'リプライ: 平均={mean(reply_lens):.0f}文字, 中央値={median(reply_lens)}文字')

# Correlation: length vs impressions for main
short = [r for r in main_tweets if len(r['text']) < 100]
mid = [r for r in main_tweets if 100 <= len(r['text']) < 140]
long = [r for r in main_tweets if len(r['text']) >= 140]
if short:
    print(f'短文(<100字): {len(short)}件, 平均imp={mean([r["imp"] for r in short]):.0f}')
if mid:
    print(f'中文(100-139字): {len(mid)}件, 平均imp={mean([r["imp"] for r in mid]):.0f}')
if long:
    print(f'長文(140字+): {len(long)}件, 平均imp={mean([r["imp"] for r in long]):.0f}')

# Reply tweet URL click detail
print(f'\n=== リプライツイートのURLクリック詳細 ===')
reply_with_url = [r for r in reply_tweets if r['url_click'] > 0]
reply_without_url = [r for r in reply_tweets if r['url_click'] == 0]
print(f'URLクリックあり: {len(reply_with_url)}件')
print(f'URLクリックなし: {len(reply_without_url)}件')
if reply_with_url:
    print('URLクリック獲得リプライ:')
    for r in sorted(reply_with_url, key=lambda x: x['url_click'], reverse=True)[:10]:
        text_short = r['text'][:60].replace('\n', ' ')
        print(f'  url_click={r["url_click"]}, imp={r["imp"]} | {text_short}')
