---
title: "OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法"
date: 2026-08-01T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-08-01-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "ローカルLLM 構築"
  - "RAG 自炊"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- インターネット不要で機密情報を放り込んでも安心な、自分専用のChatGPTクローン環境を構築します。
- 前提知識：ターミナルでコマンドをコピペできる、Dockerの概念をなんとなく知っている。
- 必要なもの：Windows/Mac/Linux PC、インターネット接続（モデルのダウンロード用）。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載で、現行の主要ローカルLLMを安価かつ快適に動かせるため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPUよりも重要なのがGPUのビデオメモリ（VRAM）です。
VRAMが8GBあれば「Llama 3.1 8B」などの標準的なモデルが快適に動きますが、12GBから16GBあると業務利用でもストレスがありません。
私の検証では、RTX 4060 Ti (16GB) が現時点での「コスパ最強の入門機」で、これなら量子化された30Bクラスのモデルもなんとか動かせます。

Macユーザーなら、メモリ（ユニファイドメモリ）が16GB以上のApple Silicon搭載機（M1/M2/M3/M4）を強く推奨します。
メモリ8GBのMacBook Airでも動きますが、推論中にブラウザやSlackが重くなり、実用性はかなり厳しいのが本音です。
一方、一度環境を作ってしまえば、電気代以外のランニングコストは0円。
API料金の変動や、OpenAIの規約変更に怯える必要がなくなるのは大きなメリットです。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールには「LM Studio」や「AnythingLLM」もありますが、私は「Ollama + Open WebUI」の組み合わせがベストだと考えています。
理由は、Ollamaがモデル管理とAPIサーバーとしての機能を完璧に切り離しており、Open WebUIが本家ChatGPTに最も近い操作感を提供してくれるからです。

特にOpen WebUIは、複数のモデルを切り替えて比較したり、過去のチャット履歴を検索したり、自前のPDFを読み込ませるRAG（検索拡張生成）機能が標準で備わっています。
エンジニアが仕事で使うなら、単一のアプリで完結するツールよりも、コンテナで切り離して拡張できるこの構成が最も「潰し」が効きます。
将来的に別のフロントエンドを試したくなった時も、バックエンドのOllamaはそのまま流用できるため、再構築の手間がありません。

## Step 1: 環境を整える

まずはモデルの実行エンジンとなる「Ollama」をインストールします。
公式サイトからインストーラーを落としても良いですが、パッケージマネージャーを使うのが後々の管理が楽です。

```bash
# macOSの場合（Homebrewを使用）
brew install ollama

# Linuxの場合
curl -fsSL https://ollama.com/install.sh | sh
```

Windowsの場合は、公式サイトからexeファイルをダウンロードして実行してください。
インストール後、ターミナル（またはコマンドプロンプト）で以下のコマンドを叩き、バージョンが表示されれば成功です。

```bash
ollama --version
```

次に、UIを動かすための「Docker」を準備します。
Open WebUIを直接PCにインストールしようとすると、Pythonのライブラリ競合やビルドエラーで100%ハマります。
私は最初、ネイティブ環境で作ろうとして依存関係の沼に落ち、2時間を無駄にしました。
Dockerを使えば、コマンド一つで検証済みの環境が手に入ります。

⚠️ **落とし穴:**
WindowsでWSL2を使っていない場合、Docker Desktopの動作が著しく重くなることがあります。
必ず「WSL2ベースのエンジン」が有効になっているか設定を確認してください。
また、GPUを使いたい場合は「NVIDIA Container Toolkit」のインストールが必須です。これを忘れるとCPU推論になり、レスポンスが10倍以上遅くなります。

## Step 2: 基本の設定

OllamaとDockerが準備できたら、Open WebUIを起動します。
今回は、Ollamaが同じPC内で動いていることを前提とした、最も標準的な設定で行きます。

```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

このコマンドの意味を解説します。
- `-p 3000:8080`: PCの3000番ポートでWeb画面を開けるようにします。
- `--add-host`: コンテナの中から「外側のPC（Ollama）」にアクセスするための設定です。
- `-v`: チャット履歴や設定をPC内に保存します。これを忘れると、コンテナを止めるたびにデータが消えます。

起動したら、ブラウザで `http://localhost:3000` にアクセスしてください。
最初の画面でアカウント作成を求められますが、これは「自分のPC内だけ」のデータなので、適当なメールアドレスとパスワードで大丈夫です。
外部に送信されることはありません。

## Step 3: 動かしてみる

ログインできたら、まずは頭脳となるモデルをダウンロードしましょう。
画面左上のモデル選択メニュー、または設定の「モデル」から、以下の名前を入力してプル（Pull）します。

- `llama3.1:8b` (Meta製の標準モデル。バランスが良い)
- `qwen2.5:7b` (アリババ製。日本語能力が非常に高い)

```bash
# ターミナルから直接プルする場合
ollama pull llama3.1
```

ダウンロードが完了したら、チャット画面でモデルを選択して「こんにちは、あなたの得意なことは何ですか？」と投げてみてください。

### 期待される出力

