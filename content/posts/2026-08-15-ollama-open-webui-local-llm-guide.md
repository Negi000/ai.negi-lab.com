---
title: "OllamaとOpen WebUIで自分専用のローカルChatGPT環境を構築する方法"
date: 2026-08-15T00:00:00+09:00
slug: "ollama-open-webui-local-llm-guide"
cover:
  image: "/images/posts/2026-08-15-ollama-open-webui-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "ローカルLLM 構築"
  - "Llama 3 実行方法"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- インターネット接続不要で、ChatGPTと同等のUIを備えたプライバシー重視のAIチャット環境を構築します。
- 前提知識：基本的なコマンド操作（コピペでOK）と、Dockerの概念をなんとなく理解していること。
- 必要なもの：NVIDIA製GPUを搭載したWindows/Linux PC、またはApple Silicon搭載のMac。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載で、現行の主要なローカルLLMを最も快適かつ安価に動かせる選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU性能よりも重要なのが「VRAM（ビデオメモリ）」の容量です。結論から言うと、VRAMが8GBあれば最低限動きますが、快適に実務で使うなら12GB以上、欲を言えば16GB以上を推奨します。

Windowsユーザーなら「RTX 3060 12GB」や「RTX 4060 Ti 16GB」が、コストパフォーマンスの面でエントリーモデルとしての最適解です。ハイエンドを狙うなら、私が使っている「RTX 4090 24GB」一択ですが、これは約28万円〜と非常に高価です。

Macユーザーの場合、メモリが「ユニファイドメモリ」としてCPUとGPUで共有されるため、最低でも16GB、できれば32GB以上のモデルを選んでください。8GBモデルでは、OSの動作分でメモリが食いつぶされ、モデルのロード時にスワップが発生してレスポンスが10秒以上遅れる「使い物にならない状態」に陥ります。

料金については、電気代以外は完全に無料です。API利用料を気にせず、1日に何万トークン消費しても追加の請求は発生しません。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段には「LM Studio」や「GPT4All」などもありますが、私はあえて「Ollama + Open WebUI」の組み合わせを推奨します。理由は、この構成が最も「本家のChatGPT」に近く、かつ拡張性が高いからです。

Open WebUIは、PDFをアップロードして内容を解析するRAG（検索拡張生成）機能や、Web検索機能、画像生成AI（Stable Diffusion等）との連携機能が標準で備わっています。また、Dockerで構築するため、環境を汚さずにアップデートや削除が容易であることも大きなメリットです。一度この環境を作っておけば、新しいモデル（Llama 3.1やQwen 2.5など）が登場した際も、コマンド一つで即座に試せるようになります。

## Step 1: 環境を整える

まずは、LLMの実行エンジンである「Ollama」をインストールします。

### Mac / Windowsの場合
公式サイト（ollama.com）からインストーラーをダウンロードして実行してください。インストール後、ターミナル（またはコマンドプロンプト）を開き、以下のコマンドを打ちます。

```bash
ollama --version
```

バージョン番号が表示されれば成功です。

### Linuxの場合
以下の1コマンドでインストールが完了します。

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

⚠️ **落とし穴:**
WindowsでNVIDIA製GPUを使っている場合、WSL2（Windows Subsystem for Linux）上でDockerを動かすのが一般的ですが、稀にGPUが認識されないことがあります。必ず最新のNVIDIA Game Readyドライバ（またはStudioドライバ）をインストールしておいてください。ドライバが古いと、LLMの計算がCPUに回され、回答速度が1/10以下になります。

## Step 2: Open WebUIをDockerで起動する

次に、ブラウザで操作するためのUIを立ち上げます。Dockerがインストールされていることを前提とします。

以下のコマンドをターミナルに貼り付けてください。

```bash
# GPUを利用して起動する場合（推奨）
docker run -d -p 3000:8080 --gpus all --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

### コマンドの解説
- `-p 3000:8080`: ブラウザから `http://localhost:3000` でアクセスできるようにします。
- `--gpus all`: Dockerコンテナの中からPCのGPUを使えるようにします。これを忘れるとCPU動作になり激重です。
- `-v open-webui:/app/backend/data`: チャット履歴や設定を保存する領域を確保します。コンテナを消してもデータが消えないようにするためです。
- `--add-host=host.docker.internal:host-gateway`: Dockerコンテナの中から、ホスト側で動いているOllamaと通信するために必要な設定です。

⚠️ **落とし穴:**
もし `--gpus all` でエラーが出る場合は、NVIDIA Container Toolkitがインストールされていません。その場合は、まずツールキットを入れるか、一時的に `--gpus all` を外して実行してください（ただし低速になります）。

## Step 3: モデルをプルして動かしてみる

ブラウザで `http://localhost:3000` を開きます。最初のログイン画面では、適当な名前とメールアドレス、パスワードを登録してアカウントを作成してください。これはローカル保存されるだけなので、本物のメールアドレスである必要はありません。

ログイン後、画面上部の設定（歯車アイコン）から「モデル」を選択し、以下のモデル名を指定してダウンロード（プル）します。

- `llama3.1:8b` （Meta製の最新汎用モデル。日本語もそこそこ強い）
- `qwen2.5:7b` （コード生成や論理的思考に非常に強い）

プルが完了したら、トップ画面の「モデルを選択」から `llama3.1:8b` を選び、何か入力してみましょう。

### 期待される出力

