---
title: "OllamaとOpen WebUIで自分専用のChatGPT環境を作る方法"
date: 2026-05-31T00:00:00+09:00
slug: "ollama-openwebui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-05-31-ollama-openwebui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 構築"
  - "Llama 3.1 ローカル"
  - "自作AIアシスタント"
---
**所要時間:** 約45分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- OllamaとOpen WebUIを連携させ、ブラウザからGPT-4o級のローカルLLMを操作できる環境を構築します。
- PythonからOllama APIを叩き、ローカルファイルを自動で要約・整理する実用的なスクリプトを作成します。
- 前提知識：ターミナルでの基本的なコマンド操作、Dockerの概念、Pythonの基礎知識。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBを積んだ最も安価なGPU。実務的なローカルLLM環境にはこれが最低ライン</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを仕事で「実用的」に使うには、スペック選びで妥協すると後悔します。
最も重要なのはVRAM（ビデオメモリ）の容量で、最低でも8GB、快適に動かすなら16GB以上が必須です。
RTX 4060 Ti (16GB版) は、コストパフォーマンスの面で現在もっとも賢い選択肢と言えます。

Apple Silicon搭載のMacを使う場合は、ユニファイドメモリが24GB以上あれば、Llama 3.1（8Bクラス）をストレスなく動かせます。
逆に、メモリ8GBのMacや、VRAM 4GB程度の古いGPUでは、レスポンスが遅すぎて実務には耐えられません。
API料金は一切かかりませんが、PCを回し続ける電気代が月数百円程度かかるのが唯一のコストです。

## なぜこの方法を選ぶのか

かつてローカルLLMの構築は、llama.cppをビルドし、複雑な環境変数を通し、モデルファイルを一つずつ手動でダウンロードする苦行でした。
しかし、現在は「Ollama」という決定版のツールが登場し、モデル管理が劇的に簡素化されています。
APIサーバーとしての完成度も高く、OpenAI互換のインターフェースを標準で備えている点が最大のメリットです。

UIに関しては、コマンドラインだけでは仕事の効率が上がりません。
「Open WebUI」は、RAG（ドキュメント読み込み）や画像生成、プロンプト管理など、商用のChatGPTに近い機能を備えています。
Dockerで構築することで、ホストOSを汚さずに最新の機能を追えるため、現時点でのベストな構成だと断言できます。

## Step 1: 環境を整える

まずはLLMの実行基盤となるOllamaをインストールします。

```bash
# macOS/Windows: 公式サイト(https://ollama.com/)からインストーラーをダウンロード
# Linux: 以下のコマンドで一発インストール
curl -fsSL https://ollama.com/install.sh | sh
```

Ollamaをインストールすると、バックグラウンドでサーバーが立ち上がります。
次に、実際に動かすモデルをダウンロード（プル）します。

```bash
# Llama 3.1 8Bモデルを取得（実務で最もバランスが良い）
ollama pull llama3.1
```

**⚠️ 落とし穴:** WindowsでWSL2を使っている場合、GPUが正しく認識されないことがあります。
`nvidia-smi` コマンドを叩いてGPUが見えるか確認してください。
もし見えない場合は、NVIDIA Container Toolkitのインストールが必要です。

## Step 2: Open WebUIをDockerで起動する

ブラウザから操作するためのGUIを構築します。
PythonでUIを自作するのも手ですが、Open WebUIの多機能さをゼロから作るのは時間の無駄です。

```bash
# Dockerを使ってOpen WebUIを起動（Ollamaが同じPCで動いている前提）
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

`--add-host=host.docker.internal:host-gateway` を指定しているのは、Dockerコンテナの中から、ホスト側で動いているOllamaのAPI（ポート11434）にアクセスさせるためです。
これがないと、UIだけ立ち上がって「モデルが見つからない」という状態になります。

## Step 3: 動かしてみる

ブラウザを開き `http://localhost:3000` にアクセスします。
初回ログイン画面が出ますが、これはローカル環境内でのユーザー管理用なので、適当なメールアドレスとパスワードで登録してください。

画面上部のモデル選択から `llama3.1:latest` を選び、何か質問を投げます。

### 期待される出力

```text
User: 業務自動化のアイデアを3つ出して。
Llama 3.1: 1. メールの自動返信下書き作成、2. 議事録の要約とタスク抽出、3. 経費精算書類のデータ化...
```

レスポンスが1秒間に20トークン以上出ていれば、実務で使える合格ラインです。
もし1文字ずつゆっくりしか出てこない場合は、GPUではなくCPUで動いてしまっています。

## Step 4: 実用レベルにする（Python連携）

「チャットして終わり」ではAIブロガーとしては不十分です。
PythonからOllamaを制御し、特定のフォルダにあるテキストファイルを一括で要約するスクリプトを作成します。

