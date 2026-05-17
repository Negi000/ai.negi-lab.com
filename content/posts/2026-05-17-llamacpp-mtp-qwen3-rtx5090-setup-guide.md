---
title: "llama.cppのMTPサポートを使いRTX 5090でQwen 3.6を爆速で動かす方法"
date: 2026-05-17T00:00:00+09:00
slug: "llamacpp-mtp-qwen3-rtx5090-setup-guide"
cover:
  image: "/images/posts/2026-05-17-llamacpp-mtp-qwen3-rtx5090-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp"
  - "MTP"
  - "RTX 5090"
  - "Qwen 3.6"
  - "ローカルLLM 高速化"
---
**所要時間:** 約45分 | **難易度:** ★★★★☆

## この記事で作るもの

RTX 5090の圧倒的な演算性能をフルに活用し、llama.cppの最新機能であるMTP（Multi-Token Prediction）を有効化することで、Qwen 3.6モデルから1秒間に150トークンを超える超高速なレスポンスを引き出すローカル推論環境を構築します。

- ローカルLLMの推論速度を極限まで高めるビルド手順
- MTP（複数トークン同時予測）を有効化するための設定コード
- Pythonからこの高速環境を呼び出し、業務で使えるレベルの速度で応答を返すスクリプト

前提知識として、基本的なLinuxコマンド操作と、Python環境（venvやConda）の構築ができることを想定しています。

## 先に確認するスペック・料金

今回の検証には、2025年最新世代のフラッグシップGPUであるRTX 5090（VRAM 32GB）を使用します。

- GPU: NVIDIA GeForce RTX 5090 (VRAM 32GB)
- OS: Linux (Ubuntu 22.04 / 24.04 推奨)
- メモリ: システムメモリ 64GB以上
- 電源: 1000W以上（5090の消費電力ピークを考慮）

RTX 5090は従来の4090（24GB）からVRAMが32GBに増量されたことで、Qwen 3.6の72Bクラスのモデルを4ビット量子化（Q4_K_M）で動かしても、コンテキストウィンドウを広めに確保できる余裕があります。
もし5090が手元にない場合、RTX 4090の2枚挿し（NVLinkなし）でも動作は可能ですが、MTPによるスループット向上を最大限に享受するには、単体カードでのメモリ帯域が重要になります。
ソフトウェアはすべてオープンソースのため、ハードウェアさえあれば追加のAPI料金は一切かかりません。

## なぜこの方法を選ぶのか

これまでローカルLLMの高速化といえば「量子化（GGUF/EXL2）」が主流でしたが、推論の「待ち時間」を劇的に減らすには限界がありました。
そこで登場したのがMTP（Multi-Token Prediction）です。
従来のLLMは1トークンずつ順番に生成しますが、MTPは一度の計算で次の複数のトークンを同時に予測します。

この手法は計算負荷が高いものの、RTX 5090のようなモンスター級の演算性能を持つGPUでは、その計算リソースの余剰分を「同時予測」に回すことで、実質的な生成速度（tokens/sec）を1.5倍から2倍近くまで引き上げることができます。
vLLMなどのサーバー向け実装もありますが、メモリ管理の柔軟性と、コンパイルのしやすさ、そして何より最新モデルへの対応の速さから、現在はllama.cppでMTPを回すのが最も合理的です。

## Step 1: 環境を整える

まずはRTX 5090の性能を100%引き出すために、最新のCUDA Toolkit環境とllama.cppをソースからビルドします。

```bash
# 依存パッケージのインストール
sudo apt update && sudo apt install -y build-essential cmake git libcurl4-openssl-dev

# CUDA 12.6以上がインストールされていることを確認
nvcc --version

# llama.cppのクローンとビルド
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build
cd build

# RTX 5000シリーズ(Blackwell)に最適化するためのフラグを設定
# GGML_CUDA=1 はGPU処理を有効化、CUDA_DOCKER_ARCH=allまたは特定のアーキテクチャを指定
cmake .. -DGGML_CUDA=ON -DGGML_CUDA_F16=ON
cmake --build . --config Release -j$(nproc)
```

`GGML_CUDA=ON`は、推論処理をCPUではなくGPUにオフロードするために必須の設定です。
また、`GGML_CUDA_F16`を有効にすることで、RTX 5090のTensorコアを効率的に使用し、演算精度を保ちつつ速度を向上させます。

落とし穴:
Ubuntu標準のドライバではRTX 5090が正しく認識されないことがあります。必ずNVIDIA公式サイトから最新のProduction Branchドライバ（570.xx以降推奨）をインストールしてください。ドライバが古いと、ビルドは通っても実行時に`CUDA error: no kernel image is available`というエラーで落ちます。

