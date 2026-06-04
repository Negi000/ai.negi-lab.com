---
title: "Nvidiaのマーケティングに惑わされない！LLMの推論性能を実測・可視化する計測ツール自作ガイド"
date: 2026-06-05T00:00:00+09:00
slug: "local-llm-inference-benchmark-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "LLM ベンチマーク 測り方"
  - "Llama-3 推論速度"
  - "Python GPU プロファイリング"
  - "bitsandbytes 使い方"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 手元のGPU環境でLLMが「1秒間に何トークン生成できるか（tokens/sec）」を厳密に計測し、グラフ化するPythonスクリプト
- LinkedInなどで拡散される「Nvidia最高！」という宣伝文句ではなく、実測値に基づいた投資判断基準
- 必要なもの：Nvidia製GPU（VRAM 8GB以上）、Python環境（3.10以上）、Hugging Faceのアカウント

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama-3クラスを余裕を持って回せるコスパ最強の入門GPU</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのはGPUの「VRAM（ビデオメモリ）容量」です。
Redditで話題になっているNvidiaのプロモーションでは「AIが速くなる」と謳われますが、VRAMが足りなければそもそもモデルが動きません。
最低でもRTX 3060（12GBモデル）かRTX 4060 Ti（16GBモデル）が必要です。
8GBのカードでも4bit量子化を使えば7Bクラスのモデルは動きますが、将来性を考えると12GB以上が最低ラインだと私は考えています。
もしGPUを持っていないなら、まずはGoogle Colabの無料枠（T4 GPU）で試すのが賢明ですが、本気で実務に使うならRTX 4090（24GB）の一択です。
私の環境ではRTX 4090を2枚挿ししていますが、1枚でもLlama-3-8Bを高速に回すには十分すぎる性能を発揮します。

## なぜこの方法を選ぶのか

既存のベンチマークソフトは多機能すぎて、「結局自分の用途で何秒かかるのか」が見えにくいという欠点があります。
また、SNS上の「爆速」という言葉は、多くの場合、非常に短いプロンプトや特定の最適化設定での数字を切り取ったものです。
今回、自分でスクリプトを書いて計測するアプローチを採るのは、入力文字数や生成トークン数による「速度の減衰」を正確に把握するためです。
エンジニアとして「広告費が乗った他人の数字」を信じるのではなく、「自分の環境で、自分のプロンプトを投げた時の結果」を正義とする姿勢が、AIの実務導入には不可欠だと思います。

## Step 1: 環境を整える

まずは計測に必要なライブラリをインストールします。
ここではPyTorchと、Hugging FaceのTransformers、そしてメモリ計測用のツールを使います。

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers accelerate bitsandbytes matplotlib pandas
```

`transformers`はLLMを動かす標準ライブラリ、`accelerate`はモデルのメモリ配置を最適化するために使います。
`bitsandbytes`は、モデルを4bitや8bitに圧縮（量子化）して、少ないVRAMで動かすために必須のライブラリです。
`matplotlib`と`pandas`は、計測結果を後でグラフにして「見える化」するために導入しています。

⚠️ **落とし穴:**
Windows環境の場合、Pythonのインストール時に「Add Python to PATH」にチェックを入れていないと、コマンドが通りません。
また、Nvidiaのドライバーが最新でないと、最新のCUDAツールキットと競合してエラーを吐くことがよくあります。
計測前に必ずGeForce Experienceなどでドライバーを最新に更新しておいてください。

## Step 2: 基本の設定

計測用のベースとなるPythonスクリプトを作成します。
ここでは、環境変数などの面倒な設定を避けつつ、安全にモデルを読み込む構成にします。

```python
import os
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# モデル名の設定。今回は軽量で高性能なLlama-3-8Bを使用
model_id = "meta-llama/Meta-Llama-3-8B-Instruct"

# 4bit量子化の設定。VRAM消費を抑えつつ速度を出すための「実務で最も使う設定」です。
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

