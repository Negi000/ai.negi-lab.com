---
title: "OllamaとOpen WebUIで自分専用のChatGPTをローカル構築する方法"
date: 2026-09-12T00:00:00+09:00
slug: "ollama-open-webui-local-llm-tutorial"
cover:
  image: "/images/posts/2026-09-12-ollama-open-webui-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "ローカルLLM 構築"
  - "Llama 3.1 RAG"
---
**所要時間:** 約25分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIを一切使わず、手元のPCだけで最新LLM（Llama 3.1やGemma 2等）とチャットできる環境を構築します。
- ブラウザから操作できるOpen WebUIを導入し、PDFの読み込み（RAG）やモデルの切り替えをGUIで完結させます。
- 前提知識として、簡単なコマンド操作（Terminal/PowerShell）とDockerの基本概念を知っているとスムーズです。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 3060 12GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 12GB搭載で、8B〜14Bクラスのモデルを快適に動かせるコスパ最強の入門GPU</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203060%252012GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203060%252012GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203060%2012GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU性能よりも重要なのが「GPUのVRAM容量」です。
結論から言うと、VRAMが8GBあれば「Llama 3.1 8B」クラスが快適に動きます。
12GBあれば少し大きめのモデルも視野に入り、16GBあれば実務レベルでストレスを感じることはありません。

Windows環境なら、NVIDIA製のRTX 3060（12GBモデル）がコスパ最強の入門機です。
「RTX 4060」はVRAM 8GB版が多いので、中古でも良いので3060の12GB版を探すのが賢い選択だと思います。
RTX 4090を2枚挿している私の環境では、70Bクラスの巨大モデルも動きますが、最初は1枚のGPUで「8B〜14B」のモデルをサクサク動かす快感を味わってください。

Macユーザーなら、最低でも16GB、できれば32GB以上のユニファイドメモリを積んだApple Silicon（M1/M2/M3）が必要です。
メモリ8GBのMacBook Airでは、モデルを読み込んだ瞬間にスワップが発生し、レスポンスが1秒間に1〜2文字という苦行になります。
投資するなら、まずはメモリです。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は、他にも「LM Studio」や「GPT4All」などがあります。
しかし、私は「Ollama + Open WebUI」の組み合わせが現在のベストプラクティスだと断言します。
理由は、Ollamaがバックエンドとして非常に軽量かつモデル管理が優秀であり、Open WebUIが本家ChatGPTに肉薄する多機能さを備えているからです。

特にOpen WebUIは、複数のモデルを同時に呼び出したり、過去のチャット履歴をベクトル検索したりする機能が標準で備わっています。
エンジニアが実務で使うなら、コマンドラインで完結するよりも、WebUI経由でRAG（外部資料読み込み）を活用する方が圧倒的に生産性が高いです。

## Step 1: Ollamaをインストールして核を作る

まずは、LLMを実行するためのエンジンである「Ollama」を導入します。
これは、モデルのダウンロード、量子化、推論実行をすべて裏側で引き受けてくれるツールです。

公式サイト（ollama.com）からインストーラーをダウンロードし、実行してください。
インストールが終わったら、ターミナル（Mac）またはPowerShell（Windows）を開き、以下のコマンドを打ちます。

```bash
# Llama 3.1の8Bモデルをダウンロードして実行
ollama run llama3.1
```

**なぜこの操作をするのか:**
`ollama run` コマンドは、モデルのダウンロードとチャットの開始を同時に行います。
ここで動けば、バックエンドの構築は8割完了です。

⚠️ **落とし穴:**
Windows環境でWSL2を使っている場合、OllamaをWSL2側に入れるかWindows側に入れるかで迷うかもしれません。
基本的には、GPUドライバーの制御が容易な「Windowsネイティブ版」を入れるのがトラブルが少なくて済みます。
また、プロキシ環境下にいる場合は環境変数 `HTTP_PROXY` を設定しないとモデルのダウンロードに失敗するので注意してください。

## Step 2: DockerでOpen WebUIを立ち上げる

次に、チャット画面となる「Open WebUI」を導入します。
これを直接PCにインストールするのは依存関係が面倒なので、Dockerを使うのが正解です。

Docker Desktopを起動した状態で、以下のコマンドを実行してください。

```bash
# Open WebUIを起動するコマンド
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

**各フラグの意味:**
- `-p 3000:8080`: PCのブラウザで `http://localhost:3000` にアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: Dockerコンテナの中から、ホストPCで動いているOllamaを見つけるための設定です。これがないと「Connection Error」で詰まります。
- `-v open-webui:/app/backend/data`: チャット履歴や設定を保存するボリュームを作成しています。コンテナを消してもデータが消えないようにするためです。

⚠️ **落とし穴:**
NVIDIA GPUを使っていて、WebUI側での処理（RAGの埋め込み計算など）も高速化したい場合は、`nvidia-container-toolkit` をインストールした上で、起動コマンドに `--gpus all` を加える必要があります。
ただし、最初は上記コマンドだけで十分動きます。

## Step 3: ブラウザから接続して初期設定

Dockerの起動が完了したら、ブラウザで `http://localhost:3000` を開きます。
最初のアクセスではアカウント作成を求められますが、これは**ローカル内のデータベースに保存されるだけ**です。
外部にメールアドレスが送信されることはないので、適当な名前とパスワードで登録してログインしてください。

ログイン後、左上のメニューから「Settings」→「Connections」を確認します。
Ollama APIのURLが `http://host.docker.internal:11434` になっていることを確認してください。

