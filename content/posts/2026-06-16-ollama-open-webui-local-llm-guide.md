---
title: "OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法"
date: 2026-06-16T00:00:00+09:00
slug: "ollama-open-webui-local-llm-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM RAG"
  - "Llama 3 日本語設定"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- インターネット不要でChatGPTのようにチャットができるローカルAI環境
- Ollamaをバックエンド、Open WebUIをフロントエンドにしたブラウザベースの操作画面
- 自分の持っているPDFやテキストファイルを読み込ませて回答させるRAG環境

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に最適。省電力で一般PCでも動かしやすい</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

この記事では、コマンド1つで起動し、即座に業務で使えるレベルのプライベートLLM環境を構築します。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、もっとも重要なのはCPUではなくGPUのビデオメモリ（VRAM）です。
私がRTX 4090を2枚挿しているのは、パラメーター数の多い巨大なモデルを高速に動かすためですが、入門ならそこまで必要ありません。

最低限、以下のスペックを満たしているか確認してください。

- **GPU:** NVIDIA製（VRAM 8GB以上推奨）または Apple Silicon（M1/M2/M3）
- **メモリ:** 16GB以上（32GBあれば安定）
- **ストレージ:** SSD空き容量 20GB以上（モデル1つにつき4GB〜10GB消費します）

WindowsユーザーでNVIDIAのGPUを持っていない場合、CPUだけでも動きますが、レスポンス速度は1トークン/秒程度まで落ち、実用的ではありません。
Macの場合は、ユニファイドメモリをOSが賢く割り振ってくれるため、16GBモデルなら「Llama 3 8B」クラスが驚くほど快適に動きます。
料金は、PC代と電気代を除けば**完全無料**です。API料金を気にせず、1日中10万トークン投げ続けても月額$0で済みます。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールは、他にもLM StudioやJanなどがあります。
それらと比較して、なぜ「Ollama + Open WebUI」の組み合わせがベストなのか。
理由は、**「拡張性と管理のしやすさ」**にあります。

Ollamaは軽量なバイナリで動作し、バックグラウンドでデーモンとして常駐します。
一方、Open WebUIはDockerで動作するため、ホスト環境を汚さずに済みます。
さらに、Open WebUIはRAG機能（PDF読み込み）やマルチユーザー管理、Modelfileの編集機能が他のツールより頭一つ抜けて洗練されています。
「ただ動かす」だけでなく「仕事のツールとして運用する」なら、この構成以外に選択肢はありません。

## Step 1: Ollamaのインストール

まずは心臓部となるOllamaをインストールします。
これはLLMのモデルをダウンロードし、推論（計算）を行うためのエンジンです。

1. [Ollama公式サイト](https://ollama.com/)にアクセスし、OSに合わせたインストーラーをダウンロードします。
2. インストーラーを実行し、画面の指示に従って完了させます。

インストールが終わったら、ターミナル（WindowsならPowerShell）を開いて以下のコマンドを叩いてください。

```bash
ollama --version
```

バージョンが表示されれば成功です。
次に、世界標準の軽量モデル「Llama 3」をダウンロードしておきます。

```bash
ollama pull llama3
```

**なぜこのコマンドを打つのか:**
`pull` はモデルのデータをローカルに保存する作業です。
事前にダウンロードしておくことで、後のWebUI設定時にスムーズに動作確認ができます。

⚠️ **落とし穴:**
Windows環境でWSL2を使っている場合、WSL側ではなくWindows本体側にOllamaをインストールすることをおすすめします。
WSL2経由だとGPUのパススルー設定でハマる初心者が非常に多いからです。
まずはWindowsネイティブ版で動かし、慣れてからDockerやWSLを検討しましょう。

## Step 2: Docker環境の準備

Open WebUIを動かすには、Dockerが必要です。
「わざわざDockerを使うのは面倒」と思うかもしれませんが、Open WebUIは頻繁にアップデートされます。
Dockerであれば、イメージを入れ替えるだけで最新機能が使えるため、長期的なメンテナンスコストが圧倒的に低くなります。

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/)をインストールします。
2. インストール後、設定の「Resources」でメモリ割り当てが十分か確認してください。

Mac（Apple Silicon）の場合、Dockerの設定で「Use Rosetta for x86_64/amd64 emulation」にチェックが入っていることを確認してください。
これがオフだと、一部のコンテナが正常に動作しないことがあります。

## Step 3: Open WebUIを起動する

いよいよ、チャット画面を立ち上げます。
ターミナルで以下のコマンドをコピー＆ペーストしてください。
これは「Ollamaが同じPC内で動いている場合」の標準的なコマンドです。

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

**設定のポイント解説:**
- `-p 3000:8080`: ブラウザから `http://localhost:3000` でアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: Dockerコンテナの中から、ホスト側で動いているOllama（11434ポート）を見つけられるようにするための設定です。これがないと「Connection Error」で詰まります。
- `-v open-webui:/app/backend/data`: チャット履歴や設定を保存する領域（ボリューム）を作成しています。これがないと、Dockerを再起動するたびに履歴が消えます。

コマンド実行後、1〜2分待ってからブラウザで `http://localhost:3000` を開いてください。

### 期待される出力
ログイン画面が表示されれば成功です。
最初のユーザー登録は、完全オフラインで自分だけのデータベースに保存されるので、適当なメールアドレスとパスワードで構いません。

## Step 4: Ollamaと連携させて実用レベルにする

