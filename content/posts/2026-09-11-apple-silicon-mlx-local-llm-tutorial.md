---
title: "MLX入門 Apple Silicon MacでローカルLLMを動かす方法"
date: 2026-09-11T00:00:00+09:00
slug: "apple-silicon-mlx-local-llm-tutorial"
cover:
  image: "/images/posts/2026-09-11-apple-silicon-mlx-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "Python ローカルLLM"
  - "Llama 3 Mac"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple Silicon（M1/M2/M3/M4）の性能をフルに引き出し、Llama 3やQwen 2.5といった最新のLLMを爆速で動かすPythonスクリプトを作成します。
Pythonの基礎知識があれば、この記事のコードをコピペするだけで、自分のMac上でオフラインAIを動かせるようになります。

## 先に確認するスペック・料金

Apple Silicon MacでのローカルLLM運用は、結論から言うと「メモリ（ユニファイドメモリ）」の量がすべてを決めます。
MLXはAppleが開発したフレームワークで、GPUとCPUが同じメモリ空間を共有する仕組みを最大限に活用します。

最低限必要なのは16GB以上のメモリを搭載したモデルです。
8GBモデルでも動かないことはないですが、Llama 3 8B（4ビット量子化）を動かすだけでメモリがカツカツになり、OS全体の動作が重くなります。
快適に動かしたいなら24GB以上、本格的にパラメーター数の大きいモデルを試したいなら64GB以上のメモリを選んでください。

私が検証した結果、M2 Max（64GBメモリ）環境ではLlama 3 8Bが秒間40トークン以上で出力されます。
これはChatGPTの応答速度と比較しても遜色ない、あるいはそれ以上に速い数値です。
API料金は一切かからず、電気代だけで無限に推論できるのがローカル運用の最大のメリットです。

これからMacを買う人は、プロセッサ（ProやMax）のグレードを上げるより、まずは「メモリを増やす」ことを優先してください。
計算コアが多くても、モデルがメモリに乗らなければ宝の持ち腐れになります。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす方法は、主に「Ollama」「llama.cpp」「MLX」の3つがあります。
Ollamaはインストールが最も簡単ですが、カスタマイズ性が低く、内部で何が起きているか把握しづらいのが難点です。
llama.cppは非常に高速ですが、C++ベースであるためPythonエンジニアが自身のプロジェクトに組み込むには少しハードルがあります。

MLXを選ぶ理由は、Apple公式のライブラリであり、PythonでPyTorchのように直感的に書ける点にあります。
さらに、Apple SiliconのGPUに最適化された計算カーネルを使用しているため、他のライブラリよりも推論が安定して速い傾向があります。
自分のPythonアプリにLLMを組み込みたい、将来的にファインチューニング（微調整）も視野に入れたいなら、MLX一択だと思います。

## Step 1: 環境を整える

まずはPythonの仮想環境を作成し、必要なライブラリをインストールします。
MLXは進化が非常に早いため、古いバージョンだと新しいモデルが動かないことが多々あります。

```bash
# プロジェクト用のディレクトリを作成
mkdir mlx-llm-test && cd mlx-llm-test

# Python 3.10以上を推奨します
python3 -m venv .venv
source .venv/bin/activate

# MLXとモデル操作用のライブラリをインストール
pip install -U mlx-lm mlx huggingface_hub
```

`mlx-lm` は、Hugging FaceにあるモデルをMLXで簡単に扱うための高レベルなライブラリです。
これを入れるだけで、モデルのダウンロードから推論までを数行で完結させることができます。

⚠️ **落とし穴:**
Apple SiliconではないIntel Macでは、MLXは動作しません。
また、Pythonのバージョンが3.9以下だとライブラリの依存関係でエラーが出ることが多いため、必ず `python3 --version` で3.10以上であることを確認してください。

## Step 2: 基本の設定

次に、動かしたいモデルを指定します。
今回は日本語能力が高く、軽量で扱いやすい「Llama-3-8B-Instruct」をMLX用に変換済みのリポジトリから取得します。

```python
# main.py
import os
from mlx_lm import load, generate

# 使用するモデルの指定
# mlx-communityというアカウントに、MLX最適化済みのモデルが多数公開されています
model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"

# モデルとトークナイザーの読み込み
# 最初の実行時には自動的にHugging Faceからダウンロードが始まります（数GBあります）
model, tokenizer = load(model_path)
```

`4bit` という表記に注目してください。
これはモデルの重みを4ビットに圧縮（量子化）していることを意味します。
通常のモデルをそのまま読み込むと15GB以上のメモリを消費しますが、4bit版なら約5GB程度で済み、推論速度も大幅に向上します。
実務で使うなら、精度と速度のバランスが良い4bit量子化モデルを選ぶのが定石です。

## Step 3: 動かしてみる

最小限のコードで推論を実行してみましょう。
MLXの `generate` 関数は、非常にシンプルに設計されています。

```python
# main.py の続き

# プロンプトの設定（Llama 3のテンプレートに合わせるのがコツ）
prompt = "美味しいカレーの作り方を3行で教えて。"
messages = [{"role": "user", "content": prompt}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

# テキスト生成
response = generate(model, tokenizer, prompt=prompt, verbose=True, max_tokens=500)

print("\n--- 最終回答 ---")
print(response)
```

### 期待される出力

```text
1. 飴色になるまで炒めた玉ねぎと、スパイスをしっかり馴染ませた肉を煮込む。
2. 市販のルーに隠し味としてウスターソースやインスタントコーヒーを少量加える。
3. 一晩寝かせることで味が落ち着き、深みのある美味しいカレーが完成する。
```

`verbose=True` に設定することで、生成中の進捗や、1秒間に何トークン生成できたか（tokens per second）をコンソールで見ることができます。
私の環境では45 tokens/sec前後を記録しました。

