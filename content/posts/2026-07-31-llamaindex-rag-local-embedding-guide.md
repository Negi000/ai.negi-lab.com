---
title: "PythonとLlamaIndexでRAGパイプラインを自作する方法"
date: 2026-07-31T00:00:00+09:00
slug: "llamaindex-rag-local-embedding-guide"
cover:
  image: "/images/posts/2026-07-31-llamaindex-rag-local-embedding-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "LlamaIndex 使い方"
  - "RAG 自作 Python"
  - "multilingual-e5-small 評価"
  - "ローカルLLM 検索実装"
---
**所要時間:** 約45分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 手元のPDFファイルを読み込み、その内容に基づいて正確に回答するRAG（検索拡張生成）チャットスクリプトを作成します。
- 検索エンジン部分を自分のPC内で動かす「ローカル埋め込み」を採用し、APIコストを抑えつつ日本語の検索精度を担保する構成です。
- Pythonの基礎（変数、関数の実行、ライブラリのインストール）さえ理解していれば、完走できるように設計しました。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLMや埋め込みモデルの並列処理に最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

RAGの実装において、最も重要なのは「埋め込み（Embedding）モデル」をどこで動かすかです。OpenAIのAPI（text-embedding-3-small等）を使うのが一番手軽ですが、ファイルを読み込むたび、検索するたびに課金が発生します。私は実務において、この部分はローカルモデルで運用することを推奨しています。

**ハードウェア要件:**
- **メモリ（RAM）:** 16GB以上を推奨します。今回使用する軽量モデル `multilingual-e5-small` は数百MBのメモリしか消費しませんが、OSやPython環境全体を考慮すると8GBでは心許ないです。
- **GPU:** あれば高速化（レスポンスが0.2秒ほど向上）しますが、今回の構成はCPUだけでも十分実用的な速度（1秒以内）で動作します。

**料金目安:**
- **OpenAI API:** 月額基本料なしの従量課金。この記事の内容を試すだけなら1ドルもかかりません。
- **ローカルモデル:** 無料。Hugging Faceからオープンソースのモデルをダウンロードして使います。

もしMacユーザーなら、M2/M3チップを搭載したメモリ16GB以上のモデルであれば、この手のAI実装は非常に快適に動作します。Windowsの場合は、RTX 3060（VRAM 12GB以上）を積んでおけば、将来的に大規模なローカルLLMを動かす際にも困りません。

## なぜこの方法を選ぶのか

RAGの実装には、有名な「LangChain」という選択肢もあります。しかし、私はあえて「LlamaIndex」を推奨します。理由はシンプルで、LangChainは多機能すぎて「今何が起きているか」がブラックボックスになりやすいからです。

LlamaIndexは「データとLLMを繋ぐ」ことに特化しており、たった数行のコードでデータの読み込みからベクトル化までを完結できます。特に今回の「ローカルで検索、OpenAIで回答」というハイブリッド構成を組む場合、LlamaIndexの直感的なインターフェースが開発効率を最大化してくれます。

## Step 1: 環境を整える

まずはプロジェクト用のディレクトリを作成し、必要なライブラリをインストールします。

```bash
mkdir my-rag-project
cd my-rag-project
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# LlamaIndex本体と、OpenAI・HuggingFace用の拡張機能をインストール
pip install llama-index llama-index-embeddings-huggingface llama-index-llms-openai python-dotenv
```

`llama-index-embeddings-huggingface` は、OpenAIの代わりに自分のPC上で「文章をベクトル（数値の列）に変換」するために必要です。`python-dotenv` は、APIキーなどの機密情報を安全に扱うために使用します。

⚠️ **落とし穴:**
ライブラリのインストール中に「pydanticのバージョンエラー」が出ることがあります。LlamaIndexは内部でPydanticを多用しているため、もしエラーが出た場合は `pip install "pydantic<2.0"` を試すか、逆に最新版にアップデートしてください。2024年現在の主流はV2系ですが、古い記事のコードをコピペするとここで詰まります。

## Step 2: 基本の設定

