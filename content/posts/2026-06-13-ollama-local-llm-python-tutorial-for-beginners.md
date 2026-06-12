---
title: "Ollama 使い方 入門: 限られたGPU資産で実用的なローカルLLM環境を構築する方法"
date: 2026-06-13T00:00:00+09:00
slug: "ollama-local-llm-python-tutorial-for-beginners"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Llama 3.1 入門"
  - "ローカルLLM Python"
  - "GPU VRAM 16GB"
---
**所要時間:** 約45分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- OllamaとPythonを組み合わせ、手元のPC（VRAM 8GB〜12GB程度）で高速に動作する「構造化データ抽出スクリプト」を作ります。
- テキストから特定の情報（日付、金額、重要事項など）を抜き出し、JSON形式で保存する実務的なツールです。
- 前提知識: Pythonの基本的な読み書きができること、ターミナル（コマンドプロンプト）の基本操作。
- 必要なもの: NVIDIA製GPU（VRAM 8GB以上推奨）またはApple Silicon搭載Mac（RAM 16GB以上推奨）。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載で最も安価。ローカルLLM入門においてこれ以上の選択肢はない</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

「ローカルLLMは富豪の遊びになった」という意見がRedditで話題ですが、エンジニアが実務で使う分には、まだ民主主義は生きています。
結論から言うと、今の基準点は「VRAM 16GB」です。
RTX 4060 Ti 16GB版（約7万円）があれば、Llama 3.1 8Bクラスを4-bit量子化で動かしても、レスポンス速度は毎秒50〜80トークン出ます。
これは人間が読む速度を遥かに超えており、RAG（外部知識参照）などのバックエンド処理には十分すぎる性能です。

VRAM 8GBのノートPCでも動作はしますが、モデルの一部がメインメモリ（RAM）に溢れ、速度が1/10以下に低下する「オフロードの壁」にぶつかります。
もしこれから機材を買うなら、RTX 4060 Ti 16GBか、中古のRTX 3090 24GB、Macならメモリ32GB以上のモデルを強く推奨します。
API料金は一切かかりません。電気代とハードウェア代のみの買い切り型です。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、llama.cpp、LM Studio、vLLMなど多岐にわたります。
その中で私が「Ollama」を勧める理由は、依存関係の管理が圧倒的に楽だからです。
ライブラリのバージョン競合で1日溶かす必要はありません。

また、APIサーバーとしての機能が標準で備わっているため、PythonからOpenAI互換の形式ですぐに呼び出せます。
「動かすまで」に1分、「アプリに組み込むまで」に5分。
このスピード感が、実務でLLMを試行錯誤する際には不可欠です。

## Step 1: 環境を整える

まずはエンジンのインストールです。
公式サイト（ollama.com）からインストーラーをダウンロードしてください。

```bash
# macOS/Linuxの場合（コマンド一つでインストール可能）
curl -fsSL https://ollama.com/install.sh | sh

# インストール確認とモデルのダウンロード
ollama run llama3.1:8b
```

`ollama run llama3.1:8b`を実行すると、約4.7GBのモデルファイルがダウンロードされます。
なぜLlama 3.1 8Bなのか。それは、現時点で「日本語能力」「論理的思考」「軽量さ」のバランスが最も優れているからです。
内部的には4-bit量子化（GGUF形式）が使われており、本来16GB必要なVRAM消費を5GB程度まで抑えています。

落とし穴:
Windows環境でWSL2を使っている場合、GPUのパススルー設定が正しくないとCPU実行になり、極端に遅くなります。
タスクマネージャーの「専用GPUメモリ」が消費されているか必ず確認してください。
動かない場合は、NVIDIA公式のCUDAドライバが最新かチェックが必要です。

## Step 2: 基本の設定

Pythonから制御するためのライブラリを準備します。
直接HTTPリクエストを投げても良いですが、公式ライブラリを使うのが最も安全です。

```bash
pip install ollama pydantic
```

次に、プロジェクトディレクトリを作成し、環境を初期化します。
APIキーは不要ですが、将来的にクラウドAIと切り替える可能性を考え、エンドポイントURLなどは定数化しておきます。

```python
import ollama
import json

# ローカルサーバーの接続確認
try:
    models = ollama.list()
    print("接続成功。利用可能なモデル:", [m['name'] for m in models['models']])
except Exception as e:
    print(f"Ollamaが起動していない可能性があります: {e}")
```

「なぜpydanticを入れたのか」と疑問に思うかもしれません。
LLMの出力をそのまま画面に出すだけなら不要ですが、システムに組み込むなら「型定義」が必須だからです。
AIの気まぐれな回答を、プログラムが扱える厳格なデータ構造に変換する準備です。

## Step 3: 動かしてみる

まずは最小限のコードで、日本語の指示が通るかテストします。

```python
response = ollama.chat(model='llama3.1:8b', messages=[
  {
    'role': 'user',
    'content': 'ローカルLLMのメリットを3行で教えて。',
  },
])

print(response['message']['content'])
```

### 期待される出力

```
1. データが外部に送信されないため、高いセキュリティを確保できる。
2. API料金を気にせず、大量のテキスト処理を低コストで実行できる。
3. オフライン環境でも動作し、カスタマイズやモデルの入れ替えが自由。
```

結果の読み方:
`response`オブジェクトには、生成にかかった時間やトークン数も含まれています。
実務では`total_duration`を確認し、1つのリクエストに何秒かかっているかを計測してください。
3秒以内なら対話型アプリに、10秒以上かかるならバッチ処理に向いています。

## Step 4: 実用レベルにする

