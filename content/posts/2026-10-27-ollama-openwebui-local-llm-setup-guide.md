---
title: "OllamaとOpen WebUIで自分専用のChatGPT環境を構築する方法"
date: 2026-10-27T00:00:00+09:00
slug: "ollama-openwebui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-10-27-ollama-openwebui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "Llama 3.1 ローカル"
  - "自宅サーバー AI"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIを一切使わず、自宅のPC内で完結するブラウザベースの対話型AI環境を構築します。
- 前提知識：Dockerの基本的なコマンド（コピペでOK）が使えること。
- 必要なもの：NVIDIA製GPU（VRAM 8GB以上推奨）を搭載したWindows/Linux、またはApple Silicon搭載のMac。

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

## 先に確認するスペック・料金

ローカルLLMを「仕事で使う」なら、最も重要なのはVRAM（ビデオメモリ）の容量です。
結論から言うと、最低でも8GB、ストレスなく動かすなら12GBから16GBは必須だと考えてください。
私は現在RTX 4090を2枚挿していますが、Llama 3.1の8Bモデルを動かすだけなら、5万円前後で買えるRTX 4060 Tiの16GBモデルが最もコスパが良い選択肢になります。

Apple Silicon搭載のMacの場合、メインメモリがVRAMとして共有されるため、最低でも24GB、理想は32GB以上のモデルを選んでください。
8GBや16GBのMacでも動くには動きますが、モデルをロードした瞬間にスワップが発生し、レスポンスが1秒間に1〜2文字程度まで落ち込むため、実用的ではありません。
料金については、ハードウェアさえあれば完全に無料です。
電気代はRTX 4090でフル稼働させても1時間あたり20円〜30円程度なので、APIの従量課金に怯える必要がなくなるのは大きなメリットです。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は、LM StudioやGPT4Allなど他にもいくつか存在します。
しかし、私は実務で使うなら「Ollama + Open WebUI」の組み合わせ一択だと確信しています。
理由は、Open WebUIが本家ChatGPTに最も近い操作感を持ちながら、RAG（PDFなどのドキュメント読み込み）や画像生成、Web検索機能との連携をプラグイン感覚で追加できる拡張性があるからです。

また、バックエンドにOllamaを採用することで、モデルの管理が非常に楽になります。
コマンド一つでLlama 3.1、Gemma 2、Mistralといった最新モデルをダウンロードし、すぐにAPIサーバーとして公開できる仕組みは、開発者にとって大きな武器になります。
一度Dockerで環境を作ってしまえば、OSを汚さずに最新のAI技術を追いかけられる。
これが、私がこの構成を強く推奨する理由です。

## Step 1: 環境を整える

まずは、LLMを動かすためのエンジンである「Ollama」をインストールします。

```bash
# MacまたはLinuxの場合
curl -fsSL https://ollama.com/install.sh | sh
```

Windowsの場合は、Ollamaの公式サイトからインストーラーをダウンロードして実行してください。
インストールが終わったら、ターミナル（またはコマンドプロンプト）を開き、以下のコマンドを叩いてください。

```bash
ollama --version
```

バージョンが表示されれば成功です。
次に、モデルをダウンロードします。まずは軽量で高性能な「Llama 3.1 8B」を入れましょう。

```bash
ollama run llama3.1
```

これだけでモデルのダウンロードが始まり、完了するとCUI上で対話が可能になります。
しかし、CUIでは履歴の管理やファイルのアップロードが不便なため、次のステップでブラウザから使えるUIを構築します。

落とし穴：WindowsでWSL2を使っている場合、GPUを認識させるために「NVIDIA Container Toolkit」のインストールが必要です。これがないとCPU実行になり、レスポンスが10倍以上遅くなります。

## Step 2: Open WebUIを起動する

次に、ブラウザから操作するための「Open WebUI」をDockerで立ち上げます。
Ollamaをすでにローカルにインストールしている場合は、以下のコマンドでUIだけを起動するのが最もクリーンです。

```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

このコマンドのポイントは `--add-host=host.docker.internal:host-gateway` です。
これを入れることで、Dockerコンテナの中からホストマシン上で動いているOllama（ポート11434）を「host.docker.internal」という名前で参照できるようになります。
また、 `-v open-webui:/app/backend/data` を指定することで、過去の会話履歴や設定がコンテナを消しても消えないようにしています。

落とし穴：ポート3000が他のアプリで使われているとエラーになります。その場合は `-p 3001:8080` のように、左側の数字を変更して対応してください。

## Step 3: 動かしてみる

ブラウザを開き、 `http://localhost:3000` にアクセスしてください。
最初の起動時にアカウント作成画面が出ますが、これはローカル環境に保存されるだけなので、好きな名前とメールアドレスで登録して大丈夫です。

ログイン後、画面上部の「モデルを選択」をクリックし、先ほどダウンロードした `llama3.1:latest` を選択します。
試しに何か入力してみましょう。

