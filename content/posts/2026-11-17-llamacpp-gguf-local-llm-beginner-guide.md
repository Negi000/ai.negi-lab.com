---
title: "llama.cpp 使い方 入門 | 低スペックPCで最新AIを動かす方法"
date: 2026-11-17T00:00:00+09:00
slug: "llamacpp-gguf-local-llm-beginner-guide"
cover:
  image: "/images/posts/2026-11-17-llamacpp-gguf-local-llm-beginner-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "Llama 3 ローカル"
  - "llama-cpp-python 入門"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

自分のPCリソースだけで動作し、外部APIに頼らずに日本語で対話ができる「ローカルLLMチャットサーバー」を構築します。
Pythonの複雑な環境構築をスキップして、C++ベースの高速な実行エンジンであるllama.cppを使い、最新のLlama 3などのモデルを動かします。

- 前提知識: 基本的なコマンドライン操作（cd, mkdir程度）ができること
- 必要なもの: ネット接続、8GB以上のメモリを搭載したPC（Mac/Windows/Linux）

## 先に確認するスペック・料金

ローカルLLMを動かす上で最も重要なのは「VRAM（ビデオメモリ）」と「メインメモリ（RAM）」の容量です。
結論から言うと、最近の軽量なモデル（8Bパラメータ前後）を動かすなら、最低でも16GBのメモリがあれば快適に動きます。
8GBでも動かないことはないですが、推論速度が極端に落ちる、あるいはOSごとフランクするリスクがあるため注意が必要です。

ハードウェアについて、NVIDIA製のGPU（RTX 3060 12GBや4060 Ti 16GBなど）があれば最高ですが、Apple Silicon（M1/M2/M3）のMacも非常に優秀です。
Macの場合はメインメモリがVRAMとして共有されるため、メモリ32GB以上のMacBookがあれば、かなりのサイズのモデルがサクサク動きます。
逆に、内蔵グラフィックスのみの一般的なWindowsノートPCだと、CPU推論になるため「1秒に数文字」程度の速度になることを覚悟してください。

費用面では、llama.cppも配布されているモデルも基本無料（オープンソース）です。
電気代以外にランニングコストはかかりませんが、本気で運用するなら、私はRTX 4090などのハイエンドGPUへの投資を強くおすすめします。
VRAM 24GBという壁を超えると、量子化なしの精度の高いモデルが仕事で使えるレベルの速度で動くようになるからです。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす方法は、PythonでTransformersライブラリを使う方法や、Ollamaを使う方法など、いくつか選択肢があります。
その中で私が「llama.cpp」と「GGUF形式」の組み合わせを推す理由は、圧倒的な「軽量さ」と「汎用性」にあります。

Python版のTransformersは、ライブラリの依存関係が非常に複雑で、CUDAのバージョンが合わずに1日潰すことがザラにあります。
対してllama.cppはC++で書かれた単一のバイナリ（実行ファイル）として動作するため、環境を汚さず、かつメモリ効率が極めて高いのが特徴です。
また、GGUFというファイル形式は、重たいAIモデルを「量子化（データの圧縮）」して、本来なら数十GB必要なモデルを数GBにまで軽量化できます。
この「手軽に試せて、かつ本番環境でも高速に動く」というバランスが、実務においてllama.cppを選ぶ最大の決め手になります。

## Step 1: 環境を整える

まずはllama.cppを自分のPCで動かせる状態にします。
今回は、最も汎用性が高く、かつ最新の最適化を享受できる「ソースコードからのビルド」を行います。

Windowsの場合は「Git for Windows」と「CMake」が必要です。
Macの場合は「Xcode Command Line Tools」が入っていれば十分です。

```bash
# llama.cppのリポジトリをクローンする
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド用ディレクトリを作成して移動
mkdir build
cd build

# ビルドを実行（Macの場合、あるいは一般的なCPUのみのPCの場合）
cmake ..
cmake --build . --config Release
```

もしあなたがNVIDIAのGPU（CUDA環境）を持っているなら、以下のコマンドでGPU支援を有効にしてビルドしてください。

```bash
# NVIDIA GPUがある場合（CUDA利用）
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release
```

落とし穴として、WindowsユーザーがCMakeを実行する際、「コンパイラが見つかりません」というエラーが出ることがよくあります。
これはVisual Studioの「C++によるデスクトップ開発」ワークロードがインストールされていないことが原因です。
無料のVisual Studio Community版を入れて、このチェックボックスにチェックを入れるだけで解決します。

## Step 2: モデルの入手（GGUF量子化済み）

