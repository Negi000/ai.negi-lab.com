---
title: "llama.cpp 使い方 入門！GGUF量子化でローカルLLMを動かす実践ガイド"
date: 2026-10-16T00:00:00+09:00
slug: "llamacpp-gguf-beginner-guide-setup"
cover:
  image: "/images/posts/2026-10-16-llamacpp-gguf-beginner-guide-setup.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp"
  - "GGUF"
  - "量子化"
  - "Llama 3"
  - "ローカルLLM 構築"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

自分のPCリソースを最大限に活用し、Llama 3やMistralなどの最新大規模言語モデル（LLM）を高速に動作させる「推論サーバー」を構築します。
Pythonのライブラリ依存に悩まされることなく、シングルバイナリで軽量に動作し、他のアプリ（Cursorや独自スクリプト）からAPI経由で呼び出せる環境を完成させます。

前提知識：
- ターミナル（コマンドプロンプト）の基本操作ができる
- Gitの基本的な使い方がわかる
- Pythonがインストールされている（Step 4で使用）

必要なもの：
- メモリ（RAM）が8GB以上のPC（16GB以上を強く推奨）
- インターネット環境（数GBのモデルをダウンロードするため）
- NVIDIA製GPU（あれば高速化可能。なくてもCPUで動作可能）

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」と「メインメモリ」の容量です。
私がRTX 4090を2枚挿しているのは、量子化なしの巨大モデルを動かすためですが、llama.cppとGGUF形式を使えば、一般的なノートPCでも十分戦えます。

目安として、7B（70億パラメータ）クラスのモデルを動かすなら、メモリは最低8GB必要です。
ただし、OSが使用する分を考慮すると、16GB以上のメモリを積んだPCでないと動作が極端に重くなり、実用的ではありません。
Macユーザーなら、M1/M2/M3チップを搭載したメモリ16GB以上のモデルであれば、非常に快適なレスポンス（秒間15〜20トークン以上）が得られます。

Windows環境でGPUを使いたい場合は、NVIDIAのRTX 3060（VRAM 12GB）以上があれば、現行の主要な軽量モデルはすべてGPUメモリに収まり、ChatGPT並みの速度で動作します。
逆に、VRAM 4GB程度の古いエントリーモデルを使っているなら、無理にGPUを使わず、メインメモリを増設してCPUで動かす方が安定します。
API料金は一切かかりません。電気代とPC代だけがコストです。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす方法はいくつかあります。Pythonの「Transformers」ライブラリを使う方法や、「Ollama」を使う方法が有名です。
しかし、あえて「llama.cpp」を直接使う理由は、その圧倒的な「軽さ」と「透明性」にあります。

Python版は、依存ライブラリ（PyTorchなど）だけで数GBのディスク容量を食いつぶし、バージョン競合で動かなくなることが多々あります。
対してllama.cppはC++で書かれたシングルバイナリに近く、無駄なオーバーヘッドがありません。
また、GGUFというファイル形式は、重みデータとメタデータを一つのファイルに詰め込めるため、管理が非常に楽です。

私が開発現場で「仕事に使えるか」を判断する際、この「環境構築の再現性」と「リソース消費の少なさ」を最優先します。
Ollamaも中身はllama.cppですが、裏側で何が起きているか把握し、細かいパラメータ（コンテキスト長やGPUオフロード数）を制御するには、本家llama.cppを直接叩くのがベストな選択です。

## Step 1: 環境を整える

まずはllama.cppを自分のPCで動かせる状態にします。
ソースコードからビルドするのが一番確実で、最新の最適化を享受できます。

### Mac（Apple Silicon）の場合
```bash
# リポジトリをクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Metal（GPU加速）を有効にしてビルド
cmake -B build -DGGML_METAL=ON
cmake --build build --config Release -j
```

### Windows（NVIDIA GPUあり）の場合
```bash
# git clone済みとして
# CUDAを有効にしてビルド（CUDA Toolkitがインストールされている前提）
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j
```

