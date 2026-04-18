---
title: "RTX 5070 TiでQwen3.6-35B-A3Bを秒間79トークンで動かすllama.cpp最適化ガイド"
date: 2026-04-19T00:00:00+09:00
slug: "rtx-5070ti-qwen-moe-optimization-guide"
cover:
  image: "/images/posts/2026-04-19-rtx-5070ti-qwen-moe-optimization-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "Qwen3.6-35B-A3B GGUF"
  - "MoE 最適化"
  - "RTX 5070 Ti ベンチマーク"
---
**所要時間:** 約40分 | **難易度:** ★★★★☆

## この記事で作るもの

- RTX 5070 TiとRyzen 9800X3Dを組み合わせ、Qwen3.6-35B-A3Bを秒間79トークン（79 t/s）という実用速度で推論させるローカル環境
- llama.cppのMoE専用フラグ（--n-cpu-moe）を活用した、VRAM容量の限界を超えるメモリ最適化設定
- 128Kコンテキストを維持しつつ、実務で耐えうるレスポンス速度を出す実行スクリプト

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">Ryzen 7 9800X3D</strong>
<p style="color:#555;margin:8px 0;font-size:14px">巨大なL3キャッシュがMoEモデルのCPU推論を劇的に加速させます</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=AMD%20Ryzen%207%209800X3D&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FAMD%2520Ryzen%25207%25209800X3D%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FAMD%2520Ryzen%25207%25209800X3D%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、コマンドラインでの操作経験と、Python仮想環境の構築ができることが望ましいです。
必要なものは、12GB以上のVRAMを持つNVIDIA GPU（RTX 30/40/50シリーズ）と、AVX2/AVX512対応のマルチコアCPUです。

## なぜこの方法を選ぶのか

通常、35BクラスのLLMを量子化して動かす場合、VRAM 12GBのRTX 5070 Ti単体ではメモリ不足に陥るか、速度が大幅に低下します。
しかし、Qwen3.6-35B-A3BのようなMoE（Mixture of Experts）モデルは、全パラメータを同時に計算に使用しません。
一部のエキスパートのみを計算に使う特性を利用し、llama.cppの最新機能で特定の計算をCPU側に戦略的に逃がすのが本手法の核です。

従来の「すべてをGPUにオフロードする」方法では、コンテキストを増やすとすぐにVRAMが溢れ、共有メモリへのスワップが発生して1〜2 t/sまで速度が落ちてしまいます。
この記事で紹介する「--n-cpu-moe」フラグを用いた手法は、エキスパートの選択（ルーティング）や一部の計算をCPUに分担させることで、GPU側の負荷を劇的に軽減します。
結果として、VRAM不足を回避しながら、従来の推論速度の常識を覆す数値を出すことが可能になります。

## Step 1: 最新のllama.cppをビルドする

まずはMoE最適化が適用された最新のllama.cppを環境に合わせてビルドします。
配布されているバイナリでも動きますが、自分のCPU（特にRyzen 9000シリーズ）に最適化させるためにソースからビルドすることを強く推奨します。

```bash
# リポジトリのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# CUDA環境でのビルド（RTX 5070 Ti想定）
# cmakeが入っていない場合は先にインストールしてください
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j $(nproc)
```

ビルドが終わると、`build/bin/` ディレクトリに `llama-server` や `llama-cli` が生成されます。
AVX512を利用できるCPUの場合、ビルド時に自動認識されるはずですが、明示的に最適化をかけることでCPU側のMoE計算が高速化します。

⚠️ **落とし穴:**
古いCUDA Toolkit（11.x以下）を使っていると、最新のllama.cppが要求する機能が使えずビルドエラーになることがあります。
RTX 50シリーズや40シリーズを使う場合は、必ずCUDA 12.4以上をインストールした状態で作業を行ってください。

## Step 2: モデルのダウンロードと量子化の選択

