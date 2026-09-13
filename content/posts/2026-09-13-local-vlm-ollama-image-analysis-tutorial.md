---
title: "OllamaとLlama-3.2-Visionで大量の画像を自動タグ付け・構造化データ化するPythonスクリプトの作り方"
date: 2026-09-13T00:00:00+09:00
slug: "local-vlm-ollama-image-analysis-tutorial"
cover:
  image: "/images/posts/2026-09-13-local-vlm-ollama-image-analysis-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Llama-3.2-Vision"
  - "Ollama 使い方"
  - "ローカルLLM 画像認識"
  - "Python AI 自動化"
---
**所要時間:** 約35分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- ローカルPC内の画像フォルダをスキャンし、AI（Llama-3.2-Vision）がその内容を解析。
- 解析結果をJSON形式で保存し、検索やデータベース登録が可能な「構造化データ」を自動生成するPythonスクリプト。
- クラウドAPI（GPT-4o等）を一切使わず、完全オフラインで1枚あたり約1〜2秒（RTX 4090環境）で処理を完結させます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載で、Vision系LLMを安価かつ安定して動かせる現時点の最適解。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、Pythonの基本的な文法（変数、ループ、pipによるライブラリ追加）が理解できていることを想定しています。

## 先に確認するスペック・料金

ローカルLLM、特にVision系（画像認識）を動かすには、通常のLLMよりもVRAM（ビデオメモリ）の消費が激しい傾向にあります。
画像データはテキストよりもトークン消費量が多く、モデルによっては画像1枚で数千トークンを占有するためです。

最低でも **VRAM 12GB以上** を搭載したNVIDIA製GPU（RTX 3060 12GB / 4060 Ti 16GBなど）を推奨します。
VRAMが足りないと、処理が極端に遅くなる（CPU推論に切り替わる）か、メモリ不足（OOM）でクラッシュします。
Macユーザーであれば、メモリ16GB以上のApple Silicon（M2/M3/M4）搭載モデルで、かつUnified Memoryを活かせる構成が必須です。

ランニングコストは電気代のみです。
GPT-4oなどのAPIを使うと、画像1,000枚の解析で数千円から1万円程度の費用が発生しますが、ローカル環境なら完全無料です。
検証機を新調する場合、現時点ではRTX 4060 Ti 16GBが「最も安価に実用レベルのVLMを動かせる選択肢」となります。

## なぜこの方法を選ぶのか

現在、マルチモーダルモデル（VLM）をローカルで動かす手段は、Llama.cpp、AutoGPTQ、Ollamaなど複数あります。
その中でも「Ollama」を選ぶ理由は、環境構築の圧倒的な速さと、モデルの重み管理の容易さです。

InternVL2やQwen2-VLといった高性能なモデルも登場していますが、Llama-3.2-Visionは「精度のバランス」と「推論速度」において、2026年現在のローカル環境で最も安定しています。
また、Pythonライブラリとしての `ollama` が非常に洗練されており、APIを叩く感覚でローカル推論を実装できるため、業務システムへの組み込みが容易だからです。

## Step 1: 環境を整える

まずは推論エンジンとなるOllamaをインストールし、必要なモデルをローカルに落とします。

```bash
# Ollamaのインストール（公式サイトからインストーラーを実行後、コマンドラインで以下を叩く）
ollama pull llama3.2-vision

# Pythonライブラリのインストール
pip install ollama pillow
```

`ollama pull llama3.2-vision` は、約11B（またはその軽量版）のマルチモーダルモデルをダウンロードします。
`pillow` は、Pythonで画像サイズを最適化し、AIに渡す前の前処理を行うために使用します。

⚠️ **落とし穴:**
Ollamaのバージョンが古いと、Visionモデルの画像入力に対応していない場合があります。
必ず `ollama serve` を最新版にアップデートしてから実行してください。
また、GPUドライバ（CUDA）が古いと速度が10倍以上遅くなるため、最新のGame Ready/Studioドライバへの更新を強く推奨します。

## Step 2: 基本の設定

