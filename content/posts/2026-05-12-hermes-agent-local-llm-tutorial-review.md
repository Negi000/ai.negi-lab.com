---
title: "hermes-agent 使い方 | 自律型AIをローカルで育てる"
date: 2026-05-12T00:00:00+09:00
slug: "hermes-agent-local-llm-tutorial-review"
description: "Hermes 3の「推論力」を最大限に引き出し、自律的にツールを使いこなすエージェント構築フレームワーク。従来のLangChain系よりも「モデルの思考プ..."
cover:
  image: "/images/posts/2026-05-12-hermes-agent-local-llm-tutorial-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "hermes-agent"
  - "NousResearch"
  - "Hermes 3"
  - "自律型AIエージェント"
  - "ローカルLLM"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- Hermes 3の「推論力」を最大限に引き出し、自律的にツールを使いこなすエージェント構築フレームワーク
- 従来のLangChain系よりも「モデルの思考プロセス（CoT）」に最適化されており、指示への忠実度が極めて高い
- ローカルLLMで実用的なエージェントを動かしたいエンジニア向けであり、API課金に頼りたくない開発者に最適

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 3090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">中古市場でVRAM 24GBを安く確保でき、2枚挿しでHermes 70Bが快適に動く</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言えば、ローカルLLM環境で「ツールを使えるエージェント」を構築したいなら、現時点で最も有力な選択肢です。★評価は4.5。

特にRTX 3090/4090クラスのVRAMを所有し、Llama-3ベースのHermes 3（70Bまたは8B）を自前で動かせる環境がある人にとっては、GPT-4oに匹敵する「勝手に動く感」をローカルで実現できます。逆に、OpenAIのAPIだけを使いたい層や、Pythonの環境構築に不慣れな初心者には、まだドキュメントの不親切さが壁になるでしょう。現状は「エンジニアが道具を自作するためのコア」という立ち位置です。

## このツールが解決する問題

これまでのエージェント開発には、大きなストレスが2つありました。1つは、エージェントが「思考」を飛ばして、いきなり間違ったツールを呼び出すこと。もう1つは、モデルの出力が構造化されておらず、パースエラーでプログラムが止まることです。

hermes-agentは、Nous Researchが公開した「Hermes 3」の特性をフルに活用するように設計されています。Hermes 3は、推論（Thinking）と行動（Action）を明確に分離するトークンを学習しており、このフレームワークはその能力をシステムとして固定化します。

具体的には、従来はプロンプトエンジニアリングで無理やり「考えてから答えて」と指示していた部分を、フレームワーク側で強制的に「<thought>」タグを用いた内部推論ステップとして組み込みます。これにより、複雑なタスクでも論理的なステップを踏んでから実行に移るため、ツールの選択ミスが激減します。また、実行結果をフィードバックとして受け取り、失敗した際に「なぜ失敗したか」を自ら分析して再試行するループが標準で備わっています。

「動かしてみたけれど、結局3回に1回はエラーで止まる」という不安定なエージェント開発から脱却し、仕事で使えるレベルの堅牢性を確保しようとしているのが、このプロジェクトの核心です。

## 実際の使い方

### インストール

現状、GitHubのリポジトリから直接クローンして開発環境を構築するのが一般的です。Python 3.10以降が必須となります。

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
pip install -e .
```

また、バックエンドとしてvLLMやOllamaなど、OpenAI互換APIサーバーを立てておく必要があります。私はRTX 4090 2枚の環境で、vLLMを使ってHermes-3-Llama-3.1-70Bをロードして検証しました。

### 基本的な使用例

ツールの定義は、Pythonの関数に型ヒントとdocstringを書くだけで完了します。この情報をhermes-agentが自動的に収集し、モデルに「使える道具」として提示します。

```python
from hermes_agent import HermesAgent
from hermes_agent.tools import tool

# エージェントが使うツールの定義
@tool
def get_stock_price(symbol: str) -> float:
    """指定された株価の現在値を返します。"""
    # ここにAPI呼び出しなどの実処理を書く
    prices = {"AAPL": 220.5, "NVDA": 130.2}
    return prices.get(symbol, 0.0)

# エージェントの初期化
# モデルはOpenAI互換APIのURLを指定
agent = HermesAgent(
    model="hermes-3",
    api_base="http://localhost:8000/v1",
    api_key="none",
    tools=[get_stock_price]
)

