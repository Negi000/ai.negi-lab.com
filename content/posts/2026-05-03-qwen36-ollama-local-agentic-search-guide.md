---
title: "Qwen3.6-27BとOllamaで高精度なローカル検索AIを作る方法"
date: 2026-05-03T00:00:00+09:00
slug: "qwen36-ollama-local-agentic-search-guide"
cover:
  image: "/images/posts/2026-05-03-qwen36-ollama-local-agentic-search-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen3.6"
  - "Ollama"
  - "Agentic Search"
  - "ローカルLLM 構築"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Qwen3.6-27Bを中核とし、外部検索結果を統合して回答する「Agentic Search（自律型検索）」スクリプト。
- RTX 3090/4090（24GB VRAM）1枚で、SimpleQA精度95.7%という商用モデル級の性能をローカルで実現します。
- 前提知識：Pythonの基礎、コマンドライン操作、Dockerまたは環境構築の基礎。
- 必要なもの：NVIDIA製GPU（VRAM 24GB推奨）、Ollama、Python 3.10以上。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">GeForce RTX 3090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">24GB VRAMを搭載し、Qwen 27Bクラスを実用的な速度で動作させる最低ラインの機材</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=ASUS%20NVIDIA%20GeForce%20RTX%203090&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FASUS%2520NVIDIA%2520GeForce%2520RTX%25203090%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FASUS%2520NVIDIA%2520GeForce%2520RTX%25203090%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

これまで「検索ができるAI」を自前で組む場合、GPT-4oなどの高価なAPIを叩くか、精度を犠牲にして軽量な7Bクラスのモデルを使うのが一般的でした。しかし、Qwen3.6-27B（※出典元に基づく特定ビルド）の登場により、24GB VRAMというコンシューマー向けハイエンド環境で、商用SaaSに匹敵する「Deep Research」が可能になりました。

あえてこの構成にする理由は、データの機密性とランニングコストの両立です。PerplexityやOpenAIのSearchを使うと、検索クエリや参照した社内ドキュメントは全て外部サーバーに流れます。また、大量にリサーチを回すと月額料金も馬鹿になりません。今回の手法は、一度機材を揃えれば電気代以外はタダです。27Bというパラメータサイズは、検索結果から必要な情報を抽出し、矛盾を特定して統合する「推論能力」において、8Bクラスとは比較にならない安定感を見せます。実務で「使えない回答」を減らすための、現時点での最適解といえるでしょう。

## Step 1: 環境を整える

まずは推論エンジンとなるOllamaのセットアップと、モデルのプルを行います。

```bash
# Ollamaのインストール（未導入の場合）
curl -fsSL https://ollama.com/install.sh | sh

# Qwen3.6-27Bをプル
# 24GB VRAMに収めるため、4-bit量子化版を指定します
ollama run qwen3.6:27b-instruct-q4_K_M
```

`q4_K_M`を指定するのは、モデルサイズと精度のバランスが最も良いためです。27BモデルをFP16で動かすと50GB以上のVRAMが必要ですが、この量子化なら約16-18GBのVRAM占有で済み、コンテキストウィンドウを広めに確保できます。

⚠️ **落とし穴:** VRAMが足りない場合、モデルがCPU（RAM）に溢れて推論速度が1トークン/秒以下まで落ちます。RTX 3060（12GB）などを使っている場合は、モデルを14Bクラスに下げるか、量子化率を`q2_K`まで下げる必要がありますが、後者は知能が著しく低下するため非推奨です。

## Step 2: 基本の設定

検索エージェントを構築するためのライブラリをインストールし、Pythonスクリプトの基礎を書き上げます。

```bash
pip install ollama duckduckgo-search pydantic
```

次に、エージェントの骨格となるコードを作成します。

```python
import os
from ollama import Client
from duckduckgo_search import DDGS

# ローカルのOllamaサーバーに接続
# タイムアウトを長めに設定するのは、27Bの思考時間が長くなる場合があるため
client = Client(host='http://localhost:11434')

def search_web(query, max_results=5):
    """
    DuckDuckGoを使用してウェブ検索を実行
    APIキー不要で無料で使えるため、プロトタイピングに最適
    """
    with DDGS() as ddgs:
        results = [r['body'] for r in ddgs.text(query, max_results=max_results)]
    return "\n".join(results)
```

ここではAPIキーが不要なDuckDuckGoを採用していますが、業務でより高精度な検索が必要な場合は、Tavily API等への差し替えを検討してください。DuckDuckGoはスクレイピング対策で稀にブロックされることがあるため、リトライ処理を入れるのが実務上の定石です。

## Step 3: 動かしてみる

検索結果をプロンプトに注入し、Qwenに回答させる最小構成のコードです。

```python
def ask_with_search(user_query):
    # 1. 検索キーワードを生成させる
    keyword_prompt = f"以下の質問に答えるための検索キーワードを3つ抽出してください: {user_query}"
    keywords = client.generate(model='qwen3.6:27b', prompt=keyword_prompt)['response']

    # 2. 検索実行
    search_context = search_web(keywords)

    # 3. 検索結果を元に最終回答
    final_prompt = f"""
    以下の情報を参考にして、質問に詳しく答えてください。
    情報が不足している場合は、推測せず「不明」と答えてください。

    【情報源】
    {search_context}

    【質問】
    {user_query}
    """

    response = client.generate(model='qwen3.6:27b', prompt=final_prompt)
    return response['response']

print(ask_with_search("2024年末時点での日本の半導体産業の最新動向は？"))
```

### 期待される出力

```
2024年末、日本の半導体産業はRapidus（ラピダス）の試作ライン構築が佳境を迎えており、
北海道千歳市での建設が進んでいます。また、TSMCの熊本第2工場への助成金が確定し...
（検索結果に基づいた具体的な固有名詞と数字が含まれる回答）
```

