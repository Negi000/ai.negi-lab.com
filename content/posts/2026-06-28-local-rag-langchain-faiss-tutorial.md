---
title: "PythonとLangChainで自分専用のPDF検索AIチャットボットを作る方法"
date: 2026-06-28T00:00:00+09:00
slug: "local-rag-langchain-faiss-tutorial"
cover:
  image: "/images/posts/2026-06-28-local-rag-langchain-faiss-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "RAG"
  - "LangChain"
  - "FAISS"
  - "ローカルLLM"
  - "Python"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 手持ちのPDFファイルを読み込み、その内容に基づいて回答するローカル完結型のRAG（検索拡張生成）システムを構築します。
- 前提知識: Pythonの基本的な文法（変数、関数、pipでのインストール）を理解していること。
- 必要なもの: Python 3.10以降の環境、8GB以上のメモリ（16GB推奨）、インターネット接続（ライブラリとモデルの初回ダウンロード用）。

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

## 先に確認するスペック・料金

今回の構成は「完全無料・完全ローカル」を目指します。外部API（OpenAIなど）への課金は一切発生しませんが、その分PCのスペックが重要になります。

最低限必要なのは、メモリ16GBを搭載したPCです。8GBでも動きますが、PDFのページ数が多いとベクトル変換中にスワップが発生し、レスポンスが数分単位まで落ちる可能性があります。もしWindows機でGPU（NVIDIA RTXシリーズ）を持っているなら、VRAMは8GB以上あると推論速度が劇的に向上します。

Macユーザーなら、M1以降のApple Siliconを搭載し、メモリが16GB以上あれば十分に実用的な速度で動作します。もしこれからハードウェアを揃えるなら、ローカルLLMの検証を快適にするためにメモリは「積めるだけ積む」のが鉄則です。私は自宅のRTX 4090 2枚挿しマシンで検証していますが、今回のコードは一般的なノートPCでも動くように軽量なモデルを選定しています。

## なぜこの方法を選ぶのか

RAGを構築する手段として、DifyやAnywhereLLMのようなノーコードツールを使う方法もあります。しかし、実務で「特定の業務フローに組み込みたい」「機密情報の漏洩を防ぐために完全にオフラインで動かしたい」という要望が出た際、ノーコードツールではカスタマイズの限界がすぐに来ます。

今回は、現在のデファクトスタンダードである「LangChain」と、軽量で高速なベクトルデータベース「FAISS」を組み合わせます。この構成は、将来的にクラウドのベクトルDB（Pineconeなど）に移行したり、LLMをGPT-4oに差し替えたりといった拡張が容易です。「中身がどう動いているか」をコードレベルで理解しておくことが、結局は一番の近道になります。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。仮想環境（venvなど）を作ってから作業することをお勧めします。

```bash
# LangChain本体と関連ライブラリ
pip install langchain langchain-community langchain-huggingface

# PDF読み込み用
pip install pypdf

# ベクトルデータベース（CPU版）
pip install faiss-cpu

# 日本語の埋め込みモデル用
pip install sentence-transformers
```

`langchain-huggingface`は、HuggingFaceにあるオープンソースの埋め込みモデルを利用するために必要です。`faiss-cpu`は、Facebookが開発した高速な類似検索ライブラリで、今回は環境構築が容易なCPU版を選択しています。GPU版（faiss-gpu）もありますが、小規模なローカル検索ならCPU版で十分なレスポンス（0.1秒以下）が出ます。

⚠️ **落とし穴:** Windows環境で`faiss-cpu`のインストールに失敗する場合は、Microsoft Visual C++ 再頒布可能パッケージが不足していることが多いです。公式サイトから最新版をインストールしてください。

また、今回はLLM本体として「Ollama」を使用します。公式サイト（ollama.com）からアプリをダウンロード・インストールし、ターミナルで以下のコマンドを実行しておいてください。

```bash
ollama run llama3
```

これにより、Meta社が公開している高性能なLLM「Llama 3」がローカルで起動可能な状態になります。

## Step 2: 基本の設定

RAGにおいて最も重要なのは「Embedding（埋め込み）」モデルの選択です。今回は日本語に強い「multilingual-e5-base」を使用します。

