---
title: "MLX 使い方 入門 (Apple Silicon搭載MacでLLMを動かす方法)"
date: 2026-08-17T00:00:00+09:00
slug: "apple-silicon-mlx-local-llm-tutorial"
cover:
  image: "/images/posts/2026-08-17-apple-silicon-mlx-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "ローカルLLM Mac"
  - "mlx-lm 入門"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple公式の機械学習フレームワーク「MLX」を利用して、MacのGPU性能を限界まで引き出し、Llama 3やQwen2.5といった最新LLMを高速に動かすPythonスクリプトを構築します。
Pythonの基礎知識があれば、外部APIに1円も払わず、プライバシーを完全に守った状態で自分専用のAIチャット環境が手に入ります。
この記事では環境構築から、実用的なストリーミング出力の実装までを解説します。

## 先に確認するスペック・料金

MLXはApple Silicon（M1, M2, M3, M4チップ）専用のライブラリです。
Intelチップを搭載した古いMacでは動作しないため、まず自分の端末を確認してください。
最も重要なのは「メモリ（ユニファイドメモリ）」の容量です。

LLMの動作はメモリ量に依存します。
8GBモデルの場合、30億パラメータ（3B）クラスが限界で、70億（7B）クラスを動かすとシステム全体が重くなり実用的ではありません。
仕事でストレスなく7B〜14Bクラスのモデルを動かすなら、最低でも24GB、理想は32GB以上のメモリを積んだモデルを推奨します。
私は検証用にMac Studio（M2 Ultra / 128GBメモリ）とMacBook Pro（M3 Max / 64GB）を使っていますが、メモリが多ければ多いほど、巨大なモデルを量子化なしで動かせるため、回答精度が劇的に安定します。

GPUについては、コア数が多いほど生成速度（Token per second）が向上します。
M2 Pro以降であれば、体感としてChatGPT（GPT-4）と同等かそれ以上のレスポンス速度が得られます。
追加のAPI料金は一切かかりません。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす手段として「llama.cpp」や「Ollama」も有名ですが、私はあえて「MLX」を推奨します。
最大の理由は、MLXがAppleのシリコンチームによって開発されており、ユニファイドメモリ・アーキテクチャに最適化されている点です。

PyTorchを経由する場合、メモリのコピーが発生してオーバーヘッドが生じることがありますが、MLXはGPUとCPUが同じメモリ空間を直接参照する「ゼロコピー」を最大限に活かします。
また、Hugging Faceとの親和性が高く、`mlx-lm`というライブラリを使えば、公開されている数万個のモデルを数行のコードでロードできます。
「セットアップの簡単さ」と「実行速度」のバランスが、現時点で最も優れているのがMLXです。

## Step 1: 環境を整える

まずはPython環境の構築です。
既存のシステム環境を汚さないよう、必ず仮想環境（venv）を作成してください。

```bash
# プロジェクトディレクトリの作成
mkdir mlx-test && cd mlx-test

# Python 3.10以上を推奨
python3 -m venv .venv

# 仮想環境のアクティベート
source .venv/bin/activate

# 必須ライブラリのインストール
pip install -U pip
pip install mlx-lm
```

`mlx-lm`は、MLX上でLLMを簡単に扱うための公式パッケージです。
これをインストールするだけで、モデルのダウンロード、量子化、推論のすべてが行えるようになります。
以前は複雑な変換スクリプトが必要でしたが、現在は非常にシンプルになりました。

⚠️ **落とし穴:**
Xcode Command Line Toolsがインストールされていないと、インストール中にエラーが出ることがあります。
`xcode-select --install` を実行して、事前にツールを導入しておいてください。
また、Pythonのバージョンが古い（3.9以下）場合、MLXの一部の機能が動作しないため、最新の安定版を使うのが鉄則です。

## Step 2: 基本の設定

