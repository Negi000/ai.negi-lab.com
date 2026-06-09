---
title: "llama-cpp-pythonで自分だけのLLM推論ベンチマークを計測する方法"
date: 2026-06-09T00:00:00+09:00
slug: "local-llm-benchmark-python-llama-cpp"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama-cpp-python 使い方"
  - "ローカルLLM ベンチマーク"
  - "推論速度 計測"
  - "GPU VRAM 不足 対処"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 自分のPC上でローカルLLMの推論速度（Tokens Per Second）と応答遅延（TTFT）を正確に計測するPythonスクリプト
- 特定のモデル（Llama 3やQwen 2など）が自分の業務で使い物になるかを「数字」で判断する基準
- 前提知識：Pythonの基本的な構文（変数、関数）がわかり、ターミナルでコマンド操作ができること
- 必要なもの：NVIDIA製GPU（VRAM 8GB以上推奨）またはApple Silicon搭載Mac、Python 3.10以降

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載で、7B/8Bモデルを余裕を持って動かせるローカルLLM入門の最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU性能は二の次です。最も重要なのはGPUの「VRAM（ビデオメモリ）容量」と「メモリ帯域幅」になります。

VRAMが8GBあれば、7B（70億パラメータ）クラスのモデルを4bit量子化（Q4_K_M）で動かせますが、コンテキスト長（入力文字数）を増やすとすぐに溢れます。実務でRAG（外部知識参照）などを行い、長い文章を読み込ませるなら最低でも12GB、できれば16GB以上のGPUを選んでください。

現在、コストパフォーマンスで選ぶならRTX 4060 Tiの16GB版が、仕事でストレスなく回すなら私が使っているRTX 4090（24GB）が鉄板です。Mac派なら、ユニファイドメモリの特性上、最低でも32GB以上のメモリを積んだモデルでないと、大規模なモデルを動かした際にスワップが発生して使い物になりません。

APIを利用する場合と違い、ローカル環境なら電気代以外のランニングコストはゼロです。一度環境を構築してしまえば、機密情報を外部に送ることなく、何万回でもテストを繰り返せます。

## なぜこの方法を選ぶのか

LM StudioやOllamaといった便利なツールは他にもありますが、私はあえて`llama-cpp-python`を直接叩く方法を推奨します。理由は「推論の裏側にある詳細なパラメータを1ミリ単位で制御できるから」です。

GUIツールは手軽ですが、バックグラウンドでどのような処理が行われているか不透明な部分があります。プロンプトの処理時間（Prompt Processing）とトークンの生成時間（Generation）を分けて計測しなければ、本当の意味での「仕事で使えるか」の判断は下せません。

また、自作スクリプトであれば、複数のモデルをループで回して一括でベンチマークを取る自動化も容易です。ネット上の「誰かが計測したベンチマーク結果」は、あなたのPC環境や入力する日本語の特性とは必ずしも一致しません。自分の手で、自分のデータを使って測ることにこそ価値があります。

## Step 1: 環境を整える

まずは、LLMを動かすためのコアとなるライブラリをインストールします。ここではGPUを活用するために、ビルドオプションを明示してインストールするのが最大のポイントです。

```bash
# NVIDIA GPU (CUDA) を使う場合
export CMAKE_ARGS="-DGGML_CUDA=ON"
pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir

# Apple Silicon (Metal) を使う場合
export CMAKE_ARGS="-DGGML_METAL=ON"
pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir
```

`export CMAKE_ARGS`を指定せずにインストールすると、GPUがある環境でもCPU推論になってしまい、速度が1/10以下に落ち込みます。インストール後、Pythonを起動して`from llama_cpp import Llama`がエラーなく実行できるか確認してください。

⚠️ **落とし穴:** Windows環境でCUDAビルドに失敗する場合、多くはVisual StudioのC++ビルドツールが入っていないか、CUDA Toolkitのパスが通っていません。インストールの前に、コマンドプロンプトで`nvcc --version`と叩いて、CUDAが認識されているか必ず確認してください。

## Step 2: 基本の設定

次に、モデルを読み込み、推論の準備を行うコードを書きます。ここではHugging Faceからダウンロードした`.gguf`形式のモデルファイルを使用します。

