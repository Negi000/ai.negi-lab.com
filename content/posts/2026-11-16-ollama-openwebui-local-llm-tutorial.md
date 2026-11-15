---
title: "OllamaとOpen WebUIで自分専用のプライベートChatGPTを構築する方法"
date: 2026-11-16T00:00:00+09:00
slug: "ollama-openwebui-local-llm-tutorial"
cover:
  image: "/images/posts/2026-11-16-ollama-openwebui-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "ローカルLLM 構築"
  - "Docker GPU 設定"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

外部サーバーに一切データを送信せず、手元のPCだけでChatGPTと同等の操作感を実現する「完全ローカルLLM環境」を構築します。
具体的には、バックエンドにOllama、フロントエンドにOpen WebUIを組み合わせ、Dockerを用いて1コマンドで立ち上がる状態を目指します。
この記事を読み終える頃には、Llama 3やGemma 2といった最新モデルに対し、PDFを読み込ませて要約させたり、プログラミングの相談をしたりできる環境が手に入ります。

- 前提知識: 基本的なコマンド操作（ターミナルやPowerShell）ができること
- 必要なもの: DockerがインストールされたPC、安定したインターネット環境（モデルのダウンロード用）

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのはCPUではなくGPUのビデオメモリ（VRAM）です。
ここを軽視すると、モデルの動作が極端に遅くなるか、あるいは全く起動しないという事態に陥ります。

具体的には、80億パラメータ（8B）クラスのモデルを快適に動かすなら、最低でも8GBのVRAMが必要です。
もし16GBあれば、少し大きめのモデルや、長い文脈（コンテキスト）を維持した対話が可能になります。
Windows機であれば「RTX 3060 12GB」や「RTX 4060 Ti 16GB」が、コストパフォーマンスの面で最も賢い選択です。
私がメインで使っているRTX 4090 24GBであれば、30Bクラスのモデルまで実用レベルで動作しますが、最初は手持ちの機材で試すのが正解です。

Apple Siliconを搭載したMac（M1/M2/M3）の場合、メインメモリ（RAM）がVRAMを兼ねる「ユニファイドメモリ」構造のため、16GB以上のメモリを積んでいれば驚くほどスムーズに動きます。
逆に、メモリ8GBのMacBook Airなどでは、OSを動かすだけで精一杯になり、LLMの推論はかなり厳しくなります。

料金面については、この環境を構築するだけなら完全に無料です。
OllamaもOpen WebUIもオープンソースであり、API使用料を気にする必要もありません。
かかる費用は、PCの電気代と、最初にハードウェアを揃えるための初期投資だけです。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールは「LM Studio」や「GPT4All」など他にもいくつか存在します。
しかし、私が「Ollama + Open WebUI」の組み合わせを実務に推奨する理由は、その拡張性と「Webブラウザで完結する」という点にあります。

LM Studioは非常に使いやすいのですが、UIが独特で、複数人で共有したり、別のPCからアクセスしたりする用途には向きません。
一方で、Open WebUIはChatGPTに酷似したインターフェースを持っており、RAG（ドキュメント読み込み）機能や、音声認識、画像生成との連携が最初から組み込まれています。
また、Dockerで運用することで、環境を汚さずに管理でき、別のマシンへの移行もスムーズです。

バックエンドにOllamaを採用するのは、モデルの管理が圧倒的に楽だからです。
`ollama run` という短いコマンド一つで、Hugging Faceからモデルを探してきて量子化設定を確認する手間をすべて自動化してくれます。
「最新のモデルをすぐに試したい、かつ実務で耐えうる高度な機能も欲しい」というワガママを叶えるなら、現時点でこの構成がベストプラクティスだと言えます。

## Step 1: 環境を整える

まずはバックエンドとなるOllamaをインストールします。
OllamaはLLMの実行エンジンとして機能し、Open WebUIからのリクエストを受け取って推論結果を返す役割を担います。

### macOS / Windows の場合
公式サイトからインストーラーをダウンロードして実行するだけです。
インストール後、バックグラウンドでOllamaが常駐していることを確認してください。

### Linux の場合
以下のコマンドを実行します。

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

