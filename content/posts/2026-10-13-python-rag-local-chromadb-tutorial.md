---
title: "Pythonで自社文書を即座に検索できるRAGパイプラインをローカル実装する方法"
date: 2026-10-13T00:00:00+09:00
slug: "python-rag-local-chromadb-tutorial"
cover:
  image: "/images/posts/2026-10-13-python-rag-local-chromadb-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Python RAG 実装"
  - "LangChain 使い方"
  - "ChromaDB 入門"
  - "ローカルLLM 検索"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

この記事では、手元のPDFファイルやテキストデータをLLMに学習させることなく、必要な情報を「検索」して回答させるRAG（Retrieval-Augmented Generation）システムを構築します。
具体的には、LangChainとChromaDBを使い、Embedding（ベクトル化）処理をローカルPCで行うことで、情報のプライバシーを保ちつつ高速に検索できるPythonスクリプトを完成させます。

前提知識として、Pythonの基本的な文法と、環境変数（.env）の扱いを理解している必要があります。
必要なものは、Python 3.10以上の実行環境と、LLMによる回答生成用のOpenAI APIキー、そして検索対象となる任意のテキストファイルです。

## 先に確認するスペック・料金

RAGの実装において最も重要なのは、ベクトル化（Embedding）を行う際のメモリ容量です。
今回は「仕事で使える」レベルを目指すため、Embeddingモデルには日本語性能が高いHuggingFaceのローカルモデルを利用します。
このため、最低でもメモリ16GB以上を推奨します。M1/M2/M3チップ搭載のMacであれば16GBモデル以上、WindowsであればRTX 3060（VRAM 12GB）以上のGPUがあると、検索インデックスの作成が劇的に速くなります。

料金面では、Embeddingをローカルで行うため、OpenAIに支払うのは「検索結果を要約して回答させる」ためのトークン代のみです。
gpt-4o-miniを利用すれば、1,000回の質問を投げても数円から数十円程度で収まります。
もし完全に無料で運用したい場合は、回答生成部分をOllamaなどのローカルLLMに差し替えることも可能ですが、まずは精度の高いOpenAIでパイプラインを組むのが最短ルートです。

## なぜこの方法を選ぶのか

RAGの実装には、OpenAIの「Assistants API」や「Azure AI Search」を使う選択肢もあります。
しかし、私はあえて「LangChain + ChromaDB（ローカル）」の構成を推奨します。
理由は明確で、インデックス作成（Embedding）にOpenAIのAPIを使うと、文書量に比例してコストがかさみ、さらにデータが外部に送信されるため企業のセキュリティポリシーに抵触しやすいからです。

ローカルにベクトルデータベース（ChromaDB）を持つことで、一度インデックスを作れば何度でも無料で高速検索が可能です。
また、LangChainを使うことで、将来的にベクトルDBをPineconeに変えたり、LLMをClaude 3.5 Sonnetに切り替えたりする際の柔軟性が担保されます。
「特定のベンダーに依存しない」構成こそが、実務で長く使えるシステムを作るコツです。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
依存関係が複雑になりがちなので、仮想環境（venvやconda）を作成してから実行してください。

```bash
# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# 必要なライブラリの一括インストール
pip install langchain langchain-openai langchain-community chromadb sentence-transformers pypdf python-dotenv
```

`langchain-community`は、ChromaDBやサードパーティ製ツールとの連携に必要です。
`sentence-transformers`は、日本語テキストをベクトル化するためのローカルモデルを動かすために使用します。
`pypdf`はPDFファイルからテキストを抽出するための標準的なライブラリです。

**落とし穴:**
Windows環境でChromaDBをインストールする際、C++のビルドツールがないとエラーが出ることがあります。
その場合は「Visual Studio Build Tools」をインストールし、「C++ によるデスクトップ開発」にチェックを入れて更新してください。
これ、初心者が一番最初につまずいて諦めるポイントです。

## Step 2: 基本の設定

プロジェクトのルートディレクトリに `.env` ファイルを作成し、OpenAIのAPIキーを記述します。
ソースコードにキーを直書きするのは、GitHubに誤ってプッシュした際に即座に課金被害に遭うリスクがあるため、実務では厳禁です。

```text
OPENAI_API_KEY=sk-xxxx...
```

