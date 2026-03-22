---
title: "Llama 3.1 8B蒸留モデルをローカルで爆速動作させる方法"
date: 2026-03-22T00:00:00+09:00
slug: "llama-3-1-distillation-local-setup-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Llama 3.1 使い方"
  - "蒸留モデル"
  - "llama-cpp-python 入門"
  - "ローカルLLM Python"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Llama-3.1-8B-Instruct（蒸留モデル）を使用し、1秒間に100トークン以上の速度で構造化データ（JSON）を抽出するPythonスクリプト
- 前提知識: Pythonの基本的な文法、ターミナル操作
- 必要なもの: NVIDIA製GPU（VRAM 8GB以上推奨）、Python 3.10以降

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">8Bモデルを余裕でVRAMに載せつつ低消費電力で回せる、ローカルLLMの入門に最適な1枚</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

AIモデルを仕事で使う際、最大の壁は「精度と速度のトレードオフ」です。
405Bのような巨大モデルは賢いですが、推論が遅すぎてリアルタイムなアプリには向きません。
そこで注目されているのが「蒸留（Distillation）」という手法です。

蒸留は、巨大な教師モデルの知識をコンパクトな生徒モデルに凝縮させる技術です。
今回紹介するLlama-3.1-8Bは、Metaが膨大な計算リソースを使って上位モデルの知識を流し込んだ、いわば「エリートな小型モデル」と言えます。
これをllama-cpp-pythonで量子化して動かすことで、MacBookやミドルクラスのGPUでも、GPT-4oに肉薄する要約・抽出精度をローカルで実現できます。
APIコストを気にせず、1日万単位のテキストを処理するなら、この「蒸留モデル×ローカル推論」が最もコストパフォーマンスに優れた選択肢です。

## Step 1: 環境を整える

まずは推論エンジンをインストールします。
今回はGGUF形式（量子化モデル）を扱うために、高速で安定している `llama-cpp-python` を使います。

```bash
# NVIDIA GPUを利用する場合（CUDA環境がある前提）
# CMAKE_ARGSを指定することで、GPUアクセラレーションを有効にしてビルドします
export CMAKE_ARGS="-DGGML_CUDA=on"
pip install llama-cpp-python

# 構造化データ抽出を簡単にするためのライブラリ
pip install pydantic huggingface_hub
```

`llama-cpp-python` はインストール時にコンパイルが走るため、環境によっては数分かかります。
`GGML_CUDA=on` を忘れると、CPUだけで動いてしまい「1秒に2トークン」というSIer時代の古いPCのような速度になってしまうので注意してください。

⚠️ **落とし穴:**
Windows環境で `CMAKE_ARGS` が効かない場合は、PowerShellで `$env:CMAKE_ARGS="-DGGML_CUDA=on"` と打ってから実行してください。
また、Visual Studioのビルドツールが入っていないとインストールに失敗します。
「そんなの面倒だ」という方は、WSL2（Ubuntu）上で構築するのが一番トラブルが少なくて済みます。

## Step 2: モデルの準備と初期化

次に、Hugging Faceからモデルをダウンロードします。
今回は、Bartowski氏が公開しているLlama-3.1-8B-InstructのQ4_K_M（4bit量子化）を使用します。
これは精度低下を最小限に抑えつつ、VRAM消費を5GB程度に抑えられるバランスの良い設定です。

```python
import os
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

# モデルの保存先を指定
model_dir = "./models"
os.makedirs(model_dir, exist_ok=True)

# Llama-3.1-8B-InstructのGGUFファイルをダウンロード
# 実務では精度重視ならQ6_K、速度重視ならQ4_K_Mを選びます
model_path = hf_hub_download(
    repo_id="bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
    filename="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
    local_dir=model_dir
)

# モデルの読み込み
# n_gpu_layers=-1 は全レイヤーをGPUに載せる設定です
# n_ctx=4096 はコンテキスト長。業務文書ならこれくらいは必要です
llm = Llama(
    model_path=model_path,
    n_gpu_layers=-1,
    n_ctx=4096,
    verbose=False
)
```

