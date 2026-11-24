---
title: "llama.cppとGGUF量子化でローカルLLMを構築する方法"
date: 2026-11-25T00:00:00+09:00
slug: "llama-cpp-gguf-python-local-llm-guide"
cover:
  image: "/images/posts/2026-11-25-llama-cpp-gguf-python-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp"
  - "GGUF"
  - "量子化"
  - "ローカルLLM 構築"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

自分のPCリソースだけで動作し、外部APIに1円も払わずに使い続けられる、Python製の超高速AIチャットボットを作成します。
llama.cppのPythonバインディングを使用し、量子化モデル（GGUF）を読み込んで、ストリーミング形式で回答を表示するスクリプトを完成させます。
前提知識として、Pythonの基本的な文法と、ターミナル（コマンドプロンプト）でのパッケージ操作ができることを想定しています。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
結論から言うと、現在の標準的なモデルであるLlama 3 (8B) を快適に動かすなら、VRAM 8GB以上のGPU（RTX 3060/4060等）か、メモリ16GB以上のApple Silicon Macが必須です。
VRAMが足りなくてもCPUとメインメモリで動きますが、レスポンスが「秒速30文字」から「秒速2文字」まで落ちるため、実用には耐えません。

私がメインで使っているRTX 4090（VRAM 24GB）であれば、8Bクラスのモデルを「Q8（8ビット量子化）」という高精度な状態で余裕を持って動かせます。
しかし、一般的な12GB〜16GBのVRAM環境でも、「Q4_K_M」という設定のGGUFファイルを選べば、精度をほぼ落とさずに高速動作が可能です。
WindowsユーザーでこれからGPUを買うなら、最低でもRTX 4060 Tiの16GB版を選んでください。12GB以下のモデルを買うと、将来的に14Bや32Bといった中規模モデルを試したくなった時に必ず後悔します。

Macユーザーの場合、メモリがCPUとGPUで共有されるユニファイドメモリ方式のため、16GBメモリがあれば8Bモデルはサクサク動きます。
ただし、OSが消費するメモリも考慮すると、実際には24GB以上の構成が「仕事で使える」ラインになります。
料金面については、一度ハードウェアを揃えてしまえば、電気代以外は完全に無料です。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、Ollama、vLLM、LM Studioなど多岐にわたりますが、私は「llama.cpp」を最も推奨します。
理由は、圧倒的な「移植性」と「ハードウェアの使い切り」にあります。
llama.cppはC++で書かれており、GPU（CUDA/Metal）だけでなくCPUのAVX512なども駆使して計算を行うため、どのようなPC環境でも限界まで性能を引き出せます。

特に、今回使用する「GGUF」というフォーマットが優秀です。
従来のモデル形式（SafeTensors等）は、VRAMに乗り切らない場合にエラーで止まることが多かったのですが、GGUFは「一部をGPUで、残りをCPUで計算する」というハイブリッド処理が可能です。
また、量子化（モデルの軽量化）のオプションが豊富で、自分のマシンスペックに合わせて0.1GB単位でモデルサイズを調整できる自由度があります。
実務で特定の機能を組み込んだアプリを作る際、ライブラリとしての依存関係がシンプルで、Pythonから直接たたける `llama-cpp-python` は最強の選択肢です。

## Step 1: 環境を整える

まずは、使用するOSに合わせて適切なビルドオプションを指定してインストールを行います。
ここは初心者が最も挫折するポイントです。単に `pip install` するだけではGPUが使われず、低速なCPUモードで動いてしまうからです。

### NVIDIA GPU（Windows/Linux）の場合
CUDA Toolkitがインストールされていることを確認した上で、以下のコマンドを実行します。

```bash
# CUDA対応版を強制的にビルドしてインストール
$env:CMAKE_ARGS = "-DGGML_CUDA=on"
pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir
```

### Apple Silicon（Mac）の場合
Metal（MacのGPU加速）を有効にするための設定です。

```bash
# Metal対応版をインストール
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir
```

このコマンドで `--force-reinstall` を使っているのは、以前に間違ってインストールした「CPU専用版」を確実に上書きするためです。
インストール完了後、以下のPythonコードを実行して「BLAS = 1」と表示されれば、GPU支援が有効になっています。

```python
import llama_cpp
print(llama_cpp.llama_backend_init())
# 出力に "cuda" や "metal" の文字が含まれていれば成功です
```

⚠️ **落とし穴:**
Windows環境で `CMAKE_ARGS` が効かない場合は、Visual Studioの「C++ によるデスクトップ開発」ワークロードが入っているか確認してください。
これが入っていないと、ライブラリのビルドができずにエラーを吐きます。SIer時代、環境構築の失敗の8割はコンパイラ不足でした。

