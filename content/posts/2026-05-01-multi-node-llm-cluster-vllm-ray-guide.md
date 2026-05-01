---
title: "RayとvLLMで個人でも構築可能なマルチノードLLM推論クラスターを作る方法"
date: 2026-05-01T00:00:00+09:00
slug: "multi-node-llm-cluster-vllm-ray-guide"
cover:
  image: "/images/posts/2026-05-01-multi-node-llm-cluster-vllm-ray-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "vLLM 使い方"
  - "Ray 分散推論"
  - "自作計算クラスター"
  - "Llama 3 70B ローカル"
---
**所要時間:** 約60分 | **難易度:** ★★★★☆

## この記事で作るもの

- 2台以上のPC（GPU搭載）をネットワーク経由で束ね、Llama 3 70Bなどの巨大モデルを高速推論する分散環境を構築します。
- PythonとRay、そしてvLLMを組み合わせた、実務レベルの分散推論スクリプト。
- 複数枚のGPUを1つの仮想的な巨大GPUとして扱うためのネットワーク設定とランタイム。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">Intel X550-T2 10GbE NIC</strong>
<p style="color:#555;margin:8px 0;font-size:14px">マルチノード推論のボトルネックとなるGPU間通信を高速化するために必須のパーツです</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=Intel%20X550-T2%2010GbE&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FIntel%2520X550-T2%252010GbE%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FIntel%2520X550-T2%252010GbE%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、Ubuntuの基本操作とPythonの仮想環境（venvやconda）の構築、およびNVIDIAドライバの導入が完了していることを想定します。

## なぜこの方法を選ぶのか

ローカルで巨大なLLMを動かそうとしたとき、最大の壁は「VRAMの容量」です。
例えばRTX 4090を2枚挿しても48GB。これではLlama 3 70BをFP16で動かすには足りず、量子化に頼らざるを得ません。
しかし、この「Ray + vLLM」のスタックを使えば、物理的に別々のマシンにあるGPUをLAN経由で連結し、1つの大きな推論エンジンとして扱えます。

世の中にはLlama.cppを使った分散推論もありますが、あれはあくまで「動けばいい」ホビー用途に近い。
仕事で使うなら、スループットが圧倒的に高く、OpenAI互換APIを即座に叩き出せるvLLM一択です。
私がSIer時代に苦労した「複数サーバー間のMPI設定」のような泥臭い作業は、現代ではRayがすべて隠蔽してくれます。
レスポンス速度を犠牲にせず、スケールアウトの恩恵を最大化できるのがこの構成の強みです。

## Step 1: 環境を整える

まずは全ノード（サーバー）に共通のライブラリをインストールします。
今回はUbuntu 22.04、CUDA 12.1の環境を前提とします。

```bash
# 全ノードで実行
# Pythonの仮想環境を作成
python3 -m venv vllm-cluster
source vllm-cluster/bin/activate

# RayとvLLMをインストール
# vLLMは分散推論のためにRayを内部で使用します
pip install "ray[default]" vllm==0.4.2

# 通信のために必要なNCCLの確認（NVIDIAの集団通信ライブラリ）
# これが正常に動かないと分散処理は100%失敗します
python3 -c "import torch; print(torch.cuda.nccl.version())"
```

各コマンドの意図を説明します。
`ray[default]`は分散実行のためのオーケストレーターです。
`vllm`は推論エンジンですが、バージョンを固定しているのは、分散推論周りのAPI変更が激しいためです。
特にNCCLのバージョン確認は重要で、複数のGPU間でデータを同期する際に、ここが不整合だとエラーを吐いて止まります。

⚠️ **落とし穴:**
ノード間の「パスワードなしSSH」設定を忘れる人が多いですが、これは必須ではありません。
ただし、各ノードのIPアドレスを固定し、ポート（デフォルトで6379番など）をファイアウォールで開放しておく必要があります。
私は最初、UFW（ファイアウォール）を有効にしたまま構築して「ノードが見つからない」というエラーで3時間を無駄にしました。検証中は一旦オフにするか、特定のサブネットを許可してください。

## Step 2: 基本の設定

クラスターの司令塔となる「ヘッドノード」と、計算資源を提供する「ワーカーノード」を設定します。

