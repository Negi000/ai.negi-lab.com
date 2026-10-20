---
title: "OllamaとOpen WebUI 使い方：プライバシー重視のローカルLLM環境構築ガイド"
date: 2026-10-20T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-10-20-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "ローカルLLM 環境構築"
  - "Llama 3.1 8B 動作環境"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

自分のPC内に、ChatGPTと遜色ない操作感で、かつ外部にデータが一切漏れないローカルLLM環境を構築します。
具体的には、バックエンドに「Ollama」、フロントエンドに「Open WebUI」を組み合わせ、Llama 3.1やGemma 2といった最新モデルをブラウザから操作できる状態にします。
技術スタックはDockerを使用するため、OSを汚さず、不要になった際の削除もコマンド一つで完結する構成を目指します。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、もっとも重要なのは「VRAM（ビデオメモリ）」の容量です。
結論から言うと、ストレスなく動作させるにはNVIDIA製GPUでVRAM 12GB以上、あるいはApple Silicon（M1/M2/M3/M4）を搭載しメモリが16GB以上のMacが最低ラインになります。

VRAM 8GBでも7B（70億）クラスのモデルは動きますが、文章生成のレスポンスが1秒間に数トークン程度まで落ち込み、実用性に欠ける場面が多いです。
もしこれから機材を揃えるなら、コストパフォーマンスの観点から「RTX 4060 Ti 16GB版」を強く推奨します。
約7万円前後で購入でき、大抵の量子化済みモデルが快適に動作します。

Macユーザーの場合、メモリは「多ければ多いほど良い」です。
Apple SiliconはメインメモリをVRAMとして共有するため、16GBメモリなら10GB程度をLLMに割り当てられます。
これにより、少し重めの13Bクラスのモデルまでなら実用的な速度（20〜30 tokens/sec）で動作可能です。

ランニングコストについては、電気代以外は「完全無料」です。
API通信が発生しないため、どれだけ長文を読み込ませても、どれだけ試行錯誤しても月額料金を気にする必要はありません。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段には、他にも「LM Studio」や「GPT4All」といったデスクトップアプリ形式があります。
それらはインストールが簡単というメリットがありますが、私はあえて「Ollama + Open WebUI」の組み合わせを選びます。

理由は、拡張性と「本家ChatGPTに近しい体験」にあります。
Open WebUIは、RAG（PDFなどのドキュメント読み込み）、ウェブ検索との連携、マルチユーザー対応など、商用サービスに匹敵する機能を備えています。
また、Ollamaはバックエンドとして軽量かつAPI互換性が高いため、将来的にCursorやDifyといった他のツールと連携させる際にも、そのまま「自分専用の推論サーバー」として活用できるからです。

## Step 1: 環境を整える

まずは、すべての土台となるDockerをインストールします。
直接PCにインストールする手法もありますが、ライブラリの依存関係で環境を汚さないために、コンテナでの運用がベストです。

Windowsの場合は「Docker Desktop」、Linuxの場合は「Docker Engine」をインストールしてください。
Windowsユーザーは、WSL2（Windows Subsystem for Linux）が有効になっていることを事前に確認してください。

次に、Ollama自体をインストールします。
公式サイト（ollama.com）からインストーラーをダウンロードし、実行するだけです。
インストール完了後、ターミナル（PowerShellやTerminal.app）を開き、以下のコマンドを入力してバージョンが表示されれば準備完了です。

```bash
ollama --version
# ollama version is 0.3.x 以上の表示が出ることを確認
```

ここで一つ重要な設定があります。
Open WebUI（コンテナ内）からOllama（ホストOS側）にアクセスできるようにするため、環境変数を設定します。

Windowsの場合は、システム環境変数の編集から `OLLAMA_HOST` に `0.0.0.0` を設定してください。
これにより、Ollamaが自分自身のPC内からの通信だけでなく、コンテナからのリクエストも受け付けるようになります。設定後はOllamaを再起動してください。

⚠️ **落とし穴:**
WindowsでDockerを使っている場合、GPUをコンテナに認識させるために「NVIDIA Container Toolkit」が必要になることがあります。
ただし、今回の構成では「Ollamaはホスト側、WebUIだけコンテナ側」にするのが最もトラブルが少ないため、まずはOllamaをPC本体に直接インストールするこの手順を推奨します。

## Step 2: Open WebUIを起動する

次に、ブラウザで操作するための画面である「Open WebUI」を立ち上げます。
以下のDockerコマンドを実行してください。このコマンドは「OllamaがホストPCで既に動いている」ことを前提とした設定になっています。

```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

各オプションの意味を解説します。
- `-p 3000:8080`: PCのブラウザから `localhost:3000` でアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: これが肝です。コンテナの中から、ホストPCで動いているOllamaを見つけるための橋渡しをします。
- `-v open-webui:/app/backend/data`: チャット履歴や設定を保存する領域（ボリューム）を作成します。これがないと、コンテナを消した時に履歴がすべて消えてしまいます。

コマンド実行後、1分ほど待ってからブラウザで `http://localhost:3000` にアクセスしてください。
ログイン画面が表示されたら、好きな名前とメールアドレスでアカウントを作成します。
これは自分のPC内だけで完結するアカウントなので、実在しないメールアドレスでも問題ありません。

## Step 3: モデルをダウンロードして動かしてみる

ログインできたら、まずは頭脳となる「モデル」をダウンロードします。
画面左下の設定、またはトップのモデル選択メニューからダウンロード可能です。

最初は、Metaが開発した最高峰のオープンモデル「Llama 3.1 8B」を試しましょう。
モデル名に `llama3.1` と入力してダウンロードを開始します。

ダウンロードが完了したら、チャット画面でモデルを選択し、以下のテスト入力を投げてみてください。

