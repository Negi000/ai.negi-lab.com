---
title: "llama.cpp 使い方 入門 | GGUF量子化モデルをローカルPCで高速に動かす方法"
date: 2026-07-18T00:00:00+09:00
slug: "llamacpp-gguf-local-llm-tutorial"
cover:
  image: "/images/posts/2026-07-18-llamacpp-gguf-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "Llama-3 ローカル"
  - "Python AI 構築"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

最新のLlama 3などの大規模言語モデル（LLM）を、手元のPCで高速に動作させる環境を構築します。
具体的には、llama.cppをビルドし、量子化されたGGUFモデルを使ってPythonからチャットAIを呼び出すスクリプトを完成させます。

- llama.cppのローカル環境構築（コンパイル）
- Hugging FaceからのGGUFモデル選定とダウンロード
- Pythonバインディング（llama-cpp-python）を用いた実用的な推論コードの実装

前提知識として、ターミナル（コマンドプロンプト）の基本操作と、Pythonの基礎的な文法を理解している必要があります。
必要なものは、インターネット環境と、ある程度のスペックを持ったPC（後述）のみです。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
結論から言うと、最低でも8GB、快適に動かすなら12GBから16GBのVRAMを搭載したGPUが望ましいです。
もしGPUがない場合でもllama.cppはCPUで動作しますが、推論速度は10倍以上の差が出ます。

Windowsユーザーであれば、NVIDIA製のRTX 3060（12GB版）やRTX 4060 Ti（16GB版）がコストパフォーマンスに優れています。
RTX 4090を2枚挿している私の環境では、量子化モデルならほぼ一瞬でレスポンスが返ってきますが、まずは手持ちの機材で試すべきです。
Macユーザーの場合は、Apple Silicon（M1/M2/M3）のユニファイドメモリが強力な武器になります。
メモリ（RAM）が16GB以上あれば、Llama 3 8Bクラスのモデルは非常にスムーズに動きます。

料金面では、完全にローカルで完結するため、電気代を除けばAPI使用料などのランニングコストは0円です。
クラウドGPU（Lambda LabsやRunPodなど）を使う選択肢もありますが、1時間あたり$0.4〜$0.8程度のコストがかかります。
長期的に検証や開発を行うのであれば、初期投資として数万円のGPUを購入したほうが、最終的な学習コストは安く済みます。

## なぜこの方法を選ぶのか

LLMを動かす手法は、Transformersライブラリを使う方法やOllamaを使う方法など、いくつか存在します。
その中で私がllama.cppを推奨するのは、圧倒的な「ポータビリティ」と「メモリ効率」が理由です。

Pythonベースのライブラリは、依存関係が複雑でライブラリのバージョン競合に悩まされることが多々あります。
一方、llama.cppはピュアなC++で書かれており、一度ビルドしてしまえば環境を汚さずに使い続けることが可能です。
また、GGUF（GPT-Generated Unified Format）というフォーマットにより、重みの量子化（圧縮）が容易です。
本来なら数十GBのVRAMを必要とするモデルを、わずか5GB程度のメモリで、しかも高い精度を維持したまま動かせるのは大きな利点です。

「とりあえず動けばいい」ならOllamaで十分ですが、「仕事で使うシステムの裏側に組み込みたい」「細かいパラメータを調整して最適化したい」なら、llama.cpp一択です。

## Step 1: 環境を整える

まずはllama.cppを自分のPCで動かせる状態にします。
ソースコードからコンパイルすることで、自分のマシンのCPU/GPU命令セットに最適化されたバイナリを生成します。

### Mac（Apple Silicon）の場合
ターミナルを開き、以下のコマンドを順に実行してください。

```bash
# リポジトリのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド（Metalを使用するように設定）
cmake -B build -DGGML_METAL=ON
cmake --build build --config Release
```

### Windows（NVIDIA GPU使用）の場合
CMakeとVisual Studioのビルドツールがインストールされている必要があります。

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build
cd build

