---
title: "OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法"
date: 2026-09-02T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-09-02-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM RAG"
  - "Docker GPU設定"
---
**所要時間:** 約25分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- WebブラウザからChatGPTと同じ操作感で、完全にオフラインで動作するAIチャット環境を構築します
- 自分のPC内にあるPDFやテキストファイルを読み込ませて回答させる「RAG（検索拡張生成）」の基盤を完成させます
- 前提知識として、基本的なコマンド操作（コピペでOK）と、Dockerという単語を聞いたことがある程度の知識が必要です

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

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPUよりも「GPUのVRAM（ビデオメモリ）」がすべてを決めます。
私が業務で検証した結果、実用的な速度（30 token/s以上）で動かすには、最低でも8GBのVRAMが必要です。
具体的にはNVIDIAのRTX 3060 12GBやRTX 4060 Ti 16GBがコスパ最強の選択肢になります。

Macユーザーなら、最低16GB（推奨32GB以上）のユニファイドメモリを搭載したApple Silicon（M1/M2/M3）を用意してください。
メモリが8GBのMacBook Airだと、モデルをロードした瞬間にスワップが発生し、動作が極端に重くなります。
この環境構築自体は無料ですが、ハードウェアスペックが足りない場合は、無理にローカルで動かすよりおとなしくClaude 3.5 Sonnetに課金するほうが賢明です。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールには「LM Studio」や「GPT4All」などもありますが、私はあえて「Ollama + Open WebUI」の組み合わせを推奨します。
理由は、Ollamaがバックエンドとして非常に軽量であり、かつAPIサーバーとしても優秀だからです。
Open WebUIを組み合わせることで、マルチユーザー管理や、RAG（資料読み込み）、さらには関数呼び出し（Function Calling）までブラウザ上で完結します。
将来的に自作アプリと連携させる際も、Ollamaが動いていればOpenAI互換APIとしてそのまま叩けるため、拡張性が他のツールとは段違いです。

## Step 1: Ollamaのインストール

まずはLLMを動かすためのエンジンである「Ollama」をインストールします。

1. [Ollama公式サイト](https://ollama.com/)にアクセスし、OSに合わせたインストーラーをダウンロードします。
2. インストール完了後、ターミナル（WindowsならPowerShell）を開き、以下のコマンドを叩いてください。

```bash
ollama --version
```

「ollama version is 0.x.x」と表示されれば成功です。
Ollamaはバックグラウンドで常駐し、モデルのダウンロードから推論の実行までをすべて肩代わりしてくれます。
この時点ではまだ「エンジン」が入っただけで、「ガソリン（モデル）」も「ハンドル（UI）」もありません。

⚠️ **落とし穴:**
Windowsユーザーで「Command not found」が出る場合、インストール後に一度PCを再起動するか、パスが通っているか確認してください。
また、会社支給のPCなどでプロキシ環境下にある場合、モデルのダウンロード（ollama pull）が失敗することがあります。その場合は環境変数 `HTTP_PROXY` の設定が必要です。

## Step 2: Docker環境の準備

Open WebUIを動かすために、Dockerを導入します。
「直接インストールすればいいのでは？」と思うかもしれませんが、Open WebUIは依存関係が多く、Python環境を汚染するリスクがあります。
Dockerを使うことで、コマンド一発で環境を使い捨てにでき、不具合が起きた際もコンテナを消すだけで元通りにできます。

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/)をインストールします。
2. 設定（Settings）→ Resources → WSL2-based engine（Windowsの場合）が有効であることを確認してください。

ここで重要なのが、GPUをDockerコンテナに認識させる設定です。
NVIDIA製GPUを使っている場合、[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)をインストールしないと、Docker内のOpen WebUIからGPUが使えず、爆速のRTX 4090を積んでいてもCPU推論になってしまいます。

## Step 3: Open WebUIのデプロイ

Dockerが準備できたら、いよいよOpen WebUIを起動します。
以下のコマンドをコピーして実行してください。

```bash
# NVIDIA GPUを使う場合
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main

# Mac (Apple Silicon) や GPUがない場合
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

コマンドの意味を解説します。
- `-p 3000:8080`: PCの3000番ポートでWeb画面を開けるようにします。
- `--add-host=host.docker.internal:host-gateway`: Dockerコンテナの中から、外側にいるOllamaにアクセスするための「道」を作ります。
- `-v open-webui:/app/backend/data`: チャット履歴や設定をPC内に保存します。これを忘れると、コンテナを止めるたびに全データが消えます。

起動したら、ブラウザで `http://localhost:3000` を開いてください。
サインアップ画面が出ますが、これはローカル内に保存されるアカウントなので、適当なメールアドレスとパスワードで登録してログインしてください。

## Step 4: モデルのダウンロードと日本語設定

ログイン直後は、まだ会話できるAIがいません。
画面左下の「設定（Settings）」→「モデル（Models）」から、使いたいモデルをダウンロードします。