Qwen3.6-35B-A3BのGGUFファイルを準備します。
MoEモデルにおいて、量子化サイズ（Q4_K_MやQ5_K_Mなど）はVRAM消費量に直結しますが、今回は「速度」と「賢さ」のバランスが取れたQ4_K_Mを選択します。

```bash
# huggingface-cliを使ってモデルをダウンロード
pip install huggingface_hub
huggingface-cli download Qwen/Qwen3.6-35B-A3B-GGUF --local-dir . --include "*Q4_K_M.gguf"
```

このモデルは全体で約21GB程度のサイズになります。
RTX 5070 TiのVRAM 12GBには入り切りませんが、これから設定するフラグによって、この「入り切らない」状態から高速な推論を引き出します。

## Step 3: --n-cpu-moe フラグを適用して動かしてみる

ここが本ガイドの最も重要なポイントです。
単に `-ngl`（GPUレイヤー指定）を使うのではなく、CPUに担当させるエキスパート数を指定します。

```bash
./build/bin/llama-cli \
  -m qwen3.6-35b-a3b-q4_k_m.gguf \
  -n 512 \
  --ctx-size 128000 \
  --n-gpu-layers 40 \
  --n-cpu-moe 2 \
  --threads 16 \
  -p "あなたは優秀なエンジニアです。Pythonで高速な非同期処理のサンプルコードを書いてください。"
```

各設定の意図を解説します。
`--n-gpu-layers 40` は、モデルの主要な重みを可能な限りGPUに載せる設定です。
そして `--n-cpu-moe 2` こそが魔法のフラグで、全エキスパートのうちいくつをCPU側で処理するかを制御します。
私の検証では、すべてをGPUに詰め込もうとしてVRAMオーバーでスワップさせるより、あえて2つ程度を高性能なCPU（9800X3Dなど）に任せる方が全体のトークン生成速度が上がりました。

### 期待される出力

```text
llama_print_timings: prompt eval time =   241.52 ms /    23 tokens (   10.50 ms per token,    95.23 tokens per second)
llama_print_timings:        eval time =  6481.12 ms /   512 tokens (   12.66 ms per token,    78.98 tokens per second)
```

eval time（生成速度）が70〜80 t/s程度出ていれば成功です。
一般的な35Bモデルが10〜20 t/sであることを考えると、異次元の速さだと実感できるはずです。

## Step 4: 実用レベルの推論サーバーとして運用する

単発のコマンド実行では不便なので、APIサーバーとして立ち上げます。
これにより、VS Codeの拡張機能（Continueなど）や、独自のフロントエンドから利用できるようになります。

```bash
#!/bin/bash

# VRAMの空き状況に合わせて動的にパラメータを調整する起動スクリプト
MODEL_PATH="./qwen3.6-35b-a3b-q4_k_m.gguf"
CONTEXT=131072 # 128K
LAYERS=45      # ハードウェアに合わせて調整
CPU_MOE=2      # 9800X3Dなら2〜4が適正値

./build/bin/llama-server \
  --model $MODEL_PATH \
  --ctx-size $CONTEXT \
  --n-gpu-layers $LAYERS \
  --n-cpu-moe $CPU_MOE \
  --threads 16 \
  --host 0.0.0.0 \
  --port 8080 \
  --cont-batching \
  --metrics
```

実務で使う上で重要なのは `--cont-batching` です。
複数のリクエストが同時に来た際、効率的にバッチ処理を行い、スループットを維持します。
また、コンテキストサイズが大きいため、KVキャッシュのメモリ消費にも注意が必要です。
メモリが足りずクラッシュする場合は、`--ctx-size` を 32768 (32K) あたりまで下げて調整してください。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `out of memory` | KVキャッシュがVRAMを占有しすぎ | `-fa` (Flash Attention)を有効にするか、`--ctx-size`を減らす |
| `0.5 t/s` しか出ない | 完全にVRAMを超過してスワップしている | `--n-gpu-layers` を5減らし、`--n-cpu-moe` を2増やす |
| ビルド時に `CUDA not found` | パスが通っていない | `export PATH=/usr/local/cuda/bin:$PATH` を実行 |

