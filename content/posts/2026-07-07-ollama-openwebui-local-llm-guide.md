---
title: "OllamaとOpen WebUIの使い方！完全プライベートなローカルLLM環境を構築する方法"
date: 2026-07-07T00:00:00+09:00
slug: "ollama-openwebui-local-llm-guide"
cover:
  image: "/images/posts/2026-07-07-ollama-openwebui-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 構築"
  - "ローカルLLM 環境構築"
  - "Llama 3 導入"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 自分のPC内で完結し、外部にデータが漏れないChatGPTライクなAIチャットUI
- Dockerを使用して環境を汚さず、コマンド一つで起動・停止ができる運用環境
- Llama 3やGemma 2、Qwen 2といった最新のオープンソースモデルをGUIで切り替えて使う仕組み

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的。安価に大型モデルを動かせる</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識：PCの基本的な操作ができること。コマンドプロンプトやターミナルに対して抵抗がないこと。
必要なもの：NVIDIA製GPUを搭載したWindows機、またはApple Silicon（M1/M2/M3）搭載のMac。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
結論から言うと、最低でも8GB、快適に動かすなら12GB〜16GBのVRAMが必要です。
メインメモリ（RAM）ではなく、GPU側のメモリである点に注意してください。

もしあなたがWindowsユーザーで、これからハードウェアを買うならRTX 4060 Tiの16GB版が、コストパフォーマンスとVRAM容量のバランスにおいて「現時点の最適解」です。
RTX 4070（VRAM 12GB）の方が計算速度は速いですが、扱えるモデルのサイズはVRAM容量に依存するため、16GBある方が「賢い大型モデル」を動かせるからです。

Macユーザーの場合、メモリは「ユニファイドメモリ」としてCPUとGPUで共有されるため、16GB以上のメモリを積んだモデルなら、7B（70億パラメータ）クラスのモデルが非常に軽快に動きます。
32GB以上あれば、実務で十分に使えるレベルの推論速度を維持しつつ、より大規模なモデルを試せます。

ソフト面での料金は、OllamaもOpen WebUIもオープンソースなので0円です。
ChatGPT Plusに月額3,000円払うコストを、ハードウェアの分割代金に回すという考え方は、エンジニアとして非常に合理的だと思います。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は、LM StudioやGPT4All、あるいはPythonで直書きするなど他にも選択肢はあります。
しかし、私は「Ollama + Open WebUI」の組み合わせが、現時点でのベストだと確信しています。

理由は3つあります。
1つ目は、モデル管理の容易さ。Ollamaは `ollama run llama3` と打つだけでモデルのダウンロードから実行までを自動化してくれます。
2つ目は、Open WebUIの機能性。RAG（ドキュメント読み込み）機能、画像生成、マルチユーザー管理、さらにはWeb検索連携まで、標準でChatGPTと同等以上の機能が揃っています。
3つ目は、拡張性。Dockerで動かすため、他のツール（例えばLangChainやDify）との連携が非常にスムーズです。

単に「動かして終わり」ではなく、将来的に自分の業務システムに組み込むためのバックエンドとしても機能するため、最初からこの構成で組むのが一番の近道です。

## Step 1: 環境を整える

まずは、LLMを実行するためのエンジンである「Ollama」と、コンテナ管理用の「Docker」をインストールします。

### Ollamaのインストール
公式サイト（https://ollama.com/）からインストーラーをダウンロードして実行してください。
インストール後、ターミナル（WindowsならPowerShell）を開き、以下のコマンドを打ちます。

```bash
ollama --version
```

バージョンが表示されれば成功です。Ollamaはバックグラウンドでサーバーとして常駐し、API（デフォルトは11434ポート）を提供します。

### Dockerのインストール
Open WebUIを動かすために、Docker Desktop（Windows/Mac）をインストールします。
なぜDockerを使うのかというと、Open WebUIには多くのライブラリ（Python, PyTorchなど）が含まれており、自分のPCに直接インストールすると環境がぐちゃぐちゃになるからです。コンテナで隔離することで、不要になったらフォルダごと消すだけで元の綺麗なPCに戻せます。

