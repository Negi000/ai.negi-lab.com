---
title: "OllamaとOpen WebUIで自分専用のプライベートChatGPTを構築する方法"
date: 2026-07-20T00:00:00+09:00
slug: "ollama-openwebui-local-llm-guide"
cover:
  image: "/images/posts/2026-07-20-ollama-openwebui-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 構築"
  - "ローカルLLM 日本語"
  - "自宅AIサーバー"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIを一切使わず、自分のPC内で完結するWeb UI付きの生成AI環境
- ChatGPTに近い操作感で、Llama 3やGemma 2などの最新モデルと会話できるシステム
- 前提知識：ターミナル（コマンドプロンプト）でコマンドをコピペできること。Dockerの概念をなんとなく知っていること

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MSI GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBを搭載し、ローカルLLMの中規模モデルを安価に動かすための最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、妥協できないのがハードウェアスペックです。

結論から言うと、WindowsならNVIDIA製GPU（VRAM 8GB以上）が必須、MacならApple Silicon（M1以降、メモリ16GB以上）が最低ラインです。VRAM 8GBあれば、現時点で最も汎用性の高い「Llama 3.1 8B」クラスをサクサク動かせますが、VRAM 4GB以下だと推論がCPUに回り、1秒間に1文字出るかどうかという絶望的な速度になります。

また、WSL2（Windows Subsystem for Linux）のセットアップで躓く人が多いですが、最新のOllamaはWindowsネイティブで動作するため、以前よりハードルは下がっています。

料金については、電気代以外は完全に0円です。Open WebUIは無料のオープンソースですし、モデルもHugging Face等から自由にダウンロードできます。APIの従量課金を気にせず、100万トークンでも200万トークンでも、納得いくまでプロンプトを試行錯誤できるのが最大のメリットです。

## なぜこの方法を選ぶのか

ローカルでAIを動かす手段は、LM StudioやJanなど他にもありますが、私は「Ollama + Open WebUI」の組み合わせを推奨します。

理由は、拡張性と「本物感」です。LM Studioは手軽ですが、RAG（ドキュメント読み込み）やマルチユーザー管理、API連携の柔軟性においてOpen WebUIに及びません。Open WebUIはその名の通り、ChatGPTのインターフェースを極めて忠実に再現しており、仕事でChatGPTを使い慣れているチームに導入しても違和感なく受け入れられます。

また、Ollamaはバックエンドとして非常に優秀です。モデルの重みを勝手に最適化し、GPUのVRAMに載るだけ載せ、残りをメインメモリに逃がす処理を自動で行ってくれます。この「何も考えなくていい」という体験は、実務でAIを回すエンジニアにとって非常に重要です。

## Step 1: 環境を整える

まずはモデルの実行エンジンである「Ollama」をインストールします。

### Windows / Mac の場合
公式サイト（https://ollama.com/）からインストーラーをダウンロードして実行するだけです。

### Linux の場合
以下のコマンドを実行します。

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

インストールが完了したら、正しく動作するか確認するためにターミナルで以下のコマンドを叩いてください。

```bash
ollama --version
```

バージョンが表示されれば成功です。次に、軽量で日本語もそこそこ扱える「Llama 3.2 (3B)」をダウンロードして動かしてみます。

```bash
ollama run llama3.2
```

これだけでモデルのダウンロードと起動が始まります。終了するには `/bye` と入力してください。

⚠️ **落とし穴:** Windowsユーザーで、なぜかGPUが認識されない場合は、グラフィックドライバが最新か確認してください。古いドライバだと、OllamaがCUDAを検知できずCPU推論にフォールバックします。

## Step 2: 基本の設定（Dockerの導入）

次に、GUI部分となる「Open WebUI」を導入します。これを直接インストールするのは環境を汚す原因になるため、Dockerを使うのが「ねぎ流」の鉄則です。

Docker Desktopがインストールされていない場合は、公式サイトからインストールしておいてください。

準備ができたら、以下のコマンドをターミナルに貼り付けます。

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

### なぜこの設定にするのか
- `-p 3000:8080`: PC側のポート3000番でアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: Dockerコンテナの中から、PC側で動いているOllamaを見つけるために必須の設定です。
- `-v open-webui:/app/backend/data`: チャット履歴や設定を保存する領域（ボリューム）を作成します。これがないと、コンテナを止めるたびに履歴が消えます。

⚠️ **落とし穴:** もしすでにポート3000を他の開発で使っているなら、`3001:8080` のように左側の数字を変えてください。

## Step 3: 動かしてみる

ブラウザを開き、`http://localhost:3000` にアクセスしてください。

最初のログイン画面では、適当な名前、メールアドレス、パスワードを登録します。これはローカルのデータベースに保存されるだけなので、本物のメールアドレスである必要はありません。最初に登録したアカウントが管理者権限を持ちます。

ログイン後、画面上部の「モデルを選択」から、先ほどダウンロードした `llama3.2:latest` を選びます。

### 期待される出力

チャット欄に「こんにちは、自己紹介してください」と入力して、以下のような返答が来れば成功です。

```text
こんにちは！私はLlama 3.2、Metaによってトレーニングされた大規模言語モデルです。
あなたのPC上で直接動作しています。何かお手伝いできることはありますか？
```

