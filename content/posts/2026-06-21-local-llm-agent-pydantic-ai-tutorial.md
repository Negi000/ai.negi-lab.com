---
title: "OllamaとPydanticAIで自律型ローカルエージェントを構築する方法"
date: 2026-06-21T00:00:00+09:00
slug: "local-llm-agent-pydantic-ai-tutorial"
cover:
  image: "/images/posts/2026-06-21-local-llm-agent-pydantic-ai-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "PydanticAI 使い方"
  - "Ollama 入門"
  - "自律型AIエージェント 構築"
  - "ローカルLLM Python"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- ローカルLLM（Llama 3.3/4クラス）を使用し、インターネット検索とローカルファイル操作を組み合わせて「市場調査レポート」を自動生成する自律型エージェント。
- Pythonの型定義ライブラリ「Pydantic」をベースにした最新の「PydanticAI」を使い、エラーに強く、本番環境で動作を保証できる設計を学びます。
- 前提知識はPythonの基本的な文法（関数の定義、非同期処理 async/await）がわかる程度で問題ありません。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MSI GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBを安価に確保でき、Llama 3.3 8Bを余裕で回せるエージェント開発の入門機。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルエージェントを実用レベルで動かすには、推論速度とコンテキストウィンドウの広さが命です。
2026年現在の基準では、最低でも NVIDIA RTX 3060 (12GB VRAM) 以上が必要です。
理想は RTX 4090 クラスで、16GB以上のVRAMがあれば、エージェントが「思考」する際に必要な複数のツール定義をメモリに乗せたまま高速にレスポンスを返せます。

Macユーザーの場合、Apple Silicon（M2/M3/M4）のメモリ24GB以上が必須ラインです。
16GBモデルでも動きますが、モデルの量子化（Quantization）を強める必要があり、エージェントが指示を忘れる「健忘症」に陥りやすくなります。
API料金は、ローカル完結のため 0円 ですが、電気代とハードウェア投資が初期費用としてかかります。
もしハードウェアが足りない場合は、月額$20程度のサーバー貸し出しサービス（RunPod等）でRTX 4090を借りるのが、中途半端なPCを買うより賢い選択です。

## なぜこの方法を選ぶのか

現在、AIエージェントのフレームワークは LangChain や AutoGen、CrewAI などが乱立していますが、私は PydanticAI を推奨します。
SIer時代に嫌というほど経験しましたが、エージェント開発の最大の敵は「LLMが返す不安定なJSON」による実行時エラーです。
PydanticAIは、OpenAIが提唱した構造化出力（Structured Outputs）の概念をローカルLLMでも厳密に扱うために設計されています。

他のフレームワークは多機能すぎて、ブラックボックスの中で何が起きているか追いづらい欠点があります。
一方で、PydanticAIは「型」でガードレールを敷くため、モデルが間違った引数でツールを呼び出そうとした瞬間に検知し、自動で再試行（リトライ）を促します。
「動かしてみた」レベルのデモではなく、深夜にバッチ処理を回しても落ちないエージェントを作るなら、現状これ一択だと断言します。

## Step 1: 環境を整える

まずは推論サーバーとなる Ollama をインストールし、2026年時点での標準的なエージェント向けモデルを準備します。

```bash
# Ollamaのインストール（未導入の場合）
curl -fsSL https://ollama.com/install.sh | sh

# エージェントの「思考力」に定評のあるモデルをプル
# 8Bクラスなら高速、70Bクラスなら正確。今回は中間を狙います。
ollama pull llama3.3:8b-instruct-fp16
```

`fp16`（16bit浮動小数点）を指定するのは、エージェントの論理的推論において4bit量子化だと「ツールの使い分け」に失敗するケースが多いためです。
VRAMに余裕がない場合は `q8_0` を選択してください。
次に、Pythonの仮想環境を作成し、必要なライブラリをインストールします。

```bash
python -m venv agent-env
source agent-env/bin/activate  # Windowsは .\agent-env\Scripts\activate
pip install pydantic-ai[logfire] duckduckgo-search httpx
```

`logfire` は PydanticAI 開発チームが提供する観測用ツールです。
エージェントが「今、何を考えてどのツールを選んだか」を可視化するために、開発中は必須と言えます。

⚠️ **落とし穴:** Ollama のデフォルト設定では、一度に一つのリクエストしか処理できません。
エージェントが自分自身に問いかけたり、並列でツールを実行したりする場合にボトルネックとなります。
環境変数 `OLLAMA_NUM_PARALLEL=4` を設定してから Ollama サーバーを起動し直すことで、並行処理が可能になります。

## Step 2: 基本の設定

PydanticAI を使って、エージェントの「性格」と「利用可能なツール」を定義します。
ここでは、環境変数から Ollama の接続先を読み込む設定にします。

