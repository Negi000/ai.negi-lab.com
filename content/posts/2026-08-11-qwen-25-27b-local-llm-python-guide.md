---
title: "Qwen 2.5 27B 使い方 | 16GB以上のVRAMを使い切るローカルLLM構築ガイド"
date: 2026-08-11T00:00:00+09:00
slug: "qwen-25-27b-local-llm-python-guide"
cover:
  image: "/images/posts/2026-08-11-qwen-25-27b-local-llm-python-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen 2.5 27B"
  - "Ollama 使い方"
  - "Python AI 実装"
  - "ローカルLLM 環境構築"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Qwen 2.5（あるいは発表が待たれる最新3.8世代）の27Bモデルをローカル環境で爆速起動し、Pythonから指示を飛ばして「構造化されたデータ（JSON形式）」を抽出するスクリプトを作成します。
- 前提知識: Pythonの基本的な読み書きができること。
- 必要なもの: NVIDIA製GPU（VRAM 16GB以上推奨）または Apple Silicon搭載Mac（メモリ24GB以上推奨）。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBで27Bモデルを動かせる最も安価な選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLM、特に27B（270億パラメータ）クラスを動かす上で、妥協できないのがVRAM（ビデオメモリ）容量です。
4bit量子化（モデルの軽量化）を施した状態で、モデル本体に約16GB、コンテキスト（対話履歴）の保持にプラス数GBが必要になります。
RTX 3060 12GBではメインメモリへのスワップが発生し、レスポンスが1秒間に1〜2文字程度まで落ち込むため、実用的ではありません。

理想はRTX 4060 Ti 16GB、あるいはRTX 3090/4090の24GBモデルです。
中古のRTX 3090なら10万円前後で手に入りますが、消費電力が350Wを超えるため、電源ユニットは850W以上を確保してください。
Macユーザーであれば、メモリが統合されているため、M2/M3 Pro以上のチップでメモリ24GB以上を積んでいれば驚くほど快適に動きます。
API料金は一切かかりませんが、電気代として月数百円〜数千円の上乗せを覚悟するだけで、プライバシーを完全に守ったまま「検閲なし」の推論環境が手に入ります。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手法は、llama.cppを直接叩く方法や、LM StudioなどのGUIツールを使う方法など多岐にわたります。
私が今回「Ollama」と「Python」を組み合わせる方法を選ぶ理由は、開発効率と再現性が最も高いからです。
Ollamaはバックエンドでllama.cppを最適化して動かしており、モデルの管理がコマンド一つで完結します。

他のツールでは、GGUFファイルを自分でHugging Faceから探してダウンロードし、パスを通す手間が発生しますが、Ollamaならその手間がありません。
また、Python APIが公式に提供されているため、一度環境を作ればLangChainやLlamaIndexといった上位ライブラリへの移行もスムーズです。
「動かす」だけでなく、その先の「アプリに組み込む」を見据えた場合、この構成が2024年現在のベストプラクティスだと言い切れます。

## Step 1: 環境を整える

まずは、推論エンジンとなるOllamaをインストールし、27Bモデルを動かすための設定を行います。

```bash
# Linux/macOSの場合
curl -fsSL https://ollama.com/install.sh | sh

# Windowsの場合は、公式サイト (https://ollama.com/) からインストーラーをダウンロードして実行
```

インストールが完了したら、ターミナル（またはコマンドプロンプト）で以下のコマンドを叩き、Qwen 2.5の27Bモデルをプルします。
※Redditで話題になっている「3.8-27b」が正式リリースされた直後であれば、タグ名が変更される可能性がありますが、基本は `qwen2.5:27b` を指定します。

```bash
# モデルのダウンロード（約16GBの通信が発生します）
ollama pull qwen2.5:27b
```

コマンドの意味: `ollama pull` はDockerのimage pullと同じ感覚で、指定したモデルをローカルストレージに保存します。
27Bは非常に巨大なファイルなので、安定した光回線環境で実行してください。