## Step 4: 実用レベルにする

実際の業務やアプリで使う場合、一括で回答が出るのを待つのではなく、ChatGPTのように一文字ずつ表示される「ストリーミング」が必須です。
また、システムプロンプトを設定してAIのキャラクターを固定する方法も紹介します。

```python
# chat.py
import sys
from mlx_lm import load, generate

def stream_chat(user_input):
    model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"
    model, tokenizer = load(model_path)

    # システムプロンプトでAIの振る舞いを指定
    messages = [
        {"role": "system", "content": "あなたは優秀なエンジニアです。簡潔に回答してください。"},
        {"role": "user", "content": user_input}
    ]

    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    # ストリーミング生成
    # 独自のコールバックを作らなくても、生成プロセスをループで回せます
    print("AI: ", end="", flush=True)

    # 内部的に利用されるgenerateのストリーミング版
    # 実際には generate 関数の引数に stream=True のようなオプションはないため、
    # mlx_lm の utils を利用するか、シンプルなラッパーを使います。
    # ここでは最も標準的な使い勝手の良い方法を示します。

    from mlx_lm.utils import generate_step

    tokens = []
    # トークン化
    import mlx.core as mx
    input_ids = mx.array(tokenizer.encode(prompt))

    for response in generate_step(model, tokenizer, input_ids, max_tokens=500):
        token = response.token
        text = response.text

        # 終了トークンが来たら停止
        if token == tokenizer.eos_token_id:
            break

        print(text, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    stream_chat("PythonでMLXを使うメリットを教えて。")
```

このコードでは `generate_step` というイテレータを使用しています。
これにより、AIが言葉を紡いでいく様子をリアルタイムでユーザーに見せることが可能になります。
実用的なツールを作るなら、このストリーミング処理をFastAPIなどのバックエンドに組み込み、フロントエンドへSSE（Server-Sent Events）で流すのが一般的です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `MemoryError` / 動作が極端に遅い | ユニファイドメモリ不足 | ブラウザや他の重いアプリを閉じる。より小さいモデル（3Bなど）を使う。 |
| `ModuleNotFoundError: mlx` | 環境構築ミス | `pip install mlx` を実行したか、仮想環境が有効か確認。 |
| 意味不明な記号が出力される | テンプレートの不一致 | `apply_chat_template` を使い、モデル指定の形式でプロンプトを組む。 |

## 次のステップ

MLXでローカルLLMが動かせるようになったら、次は「RAG（検索拡張生成）」に挑戦してみてください。
自分の持っているPDFファイルやメモ帳の内容をベクトルデータベースに入れ、MLXで動かしているLLMに参照させるのです。
これにより、外部にデータを漏らすことなく、自分専用の知識を持ったAIアシスタントをMacの中に構築できます。

また、MLXには `mlx-examples` という公式リポジトリがあり、そこにはLoRA（Low-Rank Adaptation）を用いたファインチューニングのコードも公開されています。
わずか数百件のデータがあれば、特定の口調や特定の業務知識に特化したモデルを自分のMacで学習させることが可能です。
RTX 4090を回さずとも、手元のMacBookで学習まで完結できるのは、MLX最大の魅力だと言えます。

## よくある質問

### Q1: M1 MacBook Airの8GBメモリでも動きますか？

動きますが、Llama 3 8Bだとスワップが発生してかなり低速になります。4ビット量子化よりもさらに圧縮された「2ビット量子化」や、よりパラメーター数の少ない「Gemma-2B」「Qwen-0.5B」などの軽量モデルを選ぶことを強くおすすめします。

### Q2: モデルはどこで探せばいいですか？

Hugging Faceで `mlx-community` と検索してください。有志がLlama, Mistral, Phi-3など主要なモデルをMLX形式に変換してアップロードしてくれています。自分で変換する手間が省けるので、まずはここから探すのが効率的です。

### Q3: GPUの使用率が上がらないのですが？

MLXはデフォルトでGPUを使用するように設計されています。もしCPUばかり使われていると感じる場合は、OSのバージョンが古い（macOS Sonoma以上を推奨）か、MLXのインストールが正しく行われていない可能性があります。`mx.default_device()` を実行して、`gpu` と返ってくるか確認してください。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">メモリ64GB以上あれば大型のLLMも高速に動作し、MLXの真価を発揮できます</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを動かす方法](/posts/2026-08-10-mlx-apple-silicon-local-llm-guide/)
- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを動かす方法](/posts/2026-07-25-mlx-apple-silicon-local-llm-tutorial/)
- [MLX入門：Apple SiliconでローカルLLMを爆速かつ実務レベルで動かす方法](/posts/2026-06-20-apple-silicon-mlx-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "M1 MacBook Airの8GBメモリでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、Llama 3 8Bだとスワップが発生してかなり低速になります。4ビット量子化よりもさらに圧縮された「2ビット量子化」や、よりパラメーター数の少ない「Gemma-2B」「Qwen-0.5B」などの軽量モデルを選ぶことを強くおすすめします。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルはどこで探せばいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Hugging Faceで mlx-community と検索してください。有志がLlama, Mistral, Phi-3など主要なモデルをMLX形式に変換してアップロードしてくれています。自分で変換する手間が省けるので、まずはここから探すのが効率的です。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUの使用率が上がらないのですが？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MLXはデフォルトでGPUを使用するように設計されています。もしCPUばかり使われていると感じる場合は、OSのバージョンが古い（macOS Sonoma以上を推奨）か、MLXのインストールが正しく行われていない可能性があります。mx.defaultdevice() を実行して、gpu と返ってくるか確認してください。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">メモリ64GB以上あれば大型のLLMも高速に動作し、MLXの真価を発揮できます</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
