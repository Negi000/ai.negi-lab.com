---
title: "llama.cppとGGUF量子化でローカルLLM構築入門"
date: 2026-07-10T00:00:00+09:00
slug: "llamacpp-gguf-local-llm-guide"
cover:
  image: "/images/posts/2026-07-10-llamacpp-gguf-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "ローカルLLM 構築"
  - "Llama 3.1 日本語"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- お手元のPCでLlama 3.1やMistralなどの最新AIを、商用API（GPT-4等）に頼らず完全オフラインで動かす推論環境を構築します。
- 具体的には、C++ベースの高速推論エンジン「llama.cpp」をビルドし、量子化されたGGUF形式のモデルをPythonからOpenAI互換APIとして呼び出す仕組みを作ります。
- 最終的に、プライベートなデータを一切外に出さない「自分専用のAIチャットサーバー」が手に入ります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama-3-8Bを余裕で全レイヤーロード可能。ローカルLLM入門に最適。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
結論から言うと、NVIDIA製GPUなら12GB（RTX 3060など）あれば、実務で使えるレベルの7B〜8Bクラスのモデルが快適に動きます。
もしVRAMが8GB以下の場合は、モデルの一部をメインメモリ（RAM）に逃がすことになりますが、推論速度は劇的に低下します。

Macユーザーの場合、M1/M2/M3チップを搭載し、メモリが16GB以上あれば、Windows機より快適に動くケースが多いです。
これは「ユニファイドメモリ」により、メインメモリをそのままVRAMとして割り当てられるためです。
私はRTX 4090を2枚積んでいますが、検証用にはMacBook Pro 32GBモデルも多用します。

費用については、ハードウェアさえあれば完全に0円です。
電気代はフル稼働時で1時間あたり数円〜数十円程度。
APIの従量課金を気にしてプロンプトを削るストレスから解放されるメリットは、計り知れません。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は、他にもPythonのTransformersライブラリを使う方法や、Ollamaを使う方法があります。
しかし、私は実務において「llama.cpp」を強く推奨します。
理由は、Python環境の依存関係に振り回されず、極めて軽量で、かつ「GGUF」という単一ファイル形式を扱えるからです。

Transformersを使うと、PyTorchのバージョン競合や、数十GBに及ぶモデルデータの管理に頭を抱えることになります。
一方、llama.cppはC++で書かれており、実行バイナリさえ作ればどこでも動きます。
また、GGUF形式は「重みの量子化」と「メタデータ」が一つのファイルにまとまっているため、モデルの配布や管理が非常に楽です。
「実務でシステムに組み込む」ことを考えたとき、このポータビリティは最強の武器になります。

## Step 1: 環境を整える

まずはllama.cppを自分のマシンに合わせてビルドします。
単にインストールするのではなく、GPUをフル活用できるようにコンパイルするのがポイントです。

```bash
# リポジトリのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド（macOS / Metal環境の場合）
cmake -B build -DGGML_METAL=ON
cmake --build build --config Release

# ビルド（Windows / NVIDIA GPU / CUDA環境の場合）
# 事前にCUDA Toolkitのインストールが必要です
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release
```

`GGML_METAL=ON` や `GGML_CUDA=ON` というフラグは、計算をCPUではなくGPUに肩代わりさせるための命令です。
これを忘れると、推論速度が10倍以上遅くなり、使い物になりません。
私が最初に試したときは、このフラグを忘れて「ローカルLLMは遅すぎて使えない」と誤解してしまいました。

⚠️ **落とし穴:**
Windowsユーザーで「cmakeが見つかりません」というエラーが出る場合は、Visual Studioの「C++によるデスクトップ開発」ワークロードがインストールされているか確認してください。
また、パス（Environment Variables）にCUDAのbinフォルダが含まれていないと、ビルドに成功してもGPUを認識しません。

## Step 2: 量子化モデル（GGUF）を入手する

次に、動かすための「脳」にあたるモデルデータを入手します。
Hugging Faceで公開されているモデルをそのまま使うのはサイズが大きすぎるため、有志が量子化したGGUF形式を利用します。

