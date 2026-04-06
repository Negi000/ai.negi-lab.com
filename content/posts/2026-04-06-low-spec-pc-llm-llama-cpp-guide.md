---
title: "低スペックPCでLLMを動かす llama.cpp 構築ガイド"
date: 2026-04-06T00:00:00+09:00
slug: "low-spec-pc-llm-llama-cpp-guide"
cover:
  image: "/images/posts/2026-04-06-low-spec-pc-llm-llama-cpp-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "軽量LLM 構築"
  - "Qwen2 GGUF 実行"
  - "低スペックPC AI"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- メモリ（RAM）が1GB以下の旧型PCやシングルボードコンピュータでも動作する、超軽量なローカルLLM環境を構築します。
- 前提知識：Linux（Ubuntu/Debian系）またはmacOSのターミナル操作ができること。
- 必要なもの：インターネット環境、空き容量5GB程度のストレージ。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">Raspberry Pi 5</strong>
<p style="color:#555;margin:8px 0;font-size:14px">8GBモデルなら軽量LLMを複数常駐させても余裕があり、エッジAIの実験に最適です</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=Raspberry%20Pi%205&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRaspberry%2520Pi%25205%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRaspberry%2520Pi%25205%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

1998年のiMac G3、しかもRAM 32MBでLLMが動作したというニュースは、私のようなハードウェア好きには衝撃的でした。
普段はRTX 4090を2枚挿して、VRAMの暴力でモデルを動かしている私ですが、このニュースは「リソースが限られた環境での最適化」の重要性を突きつけています。
他にもPythonベースのTransformersライブラリを使う方法がありますが、今回はあえてC++で書かれた `llama.cpp` を選びます。

理由は単純で、Pythonのオーバーヘッドを徹底的に排除し、メモリ管理を直接制御できるからです。
`llama.cpp` はメモリマップドI/O（mmap）を利用するため、RAMにモデルをすべてロードしなくても動作します。
これは、かつてSIerでリソースの限られたサーバーに無理やりミドルウェアを詰め込んでいた時代の知恵に近いものがあります。
最新のハイエンドPCがなくても、手元に転がっている数年前のラップトップや、Raspberry Pi 4/5でも驚くほど軽快にAIが動く体験を、ぜひ味わってほしいと思います。

## Step 1: 開発環境の準備

まずはコンパイルに必要なツールチェーンをインストールします。
`llama.cpp` はC++で書かれているため、ビルド環境が必須です。

```bash
# Ubuntu/Debian系の場合
sudo apt update
sudo apt install -y build-essential cmake git

# macOSの場合（Xcode Command Line Toolsが必要）
xcode-select --install
```

`build-essential` は `gcc` や `make` など、プログラムをビルドするための基本ツールセットです。
`cmake` はビルドプロセスを自動化するために使用します。
これらがないと、ソースコードからバイナリを作成することができません。

⚠️ **落とし穴:**
古いOSを使っている場合、`cmake` のバージョンが古くてビルドに失敗することがあります。
その場合は公式サイトから最新のバイナリを落としてくるか、`pip install cmake` でPython経由で新しいバージョンを入れるのが一番手っ取り早いです。

## Step 2: llama.cppのビルド

次に、ソースコードを取得して実行ファイルを作成します。
ここではCPU実行に特化した設定でビルドを行います。

```bash
# リポジトリのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド用ディレクトリの作成
mkdir build
cd build

# CMakeの実行。CPUのみで動作させる基本設定
cmake ..

# 並列ビルドの実行（-jの後の数字はCPUコア数に合わせて調整してください）
make -j4
```

`cmake ..` を実行した際、システムが自動的に最適なコンパイラ設定を探してくれます。
AVX2やAVX512といった、CPUの高速演算命令が有効になっているかログをチェックしてください。
これらが有効でないと、推論速度が10倍以上遅くなる可能性があります。

## Step 3: 超軽量モデルのダウンロード

