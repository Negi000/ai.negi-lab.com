---
title: "OllamaとOpen WebUIで自分専用のセキュアなChatGPT環境を構築する方法"
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
  - "Open WebUI 構築"
  - "Llama 3.1 ローカル"
  - "RAG 自宅サーバー"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 完全ローカルで動作する、ChatGPTライクなGUIを備えたAIチャット環境
- 外部API（OpenAI等）を一切使わず、手元のPCだけで最新のLlama 3.1やQwen 2.5と会話できるシステム
- 業務資料（PDF等）をアップロードして、ローカル環境だけでRAG（知識検索）ができる基盤

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBを積んだ最もコスパの良いGPU。これがないと14B以上のモデルが動かない</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、コマンドプロンプトやターミナルでコマンドをコピー＆ペーストできる程度の操作スキルが必要です。PCのOSはWindows 10/11（WSL2推奨）、macOS、Linuxのいずれかを想定しています。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。普通のメインメモリではなく、GPU（グラフィックボード）に載っているメモリの量で、動かせるAIの賢さが決まります。

最低ラインはVRAM 8GBです。これでLlama 3.1 (8B) クラスが快適に動きます。もし実務で「本当に使える」レベルの推論速度と精度を両立させたいなら、VRAM 12GB〜16GBを積んだグラフィックボード、またはメモリ32GB以上のApple Silicon Mac（M1/M2/M3）を用意してください。

私がメインで使っているRTX 4090 24GBであれば、現行のほとんどの量子化モデルが爆速で動きますが、これから機材を揃えるなら、コストパフォーマンスの観点から「RTX 4060 Ti 16GBモデル」一択です。3万円台の安いボードだとVRAMが4GBや8GBしかなく、数ヶ月後に必ず後悔することになります。

ソフトウェアは全てオープンソースなので、電気代以外の月額費用は0円です。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、LM Studio、GPT4All、AnythingLLMなど他にもあります。しかし、私は「Ollama + Open WebUI」の組み合わせが最強だと断言します。

理由は「拡張性」と「エコシステム」です。Ollamaはバックエンドとして非常に軽量で、バックグラウンドでデーモンとして常駐してくれるため、他のアプリからの呼び出しが容易です。そしてOpen WebUIは、本家ChatGPTのUIに最も近く、さらに複数人での利用、RAG（ドキュメント学習）、プロンプトの共有機能が標準で備わっています。

「とりあえず動かす」だけならLM Studioで良いですが、「仕事のインフラとして構築する」なら、この組み合わせ以外に選択肢はありません。

## Step 1: Ollamaのインストール

まずは心臓部となるOllamaを導入します。

WindowsやMacの場合は、公式サイトからインストーラーをダウンロードして実行するだけです。Linux（またはWindows上のWSL2）の場合は、以下のコマンドを叩きます。

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

このコマンドは、Ollamaのインストールスクリプトをダウンロードし、シェルで実行しています。インストールが終わると、バックグラウンドでOllamaのサーバーが立ち上がります。

インストールが完了したら、以下のコマンドで動作確認をしてください。

```bash
ollama --version
```

バージョン番号が表示されれば成功です。次に、モデルをダウンロードします。

```bash
ollama run llama3.1
```

初回実行時は数GBのデータダウンロードが始まります。これが終われば、ターミナル上でAIとの会話が可能になります。しかし、ターミナルでの会話は実用的ではありません。本番はここからです。

落とし穴: WindowsでWSL2を使っている場合、GPUを認識させるために「NVIDIA Container Toolkit」が必要です。これを忘れるとCPU推論になり、レスポンスが1文字1秒のような激遅環境になります。

## Step 2: Docker環境の準備

Open WebUIを最もクリーンに導入する方法は、Dockerを使うことです。直接インストールするとPythonのライブラリ競合に悩まされることになりますが、Dockerなら1つのコマンドで完結します。

Docker Desktopがインストールされていることを前提とします。まだの方は公式サイトからインストールし、設定で「Use the Docker-flavored WSL 2 backend」が有効になっていることを確認してください。

以下のコマンドをターミナルに入力します。これは「GPUを利用する設定」のOpen WebUI起動コマンドです。

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

各オプションの意味を解説します。
- `-d`: バックグラウンドで実行します。
- `-p 3000:8080`: ブラウザから `http://localhost:3000` でアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: Dockerコンテナの中から、ホスト側（Ollama）に通信するための設定です。これがないとUIからAIに繋がりません。
- `-v open-webui:/app/backend/data`: チャット履歴や設定を保存する領域（ボリューム）を作成します。これがないと、コンテナを再起動した時に全てのデータが消えます。

## Step 3: Open WebUIの初期設定

ブラウザを開き、`http://localhost:3000` にアクセスしてください。

最初にサインアップ画面が出ますが、これは「ローカル環境内にユーザーを作る」だけの手続きです。メールアドレスなどは適当で構いません。最初の1人が「管理者」として登録されます。

ログイン後、左下の自分の名前をクリックし、「Settings」→「Connections」を確認してください。Ollama APIのURLが `http://host.docker.internal:11434` になっていればOKです。

上部のモデル選択プルダウンから、先ほどダウンロードした `llama3.1:latest` を選んでみてください。

