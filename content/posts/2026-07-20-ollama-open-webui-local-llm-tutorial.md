---
title: "OllamaとOpen WebUIを連携させ、完全にオフラインで動作する「プライベートChatGPT環境」を構築します。"
date: 2026-07-20T00:00:00+09:00
slug: "ollama-open-webui-local-llm-tutorial"
cover:
  image: "/images/posts/2026-07-20-ollama-open-webui-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama"
  - "Open WebUI"
  - "ローカルLLM 構築"
  - "RAG 入門"
---
この記事を読み終える頃には、社外秘の資料を読み込ませても情報漏洩の心配がない、あなた専用の高機能なAIアシスタントが手元のPCで動いているはずです。

**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- Webブラウザから操作でき、PDF等のドキュメント解析（RAG）も可能なローカルLLM環境
- LLM実行エンジンとして「Ollama」、UIとして「Open WebUI」を組み合わせたスタック
- 前提知識：ターミナル（コマンドプロンプト）でのコピペ操作、Dockerの基本的な概念

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3 8Bを余裕を持って動かせる、最も安価な選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
メインメモリ（RAM）が32GBあっても、GPUのメモリが足りないと推論速度は極端に落ち、実用レベル（レスポンス1秒以内）での動作は望めません。

Windows/Linux環境なら、最低でも「VRAM 8GB」を搭載したNVIDIA製GPU（RTX 3060以上）を推奨します。
Llama 3 (8B) クラスのモデルを快適に動かすには12GB以上、将来的に大規模なモデル（30B以上）を視野に入れるなら24GBのRTX 3090/4090が理想的です。

Macの場合、Apple Silicon（M1/M2/M3）の「ユニファイドメモリ」がVRAMを兼ねるため非常に有利です。
ただし、OSがメモリの一部を占有するため、最低16GB、できれば24GB以上のメモリを積んだモデルを選んでください。

費用については、ハードウェアさえあれば月額料金は「$0」です。
API通信が発生しないため、どれだけ長文を投げても、どれだけドキュメントを読み込ませても追加費用はかかりません。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は、他にも「LM Studio」や「GPT4All」などがあります。
しかし、私が実務での利用に「Ollama + Open WebUI」を推す理由は、その拡張性と「ChatGPTに近いUI体験」にあります。

LM Studioは単体で完結していて使いやすい反面、複数のモデルを並行して動かしたり、複数のユーザーで共有したりするのには向きません。
一方、Ollamaは軽量なAPIサーバーとして動作し、Open WebUIはDocker上で動くWebアプリケーションです。

この構成なら、1台のサーバー（または強力なPC）でAIを動かし、家族やチームが各々のブラウザからアクセスする環境が簡単に作れます。
また、Open WebUIはRAG（外部ドキュメント参照）の機能が標準で組み込まれており、PDFをアップロードするだけで即座に専門知識を持ったAIを作れる点も、実務においては大きなアドバンテージです。

## Step 1: 環境を整える

まずはLLMの実行エンジンである「Ollama」をインストールします。
Ollamaは、複雑な量子化済みモデル（GGUF等）の管理や実行を、コマンド一つで完結させてくれるツールです。

公式サイト（ollama.com）からインストーラーをダウンロードし、実行してください。
インストール完了後、ターミナルで以下のコマンドを叩き、エンジンが正常に動いているか確認します。

```bash
# バージョンが表示されればインストール成功
ollama --version
```

次に、動作確認として軽量で高性能な「Llama 3.1 (8B)」をダウンロードし、起動してみます。

```bash
# Llama 3.1 8Bモデルのダウンロードと対話開始
ollama run llama3.1
```

コマンド実行後、プロンプトが表示されたら「Hello」と入力してみてください。
数秒で返信があれば、エンジンのセットアップは完了です。
`/bye` と入力して一度対話を終了します。

⚠️ **落とし穴:**
Windows環境でGPUが認識されない場合、NVIDIAの公式ドライバーが最新でないケースが多々あります。
また、Docker Desktopを使用している場合は、設定の「Resources」から「WSL 2」が有効になっていること、および「NVIDIA GPU Support」が有効であることを確認してください。

## Step 2: Open WebUIを起動する

次に、ブラウザから操作するための「Open WebUI」を導入します。
依存関係で環境を汚さないよう、Dockerを使って立ち上げるのが正解です。

以下のコマンドは、Ollamaが同じPC上で動いていることを前提とした設定です。

```bash
# Dockerを使用してOpen WebUIを起動
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

各設定の理由は以下の通りです。
- `-p 3000:8080`: ブラウザから `http://localhost:3000` でアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: Dockerコンテナの中から、ホストPCで動いているOllamaに通信を通すための重要な設定です。
- `-v open-webui:/app/backend/data`: チャット履歴やアップロードしたファイルを保存する場所を固定し、コンテナを消してもデータが消えないようにします。

## Step 3: 動かしてみる

ブラウザを開き、`http://localhost:3000` にアクセスしてください。
最初にアカウント作成画面が出ますが、これは完全にローカル（あなたのPC内）に保存されるものなので、適当なメールアドレスとパスワードで登録してログインします。

ログイン後、左上の「モデルを選択」から、先ほどダウンロードした `llama3.1:latest` を選択します。

### 期待される出力

チャット欄に「あなたは誰ですか？」と入力し、以下のような応答があれば成功です。

