---
title: "OllamaとOpen WebUIで自分専用のローカルChatGPT環境を構築する方法"
date: 2026-09-26T00:00:00+09:00
slug: "ollama-openwebui-local-llm-tutorial"
cover:
  image: "/images/posts/2026-09-26-ollama-openwebui-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM RAG"
  - "Llama 3 導入"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIを一切使わず、手元のPCだけでChatGPTと同等のUIを備えた生成AI環境を構築します
- PDFやテキストファイルを読み込ませて回答させる「RAG（検索拡張生成）」がブラウザから即座に利用可能になります
- 前提知識：ターミナル（コマンドプロンプト）でコマンドをコピペして実行できること、Dockerの概念をなんとなく知っていること

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでこの価格はローカルLLM入門に最も現実的な選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPUよりも圧倒的に重要なのが「GPUのVRAM（ビデオメモリ）」です。
「Llama 3 (8B)」のような標準的なモデルをストレスなく（0.1秒以内に生成開始）動かすなら、最低でも8GBのVRAMが必要です。
「仕事で使い物になる」レベルを求めるなら、VRAM 12GB以上のRTX 3060/4070シリーズ、あるいは16GB以上のRTX 4060 Ti/4080/4090が現実的な選択肢になります。

Macユーザーの場合、メモリがそのままVRAMとして機能するため、最低16GB、できれば32GB以上のモデルを強く推奨します。
メモリ8GBのMacBook Airでも動きますが、推論速度が1秒間に数文字程度まで落ち込み、実用には耐えません。
この環境構築自体に料金はかかりませんが、電気代とハードウェア投資が唯一のコストです。

## なぜこの方法を選ぶのか

ローカルでLLMを動かすツールには「LM Studio」や「Jan」もありますが、私はあえて「Ollama + Open WebUI」の組み合わせを推します。
理由は、Open WebUIが「マルチユーザー対応」であり「RAG（ドキュメント検索）機能」が極めて優秀だからです。
LM Studioは一人で検証するには手軽ですが、複数のモデルを切り替えたり、大量のPDFを読み込ませて知識ベースを作ったりするには、Open WebUIのほうが圧倒的に実務向きです。
また、Ollamaはバックエンドとして軽量で、バックグラウンドで常駐させておけば別のアプリからAPIとして叩くのも容易です。

## Step 1: Ollamaをインストールして心臓部を作る

まずはLLMの実行エンジンであるOllamaを導入します。

```bash
# Linux/macOSの場合（公式スクリプトを実行）
curl -fsSL https://ollama.com/install.sh | sh
```

Windowsの場合は、公式サイト（ollama.com）からインストーラーをダウンロードして実行してください。
インストールが終わったら、ターミナルで以下のコマンドを叩き、モデルをダウンロードして起動できるか確認します。

```bash
ollama run llama3
```

「>>>」と表示されれば、すでにあなたのPC内でLlama 3が動いています。
適当な質問を投げて、レスポンスが返ってくることを確認してください。
確認ができたら `/bye` で終了します。

⚠️ **落とし穴:**
Windows環境でGPUが認識されない場合、NVIDIAのドライバーが古いケースが多いです。
最新版にアップデートした上で、Ollamaを再起動してください。
また、WSL2を使っている場合は、WSL側からもGPUが見えているか `nvidia-smi` コマンドで確認が必要です。

## Step 2: DockerでOpen WebUIを立ち上げる

次に、ChatGPTのような見た目のUIを提供する「Open WebUI」を導入します。
これを直接Python環境で動かそうとするとライブラリの依存関係で100%苦労するため、Dockerを使うのが正解です。

```bash
# Dockerを使ってOpen WebUIを起動するコマンド
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

このコマンドの意味を解説します。
`-p 3000:8080` は、ブラウザで `http://localhost:3000` にアクセスできるようにする設定です。
`--add-host=host.docker.internal:host-gateway` は、コンテナ内のWebUIが、ホストPC側で動いているOllamaと通信するために必須の設定です。
これを忘れると、WebUIからモデルが見えず、「Connection Error」で詰まります。
`-v open-webui:/app/backend/data` は、過去のチャット履歴やアップロードしたファイルを保存するための設定です。これがないと、Dockerを止めるたびに全てのデータが消えます。

## Step 3: ブラウザからログインしてモデルを選択する

ブラウザを開き、`http://localhost:3000` にアクセスします。
最初にアカウント作成画面が出ますが、これはローカルに保存されるだけなので、好きな名前とメールアドレスで登録してください。

ログイン後、画面左上のモデル選択メニューから「llama3:latest」を選びます。
先ほどOllamaでダウンロードしたモデルがここに表示されているはずです。

### 期待される出力

