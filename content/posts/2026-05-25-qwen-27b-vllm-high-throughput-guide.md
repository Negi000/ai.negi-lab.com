---
title: "Qwen2.5 27Bを爆速化 vLLMでスループットを極限まで高めるやり方"
date: 2026-05-25T00:00:00+09:00
slug: "qwen-27b-vllm-high-throughput-guide"
cover:
  image: "/images/posts/2026-05-25-qwen-27b-vllm-high-throughput-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "vLLM 使い方"
  - "Qwen2.5 27B"
  - "推論 高速化"
  - "ローカルLLM ベンチマーク"
---
**所要時間:** 約45分 | **難易度:** ★★★★☆

## この記事で作るもの

- vLLM（推論最適化エンジン）を用いて、Qwen2.5 27BをGPUの限界まで回す推論環境
- 数十から数百のリクエストを並列処理し、スループット（tps）を最大化するPythonスクリプト
- 自身の環境で「秒間何トークン出ているか」を正確に測定するベンチマークコード

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">24GB VRAMは27Bモデルを量子化して高速運用する際の最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、Linuxの基本操作とDockerもしくはPythonの仮想環境（venv/conda）の扱いに慣れている必要があります。ハードウェアは、VRAM 24GB以上のGPU（RTX 3090/4090）が1枚、もしくはV100/A100クラスが複数枚ある環境を想定します。

## 先に確認するスペック・料金

Qwen2.5 27Bを動かす上で、最大の壁はVRAM（ビデオメモリ）容量です。FP16（通常の精度）で動かそうとすると、モデルだけで約54GBのVRAMを消費するため、個人向けのRTX 4090（24GB）1枚では到底足りません。

現実的な選択肢は2つです。一つはAWQやGPTQといった手法で「4bit量子化」されたモデルを使い、VRAMを18GB程度に抑えて24GBのGPU1枚で動かすこと。もう一つは、クラウドGPU（Lambda LabsやRunPodなど）でV100（32GB）を2枚、あるいはA100を1枚借りることです。

V100は古い世代ですが、メモリ帯域幅が900GB/sと広いため、Redditの報告にあるような「数千トークンの並列処理」には非常に向いています。中古のV100 32GBは現在10万円前後で入手可能ですが、消費電力と排熱を考えると、まずはクラウドで1時間$0.7〜$1.5程度払って試すのが賢明です。Apple Silicon（Mac）でも動作は可能ですが、vLLMの最適化の恩恵をフルに受けるなら、現状はNVIDIA GPU一択といえます。

## なぜこの方法を選ぶのか

ローカルLLMを動かす際、多くの人が最初に使うのはOllamaやllama.cppでしょう。これらは「1人のユーザーが1つのプロンプトを投げて対話する」には最適ですが、スループット（単位時間あたりの処理量）を稼ぐには不向きです。

今回採用する「vLLM」は、PagedAttentionという技術により、メモリ管理の無駄を徹底的に排除しています。通常の推論エンジンがリクエストごとに固定のメモリを確保して自滅する中、vLLMはOSの仮想メモリのように動的に管理するため、同じハードウェアでも並列処理能力が数倍から十数倍に跳ね上がります。

Redditの報告で1000 tpsを超えているのは、この「並列リクエストの詰め込み」がうまくいっているからです。単一のレスポンスが速くなるのではなく、1秒間に全体で1000文字以上の回答を生成できる状態、つまり「実務で数千件のデータを一括処理する」ための最強の構成を目指します。

## Step 1: 環境を整える

vLLMは依存関係が非常にシビアです。特にCUDAバージョンとPyTorchの整合性が崩れると、性能が半分以下になるか、そもそも起動しません。ここではUbuntu環境を前提に、最も確実なインストール手順を踏みます。

```bash
# Python 3.10以上の環境を作成
conda create -n vllm_env python=3.11 -y
conda activate vllm_env

# CUDA 12.1以上が入っていることを確認
nvcc --version

# vLLMのインストール（公式のビルド済みバイナリを使用）
pip install vllm==0.6.3.post1

# 量子化モデルを扱うための追加ライブラリ
pip install ray vllm-flash-attn
```

vLLM 0.6.x系はQwen2.5系にネイティブ対応しており、追加のパッチなしでモデルの性能を引き出せます。`vllm-flash-attn`を入れる理由は、推論時のアテンション計算を高速化し、VRAM消費を抑えるためです。これがないと、長い文脈（コンテキスト）を扱った瞬間に速度がガタ落ちします。

