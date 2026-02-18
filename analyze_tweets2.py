#!/usr/bin/env python3
"""追加分析: 曜日・日別・フックパターン"""
import csv, re
from collections import Counter, defaultdict
from statistics import mean
from datetime import datetime

CSV_PATH = r'c:\Users\vocal\Downloads\account_analytics_content_2026-01-22_2026-02-18.csv'

f = open(CSV_PATH, 'r', encoding='utf-8')
reader = csv.DictReader(f)
rows = []
for row in reader:
    row['imp'] = int(row['インプレッション数'])
    row['eng'] = int(row['エンゲージメント'])
    row['url_click'] = int(row['URLのクリック数'])
    row['likes'] = int(row['いいね'])
    row['text'] = row['ポスト本文']
    row['date_str'] = row['日付']
    rows.append(row)
f.close()

# Classify
main = [r for r in rows if '#' in r['text']]
reply = [r for r in rows if '#' not in r['text']]

# Day of week
dow_names = {'Mon':'月','Tue':'火','Wed':'水','Thu':'木','Fri':'金','Sat':'土','Sun':'日'}
dow_data = defaultdict(list)
date_data = defaultdict(list)
for r in rows:
    try:
        dt = datetime.strptime(r['date_str'], '%a, %b %d, %Y')
        dow_short = r['date_str'][:3]
        dow_data[dow_short].append(r['imp'])
        date_data[dt.strftime('%m/%d')].append(r)
    except Exception as e:
        pass

print('=== 曜日別分析 ===')
for dow in ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']:
    if dow in dow_data:
        imps = dow_data[dow]
        print(f'  {dow_names[dow]}曜: 平均imp={mean(imps):>6.1f}, ツイート数={len(imps):>3}')

print()
print('=== 日別ツイート数とインプレッション ===')
for d in sorted(date_data.keys()):
    tweets = date_data[d]
    total_imp = sum(r['imp'] for r in tweets)
    avg_imp = mean([r['imp'] for r in tweets])
    main_count = sum(1 for r in tweets if '#' in r['text'])
    reply_count = len(tweets) - main_count
    print(f'  {d}: {len(tweets):>3}件(M:{main_count:>2},R:{reply_count:>2}) 合計imp={total_imp:>5} 平均imp={avg_imp:>5.1f}')

print()
print('=== フックテンプレート分析 ===')
template_map = defaultdict(list)
for r in main:
    first_line = r['text'].split('\n')[0].strip()
    if 'このツール、使ってみたら' in first_line:
        template_map['このツール、使ってみたら...'].append(r)
    elif 'ガチでヤバくない' in first_line:
        template_map['まって、これガチでヤバくない？'].append(r)
    elif '生産性爆上がり' in first_line:
        template_map['ガチで生産性爆上がりした'].append(r)
    elif '全員見て' in first_line or '開発者全員' in first_line:
        template_map['開発者全員見て。これ神。'].append(r)
    elif '知らないと損' in first_line or '知らなかったら損' in first_line:
        template_map['知らないと損するやつ'].append(r)
    elif 'ついに' in first_line:
        template_map['ついに〜が〜'].append(r)
    elif '使い倒した' in first_line or '3日間使い倒し' in first_line:
        template_map['使い倒した結果'].append(r)
    elif '最初は「また' in first_line:
        template_map['最初は「また便利ツールか」と…'].append(r)
    elif '業界的に' in first_line:
        template_map['業界的にかなりインパクト'].append(r)
    elif '1時間悩んだ' in first_line:
        template_map['1時間悩んだエラー、一発解決'].append(r)
    elif '導入コストと効果' in first_line:
        template_map['導入コストと効果を計算'].append(r)
    elif 'SIer' in first_line:
        template_map['SIer時代の苦労は...'].append(r)
    elif '巨大AI' in first_line or 'AI企業' in first_line:
        template_map['巨大AI企業の〜'].append(r)
    else:
        template_map['その他(ユニーク)'].append(r)

print('テンプレート別パフォーマンス:')
for template, tweets in sorted(template_map.items(), key=lambda x: mean([t['imp'] for t in x[1]]), reverse=True):
    avg = mean([t['imp'] for t in tweets])
    avg_eng = mean([t['eng'] for t in tweets])
    avg_url = mean([t['url_click'] for t in tweets])
    print(f'  [{len(tweets):>3}回] 平均imp={avg:>5.0f} 平均eng={avg_eng:>4.1f} 平均url={avg_url:.2f} | {template}')

print()
print('=== リプライテンプレート分析 ===')
reply_template = defaultdict(list)
for r in reply:
    text = r['text']
    if '初心者でも分かるように' in text:
        reply_template['初心者でも分かるように解説'].append(r)
    elif '使い方のコツも紹介' in text:
        reply_template['使い方のコツも紹介'].append(r)
    elif '本当に使えるの？' in text:
        reply_template['「本当に使えるの？」検証した'].append(r)
    elif '1週間ガチで使い倒した' in text:
        reply_template['1週間ガチで使い倒した'].append(r)
    elif '最初は「また便利ツールか」' in text:
        reply_template['最初は「また便利ツールか」…'].append(r)
    elif '実際に触ってみた' in text:
        reply_template['実際に触ってみた感想'].append(r)
    elif 'ハマりポイント' in text:
        reply_template['ハマりポイントまとめ'].append(r)
    else:
        reply_template['その他'].append(r)

print('リプライテンプレート別URLクリック:')
for template, tweets in sorted(reply_template.items(), key=lambda x: mean([t['url_click'] for t in x[1]]), reverse=True):
    avg_url = mean([t['url_click'] for t in tweets])
    avg_imp = mean([t['imp'] for t in tweets])
    url_nonzero = sum(1 for t in tweets if t['url_click'] > 0)
    print(f'  [{len(tweets):>3}回] 平均url={avg_url:.2f} 平均imp={avg_imp:>5.1f} クリック有={url_nonzero:>2} | {template}')

# Period comparison with corrected date parsing
print()
print('=== 期間比較（1週間ごと）===')
week_data = defaultdict(list)
for r in rows:
    try:
        dt = datetime.strptime(r['date_str'], '%a, %b %d, %Y')
        if dt.day <= 7:
            week = f'{dt.month}/01-07'
        elif dt.day <= 14:
            week = f'{dt.month}/08-14'
        elif dt.day <= 21:
            week = f'{dt.month}/15-21'
        else:
            week = f'{dt.month}/22-{dt.day}'
        week_data[f'{dt.month:02d}_{week}'].append(r)
    except:
        pass

for wk in sorted(week_data.keys()):
    tweets = week_data[wk]
    avg_imp = mean([r['imp'] for r in tweets])
    avg_eng = mean([r['eng'] for r in tweets])
    main_c = sum(1 for r in tweets if '#' in r['text'])
    print(f'  {wk}: {len(tweets):>3}件(M:{main_c:>2}) 平均imp={avg_imp:>5.1f} 平均eng={avg_eng:.1f}')
