---
title: "llama.cpp 使い方 入門 | GGUF量子化モデルをローカルで動かす方法"
date: 2026-11-13T00:00:00+09:00
slug: "llamacpp-gguf-local-llm-guide-for-beginners"
cover:
  image: "/images/posts/2026-11-13-llamacpp-gguf-local-llm-guide-for-beginners.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "ローカルLLM 環境構築"
  - "Python AI 実装"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

自分のPCリソースを最大限に活用して、Llama 3やQwen 2.5などの最新AIを高速に動かすローカル推論環境を構築します。
具体的には、llama.cppをソースからビルドし、GGUF形式の量子化モデルをGPUとCPUのハイブリッドで動かすPythonスクリプトを完成させます。
クラウドAPIを使わず、完全にオフラインで「月額無料・プライバシー重視」のAI基盤を手にすることがこの記事のゴールです。

- 前提知識: 基本的なコマンド操作（cd, git clone等）ができること、Pythonの仮想環境が作れること
- 必要なもの: NVIDIA製GPU（RTX 30シリーズ以降推奨）またはApple Silicon搭載Mac

## 先に確認するスペック・料金

ローカルLLMの世界では「VRAM（ビデオメモリ）」が全てを決めます。
私が検証した結果、7B（70億パラメータ）クラスのモデルを快適に動かすなら、最低でも8GBのVRAMが必要です。
14Bや30Bクラスを狙うなら、RTX 4060 Tiの16GB版や、RTX 3090/4090の24GB版が必須の選択肢になります。

もしあなたがMacユーザーなら、ユニファイドメモリ（メインメモリとVRAMの共用）の恩恵を受けられるため、メモリ16GB以上のモデルを用意してください。
8GBのMacBook Airでも動かなくはないですが、ブラウザを開いた瞬間にスワップが発生し、推論速度が著しく低下します。
自作PCを組むなら、現状はRTX 4060 Ti 16GBがコストパフォーマンスにおいて最強の入門カードだと断言します。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は「Ollama」「LM Studio」など他にもありますが、私は実務においてllama.cppを直接叩く方法を推奨します。
理由は単純で、推論時のパラメータ（コンテキストサイズやGPUレイヤーの割り当て）を最も細かく制御でき、かつ最新モデルへの対応が圧倒的に早いからです。

Ollamaは内部でllama.cppを動かしていますが、ブラックボックス化されている部分が多く、特定のGPUでパフォーマンスが出ない時の切り分けが困難です。
また、Pythonから直接ライブラリとして呼び出す際、llama-cpp-pythonを使えばC++の高速性を維持したまま、業務システムへの組み込みが容易になります。
「とりあえず動く」ではなく「仕事で戦える速度」を出すなら、この構成一択です。

## Step 1: 環境を整える

まずは llama.cpp を自分のマシンに最適化した状態でビルドします。
配布されているバイナリを使うのではなく、自分でビルドすることで、お使いのCPU（AVX2/AVX512）やGPUの命令セットをフル活用できます。

Windows (CUDA利用) の場合は、以下の手順で進めます。
前提として、CUDA Toolkit（12.x推奨）とCMakeがインストールされている必要があります。

```bash
# リポジトリのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド用ディレクトリの作成
mkdir build
cd build

# CMakeでビルド設定（NVIDIA GPUを使うためのフラグを指定）
# -DGGML_CUDA=ON は、GPU推論を有効にするために必須の設定です。
cmake .. -DGGML_CUDA=ON

# コンパイル（マシンスペックに合わせて数分かかります）
cmake --build . --config Release
```

Mac (Apple Silicon) の場合は、デフォルトでMetal（GPU）が最適化されるため、よりシンプルです。

```bash
# Mac向けビルド
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make -j
```

⚠️ **落とし穴:**
Windows環境で `cmake` を実行した際に「CUDAがみつからない」というエラーが出る場合、環境変数 `PATH` にCUDAのbinディレクトリが含まれているか確認してください。
また、Visual Studioの「C++ によるデスクトップ開発」ワークロードが入っていないと、コンパイラ不足で失敗します。
SIer時代、後輩がこの環境構築だけで1日溶かしたのを見てきましたが、大抵はコンパイラのパス設定が原因です。

## Step 2: GGUFモデルの取得