⚠️ **落とし穴:**
WSL2で動かす場合、デフォルトのメモリ割り当て制限に引っかかり、モデルのロード中にプロセスが「Killed」されることがよくあります。`.wslconfig`でシステムメモリの80%程度を割り当てておくか、素直にネイティブのLinux環境で動かすことを強くおすすめします。

## Step 2: 基本の設定

次に、PythonからvLLMを呼び出し、Qwen2.5 27Bをロードします。ここでは24GBのGPU1枚でも動くように、4bit量子化されたモデル（AWQ版）を指定する設定例を紹介します。

```python
import os
from vllm import LLM, SamplingParams

# モデルの指定（Quantizedモデルを使うのが実務的）
# 24GB GPUならQwen/Qwen2.5-27B-Instruct-AWQ
model_id = "Qwen/Qwen2.5-27B-Instruct-AWQ"

# LLMエンジンの初期化
# gpu_memory_utilization: GPUメモリの何%をKVキャッシュに使うか。0.9が安定
# max_model_len: 扱う最大トークン数。長くしすぎるとVRAMを圧迫する
llm = LLM(
    model=model_id,
    gpu_memory_utilization=0.90,
    max_model_len=4096,
    trust_remote_code=True
)

# 生成パラメータの設定
# temperature=0で決定論的な回答をさせ、速度を安定させる
sampling_params = SamplingParams(
    temperature=0.0,
    top_p=0.95,
    max_tokens=512,
    presence_penalty=1.1
)
```

`gpu_memory_utilization`を0.9に設定しているのは、残りの10%をシステムのオーバーヘッドや一時的な計算用に空けておくためです。ここを1.0にすると、リクエストが集中した瞬間にOOM（Out of Memory）で落ちます。また、`trust_remote_code=True`は、Qwen独自のアーキテクチャ定義を読み込むために必要です。

## Step 3: 動かしてみる

まずはシングルリクエストで動作確認を行い、その後に「並列処理」がいかに速いかを体感します。

```python
# テスト用のプロンプト
prompts = [
    "AIエージェントの将来性について、3つのポイントで説明してください。",
]

# 推論実行
outputs = llm.generate(prompts, sampling_params)

# 結果の表示
for output in outputs:
    prompt = output.prompt
    generated_text = output.outputs[0].text
    print(f"Prompt: {prompt}")
    print(f"Generated text: {generated_text}")
```

### 期待される出力

```
AIエージェントの将来性について、以下の3つのポイントで説明します。
1. 自律性の向上: 従来のツールとは異なり、目標を設定するだけで自らタスクを分解し実行する能力が進化します。
2. パーソナライズ化: ユーザーの過去の行動や好みを学習し、最適なタイミングで支援を行うようになります。
3. マルチモーダル対応: テキストだけでなく、画像や音声、リアルタイムの画面情報を統合して理解し、操作が可能になります。
```

単一のリクエストでは、おそらく秒間50〜80トークン程度でしょう。これでも十分に速いですが、vLLMの本領はここからです。

## Step 4: 実用レベルにする（スループットの最大化）

Redditの「1000 tps」を再現するためには、大量のプロンプトを一度に流し込みます。vLLM内部のスケジューラが、これらを効率よくバッチ化してGPUに叩き込みます。

```python
import time

# 大量のダミーリクエストを作成（100件）
test_prompts = [
    "Pythonでクイックソートを実装して。" for _ in range(100)
]

start_time = time.perf_counter()

# 100件を一括生成
outputs = llm.generate(test_prompts, sampling_params)

end_time = time.perf_counter()

# 統計情報の計算
total_tokens = sum(len(output.outputs[0].token_ids) for output in outputs)
duration = end_time - start_time
tps = total_tokens / duration

print(f"処理時間: {duration:.2f} 秒")
print(f"生成トークン数: {total_tokens}")
print(f"スループット (TPS): {tps:.2f} tokens/s")
```

このコードを実行すると、GPUの使用率が100%に張り付き、ファンが激しく回るはずです。RTX 4090 1枚でも、量子化モデルを使えば数百tpsは簡単に出ます。もしV100を複数枚並列（Tensor Parallel）で動かしているなら、ここで4桁の数字が見えてきます。

実務で使う場合は、これを`FastAPI`などでラップし、Web APIとして公開するのが一般的です。vLLMには標準でOpenAI互換サーバー機能が備わっているので、以下のコマンド一つで「自前GPT-4o mini」のようなサーバーが立ち上がります。

