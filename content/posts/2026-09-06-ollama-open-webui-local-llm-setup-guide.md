---
title: "OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法"
date: 2026-09-06T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-09-06-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama"
  - "Open WebUI"
  - "ローカルLLM"
  - "環境構築"
  - "Docker"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

この記事を読み終える頃には、あなたのPC上でChatGPTと同等のUIを持ち、外部へデータが一切漏れない「完全プライベートなAI環境」が動いています。
クラウドのAPI料金を気にせず、VRAMが許す限り無限に推論を回せる環境を、DockerとOllamaを組み合わせて構築します。

- ローカルPC（Windows/Mac/Linux）で動くLLMサーバー
- ブラウザから操作できる高機能なチャットUI（Open WebUI）
- PDFやテキストを読み込ませて回答させるRAG（検索拡張生成）機能

前提として、Dockerの基本的な概念を知っているとスムーズですが、コマンドはすべてコピペで動くように解説します。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、もっとも重要なのは「ビデオメモリ（VRAM）」の容量です。
結論から言うと、7B〜8Bクラス（Llama 3.1 8Bなど）のモデルを快適に動かすなら、最低でも8GBのVRAM、できれば12GB以上が理想です。
メインメモリは16GBあれば動きますが、Open WebUIをDockerで立ち上げ、さらにブラウザを多用することを考えると32GBあるとストレスがありません。

Windows環境なら、現在コスパが最強なのは「RTX 4060 Ti 16GB」です。
これ1枚あれば、現世代の主要な軽量モデルはすべて高速に動作します。
逆に、RTX 4060 8GBだと、大規模なモデルを読み込んだ瞬間に動作が極端に重くなり、実用性を欠く場面が出てきます。

Macユーザーの場合、Apple Silicon（M1/M2/M3）のユニファイドメモリの恩恵が非常に大きいです。
メモリを32GB以上にカスタマイズしたMacBook ProやMac Studioであれば、70Bクラスの巨大なモデルも（速度は落ちますが）動かすことができます。
逆に、メモリ8GBのMacだと、モデルを読み込んだだけでOS全体の挙動が怪しくなるため、買い替えを検討したほうが賢明です。

料金面では、電気代を除けば完全に「無料」です。
API課金を気にしてプロンプトを削る必要はもうありません。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、他にも「LM Studio」や「GPT4All」など、より簡単なオールインワンアプリが存在します。
それでも私が「Ollama + Open WebUI」を推す理由は、その圧倒的な拡張性と実務への転用しやすさにあります。

LM Studioは個人が手元のPCで試す分には最高ですが、UIと実行エンジンが一体化しているため、他のアプリケーションからLLMを呼び出すのが少し面倒です。
一方、Ollamaは「バックエンド（推論エンジン）」として独立しており、Open AI互換のAPIを自動で立ち上げてくれます。
これにより、将来的にCursorなどのエディタや、自作のPythonスクリプトからローカルLLMを叩く際の設定が非常に楽になります。

さらにフロントエンドとして使う「Open WebUI」は、名前の通りChatGPTの操作感をほぼ完璧に再現しています。
マルチユーザー対応、RAG（ドキュメント検索）、Webブラウジング機能まで標準で備わっており、もはやローカル版ChatGPTと言っても過言ではありません。
仕事で使う以上、単なる「動くおもちゃ」ではなく、実用的なワークフローを組めるこの組み合わせがベストな選択肢になります。

## Step 1: 環境を整える

まずは推論エンジンである「Ollama」をインストールします。

```bash
# Mac/Linuxの場合（公式のインストールスクリプト）
curl -fsSL https://ollama.com/install.sh | sh
```

Windowsの場合は、公式サイト（ollama.com）からインストーラーをダウンロードして実行してください。
インストールが完了したら、ターミナル（Powershell等）を開き、以下のコマンドでバージョンが表示されるか確認します。

```bash
ollama --version
```

次に、動作確認として軽量なモデル「Llama 3.1 8B」をダウンロードして起動してみます。

```bash
ollama run llama3.1
```