プロジェクトのルートディレクトリに `.env` ファイルを作成し、OpenAIのAPIキーを記述します。

```text
OPENAI_API_KEY=sk-xxxx...（あなたのキー）
```

次に、メインのスクリプト `app.py` を作成し、初期設定を書きます。ここでは「どのモデルを使って検索し、どのモデルで回答するか」を定義します。

```python
import os
from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# .envファイルを読み込む
load_dotenv()

# 1. LLMの設定（回答生成用）
# 賢さとコスパのバランスが良い gpt-4o-mini を選択します
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)

# 2. Embeddingモデルの設定（検索用）
# 日本語に強く、軽量な intfloat/multilingual-e5-small を使用します
# これにより、検索のたびにOpenAIへ課金されるのを防ぎます
Settings.embed_model = HuggingFaceEmbedding(
    model_name="intfloat/multilingual-e5-small"
)

print("設定が完了しました。モデルのロードに成功しました。")
```

`temperature=0.1` に設定しているのは、RAGにおいてLLMの「創作（ハルシネーション）」を抑えるためです。事実に基づいた回答を求める場合は、0に近い値にするのが鉄則です。

## Step 3: 動かしてみる

RAGの肝となる「ドキュメントの読み込み」と「検索・回答」を実装します。まずはテスト用のデータを準備してください。`data` というフォルダを作り、その中に適当なPDFファイルを1つ入れておきましょう（例：社内規定、ガジェットの説明書など）。

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# dataフォルダ内のドキュメントをすべて読み込む
documents = SimpleDirectoryReader("./data").load_data()

# 読み込んだデータをベクトル化してインデックス（索引）を作成
# ここで multilingual-e5-small が走り、文章が数値化されます
index = VectorStoreIndex.from_documents(documents)

# 検索エンジンを起動
query_engine = index.as_query_engine()

# 実際に質問してみる
response = query_engine.query("このドキュメントの要点を3つで教えてください。")

print("--- 回答 ---")
print(response)
```

### 期待される出力

```
--- 回答 ---
1. 本ドキュメントは、2024年度の新しいリモートワーク規定について説明しています。
2. コアタイムは11:00〜15:00とし、週に最低2日の出社を推奨しています。
3. 通信費の補助として月額5,000円が支給されます。
```

結果が出ない、あるいは「知識がありません」といった回答が返ってくる場合は、PDFのテキストが「画像」として認識されていないか確認してください。LlamaIndexは標準ではOCR（文字認識）を行わないため、テキストデータとして抽出可能なPDFである必要があります。

## Step 4: 実用レベルにする

今のコードには致命的な欠点があります。スクリプトを動かすたびに「PDFのベクトル化」を実行している点です。PDFが100枚あれば、起動だけで数分待たされることになります。実務では、一度作成したインデックスをローカル保存（永続化）するのが当たり前です。

以下に、保存と読み込みを自動で行う実用的なコード例を示します。

```python
import os.path
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage
)

PERSIST_DIR = "./storage"

def get_query_engine():
    # すでに保存されたインデックスがあるかチェック
    if not os.path.exists(PERSIST_DIR):
        print("インデックスを新規作成します...")
        # データの読み込み
        documents = SimpleDirectoryReader("./data").load_data()
        # インデックス作成
        index = VectorStoreIndex.from_documents(documents)
        # ./storage フォルダに保存
        index.storage_context.persist(persist_dir=PERSIST_DIR)
    else:
        print("保存済みのインデックスを読み込みます...")
        # 保存済みデータの読み込み
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)

    return index.as_query_engine(similarity_top_k=3)

# 実行
engine = get_query_engine()
while True:
    question = input("質問を入力してください（exitで終了）: ")
    if question.lower() == "exit":
        break

    response = engine.query(question)
    print(f"\nAI: {response}\n")
