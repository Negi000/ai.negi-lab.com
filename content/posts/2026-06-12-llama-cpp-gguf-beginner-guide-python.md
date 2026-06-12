---
title: "llama.cpp 使い方 入門｜低スペックPCでLlama 3を爆速で動かす実践ガイド"
date: 2026-06-12T00:00:00+09:00
slug: "llama-cpp-gguf-beginner-guide-python"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "Llama 3 ローカル"
  - "Python 推論 高速化"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

自分のPCリソースを最大限に活用し、Llama 3 8Bなどの最新モデルを秒間20トークン以上の高速レスポンスで動かすローカル推論環境を構築します。
Pythonからライブラリとして呼び出し、AIチャット機能を自作アプリケーションに組み込むためのベースを完成させます。

前提知識：
- 基本的なコマンド操作（cd, git clone程度）ができる
- Python 3.10以上の環境がある
- 「クラウドは高いからローカルで回したい」という強い動機がある

必要なもの：
- PC（Windows / Mac / Linux）
- NVIDIA製GPU（VRAM 8GB以上推奨）または Apple Silicon（M1/M2/M3）
- インターネット接続環境（モデルのダウンロードに数GB消費します）

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
クラウドAPIを使えば月額料金やトークン課金が発生しますが、llama.cppによるローカル運用なら電気代以外は完全に無料です。

最低でもVRAM 8GBを搭載したグラフィックボード（RTX 3060 / 4060等）があれば、8Bクラスのモデルを「Q4_K_M」という量子化設定で快適に動かせます。
16GBあれば、少し工夫すれば30Bクラスのモデルも視野に入ります。
Macユーザーなら、メモリ（ユニファイドメモリ）が16GB以上あれば、M1チップ以降なら驚くほどスムーズに動作します。

もしこれから機材を揃えるなら、コストパフォーマンスの観点から「RTX 4060 Ti 16GBモデル」一択です。
AI用途において、計算速度よりも「モデルがメモリに載るかどうか」が決定的な差を生むからです。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手法は、他に「Ollama」や「LM Studio」といったGUIツールも存在します。
しかし、本気でシステムに組み込んだり、将来的に独自のチューニングを施したいなら、llama.cppを直接触るのがベストです。

llama.cppはC++で書かれており、オーバーヘッドが極限まで削ぎ落とされています。
Pythonの重いライブラリを介さずに推論できるため、起動が速く、メモリ消費も最小限です。
また、GGUFというファイルフォーマットを採用することで、GPUメモリが足りない場合に「一部をメインメモリ（RAM）に逃がす」という柔軟な運用が可能です。
これは、VRAMの限界＝動作不可となる他のフレームワークにはない圧倒的な強みです。

## Step 1: 環境を整える

まずは、llama.cppをビルドするためのツールチェーンをインストールします。
「ビルド」と聞くと難しく感じるかもしれませんが、コマンドを叩くだけで終わります。

### Windows (PowerShell) の場合
Visual Studioの「C++によるデスクトップ開発」ワークロードが必要です。

```powershell
# gitをインストールしていない場合は先にインストール
# 完了後、リポジトリをクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
```

### Mac (Terminal) の場合
Xcode Command Line Toolsが必要です。

```bash
xcode-select --install
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make -j
```

Macの場合はこれだけでMetal（GPU加速）が有効になったバイナリが生成されます。
WindowsでNVIDIA GPUを使う場合は、CMakeを利用してCUDAを有効にする必要があります。

```powershell
mkdir build
cd build
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release
```

落とし穴：CUDAツールキットがインストールされていないと、GPUが認識されずCPU推論になり、速度が1/10以下に低下します。
必ず `nvcc --version` でパスが通っているか確認してください。

## Step 2: 基本の設定

llama.cppを動かすには、モデルファイル（.gguf）が必要です。
Hugging Faceにある「Meta-Llama-3-8B-Instruct-GGUF」などを利用します。

量子化サイズは「Q4_K_M」を推奨します。
これは重みを4ビットに圧縮する設定で、精度低下を最小限に抑えつつ、ファイルサイズを半分以下に軽量化できる「黄金比」のような設定です。

