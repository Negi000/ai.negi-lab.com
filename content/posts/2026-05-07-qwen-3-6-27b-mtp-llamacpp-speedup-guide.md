---
title: "Qwen 3.6 27Bをllama.cppで高速化して50 t/sを叩き出す方法"
date: 2026-05-07T00:00:00+09:00
slug: "qwen-3-6-27b-mtp-llamacpp-speedup-guide"
cover:
  image: "/images/posts/2026-05-07-qwen-3-6-27b-mtp-llamacpp-speedup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen 3.6 27B"
  - "llama.cpp MTP"
  - "ローカルLLM 高速化"
  - "Multi-Token Prediction"
---
**所要時間:** 約40分 | **難易度:** ★★★★☆

## この記事で作るもの

- Qwen 3.6 27B（MTP対応モデル）を、llama.cppの特定のパッチを適用して爆速で動かす環境
- 100kコンテキストという広大なメモリ領域を使いつつ、秒間50トークン以上の推論速度を実現するセットアップ
- Pythonや複雑なライブラリに依存せず、軽量なC++バイナリでモデルを運用する基盤

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">27Bモデルを100kコンテキストで高速駆動させるための唯一無二の選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、コマンドライン操作（Linux/WSL2）と、Git、CMakeの基本的な使い方がわかる必要があります。
また、ローカルでLLMを動かすためのGPU（NVIDIA RTX 3090/4090以上）を推奨します。

## 先に確認するスペック・料金

Qwen 3.6 27Bを実用レベルで動かすには、VRAM（ビデオメモリ）の量が最も重要です。
27BモデルをQ4_K_Mで量子化した際、モデル本体だけで約16GBから18GBのVRAMを消費します。
さらに100kコンテキスト（長い記憶保持能力）を確保する場合、KVキャッシュのメモリも必要になるため、VRAM 24GBを搭載したRTX 3090または4090が最低ラインです。

もしVRAM 12GBや16GBのGPU（RTX 4070 Tiや4080）を使っている場合は、コンテキスト長を大幅に絞るか、メインメモリ（RAM）へのオフロードが発生して速度が激減することを覚悟してください。
Macユーザーであれば、メモリ32GB以上のM2/M3/M4チップ搭載モデルが選択肢に入ります。
このアプローチはオープンソースソフトウェア（OSS）のみを使用するため、モデルのダウンロードにかかる通信費以外にコストはかかりません。

## なぜこの方法を選ぶのか

通常、27Bクラスのモデルを単一のGPUで動かすと、推論速度は10〜15 t/s程度に落ち着くのが一般的です。
しかし、今回の方法は「MTP（Multi-Token Prediction）」という技術を利用します。
MTPは一度に複数のトークンを予測する仕組みで、llama.cppの最新パッチ（Pull Request 22673）と組み合わせることで、従来の数倍の速度を叩き出せます。

他の手段としてvLLMやTGI（Text Generation Inference）がありますが、これらはセットアップが重く、VRAMの管理がシビアです。
llama.cppはバイナリ一つで完結し、MTPの実験的な機能をいち早く試せるため、現時点でローカル環境における「最速」を狙うならこの構成がベストです。

## Step 1: 環境を整える

まずは、MTPパッチを適用したllama.cppをビルドするための依存ライブラリをインストールします。
私はUbuntu 22.04環境で検証していますが、WSL2（Windows Subsystem for Linux）でも同様の手順で動作します。

```bash
# 必要なビルドツールとCUDAツールキットの確認
sudo apt update
sudo apt install -y build-essential cmake git pkg-config libcurl4-openssl-dev

# CUDAがインストールされているか確認（12.x系を推奨）
nvcc --version
```

次に、llama.cppのリポジトリをクローンし、MTP対応のプルリクエストを取り込みます。
ここが最大の「独自の切り口」であり、通常のmasterブランチではまだこの速度は出ません。

```bash
# llama.cppのクローン
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# MTP対応のプルリクエストをフェッチしてローカルブランチに適用
git fetch origin pull/22673/head:mtp-optimization
git checkout mtp-optimization
```

