---
title: "llama.cppとGGUF量子化の使い方入門：自作PCやMacでLLMを動かす全手順"
date: 2026-10-07T00:00:00+09:00
slug: "llamacpp-gguf-beginner-guide-setup"
cover:
  image: "/images/posts/2026-10-07-llamacpp-gguf-beginner-guide-setup.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp"
  - "GGUF"
  - "量子化"
  - "ローカルLLM 使い方"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

この記事では、自分のPCのリソースを最大限に活用して、最新のLLM（Llama 3.1やMistralなど）と超高速にチャットできるOpenAI互換のAPIサーバーを構築します。
Pythonの重いライブラリを入れず、C++ベースの軽量な「llama.cpp」を使うことで、古いGPUやメモリの少ないMacでも実用レベルの速度を出せるようになります。

前提知識として、ターミナル（コマンドプロンプト）の基本的な操作と、Pythonがインストールされている環境が必要です。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」と「メインメモリ」の容量です。
結論から言うと、7Bクラス（70億パラメータ）のモデルを動かすなら、最低でも8GBのメモリ（VRAMまたはRAM）が必要です。
8GBあれば、今回紹介する「GGUF量子化」を使うことで、モデルを4bit程度に圧縮してメモリ内に収めることができます。

NVIDIAのGPU（RTX 3060 12GB以上推奨）があれば、処理をGPUにオフロードして爆速で動かせます。
一方、Apple Silicon搭載のMac（M1/M2/M3）であれば、ユニファイドメモリをフル活用できるため、16GB以上のモデルでも非常にスムーズに動作します。
「自分のPCはスペック不足かも」と思っている方でも、llama.cppならCPUだけで動かす選択肢もあるため、まずは試してみる価値があります。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手法は、他に「Ollama」や「LM Studio」といったGUIツールも存在します。
しかし、あえて「llama.cpp」を直接使う理由は、カスタマイズ性とデプロイの柔軟性が圧倒的だからです。

llama.cppはC++で書かれており、依存関係がほとんどありません。
サーバーとして起動すればOpenAIのAPIと同じ形式でリクエストを受け付けられるため、既存のCursorやCline、自作のPythonスクリプトから「接続先URLを変えるだけ」でローカルモデルに切り替えられます。
仕事で使うシステムに組み込むなら、ブラックボックス化されたGUIツールよりも、パラメータを細かく制御できるllama.cppがベストな選択肢になります。

## Step 1: 環境を整える

まずは、llama.cppを自分のPCで動かせるようにビルド（コンパイル）します。
あらかじめビルドされたバイナリをダウンロードする方法もありますが、自分のPCのCPU/GPU命令に最適化させるために、ソースからビルドすることを強く推奨します。

### Mac（Apple Silicon）の場合
ターミナルを開き、以下のコマンドを順に実行してください。

```bash
# リポジトリをクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド（Metalを有効にしてGPUをフル活用する）
make -j
```

### Windowsの場合
git bashやPowerShellではなく、`Developer PowerShell for VS 2022`などを使ってビルドします。

```powershell
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build
cd build

# CUDA（NVIDIA GPU）を使う設定でビルド
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release
```

`make`や`cmake`は、ソースコードを自分のPCで動く「実行ファイル」に変換する作業です。
特にMacなら`Metal`、Windowsなら`CUDA`を有効にしないと、GPUが使われずCPU処理になり、レスポンスが10倍以上遅くなるので注意してください。

⚠️ **落とし穴:**
Windowsユーザーで「cmakeなんて入っていない」というエラーが出る場合は、Visual Studioのインストーラーから「C++によるデスクトップ開発」にチェックを入れてインストールしてください。
これを忘れると、一生ビルドが通りません。

## Step 2: 量子化モデル（GGUF）を手に入れる

LLMの元のデータは非常に巨大で、そのままでは一般のPCメモリに収まりません。
そこで、データの精度を少しだけ落として軽量化する「量子化」という技術を使います。
今回は、すでに量子化された「GGUF」という形式のファイルをHugging Faceからダウンロードします。

私が実務でよく使うのは、Bartowski氏やMaziyarPanahi氏が公開しているプリコンパイル済みのモデルです。

