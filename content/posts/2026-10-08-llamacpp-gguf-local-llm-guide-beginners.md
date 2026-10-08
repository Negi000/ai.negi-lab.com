---
title: "llama.cpp 使い方 入門 GGUF量子化でローカルLLMを動かす方法"
date: 2026-10-08T00:00:00+09:00
slug: "llamacpp-gguf-local-llm-guide-beginners"
cover:
  image: "/images/posts/2026-10-08-llamacpp-gguf-local-llm-guide-beginners.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "ローカルLLM 構築"
  - "Llama 3 日本語"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

この記事を読むと、MacやWindowsのローカル環境でLlama 3やMistralなどの最新モデルを高速に動かす、自分専用のAIチャットサーバーが構築できます。
PythonからOpenAI互換のAPIとして呼び出せる状態までをゴールにします。

- LLMの実行基盤（llama.cpp）の構築
- GGUF形式の量子化済みモデルの選定と導入
- PythonからローカルLLMを呼び出す推論スクリプト

前提知識として、ターミナル（コマンドプロンプト）の基本操作と、Pythonの基礎的な文法を理解している必要があります。
高度な数学的知識は不要ですが、「パスを通す」といった環境構築の基本作法は求められます。

## 先に確認するスペック・料金

ローカルLLMの世界では、CPU性能よりも「VRAM（ビデオメモリ）の容量」がすべてを決定します。
目安として、Llama 3 8Bクラスを実用的な速度（20〜30 tokens/sec以上）で動かすなら、最低でも8GBのVRAMが必要です。

Macであれば、M1/M2/M3チップ以降を搭載し、メモリが16GB以上あるモデルが理想的です。
Windowsの場合、NVIDIA製のRTX 3060（12GB版）やRTX 4060 Ti（16GB版）が、コストパフォーマンスの面で最強の入門機になります。
私のメイン機はRTX 4090を2枚挿していますが、これは70B以上の巨大モデルを仕事で検証するためです。

もしVRAMが4GBしかない古いPCや、グラボがないPCであっても、llama.cppなら「CPU＋メインメモリ」で動作可能です。
ただし、レスポンスが1秒間に2〜3文字といった「お経」のような速度になる点は覚悟してください。
API利用料は0円ですが、PCの電気代と、最初に投資するハードウェア代が実質的なコストとなります。

## なぜこの方法を選ぶのか

ローカルでLLMを動かすツールは、OllamaやLM Studio、Text-generation-webuiなど数多く存在します。
それらの中で、あえて「llama.cpp」を直接触る方法を選ぶ理由は、圧倒的な「透明性」と「カスタマイズ性」にあります。

Ollamaなどは内部でllama.cppをラップしていますが、細かなパラメータ調整や最新モデルへの対応は、本家llama.cppが最も速いです。
また、Pythonから自作システムに組み込む際、ライブラリの依存関係が極めてシンプルで、本番環境へのデプロイ時に「環境が壊れる」リスクが低いのも大きなメリットです。

GGUFというファイル形式も重要です。
以前のGGML形式とは異なり、モデルのメタデータ（トークナイザーの設定や作者情報）が1つのファイルに完結して保存されています。
「どの設定で動かせばいいかわからない」という迷いが消えるため、実務で使うならGGUF一択です。

## Step 1: 環境を整える

まずはllama.cppをソースからビルドします。
バイナリ配布もありますが、自分のPCのGPU（CUDAやMetal）に最適化させるには、ローカルでのビルドが最強です。

### Mac（Apple Silicon）の場合

Macはデフォルトで「Metal」というGPU加速機構が使えるため、以下の手順で爆速になります。

```bash
# リポジトリをクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド（Apple Silicon最適化）
cmake -B build -DGGML_METAL=ON
cmake --build build --config Release
```

### Windows（NVIDIA GPU）の場合

WindowsかつNVIDIAのグラボを使っている場合は、CUDAを利用する設定でビルドします。
事前に[CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)がインストールされていることが条件です。

```bash
# gitとcmakeがインストールされている前提
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# buildディレクトリを作成して移動
mkdir build
cd build

# CUDAを有効化してビルド
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release
```

ビルドが完了すると、`build/bin/Release`（または `build/bin`）の中に `llama-cli` や `llama-server` といった実行ファイルが生成されます。

⚠️ **落とし穴:**
Windowsでビルドする際、Visual StudioのC++開発環境が入っていないとエラーになります。
「MSVCが見つかりません」といった表示が出たら、Visual Studio Installerから「C++によるデスクトップ開発」にチェックを入れてインストールしてください。
これだけで解決するケースが8割です。

