---
title: "MLX 使い方 Apple Silicon ローカルLLM 入門"
date: 2026-11-02T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-tutorial"
cover:
  image: "/images/posts/2026-11-02-mlx-apple-silicon-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX"
  - "Apple Silicon"
  - "Llama 3"
  - "ローカルLLM 構築"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple純正の機械学習フレームワーク「MLX」を利用して、Mac上でLlama 3などの最新LLMを高速に動作させるPythonチャットスクリプトを作成します。
この記事を読み終える頃には、外部APIを一切使わず、完全にオフラインで動作する自分専用のAIチャット環境が手に入ります。

- 前提知識: Pythonの基本的な読み書き、ターミナルの操作ができること
- 必要なもの: Apple Silicon（M1/M2/M3/M4チップ）搭載のMac、macOS 13.5以上

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのはチップの種類ではなく「搭載メモリ（RAM）の量」です。
Apple SiliconはCPUとGPUでメモリを共有する「ユニファイドメモリ」を採用しているため、VRAMという概念を意識せずに大容量モデルを扱えるのが最大の強みです。

最低ラインはメモリ8GBですが、OSやブラウザがメモリを消費することを考えると、快適に動かすには16GB以上を強く推奨します。
もし8GBモデルを使っているなら、動作させるモデルを「4-bit量子化」された軽量なものに限定する必要があります。
逆に32GB以上のメモリがあれば、70Bクラス（700億パラメータ）の巨大なモデルも、速度を妥協すれば動かすことが可能です。

コストに関しては、自分のMacで計算を行うため、API使用料のような従量課金は一切発生しません。
電気代と初期のハードウェア代だけで、24時間365日回し放題の環境が手に入ります。
これからMacを買い増す予定があるなら、迷わず「メモリが一番多いモデル」を選んでください。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす方法は、 llama.cpp や Ollama など他にもいくつか存在します。
しかし、Pythonエンジニアが「実務に組み込む」という視点で選ぶなら、Apple公式の MLX がベストな選択肢です。

MLXはApple Siliconのハードウェア特性を最大限に引き出すよう設計されており、配列演算がGPUに直接最適化されています。
特に MLX-LM というライブラリを使えば、Hugging Faceにある数千ものモデルを数行のコードで呼び出せるようになります。
PyTorchに近い記法で書けるため、将来的にRAG（検索拡張生成）の実装や自前データのファインチューニングへステップアップする際も、学習コストを最小限に抑えられます。

## Step 1: 環境を整える

まずはMLXを動かすためのクリーンなPython環境を作成します。
ライブラリの依存関係によるトラブルを避けるため、プロジェクトごとに仮想環境を分けるのが鉄則です。

```bash
# プロジェクト用のディレクトリを作成
mkdir mlx-test && cd mlx-test

# Python 3.10以上が必要です
python3 -m venv .venv
source .venv/bin/activate

# MLXライブラリ本体と、LLM操作用ライブラリをインストール
pip install -U mlx-lm
```

`mlx-lm` は、MLXの機能をLLM（大規模言語モデル）向けにラップしたライブラリです。
これ一つ入れるだけで、モデルのダウンロード、テキスト生成、トークナイズまで一括で扱えるようになります。

⚠️ **落とし穴:**
macOSのバージョンが古いと、MLXのインストールに失敗したり、実行時にコアダンプを吐いて落ちることがあります。
macOS 13.5以降（できれば最新のSonomaかSequoia）であることを必ず確認してください。
また、Pythonは3.10から3.12の間であれば安定して動作することを確認済みです。

## Step 2: 基本の設定

次に、動かしたいモデルを選定してスクリプトを準備します。
今回は、日本語能力が高く軽量な「Llama-3-8B」の4bit量子化版を使用します。

```python
import os
from mlx_lm import load, generate

# モデルを指定（Hugging Face上のリポジトリ名）
# 4bit版を使うのは、メモリ消費を抑えつつ推論速度を上げるためです
model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"

# モデルとトークナイザーをロード
# 初回実行時は自動的に数GBのファイルがダウンロードされます
model, tokenizer = load(model_path)
```

ここで `mlx-community` が提供しているモデルを指定するのがポイントです。
彼らはHugging Face上の人気モデルをMLX形式に変換して公開してくれている有志グループで、自分で変換する手間を省けます。
なぜ「4bit」を選ぶのかというと、8B（80億パラメータ）のモデルをそのまま（16bit）で動かすと約16GBのメモリを占有しますが、4bitなら約5GB程度で済むからです。

## Step 3: 動かしてみる

最もシンプルな形でAIに質問を投げてみます。
LLMには「指示（System Prompt）」と「ユーザーの入力」をセットで渡すのが一般的です。

```python
# Llama 3のプロンプト形式に合わせる
prompt = "あなたは優秀なアシスタントです。日本の美味しい食べ物を3つ教えてください。"
messages = [{"role": "user", "content": prompt}]

# トークナイザーを使ってプロンプトを整形
formatted_prompt = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)

# テキスト生成の実行
response = generate(model, tokenizer, prompt=formatted_prompt, verbose=True)

print("\n--- 最終回答 ---")
print(response)
```

### 期待される出力

```
1. 寿司 - 新鮮な魚介類と酢飯の組み合わせは絶品です。
2. ラーメン - 地域ごとに異なるスープの味わいが楽しめます。
3. 天ぷら - サクサクの衣と素材の旨味が特徴です。
```

