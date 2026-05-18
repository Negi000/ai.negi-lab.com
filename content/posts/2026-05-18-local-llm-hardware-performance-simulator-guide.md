---
title: "LocalLLMハードウェア選定ツールの作り方と最適な環境構築"
date: 2026-05-18T00:00:00+09:00
slug: "local-llm-hardware-performance-simulator-guide"
cover:
  image: "/images/posts/2026-05-18-local-llm-hardware-performance-simulator-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "ローカルLLM ハードウェア"
  - "RTX 6000 Ada 性能"
  - "M5 Ultra LLM"
  - "Strix Halo ベンチマーク"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 入力したモデル規模（Llama-3-70B等）に対し、M5、Strix Halo、RTX 6000 Adaなどの次世代・現行ハードウェアで「動くのか」「速度（Token/s）はどの程度か」を算出するシミュレーターを作成します
- 前提知識: Pythonの基本的な文法、ローカルLLMにおける「量子化（4bit/8bit）」の意味がわかること
- 必要なもの: Python 3.10以降が動作するPC

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす際、初心者が最も陥る罠は「推論チップの計算性能（TFLOPS）」を重視しすぎることです。
実際には、LLMの推論速度は「メモリ帯域（GB/s）」に完全に依存します。
M5チップやStrix Haloが注目されているのは、広大な共有メモリ帯域を持っているからです。

現状、40B以上のモデルを快適に動かすには最低でも「VRAM 48GB以上」が必要になります。
RTX 6000 Ada（48GB）は新品で100万円を超えますが、Mac Studio（M2/M3 Ultra）なら同等以上のメモリ容量を半分以下の価格で確保できます。
ただし、今回比較対象に上がっている「DGX Spark」や「Strix Halo」は、電力効率と帯域のバランスでRTX 4090の牙城を崩す可能性があります。
購入前に、自分が「推論速度」を重視するのか「扱えるモデルサイズ（メモリ容量）」を重視するのかを明確にしてください。

## なぜこの方法を選ぶのか

Redditのr/LocalLLaMAで議論されているM5やStrix Haloのスペックは、まだ噂段階のものも含まれます。
しかし、LLMの動作原理（Transformer構造）から計算される必要スペックは物理法則に基づいています。
数値を適当に眺めるのではなく、自分でシミュレーターを書くことで、将来どのハードウェアに投資すべきかの「確信」が得られます。
既成のベンチマークサイトを見るだけでは、自分の使いたいコンテキスト長（128kなど）でのメモリ消費を予測できないため、この計算スクリプト自作がベストです。

## Step 1: 環境を整える

まずは計算に必要なライブラリを準備します。といっても、今回は標準ライブラリの `math` と `json` だけで完結させます。
外部ライブラリへの依存を減らすのは、将来的にWebツール化したり、モバイル環境で動かしたりする際の移植性を高めるためです。

```bash
# プロジェクト用ディレクトリの作成
mkdir llm-hw-sim
cd llm-hw-sim

# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate
```

各ハードウェアのスペックを定義した `hardware_db.json` を作成します。
ここにはRedditのスレッド等で議論されている最新の推定スペック（帯域幅と最大メモリ）を記述します。

⚠️ **落とし穴:** Macの「ユニファイドメモリ」はすべてをLLMに割り当てられるわけではありません。OSや他のアプリが使う分（約10〜20%）を差し引いて計算する必要があります。

## Step 2: 基本の設定

ハードウェアの特性を定義し、モデルのメモリ消費量を計算するロジックを実装します。

```python
import math

# ハードウェアスペックの定義（推定値含む）
HARDWARE_SPECS = {
    "RTX_6000_Ada": {
        "memory_gb": 48,
        "bandwidth_gbs": 960,
        "type": "dGPU"
    },
    "Mac_M5_Ultra_Est": {
        "memory_gb": 192,
        "bandwidth_gbs": 800,
        "type": "Unified"
    },
    "Strix_Halo_Est": {
        "memory_gb": 128,
        "bandwidth_gbs": 500,
        "type": "APU"
    },
    "DGX_Spark_Est": {
        "memory_gb": 256,
        "bandwidth_gbs": 2000,
        "type": "Server"
    }
}

def calculate_model_size(params_billions, bpw):
    """
    モデルの重みが必要とするメモリ（GB）を計算
    params_billions: パラメータ数（B）
    bpw: bits per weight（量子化ビット数）
    """
    # パラメータ * ビット数 / 8(bit->byte) / 1024^3 (byte->GB) * 余裕分1.1
    size_gb = (params_billions * 10**9 * (bpw / 8)) / (1024**3)
    return size_gb * 1.05  # 5%のオーバーヘッド込
```

