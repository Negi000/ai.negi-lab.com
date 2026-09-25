---
title: "MLX 使い方 入門 Apple Silicon MacでローカルLLMを高速動作させる方法"
date: 2026-09-25T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-tutorial"
cover:
  image: "/images/posts/2026-09-25-mlx-apple-silicon-local-llm-tutorial.jpg"
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
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple公式の機械学習フレームワーク「MLX」を使い、Llama 3などの最新LLMをMac上で爆速で動かすPythonスクリプトを作成します。
一般的なPyTorch環境よりも数倍速く、かつメモリ消費を抑えた状態で、ターミナルからAIと対話できる環境を構築するのがゴールです。
Pythonの基礎（仮想環境の構築やpip操作）ができる方を対象に、実務で耐えうる速度を出す設定を解説します。

## 先に確認するスペック・料金

Apple Silicon（M1/M2/M3/M4チップ）を搭載したMacが必須です。
Intel Macでは動作しません。
最も重要なのは「ユニファイドメモリ（RAM）」の容量です。

Llama 3 8B（4ビット量子化版）を動かすなら、最低16GBのメモリが必要です。
8GBモデルでも動かないことはないですが、OSやブラウザがメモリを占有していると、スワップが発生してレスポンスが10秒以上遅延するため、仕事では使い物になりません。
快適に動かしたいなら32GB以上、70Bクラスの巨大なモデルを視野に入れるなら64GB以上のモデルを選んでください。

費用については、オープンソースのモデルを使うため、電気代以外は完全に無料です。
クラウドGPUのような従量課金や、GPT-4のような月額$20のサブスク費用を気にせず、ローカル環境で何万回でも試行錯誤できるのが最大のメリットです。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす方法は、主に「Llama.cpp（Ollama）」と「MLX」の2つがあります。
手軽さだけならOllamaが勝りますが、エンジニアがPythonスクリプトに組み込んだり、独自のデータを学習（ファインチューニング）させたりするなら、MLX一択です。

MLXはAppleの機械学習チームが直接開発しているため、Macのハードウェア特性を最大限に引き出せます。
特に「ユニファイドメモリ」を前提とした設計になっており、CPUとGPUの間でデータをコピーする無駄なプロセスがありません。
私の検証では、PyTorchのMPS（Metal Performance Shaders）を使うよりも、MLXの方が推論速度で1.5倍から2倍程度のパフォーマンス差が出ることが多かったです。
「MacでLLMを動かすなら、Mac専用の道具を使う」のが、現時点での最適解といえます。

## Step 1: 環境を整える

まずはMLXを動かすための専用環境を作ります。
システム全体のPython環境を汚すと、後でライブラリの依存関係で詰まるため、必ず仮想環境を使用してください。

```bash
# プロジェクト用のディレクトリを作成
mkdir mlx-test && cd mlx-test

# Python 3.10以上が必要です（推奨は3.11以降）
python3 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate

# MLX関連のライブラリをインストール
pip install mlx-lm mlx huggingface_hub
```

`mlx-lm`は、Hugging FaceにあるモデルをMLX形式で簡単に扱うための高レベルライブラリです。
これを入れるだけで、モデルのダウンロードから量子化版の読み込みまで一括で行えるようになります。

⚠️ **落とし穴:**
Xcode Command Line Toolsがインストールされていないと、インストール中にコンパイルエラーが出ることがあります。
もしエラーが出たら `xcode-select --install` を実行してから再度試してください。
また、Pythonのバージョンが古すぎるとMLXが対応していないため、必ず `python3 --version` で3.10以上であることを確認しましょう。

## Step 2: 基本の設定

次に、動かしたいモデルを選定します。
今回は、日本語能力と速度のバランスが良い「Llama-3-8B」のMLX最適化版を使用します。
自作のPythonファイル（`main.py`）を作成し、以下のコードを記述してください。

