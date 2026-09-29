---
title: "llama.cpp 使い方 入門！GGUF量子化でローカルLLMを動かす全手順"
date: 2026-09-29T00:00:00+09:00
slug: "llamacpp-gguf-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-09-29-llamacpp-gguf-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "Llama 3.1 ローカル環境"
  - "Python LLM 構築"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

この記事では、ローカル環境でLlama 3.1やMistralといった最新のLLM（大規模言語モデル）を高速に動作させる「llama.cpp」の環境を構築します。
最終的には、自分のPC内でOpenAI互換のAPIサーバーを立ち上げ、PythonスクリプトからAIを呼び出して自由自在に操作できる状態を目指します。

- ローカルLLMを動かすためのllama.cppビルド環境
- Hugging Faceからの最適なGGUFモデル選定とダウンロード
- PythonからローカルLLMを呼び出す推論スクリプト

前提知識：基本的なコマンドライン操作（cd, mkdir等）ができること、Pythonの基礎知識。
必要なもの：NVIDIA製GPUを搭載したPC、またはApple Silicon（M1/M2/M3）搭載のMac。

## 先に確認するスペック・料金

ローカルLLMの世界では、何よりも「VRAM（ビデオメモリ）」の容量が正義です。
目安として、7B（70億パラメータ）クラスのモデルを快適に動かすならVRAM 8GB以上、14Bクラスなら12GB〜16GB、70Bクラスを狙うなら48GB以上（RTX 3090/4090の2枚挿しなど）が必要になります。

Windowsユーザーでこれからハードウェアを揃えるなら、現状の最適解は「RTX 4060 Ti 16GB版」です。
3000番台の中古RTX 3090（24GB）も魅力的ですが、消費電力とワットパフォーマンスを考えると、個人開発レベルでは4060 Ti 16GBが最も安上がりで深く遊べます。

Macユーザーの場合、メモリがCPUと共通化されている「ユニファイドメモリ」が強力な武器になります。
メモリ16GBのMacBook Airでも7Bモデルならサクサク動きますが、本格的にやりたいならメモリ32GB以上のモデルを選ばないと、モデルをロードした瞬間にOSごと落ちる悲劇に見舞われます。

料金面については、llama.cppもモデルファイルもすべてオープンソースなので、電気代以外は完全に「無料」です。
APIの従量課金に怯えながらプロンプトを投げる日々からは、今日で卒業しましょう。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす方法は、Pythonの`transformers`ライブラリを使う方法や、`Ollama`のようなパッケージを使う方法など、いくつか存在します。
その中で私が「llama.cpp」を強く推す理由は、圧倒的な推論速度と、メモリ消費量の少なさにあります。

llama.cppはC++で書かれており、Pythonを介さずにハードウェアの性能を限界まで引き出します。
また「GGUF」という形式に量子化されたモデルを使用することで、元のモデル精度をほぼ維持したまま、ファイルサイズと使用メモリを4分の1程度まで圧縮できます。

Ollamaは内部でllama.cppを使っていますが、カスタマイズ性や最新機能の追従速度では本家llama.cppに軍配が上がります。
エンジニアとして「中身がどう動いているか」を把握し、仕事で使えるレベルの細かいパラメータ調整を行うなら、直接llama.cppを触る経験が不可欠です。

## Step 1: 環境を整える

まずはllama.cppを自分のPCのハードウェアに最適化した状態でビルド（コンパイル）します。
「ビルド済みバイナリ」を拾ってくる方法もありますが、自分でビルドしたほうが、お使いのGPUの性能を100%発揮できるため、私はこの方法しか推奨しません。

### Mac（Apple Silicon）の場合
Macの場合はXcode Command Line Toolsが必要です。ターミナルで以下を実行してください。

```bash
# ビルドツールのインストール
xcode-select --install

# リポジトリのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド（MetalというMac専用のGPU加速を有効にします）
make -j
```

### Windows（NVIDIA GPU）の場合
Windowsでは「CMake」と「Visual Studio 2022」のビルドツールが必要です。
さらに、GPUを使うためにCUDA Toolkit（12.x推奨）をインストールしておいてください。

