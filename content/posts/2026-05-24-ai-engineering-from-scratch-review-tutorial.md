---
title: "ai-engineering-from-scratch 評価：AIエンジニアを目指す中級者の最短ルート"
date: 2026-05-24T00:00:00+09:00
slug: "ai-engineering-from-scratch-review-tutorial"
description: "LangChainなどのフレームワークが隠蔽している「AIアプリの裏側」をゼロから実装して理解を深める。。既存の「ライブラリの使い方」を教える教材とは異な..."
cover:
  image: "/images/posts/2026-05-24-ai-engineering-from-scratch-review-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "ai-engineering-from-scratch"
  - "RAG実装"
  - "自作AIエージェント"
  - "LLMエンジニアリング"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- LangChainなどのフレームワークが隠蔽している「AIアプリの裏側」をゼロから実装して理解を深める。
- 既存の「ライブラリの使い方」を教える教材とは異なり、数式やロジックをPythonコードに落とし込む過程を重視している。
- 使うべき人は「ブラックボックス化したAI実装に限界を感じている中級エンジニア」。使わなくていい人は「動けばいいので最短でプロトタイプを作りたい人」。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4070 Ti SUPER 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBあればローカルでのベクトル埋め込みや推論が高速化し、学習効率が爆増する</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204070%2520Ti%2520SUPER%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204070%2520Ti%2520SUPER%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204070%20Ti%20SUPER%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

このリポジトリは、AIエンジニアとして一歩抜きん出たいなら、確実に「買い（時間を投資する価値あり）」です。★評価は 4.5。

世の中のAI教材の多くは「LangChainをpip installして、数行書けばRAGができます」という表面的なものばかりです。
しかし、いざ実務でレスポンス精度が上がらなかったり、推論速度を改善したりする必要があるとき、フレームワークの中身を知らないと手も足も出ません。
この `ai-engineering-from-scratch` は、ベクトル検索のコサイン類似度計算や、エージェントの思考ループ（ReAct）をライブラリなしのピュアなPythonで書くことを強いてきます。

正直、面倒です。しかし、この「面倒なプロセス」を通ることで、OpenAIのAPIドキュメントの行間が読めるようになります。
「なんとなく動いている」状態から「狙って制御している」状態へ脱皮したいエンジニアにとって、これほど密度の高い砂場（サンドボックス）はありません。

## このツールが解決する問題

従来、AIアプリケーション開発には「フレームワーク依存症」という大きな問題がありました。
LangChainやLlamaIndexを使えば、数行のコードで高機能なアプリが作れますが、それは「魔法の杖」を振っているに過ぎません。
内部でどのようなプロンプトが構築され、どのようなチャンク分割が行われ、検索結果がどうリランクされているのかが隠蔽されています。

実務で「精度が80%から上がらない」という壁にぶつかったとき、フレームワークの関数を眺めていても解決策は見つかりません。
この `ai-engineering-from-scratch` は、その魔法を解き明かします。
例えばRAG（検索拡張生成）であれば、ベクトルデータベースを自作のクラスでシミュレートし、検索ロジックを自分で書くことで「なぜ検索漏れが起きるのか」という構造的な理由を理解させてくれます。

また、AIエージェントの実装においても、既存のライブラリでは複雑になりがちな「思考と行動のループ」を、シンプルな `while` 文と `if` 文で再構築します。
これにより、自社独自の制約がある環境でも、フレームワークに縛られない最適なAIエンジニアリングができるようになります。
GitHubで1日に1,500スター以上を獲得した理由は、多くのエンジニアが「表層的なライブラリ操作」に飽き、本質的な技術力を求めている証拠と言えるでしょう。

## 実際の使い方

### インストール

特別なライブラリのインストールは最小限です。Python 3.10以上が推奨されています。

```bash
git clone https://github.com/rohitg00/ai-engineering-from-scratch.git
cd ai-engineering-from-scratch
python -m venv venv
source venv/bin/activate
pip install numpy openai python-dotenv
```

READMEを読み込むと分かりますが、重厚なライブラリ群ではなく、計算用の `numpy` と API連携用の `openai` 程度しか使いません。
これが「スクラッチから作る」というコンセプトの強さです。

