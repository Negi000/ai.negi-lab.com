---
title: "Local LLM 使い方 入門：OllamaとPythonで自分専用のAIアシスタントを作る方法"
date: 2026-04-10T00:00:00+09:00
slug: "local-llm-ollama-python-tutorial-llama3"
cover:
  image: "/images/posts/2026-04-10-local-llm-ollama-python-tutorial-llama3.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Llama 3.1"
  - "Ollama 使い方"
  - "ローカルLLM Python"
  - "自炊AI"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- ローカル環境でLlama 3.1を動かし、特定のテキストファイルの内容を読み取って回答するPythonスクリプト
- 前提知識：Pythonの基本的な文法（変数、関数の定義）がわかること
- 必要なもの：8GB以上のメモリを搭載したPC（Mac/Windows/Linux）、Python 3.10以降

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBあればLlama 3.1 8Bを余裕を持って高速動作させられるため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=ASUS%20NVIDIA%20GeForce%20RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FASUS%2520NVIDIA%2520GeForce%2520RTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FASUS%2520NVIDIA%2520GeForce%2520RTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

現在、ローカルLLMを動かす手段はLM StudioやJanなど多岐にわたりますが、開発者が「自動化」を目指すならOllama一択です。
APIサーバーとしての完成度が高く、今回紹介するライブラリ「ollama-python」を使えば、わずか数行でモデルの呼び出しから推論まで完結します。
API経由でOpenAIに課金し続ける方法もありますが、情報の秘匿性が求められる実務や、数万件のバッチ処理を行うケースでは、月額無料・漏洩リスクゼロのローカル環境が最強の選択肢になります。
SIer時代、社内規定でChatGPTが使えず歯痒い思いをしましたが、この環境があれば当時の業務効率は3倍以上になっていたと確信しています。

## Step 1: 環境を整える

まずは推論エンジンであるOllamaをインストールします。

```bash
# Macの場合（Homebrewを使用）
brew install ollama

# Windows/Linuxの場合
# 公式サイト（https://ollama.com/）からインストーラーをダウンロードしてください。
```

次に、今回使用するモデル「Llama 3.1 8B」をダウンロードします。
2024年後半の現在、8Bクラスで最もバランスが良いのがこのモデルです。

```bash
# モデルのダウンロード（約4.7GB）
ollama pull llama3.1
```

Ollamaは「バックグラウンドでサーバーを立てる」仕組みのため、インストール後にアプリを起動しておくだけで準備完了です。
この設計のおかげで、Python側からHTTPリクエストを投げるだけで簡単に連携できるのが強みです。

⚠️ **落とし穴:** 初回実行時、モデルのダウンロードが途中で止まることがあります。その場合は一度コマンドをCtrl+Cで中断し、再度`ollama pull`を実行してください。レジューム機能があるため、続きから再開されます。

## Step 2: 基本の設定

PythonからOllamaを操作するためのライブラリをインストールし、接続確認を行います。

```bash
pip install ollama
```

次に、基本となる接続スクリプトを作成します。

```python
import ollama

# 使用するモデル名。事前にollama pullしたものと一致させる必要があります
MODEL_NAME = "llama3.1"

def check_connection():
    try:
        # モデルのリストを取得して、接続を確認
        models = ollama.list()
        print("接続成功。利用可能なモデル:", [m['name'] for m in models['models']])
    except Exception as e:
        print(f"接続エラー: Ollamaが起動しているか確認してください。 {e}")

if __name__ == "__main__":
    check_connection()
```

ここでは、あえて単純なリスト取得を行っています。
いきなり推論を始めると、エラーが「モデルがない」のか「サーバーが死んでいる」のか切り分けにくいため、まずはこの疎通確認を挟むのが実務上の定石です。

## Step 3: 動かしてみる

いよいよ推論を実行します。
ここではストリーミング出力（一文字ずつ表示される形式）を採用します。

```python
import ollama

def ask_local_llm(prompt):
    response = ollama.chat(
        model='llama3.1',
        messages=[{'role': 'user', 'content': prompt}],
        stream=True,
    )

    print("AIの回答:")
    for chunk in response:
        # 'content'が含まれている場合のみ出力
        if 'message' in chunk and 'content' in chunk['message']:
            print(chunk['message']['content'], end='', flush=True)
    print()

if __name__ == "__main__":
    ask_local_llm("ローカルLLMを使う最大のメリットを3つ教えて")
```

### 期待される出力

```
AIの回答:
1. プライバシーとセキュリティ: データが外部サーバーに送信されないため、機密情報を扱えます。
2. コスト削減: API利用料が発生せず、ハードウェアのリソースだけで無制限に利用可能です。
3. カスタマイズ性: 特定の業務に合わせた微調整（ファインチューニング）や設定変更が自由です。
```

ストリーミングを有効にしている理由は、ローカルLLMの「体感速度」を上げるためです。
8BモデルをRTX 4090で動かせば瞬時ですが、一般的なノートPCでは回答生成に数秒から数十秒かかります。
一括表示だとフリーズしているように見えるため、実務でツールを作る際もストリーミング実装は必須と言えます。

## Step 4: 実用レベルにする

単なるチャットでは面白くないので、実務で使える「テキストファイル読み込み・要約ツール」にアップグレードします。
長大なログファイルや議事録を読み込ませるシーンを想定しています。