## Step 2: モデルのダウンロードと量子化の理解

次に、動かすためのモデル（脳みそ）を手に入れます。
公式のLlama 3をそのまま落とすと数百GBになりますが、今回は「GGUF形式」に量子化されたものを使います。

Hugging Faceで「Bartowski」氏や「MaziyarPanahi」氏といった著名な職人が公開しているリポジトリを探すのが一番の近道です。
今回は、日本語能力が高い `Llama-3-8B-Instruct` のGGUF版を例にします。

### どの量子化サイズを選べばいいか？

GGUFには `Q4_K_M` や `Q8_0` といった記号がついています。これは「重みのビット数」を表します。

- **Q4_K_M (4-bit):** 私が最も推奨する設定です。ファイルサイズを半分以下に抑えつつ、精度低下は人間が体感できないレベルに留まります。
- **Q8_0 (8-bit):** ほぼ劣化なしですが、ファイルサイズは大きくなります。VRAMに余裕があるなら。
- **IQ2_M (2-bit):** 精度が目に見えて落ちますが、スマホや低スペックPCで無理やり動かす際に使います。

実務では `Q4_K_M` を基準に考え、精度が必要なタスク（要約や論理推論）の時だけビット数を上げるのが賢い選択です。

```bash
# huggingface-cliを使ってダウンロード（例）
pip install huggingface_hub
huggingface-cli download lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF Meta-Llama-3-8B-Instruct-Q4_K_M.gguf --local-dir . --local-dir-use-symlinks False
```

## Step 3: 動かしてみる

いよいよ実行です。
llama.cppには対話モードの `llama-cli` と、サーバーモードの `llama-server` があります。
まずは動作確認のため、CLIで動かしてみましょう。

```bash
# Mac/Linuxの例（パスは環境に合わせて調整してください）
./build/bin/llama-cli \
  -m Meta-Llama-3-8B-Instruct-Q4_K_M.gguf \
  -n 512 \
  -ngl 99 \
  -p "あなたは優秀なアシスタントです。富士山の高さは？"
```

### パラメータの解説：なぜこの値にするのか

- `-m`: モデルファイルのパス。
- `-n 512`: 最大出力トークン数。短すぎると途中で切れます。
- `-ngl 99`: 「GPUにオフロードするレイヤー数」。99という大きな数字を入れることで、モデルの全レイヤーをVRAMに載せるように指示しています。VRAMが足りない場合は、自動で載る分だけ載せてくれます。
- `-p`: プロンプト（入力文）。

### 期待される出力

```text
富士山の高さは、3,776メートルです。日本で最も高い山であり、2013年には世界文化遺産にも登録されました。
```

もしここで「1文字出すのに1秒以上かかる」なら、`-ngl` が効いておらずCPUで動いている可能性があります。
ログを遡り、`BLAS = 1` もしくは `Metal` / `CUDA` の記述があるか確認してください。

## Step 4: 実用レベルにする（Python API連携）

ターミナルで動かすだけでは「動かしてみた」で終わってしまいます。
仕事で使うためには、Pythonからこのモデルを制御できるようにする必要があります。
ここで便利なのが `llama-cpp-python` ライブラリです。

```bash
# CUDA環境の場合のインストール
CMAKE_ARGS="-DGGML_CUDA=ON" pip install llama-cpp-python

# Mac (Metal) の場合
CMAKE_ARGS="-DGGML_METAL=ON" pip install llama-cpp-python
```

このライブラリを使うと、まるでOpenAIのAPIを使っているかのような感覚でローカルLLMを叩けます。

```python
import os
from llama_cpp import Llama

# モデルの初期化
# n_gpu_layers=-1 は全レイヤーをGPUに載せる設定
llm = Llama(
    model_path="./Meta-Llama-3-8B-Instruct-Q4_K_M.gguf",
    n_gpu_layers=-1,
    n_ctx=2048, # コンテキストウィンドウ（記憶できる長さ）
)

# 推論実行
response = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "あなたはプロのプログラマーです。"},
        {"role": "user", "content": "Pythonで素数を判定する関数を書いて。"}
    ],
    temperature=0.7, # 自由度。0に近いほど堅実、1に近いほど創造的
)

print(response["choices"][0]["message"]["content"])
```

### 実務でのポイント：エラーハンドリングとメモリ管理