```
私はLlama 3.1として知られる大型言語モデルです。Metaによってトレーニングされました。
何かお手伝いできることはありますか？
```

もしモデル一覧に何も表示されない場合は、設定（左下の名前アイコン）→「設定」→「外部接続」から、OllamaのURLが `http://host.docker.internal:11434` になっているか確認してください。

## Step 4: 実用レベルにする

単なるチャットボットで終わらせないために、実務で必須となる「RAG（ドキュメント解析）」機能を試します。

Open WebUIのチャット欄にある「＋」アイコン、あるいは「#」を打つことで、ローカルのファイルをアップロードできます。
例えば、製品のマニュアル（PDF）やソースコードの束をアップロードしてみてください。

アップロード後、以下のように問いかけます。

```
# [ファイル名]
このドキュメントの要点を3つにまとめて、日本語で教えてください。
```

私の場合、業務で使う複雑なAPI仕様書（100ページ超）を読み込ませていますが、必要なパラメータを抜き出す作業が30分から10秒に短縮されました。
Open WebUI側で自動的にベクトル化（情報のインデックス作成）が行われるため、ユーザーは「なぜ動くのか」を意識せずに高度な検索エンジン付きAIを使えるようになります。

さらに、プロンプトを固定したい場合は「モデル」メニューから「新しいモデルを作成」を選びます。
「System Prompt」に「あなたはシニアエンジニアです。常にTypeScriptのベストプラクティスに基づいて回答してください」と記述しておけば、特定の役割に特化したAIを量産できます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| モデル一覧に何も出ない | DockerからOllamaへの通信拒否 | `OLLAMA_ORIGINS="*"` を環境変数に設定してOllamaを再起動 |
| 回答速度が異様に遅い | GPUではなくCPUで動作している | NVIDIA Container Toolkitが未導入か、VRAM不足 |
| 接続が拒否されました | Ollamaが起動していない | タスクバーにOllamaのアイコンがあるか確認 |

## 次のステップ

ここまでで、自分だけのクローズドなAI環境が手に入りました。
次に挑戦すべきは「モデルの使い分け」です。

- 文章作成や要約なら：`Llama 3.1 (8B)`
- コーディング補助なら：`DeepSeek-Coder-V2`
- 圧倒的な賢さを求めるなら（VRAM 24GB以上必須）：`Llama 3.1 (70B)`

Ollamaなら `ollama run [モデル名]` で新しいモデルを即座に試せます。
また、Open WebUIの「Tools」機能を使えば、AIにPythonスクリプトを実行させたり、Web検索をさせたりすることも可能です。

ローカルLLMは、もはや「お遊び」の段階を過ぎ、実務で「機密情報を扱える唯一のAI」としての地位を確立しています。
まずは手元のドキュメントを1つ読み込ませることから、その真価を体感してください。

## よくある質問

### Q1: ネット接続は完全に切っても動きますか？

はい、一度モデルのダウンロードが完了すれば、LANケーブルを抜いてもWi-Fiを切っても動作します。これこそがローカルLLMを導入する最大のメリットであり、セキュリティ上の安心感に繋がります。

### Q2: 4GBのVRAMしかありませんが、動かす方法はありますか？

あります。モデルのサイズを「1B」や「3B」などの軽量なもの（Gemma 2 2Bなど）に落とせば、4GBでも高速に動作します。ただし、推論の精度（賢さ）はLlama 3.1 8Bに比べると目に見えて落ちる点は覚悟してください。

### Q3: 複数のPCからアクセスするにはどうすればいいですか？

Dockerを起動しているPCのローカルIPアドレス（例: 192.168.1.5）を調べ、他のPCのブラウザから `http://192.168.1.5:3000` にアクセスすればOKです。社内LANなど、閉じられたネットワーク内での共有に最適です。

---

## あわせて読みたい

- [Qwen2.5-Coder 使い方 | ローカルでGPT-4o級の開発環境をPythonで構築する](/posts/2026-03-21-qwen2-5-coder-python-local-guide/)
- [Qwen3.6-27BとOllamaで高精度なローカル検索AIを作る方法](/posts/2026-05-03-qwen36-ollama-local-agentic-search-guide/)
- [Qwen2.5-Coder 使い方 | ローカルでコード生成AIを動かす](/posts/2026-05-19-qwen-coder-local-setup-python-refactor/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "ネット接続は完全に切っても動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、一度モデルのダウンロードが完了すれば、LANケーブルを抜いてもWi-Fiを切っても動作します。これこそがローカルLLMを導入する最大のメリットであり、セキュリティ上の安心感に繋がります。"
      }
    },
    {
      "@type": "Question",
      "name": "4GBのVRAMしかありませんが、動かす方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "あります。モデルのサイズを「1B」や「3B」などの軽量なもの（Gemma 2 2Bなど）に落とせば、4GBでも高速に動作します。ただし、推論の精度（賢さ）はLlama 3.1 8Bに比べると目に見えて落ちる点は覚悟してください。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のPCからアクセスするにはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Dockerを起動しているPCのローカルIPアドレス（例: 192.168.1.5）を調べ、他のPCのブラウザから http://192.168.1.5:3000 にアクセスすればOKです。社内LANなど、閉じられたネットワーク内での共有に最適です。 ---"
      }
    }
  ]
}
</script>
