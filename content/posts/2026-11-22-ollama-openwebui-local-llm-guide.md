---
title: "OllamaとOpen WebUIを自分のPCだけで使う方法"
date: 2026-11-22T00:00:00+09:00
slug: "ollama-openwebui-local-llm-guide"
description: "DockerでOllamaとOpen WebUIを起動し、Web画面をPC内だけに公開する手順。GPUの確認と、オフラインでチャット・文書検索を試す前の準備も解説します。"
cover:
  image: "/images/posts/2026-11-22-ollama-openwebui-local-llm-guide.jpg"
  alt: "ローカルLLM環境の記事用イメージ"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama"
  - "Open WebUI"
  - "ローカルLLM"
  - "Docker"
---

Ollamaはモデルを動かす側、Open WebUIはブラウザで使う画面です。まずは**同じPCのブラウザからだけアクセスできる構成**で、テスト用の入力を使って動かします。初回のイメージとモデルの取得にはインターネット接続が必要です。

## Dockerで2つをつなぐ

Docker Engine 28.0.0以降を前提とする、新規セットアップの例です。この例ではGPUの追加設定は行いません。下のコマンドは既存コンテナの置き換え手順ではありません。

```sh
docker network create local-llm
docker run -d --name local-ollama --network local-llm -e OLLAMA_NO_CLOUD=1 -v local-ollama-data:/root/.ollama ollama/ollama
docker exec local-ollama ollama pull llama3.2
docker run -d --name local-webui --network local-llm -p 127.0.0.1:3000:8080 -e OLLAMA_BASE_URL=http://local-ollama:11434 -v local-webui-data:/app/backend/data ghcr.io/open-webui/open-webui:main
```

同じPCで `http://127.0.0.1:3000` を開き、初回の管理者アカウントを作成してログインします。認証は無効にしません。モデル一覧から取得したローカルモデルを選び、短いテスト文を送ります。

- **Open WebUI**は `127.0.0.1` に限定して公開します。ホストIPなしの `-p 3000:8080` は標準設定では全インターフェースが対象です。[Dockerのポート公開仕様](https://docs.docker.com/engine/network/port-publishing/)
- **Ollama**の11434番はホストに公開しません。同じDockerネットワークのOpen WebUIからコンテナ名で接続します。Dockerネットワークは外向き通信を止める設定ではありません。
- 既にホストにOllamaがある場合、コンテナ内の `localhost` はホストではありません。接続方法はOSやDockerの構成によって異なるため、[Open WebUIの公式手順](https://docs.openwebui.com/getting-started/quick-start/)を確認してください。つながらないときにOllamaを全インターフェースに公開するのは避けます。

## GPUを使っているか確かめる

チャットを1回実行した直後に `docker exec local-ollama ollama ps` を実行します。Ollamaをホストに直接入れた場合は `ollama ps` です。`PROCESSOR` 列でGPUのみ、CPUのみ、両方にまたがっているかを確認できます。返答の速さだけでは判定できません。必要なメモリは、モデルの大きさ、量子化、入力の長さなどで変わります。[Ollama公式FAQ](https://docs.ollama.com/faq#how-can-i-tell-if-my-model-was-loaded-onto-the-gpu)

## 文書検索までオフラインで使うには

1. **切断する前に準備する。** コンテナイメージとチャット用のローカルモデルに加え、文書検索で使うローカルの埋め込みモデルも取得・設定します。使う機能に応じて、文書抽出や再ランキングの依存も準備します。
2. **アプリごとに外部サービスを無効にする。** Open WebUIは準備後に `OFFLINE_MODE=true` で起動します。Ollamaは別に `OLLAMA_NO_CLOUD=1` を設定します。Open WebUIのオフライン設定は組み込みの更新確認やモデルの自動取得などを止めますが、通信そのものを遮断しません。外部API、Web検索、外部ツールなどの設定も確認します。
3. **機密資料ではなく架空の文書で検証する。** 必要なローカル接続を残しつつ外部ネットワークへの通信を遮断し、チャットと、架空の合言葉を入れたテスト用PDFの検索をそれぞれ確認します。ファイル、会話履歴、検索用データの保存先と権限も確認してから実資料を扱ってください。[Open WebUIのオフライン手順](https://docs.openwebui.com/tutorials/maintenance/offline-mode/)

既に別端末へ公開した構成を使っている場合は、同じPCから開けることだけで判断せず、他の端末から到達できないことも確認してください。