```bash
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-27B-Instruct-AWQ \
    --gpu-memory-utilization 0.9 \
    --port 8000
```

これでCursorやDifyといった外部ツールから、自作の爆速Qwenサーバーを叩けるようになります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Out of Memory (OOM)` | KVキャッシュの確保失敗 | `gpu_memory_utilization`を下げるか、`max_model_len`を小さくする |
| `FlashAttention not found` | ライブラリ未導入 | `pip install vllm-flash-attn`を実行し、CUDAバージョンを合わせる |
| `Model is not supported` | vLLMのバージョンが古い | `pip install --upgrade vllm`で最新版にする |
| スループットが出ない | リクエスト数が少なすぎる | プロンプトを一度に数百件投げてバッチ処理を効かせる |

## 次のステップ

爆速の推論環境が手に入ったら、次は「精度」と「コスト」のバランスを攻めるべきです。

1. **Speculative Decoding（投機的サンプリング）の導入**:
   Qwen2.5 27Bのような巨大なモデルの前に、Qwen2.5 0.5Bのような極小モデルを「ドラフトモデル」として置く手法です。小さなモデルが先に予測し、大きなモデルがそれを検証することで、精度を維持したままさらに2倍程度の高速化が狙えます。

2. **RAG（検索拡張生成）との統合**:
   この速度があれば、数千件のドキュメントから検索した結果をプロンプトに詰め込み、片っ端から要約・分析させる「力技のデータ処理」が可能になります。LangChainやLlamaIndexと組み合わせて、社内データの超高速スキャンツールを作ってみてください。

3. **マルチGPU環境への拡張**:
   もしGPUを増やせるなら、`tensor_parallel_size`をGPUの数に合わせるだけで、処理能力はほぼ線形に伸びます。RTX 4090を2枚挿して27BモデルをFP16で動かす快感は、一度味わうと戻れません。

## よくある質問

### Q1: V100 16GBを2枚持っていますが、Qwen 27Bは動きますか？

動きますが、FP16ではメモリ不足です。4bit量子化（AWQ）モデルを使えば、1枚あたり約9GBの消費で済むため、2枚あれば余裕を持って動作します。むしろVRAMが余る分、コンテキスト長を32k以上に伸ばす設定が可能です。

### Q2: なぜAWQ量子化を勧めるのですか？

GPTQよりも量子化による精度劣化が少なく、かつ推論速度が速い傾向にあるからです。特にQwenシリーズはAWQとの相性が良く、実務で使うなら「迷ったらAWQ」と言えるほど安定しています。

### Q3: 1000 tpsも必要ですか？個人のチャットなら10 tpsで十分では？

個人利用なら不要です。しかし、AIエージェントに「100個のタスクを並列で実行させる」場合や、大規模なデータセットにタグ付けをする実務案件では、1000 tpsという数字が「数時間かかる仕事」を「数分」に変える決定的な差になります。

---

## あわせて読みたい

- [AMD MI50でQwen 2.5 27Bを爆速化してローカルLLMサーバーを構築する方法](/posts/2026-05-14-amd-mi50-qwen-vllm-setup-guide/)
- [Qwen2.5-Coder 使い方 | ローカルでGPT-4o級の開発環境をPythonで構築する](/posts/2026-03-21-qwen2-5-coder-python-local-guide/)
- [Qwen2.5-Coder 使い方 | ローカルでコード生成AIを動かす](/posts/2026-05-19-qwen-coder-local-setup-python-refactor/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "V100 16GBを2枚持っていますが、Qwen 27Bは動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、FP16ではメモリ不足です。4bit量子化（AWQ）モデルを使えば、1枚あたり約9GBの消費で済むため、2枚あれば余裕を持って動作します。むしろVRAMが余る分、コンテキスト長を32k以上に伸ばす設定が可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "なぜAWQ量子化を勧めるのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "GPTQよりも量子化による精度劣化が少なく、かつ推論速度が速い傾向にあるからです。特にQwenシリーズはAWQとの相性が良く、実務で使うなら「迷ったらAWQ」と言えるほど安定しています。"
      }
    },
    {
      "@type": "Question",
      "name": "1000 tpsも必要ですか？個人のチャットなら10 tpsで十分では？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "個人利用なら不要です。しかし、AIエージェントに「100個のタスクを並列で実行させる」場合や、大規模なデータセットにタグ付けをする実務案件では、1000 tpsという数字が「数時間かかる仕事」を「数分」に変える決定的な差になります。 ---"
      }
    }
  ]
}
</script>