チャット画面で「こんにちは」と入力し、0.5秒以内に返答が始まれば成功です。
RTX 4090を使用している私の環境では、Llama 3 (8B) は1秒間に100トークン以上の速度で出力されます。
もし「1秒間に1〜2文字」しか出ない場合は、GPUではなくCPUで動いてしまっています。
その場合は、Dockerの設定ではなく、Ollama側がGPUを認識しているかを再確認してください。

## Step 4: 実用レベルにするための「RAG」と「Modelfile」

ここからが本番です。単なるチャットではなく、仕事で使えるツールに進化させます。

### 1. 独自ドキュメントの読み込み（RAG）
Open WebUIのチャット欄にPDFファイルをドラッグ＆ドロップしてください。
その後、プロンプトで `#` を入力すると、アップロードしたファイルが参照先として選択できます。
「この資料に基づいて、プロジェクトの懸念点を3つ挙げて」といった指示が、完全オフラインで実行可能です。
社外秘の資料をChatGPTにアップロードするわけにいかない場面で、この環境は最強の武器になります。

### 2. システムプロンプトの固定化（Modelfile）
毎回「あなたは優秀なエンジニアとして振る舞ってください」と入力するのは面倒です。
Open WebUIの「Workspace」→「Models」→「Create a Model」から、自分専用のカスタマイズモデルを作れます。

```text
# Modelfileの例
FROM llama3
PARAMETER temperature 0.7
SYSTEM """
あなたはシニアエンジニアです。
回答は簡潔に、必ず実行可能なコード例を添えて日本語で答えてください。
"""
```

このように設定して保存すれば、常に自分の好みの口調や知識レベルで回答してくれる専用AIが完成します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error (Ollama) | DockerコンテナからホストのOllamaが見えていない | Docker起動時の `--add-host` フラグを確認する |
| 生成速度が異常に遅い | VRAM不足でCPU推論に切り替わっている | より小さいモデル（Gemma-2b等）を試すかVRAMを増設する |
| 日本語が不自然 | モデル自体が日本語学習不足 | `Llama-3-Elyza` や `Gemma-2` など日本語に強いモデルをOllamaでpullする |

## 次のステップ

この環境が整ったら、次は「マルチモーダルモデル」を試してください。
Ollamaなら `ollama run llava` と打つだけで、画像を解析できるモデルが手に入ります。
Open WebUIに写真をアップロードして「この写真に写っているものを説明して」と頼めば、ローカルで画像認識まで完結します。

さらに、Pythonの `langchain` や `crewAI` と連携させるのも面白いでしょう。
Ollamaはデフォルトで `localhost:11434` でAPIを受け付けています。
自分で書いたスクリプトからこのローカルAIを呼び出し、大量のファイルを一括要約させるなどの自動化パイプラインを組むのが、実務におけるAI活用の真骨頂です。
「AIに何ができるか」を考えるフェーズから、「AIをどう組み込むか」を考えるフェーズへ進んでください。

## よくある質問

### Q1: ネット環境がなくても動きますか？

はい。モデルのダウンロード時と、Open WebUIの初回起動（コンテナイメージ取得）時以外は、完全にインターネットを切断しても動作します。飛行機の中やセキュリティの厳しいオフライン環境でも利用可能です。

### Q2: 家族やチームで共有して使えますか？

Open WebUIにはユーザー管理機能があります。PCのIPアドレスを同一LAN内に公開すれば、他のPCからブラウザ経由でアクセスしてチャットができます。ただし、同時に複数の推論を回すとVRAMが枯渇して著しく速度が低下します。

### Q3: 商用利用しても問題ないでしょうか？

使用するモデルのライセンスに依存します。例えばLlama 3は月間アクティブユーザー数が7億人を超えない限り商用利用可能です。Open WebUIやOllama自体はオープンソース（MITライセンス等）なので、ツールとしての商用利用に制限はありません。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-09-02-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIで自分専用のセキュアなローカルLLM環境を構築する方法](/posts/2026-08-23-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用のChatGPTを構築する方法](/posts/2026-06-22-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "ネット環境がなくても動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。モデルのダウンロード時と、Open WebUIの初回起動（コンテナイメージ取得）時以外は、完全にインターネットを切断しても動作します。飛行機の中やセキュリティの厳しいオフライン環境でも利用可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "家族やチームで共有して使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Open WebUIにはユーザー管理機能があります。PCのIPアドレスを同一LAN内に公開すれば、他のPCからブラウザ経由でアクセスしてチャットができます。ただし、同時に複数の推論を回すとVRAMが枯渇して著しく速度が低下します。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用しても問題ないでしょうか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "使用するモデルのライセンスに依存します。例えばLlama 3は月間アクティブユーザー数が7億人を超えない限り商用利用可能です。Open WebUIやOllama自体はオープンソース（MITライセンス等）なので、ツールとしての商用利用に制限はありません。 ---"
      }
    }
  ]
}
</script>
