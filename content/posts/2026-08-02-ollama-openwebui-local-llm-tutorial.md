---
title: "OllamaとOpen WebUIを組み合わせて、データの外部流出を完全に防ぎながらChatGPTと同等の操作感を持つローカルLLM環境を構築します。"
date: 2026-08-02T00:00:00+09:00
slug: "ollama-openwebui-local-llm-tutorial"
cover:
  image: "/images/posts/2026-08-02-ollama-openwebui-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "ローカルLLM 環境構築"
  - "Llama 3.1 日本語"
---
この記事の手順通りに進めれば、高性能なLlama 3.1やGemma 2といった最新モデルを自分のPC上で自由に、かつ無料で動かせるようになります。
API料金を気にせず、機密情報を含むコードの修正やドキュメント要約をローカルで完結させる実務環境を手に入れましょう。

**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- Webブラウザから操作できる、ChatGPTライクなUIを持つローカルAIチャット環境
- 前提知識: 基本的なコマンド操作（ターミナルやコマンドプロンプト）ができること
- 必要なもの: DockerがインストールされたPC（Windows/Mac/Linux）、インターネット接続、十分なVRAM（後述）

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU性能よりも重要なのが「VRAM（ビデオメモリ）の容量」です。
結論から言うと、NVIDIA製GPUなら最低8GB、快適に動かすなら12GB〜16GB以上が必須となります。
8GBあれば7B（70億パラメーター）クラスのモデルがサクサク動きますが、14Bや30Bクラスを実用的な速度（5〜10 tokens/sec以上）で動かすには12GB以上のVRAMが必要です。

Apple Silicon（M1/M2/M3/M4）搭載Macの場合、メインメモリ（ユニファイドメモリ）がVRAMを兼ねるため、最低16GB、できれば32GB以上のモデルを推奨します。
メモリが8GBのMacBook Airでも動くことは動きますが、スワップが発生してレスポンスが1秒間に数文字というレベルまで落ちるため、実務で使うには厳しいのが現実です。

もし今からハードウェアを揃えるなら、コストパフォーマンスの観点から「RTX 4060 Ti 16GB」一択です。
3000番台の中古を狙うのも手ですが、電力効率と将来性を考えると4000番台の16GBモデルが最も「AIエンジニアらしい」選択と言えます。
逆に、これ以下のスペックであれば、無理にローカルで動かすよりもOpenAIやAnthropicのAPIを課金して使う方が圧倒的に生産性が高いです。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールは、他にもLM Studio、Jan、GPT4Allなど多数存在します。
しかし、私が業務利用において「Ollama + Open WebUI」の組み合わせを推す理由は、圧倒的な「拡張性」と「管理のしやすさ」にあります。

Ollamaはバックエンドとして非常に優秀で、APIサーバーとして常駐させやすいため、PythonスクリプトやCursorなどのIDEから呼び出すのが容易です。
一方、Open WebUIは単なるチャットUIに留まらず、RAG（ドキュメント読み込み）機能や、複数モデルの同時比較、さらにはユーザー管理機能まで備えています。
この組み合わせは、単に「AIと話す」だけでなく、「自分専用のナレッジベースを構築する」ためのプラットフォームとして現時点で最強の構成です。

## Step 1: 環境を整える

まずはLLMの実行エンジンである「Ollama」をインストールします。

### Windows/Macの場合
公式サイト（https://ollama.com/download）からインストーラーをダウンロードして実行してください。
インストール後、タスクバーにOllamaのアイコンが表示されていれば成功です。

### Linuxの場合
以下のコマンドで一発インストールが可能です。

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

このスクリプトは、システムのアーキテクチャを自動判別し、適切なバイナリを配置してくれます。
また、systemdのサービスとして登録されるため、OS起動時に自動でバックエンドが立ち上がるようになります。

### インストールの確認
インストールができたら、ターミナル（またはPowerShell）で以下のコマンドを叩いてみてください。

```bash
ollama --version
```