ここからが本番です。
単なるチャットではなく、未構造のテキスト（議事録やメール）から、プログラムで扱いやすいJSONデータを抽出するスクリプトを書きます。

```python
from pydantic import BaseModel
from typing import List, Optional

# 抽出したいデータの構造を定義
class MeetingSummary(BaseModel):
    date: str
    participants: List[str]
    decisions: List[str]
    next_action: Optional[str]

def extract_structured_data(text: str):
    prompt = f"""
    以下のテキストから会議の要約を抽出し、必ずJSON形式で出力してください。
    余計な説明は一切不要です。

    テキスト:
    {text}
    """

    # format='json' を指定することで、Ollama側にJSON出力を強制する
    response = ollama.chat(
        model='llama3.1:8b',
        messages=[{'role': 'user', 'content': prompt}],
        format='json'
    )

    return response['message']['content']

# テストデータ
raw_text = """
2024年10月15日の打ち合わせ。参加者は田中、佐藤、鈴木。
次回のキャンペーン予算を50万円に決定した。
佐藤さんは来週までにバナーのラフ案を作成すること。
"""

result_json = extract_structured_data(raw_text)
print(result_json)

# Pydanticでバリデーション
parsed_data = MeetingSummary.model_validate_json(result_json)
print(f"日付: {parsed_data.date}")
print(f"ネクストアクション: {parsed_data.next_action}")
```

なぜ`format='json'`を使うのか。
これを使わないと、LLMは「はい、JSON形式で出力しますね：」といった余計な枕詞を付けてしまい、`json.loads`でエラーになります。
Ollamaはこの出力を強制的に制御してくれるため、パースエラーの確率を劇的に下げられます。

実務での拡張:
このスクリプトをループで回せば、数千件のメール履歴から特定の情報を抜き出すクローラーが完成します。
外部API（OpenAIなど）を使えば数万円かかる処理も、ローカルなら電気代の数十円で済みます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Error: model not found` | 指定したモデルがDLされていない | `ollama pull llama3.1:8b` を実行 |
| 生成速度が極端に遅い（1文字/秒） | VRAM不足でCPU推論になっている | モデルサイズを下げる（4b等）か、不要なアプリを閉じてVRAMを空ける |
| JSONが壊れている | モデルの性能限界または指示不足 | プロンプトに「JSONのみ出力せよ」と強調し、`format='json'`オプションを併用する |

## 次のステップ

この記事の内容ができるようになったら、次は「RAG（検索拡張生成）」に挑戦してください。
ローカルLLMの真価は、自社の社外秘ドキュメントや個人の膨大なメモを読み込ませたときに発揮されます。
`LangChain`や`LlamaIndex`といったライブラリを使えば、今回のスクリプトをベースに「自分の知識をすべて知っているAIアシスタント」を作れます。

また、ハードウェアに限界を感じたら、Quantization（量子化）の深掘りをしてください。
GGUF形式のQ4_K_M（4ビット）が標準ですが、さらに圧縮したQ2_Kなどは驚くほど低スペックで動きます。
どこまで知能を削って速度を稼ぐか、そのトレードオフを見極めるのがローカルLLM職人の醍醐味です。

## よくある質問

### Q1: AMDのGPUでも動きますか？

動きます。OllamaはAMDのROCmをサポートしています。ただし、NVIDIAのCUDAに比べるとセットアップの難易度が少し高く、ライブラリの対応も一歩遅れる傾向にあります。今から買うならNVIDIA一択です。

### Q2: 13Bや70Bの大きなモデルを動かしたい場合は？

VRAMが足りない場合、Ollamaは自動的にシステムメモリ（RAM）を使いますが、速度は絶望的に遅くなります。70Bクラスを実用速度で動かすなら、RTX 3090/4090を2枚挿しにするか、Mac Studioの128GB以上のモデルが必要です。

### Q3: 商用利用しても大丈夫ですか？

Llama 3.1などのモデルは、Metaが定める許諾条件（月間アクティブユーザー数7億人未満など）の範囲内で商用利用可能です。ただし、モデルごとにライセンスが異なるため、必ず利用前に各モデルの配布ページを確認してください。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [Local LLM 使い方 入門：OllamaとPythonで自分専用のAIアシスタントを作る方法](/posts/2026-04-10-local-llm-ollama-python-tutorial-llama3/)
- [Qwen2.5をローカル環境で動かし、API料金を気にせずコード生成を自動化するPythonスクリプトを作る方法](/posts/2026-05-09-qwen-2-5-coder-local-python-guide/)
- [ローカルLLM Qwen 2.5 Coder 使い方](/posts/2026-05-17-local-qwen-coder-html-canvas-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "AMDのGPUでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きます。OllamaはAMDのROCmをサポートしています。ただし、NVIDIAのCUDAに比べるとセットアップの難易度が少し高く、ライブラリの対応も一歩遅れる傾向にあります。今から買うならNVIDIA一択です。"
      }
    },
    {
      "@type": "Question",
      "name": "13Bや70Bの大きなモデルを動かしたい場合は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "VRAMが足りない場合、Ollamaは自動的にシステムメモリ（RAM）を使いますが、速度は絶望的に遅くなります。70Bクラスを実用速度で動かすなら、RTX 3090/4090を2枚挿しにするか、Mac Studioの128GB以上のモデルが必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用しても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Llama 3.1などのモデルは、Metaが定める許諾条件（月間アクティブユーザー数7億人未満など）の範囲内で商用利用可能です。ただし、モデルごとにライセンスが異なるため、必ず利用前に各モデルの配布ページを確認してください。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>
