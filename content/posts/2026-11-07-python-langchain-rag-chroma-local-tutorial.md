---
title: "PythonでRAG入門！LangChainとChromaで作るローカル文書検索"
date: 2026-11-07T00:00:00+09:00
slug: "python-langchain-rag-chroma-local-tutorial"
cover:
  image: "/images/posts/2026-11-07-python-langchain-rag-chroma-local-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "LangChain RAG 使い方"
  - "Chroma Python 入門"
  - "ローカルベクトルデータベース"
  - "検索拡張生成 実装"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 手元のPDFファイルを読み込み、その内容に基づいてAIが回答するRAG（検索拡張生成）システムを作ります。
- PythonとLangChain、そしてローカルで動くベクトルデータベースであるChromaを使用します。
- 外部にデータを漏らしたくない業務効率化の第一歩として、PC内で完結するデータ検索パイプラインを構築します。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的。RAGの完全ローカル化に必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

今回の実装では、テキストの埋め込み（Embedding）と回答生成にOpenAIのAPIを使用します。
生成AIモデルをローカルで動かすことも可能ですが、最初は「精度」と「デバッグのしやすさ」を優先してAPIを使うのが正解です。
API料金は、10ページ程度のPDFであれば1回のリクエストで0.1円もかからない程度なので、学習用としては無視できるレベルです。

ハードウェアに関しては、一般的なビジネスノートPC（メモリ8GB以上）で十分動作します。
ただし、将来的にLlama 3やGemma 2などのモデルを完全にローカルで動かしたい場合は、VRAM（ビデオメモリ）が12GB以上のGPUが必要です。
具体的にはNVIDIAのRTX 3060（12GB版）やRTX 4060 Ti（16GB版）が、コストパフォーマンスの面で実務上の最低ラインになります。
Macユーザーであれば、メモリ16GB以上のApple Silicon（M1/M2/M3）を積んでいれば、後のローカルLLM展開もスムーズです。

## なぜこの方法を選ぶのか

RAGを実装する手段は、LlamaIndexを使う方法や、PineconeのようなマネージドなベクトルDBを使う方法など、選択肢は山ほどあります。
その中で、なぜ「LangChain + Chroma」を最初に学ぶべきなのか。
それは、LangChainが最も抽象化されており、将来的に別のLLMやツールへ乗り換える際の「部品の交換」が容易だからです。

また、データベースにChromaを選ぶ理由は、Dockerなどのインフラ準備が一切不要で、Pythonライブラリをインストールするだけで「ローカルフォルダにデータを保存できる」点にあります。
社外秘のドキュメントをクラウドDBにアップロードすることに抵抗がある現場は多いですが、ローカルDBであればその懸念を即座に払拭できます。
FAISSも高速で良い選択肢ですが、メタデータの管理や永続化のしやすさではChromaに軍配が上がります。

## Step 1: 環境を整える

まずは必要なライブラリを一気にインストールします。
バージョン依存によるエラーを防ぐため、特定のバージョンを指定するか、最新版で統一してください。

```bash
pip install langchain langchain-openai langchain-community chromadb pypdf tiktoken
```

`langchain-openai`はOpenAIのモデルを扱うための専用パッケージです。
`pypdf`はPDFの解析に、`tiktoken`はトークン数の計算（OpenAIのモデルが裏で使います）に必要になります。
`chromadb`が今回のキモとなるローカルベクトルデータベースです。

⚠️ **落とし穴:**
Windows環境で`chromadb`をインストールする際、C++のビルドツールが足りないとエラーが出ることがあります。
その場合は「Visual Studio Build Tools」をインストールし、「C++ によるデスクトップ開発」にチェックを入れて更新してください。
これ、初心者が一番最初に挫折するポイントです。

## Step 2: 基本の設定

まずはAPIキーの設定と、ドキュメントを読み込む準備をします。
コードを動かす前に、カレントディレクトリに「data」というフォルダを作り、中に適当なPDFを1つ入れておいてください。

```python
import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# APIキーの設定（環境変数から読み込むのが実務の鉄則）
os.environ["OPENAI_API_KEY"] = "sk-..."

# 1. PDFを読み込む
# 試した結果、PyPDFLoaderが最も安定して日本語を読み取れました
loader = PyPDFLoader("./data/your_document.pdf")
raw_docs = loader.load()

# 2. テキストを適切なサイズに分割する
# なぜ分割するのか：LLMには一度に送れるトークン制限があり、また検索の精度を上げるためです
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,     # 1つの塊を500文字にする
    chunk_overlap=50,   # 前後の塊と50文字重複させる（文脈を維持するため）
    length_function=len,
)
docs = text_splitter.split_documents(raw_docs)

print(f"ドキュメントを {len(docs)} 個のチャンクに分割しました。")
```

各項目の設定には理由があります。
`chunk_size`を1000以上にすると、検索でヒットした際に不要な情報が多く混ざり、回答の精度が落ちます。
逆に100以下だと文脈が細切れになりすぎて、AIが意味を理解できなくなります。
実務経験上、日本語のドキュメントであれば「500〜800」程度がスイートスポットです。

## Step 3: 動かしてみる

次に、分割したテキストを「ベクトル化」してChroma DBに保存し、実際に検索を行ってみます。

```python
# 3. ベクトル化して保存
# フォルダ名を指定することで、次回以降は計算済みのデータを再利用できます
persist_directory = "./chroma_db"
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    persist_directory=persist_directory
)

# 4. 検索と回答の実行
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
from langchain.chains import RetrievalQA

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}) # 上位3件を取得
)

query = "この資料の要点を3つで教えてください"
response = qa_chain.invoke(query)

print("--- 質問 ---")
print(query)
print("--- 回答 ---")
print(response["result"])
```

