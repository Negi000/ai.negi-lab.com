---
title: "OllamaとOpen WebUIを組み合わせて自分専用のローカルChatGPT環境を構築する方法"
date: 2026-07-08T00:00:00+09:00
slug: "ollama-open-webui-local-llm-tutorial"
cover:
  image: "/images/posts/2026-07-08-ollama-open-webui-local-llm-tutorial.jpg"
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
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIを一切使わず、完全にオフラインで動作する高機能なAIチャット環境を構築します。
- ブラウザからChatGPTと同じ操作感で、Llama 3.1やGemma 2といった最新のオープンソースモデルを切り替えて使えます。
- PC内に保存したPDFやテキストファイルを読み込ませて回答させるRAG（検索拡張生成）機能も標準で実装します。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3.1(8B)を最速クラスで動かせる、最もコスパの良い選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

### 前提条件
- DockerまたはDocker Desktopがインストールされていること
- ターミナル（PowerShell, Terminal.app等）の基本的な操作ができること
- インターネット環境（モデルのダウンロードに数GB使用します）

---

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。メインメモリ（RAM）ではなく、GPU（グラフィックボード）に載っているメモリが処理速度のすべてを決めると言っても過言ではありません。

最低ラインはVRAM 8GBです。これでLlama 3.1 (8B) やGemma 2 (9B) クラスのモデルがストレスなく（秒間10〜20トークン程度で）動きます。もし実務で「長い文章の要約」や「複雑なプログラミング」をさせるなら、VRAM 12GB以上のRTX 3060/4060 Ti（16GB版がベスト）、あるいはApple Silicon（M1/M2/M3）を搭載したメモリ16GB以上のMacを用意してください。

Windows機でグラボがない場合、CPUとメインメモリでも動作はしますが、回答速度は1秒間に数文字程度まで落ちます。これは正直、実用的ではありません。本気で取り組むなら、中古のRTX 3090（VRAM 24GB）を積んだPCを組むのが、今の自作界隈での「正解」です。私はRTX 4090を2枚挿していますが、これなら70Bクラスの巨大モデルもサクサク動きます。

料金については、電気代以外は完全に無料です。OpenAIに毎月20ドル（約3,000円）払う必要はありません。

---

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールには「LM Studio」や「GPT4All」など、より簡単なGUIツールも存在します。しかし、私が「Ollama + Open WebUI」の組み合わせを推奨するのは、これが「最も拡張性が高く、実務に近い」からです。

Ollamaはバックエンドとして非常に優秀で、APIサーバーとして動作します。これにより、CursorやDifyといった他のツールからも同じモデルを呼び出せます。そしてOpen WebUIは、本家ChatGPTを超えるほどの多機能なインターフェースを提供してくれます。履歴の管理、マルチモーダル対応、RAG機能、さらには他のユーザーとの共有機能まで、Docker一つで完結するこの構成は、エンジニアにとっての「黄金セット」です。

---

## Step 1: Ollamaをインストールする

まずはLLMの実行エンジンである「Ollama」をインストールします。これがなければ何も始まりません。

### Windows / macOSの場合
公式サイト（https://ollama.com/ ）からインストーラをダウンロードして実行するだけです。インストール後、メニューバーに「羊」のアイコンが表示されれば成功です。

### Linuxの場合
以下のコマンドを叩きます。

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

このコマンドは、Ollamaの実行バイナリをダウンロードし、システムサービスとして登録します。

⚠️ **落とし穴:**
WindowsユーザーでWSL2を使っている場合、WSL2内ではなく「Windows側」にOllamaをインストールすることをお勧めします。GPUアクセラレーションの設定がWindowsネイティブの方が圧倒的に楽だからです。もしWSL2内からアクセスしたい場合は、環境変数 `OLLAMA_HOST=0.0.0.0` の設定が必要になりますが、まずはネイティブ版で進めましょう。

---

## Step 2: Open WebUIをDockerで起動する

次に、ブラウザから操作するためのフロントエンド「Open WebUI」を立ち上げます。これにはDockerを使います。

ターミナルを開き、以下のコマンドをコピー＆ペーストして実行してください。

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/data --name open-webui ghcr.io/open-webui/open-webui:main
```

### コマンドの解説
- `-d`: バックグラウンドで実行します。
- `-p 3000:8080`: PCの3000番ポートでアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: **ここが最重要です。** Dockerコンテナの中から、ホストPCで動いているOllamaに通信できるようにするための設定です。
- `-v open-webui:/app/data`: チャット履歴や設定を保存する領域（ボリューム）を作成します。これがないと、Dockerを再起動したときに履歴が消えます。

起動したら、ブラウザで `http://localhost:3000` にアクセスしてください。初回はアカウント作成画面が出ますが、これは自分のPC内だけに保存されるデータなので、適当なメールアドレスとパスワードで登録してログインします。

---

## Step 3: モデルをダウンロードして動かしてみる

ログインしても、最初は「モデルがありません」という状態です。Ollamaを通じて、AIの「脳」にあたるモデルをダウンロードします。

1. Open WebUIの画面左下、または設定（Settings）から「外部接続」を確認し、Ollamaと接続されているか確認します。
2. 画面上部のモデル選択プルダウン、または設定内の「モデル」から、`llama3.1` と入力してダウンロードボタンを押します。
3. 日本語能力を重視するなら `gemma2` もお勧めです。

### 動作確認
ダウンロードが終わったら、チャット欄にこう打ってみてください。

```text
あなたは優秀なアシスタントです。ローカルLLMを動かすメリットを3点、簡潔に日本語で教えてください。
```

