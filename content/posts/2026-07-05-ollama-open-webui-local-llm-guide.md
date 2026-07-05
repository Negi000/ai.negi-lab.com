---
title: "OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法"
date: 2026-07-05T00:00:00+09:00
slug: "ollama-open-webui-local-llm-guide"
cover:
  image: "/images/posts/2026-07-05-ollama-open-webui-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 構築"
  - "ローカルLLM RAG"
  - "Llama 3.1 日本語設定"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIを一切使わず、自分のPC内だけで完結するChatGPTライクなチャットUI環境
- Dockerを使用したOpen WebUIの構築と、Ollamaによる複数モデルの管理システム
- 業務資料（PDFやテキスト）を読み込ませて回答させる「ローカルRAG」の基盤

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3.1 8Bクラスを高速に動かせるコスパ最強ボード</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、コマンドプロンプトやターミナルでコマンドをコピー＆ペーストできる程度の操作スキルが必要です。Pythonのコードをバリバリ書く必要はありませんが、Dockerという仮想化ツールを使用します。

## 先に確認するスペック・料金

ローカルLLMを「仕事で使える速度」で動かすには、CPUよりもGPU（グラフィックボード）の性能がすべてを決めます。
私が推奨する最低ラインは、NVIDIA製GPUならVRAM（ビデオメモリ）が12GB以上、Macならメモリ（ユニファイドメモリ）が16GB以上のモデルです。
VRAMが8GB以下のPCでも動作自体はしますが、回答速度が1秒間に数文字程度となり、実用には耐えません。

具体的には、Windowsユーザーなら「RTX 3060 12GB」がコストパフォーマンスにおける最低ラインの聖域です。
「RTX 4060 Ti 16GB」があれば、現在主流の「Llama 3.1 8B」クラスのモデルが爆速（秒間50トークン以上）で動きます。
Macユーザーの場合、M2/M3チップ以降を搭載し、メモリを24GB以上にカスタマイズしたモデルが理想的です。
これらがあれば、電気代以外に月額費用を1円も払うことなく、無制限にAIと対話できる環境が手に入ります。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、LM StudioやGPT4Allなど他にもいくつか存在します。
しかし、私は実務での拡張性を考え「Ollama + Open WebUI」の組み合わせ一択だと考えています。
理由は、Open WebUIが「本家ChatGPTに最も近い操作感」を持っており、かつRAG（ドキュメント参照回答）の機能が標準で強力だからです。

また、Ollamaはバックグラウンドで「モデルサーバー」として動作するため、一度起動すれば他の自作スクリプトからもAPI経由で呼び出せます。
UIと推論エンジンを分離して管理することで、将来的にUIだけをアップデートしたり、モデルだけを最新のLlama 4（仮）に入れ替えたりすることが容易になります。
この「疎結合」な構成こそが、プロの現場で耐えうるシステム設計の基本です。

## Step 1: Ollamaのインストールとモデルの準備

まずは心臓部となる「Ollama」を導入します。これはLLMを動かすための軽量な実行環境です。