2024年現在、私が実務で使ってみておすすめできるモデルは以下の通りです。

- **Llama-3.1-8B-Instruct**: 汎用性最強。迷ったらこれ。
- **Gemma-2-9B-It**: Google製。日本語の表現が自然です。
- **Phi-3-mini**: 軽量。VRAMが少ない（4GB〜6GB）環境でも動きます。

設定画面の「Pull a model from Ollama.com」に `llama3.1` と入力してダウンロードボタンを押してください。
数GBのデータが降ってくるので、少し待ちます。

### 期待される動作

ダウンロード完了後、トップ画面の「モデルを選択」から `llama3.1:latest` を選び、「こんにちは、日本語で自己紹介して」と入力してください。
秒間30文字以上のペースで返答が返ってくれば、正常にGPU推論が行われています。

もし1文字ずつゆっくりしか出てこない場合は、CPUで動いています。
Dockerの設定か、NVIDIA Container Toolkitが正しく入っているか見直してください。

## Step 5: 実用レベルにする（RAGの活用）

Open WebUIの真骨頂は、資料を読み込ませるRAG機能です。
左サイドバーの「Documents」に、手持ちのPDFや技術ドキュメントをアップロードしてみてください。
その後、チャット欄で `#` を入力すると、アップロードしたファイル名が出てきます。

これを指定して質問すると、「そのドキュメントの中身に基づいて」回答してくれます。
外部のAPIにデータを送らないため、会社の機密資料や個人の家計簿などを読み込ませても安全です。
私は過去のプロジェクトの設計書をすべて突っ込んで、新しい機能を追加する際の影響範囲調査に使っていますが、精度は驚くほど高いです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error | Open WebUIからOllamaが見えていない | Docker起動時の `--add-host` 設定が正しいか確認 |
| 動作が異常に重い | GPUではなくCPUで推論している | Ollamaの設定か、VRAM不足でメインメモリを使っている |
| 日本語が不自然 | モデルが英語特化である | `gemma2` や `command-r` など日本語に強いモデルを試す |

## 次のステップ

環境が整ったら、次は「システムプロンプト」をカスタマイズしてみてください。
Open WebUIの設定から、「あなたは熟練のPythonエンジニアです。コードは必ずPEP8に準拠し、docstringを含めてください」といった指示を固定できます。

また、API経由でこのローカル環境を呼び出すことも可能です。
`http://localhost:11434/v1` はOpenAIのAPIと互換性があるため、VS Codeの拡張機能である「Continue」や「Cursor」のバックエンドをローカルOllamaに切り替えることができます。
これにより、コードを外部に一切漏らすことなく、AIによるコーディング支援を無料で受け続けることが可能になります。
次はぜひ、IDEとの連携に挑戦してみてください。

## よくある質問

### Q1: RTX 4090を2枚持っていますが、並列で動かせますか？

はい、Ollamaは自動的に複数のGPUを検知し、モデルを分割してロードしてくれます。70Bクラスの巨大なモデル（Llama-3-70Bなど）を動かす際は、VRAMを合算して利用できるため、非常に強力な環境になります。

### Q2: 毎回Dockerコマンドを打つのが面倒です。

`docker-compose.yml` を作成することをおすすめします。一度設定を書いてしまえば `docker compose up -d` だけで、OllamaとOpen WebUIの両方を連携させた状態で一発起動できるようになります。

### Q3: 外出先のスマホから自分のローカルLLMを使いたいのですが。

セキュリティリスクはありますが、TailscaleなどのVPNサービスを使うのが最も簡単で安全です。自分のPCをVPNに入れれば、外出先のスマホブラウザから自宅PCの3000番ポートにアクセスして、自分専用のAIと会話できます。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のセキュアなローカルLLM環境を構築する方法](/posts/2026-08-23-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIで最強のローカルLLM環境を構築する方法](/posts/2026-08-29-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPTを構築する方法](/posts/2026-06-22-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 4090を2枚持っていますが、並列で動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、Ollamaは自動的に複数のGPUを検知し、モデルを分割してロードしてくれます。70Bクラスの巨大なモデル（Llama-3-70Bなど）を動かす際は、VRAMを合算して利用できるため、非常に強力な環境になります。"
      }
    },
    {
      "@type": "Question",
      "name": "毎回Dockerコマンドを打つのが面倒です。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "docker-compose.yml を作成することをおすすめします。一度設定を書いてしまえば docker compose up -d だけで、OllamaとOpen WebUIの両方を連携させた状態で一発起動できるようになります。"
      }
    },
    {
      "@type": "Question",
      "name": "外出先のスマホから自分のローカルLLMを使いたいのですが。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "セキュリティリスクはありますが、TailscaleなどのVPNサービスを使うのが最も簡単で安全です。自分のPCをVPNに入れれば、外出先のスマホブラウザから自宅PCの3000番ポートにアクセスして、自分専用のAIと会話できます。 ---"
      }
    }
  ]
}
</script>