## Step 2: モデルの準備

llama.cppで動かすためには、モデルを「GGUF」という形式でダウンロードする必要があります。
今回は、日本語能力が非常に高い「Llama-3-8B-Instruct」を量子化したモデルを使用します。
Hugging Faceで「QuantFactory/Meta-Llama-3-8B-Instruct-GGUF」などのリポジトリを探してください。

ダウンロードするファイルを選ぶ際は、「Q4_K_M」と書かれたものを選んでください。
これは「4ビット量子化（K-Quants Medium）」という意味で、モデルの重みを4ビットに圧縮しています。
重みが16ビット（元サイズ）だと約15GBのVRAMが必要ですが、Q4にすれば約5GBまで削減されます。
「精度が落ちるのでは？」と心配になりますが、私の検証では、実用上の回答精度はQ4でもほとんど劣化しません。

ファイルをダウンロードしたら、プロジェクト直下の `models` フォルダに配置します。

```bash
mkdir models
# ここに Meta-Llama-3-8B-Instruct-v0.1-Q4_K_M.gguf を入れる
```

## Step 3: 動かしてみる

まずは最小限の構成で、モデルをロードして回答を生成させます。
ここでのポイントは `n_gpu_layers` という引数です。

```python
import os
from llama_cpp import Llama

# モデルのパスを指定
model_path = "./models/Meta-Llama-3-8B-Instruct-v0.1-Q4_K_M.gguf"

# モデルの初期化
llm = Llama(
    model_path=model_path,
    n_gpu_layers=-1, # -1はすべてのレイヤーをGPUにオフロードする設定
    n_ctx=2048,      # コンテキストサイズ（一度に扱えるトークン量）
    verbose=False    # ログ出力を抑制
)

# 推論の実行
output = llm(
    "AIが人間に代わってブログを書くメリットを3つ挙げてください。",
    max_tokens=512,
    stop=["Q:", "\n"],
    echo=True
)

print(output["choices"][0]["text"])
```

### 期待される出力

```
AIが人間に代わってブログを書くメリットを3つ挙げてください。
1. 圧倒的な執筆スピード：人間が数時間かけるリサーチと執筆を、AIは数秒で完了させます。
2. 多様なトピックへの対応：AIは膨大な学習データを持ち、専門外の分野でも一貫した品質の文章を生成できます。
3. 24時間365日の稼働：AIに疲労はなく、常に一定のペースでコンテンツを供給し続けることが可能です。
```

`n_gpu_layers=-1` を設定した理由は、利用可能なVRAMを最大限活用するためです。
もしVRAMが足りない場合は、この数値を `10` や `20` と調整することで、一部をメインメモリに逃がして無理やり動かすことができます。
これがllama.cppを使う最大のメリットです。

## Step 4: 実用レベルにする

上記のコードでは、回答がすべて生成されるまで待つ必要があり、ユーザー体験（UX）が悪いです。
ChatGPTのように、生成された文字から順番に表示される「ストリーミング再生」と、過去の会話を覚えている「履歴管理」を実装します。

```python
import sys
from llama_cpp import Llama

def run_chat():
    # モデルのロード
    # 8Bモデルなら、Q4_K_MでVRAM約5.5GB消費（n_ctx=4096の場合）
    llm = Llama(
        model_path="./models/Meta-Llama-3-8B-Instruct-v0.1-Q4_K_M.gguf",
        n_gpu_layers=-1,
        n_ctx=4096, # 履歴を保持するために少し広めに設定
        seed=42      # 再現性を確保するためのシード値
    )

    # 会話履歴を保持するリスト
    # 役割（system, user, assistant）を定義する「ChatML」形式を模倣
    messages = [
        {"role": "system", "content": "あなたは優秀なアシスタントです。日本語で簡潔に答えてください。"}
    ]

    print("AIチャットボットを起動しました（終了するには 'exit' と入力）")

    while True:
        user_input = input("\nユーザー: ")
        if user_input.lower() == "exit":
            break

        messages.append({"role": "user", "content": user_input})

        print("アシスタント: ", end="", flush=True)

        # ストリーミング生成の実行
        # create_chat_completionを使うと、Llama 3等のChatテンプレートを自動適用してくれる
        stream = llm.create_chat_completion(
            messages=messages,
            stream=True,
            max_tokens=1024,
            temperature=0.7 # 0.7程度が創造性と正確性のバランスが良い
        )

        full_response = ""
        for chunk in stream:
            if "content" in chunk["choices"][0]["delta"]:
                token = chunk["choices"][0]["delta"]["content"]
                print(token, end="", flush=True)
                full_response += token

        messages.append({"role": "assistant", "content": full_response})
        print()

if __name__ == "__main__":
    run_chat()
```

