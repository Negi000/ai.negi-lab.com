---
title: "MLX 使い方 入門：Apple Silicon MacでLLMを爆速化する方法"
date: 2026-10-24T00:00:00+09:00
slug: "apple-silicon-mlx-llm-getting-started-guide"
cover:
  image: "/images/posts/2026-10-24-apple-silicon-mlx-llm-getting-started-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "ローカルLLM Mac"
  - "mlx-lm チュートリアル"
---
**所要時間:** 約30分 | **難易度:** ★★★☆☆

## この記事で作るもの

Apple製の機械学習フレームワーク「MLX」を使い、MacのGPU性能を最大限に引き出してLlama 3やGemma 2などの最新LLMを爆速で動かすPythonスクリプトを作成します。
単に動かすだけでなく、業務でそのまま使える「ストリーミング出力」と「トークン生成速度の計測」を実装した実戦的なコードを構築します。
Pythonの仮想環境が作れて、ターミナルでコマンドが打てる程度の知識があれば完結できます。

## 先に確認するスペック・料金

MLXはApple Silicon（M1/M2/M3/M4チップ）専用のライブラリです。
Intel Macでは動作しないため、まずは自分のMacがApple製チップであることを確認してください。
最も重要なスペックは「ユニファイドメモリ（RAM）」の容量で、8GBモデルだと7B（70億パラメータ）クラスのモデルを動かすのが限界です。

快適に開発を行うなら、最低でも16GB、できれば32GB以上のメモリを積んだモデルを推奨します。
ローカルLLMはVRAMではなくメインメモリを直接消費するため、ブラウザやSlackを立ち上げたままだとメモリ不足でスワップが発生し、極端に動作が重くなります。
現在8GBモデルを使っているなら、買い替え検討のタイミングかもしれません。
ソフト面では、macOS 13.5以上が必要ですが、パフォーマンスの観点から最新のmacOSへのアップデートを強く推奨します。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす手法には、llama.cppやOllamaなどもあります。
しかし、Pythonエンジニアが「自分のプログラムに組み込みたい」と考えるなら、MLX（mlx-lm）がベストな選択肢です。
理由は、AppleのエンジニアがApple SiliconのGPU/NPUに最適化して開発しているため、PyTorchをそのまま動かすよりも推論速度（tokens/sec）が1.5倍〜2倍近く速くなるケースが多いからです。

また、メモリ効率を最大化する「量子化（Quantization）」が標準で組み込まれており、Hugging Faceにある数千のモデルを一行のコマンドでダウンロードしてすぐに実行できるエコシステムが整っています。
開発速度が非常に早く、最新のモデル（Llama 3.1やMistral Nemoなど）が発表された数時間後にはMLX対応版が有志によってアップロードされる点も、他のフレームワークにはない強みです。

## Step 1: 環境を整える

まずはMLX専用のPython仮想環境を作成します。
システム全体のPython環境を汚すと、後で依存関係の地獄に陥るため、必ず仮想環境を分けてください。

```bash
# プロジェクト用のディレクトリ作成
mkdir mlx-test && cd mlx-test

# Python 3.11以上を推奨（3.12でも動作確認済み）
python3 -m venv .venv

# 仮想環境の有効化
source .venv/bin/activate

# mlx-lmのインストール
pip install -U mlx-lm
```

`mlx-lm`は、MLXをLLM向けに使いやすくラップしたライブラリです。
これ一つでモデルのダウンロード、量子化、推論のすべてが完結します。
ライブラリのアップデートが非常に頻繁なため、常に `-U` オプションをつけて最新版を入れる癖をつけておきましょう。

⚠️ **落とし穴:**
Xcode Command Line Toolsがインストールされていないと、インストール中にビルドエラーが発生することがあります。エラーが出た場合は `xcode-select --install` を実行してツールを導入してください。

## Step 2: 基本の設定

次に、Pythonスクリプトを作成します。
ここでは、単に文字を出すだけでなく、メモリ管理やモデルのロード設定を適切に行うための初期化コードを書きます。

```python
# main.py
import time
from mlx_lm import load, generate

# 使用するモデルの指定
# 16GBメモリなら 4-bit量子化モデルを推奨
model_path = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"

print(f"Loading model: {model_path}...")
start_time = time.time()

# モデルとトークナイザーをロード
# tokenizer_config={"trust_remote_code": True} は、一部の特殊なモデルを動かす際に必要
model, tokenizer = load(model_path)

load_time = time.time() - start_time
print(f"Model loaded in {load_time:.2f} seconds.")
```

