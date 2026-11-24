---
title: "OllamaとOpen WebUIで自分専用のセキュアなローカルLLM環境を構築する方法"
date: 2026-11-24T00:00:00+09:00
slug: "ollama-openwebui-local-llm-setup-guide"
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
  - "Docker AIチャット"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIに一切データを送らず、完全にオフラインで動作するChatGPTライクなAIチャット環境
- Ollamaをバックエンド、Open WebUIをフロントエンドとして連携させたWebベースのUI
- PDFやテキストファイルをアップロードしてAIと対話できるRAG（検索拡張生成）機能の基盤

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MSI GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3やGemma 2を余裕を持って動かせるコスパ最強の選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、コマンドプロンプトやターミナルでコマンドをコピペできる程度の操作スキルが必要です。
Dockerを使用しますが、設定手順はすべて網羅しているので、今すぐ環境を汚さずに構築を始められます。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPUよりも重要なのがGPUのビデオメモリ（VRAM）です。
快適に動作させるための最低ラインは、NVIDIA製GPUならVRAM 8GB（RTX 3060/4060等）、Macならメモリ16GB以上のApple Silicon搭載機（M1/M2/M3）です。

VRAMが8GBあれば、現在主流の「Llama 3 (8B)」クラスのモデルがサクサク動きます。
逆にVRAMが4GB以下だと、推論がCPUに回り、レスポンスが1秒間に1文字程度まで落ちるため、実用には耐えません。
もしノートPCなどでVRAMが足りない場合は、小型モデル「Phi-3 (3.8B)」を選択することで、レスポンス速度を確保できます。

導入費用は完全に0円です。
API使用料もかかりませんし、一度環境を作ってしまえば、電気代以外にコストは発生しません。
プライバシーが重要な機密文書の要約や、社外秘コードのデバッグなど、クラウドAIには投げにくい仕事に最適です。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段には「LM Studio」や「GPT4All」などもありますが、私はあえて「Ollama + Open WebUI」の組み合わせを推奨します。
理由は、Open WebUIが本家ChatGPTに最も操作感が近く、マルチユーザー管理やRAG機能（ドキュメント読み込み）が標準で備わっているからです。

Ollamaはモデルの管理や配信（推論サーバー機能）に特化しており、バックグラウンドで軽量に動作します。
この2つを組み合わせることで、「最新モデルを1コマンドで試せる手軽さ」と「業務で使える多機能なUI」が両立できます。
将来的にサーバーを別のPCに移したり、チームで共有したりする場合も、この構成が最も柔軟に対応できます。

## Step 1: 環境を整える

まずは推論エンジンである「Ollama」をインストールします。
公式サイトからインストーラーをダウンロードして実行するだけですが、ここではその後の動作確認が重要です。

```bash
# Ollamaのバージョン確認（インストール後に実行）
ollama --version
```

Ollamaはインストールしただけでは「モデル（脳）」が入っていません。
まずは最も汎用性が高い「Llama 3」をダウンロードしておきましょう。

```bash
# Llama 3の8Bモデルをダウンロードして起動
ollama run llama3
```

コマンド実行後、ターミナル上で対話が始まれば成功です。
`/bye` と入力して一旦終了してください。

⚠️ **落とし穴:**
Windows環境でGPUを認識しない場合、最新のNVIDIAドライバがインストールされているか確認してください。
また、WSL2（Windows Subsystem for Linux）上で動かそうとするとGPUパススルーの設定が複雑になるため、最初はWindowsネイティブ版のOllamaを使うのが最も確実です。

## Step 2: DockerでOpen WebUIを起動する

次に、ブラウザから操作するための「Open WebUI」を導入します。
依存関係を汚さないために、Dockerを使用するのが業界標準のやり方です。

```bash
# Dockerコンテナの起動コマンド（GPU対応版）
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

このコマンドの各オプションには重要な意味があります。
- `-p 3000:8080`: PCの3000番ポートでWeb画面にアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: Dockerコンテナの中から、外側にいるOllama（localhost:11434）を認識させるための魔法の言葉です。
- `-v open-webui:/app/backend/data`: チャット履歴や設定を保存する領域（ボリューム）を確保しています。これがないと、Dockerを止めた時にすべての履歴が消えます。

⚠️ **落とし穴:**
Docker Desktopが起動していないとこのコマンドはエラーになります。
必ずDockerを起動した状態で実行してください。
また、すでにポート3000を使用しているアプリがある場合は、`-p 3001:8080` のように左側の数字を変更してください。

## Step 3: 動かしてみる

ブラウザを開き、`http://localhost:3000` にアクセスしてください。
最初にアカウント作成画面が出ますが、これは「ローカル環境内での管理用」なので、好きなメールアドレスと名前を入力して大丈夫です。
外部にデータは送信されません。

ログイン後、画面上部の「モデルを選択」をクリックし、先ほどダウンロードした `llama3:latest` を選びます。
適当な質問を投げてみてください。