⚠️ **落とし穴:**
Windows環境でWSL2を使っている場合、GPUが正しく認識されないことがあります。
`ollama serve` を実行した際、ログに `NVIDIA GPU detected` と出ているか必ず確認してください。
もしCPU推論になってしまう場合は、NVIDIA公式から「CUDA Toolkit」をインストールし直すと解決することが多いです。

## Step 2: 基本の設定

次に、PythonからOllamaを制御するためのライブラリをインストールし、接続確認を行います。

```bash
pip install ollama
```

ライブラリをインストールしたら、以下のPythonコードを作成します。
ここでは、単なるチャットではなく「システムプロンプト」を固定し、AIに特定の役割（エンジニア等）を持たせる設定を組み込みます。

```python
import ollama

# モデル名の定義（Step 1でプルした名前と一致させる）
MODEL_NAME = "qwen2.5:27b"

def chat_with_qwen(prompt):
    try:
        response = ollama.chat(model=MODEL_NAME, messages=[
            {
                'role': 'system',
                'content': 'あなたはシニアソフトウェアエンジニアです。回答は簡潔かつ技術的に正確に行ってください。',
            },
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        return response['message']['content']
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

# 動作確認
print(chat_with_qwen("Pythonでデコレータを使うメリットを3つ教えて"))
```

各設定の意図を解説します。
`role: system` を指定しているのは、モデルの振る舞いを安定させるためです。
27Bクラスのモデルは指示追従性が非常に高いため、ここで「JSONで返せ」や「日本語で返せ」と指定するだけで、出力の制御が格段に楽になります。
また、APIキーの設定が不要なのは、ローカルサーバー（localhost:11434）と通信しているためです。

## Step 3: 動かしてみる

スクリプトを実行すると、ターミナルに回答が流れてくるはずです。

### 期待される出力

```
1. コードの再利用性向上：共通処理（ログ出力や認証）を複数の関数に簡単に適用できます。
2. 関心の分離：ビジネスロジックと付随的な処理を分離し、可読性を高めます。
3. 既存コードの修正最小化：元の関数の定義を変更せずに、機能を追加できます。
```

結果の読み方ですが、出力の「開始までの速さ（Time to First Token）」に注目してください。
RTX 3090/4090環境であれば、ほぼ瞬時に生成が始まります。
もし数秒〜数十秒待たされる場合は、VRAMが不足してメインメモリ（RAM）にモデルが溢れている証拠です。
その場合は、Ollamaの起動オプションで量子化レベルをさらに下げたモデル（例：`qwen2.5:27b-instruct-q2_K`）を検討する必要があります。

## Step 4: 実用レベルにする

実務でLLMを使う場合、最も重宝するのは「非構造化テキストからのデータ抽出」です。
例えば、バラバラな形式のログやメール本文から、特定の項目を抜き出してJSON形式に変換するスクリプトを構築します。
27Bモデルは、この「構造化」の精度が8Bモデルとは比較にならないほど高いのが特徴です。

```python
import ollama
import json

def extract_ticket_info(text):
    # 構造化を強制するためのプロンプト
    prompt = f"""
    以下のテキストから「重要度(High/Mid/Low)」「期限」「担当者」「タスク概要」を抽出し、
    純粋なJSON形式で出力してください。余計な解説は不要です。

    テキスト:
    {text}
    """

    response = ollama.generate(
        model="qwen2.5:27b",
        prompt=prompt,
        format="json" # OllamaのJSONモードを有効化
    )

    try:
        # 文字列を辞書オブジェクトに変換
        data = json.loads(response['response'])
        return data
    except json.JSONDecodeError:
        return "JSONのパースに失敗しました"

# テストデータ
log_text = "昨日届いたメールによると、佐藤さんが来週の金曜日までにサーバーのバックアップ設定を終わらせる必要がある。緊急度はかなり高いらしい。"

result = extract_ticket_info(log_text)
print(json.dumps(result, indent=4, ensure_ascii=False))
```

