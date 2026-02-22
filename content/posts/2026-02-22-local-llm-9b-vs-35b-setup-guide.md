---
title: "自分のPCで「どのサイズのLLMを動かすべきか」という悩みは、ローカルLLM界隈では永遠のテーマです。特に最近注目されている9B（90億パラメータ）と35B（350億パラメータ）のモデルは、それぞれ実用性と性能のバランスが絶妙で、どちらをメインに据えるかで構築プランが大きく変わります。"
date: 2026-02-22T00:00:00+09:00
slug: "local-llm-9b-vs-35b-setup-guide"
description: "9Bモデルと35Bモデルの決定的な違いと、ハードウェア要件の計算方法。llama.cppを使用した、GPUメモリを最大限活用する実行環境の構築手順"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "Gemma 2 9B 構築"
  - "35Bモデル 量子化"
  - "VRAM 消費量 計算"
---
この記事では、9Bモデルと35Bモデルの性能差を理解した上で、あなたのハードウェア環境に合わせた最適なローカルLLM実行環境を構築する方法を解説します。

## この記事で学べること

- 9Bモデルと35Bモデルの決定的な違いと、ハードウェア要件の計算方法
- llama.cppを使用した、GPUメモリを最大限活用する実行環境の構築手順
- 量子化（Quantization）を使いこなし、限られたVRAMで35Bモデルを動かす設定
- 推論速度と精度のバランスを最適化するパラメータチューニング

## 前提条件

- OS: Linux (Ubuntu推奨) または Windows (WSL2 + NVIDIA Container Toolkit)
- GPU: NVIDIA製GPU（VRAM 8GB以上推奨）
- ツール: llama.cpp または Ollama（この記事では詳細設定が可能なllama.cppを使用）
- Python 3.10以上

## なぜこの知識が重要なのか

私がSIerでエンジニアをしていた頃、システムのサイジングは最も神経を使う作業の一つでした。ローカルLLMも同じで、闇雲に巨大なモデルを動かそうとしても、スワップが発生して「1文字出すのに数秒かかる」といった使い物にならない状態に陥ります。

現在のローカルLLMシーンにおいて、9Bは「RTX 3060/4060クラスのミドルレンジPCでサクサク動く実用モデル」、35Bは「RTX 3090/4090やMac Studioなどのハイエンド環境で、GPT-4に近い推論を狙うモデル」という明確な境界線になっています。

Redditの議論でも「速度の9Bか、論理力の35Bか」が焦点となっています。自分の用途が「要約や翻訳」なら9Bで十分ですし、「複雑なコーディング支援や論理パズル」なら35Bをどうにかして動かす価値があります。この使い分けを知ることで、無駄なハードウェア投資を防ぎ、今の環境で最高のパフォーマンスを引き出せるようになります。

## Step 1: 環境準備

まずは、モデルを動かすためのエンジンである `llama.cpp` をビルドします。Dockerを使う方法もありますが、GPUの性能をフルに引き出すにはネイティブ環境でのビルドが一番確実です。

```bash
# 必要な依存ライブラリのインストール
sudo apt update && sudo apt install build-essential git cmake libcurl4-openssl-dev -y

# リポジトリのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# CUDAを有効にしてビルド (NVIDIA GPUを使用する場合)
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j $(nproc)
```

ビルドが終わると `build/bin/` 配下に実行ファイルが生成されます。ここでCUDAを有効にし忘れると、CPU推論になってしまい「35Bモデルが動くのに10分かかる」という悲劇が起きるため、必ず `-DGGML_CUDA=ON` を確認してください。私は以前、環境変数のパス設定ミスで30分ほど「なぜこんなに遅いんだ…」と頭を抱えたことがあります。

## Step 2: モデルの選定とダウンロード

次に、Redditでも話題の9Bと35Bのモデルを準備します。現在は `Gemma 2 9B` や `Command R (35B)` などが人気です。これらを「GGUF」という形式でダウンロードします。

VRAM 12GBのPCを想定した場合の設定例を紹介します。

```python
# モデルサイズとVRAM消費の目安（Q4_K_M量子化の場合）
# 9Bモデル: 約5.5GB (VRAM 8GBで余裕)
# 35Bモデル: 約20GB (VRAM 24GBが必要)

# 12GBのVRAMで35Bを動かすには、さらに強い量子化（IQ2_XSなど）が必要になります
```

モデルのダウンロードには `huggingface-cli` を使うのが便利です。

```bash
pip install huggingface_hub

# 9Bモデルのダウンロード例
huggingface-cli download lmstudio-community/gemma-2-9b-it-GGUF gemma-2-9b-it-Q4_K_M.gguf --local-dir . --local-dir-use-symlinks False

# 35Bモデル（Command R）のダウンロード例
huggingface-cli download MaziyarPanahi/Command-R-v01-GGUF Command-R-v01-Q2_K.gguf --local-dir . --local-dir-use-symlinks False
```

35Bモデルを12GB程度のVRAMで動かすなら、Q2（2ビット量子化）を選択せざるを得ません。正直、Q2まで下げると知能の劣化が目立ちますが、それでも9Bのフル精度より論理的思考が優れているケースがあるのが面白いところです。

## Step 3: 実行と最適化

ビルドしたバイナリを使ってモデルを起動します。ここで重要なのが `-ngl` (number of GPU layers) パラメータです。

