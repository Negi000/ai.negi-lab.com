---
title: "PythonでRAGを自作する！ローカル検索の実装と使い方入門"
date: 2026-06-17T00:00:00+09:00
slug: "python-rag-tutorial-local-implementation"
cover:
  image: "/images/posts/2026-06-17-python-rag-tutorial-local-implementation.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "LangChain"
  - "ChromaDB"
  - "RAG実装"
  - "Python"
  - "ベクトル検索"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 自分の持っているPDFファイルを読み込み、その内容について回答するPythonスクリプト
- LangChainとChromaDBを組み合わせた、最も標準的で拡張性の高いRAGパイプライン
- プログラム経験が少しあれば、コピペと環境構築だけで「自分専用の知恵袋」が手に入ります

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBで将来的なローカルLLM/RAGの完全オフライン化に最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

RAGの実装において、最も重要なのは「メモリ（RAM）」と「API料金」の2点です。
今回の構成ではベクトルデータベースをローカルで動かすため、最低でもメモリは16GB、できれば32GBあると安定します。
私はRTX 4090を2枚積んでいますが、今回のコード自体はMacBook AirなどのノートPCでも十分に動作可能です。

料金面では、OpenAIのAPI（gpt-4o-mini）を使用します。
100ページ程度のPDFをベクトル化して数回質問する程度なら、1回あたり1円もかかりません。
ただし、何万件という大規模な文書を扱う場合は、計算リソースよりも「Embedding（ベクトル化）」のコストが蓄積していく点に注意してください。

もし完全に無料で済ませたい場合は、LLM部分を後述する「Ollama」に差し替えることも可能ですが、まずは確実かつ高速に動くAPIベースで基礎を固めるのが成功への近道です。

## なぜこの方法を選ぶのか

RAGを作る方法は、DifyやAzure AI Searchなど多くの選択肢がありますが、今回はあえて「Python + LangChain」のコードベースを選びます。
理由はシンプルで、ノーコードツールではブラックボックスになりがちな「検索ロジック」を細かくチューニングできるからです。

実務でRAGを導入すると、必ず「なぜこの回答になったのか？」という精度の壁にぶつかります。
その際、チャンク分割のサイズを1文字単位で調整したり、検索アルゴリズムをハイブリッド検索に変えたりできる自由度が、最終的な実用性を左右します。
「動くものを作る」だけでなく「仕事で勝てる精度まで追い込める」構成が、このスクリプトの着地点です。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
Pythonの仮想環境（venvやconda）を作成してから実行することを強くおすすめします。

```bash
# RAGに必要な主要ライブラリを一括インストール
pip install langchain langchain-openai chromadb pypdf python-dotenv
```

各ライブラリの役割を説明します。
`langchain` はAI処理の骨組みを作り、`langchain-openai` はOpenAIのモデルを扱うためのプラグインです。
`chromadb` はベクトルデータを保存するデータベース、`pypdf` はPDFからテキストを抽出するために使用します。
バージョン依存によるエラーを防ぐため、Python 3.10以上を使用してください。

⚠️ **落とし穴:**
Windows環境で `chromadb` のインストールに失敗する場合、多くは「C++ ビルドツール」が不足しています。
Visual Studio Installerから「C++ によるデスクトップ開発」をチェックしてインストールするか、おとなしくWSL2（Linux環境）で動かすのが賢明です。私は結局、全ての検証をUbuntuで行っています。

## Step 2: 基本の設定

次に、APIキーの設定とモデルの初期化を行います。
APIキーをコードに直書きするのは、セキュリティの観点から絶対に避けてください。

```python
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# .envファイルから環境変数を読み込む
load_dotenv()

# APIキーの確認
if "OPENAI_API_KEY" not in os.environ:
    raise ValueError("OPENAI_API_KEYを環境変数に設定してください。")

# モデルの初期化
# 埋め込みモデル（文書をベクトル化する担当）
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 回答生成モデル（検索結果を元に文章を作る担当）
# 実用性を重視してgpt-4o-miniを選択（安くて速いため）
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

`text-embedding-3-small` を選んだ理由は、前世代のモデルよりも安価で、かつ精度が高いからです。
また、`temperature=0` に設定するのは、RAGにおいて「モデルの勝手な想像（ハルシネーション）」を最小限に抑え、検索結果に忠実な回答をさせるためです。

## Step 3: 動かしてみる

いよいよPDFを読み込んで検索可能な状態にします。
スクリプトと同じディレクトリに `data` というフォルダを作り、そこに適当なPDFを1つ入れておいてください。

```python
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# 1. PDFの読み込み
loader = PyPDFLoader("./data/your_document.pdf")
raw_docs = loader.load()

# 2. テキストの分割（チャンク化）
# なぜ分割するのか：LLMには一度に読み込める文字数制限があり、
# かつ関連性の高い部分だけをピンポイントで抽出するためです。
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    separators=["\n\n", "\n", "。", "、", " "]
)
docs = text_splitter.split_documents(raw_docs)

# 3. ベクトルデータベースへの保存
# local_dbというフォルダにデータが永続化されます
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    persist_directory="./local_db"
)

# 4. 検索と回答の実行
from langchain.chains import RetrievalQA

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3})
)

query = "この資料の要点を3つで教えてください"
result = qa_chain.invoke(query)

