---
title: "Qwen2.5とPythonで技術文書を自動で構造化データに変換するツールの作り方"
date: 2026-03-05T00:00:00+09:00
slug: "qwen25-python-local-llm-json-extraction"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen2.5 使い方"
  - "Ollama Python 連携"
  - "ローカルLLM 構造化データ抽出"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- ローカルLLMのQwen2.5を活用し、PDFやマークダウン形式の技術文書から特定の項目（作成日、技術スタック、アーキテクチャの要点など）を正確に抽出してJSON形式で保存するPythonスクリプトを作ります。
- 外部API（OpenAIなど）へデータを送信せず、すべて自分のPC内で完結させるため、機密性の高い社内ドキュメントも安全に処理できます。
- 前提知識として、Pythonの基本的な文法（変数、関数、pipでのライブラリインストール）を理解している必要があります。
- 必要なものは、16GB以上のメモリを搭載したPC（GPU推奨ですがCPUでも動作可能）とPython環境です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">ASUS RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載で、Qwen2.5の7B/14Bモデルをローカルで快適に動かすのに最適な1枚</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=ASUS%20NVIDIA%20RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FASUS%2520NVIDIA%2520RTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FASUS%2520NVIDIA%2520RTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

AlibabaのAIチームから主要メンバーが離脱したというニュースが話題ですが、実務家としての私の視点は異なります。株価や組織の動向とは裏腹に、彼らが残した「Qwen2.5」というモデル自体の完成度は、現在オープンソース界隈でLlama 3.1を凌駕する場面も多いほど極めて高いです。

特に日本語の処理能力と、指示に従って特定のフォーマット（JSONなど）で出力する能力が、同サイズの他モデルと比べて頭一つ抜けています。SIer時代、私は何千枚ものExcel設計書から項目を手動でデータベースに転記する虚無な作業を何度も見てきました。当時は正規表現で無理やり抽出していましたが、表記揺れに弱く限界がありました。

今回紹介する「Ollama」と「Qwen2.5」を組み合わせた手法は、それらの苦痛を過去のものにします。APIコストを気にせず、何万件もの文書をローカルで高速に処理できる点が最大のメリットです。

## Step 1: 環境を整える

まずは、ローカル環境でLLMを動かすためのエンジンである「Ollama」をインストールします。Dockerで構築する方法もありますが、GPUのパススルー設定で時間を溶かすのは本質的ではありません。インストーラーを使うのが最も確実です。

```bash
# Ollamaを公式サイト(https://ollama.com/)からダウンロードしてインストールした後、モデルをプルします
ollama run qwen2.5:7b
```

このコマンドは、Qwen2.5の70億パラメータモデルをダウンロードし、対話モードで起動します。7bモデルは、RTX 3060（12GB VRAM）程度の環境でも非常に軽快に動作します。

次に、PythonからOllamaを制御するためのライブラリと、データ構造を定義するためのPydanticをインストールします。

```bash
pip install ollama pydantic
```

⚠️ **落とし穴:**
Windows環境でGPUが認識されない場合、NVIDIAのドライバーが古いケースがほとんどです。また、WSL2経由で動かすよりも、現在はWindowsネイティブ版のOllamaを使ったほうが推論速度（トークン生成速度）が安定する傾向にあります。

## Step 2: 基本の設定

Pythonスクリプトを作成します。ここでは、抽出したいデータの形を定義します。LLMに「いい感じに抽出して」と頼むのではなく、あらかじめ型を定義しておくことが、システムとして組み込む際の絶対条件です。

```python
import os
import json
from pydantic import BaseModel, Field
from typing import List
import ollama

# 抽出したいデータの構造をクラスで定義
class TechSpec(BaseModel):
    project_name: str = Field(description="プロジェクト名")
    languages: List[str] = Field(description="使用されているプログラミング言語のリスト")
    database: str = Field(description="使用されているデータベース名")
    frameworks: List[str] = Field(description="使用されているフレームワークやライブラリ")
    summary: str = Field(description="システムの概要を30文字以内で要約")

# モデル名の定義。Qwen2.5-7bを使用。
# 精度を重視する場合は 14b や 32b に変更可能ですが、まずは 7b で試すのが定石です。
MODEL_NAME = "qwen2.5:7b"
```

各項目に`Field(description=...)`を添えるのがコツです。これがそのままLLMへの指示（プロンプト）の一部として機能し、抽出精度を劇的に向上させます。

## Step 3: 動かしてみる

定義した構造に基づいて、実際にテキストから情報を抜き出します。Qwen2.5は「JSONモード」をサポートしているため、出力が壊れるリスクを最小限に抑えられます。

```python
def extract_tech_info(text: str):
    prompt = f"以下の技術文書から情報を抽出し、指定されたJSON形式で出力してください。\n\n文書: {text}"

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {'role': 'system', 'content': 'あなたは優秀なテクニカルエディターです。必ず指定されたJSONフォーマットで回答してください。'},
            {'role': 'user', 'content': prompt},
        ],
        format=TechSpec.model_json_schema(), # Pydanticのスキーマを渡す
        options={'temperature': 0} # 決定論的な出力を得るために0に設定
    )

    return response['message']['content']

# テスト用のダミーテキスト
sample_text = """
次世代物流システム「ハコブネ」の開発について。
本プロジェクトでは、バックエンドにPython 3.11とFastAPIを採用し、
データベースにはPostgreSQLを利用します。
また、フロントエンドはTypeScriptとNext.jsで構築され、
キャッシュ戦略としてRedisを導入しています。
"""

result = extract_tech_info(sample_text)
print(result)
```