Pythonからモデルを呼び出すための初期設定を書きます。
ここでは、単に画像を渡すだけでなく、AIが「何を出力すべきか」を定義するシステムプロンプトが重要になります。

```python
import ollama
import os
import json
from PIL import Image
import io

# 使用するモデル名
MODEL_NAME = "llama3.2-vision"

def get_image_analysis(image_path, prompt):
    # 画像を開いてバイト列に変換
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Ollama APIの呼び出し
    response = ollama.generate(
        model=MODEL_NAME,
        prompt=prompt,
        images=[image_bytes],
        format="json", # 出力をJSONに強制する
        options={"temperature": 0.1} # 出力の安定性を高めるために低めに設定
    )
    return response['response']
```

`format="json"` を指定するのが実務上のポイントです。
これにより、AIが余計な解説文（「はい、この画像は〜」など）を出力せず、純粋なJSONデータのみを返すようになります。
また、`temperature` は 0.1 に設定します。画像解析において「創造性」は不要であり、事実に基づいた一貫性のある回答が必要だからです。

## Step 3: 動かしてみる

まずは1枚の画像で、正しくJSONが返ってくるかテストします。
カレントディレクトリに `sample.jpg` を用意して実行してください。

```python
test_prompt = """
この画像を解析して、以下のJSONフォーマットで返してください。
{
  "object_detected": ["物体名1", "物体名2"],
  "scene": "場所の説明",
  "dominant_color": "主要な色",
  "summary": "1行での説明"
}
"""

try:
    result = get_image_analysis("sample.jpg", test_prompt)
    print(result)

    # JSONとしてパースできるか確認
    parsed_data = json.loads(result)
    print(f"解析成功: {parsed_data['summary']}")
except Exception as e:
    print(f"エラーが発生しました: {e}")
```

### 期待される出力

```json
{
  "object_detected": ["laptop", "coffee cup", "notebook"],
  "scene": "office desk",
  "dominant_color": "white and brown",
  "summary": "A laptop and a coffee cup on a wooden desk in a bright office."
}
```

結果が返ってこない場合、VRAM不足でモデルがロードできていない可能性があります。
その場合は `ollama list` でモデルが正常に存在するか確認し、他のメモリを消費しているアプリ（ブラウザや別のAIツール）を閉じてください。

## Step 4: 実用レベルにする

実務では1枚ずつ手動で実行することはありません。
フォルダ内の全画像を自動走査し、リトライ処理と進行状況の保存機能を備えた「バッチ処理スクリプト」へと拡張します。
特に、大きな画像はAIが処理できない場合があるため、リサイズ処理を挟むのがプロの技です。

```python
def process_folder(input_folder, output_file):
    supported_exts = (".jpg", ".jpeg", ".png")
    results = []

    # 既存の結果があれば読み込む（途中から再開用）
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            results = json.load(f)

    processed_files = {r['file_name'] for r in results}

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(supported_exts) and filename not in processed_files:
            path = os.path.join(input_folder, filename)
            print(f"Processing: {filename}...")

            try:
                # 画像をリサイズ（VRAM節約と処理高速化のため）
                with Image.open(path) as img:
                    img.thumbnail((1024, 1024))
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG')
                    img_bytes = img_byte_arr.getvalue()

                response = ollama.generate(
                    model=MODEL_NAME,
                    prompt="Describe this image in detail for a searchable database.",
                    images=[img_bytes],
                    format="json"
                )

                analysis = json.loads(response['response'])
                results.append({
                    "file_name": filename,
                    "analysis": analysis
                })

                # 1枚ごとに保存（クラッシュ対策）
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)

            except Exception as e:
                print(f"Skip {filename} due to error: {e}")

# 実行
process_folder("./my_images", "analysis_results.json")
```

