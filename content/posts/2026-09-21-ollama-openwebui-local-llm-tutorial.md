---
title: "OllamaとOpen WebUIでChatGPT風のローカルLLM環境を作る方法"
date: 2026-09-21T00:00:00+09:00
slug: "ollama-openwebui-local-llm-tutorial"
cover:
  image: "/images/posts/2026-09-21-ollama-openwebui-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM RAG"
  - "Docker AI"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 自分のPC内で完結し、外部へデータが漏洩しない「自分専用のChatGPT」環境を構築します。
- 前提知識：Dockerの基本的なコマンド（run, ps程度）がわかり、ターミナル操作に抵抗がないこと。
- 必要なもの：NVIDIA製GPUを搭載したWindows/Linux PC、またはM1以降のチップを搭載したMac。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的。安価に多くのモデルを試せる最適解。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
結論から言うと、VRAMが8GBあれば「Llama 3.1 8B」クラスが快適に動きますが、業務で実用的に使うなら12GB以上、理想を言えば16GB以上を推奨します。
私は現在RTX 4090（VRAM 24GB）を2枚挿ししていますが、1枚でも十分すぎるほど速いです。

逆に、VRAM 4GB程度の古いPCや、メモリ8GBのMacBook Airでは、モデルが読み込めてもレスポンスが1秒間に1〜2文字という「電光掲示板」レベルの速度になり、実用には耐えません。
もしスペックが足りない場合は、無理にローカルで動かそうとせず、API経由でClaude 3.5 Sonnetなどを使う方が、時間単価を考えれば圧倒的に安上がりです。
ローカルLLMの最大のメリットは「無料」ではなく「秘匿性」と「カスタマイズ性」にあることを忘れないでください。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールは、LM StudioやJan、AnythingLLMなど多岐にわたります。
その中で私が「Ollama + Open WebUI」の組み合わせを推す理由は、バックエンドとフロントエンドが完全に分離されているからです。
Ollamaはモデルの管理と実行に特化しており、メモリ効率が非常に高い。
一方でOpen WebUIは、ChatGPTのUIをほぼ完璧に再現しており、PDFの読み込み（RAG）やWeb検索機能の追加が、他のツールに比べて圧倒的に容易です。

一度Dockerでこの環境を作ってしまえば、後から別のPCへ移行するのも簡単ですし、サーバーとして公開して家族やチームで共有することもできます。
「単体で動くアプリ」よりも「システムとして組み上げられる構成」にしておくことが、エンジニアとしての拡張性を確保するポイントです。

## Step 1: 環境を整える

まずはバックエンドとなる「Ollama」をインストールします。
これはLLMを動かすためのエンジン部分です。

```bash
# macOS/Linuxの場合（Windowsは公式サイトからインストーラーをダウンロード）
curl -fsSL https://ollama.com/install.sh | sh
```