```python
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama

# 1. 埋め込みモデルの設定
# intfloat/multilingual-e5-base は日本語の検索精度が高いことで有名です。
# 最初の実行時に約1GBのモデルがダウンロードされます。
embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-base")

# 2. ローカルLLMの設定 (Ollama)
# 事前に `ollama run llama3` を実行している必要があります。
llm = Ollama(model="llama3")
```

なぜ`multilingual-e5-base`にするのか。それは、このモデルが「クエリ（質問）」と「ドキュメント（回答元）」を区別してベクトル化できるからです。以前、汎用的なモデルを試した際は、単語の一致ばかりを拾ってしまい、意味の文脈を無視した回答が目立ちました。E5シリーズに変えてからは、文脈を汲み取った検索が安定するようになりました。

## Step 3: 動かしてみる

実際にPDFを読み込み、データベース化して質問を投げます。手元に適当なPDF（マニュアルや技術書など）を用意してください。

```python
# 3. PDFの読み込みと分割
loader = PyPDFLoader("your_document.pdf") # ここに自分のPDFファイル名を指定
docs = loader.load()

# 文章を適切な長さに切る。
# チャンクサイズ500、オーバーラップ50という設定は、
# 情報を落としすぎず、かつLLMのコンテキスト窓を圧迫しないバランスの良い値です。
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
splits = text_splitter.split_documents(docs)

# 4. ベクトルデータベースの作成
# 分割した文章をベクトル化してFAISSに保存します。
vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)

# 5. 検索と回答（RAGパイプライン）
from langchain.chains import RetrievalQA

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever()
)

# 質問を投げる
query = "この書類に書かれている主要なポイントを3つ教えてください。"
response = qa_chain.invoke(query)

print("--- 質問内容 ---")
print(query)
print("\n--- 回答 ---")
print(response["result"])
```

### 期待される出力

```
--- 質問内容 ---
この書類に書かれている主要なポイントを3つ教えてください。

--- 回答 ---
提供された資料に基づくと、主要なポイントは以下の3点です。
1. ○○プロジェクトの目的は、次世代の分散型システムの構築である。
2. 開発スケジュールは2024年第3四半期から開始され、2025年春にリリース予定。
3. 予算は、初期インフラ投資を含めて1,500万円を見込んでいる。
```

結果を読み解くポイントは、回答が「自分の知識」ではなく「資料内の記述」に基づいているかどうかです。ローカルLLMはたまに嘘をつく（ハルシネーション）ことがあるため、`RetrievalQA`の設定で回答の根拠となったソースを返すように拡張することも可能です。

## Step 4: 実用レベルにする

上記のコードはシンプルですが、実務で使うには「検索精度の向上」と「再利用性」が欠かせません。毎回PDFをベクトル化するのは時間の無駄なので、一度作ったデータベースを保存・再利用するように改造しましょう。

```python
# データベースの保存
vectorstore.save_local("faiss_index")

# データベースの読み込み（2回目以降）
new_vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True # ローカル環境のみでTrueにすること
)

# より高度な検索設定
retriever = new_vectorstore.as_retriever(
    search_type="mmr", # 類似度だけでなく多様性も考慮して検索する
    search_kwargs={'k': 5, 'fetch_k': 10} # 5つの有力な情報を拾う
)

# プロンプトエンジニアリングの追加
from langchain.prompts import PromptTemplate

template = """あなたは誠実なアシスタントです。以下の資料を参考にして、質問に日本語で回答してください。
資料に答えがない場合は「わかりません」と答えてください。嘘をついてはいけません。

資料: {context}

質問: {question}

回答:"""

PROMPT = PromptTemplate(template=template, input_variables=["context", "question"])

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": PROMPT}
)
```

「MMR（Maximal Marginal Relevance）」を採用したのがミソです。通常の検索では似たような文言ばかりがヒットして情報が偏ることがありますが、MMRを使うと「似ているけれど少し違う視点の文章」を優先的に拾ってくれます。これにより、LLMがより多角的な情報をもとに回答できるようになります。