初回実行時は数GBのモデルデータがダウンロードされます。
完了後にチャット画面が表示されれば、バックエンドの準備は完了です。
`/bye` と打てば終了できます。

⚠️ **落とし穴:**
Windowsユーザーで、NVIDIAのGPUを積んでいるのにCPUで動いてしまう（回答が極端に遅い）場合は、WSL2の設定を確認してください。
`nvidia-smi` コマンドを叩いて、GPU情報が表示されない場合はドライバの再インストールが必要です。
また、Ollamaはデフォルトでバックグラウンド常駐します。設定変更を反映させる際は、タスクバーのアイコンから一度「Quit Ollama」して再起動するのを忘れないでください。

## Step 2: 基本の設定（Docker環境）

Open WebUIを構築するためにDockerを使用します。
Dockerを使う理由は、複雑なPython環境や依存ライブラリをホストOS（あなたのPC）に一切汚さずに導入できるからです。

以下の内容を `docker-compose.yml` という名前のファイルで保存してください。

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: always
    ports:
      - "3000:8080"
    volumes:
      - open-webui:/app/backend/data
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      - 'OLLAMA_BASE_URL=http://host.docker.internal:11434'

volumes:
  open-webui: {}
```

この設定のポイントは `extra_hosts` と `OLLAMA_BASE_URL` です。
Dockerコンテナの中から、あなたのPC本体（ホスト）で動いているOllamaを見つけるために、この「橋渡し」の設定が必要になります。
これを忘れると、WebUIを立ち上げても「Ollamaに接続できません」というエラーで30分は悩むことになります。

## Step 3: 動かしてみる

ターミナルで `docker-compose.yml` を置いたディレクトリに移動し、以下のコマンドを実行します。

```bash
docker compose up -d
```

コンテナが起動したら、ブラウザで `http://localhost:3000` にアクセスしてください。
ログイン画面が表示されます。

「なぜローカルなのにログインが必要なのか」と思うかもしれませんが、これはOpen WebUIがマルチユーザーを想定した設計だからです。
最初の1人目が「管理者」になります。
名前、メールアドレス、パスワードを適当に入力してアカウントを作成してください（外部に送信されることはありません）。

### 期待される出力

ログイン後、トップ画面左上の「モデルを選択」をクリックします。
先ほどコマンドラインでダウンロードした `llama3.1:latest` が選択肢にあれば成功です。
適当に「こんにちは、自己紹介して」と投げてみてください。
爆速で回答が返ってくるはずです。

もしモデルが出てこない場合は、設定メニューの「外部接続」から、OllamaのURLが `http://host.docker.internal:11434` になっているか再確認してください。

## Step 4: 実用レベルにする

単にチャットするだけなら、公式のChatGPTで十分です。
ローカル環境ならではの「実戦投入」のコツを2つ伝授します。

### 1. RAG（検索拡張生成）機能を使い倒す
Open WebUIのチャット欄にファイルをドラッグ＆ドロップしてみてください。
PDFやExcelをアップロードすると、その中身を解析して回答してくれるようになります。
「この仕様書の3ページ目にある、APIの認証方式について要約して」といった指示が、完全オフラインで可能です。
機密情報をクラウドにアップできないSIer時代の私のような人間にとって、これは文字通りの「救世主」です。

### 2. Modelfileで「自分専用エージェント」を作る
左サイドバーの「ワークスペース」から「モデル」を選び、新しいモデルを作成できます。
ここで「ベースモデル」に `llama3.1` を選び、「システムプロンプト」を書き込みます。

```text
あなたは凄腕のPythonエンジニアです。
回答は必ずコードスニペットを含め、
初心者がハマりやすいエラーの対処法を3つ併記してください。
```

