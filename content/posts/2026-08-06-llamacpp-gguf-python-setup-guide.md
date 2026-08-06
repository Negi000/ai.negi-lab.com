---
title: "llama.cpp 使い方 入門 | GGUF量子化でローカルLLMを動かす"
date: 2026-08-06T00:00:00+09:00
slug: "llamacpp-gguf-python-setup-guide"
cover:
  image: "/images/posts/2026-08-06-llamacpp-gguf-python-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "ローカルLLM Python"
  - "llama-cpp-python 入門"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

この記事を読むと、軽量なGGUF形式のモデルを使い、自分専用のローカルLLM実行サーバーをPythonで構築できます。
API料金やデータ漏洩の心配をせず、手元のPCのリソースを限界まで引き出して推論を回すスクリプトを完成させます。
具体的には、Llama 3などの最新モデルを数GBのメモリで動作させ、チャット応答を得るまでの全工程を網羅します。

前提知識として、ターミナル（PowerShellやTerminal）の基本操作と、Pythonの基礎的な文法を理解している必要があります。
必要なものは、メモリ8GB以上のPC（Mac/Windows/Linux）のみで、高価なGPUがなくても動作する設定を解説します。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」または「共有メモリ」の容量です。
一般的に、7B（70億パラメータ）クラスのモデルを実用的な速度で動かすには、量子化されたGGUF形式で約5GBから8GBの空きメモリを消費します。
もしRTX 3060（12GB）やRTX 4060 Ti（16GB）といったGPUがあれば、レスポンス速度は秒間50トークン（爆速）を超えます。

一方で、GPUがないMacBook Air（M1/M2/M3）や一般的なビジネスノートPCでも、llama.cppならCPUとメインメモリを使って動作可能です。
ただし、メモリが8GBしかないPCで他のソフトを立ち上げながら動かすと、スワップが発生して極端に動作が重くなるため注意してください。
料金は完全に無料です。モデルデータはHugging Faceから無料でダウンロードでき、推論にかかるのは電気代だけです。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段として「Ollama」や「LM Studio」といった便利なGUIツールも存在します。
しかし、実務で「特定のシステムに組み込みたい」「細かい推論パラメータをチューニングしたい」場合には、llama.cppがベストな選択肢です。
llama.cppはC++で書かれた極めて軽量なバックエンドであり、量子化技術（GGUF）によってモデルサイズを元の4分の1以下に圧縮できます。

また、Pythonバインディングである「llama-cpp-python」を使うことで、既存のPythonアプリに数行でLLM機能を統合できる柔軟性があります。
Ollamaは裏側でllama.cppを動かしていますが、その「中身」を直接操作できるスキルを身につけることで、トラブルシューティングや最適化が容易になります。
私が業務でローカルLLMを提案する際は、まずllama.cppでリソース消費の限界を検証してから実装に入るのが鉄則です。

## Step 1: 環境を整える

まずは、Pythonからllama.cppを操作するためのライブラリをインストールします。
OSやハードウェアによってインストールコマンドが異なるため、自分の環境に合わせたものを選んでください。

```bash
# CPUのみで動かす場合（一般的なノートPC）
pip install llama-cpp-python

# NVIDIA製GPU（CUDA）を使う場合（Windows/Linux）
# 以下の環境変数を設定してからインストールすることでGPUが有効になります
$env:CMAKE_ARGS="-DGGML_CUDA=on" # Windows PowerShell
export CMAKE_ARGS="-DGGML_CUDA=on" # Linux/Mac
pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir

# Apple Silicon (M1/M2/M3) を使う場合
$env:CMAKE_ARGS="-DGGML_METAL=on"
pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir
```

このコマンドは、単にライブラリを入れるだけでなく、実行環境に最適化されたバイナリをその場でビルドしています。
特に「--no-cache-dir」を付けるのは、以前のCPU版キャッシュが残ってGPUが認識されないトラブルを防ぐためです。
インストールには数分かかりますが、ここでコンパイルが通れば、あなたのPCの性能を100%引き出す準備が整います。

⚠️ **落とし穴:**
Windowsユーザーで「CMake must be installed」というエラーが出る場合は、Visual Studioの「C++によるデスクトップ開発」ワークロードが入っていません。
Microsoftの公式サイトからBuild Toolsをインストールしてください。これがないとllama.cppのビルドに失敗します。

