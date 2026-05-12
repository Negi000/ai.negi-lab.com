---
title: "Qwen2.5-122Bクラスの巨大なローカルLLMを、サーマルスロットリング（熱による速度低下）を起こさずに安定稼働させるための推論環境を構築します。"
date: 2026-05-12T00:00:00+09:00
slug: "high-end-llm-cooling-setup-guide"
cover:
  image: "/images/posts/2026-05-12-high-end-llm-cooling-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen2.5-122B"
  - "llama.cpp 使い方"
  - "マルチGPU LLM"
  - "GPU 冷却 対策"
---
この記事の手順を完了すると、GPU温度を監視しながら最適なパフォーマンスで巨大モデルを回し続ける「温度管理機能付き推論サーバー」が手に入ります。
Redditで話題になった「DGXを水道水で冷やす」という極端な事例をヒントに、実務で100GB超のモデルを扱う際の現実的な冷却戦略と設定を解説します。

**所要時間:** 約60分 | **難易度:** ★★★★☆

## この記事で作るもの

- Qwen2.5-122B（MoE）などの100GB超えモデルをマルチGPUで並列駆動させるPythonスタック
- GPUの温度上限を検知し、自動で推論リクエストを制限またはスロットリングする監視スクリプト
- 前提知識: Linuxの基本操作、Pythonでの環境構築（venv/conda）、Dockerの基礎

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 3090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 24GB搭載で、複数枚刺しによる巨大モデル運用において最もコスパが良い。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2520%25E4%25B8%25AD%25E5%258F%25A4%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2520%25E4%25B8%25AD%25E5%258F%25A4%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203090%2024GB%20%E4%B8%AD%E5%8F%A4&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

今回のターゲットであるQwen2.5-122B-a10BのQ6_K精度は、モデルサイズだけで約110GBあります。
これを動かすには、最低でも合計120GB以上のVRAM（ビデオメモリ）が必要です。
一般消費者向けのRTX 4090（24GB）なら5枚、あるいはRTX 3090（24GB）を5枚用意する、変態的な構成が求められます。

もし個人でDGX（A100/H100 8枚構成）を所有しているなら理想的ですが、現実的にはMac Studio（M2 Ultra / M3 Ultra）のメモリ192GBモデルが最も安価な代替案になります。
Windows/Linux機で組むなら、中古のRTX 3090を複数枚刺しし、電源ユニットを2基（1200W+1000Wなど）用意するのが、実務上の「最安」構成です。
電気代はフル稼働で月額数万円を見込む必要がありますが、API課金を数千万トークン単位で行うよりは安く済みます。

## なぜこの方法を選ぶのか

巨大LLMの推論において、最大の敵は「熱」です。
Redditの投稿者はDGXを水道水で冷やすことで、95%の高負荷時でも68度以下を維持したと報告していますが、これはGPUの寿命と推論速度を両立させるために極めて合理的です。
GPUは通常80〜90度に達すると、ハードウェア保護のためにクロック周波数を下げますが、これが発生するとレスポンスが極端に悪化します。

本ガイドでは、冷却設備の物理的な改造（水冷化）を推奨するのではなく、ソフトウェア側で「温度の壁」を制御する方法を採ります。
具体的には、llama.cppのサーバー機能をベースに、GPU温度が一定値を超えた場合に推論を一時待機させるラッパーを構築します。
これにより、高価なハードウェアを熱死させるリスクを最小限に抑えつつ、夜通しのバッチ処理などを安定して回せるようになります。

## Step 1: 環境を整える

まずはNVIDIAドライバとCUDAツールキット、そして推論エンジンの核となるllama.cppをビルドします。
マルチGPU環境を前提とするため、CUDAのピアツーピア通信設定を最適化します。

```bash
# NVIDIAドライバの確認
nvidia-smi

# llama.cppのクローンとビルド（CUDAサポート有効）
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build
cd build
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release -j $(nproc)
```

llama.cppをソースからビルドするのは、最新のMoE（Mixture of Experts）モデルへの対応速度が最も速いからです。
`-DGGML_CUDA=ON`フラグは、全レイヤーをGPUにオフロードするために必須の設定です。
CPUとの混合推論は、このクラスのモデルでは遅すぎて実務になりません。

