---
title: "PythonとLangChainで作るRAGパイプライン実装入門"
date: 2026-09-07T00:00:00+09:00
slug: "langchain-rag-local-pdf-tutorial"
cover:
  image: "/images/posts/2026-09-07-langchain-rag-local-pdf-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "LangChain 使い方"
  - "RAG Python 実装"
  - "Chroma VectorDB"
  - "OpenAI API 入門"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- ローカルにあるPDFファイルを読み込み、その内容に基づいてAIが回答するRAG（検索拡張生成）システムをPythonで作ります。
- 汎用的なLangChainと、軽量なベクトルデータベースであるChroma、そしてOpenAIのAPIを組み合わせて構築します。
- 最終的に、自分のPCにある独自の資料について「○○について教えて」と質問して、正確な引用付きで回答が得られる状態を目指します。

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

前提知識：
- Pythonの基本的な文法（変数、関数、pipでのインストール）がわかること
- ターミナルまたはコマンドプロンプトの操作ができること

必要なもの：
- OpenAI APIキー（従量課金制、1ドル程度の残高があれば十分です）
- Python 3.10以降がインストールされた環境
- 検索対象にしたいPDFファイル（1〜2枚の簡単なものでOK）

## 先に確認するスペック・料金

RAGの実装において、最も重要なのは「Embedding（ベクトル化）」のコストと、「Vector DB（ベクトルデータベース）」の動作環境です。
今回の構成ではOpenAIの`text-embedding-3-small`モデルを使いますが、これは100万トークンあたり約0.02ドル（約3円）と極めて安価です。
数万ページの文書を読み込ませない限り、個人の検証レベルであれば10円もかかりません。

ハードウェアについては、今回の構成（Chroma + OpenAI API）であれば、メモリ8GBのMacBook Airでも十分に動作します。
もし将来的にローカルLLM（Llama 3やQwenなど）を動かしたい場合は、VRAM 12GB以上のGPU（RTX 3060 12GBやRTX 4060 Ti 16GBなど）を推奨します。
私はRTX 4090を2枚挿していますが、これは推論速度を0.1秒単位で削るためであり、最初の学習段階ではオーバースペックです。

## なぜこの方法を選ぶのか

RAGを実装する手段は、LlamaIndexを使う方法や、Pineconeのようなクラウド型DBを使う方法など、無数にあります。
その中で今回「LangChain + Chroma」を選ぶ理由は、カスタマイズ性と環境構築の容易さのバランスが最も優れているからです。

LlamaIndexはRAGに特化しており非常に強力ですが、内部処理がブラックボックス化されやすく、実務で細かい挙動を制御したい時に苦労します。
一方、LangChainは各パーツ（Document Loader、Splitter、VectorStore）が独立しているため、仕組みを理解しながら組むのに最適です。
また、ChromaはDockerなどを立てる必要がなく、Pythonライブラリとしてローカルディレクトリにデータを保存できるため、デバッグが非常に楽です。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
実務では環境を汚さないよう、venvやcondaでの仮想環境構築を強く推奨します。

```bash
# 仮想環境の作成と有効化（推奨）
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# 必要なライブラリの一括インストール
pip install langchain langchain-openai langchain-community chromadb pypdf tictoken
```

`pypdf`はPDFの解析に、`chromadb`はベクトルデータの保存に使用します。
`tictoken`はOpenAIのトークン数を計算するためのライブラリで、これが無いとエラーが出るケースが多いため事前に入れておきます。

⚠️ **落とし穴:**
Windows環境で`chromadb`をインストールする際、C++のビルドツールが不足しているとエラーが出ることがあります。
その場合は「Visual Studio Build Tools」をインストールし、「C++ によるデスクトップ開発」にチェックを入れて更新してください。
これ、SIer時代に若手エンジニアが必ずと言っていいほどハマるポイントでした。

## Step 2: 基本の設定

