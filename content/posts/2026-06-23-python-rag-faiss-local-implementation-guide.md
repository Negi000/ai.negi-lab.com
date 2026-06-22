---
title: "PythonでRAGを自作する！ローカル検索の実装手順ガイド"
date: 2026-06-23T00:00:00+09:00
slug: "python-rag-faiss-local-implementation-guide"
cover:
  image: "/images/posts/2026-06-23-python-rag-faiss-local-implementation-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "LangChain RAG 使い方"
  - "FAISS Python 実装"
  - "ベクトルデータベース ローカル"
  - "OpenAI Embedding 料金"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 手元のPDFやテキストファイルを読み込み、その内容に基づいて回答するRAG（検索拡張生成）システムを構築します。
- LangChainとFAISSを使用し、外部のSaaSデータベースに頼らずローカル環境でベクトル検索を完結させるPythonスクリプトを作成します。
- 動作確認にはOpenAIのAPIを使用しますが、将来的にローカルLLMへ差し替え可能な構成にします。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM/Embeddingモデルを動かすのに最もコスパが良い</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、Pythonの基本的な文法と、環境変数（.envファイル）の扱いを理解している必要があります。

## 先に確認するスペック・料金

RAGの実装において最も重要なのは、開発環境のメモリとAPIコストのバランスです。

今回の構成では、ベクトルデータベースに「FAISS」を使用します。
これはメモリ上で動作するため、ドキュメントが数千ページ規模になるとRAMを消費しますが、個人開発や数冊の技術書程度であれば8GBのメモリでも十分動作します。
ただし、快適に開発を回すなら16GB以上を推奨します。

コスト面では、OpenAIのEmbeddingモデル「text-embedding-3-small」を使用します。
これは1,000,000トークンあたり$0.02と極めて安価で、一般的な技術書1冊（約10万文字）をベクトル化しても数円程度で済みます。
回答生成に使うGPT-4o-miniも安価ですが、頻繁にテストを行う場合は、OpenAIのコンソールでUsage Limit（利用制限）を月額$10程度に設定しておくと安心です。

もし完全無料で構築したい場合は、CPUでも動く「Ollama」を代替案として検討してください。
ただし、今回は「仕事で使える精度」を優先し、EmbeddingとLLMにはOpenAIを採用します。

## なぜこの方法を選ぶのか

RAGを構築する手段として、現在は「LlamaIndex」や「Pinecone」などの便利なライブラリやマネージドサービスが多数存在します。
しかし、実務でカスタマイズ性を求められる現場では、LangChainでパイプラインを自作する能力が不可欠です。

特にベクトルDBにFAISSを選ぶ理由は、その「軽量さ」と「可搬性」にあります。
PineconeのようなクラウドDBは、APIキーの管理やネットワーク遅延、無料枠の制限を考慮しなければなりませんが、FAISSならインデックスをローカルファイルとして保存・配布できます。
これは、機密性の高いドキュメントを扱う社内ツールを作る際に、「データを外部に送らない」という要件を満たすための第一歩となります。
「とりあえず動く」を超えて「本番でどう運用するか」を見据えた際に、最も汎用性が高い構成がこれです。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
Python 3.10以上の環境を用意してください。

```bash
pip install langchain langchain-openai faiss-cpu pypdf python-dotenv
```

各ライブラリの役割を説明します。
- `langchain-openai`: OpenAIのモデルをLangChainから操作するためのSDKです。
- `faiss-cpu`: Facebookが開発した高速なベクトル検索ライブラリです。GPU版もありますが、今回は汎用性を考えCPU版を使います。
- `pypdf`: PDFファイルからテキストを抽出するために必要です。
- `python-dotenv`: APIキーをソースコードに直書きしないためのデファクトスタンダードです。

⚠️ **落とし穴:**
Windows環境で`faiss-cpu`のインストールに失敗する場合は、Microsoft Visual C++ 再頒布可能パッケージが不足している可能性があります。
また、Pythonのバージョンが古すぎるとライブラリの依存関係でエラーが出るため、必ず3.10以降を使用してください。

## Step 2: 基本の設定

プロジェクトのルートディレクトリに`.env`ファイルを作成し、OpenAIのAPIキーを記述してください。