llama.cppを動かすには、モデルファイルが必要です。
今回は、Metaが公開している最強の小型モデル「Llama-3-8B」の日本語最適化版を、GGUF形式でダウンロードします。
私がよく利用しているのは、コミュニティで高い信頼を得ている「Bartowski」氏や「MaziyarPanahi」氏が公開しているリポジトリです。

モデルを選ぶ際の基準は「Q4_K_M」というキーワードです。
これは4ビット量子化を意味し、モデルの精度をほぼ維持したまま、ファイルサイズを半分以下に抑えたバランスの良い設定です。

```bash
# llama.cppのディレクトリ内にモデル保存用フォルダを作る
mkdir models

# Hugging Faceからモデルをダウンロード（ここでは例としてLlama-3-8B-Instruct-v0.1のGGUF）
# ※実際にはブラウザでダウンロードして models/ フォルダに配置するのが確実です。
```

落とし穴として、モデルのファイルサイズを甘く見ないでください。
8BモデルのQ4_K_M量子化版で、約5GB〜6GBの容量があります。
ダウンロードが途中で止まるとファイルが破損し、実行時に「magic number mismatch」というエラーが出るので、必ずファイルサイズを確認しましょう。

## Step 3: 動かしてみる

準備が整ったら、まずはコマンドラインから直接対話をしてみます。
ビルドして生成された `llama-cli`（以前は `main` という名前でした）を使います。

```bash
# コマンドラインでの実行
./bin/llama-cli -m ../models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf \
  -p "あなたは優秀なアシスタントです。日本の美味しい食べ物を3つ教えてください。" \
  -n 512 \
  -ngl 33
```

各オプションの意味は以下の通りです。
- `-m`: 使用するモデルファイルのパス。
- `-p`: モデルへの指示（プロンプト）。
- `-n`: 生成する最大トークン数。512程度あれば十分な回答が得られます。
- `-ngl`: GPUにオフロードするレイヤー数。これを指定しないとCPUだけで動くため非常に遅いです。Llama-3-8Bの場合は33を指定すれば全レイヤーがGPUに乗ります。

### 期待される出力

```text
日本の美味しい食べ物を3つご紹介します。
1. 寿司：新鮮な魚介類と酢飯の組み合わせは絶品です。
2. ラーメン：地域ごとに多様なスープと麺のバリエーションがあります。
3. お好み焼き：キャベツと生地を焼き上げた「日本のピザ」とも呼ばれるソウルフードです。
```

もし出力が「支離滅裂な文字」になる場合は、プロンプトの形式（テンプレート）が間違っている可能性があります。
Llama 3には特定のタグ（`<|begin_of_text|>`など）が必要ですが、llama-cliが自動で調整してくれることが多いです。

## Step 4: 実用レベルにする（Python API化）

コマンドラインで動かすだけでは実務に使えません。
自分のシステムに組み込むために、Pythonからllama.cppを呼び出せるようにしましょう。
ここでは `llama-cpp-python` という便利なライブラリを使います。

```bash
# ライブラリのインストール
# GPUを使う場合は CMAKE_ARGS="-DGGML_CUDA=ON" を付けてインストールする必要があります
pip install llama-cpp-python
```

次に、Pythonスクリプトを作成します。
ここでは、後でWebアプリなどに組み込みやすいように、クラス化した実装を紹介します。

```python
import os
from llama_cpp import Llama

class LocalLLMHandler:
    def __init__(self, model_path):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"モデルが見つかりません: {model_path}")

        # モデルの初期化
        # n_gpu_layers=-1 は「可能な限り全てのレイヤーをGPUに載せる」設定
        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,
            n_ctx=2048, # コンテキストウィンドウ（記憶できる長さ）
            verbose=False
        )

    def generate_response(self, prompt):
        # Llama 3のプロンプト形式に合わせる（簡易版）
        full_prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

        output = self.llm(
            full_prompt,
            max_tokens=512,
            stop=["<|eot_id|>"], # 停止トークンの指定
            echo=False
        )
        return output["choices"][0]["text"]

# 実行例
if __name__ == "__main__":
    MODEL_PATH = "./models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"
    handler = LocalLLMHandler(MODEL_PATH)

    answer = handler.generate_response("PythonでHello Worldを書くコードを教えて。")
    print(answer)
```

このコードのポイントは `n_gpu_layers=-1` です。
これまでは手動でレイヤー数を数えていましたが、最新のライブラリでは `-1` を指定するだけで自動で最大までGPUを使ってくれます。
また、`stop` 引数にモデル固有の終了タグを入れることで、AIが一人で会話を延々と続けてしまう「暴走」を防いでいます。

