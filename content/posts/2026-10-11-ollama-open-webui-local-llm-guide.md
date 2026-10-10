---
title: "OllamaとOpen WebUIで自分専用のChatGPTをローカルに構築する方法"
date: 2026-10-11T00:00:00+09:00
slug: "ollama-open-webui-local-llm-guide"
cover:
  image: "/images/posts/2026-10-11-ollama-open-webui-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 構築"
  - "ローカルLLM 入門"
  - "Docker LLM"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部API（OpenAI等）を一切使わず、自分のPC内で完結するChatGPTクローンを構築します。
- ブラウザから操作でき、PDFの読み込み（RAG）やWeb検索連携も可能な実用的なAI環境です。
- 前提知識：ターミナルの基本操作ができる、Dockerという言葉を聞いたことがある程度で大丈夫です。

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

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
メインメモリ（RAM）ではなく、GPU（グラフィックボード）に載っているメモリが、生成速度と扱えるモデルの大きさを決定します。

Windows/Linux環境なら、最低でもVRAM 8GB（RTX 3060 / 4060等）が必要です。
仕事でストレスなく使いたいなら、VRAM 12GB以上、理想は16GB（RTX 4060 Ti 16GBモデルなど）を推奨します。
私はRTX 4090の24GBを2枚使っていますが、一般的な業務利用であれば1枚で十分です。

Macユーザーの場合、Apple Silicon（M1/M2/M3）であれば、メインメモリがVRAMの役割を兼ねるため、メモリ16GB以上が必須、32GBあれば非常に快適です。
逆に、メモリ8GBのMacBook Airでは、モデルのロードだけで精一杯になり、まともに動作しません。

料金については、PC本体と電気代以外は完全に0円です。
API料金の変動や、データの外部送信を一切気にせず、機密情報を含むコードのデバッグなども安心して行えるのが最大のメリットです。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は、LM Studio、GPT4All、Janなど多岐にわたります。
その中で、なぜ「Ollama + Open WebUI」の組み合わせがベストなのか。
理由は、役割分担が明確で、拡張性が桁違いだからです。

Ollamaは、モデルの管理と実行を司る「バックエンド」として非常に優秀です。
複雑なセットアップなしに、一行のコマンドで最新モデルを最適化された状態で動かせます。
一方、Open WebUIは、その名の通り「フロントエンド」を提供します。
これらを組み合わせることで、ChatGPTと遜色ないUIに加えて、複数人での利用、ドキュメント管理、ツール連携といった「実務で欲しい機能」をすべて手に入れられます。

他のツールは「動かして遊ぶ」には良いですが、仕事のインフラとして構築するなら、この構成一択だと断言します。

## Step 1: 環境を整える

まずは、LLMを動かすエンジンである「Ollama」をインストールします。

```bash
# macOS / Linux の場合（公式のスクリプトで一発です）
curl -fsSL https://ollama.com/install.sh | sh
```

Windowsの場合は、公式サイト（ollama.com）からインストーラーをダウンロードして実行してください。

なぜOllamaを単体で入れるのかというと、後述するDocker環境から切り離しておくことで、GPUの認識トラブルを最小限に抑えられるからです。
インストールが完了したら、正しく動作するかターミナル（またはコマンドプロンプト）で確認します。

```bash
ollama --version
```

バージョン番号が表示されれば成功です。
この時点で、Ollamaはバックグラウンドでサーバーとして待機しています。

⚠️ **落とし穴:**
Windows環境で、すでにDocker Desktopを起動している場合、稀にポート（デフォルトは11434）が競合することがあります。
もしOllamaが起動しない場合は、他のアプリケーションがこのポートを占有していないか確認してください。

## Step 2: 基本の設定（Docker Compose）

次に、UI部分となる「Open WebUI」をDockerで立ち上げます。
ブラウザからアクセスできるようにするため、設定ファイルを作成します。

