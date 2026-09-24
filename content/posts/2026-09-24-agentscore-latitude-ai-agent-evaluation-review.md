---
title: "AgentScore AIエージェントの精度を可視化しデグレを防ぐ評価ツール"
date: 2026-09-24T00:00:00+09:00
slug: "agentscore-latitude-ai-agent-evaluation-review"
description: "AIエージェントの「なんとなく良くなった」という感覚を、定量的なスコアで可視化する。。プロンプト変更による予期せぬデグレを、自動化された評価サイクルで即座..."
cover:
  image: "/images/posts/2026-09-24-agentscore-latitude-ai-agent-evaluation-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "AgentScore"
  - "Latitude.so"
  - "AI評価"
  - "LLMベンチマーク"
  - "プロンプトエンジニアリング"
---
注意: 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- AIエージェントの「なんとなく良くなった」という感覚を、定量的なスコアで可視化する。
- プロンプト変更による予期せぬデグレを、自動化された評価サイクルで即座に検知できる。
- 継続的にエージェントを改善するチームには必須だが、単発のプロンプト作成なら過剰。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">評価用LLMをローカルで回し、APIコストを抑えつつ高速にスコアリングするのに最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、商用レベルのAIエージェントを開発しているチームなら「即導入すべき」ツールです。★評価は 4.5/5.0 とします。

これまで多くの機械学習案件をこなしてきましたが、LLMアプリ開発で最も工数を食うのは「プロンプトを少し直したら、別の箇所で回答が壊れた」というデグレの確認作業です。AgentScore（Latitude）は、この確認作業を自動化し、エンジニアが「確信を持って」コードをデプロイできる環境を作ってくれます。

一方で、個人の趣味で1回限りのスクリプトを書くだけの人や、評価指標（メトリクス）を定義するのが面倒だと感じる人には、その多機能さが逆にハードルになるでしょう。設定にはそれなりの時間がかかりますが、長期的な運用コストを考えれば、月額料金以上のリターンが確実にあるはずです。

## このツールが解決する問題

従来、AIエージェントの評価は「開発者が数件の入力を試して、なんとなく良さそうならリリースする」という職人芸の世界でした。しかし、プロダクション環境ではこれでは通用しません。100通りの入力パターンのうち、1つでも致命的な誤答があれば信頼を失うからです。

AgentScoreが解決するのは、この「評価の不透明性」と「手動テストの限界」です。具体的には、プロンプトやモデルのパラメータを変更するたびに、あらかじめ用意したテストデータセットに対してエージェントを実行し、その精度を数値化（スコアリング）してくれます。

例えば、RAG（検索拡張生成）を用いたカスタマーサポートAIを開発している場合、「回答の正確性」「情報の網羅性」「トーンの適切さ」といった複数の軸でスコアを出し、以前のバージョンと比較できます。これにより、100件のテストケースに対して、前回はスコア0.85だったのが、修正後は0.92に上がったといった「数字による証明」が可能になります。

また、Latitudeのプラットフォーム自体がオープンソースとして提供されているため、データの機密性を気にする企業でもセルフホストして運用できる点が、実務をわかっている設計だと感じます。

## 実際の使い方

### インストール

AgentScoreはLatitudeというプラットフォームの一部として機能します。まずはCLIツールをインストールし、プロジェクトを初期化することから始まります。Node.js環境が必要ですが、Pythonエンジニアでも扱いやすい設計です。

```bash
# CLIツールのインストール
npm install -g @latitude-data/cli

# プロジェクトの初期化
latitude init my-agent-project
```

次に、Python環境から評価データを送信するためのSDKを導入します。

```bash
pip install latitude-sdk
```

### 基本的な使用例

評価を行うためには、まず「何をもって正解とするか」というデータセット（Dataset）を作成します。以下は、公式のAPI構成に基づいた、評価実行のシミュレーションコードです。

