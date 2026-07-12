---
title: "OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法"
date: 2026-07-12T00:00:00+09:00
slug: "ollama-open-webui-local-llm-guide"
cover:
  image: "/images/posts/2026-07-12-ollama-open-webui-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "ローカルLLM 環境構築"
  - "RAG 自炊"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- インターネット不要でChatGPTのようにチャットができ、PDFなどのドキュメントを読み込ませて解析（RAG）も可能なローカルLLM環境を構築します。
- 外部APIにデータを送らないため、機密情報の要約やコード解析をセキュアに行える環境が手に入ります。
- 必要なものは、一定スペック以上のPC（Windows/Mac/Linux）のみです。

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

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
メインメモリ（RAM）ではなく、GPUが積んでいるメモリの量が動作速度と扱えるモデルのサイズを決めます。

Windowsユーザーであれば、最低でもVRAM 8GB（RTX 3060 8GB等）は欲しいところです。
実務でストレスなく動かすなら、RTX 4060 Ti 16GBや、私が使っているRTX 4090クラスが理想ですが、まずは手持ちの機材で試すのが賢明です。
Macユーザーなら、M1以降のチップを搭載し、ユニファイドメモリが16GB以上あれば十分に実用レベルで動きます。

料金については、ツールの利用料は完全に無料です。
かかるのは電気代と、ハードウェアの購入費だけです。
APIを叩くたびにお金が減る感覚から解放されるのは、開発者にとって精神衛生上とても良いものです。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、llama.cppを直接ビルドしたり、LM Studioを使ったりと様々あります。
その中で「Ollama + Open WebUI」の組み合わせを推す理由は、バックエンドとフロントエンドの分離が明確だからです。

Ollamaはモデルの管理と実行（推論サーバ）に特化しており、非常に軽量で動作が安定しています。
一方、Open WebUIはChatGPTに匹敵する多機能なインターフェースを提供しており、RAG（ドキュメント参照）やマルチユーザー管理、さらにはモデルの微調整パラメーターまでGUIで操作できます。
この組み合わせは、単に「動かしてみた」で終わらず、チーム内での共有や本格的な開発基盤として「仕事で使える」レベルに容易に拡張できるのが最大のメリットです。

## Step 1: 環境を整える

まずは、LLMの実行エンジンであるOllamaをインストールします。
OSごとにインストーラーが用意されていますが、LinuxやWSL2環境であればコマンド一発で完了します。

```bash
# Linux / WSL2 の場合
curl -fsSL https://ollama.com/install.sh | sh
```

WindowsやMacの場合は、公式サイト（ollama.com）からバイナリをダウンロードして実行するだけです。
インストールが完了したら、以下のコマンドで動作確認を行います。

```bash
ollama --version
```

このコマンドでバージョンが表示されれば、バックエンドの準備は完了です。
Ollamaはインストール後、バックグラウンドで常駐し、11434ポートでAPIリクエストを待ち受ける状態になります。

⚠️ **落とし穴:** WindowsのWSL2で動かす場合、デフォルト設定ではGPU（NVIDIA）を認識しないことがあります。
事前に最新のNVIDIAドライバーとNVIDIA Container Toolkitをインストールしておく必要があります。
これを忘れると、CPUだけで推論が走り、回答が1文字ずつ数秒かけて出てくるという「地獄の遅さ」を体験することになります。

## Step 2: 基本の設定

次に、GUI環境である「Open WebUI」を導入します。
これを直接OSにインストールするのは依存関係の解決が面倒なので、Dockerを使うのが正解です。

```bash
# Dockerを使ってOpen WebUIを起動するコマンド
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

各オプションの意味を解説します。
`-p 3000:8080` は、ブラウザから `http://localhost:3000` でアクセスできるようにする設定です。
`--add-host` の部分は非常に重要で、Dockerコンテナの中からホストマシンで動いているOllama（11434ポート）を見つけられるようにするために必要です。
`-v` は、チャット履歴やアップロードしたドキュメントを永続化するためのボリューム設定です。

設定後、ブラウザで `http://localhost:3000` を開きます。
最初のアクセスではアカウント作成を求められますが、これはローカルに保存されるだけなので、好きなメールアドレスとパスワードを設定してください。
最初に登録したユーザーが自動的に管理者権限を持ちます。

## Step 3: 動かしてみる

ログインできたら、まずはモデルをダウンロード（プル）しましょう。
画面左下の設定アイコン、あるいはトップページのモデル選択メニューから、動かしたいモデル名を入力します。

まずは、Meta社が公開している軽量かつ高性能な「Llama 3.1 8B」を試すのがおすすめです。

```text
# モデル選択欄に入力する名前
llama3.1:8b
```

ダウンロードが完了すると、チャット画面でモデルを選択できるようになります。
適当な質問を投げてみてください。

### 期待される出力

```text
User: 日本の首都はどこですか？
Assistant: 日本の首都は東京です。
```

もし、回答が英語で返ってくる場合は、システムプロンプトに「あなたは優秀な日本語アシスタントです。必ず日本語で回答してください」と入力しておくことで、挙動を固定できます。
Open WebUIの設定メニューから、デフォルトのシステムプロンプトを変更可能です。

## Step 4: 実用レベルにする

単なるチャットだけで終わらせるのはもったいないです。
実務で最も役立つのは「RAG（検索拡張生成）」機能です。

