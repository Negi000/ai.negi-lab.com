---
title: "OllamaとOpen WebUIで自分専用の機密保持ローカルLLMを構築する方法"
date: 2026-11-16T00:00:00+09:00
slug: "ollama-openwebui-local-llm-guide"
cover:
  image: "/images/posts/2026-11-16-ollama-openwebui-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "ローカルLLM RAG 構築"
  - "Docker AI環境"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

PC内部で完結し、外部へデータが一切漏れない「自分専用のChatGPTクローン」を構築します。
具体的には、バックエンドにOllama、フロントエンドにOpen WebUIを組み合わせ、ブラウザからPDF読み込みやWeb検索、画像認識が可能なAI環境をDockerで立ち上げます。
この記事を読み終える頃には、社外秘のドキュメントを読み込ませて要約させたり、プログラミングのコードレビューをローカルで完結させたりできるようになります。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのはGPUの「VRAM（ビデオメモリ）」容量です。
結論から言うと、VRAMが8GBあれば「Llama 3 8B」クラスが快適に動き、16GBあれば実務で実用的な「Command R」や「Gemma 2 27B」の量子化版が視野に入ります。

Windowsユーザーであれば、NVIDIA製のRTX 3060（12GBモデル）やRTX 4060 Ti（16GBモデル）がコストパフォーマンスの面で最適です。
Macユーザーの場合、メモリはVRAMと共有されるため、最低でも24GB、できれば32GB以上のユニファイドメモリを搭載したモデルを推奨します。
メモリが8GBや16GBしかないPCでも動作自体はしますが、推論速度が1秒間に1〜2トークン（文字）程度まで落ち込み、実用に耐えません。

ソフトウェアはすべてオープンソースを利用するため、月額費用などのランニングコストは電気代を除いて0円です。
構築前に、Docker Desktopがインストールされていること、およびWSL2（Windowsの場合）がセットアップされていることを確認してください。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールは、LM StudioやGPT4Allなど他にも多く存在します。
しかし、私は実務で使うなら「Ollama + Open WebUI」の組み合わせ一択だと考えています。

理由は、Open WebUIが本家ChatGPTに最も近い操作感を持ちながら、RAG（ドキュメント参照回答）や関数呼び出しなどの高度な機能を標準で備えているからです。
また、OllamaはAPIサーバーとしても非常に優秀で、作成した環境をそのままCursor（AIエディタ）や他の自作アプリから呼び出す基盤になります。
一つのツールで完結させるのではなく、推論エンジン（Ollama）とインターフェース（Open WebUI）を分けることで、将来的な拡張性が大幅に高まります。

## Step 1: 環境を整える

まずは推論エンジンであるOllamaをインストールします。
OllamaはLLMの実行ファイルを管理・実行するための軽量なツールです。

公式サイト（ollama.com）からインストーラーをダウンロードし、実行してください。
インストール後、ターミナル（PowerShellやTerminal.app）を開き、以下のコマンドを入力してバージョンが表示されれば成功です。

```bash
# Ollamaのバージョン確認
ollama --version
```

次に、Ollama単体でモデルをダウンロードし、動作確認を行います。
ここでは現在最も汎用性が高い「Llama 3」の80億パラメータモデル（8B）を使用します。

```bash
# Llama 3をダウンロードして実行
ollama run llama3
```

これだけでAIとの対話が可能になりますが、ターミナルでの操作は実務向きではありません。
確認ができたら `/bye` と入力して終了してください。

⚠️ **落とし穴:**
Windows環境でVPNを使用していると、Ollamaのモデルダウンロードが極端に遅くなる、あるいは失敗することがあります。
その場合は一時的にVPNを切断するか、プロキシ設定を見直してください。
また、GPUが認識されていない場合は、最新のNVIDIAドライバがインストールされているか確認が必要です。

## Step 2: 基本の設定

次に、GUI環境となるOpen WebUIをDockerで構築します。
なぜDockerを使うかというと、Pythonの依存関係でローカル環境を汚さず、かつアップデートが容易だからです。