ここで `mlx-community` が提供している4-bit量子化モデルを指定するのがコツです。
FP16（量子化なし）のモデルを読み込もうとすると、16GBメモリのMacでは一瞬でメモリ不足になり、OSごとフリーズする可能性があります。
4-bitであれば、8Bパラメータのモデルでも5GB程度のメモリ消費で済むため、非常に安定して動作します。

## Step 3: 動かしてみる

いよいよ推論を実行します。
実務でLLMを使う場合、すべての回答が生成されるまで待つのはUXが悪すぎるため、一文字ずつ出力される「ストリーミング」での実装が必須です。

```python
# main.py の続き

prompt = "Apple Siliconのすごさを、エンジニアの視点で3行で教えて。"

# Llama 3などのInstructモデルには特定のフォーマットが必要
# apply_chat_template を使うことで、モデルに最適なプロンプト形式に自動変換される
messages = [{"role": "user", "content": prompt}]
prompt_templated = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)

print("-" * 30)
print(f"Prompt: {prompt}")
print("-" * 30)

# 推論実行
# max_tokens: 生成する最大長。短すぎると途中で切れる
# temp: 0に近づけるほど決定的（真面目）、1に近づけるほど創造的（遊び）になる
response = generate(
    model,
    tokenizer,
    prompt=prompt_templated,
    max_tokens=500,
    temp=0.7,
    verbose=True # ターミナルに生成過程をストリーミング表示する
)

print("-" * 30)
```

### 期待される出力

```
Loading model: mlx-community/Meta-Llama-3.1-8B-Instruct-4bit...
Model loaded in 2.15 seconds.
------------------------------
Prompt: Apple Siliconのすごさを、エンジニアの視点で3行で教えて。
------------------------------
1. ユニファイドメモリ構造により、巨大なLLMモデルをGPU/CPU間でデータ転送するオーバーヘッドなしに高速処理できる点。
2. ワットパフォーマンスが圧倒的で、ファンが回らない静寂な環境のまま、数億パラメータの推論をローカルで完結できる点。
3. MLXのような専用フレームワークとの密結合により、ハードウェアの演算器（AMX等）を直接叩いて性能を出し切れる点。

Prompt: 38.25 tokens-per-sec
Generation: 22.10 tokens-per-sec
```

注目すべきは `tokens-per-sec` です。
M2 Pro以上のチップであれば、20〜40 tokens/sec程度の速度が出るはずです。
これは人間が文章を読む速度を遥かに上回っており、実務利用においてストレスを感じないレベルです。

## Step 4: 実用レベルにする

実際の仕事で使うなら、回答をJSON形式で受け取ったり、特定の構造に従わせたりしたい場面があります。
MLX単体でも可能ですが、ここでは「生成速度を正確に計測し、ログに残す」という実用的なラッパークラスを作成します。
これにより、モデルごとのパフォーマンス比較ができるようになります。

```python
import time
from mlx_lm import load, generate

class LocalLLMEngine:
    def __init__(self, model_id):
        self.model, self.tokenizer = load(model_id)

    def ask(self, question):
        messages = [{"role": "user", "content": question}]
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        start_gen = time.perf_counter()
        # verbose=Falseにして自分で出力をコントロールする
        output = generate(
            self.model, self.tokenizer, prompt=prompt, max_tokens=1000
        )
        end_gen = time.perf_counter()

        duration = end_gen - start_gen
        # おおよそのトークン数を計算
        token_count = len(self.tokenizer.encode(output))
        tps = token_count / duration

        return {
            "answer": output,
            "tokens_per_sec": round(tps, 2),
            "duration_sec": round(duration, 2)
        }

# 使用例
engine = LocalLLMEngine("mlx-community/Meta-Llama-3.1-8B-Instruct-4bit")
result = engine.ask("Pythonで素数を判定する最も効率的なコードを書いて。")

print(f"Answer:\n{result['answer']}")
print(f"Stats: {result['tokens_per_sec']} tokens/s, {result['duration_sec']}s")
```

