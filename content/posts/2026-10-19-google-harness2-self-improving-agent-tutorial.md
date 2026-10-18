---
title: "Google Harness2 使い方：自己改善型AIエージェントを構築する方法"
date: 2026-10-19T00:00:00+09:00
slug: "google-harness2-self-improving-agent-tutorial"
cover:
  image: "/images/posts/2026-10-19-google-harness2-self-improving-agent-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Google Harness2"
  - "自己改善型AI"
  - "AIエージェント 構築"
  - "Gemini API 使い方"
---
**所要時間:** 約45分 | **難易度:** ★★★★☆

## この記事で作るもの

Googleが公開したHarness2を利用し、AIエージェントがタスクの実行結果を自ら評価し、プロンプトや推論ステップを自動で修正・改善し続ける「自己改善ループ」を実装します。
Pythonを用いたプログラミングと、Gemini APIまたはローカルLLM（Ollama等）の連携ができれば、実務レベルの自律型エージェントの雛形が完成します。
必要なものは、Python環境とGoogle AI StudioのAPIキー、あるいはRTX 3060以上のGPUを搭載したPCです。

## 先に確認するスペック・料金

Harness2は「エージェントに何度も試行錯誤させる」性質上、トークン消費が激しくなります。
API利用の場合、Gemini 1.5 Flashなら100万トークンあたり$0.075程度と安価ですが、数百回の試行を回すと数ドル単位で課金されるため、無料枠の範囲内でテストすることをお勧めします。
ローカルで動かす場合は、VRAM 12GB以上のGPU（RTX 3060 12GB / 4070 Ti Super 16GB等）が最低ラインです。
私はRTX 4090の2枚挿しで検証していますが、推論速度がボトルネックになると改善ループの待ち時間が苦痛になるため、速度重視ならGemini 1.5 Flash、秘匿性重視ならLlama 3.1 8B (Q4_K_M) あたりが現実的な選択肢です。
Macユーザーなら、メモリ32GB以上のM2/M3プロセッサがあれば、Unified Memoryの恩恵で快適に動作します。

## なぜこの方法を選ぶのか

これまでAIエージェントの精度を上げるには、人間がプロンプトを書き直しては実行する「手動職人芸」が必要でした。
LangGraphやCrewAIも優秀ですが、それらは「構造」を定義するだけであり、中身の「質」を自動で高める仕組みは弱かったのが実情です。
Google Harness2は、エージェントの行動ログをスコアリングし、どのステップが失敗の原因だったかを特定して修正案を生成する「評価・改善の自動化」に特化しています。
SIer時代、テストコードを書く作業に工数の半分を奪われていた私からすれば、AIが勝手にテストし、勝手に実装を直してくるこの仕組みは、開発パラダイムの完全な転換だと確信しています。

## Step 1: 環境を整える

まずはHarness2のリポジトリをクローンし、依存関係を整理します。
Googleの公式ツールは依存ライブラリが重なることが多いため、必ず仮想環境（venvやconda）を作成してください。

```bash
# 仮想環境の作成とアクティベート
python -m venv harness_env
source harness_env/bin/activate  # Windowsなら .\harness_env\Scripts\activate

# Harness2のインストール（GitHubから直接取得）
git clone https://github.com/google-research/harness2.git
cd harness2
pip install -e .

# 補助的に使用するライブラリも入れておく
pip install python-dotenv langchain-google-genai tqdm
```

`pip install -e .` を使うのは、Harness2自体のソースコードを読みながら、必要に応じて内部の評価ロジックを微調整できるようにするためです。
開発が活発なライブラリを触る時は、この編集可能（Editable）インストールが鉄則です。

⚠️ **落とし穴:**
Python 3.12系では一部の依存ライブラリ（特に古いコンパイル済みパッケージ）がエラーを吐くことがあります。
安定性を重視するなら Python 3.10.x または 3.11.x を使用してください。
また、`setuptools`が古いとインストールに失敗するため、事前に `pip install -U setuptools` を実行しておきましょう。

## Step 2: 基本の設定

Harness2を動かすための設定ファイルと、環境変数の読み込みを行います。
今回は、最も手軽で高速な Gemini 1.5 Flash をメインエンジンに据えます。

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# .envファイルからAPIキーを読み込む
# APIキーは直接コードに書かず、環境変数で管理するのが実務の常識です
load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEYが設定されていません。AI Studioで発行してください。")

