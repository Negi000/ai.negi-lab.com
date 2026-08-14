---
title: "llama.cpp 使い方 入門！GGUF量子化モデルをローカルPCで動かす実践ガイド"
date: 2026-08-14T00:00:00+09:00
slug: "llamacpp-gguf-beginner-guide-local-llm"
cover:
  image: "/images/posts/2026-08-14-llamacpp-gguf-beginner-guide-local-llm.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp"
  - "GGUF量子化"
  - "ローカルLLM 構築"
  - "Llama 3 使い方"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

自分のPC（Windows/Mac/Linux）上で、オープンソースのLLMを「API料金ゼロ」で動かす推論サーバーを構築します。
具体的には、llama.cppをビルドし、Llama 3やMistralなどのGGUF形式モデルを読み込んで、ブラウザやPythonからチャットができる状態まで進めます。
Pythonの基礎知識と、ターミナルでコマンドを数行打つ覚悟があれば十分です。

## 先に確認するスペック・料金

ローカルLLMの世界では、GPUのビデオメモリ（VRAM）がすべてを決めます。
私がRTX 4090を2枚挿しているのは、単に趣味ではなく「快適な推論速度」と「モデルのサイズ」を両立させるためです。
しかし、llama.cppの最大の利点は、GPUがなくてもCPUとメインメモリ（RAM）だけで動作する点にあります。

最低限必要なスペックは、メモリ8GB以上のPCです。
16GBあれば、現在主流の「7B（70億パラメータ）」や「8B」クラスのモデルを量子化状態で余裕を持って動かせます。
逆に、4GB以下のVRAMしかない古いノートPCだと、CPU推論に頼ることになり、レスポンスが1文字ずつ「ポツ……ポツ……」と返ってくる程度になります。

もしこれからハードウェアを揃えるなら、NVIDIAのRTX 3060 12GBモデルが「安くてVRAMが多い」ため、最もコスパが良い選択肢です。
Macユーザーなら、M1以降のチップを搭載していれば、ユニファイドメモリのおかげで非常に高速に動作します。
このガイドでは、追加のAPI料金は1円もかかりません。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は、Ollama、LM Studio、LocalAIなど他にもたくさんあります。
その中で私がllama.cppを推す理由は、圧倒的な「軽量さ」と「カスタマイズ性」です。
他のツールは内部でllama.cppを動かしていることが多く、いわばllama.cppが全てのローカルLLMの「エンジン」にあたります。

エンジンを直接触れるようになると、新しいモデルが公開された数時間後には自分で量子化して試せるようになります。
また、依存ライブラリが極めて少ないため、サーバーにデプロイする際もトラブルが少ないのが実務上のメリットです。
「誰かが作ったアプリ」を使う側から、「技術の仕組みを理解して制御する側」に回るために、このアプローチがベストだと断言します。

## Step 1: 環境を整える

まずは、llama.cppを動かすための実行ファイルを作成（ビルド）します。
「ビルド」と聞くと難しそうですが、コマンドを数行打つだけです。

### Mac（Apple Silicon）の場合
Macの場合は、標準のコンパイラでMetal（GPU加速）が有効になります。

```bash
# リポジトリのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド（makeコマンド一発で終わります）
make
```

### Windows（NVIDIA GPU使用）の場合
WindowsでGPUを活かすには、CUDAツールキットがインストールされている必要があります。
ここでは、最も確実なCMakeを使った手順を紹介します。

```bash
# リポジトリのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build
cd build

# CUDAを有効にしてビルド設定（cmakeが入っている前提）
cmake .. -DGGML_CUDA=ON

# ビルド実行
cmake --build . --config Release
```

この操作で、`llama-cli`（対話用）や`llama-server`（サーバー用）という実行ファイルが生成されます。
「XXXはYYYをインストールしています」というログが流れますが、重要なのは最後にエラーが出ずに終了することです。

⚠️ **落とし穴:**
Windowsユーザーで「cmakeなんて入っていない」というエラーが出る場合、Visual Studioの「C++によるデスクトップ開発」ワークロードがインストールされていないことがほとんどです。
これだけで数GBのダウンロードが必要になるため、環境構築で一番時間がかかるポイントです。
挫折しそうなら、まずはCPU版でいいので `make` だけ試してみてください。

## Step 2: モデル（GGUF）のダウンロード

llama.cppは「GGUF」という形式のモデルファイルしか読み込めません。
Hugging Faceという、AIモデルのAmazonのようなサイトからダウンロードします。