llama.cppで動かすには、モデルを「GGUF」という形式にする必要があります。
自分で変換することも可能ですが、最初は Hugging Face に有志がアップロードしてくれている量子化済みモデルを使うのが賢明です。

「Bartowski」氏や「MaziyarPanahi」氏が公開しているモデルは信頼性が高く、量子化のバリエーションも豊富です。
今回は、日本語能力が高い「Llama-3.1-8B-Instruct」のGGUF版を例に進めます。

ダウンロードすべきファイル（量子化ビット数）の選び方は以下の通りです。
- **Q4_K_M:** 精度と速度のバランスが最高。迷ったらこれ。
- **Q8_0:** ほぼ無劣化だがファイルサイズが大きく、VRAMを食う。
- **IQ4_XS:** 最近のトレンド。さらに圧縮率を高めても精度を維持できる。

ここでは `Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf` をダウンロードし、`models` フォルダに配置したと仮定します。

## Step 3: 動かしてみる

まずはコマンドラインから直接動かして、ビルドが成功しているか、GPUが認識されているかを確認します。

```bash
# 実行コマンドの例（Windows/Linux共通）
./build/bin/Release/llama-cli.exe \
  -m models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf \
  -p "あなたは優秀なエンジニアです。Pythonで素数を判定する関数を書いてください。" \
  -n 512 \
  -ngl 33
```

### 各パラメータの意味と「なぜ」

- `-m`: モデルファイルのパス。
- `-p`: プロンプト。
- `-n`: 生成する最大トークン数。
- `-ngl 33`: **ここが最重要です。** GPUにオフロードするレイヤー数を指定します。Llama-3-8Bの場合、33を指定すると全レイヤーがVRAMに乗ります。一部だけ乗せる場合は数字を減らしますが、推論速度はガクッと落ちます。
- `-c 2048`: コンテキストサイズ（記憶保持量）。デフォルトで足りない場合は増やしますが、その分VRAM消費量も増えます。

### 期待される出力

```text
llama_print_timings: prompt eval time = 120.45 ms / 21 tokens (5.74 ms per token, 174.34 tokens per second)
llama_print_timings:        eval time = 1540.22 ms / 85 tokens (18.12 ms per token, 55.19 tokens per second)
```

「174.34 tokens per second」といった数字が出れば成功です。
実務でストレスなく使える基準は、生成速度（eval time）が 15〜20 tokens/sec 以上だと考えてください。

## Step 4: 実用レベルにする

単発のコマンド実行では仕事に使えません。
Pythonから呼び出せるように `llama-cpp-python` を導入し、APIサーバー化や複雑なスクリプトに対応させます。

```bash
# GPU支援を有効にしてインストール（ここでもフラグが重要）
$env:CMAKE_ARGS="-DGGML_CUDA=ON" # Windowsの場合
pip install llama-cpp-python
```

次に、実用的な推論スクリプトを作成します。

```python
import os
from llama_cpp import Llama

# モデルのパスを指定
model_path = "models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

# 初期化
# n_gpu_layers=-1 にすると、自動的に全レイヤーをGPUに転送します。
# これが最も手軽で、かつミスがない設定です。
llm = Llama(
    model_path=model_path,
    n_gpu_layers=-1,
    n_ctx=4096,      # 開発ドキュメントを読むならこれくらいは欲しい
    verbose=False    # ログがうるさい場合はFalseに
)

def ask_ai(question: str):
    try:
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "あなたは簡潔に回答するプロフェッショナルなアシスタントです。"},
                {"role": "user", "content": question}
            ],
            temperature=0.7, # 自由度。業務利用なら0.1〜0.7程度が安定する
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

if __name__ == "__main__":
    query = "大規模言語モデルをローカルで動かす最大のメリットを3点、箇条書きで教えてください。"
    print(ask_ai(query))
```

このスクリプトのポイントは、`n_gpu_layers=-1` です。
「自分のGPUに何枚レイヤーが乗るか」を計算するのは面倒ですが、`-1` を指定すればライブラリ側がVRAMの限界まで勝手に積んでくれます。
これにより、ハードウェア構成が変わってもコードを修正する必要がなくなります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `CUDA_ERROR_OUT_OF_MEMORY` | 指定したコンテキストサイズやレイヤー数がVRAM容量を超えた | `-c`（コンテキストサイズ）を小さくするか、量子化ビット数を下げる（Q4→Q3など） |
| `Unknown model architecture` | llama.cppのバージョンが古く、最新モデルに対応していない | `git pull` して再ビルドする。llama.cppは更新が非常に激しいです |
| 推論が極端に遅い（0.5 t/sなど） | GPUが使われずCPUだけで動いている | ビルド時に `GGML_CUDA=ON` が効いているか、`n_gpu_layers` が0になっていないか確認 |