⚠️ **落とし穴:** 複数枚のGPUを刺している場合、PCIeレーンの帯域不足で速度が出ないことがあります。
マザーボードが「x8/x8/x8/x8」以上の分割に対応しているか確認してください。x4以下のレーンに刺さっているGPUがあると、そこがボトルネックになり全体の推論速度が30%以上低下します。

## Step 2: 基本の設定

次に、巨大なモデルファイルをダウンロードし、複数のGPUにVRAMをどう割り振るかを設定します。
110GBのモデルを5枚のGPUに均等に割り振る設定ファイルを記述します。

```python
# config.py
import os

# モデルのパス（事前にHuggingFaceからQ6_K版をダウンロードしておく）
MODEL_PATH = "/models/qwen2.5-122b-moe-q6_k.gguf"

# 各GPUへのVRAM割り当て設定（単位：MB）
# 各24GBのGPUに対し、少し余裕を持って22GBずつ割り当てる
GPU_LAYERS = 80 # 全レイヤーをGPUへ
SPLIT_MODE = "layer" # レイヤーごとにGPUを分割
TENSOR_SPLIT = [22, 22, 22, 22, 22] # 各GPUのメモリ配分比率

# 危険温度のしきい値
MAX_TEMP_THRESHOLD = 75
```

`TENSOR_SPLIT`を均等にするのは、特定のGPUだけが過熱するのを防ぐためです。
OSが使用するVRAMを考慮し、メインディスプレイを接続しているGPU 0番だけは割り当てを1〜2GB少なめに設定するのがコツです。

## Step 3: 動かしてみる

まずはシンプルなサーバーモードで起動し、全GPUが認識されているか確認します。
以下のコマンドで、HTTPサーバーとして立ち上げます。

```bash
./bin/llama-server \
  -m /models/qwen2.5-122b-moe-q6_k.gguf \
  -n 2048 \
  --ngl 80 \
  --sm layer \
  --ts 22,22,22,22,22 \
  --port 8080
```

### 期待される出力

```text
llm_load_tensors: ggml ctx size =    0.15 MiB
llm_load_tensors: using CUDA for GPU multi
llm_load_tensors: [CUDA] total VRAM = 122880 MiB
llm_load_tensors: offloading 80 layers to GPU
```

この時点で `nvidia-smi` を別ターミナルで実行し、すべてのGPUのVRAM使用率が90%前後で並んでいることを確認してください。
もし一枚だけ使用率が低い場合、`--ts`（tensor split）の設定が正しく反映されていません。

## Step 4: 実用レベルにする（自動冷却制御付き推論）

ここからが本番です。
Pythonの `pynvml` ライブラリを使用して、GPU温度を監視しながら推論リクエストを制御するラッパーを作成します。
これにより、Redditの投稿者のように「冷やし続けなければならない」状況でも、安全に運用できます。

```python
import time
import requests
from pynvml import *

def get_max_gpu_temp():
    nvmlInit()
    device_count = nvmlDeviceGetCount()
    temps = []
    for i in range(device_count):
        handle = nvmlDeviceGetHandleByIndex(i)
        temp = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
        temps.append(temp)
    return max(temps)

def safe_inference(prompt):
    # 推論前に温度チェック
    while True:
        max_temp = get_max_gpu_temp()
        print(f"Current Max GPU Temp: {max_temp}°C")

        if max_temp < 75:
            break

        print("Warning: GPU temperature too high. Cooling down for 10 seconds...")
        time.sleep(10)

    # llama-serverのAPIへリクエスト
    response = requests.post(
        "http://localhost:8080/completion",
        json={"prompt": prompt, "n_predict": 512}
    )
    return response.json()["content"]

# 実行例
if __name__ == "__main__":
    test_prompt = "量子コンピュータの仕組みを詳しく解説してください。"
    result = safe_inference(test_prompt)
    print(result)
```

