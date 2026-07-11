---
title: "OllamaとOpen WebUIで自分専用のローカルAI環境を構築する方法"
date: 2026-07-11T00:00:00+09:00
slug: "ollama-open-webui-local-llm-tutorial"
cover:
  image: "/images/posts/2026-07-11-ollama-open-webui-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "Llama 3.1 ローカル"
  - "Docker LLM"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- インターネット不要で動作し、データが外部に流出しない完全プライベートなChatGPT風チャット環境
- 最新のオープンソースモデル（Llama 3.1、Gemma 2、Mistral等）をGUIで即座に切り替えて検証できる基盤
- 前提知識: 基本的なコマンド操作（ターミナルやコマンドプロンプト）ができること、Dockerの概念をなんとなく知っていること
- 必要なもの: NVIDIA製GPU（推奨）またはApple Silicon搭載のMac、Docker環境

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的。安価にVRAMを確保する最適解。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMの世界では、CPU性能よりも「GPUのビデオメモリ（VRAM）」が全てを決めます。
私が業務で20件以上の案件をこなした経験から言うと、VRAM 8GBが最低ライン、12GBでようやく実用、16GB以上で快適という感覚です。
RTX 4060 Tiの16GB版は、AIエンジニアの間では「安価なVRAMタンク」として定番の選択肢になっています。

Macの場合、メモリ（ユニファイドメモリ）がVRAMを兼ねるため、最低24GB、できれば32GB以上のモデルを選んでください。
8GBや16GBのMacでは、Llama 3の8B（80億パラメータ）モデルを動かすだけで精一杯になり、レスポンスが1秒間に数文字という「実務で使えない」速度まで落ち込みます。

ソフトウェア自体は全て無料（オープンソース）です。
クラウドLLMのような月額$20のサブスク料金はかかりませんが、PCをフル稼働させるため電気代は多少増えます。
私のRTX 4090環境では、推論時に数百ワット消費しますが、API課金を気にして思考を止めるコストに比べれば微々たるものです。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、LM StudioやGPT4Allなど他にもあります。
しかし、あえて「Ollama + Open WebUI」の組み合わせを推奨するのは、これが最も「本番環境に近い拡張性」を持っているからです。

Ollamaは内部でllama.cppを動かしていますが、APIサーバーとしての機能が非常に洗練されています。
Open WebUIは単なるチャット画面ではなく、RAG（ドキュメント読み込み）、Web検索連携、マルチユーザー管理など、実務で必要な機能がほぼ全て揃っています。
この組み合わせをDockerで構築しておけば、将来的に別のサーバーへ移行したり、自作のPythonアプリからAPIとして叩いたりする際もスムーズです。
「とりあえず動くおもちゃ」ではなく「開発のベースライン」としてこの構成をマスターしてください。

## Step 1: 環境を整える

まずは、LLMの実行エンジンである「Ollama」をインストールします。

```bash
# macOS / Linux の場合
curl -fsSL https://ollama.com/install.sh | sh

# Windows の場合
# 公式サイト (https://ollama.com/) からインストーラーをダウンロードして実行
```

インストール後、ターミナルで以下のコマンドを打ち、バージョンが表示されれば成功です。

```bash
ollama --version
```

次に、モデルをダウンロードします。今回は最も汎用性の高い「Llama 3.1 (8B)」を選択します。

```bash
ollama pull llama3.1
```

なぜLlama 3.1なのか。それは、このサイズで最も日本語の精度と推論速度のバランスが取れているからです。
4bit量子化版であれば約4.7GBのVRAM消費で済むため、現世代の多くのGPUで快適に動作します。

⚠️ **落とし穴:**
WindowsユーザーでWSL2を使っている場合、OllamaをWSL2の中にインストールするか、Windowsネイティブにインストールするか迷うはずです。
結論としては「Windowsネイティブ」へのインストールを推奨します。
WSL2経由だとGPUのパススルー設定でハマる初心者が非常に多く、パフォーマンスもネイティブの方が安定します。

## Step 2: DockerでOpen WebUIを起動する

Open WebUIをインストールするにはDockerを使うのが最も賢い選択です。
Pythonの仮想環境を作ってライブラリを一つずつ入れる手間は、依存関係の地獄（Dependency Hell）を招くだけです。

以下のコマンドをコピーして実行してください。これはOllamaが既に同じPCで動いている（Localhost）ことを前提とした設定です。

```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

各設定の意味を解説します。
- `-p 3000:8080`: ブラウザから `http://localhost:3000` でアクセスできるようにします。
- `--add-host=...`: Dockerコンテナの中から、ホスト側で動いているOllama（ポート11434）を見つけるための魔法の呪文です。
- `-v open-webui:/app/backend/data`: チャット履歴や設定を保存する領域（ボリューム）を作成します。これがないとコンテナを再起動した時に全てのデータが消えます。

⚠️ **落とし穴:**
Docker Desktopをインストールした直後のWindows/Macでは、Dockerに割り当てられているメモリ制限がデフォルトで低い場合があります。
設定画面からリソース（Resources）を開き、メモリを最低でも4GB以上（できれば8GB以上）割り当てておかないと、Open WebUIの起動プロセスが途中で落ちることがあります。

## Step 3: 動かしてみる

ブラウザを開き、`http://localhost:3000` にアクセスしてください。
最初のログイン画面ではアカウント作成を求められます。
「ローカルなのにアカウント？」と思うかもしれませんが、これは複数のユーザーで環境を共有するための仕様です。
データはローカルに保存されるので、適当な名前とメールアドレス（実在しなくてOK）で登録してください。最初に登録したユーザーが管理者権限を持ちます。

ログイン後、画面上部の「モデルを選択」から `llama3.1:latest` を選択します。