以下のコマンドをターミナルに貼り付けて実行してください。
このコマンドは、Open WebUIがホスト（あなたのPC）上で動いているOllamaと通信できるように設定されています。

```bash
# Open WebUIの起動コマンド（Windows/macOS共通）
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

各オプションの意味を説明します。
`-p 3000:8080` はPCの3000番ポートでWebUIにアクセスするための設定です。
`--add-host=host.docker.internal:host-gateway` は、Dockerコンテナの中からPC本体で動いているOllamaを見つけるために不可欠な設定です。
`-v open-webui:/app/backend/data` は、過去のチャット履歴や設定をPC内に保存するための設定で、これを忘れるとコンテナを再起動するたびにデータが消えます。

コマンド実行後、ブラウザで `http://localhost:3000` にアクセスしてください。
最初のサインアップ画面が表示されますが、これはローカルに保存されるアカウントなので、適当なメールアドレスと名前で登録して問題ありません。

## Step 3: 動かしてみる

ログイン後、まずはOllamaと正しく接続できているかを確認します。
画面左下の設定（自分の名前部分）から「Settings」→「Connections」を開き、OllamaのURLが `http://host.docker.internal:11434` になっていることを確認してください。

接続が確認できたら、トップ画面のモデル選択プルダウンから「llama3:latest」を選択します。
もしリストに出てこない場合は、画面上の検索窓に `llama3` と入力してプル（ダウンロード）を開始してください。

### 期待される出力

チャット欄に「こんにちは、自己紹介してください」と入力します。

```text
こんにちは！私はLlama 3、Metaによってトレーニングされた大規模言語モデルです。
私はあなたのPC上で直接動作しており、プライバシーが守られた状態で様々な質問に答えたり、
コードを書いたり、文章を作成したりすることができます。
```

このように返ってくれば、ローカルLLM環境の構築は完了です。
タスクマネージャーやアクティビティモニタを確認すると、GPU（または専用メモリ）の使用率が上がっていることがわかるはずです。

## Step 4: 実用レベルにする

ここからが本番です。単なるチャットではなく、業務で使えるレベルに機能を拡張します。
Open WebUIの最大の武器は「RAG（検索拡張生成）」機能です。

画面上の「+」ボタンから「Documents」を選択し、手持ちのPDFファイルやテキストファイルをアップロードしてみてください。
アップロード後、チャット欄で `#` （ハッシュタグ）を入力すると、アップロードしたファイル名が表示されます。
ファイルを選択した状態で「この資料の内容を3つの要約にまとめて」と指示を出してください。

```python
# Open WebUI内部で行われている処理のイメージ（概念）
import requests

def query_with_rag(prompt, document_id):
    # 文書から関連箇所を抽出（実際にはOpen WebUIが自動でベクトル検索を行う）
    context = search_context(document_id, prompt)

    # OllamaのAPIに文脈を添えてリクエスト
    payload = {
        "model": "llama3",
        "prompt": f"資料内容: {context}\n質問: {prompt}",
        "stream": False
    }
    response = requests.post("http://localhost:11434/api/generate", json=payload)
    return response.json()["response"]
```

私の場合、会社の就業規則や技術仕様書をすべてこれに放り込んでいます。
外部のAIサービスにアップロードするには気が引ける機密文書でも、ローカル環境なら安心して解析させることができます。
また、設定から「Web Search」を有効にし、SearXNGなどの検索エンジンと連携させれば、最新のニュースを考慮した回答も可能になります。

さらに、プログラミング用途では「Modelfile」を活用しましょう。
Open WebUIの「Workspace」→「Models」から、既存のモデルをベースに「あなたはシニアPythonエンジニアです。常に型ヒントを付け、疎結合なコードを書いてください」といったシステムプロンプトを固定した専用モデルを作成できます。
これにより、毎回長い指示（プロンプト）を打つ手間が省けます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error | DockerからOllamaが見えていない | `--add-host` 設定を再確認。またはOllamaの環境変数 `OLLAMA_HOST` を `0.0.0.0` に設定する。 |
| 回答が遅すぎる | CPUで推論している、またはVRAM不足 | モデルサイズを小さくする（8B以下）。GPUドライバを更新し、Dockerの設定でGPUを有効にする。 |
| Dockerが起動しない | WSL2の未セットアップ（Windows） | `wsl --install` を実行し、BIOSで仮想化設定（VT-x/AMD-V）を有効にする。 |