# 改善プロセスを保存するディレクトリの設定
# 試行錯誤のプロセスをログとして残すことで、後で「なぜその修正が行われたか」を分析できます
LOG_DIR = Path("./harness_logs")
LOG_DIR.mkdir(exist_ok=True)

print(f"環境準備完了: ログ出力先 -> {LOG_DIR}")
```

APIキーの発行は「Google AI Studio」から無料で行えます。
Rate Limit（リクエスト制限）に引っかからないよう、無料枠でも1分間に15リクエスト程度は許容される設定にしておくのがコツです。

## Step 3: 動かしてみる

Harness2の核となる「評価ループ」を構築します。
ここでは「入力された数式を解き、Pythonコードで検証する」という、失敗が明確に定義できるタスクを例にします。

```python
from harness2.agents import BaseAgent
from harness2.evaluators import CodeEvaluator
from harness2.loop import ImprovementLoop

# 1. エージェントの定義
# ここでは「Pythonコードを生成して数学問題を解く」エージェントを想定します
class MathAgent(BaseAgent):
    def __init__(self, model_name="gemini-1.5-flash"):
        self.model = model_name

    def run(self, task_description):
        # タスクを解くための推論プロセスを生成
        prompt = f"以下の課題をPythonコードで解決してください:\n{task_description}"
        # ここでLLMを呼び出し（擬似コード）
        response = call_llm(self.model, prompt)
        return response

# 2. 評価器（Evaluator）の設定
# 生成されたコードが正しい答えを出すか、実行して検証します
evaluator = CodeEvaluator(timeout=10)

# 3. 自己改善ループの構築
loop = ImprovementLoop(
    agent=MathAgent(),
    evaluator=evaluator,
    max_iterations=3  # 最大3回まで自分自身を修正させる
)

# 実行
task = "1から100までの素数の合計を求めてください。"
final_result = loop.run(task)

print(f"最終結果: {final_result.output}")
print(f"改善回数: {final_result.iteration_count}")
```

### 期待される出力

```
[Iteration 1] 評価スコア: 0.0 (エラー: SyntaxError)
[Iteration 1] 修正プロセス開始: プロンプトに「インデントを正確に」という制約を追加します。
[Iteration 2] 評価スコア: 1.0 (正解: 1060)
[Success] 2回目の試行でタスクを完了しました。
```

Harness2が優れているのは、単に「やり直せ」と言うのではなく、前の失敗（SyntaxErrorなど）を文脈として保持し、次の試行でそれを回避する「メタ・プロンプト」を自動生成する点にあります。

## Step 4: 実用レベルにする

実務では、単なる計算ではなく「複雑なJSONデータの整形」や「ドキュメントの要約」など、正解が一意に定まらないタスクを扱います。
この場合、LLM自身を評価器にする「LLM-as-a-Judge」を組み込みます。

```python
from harness2.evaluators import LLMEvaluator

# ビジネス文書のトーンを評価するカスタム評価器
judge_prompt = """
以下の文章が、専門家として適切で、論理的な構造になっているかを0.0〜1.0で採点してください。
理由も簡潔に添えること。
"""

business_evaluator = LLMEvaluator(
    model="gemini-1.5-pro", # 評価にはより賢いモデルを使うのが定石
    criteria=judge_prompt
)

# 実用的なエラーハンドリングを加えたループ
try:
    loop = ImprovementLoop(
        agent=MathAgent(model_name="gemini-1.5-flash"),
        evaluator=business_evaluator,
        max_iterations=5
    )
    result = loop.run("新製品『AI-Core』のプレスリリース原稿を作成してください。")
except ConnectionError as e:
    print(f"ネットワークエラーが発生しました。リトライを検討してください: {e}")
except Exception as e:
    print(f"予期しないエラー: {e}")

# ログをファイルに書き出す
with open(LOG_DIR / "session_report.md", "w") as f:
    f.write(result.full_history_markdown())
