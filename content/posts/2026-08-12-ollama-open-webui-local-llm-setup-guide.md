---
title: "OllamaとOpen WebUIで自分専用のChatGPTを構築する方法"
date: 2026-08-12T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-08-12-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "ローカルLLM 環境構築"
  - "RAG 自炊"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIを一切使わず、完全にローカル環境で動作する「RAG（書類読み込み）対応のAIチャットUI」を構築します。
- 必要なもの：Dockerが動作するPC（Windows/Mac/Linux）、インターネット環境、および相応のGPU。
- 前提知識：ターミナル（コマンドプロンプト）の基本的な操作、Dockerの基本概念。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に最も現実的。7B〜14Bモデルが余裕で動く</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU性能よりも圧倒的に重要なのが「GPUのVRAM（ビデオメモリ）」です。
7B（70億パラメータ）クラスのモデルを快適に動かすなら、最低でも8GB、できれば12GB以上のVRAMを推奨します。
私はRTX 4090の24GBを2枚使っていますが、一般的にはRTX 3060 12GBが最もコストパフォーマンス良く始められる選択肢です。

Macユーザーであれば、Apple Silicon（M1/M2/M3）搭載機が必須です。
MacはメインメモリをVRAMとして共有するため、最低でも16GB、仕事で使うなら32GB以上のメモリを積んだモデルを選んでください。
「とりあえず動く」と「実用的に使える」の間には、推論速度（トークン/秒）の大きな壁があります。

料金は、電気代以外は完全に無料です。
クラウドLLMのように1プロンプトごとに課金される恐怖から解放されるのが、ローカル環境最大のメリットと言えます。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールは「LM Studio」や「GPT4All」など他にもありますが、私は「Ollama + Open WebUI」の組み合わせが最強だと確信しています。
理由は、Ollamaが「モデル管理サーバー」として非常に優秀で、APIとして他のツールからも叩きやすいからです。
そして、そのフロントエンドであるOpen WebUIは、本家ChatGPTに肉薄する多機能さを備えています。

RAG（PDFなどのドキュメント読み込み）機能、マルチユーザー管理、Web検索連携、画像生成AI（Stable Diffusion等）との統合。
これらが一つのコンテナで完結する利便性は、他のツールでは得られません。
「とりあえず触ってみる」段階を超えて、実務のワークフローに組み込むなら、この構成一択です。

## Step 1: 環境を整える

まずはバックエンドとなるOllamaをインストールします。
公式サイトからインストーラーをダウンロードしても良いですが、今回は管理を容易にするため、MacならHomebrew、Windowsなら公式インストーラーを使います。

```bash
# Macの場合（Homebrewを使用）
brew install ollama

# インストール後、バックグラウンドで起動
brew services start ollama
```

Windowsの場合は、Ollama公式サイトから「Download for Windows」をクリックしてexeを実行してください。
タスクバーにOllamaのアイコンが出れば準備完了です。

⚠️ **落とし穴:**
WindowsでWSL2を使っている場合、OllamaをWindows側で入れるかWSL2側で入れるか迷う人が多いですが、現在は「Windows側」に入れるのが正解です。
Windows側で起動しておけば、WSL2側からも localhost:11434 経由で透過的にアクセスでき、GPUの認識もスムーズです。

## Step 2: Open WebUIを起動する

次に、ブラウザから操作するためのUI「Open WebUI」をDockerで立ち上げます。
なぜDockerを使うのか。それは、このアプリがPythonの依存関係が非常に多く、直接インストールすると環境が汚れ、高確率でエラーに遭遇するからです。

以下のコマンドをターミナルで実行してください。

```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

各設定の意味を解説します：
- `-p 3000:8080`: PCの3000番ポートでアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: Dockerコンテナの中から、外側のホスト（Ollama）を見つけるために必要です。
- `-v open-webui:/app/backend/data`: チャット履歴やアップロードしたPDFを保存する領域を永続化します。

⚠️ **落とし穴:**
Docker Desktopをインストールした直後だと、GPUがDocker側から見えていないことがあります。
特にNVIDIA製GPUを使っている場合は、`NVIDIA Container Toolkit`がインストールされているか確認してください。
これが無いと、せっかくのGPUパワーをUI側（RAGの埋め込み処理など）で活かせません。

## Step 3: 動かしてみる

ブラウザを開き `http://localhost:3000` にアクセスします。
最初のログイン画面でアカウント作成を求められますが、これは「自分のPC内に保存されるアカウント」なので、好きなメールアドレスとパスワードで登録してください。

ログインしたら、まずAIモデルをダウンロード（Pull）します。
1. 左下の設定アイコン（またはプロフィール名）から「Settings」→「Models」を開く。
2. 「Pull a model from Ollama.com」の欄に `llama3.1` と入力し、ダウンロードボタンを押す。

日本語での精度を重視するなら、東京大学の松尾研発スタートアップが公開しているモデルなどをベースにした `elyza:8b` もおすすめです。

### 期待される出力

ダウンロードが完了すると、トップ画面の上部にあるモデル選択メニューから `llama3.1` が選べるようになります。
適当に「こんにちは、あなたの得意なことは？」と投げてみてください。