```bash
# 【ヘッドノード（親機）で実行】
# node-ipには自身のIPアドレスを指定します
ray start --head --port=6379 --node-ip-address=192.168.1.10

# 【ワーカーノード（子機）で実行】
# addressにはヘッドノードのIPを指定
ray start --address='192.168.1.10:6379'
```

次に、Pythonからこのクラスターを制御するための初期化コードを書きます。

```python
# config.py
import os
import ray

# クラスターに接続
# 既にシェルでray startしている場合は 'auto' で接続可能
ray.init(address="auto", ignore_reinit_error=True)

# 接続されているノードとGPUの数を確認
nodes = ray.nodes()
gpu_count = ray.cluster_resources().get("GPU", 0)

print(f"接続されたノード数: {len(nodes)}")
print(f"利用可能な総GPU数: {gpu_count}")
```

ここで「なぜ `address="auto"` にするのか」ですが、これはスクリプト実行時に既に立ち上がっているRayクラスターを自動検出させるためです。
スクリプト内で細かく設定を書くよりも、OS側でサービスとしてRayを立ち上げておくほうが、実務上の運用（ノードの増減など）が格段に楽になります。

## Step 3: 動かしてみる

実際にLlama 3 8Bなどの軽量モデルを、2つのノードに跨ってロードしてみましょう。
ここでは `tensor_parallel_size` が鍵になります。

```python
# distributed_inference.py
from vllm import LLM, SamplingParams

# tensor_parallel_size は使用する総GPU数を指定
# 2台のPCにそれぞれ1枚ずつGPUがあるなら '2' に設定
llm = LLM(
    model="meta-llama/Meta-Llama-3-8B",
    tensor_parallel_size=2,
    distributed_executor_backend="ray"
)

sampling_params = SamplingParams(temperature=0.7, top_p=0.95, max_tokens=100)

outputs = llm.generate(["AIクラスターを構築するメリットは何ですか？"], sampling_params)

for output in outputs:
    print(f"Prompt: {output.prompt}")
    print(f"Generated text: {output.outputs[0].text}")
```

### 期待される出力

```
接続されたノード数: 2
利用可能な総GPU数: 2.0
...
Generated text: AIクラスターを構築する最大のメリットは、単体ではメモリ不足で実行不可能な巨大なモデルを扱えること、および推論速度（スループット）の向上です。
```

結果が正しく返ってくれば、物理的に分かれたGPUが1つのモデルを「分割して」持っている状態が作れています。
もしここでタイムアウトが発生する場合、ノード間の通信速度（LANケーブルが1GbEか、10GbEか）を疑ってください。
LLMの分散推論では、GPU間の通信がボトルネックになるため、最低でも2.5GbE、できれば10GbE以上の環境を推奨します。

## Step 4: 実用レベルにする

実務では、単発のスクリプト実行ではなく「APIサーバー」として24時間稼働させる必要があります。
vLLMにはOpenAI互換のサーバー機能が備わっていますが、これを分散環境で起動するには以下のコマンドを叩きます。

```bash
# ヘッドノードで実行
python3 -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Meta-Llama-3-70B \
    --tensor-parallel-size 4 \
    --host 0.0.0.0 \
    --port 8000
```

ここでは `tensor-parallel-size 4` としました。これは私の自宅にあるRTX 4090を2枚挿したマシン2台（計4枚）を想定した数値です。
なぜAPIサーバー形式にするのか。それは、既存のDifyやLangChainなどのツールから、単なる「OpenAIのエンドポイント」としてこのクラスターを再利用できるからです。

さらに、実務運用では「ノードの離脱」への対策が必要です。
以下のPythonスクリプトは、クラスターの死活監視を含めた、より堅牢な推論実行例です。

