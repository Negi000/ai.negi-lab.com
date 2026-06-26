---
title: "OllamaとOpen WebUIの使い方！自分専用のローカルLLM環境を完全構築する方法"
date: 2026-06-26T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-06-26-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM GPU設定"
  - "Docker AI環境"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- PC1台でChatGPTと遜色ない操作感を実現する、プライベートな生成AI環境を構築します。
- 外部API（OpenAI等）を一切使わず、機密情報を入力しても漏洩しないオフライン環境が手に入ります。
- Dockerを利用し、GPUを最大限活用してLlama 3.1やGemma 2といった最新モデルを動かします。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBで8Bモデルを快適に、かつ省電力で回せる現時点のベストバイ</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
結論から言うと、NVIDIA製のGPUなら最低でも8GB、実務で快適に使うなら12GB〜16GBがボーダーラインになります。

私がメインで使っているRTX 4090 24GBであれば、Llama 3.1 8Bモデルは一瞬で返答が来ますし、量子化された70Bモデルもなんとか実用的な速度で動きます。
逆に、内蔵グラフィックスのみの一般的なノートPC（Windows）だと、返答待ちで数分かかることもあり、正直「仕事で使える」レベルにはなりません。

Apple Silicon（M1/M2/M3）のMacなら、ユニファイドメモリをAIが活用できるため、メモリ16GB以上のモデルであればかなり高速に動作します。
もしこれからハードウェアを揃えるなら、WindowsならRTX 4060 Ti 16GB版が、コスパとVRAMのバランスで最も賢い選択です。

初期投資としての機材代はかかりますが、API料金は永久に0円ですし、月額$20のサブスクを払い続ける必要もなくなります。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールは、LM StudioやAnythingLLMなど他にも存在します。
しかし、私は「Ollama + Open WebUI」の組み合わせが、現時点で最強の構成だと断言します。

理由は、バックエンドとUIが分離されているため、拡張性が非常に高いからです。
Ollamaはコマンド一つでモデルを切り替えられる軽量なエンジンであり、そこにChatGPTとほぼ同じUIを提供するOpen WebUIを被せることで、プロンプト管理やRAG（資料読み込み）が格段に楽になります。

また、Dockerベースで構築するため、環境を汚さずに済み、トラブルが起きてもコンテナごと作り直せば解決するという安心感もあります。
実務で多種多様なモデルを検証する私にとって、この「管理のしやすさ」は何物にも代え難いメリットです。

## Step 1: Ollamaのインストールと動作確認

まずはエンジンとなるOllamaをインストールします。
公式サイト（ollama.com）からインストーラーをダウンロードして実行するだけですが、ここではインストール後の「動作確認」が重要です。

```bash
# インストール後、ターミナル（PowerShellやZsh）を開いて実行
ollama --version
```

バージョンが表示されたら、試しに軽量なモデル「Gemma 2 2B」を動かしてみましょう。
なぜこのモデルかと言うと、2B（20億パラメータ）であれば、GPUが弱い環境でも確実に動作を確認できるからです。

```bash
ollama run gemma2:2b
```

コマンド実行後、モデルのダウンロードが始まります。
ダウンロード完了後に「>>>」とプロンプトが出れば、すでにあなたのPC内でAIが思考を開始できる状態です。

⚠️ **落とし穴:**
Windowsの場合、Ollamaはデフォルトでタスクトレイに常駐します。
後ほどOpen WebUIと連携させる際、Ollamaが起動していないと接続エラーになります。
「Ollamaが起動しているか」は、ブラウザで `http://localhost:11434` にアクセスし、"Ollama is running" と表示されるかどうかで判断してください。

## Step 2: GPUをDockerで使うための準備

ここが初心者が最も躓き、かつ「仕事で使える速度」を出すための最重要工程です。
WindowsやLinuxでNVIDIA GPUを使う場合、Dockerコンテナの中からGPUを認識させるために「NVIDIA Container Toolkit」をインストールする必要があります。

これを忘れると、AIの計算がCPUで行われることになり、レスポンスが10倍以上遅くなります。

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) をインストールし、設定で「Use the WSL 2 based engine」にチェックが入っていることを確認します。
2. WSL2（Ubuntu等）を開き、以下のコマンドでツールキットを導入します（Linux環境を想定）。

```bash
# リポジトリの追加
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
# インストール
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
```

Mac（Apple Silicon）の場合は、Docker Desktop側で「VirtioFS」などの設定を確認するだけで、OS標準のGPUアクセラレーションが効くため、この複雑なツールキット設定は不要です。

## Step 3: Open WebUIを起動する

いよいよ、Dockerを使ってOpen WebUIを立ち上げます。
なぜDockerを使うかというと、Pythonの依存関係で「ライブラリのバージョンが合わない」といった不毛なエラーを100%回避するためです。

以下のコマンドをターミナルにコピー＆ペーストしてください。
なお、Ollama本体はPC（ホスト）側で動いているため、Dockerコンテナからホスト側に通信できるように `--add-host` オプションを付けています。

```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

各オプションの意味は以下の通りです。
- `-d`: バックグラウンドで実行します。
- `-p 3000:8080`: ブラウザから `http://localhost:3000` でアクセスできるようにします。
- `-v`: 過去のチャット履歴や設定を保存する領域（ボリューム）を作成します。これがないと、コンテナを止めるたびにデータが消えます。

### 期待される出力

