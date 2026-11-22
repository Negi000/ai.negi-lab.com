---
title: "OllamaとOpen WebUIでローカルLLMを始める：モデルの選び方"
date: 2026-07-27T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup"
cover:
  image: "/images/posts/2026-07-27-ollama-open-webui-local-llm-setup.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM おすすめ"
  - "Docker GPU連携"
---

## まず、小さいモデルを今のPCで試す

Ollamaがモデルを実行し、Open WebUIがブラウザから使う画面を提供します。GPUの購入は後で構いません。小型のローカルモデルならCPUでも試せます。速度と必要なメモリは、モデルの規模だけでなく、量子化の種類、入力の長さ、同時実行数で変わります。

## PC内に限定して起動する

[新規セットアップの共通手順](/posts/ollama-openwebui-local-llm-guide/)で、Docker Engine 28以降を使って2つのコンテナを起動します。公開するのはOpen WebUIの `127.0.0.1:3000:8080` のみで、Ollamaの11434番はホストに公開しません。ブラウザでは `http://127.0.0.1:3000` を開き、認証は有効のままにします。

以前の手順で起動済みの場合は、新規用コマンドを上から実行する前に、既存のポート割り当てと保存ボリュームを確認してください。広い範囲に公開された古いコンテナは、停止してからデータを保持する形で移行します。[Dockerのポート公開仕様](https://docs.docker.com/engine/network/port-publishing/)

## 日本語の使い勝手を比べる

1. [Ollamaのモデル一覧](https://ollama.com/search)から、ローカル実行できる軽量モデルを選びます。
2. 同じ架空の文章を使い、「箇条書きで要約」「日付と数字を原文どおり抽出」「不明点を指摘」の3問をそれぞれのモデルに出します。
3. 最初の文字が出るまでの待ち時間と、数字の取り違えを分けて見ます。比較中は長文の入力や複数の同時実行を避けると、差が分かりやすくなります。

遅かった場合は、速度だけでGPU利用を判断せず、`ollama ps` の PROCESSOR 欄を確認します。共通手順のコンテナ構成なら `docker exec local-ollama ollama ps` です。([Ollamaの確認方法](https://docs.ollama.com/faq))

## PDFを扱う前に

同じPCからだけ画面を開ける設定は、外への通信を止める設定ではありません。PDFを扱うなら、まず[文書検索の手順](/posts/ollama-openwebui-rag-tutorial-local-ai/)で、架空の文書を使って抽出と検索を試してください。