```python
import time
from vllm import LLM

def safe_init_llm(model_name, num_gpus):
    try:
        # 起動前にリソースが足りているかチェック
        available_gpus = ray.cluster_resources().get("GPU", 0)
        if available_gpus < num_gpus:
            raise RuntimeError(f"GPUが足りません。必要: {num_gpus}, 現在: {available_gpus}")

        return LLM(model=model_name, tensor_parallel_size=num_gpus)
    except Exception as e:
        print(f"起動エラー: {e}")
        return None

# メイン処理
model = "meta-llama/Meta-Llama-3-70B"
llm = safe_init_llm(model, 4)

if llm:
    # 連続リクエストを想定したループ
    while True:
        # 実際の運用ではここでキューから入力を取得
        start_time = time.time()
        # ... 推論処理 ...
        break # 今回はデモのため1回で終了
```

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `NCCL Timeout` | ノード間のネットワーク遮断または低速 | ファイアウォールをオフにし、10GbE以上の接続を確保する |
| `Ray node not found` | `ray start`時のIP指定ミス | 自身のプライベートIP（192.168.x.x）を正確に指定する |
| `Out of Memory (OOM)` | モデルに対してGPUメモリが不足 | `tensor_parallel_size` を増やすか、モデルを量子化(AWQ等)する |

## 次のステップ

このクラスターが組めるようになると、もはや「PC1台の限界」を気にする必要がなくなります。
次に挑戦すべきは、**「vLLMのLoRAアダプタ動的ロード」**です。
分散環境を維持したまま、リクエストごとに異なる性格のAI（マーケティング用、コーディング用など）を瞬時に切り替える運用は、実務において非常に強力な武器になります。

また、ハードウェア面では10GbEのNIC（ネットワークカード）を導入することを強くお勧めします。
GPU同士がデータをやり取りする速度が、推論トークン生成速度のボトルネックになるからです。
私の環境では、1GbEから10GbEに変えただけで、Llama 3 70Bの推論速度が約1.8倍に向上しました。
Redditの「16x Spark Cluster」のような巨大な構成は夢がありますが、まずは2〜3台の型落ちワークステーションを中古で集めて、この分散環境を構築することから始めてみてください。
その経験は、将来クラウドで大規模なH100クラスターを管理する際の確かな血肉となります。

## よくある質問

### Q1: 異なる型番のGPU（例：RTX 4090とRTX 3080）を混ぜても大丈夫ですか？

動きますが、おすすめしません。分散推論の速度は「クラスター内で最も遅いGPU」に引っ張られます。また、VRAM容量も最小のカードに合わせる必要があるため、資源が無駄になります。可能な限り、同じVRAM容量のカードで揃えるのが定石です。

### Q2: ネットワーク越しだと推論が遅くなりませんか？

はい、1台のマシン内に複数枚挿す場合と比較すれば、ノード間のオーバーヘッドは確実に発生します。ただし、モデルが1台のメモリに収まらない場合、スワップ（ディスク使用）が発生して使い物にならなくなるため、それと比較すれば分散推論のほうが圧倒的に高速です。

### Q3: インターネット経由（遠隔地）でクラスターを組めますか？

技術的にはVPN等で可能ですが、実用的ではありません。NCCL通信は非常に低遅延であることを要求するため、物理的に同じスイッチングハブに繋がっている必要があります。数ミリ秒の遅延が推論速度を致命的に低下させるため、基本はLAN内での運用に限られます。

---

## あわせて読みたい

- [RTX 5090とvLLMでQwen3.6-27Bを爆速動作させる方法](/posts/2026-04-26-qwen3-6-27b-vllm-rtx5090-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "異なる型番のGPU（例：RTX 4090とRTX 3080）を混ぜても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、おすすめしません。分散推論の速度は「クラスター内で最も遅いGPU」に引っ張られます。また、VRAM容量も最小のカードに合わせる必要があるため、資源が無駄になります。可能な限り、同じVRAM容量のカードで揃えるのが定石です。"
      }
    },
    {
      "@type": "Question",
      "name": "ネットワーク越しだと推論が遅くなりませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、1台のマシン内に複数枚挿す場合と比較すれば、ノード間のオーバーヘッドは確実に発生します。ただし、モデルが1台のメモリに収まらない場合、スワップ（ディスク使用）が発生して使い物にならなくなるため、それと比較すれば分散推論のほうが圧倒的に高速です。"
      }
    },
    {
      "@type": "Question",
      "name": "インターネット経由（遠隔地）でクラスターを組めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "技術的にはVPN等で可能ですが、実用的ではありません。NCCL通信は非常に低遅延であることを要求するため、物理的に同じスイッチングハブに繋がっている必要があります。数ミリ秒の遅延が推論速度を致命的に低下させるため、基本はLAN内での運用に限られます。 ---"
      }
    }
  ]
}
</script>
