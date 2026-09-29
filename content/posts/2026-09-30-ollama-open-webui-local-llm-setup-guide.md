---
title: "OllamaとOpen WebUIでローカルLLM環境を構築する方法"
date: 2026-09-30T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-09-30-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "Llama 3.1 ローカル"
  - "自宅LLM 構築"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- WebブラウザからChatGPTと同じ感覚で操作でき、自分のPC内だけで完結するセキュアなAI対話環境を構築します。
- 前提知識：ターミナル（コマンドプロンプト）でコマンドをコピペできること。
- 必要なもの：NVIDIA製GPUを搭載したWindows/Linux PC、もしくはApple Silicon（M1/M2/M3）搭載のMac。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的。8GB版と価格差以上の性能差あり。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU性能よりも圧倒的に重要なのが「VRAM（ビデオメモリ）」の容量です。
結論を言うと、VRAMが8GBあれば「Llama 3.1 8B」などの軽量モデルが快適に動き、12GBあれば実用レベル、24GB（RTX 4090など）あれば現行の主要なモデルの多くを高速に動かせます。
Macの場合はユニファイドメモリをOSと共有するため、最低でも16GB、できれば32GB以上のメモリを積んだモデルが推奨されます。

料金については、ソフトウェア自体はすべてオープンソースなので無料です。
かかる費用はPCの電気代と、ハードウェアの購入費だけです。
もしこれからGPUを買うなら、中古のRTX 3060 12GB（約3.5万円）がコストパフォーマンス最強の入門機になります。
VRAM 8GB以下のグラボを使っている場合は、推論速度が極端に落ちて1秒間に数文字しか出ない「修行」のような状態になるため、アップグレードを検討してください。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールには「LM Studio」や「GPT4All」などもありますが、私は「Ollama + Open WebUI」の組み合わせ一択だと考えています。
理由は3つあり、1つ目はバックエンド（Ollama）とフロントエンド（Open WebUI）が分離しているため、将来的にサーバーを別立てにするなどの拡張性が高いこと。
2つ目は、Open WebUIが本家ChatGPTに非常に近いUIを持ち、RAG（PDFなどのドキュメント読み込み）やWeb検索連携などの実用機能が標準で備わっていること。
3つ目は、Dockerを利用することで環境を汚さずに構築・破棄ができるため、SIer的な堅実な運用に向いているからです。

## Step 1: 環境を整える

まずはLLMの実行エンジンである「Ollama」をインストールし、次にコンテナ環境である「Docker」を準備します。

### 1. Ollamaのインストール
公式サイト（ollama.com）からインストーラーをダウンロードして実行してください。
Linuxの場合は以下のコマンド一つで完了します。

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

このコマンドは、Ollamaのバイナリをダウンロードし、システムサービスとして登録するまでを自動で行います。
手動でパスを通す手間がないため、このスクリプトを使うのが最も確実です。

### 2. Dockerのインストール
Open WebUIを動かすためにDocker Desktop（Windows/Mac）またはDocker Engine（Linux）をインストールしてください。
Windowsユーザーは、WSL2（Windows Subsystem for Linux）が有効になっていることを必ず確認してください。

⚠️ **落とし穴:**
WindowsでNVIDIA製GPUを使っている場合、Dockerコンテナ内からGPUを認識させるために「NVIDIA Container Toolkit」が必要になることがあります。
これを忘れると、せっかくのGPUが使われず、CPUだけで処理が走ってしまい「ローカルLLMは遅すぎて使えない」という誤解を生む原因になります。
インストール後、ターミナルで `nvidia-smi` と打って反応があることを確認してください。

## Step 2: 基本の設定

次に、Ollamaでモデルをダウンロード（プル）します。
今回は、Metaが公開した非常に高性能なモデル「Llama 3.1 8B」を使用します。

```bash
# Llama 3.1の80億パラメータ版をダウンロード
ollama pull llama3.1
```

なぜこのモデルを選ぶかというと、8B（80億パラメータ）というサイズが、一般的なコンシューマー向けGPUで最も高速かつ賢く動くバランスの取れたサイズだからです。
日本語の能力も高く、技術的な質問への回答精度も実用レベルに達しています。

次に、Open WebUIをDockerで起動します。以下のコマンドをターミナルに貼り付けてください。

```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

各オプションの意味を解説します：
- `-p 3000:8080`: ブラウザから `http://localhost:3000` でアクセスできるようにします。
- `--add-host=...`: コンテナ内のOpen WebUIが、ホスト側で動いているOllamaと通信するための設定です。
- `-v open-webui:...`: チャット履歴や設定を保存する領域（ボリューム）を作成しています。これを忘れるとコンテナを消した時に履歴がすべて消えます。

## Step 3: 動かしてみる

ブラウザを開き、`http://localhost:3000` にアクセスしてください。
最初の起動時にアカウント作成を求められますが、これはローカルのデータベースに保存されるだけなので、適当なメールアドレスとパスワードで構いません。
外部に送信されることはありません。

ログイン後、画面上部の「モデルを選択」から `llama3.1:latest` を選び、メッセージを入力してみます。

```text
「Pythonで、指定したディレクトリ内のファイル一覧をサイズ順に表示するスクリプトを書いてください。」
```

### 期待される出力