このスクリプトは、システムに必要なバイナリを配置し、NVIDIA GPUがある場合は自動的にドライバを認識してCUDAの設定を行ってくれます。

⚠️ **落とし穴:**
WindowsユーザーでWSL2を使用している場合、WSL2側からもGPUが見えるように「NVIDIA Container Toolkit」をインストールしておく必要があります。
これを行わないと、OllamaがCPUだけで推論を始めてしまい、レスポンスが1秒間に数文字という「絶望的な遅さ」になります。
タスクマネージャーで「GPU 0」の専用ビデオメモリが消費されているか、常に監視する癖をつけてください。

## Step 2: モデルのダウンロードと動作確認

Ollamaがインストールできたら、まずはモデルを一つダウンロードして、正しく動作するか確認します。
今回は、Metaが公開している軽量かつ高性能な「Llama 3.1 8B」を使用します。

```bash
# Llama 3.1 8Bモデルをダウンロードして実行
ollama run llama3.1
```

コマンドを入力するとダウンロードが始まります。
完了後、ターミナル上で対話が始まったら成功です。
「こんにちは」と入力して、数秒以内に返信が来るか確認してください。

なぜLlama 3.1を選ぶのか。それは、このクラスのモデルで最も日本語の精度と推論速度のバランスが良いからです。
他にも、GoogleのGemma 2やMicrosoftのPhi-3などがありますが、まずは基準となるLlama 3.1で環境を安定させることが重要です。

確認が終わったら、`/bye` と入力して終了します。
バックグラウンドでOllamaのサービス自体は動かし続けておいてください。

## Step 3: Open WebUIを起動する

いよいよフロントエンドの構築です。
Open WebUIはDockerを使って起動するのが最も簡単で確実です。
ここでは、Ollamaが同じPC内で動いていることを前提とした設定を行います。

```bash
# Dockerを使用してOpen WebUIを起動
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

各設定の意味を解説します。
- `-p 3000:8080`: ブラウザから `http://localhost:3000` でアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: Dockerコンテナの中から、ホストPCで動いているOllamaにアクセスするための重要な設定です。
- `-v open-webui:/app/backend/data`: チャット履歴や設定ファイルを保存するための領域（ボリューム）を確保します。これがないと、コンテナを再起動した際にすべてのデータが消えてしまいます。

### 動作確認
ブラウザを開き、`http://localhost:3000` にアクセスしてください。
最初のサインアップ画面が表示されます。
「ローカルなのにサインアップ？」と思うかもしれませんが、これは複数人で利用する場合の管理用です。
ここで作成した最初のユーザーが管理者になります。
外部にデータは飛ばないので、適当な名前とメールアドレスで登録して構いません。

⚠️ **落とし穴:**
もしブラウザで「Ollama connection failed」というエラーが出た場合、Ollamaが待ち受けているポートの設定が必要です。
デフォルトではOllamaはローカルホスト（127.0.0.1）からしか接続を受け付けません。
環境変数 `OLLAMA_HOST` を `0.0.0.0` に設定して、Ollamaを再起動する必要がある場合があります。
特にDockerを介す場合、このネットワーク周りの通信許可で躓く人が8割です。

## Step 4: 実用レベルの設定とRAGの活用

Open WebUIが立ち上がったら、画面左上のモデル選択から「llama3.1:latest」を選んでください。
これで準備完了ですが、ここからさらに「仕事で使える」レベルに設定を追い込みます。

### 1. 日本語システムプロンプトの設定
設定（歯車アイコン）→「設定」→「一般」から、システムプロンプトに以下を入力します。
「あなたは優秀な日本語アシスタントです。常に簡潔かつ論理的に、日本語で回答してください。」
ローカルLLMは、放っておくと英語で回答し始めることが多いため、この明示的な指示が「使える道具」にするためのコツです。

### 2. ローカルRAG（文書読み込み）を試す
Open WebUIの真骨頂はRAGです。
チャット欄にPDFファイルをドラッグ＆ドロップしてみてください。
ファイルがアップロードされると、その内容に基づいて回答してくれるようになります。
私の場合、社内の数件にわたる仕様書をすべて読み込ませ、特定の機能の整合性を確認させるという使い方をしています。
これがクラウドAIなら「情報の流出」を気にして躊躇してしまいますが、ローカルなら安心です。

