---
title: "OllamaとOpen WebUIで自分専用のChatGPTをローカル構築する方法"
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
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- Webブラウザから操作可能で、機密情報を外部に漏らさない完全オフラインの「自分専用ChatGPT」環境を構築します。
- 前提知識は「ターミナルでコマンドをコピペできること」と「Dockerの基本的な概念を知っていること」だけで十分です。
- Windows、Mac、Linuxのいずれでも動作しますが、今回は最もハマりやすいWindows（WSL2）とMacを中心に解説します。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでこの価格。ローカルLLMを実用レベルで動かすための最短ルートです</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU性能よりも「VRAM（ビデオメモリ）」の容量がすべてを決めます。
私が検証した結果、最低でも8GB、実務でストレスなく使うなら12GB〜16GBのVRAMが必要です。
VRAMが足りないとメインメモリ（RAM）にスワップされ、レスポンスが10倍以上遅くなるため、ここだけは妥協しないでください。

Windowsユーザーなら、RTX 3060（12GB版）やRTX 4060 Ti（16GB版）がコストパフォーマンスの最適解です。
Macユーザーの場合、メモリがVRAMを兼ねるため、最低16GB、できれば32GB以上のモデルを強く推奨します。
料金については、電気代以外は完全に無料です。API料金を気にせず、1日に何万トークン消費しても課金されません。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段はLM StudioやAnythingLLMなど他にもありますが、私は「Ollama + Open WebUI」の組み合わせが最強だと考えています。
理由は、Ollamaがモデルの管理と実行をバックエンドで軽量にこなし、Open WebUIが本家ChatGPTを凌ぐほどの多機能なインターフェースを提供してくれるからです。

特にOpen WebUIは、PDFやURLを読み込ませるRAG（検索拡張生成）機能や、複数のモデルを同時に呼び出して回答を比較する機能が標準装備されています。
エンジニアが実務で使う場合、単なるチャットボット以上の「ツール」としての拡張性が重要になります。
Dockerを使用するため、ホストOSの環境を汚さずに、ワンコマンドで最新バージョンへアップデートできる点も大きなメリットです。

## Step 1: 環境を整える

まずは、LLMの実行エンジンであるOllamaをインストールします。

```bash
# Mac/Linuxの場合（公式スクリプト）
curl -fsSL https://ollama.com/install.sh | sh
```

Windowsの場合は、公式サイト（ollama.com）からインストーラーをダウンロードして実行してください。
インストール後、ターミナルで `ollama --version` と打ち込み、バージョンが表示されれば成功です。
Ollamaは「バックエンド」として常駐し、モデルのダウンロードと推論計算を担当します。

⚠️ **落とし穴:** Windowsユーザーは、WSL2（Windows Subsystem for Linux）がインストールされているか確認してください。
DockerでGPUを認識させるためには、WSL2上でNVIDIA Container Toolkitが正しく設定されている必要があります。
これを忘れると、LLMがCPUで動作してしまい、1文字出すのに数秒かかる「激重」環境になってしまいます。

## Step 2: 基本の設定

次に、GUI部分となるOpen WebUIをDockerで起動します。
今回は、GPUをフル活用するための設定で立ち上げます。

```bash
# Dockerを使ってOpen WebUIを起動するコマンド
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

各オプションの意味を解説します。
`-p 3000:8080` は、ブラウザから `localhost:3000` でアクセスするためのポート設定です。
`--add-host=host.docker.internal:host-gateway` は重要で、Dockerコンテナの中からホストOS上で動いているOllamaと通信するために必要です。
`-v open-webui:/app/backend/data` は、過去のチャット履歴や設定を保存する「ボリューム」を定義しています。これがないと、コンテナを再起動するたびに履歴が消えてしまいます。

## Step 3: 動かしてみる

ブラウザを開き、`http://localhost:3000` にアクセスしてください。
初回はアカウント作成画面が出ますが、これはローカルのデータベースに保存されるだけなので、好きなメールアドレスとパスワードを入力してログインします。

次に、モデルをダウンロードします。
画面左下の設定メニュー、あるいはモデル選択画面から、使いたいモデル名を指定してダウンロードします。

```bash
# 最初に試すべきおすすめモデル
Llama3.1:8b (Meta製の高性能モデル)
Gemma2:9b (Google製の日本語に強いモデル)
Qwen2.5:7b (コーディングに極めて強いモデル)
```

ダウンロードが完了したら、チャット画面で「こんにちは」と入力してみてください。

### 期待される出力

```text
こんにちは！私はローカル環境で動作しているAIアシスタントです。
何かお手伝いできることはありますか？
```

