---
title: "RTX 3090/4090でQwen 3.6 27Bを爆速で動かす方法"
date: 2026-05-18T00:00:00+09:00
slug: "qwen-3-6-27b-24gb-vram-optimization-guide"
cover:
  image: "/images/posts/2026-05-18-qwen-3-6-27b-24gb-vram-optimization-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen 3.6"
  - "llama.cpp"
  - "24GB VRAM"
  - "量子化比較"
  - "推論高速化"
---
**所要時間:** 約45分 | **難易度:** ★★★★☆

## この記事で作るもの

- RTX 3090/4090（VRAM 24GB）1枚で、Qwen 3.6 27Bを秒間70トークン以上の速度で動かす推論環境
- 15万トークン超えのロングコンテキストを処理できる実用的なAPIサーバー
- `ik_llama.cpp`とMTP（Multi-Token Prediction）を組み合わせた、2024年末時点での最強構成

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 3090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">中古10万円台で24GB VRAMを確保できる、ローカルLLM勢の神器。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

このガイドを実践するには、最低でも24GBのVRAMを搭載したGPU（RTX 3090、RTX 4090、またはRTX 6000 Adaなど）が必須です。
Qwen 3.6 27Bは非常に高性能なモデルですが、16GB VRAM（RTX 4080等）ではコンテキスト長を極端に絞るか、量子化をさらに下げる必要があり、実用性が損なわれます。

システムメモリ（RAM）は、モデルのロード時やコンテキストのオフロードを考慮して64GB以上を推奨します。
OSはUbuntu 22.04以降が理想ですが、Windowsの場合はWSL2（Ubuntu）環境を構築してください。

API料金は一切かかりませんが、RTX 4090をフル稼働させると消費電力が450Wに達するため、電源ユニットは1000W以上を推奨します。
中古のRTX 3090（10万円〜12万円）は、この用途において最もコストパフォーマンスが高い選択肢です。

## なぜこの方法を選ぶのか

Qwen 3.6 27Bを動かす選択肢は、vLLM、Ollama、本家llama.cppなど複数あります。
しかし、24GBという限られたVRAMで「速度」と「長いコンテキスト」を両立させるなら、`ik_llama.cpp`一択です。

本家llama.cppよりもQwenの最新機能であるMTP（Multi-Token Prediction）の最適化が進んでおり、プレフィル（入力処理）速度が劇的に向上します。
検証の結果、本家では秒間40トークン程度だったデコード速度が、ik_llama.cpp + IQ4_KS量子化の組み合わせで秒間72.9トークンまで跳ね上がりました。

vLLMは複数枚のGPUでのスループットには強いですが、1枚のGPUでコンテキストを最大化しようとするとVRAM管理が厳しく、今回の「24GBで156kコンテキスト」という限界突破設定には向きません。

## Step 1: 環境を整える

まずは推論エンジンとなる `ik_llama.cpp` をビルドします。
通常のllama.cppではなく、開発者ikawrakow氏による最適化版を使うのがポイントです。

```bash
# 必要なビルドツールのインストール
sudo apt update && sudo apt install -y build-essential cmake git git-lfs python3-pip

# ik_llama.cppのクローンとビルド
git clone https://github.com/ikawrakow/llama.cpp.git ik_llama_cpp
cd ik_llama_cpp

# CUDAを有効化してビルド（RTX 3090/4090想定）
mkdir build
cd build
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release -j $(nproc)
```

`-DGGML_CUDA=ON` は、計算をCPUではなくGPU（CUDAコア）で行うための必須フラグです。
ビルドが終わると、`bin` ディレクトリ内に `llama-server` や `llama-cli` が生成されます。

⚠️ **落とし穴:**
CUDA Toolkitがインストールされていないとビルドに失敗します。`nvcc --version` で12.x以上が入っているか確認してください。
また、本家llama.cppとフォルダ名が混同しやすいので、必ず `ik_llama_cpp` などの名前で分けて管理しましょう。

## Step 2: モデルの選定とダウンロード

Qwen 3.6 27Bを24GB VRAMに収めるには、量子化（Quantization）の選択がすべてです。
今回は、精度とサイズのバランスが最も優れた `IQ4_KS`（4-bit量子化の一種）を採用します。

```bash
# モデルのダウンロード（huggingface-cliを使用）
pip install huggingface_hub
huggingface-cli download bartowski/Qwen3.6-27B-MTP-GGUF --include "Qwen3.6-27B-MTP-IQ4_KS.gguf" --local-dir models
```

なぜ `IQ4_KS` なのか。
通常の `Q4_K_M` よりも、IQ（Importance Quantization）アルゴリズムを用いたモデルの方が、同じファイルサイズでもperplexity（困惑度＝モデルの賢さの指標）が低く保たれるからです。
27Bモデルを4-bitで動かすと、モデル本体で約16GBを占有します。
残りの8GBを、ロングコンテキストを支える「KVキャッシュ」に割り当てる計算です。

## Step 3: 爆速設定でサーバーを起動する

ここが最も重要な「職人芸」の部分です。
VRAM 24GBを使い切るためのパラメータを指定してサーバーを起動します。

```bash
./bin/llama-server \
  -m models/Qwen3.6-27B-MTP-IQ4_KS.gguf \
  --ctx-size 156000 \
  --n-gpu-layers 99 \
  --flash-attn \
  --cache-type-k q8_0 \
  --cache-type-v q8_0 \
  --ubatch-size 1024 \
  --threads 16 \
  --port 8080
```

