---
title: "Claude APIで有料AI要約サービスを自作する方法"
date: 2026-04-12T00:00:00+09:00
slug: "build-your-own-ai-news-curator-claude-api"
cover:
  image: "/images/posts/2026-04-12-build-your-own-ai-news-curator-claude-api.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude API 使い方"
  - "Python 自動化 ニュース"
  - "サブスク 代替 自作"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 指定したRSSフィードやニュースサイトから情報を取得し、自分の関心事に沿ってフィルタリング・要約してDiscordやSlackに通知するPythonスクリプト。
- 月額3,000円程度のAIニュースレターサービスや、情報収集効率化ツールの代わりを自前で構築します。
- 前提知識：Pythonの基本的な文法（変数、関数、pipでのライブラリ導入）がわかること。
- 必要なもの：Anthropic APIキー（Claude 3.5 Sonnet推奨）、Python 3.10以上の環境。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">Raspberry Pi 5</strong>
<p style="color:#555;margin:8px 0;font-size:14px">24時間稼働のニュース監視スクリプトを自宅で安価に運用するなら、ラズパイ5が最高のサーバーになります</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=Raspberry%20Pi%205%20%E3%82%B9%E3%82%BF%E3%83%BC%E3%82%BF%E3%83%BC%E3%82%AD%E3%83%83%E3%83%88&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRaspberry%2520Pi%25205%2520%25E3%2582%25B9%25E3%2582%25BF%25E3%2583%25BC%25E3%2582%25BF%25E3%2583%25BC%25E3%2582%25AD%25E3%2583%2583%25E3%2583%2588%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRaspberry%2520Pi%25205%2520%25E3%2582%25B9%25E3%2582%25BF%25E3%2583%25BC%25E3%2582%25BF%25E3%2583%25BC%25E3%2582%25AD%25E3%2583%2583%25E3%2583%2588%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

世の中にはAIを活用したキュレーションサービスがあふれていますが、その多くが月額20ドル以上のサブスクリプションを要求します。
しかし、その実態は「RSSで記事を取得してLLMに投げているだけ」のものが少なくありません。
APIを直接叩けば、1回の実行コストは0.05ドル（約7円）以下に抑えられ、フィルタリングの精度も自分好みに100%カスタマイズできます。

Redditで話題になっていた「議論に明け暮れるエンジニアを横目に、サクッと自作アプリで3つのサブスクを解約した男」になるための、最も実用的な第一歩がこれです。
汎用的なツールは「万人向け」に作られていますが、自分の仕事に必要な情報だけを抜き出すには、自分でコードを書くのが結局一番速くて安上がりです。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。記事のスクレイピングとRSSの解析、そしてClaude APIとの通信用です。

```bash
pip install anthropic feedparser beautifulsoup4 requests
```

`feedparser`はRSSフィードの解析に、`beautifulsoup4`は取得したHTMLから余計な広告やタグを除去して「本文だけ」を抽出するために使用します。
LLMに渡すトークン数を節約し、コストを抑えるために、この前処理が非常に重要です。

⚠️ **落とし穴:**
`requests`でサイトを取得しようとすると、一部のサイト（Cloudflare導入済みサイトなど）から403エラーでブロックされることがあります。
その場合は、`headers`にブラウザを装飾したUser-Agentを設定する必要がありますが、まずは基本構成で進めます。

## Step 2: 基本の設定

APIキーなどの機密情報は、コードに直書きせず環境変数から読み込むようにしましょう。
SIer時代、コードにキーを直書きしてコミットし、本番環境を危険に晒した新人を見てきましたが、プロなら徹底すべきポイントです。

```python
import os
import feedparser
import requests
from bs4 import BeautifulSoup
from anthropic import Anthropic

# APIキーは環境変数から取得
# Windows: set ANTHROPIC_API_KEY=your_key
# Mac/Linux: export ANTHROPIC_API_KEY=your_key
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# あなたが追いたいニュースのRSS URL
RSS_URLS = [
    "https://feeds.feedburner.com/TheHackersNews",
    "https://techcrunch.com/feed/"
]

# 自分の「関心事」を定義
MY_INTERESTS = "LLM, ローカルLLM, GPU, NVIDIA, Python, 自動化"
```

MY_INTERESTSには、あなたが今仕事で必要としているキーワードを具体的に入れてください。
Claudeはこのキーワードを元に、大量のニュースの中から「読む価値があるもの」を選別します。

## Step 3: 動かしてみる

まずは、RSSから記事のタイトルとURLを取得し、その中身を抽出する最小限のロジックを組みます。

```python
def get_article_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # 記事本文が含まれそうなタグを抽出（サイトに合わせて調整が必要）
        paragraphs = soup.find_all('p')
        return "\n".join([p.get_text() for p in paragraphs[:10]]) # 最初の10段落に限定して節約
    except Exception as e:
        return f"エラー: {e}"

# 1件だけテスト
feed = feedparser.parse(RSS_URLS[0])
first_entry = feed.entries[0]
content = get_article_text(first_entry.link)

print(f"Title: {first_entry.title}")
print(f"Content snippet: {content[:100]}...")
```

### 期待される出力

```
Title: New Linux Malware targeting Servers...
Content snippet: A new strain of malware has been discovered targeting Linux-based servers globally. The attackers...
```