作業用のディレクトリを作成し、その中に `docker-compose.yml` という名前のファイルを作成してください。

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: always
    ports:
      - "3000:8080"
    volumes:
      - open-webui:/app/backend/data
    environment:
      # Ollamaが同じPCで動いている場合、このアドレスを指定します
      - 'OLLAMA_BASE_URL=http://host.docker.internal:11434'
    extra_hosts:
      - "host.docker.internal:host-gateway"

volumes:
  open-webui: {}
```

この設定の肝は `OLLAMA_BASE_URL` です。
`host.docker.internal` を指定することで、Dockerコンテナの中から、あなたのPC本体で動いているOllamaにアクセスできるようになります。
「なぜDocker内にOllamaを入れないのか？」と疑問に思うかもしれませんが、コンテナ内でGPUを安定して認識させる設定は、OSやドライバのバージョンによって非常に壊れやすいため、ホスト側でOllamaを動かすのが最も堅実な方法です。

設定ファイルができたら、コマンドを実行します。

```bash
docker compose up -d
```

このコマンドは、Open WebUIのイメージをダウンロードし、バックグラウンドで起動します。

⚠️ **落とし穴:**
MacのDocker Desktopを使用している場合、設定の「General」タブにある「Choose file sharing implementation」が「VirtioFS」になっていることを確認してください。
これを確認しないと、ファイルの読み書きが異常に遅くなり、起動に数分かかることがあります。

## Step 3: 動かしてみる

ブラウザを開き、 `http://localhost:3000` にアクセスしてください。
最初のアクセスではアカウント作成を求められます。
これは「ローカル環境内の管理用アカウント」なので、好きなメールアドレスとパスワードを設定して大丈夫です。

ログイン後、まずはモデルをダウンロードする必要があります。
画面左下の設定（名前をクリック）から「設定」→「モデル」へと進みます。

ここで「モデルをプルする」欄に、使いたいモデル名を入力します。
まずは、軽量で高性能な「Llama 3.1 8B」を試してみましょう。

```text
llama3.1
```

ダウンロードボタンを押すと、バックグラウンドでOllamaがモデルを取得し始めます。
容量は約4.7GBですので、ネットワーク環境によりますが数分で終わります。

### 期待される出力

ダウンロードが終わると、トップ画面の「モデルを選択」から `llama3.1:latest` が選べるようになります。
適当に「日本語で自己紹介して」と投げてみてください。

```text
（出力例）
こんにちは！私はLlama 3.1、Metaによってトレーニングされた大規模言語モデルです。
あなたの質問に答えたり、文章を作成したり、プログラミングのサポートをしたりすることができます。
```

もし、返答が1秒間に数十文字のペースで流れてくるなら、GPUが正しく使われています。
逆に、一文字ずつゆっくり表示される場合は、CPUで動いている可能性があります。
その場合は、Ollamaのログを確認してGPUが認識されているかチェックしてください。

## Step 4: 実用レベルにする

単にチャットするだけならChatGPTで十分です。
ローカル環境ならではの「実戦投入」のための設定を2つ紹介します。

### 1. ドキュメントを読ませる（RAG機能）

Open WebUIの強力な点は、標準でRAG（検索拡張生成）機能が組み込まれていることです。
チャット欄にPDFやテキストファイルをドラッグ＆ドロップしてみてください。
ファイルがアップロードされると、AIはその内容を参照して回答するようになります。

「社内の仕様書」や「公開前の技術ドキュメント」など、クラウドにアップロードしたくない情報を扱うのに最適です。
設定の「ドキュメント」セクションで、埋め込みモデル（Embedding Model）をデフォルトの `sentence-transformers` から、日本語に強いモデルに変更することも可能です。

### 2. システムプロンプト（カスタム命令）の固定化

仕事で使う場合、「常にPythonエンジニアとして振る舞ってほしい」「回答は簡潔に結論から述べてほしい」といった要望があるはずです。
Open WebUIの「モデル」管理画面から、特定のモデルに対して「システムプロンプト」を設定できます。

私は以下のプロンプトを全てのモデルに入れています。

```text
あなたは経験豊富なシニアエンジニアです。
回答は常に結論から始め、理由を簡潔に述べてください。
コードを提示する場合は、保守性と可読性を重視し、複雑なロジックにはコメントを添えてください。
```