# CUDAを有効化してビルド
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release
```

各コマンドの意味を解説します。
`git clone`は最新のソースコードを手元に持ってくる作業です。
`cmake`の工程では、Macなら「Metal（Apple GPU）」、Windowsなら「CUDA（NVIDIA GPU）」を使うようにフラグを立てています。
これにより、重い計算をCPUではなくGPUに肩代わりさせ、高速なレスポンスを実現します。

⚠️ **落とし穴:**
Windowsで`GGML_CUDA=ON`を指定してもエラーが出る場合、CUDA Toolkitが正しくインストールされていない、あるいはパスが通っていないケースがほとんどです。
`nvcc --version`コマンドを叩いて、バージョン情報が表示されるか事前に確認してください。
表示されない場合は、NVIDIA公式サイトから最新のCUDA Toolkitをインストールし、PCを再起動してからやり直してください。

## Step 2: 基本の設定

ビルドが完了したら、次に「脳」にあたるモデルファイルを用意します。
今回は汎用性が高く、日本語能力も高い「Llama-3-8B-Instruct」のGGUF版を使用します。

自分ですべてを量子化するのは時間がかかるため、まずはコミュニティが公開している変換済みモデルを利用するのが効率的です。
「Bartowski」氏や「MaziyarPanahi」氏などがHugging Face上で公開しているGGUFリポジトリを探してください。

1. [Hugging Face](https://huggingface.co/models?search=Llama-3-8B-GGUF)でモデルを探す。
2. `Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf`のようなファイルを選択する。
3. llama.cppディレクトリ内に`models`フォルダを作成し、そこに保存する。

ここで「Q4_K_M」という名前が出てきましたが、これは量子化の方式を指します。
「Q4」は4ビット量子化を意味し、元のFP16（16ビット）に比べてファイルサイズを約1/4に抑えています。
「Q4_K_M」は精度とサイズのバランスが最も良く、実務で使うならこれがデファクトスタンダードです。
「Q2」などはサイズは小さいですが、知能が著しく低下するため、特別な理由がない限り避けましょう。

## Step 3: 動かしてみる

準備が整ったので、まずはコマンドラインから動作確認を行います。
先ほどビルドしたバイナリを使用して、モデルに質問を投げます。

```bash
# Macの場合
./build/bin/llama-cli -m models/Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf -p "日本の首都はどこですか？" -n 128

# Windowsの場合
./build/bin/Release/llama-cli.exe -m models/Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf -p "日本の首都はどこですか？" -n 128 --n-gpu-layers 33
```

### 期待される出力

```text
日本の首都は東京です。東京は政治、経済、文化の中心地であり...
```

Windows環境でGPUを使っている場合、`--n-gpu-layers 33`（または`-ngl 33`）という引数が非常に重要です。
これは、モデルのレイヤーをいくつGPUにオフロード（転送）するかを指定する数値です。
Llama-3-8Bの場合、全レイヤーが33層程度なので、33を指定すればモデルのすべてがVRAMに乗り、高速に動作します。
この指定を忘れると、せっかくGPUを持っていてもCPUで計算が行われ、レスポンスが極端に遅くなります。

## Step 4: 実用レベルにする

CLIでの動作が確認できたら、次はPythonからこのモデルを制御できるようにします。
これにより、自分のアプリやBotのバックエンドとしてLLMを組み込むことが可能になります。

`llama-cpp-python`というライブラリを使用します。
これはllama.cppをPythonから呼び出すための薄いラッパーで、OpenAI互換のAPIサーバーを立てることも可能です。

```python
# ライブラリのインストール（GPUサポート付き）
# Macの場合
# CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python

# Windows (CUDA)の場合
# $env:CMAKE_ARGS="-DGGML_CUDA=on"; pip install llama-cpp-python

import os
from llama_cpp import Llama

# モデルのパスを指定
model_path = "./models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"

# AIの初期化
# n_gpu_layers=-1 は「すべてのレイヤーをGPUに送る」という意味
llm = Llama(
    model_path=model_path,
    n_gpu_layers=-1,
    n_ctx=2048, # コンテキストウィンドウ（記憶の長さ）
)

def ask_ai(prompt):
    # 推論の実行
    output = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": "あなたは優秀なアシスタントです。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7, # 自由度（0.0で固定、高いほど創造的）
        max_tokens=500
    )

    # 返答を抽出
    return output["choices"][0]["message"]["content"]

# 実機テスト
if __name__ == "__main__":
    question = "Pythonでハローワールドを書くコードを教えて"
    print(f"質問: {question}")
    response = ask_ai(question)
    print(f"AIの回答:\n{response}")