```text
ユーザー: こんにちは、自己紹介して。
AI: こんにちは！私はMetaによって訓練されたLlama 3.1という大規模言語モデルです。
    情報の要約、文章作成、プログラミングの支援などが可能です。
```

レスポンスが秒間50トークン程度（スラスラと流れるように表示される状態）であれば、GPUが正しく認識されています。

## Step 4: 実用レベルにする（RAGとAPI連携）

単にチャットするだけでなく、実務で使えるレベルに設定を追い込みます。

### 1. PDFやドキュメントの読み込み（RAG）
Open WebUIのチャット欄にファイルをドラッグ＆ドロップしてください。その後、ハッシュ記号 `#` を入力すると、アップロードしたドキュメントを選択できます。
「この仕様書に基づいて、APIの呼び出し例を書いて」といった依頼が可能になります。これは外部サーバーにデータを送信しないため、機密情報の含まれるドキュメントでも安心して解析させることができます。

### 2. PythonからローカルLLMを叩く
開発者であれば、OllamaをAPIサーバーとして使い、自作アプリに組み込みたいはずです。Ollamaは標準でOpenAI互換のAPIエンドポイントを持っています。

```python
import openai

# OllamaのAPIエンドポイントを指定
client = openai.OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama" # キーは何でも良い
)

response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "Pythonで素数を判定する関数を書いて"}]
)

print(response.choices[0].message.content)
```

**なぜこのコードなのか:**
`openai` ライブラリをそのまま使えるのがポイントです。将来的にOpenAIのAPIに切り替えたり、あるいはその逆も、`base_url` を変えるだけで対応できます。実務では「検証はローカル、本番はGPT-4」という使い分けがスムーズになります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error | Ollamaが起動していない | タスクバーのOllamaアイコンを確認 |
| 動作が異常に遅い | GPUではなくCPUで動作している | Docker起動時の `--gpus all` を確認、またはドライバ更新 |
| モデルのプルが終わらない | ネットワーク制限またはディスク不足 | モデル1つにつき約5GBの空き容量が必要 |

## 次のステップ

ここまでで、自分専用の強力なAI環境が手に入りました。次に挑戦すべきは「モデルの使い分け」と「関数呼び出し（Function Calling）」です。

例えば、単純な文章要約なら軽量な `gemma2:2b`、複雑なプログラミングなら `qwen2.5:7b`、長文読解なら `command-r` といった具合に、用途に合わせてモデルを切り替えることで、限られたPCリソースを最大限に活かせます。

また、Open WebUIの「Tools」機能を使えば、AIに特定のPythonスクリプトを実行させたり、ローカルファイルを直接編集させたりすることも可能です。ここまで来れば、あなたはもう「AIに使われる側」ではなく、AIを「自分の道具として使いこなす側」に立っています。まずは今日、手元のPCにOllamaを入れて、適当なモデルを動かすところから始めてください。

## よくある質問

### Q1: RTX 3060（12GB）とRTX 4060（8GB）ならどちらが良いですか？

断然、RTX 3060 12GBです。ローカルLLMにおいて、チップの世代の差よりも「VRAMの多さ」が正義です。12GBあれば、8Bクラスのモデルを非常に高い精度（量子化ビット数が高い状態）で動かせますし、RAGで長いコンテキストを読み込んでもエラーになりにくいです。

### Q2: 会社で使っても情報漏洩の心配はないですか？

はい、基本的には安全です。OllamaもOpen WebUIも、モデルの実行はすべてあなたのPC内（ローカルホスト）で完結します。ただし、Open WebUIの設定で「Web Search」を有効にすると、検索のために外部API（GoogleやSerper等）にクエリが飛ぶため、そこだけは注意してください。

### Q3: 複数のモデルを同時に動かすことはできますか？

VRAMが許す限り可能です。Ollamaはリクエストに応じてモデルをメモリにロード・アンロードしますが、設定で複数のモデルを常駐させることもできます。ただし、メモリを使い切ると極端に低速になるため、個人PCであれば1つずつ、あるいは軽量なモデルを2つ程度にするのが現実的です。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用の機密情報漏洩ゼロなChatGPT環境を構築する方法](/posts/2026-08-10-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法](/posts/2026-08-01-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法](/posts/2026-07-12-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3060（12GB）とRTX 4060（8GB）ならどちらが良いですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "断然、RTX 3060 12GBです。ローカルLLMにおいて、チップの世代の差よりも「VRAMの多さ」が正義です。12GBあれば、8Bクラスのモデルを非常に高い精度（量子化ビット数が高い状態）で動かせますし、RAGで長いコンテキストを読み込んでもエラーになりにくいです。"
      }
    },
    {
      "@type": "Question",
      "name": "会社で使っても情報漏洩の心配はないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、基本的には安全です。OllamaもOpen WebUIも、モデルの実行はすべてあなたのPC内（ローカルホスト）で完結します。ただし、Open WebUIの設定で「Web Search」を有効にすると、検索のために外部API（GoogleやSerper等）にクエリが飛ぶため、そこだけは注意してください。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のモデルを同時に動かすことはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "VRAMが許す限り可能です。Ollamaはリクエストに応じてモデルをメモリにロード・アンロードしますが、設定で複数のモデルを常駐させることもできます。ただし、メモリを使い切ると極端に低速になるため、個人PCであれば1つずつ、あるいは軽量なモデルを2つ程度にするのが現実的です。 ---"
      }
    }
  ]
}
</script>
