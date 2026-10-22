---
title: "PythonとLangChainで自分専用のドキュメント検索RAGを作る方法"
date: 2026-10-23T00:00:00+09:00
slug: "python-langchain-rag-local-faiss-tutorial"
cover:
  image: "/images/posts/2026-10-23-python-langchain-rag-local-faiss-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Python RAG 構築"
  - "LangChain FAISS 使い方"
  - "ローカルLLM 検索"
  - "OpenAI Embedding 料金"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 手元のPDFファイルを読み込み、その内容に基づいて正確に回答する「ローカル検索型RAGスクリプト」
- 独自のナレッジベース（社内規定、技術ドキュメントなど）をAIに学習させずに参照させる仕組み
- 前提知識：Pythonの基本的な文法（変数、関数、pipインストール）がわかること
- 必要なもの：OpenAI APIキー、Python 3.10以上の環境

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルEmbeddingやLLM推論を高速化するのに最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

RAG（Retrieval-Augmented Generation）を動かす際、最も重要なのは「メモリ（RAM）」と「APIコスト」です。
今回の構成ではベクトルデータベースに「FAISS」という軽量なライブラリを使用します。
数百ページ程度のPDFであれば、一般的なノートPC（メモリ8GB以上）で十分に動作します。
私の環境（RTX 4090 2枚挿し）ではコンマ数秒で検索が終わりますが、CPUのみの環境でも数秒あれば結果は出ます。

料金面では、OpenAIの「text-embedding-3-small」と「gpt-4o-mini」を組み合わせるのが、現時点で最もコストパフォーマンスが高い選択です。
1,000ページのテキストをベクトル化しても数円、1回の質問にかかる費用は0.1円〜0.5円程度に収まります。
もし完全に無料で運用したい場合は、モデルを「Ollama」に、埋め込みを「HuggingFace」のモデルに差し替えることも可能ですが、精度と手軽さを優先して今回はOpenAIのAPIをベースに解説します。

## なぜこの方法を選ぶのか

RAGを実装する手段は山ほどあります。
DifyやMakeなどのノーコードツールを使う方法もありますが、あえてPythonとLangChainで「自作」する理由は、カスタマイズ性と検証のしやすさにあります。

ノーコードツールはブラックボックスになりがちで、「なぜか回答がズレる」という際の原因切り分けが困難です。
また、将来的にローカルLLM（Llama 3やGemma 2）へ移行したり、独自の検索ロジックを組み込んだりする場合、コードで書かれたパイプラインが最も自由度が高いです。
今回は「検索部分をローカル（FAISS）」に置き、「生成部分をクラウド（OpenAI）」に頼るハイブリッド構成にします。
これにより、データの中身をむやみに外部へ送信せず、かつ安価で高性能な推論を手に入れます。

## Step 1: 環境を整える

まずは必要なライブラリを一括でインストールします。
LangChainは更新が非常に早いため、バージョンを固定せずに最新を入れるのが定石ですが、依存関係でハマりやすいので注意が必要です。

```bash
# RAGに必要な主要ライブラリ
pip install langchain langchain-openai langchain-community faiss-cpu pypdf python-dotenv ticket-count
```

`langchain-openai` はOpenAIのモデルを扱う専用パッケージです。
`faiss-cpu` はFacebookが開発した高速なベクトル検索エンジンです。GPU版もありますが、数千件程度のデータならCPU版で十分高速です。
`pypdf` はPDFからテキストを抽出するために使用します。

⚠️ **落とし穴:**
Windowsユーザーの場合、`faiss-cpu` のインストールでエラーが出ることがあります。その場合は、Microsoft Visual C++ 再頒布可能パッケージがインストールされているか確認してください。
また、Python 3.12系だと一部のライブラリが対応していないケースがあるため、安定を狙うなら 3.10 か 3.11 を推奨します。

## Step 2: 基本の設定

プロジェクトのルートディレクトリに `.env` ファイルを作成し、APIキーを書き込みます。
ソースコードに直書きするのは、GitHubに誤って上げた瞬間に残高が溶けるリスクがあるため、絶対に避けてください。

```bash
OPENAI_API_KEY=sk-proj-xxxx...（あなたのキー）
```

次に、Pythonスクリプトの冒頭で環境変数を読み込み、必要なクラスをインポートします。

```python
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

# .envから設定をロード
load_dotenv()

# 埋め込みモデル（テキストを数値に変換する担当）
# text-embedding-3-smallは安くて高性能なので現在の一択です
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 言語モデル（回答を生成する担当）
# 実用性を考えてgpt-4o-miniを選択。1/10の価格で旧GPT-3.5を凌駕します
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

`temperature=0` に設定しているのは、RAGにおいて「モデルの創造性」は不要だからです。
ドキュメントに書いてある事実に基づいた、誠実な回答をさせるための設定です。

## Step 3: 動かしてみる

いよいよPDFを読み込み、ベクトルデータベースを構築します。
ここでは、私が実務で必ず使う「チャンク分割」のテクニックを盛り込んでいます。

```python
def create_rag_system(file_path: str):
    # 1. PDFの読み込み
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    # 2. テキストの分割（チャンク化）
    # chunk_size=1000, overlap=200が最もバランスが良いです
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )
    texts = text_splitter.split_documents(documents)

    # 3. ベクトル化と保存
    # ここでOpenAIのAPIを叩き、テキストをベクトル（数字の羅列）に変換します
    vectorstore = FAISS.from_documents(texts, embeddings)

    return vectorstore