Open WebUIでは、メッセージ入力欄の「＋」ボタンをクリックするか、ファイルをドラッグ＆ドロップすることで、PDFやテキストファイルを読み込ませることができます。
例えば、社内の技術仕様書を読み込ませてみましょう。

```text
# 読み込ませた後の質問例
「この仕様書における、エラーハンドリングの共通ルールを箇条書きで抽出して」
```

内部では、アップロードされたドキュメントが自動的にベクトル化（Embedding）され、質問に関連する箇所を抽出してLLMに渡してくれます。
この処理もすべてローカルで行われるため、外部に情報が漏れる心配はありません。

さらに、PythonからOllamaを制御することで、大量のファイルをバッチ処理することも可能です。
以下のコードは、OllamaのAPIを直接叩いてテキストを要約する最小構成のスクリプトです。

```python
import requests
import json

def summarize_local(text):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3.1:8b",
        "prompt": f"以下の文章を短く要約してください:\n\n{text}",
        "stream": False
    }

    # タイムアウトを長めに設定（ローカルの負荷状況によるため）
    response = requests.post(url, json=payload, timeout=120)

    if response.status_code == 200:
        return response.json()['response']
    else:
        return f"Error: {response.status_code}"

# 実行例
test_text = "ローカルLLMは、プライバシーの保護とコスト削減の観点から注目されています..."
print(summarize_local(test_text))
```

このように、バックエンドとしてOllamaが動いていれば、Open WebUIというGUIと、自作スクリプトというCUIの両方から同じモデルを使い回せます。
これが「Ollama + Open WebUI」構成の最大の強みです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| 回答が極端に遅い | GPUが使われていない | `nvidia-smi`でGPU使用率を確認し、DockerにGPUパススルーを設定する |
| Connection Refused | Ollamaが起動していない | ターミナルで `ollama serve` を実行するか、サービスが動いているか確認 |
| モデルが見つからない | プル（ダウンロード）に失敗 | `ollama pull llama3.1` を手動で実行し、容量不足でないか確認 |

## 次のステップ

無事に環境が構築できたら、次はモデルの「量子化（Quantization）」について学んでみることをおすすめします。
VRAMが限られていても、量子化されたモデルを使えば、通常は動かないような巨大なモデル（Llama 3.1 70Bなど）を動かせる可能性があります。
Ollamaはデフォルトで4-bit量子化版をダウンロードしますが、用途に応じてより精度の高いモデルを「Modelfile」を作成して読み込ませることも可能です。

また、Open WebUIの「Functions」や「Filters」という機能を使えば、LLMの回答を外部APIと連携させたり、回答前に特定のワードを検閲したりするカスタマイズも可能になります。
ここまで来れば、あなた専用の「最強のAIアシスタント」が完成したと言えるでしょう。
クラウドに依存しない、自由なAIライフを楽しんでください。

## よくある質問

### Q1: VRAMが4GBしかない古いPCでも動きますか？

結論から言うと動きますが、モデル選びが重要です。
Llama 3.1 8Bは厳しいかもしれませんが、Microsoftの「Phi-3 Mini」やGoogleの「Gemma 2 2B」といった、30億パラメータ前後の軽量モデルであれば、4GBでも快適に動作します。

### Q2: 家族やチームメンバーと共有して使えますか？

はい、Open WebUIはマルチユーザー対応です。
同じLAN内にいる人なら、あなたのPCのIPアドレス（例: `http://192.168.1.5:3000`）をブラウザに入力するだけで利用できます。
管理画面からユーザー作成を制限することも可能です。

### Q3: モデルを追加するたびにディスク容量が減って困ります。

LLMのモデルは1つあたり4GB〜50GB程度あります。
不要になったモデルは `ollama rm モデル名` でこまめに削除しましょう。
モデルの保存先を外付けSSDなどに変更したい場合は、環境変数 `OLLAMA_MODELS` を設定することで変更可能です。

---

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [OllamaとOpen WebUIを組み合わせて自分専用のローカルChatGPT環境を構築する方法](/posts/2026-07-08-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIの使い方！完全プライベートなローカルLLM環境を構築する方法](/posts/2026-07-07-ollama-openwebui-local-llm-guide/)
- [NVIDIA vs Mac 2026年版ローカルLLM環境構築ガイド](/posts/2026-05-25-local-llm-nvidia-vs-mac-2026-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "VRAMが4GBしかない古いPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "結論から言うと動きますが、モデル選びが重要です。 Llama 3.1 8Bは厳しいかもしれませんが、Microsoftの「Phi-3 Mini」やGoogleの「Gemma 2 2B」といった、30億パラメータ前後の軽量モデルであれば、4GBでも快適に動作します。"
      }
    },
    {
      "@type": "Question",
      "name": "家族やチームメンバーと共有して使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、Open WebUIはマルチユーザー対応です。 同じLAN内にいる人なら、あなたのPCのIPアドレス（例: http://192.168.1.5:3000）をブラウザに入力するだけで利用できます。 管理画面からユーザー作成を制限することも可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルを追加するたびにディスク容量が減って困ります。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "LLMのモデルは1つあたり4GB〜50GB程度あります。 不要になったモデルは ollama rm モデル名 でこまめに削除しましょう。 モデルの保存先を外付けSSDなどに変更したい場合は、環境変数 OLLAMAMODELS を設定することで変更可能です。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>