### 期待される出力

チャット欄に「こんにちは、自己紹介してください」と入力します。

```text
（出力例）
こんにちは！私はLlama 3.1ベースのAIアシスタントです。
あなたのPC上で直接動作しており、プライバシーを守りながらお手伝いできます。
```

もしここで「モデルが見つかりません」というエラーが出る場合は、Open WebUIの設定（Settings）→「外部接続（Connections）」を確認してください。
OllamaのURLが `http://host.docker.internal:11434` になっている必要があります。
「localhost」ではDockerコンテナ自身を指してしまうため、接続に失敗します。

## Step 4: 実用レベルにする

単にチャットするだけならChatGPTで十分です。ローカルLLMを仕事で使うなら「Modelfile」を活用しましょう。
Open WebUIの「Workspace」→「Models」から、独自のカスタマイズモデルを作成できます。

例えば、私はSIer時代の経験を活かし、コードレビュー専用のモデルを以下のように定義しています。

```text
# Modelfileの例（Open WebUI上の設定）
FROM llama3.1
SYSTEM """
あなたはシニアソフトウェアエンジニアです。
提供されたコードに対して、以下の3点でフィードバックを行ってください。
1. セキュリティ脆弱性の有無
2. 計算量（Time Complexity）の観点からの改善案
3. Pythonicな書き方への修正
回答は常に簡潔にし、まず結論から述べてください。
"""
PARAMETER temperature 0.2
```

なぜ `temperature` を 0.2 にするのか。
デフォルトの 0.8 だとAIが「創造的」になりすぎて、コードの解釈に嘘（ハルシネーション）が混じるリスクが高まるからです。
技術的なタスクでは、この値を下げることで回答の再現性を高めるのが鉄則です。

また、Open WebUIの強力な機能に「RAG（検索拡張生成）」があります。
チャット欄にPDFやテキストファイルをドラッグ＆ドロップし、その内容について質問してみてください。
社外秘のドキュメントを読み込ませても、データは1bitも外に送信されません。
これが、私たちがクラウドではなくローカルを選ぶ最大の理由です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| 回答が極端に遅い | GPUではなくCPUで動いている | Ollamaの設定を確認。NVIDIAのドライバーが最新かチェック。 |
| 接続拒否 (Connection Refused) | Ollamaが起動していない、またはポートが閉じている | `ollama serve` が実行されているか確認。Windowsならタスクトレイをチェック。 |
| Dockerが起動しない | 仮想化機能(VT-x)がBIOSで無効 | PC再起動時にBIOS設定を開き、Virtualization TechnologyをEnableにする。 |

## 次のステップ

ここまでで、自分だけのローカルLLM環境が整いました。
次に挑戦すべきは「API経由での自動化」です。
OllamaはOpenAI互換のAPIエンドポイントを持っています。つまり、普段使っているPythonスクリプトの `base_url` を `http://localhost:11434/v1` に書き換えるだけで、自作ツールにローカルLLMを組み込めます。

例えば、大量のログファイルをローカルで要約させたり、機密性の高いメールの下書きを自動生成させたりといったことが、コストゼロで無限に行えるようになります。
また、余裕があれば「Quantization（量子化）」の理論についても調べてみてください。
なぜ16ビットのモデルを4ビットに圧縮しても精度が落ちないのかを理解すると、ハードウェア選びの解像度が一段と上がります。

## よくある質問

### Q1: RTX 3060（12GB）と 4060（8GB）ならどちらが良いですか？

断然、RTX 3060 12GBです。ローカルLLMにおいては、チップの世代の新しさよりもVRAMの容量が正義です。8GBだと、少し大きめのモデル（Llama 3 70Bの量子化版など）を動かそうとした瞬間にメモリ不足でクラッシュします。

### Q2: 会社で使う場合、セキュリティチームにどう説明すればいいですか？

「このシステムは外部ネットワークへのアウトバウンド通信を一切行わず、ローカルネットワーク内で完結する」と説明してください。実際にインターネットを切断した状態でデモを見せるのが最も説得力があります。

### Q3: モデルをダウンロードしすぎてディスク容量が足りません。

Ollamaのモデルは `~/.ollama/models` に保存されます。不要なモデルは `ollama rm モデル名` でこまめに消去しましょう。また、外部SSDに保存したい場合は、環境変数 `OLLAMA_MODELS` で保存先パスを指定可能です。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-06-16-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPT環境を作る方法](/posts/2026-05-31-ollama-openwebui-local-llm-setup-guide/)
- [OllamaとOpen WebUIの使い方！自分専用のローカルLLM環境を完全構築する方法](/posts/2026-06-26-ollama-open-webui-local-llm-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3060（12GB）と 4060（8GB）ならどちらが良いですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "断然、RTX 3060 12GBです。ローカルLLMにおいては、チップの世代の新しさよりもVRAMの容量が正義です。8GBだと、少し大きめのモデル（Llama 3 70Bの量子化版など）を動かそうとした瞬間にメモリ不足でクラッシュします。"
      }
    },
    {
      "@type": "Question",
      "name": "会社で使う場合、セキュリティチームにどう説明すればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "「このシステムは外部ネットワークへのアウトバウンド通信を一切行わず、ローカルネットワーク内で完結する」と説明してください。実際にインターネットを切断した状態でデモを見せるのが最も説得力があります。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルをダウンロードしすぎてディスク容量が足りません。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaのモデルは ~/.ollama/models に保存されます。不要なモデルは ollama rm モデル名 でこまめに消去しましょう。また、外部SSDに保存したい場合は、環境変数 OLLAMAMODELS で保存先パスを指定可能です。 ---"
      }
    }
  ]
}
</script>
