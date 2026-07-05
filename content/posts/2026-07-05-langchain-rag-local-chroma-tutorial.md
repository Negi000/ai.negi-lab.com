---
title: "PythonとLangChainでRAGパイプラインを自作する方法"
date: 2026-07-05T00:00:00+09:00
slug: "langchain-rag-local-chroma-tutorial"
cover:
  image: "/images/posts/2026-07-05-langchain-rag-local-chroma-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "LangChain"
  - "RAG 構築"
  - "Python"
  - "Chroma"
  - "OpenAI API"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- ローカルのPDFファイルを読み込み、その内容に基づいて回答するRAG（検索拡張生成）システムを構築します
- 外部API（OpenAI）とローカルベクトルDB（Chroma）を組み合わせた、実務で即戦力になる最小構成のPythonスクリプトを完成させます
- 前提知識として、Pythonの基本的な文法（変数、関数、pip操作）を理解している必要があります

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Air M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">APIベースのRAG開発なら、16GBメモリでVS Codeとブラウザが快適に動きます</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Air%2520M3%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Air%2520M3%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Air%20M3%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

RAGの実装において最も重要なのは「メモリ」と「API利用料」の管理です。
今回の構成では、推論にOpenAIのAPIを使用するため、PC側に高価なGPU（RTX 4090など）は必須ではありません。
MacBook Airのメモリ8GBモデルでも十分に動作します。

コスト面では、OpenAIの「gpt-4o-mini」と「text-embedding-3-small」を使用します。
1,000文字程度のドキュメントを10個読み込ませて100回質問しても、料金は1ドル（約150円）にも満たないでしょう。
「とりあえず試す」には最適なコストパフォーマンスです。

ただし、大量のPDF（数千ページ単位）を処理する場合は、ローカルで埋め込み（Embedding）を行う方が安上がりです。
その場合はメモリ16GB以上を推奨します。
まずは今回紹介するクラウドとローカルのハイブリッド構成で、RAGの「手触り」を掴んでください。

## なぜこの方法を選ぶのか

RAGを構築するライブラリとして「LlamaIndex」も有名ですが、私はあえて「LangChain」を推奨します。
実務の現場では、単に検索して回答するだけでなく、その後に独自のロジックを組み込んだり、複数のLLMを使い分けたりするニーズが必ず発生するからです。
LangChainは設計がモジュール化されており、部品の交換が容易なため、プロトタイプから本番運用への移行がスムーズです。

また、ベクトルDBに「Chroma」を選ぶ理由は、セットアップが不要で、実行時にフォルダが作成されるだけでデータ保存が完結するからです。
PineconeなどのクラウドDBは便利ですが、初期設定の面倒さや通信遅延が開発のテンポを削ぎます。
まずはローカルのChromaで「爆速」な開発サイクルを回すのが、私の経験上、最も効率が良いです。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
Python 3.10以上の環境を用意してください。

```bash
# 仮想環境を作成（推奨）
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# 必要なライブラリを一括インストール
pip install langchain langchain-openai langchain-community chromadb pypdf python-dotenv ticktoken
```

`langchain-openai`はOpenAI専用のコネクタ、`chromadb`はベクトルデータベース、`pypdf`はPDF解析用です。
`python-dotenv`はAPIキーを安全に管理するために使用します。
`ticktoken`はトークン数計算のためにLangChainの内部で使用されるため、事前に入れておかないとエラーを吐くことがあります。

⚠️ **落とし穴:**
`pip install langchain`だけでは、OpenAIやChromaとの連携機能はインストールされません。
最近のLangChainは機能ごとにパッケージが細分化されているため、上記のように個別のコネクタを明示的に入れる必要があります。
ここで躓いて「モジュールが見つかりません」というエラーに泣く初心者が後を絶ちません。

## Step 2: 基本の設定

APIキーの管理と、PDFを読み込むための初期設定を行います。
プロジェクトのルートディレクトリに `.env` ファイルを作成し、OpenAIのAPIキーを記述してください。

```text
OPENAI_API_KEY=sk-xxxx...（あなたのキー）
```

次に、Pythonスクリプト（`rag_basic.py`）を作成し、ライブラリをインポートして環境を読み込みます。

