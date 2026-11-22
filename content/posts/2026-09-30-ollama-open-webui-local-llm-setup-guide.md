---
title: "OllamaとOpen WebUIでローカルLLM環境を構築する方法"
date: 2026-09-30T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-09-30-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "Llama 3.1 ローカル"
  - "自宅LLM 構築"
---

Ollamaを使ったローカルチャットを起動し、繰り返し使うレビュー指示をモデルにまとめる手順です。

## 導入は共通手順から

[OllamaとOpen WebUIの共通セットアップ](/posts/ollama-openwebui-local-llm-guide/)を参照してください。Docker Engine 28以降の新規環境では、Open WebUIの公開先を `127.0.0.1:3000:8080` に絞り、Ollamaの11434番はホストに公開しません。 `http://127.0.0.1:3000` から認証して使います。手元に既存の環境がある場合はデータとボリュームの所在を確認してから移行してください。[Dockerのポート公開仕様](https://docs.docker.com/engine/network/port-publishing/)

## レビュー用のモデルを作る

まず、インストールしたローカルモデルで短いテスト文に応答することを確認します。Ollamaの [Modelfile](https://docs.ollama.com/modelfile) は、既存モデルに定型の指示を追加するためのファイルです。次の例の `FROM` は、取得済みのローカルモデルのタグに合わせて変更してください。

~~~text
FROM llama3.2:3b
SYSTEM """
コードをレビューします。正しさ、読みやすさ、テスト漏れに分けて指摘してください。
推測は事実と分け、根拠のある指摘だけを優先順で3件まで挙げてください。
"""
~~~

`Modelfile` として保存し、ホストに直接インストールしたOllamaなら、同じディレクトリで `ollama create review-helper -f ./Modelfile` を実行します。Docker構成の場合は、対象コンテナからファイルを読める状態にし、そのコンテナ内のOllamaで作成します。Open WebUIでモデル一覧を開き直し、架空の短いコードで応答を比較してください。これは指示のテンプレート化であり、モデルの再学習ではありません。

## ネット接続がなくても動く？

ローカルモデルと必要なイメージを先に取得しておけば、外部サービスを使わないチャット構成を作れます。文書検索には抽出・埋め込み用の準備も必要です。アプリのオフライン設定だけでは外部通信は遮断されません。業務データを使う前に、組織のルールに従って接続先を確認し、架空データでテストしてください。[Open WebUIのオフライン手順](https://docs.openwebui.com/tutorials/maintenance/offline-mode/)