```powershell
# リポジトリのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド用ディレクトリの作成
mkdir build
cd build

# CUDAを有効にして構成
cmake .. -DGGML_CUDA=ON

# ビルドを実行（Releaseモード）
cmake --build . --config Release
```

⚠️ **落とし穴:**
Windowsユーザーで、ビルド中に「CUDA not found」といったエラーが出る場合、環境変数 `PATH` にCUDAのbinディレクトリが含まれているか確認してください。
また、ビルド完了後に `llama-cli.exe` が生成されていない場合は、CMakeの出力ログを遡ってエラーを特定する必要があります。多くの場合、Visual Studioの「C++によるデスクトップ開発」ワークロードの入れ忘れが原因です。

## Step 2: 基本の設定

ビルドが終わったら、次は動かしたいAIモデル（GGUF形式）を入手します。
Hugging Faceというサイトで検索しますが、自分で量子化するのは手間なので、信頼できる職人が公開しているものを使わせてもらいましょう。

おすすめは `Bartowski` 氏や `MaziyarPanahi` 氏が公開しているリポジトリです。
今回は「Llama-3.1-8B-Instruct」のGGUF版を例に進めます。

1. Hugging Faceで `Llama-3.1-8B-Instruct-GGUF` を検索します。
2. 「Files and versions」タブを開きます。
3. `Q4_K_M.gguf` というファイルを探してダウンロードします。

**なぜ Q4_K_M なのか？**
量子化ビット数には「Q2」から「Q8」までありますが、数値が小さいほど軽く、大きいほど高精度です。
私の検証結果では、4ビット（Q4）が「精度低下が体感できず、かつメモリを大幅に節約できる」スイートスポットです。
迷ったら `Q4_K_M` を選べば間違いありません。

ダウンロードしたファイルは、llama.cppディレクトリ内に `models` というフォルダを作って移動させておきます。

## Step 3: 動かしてみる

いよいよ動かします。まずはAPIサーバーとして起動させ、外部（Python）から叩ける状態にします。
これが実務で最も汎用性の高い動かし方です。

```bash
# Mac/Linuxの場合
./llama-server -m models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf -ngl 33 -c 4096

# Windowsの場合（build/bin/Release等にあるexeを指定）
./bin/Release/llama-server.exe -m models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf -ngl 33 -c 4096
```

設定値の理由：
- `-m`: モデルファイルのパス。
- `-ngl 33`: GPUにオフロードするレイヤー数。Llama-3 8Bは約33レイヤーなので、全部GPUに乗せるなら33（またはそれ以上）を指定します。これによって爆速になります。
- `-c 4096`: コンテキストサイズ。一度に扱えるトークン数です。仕事で使うなら4096〜8192程度は確保しましょう。

### 期待される出力

サーバーが起動すると、ターミナルに以下のようなログが流れます。

```
HTTP server listening: http://127.0.0.1:8080
```

この状態でブラウザから `http://localhost:8080` にアクセスすると、簡易的なチャット画面が表示されます。
まずはそこで「こんにちは、自己紹介して」と送ってみてください。
秒間30〜100トークン程度の速度で返文が来れば、成功です。

## Step 4: 実用レベルにする

サーバーが立ち上がったら、今度はPythonからこのローカルLLMを制御します。
llama.cppのサーバーモードはOpenAI APIと互換性があるため、`openai`ライブラリをそのまま使えます。

まず、ライブラリをインストールします。

```bash
pip install openai
```

次に、以下のスクリプトを作成して実行してください。

```python
import openai

# ローカルで立ち上げたllama-serverを指すように設定
client = openai.OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="sk-no-key-required" # ローカルなので何でも良い
)

def ask_local_llm(prompt):
    try:
        response = client.chat.completions.create(
            model="local-model", # llama-server側で指定したモデル名が反映される
            messages=[
                {"role": "system", "content": "あなたは優秀なエンジニアです。簡潔に回答してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, # 創造性の調整。0に近いほど確実な回答になる
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {e}"

if __name__ == "__main__":
    question = "Pythonで高速な素数判定アルゴリズムを書いて。"
    answer = ask_local_llm(question)
    print(f"--- 回答 ---\n{answer}")
```

