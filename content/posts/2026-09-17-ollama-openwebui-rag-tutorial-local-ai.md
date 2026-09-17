---
title: "OllamaとOpen-WebUIで構築するローカルAI検索マシンの作り方"
date: 2026-09-17T00:00:00+09:00
slug: "ollama-openwebui-rag-tutorial-local-ai"
cover:
  image: "/images/posts/2026-09-17-ollama-openwebui-rag-tutorial-local-ai.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open-WebUI 入門"
  - "ローカルLLM RAG"
  - "Llama 3.1 日本語"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- OllamaとOpen-WebUIを連携させ、自分のPC内のドキュメント（PDFやテキスト）に対して、完全にオフラインで高速に回答させるRAG（検索拡張生成）環境を構築します。
- Python環境を汚さず、Dockerを使って「コマンド一つ」で再現可能な構成にします。
- 外部APIに一切データを送らないため、仕事の機密資料や未公開のメモを読み込ませても情報漏洩の心配がないプライベート検索エンジンが手に入ります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、ターミナルでコマンドをコピペできる程度のスキルがあれば問題ありません。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのはGPUのVRAM容量です。
結論から言うと、NVIDIA製GPUでVRAM 8GB以上、もしくはApple Silicon（M1/M2/M3/M4）でメモリ16GB以上を積んだマシンが最低ラインになります。

RTX 3060（12GB版）があれば、今回使用するLlama 3.1（8B）クラスのモデルがサクサク動きます。
レスポンス速度は1秒間に50〜80トークン程度出るため、人間が読むスピードを遥かに超える快適さです。
VRAMが8GBを下回るとメインメモリ（RAM）へのスワップが発生し、レスポンスが0.5秒/1トークン程度まで落ちるため、実用には耐えません。

Macユーザーの場合、メモリ（ユニファイドメモリ）がLLMの動作領域になるため、最低16GB、できれば32GB以上を推奨します。
MacBook Airのメモリ8GBモデルでも動作はしますが、RAGで長文を読み込ませると一気に重くなるのが現実です。
費用面では、OllamaもOpen-WebUIもオープンソースなので、電気代以外は完全無料です。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールはLM StudioやAnythingLLMなど他にもありますが、私は「Open-WebUI」一択だと考えています。
最大の理由は、ChatGPTとほぼ同等のインターフェースを持ちながら、RAG（ドキュメント読み込み）の精度設定や、複数のモデルを並行して動かす「ツール連携」が最も強力だからです。

他のツールは「動かして終わり」になりがちですが、Open-WebUIはマルチユーザー管理機能もあり、自宅サーバーに立てて家族やチームで共有するといった実務的な運用に耐えられます。
また、Redditの r/LocalLLaMA コミュニティでも最も活発に開発が進んでおり、新機能の追加スピードが異常に速いのも魅力です。

## Step 1: 環境を整える

まずは土台となるDocker Desktopをインストールしてください。
すでに導入済みの方は、以下のコマンドでNVIDIA GPUをDockerから認識させるためのツール（Windows/Linuxの場合）が入っているか確認しましょう。

```bash
# NVIDIA Container Toolkitのインストール確認（Linuxの場合）
nvidia-smi
```

次に、LLMの実行エンジンである「Ollama」をインストールします。

```bash
# macOS/Linuxの場合（公式バイナリを推奨）
curl -fsSL https://ollama.com/install.sh | sh
```

Windowsの場合は公式サイトからインストーラーをダウンロードして実行するだけでOKです。
Ollamaは「モデルのダウンロード」と「推論サーバー」を兼ねており、これ単体でも動きますが、GUIがないためOpen-WebUIと組み合わせます。

⚠️ **落とし穴:** WSL2上でDockerを動かしているWindowsユーザーは、GPUパススルーの設定を忘れがちです。`nvidia-smi` コマンドがWSL内で動かない限り、LLMはCPUで動作し、驚くほど遅くなります。最新のNVIDIAドライバーをホスト側にインストールすれば、最近のWSL2なら自動で認識されるはずです。

## Step 2: 基本の設定

Ollamaがインストールできたら、今回使用するモデルをダウンロードします。
実務で最もバランスが良いのは、Metaが公開した「Llama 3.1 8B」です。

```bash
# ターミナルで実行
ollama pull llama3.1
```

なぜLlama 3.1なのか。それは、日本語能力が飛躍的に向上しており、かつRAGで長いコンテキスト（文章）を読み込ませても破綻しにくい「128kトークン」に対応しているからです。

次に、Open-WebUIをDockerで起動します。
以下のコマンドは、Ollamaが同じマシンで動いていることを想定した設定です。

```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

このコマンドのポイントは `--add-host` オプションです。
Dockerコンテナの中から、ホストマシンで動いているOllama（ポート11434）にアクセスするために必要となります。
`-v open-webui:/app/backend/data` は、アップロードした書類やチャット履歴を永続化するための設定です。これがないと、コンテナを再起動した瞬間にデータがすべて消えます。

## Step 3: 動かしてみる

ブラウザを開き、 `http://localhost:3000` にアクセスしてください。
最初の画面でアカウント作成を求められますが、これはローカルに保存されるだけなので、好きなメールアドレスとパスワードで登録してログインします。

1. 画面上部のモデル選択メニューから「llama3.1:latest」を選択。
2. 下部のチャット欄に「こんにちは、自己紹介して」と入力。

### 期待される出力

```text
こんにちは！私はMetaによってトレーニングされたLlama 3.1という大規模言語モデルです。
日本語での対話や要約、プログラミングのサポートなどが可能です。何かお手伝いできることはありますか？
```