```python
import time
import os
from llama_cpp import Llama

# モデルのパス（自分の環境に合わせて変更）
# 例: Meta-Llama-3-8B-Instruct-Q4_K_M.gguf
MODEL_PATH = "models/llama-3-8b-instruct.Q4_K_M.gguf"

# モデルの初期化
# n_gpu_layers: GPUにオフロードするレイヤー数。-1に設定すると全レイヤーをGPUに載せる
# n_ctx: コンテキストウィンドウのサイズ。業務利用なら最低でも4096、できれば8192
llm = Llama(
    model_path=MODEL_PATH,
    n_gpu_layers=-1,
    n_ctx=4096,
    verbose=False # ログがうるさいのでベンチマーク時はFalse
)
```

`n_gpu_layers=-1`は、VRAMが許す限りすべての計算をGPUに任せる設定です。もしVRAMが足りずにエラーが出る場合は、この値を徐々に下げていく（32, 16など）ことで、CPUとGPUのハイブリッド推論が可能になります。ただし、1レイヤーでもCPUに落ちると急激に遅くなるため、可能な限りGPUに収まる量子化サイズ（Q4やQ5）を選ぶのが実務上のセオリーです。

## Step 3: 動かしてみる

いよいよベンチマークを計測するメイン処理を書きます。単に結果を表示するだけでなく、「最初の1文字が出るまでの時間（TTFT）」と「その後の生成速度（TPS）」を分離して計測します。

```python
def run_benchmark(prompt):
    start_time = time.time()

    # 推論の実行
    # stream=Trueにすることで、生成されるトークンを逐次取得できる
    response = llm(
        prompt,
        max_tokens=512,
        stop=["<|eot_id|>"], # モデルに応じた停止トークン
        stream=True
    )

    first_token_time = None
    token_count = 0

    print(f"Prompt: {prompt}")
    print("Response: ", end="", flush=True)

    for chunk in response:
        if first_token_time is None:
            first_token_time = time.time()
            ttft = first_token_time - start_time

        content = chunk["choices"][0]["text"]
        if content:
            print(content, end="", flush=True)
            token_count += 1

    end_time = time.time()
    total_time = end_time - start_time
    tps = token_count / (end_time - first_token_time) if token_count > 0 else 0

    print(f"\n\n--- Benchmark Results ---")
    print(f"Time to First Token (TTFT): {ttft:.2f} sec")
    print(f"Tokens Per Second (TPS): {tps:.2f} tokens/sec")
    print(f"Total Time: {total_time:.2f} sec")
    print(f"Total Tokens: {token_count}")

# 実行
run_benchmark("ローカルLLMを業務で活用するメリットとリスクを、500文字程度で論理的に説明してください。")
```

### 期待される出力

```
Time to First Token (TTFT): 0.15 sec
Tokens Per Second (TPS): 45.20 tokens/sec
```

結果の読み方ですが、人間が読んでいて「速い」と感じるのはTPSが20以上です。30を超えるとスクロールが追いつかないほどになり、実用性は非常に高いと言えます。逆に10を切ると、待たされている感覚が強くなり、チャットボットとしての運用は厳しくなります。

## Step 4: 実用レベルにする

実務では、一つのプロンプトに対する速度だけでは不十分です。「長いプロンプトを入れた時にどれくらい遅くなるか」を知る必要があります。RAGなどの用途では、数千文字のコンテキストを流し込むため、プロンプトの処理（Prefill速度）がボトルネックになるからです。

以下のコードでは、入力サイズを変えながらパフォーマンスをループ計測します。

```python
import json

prompts = [
    "短文プロンプト: LLMとは何ですか？",
    "長文プロンプト: " + "これはテストです。" * 100 # 約1000トークン以上の入力を想定
]

results = []

for p in prompts:
    # 前述のrun_benchmarkと同様のロジックで計測
    # 計測結果を辞書形式で保存
    stats = {
        "prompt_length": len(p),
        "ttft": 0.15, # 実際には計測値を入れる
        "tps": 45.2
    }
    results.append(stats)

# 結果をJSONで保存（後の比較用）
with open("benchmark_results.json", "w") as f:
    json.dump(results, f, indent=4)
```