このクラス化により、例えば複数の質問をリストで渡し、一括で処理してログに保存するといったバッチ処理への拡張が容易になります。
また、`generate`関数の引数に `stop` を追加することで、特定の文字列が出現した瞬間に生成を止める（プログラミング時のガードレール）といった制御も可能になります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `zsh: command not found: pip` | Python環境が正しく設定されていない | `python3 -m pip` を使うか、仮想環境をアクティベートする |
| `Killed` または `Memory Error` | 物理メモリ不足（Swapも限界） | モデルを 4-bit もしくは 2-bit 量子化のものに変える。ブラウザのタブを閉じる。 |
| 出力が文字化けする | モデルとトークナイザーの不一致 | `mlx-community` など信頼できるソースのモデルを使い、キャッシュを削除して再試行する |
| 推論が異様に遅い | GPUが使われていない、またはバックグラウンドで重い処理中 | `Activity Monitor` の「GPU履歴」を確認。他のGPU負荷が高いアプリを終了する。 |

## 次のステップ

MLXでローカルLLMを動かすことに成功したら、次は「RAG（検索拡張生成）」への組み込みに挑戦してください。
自分のPC内にあるPDFやMarkdownファイルをベクタライズし、MLX経由でLLMに読み込ませることで、ネットに繋がない「自分専用のセキュアなAI検索エンジン」が構築できます。

また、MLXは推論だけでなく「LoRA（Low-Rank Adaptation）」を用いたファインチューニング（追加学習）もサポートしています。
自分の過去のメールやチャット履歴をMLXで学習させれば、自分の口癖や思考パターンを模倣したAIを数分で作成することも可能です。
これらはすべて、外部のAPIに1円も払うことなく、あなたのMacの中で完結します。

## よくある質問

### Q1: メモリ8GBのMacBook Airでも動きますか？

結論、動きますがモデル選びがシビアです。
4-bit量子化した7B（Llama 3やMistral）なら動きますが、メモリの空きがカツカツになるため、他のアプリをすべて閉じる必要があります。快適さを求めるなら、3.5Bクラス（Phi-3 miniなど）のモデルを選ぶのが賢明です。

### Q2: MLXとOllama、どっちを使うべきですか？

「とにかく手軽にチャットしたい」ならOllamaです。
一方で、「Pythonプログラムの一部として組み込みたい」「独自の推論ロジックを書きたい」「特定のモデルを自分で量子化したい」というエンジニアリング用途であれば、MLX一択です。

### Q3: GPUではなくNPUは使われないのですか？

MLXは現状、主にGPU（Metal）とCPUを利用します。
Apple SiliconのNPU（Neural Engine）は、主にCore ML経由の推論で威力を発揮しますが、大規模言語モデルのような巨大なウェイトを扱う計算では、メモリ帯域の広いGPUの方が有利なため、MLXは意図的にGPU最適化を優先しています。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac Studio</strong>
<p style="color:#555;margin:8px 0;font-size:14px">ユニファイドメモリ64GBなら30B以上の大型モデルもローカルで余裕を持って動かせる</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを高速動作させる方法](/posts/2026-09-01-mlx-apple-silicon-local-llm-tutorial/)
- [MLX 使い方 入門：Apple SiliconでLLMを爆速動作させる](/posts/2026-07-22-mlx-apple-silicon-local-llm-guide/)
- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを高速に動かす方法](/posts/2026-08-04-mlx-apple-silicon-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "メモリ8GBのMacBook Airでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "結論、動きますがモデル選びがシビアです。 4-bit量子化した7B（Llama 3やMistral）なら動きますが、メモリの空きがカツカツになるため、他のアプリをすべて閉じる必要があります。快適さを求めるなら、3.5Bクラス（Phi-3 miniなど）のモデルを選ぶのが賢明です。"
      }
    },
    {
      "@type": "Question",
      "name": "MLXとOllama、どっちを使うべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "「とにかく手軽にチャットしたい」ならOllamaです。 一方で、「Pythonプログラムの一部として組み込みたい」「独自の推論ロジックを書きたい」「特定のモデルを自分で量子化したい」というエンジニアリング用途であれば、MLX一択です。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUではなくNPUは使われないのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MLXは現状、主にGPU（Metal）とCPUを利用します。 Apple SiliconのNPU（Neural Engine）は、主にCore ML経由の推論で威力を発揮しますが、大規模言語モデルのような巨大なウェイトを扱う計算では、メモリ帯域の広いGPUの方が有利なため、MLXは意図的にGPU最適化を優先しています。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Mac Studio</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">ユニファイドメモリ64GBなら30B以上の大型モデルもローカルで余裕を持って動かせる</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
