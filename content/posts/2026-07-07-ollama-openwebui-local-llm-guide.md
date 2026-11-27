---
title: "OllamaとOpen WebUIの始め方：自分のPCだけで使うローカルLLM"
date: 2026-07-07T00:00:00+09:00
slug: "ollama-openwebui-local-llm-guide"
description: "OllamaのAPIをLANに公開せず、Open WebUIを同じPCから開く構成。導入時の通信と、準備後にオフラインで使う条件を分けて解説します。"
cover:
  image: "/images/posts/2026-07-07-ollama-openwebui-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 構築"
  - "ローカルLLM 環境構築"
  - "ローカル推論"
---

> 訂正：以前の手順には、Web UIとOllamaのAPIを同じネットワーク上の他の機器からも利用できるようにする設定が含まれていました。ここでは、ブラウザで使う入口を自分のPCに限定し、OllamaのAPIをホストのポートに公開しない構成に変更しました。以前の構成を使っていて他の端末に公開する意図がなければ、該当コンテナを停止し、ネイティブ版Ollamaの待受設定を既定のループバックに戻してから進めてください。既存の履歴やモデルは削除する必要はありません。

## 1. まずCPUで一度動かす

この例は、Dockerが起動している個人用PC向けです。OllamaとOpen WebUIを専用のDockerネットワークに置きます。モデル推論はまずCPUで試せるので、GPUの設定はあとから切り分けられます。公開ポートを同じPCに制限するため、Docker Engineは28.0.0以降を使ってください。[Dockerのポート公開の仕様](https://docs.docker.com/engine/network/port-publishing/)

以下は新規セットアップ用です。同じ名前のコンテナやネットワークがある場合は、既存の構成を確認してから進めてください。

```bash
docker network create local-llm
docker run -d --name local-llm-ollama --network local-llm -e OLLAMA_NO_CLOUD=1 -v local-llm-models:/root/.ollama ollama/ollama
docker exec local-llm-ollama ollama pull llama3.2:1b
docker run -d --name local-llm-webui --network local-llm -p 127.0.0.1:3000:8080 -e OLLAMA_BASE_URL=http://local-llm-ollama:11434 -v local-llm-webui:/app/backend/data ghcr.io/open-webui/open-webui:main
```

[OllamaのDocker手順](https://docs.ollama.com/docker)、[Ollamaのクラウド機能の無効化](https://docs.ollama.com/faq)、[Open WebUIのクイックスタート](https://docs.openwebui.com/getting-started/quick-start/)も参照してください。イメージタグは更新されるので、同じ構成を再現したい場合は動作を確認したバージョンやダイジェストを記録します。

## 2. ブラウザで接続を確認する

同じPCのブラウザで `http://127.0.0.1:3000` を開き、最初の管理用アカウントを作ります。認証を有効にしたまま、モデル一覧から `llama3.2:1b` を選び、機密情報を含まないテスト文を送ります。一覧が空なら、`docker exec local-llm-ollama ollama list` でモデルの取得を確認し、Open WebUIの管理画面でOllamaへの接続先が `http://local-llm-ollama:11434` になっているかを確認してください。

`docker ps` のポート欄で、Open WebUIは `127.0.0.1:3000->8080/tcp`、Ollamaはホストへの割り当てがないことを確認できます。Ollamaはコンテナ内の `11434/tcp` が表示される場合がありますが、ホストIPからの割り当てとは別です。[OllamaのローカルAPI](https://docs.ollama.com/api/authentication)は認証不要なので、LAN側へ公開しないでください。名前付きボリュームにはモデルと履歴が保存されます。バックアップや移行時は、この2つを別々に扱います。

## 3. オフラインで使う条件を確認する

初回のイメージ、モデル、必要な依存ファイルはネットに接続できるうちに取得します。その後、クラウドモデルやWeb検索などの外部連携を使わずに、回線を切ってチャットを試します。文書検索も使う場合は、文書の抽出ツールと埋め込みモデルもローカルに用意し、別途テストしてください。Open WebUIのオフライン設定は一部のダウンロードや更新確認を抑えるもので、外部通信を一律に遮断する仕組みではありません。[オフライン運用ガイド](https://docs.openwebui.com/tutorials/maintenance/offline-mode/)

小さいモデルで接続できたら、普段の入力で応答時間とメモリ使用量を測ります。GPUが必要になったら、[OllamaのGPU対応](https://docs.ollama.com/gpu)を確認してください。Apple SiliconでGPUを使いたい場合は、今回のCPU用コンテナとは別に、ネイティブ版Ollamaの利用を検討します。職場のPCや資料を扱う場合は、ソフト導入とデータ取り扱いの規程を先に確認してください。

## よくある質問

### インターネットなしでも動きますか？

初回のイメージとモデルの取得には通常、通信が必要です。ローカルモデルを取得したあと、外部機能を使わないチャットを切断状態で確認してください。

### GPUは必須ですか？

この手順はCPUでも試せます。必要なメモリと応答速度は、モデル、量子化、入力の長さ、PC構成によって変わります。まず小さいモデルで測ってください。

### スマホから同じWi-Fiで開けますか？

この手順では同じPCに接続を限定するため、スマホからは開きません。スマホで使う場合は別の構成として、認証・通信の暗号化・接続元の制限を設計してください。OllamaのAPIは直接公開しません。

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "インターネットなしでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "初回のイメージとモデルの取得には通常、通信が必要です。ローカルモデルを取得したあと、外部機能を使わないチャットを切断状態で確認してください。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUは必須ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "この手順はCPUでも試せます。必要なメモリと応答速度は、モデル、量子化、入力の長さ、PC構成によって変わります。まず小さいモデルで測ってください。"
      }
    },
    {
      "@type": "Question",
      "name": "スマホから同じWi-Fiで開けますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "この手順では同じPCに接続を限定するため、スマホからは開きません。スマホで使う場合は別の構成として、認証・通信の暗号化・接続元の制限を設計してください。OllamaのAPIは直接公開しません。"
      }
    }
  ]
}
</script>
