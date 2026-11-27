---
title: "OllamaとOpen WebUIでローカルLLM環境を構築する方法"
date: 2026-11-28T00:00:00+09:00
slug: "ollama-openwebui-local-llm-guide"
cover:
  image: "/images/posts/2026-11-28-ollama-openwebui-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 構築"
  - "ローカルLLM 環境構築"
  - "Docker GPU設定"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- インターネット接続不要で、機密情報を扱っても安心な「自分専用のChatGPT」環境
- Dockerを利用して、コマンド一つでGUI（Open WebUI）とバックエンド（Ollama）を連携させたシステム
- Llama 3.1やGemma 2といった最新モデルを、ブラウザから快適に操作できる実行基盤

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

前提知識として、ターミナル（コマンドプロンプト）でのコピペ操作と、Dockerの基本的な概念を知っている必要があります。
ハードウェアについては、NVIDIA製GPU（VRAM 8GB以上）を搭載したWindows/Linux、または16GB以上のメモリを積んだMacを推奨します。

## 先に確認するスペック・料金

ローカルLLMを「仕事で使える」レベルで動かすには、GPUのVRAM（ビデオメモリ）が全てを決めます。
私が業務で検証した結果、7B（70億パラメーター）クラスのモデルを快適に動かすには最低8GB、将来的に13BやRAG（外部知識参照）を多用するなら12GB〜16GBのVRAMが必須です。
VRAMが不足するとメインメモリに処理が逃げ、レスポンスが10倍以上遅くなるため、スペック不足のPCで無理に構築するのはおすすめしません。

Macユーザーの場合、ユニファイドメモリがVRAMとして機能するため、16GB以上のメモリがあれば8Bクラスのモデルが驚くほどスムーズに動きます。
一方で、Intel Macや内蔵GPUのみのWindowsノートPCでは、動作が重すぎて実用には耐えないでしょう。
電気代はモデルの推論時に100W〜300Wほど消費しますが、API課金（GPT-4oなど）と異なり、どれだけ使っても月額料金はゼロです。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、LM StudioやAnythingLLMなど他にも存在します。
しかし、エンジニアが実務で使うなら「Ollama + Open WebUI」の組み合わせがベストな選択肢です。
理由は、Open WebUIがChatGPTとほぼ同等のインターフェースを持ち、PDF読み込み（RAG）やWeb検索、複数ユーザー管理機能まで備えているからです。

また、Ollamaをバックエンドに据えることで、Pythonスクリプトや他のツールからAPI経由で簡単にモデルを呼び出せます。
Docker Composeを使うことで、環境を汚さずに構築・廃棄ができる点も、検証を繰り返すエンジニアにとって大きなメリットになります。
今回は、拡張性と安定性を重視し、Dockerを用いた構築手順を解説します。

## Step 1: 環境を整える

まずは、LLMの実行エンジンであるOllamaをインストールし、GPUを使える状態にします。

```bash
# Linux (Ubuntu等) の場合、以下のコマンドで一発インストールできます
curl -fsSL https://ollama.com/install.sh | sh
```

WindowsやMacの場合は、Ollamaの公式サイトからインストーラーをダウンロードして実行してください。
インストール後、ターミナルで `ollama --version` と入力し、バージョンが表示されれば成功です。

次に、Docker環境を準備します。Windowsの方は「Docker Desktop」を、Linuxの方は `docker-compose` が使える状態にしてください。
特にWindows/LinuxでNVIDIA GPUを使う場合、Dockerコンテナ内からGPUを認識させるために「NVIDIA Container Toolkit」が必要です。

⚠️ **落とし穴:**
WindowsのDocker DesktopでGPUを認識させるには、WSL2（Windows Subsystem for Linux）が最新である必要があります。
ターミナルで `wsl --update` を実行しておかないと、コンテナ起動時に「GPUが見つかりません」というエラーで数時間溶かすことになります。

## Step 2: 基本の設定

OllamaとOpen WebUIを連携させるための `docker-compose.yaml` ファイルを作成します。
この設定にすることで、GPUをフル活用しつつ、データを永続化して保存できるようになります。

```yaml
services:
  ollama:
    volumes:
      - ./ollama:/root/.ollama
    container_name: ollama
    pull_policy: always
    tty: true
    restart: unless-stopped
    image: ollama/ollama:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  open-webui:
    build:
      context: .
      args:
        python_version: 3.11
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    volumes:
      - ./open-webui:/app/backend/data
    depends_on:
      - ollama
    ports:
      - "3000:8080"
    environment:
      - 'OLLAMA_BASE_URL=http://ollama:11434'
      - 'WEBUI_SECRET_KEY=yoursecretkeyhere'
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped
```

各設定の意図を解説します。
`OLLAMA_BASE_URL` に `http://ollama:11434` を指定しているのは、Dockerネットワーク内でコンテナ名を使って通信するためです。
また、`volumes` を設定することで、コンテナを削除してもダウンロードしたモデルや会話履歴が消えないようにしています。
`WEBUI_SECRET_KEY` はセッション管理に使うため、適当な長い文字列に変更してください。

## Step 3: 動かしてみる

設定ファイルが準備できたら、コンテナを起動します。

```bash
# コンテナの起動
docker compose up -d
```

起動したら、ブラウザで `http://localhost:3000` にアクセスしてください。
最初の画面でアカウント作成を求められますが、これはローカルに保存されるだけなので、好きなメールアドレスとパスワードで登録してログインします。

ログイン後、左上のモデル選択メニューから、動かしたいモデルをプル（ダウンロード）します。
まずは、日本語能力が高い「Llama 3.1」を試してみましょう。