私のおすすめは、Bartowski氏やTheBloke氏が公開しているリポジトリです。
今回は、日本語性能が高い「Llama-3.1-8B-Instruct」を例にします。

1. Hugging Faceで `Llama-3.1-8B-Instruct-GGUF` を検索します。
2. 「Files and versions」タブから、`Q4_K_M.gguf` という名前のファイルをダウンロードします。
3. `llama.cpp` ディレクトリ内に `models` フォルダを作り、そこに配置します。

ここで「Q4_K_M」を選ぶ理由は、モデルの精度をほぼ維持したまま、サイズを元の約1/4（約5GB）まで圧縮できるからです。
4ビット量子化（Q4）は、現在のローカルLLMにおける「黄金比」と言えます。
これ以下のQ2やQ3にすると、明らかに回答の論理性が崩れ始めます。

## Step 3: 動かしてみる

まずはコマンドラインから直接モデルを動かし、正常にビルドできているか確認します。

```bash
# llama-cliを使用して対話を開始
./build/bin/llama-cli \
  -m models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf \
  -n 512 \
  -ngl 99 \
  -p "あなたは優秀なエンジニアです。Pythonで爆速なソートアルゴリズムを書いてください。"
```

### 期待される出力

```text
llama_print_timings: prompt eval time = 120.45 ms / 23 tokens ( 5.24 ms per token)
llama_print_timings:        eval time = 4500.12 ms / 150 tokens ( 30.00 ms per token)
[生成されたコード]
...
```

ここで最も注目すべきは `-ngl 99` というオプションです。
これは「GPUに何レイヤーオフロードするか」を指定する数値で、99と入れておけば「全レイヤーをGPUに載せる」という意味になります。
VRAMが足りない場合は、この数値を徐々に下げて（例：20、30）調整します。
全ての計算がGPUで行われていれば、1秒間に数十トークン（爆速）で文字が出力されるはずです。

## Step 4: 実用レベルにする（APIサーバー化）

CLIで動かすだけでは不便なので、次はllama.cppを「APIサーバー」として起動します。
これにより、既存のOpenAI SDKを使ったプログラムから、自分のローカルLLMをGPT-4と同じように叩けるようになります。

```bash
# APIサーバーを起動
./build/bin/llama-server \
  -m models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf \
  --port 8080 \
  -ngl 99
```

サーバーが立ち上がったら、別のターミナルからPythonで接続してみましょう。
ライブラリは `openai` そのまま使えます。

```python
import os
from openai import OpenAI

# ローカルサーバーに接続するための設定
client = OpenAI(
    base_url="http://localhost:8080/v1", # llama.cppのデフォルトエンドポイント
    api_key="sk-no-key-required"         # ローカルなのでキーは不要
)

response = client.chat.completions.create(
    model="local-model",
    messages=[
        {"role": "system", "content": "あなたは技術に詳しいアシスタントです。"},
        {"role": "user", "content": "RAG（検索拡張生成）のメリットを3行で説明して。"}
    ],
    temperature=0.7
)

print(response.choices[0].message.content)
```

この方法の凄さは、**「ソースコードを一行も変えずに、接続先URLを変えるだけで商用AIからローカルAIに切り替えられる」**点にあります。
開発時は安価なローカルLLMを使い、本番だけGPT-4Oに切り替えるといった運用がスムーズに行えます。

また、`llama-server` は軽量なWeb UIも内蔵しています。
ブラウザで `http://localhost:8080` を開くだけで、ChatGPTのようなチャット画面が即座に使えます。
私は、社内の機密文書を要約させる際に、このローカルサーバーを立てて処理を行っています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `error loading model: logic error` | GGUFのバージョンが古い、またはファイルが壊れている。 | llama.cppを最新に更新し、モデルを再DLしてください。 |
| `CUDA error 2: out of memory` | GPUのメモリ（VRAM）が足りない。 | `-ngl` の値を減らすか、より小さい量子化（Q3_K_Sなど）を使ってください。 |
| `Unknown argument --port` | バイナリが正しくビルドされていない。 | `llama-server` が `build/bin` 内に存在するか確認してください。 |
| 出力が文字化けする | 日本語に対応していない古いモデルを使っている。 | Llama-3.1やMistral v0.3など、多言語対応モデルを選んでください。 |