このスクリプトの肝は `img.thumbnail((1024, 1024))` です。
最近のスマホ写真は4K以上の解像度がありますが、VLM内部では固定解像度にリサイズされて処理されます。
事前にPython側でリサイズしてバイト列を小さくしておくことで、Ollamaへの転送負荷を減らし、推論の安定性を劇的に向上させることができます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ollama.ResponseError: model not found` | モデルのダウンロード失敗 | `ollama pull llama3.2-vision` を再実行する。 |
| `JSONDecodeError` | AIがJSON以外の文字を出力した | システムプロンプトで「JSONのみ返せ」と念押しし、`format="json"` を設定する。 |
| 推論が異様に遅い（数分かかる） | CPU推論になっている | VRAM不足。より小さいモデル（Moondream2等）を試すか、GPUのメモリを空ける。 |
| 画像が認識されない | 非対応形式または破損 | Pillowで一度開き、RGB形式のJPEGに変換してからAIに渡す。 |

## 次のステップ

このスクリプトが動いたら、次は「検索システム」への応用を考えてみてください。
生成されたJSONを **ChromaDB** や **Qdrant** などのベクトルデータベースに投入すれば、自然言語で「赤い車が写っている写真を探して」と指示してローカル画像を検索する「自作Googleフォト」が構築できます。

また、2026年現在のトレンドとしては、**InternVL2-Llama3-76B** などの巨大なVLMを、今回紹介したコードの `MODEL_NAME` を書き換えるだけで試すことができます。
精度に満足がいかない場合は、よりパラメータ数の多いモデルへスイッチしてみてください。
その際、RTX 4090 2枚挿しによるNVLink環境があれば、さらに高精度な解析を高速に回すことが可能になります。

## よくある質問

### Q1: Ollama以外のライブラリ（PyTorch等）で直接動かすのと何が違いますか？

Ollamaは内部で量子化（GGUF形式）を最適に行っているため、VRAM消費を抑えつつ高速に動作します。生のリポジトリからPyTorchで動かすと、VRAMを2倍以上消費することが多く、設定も複雑です。

### Q2: 1枚の画像に複数の質問をしたい場合は？

`ollama.chat` を使い、対話履歴を維持しながら質問を重ねる形式に書き換えてください。ただし、バッチ処理で構造化データを作る目的なら、1回のプロンプトですべての項目をJSONで答えさせる方が効率的です。

### Q3: 日本語のプロンプトでも正しく動きますか？

Llama-3.2-Visionは日本語をある程度理解しますが、解析精度は英語プロンプトの方が一段高いです。英語で出力させ、後から別のLLM（Llama-3.1等）で日本語訳するか、Deepl API等と連携させるのが実務での鉄板構成です。

---

## あわせて読みたい

- [Qwen 3.6 35B A3B 使い方 | ローカルLLMでプロ級のコード解析環境を作る方法](/posts/2026-05-11-qwen-36-35b-local-llm-code-review-guide/)
- [Qwen 2.5やGemma 2をローカル環境で高速に動かす方法](/posts/2026-04-29-how-to-setup-local-llm-qwen-python-ollama/)
- [ローカルLLM Qwen 2.5 Coder 使い方](/posts/2026-05-17-local-qwen-coder-html-canvas-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Ollama以外のライブラリ（PyTorch等）で直接動かすのと何が違いますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaは内部で量子化（GGUF形式）を最適に行っているため、VRAM消費を抑えつつ高速に動作します。生のリポジトリからPyTorchで動かすと、VRAMを2倍以上消費することが多く、設定も複雑です。"
      }
    },
    {
      "@type": "Question",
      "name": "1枚の画像に複数の質問をしたい場合は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ollama.chat を使い、対話履歴を維持しながら質問を重ねる形式に書き換えてください。ただし、バッチ処理で構造化データを作る目的なら、1回のプロンプトですべての項目をJSONで答えさせる方が効率的です。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語のプロンプトでも正しく動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Llama-3.2-Visionは日本語をある程度理解しますが、解析精度は英語プロンプトの方が一段高いです。英語で出力させ、後から別のLLM（Llama-3.1等）で日本語訳するか、Deepl API等と連携させるのが実務での鉄板構成です。 ---"
      }
    }
  ]
}
</script>
