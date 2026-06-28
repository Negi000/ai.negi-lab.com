---
title: "OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法"
date: 2026-06-28T00:00:00+09:00
slug: "ollama-open-webui-local-llm-tutorial"
cover:
  image: "/images/posts/2026-06-28-ollama-open-webui-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 構築"
  - "ローカルLLM RAG"
  - "Llama 3.1 日本語"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIに一切データを送らず、完全にオフラインで動作する「自分専用ChatGPT」環境を構築します。
- ブラウザから操作できるOpen WebUIをインターフェースに使い、Llama 3.1やGemma 2といった最新モデルと日本語で対話できるようにします。
- PDFやテキストファイルを読み込ませて回答させる「RAG（検索拡張生成）」の基礎機能までを実装します。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、コマンドプロンプトやターミナルでコマンドをコピペできる程度の操作スキルが必要です。
PCはWindows、Mac、Linuxのいずれかで構いません。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのはCPU性能ではなく「VRAM（ビデオメモリ）」の容量です。
結論から言うと、VRAM 8GBが「実用レベルの最低ライン」となります。

Windows機ならNVIDIA製GPUが必須です。
RTX 3060（12GB版）やRTX 4060 Ti（16GB版）があれば、現行の主要な軽量モデル（8Bクラス）はサクサク動きます。
VRAM 4GB以下のノートPCだと、量子化された極小モデルしか動かせず、回答精度が著しく落ちるためおすすめしません。

Macの場合は、M1チップ以降のApple Silicon搭載機が必要です。
MacはメインメモリをVRAMとして共有するため、メモリ16GB以上のモデルを強く推奨します。
メモリ8GBのMacBook Airでも動きますが、モデルをロードした瞬間にスワップが発生し、レスポンスが1秒間に1〜2文字程度まで落ちるため、常用は厳しいです。

料金については、ソフトウェアはすべてオープンソースなので無料です。
かかるのはPCの電気代だけ。
API料金を気にせず、1日に何万トークン投げても月額$20のサブスク料金を払う必要もありません。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールは「LM Studio」や「GPT4All」など他にもありますが、私は「Ollama + Open WebUI」の組み合わせ一択だと考えています。

最大の理由は「拡張性」と「インターフェースの完成度」です。
LM Studioはシングルユーザーでの利用に特化していますが、Open WebUIはDocker上で動作し、複数のユーザーアカウントを作成したり、過去のチャット履歴をサーバー側に保存したりできます。

また、Open WebUIは「RAG機能」が標準搭載されており、PDFをドラッグ＆ドロップするだけで、その内容に基づいた回答を生成できます。
この「仕事で使える感」が、他のツールとは一線を画しています。
将来的に自宅サーバーを構築して、家族やチームでAI環境を共有したい場合も、この構成ならそのまま移行できます。

## Step 1: 環境を整える

まずはLLMの実行エンジンである「Ollama」をインストールします。
Ollamaは、複雑なモデルの重み管理や推論サーバーの立ち上げを、コマンド一つで完結させてくれる非常に優秀なツールです。

公式サイト（ollama.com）からインストーラーをダウンロードして実行してください。
インストールが終わったら、ターミナル（WindowsはPowerShell）を開き、以下のコマンドを打ち込みます。

```bash
# Ollamaが正しくインストールされたか確認
ollama --version

# テストとしてLlama 3.1（8B）をダウンロードして起動
ollama run llama3.1
```

`ollama run llama3.1`を実行すると、モデルのダウンロードが始まります。
初回は4〜5GB程度の通信が発生するため、安定した回線で実行してください。
完了後にプロンプトが表示されれば、この時点で「CUIでのチャット」は可能になります。

⚠️ **落とし穴:**
Windows環境でNVIDIA製GPUを積んでいるのに、動作が異常に遅い場合は「タスクマネージャー」を確認してください。
CPU使用率が100%に張り付いているなら、GPUが認識されていません。
多くの場合、NVIDIAの最新ドライバをインストールすることで解決します。
また、WSL2を使っている場合は、WSL2側でGPUパススルーの設定が必要です。

## Step 2: 基本の設定

次に、GUIとなる「Open WebUI」をDockerで立ち上げます。
なぜDockerを使うのかというと、Open WebUIが必要とする膨大なライブラリ群（Pythonパッケージやベクトルデータベース）で、メインのOS環境を汚さないためです。

まず、Docker Desktopがインストールされていることを前提とします。
以下のコマンドを1行ずつコピーして実行してください。

```bash
# Open WebUIのコンテナを起動する
# port 3000で待ち受け、データを保存するためにボリュームを作成します
docker run -d -p 3000:8080 ^
  --add-host=host.docker.internal:host-gateway ^
  -v open-webui:/app/backend/data ^
  --name open-webui ^
  ghcr.io/open-webui/open-webui:main
```
※Mac/Linuxの場合は、行末の `^` を `\` に書き換えてください。

`--add-host=host.docker.internal:host-gateway` というオプションが非常に重要です。
これは、Dockerコンテナの中から、ホスト側で動いているOllama（localhost:11434）にアクセスするための設定です。
これがないと、GUIからOllamaを認識できず「Connection Error」で詰まります。

## Step 3: 動かしてみる

ブラウザを開き、`http://localhost:3000` にアクセスしてください。
ログイン画面が表示されます。

1. 「Sign Up」をクリックしてアカウントを作成します。
2. 最初のユーザーは自動的に管理者権限（Admin）が付与されます。
3. ログイン後、画面左上のモデル選択メニューをクリックします。