ログインしたら、左上の設定（歯車アイコン）から「Settings」→「Connections」を確認します。
Ollama Base URLが `http://host.docker.internal:11434` になっているはずです。
「Check connection」をクリックして緑色のチェックが出れば、連携完了です。

次に、実際にAIに仕事をさせてみましょう。

### 1. モデルを選択する
画面上部のセレクトボックスから、先ほどpullした `llama3:latest` を選びます。

### 2. 日本語で指示を出す
「こんにちは、あなたの得意なことを教えてください」と入力します。
もし英語で返ってくる場合は、以下の設定を試してください。

### 3. Modelfileで日本語特化設定を作る
Open WebUIの「Workspace」→「Models」→「Create a model」から、自分専用のカスタムモデルを作れます。
- **Base Model:** `llama3:latest`
- **System Prompt:** `あなたは優秀な日本人アシスタントです。必ず日本語で、丁寧な敬語で回答してください。`

このように、特定の役割（プログラマー、翻訳家、校正者）を与えたモデルを量産できるのが、ローカルLLMの醍醐味です。

## 実務で使えるRAG（資料読み込み）機能を試す

私がOpen WebUIを推す最大の理由が、標準搭載されたRAG機能です。
チャット欄にPDFファイルをドラッグ＆ドロップしてください。
その後、プロンプトの先頭に `#` を入力すると、アップロードしたファイルが参照先として選択できます。

「この資料の要点を3つにまとめて」と入力するだけで、外部サーバーにデータを送信することなく、手元のPC内だけで重要書類の解析が完結します。
これはセキュリティに厳しいSIer時代の私から見ても、革命的な利便性です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error (11434) | Ollamaが起動していない | タスクバーにOllamaのアイコンがあるか確認 |
| WebUIが重くて動かない | Dockerのメモリ割り当て不足 | Docker Desktopの設定でメモリを8GB以上に増やす |
| GPUが認識されない | NVIDIA Container Toolkit未導入 | Linux環境の場合、専用のToolkitをインストールする必要あり |
| 返答がめちゃくちゃ遅い | CPUで動作している | VRAM容量の小さいモデル（Gemma-2bなど）に変更する |

## 次のステップ

ここまでできれば、あなたのPCは「プライバシーが守られた最強の思考ツール」に進化しました。
次に挑戦すべきことは以下の3つです。

1. **より強力なモデルの試用:**
   VRAMが12GB以上あるなら、`Mistral` や `Qwen2` を試してください。特に日本語能力はモデルによって大きな差があります。
2. **自動化の構築:**
   OllamaのAPIポート（11434）はPythonからも叩けます。これを使って「フォルダ内の全ファイルを一括で要約するスクリプト」などを自作してみましょう。
3. **ハードウェアの増強:**
   ローカルLLMは「機材への投資」がそのまま「知能の向上」に直結します。中古のRTX 3090（VRAM 24GB）を手に入れると、動かせるモデルの選択肢が劇的に広がります。

自分で環境を構築したことで、もうAI企業の価格改定や規約変更に怯える必要はありません。

## よくある質問

### Q1: 社内のPCで構築しても大丈夫ですか？

技術的には可能ですが、Dockerのインストールには管理者権限が必要です。また、ローカルでLLMを回すとPCのファンが全開で回り、消費電力も上がるため、ノートPCよりはデスクトップPCでの運用を推奨します。

### Q2: モデルをダウンロードしすぎて容量が足りなくなりました。

Ollamaのモデル保存先はデフォルトでCドライブです。環境変数 `OLLAMA_MODELS` を設定することで、外付けSSDなどに保存先を変更できます。500GB程度の専用SSDがあると安心です。

### Q3: Open WebUIを他のデバイス（スマホなど）から使えますか？

同じWi-Fi内であれば、PCのIPアドレスをスマホのブラウザに入力（例: `http://192.168.1.5:3000`）すればアクセス可能です。自分専用のプライベートAIを持ち歩く感覚で使えます。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のChatGPT環境を作る方法](/posts/2026-05-31-ollama-openwebui-local-llm-setup-guide/)
- [Ollama 使い方 入門: 限られたGPU資産で実用的なローカルLLM環境を構築する方法](/posts/2026-06-13-ollama-local-llm-python-tutorial-for-beginners/)
- [Qwen3.6-27BとCoder-Nextをローカル環境で動かしてGit Diffから自動レビューを行うスクリプトを作る方法](/posts/2026-05-03-qwen3-coder-next-local-git-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "社内のPCで構築しても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "技術的には可能ですが、Dockerのインストールには管理者権限が必要です。また、ローカルでLLMを回すとPCのファンが全開で回り、消費電力も上がるため、ノートPCよりはデスクトップPCでの運用を推奨します。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルをダウンロードしすぎて容量が足りなくなりました。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaのモデル保存先はデフォルトでCドライブです。環境変数 OLLAMAMODELS を設定することで、外付けSSDなどに保存先を変更できます。500GB程度の専用SSDがあると安心です。"
      }
    },
    {
      "@type": "Question",
      "name": "Open WebUIを他のデバイス（スマホなど）から使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "同じWi-Fi内であれば、PCのIPアドレスをスマホのブラウザに入力（例: http://192.168.1.5:3000）すればアクセス可能です。自分専用のプライベートAIを持ち歩く感覚で使えます。 ---"
      }
    }
  ]
}
</script>