1. [Ollama公式サイト](https://ollama.com/)からインストーラーをダウンロードして実行します。
2. インストール完了後、ターミナル（Mac）またはコマンドプロンプト（Windows）を開きます。
3. 以下のコマンドを入力して、Metaの最新モデル「Llama 3.1 8B」をダウンロードします。

```bash
# モデルのダウンロードと起動
ollama run llama3.1
```

このコマンドを実行すると、約4.7GBのモデルデータがダウンロードされます。
完了後、ターミナル上で直接会話ができるようになりますが、日本語が少し怪しい場合があります。
ここでは動作確認だけ行い、`/bye` と入力して一旦終了してください。

⚠️ **落とし穴:**
Windowsの場合、インストール直後は環境変数が反映されず「ollama command not found」と出ることがあります。
その場合は一度コマンドプロンプトを閉じて再起動してください。
また、VRAMが不足しているとCPU推論に切り替わり、PCのファンが爆音で回り始めるので注意が必要です。

## Step 2: Open WebUIをDockerで起動する

次に、ブラウザから操作するためのGUIである「Open WebUI」を構築します。
Pythonの仮想環境で直接動かす方法もありますが、依存関係の地獄（ライブラリの衝突）を避けるため、Dockerを使うのが正解です。

まず、[Docker Desktop](https://www.docker.com/products/docker-desktop/)をインストールして起動しておいてください。
次に、適当な作業用フォルダを作成し、その中に `docker-compose.yml` という名前で以下の内容を保存します。

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: always
    ports:
      - "3000:8080"
    volumes:
      - open-webui-data:/app/data
    environment:
      - 'OLLAMA_BASE_URL=http://host.docker.internal:11434'
    extra_hosts:
      - "host.docker.internal:host-gateway"

volumes:
  open-webui-data:
```

### なぜこの設定にするのか
`OLLAMA_BASE_URL` に `host.docker.internal` を指定しているのが最大のポイントです。
Dockerコンテナの中から見ると、PC本体で動いているOllamaは「外部サーバー」に見えます。
この設定を入れることで、コンテナ内からPC本体（ホスト）の11434ポートで待機しているOllamaを認識できるようになります。

設定ができたら、ターミナルでそのフォルダに移動し、以下のコマンドを叩きます。

```bash
docker-compose up -d
```

これで、バックグラウンドでチャット画面のサーバーが立ち上がりました。

## Step 3: 動かしてみる

ブラウザを開き、 `http://localhost:3000` にアクセスしてください。
最初の画面でアカウント登録を求められますが、これは**自分のPC内に保存されるだけのローカルアカウント**です。
メールアドレスなどは適当なもので構いません。

1. ログイン後、左上の「モデルを選択」から `llama3.1:latest` を選びます。
2. 下部のチャット欄に「こんにちは、自己紹介してください」と入力します。

### 期待される出力
```text
こんにちは！私はLlama 3.1、Metaによってトレーニングされた大規模言語モデルです。
あなたのPC上で直接動作しており、プライバシーを守りながらお手伝いできます。
```

もしモデルが出てこない場合は、右上の設定（歯車アイコン）→「設定」→「接続」から、OllamaのURLが正しく設定されているか、通信が通っているかを確認してください。

## Step 4: 実用レベルにする（日本語特化とRAG）

標準のLlama 3.1は英語ベースのため、たまに英語で回答が返ってくることがあります。
これを解決するために、Open WebUIの「Modelfile」機能を使って、日本語専用の「システムプロンプト」を固定した自分専用モデルを作ります。

1. Open WebUIの左メニューから「ワークスペース」→「モデル」→「モデルを作成」をクリック。
2. 名前を「Llama-3.1-JP」などに設定。
3. 「ベースモデル」に `llama3.1:latest` を選択。
4. 「Modelfile」の欄に以下を追記します。

```text
SYSTEM "あなたは優秀な日本人のアシスタントです。回答は必ず日本語で行ってください。
専門的な用語も分かりやすく解説し、常に論理的で丁寧な口調を心がけてください。"
PARAMETER temperature 0.7
```

「作成」を押すと、新しいモデルがリストに加わります。これだけで日本語の安定感が激変します。

さらに実務で使うなら、チャット欄の「＋」ボタン、あるいはファイルのドラッグ＆ドロップを試してください。
PDFファイルを読み込ませると、Open WebUIが内部で自動的にベクトル化（RAG）を行い、「この資料に基づいて、第3章の要点をまとめて」といった指示が出せるようになります。
この処理もすべてローカルで行われるため、社外秘の企画書をChatGPTにアップロードしてヒヤヒヤする必要はもうありません。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error (11434) | Ollamaが起動していない | タスクバーにOllamaのアイコンがあるか確認 |
| 回答が極端に遅い | GPUが使われていない | Docker DesktopのGpuSupport設定を確認、またはVRAM不足 |
| 404 Not Found | モデル名が間違っている | `ollama list` で正しい名前を確認して入力 |

## 次のステップ

無事に環境が動いたら、次は「モデルの使い分け」に挑戦してください。
論理的思考が必要なときは Llama 3.1 8B、より軽量に動かしたいときは Google の Gemma 2 2B など、用途に合わせて `ollama pull` でモデルを増やすことができます。

また、RTX 3090/4090 などの大容量VRAMを積んでいるなら、Llama 3.1 70B（約40GB）の「クオンタイズ（軽量化）版」を動かしてみるのも面白いでしょう。
ここまで来れば、APIの従量課金に怯える日々から解放され、ローカルLLMを「自分だけの思考拡張ツール」として24時間フル活用できるようになります。
次は、CursorなどのAIエディタとこのOllamaを連携させて、ローカル完結のコーディング環境を構築するのもおすすめです。

## よくある質問

### Q1: 社内の別PCからもこのチャット画面を使えますか？

可能です。Ollamaの環境変数 `OLLAMA_HOST` を `0.0.0.0` に設定し、Dockerの `OLLAMA_BASE_URL` にホストPCのローカルIPを指定すれば、同じLAN内の他のPCのブラウザからアクセスできます。

### Q2: GPUがないノートPCでも動きますか？

動きますが、非常に低速です。CPUだけで動かす場合は、モデル名の後ろに `:mincp` などが付いた軽量なものを選ぶか、2B（20億パラメータ）以下の非常に小さなモデルを選択することをお勧めします。

### Q3: データのプライバシーは本当に大丈夫ですか？

はい。今回構築した構成では、モデルのダウンロード時以外にインターネット通信は発生しません。入力したテキストやアップロードした書類が外部のサーバーに送信されることは物理的にありません。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-06-16-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPT環境を作る方法](/posts/2026-05-31-ollama-openwebui-local-llm-setup-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPTを構築する方法](/posts/2026-06-22-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "社内の別PCからもこのチャット画面を使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Ollamaの環境変数 OLLAMAHOST を 0.0.0.0 に設定し、Dockerの OLLAMABASEURL にホストPCのローカルIPを指定すれば、同じLAN内の他のPCのブラウザからアクセスできます。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUがないノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、非常に低速です。CPUだけで動かす場合は、モデル名の後ろに :mincp などが付いた軽量なものを選ぶか、2B（20億パラメータ）以下の非常に小さなモデルを選択することをお勧めします。"
      }
    },
    {
      "@type": "Question",
      "name": "データのプライバシーは本当に大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。今回構築した構成では、モデルのダウンロード時以外にインターネット通信は発生しません。入力したテキストやアップロードした書類が外部のサーバーに送信されることは物理的にありません。 ---"
      }
    }
  ]
}
</script>
