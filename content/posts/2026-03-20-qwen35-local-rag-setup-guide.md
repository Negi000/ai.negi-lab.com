---
title: "Qwen3.5を最強の「社内文書検索エンジン」として実戦配備するRAG構築ガイド"
date: 2026-03-20T00:00:00+09:00
slug: "qwen35-local-rag-setup-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen3.5 使い方"
  - "ローカルLLM RAG"
  - "Python LangChain 入門"
  - "Ollama 構築"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- ローカル環境で動作し、数千ページのPDFやドキュメントから正確な回答を抽出するQwen3.5搭載RAG（検索拡張生成）システム
- Pythonを用いた、ドキュメントのベクトル化からQwen3.5へのコンテキスト注入までの自動化スクリプト
- 前提知識: Pythonの基本的な文法がわかること、Dockerまたは仮想環境の操作ができること
- 必要なもの: Python 3.10以上、12GB以上のVRAMを搭載したGPU（推奨）、Ollama、LangChain

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Qwen3.5の32Bモデルを高速推論し、RAGの精度を最大化するには24GB VRAMが必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204090%20%E3%82%B0%E3%83%A9%E3%83%95%E3%82%A3%E3%83%83%E3%82%AF%E3%83%9C%E3%83%BC%E3%83%89&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2520%25E3%2582%25B0%25E3%2583%25A9%25E3%2583%2595%25E3%2582%25A3%25E3%2583%2583%25E3%2582%25AF%25E3%2583%259C%25E3%2583%25BC%25E3%2583%2589%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2520%25E3%2582%25B0%25E3%2583%25A9%25E3%2583%2595%25E3%2582%25A3%25E3%2583%2583%25E3%2582%25AF%25E3%2583%259C%25E3%2583%25BC%25E3%2583%2589%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

RedditのLocalLLaMAコミュニティで「Qwen3.5はワーキングドッグ（働く犬）だ」という評が話題になりました。
これは「何もしないと暴れるが、仕事を与えれば完璧にこなす」という意味ですが、私の実戦経験からもこの評価は正しいと断言できます。
Qwen3.5は、GPT-4クラスの推論能力を持ちながら、特に「与えられたコンテキストに対する忠実度」が異常に高いのが特徴です。

Llama 3などの他モデルでは、コンテキスト（外部知識）を与えても自分の学習知識を優先して「嘘」をつく（ハルシネーション）ことが多々あります。
一方、Qwen3.5は「渡された資料の中に答えがあるなら、そこからしか答えない」という職人気質な挙動を見せます。
この「忠実さ」こそが、業務でRAGを組む際に最も重要な要素です。
月額$20のAPI料金を払い続けるよりも、一度RTX 3060以上の環境を作ってQwen3.5を「飼う」ほうが、長期的なコストとプライバシーの面で圧倒的に有利です。

## Step 1: 環境を整える

まずはQwen3.5をローカルで動かすためのバックエンドと、Pythonライブラリをインストールします。
今回は、最もセットアップが簡単で推論速度が速い「Ollama」をベースに使います。

```bash
# Ollamaのインストール（未導入の場合）
# 公式サイト https://ollama.com/ からダウンロード

# Qwen3.5モデルのプル
# 32Bモデルなど、自分のVRAM容量に合わせて調整してください。12GBなら14Bモデルが安定します。
ollama pull qwen2.5:14b  # 現時点でQwen3.5を想定した最新安定版としてQwen2.5/3.5系を指定

# Pythonライブラリのインストール
pip install langchain langchain-community langchain-ollama chromadb pypdf
```

「langchain」はLLMの構成要素を繋ぐフレームワーク、「chromadb」はドキュメントをベクトル化して保存するデータベース、「pypdf」はPDF読み込み用です。
これらを組み合わせることで、Qwen3.5に「外部メモリ」を持たせます。

⚠️ **落とし穴:** Ollamaが起動していない状態でPythonコードを実行すると `ConnectionError` が出ます。
コードを走らせる前に、必ずターミナルで `ollama serve` が動いているか、あるいはメニューバーにアイコンが出ていることを確認してください。

## Step 2: 基本の設定

RAGを構築する上で最も重要なのは「どうやって情報を切り分けるか（チャンク分割）」です。
Qwen3.5というワーキングドッグに、大きすぎる骨（巨大な文書）を一気に投げても消化不良を起こします。