このコードの肝は `format="json"` オプションです。
これはOllama側で出力をJSONに強制する機能で、プログラマが後続の処理でデータを扱いやすくするための必須設定です。
27Bモデルであれば、「緊急度はかなり高い」という曖昧な表現を「High」と正しくマッピングする能力を持っています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Error: pull model manifest... | ネットワーク不安定またはモデル名ミス | `ollama list` で確認し、モデル名を再確認 |
| 動作が異常に重い | VRAM不足によるメインメモリ使用 | 量子化ビット数の低いモデルを選択する |
| Pythonから接続できない | Ollamaサーバーが起動していない | ターミナルで `ollama serve` を実行 |

## 次のステップ

この記事で、27Bクラスの強力なローカルLLMをPythonから自在に操る基盤が整いました。
次に挑戦すべきは、ローカル環境での「RAG（検索拡張生成）」の構築です。
今回構築したQwen環境と、ベクターデータベース（ChromaDBやQdrant）を組み合わせれば、社外秘のドキュメントを一切クラウドに上げることなく、自社専用のAIチャットボットが作れます。

また、27Bモデルは推論能力が高いため、LangChainの `Agent` 機能を使って「必要に応じてPythonコードを自ら生成し、実行して計算結果を返す」という自律型エージェントの実験にも最適です。
まずは、自分の過去のメール履歴やメモ帳をテキスト化し、Step 4のスクリプトに流し込んで、自分専用のデータベースを構築することから始めてみてください。
クラウドAPIの課金タイマーを気にせず、何万回でも試行錯誤できるのがローカルLLM最大の醍醐味です。

## よくある質問

### Q1: RTX 4060 (8GB) しか持っていませんが、動かす方法はありますか？

27Bモデルを8GBで動かすのは、どんなに量子化しても厳しいです。動作したとしても、1秒間に0.5文字程度の速度になり、ストレスで使い物になりません。8GB環境であれば、Qwen 2.5の7Bモデルを強く推奨します。7Bでも十分賢いです。

### Q2: 27Bモデルを動かしている間、PCで他の作業（ゲームなど）はできますか？

VRAMをほぼ占有するため、グラフィック負荷の高い作業やゲームは同時に行えません。画面描画がカクついたり、最悪の場合ドライバがクラッシュします。推論専用のサブ機を用意するか、作業をしない時間帯にバッチ処理させるのが私流の運用です。

### Q3: 商用利用は可能ですか？

Qwen 2.5シリーズは、AlibabaがApache 2.0ライセンス（またはそれに準ずる許諾）で公開しており、商用利用が可能です。ただし、モデルサイズが大きいため、商用サービスとして公開する場合は、Hugging Face Inference Endpointsなどのホスティング検討が必要になるでしょう。

---

## あわせて読みたい

- [ローカルLLM Qwen 2.5 Coder 使い方](/posts/2026-05-17-local-qwen-coder-html-canvas-tutorial/)
- [Qwen 2.5 27B 使い方 入門：24GB VRAMでGPT-4級のコード生成環境を構築する方法](/posts/2026-04-24-qwen-2-5-27b-local-python-guide/)
- [Qwen 3.6 27B 使い方 | ローカルLLM環境構築と量子化モデル比較ガイド](/posts/2026-04-28-qwen-36-27b-gguf-quantization-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 4060 (8GB) しか持っていませんが、動かす方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "27Bモデルを8GBで動かすのは、どんなに量子化しても厳しいです。動作したとしても、1秒間に0.5文字程度の速度になり、ストレスで使い物になりません。8GB環境であれば、Qwen 2.5の7Bモデルを強く推奨します。7Bでも十分賢いです。"
      }
    },
    {
      "@type": "Question",
      "name": "27Bモデルを動かしている間、PCで他の作業（ゲームなど）はできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "VRAMをほぼ占有するため、グラフィック負荷の高い作業やゲームは同時に行えません。画面描画がカクついたり、最悪の場合ドライバがクラッシュします。推論専用のサブ機を用意するか、作業をしない時間帯にバッチ処理させるのが私流の運用です。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用は可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Qwen 2.5シリーズは、AlibabaがApache 2.0ライセンス（またはそれに準ずる許諾）で公開しており、商用利用が可能です。ただし、モデルサイズが大きいため、商用サービスとして公開する場合は、Hugging Face Inference Endpointsなどのホスティング検討が必要になるでしょう。 ---"
      }
    }
  ]
}
</script>