```text
# Open WebUIのモデル設定画面で入力する名前
llama3.1:8b
```

### 期待される出力

ダウンロード完了後、チャット欄に「こんにちは、自己紹介をしてください」と入力します。
数秒後に以下のような返答が返ってくれば成功です。

```
こんにちは！私はLlama 3.1ベースのAIアシスタントです。
あなたのPC上でローカルに動作しており、プライバシーを守りながらお手伝いができます。
```

結果を確認する際は、タスクマネージャーや `nvidia-smi` コマンドで、GPUのVRAMが消費されているか確認してください。
8Bモデルであれば、5GB〜6GB程度のVRAMが占有されているはずです。

## Step 4: 実用レベルにする

単にチャットするだけでなく、業務で使うための設定を行います。
Open WebUIの強力な機能の一つに「ドキュメント参照（RAG）」があります。
PDFやテキストファイルをチャット欄にドラッグ＆ドロップするだけで、その内容に基づいた回答が可能になります。

また、特定の役割を持たせた「カスタムモデル（Modelfile）」を作成して保存しておくことができます。
例えば、コードレビュー専用のAIを作る場合は、以下の設定を「Model Files」セクションに追加します。

```dockerfile
# カスタムModelfileの例
FROM llama3.1:8b
SYSTEM """
あなたはシニアソフトウェアエンジニアです。
提供されたコードに対して、パフォーマンス、セキュリティ、可読性の観点から
厳しく、かつ具体的な改善案を日本語で提示してください。
"""
PARAMETER temperature 0.2
```

`temperature`（温度感）を 0.2 と低めに設定しているのは、コードレビューにおいてAIの「創作」を抑え、決定論的で正確な出力を得るためです。
このように用途に合わせてパラメータを調整したモデルを量産できるのが、ローカル環境の醍醐味です。

さらに、APIを活用して外部ツールと連携させることも検討してください。
Open WebUIは、右上の設定から「API Keys」を発行できます。
これを使えば、CursorなどのAIエディタや、自作のPythonスクリプトから、自宅サーバーのLLMを呼び出すことが可能になります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| GPU can't be found | NVIDIA Toolkitの未導入 | `nvidia-container-toolkit` をホスト側にインストールする |
| Connection Refused | コンテナ間のネットワーク不備 | `OLLAMA_BASE_URL` が `http://ollama:11434` か再確認 |
| 回答が極端に遅い | VRAM不足でCPU推論中 | モデルを小さいもの（`phi3` 等）に変えるか、VRAMを増設する |

## 次のステップ

ここまでできれば、あなたの手元には「完全にプライベートな知能」が備わったことになります。
次に挑戦すべきは、ローカルLLMを特定の業務フローに組み込むことです。

具体的には、社内のドキュメント（MarkdownやPDF）を大量に読み込ませて、社内規定や技術仕様に答える「専用RAG」の構築をおすすめします。
Open WebUIの設定にある「Documents」機能を使えば、追加のプログラミングなしでベクター検索を試すことができます。
また、PythonのLangChainやLlamaIndexを使って、OllamaのAPIを叩く自作エージェントの開発にもぜひ取り組んでみてください。
ローカルで動かすからこそ、APIコストを気にせず、何万回でも試行錯誤できるのが最大の武器になります。

## よくある質問

### Q1: モデルをダウンロードする時にエラーが出ます

プロキシ環境下や、ディスク容量不足が原因であることが多いです。
特にLlama 3.1 8Bは5GB程度ですが、70Bクラスになると40GB以上の空き容量が必要になります。
インストール先（デフォルトではCドライブやルート）の空き容量を事前に確保してください。

### Q2: セキュリティ面で気をつけることはありますか？

Dockerのポート `3000` を公開設定にすると、外部から誰でもあなたのLLMを使えてしまいます。
家庭内LAN以外からはアクセスできないようにファイアウォールを設定するか、Open WebUIの認証機能を必ず有効にして運用してください。

### Q3: 日本語の精度を上げるにはどうすればいいですか？

システムプロンプト（System Prompt）で「あなたは日本語の専門家です」と明示するのが最も簡単です。
また、Llama 3.1以外にも、日本語に特化した「Llama-3-elyza」などのモデルをOllamaにインポートして使うのも非常に効果的です。

---

## あわせて読みたい

- [OllamaとOpen WebUIの使い方！完全プライベートなローカルLLM環境を構築する方法](/posts/2026-07-07-ollama-openwebui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPTを爆速で構築する方法](/posts/2026-10-17-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-09-02-ollama-open-webui-local-llm-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "モデルをダウンロードする時にエラーが出ます",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "プロキシ環境下や、ディスク容量不足が原因であることが多いです。 特にLlama 3.1 8Bは5GB程度ですが、70Bクラスになると40GB以上の空き容量が必要になります。 インストール先（デフォルトではCドライブやルート）の空き容量を事前に確保してください。"
      }
    },
    {
      "@type": "Question",
      "name": "セキュリティ面で気をつけることはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Dockerのポート 3000 を公開設定にすると、外部から誰でもあなたのLLMを使えてしまいます。 家庭内LAN以外からはアクセスできないようにファイアウォールを設定するか、Open WebUIの認証機能を必ず有効にして運用してください。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の精度を上げるにはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "システムプロンプト（System Prompt）で「あなたは日本語の専門家です」と明示するのが最も簡単です。 また、Llama 3.1以外にも、日本語に特化した「Llama-3-elyza」などのモデルをOllamaにインポートして使うのも非常に効果的です。 ---"
      }
    }
  ]
}
</script>