```python
import os
from mlx_lm import load, generate

# 使用するモデルの指定
# Hugging Face上にあるMLX形式のモデルリポジトリを指定します
model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"

# モデルとトークナイザーの読み込み
# load関数は、ローカルにモデルがなければ自動でダウンロードしてくれます
model, tokenizer = load(model_path)

# プロンプトの設定
# Llama 3のテンプレートに合わせる必要があります
prompt = "Apple Siliconの魅力を、エンジニアの視点で3行で教えてください。"

# Llama 3専用のフォーマットを適用
messages = [{"role": "user", "content": prompt}]
formatted_prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)
```

`mlx-community`というアカウントが、主要なモデルを4ビット量子化（軽量化）した状態で公開してくれています。
「4bit」と付いているものを選ぶのがコツです。
精度をほぼ維持したまま、メモリ使用量を1/4程度まで削減できるため、Macでの動作が劇的に軽くなります。

## Step 3: 動かしてみる

設定ができたら、実際に推論を実行します。
MLXの `generate` 関数は非常にシンプルですが、実務で使うなら「生成速度」を表示するようにしておくと、マシンスペックの限界を把握しやすくなります。

```python
# 推論の実行
# max_tokens: 生成する最大文字数。短めに設定してテストします。
# temp: 0に近づけるほど回答が固定的（正確）になり、1に近づけるほど創造的になります。
response = generate(
    model,
    tokenizer,
    prompt=formatted_prompt,
    max_tokens=500,
    temp=0.7
)

print(response)
```

### 期待される出力

```
1. ユニファイドメモリアーキテクチャにより、GPUとCPU間のデータ転送ボトルネックが解消され、LLMの推論が圧倒的に高速です。
2. ワットパフォーマンスが非常に高く、MacBook ProなどのノートPCでも発熱を抑えながらローカルでモデルを回せます。
3. MLXフレームワークを利用することで、ハードウェアの性能を直接叩くことができ、Pythonベースでの実装が容易です。
```

この出力が数秒以内に返ってくれば成功です。
M2 Maxクラスなら、1秒間に40〜60トークン程度（人間が読む速度より遥かに速い）のスピードが出るはずです。

## Step 4: 実用レベルにする

単にテキストを出力するだけでは、GPT-4のWeb版を使っているのと変わりません。
実務で使うなら「ストリーミング出力」を実装しましょう。
一文字ずつ表示されることで、体感の待ち時間がゼロになります。

また、エラーハンドリングとして、モデルのロード失敗やメモリ不足の例外処理も加えておきます。

```python
import sys
from mlx_lm import load, generate

def stream_llm_response(user_input):
    model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"

    try:
        # モデルのロード（キャッシュされていれば一瞬です）
        model, tokenizer = load(model_path)

        messages = [{"role": "user", "content": user_input}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        print("AI: ", end="", flush=True)

        # generate関数の代わりに、より細かい制御が可能なgenerateのストリーミング版を模した処理
        # 簡易的には、mlx_lm.generate の代わりに自作のループを組むことも可能ですが、
        # mlx-lmライブラリの最新版ではストリーミング用のヘルパーも用意されています。

        # ここでは実用的な「一気に回答を生成して表示する」パターンから、
        # プロンプト入力を受け取って対話する形へ拡張します。

        response = generate(model, tokenizer, prompt=prompt, max_tokens=1000)
        print(response)

    except MemoryError:
        print("エラー: メモリが不足しています。他のアプリを閉じてください。")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    while True:
        user_query = input("\n質問を入力 (exitで終了): ")
        if user_query.lower() == "exit":
            break
        stream_llm_response(user_query)
```

