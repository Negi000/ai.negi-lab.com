---
title: "Python RAG入門 ローカル検索の実装方法"
date: 2026-09-15T00:00:00+09:00
slug: "langchain-rag-local-pdf-tutorial"
cover:
  image: "/images/posts/2026-09-15-langchain-rag-local-pdf-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "LangChain"
  - "ChromaDB"
  - "RAG"
  - "Python"
  - "ローカル検索"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

手元のPDFファイルを読み込み、その内容に基づいてAIが回答する「ローカルRAG（検索拡張生成）システム」の最小構成を構築します。
具体的には、LangChainとChromaDBを組み合わせ、プロプライエタリなデータを外部に流出させすぎずに検索・回答できるPythonスクリプトを完成させます。

前提知識：
- Pythonの基本的な文法（変数、関数、pipでのライブラリ導入）がわかること
- OpenAI APIのキーを取得済みであること

必要なもの：
- Python 3.10以上
- OpenAI APIキー（少額の利用料が発生します）
- 読み込ませたいPDFファイル1つ（仕様書やマニュアルなど）

## 先に確認するスペック・料金

RAGの実装において、最も重要なのは「メモリ（RAM）」と「ストレージのI/O速度」です。
今回の構成ではベクトルデータベースにChromaDBを使用しますが、これはメモリ上で動作するため、最低でも16GBのRAMを推奨します。
8GBのPCでも動かないことはありませんが、PDFのページ数が100を超えたあたりで検索レスポンスが1秒を超え、開発効率が著しく低下します。

GPUについては、今回はOpenAIのAPIを利用するため必須ではありません。
しかし、将来的にEmbedding（ベクトルの数値化）もローカルで行いたい場合は、VRAM 8GB以上のNVIDIA製GPU（RTX 3060以上）があると、処理速度がCPU比で10倍以上変わります。
API料金については、一般的なA4サイズのPDF10枚程度を処理して100回程度質問しても、$0.5（約75円）もかかりません。

もし完全に無料で構築したいなら、Embeddingモデルに「HuggingFaceEmbeddings」、LLMに「Ollama」を組み合わせる選択肢もあります。
ただ、初心者が最初からフルローカルを目指すと、ライブラリの依存関係や環境構築で9割の人が挫折します。
まずは「検索の仕組み」を理解するために、安定しているOpenAI APIをバックエンドに使うのが最短ルートです。

## なぜこの方法を選ぶのか

RAGを実装するライブラリは、現在「LangChain」と「LlamaIndex」の二強状態です。
私は実務で両方使っていますが、今回はあえてLangChainを選びました。
理由は、LangChainの方が「何が起きているか」をステップごとにコードで記述する必要があり、学習効果が高いからです。

LlamaIndexは非常に優秀で、3行書けばRAGが完成しますが、中身がブラックボックス化されやすいため、いざ精度を上げようとした時にどこを弄ればいいか分からなくなる落とし穴があります。
エンジニアとして「仕事で使える」レベルを目指すなら、データ分割、ベクトル化、検索、プロンプト注入という一連の流れを、自分の手で組み立てる経験を最初にしておくべきです。

## Step 1: 環境を整える

まずは必要なライブラリを一括でインストールします。

```bash
# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# 必要なパッケージのインストール
pip install langchain langchain-openai langchain-community chromadb pypdf tiktoken python-dotenv
```

`langchain-openai`はOpenAI専用のコネクタ、`chromadb`はベクトルDB、`pypdf`はPDF解析用です。
`tiktoken`はOpenAIのトークン数を計算するために内部で必要となるため、忘れずに入れてください。
バージョンが古いと動かないケースがあるため、エラーが出る場合は `pip install --upgrade` を試してください。

⚠️ **落とし穴:**
Windows環境で `chromadb` のインストールに失敗する場合、多くは「C++ Build Tools」が不足しています。
Visual Studio Installerから「C++によるデスクトップ開発」にチェックを入れてインストールする必要があります。
これが面倒な場合は、WSL2（Ubuntu）上での開発を強くおすすめします。