コマンド実行後、長い文字列（コンテナID）が表示されれば成功です。
ブラウザを開き、`http://localhost:3000` にアクセスしてください。
初回ログイン画面が出ますので、適当なメールアドレスとパスワードでアカウントを作成します（このデータはあなたのPC内にしか保存されません）。

## Step 4: モデルの読み込みと日本語化

Open WebUIにログインしたら、左下のユーザー名から「Settings」→「General」を開き、言語を日本語に設定しましょう。
次に、モデルを選択して対話を開始しますが、もしモデル一覧が空の場合は、以下の手順で追加します。

1. 画面上部のモデル選択欄をクリック。
2. `llama3.1:8b` などのモデル名を入力してダウンロードボタンを押す。
3. もしくは、設定の「Models」から直接プル（取得）する。

ここで私がおすすめするモデルは `qwen2.5:7b` です。
中国のアリババが開発したモデルですが、日本語能力が極めて高く、Llama 3.1よりも自然な敬語やニュアンスを理解してくれます。
実務でコードを書かせたり、文章を要約させたりするなら、現時点ではこのサイズ帯で最強だと感じています。

## 実用レベルにする：RAG（ドキュメント参照）を活用する

Open WebUIの真骨頂は、特別なコードを書かずに「RAG（検索拡張生成）」が使える点にあります。
使い方は驚くほど簡単です。

1. チャット画面で「+」ボタンを押すか、ファイルをドラッグ＆ドキュメントをアップロード。
2. アップロードしたファイルに対して「このドキュメントを要約して」と指示。

これだけで、AIがドキュメント内を検索し、その内容に基づいて回答を生成します。
例えば、会社の就業規則や、最新技術のPDFマニュアルを読み込ませることで、ネットに落ちていないクローズドな情報に基づいた回答が可能になります。

私はこれを、過去のプロジェクトの設計書（数MBのPDF）を解析させるのに使っています。
「○○機能の仕様を教えて」と聞くだけで、膨大なページから正確な記述を引っ張ってきてくれるため、ドキュメントを読み直す時間が大幅に削減されました。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Connection Error` | DockerからホストのOllamaが見えていない | Docker起動時の `--add-host` 設定を再確認する |
| 回答が異常に遅い | CPUで動作している | NVIDIA Container Toolkitが正しく設定されているか `nvidia-smi` で確認 |
| モデルがダウンロードできない | ネット回線の切断、またはディスク容量不足 | モデル1つにつき数GB〜数十GBの空き容量を確保する |

## 次のステップ

ここまでで、あなたは「完全にプライベートな生成AI環境」を手に入れました。
次に挑戦してほしいのは、以下の3点です。

1. **システムプロンプトの調整:**
   設定から「You are a professional Python developer」などのプロンプトを固定することで、より実務に特化した回答が得られるようになります。

2. **マルチモーダルモデルの試行:**
   `llava` や `moondream` といった画像認識モデルをOllamaでダウンロードしてみてください。
   Open WebUIに画像をアップロードして「この写真には何が写っている？」と聞くことができるようになります。

3. **API経由での利用:**
   OllamaはOpenAI互換のAPIエンドポイントを持っています。
   CursorやVS CodeのAI拡張機能（Continue等）の接続先を `http://localhost:11434/v1` に書き換えることで、コーディングアシスタントとしても活用できます。

ローカルLLMは、もはや「動かして遊ぶおもちゃ」ではなく、仕事の生産性を数倍に引き上げる「実用ツール」へと進化しました。
まずは `qwen2.5` でメールの返信案を作るところから、その実力を体感してみてください。

## よくある質問

### Q1: ネット接続は全く不要ですか？

モデルの初回ダウンロード時のみインターネットが必要ですが、一度ダウンロードしてしまえば、その後はPCを完全にオフラインにしても対話が可能です。飛行機の中やセキュリティの厳しい環境でも使えます。

### Q2: 4090を2枚持っていないとダメですか？

全くそんなことはありません。8B程度のモデルであれば、数万円で買えるRTX 3060（VRAM 12GB版）でも驚くほど快適に動きます。私の4090×2は、巨大なモデルを強引に動かすための極端な例です。

### Q3: データの漏洩リスクは本当にゼロですか？

はい、この構成であればデータはあなたのPCの外に出ません。Dockerコンテナ内の通信もローカルホストで完結しています。ただし、Open WebUIのWeb管理画面を外部公開（ポート開放）する場合は、適切な認証設定が必要です。

---

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-06-16-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPTを構築する方法](/posts/2026-06-22-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPT環境を作る方法](/posts/2026-05-31-ollama-openwebui-local-llm-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "ネット接続は全く不要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデルの初回ダウンロード時のみインターネットが必要ですが、一度ダウンロードしてしまえば、その後はPCを完全にオフラインにしても対話が可能です。飛行機の中やセキュリティの厳しい環境でも使えます。"
      }
    },
    {
      "@type": "Question",
      "name": "4090を2枚持っていないとダメですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "全くそんなことはありません。8B程度のモデルであれば、数万円で買えるRTX 3060（VRAM 12GB版）でも驚くほど快適に動きます。私の4090×2は、巨大なモデルを強引に動かすための極端な例です。"
      }
    },
    {
      "@type": "Question",
      "name": "データの漏洩リスクは本当にゼロですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、この構成であればデータはあなたのPCの外に出ません。Dockerコンテナ内の通信もローカルホストで完結しています。ただし、Open WebUIのWeb管理画面を外部公開（ポート開放）する場合は、適切な認証設定が必要です。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>
