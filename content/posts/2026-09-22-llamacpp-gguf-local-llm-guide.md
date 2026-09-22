---
title: "llama.cpp 使い方 入門 | GGUF量子化モデルをローカルPCで動かす方法"
date: 2026-09-22T00:00:00+09:00
slug: "llamacpp-gguf-local-llm-guide"
cover:
  image: "/images/posts/2026-09-22-llamacpp-gguf-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "ローカルLLM 構築"
  - "Python AI 実装"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

この記事では、オープンソースのライブラリ「llama.cpp」を用いて、Llama 3やMistralといった最新のLLMを自分のPC上で動かす環境を構築します。
最終的には、PythonスクリプトからローカルLLMを呼び出し、外部APIに1円も払わずに「プライベートなAIチャット」ができる状態を目指します。

前提知識として、ターミナル（コマンドプロンプト）での基本操作と、Pythonの環境構築ができることを想定しています。
それ以外の、量子化の仕組みやビルドのコツについては、実務で20件以上の案件をこなしてきた私の経験をベースに解説します。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
結論から言うと、最低でも8GB、快適に動かすなら16GB以上のVRAMを搭載したNVIDIA製GPU（RTX 30シリーズ以降）を推奨します。
Macユーザーであれば、メモリ16GB以上のApple Silicon（M1/M2/M3）があれば、驚くほどスムーズに動作します。

「自分のPCにはGPUがない」という場合でも、llama.cppならCPUだけで動かすことが可能です。
ただし、推論速度は1秒間に1〜2トークン程度（人間が読むより遅い）になる覚悟が必要です。
メモリ（RAM）については、動かしたいモデルのサイズ＋4GB程度の余裕を見てください。
例えば、7B（70億パラメータ）のモデルを4bit量子化した「GGUF形式」であれば、約5GBのメモリを消費します。

料金については、オープンソースソフトウェアを使用するため、電気代を除けば完全に無料です。
クラウドのGPUインスタンスを借りる場合は、A100などで1時間あたり数百円かかりますが、自前のRTX 4090であれば、初期投資（約30万円）だけで、24時間365日動かし放題になります。
仕事で使うなら、この「情報の秘匿性」と「ランニングコストゼロ」のメリットは、初期投資を数ヶ月で回収できるレベルの価値があります。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は、他にも「Ollama」や「Python + Transformers」などがあります。
しかし、私が実務で「llama.cpp」を最優先で選ぶ理由は、圧倒的な「軽量さ」と「移植性」にあります。

Pythonのライブラリ（Transformers）は、依存関係が非常に重く、PyTorchのバージョン管理だけで1日潰れることも珍しくありません。
一方でllama.cppはC++で書かれており、単一の実行ファイル、あるいはシンプルな共有ライブラリとして動作します。
また、Apple Siliconの「Metal」やNVIDIAの「CUDA」を最大限に引き出す最適化が施されており、同じハードウェアでもPython経由より2〜3倍速いレスポンス（0.1秒以下の初動）が得られることもあります。

さらに、独自フォーマットの「GGUF」が秀逸です。
これは重みデータだけでなく、モデルの設定やボキャブラリを一つのファイルに同梱できる形式で、ファイル一つコピーすれば他の環境でも同じように動くという、配布のしやすさが実務では非常に重宝します。

## Step 1: 環境を整える

まずは、llama.cppを自分のPCでビルド（コンパイル）します。
「配布されている実行ファイルを使えばいいのでは？」と思うかもしれませんが、自分のPCのCPU（AVX512対応など）やGPU（CUDAコア数）に最適化してビルドするのが、速度を出すための鉄則です。

Windows（CUDA利用を想定）の場合は、以下の手順で進めます。

```bash
# リポジトリのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド用ディレクトリの作成
mkdir build
cd build

# CMakeでビルド設定（CUDAを有効化）
# -DGGML_CUDA=ON を指定することでGPUをフル活用します
cmake .. -DGGML_CUDA=ON

# ビルド実行（PCのスペックに合わせて数分かかります）
cmake --build . --config Release
```

Mac（Apple Silicon）の場合は、`-DGGML_METAL=ON` を指定するか、標準で最適化されるため単純に `make` を実行するだけでも十分なパフォーマンスが出ます。

