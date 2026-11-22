---
title: "OllamaとOpen WebUI：自分のPCだけで使うための設定確認"
date: 2026-11-06T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-11-06-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM GPUスペック"
  - "Llama 3.1 日本語"
---

Ollamaで推論し、Open WebUIでチャットする構成を、自分のPCだけで使うための確認手順です。インストールから始める場合は[共通セットアップ](/posts/ollama-openwebui-local-llm-guide/)を参照してください。ここでは、すでに導入した環境の点検に絞ります。

## 公開ポートと認証を確認する

共通手順では Docker Engine 28以降を使い、Open WebUIは `127.0.0.1:3000:8080` にだけ公開します。Ollamaの11434番はホストに公開せず、同じDockerネットワークのWebUIから接続します。WebUIの認証は無効にしません。[Dockerのポート公開仕様](https://docs.docker.com/engine/network/port-publishing/)

旧版の手順で構築済みなら、まず `docker ps` の `PORTS` 欄を確認してください。WebUIの3000番が `0.0.0.0` や `[::]` に割り当てられている、またはOllamaの11434番がホストに公開されている場合は、必要がなければ対象のサービスを停止し、データの保存先を確認してから共通手順の構成へ移行します。モデルやチャット履歴のボリュームは削除しないでください。

ブラウザは同じPCで `http://127.0.0.1:3000` を開きます。画面は出るがモデルが選べない場合は、Ollama側にモデルが入っているかと、WebUIの接続先を確認します。接続エラーを直すために、Ollamaを外部向けに開く必要はありません。

## ローカル推論と通信遮断は別

ローカルモデルを選んでも、モデルやイメージの取得、クラウドプロバイダー、Web検索、外部ツールなどが通信することがあります。Open WebUIのオフライン設定はファイアウォールではありません。完全に外へ出さない必要がある場合は、必要なデータを先に準備した上で外部通信を遮断し、架空の入力でテストします。業務データは組織が許可した構成だけで扱ってください。[Open WebUIのオフライン手順](https://docs.openwebui.com/tutorials/maintenance/offline-mode/)