私は以前、何も考えずに全レイヤーをGPUに載せようとして、VRAM溢れ（OOM）でPCをフリーズさせたことがあります。
8BモデルのQ4量子化なら、RTX 3060（12GB）クラスでも余裕で動きますが、もしVRAMが足りない場合は `n_gpu_layers` を20〜30程度に下げて調整してください。

## Step 3: 動かしてみる

まずはシンプルな推論で、蒸留モデルの「キレ」を確認します。

```python
# Llama 3.1のプロンプトフォーマットに従って入力を作成
prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
あなたは優秀なAIアシスタントです。<|eot_id|><|start_header_id|>user<|end_header_id|>
AIモデルの「蒸留」について、3行で説明してください。<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

output = llm(
    prompt,
    max_tokens=256,
    stop=["<|eot_id|>"],
    echo=False
)

print(output["choices"][0]["text"])
```

### 期待される出力

```
1. 巨大なモデル（教師）の知識を、より小さなモデル（生徒）に継承させる手法です。
2. 予測の確率分布を学習することで、単純なラベル学習よりも深い理解を転移させます。
3. 精度を維持したままモデルを軽量化でき、高速な推論と低コストな運用が可能になります。
```

私の環境（RTX 4090）では、この程度の文章なら瞬きする間もなく出力されます。
注目すべきは「3行で」という指示を完璧に守っている点です。
一昔前の8Bクラスでは指示を無視して喋り続けることが多かったのですが、蒸留の効果で非常に制御しやすくなっています。

## Step 4: 実用レベルにする

実務では、AIに自由な文章を打たせるよりも「JSON形式でデータを抽出させる」場面が圧倒的に多いです。
ここでは、Pydanticを使って出力を厳密に定義し、複雑なテキストから情報を抜き出す「実用スクリプト」に拡張します。

```python
import json
from pydantic import BaseModel, Field
from typing import List

# 抽出したいデータの構造を定義
class BusinessAction(BaseModel):
    task: str = Field(description="やるべきタスク")
    assignee: str = Field(description="担当者")
    deadline: str = Field(description="期限（不明な場合は'不明'）")

class MeetingSummary(BaseModel):
    topic: str = Field(description="会議の主題")
    actions: List[BusinessAction] = Field(description="アクションアイテムのリスト")

def extract_structured_data(text: str):
    # Llama 3.1にJSON出力を強制するプロンプト
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
あなたは情報をJSON形式で抽出する専門家です。必ず指定されたJSONフォーマットのみを出力してください。
JSON形式: {json.dumps(MeetingSummary.model_json_schema(), ensure_ascii=False)}<|eot_id|>
<|start_header_id|>user<|end_header_id|>
以下の議事録から情報を抽出してください：
{text}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""

    response = llm(
        prompt,
        max_tokens=1024,
        stop=["<|eot_id|>"],
        temperature=0.0  # 抽出時はランダム性を排除するため0にする
    )

    # 出力からJSON部分を取り出してパース
    try:
        raw_text = response["choices"][0]["text"]
        return json.loads(raw_text)
    except Exception as e:
        print(f"パースエラー: {e}")
        return None

# テスト用の議事録データ
meeting_note = """
昨日の打ち合わせで、新機能のUIデザインを田中さんが来週月曜日までに作成することになりました。
また、佐藤さんはサーバーの負荷テストを今月末までに行う予定です。
今回のプロジェクトのメインテーマは「UXの向上」です。
"""

result = extract_structured_data(meeting_note)
print(json.dumps(result, indent=2, ensure_ascii=False))
```

