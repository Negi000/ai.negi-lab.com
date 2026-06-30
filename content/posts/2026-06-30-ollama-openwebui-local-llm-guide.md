---
title: "OllamaとOpen WebUI 使い方ガイド！ローカルLLM構築"
date: 2026-06-30T00:00:00+09:00
slug: "ollama-openwebui-local-llm-guide"
cover:
  image: "/images/posts/2026-06-30-ollama-openwebui-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM おすすめ"
  - "Docker AI環境"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- Dockerを利用した、ブラウザから操作できるプライベートなAIチャット環境（Ollama + Open WebUI）
- 自分のPC内だけで完結し、外部にデータが漏れないセキュアな開発基盤
- Llama 3.1やGemma 2といった最新モデルを即座に切り替えて検証できる環境

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 3060 12GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 12GB搭載で最も安価にローカルLLMを実用レベルで動かせる</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203060%252012GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203060%252012GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203060%2012GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、コマンドプロンプトやターミナルでコマンドをコピペできること、Dockerの概念をなんとなく知っていることが望ましいです。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPUよりも圧倒的に重要なのがGPUのVRAM（ビデオメモリ）容量です。
結論から言うと、VRAM 8GBが「動かして遊べる」最低ライン、12GB以上が「仕事で実用的に使える」ラインになります。

WindowsユーザーならNVIDIA製のRTX 3060（12GB版）が、現時点で最もコストパフォーマンスが高い選択肢です。
VRAMが足りないと、推論速度が1秒間に数文字という「スワップ地獄」に陥り、実用には耐えません。
Macユーザーの場合は、メモリがVRAMと共有されるため、最低でも24GB（できれば36GB以上）のユニファイドメモリを積んだApple Silicon（M2/M3/M4）が必要です。

料金については、ハードウェアさえあれば完全に無料です。
ChatGPT Plusの月額$20を払い続けるのと、RTX 3060を4万円前後で買うのとでは、1年で元が取れる計算になります。
プライバシーが重要な案件や、数千件のドキュメントを読み込ませるRAG（検索拡張生成）の実験を、APIコストを気にせず回せるのが最大のメリットです。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールには、LM StudioやAnythingLLMなど多くの選択肢があります。
しかし、私が実務で「Open WebUI」を強く推す理由は、その圧倒的な「ChatGPT再現度」と「拡張性」にあります。

Open WebUIは、単なるチャット画面ではなく、RAG（ドキュメントアップロード）、マルチユーザー管理、モデルのパラメータ調整、さらには関数呼び出し（Tools）まで対応しています。
また、バックエンドにOllamaを採用することで、モデルの管理がコマンド一つで完結し、非常に軽量に動作します。
この組み合わせは、ローカル環境における「決定版」と言っても過言ではなく、世界中のエンジニアがメイン環境として採用している構成です。

## Step 1: 環境を整える

まずは心臓部となる「Ollama」をインストールします。
Ollamaは、複雑なライブラリ管理が必要なLLMを、まるでパッケージマネージャーのように簡単に扱えるツールです。