今回は、日本語に強い「Llama-3-8B-Instruct」を量子化したものを使ってみましょう。
「量子化」とは、モデルの重みを間引いて、性能を維持しつつサイズを劇的に小さくする技術です。

おすすめは、`Bartowski`氏や`MaziyarPanahi`氏といった有名コントリビューターが公開しているGGUFファイルです。
ファイル名に「Q4_K_M」と付いているものを選んでください。
これは「4ビット量子化」を意味し、モデルのサイズを元の4分の1程度（約5GB前後）に抑えつつ、知能の低下を最小限に留めた「実務上の黄金比」的な設定です。

```bash
# llama.cppディレクトリ内にmodelsフォルダを作成
mkdir models
# ここにブラウザ等でダウンロードした .gguf ファイルを配置します
```

なぜ「Q4_K_M」なのか。
私の検証では、Q8（8ビット）にしても回答の質は体感で5%も変わりませんが、メモリ消費量は2倍になります。
逆にQ2（2ビット）まで下げると、言葉遣いが支離滅裂になります。
仕事で使うならQ4一択、少し余裕があるならQ6を選ぶのが賢い選択です。

## Step 3: 動かしてみる

いよいよ動かします。まずは最もシンプルなCLI（コマンドラインインターフェース）モードで、モデルが正常に読み込めるか確認しましょう。

```bash
# Mac/Linuxの場合
./llama-cli -m models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf -p "あなたは優秀なアシスタントです。自己紹介をしてください。" -n 128

# Windowsの場合（build/bin/Release等に実行ファイルがあるはずです）
./bin/Release/llama-cli.exe -m models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf -p "あなたは優秀なアシスタントです。自己紹介をしてください。" -n 128
```

### 期待される出力

```text
llama_print_timings: prompt eval time =     235.12 ms /    13 tokens (   18.09 ms per token,    55.29 tokens per second)
llama_print_timings:        eval time =    4521.45 ms /   127 tokens (   35.60 ms per token,    28.09 tokens per second)

こんにちは！私はAIアシスタントです。お手伝いできることがあれば教えてください。
```

結果の読み方で注目すべきは `tokens per second`（t/s）です。
これが10t/s以上なら、人間が文章を読むスピードよりも速いので「実用的」と言えます。
30t/sを超えていれば、爆速です。
もし1〜2t/sしか出ていないなら、GPUが正しく認識されていないか、メモリ不足でスワップが発生しています。

## Step 4: 実用レベルにする（サーバーモード）

CLIで動かすだけでは不便です。
llama.cppには、OpenAI API互換のHTTPサーバー機能が内蔵されています。
これを使えば、既存のOpenAI向けライブラリ（LangChainやCursorなど）を、接続先を変えるだけでそのままローカルLLMに流用できます。

```bash
# サーバーを起動
./llama-server -m models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf --port 8080 --n-gpu-layers 99
```

ここで重要なのが `--n-gpu-layers 99` です。
これは「モデルの層のうち、何層をGPUにオフロードするか」という指定です。
「99」という大きな数字を入れることで、全レイヤーをVRAMに乗せるように指示しています（VRAMが足りない場合は自動で調整されます）。
これを忘れると、たとえ高価なGPUを積んでいてもCPUで計算されてしまい、宝の持ち腐れになります。

次に、このサーバーに対してPythonからリクエストを送るスクリプトを書きましょう。

```python
import requests
import json

def chat_with_local_llm(prompt):
    url = "http://localhost:8080/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    # OpenAI API互換のフォーマット
    data = {
        "messages": [
            {"role": "system", "content": "あなたは簡潔に答える専門家です。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "stream": False
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status() # エラーがあれば例外を投げる
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"エラーが発生しました: {e}"

# 実行
if __name__ == "__main__":
    result = chat_with_local_llm("Pythonで素数を判定する関数を書いてください。")
    print(result)
```

このスクリプトを使えば、あなたの自作アプリにローカルLLMを簡単に組み込めます。
APIキーの流出を心配する必要も、月額20ドルのサブスクリプションを気にする必要もありません。
機密情報を含む社内ドキュメントの要約などをさせたい場合、この「完全オフライン」の環境が最強の武器になります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `CUDA error: out of memory` | GPUのVRAMが足りない | `--n-gpu-layers` の値を下げるか、より小さい量子化モデル（Q3など）を使う |
| `command not found: make` | 開発ツールが未インストール | Macなら `xcode-select --install`、Linuxなら `build-essential` を入れる |
| 漢字が化ける・回答が不自然 | モデル自体が日本語に未対応 | `Llama-3-8B-Instruct` や `Mistral-7B-v0.3` などの多言語対応モデルを選ぶ |
| 推論が異様に遅い | CPUで動作している | ビルド時に `GGML_CUDA=ON` を指定したか、または `--n-gpu-layers` を設定したか確認 |