この時点で、単なるLLMの知識（カットオフ日）を超えた、最新情報の回答が可能になっています。

## Step 4: 実用レベルにする

実務では、1回の検索で満足な結果が得られないことが多いです。そこで、モデルに「今の情報で足りるか？」を判断させ、足りなければ再検索させる「Agentic Loop」を実装します。

```python
import json

def agentic_research(task, max_iterations=3):
    context = ""
    for i in range(max_iterations):
        print(f"思考ループ {i+1}回目...")

        # 判断プロンプト
        check_prompt = f"""
        タスク: {task}
        現在の知識: {context}

        十分な情報がありますか？[YES]または[NO, 検索キーワード]の形式で答えてください。
        """
        decision = client.generate(model='qwen3.6:27b', prompt=check_prompt)['response']

        if "YES" in decision.upper():
            break

        # 検索キーワードを抽出して実行
        search_query = decision.replace("NO,", "").strip()
        new_info = search_web(search_query)
        context += f"\n--- 検索結果({search_query}) ---\n{new_info}"

    # 最終集計
    report_prompt = f"以下の調査結果を統合し、専門的なレポートを作成せよ:\n{context}\nタスク:{task}"
    return client.generate(model='qwen3.6:27b', prompt=report_prompt)['response']

final_report = agentic_research("最新のLLM量子化技術『GGUF vs EXL2』のベンチマーク比較")
print(final_report)
```

このループ構造にすることで、情報の抜け漏れが激減します。Qwen3.6-27Bはこの「自己批判（Self-Correction）」が非常に上手く、適当な検索で茶を濁そうとする8Bモデルとは一線を画す精度のレポートを吐き出します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `OOM: Out of Memory` | VRAM容量不足。 | 4-bit量子化版を使用するか、システム全体で他のGPU使用アプリを閉じる。 |
| 検索結果が空 | DuckDuckGoのレート制限。 | 数秒の `time.sleep()` を入れるか、VPN経由でIPを変更する。 |
| 回答が英語になる | システムプロンプトの不足。 | プロンプトの冒頭に「必ず日本語で答えてください」と明記する。 |

## 次のステップ

このローカル検索エージェントが動くようになったら、次は「情報の信頼性評価」を組み込んでみてください。現在のスクリプトは、検索にかかった情報を全て等しく信じてしまいます。そこで、取得した各URLに対して「このサイトは公式ドキュメントか？ 個人のブログか？」をQwenに判定させ、情報の重み付けを行うロジックを追加すると、さらに精度は跳ね上がります。

また、社内Wikiや過去の議事録がある場合は、DuckDuckGoの代わりに`ChromaDB`や`Qdrant`といったベクトルデータベースを検索先に加える「ハイブリッドRAG」への拡張も容易です。これにより、世界中の最新情報と、あなただけが持つ機密情報を組み合わせた、世界に一つだけの最強の意思決定支援ツールが完成します。ローカルLLMの真価は、こうした「カスタマイズの自由度」にこそあります。

## よくある質問

### Q1: RTX 3090/4090がないと全く動かないのでしょうか？

12GB程度のVRAMでもQwenの7Bや14Bなら高速に動きます。ただし、27Bモデルのような複雑な推論（情報の矛盾検知など）を期待する場合、速度を犠牲にしてメインメモリ（RAM）を併用するか、24GBクラスのGPUを用意するのが現実的です。

### Q2: 検索結果が長すぎてコンテキストウィンドウを超えてしまいます。

Ollamaのデフォルト設定ではコンテキストが4096トークンに制限されている場合があります。`Modelfile`を作成し、`PARAMETER num_ctx 32768`のように設定を書き換えて、コンテキストを拡張してロードし直してください。

### Q3: 商用利用は可能ですか？

Qwen 2.5/3.6シリーズは基本的にApache 2.0またはそれに準ずるライセンスで公開されていますが、最新のモデルについては公式リポジトリのライセンス条項を必ず確認してください。多くの場合、商用利用も可能ですが、モデル名が「Qwen」であることを明記する必要があります。

---

## あわせて読みたい

- [Qwen3.6-35B-A3B 使い方 入門：MoEモデルをローカル環境で爆速動作させる方法](/posts/2026-04-16-qwen3-6-35b-moe-python-guide/)
- [Qwen2.5-Coder 使い方 | ローカルでGPT-4o級の開発環境をPythonで構築する](/posts/2026-03-21-qwen2-5-coder-python-local-guide/)
- [Qwen3.5-9B-Claude-4.6-Opus-Uncensored-Distilled-GGUF 使い方入門](/posts/2026-03-16-qwen3-5-9b-uncensored-gguf-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3090/4090がないと全く動かないのでしょうか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "12GB程度のVRAMでもQwenの7Bや14Bなら高速に動きます。ただし、27Bモデルのような複雑な推論（情報の矛盾検知など）を期待する場合、速度を犠牲にしてメインメモリ（RAM）を併用するか、24GBクラスのGPUを用意するのが現実的です。"
      }
    },
    {
      "@type": "Question",
      "name": "検索結果が長すぎてコンテキストウィンドウを超えてしまいます。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaのデフォルト設定ではコンテキストが4096トークンに制限されている場合があります。Modelfileを作成し、PARAMETER numctx 32768のように設定を書き換えて、コンテキストを拡張してロードし直してください。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用は可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Qwen 2.5/3.6シリーズは基本的にApache 2.0またはそれに準ずるライセンスで公開されていますが、最新のモデルについては公式リポジトリのライセンス条項を必ず確認してください。多くの場合、商用利用も可能ですが、モデル名が「Qwen」であることを明記する必要があります。 ---"
      }
    }
  ]
}
</script>