```

`similarity_top_k=3` という設定を追加しました。これは「質問に関連する文章を、上位3つまで探してLLMに渡す」という意味です。回答の精度が低い場合は、この値を5〜7に増やすと改善することが多いです。ただし、増やしすぎるとLLMが処理する文字数（トークン数）が増え、料金が上がるので注意してください。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError` | ライブラリの不足 | `pip install` で必要な拡張機能を個別に入れる |
| `OpenAI API Quota Exceeded` | 無料枠切れ、または残高不足 | OpenAIのダッシュボードでクレジットをチャージする |
| 回答が英語になる | モデルの言語優先度 | プロンプトに「日本語で答えてください」と明示するか、GPT-4o等の強力なモデルを使う |

## 次のステップ

ここまでで、基本的なRAGの形は完成しました。しかし、実務で使うにはまだ改善の余地があります。

1. **ハイブリッド検索の導入:** 現在のベクトル検索は「意味」で探しますが、「製品番号」などの固有名詞の検索には弱いです。キーワード検索（BM25）と組み合わせることで、精度は劇的に向上します。
2. **チャンクサイズの最適化:** 文章をどのくらいの長さで区切って保存するか（チャンクサイズ）は、RAGの精度を左右する最大の変数です。LlamaIndexの `Settings.chunk_size` を調整して、自分のデータに最適な値を探してみてください。
3. **UIの構築:** 今回はコンソール画面でしたが、`Streamlit` を使えば、15分程度でブラウザから使えるチャットアプリに進化させることができます。

まずは、自分の手元にある「いつも検索に苦労しているドキュメント」を `data` フォルダに放り込み、自分専用のAIアシスタントを作ってみてください。自分のデータでAIが正解を出す瞬間こそが、RAG開発の醍醐味です。

## よくある質問

### Q1: PDF以外のファイル（ExcelやCSV）も読み込めますか？

はい、読み込めます。LlamaIndexには `LlamaParse` や各種リーダーが用意されており、Excelなら `PandasIndexRetriever` を使うことで表データの構造を保ったまま検索が可能です。ただし、構造化データは通常のRAGよりも設定が少し複雑になります。

### Q2: 埋め込みモデルをOpenAIにするのとローカルにするの、どっちが良い？

精度重視なら OpenAI の `text-embedding-3-large` ですが、日本語のプライベートな書類を扱うならローカルの `multilingual-e5` シリーズが圧倒的にコスパが良いです。私は機密性の高い案件では、常にローカルモデルを選択しています。

### Q3: 読み込ませるドキュメントの量に上限はありますか？

理論上、ベクトルDBを使うため数万ページでも扱えます。ただし、一度にLLMへ渡せる量（コンテキストウィンドウ）には上限があります。そのため、検索（Retrieval）のステップで「いかに関連性の高い部分だけを抽出するか」が技術的な腕の見せ所になります。

---

## あわせて読みたい

- [LlamaIndexとPythonで作るローカルRAG検索システム実装ガイド](/posts/2026-07-30-llamaindex-local-rag-python-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "PDF以外のファイル（ExcelやCSV）も読み込めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、読み込めます。LlamaIndexには LlamaParse や各種リーダーが用意されており、Excelなら PandasIndexRetriever を使うことで表データの構造を保ったまま検索が可能です。ただし、構造化データは通常のRAGよりも設定が少し複雑になります。"
      }
    },
    {
      "@type": "Question",
      "name": "埋め込みモデルをOpenAIにするのとローカルにするの、どっちが良い？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "精度重視なら OpenAI の text-embedding-3-large ですが、日本語のプライベートな書類を扱うならローカルの multilingual-e5 シリーズが圧倒的にコスパが良いです。私は機密性の高い案件では、常にローカルモデルを選択しています。"
      }
    },
    {
      "@type": "Question",
      "name": "読み込ませるドキュメントの量に上限はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "理論上、ベクトルDBを使うため数万ページでも扱えます。ただし、一度にLLMへ渡せる量（コンテキストウィンドウ）には上限があります。そのため、検索（Retrieval）のステップで「いかに関連性の高い部分だけを抽出するか」が技術的な腕の見せ所になります。 ---"
      }
    }
  ]
}
</script>