Windowsユーザーは「WSL 2」が有効になっていることを確認してください。Docker Desktopの設定で「Use the WSL 2 based engine」にチェックが入っていればOKです。

⚠️ **落とし穴:**
Windowsの場合、Ollamaをインストールした直後だと、タスクトレイにOllamaが常駐しています。
後のステップでDockerからOllamaに接続する際、Ollamaの「待機設定」が127.0.0.1（自分自身）だけに制限されていると、Dockerコンテナの中から接続を拒否されることがあります。
これを防ぐために、環境変数 `OLLAMA_HOST` を `0.0.0.0` に設定しておくのが無難ですが、まずはデフォルトで進め、繋がらなかったら後述のトラブルシューティングを参照してください。

## Step 2: 基本の設定

Dockerを使ってOpen WebUIを起動します。
ここでは、Ollamaが同じPC内で動いていることを前提とした、最も標準的で安定する起動コマンドを使います。

ターミナルで以下のコマンドをコピペして実行してください。

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

各オプションの意味を説明します。
- `-d`: バックグラウンドで実行します。
- `-p 3000:8080`: ブラウザから `http://localhost:3000` でアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: これが一番重要です。Dockerコンテナの中から「ホストPC（Ollamaが動いている場所）」を指す名前を定義しています。
- `-v open-webui:/app/backend/data`: チャット履歴や設定を保存する領域（ボリューム）を作成します。これを忘れると、コンテナを再起動したときに全てのデータが消えます。

## Step 3: 動かしてみる

ブラウザを開き、`http://localhost:3000` にアクセスしてください。
最初にアカウント作成画面が出ますが、これは**ローカル内のデータベースに保存されるだけ**なので、好きなメールアドレスとパスワードで登録してログインしてください。外部に送信されることはありません。

ログインしたら、左上の「モデルを選択」をクリックします。
まだモデルがない場合は、設定（左下の歯車アイコン）から「設定」→「モデル」へと進み、「モデルをプル」の入力欄に以下を打ち込んでダウンロードしてください。

```text
llama3.1:8b
```

ダウンロードが完了したら、トップ画面に戻ってモデルを選択し、何か入力してみましょう。

### 期待される出力

```text
User: こんにちは、自己紹介をお願いします。
AI: こんにちは！私はLlama 3という大規模言語モデルです。Metaによってトレーニングされました。
何かお手伝いできることはありますか？
```

レスポンスが返ってくれば成功です。
タスクマネージャー（Windows）やアクティビティモニタ（Mac）を開いて、GPUの使用率が上がっていることを確認してください。もしCPUが100%になっていて返答が極端に遅い場合は、GPUが正しく認識されていません。

## Step 4: 実用レベルにする

単なるチャットで終わらせず、実務で使えるように設定を追い込みます。
私が実際に仕事で使っている「日本語に強い」設定と、ドキュメント読み込み（RAG）の活用法を紹介します。

### 日本語モデルの追加
Llama 3も優秀ですが、日本語の自然さでは「Qwen 2」や「Gemma 2」が非常に強力です。
特にQwen 2 7B（アリババ製）は、日本語のニュアンス理解が驚くほど高いです。
設定から `qwen2:7b` を追加してみてください。

### RAG（ドキュメント参照）機能
Open WebUIの真骨頂はこれです。
チャット欄の左にある「＋」ボタンを押すか、ファイルをドラッグ＆ドロップしてください。
例えば、会社の就業規則（PDF）や、開発中のソースコードを読み込ませます。

その後、以下のように問いかけます。
```text
#document を参照して、このコードのバグを指摘してください。
```
これで、自分のPC内のデータだけを参照した、セキュアなAIアシスタントが完成します。