# サンプルのPDF（例: manual.pdf）を指定して実行
# PDFはスクリプトと同じフォルダに置いてください
vectorstore = create_rag_system("manual.pdf")
print("ベクトルデータベースの構築が完了しました。")
```

### 期待される出力

```
ベクトルデータベースの構築が完了しました。
```

ここで重要なのは `chunk_overlap` です。
文章をぶつ切りにすると、前後の文脈が失われて検索精度が落ちます。
200文字ほど重ねて分割することで、文脈を維持したまま検索対象にすることができます。

## Step 4: 実用レベルにする

単に回答させるだけでなく、実務では「どの資料の、どこを参考にしたか」というソース（根拠）の提示が必須です。
これがないと、AIが嘘をついているのか判断できません。

```python
def ask_question(vectorstore, query: str):
    # 検索エンジンとしての設定
    # search_kwargs={"k": 3} は「関連する上位3つのチャンクを探す」という意味
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # チェーンの構築
    # return_source_documents=True で参照元を返してくれるようにします
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )

    # 質問の実行
    response = qa_chain.invoke({"query": query})

    print(f"質問: {query}")
    print(f"回答: {response['result']}")
    print("\n--- 参照元ドキュメント ---")
    for doc in response["source_documents"]:
        page_num = doc.metadata.get("page", "不明")
        print(f"参照ページ: {page_num + 1}ページ目")
        print(f"内容一部: {doc.page_content[:100]}...")
        print("-" * 20)

# 実際の質問例
ask_question(vectorstore, "この製品の保証期間は何年ですか？")
```

このスクリプトは、単なるチャットではなく「証拠付き回答マシン」になります。
`chain_type="stuff"` は、見つけた情報をすべてプロンプトに詰め込む最もシンプルな方式です。
情報量が多い場合は別の方式もありますが、大抵のケース（1回の回答に数ページの参照）であればこれが最も精度が安定します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `AuthenticationError` | APIキーが正しく読み込めていない | `.env` のファイル名と、中に `OPENAI_API_KEY=` が正しく書かれているか確認 |
| `pypdf` が読み込めない | PDFが暗号化されているか、画像ベース | スキャンしたPDFの場合は、OCRライブラリ（pytesseract等）を併用する必要がある |
| 回答が「わかりません」になる | チャンクサイズが小さいか、検索数(k)が不足 | `chunk_size` を増やすか、`search_kwargs={"k": 5}` に増やして試す |

## 次のステップ

この記事で作成したRAGシステムは、全ての処理をメモリ上で行っています。
そのため、プログラムを終了するとベクトルデータは消えてしまいます。
実用化するためには、以下の2点に挑戦してみてください。

1. **ベクトルインデックスの保存と読み込み**: `vectorstore.save_local("faiss_index")` を使えば、二度目以降はPDFを読み込まずに高速起動できます。
2. **Web UIの追加**: `Streamlit` を使えば、このPythonスクリプトをわずか30行程度の追加でブラウザから使える社内ツールに変身させられます。

私の経験上、RAGの精度を左右するのはモデルの性能よりも「いかに綺麗にドキュメントを分割し、ゴミデータを除去するか」という前処理の泥臭い作業です。
まずは手元のPDFで試してみて、期待通りの回答が返ってこない時に「どう分割すればAIが理解しやすいか」を考えるのが、AIエンジニアへの近道です。

## よくある質問

### Q1: PDFではなく、ExcelやWordも読み込めますか？

可能です。LangChainには `UnstructuredExcelLoader` や `Docx2txtLoader` などが用意されています。ただし、Excelは構造化データなので、テキストとして分割するよりも一度CSVに変換してから処理する方が精度が出やすい傾向にあります。

### Q2: 10,000ページを超える膨大な資料がある場合は？

FAISSでも動作しますが、データの管理が大変になります。その場合は、`Chroma` や `Pinecone` といった本格的なベクトルデータベースへの移行を検討してください。また、検索対象が多すぎると「ノイズ」が増えるため、ハイブリッド検索（キーワード検索＋ベクトル検索）の導入が必要になります。

### Q3: 完全にオフラインで動かすことはできますか？

はい、できます。`ChatOpenAI` の代わりに `Ollama` を使い、`OpenAIEmbeddings` の代わりに `HuggingFaceEmbeddings` を使えば、インターネット接続なしの完全ローカルRAGが構築可能です。ただし、回答の質はPCのGPU性能とモデルサイズに依存します。

---

## あわせて読みたい

- [PythonとLlamaIndexで作るRAGローカル検索の実装ガイド](/posts/2026-08-30-llamaindex-rag-local-search-guide/)
- [PythonでRAGを自作する！ローカル検索の実装手順ガイド](/posts/2026-06-23-python-rag-faiss-local-implementation-guide/)
- [Pythonで自社文書を即座に検索できるRAGパイプラインをローカル実装する方法](/posts/2026-10-13-python-rag-local-chromadb-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "PDFではなく、ExcelやWordも読み込めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。LangChainには UnstructuredExcelLoader や Docx2txtLoader などが用意されています。ただし、Excelは構造化データなので、テキストとして分割するよりも一度CSVに変換してから処理する方が精度が出やすい傾向にあります。"
      }
    },
    {
      "@type": "Question",
      "name": "10,000ページを超える膨大な資料がある場合は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "FAISSでも動作しますが、データの管理が大変になります。その場合は、Chroma や Pinecone といった本格的なベクトルデータベースへの移行を検討してください。また、検索対象が多すぎると「ノイズ」が増えるため、ハイブリッド検索（キーワード検索＋ベクトル検索）の導入が必要になります。"
      }
    },
    {
      "@type": "Question",
      "name": "完全にオフラインで動かすことはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、できます。ChatOpenAI の代わりに Ollama を使い、OpenAIEmbeddings の代わりに HuggingFaceEmbeddings を使えば、インターネット接続なしの完全ローカルRAGが構築可能です。ただし、回答の質はPCのGPU性能とモデルサイズに依存します。 ---"
      }
    }
  ]
}
</script>