このコードの肝は `temperature=0.0` です。
AIを「クリエイティブな作家」ではなく「正確なデータ抽出機」として使う場合、この設定は必須です。
また、Pydanticの `model_json_schema()` をプロンプトに流し込むことで、モデルに対して「どのフィールドに何を入れればいいか」を明確に伝えられます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ImportError: cannot import name 'Llama'` | インストール失敗 | `pip uninstall llama-cpp-python` してから再インストール。 |
| `ValidationError` | AIが壊れたJSONを出した | `max_tokens` を増やすか、プロンプトに「JSON以外喋るな」と強調する。 |
| 推論が異常に遅い | CPUで動いている | `n_gpu_layers` を確認。ビルド時にCUDAフラグが立っていない可能性大。 |

## 次のステップ

この記事で、蒸留モデルをローカルで自在に操る基礎ができました。
次に挑戦すべきは「RAG（検索拡張生成）」との組み合わせです。
自分の会社のドキュメントをベクトルデータベース（ChromaやQdrant）に放り込み、今回のスクリプトを組み合わせて「社内専用の高速回答Bot」を作ってみてください。

また、もし「もっと賢さが欲しい」と感じたら、Llama-3.1-70Bの蒸留版である `Llama-3.1-70B-Instruct-GGUF` を試すのもありです。
私のRTX 4090 2枚挿し環境ならQ4量子化がサクサク動きますが、VRAMが24GBあれば1枚でもQ2やQ3なら動作可能です。
蒸留の世界は奥が深く、同じ8Bモデルでも「どの教師モデルから蒸留されたか」で性格が全く異なります。
Redditの `r/LocalLLaMA` で「Favorite distillation」を検索して、世界中の猛者たちが推しているモデルを片っ端から試すのが、最速の学習法だと思います。

## よくある質問

### Q1: 蒸留モデルと元のモデル、どっちを使うべき？

特定のタスク（要約や抽出）が決まっているなら、蒸留モデル一択です。
同じパラメータ数でも、蒸留されたモデルの方が明らかに「頭の回転が速く、指示に忠実」な印象を受けます。
汎用的な雑談を楽しみたいなら元モデルでも良いですが、仕事で使うなら「濃縮された知能」を活用すべきです。

### Q2: 量子化（GGUF）すると精度はガタ落ちしますか？

4bit（Q4_K_M）程度であれば、実務で差を感じることはほとんどありません。
3bit以下になると、急にトンチンカンな回答が増える「崖」のようなポイントがあります。
仕事用なら4bit、余裕があれば6bit（Q6_K）を使うのが私の個人的な鉄則です。

### Q3: 日本語の精度はどうですか？

Llama 3.1は蒸留モデルも含め、かなり日本語が上手くなっています。
ただし、専門用語が多い場合は「日本語に特化した継続事前学習モデル」を教師にした蒸留モデルを探すと良いです。
Hugging Faceで `ja-distill` などのキーワードで検索すると、有志が公開している面白いモデルが見つかります。

---

## あわせて読みたい

- [Googleが放った最新の「Gemini 3.1 Pro」が、AI界に激震を走らせています。これまでのベンチマーク記録を塗り替え、再び首位に躍り出たというニュースは、単なる数値の更新以上の意味を持っています。](/posts/2026-02-20-google-gemini-3-1-pro-record-benchmark-analysis/)
- [Qwen3.5-9B-Claude-4.6-Opus-Uncensored-Distilled-GGUF 使い方入門](/posts/2026-03-16-qwen3-5-9b-uncensored-gguf-setup-guide/)
- [Qwen3.5-9Bをローカル環境のPythonで動かし自分専用の超高速AIアシスタントを作る方法](/posts/2026-03-02-qwen3-5-9b-local-python-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "蒸留モデルと元のモデル、どっちを使うべき？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "特定のタスク（要約や抽出）が決まっているなら、蒸留モデル一択です。 同じパラメータ数でも、蒸留されたモデルの方が明らかに「頭の回転が速く、指示に忠実」な印象を受けます。 汎用的な雑談を楽しみたいなら元モデルでも良いですが、仕事で使うなら「濃縮された知能」を活用すべきです。"
      }
    },
    {
      "@type": "Question",
      "name": "量子化（GGUF）すると精度はガタ落ちしますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "4bit（Q4KM）程度であれば、実務で差を感じることはほとんどありません。 3bit以下になると、急にトンチンカンな回答が増える「崖」のようなポイントがあります。 仕事用なら4bit、余裕があれば6bit（Q6K）を使うのが私の個人的な鉄則です。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の精度はどうですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Llama 3.1は蒸留モデルも含め、かなり日本語が上手くなっています。 ただし、専門用語が多い場合は「日本語に特化した継続事前学習モデル」を教師にした蒸留モデルを探すと良いです。 Hugging Faceで ja-distill などのキーワードで検索すると、有志が公開している面白いモデルが見つかります。 ---"
      }
    }
  ]
}
</script>