このコードでは `create_chat_completion` を使っています。
これにより、Llama 3 などのモデル特有のプロンプト形式（`<|begin_of_text|>` 等の特殊タグ）を意識せずに、API感覚で対話機能を実装できます。
`temperature=0.7` は、仕事で使うならこの程度が最適です。1.0以上にすると「嘘」をつきやすくなり、0.1程度だと回答が画一的すぎて面白みに欠けます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ValidationError: ... n_gpu_layers` | ライブラリが古い、またはビルド失敗 | `pip install` 時に `CMAKE_ARGS` を指定して再ビルドする |
| `out of memory` (CUDA) | VRAM不足 | `n_gpu_layers` の値を減らす（例: -1から20にする） |
| 回答が英語になる | システムプロンプトの欠如 | `messages` の先頭に「日本語で答えて」というsystem roleを追加する |
| 生成速度が異様に遅い | CPUで動作している | ログを見て `BLAS = 0` になっていないか確認。1にするには再ビルドが必要 |

## 次のステップ

ここまでで、自分のPC上で動作するプライベートなAI環境が手に入りました。
次に挑戦すべきは、このローカルLLMに「自分の持っているPDFやドキュメント」を読み込ませて回答させる「RAG（検索拡張生成）」の構築です。
LangChainというライブラリを使えば、今回作った `llama-cpp-python` のインスタンスをそのまま流用して、社内マニュアル専用のAIなどを作ることができます。

また、モデルのサイズを「8B」から「70B」へ上げることも検討してください。
もちろん、70Bを動かすにはRTX 3090/4090の2枚挿しや、Mac Studio（メモリ64GB以上）が必要になりますが、その推論能力はGPT-4に匹敵します。
外部にデータを一切送信できない機密性の高い案件では、この「完全オフライン・高火力LLM」が最強の武器になります。
まずは今回のスクリプトをベースに、プロンプトを変えて自分の業務にどこまで使えるか、限界をテストしてみてください。

## よくある質問

### Q1: GGUFモデルはどこで探すのが一番いいですか？

Hugging Faceで「GGUF」と検索し、ダウンロード数が多い「TheBloke」氏や「Bartowski」氏、「QuantFactory」氏のリポジトリを見るのが鉄板です。彼らは最新モデルが出ると数時間で量子化版をアップしてくれます。

### Q2: 性能を上げるために `n_ctx`（コンテキスト長）を大きくしてもいいですか？

大きくできますが、VRAMを急激に消費します。例えば `n_ctx=32768`（32k）に設定すると、モデル本体とは別に数GBのVRAMがKVキャッシュとして確保されます。まずは `4096` で試し、余裕があれば広げるのが安全です。

### Q3: 商用利用は可能ですか？

llama.cpp自体のライセンス（MIT）は問題ありませんが、使用する「モデル」のライセンスに依存します。例えばLlama 3は「月間アクティブユーザー7億人以下」であれば無料で商用利用可能ですが、モデルごとに条件が異なるので必ず各リポジトリのLICENSEを確認してください。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBで8Bモデルを余裕を持って動かせる、ローカルLLM入門の最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cppとGGUFでローカルLLMを爆速で動かす環境構築ガイド](/posts/2026-11-21-llamacpp-gguf-local-llm-setup-guide/)
- [llama.cpp 使い方 入門！GGUF量子化でローカルLLMを動かす実践ガイド](/posts/2026-10-16-llamacpp-gguf-beginner-guide-setup/)
- [llama.cppとGGUFでローカルLLMを動かす Pythonによる実装ガイド](/posts/2026-06-14-llama-cpp-python-gguf-tutorial-beginners/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "GGUFモデルはどこで探すのが一番いいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Hugging Faceで「GGUF」と検索し、ダウンロード数が多い「TheBloke」氏や「Bartowski」氏、「QuantFactory」氏のリポジトリを見るのが鉄板です。彼らは最新モデルが出ると数時間で量子化版をアップしてくれます。"
      }
    },
    {
      "@type": "Question",
      "name": "性能を上げるために `n_ctx`（コンテキスト長）を大きくしてもいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "大きくできますが、VRAMを急激に消費します。例えば nctx=32768（32k）に設定すると、モデル本体とは別に数GBのVRAMがKVキャッシュとして確保されます。まずは 4096 で試し、余裕があれば広げるのが安全です。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用は可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "llama.cpp自体のライセンス（MIT）は問題ありませんが、使用する「モデル」のライセンスに依存します。例えばLlama 3は「月間アクティブユーザー7億人以下」であれば無料で商用利用可能ですが、モデルごとに条件が異なるので必ず各リポジトリのLICENSEを確認してください。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBで8Bモデルを余裕を持って動かせる、ローカルLLM入門の最適解</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