次に、動かしたいモデルを選びます。
今回は日本語能力と軽量さのバランスが良い「Qwen2.5-7B-Instruct」の4bit量子化版を例にします。
4bit量子化とは、モデルの重みを圧縮することで、メモリ消費量を抑えつつ高速化する手法です。

```python
import os
from mlx_lm import load, generate

# 1. モデルの指定（Hugging Face上のリポジトリ名）
# 自分で変換しなくても、コミュニティが公開している「-4bit」版を使うのが効率的です
model_name = "mlx-community/Qwen2.5-7B-Instruct-4bit"

# 2. モデルとトークナイザーのロード
# load関数は、ローカルにモデルがなければ自動でHugging Faceからダウンロードします
model, tokenizer = load(model_name)

# なぜloadを使うのか：
# MLXのload関数は、Apple Siliconのメモリ配置に最適化された形で重みを展開します
# 初回実行時はダウンロードに数分かかりますが、2回目以降はキャッシュから瞬時に読み込まれます
```

モデルの選定理由は「日本語の指示に忠実であること」です。
Llama 3も優秀ですが、日本語での自然な対話においてはQwen2.5の方が一歩リードしている印象を私は持っています。

## Step 3: 動かしてみる

まずは最小限のコードで、テキストが生成されるか確認します。
MLXの`generate`関数を使います。

```python
# プロンプトの作成
prompt = "美味しいカレーの隠し味を3つ教えてください。"

# チャット形式のプロンプトテンプレートを適用
# これを忘れると、モデルが「会話」として認識せず、文章の続きを書き始めるだけになります
messages = [{"role": "user", "content": prompt}]
formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

# 生成の実行
response = generate(model, tokenizer, prompt=formatted_prompt, verbose=True)

print(response)
```

### 期待される出力

```
カレーの隠し味としておすすめの3つは以下の通りです：
1. インスタントコーヒー：深いコクと苦味が加わり、一晩寝かせたような味になります。
2. すりおろしリンゴ：自然な甘みと酸味が加わり、味がまろやかになります。
3. ウスターソース：スパイスの複雑さと塩味が加わり、全体の味が引き締まります。
```

`verbose=True`を設定すると、コンソールに生成速度（tokens/sec）が表示されます。
M2 Maxクラスであれば、秒間50〜100トークン程度の速度が出るはずです。
これは人間が読む速度を遥かに超えており、実務で使うには十分すぎるスペックです。

## Step 4: 実用レベルにする

単にテキストを一括表示するだけでは、長い回答のときに待ち時間が発生し、UX（ユーザー体験）が悪くなります。
ChatGPTのように、生成された文字から順次表示する「ストリーミング出力」を実装しましょう。
これが仕事で使えるスクリプトにするための必須条件です。

```python
import mlx.core as mx
from mlx_lm import load, generate
from mlx_lm.utils import generate_step

def stream_chat(model_name, user_input):
    model, tokenizer = load(model_name)

    messages = [{"role": "user", "content": user_input}]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    # トークン化
    prompt_tokens = mx.array(tokenizer.encode(prompt))

    print(f"User: {user_input}")
    print("Assistant: ", end="", flush=True)

    tokens = []
    # generate_stepを使って1トークンずつ生成を制御
    # max_tokensを設定して無限ループを防ぐ
    for (token, prob), n in zip(generate_step(prompt_tokens, model), range(1000)):
        if token == tokenizer.eos_token_id:
            break

        # 1トークンずつデコードして表示
        s = tokenizer.decode([token])
        print(s, end="", flush=True)
        tokens.append(token)

    print("\n")

if __name__ == "__main__":
    # 実行
    stream_chat("mlx-community/Qwen2.5-7B-Instruct-4bit", "Pythonで素数判定プログラムを書いて")
```