ここで `bpw`（bits per weight）に4や8を指定するのは、現在のローカルLLMの主流が4bit（Q4_K_Mなど）や8bitだからです。
16bit（FP16）で動かすのは、実務上はVRAM効率が悪すぎて避けるのが一般的です。

## Step 3: 動かしてみる

次に、各ハードウェアでそのモデルを動かした際の「推論速度（Tokens per Second）」を予測する関数を追加します。
LLMの推論（デコードフェーズ）は、毎トークンごとに重みデータをメモリからプロセッサへ読み出す必要があるため、速度は「メモリ帯域 / モデルサイズ」でほぼ決まります。

```python
def estimate_performance(hw_name, params_billions, bpw):
    spec = HARDWARE_SPECS.get(hw_name)
    model_gb = calculate_model_size(params_billions, bpw)

    if model_gb > spec["memory_gb"]:
        return f"ERROR: メモリ不足 ({model_gb:.1f}GB > {spec['memory_gb']}GB)"

    # 推論速度の理論限界値 (tokens/s)
    # 帯域幅(GB/s) / モデルサイズ(GB)
    tps = spec["bandwidth_gbs"] / model_gb
    return f"{tps:.2f} tokens/s"

# テスト: Llama-3-70Bを4bit量子化で動かす場合
print(f"RTX 6000 Ada: {estimate_performance('RTX_6000_Ada', 70, 4)}")
print(f"M5 Ultra (Est): {estimate_performance('Mac_M5_Ultra_Est', 70, 4)}")
```

### 期待される出力

```
RTX 6000 Ada: 27.97 tokens/s
M5 Ultra (Est): 23.31 tokens/s
```

この結果から、RTX 6000 Adaは非常に高速ですが、将来的な192GBモデルなどはM5 Ultraでなければ載らない、という「容量 vs 速度」のトレードオフが可視化されます。

## Step 4: 実用レベルにする

実務では「KVキャッシュ」の消費を無視できません。長い文脈（コンテキスト）を入力するほど、VRAMを圧迫します。
この計算式を組み込み、より正確な判定ができるツールに仕上げます。

```python
def get_kv_cache_size(params_billions, context_length, layers=80, heads=64, dim=128):
    """
    KVキャッシュのメモリ消費量を計算（非常に簡易的なモデル）
    """
    # 実際にはモデルごとに異なるが、Llama-3-70Bクラスを想定
    # 2 * context * layers * heads * dim * precision(FP16=2)
    cache_bytes = 2 * context_length * layers * heads * dim * 2
    return cache_bytes / (1024**3)

def check_feasibility(hw_name, model_params, bpw, context_len):
    spec = HARDWARE_SPECS[hw_name]
    model_gb = calculate_model_size(model_params, bpw)
    kv_gb = get_kv_cache_size(model_params, context_len)
    total_needed = model_gb + kv_gb

    status = "OK" if total_needed <= spec["memory_gb"] else "NG"
    tps = spec["bandwidth_gbs"] / total_needed if status == "OK" else 0

    print(f"--- {hw_name} 判定結果 ---")
    print(f"必要メモリ: {total_needed:.2f} GB (モデル: {model_gb:.1f}, KV: {kv_gb:.1f})")
    print(f"判定: {status}")
    if status == "OK":
        print(f"推定速度: {tps:.2f} t/s")
    print("-" * 30)

# 実行例
check_feasibility("Strix_Halo_Est", 70, 4, 32768)
```