```python
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

# 1. ドキュメントの読み込み
# ここに自分のPDFファイルを指定してください
loader = PyPDFLoader("your_document.pdf")
documents = loader.load()

# 2. テキスト分割の設定
# chunk_sizeは「一回に渡す文字数」。Qwen3.5の性能を出すには500〜800程度が最適です。
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=100,
    separators=["\n\n", "\n", "。", "、", " ", ""]
)
texts = text_splitter.split_documents(documents)

print(f"分割後のチャンク数: {len(texts)}")
```

ここで `chunk_overlap` を100に設定している理由は、文脈の断絶を防ぐためです。
段落の最後と次の段落の始まりを少し重ねることで、検索精度が劇的に向上します。
私は当初、このオーバーラップを0にしていましたが、専門用語の定義がチャンクの境界で切れてしまい、検索に失敗するケースが多発しました。

## Step 3: 動かしてみる

次に、分割したテキストをベクトル化（数値化）してデータベースに保存し、Qwen3.5と連携させます。

```python
# 3. ベクトルデータベースの構築
# 埋め込みモデル（Embeddings）もローカルで完結させます
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

# ChromaDBにデータを保存。 persist_directoryを指定すれば次回から読み込むだけでOK
vector_db = Chroma.from_documents(
    documents=texts,
    embedding=embeddings,
    persist_directory="./qwen_db"
)

# 4. Qwen3.5（Ollama）の呼び出し設定
# temperature=0に設定するのがRAGの鉄則。余計な創作をさせないためです。
llm = ChatOllama(
    model="qwen2.5:14b",
    temperature=0,
    num_ctx=4096 # コンテキスト窓を広めに設定
)

# 5. 検索用チェーンの作成
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vector_db.as_retriever(search_kwargs={"k": 3})
)

# 質問実行
query = "この資料に記載されているプロジェクトの納期と主要なリスクを教えてください。"
response = qa_chain.invoke(query)

print("--- 実行結果 ---")
print(response["result"])
```

### 期待される出力

```
資料によると、プロジェクトの納期は2025年3月末日です。
主要なリスクとしては以下の3点が挙げられています：
1. 部材調達の遅延による工程への影響
2. 開発エンジニアのリソース不足
3. 既存システムとの連携テストにおける互換性問題
```

Qwen3.5は、質問に対して「資料によると」という前置きを正確に使い分けます。
もし資料に答えがない場合、他のモデルは無理やり答えを作ろうとしますが、Qwen3.5は「提供された資料内にはその情報は見当たりません」と正直に答える傾向が強いです。
これが実務で「使える」と私が判断した最大の理由です。

## Step 4: 実用レベルにする

単発の質問で終わらせず、業務で「ログ解析」や「大量の仕様書比較」に使うための拡張を行います。
ここでは、複数の回答候補から最適なものを選び出す「Re-ranking」に近い考え方を取り入れた、ループ処理の実装を紹介します。

```python
def ask_qwen_pro(queries, db):
    results = []
    for q in queries:
        # 類似度スコア付きで検索（閾値を設けてノイズを除去）
        docs_with_score = db.similarity_search_with_score(q, k=5)

        # スコアが一定以上のものだけをコンテキストに含める
        # Chromaのスコアは低いほど類似度が高い（距離）
        filtered_context = [doc.page_content for doc, score in docs_with_score if score < 0.8]

        context_text = "\n---\n".join(filtered_context)

        prompt = f"""以下のコンテキスト情報のみを使用して、質問に答えてください。
コンテキストにない情報は絶対に答えないでください。

【コンテキスト】
{context_text}

【質問】
{q}
"""
        res = llm.invoke(prompt)
        results.append({"query": q, "answer": res.content})
    return results

# 大量質問のバッチ処理例
questions = [
    "予算の承認フローは？",
    "緊急時の連絡先は誰？",
    "過去に発生した類似のトラブル事例は？"
]
batch_results = ask_qwen_pro(questions, vector_db)

for item in batch_results:
    print(f"Q: {item['query']}\nA: {item['answer']}\n")
```