```text
OPENAI_API_KEY=sk-xxxx...
```

次に、ドキュメントを読み込んで「チャンク」と呼ばれる断片に分割するコードを書きます。
なぜ分割が必要かというと、LLMには一度に読み込める文字数（コンテキストウィンドウ）に制限があり、かつ情報の密度を高めるためです。

```python
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# .envからAPIキーを読み込む
load_dotenv()

def create_vector_store(pdf_path):
    # Step 2-1: PDFの読み込み
    # PyPDFLoaderは1ページを1つのDocumentオブジェクトとして扱います
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    # Step 2-2: テキスト分割（チャンキング）
    # chunk_sizeは512〜1024が実務上のスイートスポットです
    # chunk_overlapは文脈を維持するために10%程度重ねます
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", "。", "、", " ", ""]
    )
    docs = text_splitter.split_documents(pages)

    # Step 2-3: 埋め込み（Embedding）とFAISSへの保存
    # text-embedding-3-smallはコストと精度のバランスが最強です
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # ここで実際にOpenAIのAPIを叩いてベクトル化します
    vectorstore = FAISS.from_documents(docs, embeddings)

    # 作成したインデックスをローカルに保存（次回から再利用可能）
    vectorstore.save_local("faiss_index")

    print(f"インデックスを作成しました。チャンク数: {len(docs)}")
    return vectorstore

# 実行例（sample.pdfを同じディレクトリに置いてください）
# vectorstore = create_vector_store("sample.pdf")
```

設定のポイントは`RecursiveCharacterTextSplitter`の`separators`です。
デフォルト設定では日本語の句読点で上手く切れないことがあるため、明示的に「。」などを指定しています。
これを怠ると、文章の途中でブツ切りになり、検索精度が著しく低下します。

## Step 3: 動かしてみる

インデックスができたら、次は質問を投げて関連箇所を検索し、LLMに回答させてみます。

```python
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

def ask_question(query):
    # 保存したインデックスの読み込み
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

    # LLMの設定
    # 実務ではgpt-4o-miniで十分なケースが多いです。レスポンスは1秒以内。
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    # RAGのチェーン（手順）を構築
    # search_kwargs={"k": 3} は「関連する上位3つのチャンクを取得する」という意味です
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3})
    )

    # 質問実行
    response = qa_chain.invoke(query)
    return response["result"]

# 動作確認
# print(ask_question("このドキュメントの要約を教えてください"))
```

### 期待される出力

```
このドキュメントに基づくと、主な内容は以下の3点です。
1. ○○システムの導入手順
2. 設定ファイル（config.json）の記述方法
3. 障害発生時のトラブルシューティング...
```

`allow_dangerous_deserialization=True`という設定に驚くかもしれませんが、これはFAISSが内部で`pickle`を使用しているための警告です。
自分で作ったインデックスを読み込む分には安全ですが、出所不明のインデックスファイルを読み込む際は注意が必要だという実務上のサインです。

## Step 4: 実用レベルにする

ここまでのコードは基本ですが、実務で使うには「回答の根拠（ソース）」を表示する機能が欠かせません。
LLMが嘘をつく「ハルシネーション」を防ぐため、どのページのどの記述を参考にしたかをユーザーに示す必要があります。

また、毎回PDFを読み込んでベクトル化するのは無駄なので、インデックスが存在すればそれを使い、なければ作成するロジックを組み込みます。

```python
from langchain.chains import RetrievalQAWithSourcesChain

def smart_rag_system(pdf_path, query):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    index_path = "faiss_index"

    if os.path.exists(index_path):
        vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    else:
        # Step 2で作った関数を呼び出す
        vectorstore = create_vector_store(pdf_path)

    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    # ソース付きの回答を生成するチェーン
    # chain_type="stuff" は取得したドキュメントをすべてプロンプトに詰め込む最もシンプルな方式
    qa_chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 5})
    )

    result = qa_chain.invoke({"question": query})

    print(f"回答: {result['answer']}")
    print(f"ソース: {result['sources']}")

# 最終的な実行
if __name__ == "__main__":
    target_pdf = "my_document.pdf"
    question = "初期設定のポート番号は何番ですか？"
    smart_rag_system(target_pdf, question)
```