バージョン番号が表示されれば、エンジンの準備は完了です。

⚠️ **落とし穴:**
WindowsでWSL2を使用している場合、GPUをOllamaに認識させるには「NVIDIA Container Toolkit」が必要になることがあります。
基本的にはWindowsネイティブ版のOllamaをインストールする方が、GPUアクセラレーションの設定が自動で行われるため、初心者には無難です。

## Step 2: モデルのダウンロードと動作確認

次に、実際に動かす「脳」にあたるモデルをダウンロードします。
今回は、Metaが公開した非常に高性能なモデル「Llama 3.1 8B」を例にします。

```bash
# Llama 3.1 8Bモデルをダウンロードして実行
ollama run llama3.1
```

このコマンドを実行すると、まず数GBのモデルファイルのダウンロードが始まります。
完了すると対話モードに移行するので、何か入力してみてください。

```text
>>> 日本語で自己紹介してください。
こんにちは！私はLlama 3.1、Metaによってトレーニングされた大規模言語モデルです...
```

ここで「レスポンスが異様に遅い」と感じた場合は、GPUではなくCPUで動いている可能性があります。
Ollamaのログを確認し、`GPU` という文字列が含まれているかチェックしてください。

## Step 3: Open WebUIを起動する

Ollamaだけでも対話は可能ですが、過去の履歴管理やファイルのアップロードを行うために、Dockerを使って「Open WebUI」を導入します。
Python環境を汚さず、依存関係のトラブルを避けるためにDockerを使うのがエンジニアとしての正解です。

以下のコマンドを一行で実行してください。

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

### コマンドの解説
- `-d`: バックグラウンドで実行します。
- `-p 3000:8080`: PCの3000番ポートでアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: Dockerコンテナの中から、ホスト側で動いているOllama（127.0.0.1）にアクセスするための設定です。これが無いと「Ollamaに接続できない」というエラーにハマります。
- `-v open-webui:/app/backend/data`: チャット履歴や設定を保存するボリュームを作成します。コンテナを消してもデータが消えないようにするためです。

### 期待される出力
コマンド実行後、ブラウザで `http://localhost:3000` にアクセスしてください。
ログイン画面が表示されたら、最初のユーザーを登録します（このデータはローカルにのみ保存されます）。

ログイン後、画面上部の「モデルを選択」から `llama3.1:latest` を選べば、ブラウザ上でローカルAIが動き出します。

## Step 4: 実用レベルにする

単にチャットするだけでなく、業務で使えるレベルにカスタマイズしましょう。
Open WebUIの強力な機能の一つに「Modelfile」の作成があります。
特定の役割（例えば「最強のPythonコードレビュアー」）を持たせた専用AIを数クリックで作れます。

### カスタムモデル（ペルソナ）の作成
1. Open WebUIのサイドメニューから「モデル」→「モデルを作成」を選択。
2. 名前を「Code-Expert」などに設定。
3. ベースモデルに `llama3.1:latest` を指定。
4. 「システムプロンプト」に以下を記述。

```text
あなたは8年以上の経験を持つシニアPythonエンジニアです。
ユーザーが提出したコードに対し、以下の観点でフィードバックを行ってください。
1. バグの可能性
2. PEP 8に基づいた可読性の改善
3. 実行速度の最適化案
回答は常に簡潔かつ実践的であること。
```

5. 「保存」をクリック。

これで、次回からこの「Code-Expert」を呼び出すだけで、一貫した品質のレビューを受けられるようになります。
私はこれを「ドキュメント翻訳専門」「SQLクエリ生成専門」など、タスクごとに5つほど使い分けていますが、プロンプトを毎回書く手間が省けて非常に快適です。