Windowsユーザーは[Ollama公式サイト](https://ollama.com/)から「Download for Windows」をクリックしてインストールしてください。
インストールが終わったら、ターミナル（またはコマンドプロンプト）を開いて、正しく認識されているか確認します。

```bash
ollama --version
```

このコマンドでバージョンが表示されればOKです。
Ollamaはインストールした時点でバックグラウンドプロセスとして常駐します。
これが動いていないと、後のOpen WebUIと連携できません。

⚠️ **落とし穴:**
WindowsでNVIDIA製GPUを使っている場合、稀にOllamaがGPUを認識せず、CPUで動こうとすることがあります。
`ollama run llama3.1` を実行してみて、タスクマネージャーの「専用GPUメモリ」が消費されているか確認してください。
もし消費されていなければ、グラフィックドライバを最新に更新し、PCを再起動してください。

## Step 2: Open WebUIをDockerで起動する

次に、ブラウザから操作するための「Open WebUI」を立ち上げます。
Python環境を汚したくないので、Dockerを使うのが正解です。
ここでは「Ollamaが同じPC内で動いている」ことを前提としたコマンドを実行します。

```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

各オプションの意味を説明します。
`-p 3000:8080` は、ブラウザで `localhost:3000` にアクセスできるようにするための設定です。
`--add-host=host.docker.internal:host-gateway` が最も重要で、これがないとDockerコンテナ内のOpen WebUIから、ホスト側（自分のPC）で動いているOllamaに接続できません。
`-v open-webui:/app/backend/data` は、過去のチャット履歴を保存するための「ボリューム」設定です。これを忘れると、コンテナを止めた瞬間に履歴がすべて消えます。

⚠️ **落とし穴:**
すでにポート3000を別の開発（Reactなど）で使っている場合は、`-p 3001:8080` のように左側の数字を変更してください。

## Step 3: モデルをダウンロードして動かしてみる

ブラウザを開き、`http://localhost:3000` にアクセスします。
最初にアカウント作成画面が出ますが、これはローカル環境内に保存されるだけなので、適当な名前とメールアドレスで登録してログインしてください。

ログイン後、左上のモデル選択メニューから「モデルをダウンロード」といった項目（または設定 > モデル > モデルをプル）を探し、以下のモデル名を入力して実行します。

```text
llama3.1:8b
```

ダウンロードが完了すると、ChatGPTと同じような入力欄が現れます。
試しに日本語で話しかけてみましょう。

### 期待される出力

```text
入力：ローカルLLMのメリットを3つ教えて。
出力：
1. プライバシー保護：データが外部サーバーに送信されません。
2. オフライン動作：インターネット接続なしで利用可能です。
3. コスト：API利用料がかからず、電気代だけで使い放題です。
```

もし応答が返ってこない場合は、設定の「外部接続（Connections）」セクションを確認してください。
OllamaのURLが `http://host.docker.internal:11434` になっている必要があります。
`localhost:11434` ではDockerコンテナ自身を指してしまうため、接続に失敗します。

## Step 4: 実用レベルにする

単にチャットするだけならChatGPTで十分です。
ローカルLLMを「仕事で使える」レベルに引き上げるために、2つの設定を行います。

### 1. システムプロンプトの固定
Open WebUIの設定から「モデルファイル（Model Files）」を作成できます。
ここで「あなたは優秀なPythonエンジニアです。回答は常に簡潔な日本語で行い、コード例には必ず型ヒントを付けてください」といった指示を固定しておくと、回答の質が劇的に安定します。

### 2. PDF読み込み（RAG）の活用
入力欄の左側にある「＋」ボタン、またはファイルをドラッグ＆ドロップすることで、PDFやテキストファイルを読み込めます。
社外秘のドキュメントや、まだ世に出ていないプロジェクトの仕様書を読み込ませて、その内容について質問してみてください。
クラウドAIには絶対に投げられないデータを扱える。これこそがローカルLLMの真骨頂です。

```python
# Open WebUIの内部では、読み込まれたファイルが自動でベクトル化され
# 質問に関連する箇所がコンテキストとしてLLMに渡される仕組みになっています。
```

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error | DockerからOllamaが見えていない | API URLを `http://host.docker.internal:11434` に変更 |
| 動作が極端に重い | GPUではなくCPUで推論している | NVIDIA Container Toolkitを導入するか、モデルを4bit量子化版に変更 |
| Dockerが起動しない | WSL2またはDocker Desktopの未設定 | Windowsの場合はWSL2バックエンドを有効化する |

## 次のステップ

無事に環境が構築できたら、次は「モデルの使い分け」に挑戦してください。
汎用的な会話なら `Llama 3.1` で良いですが、日本語の自然さを追求するなら `Gemma 2`、コーディング特化なら `DeepSeek-Coder` など、用途に合わせてモデルを切り替えるのがローカル運用の醍醐味です。

さらに、Open WebUIの「Functions」機能を使えば、Pythonスクリプトを書いてLLMに独自のツール（天気予報取得やデータベース操作など）を使わせることも可能です。
私は自作のRAGパイプラインを組み込んで、過去5年分の技術ブログ記事をすべて学習させた「自分専用エージェント」を運用しています。
一度この自由度を知ってしまうと、プロンプトの検閲や課金制限があるクラウドAIには戻れなくなりますよ。

## よくある質問

### Q1: NVIDIAのGPUがないと絶対に動かないのでしょうか？

Apple Silicon（M1/M2/M3/M4）搭載のMacであれば、非常に高速に動作します。WindowsでGPUがない場合はCPU動作になりますが、実用的な速度は期待できません。その場合は、お試し程度と考えてください。

### Q2: データのプライバシーは本当に守られていますか？

はい。今回構築した環境は、モデルのダウンロード時以外、外部と通信する必要がありません。DockerコンテナとOllamaのプロセスが自分のPC内で完結しているため、入力したプロンプトが学習に使われることもありません。

### Q3: モデルはどうやって選べばいいですか？

まずは `llama3.1:8b` を基準にしてください。日本語を重視するなら `gemma2:9b` や `command-r-v01` がおすすめです。VRAMが24GB以上あるなら、より賢い `llama3.1:70b` の量子化版も視野に入ります。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のセキュアなローカルLLM環境を構築する方法](/posts/2026-08-23-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用の機密保持ローカルLLM環境を作る方法](/posts/2026-07-23-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで最強のローカルLLM環境を構築する方法](/posts/2026-08-29-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "NVIDIAのGPUがないと絶対に動かないのでしょうか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Apple Silicon（M1/M2/M3/M4）搭載のMacであれば、非常に高速に動作します。WindowsでGPUがない場合はCPU動作になりますが、実用的な速度は期待できません。その場合は、お試し程度と考えてください。"
      }
    },
    {
      "@type": "Question",
      "name": "データのプライバシーは本当に守られていますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。今回構築した環境は、モデルのダウンロード時以外、外部と通信する必要がありません。DockerコンテナとOllamaのプロセスが自分のPC内で完結しているため、入力したプロンプトが学習に使われることもありません。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルはどうやって選べばいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "まずは llama3.1:8b を基準にしてください。日本語を重視するなら gemma2:9b や command-r-v01 がおすすめです。VRAMが24GB以上あるなら、より賢い llama3.1:70b の量子化版も視野に入ります。 ---"
      }
    }
  ]
}
</script>
