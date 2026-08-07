---
title: "llama.cpp 使い方 入門｜GGUF量子化モデルをローカルPCで高速に動かす方法"
date: 2026-08-07T00:00:00+09:00
slug: "llama-cpp-gguf-python-local-llm-guide"
cover:
  image: "/images/posts/2026-08-07-llama-cpp-gguf-python-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "Python LLM ローカル"
  - "llama-cpp-python インストール"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

この記事を読み進めることで、Llama 3やQwenといった最新のLLM（大規模言語モデル）を、Pythonから呼び出して高速に動作させる「チャット用バックエンド」が完成します。
単に動かすだけでなく、モデルを量子化してメモリ消費を抑え、GPUの性能を限界まで引き出す設定を自力で行えるようになります。
Pythonの基礎（pipインストールや関数の作成）ができる方を対象としています。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）の容量」です。
8GBあればLlama 3 8Bクラスを実用レベルで動かせますが、快適さを求めるなら12GB以上を強く推奨します。
私はRTX 4090の24GBを2枚使っていますが、GGUF量子化を使えば安価なRTX 3060 12GBでも驚くほど高速に動作します。

Macユーザーの場合、メモリ（ユニファイドメモリ）が16GB以上あれば、M1/M2/M3チップの性能を活かして高速な推論が可能です。
メモリ8GBのモデルだと、OSの動作分でカツカツになり、推論速度が著しく低下するので注意してください。
料金については、オープンソースのモデルを使うため、一度環境を整えてしまえば電気代以外は一切かかりません。

これからハードウェアを揃えるなら、VRAM 16GBを搭載したRTX 4060 Tiが、最もコストパフォーマンス良くllama.cppを回せる選択肢になります。
中古のRTX 3060 12GBも、2万円台後半で見つかるなら入門用として悪くない投資です。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手法には「Ollama」「vLLM」「llama.cpp」など複数の選択肢があります。
その中で私が「llama.cpp」を推す理由は、依存関係が非常にクリーンで、あらゆるプラットフォーム（Windows, Linux, macOS）で動作し、かつ「GGUF」という軽量フォーマットの恩恵を最大化できるからです。

Ollamaは内部でllama.cppを使用しており使い勝手は抜群ですが、細かい推論パラメータのチューニングや、自作アプリへの組み込みやすさではllama.cppのPythonバインディング（llama-cpp-python）に軍配が上がります。
特に、限られたVRAMを1MB単位で節約しながら、CPUとGPUのハイブリッド推論を行いたい実務シーンでは、llama.cpp以外の選択肢はあり得ません。
量子化技術によって、本来40GBのVRAMが必要なモデルを5GB程度に圧縮して動かせる快感は、一度味わうと戻れなくなります。

## Step 1: 環境を整える

まずは、llama.cppをPythonから扱うためのライブラリをインストールします。
ここが最大の関門です。GPUを使えるようにビルドしないと、推論が絶望的に遅くなります。

### Windows (NVIDIA GPU使用) の場合
CUDA Toolkitがインストールされていることが前提です。私はv12.x系を使用しています。

```bash
# CUDA対応版をインストールするための環境変数設定
$env:CMAKE_ARGS = "-DGGML_CUDA=ON"
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

### macOS (Apple Silicon) の場合
Metalを有効にすることで、爆速で動きます。

```bash
CMAKE_ARGS="-DGGML_METAL=ON" pip install llama-cpp-python
```

これらのコマンドは「ただライブラリを入れる」のではなく「あなたのPCのGPUを計算に使うための専用部品を組み込む」作業です。
これを忘れると、全ての計算がCPUで行われ、1文字出力するのに数秒待たされることになります。

⚠️ **落とし穴:**
Windowsユーザーで「error: Microsoft Visual C++ 14.0 or greater is required」というエラーが出た場合、Visual Studio Build Toolsが足りていません。
「C++によるデスクトップ開発」にチェックを入れてインストールしてください。
これを入れないと、llama.cppの心臓部であるC++コードのコンパイルが失敗します。

## Step 2: 基本の設定

環境ができたら、次は「脳」となるモデルファイルを準備します。
Hugging Faceで「[モデル名]-GGUF」と検索し、`.gguf`という拡張子のファイルをダウンロードします。
今回は汎用性が高い「Llama-3-8B-Instruct-v0.1-GGUF」を例にします。

量子化ビット数は、精度と速度のバランスが良い「Q4_K_M」または「Q5_K_M」を選んでください。
4ビット（Q4）以下に下げると知能が目に見えて低下し、8ビット以上に上げても人間には違いがほぼ分かりません。

```python
import os
from llama_cpp import Llama