## 次のステップ

この記事の内容をマスターしたら、次は「RAG（検索拡張生成）」に挑戦してみてください。
自分のメモ帳や社内ドキュメントをベクトル化してデータベースに入れ、llama.cppと組み合わせることで、「自分自身の過去の思考」を検索して答えてくれるAIが作れます。

また、より高い精度を求めるなら、RTX 4090のようなハイエンドGPUを積み、30Bや70Bといった巨大なモデルを4ビット量子化で動かすことにも価値があります。
これらは推論速度こそ落ちますが、GPT-4に匹敵する知能をオフラインで発揮します。

AIエンジニアとしてのキャリアにおいて、こうした「インフラの裏側」を理解していることは大きな強みになります。
モデルがどのように量子化され、メモリに乗り、計算されているかを知ることで、コストと精度のトレードオフを適切に設計できるようになるからです。

## よくある質問

### Q1: メインメモリ（RAM）が8GBしかないPCでも動きますか？

動くことは動きますが、非常に厳しいです。モデルファイルだけで5GB前後占有するため、OSの動作と合わせるとスワップが発生し、1文字出すのに数秒かかる状態になります。最低でも16GB、快適さを求めるなら32GBへの増設を強く推奨します。

### Q2: 量子化モデル（Q4_K_M）の精度はどれくらい落ちますか？

数値的なベンチマーク（PPL：パープレキシティ）では数%の低下が見られますが、実際のチャット用途で体感できるほどの差はほとんどありません。むしろ、量子化によって動作が軽快になるメリットの方が実務上は圧倒的に大きいです。

### Q3: GPUがないノートPC（Intel/AMD内蔵グラフィックス）でも使えますか？

はい、llama.cppはCPU推論も非常に高速です。AVX2やAVX-512といった命令セットを自動で活用します。ただし、GPU推論に比べると数分の一の速度になるため、短文の要約やタスク処理などの用途から試すのが良いでしょう。

---

## あわせて読みたい

- [llama.cpp 使い方 入門：GGUF量子化モデルをローカルPCで爆速動作させる全手順](/posts/2026-06-20-llama-cpp-gguf-local-llm-tutorial/)
- [llama.cpp 使い方 入門｜低スペックPCでLlama 3を爆速で動かす実践ガイド](/posts/2026-06-12-llama-cpp-gguf-beginner-guide-python/)
- [DeepSeek V4 Flash 使い方！llama.cppで最新モデルをローカル構築する手順](/posts/2026-06-06-deepseek-v4-flash-llamacpp-local-setup/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "メインメモリ（RAM）が8GBしかないPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動くことは動きますが、非常に厳しいです。モデルファイルだけで5GB前後占有するため、OSの動作と合わせるとスワップが発生し、1文字出すのに数秒かかる状態になります。最低でも16GB、快適さを求めるなら32GBへの増設を強く推奨します。"
      }
    },
    {
      "@type": "Question",
      "name": "量子化モデル（Q4_K_M）の精度はどれくらい落ちますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "数値的なベンチマーク（PPL：パープレキシティ）では数%の低下が見られますが、実際のチャット用途で体感できるほどの差はほとんどありません。むしろ、量子化によって動作が軽快になるメリットの方が実務上は圧倒的に大きいです。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUがないノートPC（Intel/AMD内蔵グラフィックス）でも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、llama.cppはCPU推論も非常に高速です。AVX2やAVX-512といった命令セットを自動で活用します。ただし、GPU推論に比べると数分の一の速度になるため、短文の要約やタスク処理などの用途から試すのが良いでしょう。 ---"
      }
    }
  ]
}
</script>