```
入力例: 「ローカルLLMを構築するメリットを3つ教えて」
```

### 期待される出力

```
1. プライバシーとセキュリティ：データが外部サーバーに送信されない。
2. コスト削減：API料金が発生せず、無制限に利用可能。
3. カスタマイズ性：自分のデータに基づいた学習や調整が自由。
```

もしモデルが出てこない場合は、画面左下のユーザー名 → Settings → Connections を開き、Ollama APIのURLが `http://host.docker.internal:11434` になっているか確認してください。
Docker内からホスト側のOllamaを呼ぶ際、このアドレス指定が必須になります。

## Step 4: 実用レベルにする

単なるチャットで終わらせるのはもったいないです。
仕事で使えるレベルにするために、特定のドキュメントに基づいた回答をさせる「RAG機能」を設定しましょう。

Open WebUIでは、チャット欄の「＋」ボタンからファイルをアップロードするか、設定画面の「Documents」にPDFを放り込むだけで準備完了です。
内部で自動的にベクトル化（AIが検索しやすい形に変換）が行われます。

次に、特定の業務に特化した「モデルファイル（Modelfile）」を作成してみましょう。
例えば、常に日本語で、かつエンジニアらしい簡潔な回答をする設定です。

```dockerfile
# Open WebUIの「Workspace」→「Models」から作成可能
FROM llama3
SYSTEM """
あなたはシニアソフトウェアエンジニアです。
回答は簡潔に、必ず日本語で行ってください。
コードを提示する場合は、パフォーマンスと可読性のバランスを重視してください。
"""
PARAMETER temperature 0.7
```

`temperature`（温度）を0.7に設定しているのは、回答に程よい柔軟性を持たせるためです。
0に近づけるほど機械的な正確さが増し、1に近づけるほど創造的になります。
プログラミング相談なら0.2〜0.5、アイデア出しなら0.8以上が経験上のベストです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error | DockerからOllamaが見えていない | 接続URLを `http://host.docker.internal:11434` に修正 |
| 回答が極端に遅い | GPUが使われずCPU推論になっている | Ollamaのログを確認し、VRAM不足がないかチェック |
| 漢字が中華フォントになる | ブラウザの言語設定の問題 | Open WebUIの設定で言語を「日本語」に固定 |

## 次のステップ

ここまでで、自分だけのセキュアなAI環境が整いました。
次に挑戦すべきは、モデルの「使い分け」です。

例えば、文章の要約や翻訳なら、日本語能力が高い「Gemma 2」や「Command R」を `ollama pull` で追加してみてください。
特定のタスクに特化したモデルを複数インストールし、Open WebUI上で切り替えながら使うことで、作業効率は劇的に向上します。

また、API経由でこの環境を「Cursor」などのコードエディタと連携させることも可能です。
ローカルで動くLLMを、あなたの開発ワークフローのどこに組み込むか。
それを模索するのが、この環境を手に入れた後の最大の楽しみです。

## よくある質問

### Q1: 自宅のPCに外部からアクセスすることはできますか？

可能です。Docker起動時のポート設定を調整し、ルーターのポート開放やVPN（Tailscale等）を組み合わせれば、外出先からスマホで自宅のRTX 4090を回すといった使い方もできます。

### Q2: 4-bit量子化などの難しい言葉を聞きますが、どれを選べばいいですか？

Ollamaで標準で落ちてくるモデルは、多くの場合4-bit量子化されています。これは精度をほぼ落とさずにメモリ消費を1/4程度にする技術です。個人利用なら、この標準設定（q4_K_Mなど）が最もバランスが良いです。

### Q3: 日本語の精度が低い気がします。改善方法はありますか？

モデルの選択が重要です。Llama 3でも「Llama-3-70B」なら非常に賢いですが、VRAMが40GB以上必要です。一般家庭のPCなら、日本語に強い「Command R」や、Googleが公開している「Gemma 2 9B」を試すと劇的に改善します。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-09-02-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-06-16-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用の機密保持ローカルLLM環境を作る方法](/posts/2026-07-23-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "自宅のPCに外部からアクセスすることはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Docker起動時のポート設定を調整し、ルーターのポート開放やVPN（Tailscale等）を組み合わせれば、外出先からスマホで自宅のRTX 4090を回すといった使い方もできます。"
      }
    },
    {
      "@type": "Question",
      "name": "4-bit量子化などの難しい言葉を聞きますが、どれを選べばいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaで標準で落ちてくるモデルは、多くの場合4-bit量子化されています。これは精度をほぼ落とさずにメモリ消費を1/4程度にする技術です。個人利用なら、この標準設定（q4KMなど）が最もバランスが良いです。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の精度が低い気がします。改善方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデルの選択が重要です。Llama 3でも「Llama-3-70B」なら非常に賢いですが、VRAMが40GB以上必要です。一般家庭のPCなら、日本語に強い「Command R」や、Googleが公開している「Gemma 2 9B」を試すと劇的に改善します。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>