```
私はMetaによってトレーニングされたAIモデル、Llama 3.1です。
テキストの生成、翻訳、要約、コードの作成など、幅広いタスクをお手伝いできます。
ローカル環境で動作しているため、プライバシーを守りながら対話が可能です。
```

このように返ってくれば成功です。

## Step 4: 実用レベルにする

「動いてよかった」で終わらせないのが私の主義です。
仕事で使うなら、特定のドキュメントに基づいた回答をさせる「RAG」機能を使いこなしましょう。

1. チャット入力欄の左側にある「＋」アイコン、あるいは「Documents」メニューからPDFファイルをアップロードします。
2. アップロードしたファイルに対して「#ファイル名」でメンションを送るか、設定でそのファイルをソースとして指定します。
3. 「この資料の3ページ目にある、プロジェクトの予算案を要約して」と指示を出します。

このとき、Open WebUIは内部でドキュメントを「ベクトル化」して検索可能な状態にします。
デフォルトではCPUで処理されますが、設定の「Documents」タブから「Embedding Model Engine」を `ollama` に変更し、モデルに `mxbai-embed-large` などを指定すると、埋め込み処理もGPUで高速化できます。

さらに、プロンプトを固定したい場合は「Modelfile」を作成します。
「Settings」→「Models」から既存のモデルをベースに新しいモデルを作成し、System Promptに「あなたは優秀なSIerのシニアエンジニアです。回答は常に簡潔なMarkdown形式で行い、コード例には必ず型定義を含めてください」と記述します。
これにより、自分専用の専門家AIを量産できます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error (11434) | Ollamaが起動していない | タスクバーでOllamaが動いているか確認。または `ollama serve` を実行。 |
| 回答が極端に遅い | GPUではなくCPUで推論している | VRAM容量を超えたモデルを使っている可能性あり。より小さい量子化モデル（4bit等）を試す。 |
| 日本語が不自然 | モデルの学習データ不足 | `elyza:8b` や `gemma2` など、日本語に強いモデルに変更する。 |

## 次のステップ

ここまでできれば、あなたのPCは「プライバシー完全保護のAI拠点」になりました。
次に挑戦すべきは、このOllamaを他のツールと連携させることです。

例えば、VS Codeの拡張機能である「Continue」や「Cline」を使えば、今構築したOllamaをバックエンドにして、ローカルLLMによるコーディング補完環境が作れます。
GitHub Copilotに月額$10払うのをやめて、自前のRTX 4090に仕事をさせる。これこそが自作サーバー派の醍醐味です。

また、DifyというLLMアプリ開発プラットフォームをDockerで立てて、Ollamaを接続してみてください。
複雑な業務フローをノーコードで自動化するエージェントが、完全にオフラインで動き出します。
その一歩として、まずは今日作った環境で、自分の過去の業務メモをPDF化してRAGで検索させてみることから始めてください。

## よくある質問

### Q1: スペック不足で動かない場合、どこを妥協すべきですか？

GPUを買い替えるのが一番ですが、予算がないなら「モデルの量子化（Quantization）」を意識してください。`llama3.1:8b-instruct-q4_K_M` のように、末尾にq4（4bit）とついたものを選べば、精度をそこまで落とさずメモリ消費を半分以下に抑えられます。

### Q2: 家族やチームメンバーとこの環境を共有できますか？

はい、Open WebUIはマルチユーザー対応です。PCのローカルIPアドレス（192.168.xx.xxなど）を共有すれば、同じWi-Fi内の他のスマホやPCからブラウザ経由で利用可能です。ただし、同時に重い推論を走らせるとVRAMの奪い合いになるので注意してください。

### Q3: モデルを消したいときはどうすればいいですか？

ターミナルで `ollama rm llama3.1` のようにコマンドを打つか、Open WebUIの設定画面からゴミ箱アイコンをクリックしてください。モデルファイルは数GB単位でストレージを圧迫するので、使わないものはこまめに消すのがコツです。

---

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法](/posts/2026-07-12-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法](/posts/2026-08-01-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIを組み合わせて自分専用のローカルChatGPT環境を構築する方法](/posts/2026-07-08-ollama-open-webui-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "スペック不足で動かない場合、どこを妥協すべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "GPUを買い替えるのが一番ですが、予算がないなら「モデルの量子化（Quantization）」を意識してください。llama3.1:8b-instruct-q4KM のように、末尾にq4（4bit）とついたものを選べば、精度をそこまで落とさずメモリ消費を半分以下に抑えられます。"
      }
    },
    {
      "@type": "Question",
      "name": "家族やチームメンバーとこの環境を共有できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、Open WebUIはマルチユーザー対応です。PCのローカルIPアドレス（192.168.xx.xxなど）を共有すれば、同じWi-Fi内の他のスマホやPCからブラウザ経由で利用可能です。ただし、同時に重い推論を走らせるとVRAMの奪い合いになるので注意してください。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルを消したいときはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ターミナルで ollama rm llama3.1 のようにコマンドを打つか、Open WebUIの設定画面からゴミ箱アイコンをクリックしてください。モデルファイルは数GB単位でストレージを圧迫するので、使わないものはこまめに消すのがコツです。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>