iMac G3の例では極限まで小さいモデルが使われましたが、実用性を考えて「Qwen2-0.5B-Instruct」の量子化版を使用します。
アリババが開発したこのモデルは、パラメータ数が0.5B（約5億）と非常に小さく、かつ日本語の理解力も備えています。

```bash
# llama.cppのルートディレクトリに戻る
cd ..

# モデル格納用ディレクトリ作成
mkdir models

# Hugging FaceからGGUF形式のモデルをダウンロード
# ここではメモリ消費を抑えるためにQ4_K_M（4ビット量子化）を選択
curl -L https://huggingface.co/Qwen/Qwen2-0.5B-Instruct-GGUF/resolve/main/qwen2-0.5b-instruct-q4_k_m.gguf -o models/qwen2-0.5b-instruct-q4_k_m.gguf
```

なぜこのモデルなのか。
0.5Bモデルを4ビット量子化すると、モデルサイズは約350MB程度になります。
これなら、OSが使うメモリを除いても、512MBのRAMがあれば余裕で動作します。
「賢さ」ではGPT-4に遠く及びませんが、特定のタスク（テキスト分類や簡単な応答）なら十分仕事に使えます。

## Step 4: 最小構成で動かしてみる

いよいよ実行です。
メモリ消費を最小限に抑えるためのパラメータを付与して起動します。

```bash
./build/bin/llama-cli \
  -m models/qwen2-0.5b-instruct-q4_k_m.gguf \
  -p "あなたは優秀なアシスタントです。今日の晩御飯の献立を1つ提案してください。" \
  -n 128 \
  --ctx-size 512 \
  --threads 4 \
  --no-mmap
```

各パラメータの意味を解説します。
`-m` はモデルファイルの指定。
`-n 128` は最大出力トークン数。これを制限することで、メモリの動的な消費を防ぎます。
`--ctx-size 512` はコンテキストサイズ（記憶の長さ）です。デフォルトはもっと大きいですが、低スペック環境ではここを削るのが鉄則です。
`--no-mmap` は、モデル全体を強制的にメモリにロードする設定です。スワップが発生して極端に遅くなるのを防ぐために、RAMに余裕があるなら付けてください。逆に32MBしかないような極限環境なら、これを除外してOSの仮想メモリに頼ることになります。

### 期待される出力

```text
晩御飯には「鶏肉とキャベツの味噌炒め」はいかがでしょうか。
材料も少なく、15分程度で作れるので忙しい時にも最適です。
```

このような応答が数秒で返ってくれば成功です。
私の環境（Core i5の古いノートPC）では、毎秒約30トークンという爆速で出力されました。
ハイエンドGPUを使わなくても、これだけの速度が出るのは `llama.cpp` の最適化の賜物です。

## Step 5: 実用レベルのAPIサーバーにする

「動いて終わり」では仕事になりません。
この軽量LLMを、外部から呼び出せるAPIサーバーとして運用してみましょう。
Pythonスクリプトなどから、OpenAI互換の形式で呼び出せるようになります。

```bash
./build/bin/llama-server \
  -m models/qwen2-0.5b-instruct-q4_k_m.gguf \
  --port 8080 \
  --ctx-size 1024 \
  --threads 4
```

サーバーを起動した状態で、別のターミナルから `curl` でリクエストを投げてみます。

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "PythonでHello Worldを書いて"}
    ]
  }'
```

これで、あなたの古いPCが「AIサーバー」に変わりました。
私は自宅サーバー（RTX 4090搭載）の横で、消費電力わずか5WのRaspberry Piにこのサーバーを常駐させています。
ちょっとしたテキストの整形や、ログの分類を自動化するのに、わざわざ電気を食うGPUを回す必要はありません。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Segmentation fault` | メモリ不足、または量子化形式の不一致 | `--ctx-size` を小さくするか、より小さい量子化（Q2_Kなど）を試す。 |
| `Illegal instruction` | CPUがAVX2などの命令セットに対応していない | CMake実行時に `-DGGML_AVX2=OFF` などのフラグを立てて再ビルドする。 |
| 出力が文字化けする | モデルが日本語非対応、またはプロンプトの不備 | Qwen2やLlama-3など、多言語対応モデルを使用しているか確認する。 |