## 次のステップ

ここまでで、あなたは自分専用のセキュアなAI環境を手に入れました。
次に挑戦すべきは「モデルの使い分け」と「外部アプリ連携」です。

1. **モデルの選定:**
日本語能力を重視するなら、サイバーエージェントの「OpenCALM」や、Googleの「Gemma 2」をOllamaにインポートして試してみてください。
特にGemma 2 9Bは、Llama 3 8Bよりも日本語の自然さで勝るケースが多いです。

2. **Cursorとの連携:**
AIエディタの「Cursor」の設定から、モデルのベースURLを `http://localhost:11434` に書き換えることで、ローカルのOllamaを使ってコード生成を行えるようになります。
これにより、コードを一切外部サーバーに送らずにAI補完を利用できます。

3. **APIを活用した自動化:**
Pythonの `requests` ライブラリを使って、ローカルLLMを自作のスクリプトに組み込んでみてください。
大量のテキストファイルの分類や、特定のフォーマットへの変換など、API料金を気にせず数千件のデータを一気に処理する快感は、ローカル環境ならではの体験です。

## よくある質問

### Q1: 社内の他のメンバーにもこの画面を使わせることはできますか？

可能です。Dockerを起動しているPCのローカルIPアドレス（例: 192.168.1.10:3000）を同じネットワーク内のメンバーに共有すれば、ブラウザからアクセスできます。Open WebUIには管理者機能があり、新規ユーザーの登録制限やモデルの利用制限も行えます。

### Q2: 動作が重いのですが、グラフィックボードを買い替えるしかないですか？

まずは「量子化（Quantization）」レベルを確認してください。Ollamaはデフォルトで4-bit量子化モデルを使用しますが、それでも重い場合はさらに圧縮率の高いモデルを探すか、モデルサイズを4Bや2Bなどの小さいものに変更することで改善する可能性があります。

### Q3: モデルを自分で追加するにはどうすればいいですか？

Hugging Faceなどで公開されているGGUF形式のファイルを入手し、「Modelfile」を作成することでOllamaに取り込めます。Open WebUI上の「Workspace」から「Modelfile」を直接記述してインポートすることも可能で、専門的な知識がなくても比較的簡単に拡張できます。

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
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載で、Llama 3などの主要モデルを余裕を持って動かせる入門最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [OllamaとOpen WebUI 使い方ガイド！ローカルLLM構築](/posts/2026-06-30-ollama-openwebui-local-llm-guide/)
- [OllamaとOpen WebUIの使い方！自分専用のローカルLLM環境を完全構築する方法](/posts/2026-06-26-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法](/posts/2026-11-03-ollama-open-webui-local-llm-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "社内の他のメンバーにもこの画面を使わせることはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Dockerを起動しているPCのローカルIPアドレス（例: 192.168.1.10:3000）を同じネットワーク内のメンバーに共有すれば、ブラウザからアクセスできます。Open WebUIには管理者機能があり、新規ユーザーの登録制限やモデルの利用制限も行えます。"
      }
    },
    {
      "@type": "Question",
      "name": "動作が重いのですが、グラフィックボードを買い替えるしかないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "まずは「量子化（Quantization）」レベルを確認してください。Ollamaはデフォルトで4-bit量子化モデルを使用しますが、それでも重い場合はさらに圧縮率の高いモデルを探すか、モデルサイズを4Bや2Bなどの小さいものに変更することで改善する可能性があります。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルを自分で追加するにはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Hugging Faceなどで公開されているGGUF形式のファイルを入手し、「Modelfile」を作成することでOllamaに取り込めます。Open WebUI上の「Workspace」から「Modelfile」を直接記述してインポートすることも可能で、専門的な知識がなくても比較的簡単に拡張できます。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GB搭載で、Llama 3などの主要モデルを余裕を持って動かせる入門最適解</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