## Step 2: モデルのダウンロード（GGUF形式）

llama.cppで動かすには、モデルが「GGUF」という形式である必要があります。
本家Metaが配布しているモデルはそのままでは動かないため、有志が量子化したファイルをHugging Faceから取得します。

おすすめは「Bartowski」氏や「MaziyarPanahi」氏が公開しているリポジトリです。
今回は、日本語能力が高く軽量な「Llama-3-8B-Instruct-v0.1」のGGUF版を例に進めます。

1. [Hugging Face](https://huggingface.co/)で「Llama-3-8B-Instruct-GGUF」を検索します。
2. 「Files and versions」タブから、`Q4_K_M.gguf` という名前のファイルをダウンロードします。
3. プロジェクトのディレクトリに `models` フォルダを作成し、そこに保存します。

なぜ `Q4_K_M` を選ぶのか。
それは、重み（精度）を4ビットに圧縮しつつ、知能の低下を最小限に抑えた「最もコスパの良い」設定だからです。
Q2（2ビット）まで下げるとモデルはバカになりますし、Q8（8ビット）にするとメモリを食い過ぎて動作が重くなります。
実務でのプロトタイプ作成には、このQ4_K_Mが業界標準と言えるでしょう。

## Step 3: 動かしてみる

モデルが準備できたら、最小限のコードで推論を試してみましょう。
ここでは、モデルの読み込みからテキスト生成までの基本フローを記述します。

```python
import os
from llama_cpp import Llama

# モデルファイルのパスを指定
# 自分の環境に合わせてパスを書き換えてください
model_path = "./models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"

# モデルの初期化
# n_ctx: コンテキストサイズ（一度に扱えるトークン量。1024〜4096が目安）
# n_gpu_layers: GPUにオフロードするレイヤー数。-1を指定すると全レイヤーをGPUに載せます
llm = Llama(
    model_path=model_path,
    n_ctx=2048,
    n_gpu_layers=-1 if os.name != 'nt' else 32
)

# 推論の実行
response = llm(
    "AIについて、3行で簡潔に説明してください。",
    max_tokens=256,
    stop=["Q:", "\n"],
    echo=True
)

print(response["choices"][0]["text"])
```

### 期待される出力

```
AI（人工知能）とは、人間の知的能力をコンピュータで模倣する技術です。
データの学習を通じて、推論、判断、問題解決などを自動で行うことができます。
現代では自動運転や画像生成など、幅広い分野で実用化が進んでいます。
```

結果の読み方ですが、`response` は辞書形式で返ってきます。
`choices[0]["text"]` に生成された文章が格納されています。
もし文字化けしたり、出力が途中で切れる場合は、`max_tokens` の値を増やしてみてください。

## Step 4: 実用レベルにする

単発の推論だけでは実務に使えません。
次は「ストリーミング出力」と「チャット形式（Chat Completion API風）」に対応させます。
一文字ずつ文字が表示されるあの挙動を実装することで、ユーザー体験が劇的に向上します。

```python
from llama_cpp import Llama

# モデルの読み込み（GPUを最大限活用する設定）
llm = Llama(
    model_path="./models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf",
    n_ctx=4096,
    n_gpu_layers=-1, # M1/M2 MacやRTX 3060以上なら-1を推奨
    verbose=False    # ログを非表示にして出力を綺麗にする
)

def ask_ai(prompt):
    # OpenAI APIと同じ形式でメッセージを構成
    messages = [
        {"role": "system", "content": "あなたは優秀なアシスタントです。"},
        {"role": "user", "content": prompt}
    ]

    # ストリーミングを有効にして実行
    stream = llm.create_chat_completion(
        messages=messages,
        stream=True
    )

    print("AI: ", end="", flush=True)
    for chunk in stream:
        delta = chunk["choices"][0]["delta"]
        if "content" in delta:
            print(delta["content"], end="", flush=True)
    print()

# 実行
ask_ai("ローカルLLMを業務で導入するメリットを3つ挙げてください。")
```

このコードでは `create_chat_completion` を使っています。
これにより、OpenAIのAPIとほぼ同じメッセージ構造（System/User/Assistant）でやり取りができるようになります。
実務では、過去の会話履歴をリストに保持して `messages` に渡すことで、文脈を考慮したチャットボットが完成します。

ストリーミング出力を採用した理由は、ローカルLLMはどうしても最初の1文字が出るまで数秒かかる場合があるからです。
一気に全文を出そうとすると「固まっている」と誤解されますが、1文字ずつ出すことで体感速度が0.5秒以下まで改善されます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Address already in use` | 他のプロセスがGPUを専有している | 使用していないAIツールやブラウザを閉じる |
| `Model not found` | パスの指定ミス | `os.path.exists()` で確認するか絶対パスを使う |
| `Illegal instruction` | CPUがAVX2等に対応していない | 古いPCの場合、ビルド設定を見直す必要がある |
| 出力が非常に遅い | GPUが認識されていない | `n_gpu_layers` が 0 になっていないか確認する |

## 次のステップ

この記事の内容をマスターしたら、次は「RAG（検索拡張生成）」に挑戦してみてください。
llama.cppで動かしているモデルに、自分のPDFファイルや社内ドキュメントを読み込ませる手法です。
具体的には「LangChain」や「LlamaIndex」といったライブラリを組み合わせることで、特定の知識に特化したAIをローカル完結で作ることができます。

また、Web UIが必要な場合は「Text Generation WebUI」を導入するのも良いでしょう。
しかし、まずは今回のようにPythonコードから直接モデルを叩けるようになったことが大きな一歩です。
コードから触れるようになると、バッチ処理で数万件のデータを一気に要約したり、独自のAPIサーバーを立てたりと、応用範囲が無限に広がります。
まずは手元のモデルに、いろいろな質問を投げかけて、量子化による「賢さの変化」を体感してみてください。

## よくある質問

### Q1: メモリ16GBのMacBook Airで、どのくらいのサイズのモデルまで動かせますか？

8Bクラス（Llama-3など）のQ4_K_M量子化なら余裕で動きます。14Bクラスもいけますが、ブラウザなどを開きすぎていると動作が重くなります。70Bクラスはメモリ不足でスワップが発生し、実用には耐えません。

### Q2: 実行中に「ggml_cuda: out of memory」と出ます。

GPUのVRAMが足りていません。`n_gpu_layers` の値を少しずつ下げて（例: 32 → 20）、一部の処理をCPUに逃がしてください。これで動作は遅くなりますが、エラーを回避して動かすことが可能です。

### Q3: 商用利用は可能ですか？

llama.cpp自体はMITライセンスなので問題ありません。ただし、使用する「モデル」のライセンス（Llama 3ならLlama 3 Community Licenseなど）に依存します。多くは商用利用可能ですが、月間アクティブユーザー数に制限がある場合もあるので、個別に確認してください。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に最適。7B〜14Bモデルが余裕で載ります</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cpp 使い方 入門：GGUF量子化でローカルLLMを爆速にする方法](/posts/2026-07-12-llama-cpp-gguf-quantization-tutorial-python/)
- [llama.cpp 使い方 入門｜低スペックPCでLlama 3を爆速で動かす実践ガイド](/posts/2026-06-12-llama-cpp-gguf-beginner-guide-python/)
- [llama.cpp 使い方 入門：GGUF量子化モデルをローカルPCで爆速動作させる全手順](/posts/2026-06-20-llama-cpp-gguf-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "メモリ16GBのMacBook Airで、どのくらいのサイズのモデルまで動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "8Bクラス（Llama-3など）のQ4KM量子化なら余裕で動きます。14Bクラスもいけますが、ブラウザなどを開きすぎていると動作が重くなります。70Bクラスはメモリ不足でスワップが発生し、実用には耐えません。"
      }
    },
    {
      "@type": "Question",
      "name": "実行中に「ggml_cuda: out of memory」と出ます。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "GPUのVRAMが足りていません。ngpulayers の値を少しずつ下げて（例: 32 → 20）、一部の処理をCPUに逃がしてください。これで動作は遅くなりますが、エラーを回避して動かすことが可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用は可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "llama.cpp自体はMITライセンスなので問題ありません。ただし、使用する「モデル」のライセンス（Llama 3ならLlama 3 Community Licenseなど）に依存します。多くは商用利用可能ですが、月間アクティブユーザー数に制限がある場合もあるので、個別に確認してください。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでローカルLLM入門に最適。7B〜14Bモデルが余裕で載ります</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