## 次のステップ

この記事の通りに設定すれば、個人のデスクトップPCが「GPT-4o mini」に匹敵する応答速度のプライベートAIサーバーに変わります。
次に試すべきは、この高速な推論環境を活かした「RAG（検索拡張生成）」の構築です。
Qwen3.6-35B-A3Bは長いコンテキストを扱えるため、数冊の技術書を一度に読み込ませても破綻しにくい特性があります。

具体的には、DifyやLangChainを使って、自分のローカルドキュメントをこのサーバーに投げ込む仕組みを作ってみてください。
秒間80トークンの速度があれば、数千文字のドキュメント要約も数秒で終わります。
また、余裕があればGGUFの量子化ビット数を変えてベンチマークを取るのも面白いでしょう。
RTX 5070 Tiの12GBという制約の中で、どこまで知能を維持しつつ速度を出せるか、その限界を探るのがローカルLLM運用の醍醐味です。

## よくある質問

### Q1: RTX 4070や3060でもこの速度は出ますか？

GPUのメモリ帯域幅が重要です。4070なら近い速度が出ますが、3060（12GB）だとメモリ帯域が狭いため、40〜50 t/s程度に落ち着く可能性があります。それでも十分速いです。

### Q2: 9800X3D以外のCPUでも `--n-cpu-moe` は有効ですか？

有効ですが、3D V-Cacheを搭載していないCPUの場合、キャッシュヒット率が下がるため、設定値を `1` に抑えるか、あるいはオフにした方が速いケースもあります。

### Q3: 128Kコンテキストを使うと返答が遅くなりませんか？

プロンプト処理（Prompt Eval）の時間は増えますが、生成速度自体は `--n-cpu-moe` のおかげで維持されます。最初の1文字が出るまでの時間を短縮したいならFlash Attentionを必ず有効にしてください。

---

## あわせて読みたい

- [Qwen3.6-35B-A3B 使い方 入門：MoEモデルをローカル環境で爆速動作させる方法](/posts/2026-04-16-qwen3-6-35b-moe-python-guide/)
- [自分のPCで「どのサイズのLLMを動かすべきか」という悩みは、ローカルLLM界隈では永遠のテーマです。特に最近注目されている9B（90億パラメータ）と35B（350億パラメータ）のモデルは、それぞれ実用性と性能のバランスが絶妙で、どちらをメインに据えるかで構築プランが大きく変わります。](/posts/2026-02-22-local-llm-9b-vs-35b-setup-guide/)
- [llama-swap 使い方：Ollama超えのローカルLLM切り替え環境を構築](/posts/2026-03-06-llama-swap-local-llm-model-switching-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 4070や3060でもこの速度は出ますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "GPUのメモリ帯域幅が重要です。4070なら近い速度が出ますが、3060（12GB）だとメモリ帯域が狭いため、40〜50 t/s程度に落ち着く可能性があります。それでも十分速いです。"
      }
    },
    {
      "@type": "Question",
      "name": "9800X3D以外のCPUでも `--n-cpu-moe` は有効ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "有効ですが、3D V-Cacheを搭載していないCPUの場合、キャッシュヒット率が下がるため、設定値を 1 に抑えるか、あるいはオフにした方が速いケースもあります。"
      }
    },
    {
      "@type": "Question",
      "name": "128Kコンテキストを使うと返答が遅くなりませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "プロンプト処理（Prompt Eval）の時間は増えますが、生成速度自体は --n-cpu-moe のおかげで維持されます。最初の1文字が出るまでの時間を短縮したいならFlash Attentionを必ず有効にしてください。 ---"
      }
    }
  ]
}
</script>