```python
import os

def list_files_by_size(directory):
    files = [os.path.join(directory, f) for f in os.listdir(directory)]
    # サイズを取得してソート
    files.sort(key=lambda x: os.path.getsize(x), reverse=True)

    for f in files:
        size = os.path.getsize(f)
        print(f"{os.path.basename(f)}: {size} bytes")

list_files_by_size(".")
```

レスポンスが1秒間に20トークン（日本語なら約30〜40文字）以上出ていれば、GPUが正しく活用されています。
もし1文字ずつゆっくり出てくる場合は、GPUが認識されておらずCPU推論になっている可能性が高いです。

## Step 4: 実用レベルにする

単に会話するだけでなく、特定の業務に特化させた「カスタムモデル（Modelfile）」を作成して、実用性を高めます。
例えば、「SIerのシニアエンジニアとして、コードレビューを厳しく行うAI」を作ってみます。

Open WebUIの左メニューから「モデル」→「新しいモデルを作成」を選び、以下の設定を入力します。

### ベースモデル
`llama3.1:latest`

### システムプロンプト（ModelfileのFROM行の下に記述される内容）
```text
あなたは経験豊富なシニアソフトウェアエンジニアです。
ユーザーから提出されたコードに対し、以下の観点で厳格にレビューしてください。
1. セキュリティ脆弱性（SQLインジェクション、XSS等）
2. パフォーマンス（無駄なループ、メモリリーク）
3. 可読性と命名規則
4. 例外処理の適切さ
「良さそうですね」といった妥協は一切不要です。修正すべき点を箇条書きで具体的に指摘してください。
```

この設定を行うだけで、汎用的なLlama 3.1が「厳しいレビュアー」に豹変します。
実務では、このように「役割を与えたモデル」を複数作っておき、用途に応じて切り替えるのがプロの使いかたです。
私は「ブログ記事の下書き担当」「Pythonのデバッグ担当」「英語論文の要約担当」の3つを常駐させています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Connection refused` | Ollamaが起動していない | ツールバーにOllamaのアイコンがあるか確認。Linuxなら `systemctl start ollama` |
| `Docker: command not found` | Dockerが未インストール | 各OS向けのDocker Desktop等をインストールして再起動 |
| 推論が異様に遅い | GPUが認識されていない | Docker実行時に `--gpus all` オプションを追加するか、ドライバを更新 |
| メモリ不足で落ちる | モデルがVRAMに入り切らない | パラメータ数の小さいモデル（`qwen2.5:3b` など）を試す |

## 次のステップ

無事に環境が動いたら、次は「RAG（検索拡張生成）」に挑戦してみてください。
Open WebUIには、チャット欄にPDFやテキストファイルをドラッグ＆ドロップするだけで、その内容に基づいて回答してくれる機能があります。
社内のマニュアルや、自分が過去に書いた設計書を読み込ませることで、世界に一つだけの「自分専用ナレッジベース」が完成します。

また、API経由でこのローカルLLMを操作するのも面白いです。
OllamaはOpenAI APIと互換性のあるエンドポイント（`http://localhost:11434/v1`）を持っているため、CursorやAiderといったコーディングアシスタントの接続先を自分のPCに向けることができます。
これにより、月額20ドルのサブスク料金を払わずに、プライバシーを守りながらAI開発環境を手に入れることが可能になります。
これこそが、エンジニアがローカルLLMを構築する最大のメリットだと私は確信しています。

## よくある質問

### Q1: 自宅サーバーがないと厳しいですか？

いいえ、普段使いのPCで十分です。ただし、ノートPCの場合は発熱が凄まじいので、冷却台を使うなどの対策をおすすめします。私は検証で長時間回す時は、MacBook Proの下に保冷剤（結露防止済み）を置くこともあります。

### Q2: ネットに繋がっていなくても動きますか？

はい、モデルのダウンロード時以外は完全にオフラインで動作します。機密性の高いプロジェクトや、ネット環境が不安定な場所での作業には最適です。これがクラウドAIにはない、ローカルLLMだけの強みです。

### Q3: おすすめの日本語モデルはありますか？

現時点では `Llama 3.1` が非常に優秀ですが、日本語に特化させたいなら `Qwen2.5` や、Googleが公開している `Gemma 2` も試す価値があります。Ollamaなら `ollama run gemma2` と打つだけで数分で試せます。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルAI環境を構築する方法](/posts/2026-07-11-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法](/posts/2026-08-01-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPTを構築する方法](/posts/2026-08-12-ollama-open-webui-local-llm-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "自宅サーバーがないと厳しいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ、普段使いのPCで十分です。ただし、ノートPCの場合は発熱が凄まじいので、冷却台を使うなどの対策をおすすめします。私は検証で長時間回す時は、MacBook Proの下に保冷剤（結露防止済み）を置くこともあります。"
      }
    },
    {
      "@type": "Question",
      "name": "ネットに繋がっていなくても動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、モデルのダウンロード時以外は完全にオフラインで動作します。機密性の高いプロジェクトや、ネット環境が不安定な場所での作業には最適です。これがクラウドAIにはない、ローカルLLMだけの強みです。"
      }
    },
    {
      "@type": "Question",
      "name": "おすすめの日本語モデルはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "現時点では Llama 3.1 が非常に優秀ですが、日本語に特化させたいなら Qwen2.5 や、Googleが公開している Gemma 2 も試す価値があります。Ollamaなら ollama run gemma2 と打つだけで数分で試せます。 ---"
      }
    }
  ]
}
</script>