### プロンプトの固定（システムプロンプト）
設定の「パーソナライゼーション」から、全てのチャットに適用する指示を書けます。
私は常に「回答は簡潔に。エンジニア的な視点で、メリットだけでなくデメリットも提示すること」と入れています。
これだけで、AI特有の「丁寧すぎて要点が見えない回答」を劇的に減らせます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Connection Error` | DockerからOllamaに繋がっていない | Step 2の `--add-host` が正しいか確認。またはホストPCのIPアドレスを直接指定する。 |
| 回答が極端に遅い | GPUを使わずCPUで推論している | WindowsならOllamaを一度終了し、タスクトレイからも消してから再起動。ドライバを最新にする。 |
| Dockerが起動しない | WSL 2の未インストール | PowerShellで `wsl --update` を実行し、再起動する。 |

## 次のステップ

おめでとうございます。これであなたの手元には、世界最強クラスの知能が「オフラインかつ完全プライベート」な状態で手に入りました。
ここからさらに活用するためのアイデアを3つ提案します。

1. **Modelfileを作ってみる**: Ollamaには `Modelfile` という設定ファイルがあり、「専門家としての性格」を焼き付けたカスタムモデルを自作できます。これをOpen WebUIに登録すれば、いつでも特定のタスクに特化したAIを呼び出せます。
2. **APIとして活用する**: `localhost:11434` で動いているOllamaは、そのままAPIサーバーとして使えます。Pythonから `requests` で叩いたり、Cursor（AIエディタ）のバックエンドとして指定したりしてみてください。
3. **スマホからアクセスする**: 同じWi-Fi内であれば、PCのローカルIPアドレス（192.168.x.x）を指定してスマホのブラウザから `http://192.168.x.x:3000` にアクセスすれば、自前ChatGPTをスマホで持ち歩けます。

ローカルLLMの世界は日進月歩です。Hugging Faceを眺めて、新しいモデルがリリースされるたびに `ollama run` で試す。このワクワク感こそが、AIエンジニアとしての最大の醍醐味だと私は思います。

## よくある質問

### Q1: VRAMが8GBしかありませんが、大きなモデルは動かせませんか？

「量子化」という技術のおかげで、4bit量子化されたモデルであれば、7B〜14Bクラスなら8GBでも動きます。ただし、70Bクラスになると推論速度が極端に落ちるか、メモリ不足でエラーになります。まずは8Bモデルから試すのが正解です。

### Q2: Open WebUIが英語表示で使いにくいです。

設定（歯車アイコン）の「General」タブに「Language」設定があります。そこを「Japanese」に変更すれば、UIの大部分が日本語化されます。ただし、一部の新しい機能は英語のままのこともありますが、直感的に操作できるはずです。

### Q3: 会社のPCで動かしても大丈夫ですか？

技術的には可能ですが、Dockerのインストール権限や、社内セキュリティポリシーに注意してください。データ自体は外部に送信されませんが、モデルのダウンロード時に数GBの通信が発生するため、ネットワーク管理者に確認することをおすすめします。

---

## あわせて読みたい

- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-07-05-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPT環境を作る方法](/posts/2026-05-31-ollama-openwebui-local-llm-setup-guide/)
- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-06-28-ollama-open-webui-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "VRAMが8GBしかありませんが、大きなモデルは動かせませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "「量子化」という技術のおかげで、4bit量子化されたモデルであれば、7B〜14Bクラスなら8GBでも動きます。ただし、70Bクラスになると推論速度が極端に落ちるか、メモリ不足でエラーになります。まずは8Bモデルから試すのが正解です。"
      }
    },
    {
      "@type": "Question",
      "name": "Open WebUIが英語表示で使いにくいです。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "設定（歯車アイコン）の「General」タブに「Language」設定があります。そこを「Japanese」に変更すれば、UIの大部分が日本語化されます。ただし、一部の新しい機能は英語のままのこともありますが、直感的に操作できるはずです。"
      }
    },
    {
      "@type": "Question",
      "name": "会社のPCで動かしても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "技術的には可能ですが、Dockerのインストール権限や、社内セキュリティポリシーに注意してください。データ自体は外部に送信されませんが、モデルのダウンロード時に数GBの通信が発生するため、ネットワーク管理者に確認することをおすすめします。 ---"
      }
    }
  ]
}
</script>