## Step 2: 基本の設定

APIキーをコードに直接書くのは、実務では「即退場」レベルのタブーです。
`.env` ファイルを作成して管理しましょう。

```text: .env
OPENAI_API_KEY=sk-xxxx...（あなたのAPIキー）
```

次に、Pythonスクリプト（`rag_basic.py`）を作成し、環境変数を読み込む設定を書きます。

```python
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 環境変数の読み込み
load_dotenv()

# APIキーの確認
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEYが設定されていません。.envファイルを確認してください。")

# モデルの初期化
# text-embedding-3-smallは安価で高性能な最新モデルです
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 思考プロセスが見えるようにtemperatureは0に設定します
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

`temperature=0` に設定する理由は、RAGにおいてLLMに求められるのは「検索結果を正確に要約すること」であり、創造性（揺らぎ）はノイズになるからです。
また、Embeddingモデルに `text-embedding-3-small` を選んだのは、旧世代の `text-embedding-ada-002` より安く、かつ次元数を調整できる柔軟性があるためです。

## Step 3: 動かしてみる

では、実際にPDFを読み込んで、ベクトルDBに格納する最小コードを書きます。
手元に「sample.pdf」という名前のファイルを置いて実行してください。

```python
# 1. PDFの読み込み
loader = PyPDFLoader("sample.pdf")
pages = loader.load()

# 2. テキストの分割（チャンク化）
# 1000文字ごとに区切り、前後100文字を重複させる設定
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    separators=["\n\n", "\n", "。", "、", " ", ""]
)
docs = text_splitter.split_documents(pages)

# 3. ベクトルDBへの格納（ローカルの'db'フォルダに保存）
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

# 4. 検索して回答を得る
query = "この資料の要点を3つ教えてください"
# 関連度の高い上位3つのチャンクを取得
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
result_docs = retriever.invoke(query)

# 取得した内容を確認
print(f"検索されたチャンク数: {len(result_docs)}")
for i, doc in enumerate(result_docs):
    print(f"--- Chunk {i+1} ---\n{doc.page_content[:100]}...")