このコードのポイントは `generate_step` です。
ループを回しながらトークンを一つずつ受け取れるため、生成の途中で処理を中断させたり、別の処理を挟んだりすることが可能になります。
実務では、この出力をFastAPIなどでラップして、Webブラウザ側のUIに流し込むのが一般的です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ImportError: DLL load failed` | Pythonのアーキテクチャ不一致 | Rosetta 2経由ではなく、ネイティブなarm64版Pythonを使用してください。 |
| `MemoryError / Out of Memory` | メモリ不足 | モデルサイズを下げるか（7B→3B）、より高い量子化（4bit）を使用してください。 |
| 生成が止まらない（ループする） | 停止トークン（EOS）の判定漏れ | `tokenizer.eos_token_id` を正しく検知してループを抜ける処理を入れてください。 |

## 次のステップ

MLXでローカルLLMを動かせるようになったら、次は「RAG（検索拡張生成）」に挑戦してみてください。
自分の持っているPDFやドキュメントをベクトルデータベースに保存し、MLXで動かしているLLMに参照させる手法です。
外部APIを使わないため、社外秘の資料を読み込ませても情報漏洩のリスクがありません。

具体的には `LangChain` や `LlamaIndex` と組み合わせて運用するのが王道です。
また、MLXには「Fine-tuning（微調整）」の機能も備わっています。
特定の言い回しや専門知識を学習させ、より自分好みのAIに育て上げるのがローカルLLM運用の醍醐味と言えます。
まずはHugging Faceで「mlx-community」が公開している他のモデルを試し、自分のMacでどれくらいの速度が出るか計測することから始めてみてください。

## よくある質問

### Q1: メモリ8GBのMacBook Airでも動きますか？

動きますが、かなり厳しいです。
1B（10億パラメータ）や3Bクラスの小型モデルであれば軽快に動きますが、7Bクラスはスワップが発生し、システム全体が重くなります。
8GB端末なら、まずは `mlx-community/Llama-3.2-1B-Instruct-4bit` あたりから試すのが無難です。

### Q2: ネットに繋がっていなくても使えますか？

はい、一度モデルをダウンロードしてしまえば、完全にオフラインで動作します。
これがローカルLLMの最大のメリットです。
飛行機の中や、セキュリティの厳しいオフライン環境でも、自分専用のAIアシスタントを使い続けることができます。

### Q3: GPU使用率が100%になりませんが故障ですか？

正常です。
MLXはメモリ帯域（Memory Bandwidth）をボトルネックにすることが多く、演算ユニットが常にフル稼働するわけではありません。
特に推論時はGPUを効率的に休ませながら処理を行うため、ファンが爆音で回らないことも多いのがMLXの特徴です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">MLXでの推論・微調整を快適に行うための十分なメモリとGPU性能を装備</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 Apple SiliconでローカルLLMを動かす入門ガイド](/posts/2026-08-07-mlx-apple-silicon-local-llm-tutorial/)
- [MLX 使い方 Apple SiliconでローカルLLMを爆速動作させる方法](/posts/2026-06-12-mlx-apple-silicon-local-llm-guide/)
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
        "text": "動きますが、かなり厳しいです。 1B（10億パラメータ）や3Bクラスの小型モデルであれば軽快に動きますが、7Bクラスはスワップが発生し、システム全体が重くなります。 8GB端末なら、まずは mlx-community/Llama-3.2-1B-Instruct-4bit あたりから試すのが無難です。"
      }
    },
    {
      "@type": "Question",
      "name": "ネットに繋がっていなくても使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、一度モデルをダウンロードしてしまえば、完全にオフラインで動作します。 これがローカルLLMの最大のメリットです。 飛行機の中や、セキュリティの厳しいオフライン環境でも、自分専用のAIアシスタントを使い続けることができます。"
      }
    },
    {
      "@type": "Question",
      "name": "GPU使用率が100%になりませんが故障ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "正常です。 MLXはメモリ帯域（Memory Bandwidth）をボトルネックにすることが多く、演算ユニットが常にフル稼働するわけではありません。 特に推論時はGPUを効率的に休ませながら処理を行うため、ファンが爆音で回らないことも多いのがMLXの特徴です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">MLXでの推論・微調整を快適に行うための十分なメモリとGPU性能を装備</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