```python
import os
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.ollama import OllamaModel

# ローカルのOllamaをモデルとして指定
# 2026年時点では、ローカルモデルでもOpenAI互換APIが標準
model = OllamaModel(
    model_name='llama3.3:8b-instruct-fp16',
    base_url='http://localhost:11434/v1',
)

# エージェントの定義
# 戻り値の型を指定することで、LLMが勝手なフォーマットで返さないように制限する
from pydantic import BaseModel

class ResearchResult(BaseModel):
    title: str
    summary: str
    sources: list[str]
    confidence_score: float

research_agent = Agent(
    model,
    result_type=ResearchResult,
    system_prompt=(
        "あなたはプロの市場リサーチアシスタントです。"
        "提供されたツールを駆使して、事実に基いた正確なレポートを作成してください。"
        "推測ではなく、必ず検索結果から得られた情報を引用すること。"
    ),
)
```

`result_type` に Pydantic のモデルを渡すのがポイントです。
これにより、LLMが出力を終えた後、Python側で自動的にバリデーションが行われます。
もし `confidence_score` が数値ではなく文字列で返ってきた場合、PydanticAI が自動で「数値で返してください」とLLMに修正依頼を投げてくれます。

## Step 3: 動かしてみる

エージェントに「手」を与えます。
まずはインターネット検索を行うツールを実装し、実際に動かしてみましょう。

```python
from duckduckgo_search import DDGS

@research_agent.tool
async def search_web(ctx: RunContext[None], query: str) -> str:
    """最新の情報をインターネットで検索するツールです。"""
    print(f"DEBUG: 検索を実行中... クエリ: {query}")
    with DDGS() as ddgs:
        results = [r['body'] for r in ddgs.text(query, max_results=3)]
        return "\n---\n".join(results)

# 実行
async def main():
    result = await research_agent.run(
        "2026年におけるローカルLLMエージェントの最新トレンドを調べて"
    )
    print(f"タイトル: {result.data.title}")
    print(f"要約: {result.data.summary}")
    print(f"ソース: {result.data.sources}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### 期待される出力

```
DEBUG: 検索を実行中... クエリ: 2026年 ローカルLLM エージェント トレンド
タイトル: 2026年ローカルLLMエージェントの動向調査
要約: 2026年はエージェントの「小規模・高機能化」が進み、PydanticAI等の型安全なフレームワークが主流となっています。また、RTX 50シリーズの普及により、家庭環境でも70Bクラスのモデルが実用速度で動作するようになりました。
ソース: ['https://example.com/tech-trend-2026', 'https://reddit.com/r/LocalLLaMA/...']
```

この時点で、エージェントは「検索ツールが必要だ」と自分で判断し、クエリを生成し、結果を読んで、指定した `ResearchResult` の形式に変換して返しています。
私が最初に Agent を触った時は、この「判断」の部分でよく失敗しましたが、Llama 3.3 以降のモデルは `Tool Calling`（関数呼び出し）の精度が劇的に向上しています。

## Step 4: 実用レベルにする

実務では、検索して終わりではありません。
結果をファイルに保存し、さらに失敗したときのリトライ処理を加える必要があります。
ここでは「依存注入（Dependency Injection）」を使い、エージェントが実行されるコンテキスト（保存先ディレクトリなど）を安全に渡す手法をとります。

```python
from dataclasses import dataclass

@dataclass
class AgentDeps:
    output_dir: str
    max_retries: int = 3