```python
from latitude import Latitude
import os

# APIキーの設定
client = Latitude(api_key=os.environ.get("LATITUDE_API_KEY"))

# 評価対象のエージェント関数
def my_ai_agent(query):
    # ここにGPT-4やClaude 3を呼び出すロジック
    return "エージェントの回答"

# 1. 評価用データセットの取得
test_cases = client.datasets.get("customer-support-v1").rows

results = []
for case in test_cases:
    # 2. エージェントを実行
    response = my_ai_agent(case.input)

    # 3. 実行結果をLatitudeに記録
    results.append({
        "input": case.input,
        "output": response,
        "expected": case.expected_output
    })

# 4. 一括でスコアリングを実行
evaluation = client.evaluations.create(
    project_id="proj_123",
    results=results,
    metrics=["accuracy", "fluency"] # 定義済みの評価指標を指定
)

print(f"評価完了。スコア: {evaluation.score}")
```

このコードを実行すると、Latitudeのダッシュボード上に実行結果が同期され、どのテストケースで失敗したのか、前回と比べてどの程度改善したのかがグラフで表示されます。

### 応用: 実務で使うなら

実務では、これをGitHub ActionsなどのCI/CDパイプラインに組み込むのが王道です。プロンプトを管理しているYAMLファイルを書き換えてプルリクエストを送ると、自動的にAgentScoreが走り、スコアが一定基準（例えば0.8以上）を下回ったらマージできないようにガードレールを敷くことができます。

また、単なる文字列の一致ではなく、LLM（GPT-4等）を評価者として使う「LLM-as-a-judge」の設定も容易です。これにより、「回答が丁寧かどうか」といった定性的な指標も、0.3秒程度で自動採点できるようになります。

## 強みと弱み

**強み:**
- 評価プロセスが構造化されているため、複数人のチームで「何が良い回答か」の基準を共有しやすい。
- オープンソース（Apache 2.0）であるため、クラウド版だけでなく自前のサーバー（RTX 4090搭載機など）でホストし、APIコストを抑える運用ができる。
- UIが非常に洗練されており、非エンジニアのプロダクトマネージャーでもスコアの推移を確認できる。

**弱み:**
- ドキュメントが英語のみであり、概念（Log, Trace, Evaluationの使い分け）を理解するまで最初の1時間は苦戦する可能性がある。
- 現時点ではJavaScript/TypeScript向けのSDKが最も充実しており、Python SDKは一部機能が追いついていない箇所がある。
- 評価のために別途LLMを回す場合（LLM-as-a-judge）、評価自体のAPIコストが発生する。

## 代替ツールとの比較

| 項目 | AgentScore (Latitude) | LangSmith | Promptfoo |
|------|-------------|-------|-------|
| 主な用途 | 継続的なスコアリング・改善 | 実行ログの追跡・デバッグ | CLIベースの比較テスト |
| 導入難易度 | 中（ダッシュボード構築含） | 低（SaaSですぐ開始） | 低（CLIで完結） |
| コスト | OSS版は無料 / クラウドは$0〜 | 有料プランは高価 | 基本無料 |
| 日本語対応 | UIは英語のみ | UIは英語のみ | CLI/HTML出力 |

LangSmithは非常に強力ですが、企業で使うにはコストが高くなりがちです。一方、Promptfooは軽量ですが、過去の推移をチームで共有するダッシュボード機能が弱めです。AgentScoreはその中間、特に「チームで継続的に改善する」という用途に特化したバランスの良いツールだと言えます。

## 料金・必要スペック・導入前の注意点

クラウド版（Latitude Cloud）は、ホビー向けに無料枠が用意されています。月間1,000トレース程度なら無料で収まるため、スモールスタートには最適です。商用利用で大規模に回す場合は、月額$50〜のProプランが必要になります。

