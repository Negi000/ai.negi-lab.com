---
title: "OllamaとOpen WebUIの入門：起動とモデル接続を切り分ける"
date: 2026-10-05T00:00:00+09:00
slug: "ollama-open-webui-local-llm-tutorial"
cover:
  image: "/images/posts/2026-10-05-ollama-open-webui-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM RAG"
  - "Llama 3 導入ガイド"
---

ローカルAIチャットが動かないときは、「画面を開けない」「画面は開くがモデルが出ない」「モデルは動くが遅い」を分けると原因を追いやすくなります。

## 新しく始める場合

[2つのコンテナを使う共通セットアップ](/posts/ollama-openwebui-local-llm-guide/)を参照してください。Docker Engine 28以降でOpen WebUIを `127.0.0.1:3000:8080` に限定して公開し、Ollamaの11434番はホストに公開しません。使うのは同じPCの `http://127.0.0.1:3000` で、認証は無効にしません。[Dockerのポート公開仕様](https://docs.docker.com/engine/network/port-publishing/)

## 起動で詰まったら

| 症状 | 最初に確認すること |
|---|---|
| ブラウザで画面が開かない | `docker ps` でWebUIのコンテナが起動中かと、ホスト側のポートが `127.0.0.1:3000` かを確認します。 |
| 画面は開くがモデルが出ない | Ollama側でモデルが取得済みかと、WebUI側の接続先を確認します。共通手順の構成では、両方を同じDockerネットワークにつなぎ、接続先を `http://local-ollama:11434` にします。 |
| モデルは動くが遅い | 短い入力と小型モデルで切り分けます。GPUを設定した構成なら応答中に `ollama ps` で実際のCPU/GPU利用を確認します。 |

すでにホスト側にOllamaをインストールしている場合、Docker内の `localhost` はホストを指しません。OS別の接続方法は[Open WebUIの公式手順](https://docs.openwebui.com/getting-started/quick-start/)を確認してください。接続エラーを直すためにポートを無条件で全インターフェースへ開く必要はありません。

## 会社のPCで試せる？

DockerやWSL、モデルの取得に制限がある場合は、会社のルールと許可を先に確認してください。ブラウザから使えること自体は、外部に通信しないことを意味しません。外部サービスの設定を確認し、必要なイメージやモデルを準備してから、外部通信を遮断した環境で架空の入力をテストしてください。[オフラインで動かすための準備](https://docs.openwebui.com/tutorials/maintenance/offline-mode/)