## 次のステップ

無事に動いたら、次は「自分だけの知識」を学習させるRAG（検索拡張生成）に挑戦してください。
llama.cppは、単なるチャットボットとしてだけでなく、埋め込みベクトル生成（Embedding）用のサーバーとしても優秀です。

具体的には、LangChainやLlamaIndexと組み合わせて、社内のPDFドキュメントを読み込ませる仕組みを作ってみるのがおすすめです。
クラウドのAPIを使うと「社外秘データが送信される」というリスクで稟議が通りにくいですが、ローカル環境ならセキュリティ担当者を説得するコストを大幅にカットできます。

また、RTX 4090を2枚挿しして、70B（700億パラメータ）クラスのモデルを4ビット量子化で動かせるようになると、世界が変わります。
GPT-4に近い推論能力が自分のデスク上で、電気代だけで動く快感は、一度味わうと戻れません。

## よくある質問

### Q1: ゲーミングノートPCでも動きますか？

動きますが、熱対策が重要です。
LLMの推論はGPUを長時間フル稼働させるため、冷却が不十分だとサーマルスロットリングが発生し、速度が低下します。
また、ノートPCのGPUはVRAMが8GB以下のものが多いため、モデル選びには注意が必要です。

### Q2: 量子化すると精度はどれくらい落ちますか？

私の体感では、Q4_K_M（4ビット相当）であれば、一般的なチャットやコーディング補助において劣化を感じることはほぼありません。
逆にQ2（2ビット）まで下げると、文章の論理構成が崩れたり、同じ言葉を繰り返したりする「ボットらしさ」が目立つようになります。
実務ならQ4以上、理想はQ5やQ6です。

### Q3: llama-cpp-python で APIサーバーを立てるには？

ライブラリに付属しているサーバー機能を使いましょう。
`python -m llama_cpp.server --model models/your_model.gguf` と実行するだけで、OpenAI互換のAPIエンドポイントが立ち上がります。
これにより、CursorやDifyなどの外部ツールから、自前のローカルLLMを簡単に呼び出せるようになります。

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
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3.1等の8Bモデルを全レイヤー余裕を持って載せられる</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cpp 使い方 入門 | GGUF量子化モデルをローカルPCで動かす方法](/posts/2026-09-22-llamacpp-gguf-local-llm-guide/)
- [llama.cpp 使い方 入門：GGUF量子化モデルをローカルPCで爆速動作させる方法](/posts/2026-07-16-llamacpp-gguf-local-llm-beginner-guide/)
- [llama.cppとGGUF量子化でローカルLLMを動かす完全ガイド](/posts/2026-08-22-llamacpp-gguf-local-llm-beginner-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "ゲーミングノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、熱対策が重要です。 LLMの推論はGPUを長時間フル稼働させるため、冷却が不十分だとサーマルスロットリングが発生し、速度が低下します。 また、ノートPCのGPUはVRAMが8GB以下のものが多いため、モデル選びには注意が必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "量子化すると精度はどれくらい落ちますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "私の体感では、Q4KM（4ビット相当）であれば、一般的なチャットやコーディング補助において劣化を感じることはほぼありません。 逆にQ2（2ビット）まで下げると、文章の論理構成が崩れたり、同じ言葉を繰り返したりする「ボットらしさ」が目立つようになります。 実務ならQ4以上、理想はQ5やQ6です。"
      }
    },
    {
      "@type": "Question",
      "name": "llama-cpp-python で APIサーバーを立てるには？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ライブラリに付属しているサーバー機能を使いましょう。 python -m llamacpp.server --model models/yourmodel.gguf と実行するだけで、OpenAI互換のAPIエンドポイントが立ち上がります。 これにより、CursorやDifyなどの外部ツールから、自前のローカルLLMを簡単に呼び出せるようになります。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでLlama 3.1等の8Bモデルを全レイヤー余裕を持って載せられる</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