### 3. パフォーマンスの最適化
もし動作が重いと感じたら、設定から「パラメータ」を開き、「Temperature」を0.7程度に、「Top K」を40程度に調整してみてください。
また、コンテキスト長（Context Length）を4096から8192に増やすと、長い対話でも前の話を忘れにくくなります。
ただし、コンテキストを増やすほどVRAMを消費するため、自分のPCの限界を見極めながら調整するのがコツです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| モデルが表示されない | Open WebUIがOllamaを見失っている | Dockerの実行コマンドに `--add-host` が入っているか再確認 |
| 回答が異常に遅い | GPUではなくCPUで推論している | WindowsならタスクマネージャーのGPU負荷を確認。ドライバの再インストールを推奨 |
| Dockerが起動しない | ポート3000が既に使用されている | `-p 3001:8080` のように左側の数字を変更する |
| メモリ不足で落ちる | VRAMの容量を超えたモデルを選択した | 8B以上のモデル（70Bなど）は避けるか、量子化率の高い（4bit等）モデルを選ぶ |

## 次のステップ

無事に環境が構築できたら、次は「Modelfile」の作成に挑戦してみてください。
Ollamaでは、既存のモデルに特定の性格や知識を持たせた自分専用の派生モデル（例えば、特定のプログラミング言語に特化したエンジニアモデルなど）を簡単に定義できます。

また、Open WebUIの「Functions」機能を使えば、Pythonスクリプトを介してローカルのファイルを操作したり、Web検索の結果をLLMに渡したりすることも可能です。
さらに一歩進むなら、RTX 4090を2枚挿しして「マルチGPU」環境を構築し、70Bクラスの超高性能モデルを動かす世界が待っています。
この規模になると、GPT-4oに匹敵する知能を完全にオフラインで所有する快感を得られます。
ローカルLLMの世界は、一度足を踏み入れると戻れないほど奥が深く、そして何より自由です。

## よくある質問

### Q1: ネット接続がなくても使えますか？

はい、モデルのダウンロード時以外はインターネット接続は不要です。飛行機の中でも、電波の届かない地下室でも、PCの電源さえあれば完全に動作します。これがローカル環境最大の強みです。

### Q2: 会社で使いたいのですが、セキュリティリスクはありますか？

理論上、外部へデータが送信されることはありません。ただし、Dockerイメージやモデルファイルをダウンロードする際の経路だけは注意してください。一度構築してしまえば、ネットワークを遮断しても動作し続けます。

### Q3: モデルの種類が多くてどれを選べばいいか分かりません。

まずは `llama3.1` (8B) から始めましょう。日本語重視なら `command-r` や `gemma2` も優秀です。コーディング用途なら `codellama` や `deepseek-coder` を試してみてください。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBを安価に確保でき、8Bモデルを余裕で動かせるため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法](/posts/2026-11-03-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPTをローカル構築する方法](/posts/2026-09-12-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用の機密情報漏洩ゼロなChatGPT環境を構築する方法](/posts/2026-08-10-ollama-open-webui-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "ネット接続がなくても使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、モデルのダウンロード時以外はインターネット接続は不要です。飛行機の中でも、電波の届かない地下室でも、PCの電源さえあれば完全に動作します。これがローカル環境最大の強みです。"
      }
    },
    {
      "@type": "Question",
      "name": "会社で使いたいのですが、セキュリティリスクはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "理論上、外部へデータが送信されることはありません。ただし、Dockerイメージやモデルファイルをダウンロードする際の経路だけは注意してください。一度構築してしまえば、ネットワークを遮断しても動作し続けます。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルの種類が多くてどれを選べばいいか分かりません。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "まずは llama3.1 (8B) から始めましょう。日本語重視なら command-r や gemma2 も優秀です。コーディング用途なら codellama や deepseek-coder を試してみてください。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBを安価に確保でき、8Bモデルを余裕で動かせるため</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