次に、ドキュメントを読み込み、適切なサイズに分割する処理を書きます。
LLMには一度に送れる文字数制限があるため、長い文書は「チャンク」と呼ばれる塊に分ける必要があります。

```python
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# .envからAPIキーを読み込む
load_dotenv()

# 1. ドキュメントの読み込み
# ここでは例として "manual.pdf" を読み込みます
loader = PyPDFLoader("manual.pdf")
raw_docs = loader.load()

# 2. テキストの分割（チャンキング）
# chunk_sizeは500〜1000文字程度がバランスが良いです
# chunk_overlapは「文脈の切れ目」を防ぐために20%程度重ねます
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n\n", "\n", "。", "、", " ", ""]
)
docs = text_splitter.split_documents(raw_docs)

# 3. Embeddingモデルの設定
# 日本語に強い "intfloat/multilingual-e5-small" を使用します
# これはローカルで動作するため、API代はかかりません
embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")

# 4. ベクトルデータベース（ChromaDB）の初期化と保存
# "db" フォルダに永続化保存します
vector_db = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
```

**なぜこの設定にするのか:**
`RecursiveCharacterTextSplitter` で `separators` を指定しているのは、日本語の文章が変なところで切れないようにするためです。
デフォルト設定だと単語の途中で切れてしまい、検索精度が落ちる原因になります。
また、`multilingual-e5-small` は軽量ながら日本語の検索精度が非常に高く、RTX 3060程度のGPUでも爆速で処理が終わります。

## Step 3: 動かしてみる

インデックスが作成できたら、実際に質問を投げて「関連する文書」が正しく取り出せるか確認します。
まずは回答を生成させず、検索結果だけを表示させてみましょう。

```python
# 検索クエリ
query = "有給休暇の申請方法について教えてください"

# 類似度検索の実行（上位3件を取得）
search_results = vector_db.similarity_search(query, k=3)

print(f"--- 検索結果: {len(search_results)}件 ---")
for i, doc in enumerate(search_results):
    print(f"\n[ソース {i+1}]:")
    print(doc.page_content[:200] + "...") # 冒頭200文字のみ表示
```

### 期待される出力

```
--- 検索結果: 3件 ---

[ソース 1]:
第15条（有給休暇の申請） 社員は、有給休暇を取得しようとする場合、取得希望日の3日前までに、社内システムを通じて申請を行わなければならない。緊急の場合は直属の上司に連絡し...

[ソース 2]:
...休暇に関する規定。有給休暇は入社半年後に10日分付与される。申請フローについては、別紙マニュアルの「勤怠管理システム操作手順」を参照すること。
```

このように、質問に対して「意味が近い」部分が抽出されていれば成功です。
ここで全く関係ない文章が出てくる場合は、Step 2の `chunk_size` を調整するか、PDFの読み込みが文字化けしていないかを確認してください。

## Step 4: 実用レベルにする

検索した結果をLLM（gpt-4o-mini）に渡し、自然な文章で回答を生成させるパイプラインを構築します。
ここでは「質問に対する答えが文書内にない場合、適当に嘘をつかない」ようにシステムプロンプトを調整するのが実務上のポイントです。

```python
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# LLMの設定
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

# RAG専用のプロンプトテンプレートを作成
# 嘘をつかせないための制約を日本語で明示します
prompt_template = """あなたは誠実なアシスタントです。
以下の【コンテキスト】にある情報だけを使って回答してください。
答えが分からない場合は「分かりません」と答え、自分で勝手に情報を作らないでください。

【コンテキスト】
{context}

質問: {question}
回答:"""

PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)

# 検索と回答生成を繋ぐChainを作成
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vector_db.as_retriever(search_kwargs={"k": 3}),
    chain_type_kwargs={"prompt": PROMPT}
)

# 実行
response = qa_chain.invoke("有給休暇は何日前までに申請が必要？")
print(response["result"])
```