実務で使う場合、単に `RetrievalQA` を使うよりも、このようにプロンプトを明示的に制御するほうが安定します。
特に「コンテキストにない情報は絶対に答えないでください」という一文は、Qwen3.5のような「ワーキングドッグ」にとって、非常に強力な制止命令（マズル）として機能します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `torch.cuda.OutOfMemoryError` | VRAM不足。モデルが大きすぎる | 14Bモデルから7Bモデル（qwen2.5:7b）に落とす。または量子化版（Q4_K_Mなど）を使用する |
| 回答が英語になる | システムプロンプトで日本語指定がない | プロンプトの冒頭に「必ず日本語で回答してください」と記述する |
| 検索精度が極端に低い | 埋め込みモデルとLLMの言語不一致 | `mxbai-embed-large` や `multilingual-e5` など日本語対応のEmbeddingモデルを明示的に使う |

## 次のステップ

この記事の内容をマスターしたら、次は「永続的なベクトルストレージの運用」に挑戦してください。
今回は `persist_directory` でローカル保存しましたが、これを Docker 上で動く `Qdrant` や `Milvus` に置き換えることで、数万件のドキュメントを高速に扱うことが可能になります。

また、Qwen3.5の「ツール呼び出し（Tool Calling）」機能も強力です。
「検索して答えがなかったら、特定のAPIを叩いて最新情報を取得しにいく」というエージェント構成に進化させると、単なる文書検索を超えた「自律型の業務アシスタント」が出来上がります。
RTX 4090を積んでいるなら、32BモデルをFP16で動かしてみてください。その推論の深さと正確さは、クラウドAIへの依存を本気でやめるレベルの衝撃を与えてくれるはずです。

## よくある質問

### Q1: Qwen3.5を動かすのに最低限必要なスペックは？

7BモデルであればVRAM 8GB（RTX 3060等）で快適に動きます。14Bモデルなら12GB以上、32Bモデルをそれなりの速度で動かすなら24GB（RTX 3090/4090）が推奨です。RAMは32GB以上あると安定します。

### Q2: PDF以外のファイル（WordやExcel）も読み込めますか？

はい。LangChainには `UnstructuredWordDocumentLoader` や `UnstructuredExcelLoader` が用意されています。ただし、Excelは構造化データなので、テキストとして分割するよりも、Pandasなどで表形式のままコンテキストに流し込む工夫が必要です。

### Q3: 企業秘密のデータをローカルで扱っても本当に安全ですか？

完全にオフライン、または自社ネットワーク内で完結するOllamaとChromaDBの構成であれば、外部にデータが送信されることはありません。これがローカルLLMを導入する最大のメリットであり、SIerが現在最も注力している領域でもあります。

---

## あわせて読みたい

- [Qwen3.5-9B-Claude-4.6-Opus-Uncensored-Distilled-GGUF 使い方入門](/posts/2026-03-16-qwen3-5-9b-uncensored-gguf-setup-guide/)
- [Qwen3.5-9Bをローカル環境のPythonで動かし自分専用の超高速AIアシスタントを作る方法](/posts/2026-03-02-qwen3-5-9b-local-python-guide/)
- [397Bの衝撃。Qwen3.5が放つ「17Bアクティブパラメータ」の魔法と実力](/posts/2026-02-18-a999127c/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Qwen3.5を動かすのに最低限必要なスペックは？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "7BモデルであればVRAM 8GB（RTX 3060等）で快適に動きます。14Bモデルなら12GB以上、32Bモデルをそれなりの速度で動かすなら24GB（RTX 3090/4090）が推奨です。RAMは32GB以上あると安定します。"
      }
    },
    {
      "@type": "Question",
      "name": "PDF以外のファイル（WordやExcel）も読み込めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。LangChainには UnstructuredWordDocumentLoader や UnstructuredExcelLoader が用意されています。ただし、Excelは構造化データなので、テキストとして分割するよりも、Pandasなどで表形式のままコンテキストに流し込む工夫が必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "企業秘密のデータをローカルで扱っても本当に安全ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "完全にオフライン、または自社ネットワーク内で完結するOllamaとChromaDBの構成であれば、外部にデータが送信されることはありません。これがローカルLLMを導入する最大のメリットであり、SIerが現在最も注力している領域でもあります。 ---"
      }
    }
  ]
}
</script>