print(result["result"])
```

### 期待される出力

```
提供された資料に基づくと、主な要点は以下の3点です。
1. ○○プロジェクトの目的は、次世代のAI活用基盤を構築することにある。
2. 2024年度の予算配分は、前年度比で20%増加している。
3. 実施スケジュールは、Q3までにプロトタイプを完成させる予定である。
```

ここで重要なのは `chunk_overlap` の設定です。
文章をぶつ切りにすると、前後の文脈が壊れて検索にヒットしにくくなります。
100文字程度「重ねて」分割することで、文脈の断絶を防いでいます。これは実務的なRAG構築の鉄則です。

## Step 4: 実用レベルにする

最小限の構成で動いたら、次は「実務で使えるレベル」に引き上げます。
具体的には、回答の根拠となった「参照元ソース」を表示できるようにします。
これができないと、AIが嘘をついているのか、本当に資料に書いてあるのか判断できません。

```python
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# 独自のプロンプトを定義
# AIに「資料にないことは答えない」と厳格に指示するのが実務のコツです
system_prompt = (
    "あなたは誠実なアシスタントです。以下のコンテキストのみを使用して質問に答えてください。"
    "コンテキストから答えが見つからない場合は「資料に記載がありません」と答えてください。"
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

# チェーンの再構築
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(vectorstore.as_retriever(), question_answer_chain)

# 実行
response = rag_chain.invoke({"input": "予算の詳細は？"})

print(f"回答: {response['answer']}")
print("\n--- 参照元 ---")
for doc in response["context"]:
    print(f"Source: {doc.metadata['source']} (Page: {doc.metadata['page']})")
```

このように、メタデータ（ファイル名やページ番号）を表示させることで、ユーザーの信頼度が格段に上がります。
私はクライアントに納品する際、必ずこの「出典表示機能」をセットにしています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError: No module named 'pypdf'` | ライブラリの不足 | `pip install pypdf` を実行してください |
| `RateLimitError` | APIの使用制限 | 支払い情報の登録を確認し、Tierを上げてください |
| 全く関係ない回答が返る | 検索の精度不足 | `chunk_size` を小さくするか、検索件数 `k` を増やしてください |
| 日本語が文字化けする | PDFのエンコード問題 | `UnstructuredPDFLoader` など別のローダーを試してください |

## 次のステップ

この記事で、RAGの「基本パイプライン」は完成しました。
しかし、ここがスタート地点です。
実務でさらに精度を上げるためには、以下の3つの方向に拡張することをおすすめします。

1. **ハイブリッド検索の実装**: ベクトル検索だけでなく、キーワード検索（BM25）を組み合わせる。
2. **Re-ranking（再ランク付け）**: 検索された候補を、Cohereなどのリランカーモデルでもう一度並び替える。
3. **ローカルLLMへの移行**: `OpenAIEmbeddings` を `HuggingFaceEmbeddings` に、`ChatOpenAI` を `Ollama` に変えるだけで、完全オフラインで動作するプライベートRAGになります。

まずは今回のスクリプトをベースに、自分の持っている議事録や技術書を読み込ませて、検索の「クセ」を掴んでみてください。
その積み重ねが、AIを「おもちゃ」から「武器」に変える唯一の方法です。

## よくある質問

### Q1: PDFがスキャンされた画像形式なのですが、読み込めますか？

`pypdf` では画像の中のテキストは読み取れません。
その場合は `pytesseract` などのOCRエンジンを併用するか、Azure AI Document Intelligenceのような高機能なパーサーを使う必要があります。実務ではこちらが標準です。

### Q2: データベースをクラウド化したい場合はどうすればいいですか？

ChromaDBをサーバーモードで動かすか、PineconeやWeaviateといったフルマネージドサービスを使います。
コードの `vectorstore` の部分を差し替えるだけで対応可能なので、まずはローカルでロジックを固めるのが先決です。

### Q3: 回答が遅いと感じるのですが、改善策はありますか？

回答速度（レイテンシ）のボトルネックは、多くの場合LLMの生成時間にあります。
`gpt-4o-mini` などの高速なモデルを使うか、ストリーミング再生（文字が順次表示される形式）を実装することで、体感速度を劇的に向上させられます。

---

## あわせて読みたい

- [Gemma 2の隠し機能「MTP」を使い倒す！推論を高速化させる実装ガイド](/posts/2026-04-07-gemma-2-mtp-inference-acceleration-guide/)
- [MemPalace 使い方：AIエージェントの長期記憶を劇的に改善するオープンソース実装](/posts/2026-06-07-mempalace-ai-memory-system-review/)
- [四足歩行ロボットの「脳」がオープンソースで民主化される時代がやってきました](/posts/2026-02-19-botbot-open-source-legged-robot-brain-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "PDFがスキャンされた画像形式なのですが、読み込めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "pypdf では画像の中のテキストは読み取れません。 その場合は pytesseract などのOCRエンジンを併用するか、Azure AI Document Intelligenceのような高機能なパーサーを使う必要があります。実務ではこちらが標準です。"
      }
    },
    {
      "@type": "Question",
      "name": "データベースをクラウド化したい場合はどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ChromaDBをサーバーモードで動かすか、PineconeやWeaviateといったフルマネージドサービスを使います。 コードの vectorstore の部分を差し替えるだけで対応可能なので、まずはローカルでロジックを固めるのが先決です。"
      }
    },
    {
      "@type": "Question",
      "name": "回答が遅いと感じるのですが、改善策はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "回答速度（レイテンシ）のボトルネックは、多くの場合LLMの生成時間にあります。 gpt-4o-mini などの高速なモデルを使うか、ストリーミング再生（文字が順次表示される形式）を実装することで、体感速度を劇的に向上させられます。 ---"
      }
    }
  ]
}
</script>