レスポンスが返ってきたら、右下の「設定（歯車アイコン）」から「設定」→「一般」に進み、言語を日本語に変更しておきましょう。

## Step 4: 実用レベルにする

ここからが本番です。単なるチャットボットではなく、自分の資料を読み込ませるRAG環境を作ります。
Open-WebUIには標準でRAG機能が組み込まれています。

1. チャット欄の左側にある「＋」アイコン、もしくはクリップアイコンをクリックします。
2. 手持ちのPDFファイル（例：製品マニュアル、社内規定、自分の過去のブログ記事など）をアップロードします。
3. チャット欄に `#` （ハッシュマーク）を入力すると、アップロードしたファイル名が表示されるので選択します。
4. 「この資料の内容を要約して、重要な3点を教えて」と入力します。

このとき、Open-WebUIの裏側では以下の処理が走っています。
- PDFをテキストに分解
- 文をベクトル化（Embedding）してデータベースに保存
- 質問に関連する部分だけを抽出してLLMに渡す

### 実用的なコード（API経由での一括処理）

もし大量のドキュメントを外部プログラムから一括で処理したい場合は、OllamaのAPIを直接叩くのが速いです。
Pythonを使って、特定のフォルダ内のテキストをすべて要約させるスクリプトの例を紹介します。

```python
import requests
import json
import os

# Ollama APIエンドポイント（デフォルト）
OLLAMA_URL = "http://localhost:11434/api/generate"

def summarize_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # ローカルモデルを呼び出す
    # stream=Falseにすることで、生成が終わるまで待機する
    payload = {
        "model": "llama3.1",
        "prompt": f"以下の文章を200文字程度で要約してください:\n\n{content}",
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        return f"エラーが発生しました: {e}"

# 実行例
if __name__ == "__main__":
    summary = summarize_file("my_note.txt")
    print(f"--- 要約結果 ---\n{summary}")
```

このスクリプトのミソは、`requests` ライブラリだけで動く点です。
複雑なLangChainなどを使わなくても、OllamaのAPIはシンプルなので、これだけで十分実務に組み込めます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Refused | Ollamaが起動していない、またはポートが閉じている | Ollamaを起動し、環境変数 `OLLAMA_HOST=0.0.0.0` を確認する |
| 生成が異様に遅い | GPUではなくCPUで動作している | DockerにGPUを割り当てる設定（--gpus all）を追加して再起動する |
| RAGで日本語が化ける | PDFのエンコーディング問題 | 一度テキストファイルに変換してからアップロードするか、PDFのOCR処理を確認する |

## 次のステップ

ここまでで、自分専用のプライベートAI環境が整いました。
次に挑戦すべきは「Web Search機能の統合」です。
Open-WebUIの設定画面にある「Web Search」を有効にし、SearXNGなどの検索エンジンと連携させると、最新のニュースを含めた回答がローカルLLMで可能になります。

また、Redditの `r/LocalLLaMA` では、最近「Granite-3.0」というIBMのモデルも話題です。
Llamaよりも軽量でありながら、プログラミングやRAGに特化しているため、`ollama pull granite3-dense` で試してみる価値はあります。
自分の業務に最適なモデルを「pull」して「試す」。この試行錯誤のコストがゼロなのがローカルLLMの最大の醍醐味です。

## よくある質問

### Q1: クラウド版（ChatGPT等）と比較して、回答の精度はどうですか？

正直に言うと、GPT-4oと比較すれば劣ります。しかし、Llama 3.1 8BはGPT-3.5を完全に凌駕しており、特定の専門文書に基づいた回答（RAG）であれば、外部に漏らせないデータを扱えるという圧倒的なメリットが精度の差を埋めます。

### Q2: 複数のPDFを一度に読み込ませることはできますか？

可能です。Open-WebUIの「ドキュメント」メニューから、フォルダごとアップロードして「コレクション」としてまとめられます。チャット時に `#コレクション名` で指定すれば、数千ページの資料を横断的に検索できます。

### Q3: 自分のPCを外部からアクセスできるようにしたいです。

セキュリティ上、基本的にはおすすめしません。どうしてもやりたい場合は、VPN（Tailscale等）を使いましょう。グローバルIPを公開してポート開放するのは、LLMの脆弱性を突かれるリスクがあるため、社内LAN内での運用に留めるべきです。

---

## あわせて読みたい

- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-06-28-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用のセキュアなローカルLLM環境を構築する方法](/posts/2026-08-23-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-07-05-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "クラウド版（ChatGPT等）と比較して、回答の精度はどうですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "正直に言うと、GPT-4oと比較すれば劣ります。しかし、Llama 3.1 8BはGPT-3.5を完全に凌駕しており、特定の専門文書に基づいた回答（RAG）であれば、外部に漏らせないデータを扱えるという圧倒的なメリットが精度の差を埋めます。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のPDFを一度に読み込ませることはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Open-WebUIの「ドキュメント」メニューから、フォルダごとアップロードして「コレクション」としてまとめられます。チャット時に #コレクション名 で指定すれば、数千ページの資料を横断的に検索できます。"
      }
    },
    {
      "@type": "Question",
      "name": "自分のPCを外部からアクセスできるようにしたいです。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "セキュリティ上、基本的にはおすすめしません。どうしてもやりたい場合は、VPN（Tailscale等）を使いましょう。グローバルIPを公開してポート開放するのは、LLMの脆弱性を突かれるリスクがあるため、社内LAN内での運用に留めるべきです。 ---"
      }
    }
  ]
}
</script>