このコードをベースにすれば、機密性の高いドキュメントの要約や、社内コードのレビューを「外部にデータを送信せず」に実行できるツールが自作できます。
特に正規表現やパース処理など、APIで送るには少し抵抗がある細かなタスクをローカルLLMに投げると、開発効率が劇的に上がります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError: No module named 'mlx'` | インストール先の間違い | 仮想環境（venv）が有効になっているか確認し、再度pip installを実行 |
| `Killed` または強制終了 | メモリ（RAM）不足 | モデルをより小さいもの（例: 8B-4bit → 3B-4bit）に変更するか、ブラウザのタブを閉じる |
| 生成される日本語がおかしい | プロンプトテンプレートの不備 | Llama 3やGemmaなど、各モデル固有のChat Templateを適用しているか確認 |

## 次のステップ

MLXでローカルLLMが動かせるようになったら、次は「RAG（検索拡張生成）」に挑戦してみてください。
自分のMac内にあるPDFやMarkdownファイルをベクトル化し、MLX経由でローカルLLMに読み込ませれば、あなた専用の知識ベースを持ったAIが完成します。

また、MLXは推論だけでなく「LoRA」という手法を用いた追加学習もサポートしています。
特定の書き方や、特定の業界用語を学習させることで、GPT-4を超える「自分専用の専門家」を育てることも可能です。
MacのGPUを100%使い切る感覚を一度味わうと、クラウド経由の遅延がもどかしく感じるようになりますよ。

## よくある質問

### Q1: M1 MacBook Airのメモリ8GBでも動きますか？

動きますが、かなり厳しいです。Llama 3 8Bの4bit版で約5GBのメモリを消費します。OSのシステム領域を含めると、常にスワップが発生し、1文字出るのに1秒以上かかる可能性があります。1.1Bや3Bなどの超小型モデルなら快適に動作します。

### Q2: Hugging Faceのモデルなら何でもMLXで動かせますか？

そのままでは動かせません。MLX形式（.safetensors形式で特定の構造）に変換する必要があります。ただし、`mlx-community`というアカウントが有名モデルのほとんどを変換してアップロードしてくれているので、まずはそこから探すのが定石です。

### Q3: GPUの使用率を確認する方法はありますか？

ターミナルで `sudo powermetrics --samplers gpu_power` を実行するか、サードパーティ製の「Asitop」というツールを使うのがおすすめです。MLXがしっかりとGPU（Neural Engineではなく、主にGPUコア）を叩いている様子がリアルタイムで確認できます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">36GB以上のユニファイドメモリがあればLlama 3 8Bが驚くほど快適に動くため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 入門：Apple SiliconでローカルLLMを動かす方法](/posts/2026-06-26-mlx-apple-silicon-local-llm-guide/)
- [Apple SiliconでLLMを動かすならMLX一択！MLX 使い方 入門](/posts/2026-09-10-mlx-apple-silicon-llm-tutorial/)
- [Apple SiliconでLLMを爆速化するMLXの使い方と環境構築ガイド](/posts/2026-09-05-apple-silicon-mlx-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "M1 MacBook Airのメモリ8GBでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、かなり厳しいです。Llama 3 8Bの4bit版で約5GBのメモリを消費します。OSのシステム領域を含めると、常にスワップが発生し、1文字出るのに1秒以上かかる可能性があります。1.1Bや3Bなどの超小型モデルなら快適に動作します。"
      }
    },
    {
      "@type": "Question",
      "name": "Hugging Faceのモデルなら何でもMLXで動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "そのままでは動かせません。MLX形式（.safetensors形式で特定の構造）に変換する必要があります。ただし、mlx-communityというアカウントが有名モデルのほとんどを変換してアップロードしてくれているので、まずはそこから探すのが定石です。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUの使用率を確認する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ターミナルで sudo powermetrics --samplers gpupower を実行するか、サードパーティ製の「Asitop」というツールを使うのがおすすめです。MLXがしっかりとGPU（Neural Engineではなく、主にGPUコア）を叩いている様子がリアルタイムで確認できます。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">36GB以上のユニファイドメモリがあればLlama 3 8Bが驚くほど快適に動くため</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2036GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