1. [Hugging Face](https://huggingface.co/models?search=Llama-3.1-8B-Lexi-Llama-GGUF) にアクセス。
2. `Llama-3.1-8B-Instruct-GGUF` などのモデルを探す。
3. 「Files and versions」タブから、`Q4_K_M.gguf` というファイル名のものをダウンロードする。

`Q4_K_M`は、精度とサイズのバランスが最も良い「4bit量子化」の設定です。
8Bモデルなら、このファイル一つで約5GB程度の容量になります。

```bash
# llama.cppディレクトリ内に models フォルダを作って保存
mkdir models
mv ~/Downloads/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf ./models/
```

## Step 3: 動かしてみる

準備が整ったので、まずはコマンドラインから直接モデルを動かしてみましょう。

```bash
# llama.cppのディレクトリで実行
./llama-cli -m models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf \
  -p "You are a helpful assistant. 日本語で答えてください。" \
  -cnv \
  --n-gpu-layers 99
```

各設定の意味は以下の通りです。
- `-m`: モデルファイルのパス。
- `-p`: システムプロンプト。AIの役割を指定。
- `-cnv`: 対話モード（Conversation）。チャット形式でやり取りできる。
- `--n-gpu-layers 99`: すべての計算層をGPUに丸投げする設定。VRAMが足りない場合はこの数字を下げますが、最近の8Bモデルなら4090でもM2 Macでも全部載ります。

### 期待される出力

```text
User: こんにちは、自己紹介してください。
Llama: こんにちは！私はMetaによってトレーニングされたAIアシスタントです。
プログラミングや文章作成、翻訳などのお手伝いができます。
```

もしここで文字化けしたり、極端に生成が遅い（1秒間に1文字以下）場合は、GPUが正しく認識されていません。
ビルド時のログを見直して、`CUDA`や`Metal`の文字があるか確認してください。

## Step 4: 実用レベルにする（サーバーモード）

CLIで動かすだけでは不便です。
llama.cppの真骨頂は、軽量な「サーバーモード」にあります。
これを起動しておけば、外部ツールからAPI経由で呼び出せるようになります。

```bash
./llama-server -m models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf \
  --port 8080 \
  --n-gpu-layers 99 \
  --api-key your_secret_key
```

これで、`http://localhost:8080` でOpenAI互換のAPIが立ち上がりました。
次に、Pythonからこのローカルサーバーを叩くコードを書いてみましょう。

```python
import openai

# ローカルで立ち上げたllama-serverを指定
client = openai.OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="your_secret_key" # サーバー側で指定したもの
)

response = client.chat.completions.create(
    model="local-model", # サーバー側では何を指定しても動く
    messages=[
        {"role": "system", "content": "あなたはプロのエンジニアです。"},
        {"role": "user", "content": "Pythonで高速な素数判定プログラムを書いて。"}
    ]
)

print(response.choices[0].message.content)
```

この方法の利点は、クラウドのAPI（GPT-4など）を使っているコードの `base_url` を書き換えるだけで、一瞬で「完全オフライン・無料・プライバシー保護」な環境に切り替えられる点です。
私は機密性の高いドキュメントの要約や、大量のテストデータの生成をローカルで行う際にこの構成を多用しています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `error loading model` | ファイルが壊れている、またはパスが違う | ダウンロードを再試行し、パスをフルパスで指定してみる |
| `out of memory` | VRAMが足りない | `--n-gpu-layers` の値を減らす（例: 20） |
| `command not found: make` | 開発ツールが入っていない | Macなら `xcode-select --install` を実行 |
| 生成速度が異様に遅い | CPUだけで計算している | ビルド時に `GGML_CUDA=ON` などを忘れていないか確認 |

## 次のステップ

llama.cppをサーバーとして動かせるようになったら、次は「Cursor」や「Continue」といったエディタ拡張機能と連携させてみてください。
設定画面のAPI URLを `http://localhost:8080/v1` に書き換えるだけで、自分のPCで動くAIがコードを書いてくれるようになります。

また、余裕があれば「RAG（検索拡張生成）」の実験に進むのも面白いです。
ローカルLLMなら、数万件のプライベート文書を読み込ませても外部にデータが漏れる心配がありません。
llama.cppにはPythonバインディング（llama-cpp-python）も存在するので、LangChainと組み合わせて独自のローカルAIエージェントを作ってみるのも良いでしょう。

## よくある質問

### Q1: Q4_K_MとかQ8_0とか、量子化の種類が多すぎてどれを選べばいいですか？

実用上は `Q4_K_M` または `Q5_K_M` が最強です。4bit（Q4）以下に落とすと急激に頭が悪くなりますが、4bitから8bit（Q8）に上げても、精度の向上は微々たるものです。メモリを節約して、その分長いコンテキスト（入力文字数）を確保する方が実務では有利です。

### Q2: 複数のGPU（RTX 4090 2枚など）を持っている場合、どうすればいいですか？

llama.cppはデフォルトでマルチGPUに対応しています。ビルド時にCUDAを有効にしていれば、特に設定しなくてもVRAMを合算して使ってくれます。もし特定のGPUだけ使いたい場合は、環境変数 `CUDA_VISIBLE_DEVICES` で制御可能です。

### Q3: Pythonライブラリの llama-cpp-python とは何が違うんですか？

本家 llama.cpp はC++の実行ファイル、Python版はそのラッパー（包み紙）です。速度はどちらも優秀ですが、この記事のように `llama-server` を直接使う方が、更新速度が速く、依存関係のトラブル（インストール失敗）も少ないので、個人的には本家を直接使うのが一番安定すると感じています。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的。8Bモデルなら余裕で全レイヤー載ります</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cppとGGUFでローカルLLMを動かす Pythonによる実装ガイド](/posts/2026-06-14-llama-cpp-python-gguf-tutorial-beginners/)
- [llama.cppでKVキャッシュを最適化し推論を高速化する方法](/posts/2026-06-08-llamacpp-kv-cache-optimization-guide/)
- [ローカルLLM用GPUの選び方｜Qwen 27Bを動かすVRAM容量と量子化の罠](/posts/2026-08-22-local-llm-gpu-vram-quantization-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Q4_K_MとかQ8_0とか、量子化の種類が多すぎてどれを選べばいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "実用上は Q4KM または Q5KM が最強です。4bit（Q4）以下に落とすと急激に頭が悪くなりますが、4bitから8bit（Q8）に上げても、精度の向上は微々たるものです。メモリを節約して、その分長いコンテキスト（入力文字数）を確保する方が実務では有利です。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のGPU（RTX 4090 2枚など）を持っている場合、どうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "llama.cppはデフォルトでマルチGPUに対応しています。ビルド時にCUDAを有効にしていれば、特に設定しなくてもVRAMを合算して使ってくれます。もし特定のGPUだけ使いたい場合は、環境変数 CUDAVISIBLEDEVICES で制御可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "Pythonライブラリの llama-cpp-python とは何が違うんですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "本家 llama.cpp はC++の実行ファイル、Python版はそのラッパー（包み紙）です。速度はどちらも優秀ですが、この記事のように llama-server を直接使う方が、更新速度が速く、依存関係のトラブル（インストール失敗）も少ないので、個人的には本家を直接使うのが一番安定すると感じています。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでローカルLLM入門に現実的。8Bモデルなら余裕で全レイヤー載ります</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