1. [Ollama公式サイト](https://ollama.com/)からインストーラーをダウンロードし、実行します。
2. インストール完了後、ターミナル（WindowsはPowerShell）を開き、以下のコマンドを入力してください。

```bash
# Ollamaが正しくインストールされたか確認
ollama --version

# 最新のLlama 3.1 (8B) モデルをダウンロードして起動
ollama run llama3.1
```

`ollama run`コマンドは、モデルが手元になければ自動でダウンロードし、サーバーを立ち上げ、対話モードに入ります。
XXXはモデル名を指しており、8B（80億パラメータ）であれば一般的なゲーミングPCでサクサク動きます。

⚠️ **落とし穴:**
WindowsでGPUが認識されない場合、NVIDIAのドライバーが古いケースがほとんどです。
必ず「Game Ready」ではなく「Studio」ドライバーの最新版を入れるようにしてください。
また、WSL2を使わなくても現在はネイティブで動作しますが、Dockerと併用する場合はWSL2の設定が正しく終わっている必要があります。

## Step 2: DockerでOpen WebUIを立ち上げる

次に、ブラウザから操作するためのUI部分を構築します。
Open WebUIは、Dockerを使って立ち上げるのが最もクリーンで、トラブルが少ない方法です。

```bash
# Open WebUIのコンテナを起動する
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

このコマンドには重要な意味が3つ含まれています。
- `-p 3000:8080`: ブラウザから `http://localhost:3000` でアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: Dockerコンテナの中から、ホストPCで動いているOllamaに接続するための設定です。
- `-v open-webui:/app/backend/data`: チャット履歴や設定を「ボリューム」として保存します。これがないと、コンテナを止めた時に全てのデータが消えます。

起動には少し時間がかかりますが、`docker ps` コマンドで `STATUS` が `Up` になっていれば成功です。

## Step 3: 動かしてみる

ブラウザを開き、 `http://localhost:3000` にアクセスしてください。
最初にアカウント作成画面が出ますが、これは自分のPC内に保存されるだけなので、好きなメールアドレスとパスワードで登録してログインします。

### 期待される動作

1. 画面上部の「モデルを選択」から、先ほどダウンロードした `llama3.1:latest` を選びます。
2. チャット欄に「こんにちは、自己紹介してください」と入力します。
3. 日本語で返答が来れば成功です。

もし英語で返ってくる場合は、左下の設定（自分のアイコン）→「Settings」→「General」から、システムプロンプトに「あなたは優秀なアシスタントです。必ず日本語で回答してください。」と入力して保存してください。
これが、ローカルLLMを日本語特化させるための最も簡単なハックです。

## Step 4: 実用レベルにする

単にチャットするだけではもったいないので、業務で使えるレベルにカスタマイズします。
私が実務で多用しているのは「Modelfile」の作成と「RAG」の活用です。

### 日本語特化モデルの追加

Llama 3.1も優秀ですが、日本語の自然さでは「Gemma 2」や「Llama-3-ELYZA-JP」に軍配が上がることがあります。
Open WebUIの「Workspace」→「Models」から、既存のモデルをベースにした「カスタムモデル」を作成できます。

```text
# Modelfileの例
FROM llama3.1
PARAMETER temperature 0.7
SYSTEM """
あなたはIT専門ブロガー「ねぎ」として振る舞ってください。
結論ファーストで、技術的な正確さを保ちつつ、親しみやすい日本語で回答してください。
"""
```

このように設定することで、特定のキャラクターや役割を持たせた専用AIを量産できます。
私は案件ごとに「Pythonコードレビュー専門」「ドキュメント要約専門」など、5種類ほどのカスタムモデルを使い分けています。

### ドキュメント読み込み（RAG）の試行

Open WebUIのチャット欄にファイルをドラッグ＆ドロップしてみてください。
PDFやテキストファイルを読み込ませ、その内容について質問できるようになります。
これは内部で「ベクトル検索」が行われており、数万文字の仕様書から特定の記述を探し出すといった作業が、数秒で完了します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error | Open WebUIがOllamaを見つけられていない | Docker起動時の `--add-host` 設定を再確認する |
| 生成速度が異常に遅い | GPUではなくCPUで動作している | Ollamaの設定でGPUが有効か確認し、VRAM不足ならモデルを小さいもの（3Bなど）に変える |
| ブラウザが真っ白 | コンテナが正しく起動していない | `docker logs -f open-webui` でエラーログを確認する |

## 次のステップ

ここまでで、あなたの手元には最強のAI検証環境が整いました。
次に挑戦してほしいのは、このOllamaを「外部からAPIとして叩く」ことです。

例えば、VS Codeの拡張機能である「Continue」や「Llama Coder」を使えば、GitHub Copilotの代わりに自分のローカルLLMを使ってコード補完ができるようになります。
これにより、ソースコードを一切外部サーバーに送ることなく、AIによるコーディング支援を受けることが可能になります。

また、Difyというノーコードツールと連携させることで、ローカルLLMを使った複雑なワークフローを構築することもできます。
AIを「チャット」で終わらせず、「エージェント」として使い倒すフェーズへ進んでください。

## よくある質問

### Q1: 社内のPCに構築してもセキュリティ的に大丈夫ですか？

はい、大丈夫です。OllamaもOpen WebUIも、今回紹介したDocker構成であれば、インターネットへデータを送信することはありません。ただし、モデルのダウンロード時だけは外部と通信するため、その点だけ留意してください。

### Q2: 4bit量子化などの「量子化」モデルとは何ですか？

巨大なモデルの精度をほぼ落とさずに、ファイルサイズを1/4程度に圧縮する技術です。Ollamaがデフォルトで落としてくるモデルは4bit量子化されており、これが「家庭用PCでも高性能AIが動く」最大の理由です。

### Q3: 複数のモデルを同時に動かせますか？

VRAMが許す限り動かせますが、推論時は1つのモデルにリソースを集中させるのが一般的です。Open WebUIを使えば、複数のモデルに同じ質問を投げて、回答を横並びで比較（ベンチマーク）することも簡単にできます。

---

## あわせて読みたい

- [OllamaとOpen WebUIの使い方！自分専用のローカルLLM環境を完全構築する方法](/posts/2026-06-26-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-06-16-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPTを構築する方法](/posts/2026-06-22-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "社内のPCに構築してもセキュリティ的に大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、大丈夫です。OllamaもOpen WebUIも、今回紹介したDocker構成であれば、インターネットへデータを送信することはありません。ただし、モデルのダウンロード時だけは外部と通信するため、その点だけ留意してください。"
      }
    },
    {
      "@type": "Question",
      "name": "4bit量子化などの「量子化」モデルとは何ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "巨大なモデルの精度をほぼ落とさずに、ファイルサイズを1/4程度に圧縮する技術です。Ollamaがデフォルトで落としてくるモデルは4bit量子化されており、これが「家庭用PCでも高性能AIが動く」最大の理由です。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のモデルを同時に動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "VRAMが許す限り動かせますが、推論時は1つのモデルにリソースを集中させるのが一般的です。Open WebUIを使えば、複数のモデルに同じ質問を投げて、回答を横並びで比較（ベンチマーク）することも簡単にできます。 ---"
      }
    }
  ]
}
</script>