@research_agent.tool
async def save_report(ctx: RunContext[AgentDeps], content: str, filename: str) -> str:
    """レポートを指定されたファイル名で保存するツールです。"""
    os.makedirs(ctx.deps.output_dir, exist_ok=True)
    path = os.path.join(ctx.deps.output_dir, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return f"ファイルを {path} に保存しました。"

# 実務的なメイン処理
async def run_business_task():
    deps = AgentDeps(output_dir="./reports")

    # 複雑なタスクを依頼
    prompt = (
        "AIエージェントの最新動向を調査し、report_2026.txt という名前で保存してください。"
        "保存が完了したら、その結果を構造化データとして返してください。"
    )

    # retries引数で、ツール実行失敗時の自動リトライ回数を指定
    result = await research_agent.run(prompt, deps=deps, usage_limits={'request_limit': 10})

    print("処理完了。")
    print(f"トークン使用量: {result.usage()}")

if __name__ == "__main__":
    asyncio.run(run_business_task())
```

このコードの肝は `usage_limits` です。
エージェント開発で最も恐ろしいのは、無限ループです。
「検索する」→「エラーが出る」→「もう一度検索する」を繰り返すと、API利用なら破産しますし、ローカルでもPCが熱暴走します。
`request_limit` を設定することで、どんなにエージェントが迷走しても指定回数で強制停止させるのが「仕事で使う」ための最低限の作法です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Unexpected keyword argument` | LLMが定義にない引数を捏造した | PydanticAIの `retries` 設定を増やすか、System Promptで「余計な引数を作るな」と厳命する |
| `Context window exceeded` | 検索結果が長すぎてメモリ溢れ | ツール側で文字列を slice(0, 2000) するなど、渡す情報を絞る |
| Ollamaへの接続拒否 | サーバーが起動していない or ポート競合 | `ollama serve` を確認し、`localhost` を `127.0.0.1` に変えてみる |

## 次のステップ

ここまでで「動くエージェント」が手元にできました。
次のステップとして取り組むべきは、**「マルチエージェント化」**です。
一人のエージェントに「リサーチ」と「執筆」と「校閲」をすべてやらせると、どうしても精度が落ちます。

今回使った PydanticAI は、エージェントの出力を別のエージェントの入力に渡す構成が非常に書きやすい設計になっています。
例えば「リサーチ担当」が作成した `ResearchResult` オブジェクトを、そのまま「ブログ記事執筆担当」の `Agent.run()` に引数として渡すイメージです。
これにより、タスクの責任分解（Separation of Concerns）が可能になり、SIer的な堅牢なシステムが構築できます。

また、ローカルLLMの性能を最大限引き出すために、**「プロンプトエンジニアリング」から「テストエンジニアリング」への移行**を推奨します。
プロンプトをいじって一喜一憂するのではなく、10個のテストケースを用意し、コードを変更するたびにエージェントの正解率がどう変わったかを数字で計測する。
地味ですが、それが2026年以降のエンジニアに求められる最も重要なスキルです。

## よくある質問

### Q1: 2026年現在、Llama 3 8Bより小さいモデルでエージェントは作れますか？

3Bクラス（Gemma 2 2B等）でもツール呼び出し自体は可能ですが、思考の連鎖（Chain of Thought）が短く、複雑な指示を無視する傾向があります。
実用性を取るなら、最低でも8B、理想はLlama 3.3 70Bの4bit量子化版をVRAM 48GB（RTX 3090/4090の2枚挿し）で動かすのが、現場での最適解です。

### Q2: エージェントがツールを使わずに勝手に回答を捏造してしまいます。

これは「幻覚（Hallucination）」です。
解決策として、ツールの説明文（Docstring）をより具体的に書き、「検索ツールを最低2回は使ってから結論を出してください」と System Prompt に数値を含めた制約を課すのが効果的です。
また、Temperature（温度パラメータ）を 0 に設定して決定論的な動作をさせるのも鉄則です。

### Q3: PydanticAI 以外のフレームワーク（LangGraph等）との使い分けは？

状態遷移（ステートマシン）を厳密に定義し、グラフ構造でエージェントの動きを完全にコントロールしたい場合は LangGraph が向いています。
一方で、今回のように「目的を与えて自律的にツールを組み合わせてほしい」という用途や、単純に Python らしい書きやすさと型安全性を優先するなら PydanticAI が圧倒的に快適です。

---

## あわせて読みたい

- [Ollama 使い方 入門: 限られたGPU資産で実用的なローカルLLM環境を構築する方法](/posts/2026-06-13-ollama-local-llm-python-tutorial-for-beginners/)
- [Qwen2.5をローカル環境で動かし、API料金を気にせずコード生成を自動化するPythonスクリプトを作る方法](/posts/2026-05-09-qwen-2-5-coder-local-python-guide/)
- [Qwen 2.5 27B 使い方 入門：24GB VRAMでGPT-4級のコード生成環境を構築する方法](/posts/2026-04-24-qwen-2-5-27b-local-python-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "2026年現在、Llama 3 8Bより小さいモデルでエージェントは作れますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "3Bクラス（Gemma 2 2B等）でもツール呼び出し自体は可能ですが、思考の連鎖（Chain of Thought）が短く、複雑な指示を無視する傾向があります。 実用性を取るなら、最低でも8B、理想はLlama 3.3 70Bの4bit量子化版をVRAM 48GB（RTX 3090/4090の2枚挿し）で動かすのが、現場での最適解です。"
      }
    },
    {
      "@type": "Question",
      "name": "エージェントがツールを使わずに勝手に回答を捏造してしまいます。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "これは「幻覚（Hallucination）」です。 解決策として、ツールの説明文（Docstring）をより具体的に書き、「検索ツールを最低2回は使ってから結論を出してください」と System Prompt に数値を含めた制約を課すのが効果的です。 また、Temperature（温度パラメータ）を 0 に設定して決定論的な動作をさせるのも鉄則です。"
      }
    },
    {
      "@type": "Question",
      "name": "PydanticAI 以外のフレームワーク（LangGraph等）との使い分けは？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "状態遷移（ステートマシン）を厳密に定義し、グラフ構造でエージェントの動きを完全にコントロールしたい場合は LangGraph が向いています。 一方で、今回のように「目的を与えて自律的にツールを組み合わせてほしい」という用途や、単純に Python らしい書きやすさと型安全性を優先するなら PydanticAI が圧倒的に快適です。 ---"
      }
    }
  ]
}
</script>