```python
import os
import ollama

def summarize_file(file_path):
    if not os.path.exists(file_path):
        print(f"エラー: {file_path} が見つかりません。")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # ローカルLLMへの指示（プロンプト）の組み立て
    # 専門用語が含まれる場合は「〜という文脈で」と添えると精度が上がります
    prompt = f"""
    以下のテキストを、重要なポイントを3つの箇条書きで要約してください。

    ---
    {content}
    ---
    """

    print(f"--- {file_path} を解析中 ---")

    response = ollama.chat(
        model='llama3.1',
        messages=[{'role': 'user', 'content': prompt}],
    )

    print(response['message']['content'])

# テスト用のファイル作成
with open("sample.txt", "w", encoding="utf-8") as f:
    f.write("ローカルLLMの発展により、個人でも高性能なAIを運用できる時代が来ました。\n"
            "特にLlama 3.1のようなモデルは、従来の小型モデルとは比較にならない推論能力を持ちます。\n"
            "これにより、情報の機密性を保ちながら、業務の自動化を推進することが可能です。")

if __name__ == "__main__":
    summarize_file("sample.txt")
```

このコードのポイントは、コンテキストの渡し方です。
Llama 3.1 8Bのコンテキストウィンドウは128kトークンと非常に大きいですが、ローカル環境ではVRAM容量によって制限を受けます。
私の環境（VRAM 24GB x2）では余裕ですが、16GB以下のGPUを使っている場合は、一度に読み込ませるテキストを5,000文字程度に抑えるのが、レスポンス速度を維持するコツです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ConnectionError` | Ollamaアプリが起動していない | メニューバーやタスクマネージャーでOllamaが動いているか確認。 |
| 出力が非常に遅い | メモリ（VRAM）不足 | 量子化モデル（Q4_K_Mなど）を使用するか、ブラウザ等の他アプリを閉じる。 |
| `Model not found` | モデル名のタイポ、または未ダウンロード | `ollama list`で正確な名前を確認。`pull`し直す。 |

## 次のステップ

ここまでできれば、ローカルLLMを「自分の業務の一部」として組み込む基礎は完成です。
次は、このスクリプトに「Web検索の結果」を渡したり、複数のPDFを一度に読み込ませたりする「RAG（検索拡張生成）」に挑戦してみてください。
特に、LangChainやLlamaIndexといったフレームワークを組み合わせると、ローカルLLMの可能性はさらに広がります。
私自身、100ページ超の技術仕様書をローカルRAGに食わせて、特定のパラメータ設定の根拠を一瞬で探し出すツールを作りましたが、これがもう手放せません。
まずは自分のPCにあるメモ帳やログファイルを読み込ませることから始めてみてください。

## よくある質問

### Q1: グラボがないノートPCでも動きますか？

動きます。OllamaはCPU推論（llama.cppベース）にも対応しています。ただし、8BモデルをCPUで動かすと1秒間に数文字程度の速度になるため、より軽量な「Phi-3」や「Gemma 2 2B」などを選ぶのが現実的です。

### Q2: 会社で使ってもデータは漏洩しませんか？

理論上、100%安全です。Ollamaはインターネット接続なしでも動作します（モデルのダウンロード時を除く）。不安な場合は、ファイアウォールでOllamaのプロセスのアウトバウンド通信を遮断すれば、完全にスタンドアロンなAI環境になります。

### Q3: 日本語の精度が低いと感じるのですが？

Llama 3.1は多言語対応が進んでいますが、もし不満なら「Llama-3-Swallow」などの日本語特化モデル（日本語継続事前学習モデル）を試してください。Ollamaのライブラリからそれらの派生モデルも簡単に取得可能です。

---

## あわせて読みたい

- [Qwen3-Coder-Next 使い方 | 最強のコード生成AIで開発を自動化する手順](/posts/2026-03-07-qwen3-coder-next-local-python-tutorial/)
- [Gemma 4の最新GGUFをllama.cppで動かし実戦投入する最短ルート](/posts/2026-04-08-gemma-4-gguf-llamacpp-tutorial/)
- [Llama 3.1 8B蒸留モデルをローカルで爆速動作させる方法](/posts/2026-03-22-llama-3-1-distillation-local-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "グラボがないノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きます。OllamaはCPU推論（llama.cppベース）にも対応しています。ただし、8BモデルをCPUで動かすと1秒間に数文字程度の速度になるため、より軽量な「Phi-3」や「Gemma 2 2B」などを選ぶのが現実的です。"
      }
    },
    {
      "@type": "Question",
      "name": "会社で使ってもデータは漏洩しませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "理論上、100%安全です。Ollamaはインターネット接続なしでも動作します（モデルのダウンロード時を除く）。不安な場合は、ファイアウォールでOllamaのプロセスのアウトバウンド通信を遮断すれば、完全にスタンドアロンなAI環境になります。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の精度が低いと感じるのですが？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Llama 3.1は多言語対応が進んでいますが、もし不満なら「Llama-3-Swallow」などの日本語特化モデル（日本語継続事前学習モデル）を試してください。Ollamaのライブラリからそれらの派生モデルも簡単に取得可能です。 ---"
      }
    }
  ]
}
</script>