### 基本的な使用例

たとえば、RAGの核心である「コサイン類似度によるドキュメント検索」を、ライブラリを使わずに実装する例が紹介されています。

```python
import numpy as np

def cosine_similarity(v1, v2):
    # ベクトル間のコサイン類似度を計算する基本ロジック
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    return dot_product / (norm_v1 * norm_v2)

# 実務でのカスタマイズポイント
# 実際にはここに、特定のキーワードの重み付け（TF-IDFとのハイブリッド）などを加えることで、
# 既存のVector DBでは対応しきれない「ドメイン特化型検索」が可能になります。
```

このコード自体はシンプルですが、これを自作のベクトルストアクラスに組み込むプロセスこそが、このリポジトリの真髄です。
公式のノートブック（.ipynb）に沿って進めると、データのベクトル化からリトリーバルまでを自分の手で組み立てることになります。

### 応用: 実務で使うなら

実務において、AIエージェントの「ツール利用（Tool Calling）」を既存フレームワークで実装すると、エラー時の挙動が追いにくいという課題があります。
このプロジェクトの知見を活かせば、以下のようにエージェントの推論ループを制御できます。

```python
def simple_agent_loop(query, tools):
    history = [{"role": "user", "content": query}]

    for _ in range(5):  # 最大5回の試行。無限ループ防止。
        # ここでOpenAI APIを叩き、関数呼び出しが必要か判断
        response = call_llm(history, tools)

        if response.finish_reason == "stop":
            return response.content

        if response.tool_calls:
            # ツールの実行結果をhistoryに追加し、再度LLMに問い合わせる
            results = execute_tools(response.tool_calls)
            history.append({"role": "tool", "content": results})

    return "制限回数内に回答できませんでした"
```

このように、ループの回数制限やリトライロジックを自分で書くことで、本番環境で「AIが暴走してコストが跳ね上がる」といったリスクを確実に防げるようになります。

## 強みと弱み

**強み:**
- フレームワークの依存関係に起因する脆弱性やアップデートによる破壊的変更から解放される。
- 「なぜ動かないのか」を特定するデバッグ能力が、この学習を通じて飛躍的に向上する。
- 独自の重み付け検索や、特殊なワークフローを実装するための基礎体力がつく。
- 実装がシンプル（Pure Python + Numpy中心）なので、将来的に別の言語（RustやGo）に移植しやすい。

**弱み:**
- 日本語ドキュメントはなく、すべて英語のノートブックと解説を読み解く必要がある。
- 「動くもの」をすぐに公開したい場合には不向き。あくまで学習と、最適化されたエンジニアリングのためのもの。
- GPUをガンガン回すようなローカルLLM最適化よりは、API（OpenAI等）をベースにしたロジック構築に比重が置かれている。
- 本格的な本番運用（スケーラビリティやセキュリティ）については、別途設計が必要。

## 代替ツールとの比較

| 項目 | ai-engineering-from-scratch | LangChain | DeepLearning.ai (Short Courses) |
|------|-------------|-------|-------|
| 目的 | 実装の内部理解・自作 | 開発スピードの最大化 | 概念と使い方の学習 |
| 柔軟性 | 極めて高い | フレームワークの仕様に依存 | 低い（動画中心） |
| 学習コスト | 高い（コードを一行ずつ書く） | 低い（既存部品を繋ぐ） | 中（概念は学べるが実装力は別） |
| 実務への応用 | 独自エンジンの構築に最適 | 標準的なプロトタイプに最適 | 知識のアップデートに最適 |

「LangChain」が便利なレゴブロックだとすれば、このリポジトリは「プラスチックを成形してブロックそのものを作る方法」を教えてくれます。

## 料金・必要スペック・導入前の注意点

このリポジトリ自体は無料（MITライセンス等）で利用可能ですが、学習にはOpenAIのAPIキーがほぼ必須です。
一通りのノートブックを試すのに、GPT-4o miniなどの安価なモデルを使えば、月額$5〜$10程度で十分に遊べます。