### 期待される出力

チャット欄に「こんにちは」と入力し、数秒以内に返答が返ってくれば成功です。

```text
AI: こんにちは！何かお手伝いできることはありますか？
```

もし返答が極端に遅い場合は、タスクマネージャー（Windows）やアクティビティモニタ（Mac）を開いて、GPUの負荷を確認してください。GPUが動いていない場合、Step 2のDocker設定やNVIDIAドライバーのバージョンを疑う必要があります。

## Step 4: 実用レベルにするためのカスタマイズ

ただ会話するだけならChatGPTで十分です。ローカル環境ならではの「実戦的な使い方」を2つ紹介します。

### 1. 「Modelfile」による専用人格の作成

Open WebUI上で「Workspace」→「Models」→「Create a Model」を開きます。
Base Modelに `llama3.1` を選び、System Promptに「あなたは優秀なPythonエンジニアです。コード以外の説明は一切不要です」と入力して保存します。
これで、余計な挨拶をしない「コード生成専用AI」が完成します。業務効率が劇的に上がります。

### 2. RAG（ドキュメント検索）の活用

チャット画面にPDFファイルをドラッグ＆ドロップしてください。
その後、「このドキュメントの内容に基づいて要約して」と指示します。
外部に送信できない社内規定や、未公開のプロジェクト資料を読み込ませても、データはあなたのPCから一歩も外に出ません。これこそがローカルLLMを導入する最大の意義です。

Open WebUIは内部で「ChromaDB」というベクトルデータベースを自動構築してくれます。複雑なコードを書かずにRAGが使えるのは、現時点でこのツールが唯一無二の存在である理由です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error (Ollama) | Dockerからホストに通信できていない | `OLLAMA_BASE_URL`の設定を再確認 |
| 推論速度が1文字/秒以下 | GPUではなくCPUで動作している | NVIDIA Toolkitの再導入とDocker再起動 |
| モデルが出てこない | `ollama pull`が完了していない | ターミナルで再度`ollama pull`を実行 |

## 次のステップ

ここまで構築できれば、あなたは「自分専用のAI工場」を手に入れたも同然です。
次に挑戦すべきは、以下の3点です。

1. **モデルの使い分け**:
   論理的思考が必要な時は `llama3.1:70b`（重いですが賢いです）、日常の雑務は `gemma2:9b` や `qwen2.5:7b` といった軽量モデルに切り替えてみてください。
2. **API連携**:
   OllamaはOpenAI互換のAPIエンドポイントを持っています。VS Codeの拡張機能「Continue」や「Cursor」のバックエンドにOllamaを指定することで、ローカルLLMによるコード補完環境が完成します。
3. **ハードウェアの増強**:
   モデルを動かす中で「もっと賢いモデルを動かしたい」と感じたら、VRAM容量を増やす検討をしてください。VRAM 48GB（4090×2枚など）あれば、ビジネスでも通用する巨大なモデルを自宅で回せるようになります。

AIを「消費」する側から、自分のPCで「所有」する側へ。この第一歩が、あなたのエンジニアとしての価値を大きく変えるはずです。

## よくある質問

### Q1: Ollamaはインターネットに繋がっていなくても動きますか？

はい、一度モデルをダウンロード（ollama pull）してしまえば、以降は完全にオフラインで動作します。飛行機の中や、セキュリティの厳しいオフライン環境でもAIを利用できるのが最大の強みです。

### Q2: 家族やチームでこの環境を共有することはできますか？

可能です。Dockerを動かしているPCのローカルIP（例: 192.168.1.10:3000）を同じWi-Fi内の他のデバイスで叩けば、ブラウザ経由で共有できます。Open WebUIにはユーザー管理機能があるため、履歴も個別に保存されます。

### Q3: おすすめの日本語モデルはありますか？

現時点では `qwen2.5` シリーズが日本語に非常に強く、知識量も豊富です。また、日本のELYZA社が公開している `elyza:8b-llama3-q4_k_m` なども、自然な日本語を話すため非常におすすめです。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のChatGPT環境を作る方法](/posts/2026-05-31-ollama-openwebui-local-llm-setup-guide/)
- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-07-05-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のローカルAI環境を構築する方法](/posts/2026-07-11-ollama-open-webui-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Ollamaはインターネットに繋がっていなくても動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、一度モデルをダウンロード（ollama pull）してしまえば、以降は完全にオフラインで動作します。飛行機の中や、セキュリティの厳しいオフライン環境でもAIを利用できるのが最大の強みです。"
      }
    },
    {
      "@type": "Question",
      "name": "家族やチームでこの環境を共有することはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Dockerを動かしているPCのローカルIP（例: 192.168.1.10:3000）を同じWi-Fi内の他のデバイスで叩けば、ブラウザ経由で共有できます。Open WebUIにはユーザー管理機能があるため、履歴も個別に保存されます。"
      }
    },
    {
      "@type": "Question",
      "name": "おすすめの日本語モデルはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "現時点では qwen2.5 シリーズが日本語に非常に強く、知識量も豊富です。また、日本のELYZA社が公開している elyza:8b-llama3-q4km なども、自然な日本語を話すため非常におすすめです。 ---"
      }
    }
  ]
}
</script>
