---
title: "PythonでRAGを自作する！ローカルドキュメント検索の実装ガイド"
date: 2026-11-23T00:00:00+09:00
slug: "python-langchain-rag-local-pdf-guide"
cover:
  image: "/images/posts/2026-11-23-python-langchain-rag-local-pdf-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "LangChain RAG 使い方"
  - "ChromaDB 実装方法"
  - "Python ベクトル検索"
  - "ローカルLLM PDF読み込み"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 手持ちのPDFやテキストファイルを読み込み、その内容に基づいて回答するRAG（検索拡張生成）システムをPythonで構築します
- 外部APIへの依存を最小限に抑え、自分のPC内のデータを使って精度の高い回答を得るスクリプトを完成させます
- 前提知識として、Pythonの基本的な文法と`pip`によるライブラリインストールができる必要があります

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM/Embeddingの検証を回すのに最もコスパが良い選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

RAGの実装には、データを数値化する「Embedding（埋め込み）」と、回答を生成する「LLM（大規模言語モデル）」の2つが必要です。
OpenAIのAPI（gpt-4o-mini等）を使う場合は、手元のPCは数年前のノートPCで十分です。
一方、完全ローカル（Llama 3やGemma 2など）で動かす場合は、VRAM 12GB以上のGPU（RTX 3060 12GB / RTX 4070 Ti Super以上）か、メモリ16GB以上のApple Silicon搭載Macを強く推奨します。

API料金については、1,000ページのPDFを読み込んでもEmbeddingコストは数円、1回の質問も0.1円〜1円程度で収まります。
「高そうだから」と躊躇してローカルLLMの環境構築に何日も溶かすより、まずはAPIで「動くロジック」を組んでしまうのが実務的な最適解です。
私は自宅のRTX 4090 2枚挿しサーバーで検証していますが、検証の初期段階では試行錯誤のスピードを優先して、常にAPIベースでプロトタイプを作っています。

## なぜこの方法を選ぶのか

RAGを実装するライブラリは、現在「LangChain」と「LlamaIndex」の二択です。
今回は、カスタマイズ性が高く、将来的にエージェント化（自律的にタスクをこなす機能）への拡張が容易なLangChainを選択しました。
ベクトルデータベースには、環境構築が不要でPythonプロセス内で動作する「ChromaDB」を使います。

Pineconeのようなクラウド型ベクトルDBもありますが、個人のPCにある数MB〜数十MBのドキュメントを扱うなら、ローカルで完結するChromaDBの方がレスポンスも速く、データ流出のリスクも抑えられます。
まずは「手元のファイルを確実に検索に引っ掛ける」という最小単位の成功体験を優先すべきです。

## Step 1: 環境を整える

まずは必要なライブラリを一括でインストールします。

```bash
# 仮想環境を作成して有効化（推奨）
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# 必要なライブラリのインストール
pip install langchain langchain-openai chromadb pypdf tiktoken
```

`langchain-openai`はOpenAIのモデルを扱うためのパッケージ、`chromadb`は検索用データベース、`pypdf`はPDFから文字を抽出するために使用します。
`tiktoken`はトークン数（文字の長さの単位）を計算するために必要で、これがないとテキストの分割時にエラーが出ることがあります。

⚠️ **落とし穴:**
`pypdf`は稀にスキャンされた画像形式のPDFを読み込めないことがあります。その場合は`pytesseract`などのOCRライブラリが必要になりますが、まずはテキスト情報が含まれている通常のPDFで試してください。また、Python 3.12系では一部のライブラリがビルドエラーを起こすことがあるため、安定性を求めるなら3.10か3.11の使用を推奨します。

## Step 2: 基本の設定

プロジェクトのディレクトリに `data` という名前のフォルダを作り、そこに回答させたいPDFファイルを1つ入れておいてください。
次に、環境変数にOpenAIのAPIキーを設定します。

```python
import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# 1. APIキーの設定
# セキュリティのため、本来は .envファイルなどから読み込むべきです
os.environ["OPENAI_API_KEY"] = "sk-..."

# 2. モデルの初期化
# Embeddingモデルは text-embedding-3-small を使用（安くて高性能）
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 回答生成用モデル
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

`temperature=0` に設定する理由は、RAGにおいて「モデルの勝手な想像」を排除するためです。
実務で使うRAGにおいて、クリエイティビティは不要です。
ドキュメントに書いてあることを、書いてある通りに答えてもらうことが最も重要だからです。

## Step 3: 動かしてみる

ドキュメントを読み込み、検索可能な状態（Vector Store）にしてから、実際に質問を投げてみます。

```python
# 1. PDFの読み込み
loader = PyPDFLoader("./data/your_document.pdf")
raw_documents = loader.load()

# 2. テキストの分割（チャンク化）
# 長い文章をそのまま検索にかけることはできません。
# 1000文字程度の塊（チャンク）に分割します。
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    separators=["\n\n", "\n", "。", "、", " "]
)
documents = text_splitter.split_documents(raw_documents)

# 3. ベクトルデータベースへの保存
# ここでテキストが数値（ベクトル）に変換され、DBに格納されます。
vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory="./chroma_db" # データベースを保存する場所
)

# 4. 検索と回答
from langchain.chains import RetrievalQA

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}) # 上位3つの関連チャンクを取得
)

query = "この資料に記載されている主要な課題は何ですか？"
response = qa_chain.invoke(query)