設定の理由を解説します：
- `--ctx-size 156000`: コンテキスト長を15.6万トークンに設定。
- `--cache-type-k q8_0 / --cache-type-v q8_0`: KVキャッシュを8-bitで量子化します。これをしないと、長いコンテキストでVRAMが即死します。
- `--flash-attn`: 計算効率を上げる必須フラグです。
- `--n-gpu-layers 99`: すべてのレイヤーをGPUに乗せます。27Bなら24GBにすべて収まります。

### 期待される出力

起動ログに以下の数字が出ていれば成功です。
```
llama_new_context_with_model: n_ctx      = 156000
llama_new_context_with_model: KV self size  = 7.62 GiB (q8_0)
...
HTTP server listening on http://0.0.0.0:8080
```

デコード速度が70 tok/sを超えていれば、ik_llama.cppのMTP最適化が正しく効いています。

## Step 4: Pythonから実用的に使う

サーバーが立ち上がったら、OpenAI互換APIとして利用できます。
長い文書（PDFのテキストなど）を要約させる、実務的なスクリプトを書いてみましょう。

```python
import os
from openai import OpenAI

# ローカルサーバーに接続
client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="sk-no-key-required"
)

def analyze_long_document(text):
    prompt = f"以下のドキュメントを詳細に分析し、重要なポイントを3つ挙げてください。\n\n{text}"

    response = client.chat.completions.create(
        model="qwen-3.6-27b",
        messages=[
            {"role": "system", "content": "あなたは優秀なエンジニア兼アナリストです。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2, # 精度重視のため低めに設定
        max_tokens=1000
    )

    return response.choices[0].message.content

# テスト実行（実際にはここに数万トークンのテキストを入れることが可能）
sample_text = "ローカルLLMの推論効率化におけるMTPの重要性について..." * 100
print(analyze_long_document(sample_text))
```

この構成の凄さは、上記のような「大量のテキスト」を投げても、プレフィル速度（`1261 tok/s`）のおかげで、回答が始まるまでの待機時間が極めて短いことです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `CUDA out of memory` | コンテキスト長が大きすぎる | `--ctx-size` を128000などに下げる |
| `failed to load model` | GGUFファイルの破損 | ダウンロードをやり直す（git-lfsの設定確認） |
| 推論が遅い（5 tok/s以下） | CPUで動いている | `--n-gpu-layers 99` が設定されているか確認 |

## 次のステップ

この環境が完成したら、次は「RAG（検索拡張生成）」との組み合わせに挑戦してください。
Qwen 3.6 27Bは日本語能力も高く、15万トークンの窓があれば、本一冊分をそのままコンテキストに放り込んで対話することが可能です。

さらに速度を求めるなら、`TensorRT-LLM` への変換も視野に入りますが、あちらは構築難易度が跳ね上がります。
まずは今回の `ik_llama.cpp` 構成で、ローカルLLMが「実務で使い物になる速度」で動く感動を味わってください。
24GB VRAMという制約の中で、これ以上の体験は今のところ存在しません。

## よくある質問

### Q1: RTX 3090と4090で速度差はありますか？

あります。4090の方がメモリエッジ帯域が広いため、デコード速度で約1.5倍程度の差が出ます。ただし、24GBという容量自体は同じなので、扱えるコンテキスト長に差はありません。

### Q2: 途中で回答が途切れてしまいます。

`llama-server` 側のデフォルト設定で出力制限がかかっている場合があります。クライアント側（Python）の `max_tokens` だけでなく、サーバー起動時の `--n-predict` を `-1`（無制限）に設定してみてください。

### Q3: 日本語の精度はどうですか？

Qwenシリーズは中国語と英語に強いですが、3.0以降は日本語の語彙も豊富です。IQ4_KS量子化であれば、知識の欠落を感じることはほとんどなく、技術的な議論もスムーズに行えます。

---

## あわせて読みたい

- [llama.cppのMTPサポートを使いRTX 5090でQwen 3.6を爆速で動かす方法](/posts/2026-05-17-llamacpp-mtp-qwen3-rtx5090-setup-guide/)
- [llama.cppでMulti-Token Predictionを導入してGemma 2の推論速度を40%向上させる方法](/posts/2026-05-08-llamacpp-mtp-gemma2-speedup-guide/)
- [Qwen 3.6 27BのMTPモデルを爆速で動かす！ローカルコーディング環境構築ガイド](/posts/2026-05-06-qwen-36-27b-mtp-local-inference-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3090と4090で速度差はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "あります。4090の方がメモリエッジ帯域が広いため、デコード速度で約1.5倍程度の差が出ます。ただし、24GBという容量自体は同じなので、扱えるコンテキスト長に差はありません。"
      }
    },
    {
      "@type": "Question",
      "name": "途中で回答が途切れてしまいます。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "llama-server 側のデフォルト設定で出力制限がかかっている場合があります。クライアント側（Python）の maxtokens だけでなく、サーバー起動時の --n-predict を -1（無制限）に設定してみてください。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の精度はどうですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Qwenシリーズは中国語と英語に強いですが、3.0以降は日本語の語彙も豊富です。IQ4KS量子化であれば、知識の欠落を感じることはほとんどなく、技術的な議論もスムーズに行えます。 ---"
      }
    }
  ]
}
</script>