```python
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

# .envから設定を読み込む
load_dotenv()

# APIキーが読み込めているか確認
if not os.environ.get("OPENAI_API_KEY"):
    raise ValueError("APIキーが設定されていません。.envファイルを確認してください。")

# 1. モデルの初期化
# 埋め込みモデルはコスト効率と精度のバランスが良い 'text-embedding-3-small' を選択
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 回答生成モデルは最新の 'gpt-4o-mini'。temperatureは事実に基づかせるため 0 に設定
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

埋め込みモデルに `text-embedding-3-small` を選ぶ理由は、前世代のモデルより安く、かつ日本語の検索精度も向上しているからです。
また、`temperature=0` は実務上の鉄則です。
AIにクリエイティビティを求めていないRAGにおいて、回答の揺らぎは「嘘（ハルシネーション）」の温床になります。

## Step 3: 動かしてみる

手元にあるPDFファイルを一つ用意してください（名前を `document.pdf` とします）。
これを読み込み、ベクトルDBに格納して検索するまでの最小コードを書きます。

```python
# 2. ドキュメントの読み込み
loader = PyPDFLoader("document.pdf")
documents = loader.load()

# 3. テキストの分割（チャンク化）
# 長い文章はそのままベクトル化できないため、適切なサイズに切る
text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=500,
    chunk_overlap=50
)
chunks = text_splitter.split_documents(documents)

# 4. ベクトルDBへの格納
# 'db' というフォルダ名でローカルに保存される
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

# 5. RAGシステムの構築
# 検索して回答する「鎖（Chain）」を作る
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3})
)

# 6. 質問を実行
query = "この資料の要点を3つで教えてください"
response = qa_chain.invoke(query)

print("--- 質問 ---")
print(query)
print("\n--- 回答 ---")
print(response["result"])
```

### 期待される出力

```
--- 質問 ---
この資料の要点を3つで教えてください

--- 回答 ---
資料に基づくと、主な要点は以下の3点です。
1. ○○プロジェクトの目的は、次世代のAI基盤を構築すること。
2. 予算規模は5,000万円で、来年3月までの完遂を目指している。
3. 主な課題として、データのクレンジングコストが挙げられている。
```

この「チャンク分割」という工程がRAGの心臓部です。
`chunk_size=500` は、一つのデータの塊を500文字程度にするという意味です。
短すぎると文脈が切れ、長すぎると検索精度が落ちるため、まずは500から始めるのが私の定番です。

## Step 4: 実用レベルにする

実務でこのスクリプトを運用しようとすると、「なぜその回答になったのか？」という根拠を求められます。
また、検索結果が全くヒットしなかった場合に、AIが適当な嘘をつくのを防ぐ必要があります。
これらを解決する「実用版」にアップグレードしましょう。

```python
from langchain.prompts import PromptTemplate

# カスタムプロンプトの定義
# 「知らないことは知らないと言わせる」ための制約を加える
prompt_template = """あなたは誠実なアシスタントです。
以下のコンテキスト（参考資料）を利用して質問に答えてください。
コンテキストの中に答えがない場合は、無理に答えず「資料には記載がありません」と伝えてください。

コンテキスト:
{context}

質問:
{question}

回答:"""

PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)

# 強化版RAGシステム
qa_chain_advanced = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}), # 検索結果を5つに増やす
    return_source_documents=True, # 根拠となるドキュメントを返す
    chain_type_kwargs={"prompt": PROMPT}
)

# 実行
result = qa_chain_advanced.invoke("プロジェクトの期限はいつですか？")

print("【回答】")
print(result["result"])

print("\n【根拠となった資料の抜粋】")
for doc in result["source_documents"]:
    print(f"- ページ {doc.metadata['page']}: {doc.page_content[:50]}...")