この構成にすることで、「回答の最後に関連ページ番号が表示される」ようになります。
私の経験上、業務利用でユーザーが最も安心するのは「LLMが賢いこと」よりも「どこに書いてあるかすぐ確認できること」です。
このソース提示機能があるだけで、ツールの信頼性は格段に上がります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `RateLimitError` | OpenAIの無料枠終了またはAPI制限 | 支払い設定を確認し、Usage Limitを上げる |
| `KeyError: 'OPENAI_API_KEY'` | .envが読み込めていない | `load_dotenv()`をimport直後に実行しているか確認 |
| 検索精度が極端に低い | チャンクサイズが不適切 | 文章の構造に合わせて`chunk_size`を500〜1500の間で調整 |
| PDFが読み込めない | 暗号化されたPDFや画像のみのPDF | `pypdf`ではなく`pdfminer.six`やOCRライブラリを検討 |

## 次のステップ

この記事で作成したシステムはRAGの「心臓部」です。
これをマスターした後に取り組むべきことは2つあります。

1つ目は「ハイブリッド検索」の実装です。
ベクトル検索（意味で探す）は強力ですが、「商品型番」や「固有のプロジェクト名」などの完全一致検索には弱い側面があります。
これにBM25という伝統的なキーワード検索を組み合わせることで、実務上の精度はさらに20%以上向上します。

2つ目は「ローカルLLMへの移行」です。
今回OpenAIを使った部分を「Ollama」や「llama.cpp」に差し替えてみてください。
RTX 3060以上のGPUがあれば、Llama 3やGemma 2といった最新モデルをローカルで動かし、完全にオフラインで機密情報を処理するRAGが完成します。
この記事の構成はインターフェースをLangChainに統一しているため、モデルの差し替えは数行の変更で済むはずです。

## よくある質問

### Q1: 大量のドキュメントを読み込ませても大丈夫ですか？

FAISSは数万件のチャンクでも高速に検索できますが、すべてメモリに展開されます。
目安として、10万チャンク（一般的な本100冊分以上）を超える場合は、SQLiteをバックエンドに持つ「ChromaDB」や、ディスクベースの検索を検討してください。

### Q2: 精度を上げるための「チャンクサイズ」の正解は？

正解はありませんが、私はまず「800」から始めます。
短すぎると文脈が消え、長すぎると検索に関係ないノイズが混じります。
「1段落がしっかり収まる程度」を意識して、自分の扱うドキュメントの傾向に合わせて微調整するのが実務の鉄則です。

### Q3: 日本語の検索に強いモデルは他にありますか？

OpenAIの`text-embedding-3-small`は日本語でも非常に優秀ですが、より特化したものとしてCohereの`embed-multilingual-v3.0`も選択肢に入ります。
ただし、最初はOpenAIで組み、検索漏れが気になる段階でモデル比較を行うのが効率的です。

---

## あわせて読みたい

- [PythonでRAGを自作する！ローカル検索の実装と使い方入門](/posts/2026-06-17-python-rag-tutorial-local-implementation/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "大量のドキュメントを読み込ませても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "FAISSは数万件のチャンクでも高速に検索できますが、すべてメモリに展開されます。 目安として、10万チャンク（一般的な本100冊分以上）を超える場合は、SQLiteをバックエンドに持つ「ChromaDB」や、ディスクベースの検索を検討してください。"
      }
    },
    {
      "@type": "Question",
      "name": "精度を上げるための「チャンクサイズ」の正解は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "正解はありませんが、私はまず「800」から始めます。 短すぎると文脈が消え、長すぎると検索に関係ないノイズが混じります。 「1段落がしっかり収まる程度」を意識して、自分の扱うドキュメントの傾向に合わせて微調整するのが実務の鉄則です。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の検索に強いモデルは他にありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "OpenAIのtext-embedding-3-smallは日本語でも非常に優秀ですが、より特化したものとしてCohereのembed-multilingual-v3.0も選択肢に入ります。 ただし、最初はOpenAIで組み、検索漏れが気になる段階でモデル比較を行うのが効率的です。 ---"
      }
    }
  ]
}
</script>