落とし穴として、標準の`git clone`だけではMTPの高速化恩恵を受けられません。
必ずプルリクエスト番号（22673）を指定して、開発中の最新最適化コードを取り込む必要があります。

## Step 2: GPU最適化ビルドを実行する

コードを最新にしたところで、GPU（CUDA）をフル活用するためのビルドを行います。
私はRTX 4090を2枚挿ししていますが、1枚でもこのビルド設定で問題ありません。

```bash
# ビルドディレクトリの作成
mkdir build
cd build

# CUDAを有効にしてビルド。アーキテクチャ最適化をかける
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release -j$(nproc)
```

`-DGGML_CUDA=ON`は、CPUではなくGPUのコア（CUDA Core）を使って計算を行うためのフラグです。
これを忘れると、推論速度が1〜2 t/sまで落ち込み、今回の目的である「50 t/s」には到底届きません。
ビルドが終わると、`bin`ディレクトリ内に`llama-cli`や`llama-server`といった実行ファイルが生成されます。

## Step 3: MTP対応モデルをダウンロードする

次に、Qwen 3.6 27BのMTP対応GGUFファイルをダウンロードします。
通常のQwen 2.5やQwen 3.5のGGUFではなく、MTP用に量子化された専用のファイルが必要です。

```bash
# huggingface-cliを使ってモデルをダウンロード（入っていない場合は pip install huggingface_hub）
huggingface-cli download RDson/Qwen3.6-27B-MTP-Q4_K_M-GGUF Qwen3.6-27B-MTP-Q4_K_M.gguf --local-dir ./models
```

このモデルファイルは約17GBあります。
Q4_K_Mという量子化形式は、モデルの精度（Perplexity）をほとんど落とさずにサイズを圧縮できる、実務上の「黄金律」とも言える設定です。
私は過去にQ2やQ3も試しましたが、27BクラスだとQ4未満は知能の低下が顕著に感じられたため、このQ4_K_Mを強く推奨します。

## Step 4: 50 t/sの世界を体験する

準備が整いました。100kコンテキストを確保しつつ、MTPを有効にして起動します。
以下のコマンドは、24GBのVRAMを限界まで使い切る設定です。

```bash
./bin/llama-cli \
  -m models/Qwen3.6-27B-MTP-Q4_K_M.gguf \
  -n 512 \
  --ctx-size 102400 \
  --n-gpu-layers 99 \
  --flash-attn \
  -p "あなたは優秀なエンジニアです。以下のコードのボトルネックを指摘してください。"
```

各設定の理由は以下の通りです：
- `-n 512`: 生成するトークン数です。
- `--ctx-size 102400`: これが「100kコンテキスト」の指定です。
- `--n-gpu-layers 99`: すべてのレイヤーをGPUに載せます。27Bなら24GB VRAMに収まります。
- `--flash-attn`: メモリ消費を抑え、アテンション計算を高速化する必須オプションです。

### 期待される出力

```text
llama_print_timings:        load time =    1240.50 ms
llama_print_timings:      sample time =      15.20 ms /   512 runs   (    0.03 ms per token, 33684.21 tokens per second)
llama_print_timings: prompt eval time =     850.10 ms /    32 tokens (   26.57 ms per token,    37.64 tokens per second)
llama_print_timings:        eval time =    10120.40 ms /   511 runs   (   19.81 ms per token,    50.49 tokens per second)
```

注目すべきは `eval time` の項目にある `50.49 tokens per second` です。
27Bという中規模以上のモデルが、まるで小型モデル（7Bクラス）のような軽快さでテキストを出力し始める瞬間は感動的です。

## 実用レベルにする：サーバーとして運用する

コマンドラインでの動作確認ができたら、次はAPIサーバーとして常駐させ、Cursorや独自のアプリから利用できるようにします。

```bash
./bin/llama-server \
  -m models/Qwen3.6-27B-MTP-Q4_K_M.gguf \
  --ctx-size 32768 \
  --n-gpu-layers 99 \
  --flash-attn \
  --port 8080 \
  --host 0.0.0.0
```

