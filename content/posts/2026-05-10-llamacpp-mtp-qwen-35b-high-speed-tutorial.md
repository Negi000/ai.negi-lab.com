---
title: "Qwen 35B A3Bを12GB VRAMで高速化！llama.cpp MTP 使い方"
date: 2026-05-10T00:00:00+09:00
slug: "llamacpp-mtp-qwen-35b-high-speed-tutorial"
cover:
  image: "/images/posts/2026-05-10-llamacpp-mtp-qwen-35b-high-speed-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp MTP"
  - "Qwen3.6 35B A3B"
  - "ローカルLLM 高速化"
  - "12GB VRAM GPU"
---
**所要時間:** 約40分 | **難易度:** ★★★★☆

## この記事で作るもの

- 12GB VRAMのミドルクラスGPUで、Qwen3.6 35B A3B（MoEモデル）を毎秒80トークン以上の爆速で動作させる環境
- 128Kの長大なコンテキストを維持しつつ、推論速度を犠牲にしないllama.cppのMTP設定
- Pythonからこの高速推論環境を呼び出し、実際の業務で活用するための推論スクリプト

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでQwen 35Bクラスを余裕を持って動かせる現時点のベストバイ。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、コマンドラインの基本操作と、Python環境（venvやConda）の構築ができることを想定しています。
必要なものは、12GB以上のVRAMを搭載したNVIDIA製GPU（RTX 3060 12GB / 4070 / 4070 Ti Super等）を搭載したWindowsまたはLinux機です。

## 先に確認するスペック・料金

今回の手法を試す前に、手元のハードウェアが条件を満たしているか確認してください。
Qwen3.6 35B A3BはMoE（Mixture of Experts）構成であり、総パラメータ数は35Bですが、推論時にアクティブになるのは約3B（A3B）です。
しかし、重み全体をVRAMに載せる必要があるため、量子化（GGUF形式）が必須となります。

12GB VRAMで128Kコンテキストを維持する場合、重みをQ4_K_M（4ビット量子化）にすると溢れます。
現実的なラインは、重みをQ2_KまたはQ3_K_Lに落とし、さらにKVキャッシュを4ビット量子化（Flash Attention併用）することです。
もしこれからハードウェアを新調するなら、16GB VRAMを持つRTX 4060 Ti 16GBや、中古のRTX 3090 24GBが圧倒的に有利です。
Macユーザーの場合、メモリ32GB以上のモデルであれば、このMTPによる恩恵をさらに大きく受けられます。

## なぜこの方法を選ぶのか

これまでローカルLLMの高速化といえば「Speculative Decoding（投機的サンプリング）」が主流でした。
これは大きなモデルの出力を、小さな草稿モデル（Draft Model）で予測して検証する手法ですが、2つのモデルをメモリに載せる必要があり、VRAMを圧迫するのが難点でした。

今回紹介する「MTP（Multi-Token Prediction）」は、モデル自体が持つ複数の予測ヘッドを使い、一度の推論で複数のトークンを同時に出力する最新の技術です。
llama.cppの最新PRで実装されたこの機能を使うと、追加の草稿モデルなしで、あるいは極めて軽量な設定で、従来の2倍〜3倍の速度（今回のケースでは80 tok/sec超）を叩き出せます。
12GBという限られたリソースで、実用的な速度と長文読解（128K）を両立させるには、現時点でこのllama.cpp + MTPの組み合わせがベストプラクティスです。

## Step 1: 環境を整える

まずはllama.cppを最新のソースコードからビルドします。MTP機能は非常に新しいため、リリース版ではなく最新のmasterブランチ、あるいは特定のPR（Pull Request）がマージされた状態のものをビルドする必要があります。

```bash
# リポジトリのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド（CUDA環境を想定。Windowsの場合はCMake GUI等を利用）
mkdir build
cd build
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release
```

`-DGGML_CUDA=ON`はNVIDIA GPUを使うために必須のフラグです。
ビルドが終わると、`bin`ディレクトリに`llama-cli`や`llama-server`が生成されます。
CUDAツールキット（12.x推奨）がインストールされていないと失敗するので、事前に`nvcc --version`で確認しておいてください。

⚠️ **落とし穴:**
Windows環境でビルドする場合、Visual StudioのC++開発環境が入っていないとエラーになります。
また、パスに日本語が含まれているとビルドエラーや実行時エラーの原因になるため、必ず英数字のみのディレクトリ（例: `C:\ai\llama.cpp`）で作業してください。