### 期待される出力

```
--- 質問 ---
この資料の要点を3つで教えてください
--- 回答 ---
1. 本資料は2024年度のAI導入ガイドラインについて解説しています。
2. セキュリティ基準として、個人情報の取り扱いに関する3つのルールを定めています。
3. 実装フェーズでは、まずスモールスタートで検証を行うことを推奨しています。
```

結果の読み方ですが、もし「回答が的外れ」だった場合は、`search_kwargs={"k": 3}`の数字を増やしてみてください。
ただし、増やすほどLLMに送る文字数が増えて料金が上がるので注意が必要です。

## Step 4: 実用レベルにする

実務で運用する場合、先ほどのコードでは「毎回DBを新規作成」してしまい、効率が悪いです。
また、ユーザーが「何を聞くか分からない」状況では、単純なキーワード検索だけでは不十分です。
ここでは「既存のDBを読み込む」処理と、検索精度を劇的に上げる「Multi-Query Retriever」の考え方を導入します。

```python
from langchain.retrievers.multi_query import MultiQueryRetriever

# 既存のDBを読み込む
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-small")
)

# 質問を多角化するリトリーバーを設定
# 1つの質問をAIが複数の視点で言い換え、それら全てで検索をかけます
# これにより「言葉の揺れ」による検索漏れを防止できます
retriever_from_llm = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(),
    llm=llm
)

# 実用的なエラーハンドリングを含めた実行関数
def ask_ai(question):
    try:
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever_from_llm
        )
        res = qa_chain.invoke(question)
        return res["result"]
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

# 実行
print(ask_ai("プロジェクトの納期はいつですか？"))
```

最初に私がこの構成を試したとき、シンプルな検索ではヒットしなかった情報が、Multi-Queryを入れた瞬間に正確に拾えるようになりました。
「納期は？」という短い質問を、AIが「デッドラインは？」「スケジュールを教えて」「いつまでに完了すべきか？」と自動で広げてくれるからです。
実務で「AIが全然まともな回答をしない」と嘆く人の多くは、この検索部分の工夫を飛ばしています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `sqlite3.OperationalError` | SQLiteのバージョンが古い | `pysqlite3-binary`をインストールして、コード冒頭で上書きする。 |
| `RateLimitError` | APIの無料枠制限 | クレジットを最低$5チャージするか、時間を置いて実行する。 |
| 検索結果が「情報がない」となる | Chunkingの失敗 | `chunk_size`を大きくするか、PDFが画像形式（OCRが必要）でないか確認する。 |

## 次のステップ

この記事の内容をマスターしたら、次は「データの更新」に挑戦してください。
現在のコードでは、PDFが増えるたびにDBを再構築するか、手動で追加するコードを書く必要があります。
実務では、フォルダを監視して新しいファイルが入ったら自動でベクトル化する「インデックス管理の自動化」が求められます。

また、精度に満足できなくなったら、OpenAIEmbeddingsを使い続けるのではなく、日本語に特化した「multilingual-e5」などのモデルをローカルで動かして比較してみるのも面白いです。
LangChainなら、`embeddings = ...` の一行を書き換えるだけで、その検証が可能です。
これができると、エンジニアとしての価値は一気に上がります。

## よくある質問

### Q1: 自社のサーバーからデータを一歩も出したくないのですが。

その場合は、OpenAIの代わりにOllamaを使ってローカルLLM（Llama 3など）を立ち上げ、EmbeddingsもHuggingFaceのローカルモデルに差し替えてください。この記事のLangChainの構造はそのままで、コンポーネントを差し替えるだけで完全オフライン化が可能です。

### Q2: PDFの中に表組みがあるのですが、うまく読み取れません。

通常の`PyPDFLoader`は表をテキストとして平坦化してしまいます。表の構造を維持したい場合は、`UnstructuredPDFLoader`を使用するか、Azure AI Document Intelligenceなどの高度な解析ツールと連携させる必要があります。

### Q3: Chroma DBのデータが増えると遅くなりませんか？

数万件程度のドキュメントであれば、Chroma（ローカル運用）でもレスポンスは1秒以内です。もし数百万件規模の全社データを扱うなら、検索エンジンに近い性質を持つQdrantやMilvusといった、より大規模向けのベクトルDBへ移行を検討してください。

---

## あわせて読みたい

- [PythonでRAGを自作する！ローカル検索の実装手順ガイド](/posts/2026-06-23-python-rag-faiss-local-implementation-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "自社のサーバーからデータを一歩も出したくないのですが。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "その場合は、OpenAIの代わりにOllamaを使ってローカルLLM（Llama 3など）を立ち上げ、EmbeddingsもHuggingFaceのローカルモデルに差し替えてください。この記事のLangChainの構造はそのままで、コンポーネントを差し替えるだけで完全オフライン化が可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "PDFの中に表組みがあるのですが、うまく読み取れません。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "通常のPyPDFLoaderは表をテキストとして平坦化してしまいます。表の構造を維持したい場合は、UnstructuredPDFLoaderを使用するか、Azure AI Document Intelligenceなどの高度な解析ツールと連携させる必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "Chroma DBのデータが増えると遅くなりませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "数万件程度のドキュメントであれば、Chroma（ローカル運用）でもレスポンスは1秒以内です。もし数百万件規模の全社データを扱うなら、検索エンジンに近い性質を持つQdrantやMilvusといった、より大規模向けのベクトルDBへ移行を検討してください。 ---"
      }
    }
  ]
}
</script>