### 期待される出力
```text
1. プライバシー: 外部サーバーにデータが送信されないため、機密情報を扱えます。
2. コスト: 一度環境を構築すれば、API使用料を気にせず無制限に利用可能です。
3. カスタマイズ: モデルの挙動やシステムプロンプトを自由に変更できます。
```

レスポンスが返ってくれば、環境構築は成功です。

---

## Step 4: 実用レベルの設定（RAGとModelfile）

単にチャットするだけならChatGPTで十分です。ここからは「ローカルだからこそできる」実用的なカスタマイズを行います。

### 1. 独自の「専門家」を作る（Modelfile）
特定の役割を与えたモデルを固定できます。Open WebUIの「モデル」作成画面から、ベースモデルを `llama3.1` に指定し、システムプロンプトに以下を設定してみましょう。

```text
# システムプロンプト例
あなたはPython専門のシニアエンジニアです。
回答は必ずコード例を含め、PEP8準拠で書いてください。
余計な挨拶は不要です。
```

これで、毎回「プログラミングのアドバイスをして」と指示しなくても、即座に専門的なコードが返ってくる専用AIが完成します。

### 2. ローカルドキュメントを読み込ませる（RAG）
Open WebUIのチャット欄にファイルをドラッグ＆ドロップするか、`#` を入力してみてください。PC内のドキュメントを参照して回答するモードになります。
これは、会社の社内規定PDFや、進行中のプロジェクトの仕様書を読み込ませるのに最適です。データは一切外に出ないため、社外秘の情報でも安心して放り込めます。

### 3. GPU使用率を最適化する（Windows）
もし動作が重いと感じたら、タスクマネージャーの「パフォーマンス」タブで「専用ビデオメモリ」が溢れていないか確認してください。VRAMが足りないと、処理がメインメモリ（RAM）にスワップされ、極端に遅くなります。その場合は、パラメータ数の少ないモデル（例: `phi3:mini` や `llama3.1:8b` の軽量量子化版）を選ぶのが賢明です。

---

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error (Ollamaに繋がらない) | Dockerからホストへの通信が遮断されている | Docker起動時の `--add-host` オプションを確認し、Ollamaの設定で `OLLAMA_ORIGINS="*"` を設定する |
| 回答がめちゃくちゃ遅い | GPUではなくCPUで動作している | NVIDIAの場合は最新のドライバを入れ、OllamaがGPUを認識しているかログを確認する |
| ブラウザに何も表示されない | ポート競合またはDockerの起動失敗 | `docker ps` でコンテナが動いているか確認し、他のアプリが3000番ポートを使っていないか調べる |

---

## 次のステップ

環境が整ったら、次は「自分の業務フローにどう組み込むか」を考えてみましょう。
例えば、Pythonスクリプトを書いて、OllamaのAPI（デフォルトで `http://localhost:11434/api/generate`）を叩き、大量のテキストデータを一括で要約させる処理などは、ローカル環境ならではの活用法です。

また、「Dify」というツールと今回作ったOllamaを連携させると、さらに高度なAIエージェントをノーコードで構築できます。Llama 3.1 70Bなどの巨大なモデルを動かしたい衝動に駆られたら、それはRTX 3090/4090をポチるタイミングかもしれません。VRAM 24GBの世界へようこそ。

---

## よくある質問

### Q1: Macのメモリは最低どれくらい必要ですか？

最低16GB、できれば32GB以上を推奨します。Apple SiliconはメインメモリとVRAMが共有されている（ユニファイドメモリ）ため、OSやブラウザが使う分を差し引くと、8GBモデルではAIに割り当てられる容量が極めて少なくなり、動作が不安定になります。

### Q2: 企業で導入する際のセキュリティリスクはありますか？

この構成の最大の特徴は「エアギャップ（オフライン）」運用が可能な点です。Dockerイメージとモデルを一度ダウンロードしてしまえば、ネット接続を切っても動作します。ただし、Open WebUIの認証設定を怠り、社内ネットワークに公開設定で放置するのは危険です。必ず管理用パスワードを設定してください。

### Q3: 日本語の精度が一番高いモデルは何ですか？

2024年現在の私のお気に入りは、Googleの `Gemma 2 (9B / 27B)` です。日本語の自然さと論理的思考のバランスが非常に良い。次点で `Llama 3.1` ですが、こちらはシステムプロンプトで「日本語で回答して」と強めに指示する必要があります。

---

## あわせて読みたい

- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-06-28-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIの使い方！完全プライベートなローカルLLM環境を構築する方法](/posts/2026-07-07-ollama-openwebui-local-llm-guide/)
- [NVIDIA vs Mac 2026年版ローカルLLM環境構築ガイド](/posts/2026-05-25-local-llm-nvidia-vs-mac-2026-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Macのメモリは最低どれくらい必要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "最低16GB、できれば32GB以上を推奨します。Apple SiliconはメインメモリとVRAMが共有されている（ユニファイドメモリ）ため、OSやブラウザが使う分を差し引くと、8GBモデルではAIに割り当てられる容量が極めて少なくなり、動作が不安定になります。"
      }
    },
    {
      "@type": "Question",
      "name": "企業で導入する際のセキュリティリスクはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "この構成の最大の特徴は「エアギャップ（オフライン）」運用が可能な点です。Dockerイメージとモデルを一度ダウンロードしてしまえば、ネット接続を切っても動作します。ただし、Open WebUIの認証設定を怠り、社内ネットワークに公開設定で放置するのは危険です。必ず管理用パスワードを設定してください。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の精度が一番高いモデルは何ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "2024年現在の私のお気に入りは、Googleの Gemma 2 (9B / 27B) です。日本語の自然さと論理的思考のバランスが非常に良い。次点で Llama 3.1 ですが、こちらはシステムプロンプトで「日本語で回答して」と強めに指示する必要があります。 ---"
      }
    }
  ]
}
</script>