print(f"質問: {query}")
print(f"回答: {response['result']}")
```

### 期待される出力

```
質問: この資料に記載されている主要な課題は何ですか？
回答: 本資料に基づくと、主要な課題は以下の3点です。
1. 若年層の採用コストが前年比で20%増加している点。
2. 既存システムの老朽化に伴うメンテナンス費用の増大。
3. リモートワーク移行による社内コミュニケーションの質の低下。
```

`chunk_overlap`を100に設定しているのは、分割した境目に重要な情報があった場合、前後の文脈が途切れないようにするためです。
これを0にすると、例えば「A社の課題は」と「人材不足である」が別々のチャンクに分断され、正しく検索できなくなるリスクがあります。

## Step 4: 実用レベルにする

上記のコードだけでも動きますが、実務で使うには「どの資料の何ページ目を参照したか」というソースの明示が不可欠です。
これがないと、AIが嘘をついた（ハルシネーション）ときに、人間が裏取りをすることができません。

```python
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# 独自のプロンプトを定義
system_prompt = (
    "あなたは誠実なアシスタントです。提供されたコンテキストのみを使用して質問に答えてください。"
    "コンテキストに答えがない場合は「わかりません」と答えてください。"
    "回答の最後には、必ず参照したソース情報を記載してください。"
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

# 新しい形式のチェーン作成
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(vectorstore.as_retriever(), question_answer_chain)

# 実行
result = rag_chain.invoke({"input": "予算案の総額を教えてください。"})

print(result["answer"])

# 参照元のメタデータを確認
for doc in result["context"]:
    print(f"参照元: {doc.metadata.get('source')} (Page: {doc.metadata.get('page')})")
```

このようにメタデータを出力させることで、回答の信頼性が飛躍的に向上します。
私は以前、社内規定のRAGを構築した際、この「ページ数表示」を実装しなかったために、人事担当者から「本当に合っているのか不安で使えない」と突き返された経験があります。
システムへの信頼は、精度だけでなく「検証可能性」からも生まれます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `RateLimitError` | OpenAIのAPI利用上限 | 支払い設定を確認するか、数分待って再試行する。 |
| `pypdf`で文字が取れない | PDFが画像（スキャン） | OCRライブラリを使うか、テキスト付きPDFを用意する。 |
| 検索精度が低い | チャンクサイズが不適切 | 文章の構造に合わせて `chunk_size` を調整する。 |
| `sqlite3` のバージョンエラー | ChromaDBの要求バージョン不足 | `pysqlite3-binary` をインストールして上書きする。 |

## 次のステップ

この記事で作成したRAGは、基本的な「一問一答」形式です。
しかし、実際の業務では「さっきの回答の、2番目の項目についてもっと詳しく教えて」といった対話の流れが必要になります。
これを実現するには、過去の発言を保存する「Memory」機能を組み込む必要があります。

また、日本語の検索精度をさらに高めたい場合は、単なるベクトル検索だけでなく、キーワード一致を組み合わせた「Hybrid Search（ハイブリッド検索）」や、検索結果をAIが再度ランク付けする「Reranking（リランキング）」の導入を検討してください。
これらはLangChainの `EnsembleRetriever` や、Cohereが提供するRerank APIを使うことで、比較的簡単に実装可能です。
まずはこの記事のコードをベースに、自分の持っている複雑なPDF（図表が多いものなど）を読み込ませて、どこまで正解できるかテストすることから始めてみてください。

## よくある質問

### Q1: ローカルLLMに切り替えるにはどうすればいいですか？

`Ollama`を使うのが最も簡単です。PCにOllamaをインストールし、`langchain_community.chat_models import ChatOllama`を使って、`llm = ChatOllama(model="llama3")`と書き換えるだけで、ロジックはそのままで完全オフライン化できます。

### Q2: 1,000ファイル以上ある場合も同じコードで大丈夫ですか？

ファイル数が増えると、ChromaDBの検索が遅くなったり、メモリを圧迫したりします。1,000ファイルを超える場合は、QdrantやWeaviateといった専用のベクトルデータベースサーバーを立て、インデックスを外部管理する構成にするのが一般的です。

### Q3: PDF以外のファイル（WordやExcel）はどうすればいいですか？

LangChainには `Docx2txtLoader` や `UnstructuredExcelLoader` など、ファイル形式ごとのローダーが用意されています。これらに入れ替えるだけで、読み込み後のチャンク分割やベクトル化の工程は全く同じコードが使い回せます。

---

## あわせて読みたい

- [PythonでRAGを自作する！ローカル検索の実装手順ガイド](/posts/2026-06-23-python-rag-faiss-local-implementation-guide/)
- [PythonでRAG入門！LangChainとChromaで作るローカル文書検索](/posts/2026-11-07-python-langchain-rag-chroma-local-tutorial/)
- [PythonでRAGを自作する！ローカル検索の実装と使い方入門](/posts/2026-06-17-python-rag-tutorial-local-implementation/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "ローカルLLMに切り替えるにはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaを使うのが最も簡単です。PCにOllamaをインストールし、langchaincommunity.chatmodels import ChatOllamaを使って、llm = ChatOllama(model=\"llama3\")と書き換えるだけで、ロジックはそのままで完全オフライン化できます。"
      }
    },
    {
      "@type": "Question",
      "name": "1,000ファイル以上ある場合も同じコードで大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ファイル数が増えると、ChromaDBの検索が遅くなったり、メモリを圧迫したりします。1,000ファイルを超える場合は、QdrantやWeaviateといった専用のベクトルデータベースサーバーを立て、インデックスを外部管理する構成にするのが一般的です。"
      }
    },
    {
      "@type": "Question",
      "name": "PDF以外のファイル（WordやExcel）はどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "LangChainには Docx2txtLoader や UnstructuredExcelLoader など、ファイル形式ごとのローダーが用意されています。これらに入れ替えるだけで、読み込み後のチャンク分割やベクトル化の工程は全く同じコードが使い回せます。 ---"
      }
    }
  ]
}
</script>