```bash
# モデルを保存するディレクトリを作成
mkdir models

# 手動でダウンロードしたファイルを models/ 内に配置
# 例: Meta-Llama-3-8B-Instruct-Q4_K_M.gguf
```

次に、Pythonからllama.cppを操作するためのラッパー「llama-cpp-python」をインストールします。
これが「仕事で使えるAIシステム」を作るための心臓部になります。

```bash
# NVIDIA GPU利用者の場合
$env:CMAKE_ARGS="-DGGML_CUDA=ON"
pip install llama-cpp-python

# Mac利用者の場合
CMAKE_ARGS="-DGGML_METAL=ON" pip install llama-cpp-python
```

落とし穴：単に `pip install` するだけでは、GPUサポートが無効な状態でインストールされます。
必ず `CMAKE_ARGS` を指定して、お使いのハードウェアに最適化されたバイナリをコンパイルさせてください。

## Step 3: 動かしてみる

最小構成のスクリプトで、モデルが正常にロードされ、GPUで推論されているかを確認します。
以下のコードを `test_run.py` として保存してください。

```python
import os
from llama_cpp import Llama

# モデルのパスを指定
# n_gpu_layersは重要：-1にすると全ての層をGPUにオフロードします
llm = Llama(
    model_path="./models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf",
    n_gpu_layers=-1,
    n_ctx=2048  # 文脈ウィンドウサイズ。メモリに合わせて調整
)

# 推論実行
output = llm(
    "Q: 空が青い理由を短く説明してください。 A:",
    max_tokens=100,
    stop=["Q:", "\n"],
    echo=True
)

print(output["choices"][0]["text"])
```

### 期待される出力

```
A: 太陽光が地球の大気中の分子と衝突し、波長の短い青い光が散乱されやすいためです（レイリー散乱）。
```

ここでログに `BLAS = 1` または `METAL = 1` と表示されていれば、正しくGPUが動いています。
もし `BLAS = 0` の場合はCPU推論になっており、私の経験上、1トークンの生成に数秒かかるストレスフルな環境になっているはずです。

## Step 4: 実用レベルにする

実務で使うためには、単発の推論ではなく「チャット形式」への対応と、ストリーミング出力（文字が1つずつ出てくる挙動）が不可欠です。
これがあるだけで、ユーザー体験は劇的に向上します。

```python
import sys
from llama_cpp import Llama

llm = Llama(
    model_path="./models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf",
    n_gpu_layers=-1,
    n_ctx=4096,
    verbose=False # 余計なログを消す
)

def chat_stream(prompt):
    # Llama 3のテンプレートを模した形式
    system_prompt = "あなたは誠実で優秀な日本人のアシスタントです。"
    full_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

    stream = llm(
        full_prompt,
        max_tokens=1024,
        stream=True,
        stop=["<|eot_id|>"]
    )

    for output in stream:
        token = output["choices"][0]["text"]
        yield token

# インタラクティブな実行
print("AIとの対話を開始します（exitで終了）")
while True:
    user_input = input("\nユーザー: ")
    if user_input.lower() == "exit":
        break

    print("アシスタント: ", end="", flush=True)
    for part in chat_stream(user_input):
        print(part, end="", flush=True)
    print()
```

このコードでは `stream=True` を設定しています。
これにより、AIが全ての文章を書き終えるのを待たずに、生成されたそばから画面に表示されます。
実務的なアプリケーション（例えばSlackボットや社内ツール）を作る際、この「応答開始までの速さ」がシステムの評価を左右します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `CUDA out of memory` | VRAM不足 | `n_gpu_layers` の値を少しずつ下げて（例: 20）、一部をメインメモリに逃がす |
| `Model not found` | パス指定ミス | 相対パスではなく、`os.path.abspath` で絶対パスを指定する |
| 生成が止まらない | Stopトークン未設定 | 使用するモデルのフォーマット（Llama 3なら `<|eot_id|>`）を `stop` 引数に入れる |
| 動作が異常に遅い | CPU推論になっている | `llama-cpp-python` をビルドオプション付きで再インストールする |

