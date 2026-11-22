---
title: "OllamaとOpen WebUIで手元のPDFを検索する：ローカルRAG入門"
date: 2026-09-17T00:00:00+09:00
slug: "ollama-openwebui-rag-tutorial-local-ai"
cover:
  image: "/images/posts/2026-09-17-ollama-openwebui-rag-tutorial-local-ai.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open-WebUI 入門"
  - "ローカルLLM RAG"
  - "Llama 3.1 日本語"
---

PDFの質問に答えてくれる環境を作るには、会話モデルに加えて、PDFから文字を取り出す処理と、文章を検索するための埋め込みモデルが必要です。ここでは、機密資料を使わずに検索の結果を確かめます。

## 画面とモデルの準備

[共通セットアップ](/posts/ollama-openwebui-local-llm-guide/)で、Docker Engine 28以降を使い、Open WebUIだけを `127.0.0.1:3000:8080` に公開します。Ollamaの11434番はホストに公開せず、WebUIは `http://127.0.0.1:3000` から認証して使います。[Dockerのポート公開仕様](https://docs.docker.com/engine/network/port-publishing/)

Open WebUIの管理画面にあるドキュメント設定で、抽出・埋め込みの接続先を確認します。ネットを切って使う場合は、必要な抽出機能と埋め込みモデルを事前に準備し、再ランキングを使うならその処理もローカルで用意します。ローカルの会話モデルを選んだだけでは、文書処理までローカルになったとは言えません。[Open WebUIのオフライン手順](https://docs.openwebui.com/tutorials/maintenance/offline-mode/)

## 架空の資料で検索を試す

1. 「テスト倉庫の棚番号は B-47。棚卸しは4月12日。」と書いたテキスト、または文字を選択できるPDFを作ります。
2. Open WebUIでチャットに添付するか、ワークスペースのナレッジに登録してチャットから選びます。
3. 「棚番号は何ですか。該当箇所を示してください」と質問します。答えだけでなく、引用元の文に B-47 があることを確認します。
4. 次に「倉庫の住所は？」と聞きます。資料にない答えをもっともらしく補ってしまわないかを見るためです。

手順：[Open WebUIのRAGガイド](https://docs.openwebui.com/features/chat-conversations/rag/)

## 答えが見つからないとき

まずPDFから文字をコピーできるか確認します。画像だけのスキャンなら、許可されたローカルOCRなどで文字を抽出してから再登録します。文字が取れるなら、質問の言葉を文書内の見出しや固有名詞に寄せ、関連箇所が取得できているかを見ます。モデルを大きくするのは、抽出と検索の結果を確かめたあとです。

社内資料などを扱う前に、外部サービスを無効にし、必要なローカル接続を残したまま外向き通信を遮断して、チャットと文書検索をそれぞれ試してください。アップロードした文書、会話履歴、検索データの保存先と権限も確認します。