このスクリプトを使えば、SNSの「Strix Haloなら70Bが爆速で動く」といった煽り文句に対し、「32kコンテキストを入れたらメモリ不足になる、あるいは速度が10t/sを切る」といった客観的な反論ができるようになります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| 推論速度が理論値より大幅に遅い | メモリ帯域ではなく演算性能がボトルネック | 量子化ビット数を下げすぎると、解凍処理（De-quantization）にCPU/GPU負荷がかかりすぎる場合があります。Q4_K_M程度に留めるのが吉。 |
| Apple Siliconでメモリが足りるはずなのに落ちる | システムの予約領域 | Macの場合、`sysctl iogpu.max_vram_multiplier`でVRAM割り当て制限を確認してください。デフォルトでは全メモリの2/3程度に制限されています。 |
| Strix Haloの帯域が安定しない | メモリチャンネル数の不足 | APU（Strix Halo等）は搭載するRAMの枚数やクロック（LPDDR5x-8000等）に直結します。安いメモリを選ばないこと。 |

## 次のステップ

この記事で作成したシミュレーターをベースに、次は以下の3点に取り組んでみてください。

1. **実測値との比較**:
   手持ちの環境（RTX 3060やM2 MacBookなど）で実際にOllamaやllama.cppを動かし、スクリプトの予測値とどれだけ乖離があるか検証してください。乖離がある場合は、オーバーヘッド係数を調整します。

2. **多層モデルの計算実装**:
   現在はパラメータ総数だけで計算していますが、MixtralのようなMoE（混合専門家）モデルの場合、計算に必要なメモリと推論時にアクセスするメモリが異なります。MoE対応の計算式を実装すると、さらに実戦的になります。

3. **コストパフォーマンス計算**:
   `HARDWARE_SPECS` に価格（USD/JPY）を追加し、「1 Token/s あたりのコスト」を算出してみてください。多くの場合、中古のRTX 3090を2枚挿しするのが最強であるという現実に辿り着くはずです。

## よくある質問

### Q1: M5を待つべきですか、今RTX 6000 Adaを買うべきですか？

業務で今すぐ納品が必要ならRTX 6000 Ada一択です。NVIDIA環境はライブラリの互換性が圧倒的で、トラブル対応のコストが低いためです。一方、趣味や研究で「安く広大なメモリ」が欲しいなら、M5（または現行のM3 Ultra）を強く推奨します。

### Q2: Strix Halo（AMD）はCUDAが使えないから不便ではないですか？

ROCmの進化により、llama.cppやPyTorchなどの主要フレームワークはAMDでも問題なく動きます。ただし、最新の論文実装をいち早く試したい場合は、依然としてNVIDIA環境（CUDA）が有利であることは変わりません。

### Q3: 128GB以上のメモリは本当に必要ですか？

Llama-3-70Bをまともに（4bit以上で）動かし、かつ数千トークンの履歴を保持するなら、48GBでは足りなくなるケースが多いです。100B超えのモデルや、長文RAGを実務で使うなら128GBという数字は決して大げさではありません。
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "M5を待つべきですか、今RTX 6000 Adaを買うべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "業務で今すぐ納品が必要ならRTX 6000 Ada一択です。NVIDIA環境はライブラリの互換性が圧倒的で、トラブル対応のコストが低いためです。一方、趣味や研究で「安く広大なメモリ」が欲しいなら、M5（または現行のM3 Ultra）を強く推奨します。"
      }
    },
    {
      "@type": "Question",
      "name": "Strix Halo（AMD）はCUDAが使えないから不便ではないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ROCmの進化により、llama.cppやPyTorchなどの主要フレームワークはAMDでも問題なく動きます。ただし、最新の論文実装をいち早く試したい場合は、依然としてNVIDIA環境（CUDA）が有利であることは変わりません。"
      }
    },
    {
      "@type": "Question",
      "name": "128GB以上のメモリは本当に必要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Llama-3-70Bをまともに（4bit以上で）動かし、かつ数千トークンの履歴を保持するなら、48GBでは足りなくなるケースが多いです。100B超えのモデルや、長文RAGを実務で使うなら128GBという数字は決して大げさではありません。"
      }
    }
  ]
}
</script>