次に、APIキーの設定とデータの準備を行います。
コード内にAPIキーを直書きするのは、セキュリティの観点から絶対に避けてください。

```python
import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import Chroma

# 環境変数の設定（実際には .env ファイルなどから読み込むのがベスト）
os.environ["OPENAI_API_KEY"] = "your-api-key-here"

# 1. モデルの初期化
# 埋め込みモデル：text-embedding-3-smallは安くて高性能な最新版です
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# LLM：今回はコスパ重視で gpt-4o-mini を選択します
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

`temperature=0`にする理由は、RAGにおいて「事実に基づいた回答」を求めるためです。
値が高いとAIが勝手に話を盛る（ハルシネーションを起こす）確率が上がり、業務ツールとしては使い物にならなくなります。

## Step 3: 動かしてみる

ここでは「PDFを読み込む」「分割する」「ベクトル化して保存する」というRAGの心臓部を実装します。
まずはスクリプトと同じフォルダに `data.pdf` という名前で適当なPDFを置いてください。

```python
# 2. ドキュメントの読み込み
loader = PyPDFLoader("data.pdf")
raw_documents = loader.load()

# 3. テキストの分割（チャンク化）
# 1000文字ごとに区切り、前後の文脈が切れないよう100文字重複させます
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
documents = text_splitter.split_documents(raw_documents)

# 4. ベクトルデータベースの作成と保存
# './db' フォルダにデータが永続化されます
vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory="./db"
)

# 5. 検索と回答の実行
query = "この資料の主要なトピックは何ですか？"
# 関連する上位3つのチャンクを取得
docs = vectorstore.similarity_search(query, k=3)

# 検索結果をコンソールに表示して確認
for i, doc in enumerate(docs):
    print(f"--- 検索結果 {i+1} ---")
    print(doc.page_content[:100] + "...")
```

### 期待される出力

```text
--- 検索結果 1 ---
本プロジェクトの目的は、AIを活用した業務効率化であり、特にRAGを用いた社内文書検索システムの構築に焦点を当てています...
--- 検索結果 2 ---
システム構成図：ユーザーからのクエリはEmbeddingモデルによってベクトル化され、Vector DBとの照合が行われます...
```

ここで重要なのは、AIに投げる前に「ちゃんと関連する文章が拾えているか」を確認することです。
もし期待した文章が拾えていないなら、それはLLMのせいではなく、検索ロジックや分割設定の問題です。

## Step 4: 実用レベルにする

単に検索結果を表示するだけでは不十分です。
実務では、検索結果をLLMに渡し、「以下の文脈を参考にして、質問に答えてください」というプロンプトを構成する必要があります。
LangChainの「RetrievalQA」という機能を使って、これを自動化しましょう。

```python
from langchain.chains import RetrievalQA

# 6. RAGチェーンの構築
# chain_type="stuff" は、検索結果をすべてプロンプトに詰め込む最もシンプルな方式です
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    return_source_documents=True # 引用元を返してくれるように設定
)

# 7. 質問の実行
question = "資料に基づき、導入のメリットを箇条書きで教えてください。"
result = qa_chain.invoke({"query": question})

print("【回答】")
print(result["result"])

print("\n【情報源】")
for doc in result["source_documents"]:
    print(f"- ページ: {doc.metadata['page']} (ファイル: {doc.metadata['source']})")