## 次のステップ

ここまでで、「超低リソースでLLMを動かす」という目標は達成できました。
しかし、0.5B程度のモデルだと、複雑な推論をさせると嘘（ハルシネーション）をつくことが目立ちます。
これを実務で使うための次のステップは、**「RAG（検索拡張生成）」との組み合わせ**です。

モデル自体に知識を持たせるのではなく、外部ファイル（PDFやDB）から検索したテキストをコンテキストに流し込む手法です。
軽量モデルでも、コンテキストに正解が書いてあれば、それを要約して答えることは得意です。
例えば、社内のマニュアルを読み込ませた「超軽量・省電力な社内QAボット」などは、この構成で十分に運用可能です。
次は、`LangChain` や `LlamaIndex` を使って、この軽量サーバーを脳として動かすアプリケーション構築に挑戦してみてください。

## よくある質問

### Q1: 32MB RAMの環境で動かすには、他に何を削ればいいですか？

OS自体のメモリ消費を削る必要があります。GUIを切り、最小構成のLinux（Alpine Linuxなど）を使い、さらにスワップ領域を高速なSSD上に確保してください。モデルも100Mパラメータ以下の超小型モデルを選定する必要があります。

### Q2: 推論速度が非常に遅いのですが、改善策はありますか？

ビルド時に最適なコンパイラフラグが立っているか確認してください。また、バックグラウンドで動いている不要なプロセスを停止させるだけでも、CPUのL3キャッシュの競合が減り、速度が改善することがあります。

### Q3: GPUがある場合は、どう設定を変えればいいですか？

CMakeの実行時に `-DGGML_CUDA=ON` を付けることで、GPU（CUDA）を利用したビルドが可能です。実行時に `-ngl 99` （GPUレイヤー数）を指定すれば、VRAMをフル活用してさらに高速な推論が行えます。

---

## あわせて読みたい

- [llama-swap 使い方：Ollama超えのローカルLLM切り替え環境を構築](/posts/2026-03-06-llama-swap-local-llm-model-switching-guide/)
- [Qwen3.5-35BをVRAM 16GBで爆速動作させるローカルLLM構築術](/posts/2026-02-27-qwen35-35b-local-setup-16gb-vram/)
- [自分のPCで「どのサイズのLLMを動かすべきか」という悩みは、ローカルLLM界隈では永遠のテーマです。特に最近注目されている9B（90億パラメータ）と35B（350億パラメータ）のモデルは、それぞれ実用性と性能のバランスが絶妙で、どちらをメインに据えるかで構築プランが大きく変わります。](/posts/2026-02-22-local-llm-9b-vs-35b-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "32MB RAMの環境で動かすには、他に何を削ればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "OS自体のメモリ消費を削る必要があります。GUIを切り、最小構成のLinux（Alpine Linuxなど）を使い、さらにスワップ領域を高速なSSD上に確保してください。モデルも100Mパラメータ以下の超小型モデルを選定する必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "推論速度が非常に遅いのですが、改善策はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ビルド時に最適なコンパイラフラグが立っているか確認してください。また、バックグラウンドで動いている不要なプロセスを停止させるだけでも、CPUのL3キャッシュの競合が減り、速度が改善することがあります。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUがある場合は、どう設定を変えればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "CMakeの実行時に -DGGMLCUDA=ON を付けることで、GPU（CUDA）を利用したビルドが可能です。実行時に -ngl 99 （GPUレイヤー数）を指定すれば、VRAMをフル活用してさらに高速な推論が行えます。 ---"
      }
    }
  ]
}
</script>