もし Step 1 でダウンロードした `llama3.1` がリストに出てこない場合は、設定画面（Settings > Connections）を確認してください。
OllamaのURLが `http://host.docker.internal:11434` になっている必要があります。

### 期待される出力

チャット欄に「こんにちは、自己紹介してください」と入力してみましょう。

```text
（出力例）
こんにちは！私はLlama 3.1、Metaによってトレーニングされた大規模言語モデルです。
あなたのPC上で直接動作しており、プライバシーが守られた状態で対話が可能です。
```

レスポンス速度はどうでしょうか。
私のRTX 4090環境では瞬時に出力されますが、RTX 3060クラスでも「人間が読む速度」よりは遥かに速く出力されるはずです。

## Step 4: 実用レベルにする

単にチャットするだけではもったいないので、業務で使えるレベルにカスタマイズします。
私が実務で必ず設定するのは「日本語特化のシステムプロンプト」です。

1. Open WebUIの「Workspace」メニューから「Models」を選択します。
2. 使用しているモデル（llama3.1など）の編集ボタンを押します。
3. 「System Prompt」欄に以下を記述します。

```text
あなたは優秀な日本人エンジニアの助手です。
回答は常に日本語で行ってください。
専門用語については、必要に応じて英語を併記してください。
結論から述べ、その後に詳細を解説する論理的な構造で回答してください。
```

これで、不自然な英語混じりの回答を防げます。

さらに、RAG機能を試してみましょう。
チャット画面の「＋」ボタンから、手持ちのPDF（例えば製品のマニュアルや社内規定）をアップロードします。
その後、プロンプトで「#（ファイル名）」を指定して質問すると、そのファイルの内容に基づいて回答を生成します。
これはOpenAIの「GPTs」とほぼ同じ体験ですが、データが一切外に出ないという圧倒的な安心感があります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error | DockerからOllamaが見えていない | host.docker.internalの設定を再確認 |
| 出力が極端に遅い | GPUではなくCPUで推論している | VRAM不足か、ドライバ未認識。モデルサイズを下げる（8B→3B） |
| 日本語が不自然 | モデルの学習データの不足 | Llama-3-Swallowなど日本語強化モデルをOllamaに導入する |
| コンテナが起動しない | ポート3000が他で使用中 | `-p 8080:8080` など別のポート番号に変更して実行 |

## 次のステップ

ここまで構築できれば、あなたの手元には最強の「実験場」があります。
次に挑戦してほしいのは、用途に合わせたモデルの使い分けです。

1. **プログラミング:** `codellama` や `deepseek-coder` をダウンロードして、コード生成の精度を比較してみてください。
2. **軽量化:** `gemma2:2b` など、より小さなモデルを試して、速度と精度のトレードオフを体感してください。
3. **API連携:** OllamaはOpenAI互換のAPIエンドポイントを持っています。Pythonから `requests` ライブラリを使って、自作アプリにLLMを組み込むコードを書いてみるのも面白いでしょう。

ローカルLLMの世界は日進月歩です。
昨日まで動かなかったモデルが、アップデート一つで爆速になることも珍しくありません。
この環境をベースに、自分だけのAI活用術を模索してみてください。

## よくある質問

### Q1: 社内の共有サーバーに構築して、チームで使うことはできますか？

はい、可能です。Dockerを動かしているマシンのIPアドレス（例: 192.168.1.50:3000）を共有すれば、同じLAN内のPCからブラウザ経由でアクセスできます。ユーザー登録を「承認制」にする設定もOpen WebUI側で行えます。

### Q2: モデルのダウンロードが途中で止まってしまいます。

Ollamaのモデルサーバーが混み合っているか、回線が不安定な可能性があります。一度 `Ctrl+C` で止めてから再度 `ollama run` を実行してください。Ollamaはレジューム機能（続きからダウンロード）をサポートしているので、最初からやり直す必要はありません。

### Q3: VRAM 12GBで30B以上の大きなモデルを動かす方法はありますか？

VRAMに入り切らないモデルは、一部をメインメモリ（RAM）に逃がして動かすことができます。ただし、推論速度は1/10以下に激減します。基本的には「VRAMに収まるサイズ」のモデル（4bit量子化された8Bモデルなど）を選ぶのが実務的な判断です。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-06-16-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPT環境を作る方法](/posts/2026-05-31-ollama-openwebui-local-llm-setup-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPTを構築する方法](/posts/2026-06-22-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "社内の共有サーバーに構築して、チームで使うことはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、可能です。Dockerを動かしているマシンのIPアドレス（例: 192.168.1.50:3000）を共有すれば、同じLAN内のPCからブラウザ経由でアクセスできます。ユーザー登録を「承認制」にする設定もOpen WebUI側で行えます。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルのダウンロードが途中で止まってしまいます。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaのモデルサーバーが混み合っているか、回線が不安定な可能性があります。一度 Ctrl+C で止めてから再度 ollama run を実行してください。Ollamaはレジューム機能（続きからダウンロード）をサポートしているので、最初からやり直す必要はありません。"
      }
    },
    {
      "@type": "Question",
      "name": "VRAM 12GBで30B以上の大きなモデルを動かす方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "VRAMに入り切らないモデルは、一部をメインメモリ（RAM）に逃がして動かすことができます。ただし、推論速度は1/10以下に激減します。基本的には「VRAMに収まるサイズ」のモデル（4bit量子化された8Bモデルなど）を選ぶのが実務的な判断です。 ---"
      }
    }
  ]
}
</script>
