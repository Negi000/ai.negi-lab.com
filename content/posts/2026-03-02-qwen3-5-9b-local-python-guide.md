---
title: "Qwen3.5-9Bをローカル環境のPythonで動かし自分専用の超高速AIアシスタントを作る方法"
date: 2026-03-02T00:00:00+09:00
slug: "qwen3-5-9b-local-python-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen3.5-9B 使い方"
  - "llama-cpp-python 入門"
  - "ローカルLLM Python 構築"
---
**所要時間:** 約30分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Qwen3.5-9B（GGUF版）をPythonから制御し、日本語で自然な対話ができるストリーミング形式のチャットスクリプト。
- 前提知識: Pythonの基本的な読み書きができること、コマンドライン操作に抵抗がないこと。
- 必要なもの: NVIDIA製GPU（VRAM 8GB以上推奨）、Python 3.10以降。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">9Bモデルを快適に、かつ余裕を持って動かすならVRAM 16GB搭載のこのカードがコスパ最強です。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=ASUS%20NVIDIA%20GeForce%20RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FASUS%2520NVIDIA%2520GeForce%2520RTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FASUS%2520NVIDIA%2520GeForce%2520RTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

Qwen3.5-9Bは、Alibabaが開発した最新の軽量モデルです。
同サイズのLlama 3 8Bと比較して、圧倒的に「日本語の語彙力と文脈理解」に長けているのが最大の特徴です。
SIer時代、私は多言語モデルの日本語の不自然さに何度も泣かされてきましたが、Qwenシリーズは漢字の扱いが正確で、ビジネス文書の生成でも手直しがほとんどいりません。

今回は、あえてHugging Faceのtransformersではなく「llama-cpp-python」を使用します。
理由は明確で、VRAMの消費量を抑えつつ、量子化（GGUF形式）によって推論速度を劇的に向上させるためです。
RTX 3060クラスのミドルレンジGPUでも、1秒間に50トークン以上の爆速で文字が流れる快感は、クラウドAPIでは味わえません。

## Step 1: 環境を整える

まずはGPUを最大限に活かすためのライブラリをインストールします。
ここは初心者が最も躓きやすい「ビルド設定」が含まれる重要なステップです。

```bash
# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# CUDAを使用するためのビルドフラグを設定してインストール
# これを忘れるとCPU推論になり、1文字出すのに数秒待たされることになります
export CMAKE_ARGS="-DLLAMA_CUDA=on"
pip install llama-cpp-python

# モデルをダウンロードするためのツール
pip install huggingface_hub
```

`CMAKE_ARGS="-DLLAMA_CUDA=on"` は、llama-cppに対して「NVIDIAのGPU（CUDA）を使うようにコンパイルせよ」と命令するスイッチです。
これを指定せずにインストールすると、どれだけ高価なGPUを積んでいても宝の持ち腐れになるので注意してください。

⚠️ **落とし穴:**
Windows環境で `CMAKE_ARGS` が効かない場合は、PowerShellで `$env:CMAKE_ARGS="-DLLAMA_CUDA=on"` と実行してからインストールしてください。
また、事前にVisual Studioの「C++によるデスクトップ開発」ワークロードとCUDA Toolkitがインストールされている必要があります。

## Step 2: 基本の設定

次に、モデルファイルをダウンロードします。
今回はUnslothが公開している最適化済みのGGUF版（Q4_K_M量子化）を使用します。
これは「画質とファイルサイズのバランス」が最も良い設定です。

```python
import os
from huggingface_hub import hf_hub_download

# モデルの保存先
model_name = "unsloth/Qwen3.5-9B-GGUF"
model_file = "Qwen3.5-9B-Q4_K_M.gguf"
model_path = "./models"

if not os.path.exists(model_path):
    os.makedirs(model_path)

# モデルのダウンロード（約5.5GBあります）
path = hf_hub_download(
    repo_id=model_name,
    filename=model_file,
    local_dir=model_path
)

print(f"モデルの準備が完了しました: {path}")
```

なぜ「Q4_K_M」という形式を選ぶのか。
それは、重みを4ビットに圧縮しても、モデルの賢さ（パープレキシティ）の低下を最小限に抑えつつ、VRAM使用量を半分以下にできるからです。
実務経験上、9Bクラスのモデルなら4ビット量子化で十分な精度が出せると確信しています。

## Step 3: 動かしてみる

いよいよ、PythonからQwen3.5を呼び出します。
まずは「ちゃんとGPUが使われているか」を確認するための最小限のコードを書きましょう。

```python
from llama_cpp import Llama

# モデルの初期化
llm = Llama(
    model_path="./models/Qwen3.5-9B-Q4_K_M.gguf",
    n_gpu_layers=-1, # 全ての層をGPUにロードする設定（これが最速）
    n_ctx=4096,      # コンテキストウィンドウ（記憶できる長さ）
    verbose=False    # ログ出力を抑制
)

# プロンプトの実行
response = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "あなたは優秀なアシスタントです。"},
        {"role": "user", "content": "Qwen3.5-9Bの特徴を短く教えてください。"}
    ]
)

print(response["choices"][0]["message"]["content"])
```

### 期待される出力

```
Qwen3.5-9Bは、Alibaba Cloudが開発した最新の言語モデルです。
1. 前世代より多言語対応、特に日本語の理解力が大幅に向上。
2. 9Bという軽量サイズながら、推論速度と精度のバランスが優れている。
3. 数学やコーディング能力も強化されています。
```