# モデルファイルのパスを指定
# 事前にダウンロードして、スクリプトと同じフォルダに置いておく
model_path = "Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"

# モデルの初期化
llm = Llama(
    model_path=model_path,
    n_gpu_layers=-1, # すべてのレイヤーをGPUに転送（最速設定）
    n_ctx=2048,      # コンテキストサイズ（記憶の長さ）
    verbose=False    # 余計なログを出さない
)
```

`n_gpu_layers`を`-1`にするのがコツです。
これは「GPUのメモリが許す限り、全ての計算をGPUに丸投げする」という意味です。
VRAMが足りない場合は、この数値を「20」や「30」と調整して、一部の計算だけをCPUに逃がす設定にします。

## Step 3: 動かしてみる

準備が整ったので、まずは最小限のコードでモデルに喋らせてみましょう。
LLMに役割（System Prompt）を与えて、質問を投げます。

```python
# 推論の実行
response = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "あなたは優秀なエンジニアです。簡潔に回答してください。"},
        {"role": "user", "content": "Pythonで高速なAPIを作るならどのフレームワークがおすすめ？"}
    ],
    temperature=0.7, # 自由度（0.0で固定、高いほど創造的）
)

# 結果の表示
print(response["choices"][0]["message"]["content"])
```

### 期待される出力

```
高速なAPIを構築するなら、FastAPIが最もおすすめです。
理由は、StarletteとPydanticをベースにしており、非同期処理（async/await）を標準でサポートしているためです。
また、自動でSwaggerドキュメントが生成される点も開発効率を大幅に向上させます。
```

このレスポンスが返ってくる速さに注目してください。
適切にGPUが認識されていれば、8Bモデルなら1秒間に数十トークン（文字）が生成されるはずです。
もし「1文字ずつ、ゆっくり表示される」なら、Step 1のGPU設定が失敗している可能性が高いです。

## Step 4: 実用レベルにする

実務で使うなら、回答が生成されるのを待ってから表示するのではなく、生成されたそばから表示する「ストリーミング」が必須です。
また、エラー処理と再利用性を考慮したクラス化を行います。

```python
import sys

class LocalAI:
    def __init__(self, model_path):
        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,
            n_ctx=4096,
            seed=42 # 結果を固定したい場合に指定
        )

    def chat(self, prompt):
        # ストリーミングを有効にする
        stream = self.llm.create_chat_completion(
            messages=[
                {"role": "user", "content": prompt}
            ],
            stream=True
        )

        full_response = ""
        for chunk in stream:
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                content = delta["content"]
                print(content, end="", flush=True) # 1文字ずつ即座に出力
                full_response += content

        print("\n") # 最後に改行
        return full_response

# 実行コード
if __name__ == "__main__":
    ai = LocalAI("Meta-Llama-3-8B-Instruct-Q4_K_M.gguf")

    while True:
        user_input = input("質問を入力してください（exitで終了）: ")
        if user_input.lower() == "exit":
            break
        ai.chat(user_input)