⚠️ **落とし穴:**
Windowsユーザーで「cmakeが見つかりません」というエラーが出る場合は、Visual Studioの「C++によるデスクトップ開発」ワークロードがインストールされているか確認してください。
また、CUDA ToolkitがインストールされていないとGPU版は作れません。
私は最初、これを知らずにビルドして「GPUを積んでいるのにCPUでしか動かない」と3時間ほど悩みました。必ず `nvidia-smi` コマンドでCUDAが入っているか確認してください。

## Step 2: 基本の設定

次に、動かしたいLLMのモデルデータをダウンロードします。
今回は、日本語能力が高く、ローカルでも扱いやすい「Llama-3-8B-Instruct」をベースにした量子化モデルを使います。

Hugging Faceで「[モデル名] GGUF」と検索すると、多くの有志が変換済みモデルを公開しています。
私はいつも「Bartowski」氏や「MaziyarPanahi」氏がアップロードしているファイルを利用しています。

ダウンロードすべきファイル（量子化ビット数）の選び方は、以下の基準で決めてください。

- **Q4_K_M:** 迷ったらこれ。精度とサイズのバランスが最強。VRAM消費も抑えめ。
- **Q8_0:** ほぼ無劣化だが、ファイルサイズが倍になる。VRAMに余裕があるなら。
- **IQ2_M:** 極限まで削ったもの。スマホで動かしたい時以外は非推奨。

ダウンロードした `.gguf` ファイルは、`llama.cpp/models` ディレクトリに配置します。

## Step 3: 動かしてみる

ビルドが完了し、モデルが用意できたら、まずはCLI（コマンドラインインターフェース）で動作確認をします。
ここでは、単に動かすだけでなく「GPUにどれだけ処理をオフロードするか」の指定が肝になります。

```bash
# build/bin/Release に生成された llama-cli を実行（パスは環境に合わせて調整）
./llama-cli -m models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf \
  -n 512 \
  --color \
  -ngl 33 \
  -p "あなたは優秀なアシスタントです。富士山の高さは？"
```

### 期待される出力

```
富士山の高さは、3,776.12メートルです。日本で最も高い山であり、ユネスコの世界遺産にも登録されています。
```

ここで重要なオプションが `-ngl 33`（--n-gpu-layers）です。
これは「LLMの層（レイヤー）のうち、いくつをGPUに任せるか」という設定です。
Llama-3-8Bの場合は全33レイヤーなので、33を指定すればモデルの丸ごとすべてがVRAMに乗り、爆速で推論が始まります。
VRAMが足りない場合は、この数字を「20」や「10」に減らすことで、GPUとCPUの「ハイブリッド推論」が可能になります。
これがllama.cppが「神」と呼ばれる最大の理由です。

## Step 4: 実用レベルにする

CLIで動くだけでは実務には使えません。
Pythonからライブラリとして呼び出し、既存のシステムに組み込めるようにしましょう。
ここでは `llama-cpp-python` という便利なラッパーライブラリを使います。

```bash
# CUDA対応版をインストール（ここを間違えるとCPU動作になり遅い）
$env:CMAKE_ARGS="-DGGML_CUDA=on"
pip install llama-cpp-python
```

以下は、チャット形式でLLMと対話するためのPythonスクリプトです。

```python
import os
from llama_cpp import Llama

# モデルのパスを指定（Step 2で保存した場所）
model_path = "./models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"

# モデルの初期化
# n_gpu_layers=-1 は「全レイヤーをGPUに載せる」という指定です。便利。
llm = Llama(
    model_path=model_path,
    n_gpu_layers=-1,
    n_ctx=2048, # コンテキストウィンドウ（記憶できる長さ）
)

def ask_ai(prompt):
    # Llama 3のテンプレートに合わせたフォーマット
    full_prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

    response = llm(
        full_prompt,
        max_tokens=512,
        stop=["<|eot_id|>"],
        echo=False
    )

    return response["choices"][0]["text"]

# 実行
if __name__ == "__main__":
    question = "PythonでWebスクレイピングをする際の注意点を3つ教えて"
    print(f"質問: {question}")
    answer = ask_ai(question)
    print(f"回答: {answer}")
```