ハードウェアスペックについては、複雑なモデルのトレーニングではないため、MacBook Airや一般的なWindowsノートPC（メモリ16GB以上を推奨）で事足ります。
ただし、ローカルLLMを使って実験したい場合は、VRAMが12GB以上のGPUを搭載したデスクトップPC（例えばRTX 4070 Ti SUPER 16GBモデルなど）があると、応答を待つストレスが劇的に減ります。
特にベクトル埋め込み（Embedding）をローカルで数千件回す場合、CPUだけでは10分かかる処理が、GPUを使えば10秒で終わります。

商用利用については、リポジトリ内のコードをベースに自作エンジンを組む分には問題ありませんが、各コードが参照している外部APIの利用規約には注意してください。

## 私の評価

私はこのプロジェクトに★4.5をつけます。
理由は、現在のAI開発シーンに最も欠けている「泥臭い実装力」に焦点を当てているからです。
SIer時代、ブラックボックスな商用パッケージを使ってトラブルが起きたとき、ソースコードが見えないもどかしさを何度も味わいました。
AIの世界でも、LangChainを10個繋ぎ合わせただけの「AIエンジニア」は、近い将来、より高度な自動化ツールに淘汰されるでしょう。

しかし、コサイン類似度の数式をPythonで書き、トークン制限を意識しながら自前でコンテキストウィンドウを管理できるエンジニアは、モデルが変わっても生き残れます。
このリポジトリは、そういう「足腰の強いエンジニア」になるためのトレーニングメニューです。
唯一、初心者が手を出すと途中で挫折する可能性が高いため、Pythonのクラス継承や内包表記がすらすら書けるようになってから取り組むことをおすすめします。

## よくある質問

### Q1: LangChainをすでに使っていますが、これを学ぶ意味はありますか？

大いにあります。LangChainの内部で何が起きているか（抽象化されている部分）を理解することで、エラーが出た際の切り分けや、ライブラリのバグを回避する実装が自分でできるようになります。

### Q2: 実行に必要なコストはどのくらいですか？

リポジトリをクローンして試すだけなら、OpenAI APIの利用料のみです。GPT-4o miniを使えば数ドルで一通りのチュートリアルを完走できます。ローカル実行なら完全に無料です。

### Q3: 完全にゼロからの初心者でも理解できますか？

正直に言うと、Pythonの基本文法（リスト操作、辞書、関数、クラス）が怪しい人には厳しいです。少なくとも「APIを叩く」ことの意味がわかり、NumPyの基本的な行列演算に抵抗がないことが前提となります。

---

## あわせて読みたい

- [DreamServer 使い方・評価｜ローカルAI環境を一台で完結させる決定版](/posts/2026-05-18-dreamserver-local-ai-full-review-tutorial/)
- [Pluraiレビュー：LLMの「評価」を言語化してガードレール化する実装ガイド](/posts/2026-04-29-plurai-llm-eval-vibe-check-guardrails/)
- [Airtableが自律型AIの司令塔に？マルチエージェントを動かす「Superagent from Airtable」を徹底レビュー](/posts/2026-01-31-40f1b4d1/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "LangChainをすでに使っていますが、これを学ぶ意味はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "大いにあります。LangChainの内部で何が起きているか（抽象化されている部分）を理解することで、エラーが出た際の切り分けや、ライブラリのバグを回避する実装が自分でできるようになります。"
      }
    },
    {
      "@type": "Question",
      "name": "実行に必要なコストはどのくらいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "リポジトリをクローンして試すだけなら、OpenAI APIの利用料のみです。GPT-4o miniを使えば数ドルで一通りのチュートリアルを完走できます。ローカル実行なら完全に無料です。"
      }
    },
    {
      "@type": "Question",
      "name": "完全にゼロからの初心者でも理解できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "正直に言うと、Pythonの基本文法（リスト操作、辞書、関数、クラス）が怪しい人には厳しいです。少なくとも「APIを叩く」ことの意味がわかり、NumPyの基本的な行列演算に抵抗がないことが前提となります。 ---"
      }
    }
  ]
}
</script>