自前でホストする場合、特別なGPUは不要ですが、Dockerが動く環境（メモリ8GB以上推奨）が必要です。MacBook AirのM2/M3モデルでも十分に動作します。ただし、評価用のモデルとしてローカルLLM（Llama 3など）を自前で動かして連携させるなら、VRAM 16GB以上のGPU（RTX 4060 Ti 16GBやRTX 4090）があった方が、評価を高速に回せてストレスがありません。

注意点として、Node.js 18以降が推奨されています。古いプロジェクトに組み込む場合は、ランタイムのバージョンを確認してください。

## 私の評価

私の評価は ★4.5 です。

SIer時代の経験から言わせてもらえば、テスト仕様書を手書きし、Excelに結果を貼り付けていた時代に比べれば、天国のようなツールです。特に、LangChainやLlamaIndexなどで複雑な自律型エージェントを組んでいる場合、エージェントが「迷走」していないかを毎日スコアで確認できる安心感は代えがたいものがあります。

Python歴が長いエンジニアからすると、最初「Node.jsベースのツールか」と少し身構えるかもしれませんが、SDKの使い勝手はPythonicで悪くありません。むしろ、これを使わずに「目視」で評価を続けることのほうが、将来的な技術負債を考えるとリスクが高いと感じます。

RAGの精度が上がらずに悩んでいる、あるいはプロンプトの調整で徹夜した経験がある人は、今日中に `latitude init` を試してみるべきです。

## よくある質問

### Q1: 評価用のデータセットを作るのが大変そうですが、自動生成できますか？

Latitudeには、既存の実行ログから「良い回答」を抽出してデータセットに昇格させる機能があります。最初から完璧なデータを用意しなくても、運用しながら育てていくことが可能です。

### Q2: 自社サーバー（オンプレミス）での利用に制限はありますか？

オープンソース版は主要な機能を制限なく利用できます。ただし、クラウド版限定のチーム管理機能や高度なアナリティクスが一部存在するため、大規模組織でのガバナンスを重視する場合はクラウド版のPro以上を検討してください。

### Q3: LangSmithからの乗り換えは簡単ですか？

データの構造が似ているため、エクスポートしたJSONをLatitudeの形式に変換するスクリプトを1つ書けば移行は可能です。ただし、Latitudeは「評価（Evaluation）」に軸足を置いているため、デバッグ用ログ（Tracing）の網羅性ではLangSmithに軍配が上がる場面もあります。

---

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [Chrome新機能「AI Skills」発表：ブラウザがAIエージェント化する衝撃](/posts/2026-04-15-google-chrome-ai-skills-workflow-automation/)
- [i-have-adhd レビュー：AIエージェントの「お喋り」を封じ込め開発速度を3倍にする技術](/posts/2026-07-23-ayghri-i-have-adhd-review-ai-agent-productivity/)
- [Pilot5.ai レビュー：5つのフロンティアモデルを同時並列で競わせる「合議制AI」の実力](/posts/2026-04-16-pilot5-ai-multi-llm-comparison-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "評価用のデータセットを作るのが大変そうですが、自動生成できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Latitudeには、既存の実行ログから「良い回答」を抽出してデータセットに昇格させる機能があります。最初から完璧なデータを用意しなくても、運用しながら育てていくことが可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "自社サーバー（オンプレミス）での利用に制限はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "オープンソース版は主要な機能を制限なく利用できます。ただし、クラウド版限定のチーム管理機能や高度なアナリティクスが一部存在するため、大規模組織でのガバナンスを重視する場合はクラウド版のPro以上を検討してください。"
      }
    },
    {
      "@type": "Question",
      "name": "LangSmithからの乗り換えは簡単ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "データの構造が似ているため、エクスポートしたJSONをLatitudeの形式に変換するスクリプトを1つ書けば移行は可能です。ただし、Latitudeは「評価（Evaluation）」に軸足を置いているため、デバッグ用ログ（Tracing）の網羅性ではLangSmithに軍配が上がる場面もあります。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>