`n_gpu_layers=-1` という設定が肝です。
これを指定することで、モデルの全パラメータをVRAMに載せます。
もしVRAMが足りずにエラーが出る場合は、この数値を `20` や `30` に減らして調整してください。

## Step 4: 実用レベルにする

「1回質問して終わり」では実務に使えません。
次は、会話が連続して続き、かつ回答がリアルタイムに表示される「ストリーミング版」を実装します。
私がローカルLLMを検証する際は、必ずこの形式でレスポンスの「体感速度」を測ります。

```python
import sys
from llama_cpp import Llama

class QwenChat:
    def __init__(self, model_path):
        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,
            n_ctx=8192, # 開発ドキュメント等の長い文章を読ませるために拡張
            flash_attn=True # 高速化のためのFlash Attentionを有効化
        )
        self.history = [{"role": "system", "content": "あなたは技術に詳しいAI専門ブロガーです。"}]

    def chat(self):
        print("--- Qwen3.5-9B Chat Start (Ctrl+Cで終了) ---")
        while True:
            try:
                user_input = input("\nあなた: ")
                if not user_input: continue

                self.history.append({"role": "user", "content": user_input})
                print("AI: ", end="", flush=True)

                stream = self.llm.create_chat_completion(
                    messages=self.history,
                    stream=True # ここをTrueにすることで、生成された文字から順次出力される
                )

                full_response = ""
                for chunk in stream:
                    delta = chunk["choices"][0]["delta"]
                    if "content" in delta:
                        content = delta["content"]
                        print(content, end="", flush=True)
                        full_response += content

                self.history.append({"role": "assistant", "content": full_response})
                print()

            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    chat_app = QwenChat("./models/Qwen3.5-9B-Q4_K_M.gguf")
    chat_app.chat()
```

このスクリプトでは、`stream=True` を使って、モデルが単語を生成するたびに画面に出力しています。
また、`self.history` に過去の発言を蓄積することで、前後の文脈を理解した対話が可能になります。
SIerでの保守案件などで「過去のログを解析させる」ような使い方も、この構造なら簡単に拡張できます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ValidationError` | プロンプトの形式ミス | `messages` のリスト構造を再確認する |
| `out of memory` | VRAM不足 | `n_gpu_layers` を下げるか `n_ctx` を小さくする |
| `cl.exe not found` | MSVCが入っていない | Visual Studio Build Toolsをインストールする |
| 生成速度が極端に遅い | CPUで動作している | `llama-cpp-python` をCUDA有効で再インストールする |

## 次のステップ

お疲れ様でした。これであなたの手元には、世界最高峰の軽量LLMが24時間365日使い放題の環境が整いました。
次に挑戦すべきは「RAG（検索拡張生成）」の構築です。
今回作ったスクリプトに、自社のマニュアルやPDFの内容をベクトル化して読み込ませれば、世界に一つだけの専門家AIが完成します。

また、Qwen3.5-9BはFunction Callingの精度も高いです。
「明日の天気は？」と聞かれたら自動で天気APIを叩きに行く、といった外部連携スクリプトへ拡張するのも面白いでしょう。
RTX 4090を2枚刺している私でも、この9Bモデルの挙動の軽快さには毎日驚かされています。
ローカルLLMの世界は、ここからが本当の始まりです。

## よくある質問

### Q1: 16GBのメモリしかありませんが動きますか？

メインメモリ（RAM）が16GBあれば、GGUF形式の9Bモデルは余裕で動きます。ただし、GPUを活用しない場合はCPU負荷が100%になり、回答速度は1秒間に数文字程度まで落ちる可能性があります。

### Q2: 途中で回答が切れてしまいます。

`create_chat_completion` の引数に `max_tokens=2048` などを指定して、最大出力数を増やしてください。また、`n_ctx`（コンテキストサイズ）が入力文に対して小さすぎないかも確認してください。

### Q3: 日本語がたまに変な漢字になります。

システムプロンプト（System Role）で「あなたは日本語のネイティブスピーカーです」とはっきり指示を出してください。また、モデルファイルが破損していないかハッシュ値を確認するのも有効です。

---

## あわせて読みたい

- [Qwen3.5-35BをVRAM 16GBで爆速動作させるローカルLLM構築術](/posts/2026-02-27-qwen35-35b-local-setup-16gb-vram/)
- [Qwen3.5-35B-A3BとAiderで爆速コーディング環境を構築する方法](/posts/2026-02-25-qwen35-35b-aider-local-ai-coding-guide/)
- [次世代AI「Qwen3.5」をいち早くローカル環境で試す方法](/posts/2026-02-08-5c9988c9/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "16GBのメモリしかありませんが動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "メインメモリ（RAM）が16GBあれば、GGUF形式の9Bモデルは余裕で動きます。ただし、GPUを活用しない場合はCPU負荷が100%になり、回答速度は1秒間に数文字程度まで落ちる可能性があります。"
      }
    },
    {
      "@type": "Question",
      "name": "途中で回答が切れてしまいます。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "createchatcompletion の引数に maxtokens=2048 などを指定して、最大出力数を増やしてください。また、nctx（コンテキストサイズ）が入力文に対して小さすぎないかも確認してください。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語がたまに変な漢字になります。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "システムプロンプト（System Role）で「あなたは日本語のネイティブスピーカーです」とはっきり指示を出してください。また、モデルファイルが破損していないかハッシュ値を確認するのも有効です。 ---"
      }
    }
  ]
}
</script>