`cmake` コマンドは、自分のPC環境に合わせて「どうやってコンパイルするか」の設計図を作る作業です。
`-DGGML_METAL=ON` や `-DGGML_CUDA=ON` を指定することで、CPUだけでなくGPUも計算に参加させるよう指示しています。
これを忘れると、どれだけ高価なGPUを積んでいてもCPUだけで計算することになり、動作が数倍遅くなります。

⚠️ **落とし穴:**
Windowsユーザーで `cmake` が入っていない場合、Visual Studioの「C++によるデスクトップ開発」ワークロードが必要です。
これが入っていないと、コンパイルエラーで「コンパイラが見つかりません」と言われます。
面倒に感じるかもしれませんが、一度ビルドしてしまえば、後はバイナリをコピーするだけでどこでも動くのがllama.cppの強みです。

## Step 2: 基本の設定

llama.cpp本体ができたら、次は「脳」にあたるモデルデータ（GGUF形式）を用意します。
Hugging Faceからダウンロードするのが一般的です。

今回は、日本語能力が高い「Llama-3-8B」の量子化版を使用します。
ファイルを探す際は、ファイル名に `Q4_K_M` と付いているものを選んでください。

```bash
# モデルを格納するディレクトリを作成
mkdir models

# Hugging Faceからモデルをダウンロード（例：Bartowski氏のレポジトリなどから）
# 実際にはブラウザでダウンロードして models/ ディレクトリに配置してください。
# 推奨ファイル：Meta-Llama-3-8B-Instruct-Q4_K_M.gguf
```

なぜ `Q4_K_M` なのか。
量子化とは、モデルの重み（データの精度）を間引いて軽くする技術です。
本来16bitあるデータを4bitに圧縮すると、ファイルサイズは1/4になりますが、精度は数%しか落ちません。
私の検証では、8bit（Q8_0）と4bit（Q4_K_M）を比較しても、日常的なタスクでの回答精度に体感できるほどの差はありませんでした。
逆に、4bitにすることでVRAM消費が劇的に減り、より長い文脈を扱えるようになります。

## Step 3: 動かしてみる

準備が整いました。まずはターミナル上で対話してみましょう。
ビルドした実行ファイルは `build/bin/` の中にあります。

```bash
# インタラクティブモードで起動
./build/bin/llama-cli \
  -m models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf \
  -n 512 \
  --prio 2 \
  -ngl 33 \
  -p "あなたは優秀なアシスタントです。日本語で回答してください。 \nユーザー: 自己紹介をしてください。 \nアシスタント:"
```

各オプションの意味：
- `-m`: モデルファイルのパス。
- `-n`: 生成する最大トークン数。
- `-ngl`: GPUに送るレイヤー数。Llama-3-8Bなら33を指定すれば、全計算がGPUで行われます（VRAMが足りない場合はこの数字を下げます）。
- `-p`: プロンプト（指示文）。

### 期待される出力

```text
私はAIアシスタントです。あなたの質問に答えたり、文章を作成したり、プログラミングのサポートをしたりすることができます。何かお手伝いできることはありますか？
```

レスポンスの最後に「tokens per second」という数字が出ます。これが10以上なら実用的、30以上なら爆速です。
もし動作が極端に遅い場合は、`-ngl` の値を確認してください。0になっているとCPUだけで動いています。

## Step 4: 実用レベルにする

ターミナルで対話するだけでは「仕事で使える」とは言えません。
llama.cppを「サーバー」として立ち上げ、Pythonや他のアプリからAPIとして叩けるようにします。

```bash
# サーバーモードで起動
./build/bin/llama-server \
  -m models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf \
  --port 8080 \
  -ngl 33
```

これで、`http://localhost:8080` でOpenAI互換のAPIサーバーが立ち上がりました。
次に、Pythonからこのサーバーを利用するスクリプトを書きます。

```python
import requests
import json

def ask_local_llm(prompt):
    url = "http://localhost:8080/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    # OpenAI APIと同じ形式のペイロード
    data = {
        "messages": [
            {"role": "system", "content": "丁寧な日本語で回答するAIです。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "stream": False
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code}"

# 実行
if __name__ == "__main__":
    answer = ask_local_llm("Pythonで素数を判定する関数を書いて。")
    print(answer)
```