仕事で使う場合、このスクリプトをFastAPIなどのWebフレームワークでラップすれば、社内専用のセキュアなAIチャットAPIが完成します。
データが外部（OpenAIなど）に送信されないため、機密情報を扱う業務でも安心して導入できるのが最大のメリットです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `error loading model: format not supported` | モデルのファイル形式が古い | llama.cppのバージョンを上げるか、最新のGGUFファイルを再ダウンロードする |
| `out of memory` (CUDA error) | VRAMが不足している | `-ngl` の値を減らして一部をCPUに逃がすか、より小さい量子化（Q3_Kなど）を使う |
| `llama-cli` が見つからない | ビルドに失敗しているか、パスが違う | `build/bin/` ディレクトリの中を確認する。Windowsは `.exe` が付いているか確認 |
| 推論がめちゃくちゃ遅い | GPUが使われていない | ビルド時に `GGML_CUDA=ON` を忘れていないか確認。実行時に `n_gpu_layers` を指定しているか確認 |

## 次のステップ

llama.cppでローカルLLMを動かせるようになったら、次は「RAG（検索拡張生成）」に挑戦してみてください。
自分の持っているPDFやテキストファイルをAIに読み込ませて、その内容に基づいて回答させる仕組みです。
ローカルLLMとRAGを組み合わせれば、完全にオフラインで動作する「自社専用のナレッジベース」が構築できます。

また、より高速な推論を求めるなら「vLLM」や「TensorRT-LLM」という選択肢もありますが、これらはLinux環境と強力なGPUを前提とします。
まずはこのllama.cppで「モデルのサイズによる回答精度の違い」や「量子化による速度変化」を体感し、自分の用途に最適なスペックを見極めるのが、遠回りに見えて一番の近道です。
私は自宅のRTX 4090サーバーで、常に複数のモデルを検証していますが、やはり「とりあえず動かす」ならllama.cppが今でも最強のツールだと思っています。

## よくある質問

### Q1: ゲーミングPCではない普通のノートPCでも動きますか？

動きますが、速度は期待しないでください。1秒間に1〜2文字程度の生成速度になることが多いです。ただし、GGUFの「Q2_K」などの極端な量子化モデルを使えば、メモリ消費をさらに抑えて動かすことは可能です。

### Q2: どのモデルをダウンロードすればいいか分かりません

まずは「Llama-3-8B-Instruct」のGGUF版を探してください。日本語能力を重視するなら「Llama-3-8B-Japanese-Instruct」といった、日本語で追加学習されたモデルを選ぶと、より自然な回答が得られます。

### Q3: 商用利用は可能ですか？

llama.cpp自体はMITライセンスで自由に使えますが、モデル（Llama 3など）にはそれぞれのライセンスがあります。Metaのライセンスは非常に寛容ですが、月間アクティブユーザー数が数億人を超えるような超大規模サービスで使う場合は個別の許可が必要です。通常のビジネス利用なら問題ありません。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3 8Bクラスを全レイヤーGPUに乗せて高速動作させるのに最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cpp 使い方 入門｜低スペックPCでLlama 3を爆速で動かす実践ガイド](/posts/2026-06-12-llama-cpp-gguf-beginner-guide-python/)
- [llama.cpp 使い方 入門：GGUF量子化モデルをローカルPCで爆速動作させる全手順](/posts/2026-06-20-llama-cpp-gguf-local-llm-tutorial/)
- [llama.cpp 使い方 入門 | GGUF量子化でローカルLLMを動かす](/posts/2026-08-06-llamacpp-gguf-python-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "ゲーミングPCではない普通のノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、速度は期待しないでください。1秒間に1〜2文字程度の生成速度になることが多いです。ただし、GGUFの「Q2K」などの極端な量子化モデルを使えば、メモリ消費をさらに抑えて動かすことは可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "どのモデルをダウンロードすればいいか分かりません",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "まずは「Llama-3-8B-Instruct」のGGUF版を探してください。日本語能力を重視するなら「Llama-3-8B-Japanese-Instruct」といった、日本語で追加学習されたモデルを選ぶと、より自然な回答が得られます。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用は可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "llama.cpp自体はMITライセンスで自由に使えますが、モデル（Llama 3など）にはそれぞれのライセンスがあります。Metaのライセンスは非常に寛容ですが、月間アクティブユーザー数が数億人を超えるような超大規模サービスで使う場合は個別の許可が必要です。通常のビジネス利用なら問題ありません。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでLlama 3 8Bクラスを全レイヤーGPUに乗せて高速動作させるのに最適</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