もし回答が極端に遅い場合は、OllamaがGPUを認識しているか確認してください。
ターミナルで `docker stats` を叩き、CPU使用率が100%に張り付いていなければ、GPUが正しく仕事をしている証拠です。

## Step 4: 実用レベルにする

ここからが本番です。Open WebUIの真骨頂である「RAG機能」を活用しましょう。
チャット欄にPDFファイルをドラッグ＆ドロップするか、URLを貼り付けてみてください。
すると、AIはそのドキュメントの内容を「踏まえた」上で回答してくれます。

実務では、社内の議事録や技術ドキュメントを読み込ませるのが最も効果的です。
クラウドLLMには投げられない未公開情報を、ローカル環境で安全に要約させることができます。

さらに「モデルの比較」も活用してください。
画面上部の「＋」ボタンから複数のモデルを選択し、同じプロンプトを投げます。
「ロジックはLlama3.1が強いが、日本語の自然さはGemma2が上だ」といった、実務における使い分けの判断基準が手に入ります。

また、APIキーを管理する `.env` ファイルなどをいちいち書かなくていいのも楽です。
Open WebUIの設定画面から、OpenAIやAnthropicのAPIキーを入力すれば、ローカルモデルとクラウドモデルを同じUIでシームレスに切り替えて使えます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error | コンテナからホストのOllamaが見えていない | Step 2の `--add-host` オプションを確認する |
| 回答が1文字ずつで非常に遅い | GPUではなくCPUで動作している | NVIDIA Driverを最新にし、WSL2の設定を見直す |
| モデルのダウンロードが途中で止まる | ディスク容量不足、またはネットワーク制限 | `~/.ollama` ディレクトリの空き容量を確保する |
| Dockerが起動しない | メモリ割り当て不足 | Docker Desktopの設定でメモリを4GB以上に増やす |

## 次のステップ

環境が整ったら、次は「プロンプトエンジニアリング」を卒業して、「システムの自動化」に踏み出しましょう。
OllamaはローカルでAPIサーバーとしても機能しています。
Pythonから `requests` ライブラリを使って、ローカルLLMを自分のプログラムに組み込んでみてください。

例えば、特定のフォルダに保存されたログファイルを監視し、エラーが出たら自動でローカルLLMが解析してSlackに通知するスクリプトなどは、1時間もあれば書けます。
外部APIのレートリミットや料金を気にせず、無限にテストを回せるのは開発者にとって最高の特権です。

また、余裕があれば「Quantization（量子化）」についても調べてみてください。
VRAMが少ない環境でも、16bitのモデルを4bitに圧縮して動かすテクニックを知れば、より巨大なモデルを自分のPCで飼い慣らすことができるようになります。

## よくある質問

### Q1: 会社のPCでも動かせますか？

基本的には動きますが、Dockerのインストール権限が必要です。また、WSL2がセキュリティポリシーで禁止されている場合もあります。その際は、Dockerを使わずにOllama単体と実行バイナリ形式のUIを組み合わせる手法を検討してください。

### Q2: モデルの選び方がわかりません。

まずは `llama3.1:8b` を基準にしてください。日本語の対話精度を求めるなら `gemma2`、プログラミングの補助なら `qwen2.5` が現時点での私の推しです。VRAMが12GBあるなら、少し大きめの `14b` クラスのモデルも快適に動きます。

### Q3: GPUなしのノートPCでも動きますか？

動きますが、実用的ではありません。MacBookのM1/M2/M3チップであればGPU統合メモリなので高速ですが、一般的なIntel/AMDのノートPC（内蔵GPUのみ）だと、回答速度は1秒間に1〜2文字程度になります。短文の要約程度なら使えますが、長文作成は厳しいです。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-09-02-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIで自分専用のセキュアなローカルLLM環境を構築する方法](/posts/2026-08-23-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用のChatGPTを構築する方法](/posts/2026-06-22-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "会社のPCでも動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的には動きますが、Dockerのインストール権限が必要です。また、WSL2がセキュリティポリシーで禁止されている場合もあります。その際は、Dockerを使わずにOllama単体と実行バイナリ形式のUIを組み合わせる手法を検討してください。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルの選び方がわかりません。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "まずは llama3.1:8b を基準にしてください。日本語の対話精度を求めるなら gemma2、プログラミングの補助なら qwen2.5 が現時点での私の推しです。VRAMが12GBあるなら、少し大きめの 14b クラスのモデルも快適に動きます。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUなしのノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、実用的ではありません。MacBookのM1/M2/M3チップであればGPU統合メモリなので高速ですが、一般的なIntel/AMDのノートPC（内蔵GPUのみ）だと、回答速度は1秒間に1〜2文字程度になります。短文の要約程度なら使えますが、長文作成は厳しいです。 ---"
      }
    }
  ]
}
</script>
