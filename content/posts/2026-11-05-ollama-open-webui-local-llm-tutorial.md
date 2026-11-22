---
title: "OllamaとOpen WebUI：文書検索を架空のPDFで試す"
date: 2026-11-05T00:00:00+09:00
slug: "ollama-open-webui-local-llm-tutorial"
cover:
  image: "/images/posts/2026-11-05-ollama-open-webui-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "ローカルLLM 環境構築"
  - "RAG 自作"
---

ローカルAIチャットが使えるようになったら、まず架空の文書1つで、質問に対して文書の該当箇所が返るかを試します。このように文書検索を回答に組み合わせる仕組みをRAGと呼びます。

## 最初に安全な構成で起動する

導入は[共通セットアップ](/posts/ollama-openwebui-local-llm-guide/)へ。Docker Engine 28以降では、WebUIだけを `127.0.0.1:3000:8080` に公開し、Ollamaの11434番はホストに出しません。ログインを有効にし、同じPCの `http://127.0.0.1:3000` から開きます。旧版の設定で導入済みの場合は、[公開ポートの確認手順](/posts/ollama-open-webui-local-llm-setup-guide/)も参照してください。

## 文書が根拠になっているかを試す

1. 「架空のサポート受付時間は平日10:00〜16:00」とだけ書いたPDFかテキストを、Open WebUIの文書機能で追加します。
2. 文書を選択して「サポート受付時間を、該当箇所と一緒に教えてください」と質問します。答えが元の文に合っているか、参照表示があれば開いて確認します。
3. 「土曜日の受付時間は？」と聞きます。文書にない情報を補ってしまう場合があるため、回答を元の資料で確認する運用にします。文書が見つからなければ、テキスト抽出や文書のひも付けを確認します。画像だけのPDFはOCRが必要な場合があります。

## 文書を入れる前に確認すること

回答に使うモデルだけでなく、埋め込みモデルやOCR、外部検索の接続先も確認します。初回のモデル取得には通信が必要な場合があります。オフライン設定だけでは外部通信を遮断できません。社内資料・個人情報を使う前に、組織のルールを確認し、意図した接続先以外を遮断した状態で架空データを試してください。[Open WebUIのオフライン手順](https://docs.openwebui.com/tutorials/maintenance/offline-mode/) · [RAGの追加ガイド](/posts/ollama-openwebui-rag-tutorial-local-ai/)