```bash
# 9Bモデルの起動（全レイヤーをGPUにオフロード）
./build/bin/llama-cli -m gemma-2-9b-it-Q4_K_M.gguf \
  -ngl 99 \
  -p "あなたは優秀なエンジニアです。Rustの所有権について解説してください。" \
  -n 512
```

35Bモデルを「GPU + CPU」のハイブリッドで動かす場合は、レイヤー数を調整します。

```bash
# 35Bモデルの起動（VRAMに合わせてレイヤーを一部オフロード）
# 例: 40レイヤー中 20レイヤーだけGPUに載せる
./build/bin/llama-cli -m Command-R-v01-Q4_K_M.gguf \
  -ngl 20 \
  -c 4096 \
  --flash-attn
```

`--flash-attn` は必ず有効にしてください。メモリ消費を抑えつつ計算を高速化できる、現代のLLM実行における「必須オプション」です。これを忘れると、長いコンテキストを扱った瞬間にVRAMが溢れてクラッシュします。

## Step 4: 応用テクニック

複数のモデルを頻繁に切り替えるなら、設定をJSONファイルやシェルスクリプトで管理するのが賢いやり方です。私は以下のような構成で管理しています。

```bash
#!/bin/bash
# run_llm.sh

MODEL_PATH="./models/gemma-2-9b-it-Q4_K_M.gguf"
GPU_LAYERS=99
CONTEXT_SIZE=8192

./build/bin/llama-cli \
  -m "$MODEL_PATH" \
  -ngl "$GPU_LAYERS" \
  -c "$CONTEXT_SIZE" \
  --flash-attn \
  --temp 0.7 \
  --repeat-penalty 1.1 \
  --color -i
```

このように `-i` モード（インタラクティブモード）で起動すれば、チャット形式で対話が可能になります。また、35BクラスのモデルでRAG（外部知識参照）を試す場合は、コンテキストサイズ `-c` を大きめに確保する必要がありますが、その分VRAMを消費するため、9Bモデルでコンテキストを広めに取る方が実用的な場面も多いです。

## よくあるエラーと対処法

### エラー1: CUDA error: out of memory

```
ggml_cuda_host_malloc: failed to allocate 4096.00 MiB of pinned memory
common_run: error: failed to load model
```

**原因:** GPUのメモリ不足です。指定したレイヤー数（-ngl）が多すぎるか、他のアプリケーションがVRAMを消費しています。
**解決策:** `-ngl` の数値を少しずつ下げてください（例: 35 -> 20）。または、より高圧縮な量子化モデル（Q4_K_M -> Q3_K_Sなど）に変更します。

### エラー2: slow inference speed (0.5 tokens/s)

**原因:** モデルの大部分がCPU（メインメモリ）で処理されています。
**解決策:** `-ngl` を最大値（99など）にして、全レイヤーがGPUに乗っているかログを確認してください。もしVRAMに入り切らない場合は、性能を諦めてモデルサイズを9Bに下げるのが現実的です。

## ベストプラクティス

実務でローカルLLMを運用するなら、以下の3点を意識してください。

1.  **「迷ったら9B」から始める**: Gemma 2 9BやLlama 3 8Bは、現代のSIer業務（コード修正案の作成、ドキュメント要約）において驚くほど優秀です。まずはこれがストレスなく動く環境を作ることが先決です。
2.  **KVキャッシュの圧縮**: 長い会話をするなら `cache_type_k` などを設定してメモリを節約しましょう。
3.  **UIツールの活用**: コマンドラインに慣れたら `Open WebUI` などをフロントエンドに据えると、過去の履歴管理が楽になり、実用性が一気に高まります。

## まとめ

ローカルLLMの選択は、単なるスペック比較ではなく「自分のPC資産をどう分配するか」という戦略そのものです。9Bモデルは、多くのユーザーにとって「速度・精度・省電力」のバランスが最も取れた選択肢になります。一方で、35Bモデルは量子化を駆使することで、かつての巨大モデル並みの知能を家庭用PCで再現できる夢があります。

まずは、自分のGPUに全レイヤーが収まる最大の量子化ビット数を見つけるところから始めてみてください。9BのQ8（高精度）と35BのQ2（低精度）で、自分のよく使うプロンプトに対する回答がどう変わるかを比較してみるのも面白いですよ。

まずは `llama.cpp` のビルドと、Gemma 2 9Bの実行から試してみてください。そのレスポンスの速さを体感すれば、ローカルLLMの可能性にワクワクすること間違いなしです。

---
### メタデータ

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## この記事を読んだ方へのおすすめ

**GeForce RTX 4060 Ti 16GB**

35Bモデルを実用的な速度と精度で動かすための、最もコスパの良いVRAM 16GB搭載ビデオカードです

[Amazonで詳細を見る](https://www.amazon.co.jp/s?k=ASUS%20NVIDIA%20GeForce%20RTX%204060%20Ti%2016GB&tag=negi3939-22){{< rawhtml >}}<span style="margin: 0 8px; color: #999;">|</span>{{< /rawhtml >}}[楽天で探す](https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FASUS%2520NVIDIA%2520GeForce%2520RTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FASUS%2520NVIDIA%2520GeForce%2520RTX%25204060%2520Ti%252016GB%2F)

<small style="color: #999;">※アフィリエイトリンクを含みます</small>