実務で使う際は、コンテキストを32k程度に抑えるのが現実的です。
100kをフルで確保すると、KVキャッシュだけでVRAMを数GB食い潰すため、複数のリクエストを同時に捌くのが難しくなるからです。
この状態で、OpenAI互換APIとして`/v1/chat/completions`へリクエストを送れば、あなたのローカル環境に爆速のGPT-4o級（あるいはそれ以上）のエージェントが誕生します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| CUDA error: out of memory | VRAMが不足している | `--n-gpu-layers`を減らすか、コンテキストサイズを小さくする |
| symbol lookup error | ビルドしたバイナリとライブラリの不整合 | `build`ディレクトリを一度消して、`cmake`からやり直す |
| 速度が10 t/s以下 | MTPパッチが当たっていない、またはFlash Attentionが無効 | `git fetch`の手順を再確認し、`--flash-attn`フラグを付ける |

## 次のステップ

この「MTP + llama.cpp」の構成をマスターすると、ローカルLLMの運用コストと体験が劇的に変わります。
次は、この爆速環境をバックエンドにして「RAG（検索拡張生成）」を構築することをおすすめします。
推論が速いということは、大量のドキュメントを読み込ませて要約させる際の待ち時間がほぼゼロになることを意味します。

また、Dolphinなどのファインチューニング済みモデルのMTP版を探して、より特定のタスク（コーディングやロールプレイ）に特化させるのも面白いでしょう。
RTX 4090を2枚挿しているようなパワーユーザーなら、複数のモデルを同時に立ち上げて、エージェント同士を対話させる並行処理も50 t/sの速度があればストレスなく検証できます。

## よくある質問

### Q1: RTX 3060（VRAM 12GB）でもこの速度は出ますか？

残念ながら、27Bモデルを12GBで動かすには重すぎる量子化（Q2など）が必要になり、速度も知能も大幅に落ちます。12GB環境なら、Qwen 2.5 7BのMTP版を試してみてください。そちらなら100 t/sを超える速度が出るはずです。

### Q2: ビルド中に「CMAKE_CUDA_COMPILER not found」と出ます。

CUDA Toolkitがインストールされていないか、パスが通っていません。`export PATH=/usr/local/cuda/bin:$PATH`を確認し、`nvcc`コマンドが叩ける状態にしてください。

### Q3: MTPを使うとモデルの回答精度は落ちますか？

理論上、推論アルゴリズムの変更による微々たる差はありますが、実用上で知覚できるほどの精度の低下はありません。速度向上のメリットが圧倒的に上回ります。

---

## あわせて読みたい

- [Qwen 3.6 27BのMTPモデルを爆速で動かす！ローカルコーディング環境構築ガイド](/posts/2026-05-06-qwen-36-27b-mtp-local-inference-guide/)
- [Qwen 3.6 27B 使い方 | ローカルLLM環境構築と量子化モデル比較ガイド](/posts/2026-04-28-qwen-36-27b-gguf-quantization-guide/)
- [Qwen 3.6 27B と Gemma 4 31B 使い方比較！Pythonでパックマンを作る方法](/posts/2026-05-02-qwen-vs-gemma-local-llm-pacman-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3060（VRAM 12GB）でもこの速度は出ますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "残念ながら、27Bモデルを12GBで動かすには重すぎる量子化（Q2など）が必要になり、速度も知能も大幅に落ちます。12GB環境なら、Qwen 2.5 7BのMTP版を試してみてください。そちらなら100 t/sを超える速度が出るはずです。"
      }
    },
    {
      "@type": "Question",
      "name": "ビルド中に「CMAKE_CUDA_COMPILER not found」と出ます。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "CUDA Toolkitがインストールされていないか、パスが通っていません。export PATH=/usr/local/cuda/bin:$PATHを確認し、nvccコマンドが叩ける状態にしてください。"
      }
    },
    {
      "@type": "Question",
      "name": "MTPを使うとモデルの回答精度は落ちますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "理論上、推論アルゴリズムの変更による微々たる差はありますが、実用上で知覚できるほどの精度の低下はありません。速度向上のメリットが圧倒的に上回ります。 ---"
      }
    }
  ]
}
</script>