このスクリプトは、推論を開始する前に全GPUの温度をスキャンします。
最高温度が75度を超えている場合、10秒間のクールダウンタイムを設けます。
Redditのような物理的な水冷環境がない場合でも、この「ソフトウェア・スロットリング」により、ハードウェアへのダメージを劇的に抑えられます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| CUDA error: out of memory | KVキャッシュの確保失敗 | `--ctx-size` を小さくするか、`--ts` の値を微調整して余白を作る |
| 推論中にPCが落ちる | 電源ユニットの容量不足 | GPU 1枚あたりの消費電力を `nvidia-smi -pl` で制限する |
| 動作が異常に遅い (0.1 tok/s) | 一部のレイヤーがCPUに漏れている | `--ngl`（GPUレイヤー数）をモデルの全数に合わせて増やす |

## 次のステップ

この記事の環境が構築できれば、100Bクラスのモデルを「自分専用の知能」として実戦投入できます。
次に試すべきは、この推論サーバーをバックエンドにした RAG（検索拡張生成）システムの構築です。
Qwen2.5-122Bのような巨大モデルはコンテキストの理解力が非常に高いため、数万ページのドキュメントから情報を抽出する際、GPT-4oに匹敵する精度を発揮します。

また、物理的な冷却に興味が出たなら、Redditのように水道水を直接流すのはリスクが高いですが、業務用サーバーケース（4Uサイズ）に大口径ファンを並べる「高密度空冷」へのアップグレードを検討してください。
ローカルLLMの運用は、最終的に「いかに熱を逃がすか」という物理学の戦いになります。

## よくある質問

### Q1: RTX 4090を2枚しか持っていませんが、122Bモデルは動かせませんか？

IQ2_Mなどの低ビット量子化（2bit相当）なら動く可能性はありますが、知能が著しく低下します。基本的にはモデルを小さくするか（Qwen2.5-72Bなど）、メモリを増設するのが実務上の正解です。

### Q2: なぜOllamaではなくllama.cppを直接使うのですか？

Ollamaも中身はllama.cppですが、マルチGPUの細かいVRAM割り当て（--ts）や、最新のMoEモデルへの最適化フラグを直接制御するには、llama.cppの方が自由度が高く、熱管理もしやすいためです。

### Q3: 水道水での冷却は本当に効果がありますか？

Redditの報告にある通り、水は空気よりも熱容量が圧倒的に大きいため、冷却効率は最強です。ただし、結露によるショートのリスクがあるため、実務では本格水冷キット（DIY水冷）を組み、ラジエーターで冷やすのが一般的です。

---

## あわせて読みたい

- [Qwen3.5-35BをVRAM 16GBで爆速動作させるローカルLLM構築術](/posts/2026-02-27-qwen35-35b-local-setup-16gb-vram/)
- [Qwen2.5-Coder 使い方 | ローカルでGPT-4o級の開発環境をPythonで構築する](/posts/2026-03-21-qwen2-5-coder-python-local-guide/)
- [Qwen2.5 32B 使い方 入門：ローカル環境で爆速RAGシステムを構築する方法](/posts/2026-04-13-local-rag-qwen2-5-32b-ollama-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 4090を2枚しか持っていませんが、122Bモデルは動かせませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "IQ2Mなどの低ビット量子化（2bit相当）なら動く可能性はありますが、知能が著しく低下します。基本的にはモデルを小さくするか（Qwen2.5-72Bなど）、メモリを増設するのが実務上の正解です。"
      }
    },
    {
      "@type": "Question",
      "name": "なぜOllamaではなくllama.cppを直接使うのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaも中身はllama.cppですが、マルチGPUの細かいVRAM割り当て（--ts）や、最新のMoEモデルへの最適化フラグを直接制御するには、llama.cppの方が自由度が高く、熱管理もしやすいためです。"
      }
    },
    {
      "@type": "Question",
      "name": "水道水での冷却は本当に効果がありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Redditの報告にある通り、水は空気よりも熱容量が圧倒的に大きいため、冷却効率は最強です。ただし、結露によるショートのリスクがあるため、実務では本格水冷キット（DIY水冷）を組み、ラジエーターで冷やすのが一般的です。 ---"
      }
    }
  ]
}
</script>