```

このコードのポイントは `stream=True` です。
ChatGPTのように文字が流れるように表示されるため、ユーザーの待ち時間を視覚的に減らすことができます。
また、`seed`を固定することで、同じ質問に対して同じ回答を出すよう調整しており、デバッグが容易になります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Address already in use` | 過去のプロセスがGPUを掴んだまま | タスクマネージャーか`nvidia-smi`でPythonプロセスを終了 |
| `Model path does not exist` | ファイル名の間違い | `.gguf`の拡張子が二重になっていないか確認 |
| `CUDA error: out of memory` | VRAM容量不足 | `n_gpu_layers`の値を減らす（例: 20） |
| 推論が非常に遅い | CPUで動作している | `CMAKE_ARGS`を付けてライブラリを再インストール |

## 次のステップ

ここまでで、あなたは自分のPC上で知能を動かす基盤を手に入れました。
次に挑戦すべきは「RAG（検索拡張生成）」の実装です。
llama.cppはテキスト生成だけでなく、文章をベクトル化（Embedding）する機能も持っています。

自分のドキュメントや社内マニュアルをベクトルデータベース（ChromaやQdrant）に保存し、質問に関連する箇所をllama.cppに読み込ませることで、「あなたのデータについて回答するAI」が作れます。
API経由ではなくローカルで完結するため、機密情報の流出を気にせず、社内サーバーでAIを運用できるようになります。

まずは、より大きなモデル（Llama-3-70Bなど）をQ2_K（2ビット量子化）などの極限まで削った状態で動かしてみるのも面白いでしょう。
ビット数を下げても、モデルサイズが大きい方が賢いという「規模の経済」を実感できるはずです。

## よくある質問

### Q1: GGUFと他の形式（Safari, AWQ）は何が違うのですか？

GGUFはllama.cpp専用に設計された形式で、CPUとGPUの両方で効率的に動くよう最適化されています。最大の特徴は「1ファイルで完結する」ことで、設定ファイルやトークナイザーを別々に管理する必要がありません。

### Q2: 性能を引き出すための最適なスレッド数は？

基本的には物理コア数と同じに設定するのがベストです。`Llama`クラスの引数に `n_threads=8` のように指定できます。多すぎてもオーバーヘッドで逆に遅くなるので、自身のCPUスペックに合わせて調整してください。

### Q3: 複数のGPUを持っている場合、両方使えますか？

はい、llama.cppはマルチGPUに対応しています。基本的には自動で認識されますが、特定のGPUを指定したい場合は環境変数 `CUDA_VISIBLE_DEVICES` で制御可能です。4090を2枚刺している私の環境では、特に追加設定なしでVRAM 48GBとして認識されています。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBを搭載しており、GGUF量子化モデルを余裕を持って動かせる入門最適解です。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cpp 使い方 入門 | GGUF量子化モデルをローカルPCで高速に動かす方法](/posts/2026-07-18-llamacpp-gguf-local-llm-tutorial/)
- [llama.cpp 使い方 入門 | GGUF量子化でローカルLLMを動かす](/posts/2026-08-06-llamacpp-gguf-python-setup-guide/)
- [llama.cpp 使い方 入門｜低スペックPCでLlama 3を爆速で動かす実践ガイド](/posts/2026-06-12-llama-cpp-gguf-beginner-guide-python/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "GGUFと他の形式（Safari, AWQ）は何が違うのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "GGUFはllama.cpp専用に設計された形式で、CPUとGPUの両方で効率的に動くよう最適化されています。最大の特徴は「1ファイルで完結する」ことで、設定ファイルやトークナイザーを別々に管理する必要がありません。"
      }
    },
    {
      "@type": "Question",
      "name": "性能を引き出すための最適なスレッド数は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的には物理コア数と同じに設定するのがベストです。Llamaクラスの引数に nthreads=8 のように指定できます。多すぎてもオーバーヘッドで逆に遅くなるので、自身のCPUスペックに合わせて調整してください。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のGPUを持っている場合、両方使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、llama.cppはマルチGPUに対応しています。基本的には自動で認識されますが、特定のGPUを指定したい場合は環境変数 CUDAVISIBLEDEVICES で制御可能です。4090を2枚刺している私の環境では、特に追加設定なしでVRAM 48GBとして認識されています。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBを搭載しており、GGUF量子化モデルを余裕を持って動かせる入門最適解です。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