### 期待される出力

```json
{
  "project_name": "ハコブネ",
  "languages": ["Python", "TypeScript"],
  "database": "PostgreSQL",
  "frameworks": ["FastAPI", "Next.js", "Redis"],
  "summary": "次世代物流システムの開発プロジェクト"
}
```

Qwen2.5は日本語の文脈を正確に捉え、Redisをフレームワーク/ライブラリのカテゴリに分類するなど、賢い判断をしてくれます。`temperature`を0にするのは、同じ入力に対して常に同じ結果を出すためです。これはプログラムの一部として組み込む際に必須の設定です。

## Step 4: 実用レベルにする

実際の業務では、1つのテキストを処理して終わりではありません。大量のファイルが入ったフォルダを監視し、エラーが起きた際にリトライする仕組みが必要です。

特にローカルLLMは、稀にJSONのパースに失敗する出力を返すことがあります。そのため、Pydanticの`model_validate_json`を使って、プログラム側でバリデーションをかけるのが「仕事で使える」コードへの第一歩です。

```python
import time

def robust_extraction(text: str, retries: int = 3):
    for i in range(retries):
        try:
            raw_content = extract_tech_info(text)
            # LLMの出力をパースして、TechSpecクラスのインスタンスを作る
            validated_data = TechSpec.model_validate_json(raw_content)
            return validated_data.model_dump()
        except Exception as e:
            print(f"試行 {i+1} 回目: エラー発生 {e}。再試行します。")
            time.sleep(1)
    return None

# 実用的なバッチ処理の例
documents = [sample_text] # 実際にはファイルから読み込んだリスト
final_results = []

for doc in documents:
    data = robust_extraction(doc)
    if data:
        final_results.append(data)

# 結果をJSONファイルとして保存
with open("extracted_data.json", "w", encoding="utf-8") as f:
    json.dump(final_results, f, ensure_ascii=False, indent=2)

print(f"{len(final_results)} 件のデータを処理しました。")
```

このように、リトライ処理を入れることで、ローカルLLM特有の不安定さをカバーできます。私が過去に受けた機械学習案件でも、モデル自体の精度向上に時間をかけるより、こうした外側のガードレールをしっかり作る方が、最終的なシステムの信頼性は高まりました。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ollama.ResponseError: model not found` | モデルがダウンロードされていない | `ollama pull qwen2.5:7b` を実行してください。 |
| 抽出結果が空、または不正確 | プロンプトが曖昧 | `Field`の`description`をより具体的に書き換えてください。 |
| 処理速度が極端に遅い | CPUで動作している | PCにNVIDIA製GPUがある場合は、CUDAが認識されているか確認してください。 |

## 次のステップ

今回作成したスクリプトは、特定の構造を持ったデータを抽出する「情報の構造化」に特化しています。これをマスターした後は、LangChainなどのフレームワークを導入し、PDFからテキストを抽出する部分の自動化や、抽出したデータをベクトルデータベース（Chromaなど）に格納して検索できるようにする「RAG（検索拡張生成）」へと拡張してみてください。

また、Qwen2.5にはさらに高性能な32bや72bモデルも存在します。RTX 4090などの強力なGPUを持っているなら、ぜひモデルサイズを上げてみてください。7bでは抽出漏れがあった複雑な契約書や、難解な技術論文でも、驚くほどの精度で構造化できるようになります。

AIの開発チームに動きがあっても、公開されたモデルの価値は変わりません。むしろ、使い倒すノウハウを今のうちに蓄積しておくことが、今後のキャリアにおいて大きなアドバンテージになると私は確信しています。

## よくある質問

### Q1: 7bモデルだと精度が足りない場合はどうすればいいですか？

モデルのサイズを14bまたは32bに上げてください。Ollamaなら`ollama run qwen2.5:14b`と打つだけで変更可能です。ただし、14bは16GB以上の、32bは24GB以上のVRAMを持つGPUがないと動作が非常に遅くなります。

### Q2: 会社で使う際、プロンプトに機密情報を入れても大丈夫ですか？

はい、この方法は完全にオフラインで動作しているため、データがAlibabaや外部サーバーに送信されることはありません。ネットワークを切断した状態でも動作することを確認してみると、より安心できると思います。

### Q3: 日本語の文字化けが発生するのですが。

Pythonでファイルを扱う際は、必ず`encoding='utf-8'`を指定してください。特にWindowsのデフォルト（cp932）では、LLMが生成した多言語テキストを正しく保存できないケースが多々あります。

---

## あわせて読みたい

- [Qwen3.5-35B-A3BとAiderで爆速コーディング環境を構築する方法](/posts/2026-02-25-qwen35-35b-aider-local-ai-coding-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "7bモデルだと精度が足りない場合はどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデルのサイズを14bまたは32bに上げてください。Ollamaならollama run qwen2.5:14bと打つだけで変更可能です。ただし、14bは16GB以上の、32bは24GB以上のVRAMを持つGPUがないと動作が非常に遅くなります。"
      }
    },
    {
      "@type": "Question",
      "name": "会社で使う際、プロンプトに機密情報を入れても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、この方法は完全にオフラインで動作しているため、データがAlibabaや外部サーバーに送信されることはありません。ネットワークを切断した状態でも動作することを確認してみると、より安心できると思います。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の文字化けが発生するのですが。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Pythonでファイルを扱う際は、必ずencoding='utf-8'を指定してください。特にWindowsのデフォルト（cp932）では、LLMが生成した多言語テキストを正しく保存できないケースが多々あります。 ---"
      }
    }
  ]
}
</script>