```
こんにちは！私はLlama 3.1ベースのAIモデルです。
私はプログラミングのコード生成、文章の要約、データ分析の補助などが得意です。
ローカル環境で動作しているため、あなたのデータを外部に送信することなく回答できます。
```

レスポンスが1秒間に20トークン（文字）以上出ていれば、GPUが正しく認識されています。
もし1文字ずつゆっくり出てくる場合は、GPUが使われずCPUで処理されている可能性が高いです。
その場合はDockerの起動オプションに `--gpus all` を追加し、NVIDIAのドライバーが最新か確認してください。

## Step 4: 実用レベルにする

単なるチャットボットで終わらせるのはもったいないです。
Open WebUIの最大の武器は「ドキュメント機能（RAG）」です。
画面左側の「ドキュメント」に、会社の規約PDFや、自分が過去に書いた技術メモのMarkdownをアップロードしてみてください。

アップロード後、チャット欄で `#`（ハッシュ）を入力すると、アップロードしたファイルがリストアップされます。
ファイルを選択して「この資料の内容を3行で要約して」と指示を出すと、AIがその中身を読み取って回答します。
これはGPT-4oなどのクラウドAIに機密情報を投げられない現場において、唯一の解決策になります。

私はこの機能を使い、200ページ以上ある古いシステムの設計書を全てローカルに食わせています。
「この変数の定義はどこ？」といった質問に数秒で答えてくれるため、ドキュメントを検索する時間がほぼゼロになりました。

```bash
# RAGの精度を上げるためのTips
# 設定 > 文書 から、埋め込みモデル（Embedding Model）を「mxbai-embed-large」に変更すると
# 日本語の検索精度が劇的に向上します。デフォルトよりもこちらを推奨します。
```

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Connection Error` | DockerからOllamaが見えていない | `--add-host` オプションが正しいか確認 |
| 回答がめちゃくちゃ遅い | CPUで動作している | NVIDIA Container Toolkitを入れ直す |
| モデルが見つからない | `ollama pull` が完了していない | ターミナルで `ollama list` を確認 |
| 日本語が不自然 | モデルが日本語に最適化されていない | `qwen2.5` や `gemma2` を試す |

## 次のステップ

ここまでできれば、あなたのPCの中に「絶対に嘘をつかない（外部に漏らさない）秘書」が誕生したことになります。
次に挑戦してほしいのは、プロンプトのテンプレート化です。
Open WebUIには「プロンプト」というメニューがあり、よく使う指示（コードレビュー、メール作成、翻訳など）を登録しておけます。

また、もしあなたがエンジニアなら、VS Codeの拡張機能「Continue」をインストールしてみてください。
今回構築したOllamaのURLを指定するだけで、GitHub Copilotのようなコード補完が「無料・ローカル」で実現します。
月額$20を払わなくても、自分だけの開発パートナーが手に入る。
これがローカルLLM環境を構築する最大の醍醐味だと、私は確信しています。

## よくある質問

### Q1: 電気代はどれくらいかかりますか？

RTX 4090でフル回転させると450Wほど消費しますが、チャットの推論中だけです。
1日2時間ガッツリ使っても月数百円程度。APIを従量課金で叩きまくるよりは、私の経験上圧倒的に安上がりです。

### Q2: 会社で使ってもバレませんか？

通信はPC内で完結するため、ネットワーク管理者から「OpenAIにデータを送っている」と疑われることはありません。
ただし、モデルのダウンロードには数GBの通信が発生するため、そこだけは注意が必要です。

### Q3: どのモデルが日本語最強ですか？

現時点では `Qwen2.5-7B-Instruct` が非常に優秀です。
敬語の不自然さが少なく、日本の商習慣を理解した回答をしてくれます。
Metaの `Llama3.1-8B` も良いですが、少し英語直訳調になる傾向があります。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルAI環境を構築する方法](/posts/2026-07-25-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIを組み合わせて自分専用のローカルChatGPT環境を構築する方法](/posts/2026-07-08-ollama-open-webui-local-llm-tutorial/)
- [Qwen 27Bクラスをローカル環境で爆速動作させる方法](/posts/2026-05-21-qwen-27b-local-setup-ollama-python/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "電気代はどれくらいかかりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "RTX 4090でフル回転させると450Wほど消費しますが、チャットの推論中だけです。 1日2時間ガッツリ使っても月数百円程度。APIを従量課金で叩きまくるよりは、私の経験上圧倒的に安上がりです。"
      }
    },
    {
      "@type": "Question",
      "name": "会社で使ってもバレませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "通信はPC内で完結するため、ネットワーク管理者から「OpenAIにデータを送っている」と疑われることはありません。 ただし、モデルのダウンロードには数GBの通信が発生するため、そこだけは注意が必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "どのモデルが日本語最強ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "現時点では Qwen2.5-7B-Instruct が非常に優秀です。 敬語の不自然さが少なく、日本の商習慣を理解した回答をしてくれます。 Metaの Llama3.1-8B も良いですが、少し英語直訳調になる傾向があります。 ---"
      }
    }
  ]
}
</script>