```

このコードのポイントは `return_source_documents=True` です。
仕事でAIを使う場合、「どこに書いてあったのか」というエビデンスは必須です。
これがあるだけで、ユーザーからの信頼度が劇的に変わります。

また、`search_kwargs={"k": 3}` の値を調整することで、AIに渡す情報の量を制御できます。
情報が多すぎるとコストがかかり、少なすぎると回答が不正確になります。
実務での最適解は、ドキュメントの性質にもよりますが `k=3〜5` 程度に落ち着くことが多いですね。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `OpenAI API Key not found` | 環境変数が正しく読み込まれていない | `os.environ`に直接入れるか、`.env`ファイルと`python-dotenv`を併用する |
| `pypdf`関連のImportError | ライブラリが未インストール | `pip install pypdf`を実行し、IDEのインタープリタ設定を確認する |
| 回答が「分かりません」になる | チャンクサイズが大きすぎて検索精度が落ちている | `chunk_size`を500程度に下げ、`chunk_overlap`を調整する |
| DB作成時にエラーが出る | 前回のゴミデータが残っている | `./db`フォルダを一度削除してから再実行する |

## 次のステップ

お疲れ様でした。これで「PDFを理解して答えるAI」のプロトタイプが完成しました。
このシステムをさらに実用的にするためには、以下の3つのステップに挑戦してみてください。

1. **マルチモーダル対応**:
最近のOpenAI API（gpt-4oなど）は画像を理解できます。PDF内の図表を画像として切り出し、それを説明文としてベクトル化する仕組みを入れると、より高度な回答が可能になります。

2. **ハイブリッド検索の導入**:
ベクトル検索は「意味」で検索しますが、「製品型番」や「専門用語」などの完全一致には弱いです。キーワード検索（BM25など）と組み合わせる「ハイブリッド検索」を実装すると、業務での実用性が格段に上がります。

3. **ローカルLLMへの切り替え**:
OpenAIの代わりに「Ollama」や「llama.cpp」をバックエンドに使うことで、完全にオフライン（機密情報が外に出ない）環境を構築できます。
私の自宅サーバーではRTX 4090を活用して、社外秘のメモをローカルRAGで処理していますが、プライバシーを気にせず使える安心感は格別ですよ。

## よくある質問

### Q1: 大量のPDF（数千ファイル）を読み込ませても大丈夫ですか？

ファイル数が多い場合、初期のベクトル化に時間がかかります。
また、Chromaのインデックス作成も重くなるため、商用環境ではQdrantやWeaviateといったスタンドアロン型のベクトルDBサーバーを検討してください。

### Q2: 日本語の文書だと検索精度が落ちる気がします。

OpenAIのEmbeddingは優秀ですが、日本語特有の表現に弱い場合があります。
その場合は、日本語に特化した埋め込みモデル（`multilingual-e5-large`など）を試してみてください。HuggingFace経由で簡単に利用できます。

### Q3: 回答の生成に時間がかかります（レスポンスが遅い）。

原因はLLMの推論速度か、検索対象のチャンク数が多すぎるかのどちらかです。
まずは `gpt-4o-mini` のような高速なモデルを使い、それでも遅い場合はストリーミング出力（一文字ずつ表示する機能）を実装して、体感速度を改善するのが定石です。

---

## あわせて読みたい

- [AIエージェントをDockerで安全に動かすサンドボックス構築方法](/posts/2026-08-17-ai-agent-safe-docker-sandbox-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "大量のPDF（数千ファイル）を読み込ませても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ファイル数が多い場合、初期のベクトル化に時間がかかります。 また、Chromaのインデックス作成も重くなるため、商用環境ではQdrantやWeaviateといったスタンドアロン型のベクトルDBサーバーを検討してください。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の文書だと検索精度が落ちる気がします。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "OpenAIのEmbeddingは優秀ですが、日本語特有の表現に弱い場合があります。 その場合は、日本語に特化した埋め込みモデル（multilingual-e5-largeなど）を試してみてください。HuggingFace経由で簡単に利用できます。"
      }
    },
    {
      "@type": "Question",
      "name": "回答の生成に時間がかかります（レスポンスが遅い）。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "原因はLLMの推論速度か、検索対象のチャンク数が多すぎるかのどちらかです。 まずは gpt-4o-mini のような高速なモデルを使い、それでも遅い場合はストリーミング出力（一文字ずつ表示する機能）を実装して、体感速度を改善するのが定石です。 ---"
      }
    }
  ]
}
</script>