```

このコードのポイントは、`n_gpu_layers=-1`の設定です。
モデルのレイヤー数を手動で数えるのは面倒なので、`-1`を指定することで自動的にすべてのレイヤーをGPUに割り当ててくれます。
また、`n_ctx`（コンテキストサイズ）はデフォルトでは512と短いことが多いです。
実務で長文を扱いたい場合は、ここを`2048`や`4096`に設定しますが、増やしすぎるとVRAMを激しく消費するため注意が必要です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `error loading model` | GGUFファイルの破損またはパスミス | モデルのダウンロードをやり直すか、相対パスが正しいか確認する |
| `CUDA error: out of memory` | VRAM容量不足 | `n_gpu_layers`の値を減らすか、より小さい（量子化ビット数の低い）モデルを使う |
| 推論速度が異常に遅い | GPUが使われていない | ビルド時にCUDA/Metalフラグを立てているか、`n_gpu_layers`を指定しているか再確認 |
| Pythonでimportエラー | インストール失敗 | `pip uninstall llama-cpp-python`してから、CMAKE_ARGSを正しく設定して再実行 |

## 次のステップ

ここまでで、自分のPC上でAIを自由に動かす「土台」が完成しました。
この次に挑戦すべきは、以下の3つの方向性です。

1. **RAG（検索拡張生成）の実装**:
自分のメモ帳や社内ドキュメント（PDF）を読み込ませて、その内容に基づいて回答する仕組みを作ってみてください。
`langchain`や`LlamaIndex`といったライブラリを使えば、llama-cpp-pythonと連携させて比較的簡単に構築できます。

2. **マルチモーダルへの挑戦**:
最近のllama.cppは画像認識モデル（LLaVAなど）にも対応しています。
画像ファイルを読み込ませて「この画像には何が写っていますか？」と問いかけるスクリプトを作ると、応用の幅が一気に広がります。

3. **APIサーバーとしての運用**:
`llama-cpp-python[server]`をインストールすれば、OpenAI互換のAPIサーバーを数秒で立ち上げられます。
これにより、CursorやAiderといった開発支援ツールから、自前のローカルLLMを呼び出してコードを書かせることができるようになります。

ローカルLLMの世界は日進月歩ですが、llama.cppという基本を押さえておけば、どんな新しいモデルが出てもすぐに対応できるようになります。
まずは今回のスクリプトをベースに、自分専用のAIツールを作り始めてみてください。

## よくある質問

### Q1: VRAMが足りない場合、モデルを動かすことは全く不可能ですか？

いいえ、可能です。llama.cppは「重みの一部をGPU、残りをメインメモリ（RAM）」に分散して配置できます。
`n_gpu_layers`の値を調整して、GPUに乗る分だけをオフロードすれば、速度は落ちますが動作は継続します。

### Q2: 4bit量子化（Q4_K_M）にすると、どのくらい賢さが落ちますか？

体感的な低下はわずかです。
一般的な用途（プログラミング補助や要約）であれば、FP16（無圧縮）との差を人間が判別するのは困難なレベルにあります。
VRAMを節約して高速化するメリットの方が圧倒的に大きいです。

### Q3: 最新のLlama 3.1やGoogleのGemma 2なども同じ手順で動きますか？

はい、基本的には同じです。
新しいモデルが登場した直後は、llama.cppのリポジトリを`git pull`して最新版を再ビルドする必要があります。
開発陣の対応が非常に速いため、モデル発表から数時間後にはGGUFで動かせるようになっていることが多いです。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3 8Bクラスを余裕を持って動かせる入門最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cpp 使い方 入門：GGUF量子化モデルをローカルPCで爆速動作させる方法](/posts/2026-07-16-llamacpp-gguf-local-llm-beginner-guide/)
- [llama.cpp 使い方 入門：GGUF量子化モデルをローカルPCで爆速動作させる全手順](/posts/2026-06-20-llama-cpp-gguf-local-llm-tutorial/)
- [llama.cpp 使い方 入門｜低スペックPCでLlama 3を爆速で動かす実践ガイド](/posts/2026-06-12-llama-cpp-gguf-beginner-guide-python/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "VRAMが足りない場合、モデルを動かすことは全く不可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ、可能です。llama.cppは「重みの一部をGPU、残りをメインメモリ（RAM）」に分散して配置できます。 ngpulayersの値を調整して、GPUに乗る分だけをオフロードすれば、速度は落ちますが動作は継続します。"
      }
    },
    {
      "@type": "Question",
      "name": "4bit量子化（Q4_K_M）にすると、どのくらい賢さが落ちますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "体感的な低下はわずかです。 一般的な用途（プログラミング補助や要約）であれば、FP16（無圧縮）との差を人間が判別するのは困難なレベルにあります。 VRAMを節約して高速化するメリットの方が圧倒的に大きいです。"
      }
    },
    {
      "@type": "Question",
      "name": "最新のLlama 3.1やGoogleのGemma 2なども同じ手順で動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、基本的には同じです。 新しいモデルが登場した直後は、llama.cppのリポジトリをgit pullして最新版を再ビルドする必要があります。 開発陣の対応が非常に速いため、モデル発表から数時間後にはGGUFで動かせるようになっていることが多いです。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでLlama 3 8Bクラスを余裕を持って動かせる入門最適解</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