### RAG（ナレッジベース）の活用
Open WebUIは、PDFやテキストファイルをアップロードして、その内容に基づいた回答をさせるRAG機能が標準搭載されています。
チャット欄にファイルをドラッグ＆ドロップし、`#` を入力してファイル名を指定してから質問するだけです。
社外秘の仕様書や、最新すぎて学習データに含まれていないライブラリのドキュメントを読み込ませる際に、情報漏洩を気にせず投げ込めるのがローカル環境の最大の強みです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Connection Error` | Open WebUIがOllamaを見つけられない | Docker起動コマンドの `--add-host` 設定を確認する |
| `WebUIが重い` | ブラウザのハードウェア加速設定 | Chromeの設定から「ハードウェアアクセラレーション」をONにする |
| `モデルが消える` | ボリューム設定ミス | `docker run` 時の `-v` オプションが正しく設定されているか確認 |
| `応答が英語になる` | モデルの特性 | システムプロンプトに「常に日本語で回答してください」と明記する |

## 次のステップ

ここまでで、自分専用のローカルAI環境が整いました。
次に挑戦すべきは「モデルの量子化（Quantization）」の理解と、より軽量なモデルの試行です。
例えば、Googleの `gemma2:9b` は日本語能力が非常に高く、Llama 3.1よりも自然な回答をすることが多いです。
また、Microsoftの `phi3` のような小規模モデルを使えば、ノートPCのバッテリー駆動時でも高速に動作させることが可能です。

実務への応用としては、CursorというエディタにこのOllamaのURL（`http://localhost:11434`）を紐付けることをおすすめします。
コードを書いている最中に、完全にオフラインでAIの支援を受けられるようになります。
「API代がもったいないから質問を控える」という心理的なブレーキを外すことが、AI時代においてスキルを最速で磨く鍵になります。

## よくある質問

### Q1: 社内の別PCからもこのWebUIを使えますか？

可能です。Dockerを動かしているPCのIPアドレス（例: 192.168.1.10）がわかれば、同じWi-Fi内であれば `http://192.168.1.10:3000` でアクセスできます。ただし、セキュリティのためにファイアウォール設定には注意してください。

### Q2: 4bit量子化（Q4_K_M）とは何ですか？品質は落ちませんか？

モデルの重みデータを圧縮する技術です。8bitや16bitに比べるとわずかに精度は落ちますが、VRAM使用量を劇的に減らせます。実務レベルでは4bitや5bitでも十分な性能を発揮するため、Ollamaのデフォルト設定（Q4）で問題ありません。

### Q3: GPUが無いPCでも動かす方法はありますか？

動きますが、非常に低速です。CPU（AVX2命令セット対応）であれば実行自体は可能ですが、回答を待つ時間が苦痛になる可能性が高いです。その場合は、MacBookのApple Silicon搭載モデルへの乗り換えを強く検討してください。

---

## あわせて読みたい

- [OllamaとOpen WebUIを組み合わせて自分専用のローカルChatGPT環境を構築する方法](/posts/2026-07-08-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用のChatGPTをローカル構築する方法](/posts/2026-07-21-ollama-openwebui-local-llm-setup-guide/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法](/posts/2026-07-12-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "社内の別PCからもこのWebUIを使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Dockerを動かしているPCのIPアドレス（例: 192.168.1.10）がわかれば、同じWi-Fi内であれば http://192.168.1.10:3000 でアクセスできます。ただし、セキュリティのためにファイアウォール設定には注意してください。"
      }
    },
    {
      "@type": "Question",
      "name": "4bit量子化（Q4_K_M）とは何ですか？品質は落ちませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデルの重みデータを圧縮する技術です。8bitや16bitに比べるとわずかに精度は落ちますが、VRAM使用量を劇的に減らせます。実務レベルでは4bitや5bitでも十分な性能を発揮するため、Ollamaのデフォルト設定（Q4）で問題ありません。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUが無いPCでも動かす方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、非常に低速です。CPU（AVX2命令セット対応）であれば実行自体は可能ですが、回答を待つ時間が苦痛になる可能性が高いです。その場合は、MacBookのApple Silicon搭載モデルへの乗り換えを強く検討してください。 ---"
      }
    }
  ]
}
</script>