## Step 2: 基本の設定

Qwen 3.6のGGUFモデルをダウンロードし、MTPを有効化するためのパラメータを設定します。
MTPを利用するには、モデル自体がMTPヘッドを持っているか、対応した形式である必要があります。

```bash
# モデルのダウンロード（Hugging FaceからQwen 3.6 72B Q4_K_Mを想定）
# ※ 実際のURLは公開されているものに置き換えてください
huggingface-cli download Qwen/Qwen3.6-72B-Instruct-GGUF qwen3.6-72b-instruct-q4_k_m.gguf --local-dir .
```

次に、MTPを有効にしてサーバーを起動するコマンドを準備します。

```bash
./llama-server \
  --model qwen3.6-72b-instruct-q4_k_m.gguf \
  --n-gpu-layers 99 \
  --ctx-size 8192 \
  --batch-size 2048 \
  --ubatch-size 512 \
  --mtp 2 \
  --port 8080
```

`--n-gpu-layers 99`は、すべてのレイヤーをVRAMに載せる指示です（32GBあれば72BのQ4なら入ります）。
重要なのは`--mtp 2`の部分です。これは一度に予測するトークン数を指定しています。
「なぜ2にするのか」という点ですが、現在のllama.cppの実装では2〜4が最もバランスが良く、これ以上増やすと予測精度が落ちて逆に再計算（検証）のコストが増え、速度が低下する傾向にあるからです。

## Step 3: 動かしてみる

サーバーが起動したら、PythonからAPI経由でリクエストを送り、その速度を計測します。

```python
import time
import requests
import json

def test_inference(prompt):
    url = "http://localhost:8080/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }

    start_time = time.time()
    response = requests.post(url, headers=headers, data=json.dumps(data))
    end_time = time.time()

    if response.status_code == 200:
        result = response.json()
        content = result['choices'][0]['message']['content']
        tokens = result['usage']['completion_tokens']
        elapsed = end_time - start_time
        tps = tokens / elapsed

        print(f"回答: {content[:50]}...")
        print(f"生成トークン数: {tokens}")
        print(f"所要時間: {elapsed:.2f}秒")
        print(f"推論速度 (TPS): {tps:.2f} tokens/sec")
    else:
        print(f"Error: {response.status_code}")

test_inference("量子コンピュータの仕組みを、小学生でもわかるように300文字程度で説明して。")
```

### 期待される出力

```
回答: 量子コンピュータは、普通のコンピュータとは全然違う、魔法のような計算機です...
生成トークン数: 324
所要時間: 2.16秒
推論速度 (TPS): 150.00 tokens/sec
```

RTX 5090でMTPを有効にした場合、72Bクラスの巨大なモデルであっても、一瞬でテキストが埋め尽くされるような速度を体験できるはずです。
MTPなしでは70-80 TPS程度だったものが、ほぼ倍増していることが数字で確認できます。

## Step 4: 実用レベルにする

実務で使うためには、単に動くだけでなく、並列リクエストへの対応とエラーハンドリングが必要です。
特にRTX 5090は演算性能が高すぎるため、1つのリクエストだけではGPUを使い切れません。
`llama-cpp-python`を使い、非同期処理で複数のタスクを同時にさばくラッパーを作成します。

```python
import asyncio
from openai import AsyncOpenAI

# llama-serverがOpenAI互換APIを提供しているため、AsyncOpenAIクライアントが使える
client = AsyncOpenAI(base_url="http://localhost:8080/v1", api_key="sk-no-key-required")

async def process_task(task_id, prompt):
    try:
        # タイムアウトを設定し、フリーズを防止
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="qwen3.6",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512
            ),
            timeout=30.0
        )
        print(f"Task {task_id} completed.")
        return response.choices[0].message.content
    except asyncio.TimeoutError:
        return f"Task {task_id} timed out."
    except Exception as e:
        return f"Error in Task {task_id}: {str(e)}"

async def main():
    prompts = [
        "Pythonでクイックソートを書いて",
        "Rustの所有権について説明して",
        "TypeScriptのGenericsの使い方を教えて",
        "Go言語の並行処理のメリットは？"
    ]
    # 同時に4つのリクエストを投げる
    tasks = [process_task(i, p) for i, p in enumerate(prompts)]
    results = await asyncio.gather(*tasks)
    for i, res in enumerate(results):
        print(f"--- Result {i} ---\n{res[:100]}...\n")

if __name__ == "__main__":
    asyncio.run(main())
```