また、プロンプトを明示することで、ローカルLLM特有の「英語で回答し始める現象」や「勝手に一般常識で補完して嘘をつく現象」を抑制できます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError: No module named 'pypdf'` | ライブラリのインストール漏れ | `pip install pypdf` を実行する |
| `pydantic.v1.error_wrappers.ValidationError` | LangChainのバージョン競合 | 各パッケージを最新版にアップグレードする |
| 回答が英語になる | プロンプトが不足している | プロンプトに「必ず日本語で回答して」と明記する |
| メモリ不足で終了する | PDFが巨大すぎる、またはRAM不足 | チャンクサイズを下げるか、ページを絞って読み込む |

## 次のステップ

この記事の内容をマスターしたら、次は「RAGの精度評価」に挑戦してみてください。具体的には「Ragas」というライブラリを使い、生成された回答の妥当性を数値化（0〜1.0）することです。

実務では「なんとなく動く」では不十分で、「どれくらいの確率で正しい情報を拾えているか」の指標が求められます。また、複数のPDFファイルをフォルダに放り込み、自動的にすべてを読み込んでデータベースを同期させるバッチ処理を作成するのも良い練習になります。

私の経験上、RAGの精度は「LLMの性能」よりも「データの切り出し方（チャンキング）」と「埋め込みモデルの品質」に依存します。今回のコードをベースに、自分にとって最適な「切り出しサイズ」を探ってみてください。

## よくある質問

### Q1: 会社で使う場合、セキュリティ面で気をつけることはありますか？

この構成は完全にローカルで動作するため、外部にデータが送信されることはありません。ただし、HuggingFaceのモデルをダウンロードする際は外部通信が発生します。完全にオフラインの環境で動かす場合は、一度インターネットがある環境でモデルをキャッシュさせ、そのディレクトリをコピーする必要があります。

### Q2: PDFの図表やグラフも検索対象にできますか？

今回の`PyPDFLoader`はテキスト情報のみを抽出します。図表やグラフを認識させたい場合は、PDFを画像に変換してOCR（光学文字認識）をかけるか、Unstructuredのようなマルチモーダル対応のローダーを導入する必要があります。これらは処理が重いため、まずはテキストから始めるのが無難です。

### Q3: 回答速度を上げるにはどうすればいいですか？

Ollamaのモデルをより軽量なもの（`phi3`や`gemma:2b`など）に変更するのが最も効果的です。また、GPUがある場合は、PyTorchがGPUを認識しているか確認してください。CPUのみで動作させている場合は、スレッド数を制限することで他ソフトの動作を妨げずに処理できる場合もあります。

---

## あわせて読みたい

- [MemPalace 使い方：AIエージェントの長期記憶を劇的に改善するオープンソース実装](/posts/2026-06-07-mempalace-ai-memory-system-review/)
- [PythonでRAGを自作する！ローカル検索の実装と使い方入門](/posts/2026-06-17-python-rag-tutorial-local-implementation/)
- [Apple Siliconで爆速LLM。MLXを使ったローカルLLM環境構築ガイド](/posts/2026-06-16-apple-silicon-mlx-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "会社で使う場合、セキュリティ面で気をつけることはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "この構成は完全にローカルで動作するため、外部にデータが送信されることはありません。ただし、HuggingFaceのモデルをダウンロードする際は外部通信が発生します。完全にオフラインの環境で動かす場合は、一度インターネットがある環境でモデルをキャッシュさせ、そのディレクトリをコピーする必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "PDFの図表やグラフも検索対象にできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "今回のPyPDFLoaderはテキスト情報のみを抽出します。図表やグラフを認識させたい場合は、PDFを画像に変換してOCR（光学文字認識）をかけるか、Unstructuredのようなマルチモーダル対応のローダーを導入する必要があります。これらは処理が重いため、まずはテキストから始めるのが無難です。"
      }
    },
    {
      "@type": "Question",
      "name": "回答速度を上げるにはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaのモデルをより軽量なもの（phi3やgemma:2bなど）に変更するのが最も効果的です。また、GPUがある場合は、PyTorchがGPUを認識しているか確認してください。CPUのみで動作させている場合は、スレッド数を制限することで他ソフトの動作を妨げずに処理できる場合もあります。 ---"
      }
    }
  ]
}
</script>
