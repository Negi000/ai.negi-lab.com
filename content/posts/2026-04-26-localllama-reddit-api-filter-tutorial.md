---
title: "r/LocalLLaMA 活用術！最新AI情報を自動収集するフィルター実装ガイド"
date: 2026-04-26T00:00:00+09:00
slug: "localllama-reddit-api-filter-tutorial"
cover:
  image: "/images/posts/2026-04-26-localllama-reddit-api-filter-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Reddit API 使い方"
  - "LocalLLaMA フィルター"
  - "Python LLM 自動化"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

巨大化したコミュニティ「r/LocalLLaMA」から、仕事で使える技術情報だけをLLMで自動抽出するPythonスクリプトを作ります。
100万人規模のトラフィックを誇るこのフォーラムは、ルール改定によって「質の高い投稿」を求めています。
そのフィルタリングを自分で行い、DiscordやSlackに流すところまでを自動化します。

- Python 3.10以上が動作する環境
- Reddit API（無料）の利用登録
- OpenAI API または ローカルLLM（Llama-3など）の実行環境

## なぜこの方法を選ぶのか

r/LocalLLaMAは今や週100万人が訪れる巨大掲示板です。
情報の鮮度は世界一ですが、ルールが厳格化された背景には「質の低い投稿やAI生成のゴミ投稿」の急増があります。
ブラウザで毎日チェックするのは時間の無駄ですし、見落としも増えます。

Reddit公式の「Hot」や「Top」ソートは、面白ネタ（ミーム）が上位に来やすく、実務に必要な「ベンチマーク結果」や「量子化手法の新提案」が埋もれがちです。
そこで、Reddit APIで情報を取得し、LLMに「この記事は技術的に新しいか」「仕事で応用可能か」をルールに基づいて判断させる自作フィルターが、最も効率的で確実な解決策になります。

## Step 1: 環境を整える

まずはReddit APIを叩くためのライブラリと、LLM操作用のライブラリをインストールします。

```bash
# Reddit操作用の公式ラッパーPRAWと、LLM連携用のライブラリを導入
pip install praw openai python-dotenv
```

PRAW（Python Reddit API Wrapper）は、複雑なRedditのAPI仕様を抽象化してくれるため、エンジニアならこれ一択です。
環境変数を管理するために `python-dotenv` も必須です。APIキーをコードに直書きするのはSIer時代なら即刻クビ案件ですから、必ず `.env` ファイルで管理しましょう。

⚠️ **落とし穴:** Reddit APIの「Client ID」と「Secret」を取得する際、アプリの種類を必ず 「script」 にしてください。web appなどを選ぶとリダイレクトURLの設定が必要になり、スクリプト実行でエラーになります。

## Step 2: 基本の設定

`.env` ファイルを作成し、取得した認証情報を記述します。

```env
REDDIT_CLIENT_ID="あなたのID"
REDDIT_CLIENT_SECRET="あなたのシークレット"
REDDIT_USER_AGENT="LocalLLaMA-Filter-Bot v1.0 by /u/yourusername"
OPENAI_API_KEY="sk-..."
```

次に、Python側でこれらを読み込み、初期化するコードを書きます。

```python
import os
import praw
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Reddit APIの初期化
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

# LLM（今回はOpenAI）の初期化
# ローカルLLM（Ollama等）を使う場合は base_url を変更してください
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

`user_agent` は適当な文字列でも動きますが、RedditのAPIガイドラインでは「プラットフォーム名：アプリID：バージョン：作者名」の形式が推奨されています。
これを守らないとレート制限（アクセス拒否）が厳しくなることがあるため、私は常に詳細に記述するようにしています。

## Step 3: 動かしてみる

まずはr/LocalLLaMAの「New（新着）」から最新の5件を取得して、タイトルを表示してみます。

```python
subreddit = reddit.subreddit("LocalLLaMA")

print("--- 最新の投稿 ---")
for submission in subreddit.new(limit=5):
    print(f"Title: {submission.title}")
    print(f"Score: {submission.score}")
    print("-" * 20)