# トークナイザーとモデルの読み込み
# device_map="auto"にすることで、最適なVRAM配置を自動で行ってくれます。
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True
)

# 推論を高速化するための設定。
model.eval()
```

ここで`load_in_4bit=True`にしている理由は、多くのユーザーが12GB〜16GBのVRAMで運用することを想定しているからです。
FP16（量子化なし）で動かすと8BモデルでもVRAMを約15GB消費しますが、4bitなら約5.5GBまで抑えられます。
実務において「速度と精度のバランス」が最も取れているのがこの4bit NF4形式だと私は判断しています。

## Step 3: 動かしてみる

次に、実際にテキストを生成させて、その「生成開始までの時間」と「生成中の速度」を計測する関数を実装します。

```python
def measure_performance(prompt, max_new_tokens=100):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # 最初の1回はGPUのウォームアップとして計測から除外します
    # これをやらないと、初回のライブラリ読み込み速度が混じって正確な数字が出ません
    _ = model.generate(**inputs, max_new_tokens=1)

    # 本番の計測
    torch.cuda.synchronize() # GPUの処理が終わるのを待機
    start_time = time.time()

    with torch.no_grad():
        output_tokens = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7
        )

    torch.cuda.synchronize()
    end_time = time.time()

    # 生成されたトークン数を算出（入力分を差し引く）
    new_tokens = output_tokens[0][len(inputs["input_ids"][0]):]
    num_tokens = len(new_tokens)
    total_time = end_time - start_time

    tokens_per_sec = num_tokens / total_time

    return tokens_per_sec, total_time, num_tokens

# テスト実行
prompt = "Explain the importance of local LLMs in three sentences."
tps, duration, count = measure_performance(prompt)

print(f"計測結果: {tps:.2f} tokens/sec")
print(f"生成時間: {duration:.2f} 秒")
print(f"生成トークン数: {count}")
```

### 期待される出力

```
計測結果: 45.21 tokens/sec
生成時間: 2.21 秒
生成トークン数: 100
```

RTX 4090であれば、Llama-3-8B (4bit) で50〜60 tokens/sec程度、RTX 3060であれば20〜30 tokens/sec程度が出るはずです。
人間が読む速度はだいたい5〜10 tokens/secと言われているので、20を超えていれば実用上は「爆速」と感じるレベルです。

## Step 4: 実用レベルにする

単発の計測では、たまたまその時にOSが裏で動いていた等のノイズが含まれます。
実務で使えるデータにするために、複数の異なるプロンプト長で計測を行い、その結果をグラフ化する「ベンチマークスイート」に拡張しましょう。

```python
import matplotlib.pyplot as plt
import pandas as pd

def run_benchmark():
    prompts = [
        "Short prompt: Hello!",
        "Medium prompt: " + "What is AI? " * 20,
        "Long prompt: " + "Tell me a long story. " * 50
    ]

    results = []

    for i, p in enumerate(prompts):
        print(f"Running test {i+1}/3...")
        tps, duration, count = measure_performance(p, max_new_tokens=256)
        results.append({
            "Prompt Type": ["Short", "Medium", "Long"][i],
            "Tokens/Sec": tps,
            "Total Time": duration
        })

    df = pd.DataFrame(results)

    # グラフの描画
    plt.figure(figsize=(10, 6))
    plt.bar(df["Prompt Type"], df["Tokens/Sec"], color='skyblue')
    plt.title("LLM Inference Speed Benchmark (Llama-3-8B)")
    plt.ylabel("Tokens per Second")
    plt.xlabel("Prompt Length")
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # 結果の保存
    plt.savefig("benchmark_results.png")
    df.to_csv("benchmark_data.csv", index=False)
    print("計測完了。benchmark_results.png を確認してください。")

if __name__ == "__main__":
    run_benchmark()