このコードのポイントは、`base_url` をローカルホストに変更している点だけです。
これだけで、既存のOpenAI向けに書かれたコードを1行も変えずにローカルLLMへ差し替えることが可能になります。
機密情報を扱う業務で、「外部にデータを送りたくないがLLMの力は借りたい」という場面で最強のソリューションになります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `error loading model` | RAM/VRAM不足 | モデルの量子化ビット数を下げる（Q4→Q2）か、小さいモデル（3Bクラス）を試す。 |
| 推論がめちゃくちゃ遅い | GPUが使われていない | `-ngl` オプションが0になっていないか確認。ビルド時にCUDA/Metalが有効になっていない可能性が高い。 |
| 回答が途中で切れる | `-n` または `-c` 不足 | 起動引数の `-c` (context) の値を増やす。 |
| 日本語が文字化けする | モデルが日本語非対応 | Llama 3.1 InstructやCommand Rなど、多言語対応を謳っているモデルを使用する。 |

## 次のステップ

無事に動かせたなら、次は「RAG（検索拡張生成）」に挑戦してみてください。
自分の持っているPDFやテキストファイルをベクトル化してデータベースに入れ、llama.cpp経由で回答させるシステムです。

具体的には `LangChain` や `LlamaIndex` と組み合わせて、今回作った `base_url` を指定するだけです。
また、VS Codeの拡張機能である `Continue` や `Cursor` のバックエンドとしてこのローカルサーバーを指定すれば、コード生成も完全オフライン・無料で実行できるようになります。

RTX 4090などの上位GPUを持っているなら、複数のモデルを同時に立ち上げて、AI同士を議論させるエージェントシステムの構築も面白いでしょう。
ローカルLLMは、自由度こそが最大の価値です。

## よくある質問

### Q1: グラボがない古いノートPCでも動きますか？

動きますが、速度は期待しないでください。llama.cppはCPU（AVX2/AVX512命令）もフル活用するため、最近のCore i7等なら、7Bモデルで秒間2〜5トークン程度は出ます。黙々と文章を生成させるバッチ処理なら実用圏内です。

### Q2: どのGGUFファイルを選べばいいか分かりません。

基本は `Q4_K_M` です。メモリに余裕があるなら `Q5_K_M` や `Q6_K` を。逆にメモリがカツカツで、どうしても動かしたいなら `IQ3_S` などを試してください。3ビット以下は知能が目に見えて落ちるので、検証用と割り切るべきです。

### Q3: llama.cppを最新版に更新するには？

`git pull` してから、Step 1と同じビルドコマンドを叩き直すだけです。llama.cppは開発速度が異常に早く、週単位で新しいモデルへの対応や高速化が行われるため、月1回は更新することをおすすめします。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBで7B〜14Bモデルをフルロードできる、ローカルLLM入門の最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cpp 使い方 入門 | GGUF量子化でローカルLLMを動かす](/posts/2026-08-06-llamacpp-gguf-python-setup-guide/)
- [llama.cpp 使い方 入門：GGUF量子化モデルをローカルPCで爆速動作させる全手順](/posts/2026-06-20-llama-cpp-gguf-local-llm-tutorial/)
- [llama.cpp 使い方 入門 (GGUF量子化でローカルLLMを動かす方法)](/posts/2026-07-19-llamacpp-gguf-setup-guide-for-beginners/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "グラボがない古いノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、速度は期待しないでください。llama.cppはCPU（AVX2/AVX512命令）もフル活用するため、最近のCore i7等なら、7Bモデルで秒間2〜5トークン程度は出ます。黙々と文章を生成させるバッチ処理なら実用圏内です。"
      }
    },
    {
      "@type": "Question",
      "name": "どのGGUFファイルを選べばいいか分かりません。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本は Q4KM です。メモリに余裕があるなら Q5KM や Q6K を。逆にメモリがカツカツで、どうしても動かしたいなら IQ3S などを試してください。3ビット以下は知能が目に見えて落ちるので、検証用と割り切るべきです。"
      }
    },
    {
      "@type": "Question",
      "name": "llama.cppを最新版に更新するには？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "git pull してから、Step 1と同じビルドコマンドを叩き直すだけです。llama.cppは開発速度が異常に早く、週単位で新しいモデルへの対応や高速化が行われるため、月1回は更新することをおすすめします。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBで7B〜14Bモデルをフルロードできる、ローカルLLM入門の最適解</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