私の環境（RTX 4090）では、このクラスのモデルは瞬時に回答が終わります。ノートPC（M2 MacBook Air / 16GB）でも、ストレスなく会話できる速度が出るはずです。

## Step 4: 実用レベルにする

単にチャットするだけならChatGPTで十分です。ローカル環境を「仕事で使える」レベルに引き上げるための設定を行います。

### 1. 日本語特化モデルの導入
Llama 3.2は優秀ですが、日本語の自然さでは国産モデルに劣る場合があります。実務で使うなら、以下のコマンドで日本語に強いモデルを追加しましょう。

```bash
# ELYZA (Llama 3ベースの日本語強化版)
ollama run elyza:8b
```

Open WebUIの画面をリロードすれば、モデル選択肢にELYZAが現れます。

### 2. RAG（ドキュメント検索）を試す
Open WebUIの真骨頂は、PDFやテキストファイルをアップロードして、その内容について質問できる機能です。

チャット欄の左側にある「＋」ボタン、あるいは「#」を入力してからファイルをアップロードしてください。
私はよく、会社の複雑な就業規則や、数千行あるライブラリのドキュメントを放り込んでいます。外部APIを使わないので、機密情報をアップロードしても情報漏洩のリスクがゼロなのが最大の強みです。

### 3. Web検索の有効化（オプション）
設定から「Web Search」を有効にし、SearXNGなどの検索エンジンと連携させると、ローカルLLMでありながら最新のニュースを取り込んだ回答が可能になります。ただし、これは少し構築難易度が上がるため、まずは手元のファイルを読み込ませるRAGから使い倒すのが近道です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error (Ollama) | Open WebUIからOllamaが見えていない | Docker起動時の `--add-host` 設定を確認 |
| 動作が異常に重い | GPUではなくCPUで動いている | Ollamaのログを確認し、VRAM不足がないかチェック |
| ログインできない | Dockerボリュームの不具合 | `docker volume rm open-webui` で初期化（履歴は消える） |

## 次のステップ

ここまでで、自分だけのクローズドなAI環境が手に入りました。次にやるべきは「自分専用のシステムプロンプトの固定」です。

Open WebUIの「ワークスペース」機能から「モデル」を作成し、ベースモデル（Llama 3.1など）に対して「あなたは優秀なPythonエンジニアです。常に型ヒントを付け、疎結合なコードを書いてください」といった指示を固定してください。

これにより、毎回指示を書かなくても、特定の業務に特化したAIを量産できます。私は「コードレビュー用」「記事構成案作成用」「英文メール添削用」と5つ以上の専用モデルを使い分けています。

また、RTX 3060 12GBなど、VRAMが多い安価なGPUを1枚買い足すだけで、より巨大なモデル（Command RやLlama 3.1 70Bの量子化版）も動かせるようになります。ローカルLLMの世界は、ハードウェアへの投資がダイレクトに知能の向上に繋がるので、非常に面白い領域ですよ。

## よくある質問

### Q1: 会社の共有PCに構築しても大丈夫ですか？

技術的には可能ですが、DockerとOllamaの実行権限が必要です。また、ローカルで完結するとはいえ、モデルのダウンロード（数GB単位）が発生するため、ネットワーク管理者に確認することをお勧めします。セキュリティ面では、外部へデータが飛ばないため、むしろChatGPTより安全と言えます。

### Q2: スマホからもこのUIを使いたいのですが。

同じWi-Fi内であれば、PCのローカルIPアドレス（例: 192.168.1.10:3000）をスマホのブラウザに入力すればアクセス可能です。ただし、Open WebUIの認証設定をしっかり行い、不用意に外部公開（ポート開放）しないよう注意してください。

### Q3: おすすめのモデルはどれですか？

汎用性なら `llama3.1:8b`、日本語の精度重視なら `elyza:8b`、軽量さ重視なら `gemma2:2b` か `llama3.2:3b` です。私のブログでも定期的にベンチマークを公開しているので、そちらを参考に選んでみてください。

---

## あわせて読みたい

- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-07-05-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIの使い方！完全プライベートなローカルLLM環境を構築する方法](/posts/2026-07-07-ollama-openwebui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPT環境を作る方法](/posts/2026-05-31-ollama-openwebui-local-llm-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "会社の共有PCに構築しても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "技術的には可能ですが、DockerとOllamaの実行権限が必要です。また、ローカルで完結するとはいえ、モデルのダウンロード（数GB単位）が発生するため、ネットワーク管理者に確認することをお勧めします。セキュリティ面では、外部へデータが飛ばないため、むしろChatGPTより安全と言えます。"
      }
    },
    {
      "@type": "Question",
      "name": "スマホからもこのUIを使いたいのですが。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "同じWi-Fi内であれば、PCのローカルIPアドレス（例: 192.168.1.10:3000）をスマホのブラウザに入力すればアクセス可能です。ただし、Open WebUIの認証設定をしっかり行い、不用意に外部公開（ポート開放）しないよう注意してください。"
      }
    },
    {
      "@type": "Question",
      "name": "おすすめのモデルはどれですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "汎用性なら llama3.1:8b、日本語の精度重視なら elyza:8b、軽量さ重視なら gemma2:2b か llama3.2:3b です。私のブログでも定期的にベンチマークを公開しているので、そちらを参考に選んでみてください。 ---"
      }
    }
  ]
}
</script>