```

このスクリプトを動かすことで、入力プロンプトが長くなった時に「どれだけ生成速度が落ちるか」が可視化されます。
Nvidiaの広告にある「〇〇倍高速」という数字は、往々にしてShort promptでの数値であることが多いため、MediumやLongでの落ち幅を見るのがエンジニアの視点です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Out of Memory (OOM) | VRAM容量不足 | `max_new_tokens`を減らすか、モデルをより小さなもの（Phi-3など）に変更する |
| `bitsandbytes` エラー | Windows環境特有のDLL読み込み失敗 | `pip install bitsandbytes-windows` を試すか、WSL2環境へ移行する |
| 推論速度が異常に遅い (1-2 tps) | GPUではなくCPUで動いている | `model.to("cuda")` が正しく実行されているか確認。PyTorchのCUDA版が入っていない可能性大 |

## 次のステップ

この記事で、あなたは「自分の手元の環境での真実」を数値化する手段を手に入れました。
次にやるべきことは、このスクリプトを使って「量子化による速度変化」の計測です。
`bnb_4bit_compute_dtype`を`torch.float16`に変えたり、量子化なしのFP16と比較してみてください。
驚くことに、量子化によってデータ量が減ると、計算負荷は上がるはずなのに、メモリ帯域のボトルネックが解消されて「速度が上がる」現象を目の当たりにするでしょう。

また、Redditの投稿で指摘されていたようなSNS上の「サクラ」と思われる投稿を見かけたら、そのモデル名と設定をこのスクリプトに放り込んでみてください。
広告通りの数字が出ない時、そこには必ず「プロンプトが極端に短い」か「特別な専用ハードウェアを使っている」というカラクリがあります。
常にコードと実測値をベースに判断する癖をつけることが、AI戦国時代を生き残るエンジニアの必須スキルです。

## よくある質問

### Q1: RTX 4060（VRAM 8GB）でもこのスクリプトは動きますか？

動きます。ただし、Llama-3-8Bを動かすとVRAMがギリギリになるため、ブラウザや他のソフトを落としてから実行してください。
もしメモリ不足になる場合は、モデルを`microsoft/Phi-3-mini-4k-instruct`に変えるのがおすすめです。

### Q2: なぜ計測の前に「ウォームアップ」が必要なのですか？

GPUは初回の計算時にカーネルのコンパイルやメモリの確保を行うため、どうしても時間がかかります。
これを計測に含めてしまうと、純粋な生成速度（tokens/sec）が低く出てしまい、実際の使用感とはかけ離れた数字になるからです。

### Q3: Mac（Apple Silicon）で同じことをするにはどうすればいいですか？

Macの場合はCUDAが使えないため、`device_map="auto"`の代わりに`device="mps"`を指定し、PyTorchのMPS（Metal Performance Shaders）対応版を使う必要があります。
ただし、今回のスクリプトで使っている`bitsandbytes`はNvidia GPU専用なので、Macでは`MLX`ライブラリを使った別の実装にするのがベストです。
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 4060（VRAM 8GB）でもこのスクリプトは動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きます。ただし、Llama-3-8Bを動かすとVRAMがギリギリになるため、ブラウザや他のソフトを落としてから実行してください。 もしメモリ不足になる場合は、モデルをmicrosoft/Phi-3-mini-4k-instructに変えるのがおすすめです。"
      }
    },
    {
      "@type": "Question",
      "name": "なぜ計測の前に「ウォームアップ」が必要なのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "GPUは初回の計算時にカーネルのコンパイルやメモリの確保を行うため、どうしても時間がかかります。 これを計測に含めてしまうと、純粋な生成速度（tokens/sec）が低く出てしまい、実際の使用感とはかけ離れた数字になるからです。"
      }
    },
    {
      "@type": "Question",
      "name": "Mac（Apple Silicon）で同じことをするにはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Macの場合はCUDAが使えないため、devicemap=\"auto\"の代わりにdevice=\"mps\"を指定し、PyTorchのMPS（Metal Performance Shaders）対応版を使う必要があります。 ただし、今回のスクリプトで使っているbitsandbytesはNvidia GPU専用なので、MacではMLXライブラリを使った別の実装にするのがベストです。"
      }
    }
  ]
}
</script>