これを「Python Master」といった名前で保存しておけば、いつでも特定の専門家と対話できるようになります。
これは、内部的には `ollama create` コマンドで新しいモデルファイルを生成しているのと同じですが、UI上からノーコードで管理できるのがOpen WebUIの強みです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Connection Error` | DockerからOllamaが見えていない | `docker-compose.yml` の `host.docker.internal` 設定を確認。 |
| 回答が1文字ずつで非常に遅い | GPUが使われずCPUで推論している | Ollamaの設定画面でGPUが認識されているか確認。VRAM不足でメインメモリに溢れている可能性もあり。 |
| モデルのダウンロードが止まる | ネットワーク断線またはディスク容量不足 | モデルファイルは1つ4GB〜8GBあります。空き容量を確保して `ollama pull` を再試行。 |

## 次のステップ

ここまでできれば、あなたのPCは「最強の思考補助ツール」に進化しました。
次にやるべきことは、この環境を「外部から呼び出す」ことです。

たとえば、VS Codeの拡張機能である「Continue」や「Aider」の設定画面で、APIエンドポイントを `http://localhost:11434` に向けてみてください。
GitHub Copilotのようなコード補完が、自分のローカルLLMを使って動かせるようになります。
さらに、Pythonの `langchain` や `llamaindex` を使って、自分のローカルLLMを組み込んだ独自のAIアプリを開発するのも面白いでしょう。

私はよく、深夜に思いついた大量のテキストデータの分類や構造化を、ローカルLLMに「流しっぱなし」にして寝ます。
朝起きたら、数百円分のAPI課金が発生することなく、綺麗に整理されたJSONファイルが出来上がっている。
この「自由」を一度味わうと、もうクラウド一択の生活には戻れません。

## よくある質問

### Q1: RTX 3060 12GBでも動きますか？

結論、めちゃくちゃ快適に動きます。Llama 3.1 8Bクラスならお釣りが出るレベルです。12GBというVRAM量は、中規模モデルを動かす上での「最低ラインかつ最もコスパの良い選択」と言えます。

### Q2: 会社で使ってもセキュリティ上問題ないですか？

はい、この構成の最大の利点です。OllamaもOpen WebUI（Docker）も、モデルをダウンロードした後はインターネット接続なしで動作します。外部サーバーにプロンプトが送信されることはありませんが、モデルのダウンロード時だけは通信が必要です。

### Q3: 複数のLLMを同時に使い分けられますか？

可能です。Open WebUIの画面上でモデルを切り替えるだけで、Ollamaが自動でメモリ上のモデルを入れ替えてくれます。ただし、複数のモデルを「同時に」起動したままにするには、それだけの合計VRAM容量が必要になるので注意してください。

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
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的。8Bモデルが余裕で動く。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [OllamaとOpen WebUIを連携させ、完全にオフラインで動作する「プライベートChatGPT環境」を構築します。](/posts/2026-07-20-ollama-open-webui-local-llm-tutorial/)
- [ローカルLLM環境の選び方とおすすめGPU比較：RTX 4060 Tiから4090、Macまで](/posts/2026-09-05-local-llm-gpu-buying-guide-rtx-vram/)
- [OllamaでAlexaを賢く！ローカルLLM構築におすすめのGPU・PC比較と選び方](/posts/2026-06-06-ollama-powered-alexa-hardware-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3060 12GBでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "結論、めちゃくちゃ快適に動きます。Llama 3.1 8Bクラスならお釣りが出るレベルです。12GBというVRAM量は、中規模モデルを動かす上での「最低ラインかつ最もコスパの良い選択」と言えます。"
      }
    },
    {
      "@type": "Question",
      "name": "会社で使ってもセキュリティ上問題ないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、この構成の最大の利点です。OllamaもOpen WebUI（Docker）も、モデルをダウンロードした後はインターネット接続なしで動作します。外部サーバーにプロンプトが送信されることはありませんが、モデルのダウンロード時だけは通信が必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のLLMを同時に使い分けられますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Open WebUIの画面上でモデルを切り替えるだけで、Ollamaが自動でメモリ上のモデルを入れ替えてくれます。ただし、複数のモデルを「同時に」起動したままにするには、それだけの合計VRAM容量が必要になるので注意してください。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでローカルLLM入門に現実的。8Bモデルが余裕で動く。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
