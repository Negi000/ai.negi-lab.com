---
title: "OllamaとOpen WebUIでローカルLLM環境を構築する方法"
date: 2026-10-30T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-10-30-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM おすすめ"
  - "Docker LLM 構築"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIを一切介さず、自分のPC内で完結するChatGPTクローン（Open WebUI）を構築します。
- ローカルLLM実行エンジン「Ollama」をバックエンドに使い、ブラウザからLlama 3やMistral、Command Rなどの最新モデルを操作可能にします。
- 前提知識として、簡単なコマンド操作とDockerの基本概念を知っている必要があります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的。7Bモデルなら余裕で動く</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを仕事で使うなら、スペック不足は致命的なストレスになります。
最も重視すべきはGPUの「VRAM（ビデオメモリ）」容量です。
7B〜8Bクラスのモデルをレスポンス0.5秒前後で動かすなら、最低でも8GBのVRAMが必要。
本格的にRAG（文書読み込み）や長いプロンプトを扱うなら、16GB以上のVRAMを搭載したRTX 4060 Ti 16GBやRTX 4090、あるいは24GB以上の統合メモリを持つApple Silicon Mac（M2/M3 Pro以上）を推奨します。

「自分のPCで動くか不安」という方は、まず既存のPCでOllamaだけをインストールして試してください。
ソフト自体は無料ですし、CPUだけでも動作はしますが、回答速度が毎秒1〜2トークン程度になり、実用には耐えません。
API料金は月額$0ですが、その分ハードウェアへの初期投資がランニングコストの代わりになると考えてください。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段はLM StudioやGPT4Allなど複数ありますが、私は「Ollama + Open WebUI」の組み合わせが最強だと考えています。
理由は、モデル管理の容易さと、UIの多機能さです。
Open WebUIは単なるチャット画面ではなく、RAG（PDF読み込み）、マルチユーザー管理、画像生成AIとの連携など、本家ChatGPT Plusに近い機能を備えています。

また、Dockerを利用することで環境を汚さず、バックエンド（Ollama）とフロントエンド（Open WebUI）を切り離して管理できます。
将来的に別のサーバーにモデルを逃がしたり、複数のPCからアクセスしたりする拡張性が圧倒的に高いのです。

## Step 1: Ollamaのインストールとモデルの準備

まずは心臓部となるOllamaをインストールします。

```bash
# 公式サイト（https://ollama.com/）からインストーラーをダウンロードして実行
# インストール後、以下のコマンドで動作確認
ollama --version
```

次に、日本語能力が高い軽量モデル「Llama 3」をダウンロードします。

```bash
# 8Bモデルをプル（約4.7GBのダウンロードが発生します）
ollama pull llama3
```

Ollamaはデフォルトで「127.0.0.1:11434」で待機します。
しかし、Docker上のOpen WebUIから接続する場合、ホスト側のIPアドレスを明示的に許可する必要があります。

⚠️ **落とし穴:**
Windowsの場合、システムトレイのOllamaアイコンから一度「Quit」して終了させ、環境変数 `OLLAMA_HOST` に `0.0.0.0` を設定して再起動しないと、Dockerコンテナからの接続が拒否されることがあります。
ここを忘れると、UI上で「Connection Error」が出て1時間は悩むことになります。

## Step 2: Docker ComposeでOpen WebUIを立ち上げる

Open WebUIを直接インストールするのは依存関係の解決が面倒なので、Dockerを使います。
以下の `docker-compose.yml` を作成してください。

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: always
    ports:
      - "3000:8080"
    volumes:
      - open-webui:/app/data
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    extra_hosts:
      - "host.docker.internal:host-gateway"

volumes:
  open-webui: {}
```

`OLLAMA_BASE_URL` に `http://host.docker.internal:11434` を指定するのがポイントです。
これにより、コンテナの中からホストPC上で動いているOllamaへ通信がつながります。

```bash
# コンテナを起動
docker compose up -d
```

## Step 3: 動かしてみる

ブラウザで `http://localhost:3000` にアクセスします。
初回起動時はアカウント作成を求められますが、これはローカルに保存されるデータベース用の管理アカウントです。
外部に送信されるわけではないので、適当なメールアドレスとパスワードで登録してください。

ログイン後、画面上部の「モデルを選択」から先ほどプルした `llama3:latest` を選びます。
チャット欄に「こんにちは、自己紹介してください」と入力してみましょう。

### 期待される出力