## 次のステップ

ここまでで、あなたの手元には「世界最高レベルの知能を、オフラインかつ無料で動かす環境」が整いました。
次に挑戦すべきは、このllama.cppをバックエンドにした「RAG（検索拡張生成）」の構築です。

自分のPDFファイルや社内ドキュメントを読み込ませ、その内容に基づいてAIに回答させる仕組みを作ってみてください。
LangChainやLlamaIndexといったライブラリを使えば、今回の `llama-cpp-python` をそのまま連携させることが可能です。
また、複数のGPUを持っているなら、`n_gpu_layers` を調整して巨大なモデル（Llama 3 70B等）を分割ロードする検証も非常に面白いです。

ローカルLLMの世界は、ハードウェアの制約を「設定」でどう乗り越えるかが醍醐味です。
ぜひ、自分のPCに合わせた最適なパラメータを探求してみてください。

## よくある質問

### Q1: Macのメモリはどれくらい必要ですか？

8Bモデルなら8GBでも動きますが、OSやブラウザの消費分を考えると16GBが最低ラインです。70Bクラスを動かしたいなら64GB以上を推奨します。MacはVRAMとRAMを共有するため、メモリ量がそのまま扱えるモデルのサイズに直結します。

### Q2: 量子化（Q4_K_Mなど）をすると頭が悪くなりませんか？

厳密にはわずかに精度が落ちますが、実務でその差を体感することは稀です。それよりも、量子化によって推論速度が3倍になり、より大きなモデルがメモリに載るメリットの方が圧倒的に大きいです。迷ったらQ4かQ5を選んでおけば間違いありません。

### Q3: 複数のGPUを持っている場合、両方使えますか？

はい、llama.cppはマルチGPUに対応しています。ビルド時にCUDAを有効にしていれば、自動的にレイヤーが分配されます。特定のGPUに偏らせたい場合は、環境変数 `CUDA_VISIBLE_DEVICES` で制御可能です。私の環境（RTX 4090 x 2）では、この方法で大規模モデルを高速化しています。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MSI GeForce RTX 4060 Ti GAMING X SLIM 16G</strong>
<p style="color:#555;margin:8px 0;font-size:14px">16GBのVRAMはローカルLLM運用において最もコスパが良い選択肢です。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [低スペックPCでLLMを動かす llama.cpp 構築ガイド](/posts/2026-04-06-low-spec-pc-llm-llama-cpp-guide/)
- [DeepSeek V4 Flash 使い方！llama.cppで最新モデルをローカル構築する手順](/posts/2026-06-06-deepseek-v4-flash-llamacpp-local-setup/)
- [llama-swap 使い方：Ollama超えのローカルLLM切り替え環境を構築](/posts/2026-03-06-llama-swap-local-llm-model-switching-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Macのメモリはどれくらい必要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "8Bモデルなら8GBでも動きますが、OSやブラウザの消費分を考えると16GBが最低ラインです。70Bクラスを動かしたいなら64GB以上を推奨します。MacはVRAMとRAMを共有するため、メモリ量がそのまま扱えるモデルのサイズに直結します。"
      }
    },
    {
      "@type": "Question",
      "name": "量子化（Q4_K_Mなど）をすると頭が悪くなりませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "厳密にはわずかに精度が落ちますが、実務でその差を体感することは稀です。それよりも、量子化によって推論速度が3倍になり、より大きなモデルがメモリに載るメリットの方が圧倒的に大きいです。迷ったらQ4かQ5を選んでおけば間違いありません。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のGPUを持っている場合、両方使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、llama.cppはマルチGPUに対応しています。ビルド時にCUDAを有効にしていれば、自動的にレイヤーが分配されます。特定のGPUに偏らせたい場合は、環境変数 CUDAVISIBLEDEVICES で制御可能です。私の環境（RTX 4090 x 2）では、この方法で大規模モデルを高速化しています。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MSI GeForce RTX 4060 Ti GAMING X SLIM 16G</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">16GBのVRAMはローカルLLM運用において最もコスパが良い選択肢です。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