このコードのポイントは `n_gpu_layers=-1` です。
実務でサーバーにデプロイする際、GPUの型番によってレイヤー数が変わるのが面倒ですが、`-1` を指定しておけば、そのハードウェアで可能な限りGPUを使ってくれます。
また、`stop` 引数にモデル固有の終了トークン（`<|eot_id|>`など）を入れないと、AIが一人二役で会話を続けてしまう「暴走」が起きるので注意してください。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `CUDA not found` | システムにCUDA Toolkitが入っていない | NVIDIA公式サイトからインストールしパスを通す |
| `Out of memory` | VRAM容量に対してモデルが大きすぎる | `n_gpu_layers` を減らすか、より高い量子化（Q4→Q2）を使う |
| 回答が文字化けする | プロンプトテンプレートが間違っている | 使用するモデルの公式ドキュメントで推奨テンプレートを確認する |
| 推論が極端に遅い | `CMAKE_ARGS` を指定せずにpip installした | 一度アンインストールし、環境変数を設定して再インストールする |

## 次のステップ

ここまでで、あなたのPC上でLLMが自由に動くようになりました。
次に挑戦すべきは「RAG（検索拡張生成）」の構築です。
llama.cppにはローカルサーバーを立ち上げる機能（`llama-server`）もあり、これを使うと、まるでOpenAIのAPIを使っているかのような感覚で、自作アプリからローカルLLMを叩けるようになります。

また、DifyやOpen WebUIといったツールと連携させれば、コードを一行も書かずに「自分専用のChatGPT」をGUIで構築することも可能です。
「クラウドAIにデータを送れない」という制約がある法人の現場では、この llama.cpp + Dify の組み合わせが現在、最強のソリューションになっています。

まずは、自分の興味のある分野のPDFを読み込ませて、それについて回答してくれる「ローカルナレッジベース」を作ってみてください。
APIの課金メーターを気にせず、100回でも1000回でもテストできる楽しさを知ると、もうクラウドには戻れなくなりますよ。

## よくある質問

### Q1: AMDのGPU（Radeon）でも動きますか？

はい、動きます。ビルド時に `GGML_HIPBLAS=ON` を指定することで、AMDのROCmプラットフォームを利用できます。ただし、CUDAに比べると環境構築の難易度は少し高く、情報の少なさに苦労するかもしれません。

### Q2: 7Bモデルと70Bモデル、どちらを使うべきですか？

個人のPC（VRAM 8-16GB）なら7B一択です。70Bを量子化して動かすにはVRAMが30GB〜40GB必要になります。RTX 3090/4090の2枚挿し構成にすれば、70Bもサクサク動きますが、まずは7Bで「動かすコツ」を掴むのが得策です。

### Q3: GGUFファイルは自分で作れますか？

可能です。llama.cppのリポジトリに含まれる `convert_hf_to_gguf.py` を使えば、Hugging Faceにある通常のモデル（Safetensors形式）をGGUFに変換できます。お気に入りの最新モデルがまだGGUF化されていない時は、自分で変換するのも一つの手です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3等の8Bモデルを余裕を持ってフルロードでき、コスパ最強です</p>
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
      "name": "AMDのGPU（Radeon）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、動きます。ビルド時に GGMLHIPBLAS=ON を指定することで、AMDのROCmプラットフォームを利用できます。ただし、CUDAに比べると環境構築の難易度は少し高く、情報の少なさに苦労するかもしれません。"
      }
    },
    {
      "@type": "Question",
      "name": "7Bモデルと70Bモデル、どちらを使うべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "個人のPC（VRAM 8-16GB）なら7B一択です。70Bを量子化して動かすにはVRAMが30GB〜40GB必要になります。RTX 3090/4090の2枚挿し構成にすれば、70Bもサクサク動きますが、まずは7Bで「動かすコツ」を掴むのが得策です。"
      }
    },
    {
      "@type": "Question",
      "name": "GGUFファイルは自分で作れますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。llama.cppのリポジトリに含まれる converthftogguf.py を使えば、Hugging Faceにある通常のモデル（Safetensors形式）をGGUFに変換できます。お気に入りの最新モデルがまだGGUF化されていない時は、自分で変換するのも一つの手です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでLlama 3等の8Bモデルを余裕を持ってフルロードでき、コスパ最強です</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