実務で運用する場合、LLMの初期化（`Llama(...)` の部分）は非常に重い処理です。
リクエストのたびに初期化するのではなく、一度読み込んだインスタンスを使い回すように設計してください。
また、VRAMが不足するとプログラムがクラッシュするため、`try-except` で囲むよりも前に、監視ツール（`nvidia-smi` など）で空き容量を確認する癖をつけましょう。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `error loading model` | GGUFファイルの破損またはパス間違い | ファイルサイズを確認し、絶対パスで指定してみる |
| `out of memory` | VRAM不足 | `-ngl` の値を減らすか、より小さい量子化モデル（Q2_K等）を使う |
| `CMake not found` | ビルドツールの不足 | brew install cmake や 公式インストーラで導入 |
| 回答が文字化けする | プロンプト形式の不一致 | Llama 3専用のテンプレート（<|begin_of_text|>等）を使用する |

## 次のステップ

ここまでできれば、あなたのPCは「オフラインでも動く最強の脳」を手に入れたことになります。
次に挑戦すべきは、以下の3点です。

1. **RAG（検索拡張生成）の実装:** 自分のPDFや社内ドキュメントを読み込ませて、その内容に基づいて回答させる仕組みです。LangChainやLlamaIndexとllama.cppを組み合わせることで実現できます。
2. **OpenAI互換サーバーの起動:** `python -m llama_cpp.server` を実行すれば、既存のCursorやClineといったAIエディタの接続先を自分のPCに変更できます。
3. **長文コンテキストの検証:** `n_ctx` を8192や16384に増やして、どこまで長い文章を一度に扱えるか試してみてください。VRAM消費量が激増するので、その変化を観察するのも勉強になります。

ローカルLLMは、プライバシーが守られるだけでなく、APIコストを気にせず「試行錯誤の回数を無限に増やせる」のが最大の武器です。
まずは1日1回、何かの作業をローカルLLMに投げるところから始めてみてください。

## よくある質問

### Q1: グラボがない普通のノートPCでも動きますか？

動きます。llama.cppの最大の強みはCPU推論の速さです。Llama-3-8BのQ4量子化なら、メモリが8GBあれば動作自体は可能です。ただし、生成速度は1秒間に数文字程度になるため、長い文章の生成には向きません。

### Q2: 実行中にPCが爆音でファンを回し始めました。故障ですか？

正常です。LLMの推論は、行列演算という計算を数千億回繰り返すため、CPUやGPUにフル負荷がかかります。温度が上がりすぎるとサーマルスロットリング（性能低下）が起きるので、冷却台などを使うのがおすすめです。

### Q3: GGUFモデルはどこで探すのが一番安全ですか？

Hugging Face（huggingface.co）というサイトで、モデル名に「GGUF」を加えて検索してください。投稿者のダウンロード数やライク数を確認し、公式または評価の高い「Bartowski」氏などのアカウントから入手するのが定石です。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでこの価格帯はローカルLLM入門に最も現実的な選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cpp 使い方 入門：GGUF量子化モデルをローカルPCで爆速動作させる全手順](/posts/2026-06-20-llama-cpp-gguf-local-llm-tutorial/)
- [llama.cpp 使い方 入門 | GGUF量子化モデルをローカルPCで動かす方法](/posts/2026-09-22-llamacpp-gguf-local-llm-guide/)
- [llama.cpp 使い方 入門：GGUF量子化モデルをローカルPCで爆速動作させる方法](/posts/2026-07-16-llamacpp-gguf-local-llm-beginner-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "グラボがない普通のノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きます。llama.cppの最大の強みはCPU推論の速さです。Llama-3-8BのQ4量子化なら、メモリが8GBあれば動作自体は可能です。ただし、生成速度は1秒間に数文字程度になるため、長い文章の生成には向きません。"
      }
    },
    {
      "@type": "Question",
      "name": "実行中にPCが爆音でファンを回し始めました。故障ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "正常です。LLMの推論は、行列演算という計算を数千億回繰り返すため、CPUやGPUにフル負荷がかかります。温度が上がりすぎるとサーマルスロットリング（性能低下）が起きるので、冷却台などを使うのがおすすめです。"
      }
    },
    {
      "@type": "Question",
      "name": "GGUFモデルはどこで探すのが一番安全ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Hugging Face（huggingface.co）というサイトで、モデル名に「GGUF」を加えて検索してください。投稿者のダウンロード数やライク数を確認し、公式または評価の高い「Bartowski」氏などのアカウントから入手するのが定石です。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">GeForce RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでこの価格帯はローカルLLM入門に最も現実的な選択肢</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