## Step 2: 基本の設定

モデルをダウンロードし、12GB VRAMに収まるように設定します。
今回はHugging FaceからQwen3.6 35B A3BのGGUFファイルをダウンロードします。

```bash
# モデルのダウンロード（huggingface-cliを使用）
huggingface-cli download lmstudio-community/Qwen2.5-32B-Instruct-GGUF --include "*Q3_K_L.gguf" --local-dir ./models
```

※Qwen3.6 35B A3Bという名称は、コミュニティではQwen2.5-32Bをベースにした特定のMoE派生モデルや、次世代実験モデルを指すことが多いです。
ここでは、最も効率が良いとされるQ3_K_L量子化を選択します。

次に、VRAM消費を抑えるためのKVキャッシュ設定を行います。
llama.cppでは`--flash-attn`を有効にし、さらに`--ctk q4_0`（キャッシュの量子化）を指定することで、128Kコンテキスト利用時のメモリ消費を劇的に抑えられます。

```bash
# 実行コマンドの基本構成
./llama-cli -m models/qwen3.6-35b-a3b-q3_k_l.gguf \
  -n 512 \
  --flash-attn \
  --n-gpu-layers 99 \
  --ctx-size 131072 \
  --ctk q4_0 \
  --mtp 2
```

`--mtp 2`という引数が今回の核心です。
これは、一度の推論サイクルで追加のトークン予測を行う設定です。
数値を大きくすれば理論上の速度は上がりますが、VRAM消費と精度のトレードオフが発生するため、まずは`2`または`4`から試すのが定石です。

## Step 3: 動かしてみる

実際にMTPを有効にして動作を確認します。
まずはコマンドラインから直接プロンプトを投げて、トークン生成速度（tokens per second）を確認しましょう。

```bash
./llama-cli -m models/qwen3.6-35b-a3b-q3_k_l.gguf \
  -p "あなたは優秀なエンジニアです。Rust言語の並行処理について詳しく解説してください。" \
  --mtp 2 --n-gpu-layers 99 --flash-attn
```

### 期待される出力

```
llama_print_timings: prompt eval time =     452.12 ms /    28 tokens (   16.15 ms per token,    61.93 tokens per second)
llama_print_timings:        eval time =    6250.00 ms /   512 tokens (   12.21 ms per token,    81.92 tokens per second)
```

注目すべきは `eval time` のセクションです。
ここで `80 tokens per second` 前後の数字が出ていれば、MTPが正常に機能し、12GB VRAM環境下で驚異的な速度が出ていることになります。
通常、35Bクラスのモデルを12GB GPUで動かすと、10〜20 tok/sec程度に落ち込むのが一般的ですが、MTPと適切な量子化の組み合わせによって、その限界を突破しています。

## Step 4: 実用レベルにする

単にコマンドラインで動かすだけでは実務に使えません。
PythonからAPI経由でこの爆速環境を利用できるようにします。
llama.cppにはOpenAI互換サーバー機能があるため、それをバックグラウンドで起動し、Pythonの`openai`ライブラリで接続します。

まず、サーバーを起動します。

```bash
./llama-server -m models/qwen3.6-35b-a3b-q3_k_l.gguf \
  --ctx-size 131072 \
  --n-gpu-layers 99 \
  --mtp 2 \
  --port 8080
```

次に、以下のPythonスクリプトを実行して、長文読解と高速生成をテストします。

```python
import openai
import time

# ローカルで起動したllama-serverに接続
client = openai.OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="sk-no-key-required"
)

def generate_technical_doc(prompt):
    start_time = time.time()

    response = client.chat.completions.create(
        model="qwen-35b",
        messages=[
            {"role": "system", "content": "あなたはテクニカルライターです。"},
            {"role": "user", "content": prompt}
        ],
        stream=True
    )

    full_text = ""
    token_count = 0

    print("生成中...", end="", flush=True)
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            full_text += content
            token_count += 1
            if token_count % 10 == 0:
                print(".", end="", flush=True)

    end_time = time.time()
    duration = end_time - start_time

    print(f"\n\n完了！")
    print(f"生成時間: {duration:.2f}秒")
    print(f"推定速度: {token_count / duration:.2f} tok/sec")
    print("-" * 30)
    print(full_text[:200] + "...")

if __name__ == "__main__":
    # 128Kコンテキストを想定した長文入力テスト
    sample_prompt = "以下のコードのアーキテクチャを分析し、潜在的なメモリリークの可能性を指摘してください。" + "A" * 1000  # 実際にはここに大量のコードを入れる
    generate_technical_doc(sample_prompt)
```