```
こんにちは！私はLlama 3、Metaによってトレーニングされた大規模言語モデルです。
あなたのPC上で動作しており、プライバシーを保ちながら質問に答えたり、コードを書いたりすることができます。
```

もし回答が返ってこない場合は、Dockerのログを確認してください。
`docker logs -f open-webui` で、Ollamaへの接続エラーが出ていないかチェックできます。

## Step 4: 実用レベルにする（RAG機能の活用）

Open WebUIの真骨頂は、ローカルファイルを読み込ませるRAG（検索拡張生成）機能です。
仕事で使う機密性の高いドキュメントを読み込ませても、データは一切外に出ません。

1. チャット入力欄の左側にある「＋」アイコンをクリックするか、ファイルをドラッグ＆ドロップします。
2. ドキュメントをアップロードすると、AIはその内容を参照して回答できるようになります。
3. 文書を参照させる際は、プロンプトに `#` を入力してファイル名を選択します。

さらに、設定の「Content Extraction」から「Web Search」を有効にすれば、検索結果を元に回答させることも可能です。
ただし、これにはSearXNGなどの検索エンジンを別途立てる必要があるため、まずはファイル読み込みによる「社内/自分専用Wiki化」から始めるのが実用的です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error (Ollama) | Ollamaが0.0.0.0で待機していない | 環境変数 `OLLAMA_HOST=0.0.0.0` を設定してOllama再起動 |
| 回答が極端に遅い | GPUが使われずCPUで推論している | WindowsならNVIDIAコントロールパネルでGPU使用を確認 |
| Docker起動失敗 | ポート3000が既に使用中 | `docker-compose.yml` の左側のポートを `3001:8080` 等に変更 |

## 次のステップ

無事に環境が動いたら、次は「モデルの使い分け」に挑戦してください。
論理的思考が必要なタスクなら `llama3`、日本語の自然さを重視するなら `elyza/elyza-llama-3-8b`、長文の要約なら `command-r` など、Ollamaなら1コマンドでモデルを切り替えられます。

また、iPhoneやiPadのブラウザからPCのローカルIPアドレス（例: `192.168.1.5:3000`）にアクセスすれば、自宅内どこでも自分専用AIを持ち歩けます。
API課金を気にせず、1日中AIと壁打ちできる環境は、エンジニアとしての生産性を劇的に変えてくれます。

## よくある質問

### Q1: 完全にオフラインでも使えますか？

はい、一度モデルのダウンロードが完了すれば、インターネット接続を切断しても動作します。
飛行機の中や電波の届かない場所でも、セキュアにAIを利用できるのがローカルLLM最大のメリットです。

### Q2: 家族やチームで共有して使えますか？

Open WebUIにはユーザー管理機能があります。
設定で「新規登録を許可」にしておけば、同じネットワーク内の他のユーザーにアカウントを作らせ、別々のチャット履歴を持たせることが可能です。

### Q3: VRAMが足りないとどうなりますか？

モデルがVRAMに入り切らない場合、溢れた分がメインメモリ（RAM）に送られます。
動作はしますが、通信速度のボトルネックにより回答速度が極端に低下します。
その場合は「Q4_K_M」などの量子化レベルが高い（ファイルサイズが小さい）モデルを選んでください。

---

## あわせて読みたい

- [OllamaとOpen WebUI 使い方ガイド！ローカルLLM構築](/posts/2026-06-30-ollama-openwebui-local-llm-guide/)
- [OllamaとOpen WebUIで最強のローカルLLM環境を構築する方法](/posts/2026-07-27-ollama-open-webui-local-llm-setup/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-08-09-ollama-openwebui-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "完全にオフラインでも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、一度モデルのダウンロードが完了すれば、インターネット接続を切断しても動作します。 飛行機の中や電波の届かない場所でも、セキュアにAIを利用できるのがローカルLLM最大のメリットです。"
      }
    },
    {
      "@type": "Question",
      "name": "家族やチームで共有して使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Open WebUIにはユーザー管理機能があります。 設定で「新規登録を許可」にしておけば、同じネットワーク内の他のユーザーにアカウントを作らせ、別々のチャット履歴を持たせることが可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "VRAMが足りないとどうなりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデルがVRAMに入り切らない場合、溢れた分がメインメモリ（RAM）に送られます。 動作はしますが、通信速度のボトルネックにより回答速度が極端に低下します。 その場合は「Q4KM」などの量子化レベルが高い（ファイルサイズが小さい）モデルを選んでください。 ---"
      }
    }
  ]
}
</script>