### 動作確認テスト

画面上部のモデル選択プルダウンから `llama3.1:latest` を選び、何か質問を投げます。

```text
User: 日本でおすすめの観光地を3つ教えて。
```

### 期待される出力

```text
Assistant: 1. 京都（伝統文化）、2. 東京（都市体験）、3. 北海道（自然とグルメ）...（数秒で返信が始まる）
```

レスポンスが数秒以内に返ってくれば、GPUが正しく認識されています。
もし1文字出すのに1秒以上かかる場合は、CPU推論になっている可能性が高いです。
Ollamaのログを確認し、GPU（CudaやMetal）が有効になっているかチェックしてください。

## Step 4: 実用レベルの「自分専用AI」に育てる

ただチャットするだけではChatGPTの劣化版です。
ローカルLLMの真価は「機密情報の流し込み」にあります。

### 1. PDFやドキュメントのRAG活用
Open WebUIのチャット欄に、手持ちのPDFファイルをドラッグ＆ドキュメントをアップロードしてください。
その後、`#ファイル名` と入力してから質問すると、そのファイルの内容に基づいて回答してくれます。
社外秘の仕様書や、自分だけのメモを読み込ませても、データが外部に漏れることは一切ありません。

### 2. Modelfileによるカスタマイズ
特定の役割を持たせた「カスタムモデル」を作るのも簡単です。
「Workspace」→「Models」から新しいモデルを作成し、ベースモデルに `llama3.1` を選択。
「System Prompt」に以下のような指示を書き込みます。

```text
あなたは凄腕のPythonエンジニアです。
回答は常にコード例を含め、簡潔に日本語で説明してください。
また、パフォーマンスとセキュリティの観点からのアドバイスを必ず1つ添えてください。
```

これで、自分好みの性格を持ったエンジニア専用AIが完成します。
私はこれを使って、コードレビュー専用のボットをローカルで運用しています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error | DockerからOllamaが見えていない | 起動コマンドに `--add-host` があるか再確認。Ollama側で `OLLAMA_HOST=0.0.0.0` の設定が必要な場合も。 |
| 反応が異常に遅い | メモリ不足でCPU推論になっている | モデルサイズを下げる（8B以下にする）。またはPCのメモリ/VRAMを増設する。 |
| モデルが出てこない | Ollamaでpullが完了していない | ターミナルで `ollama pull llama3.1` を実行してからWebUIをリロードする。 |

## 次のステップ

ここまでできれば、あなたのPCは強力なAIサーバーに進化しました。
次に挑戦すべきは「モデルの使い分け」です。

- **論理的思考が必要なとき:** `llama3.1:8b` や `gemma2:9b`
- **コーディング:** `codegemma` や `deepseek-coder`
- **軽量に済ませたいとき:** `phi3`

また、Open WebUIの設定から「Image Generation」を有効にし、Stable Diffusion（Automatic1111など）と連携させれば、同じ画面で画像生成まで完結できます。
API利用料を気にせず、プロンプトを1日中投げ続ける生活は、一度味わうと戻れません。
まずは手元の1ファイル、自分のメモを読み込ませることから始めてみてください。

## よくある質問

### Q1: Ollamaを動かすのに電気代はどのくらいかかりますか？

一般的なゲーミングPC（RTX 3060等）で推論回している間は、概ね200W〜300W程度の消費電力です。
24時間フル回転させなければ、月数百円程度の変化で収まります。APIを従量課金で叩き続けるよりは、圧倒的に安上がりだと思います。

### Q2: Open WebUIが「404 Not Found」で表示されません。

Dockerコンテナが正常に起動しているか `docker ps` で確認してください。
ポート3000が他のアプリ（Node.js開発など）で使われている場合は、コマンドの `-p 3001:8080` のように左側の数字を変えて試してみてください。

### Q3: 日本語の能力が低い気がするのですが、改善できますか？

モデルによります。Llama 3.1は日本語も得意ですが、より自然な日本語を求めるなら「Llama-3-Elyza-JP」などの和製チューニングモデルをGGUF形式でOllamaに取り込むのがおすすめです。
`ollama run` で公式にないモデルも、Modelfileを書けば簡単に使えます。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法](/posts/2026-08-01-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIで自分専用のローカルChatGPT環境を構築する方法](/posts/2026-08-15-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用の機密情報漏洩ゼロなChatGPT環境を構築する方法](/posts/2026-08-10-ollama-open-webui-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Ollamaを動かすのに電気代はどのくらいかかりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "一般的なゲーミングPC（RTX 3060等）で推論回している間は、概ね200W〜300W程度の消費電力です。 24時間フル回転させなければ、月数百円程度の変化で収まります。APIを従量課金で叩き続けるよりは、圧倒的に安上がりだと思います。"
      }
    },
    {
      "@type": "Question",
      "name": "Open WebUIが「404 Not Found」で表示されません。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Dockerコンテナが正常に起動しているか docker ps で確認してください。 ポート3000が他のアプリ（Node.js開発など）で使われている場合は、コマンドの -p 3001:8080 のように左側の数字を変えて試してみてください。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の能力が低い気がするのですが、改善できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデルによります。Llama 3.1は日本語も得意ですが、より自然な日本語を求めるなら「Llama-3-Elyza-JP」などの和製チューニングモデルをGGUF形式でOllamaに取り込むのがおすすめです。 ollama run で公式にないモデルも、Modelfileを書けば簡単に使えます。 ---"
      }
    }
  ]
}
</script>