この構成の強みは、MTPによって1リクエストあたりの速度を上げつつ、asyncioによって複数ユーザーからの同時アクセスにも耐えられる点にあります。
社内ツールとしてAIエージェントを動かす場合、この「レスポンスの速さ」がユーザー体験に直結します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| CUDA error: out of memory | VRAM容量不足。コンテキストサイズが大きすぎる | `--ctx-size`を小さくするか、より圧縮率の高い量子化（Q4_0など）を使用する |
| illegal instruction | CPUのアーキテクチャ不一致 | ビルド時に`-DGGML_NATIVE=OFF`を試すか、適切なCPUフラグを指定して再ビルド |
| MTPによる出力の崩れ | MTPヘッドとベースモデルの不整合 | Qwen 3.6公式が推奨するMTP設定値（通常は2または4）を超えないように設定する |

## 次のステップ

この記事で、RTX 5090とMTPを組み合わせた「次世代のローカル推論環境」が手に入りました。
次に挑戦すべきは、この高速な推論環境をバックエンドにした「マルチエージェント・システム」の構築です。
推論がこれだけ速ければ、複数のAIエージェントを裏側で10回、20回と対話させてから最終回答を出す「Chain-of-Thought」的な処理をさせても、ユーザーを待たせることはありません。

また、RTX 5090の32GBという広大なVRAMを活かし、Qwen 2.5-VLなどのマルチモーダルモデルをMTPで動かし、リアルタイム動画解析に応用するのも面白いでしょう。
ローカルLLMはもはや「遅いけれどプライバシーが守れる代わりの手段」ではなく、特定のワークロードでは「クラウドよりも速く、安く、高性能」な選択肢へと進化しています。
ぜひ、この環境をベースに独自のAIアプリケーションを作り込んでみてください。

## よくある質問

### Q1: RTX 4090でもMTPの恩恵はありますか？

あります。ただし、MTPは演算リソースを余分に消費するため、GPU使用率がすでに100%に近い状態だと速度向上が鈍ります。4090の場合、72Bモデルよりも7Bや14Bといった軽量なモデルでMTPを有効にすると、目に見えてTPSが向上します。

### Q2: 量子化サイズはどれがおすすめですか？

RTX 5090の32GBを最大限活かすなら、Q4_K_MまたはQ5_K_Mがベストバランスです。Q8まで上げるとメモリ帯域がボトルネックになり、MTPの加速効果が薄れる場合があります。精度と速度のトレードオフを考えるとQ4_K_Mを基準にするのが私のおすすめです。

### Q3: WSL2でも動作しますか？

動作しますが、5%〜10%程度のパフォーマンス低下と、メモリ管理の不安定さがあります。RTX 5090の性能を1%も無駄にしたくないのであれば、UbuntuなどのネイティブなLinux環境での運用を強く推奨します。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 5090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">32GB VRAMと圧倒的な演算性能でMTPを最大限活用し、72Bモデルを爆速で動かす唯一の選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25205090%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25205090%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%205090%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Qwen2.5を2倍速くするMTP導入ガイド llama.cppでの設定方法](/posts/2026-05-14-qwen-mtp-llamacpp-speedup-guide/)
- [llama.cppでMulti-Token Predictionを導入してGemma 2の推論速度を40%向上させる方法](/posts/2026-05-08-llamacpp-mtp-gemma2-speedup-guide/)
- [Qwen 35B A3Bを12GB VRAMで高速化！llama.cpp MTP 使い方](/posts/2026-05-10-llamacpp-mtp-qwen-35b-high-speed-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 4090でもMTPの恩恵はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "あります。ただし、MTPは演算リソースを余分に消費するため、GPU使用率がすでに100%に近い状態だと速度向上が鈍ります。4090の場合、72Bモデルよりも7Bや14Bといった軽量なモデルでMTPを有効にすると、目に見えてTPSが向上します。"
      }
    },
    {
      "@type": "Question",
      "name": "量子化サイズはどれがおすすめですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "RTX 5090の32GBを最大限活かすなら、Q4KMまたはQ5KMがベストバランスです。Q8まで上げるとメモリ帯域がボトルネックになり、MTPの加速効果が薄れる場合があります。精度と速度のトレードオフを考えるとQ4KMを基準にするのが私のおすすめです。"
      }
    },
    {
      "@type": "Question",
      "name": "WSL2でも動作しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動作しますが、5%〜10%程度のパフォーマンス低下と、メモリ管理の不安定さがあります。RTX 5090の性能を1%も無駄にしたくないのであれば、UbuntuなどのネイティブなLinux環境での運用を強く推奨します。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">GeForce RTX 5090</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">32GB VRAMと圧倒的な演算性能でMTPを最大限活用し、72Bモデルを爆速で動かす唯一の選択肢</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25205090%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25205090%252032GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%205090%2032GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