```

### 期待される出力

```
--- 最新の投稿 ---
Title: New quantization method for Llama 3.1 70B...
Score: 15
--------------------
Title: Why is my 4090 slow?
Score: 2
--------------------
...
```

この段階では、技術的な情報と単なる質問（初歩的なトラブル）が混ざっています。
私の経験上、ここから「自分の業務に関係あるもの」だけを抽出するのが一番の苦労ポイントです。

## Step 4: 実用レベルにする

ここからが本番です。取得した投稿の「本文（selftext）」をLLMに渡し、r/LocalLLaMAの新しいルール（技術的品質の維持）に合致するか、そして実務に役立つかを判定させます。

```python
def evaluate_post(title, content):
    prompt = f"""
    あなたはAIエンジニアの専門査読者です。
    以下のRedditの投稿が、技術的に価値があるか判定してください。

    判定基準:
    1. 新しいモデル、ライブラリ、または量子化手法の紹介か？
    2. 実装コードやベンチマーク結果が含まれているか？
    3. 単なる初心者向けの質問や、既知の情報の繰り返しではないか？

    投稿タイトル: {title}
    投稿内容: {content[:500]}... (省略)

    出力形式:
    Score: (0-10)
    Reason: (1行で理由)
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# 実際にフィルタリングを実行
print("\n--- 技術的に価値の高い投稿を抽出 ---")
for submission in subreddit.new(limit=10):
    # 短すぎる投稿や画像のみの投稿はスキップ
    if len(submission.selftext) < 100:
        continue

    evaluation = evaluate_post(submission.title, submission.selftext)

    # スコアが7以上のものだけを表示
    if "Score: 7" in evaluation or "Score: 8" in evaluation or "Score: 9" in evaluation or "Score: 10" in evaluation:
        print(f"【採用】 {submission.title}")
        print(evaluation)
        print(f"URL: https://www.reddit.com{submission.permalink}\n")
```

このスクリプトでは、`gpt-4o-mini` を使っています。
1リクエストあたり約0.01円以下で済むため、100件処理しても数円です。
SIer時代に手作業で技術調査報告書を作っていた時間を考えれば、タダみたいなものです。

温度感（temperature）を0に設定しているのは、判定のブレをなくすためです。
また、`content[:500]` と制限をかけているのは、Redditには時折、長大なログを貼り付けるユーザーがいるからです。トークン消費を抑えつつ、要点だけを判断させるのがコツです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `praw.exceptions.RedditAPIException: RATELIMIT` | APIの叩きすぎ。短時間にリクエストが集中した | `time.sleep(2)` を入れるか、取得件数（limit）を減らす |
| `OpenAI API Key not found` | `.env` の読み込み失敗 | `load_dotenv()` が `os.getenv` の前に呼ばれているか確認 |
| 判定結果が全部0点になる | プロンプトが厳しすぎる | 判定基準を「自分の興味があるキーワード」に具体化する |

## 次のステップ

この記事で作成したスクリプトをGitHub Actionsや、自宅サーバーのcronに登録すれば、毎日決まった時間に「技術価値の高いAIニュース」が手元に届くようになります。

さらに応用するなら、抽出した情報を元に「要約」を作成し、自分のNotionやSlackに自動投稿する機能を付けてみてください。
私はRTX 4090を2枚挿した自宅サーバーで、このフィルタリングをローカルのLlama-3-8Bで行っています。
外部APIを使わずに、完全にプライベートな「自分専用AIニュースレター」を構築するのも、ローカルLLM使いとしての醍醐味ですね。

今回のr/LocalLLaMAのルール改定は、コミュニティが「量より質」へ転換するシグナルです。
ツールを自作して、その質の高い情報だけを効率的に吸収できる体制を整えましょう。

## よくある質問

### Q1: Reddit APIの利用に料金はかかりますか？

通常の個人利用（スクリプトからの取得）であれば、現在のところ無料で利用可能です。ただし、1分間に100リクエスト程度のレート制限があるため、大量の過去データを一気に取得するような使い方の場合は注意が必要です。

### Q2: OpenAIではなく、OllamaなどのローカルLLMを使いたい場合は？

OpenAIのライブラリの `base_url` を `http://localhost:11434/v1` （Ollamaのデフォルト）に変更するだけで、コードの大部分を書き換えずに移行できます。RTX 3060以上のGPUがあれば、Llama-3-8Bクラスで十分な判定が可能です。

### Q3: 投稿に画像やPDFが含まれている場合はどうすればいいですか？

今回のスクリプトはテキストベースですが、PyMuPDFなどでリンク先のPDFを読み取ったり、GPT-4o（マルチモーダル）に画像URLを渡すことで、ベンチマークのグラフ画像なども解析対象に含めることができ、より精度が上がります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">ローカルLLMを自作フィルターで回すなら、24GB VRAMを持つ4090が現状の最適解です</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [LocalLLaMA Discordサーバーに参加してAIボットを活用する方法](/posts/2026-01-19-728a1678/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Reddit APIの利用に料金はかかりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "通常の個人利用（スクリプトからの取得）であれば、現在のところ無料で利用可能です。ただし、1分間に100リクエスト程度のレート制限があるため、大量の過去データを一気に取得するような使い方の場合は注意が必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "OpenAIではなく、OllamaなどのローカルLLMを使いたい場合は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "OpenAIのライブラリの baseurl を http://localhost:11434/v1 （Ollamaのデフォルト）に変更するだけで、コードの大部分を書き換えずに移行できます。RTX 3060以上のGPUがあれば、Llama-3-8Bクラスで十分な判定が可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "投稿に画像やPDFが含まれている場合はどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "今回のスクリプトはテキストベースですが、PyMuPDFなどでリンク先のPDFを読み取ったり、GPT-4o（マルチモーダル）に画像URLを渡すことで、ベンチマークのグラフ画像なども解析対象に含めることができ、より精度が上がります。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品</p> <strong style=\"font-size:16px\">GeForce RTX 4090</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">ローカルLLMを自作フィルターで回すなら、24GB VRAMを持つ4090が現状の最適解です</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonで見る</a> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">楽天で見る</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