`generate` 関数の `verbose=True` を設定すると、トークンの生成速度（tokens/sec）が表示されます。
M2 Pro以上のチップなら、毎秒30〜50トークン程度は出るはずです。
これは人間が読むスピードよりも遥かに速いレスポンスです。

## Step 4: 実用レベルにする

上記のコードでは、AIが全ての回答を生成し終わるまで待機する必要があります。
これでは使い勝手が悪いため、一文字ずつリアルタイムに出力される「ストリーミング出力」を実装します。
また、メモリ管理をより厳密に行うための設定も加えます。

```python
import mlx.core as mx
from mlx_lm import load, generate
from mlx_lm.utils import generate_step

model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"
model, tokenizer = load(model_path)

def chat_stream(user_input):
    messages = [{"role": "user", "content": user_input}]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    print("AI: ", end="", flush=True)

    # ストリーミング生成のコアロジック
    # generate_stepを使うことで、生成されたトークンを一つずつ取得できる
    tokens = []
    for response in generate_step(mx.array(tokenizer.encode(prompt)), model):
        token = response.token
        if token == tokenizer.eos_token_id:
            break

        # トークンをテキストに変換して表示
        word = tokenizer.decode([token])
        print(word, end="", flush=True)
        tokens.append(token)

    print("\n")

# 実行
chat_stream("PythonでMLXを使うメリットは何ですか？")
```

このコードでは `generate_step` を使い、GPUが次の単語を予測するたびにその場で標準出力に書き出しています。
これにより、ユーザーは最初の1文字が出るまでの待機時間（Latency）をほとんど感じなくなります。
実務でチャットツールを作る際は、このストリーミング実装が必須条件と言えるでしょう。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError: No module named 'mlx'` | インストール失敗または仮想環境の未有効化 | `pip install mlx-lm` を再試行し、`source .venv/bin/activate` を確認 |
| `Killed` または `Segmentation fault` | メモリ不足（RAM不足） | ブラウザなど他のアプリを閉じるか、より小さいモデル（2Bクラス）を試す |
| 回答が文字化けする | トークナイザーの不一致 | `load` 関数で正しい `model_path` を指定しているか再確認 |
| 推論が異常に遅い | 他のGPU負荷が高い、またはSwapが発生している | アクティビティモニタで「メモリプレッシャー」が赤くないか確認 |

## 次のステップ

MLXでローカルLLMを動かすことに成功したら、次は「RAG（検索拡張生成）」に挑戦してみてください。
自分の持っているPDFファイルやメモ帳の中身をベクトルデータベースに入れ、それをMLX経由でLLMに読み込ませることで、社内文書に答えてくれる専用AIが作れます。

また、MLXには `mlx-examples` という公式リポジトリがあり、そこには画像の生成（Stable Diffusion）や音声の文字起こし（Whisper）をMLXで高速化するサンプルが豊富に揃っています。
Apple Siliconのポテンシャルを引き出すコードを読み解くことで、次世代のオンデバイスAI開発のスキルが身につくはずです。
APIにお金を払い続けるのではなく、手元の最強のハードウェアを使い倒す。
それがこれからのエンジニアの醍醐味だと思います。

## よくある質問

### Q1: Intel MacでもMLXは動きますか？

動きません。MLXはApple Silicon（Mシリーズチップ）のアーキテクチャに特化して設計されたライブラリです。Intel Macをお使いの場合は、CPU推論に強い `llama.cpp` を検討してください。

### Q2: どのモデルを選ぶのが一番賢い選択ですか？

2024年現在、日本語なら `Llama-3-8B` ベースのモデルか、Googleの `Gemma-2-9B` がバランスが良いです。メモリが8GBなら `Phi-3-mini` のような3B（30億パラメータ）前後のモデルを選ぶと軽快に動作します。

### Q3: PythonではなくSwiftからMLXを使いたいのですが。

可能です。MLXにはSwiftバインディングも用意されています。iOSアプリにLLMを組み込みたい場合は、 `mlx-swift` をチェックしてください。今回のPythonコードとほぼ同じロジックで実装できます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">大容量ユニファイドメモリで70BクラスのLLMも快適に動作する最強の検証環境</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを高速動作させる方法](/posts/2026-09-25-mlx-apple-silicon-local-llm-tutorial/)
- [MLX 使い方 入門：Apple SiliconでローカルLLMを動かす方法](/posts/2026-06-26-mlx-apple-silicon-local-llm-guide/)
- [MLX 使い方 入門：Apple SiliconでローカルLLMを爆速で動かす実践ガイド](/posts/2026-11-01-apple-silicon-mlx-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Intel MacでもMLXは動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きません。MLXはApple Silicon（Mシリーズチップ）のアーキテクチャに特化して設計されたライブラリです。Intel Macをお使いの場合は、CPU推論に強い llama.cpp を検討してください。"
      }
    },
    {
      "@type": "Question",
      "name": "どのモデルを選ぶのが一番賢い選択ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "2024年現在、日本語なら Llama-3-8B ベースのモデルか、Googleの Gemma-2-9B がバランスが良いです。メモリが8GBなら Phi-3-mini のような3B（30億パラメータ）前後のモデルを選ぶと軽快に動作します。"
      }
    },
    {
      "@type": "Question",
      "name": "PythonではなくSwiftからMLXを使いたいのですが。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。MLXにはSwiftバインディングも用意されています。iOSアプリにLLMを組み込みたい場合は、 mlx-swift をチェックしてください。今回のPythonコードとほぼ同じロジックで実装できます。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">大容量ユニファイドメモリで70BクラスのLLMも快適に動作する最強の検証環境</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