```

このコードのポイントは `return_source_documents=True` です。
これを入れることで、AIの回答の「元ネタ」を特定できるようになります。
また、`search_kwargs={"k": 5}` とすることで、検索の網を広げています。
実務では、1つや2つの断片では情報が足りないことが多いため、多めに取得してLLMに精査させる方が精度が安定します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| RateLimitError | OpenAIの無料枠終了またはAPI制限 | 有料チャージを行うか、APIのTierを上げる |
| sqlite3.OperationalError | Chromaに必要なSQLiteのバージョンが古い | `pip install pysqlite3-binary` を入れ、コード冒頭で上書きする |
| 回答が「わかりません」ばかり | チャンク分割が不適切 | `chunk_overlap` を増やして、文脈の切れ目をカバーする |

特に2番目のSQLiteのエラーは、古いLinux環境（Amazon Linux 2など）でよく遭遇します。
ローカルで動いているのにデプロイした瞬間に動かなくなる原因の9割はこれです。

## 次のステップ

RAGパイプラインが動くようになったら、次は「精度の評価」に挑戦してください。
AIが正しく回答できているかを人間が目視で確認するのは、100件を超えたあたりで限界が来ます。
「Ragas」というライブラリを使えば、LLM自身にRAGの精度を採点させることが可能です。

また、今回はPDF 1つでしたが、これをフォルダ内の全ファイルに対応させたり、WebサイトのURLを読み込ませたりするように拡張するのも面白いでしょう。
LangChainには `DirectoryLoader` や `WebBaseLoader` など、これらを1行で実現する部品が揃っています。

最終的には、このスクリプトを「Streamlit」や「FastAPI」と組み合わせて、Webアプリケーションとして公開することを目指してみてください。
「自分で作ったツールが、自分の知識を元に答えてくれる」という体験は、AI開発の醍醐味そのものです。

## よくある質問

### Q1: 社内の機密情報をOpenAIのAPIに投げても大丈夫ですか？

OpenAIのAPI経由で送信されたデータは、モデルの学習には利用されないことが規約で明記されています（2024年現在）。
ただし、社内規定で「外部API自体がNG」な場合は、埋め込みモデルをローカルのHuggingFaceモデル（e5など）に置き換え、LLMをOllamaなどのローカル実行に切り替える必要があります。

### Q2: PDF以外のファイル（ExcelやWord）も読み込めますか？

はい、可能です。
LangChainには `UnstructuredWordDocumentLoader` や `UnstructuredExcelLoader` が用意されています。
ただし、Excelのような構造化データはRAGと相性が悪いため、CSVに変換して読み込ませるか、Pandasを活用する別の手法（Pandas Agentなど）を検討する方が賢明です。

### Q3: 検索精度をさらに上げるにはどうすればいいですか？

「ハイブリッド検索」を検討してください。
ベクトル検索（意味の類似度）だけでなく、キーワード検索（BM25など）を組み合わせる手法です。
特定の製品名や型番など、一文字でも間違えると意味が変わる情報を扱う場合は、キーワード検索を併用しないと実務レベルの精度は出ません。

---

## あわせて読みたい

- [PythonとLangChainで自分専用のPDF検索AIチャットボットを作る方法](/posts/2026-06-28-local-rag-langchain-faiss-tutorial/)
- [PythonでRAGを自作する！ローカル検索の実装と使い方入門](/posts/2026-06-17-python-rag-tutorial-local-implementation/)
- [Gemma 2の隠し機能「MTP」を使い倒す！推論を高速化させる実装ガイド](/posts/2026-04-07-gemma-2-mtp-inference-acceleration-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "社内の機密情報をOpenAIのAPIに投げても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "OpenAIのAPI経由で送信されたデータは、モデルの学習には利用されないことが規約で明記されています（2024年現在）。 ただし、社内規定で「外部API自体がNG」な場合は、埋め込みモデルをローカルのHuggingFaceモデル（e5など）に置き換え、LLMをOllamaなどのローカル実行に切り替える必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "PDF以外のファイル（ExcelやWord）も読み込めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、可能です。 LangChainには UnstructuredWordDocumentLoader や UnstructuredExcelLoader が用意されています。 ただし、Excelのような構造化データはRAGと相性が悪いため、CSVに変換して読み込ませるか、Pandasを活用する別の手法（Pandas Agentなど）を検討する方が賢明です。"
      }
    },
    {
      "@type": "Question",
      "name": "検索精度をさらに上げるにはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "「ハイブリッド検索」を検討してください。 ベクトル検索（意味の類似度）だけでなく、キーワード検索（BM25など）を組み合わせる手法です。 特定の製品名や型番など、一文字でも間違えると意味が変わる情報を扱う場合は、キーワード検索を併用しないと実務レベルの精度は出ません。 ---"
      }
    }
  ]
}
</script>