このようにデータを蓄積することで、新しいモデル（例えばLlama 3からLlama 4へ）が出た際に「自分のハードウェアでどれだけ性能が向上したか」を客観的に比較できるようになります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `AddressSpace/Memory Error` | VRAM不足 | `n_gpu_layers`を減らすか、より高い量子化（Q4_K_M → Q3_K_S）を選択する。 |
| `Unknown argument -DGGML_CUDA` | `llama-cpp-python`のバージョンが古い | `pip cache purge`をしてから最新版を再インストールする。 |
| `TPSが極端に低い (1~2)` | CPU推論になっている | インストール時の`CMAKE_ARGS`が正しく反映されているか確認。 |

## 次のステップ

ここまでで、あなたは「自分の環境におけるLLMの真の実力」を数値化できるようになりました。次に挑むべきは、このスクリプトを「モデルの選別」に使うことです。

現在、Hugging Faceには数万のモデルがアップロードされていますが、その多くは特定のベンチマークに特化しただけの「数字遊び」のモデルです。しかし、あなたが作ったこのスクリプトに、実際に業務で使う予定のプロンプトを流し込めば、どのモデルが最も「賢く、かつ速いのか」が分かります。

具体的には、`Quantization`（量子化）による精度の劣化と速度のトレードオフを検証してみてください。一般的にQ4（4ビット）がバランスが良いとされますが、日本語の複雑な文脈ではQ6以上が必要になるケースもあります。これを「体感」ではなく「自分のスクリプトによる数値」で語れるようになれば、AIエンジニアとしての信頼度は格段に上がります。

## よくある質問

### Q1: NVIDIAのGPUでなくても動きますか？

動きますが、速度は期待できません。AMD製GPUならROCm、MacならMetalを使用するようにビルドすれば高速化されますが、互換性と情報の多さではNVIDIA一択です。仕事で使うなら、ケチらずにGeForce RTXシリーズを買うことを強く勧めます。

### Q2: 量子化モデル（GGUF）はどこで手に入りますか？

Hugging Faceで「モデル名 + GGUF」で検索してください。有名なのは `Bartowski` 氏や `MaziyarPanahi` 氏が公開しているものです。自分で量子化を行うことも可能ですが、まずは有志が公開しているものを使うのが近道です。

### Q3: VRAM 8GBしかないのですが、工夫でなんとかなりますか？

3B（30億パラメータ）クラスのモデルなら余裕で動きます。7Bクラスなら、量子化をQ4以下に下げ、`n_ctx`（コンテキストサイズ）を1024程度に絞ればなんとかGPUに載ります。ただし、実務レベルの長文を扱うにはやはり12GB以上が欲しくなります。

---

## あわせて読みたい

- [ローカルLLMの推論速度を最大化するGPU環境構築とllama-cpp-python最適化ガイド](/posts/2026-05-30-local-llm-gpu-optimization-llama-cpp-guide/)
- [Qwen 35B A3Bを12GB VRAMで高速化！llama.cpp MTP 使い方](/posts/2026-05-10-llamacpp-mtp-qwen-35b-high-speed-tutorial/)
- [低スペックPCでLLMを動かす llama.cpp 構築ガイド](/posts/2026-04-06-low-spec-pc-llm-llama-cpp-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "NVIDIAのGPUでなくても動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、速度は期待できません。AMD製GPUならROCm、MacならMetalを使用するようにビルドすれば高速化されますが、互換性と情報の多さではNVIDIA一択です。仕事で使うなら、ケチらずにGeForce RTXシリーズを買うことを強く勧めます。"
      }
    },
    {
      "@type": "Question",
      "name": "量子化モデル（GGUF）はどこで手に入りますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Hugging Faceで「モデル名 + GGUF」で検索してください。有名なのは Bartowski 氏や MaziyarPanahi 氏が公開しているものです。自分で量子化を行うことも可能ですが、まずは有志が公開しているものを使うのが近道です。"
      }
    },
    {
      "@type": "Question",
      "name": "VRAM 8GBしかないのですが、工夫でなんとかなりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "3B（30億パラメータ）クラスのモデルなら余裕で動きます。7Bクラスなら、量子化をQ4以下に下げ、nctx（コンテキストサイズ）を1024程度に絞ればなんとかGPUに載ります。ただし、実務レベルの長文を扱うにはやはり12GB以上が欲しくなります。 ---"
      }
    }
  ]
}
</script>