これにより、毎回「結論から書いて」と指示する手間が省け、業務効率が劇的に向上します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Connection Error` | DockerからOllamaに繋がっていない | `OLLAMA_BASE_URL` が正しいか、Ollamaが起動しているか確認 |
| 回答が非常に遅い | CPUで動作している | GPUドライバを最新にし、Ollamaを再起動する。VRAM不足でモデルがはみ出している可能性も |
| モデルが見つからない | プル（ダウンロード）が未完了 | ターミナルで `ollama list` を叩き、モデルが存在するか確認する |

## 次のステップ

ここまでで、あなたは自分専用のセキュアなAI環境を手に入れました。
次に挑戦すべきことは「モデルの使い分け」です。

- **日常的なタスク:** `llama3.1` (8B)
- **論理的思考が必要なタスク:** `gemma2` (9B) または `phi3:medium`
- **コーディング:** `deepseek-coder-v2` (Lite)

Open WebUIなら、チャット画面の上部でモデルを即座に切り替えられます。
また、DifyなどのプロンプトエンジニアリングツールとOllamaを連携させることで、特定の業務を自動化する「AIエージェント」の開発にも踏み出せます。

ローカルLLMの世界は、一度環境を作ってしまえば、あとはモデルを入れ替えるだけで最新技術を追い続けられます。
まずは自分のPCを、24時間無償で働いてくれる優秀なアシスタントに変えるところから始めてみてください。

## よくある質問

### Q1: 複数のPCからこのWebUIを使うことはできますか？

可能です。Dockerを動かしているPCのIPアドレス（例: 192.168.1.10）を調べれば、同じWi-Fi内のスマホや別のPCから `http://192.168.1.10:3000` でアクセスできます。家族やチームで共有のAIサーバーとして運用するのも便利です。

### Q2: モデルのダウンロードに失敗したり、途中で止まったりします。

Ollamaのダウンロードサーバーが混み合っているか、ディスク容量不足が考えられます。特にLlama 3.1 70Bなどの巨大なモデルを落とす際は、40GB以上の空き容量を確保してください。失敗した場合は `ollama pull` コマンドを再度実行すれば、途中から再開されます。

### Q3: OpenAIのAPIも使いたいのですが、統合できますか？

はい、簡単にできます。Open WebUIの設定画面の「外部接続」から、OpenAIのAPIキーを入力するだけで、ローカルモデルとGPT-4oを同じUIで使い分けることができます。コストを抑えたい時はローカル、精度重視の時はGPT-4oといったハイブリッド運用が私のおすすめです。

---

## あわせて読みたい

- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-07-05-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のローカルAI環境を構築する方法](/posts/2026-07-11-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIの使い方！完全プライベートなローカルLLM環境を構築する方法](/posts/2026-07-07-ollama-openwebui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "複数のPCからこのWebUIを使うことはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Dockerを動かしているPCのIPアドレス（例: 192.168.1.10）を調べれば、同じWi-Fi内のスマホや別のPCから http://192.168.1.10:3000 でアクセスできます。家族やチームで共有のAIサーバーとして運用するのも便利です。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルのダウンロードに失敗したり、途中で止まったりします。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaのダウンロードサーバーが混み合っているか、ディスク容量不足が考えられます。特にLlama 3.1 70Bなどの巨大なモデルを落とす際は、40GB以上の空き容量を確保してください。失敗した場合は ollama pull コマンドを再度実行すれば、途中から再開されます。"
      }
    },
    {
      "@type": "Question",
      "name": "OpenAIのAPIも使いたいのですが、統合できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、簡単にできます。Open WebUIの設定画面の「外部接続」から、OpenAIのAPIキーを入力するだけで、ローカルモデルとGPT-4oを同じUIで使い分けることができます。コストを抑えたい時はローカル、精度重視の時はGPT-4oといったハイブリッド運用が私のおすすめです。 ---"
      }
    }
  ]
}
</script>