```text
Pythonで現在時刻を表示するスクリプトを書いて。
```

### 期待される出力

```python
from datetime import datetime
print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
```

正常に応答が返ってきたら成功です。
もし応答が極端に遅い場合は、OllamaがGPUではなくCPUを使っていないか確認してください。
私の環境（RTX 4090）では、この程度の回答は1秒かからずに生成が完了します。

## Step 4: 実用レベルにする

ここからが本番です。Open WebUIの真骨頂である「ドキュメント連携（RAG）」を設定しましょう。
左側のメニューにある「ドキュメント」をクリックし、手元にあるPDFファイルをアップロードしてみてください。

アップロード後、チャット画面で「#」を入力してからファイル名を選択し、その内容について質問します。
例えば、「この仕様書の3ページ目にある制限事項を要約して」といった具合です。
Open WebUIは内部でベクトルデータベースを持っており、アップロードされたファイルを自動的に分割・索引化してくれます。

次に、モデルの微調整を行います。
「設定」→「一般」→「アドバンスド・パラメータ」から、 `Temperature`（温度）を調整してください。
- 0.2前後：事実に基づいた正確な回答（コード作成や要約向き）
- 0.7前後：人間らしい自然な回答（アイデア出しやメール作成向き）

私は仕事で使う場合、常に0.2に設定して「嘘をつかない」ことを優先させています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error | Open WebUIがOllamaを見失っている | 設定の「外部接続」でURLを `http://host.docker.internal:11434` に変更する |
| 生成速度が異様に遅い | GPUが認識されずCPUで計算している | NVIDIAドライバを最新にし、Ollamaの再起動を行う |
| 403 Forbidden | Dockerのネットワーク設定ミス | ブラウザのキャッシュを消すか、シークレットモードで試す |

## 次のステップ

環境が整ったら、次は「独自のカスタムモデル（Modelfile）」の作成に挑戦してください。
例えば、「あなたはプロのPythonエンジニアです。回答は常にコードを優先し、解説は最小限にしてください」という指示をあらかじめ組み込んだ専用モデルを作ることができます。

また、APIキーを取得して、Open WebUIからClaude 3.5やGPT-4oを呼び出す設定を追加するのもおすすめです。
ローカルLLMで処理できる簡単なタスクと、高機能な商用AIで処理すべき複雑なタスクを、一つのUIで使い分ける。
これが、2024年現在のAI活用における「正解」だと私は考えています。
さらに自動化を進めたいなら、Difyを組み合わせてワークフローを構築する道もありますが、まずはこの「自分専用ChatGPT」を使い倒すことから始めてみてください。

## よくある質問

### Q1: 会社で使いたいのですが、データは外部に漏れませんか？

完全にローカルで完結します。OllamaもOpen WebUIも、あなたが明示的に外部API（OpenAIなど）を設定しない限り、インターネットへ会話データを送信することはありません。機密情報の要約などに最適です。

### Q2: 16GBのメモリしかないPCでも動きますか？

8B（80億パラメータ）以下のモデルなら動きます。ただし、ブラウザや他のソフトを立ち上げているとメモリ不足で重くなるため、4bit量子化されたモデル（デフォルトでこれです）を使うことを徹底してください。

### Q3: モデルを消したいときはどうすればいいですか？

ターミナルから `ollama rm モデル名` で削除できます。Open WebUI上からも「管理設定」→「モデル」から削除可能ですが、ディスク容量を確実に空けるならコマンドラインからの削除が確実です。

---

## あわせて読みたい

- [OllamaとOpen WebUIでローカルLLM環境を構築する方法](/posts/2026-09-30-ollama-open-webui-local-llm-setup-guide/)
- [ローカルLLMをPythonで制御して自分専用のプライベートAIを作る方法](/posts/2026-07-26-local-llm-python-ollama-guide/)
- [OllamaとOpen WebUIで自分専用のローカルAI環境を構築する方法](/posts/2026-07-11-ollama-open-webui-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "会社で使いたいのですが、データは外部に漏れませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "完全にローカルで完結します。OllamaもOpen WebUIも、あなたが明示的に外部API（OpenAIなど）を設定しない限り、インターネットへ会話データを送信することはありません。機密情報の要約などに最適です。"
      }
    },
    {
      "@type": "Question",
      "name": "16GBのメモリしかないPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "8B（80億パラメータ）以下のモデルなら動きます。ただし、ブラウザや他のソフトを立ち上げているとメモリ不足で重くなるため、4bit量子化されたモデル（デフォルトでこれです）を使うことを徹底してください。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルを消したいときはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ターミナルから ollama rm モデル名 で削除できます。Open WebUI上からも「管理設定」→「モデル」から削除可能ですが、ディスク容量を確実に空けるならコマンドラインからの削除が確実です。 ---"
      }
    }
  ]
}
</script>