```

「評価には、実行エージェントより一段階上のモデル（Flashに対してProなど）を使う」のが、精度を安定させる秘訣です。
これは、学生（エージェント）の解答を先生（上位モデルの評価器）が添削する構図を作るためです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Rate Limit Exceeded | 無料枠で短時間にリクエストしすぎ | `time.sleep()`をループに入れるか、有料ティアへ移行 |
| Infinite Loop | 改善策がループし、スコアが上がらない | `max_iterations`を低めに設定し、改善プロンプトを具体化する |
| ModuleNotFoundError | Harness2の内部パスが通っていない | `pip install -e .` を実行したディレクトリを確認する |

## 次のステップ

この記事で、Harness2を使って「AIが自ら考えて改善する」第一歩を踏み出しました。
次にやるべきことは、この改善ループを「データの質を上げる」ために使うことです。
例えば、手元にある汚いCSVデータを読み込ませ、LLMにクレンジングコードを書かせ、その実行結果が期待通り（欠損値ゼロ、型不一致ゼロなど）になるまで自己修正させるスクリプトを書いてみてください。

また、ローカルLLM派の方は、Geminiの代わりに `Ollama` や `vLLM` をバックエンドに接続することに挑戦してください。
Harness2の `BaseAgent` を継承して、`requests` ライブラリでローカルサーバーのAPIを叩くように書き換えるだけで、完全オフラインの自己改善エージェントが構築できます。
私はこの仕組みを使い、深夜のサーバーでドキュメントの自動整理を24時間回し続けていますが、朝起きるたびにプロンプトが洗練されていく様子を見るのは、エンジニアとしての至福の瞬間です。

## よくある質問

### Q1: Gemini以外のAPI（OpenAIやClaude）でも使えますか？

はい、使えます。Harness2は抽象化されているため、BaseAgentクラスをラップしてOpenAIのSDKを呼び出すように書き換えるだけです。ただし、Google製のツールなのでGeminiとの親和性が最も高く、設定が容易です。

### Q2: 改善ループが無限に回って課金が怖いです。止める方法は？

`ImprovementLoop` の引数にある `max_iterations` を必ず設定してください。デフォルトで無制限になっていることは稀ですが、明示的に3〜5回に制限しておくのが安全です。また、一定スコア（例: 0.95）を超えたら即座に終了する終了条件も実装可能です。

### Q3: ローカルLLMで動かす場合、どのモデルがおすすめですか？

自己改善の文脈を理解するには、最低でも Llama 3.1 8B 以上の賢さが必要です。4ビット量子化モデルなら VRAM 8GB でも動きますが、改善の質を求めるなら 70B クラスのモデルを 4090 の 2 枚挿し（あるいは Mac の大容量メモリ）で回すのが理想的です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4070 Ti Super 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBを搭載し、ローカルLLMでの改善ループを現実的な速度で回せるコスパ機</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204070%2520Ti%2520Super%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204070%2520Ti%2520Super%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204070%20Ti%20Super%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [AIエージェント実行環境をE2Bで安全に構築する方法](/posts/2026-09-06-ai-agent-sandbox-e2b-python-guide/)
- [AIエージェントをDockerで安全に動かすサンドボックス構築方法](/posts/2026-08-17-ai-agent-safe-docker-sandbox-tutorial/)
- [ローカルAIエージェント特化モデルMuse GlimmerおすすめPC構成と比較](/posts/2026-08-11-muse-glimmer-local-agent-gpu-comparison/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Gemini以外のAPI（OpenAIやClaude）でも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、使えます。Harness2は抽象化されているため、BaseAgentクラスをラップしてOpenAIのSDKを呼び出すように書き換えるだけです。ただし、Google製のツールなのでGeminiとの親和性が最も高く、設定が容易です。"
      }
    },
    {
      "@type": "Question",
      "name": "改善ループが無限に回って課金が怖いです。止める方法は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ImprovementLoop の引数にある maxiterations を必ず設定してください。デフォルトで無制限になっていることは稀ですが、明示的に3〜5回に制限しておくのが安全です。また、一定スコア（例: 0.95）を超えたら即座に終了する終了条件も実装可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "ローカルLLMで動かす場合、どのモデルがおすすめですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "自己改善の文脈を理解するには、最低でも Llama 3.1 8B 以上の賢さが必要です。4ビット量子化モデルなら VRAM 8GB でも動きますが、改善の質を求めるなら 70B クラスのモデルを 4090 の 2 枚挿し（あるいは Mac の大容量メモリ）で回すのが理想的です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4070 Ti Super 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBを搭載し、ローカルLLMでの改善ループを現実的な速度で回せるコスパ機</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204070%2520Ti%2520Super%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204070%2520Ti%2520Super%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204070%20Ti%20Super%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