この方法の凄さは、既存のOpenAI SDKを使っているツール（Cursorや各種エージェントツール）の接続先を `localhost:8080` に変えるだけで、そのままローカルLLMに差し替えられる点にあります。
実際に私は、機密性の高いコードを書く際はCursorの接続先をこのローカルサーバーに切り替えています。
外部にデータが飛ばない安心感と、サブスク料金を気にせず無限に試行錯誤できる自由度は、一度味わうと戻れません。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `error loading model` | ファイルが壊れている、またはGGUF形式ではない | モデルを再ダウンロードし、拡張子が `.gguf` であることを確認する |
| `out of memory` | VRAMまたはRAMが不足している | `-ngl` の値を下げるか、より小さい量子化（Q2_Kなど）のモデルを使う |
| `command not found` | ビルドが失敗している、またはパスが通っていない | `ls build/bin` で実行ファイルが存在するか確認する |

## 次のステップ

ここまでできれば、あなたのPCは立派なAI開発環境です。
次に挑戦してほしいのは「複数のモデルの使い分け」です。
論理的思考が必要なコード生成なら「Llama-3-70B」のQ3量子化版（メモリ40GB程度必要ですが）、サクッと要約するだけなら「Gemma-2B」といった具合に、タスクに合わせてモデルを入れ替えてみてください。

また、llama.cppには「文法制限（Grammar）」という強力な機能があります。
出力を必ずJSON形式に強制したり、特定の単語リストから選ばせたりすることができます。
これをマスターすると、LLMの不安定な出力をパースする苦労から解放され、一気にシステムとしての信頼性が高まります。
ローカルLLMは、もはや「おもちゃ」ではなく、工夫次第で商用サービスに組み込める「道具」です。

## よくある質問

### Q1: AMDのGPUでも動きますか？

はい、動きます。ビルド時に `-DGGML_HIPBLAS=ON` を指定してください（ROCmがインストールされている必要があります）。ただし、NVIDIAやApple Siliconに比べると環境構築の難易度は少し上がります。

### Q2: 量子化すると、どのくらい頭が悪くなりますか？

4bit（Q4_K_M）程度であれば、ベンチマークスコアの低下は数%以内です。それよりも、量子化によって浮いたメモリで「より大きなパラメータを持つモデル」を動かす方が、トータルの賢さは圧倒的に向上します。

### Q3: サーバーとして公開して外部から使えますか？

可能ですが、llama.cppのサーバー機能には標準で認証機能がありません。外部に公開する場合は、リバースプロキシ（Nginxなど）を挟んで認証を追加するか、VPN経由でアクセスするようにしてください。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3 8Bクラスを余裕で全オフロード可能な、入門に最適なGPUです。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cpp 使い方 入門！GGUF量子化モデルをローカルPCで動かす実践ガイド](/posts/2026-08-14-llamacpp-gguf-beginner-guide-local-llm/)
- [llama.cppとGGUFでローカルLLMを動かす Pythonによる実装ガイド](/posts/2026-06-14-llama-cpp-python-gguf-tutorial-beginners/)
- [llama.cppとGGUF量子化の使い方入門：自作PCやMacでLLMを動かす全手順](/posts/2026-10-07-llamacpp-gguf-beginner-guide-setup/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "AMDのGPUでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、動きます。ビルド時に -DGGMLHIPBLAS=ON を指定してください（ROCmがインストールされている必要があります）。ただし、NVIDIAやApple Siliconに比べると環境構築の難易度は少し上がります。"
      }
    },
    {
      "@type": "Question",
      "name": "量子化すると、どのくらい頭が悪くなりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "4bit（Q4KM）程度であれば、ベンチマークスコアの低下は数%以内です。それよりも、量子化によって浮いたメモリで「より大きなパラメータを持つモデル」を動かす方が、トータルの賢さは圧倒的に向上します。"
      }
    },
    {
      "@type": "Question",
      "name": "サーバーとして公開して外部から使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能ですが、llama.cppのサーバー機能には標準で認証機能がありません。外部に公開する場合は、リバースプロキシ（Nginxなど）を挟んで認証を追加するか、VPN経由でアクセスするようにしてください。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでLlama 3 8Bクラスを余裕で全オフロード可能な、入門に最適なGPUです。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