**実務での改善ポイント:**
`temperature=0` に設定しているのは、回答のランダム性を排除し、常に同じ根拠に基づいた回答を得るためです。
また、`chain_type="stuff"` は検索結果をすべてプロンプトに詰め込む最もシンプルな手法ですが、文書量が多い場合は `map_reduce` など別の手法を検討する必要があります。
しかし、一般的な社内マニュアル程度であれば、この `stuff` 形式が最も精度が高く、コストも抑えられます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError: No module named 'pypdf'` | ライブラリの不足 | `pip install pypdf` を実行してください。 |
| `OpenAI API Key not found` | .envが読み込めていない | `load_dotenv()` を呼び出す前に環境変数を参照していないか確認。 |
| 検索結果が全く関係ない内容になる | Chunk Sizeが不適切 | `chunk_size` を大きくするか、Embeddingモデルを `e5-large` に上げてみてください。 |
| 実行時にメモリ不足で落ちる | ローカルモデルが重すぎる | HuggingFaceのモデル名を `small` 版に変更するか、CPU実行に切り替えてください。 |

## 次のステップ

ここまでで、基本的なローカルRAGパイプラインが完成しました。
しかし、実務で運用するにはまだ「評価」と「UI」が足りません。

次のステップとしては、以下の3点に挑戦してみてください。
1. **Streamlitを使ったWeb UI化**: Pythonだけで簡単にチャット画面が作れます。
2. **ハイブリッド検索の実装**: ベクトル検索だけでなく、キーワード検索（BM25）を組み合わせることで、専門用語の検索精度が跳ね上がります。
3. **メタデータフィルタリング**: 「2023年度の文書だけから探す」といった条件付けを可能にすることで、古い情報に基づいた誤回答を防げます。

特に、ドキュメントの数が増えてくると、単なるベクトル検索だけでは限界が来ます。
その時は、LlamaIndexなどのよりデータ管理に特化したライブラリへの移行を検討する時期です。

## よくある質問

### Q1: PDFの中に画像（表や図）がある場合、それも読み込めますか？

通常の `PyPDFLoader` ではテキストしか抽出できません。画像内の文字を読み取るには `Unstructured` や `Azure AI Document Intelligence` などのOCR機能を持つライブラリが必要です。今回の構成はテキスト主体のドキュメント向けです。

### Q2: 会社で使う場合、データは本当に安全ですか？

Embedding（ベクトル化）はローカルの `sentence-transformers` で行っているため、文書そのものがOpenAIに送られて学習に使われることはありません。ただし、回答生成時に「検索でヒットした断片」だけはOpenAIのAPIに送信されます。これが許容できない場合は、回答生成もOllamaなどの完全ローカル環境で行う必要があります。

### Q3: 複数のファイルを一度に読み込ませるにはどうすればいいですか？

`DirectoryLoader` を使います。`loader = DirectoryLoader('./data_folder', glob="**/*.pdf", loader_cls=PyPDFLoader)` のように記述すれば、指定したフォルダ内のすべてのPDFを一括でインデックス化できます。

---

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBによりローカルでのEmbeddingと推論を低価格で両立できるため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [PythonとLangChainで作るRAGパイプライン実装入門](/posts/2026-09-07-langchain-rag-local-pdf-tutorial/)
- [PythonとLlamaIndexで作るRAGローカル検索の実装ガイド](/posts/2026-08-30-llamaindex-rag-local-search-guide/)
- [AIエージェントをDockerで安全に動かすサンドボックス構築方法](/posts/2026-08-17-ai-agent-safe-docker-sandbox-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "PDFの中に画像（表や図）がある場合、それも読み込めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "通常の PyPDFLoader ではテキストしか抽出できません。画像内の文字を読み取るには Unstructured や Azure AI Document Intelligence などのOCR機能を持つライブラリが必要です。今回の構成はテキスト主体のドキュメント向けです。"
      }
    },
    {
      "@type": "Question",
      "name": "会社で使う場合、データは本当に安全ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Embedding（ベクトル化）はローカルの sentence-transformers で行っているため、文書そのものがOpenAIに送られて学習に使われることはありません。ただし、回答生成時に「検索でヒットした断片」だけはOpenAIのAPIに送信されます。これが許容できない場合は、回答生成もOllamaなどの完全ローカル環境で行う必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のファイルを一度に読み込ませるにはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "DirectoryLoader を使います。loader = DirectoryLoader('./datafolder', glob=\"/.pdf\", loadercls=PyPDFLoader) のように記述すれば、指定したフォルダ内のすべてのPDFを一括でインデックス化できます。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBによりローカルでのEmbeddingと推論を低価格で両立できるため</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