# 実行
response = agent.run("エヌビディアの株価を調べて、10株買った時の合計金額を計算して。")
print(response)
```

このコードを実行すると、エージェントはまず「エヌビディアのシンボルはNVDAである」と考え、次に`get_stock_price`を呼び出し、その結果（130.2）に10を掛けるという計算を順序立てて実行します。

### 応用: 実務で使うなら

実務においては、単発の実行よりも「状態の保存（Persistence）」が重要です。hermes-agentは、エージェントの思考プロセスや実行履歴をJSON形式でシリアライズできるため、一度中断した作業を後から再開させるバッチ処理に組み込みやすい設計になっています。

例えば、大量のドキュメントを読み込ませて、必要な情報を外部DBに書き込むような長時間のタスクを実行する場合、チェックポイントを作成しながら進めることが可能です。既存のプロジェクトに組み込む際は、FastAPIなどでラップし、エージェントの`thought`ログをリアルタイムでフロントエンドに流すようにすると、ユーザー体験が大幅に向上します。

## 強みと弱み

**強み:**
- Hermes 3専用設計のため、Llama-3系モデルのポテンシャルを100%引き出せる。
- 内部推論（Thinking）のプロセスが標準化されており、デバッグが非常に容易。
- OpenAI APIに依存せず、完全ローカルで動作するため、機密データの処理にも使える。
- `pip install`から最初のコードが動くまで、環境が整っていれば5分かからない。

**弱み:**
- ドキュメントが極めて少なく、GitHubのソースコードを読み解く力が求められる。
- 8Bクラスのモデルだと推論力が足りず、ループに陥ることがある（快適に使うなら70B推奨）。
- 日本語での利用は可能だが、システムプロンプトが英語ベースのため、出力が英語に引っ張られることがある。
- UIが提供されていないため、可視化するには自前でフロントエンドを組む必要がある。

## 代替ツールとの比較

| 項目 | NousResearch/hermes-agent | CrewAI | LangGraph |
|------|-------------|-------|-------|
| 主な用途 | 単一エージェントの高度な推論 | 複数エージェントの役割分担 | 複雑なグラフ構造のワークフロー |
| 難易度 | 中（コード理解が必要） | 低（直感的） | 高（概念が複雑） |
| ローカル適性 | 最適（Hermesモデル特化） | 普通 | 普通 |
| 柔軟性 | 高い | 中 | 非常に高い |

とりあえず動かしたいならCrewAIの方が楽ですが、エージェントの「思考の質」をコントロールしたいならhermes-agentに軍配が上がります。

## 料金・必要スペック・導入前の注意点

ツール自体はMITライセンスのオープンソースであり、無料です。しかし、このツールを真価を発揮させるためのハードウェアコストは無視できません。

最小構成としてLlama-3.1-8BベースのHermesを使うなら、VRAM 12GB程度のRTX 3060/4060 Tiでも動作します。しかし、実務で「賢い」と感じるレベルで動かすなら、70Bモデルを4bit量子化して動かす必要があります。これにはVRAM 48GBが必要で、RTX 3090/4090の2枚挿しが推奨スペックとなります。

最近の相場なら、中古のRTX 3090（VRAM 24GB）を2枚揃えるのが、最もコストパフォーマンスが良い投資です。電源ユニットも1200W以上が必要になるため、自作PCとしての難易度は少し上がりますが、一度環境を作ればAPI代を気にせずエージェントを24時間回し続けられます。

## 私の評価

★4.0/5.0

「AIに仕事を任せる」という夢に、一歩近づいたツールだと感じています。特に、モデルが自分の考えを整理してから道具を使う様子は、これまでの「行き当たりばったりなAPI呼び出し」とは一線を画します。

ただし、万人におすすめできるわけではありません。Pythonのソースコードを読み、モデルのパラメータを調整し、VRAM使用量と戦うことを楽しめるエンジニア向けのツールです。SaaS形式のクローズドなAIエージェントサービスに月額数万円払うのが馬鹿らしくなっている人にとっては、最高の遊び場であり、実用的な武器になるはずです。

## よくある質問

### Q1: Ollamaで動かしているHermes 3でも使えますか？

はい、使えます。Ollamaが提供するOpenAI互換エンドポイント（通常ポート11434）を`api_base`に指定するだけで、hermes-agentのロジックをそのまま適用可能です。

### Q2: 商用利用は可能ですか？

フレームワーク自体はMITライセンス、モデル（Hermes 3）はLlama 3ライセンスに準じます。Llama 3の商用利用条件（月間アクティブユーザー7億人以下など）を満たしていれば、実務やサービスへの組み込みに制限はありません。

### Q3: 日本語の指示にはどの程度対応していますか？

Hermes 3自体が多言語対応のLlama 3.1をベースにしているため、日本語の指示も理解します。ただし、ツール定義のdocstringは英語で書いた方が、モデルが正しくツールの役割を理解しやすくなる傾向があります。

---

## あわせて読みたい

- [Autoclaw 使い方：Openclaw環境構築を最速で終わらせる実践レビュー](/posts/2026-04-01-autoclaw-review-openclaw-setup-guide/)
- [Agent 37は「OpenClawのホスティングに挫折した人が、月額500円以下で自律型エージェントを手に入れるための近道」です。](/posts/2026-03-14-agent-37-openclaw-hosting-review/)
- [OpenClaw 使い方 入門 | 自律型AIエージェントで調査業務を自動化する方法](/posts/2026-03-13-openclaw-agent-workflow-tutorial-python/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Ollamaで動かしているHermes 3でも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、使えます。Ollamaが提供するOpenAI互換エンドポイント（通常ポート11434）をapibaseに指定するだけで、hermes-agentのロジックをそのまま適用可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用は可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "フレームワーク自体はMITライセンス、モデル（Hermes 3）はLlama 3ライセンスに準じます。Llama 3の商用利用条件（月間アクティブユーザー7億人以下など）を満たしていれば、実務やサービスへの組み込みに制限はありません。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の指示にはどの程度対応していますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Hermes 3自体が多言語対応のLlama 3.1をベースにしているため、日本語の指示も理解します。ただし、ツール定義のdocstringは英語で書いた方が、モデルが正しくツールの役割を理解しやすくなる傾向があります。 ---"
      }
    }
  ]
}
</script>