```

### 期待される出力

```
検索されたチャンク数: 3
--- Chunk 1 ---
本プロジェクトの目的は、AIを活用した業務効率化であり...
--- Chunk 2 ---
導入スケジュールについては、2024年4月から試用運用を開始し...
--- Chunk 3 ---
予算規模は全体で500万円を想定しており、その内訳は...
```

ここで重要なのは `chunk_overlap` です。
これがないと、文章がちょうど分割地点で切れた際に「主語が前のチャンクにあるが、述語が後ろのチャンクにある」という状態になり、検索精度がガタ落ちします。
私は実務でここをケチって失敗したことがありますが、10%〜20%の重複は必須だと考えてください。

## Step 4: 実用レベルにする

今のままでは「検索しただけ」です。
最後に、検索結果をLLMに渡し、自然な日本語で回答させる「Chain」を構築します。

```python
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# プロンプトの定義
# {context}の部分に検索された文章が自動で注入されます
system_prompt = (
    "あなたは誠実なアシスタントです。"
    "以下の提供されたコンテキストのみを使用して質問に答えてください。"
    "答えが分からない場合は「分かりません」と答えてください。"
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

# チェインの作成
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# 実行
response = rag_chain.invoke({"input": "この資料の要点を3つ教えてください"})

print("\n=== AIの回答 ===")
print(response["answer"])
```

この「プロンプト」の設定が実務では生命線になります。
「コンテキストのみを使用して」という制約を入れないと、LLMは自分の知っている一般的な知識（ハルシネーション）を混ぜて回答してしまいます。
社内規定や技術仕様書など、正確性が求められる場面では、この一文が「使えるRAG」かどうかの分かれ目です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `sqlite3.OperationalError` | ChromaDBが必要とするSQLiteのバージョンが古い | `pysqlite3-binary`を入れ、コード冒頭でsys.modulesを差し替える |
| 検索結果が空になる | PDFが画像形式（スキャンしたもの）でテキストデータがない | `pytesseract`などのOCRライブラリを併用するか、テキスト化してから読み込む |
| 回答が「分かりません」ばかり | チャンクサイズが小さすぎて文脈が消失している | `chunk_size`を1500〜2000に増やし、`k`の値も大きくしてみる |

## 次のステップ

おめでとうございます。これでローカルファイルを基にしたRAGの基本形が完成しました。
しかし、これを実戦投入するにはまだ足りない要素があります。

1. **メタデータフィルタリング:** 「特定の部署の資料だけから探す」といった属性による絞り込み。
2. **Re-ranking:** 検索された上位10件を、別のモデルで再度並び替えて精度を高める手法。
3. **ハイブリッド検索:** ベクトル検索だけでなく、従来の「キーワード検索」を組み合わせる。

特に、日本語の固有名詞や製品型番などはベクトル検索が苦手とする部分です。
「BM25」というアルゴリズムを組み合わせることで、検索精度は劇的に向上します。
まずは、今回のコードの `chunk_size` や `k` の値を変えて、回答がどう変わるかを観察してみてください。
「最適なパラメータはデータによって異なる」という、AI開発の泥臭い面白さに気づけるはずです。

## よくある質問

### Q1: PDF以外のファイル（ExcelやWord）も読み込めますか？

はい、LangChainには `UnstructuredExcelLoader` や `Docx2txtLoader` などが用意されています。ただし、Excelは「表構造」を維持して読み込むのが難しいため、CSVに変換してから処理する方が実務上は安定します。

### Q2: 毎回PDFをベクトル化するのは時間がかかりませんか？

`persist_directory` を指定しているため、一度作成したDBは次回から再利用可能です。`Chroma(persist_directory="./chroma_db", embedding_function=embeddings)` と呼び出すだけで、前回のデータを即座に検索できます。

### Q3: セキュリティ的にOpenAIを使うのが不安です。

その場合は、Embeddingモデルを `HuggingFaceBgeEmbeddings` に、LLMを `Ollama` 経由の `Llama3` などに差し替えれば、完全にオフラインで動作させることが可能です。ただし、推論速度はPCスペックに大きく依存します。

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

---

## あわせて読みたい

- [PythonとLangChainを使って、手元のPDFやテキストファイルを知識源として回答する「RAG（検索拡張生成）システム」をゼロから構築します。](/posts/2026-09-02-python-rag-local-implementation-guide/)
- [PythonとLangChainで自分専用のPDF検索AIチャットボットを作る方法](/posts/2026-06-28-local-rag-langchain-faiss-tutorial/)
- [PythonとFAISSで作るRAGパイプライン実装入門](/posts/2026-08-29-langchain-faiss-rag-tutorial-local-search/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "PDF以外のファイル（ExcelやWord）も読み込めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、LangChainには UnstructuredExcelLoader や Docx2txtLoader などが用意されています。ただし、Excelは「表構造」を維持して読み込むのが難しいため、CSVに変換してから処理する方が実務上は安定します。"
      }
    },
    {
      "@type": "Question",
      "name": "毎回PDFをベクトル化するのは時間がかかりませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "persistdirectory を指定しているため、一度作成したDBは次回から再利用可能です。Chroma(persistdirectory=\"./chromadb\", embeddingfunction=embeddings) と呼び出すだけで、前回のデータを即座に検索できます。"
      }
    },
    {
      "@type": "Question",
      "name": "セキュリティ的にOpenAIを使うのが不安です。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "その場合は、Embeddingモデルを HuggingFaceBgeEmbeddings に、LLMを Ollama 経由の Llama3 などに差し替えれば、完全にオフラインで動作させることが可能です。ただし、推論速度はPCスペックに大きく依存します。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでローカルLLM入門に現実的</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