```text
あなたは優秀なプログラミングアシスタントです。
Pythonで「指定したフォルダ内の画像ファイルをすべてリサイズする」コードを書いてください。
```

### 期待される出力

```python
import os
from PIL import Image

def resize_images(directory, size=(800, 800)):
    for filename in os.listdir(directory):
        if filename.endswith((".jpg", ".png", ".jpeg")):
            # 処理内容が続く...
```

レスポンスが返ってきたら、タスクマネージャー（Windows）やアクティビティモニタ（Mac）を開いてみてください。
GPUの専用メモリ使用率が上がっていれば、正しくローカルのハードウェアが使われています。
私のアセット環境（RTX 4090）では、Llama 3.1 8Bなら瞬時に回答が生成されますが、これがAPI経由ではない「手元の計算資源」で動いているという事実に、私は毎回少し感動します。

## Step 4: 実用レベルにする（RAG機能の活用）

Open WebUIをただのチャットUIで終わらせるのはもったいないです。
この環境の最大の利点は、自分の手元にある秘匿性の高いファイルを読み込ませる「RAG（検索拡張生成）」が標準搭載されている点にあります。

使い方は簡単です。チャット欄に「#（シャープ）」を入力してみてください。
すると「ドキュメントのアップロード」という選択肢が出てきます。
ここに、社外秘の仕様書や、一般には公開されていない技術資料のPDFを放り込みます。

```text
#仕様書.pdf
このシステムのデータベース設計における制約事項を3点、箇条書きで抽出してください。
```

このように指示を出すと、Open WebUIは自動的にPDFを解析し、その内容に基づいて回答を生成します。
クラウド型のAIサービスでは「データを学習に使われるのではないか」という懸念が常に付きまといますが、このローカル環境であれば、物理的にインターネットから切り離した状態でも動作します。
この「安心感」こそが、実務でローカルLLMを運用する最大の価値だと私は考えます。

また、設定から「Web Search」を有効にすれば、検索エンジンと連携して最新情報を取得することも可能です。
無料のツールだけで、ここまで高機能な自分専用AIアシスタントが構築できるのは、少し前までは考えられなかったことです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Errorが出る | WebUIがOllamaを見失っている | Step 2の `--add-host` 設定を再確認し、Ollama側の `OLLAMA_HOST` 環境変数を見直す |
| 動作が異常に遅い | GPUではなくCPUで推論している | グラフィックドライバを最新にし、OllamaがGPUを認識しているかログを確認する |
| モデルのDLが途中で止まる | ストレージ不足か通信環境 | 1モデルあたり5GB〜10GBの空き容量が必要です。ディスク容量を確認してください |

## 次のステップ

無事に環境が構築できたら、次はモデルの「使い分け」をマスターしてください。
Llama 3.1は汎用性に優れていますが、日本語の自然さでは「Gemma 2」や「Llama-3-Swallow」に分がある場合があります。
Ollamaなら `ollama run` コマンド一つで新しいモデルを秒速で試せるので、自分の用途に合うモデルを探す旅に出てみてください。

さらにステップアップするなら、構築したOllamaを「Cursor」というコードエディタと連携させることをお勧めします。
Cursorの設定から「OpenAI API互換」の項目にローカルのURLを入れるだけで、自分が書いているコードを外部に1行も送ることなく、AIによるコーディング補完が受けられるようになります。
これこそが、SIer出身でセキュリティにうるさい私が、最終的に行き着いた理想の開発環境です。

## よくある質問

### Q1: Dockerを使わずに構築してもいいですか？

もちろん可能ですが、Open WebUIは依存するライブラリが多く、Python環境が壊れるリスクがあります。Dockerなら `docker stop` してコンテナを消すだけで元の綺麗な状態に戻せるため、初心者ほどコンテナ管理を推奨します。

### Q2: 会社支給のPC（GPUなし）でも動きますか？

動きますが、CPU推論になるため回答生成は非常にゆっくりになります。1秒間に1〜2文字程度の速度です。実務で使うなら、MacBook ProのMシリーズ搭載モデルか、NVIDIA製GPU搭載のデスクトップPCを用意するのが賢明です。

### Q3: 複数のモデルを同時に起動できますか？

VRAMが許す限り可能です。Ollamaは自動的にメモリ管理を行いますが、複数の巨大なモデルを同時に動かそうとすると、メモリ溢れが発生してCPU推論に切り替わり、激重になります。使わないモデルはこまめに終了させるのがコツです。

---

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的。電気代と性能のバランスが最高</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のChatGPTを構築する方法](/posts/2026-08-12-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIを組み合わせて自分専用のローカルChatGPT環境を構築する方法](/posts/2026-07-08-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法](/posts/2026-07-12-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Dockerを使わずに構築してもいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "もちろん可能ですが、Open WebUIは依存するライブラリが多く、Python環境が壊れるリスクがあります。Dockerなら docker stop してコンテナを消すだけで元の綺麗な状態に戻せるため、初心者ほどコンテナ管理を推奨します。"
      }
    },
    {
      "@type": "Question",
      "name": "会社支給のPC（GPUなし）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、CPU推論になるため回答生成は非常にゆっくりになります。1秒間に1〜2文字程度の速度です。実務で使うなら、MacBook ProのMシリーズ搭載モデルか、NVIDIA製GPU搭載のデスクトップPCを用意するのが賢明です。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のモデルを同時に起動できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "VRAMが許す限り可能です。Ollamaは自動的にメモリ管理を行いますが、複数の巨大なモデルを同時に動かそうとすると、メモリ溢れが発生してCPU推論に切り替わり、激重になります。使わないモデルはこまめに終了させるのがコツです。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでローカルLLM入門に現実的。電気代と性能のバランスが最高</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