## 次のステップ

ここまでで、あなたは「自分のPCで知能を飼いならす」第一歩を踏み出しました。
次にやるべきことは、このローカル環境をさらに実用的にすることです。

1. **RAG（検索拡張生成）の実装**:
   自分のPDFファイルやメモ帳をLLMに読み込ませてみましょう。ローカルLLMなら、プライベートな日記を読み込ませても誰にも見られません。

2. **モデルの比較**:
   Hugging Faceには、プログラミング特化の「DeepSeek-Coder」や、1B（10億）という超軽量な「Gemma」など、無数のモデルがあります。
   今回作った環境なら、モデルファイルを入れ替えるだけで、それぞれの得意不得意をベンチマークできます。

3. **ツールの連携**:
   VS Codeの拡張機能である「Continue」や「aider」の設定を書き換えて、ローカルのllama.cppサーバーを見るように設定してみてください。
   コーディングアシスタントが完全無料で使い放題になります。

私は、AIは「借り物（API）」から「所有物（ローカル）」になっていく過渡期にいると考えています。
自分のマシンでモデルを回し、その熱気を感じながらプロンプトを練る時間は、エンジニアとして最高にエキサイティングな体験ですよ。

## よくある質問

### Q1: GGUFと他の形式（safetensors等）は何が違うのですか？

GGUFはllama.cppのために開発された専用フォーマットです。最大の特徴は、一つのファイルに「モデルの重み」と「メタデータ（モデルの設定情報）」が全て含まれている点です。さらに、メモリに直接マップできる構造のため、読み込みが非常に高速というメリットがあります。

### Q2: 4-bit量子化で精度はどれくらい落ちますか？

研究データによれば、7B〜13Bクラスのモデルにおいて、4-bit（Q4_K_M）の精度低下はごく僅か（Perplexityという指標で数%程度）です。実務レベルのタスクであれば、回答の質よりも「VRAMに収まること」や「推論速度」のメリットの方が遥かに大きいです。

### Q3: Pythonライブラリの llama-cpp-python を使わないのはなぜですか？

llama-cpp-pythonは非常に便利ですが、ビルド時の依存関係でハマりやすいのが難点です。まずは本家llama.cppをサーバーモードで動かし、REST API経由で操作する方が、推論エンジンとアプリケーション側を分離できるため、デバッグがしやすく、私はこの構成を好みます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 3060 12GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 12GBを安価に確保でき、7Bモデルのフルオフロードに最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203060%252012GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203060%252012GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203060%2012GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cpp 使い方 入門：GGUF量子化モデルをローカルPCで爆速動作させる全手順](/posts/2026-06-20-llama-cpp-gguf-local-llm-tutorial/)
- [llama.cpp 使い方 入門：GGUF量子化モデルをローカルPCで爆速動作させる方法](/posts/2026-07-16-llamacpp-gguf-local-llm-beginner-guide/)
- [DeepSeek V4 Flash 使い方！llama.cppで最新モデルをローカル構築する手順](/posts/2026-06-06-deepseek-v4-flash-llamacpp-local-setup/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "GGUFと他の形式（safetensors等）は何が違うのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "GGUFはllama.cppのために開発された専用フォーマットです。最大の特徴は、一つのファイルに「モデルの重み」と「メタデータ（モデルの設定情報）」が全て含まれている点です。さらに、メモリに直接マップできる構造のため、読み込みが非常に高速というメリットがあります。"
      }
    },
    {
      "@type": "Question",
      "name": "4-bit量子化で精度はどれくらい落ちますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "研究データによれば、7B〜13Bクラスのモデルにおいて、4-bit（Q4KM）の精度低下はごく僅か（Perplexityという指標で数%程度）です。実務レベルのタスクであれば、回答の質よりも「VRAMに収まること」や「推論速度」のメリットの方が遥かに大きいです。"
      }
    },
    {
      "@type": "Question",
      "name": "Pythonライブラリの llama-cpp-python を使わないのはなぜですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "llama-cpp-pythonは非常に便利ですが、ビルド時の依存関係でハマりやすいのが難点です。まずは本家llama.cppをサーバーモードで動かし、REST API経由で操作する方が、推論エンジンとアプリケーション側を分離できるため、デバッグがしやすく、私はこの構成を好みます。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">GeForce RTX 3060 12GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 12GBを安価に確保でき、7Bモデルのフルオフロードに最適</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203060%252012GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203060%252012GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%203060%2012GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