ここで「本文が正しく取れているか」を確認してください。
もしHTMLタグが混ざりすぎている場合は、`soup.get_text()`の処理を見直す必要があります。

## Step 4: 実用レベルにする

ここからが本番です。取得した本文をClaudeに渡し、「私の関心に合致するか」を判定させ、合致する場合のみ要約を作成させます。
これが有料サービスのコア機能を自作する部分です。

```python
def analyze_article(title, content):
    prompt = f"""
    以下の記事は私の関心事（{MY_INTERESTS}）に関連していますか？
    関連がある場合のみ、以下の形式で出力してください。関連がない場合は「SKIP」とだけ出力してください。

    【判定】: 関連あり
    【重要度】: 1-10で評価
    【要約】: 3行で簡潔に説明
    【理由】: なぜ私の関心に関連すると判断したか

    記事タイトル: {title}
    記事本文: {content}
    """

    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=500,
        temperature=0, # 分析精度を上げるためランダム性を排除
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

# 全RSSフィードをスキャン
for url in RSS_URLS:
    feed = feedparser.parse(url)
    for entry in feed.entries[:3]: # テスト用に各フィード3件まで
        full_text = get_article_text(entry.link)
        result = analyze_article(entry.title, full_text)

        if "SKIP" not in result:
            print(f"--- 注目記事 ---\n{result}\nURL: {entry.link}\n")
```

このコードのポイントは `temperature=0` です。
クリエイティブな文章は不要で、論理的なフィルタリングが欲しいため、モデルの振れ幅を最小限に抑えています。
また、プロンプトで「SKIP」を定義することで、不要な情報の出力を防ぎ、APIコストと確認の手間を削減しています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| 403 Forbidden | サイト側のスクレイピング対策 | `requests.get`の引数に`headers={'User-Agent': 'Mozilla/5.0'}`を追加する |
| AuthenticationError | APIキーの読み込み失敗 | `os.environ`ではなく一時的に直書きして確認するか、シェルを再起動する |
| Context Window Exceeded | 記事が長すぎる | `paragraphs[:10]`のように、渡すテキスト量を制限する。Claude 3.5 Sonnetなら200kトークンまで入るが、コスト節約のために絞るのが吉 |

## 次のステップ

この記事の内容をマスターしたら、次は「定期実行」と「通知」の自動化に挑戦してください。
私はこのスクリプトをGitHub Actionsで3時間おきに実行し、自分のDiscordサーバーの専用チャンネルにWebhookで投稿するようにしています。
これで、わざわざニュースサイトを巡回する時間はゼロになりました。

また、抽出したデータをSQLiteなどのデータベースに保存し、1週間分をまとめて「今週のトレンドレポート」としてClaudeに再構成させるのも面白いでしょう。
APIコストは月額に換算しても数百円程度です。
20ドルのサブスクを払う代わりに、その予算でRTX 4090の電気代を賄う方が、AIエンジニアとしては健全な投資だと私は思います。

## よくある質問

### Q1: Claude 3 OpusではなくSonnetを使う理由は？

実務上のコスパと速度です。要約やフィルタリングというタスクにおいて、Sonnet 3.5はOpusに匹敵する、あるいは上回る精度を見せつつ、料金は1/5程度で済みます。レスポンスも圧倒的に速いです。

### Q2: 記事が数千件ある場合、API破産しませんか？

まずタイトルだけでフィルタリングし、関連度が高そうなものだけ本文を取得してLLMに投げる二段構えにしてください。これにより、APIに投げる件数を1/10以下に絞り込めます。

### Q3: 日本語のサイトでも同じように動きますか？

全く問題ありません。Claudeは多言語に非常に強いため、プロンプトが日本語であれば、英語の記事を日本語で要約させることも、その逆もシームレスに行えます。これこそが自作の醍醐味です。

---

## あわせて読みたい

- [Claude APIで高度なリスク分析エージェントを構築する方法](/posts/2026-03-01-anthropic-claude-api-python-risk-analysis-guide/)
- [Claude Marketplaceで最適なAIツールを最短で見つける方法](/posts/2026-03-09-claude-marketplace-ai-tool-selection-guide/)
- [Claude Code「Auto Mode」解禁。Anthropicが選んだ自律型開発の現実解](/posts/2026-03-25-claude-code-auto-mode-autonomous-coding/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude 3 OpusではなくSonnetを使う理由は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "実務上のコスパと速度です。要約やフィルタリングというタスクにおいて、Sonnet 3.5はOpusに匹敵する、あるいは上回る精度を見せつつ、料金は1/5程度で済みます。レスポンスも圧倒的に速いです。"
      }
    },
    {
      "@type": "Question",
      "name": "記事が数千件ある場合、API破産しませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "まずタイトルだけでフィルタリングし、関連度が高そうなものだけ本文を取得してLLMに投げる二段構えにしてください。これにより、APIに投げる件数を1/10以下に絞り込めます。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語のサイトでも同じように動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "全く問題ありません。Claudeは多言語に非常に強いため、プロンプトが日本語であれば、英語の記事を日本語で要約させることも、その逆もシームレスに行えます。これこそが自作の醍醐味です。 ---"
      }
    }
  ]
}
</script>