```python
import os
import requests
import json

# Ollama APIの設定。デフォルトのポートは11434
OLLAMA_URL = "http://localhost:11434/api/generate"

def summarize_text(text):
    """
    指定されたテキストをOllamaを使って要約する
    """
    payload = {
        "model": "llama3.1",
        "prompt": f"以下のテキストを仕事で役立つ形式で簡潔に要約してください:\n\n{text}",
        "stream": False # 実務ではストリームより一括取得の方が扱いやすい
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "要約に失敗しました")
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

def process_files(directory):
    """
    ディレクトリ内の.txtファイルをすべて要約する
    """
    if not os.path.exists(directory):
        print(f"ディレクトリが見つかりません: {directory}")
        return

    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"--- {filename} を要約中 ---")
                summary = summarize_text(content)
                print(summary)
                print("\n")

if __name__ == "__main__":
    # ここに要約したいファイルが入っているパスを指定
    target_dir = "./docs"
    process_files(target_dir)
```

このスクリプトでは `requests` ライブラリだけでOllamaと通信しています。
外部ライブラリを最小限にしているのは、依存関係によるトラブルを避けるためです。
`stream: False` に設定することで、プログラム側で全文を受け取ってから次の処理へ進めるようにしています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Refused | Ollamaが起動していない | ツールバーのOllamaアイコンを確認、または `ollama serve` を実行 |
| モデルが表示されない | Open WebUIの設定ミス | WebUIの設定から「Ollama API URL」が `http://host.docker.internal:11434` になっているか確認 |
| 動作が異常に重い | VRAM不足でCPU推論になっている | モデルを小さいもの（`phi3` や `gemma:2b`）に変更して試す |

## 次のステップ

環境が整ったら、次は「RAG（検索拡張生成）」に挑戦してください。
Open WebUIの画面左下にある「Documents」にPDFやCSVをアップロードすれば、その内容に基づいた回答が可能になります。
これは、会社の社内規定や技術ドキュメントを読み込ませて「自分専用のAIアシスタント」を作る第一歩です。

また、API経由でCursorなどのAIエディタと連携させるのもおすすめです。
ローカルLLMをエディタのバックエンドに指定すれば、コードを外部に送信することなく補完機能を使えます。
ハードウェアに余裕があるなら、16GB以上のVRAMを活かして `Llama-3.1-70B` の軽量量子化版（Q2_K等）を試してみてください。
知識の深さが8Bモデルとは比較にならないほど向上します。

## よくある質問

### Q1: 自宅サーバーではなくノートPCでも動きますか？

M2/M3チップを積んだMacBook Air（メモリ16GB以上）なら驚くほど快適に動きます。
Windowsノートの場合は、ゲーミングモデルでない限り厳しいですが、最近のIntel Core Ultra搭載機ならNPUや内蔵GPUを使ってある程度動作します。

### Q2: OpenAIのAPIを使うのと比べて精度はどうですか？

正直に言えば、GPT-4oと比較すると、Llama 3.1 8Bは推論能力で一歩譲ります。
しかし、特定のフォーマットへの変換や単純な要約、情報の抽出といった「定型業務」であれば、ローカルモデルでも十分すぎる成果を出せます。

### Q3: 複数のモデルを同時に動かすことはできますか？

VRAMが許す限り可能です。Ollamaは自動的にメモリ管理を行ってくれます。
ただし、同時に動かすと1つあたりの推論速度が落ちるため、基本的には1つのタスクに1つのモデルを集中させるのが、私の経験上もっとも効率的です。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [Qwen2.5をローカル環境で動かし、API料金を気にせずコード生成を自動化するPythonスクリプトを作る方法](/posts/2026-05-09-qwen-2-5-coder-local-python-guide/)
- [Qwen 2.5やGemma 2をローカル環境で高速に動かす方法](/posts/2026-04-29-how-to-setup-local-llm-qwen-python-ollama/)
- [ローカルLLMで漫画翻訳！Manga Translatorの使い方と導入手順](/posts/2026-03-15-local-manga-translator-rust-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "自宅サーバーではなくノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "M2/M3チップを積んだMacBook Air（メモリ16GB以上）なら驚くほど快適に動きます。 Windowsノートの場合は、ゲーミングモデルでない限り厳しいですが、最近のIntel Core Ultra搭載機ならNPUや内蔵GPUを使ってある程度動作します。"
      }
    },
    {
      "@type": "Question",
      "name": "OpenAIのAPIを使うのと比べて精度はどうですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "正直に言えば、GPT-4oと比較すると、Llama 3.1 8Bは推論能力で一歩譲ります。 しかし、特定のフォーマットへの変換や単純な要約、情報の抽出といった「定型業務」であれば、ローカルモデルでも十分すぎる成果を出せます。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のモデルを同時に動かすことはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "VRAMが許す限り可能です。Ollamaは自動的にメモリ管理を行ってくれます。 ただし、同時に動かすと1つあたりの推論速度が落ちるため、基本的には1つのタスクに1つのモデルを集中させるのが、私の経験上もっとも効率的です。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>