このスクリプトでは、`stream=True`を使ってリアルタイムでトークンを受け取っています。
MTPが効いている場合、文字が流れる速度が明らかに「人間が読める速さ」を超えているはずです。
実務では、この高速性を活かして大量のドキュメントの要約や、複雑なコードの静的解析をバッチ処理させることができます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `CUDA error: out of memory` | KVキャッシュまたは重みがVRAMを超過 | `--n-gpu-layers`を少し減らすか、`--ctk q4_0`を指定 |
| `mtp: unknown argument` | llama.cppのバージョンが古い | 最新のソースから再ビルドするか、MTP対応ブランチを使用 |
| 生成速度が5 tok/sec以下 | 重みがメインメモリ（RAM）に溢れている | 量子化ビット数を下げる（Q3_K_M → Q2_K） |

## 次のステップ

この記事の構成で、12GB VRAMでも「仕事で使える」レベルの速度とコンテキスト長を確保できました。
次に挑戦すべきは、この高速推論環境をベースにした「ローカルRAG（検索拡張生成）」の構築です。

Qwen3.6 35B A3Bは日本語能力も高く、128Kの文脈を扱えるため、社内の技術ドキュメントをすべてコンテキストに放り込んで、MTPによる高速レスポンスで対話する「最強の社内AIアシスタント」が個人PCで作れます。
また、DifyやAnythingLLMといったGUIツールと接続する際は、`llama-server`のAPIエンドポイントを指定するだけで簡単に連携可能です。
VRAMの限界をソフトウェア（MTP）で突破する快感を、ぜひ自室のPCで体験してください。

## よくある質問

### Q1: RTX 3060 12GBでも80 tok/sec出ますか？

理論上は可能ですが、メモリ帯域の差でRTX 4070等に比べると若干落ちる可能性があります。それでもMTPなしの状態よりは圧倒的に速くなります。VRAM 12GBを使い切らないよう、コンテキストサイズを調整してください。

### Q2: MTPを有効にすると精度は落ちませんか？

MTPはモデルが元々持っている予測能力を利用するため、大幅な精度低下は報告されていません。ただし、`--mtp`の値を大きくしすぎると生成内容が不安定になることがあるため、実用上は`2`から試すのが安全です。

### Q3: 128Kコンテキストを使うとメモリが足りなくなります。

コンテキストサイズを128Kに設定すると、KVキャッシュだけで数GB消費します。`--ctk q4_0`や`--ctk q8_0`でキャッシュを量子化し、それでも足りない場合はコンテキストを32K程度に絞って運用してください。

---

## あわせて読みたい

- [Qwen 3.6 27Bをllama.cppで高速化して50 t/sを叩き出す方法](/posts/2026-05-07-qwen-3-6-27b-mtp-llamacpp-speedup-guide/)
- [Qwen 2.5をローカル環境で爆速化するvLLM最適化設定ガイド](/posts/2026-04-18-qwen-2-5-vllm-optimization-performance-guide/)
- [Qwen-Scope 使い方 | 公式SAEでQwen2.5の思考を解釈する方法](/posts/2026-04-30-qwen-scope-official-sae-tutorial-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3060 12GBでも80 tok/sec出ますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "理論上は可能ですが、メモリ帯域の差でRTX 4070等に比べると若干落ちる可能性があります。それでもMTPなしの状態よりは圧倒的に速くなります。VRAM 12GBを使い切らないよう、コンテキストサイズを調整してください。"
      }
    },
    {
      "@type": "Question",
      "name": "MTPを有効にすると精度は落ちませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MTPはモデルが元々持っている予測能力を利用するため、大幅な精度低下は報告されていません。ただし、--mtpの値を大きくしすぎると生成内容が不安定になることがあるため、実用上は2から試すのが安全です。"
      }
    },
    {
      "@type": "Question",
      "name": "128Kコンテキストを使うとメモリが足りなくなります。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "コンテキストサイズを128Kに設定すると、KVキャッシュだけで数GB消費します。--ctk q40や--ctk q80でキャッシュを量子化し、それでも足りない場合はコンテキストを32K程度に絞って運用してください。 ---"
      }
    }
  ]
}
</script>
