---
title: "PythonでRAGパイプラインを自作する方法"
date: 2026-09-24T00:00:00+09:00
slug: "llamaindex-rag-local-search-tutorial"
cover:
  image: "/images/posts/2026-09-24-llamaindex-rag-local-search-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "LlamaIndex"
  - "RAG 構築"
  - "Python チュートリアル"
  - "Qdrant 使い方"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 手持ちのPDFやテキストファイルを読み込み、その内容に基づいてAIが回答する「ローカルデータ検索RAGスクリプト」を作成します。
- 外部にデータを漏らさないためのローカルLLM（Ollama）への切り替え方法まで網羅します。
- 前提知識として、Pythonの基本的な文法（変数、関数、pipでのライブラリインストール）を理解している必要があります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載でローカルLLMとRAGの検証を低予算で始めるのに最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

RAGを動かす上で最も重要なのは「メモリ（VRAM）」と「APIコスト」のバランスです。
OpenAIのAPIを使う場合、初期費用はほぼゼロ（従量課金）ですが、機密データを扱う場合はローカルLLMの検討が必要です。

ローカルで全て完結させるなら、最低でもVRAMが8GB、できれば12GB以上のGPU（RTX 3060 12GB / 4070以降）を推奨します。
Macユーザーなら、ユニファイドメモリが16GB以上あれば、Llama 3 (8Bクラス) が快適に動作します。
メモリが8GBしかないPCで無理に動かそうとすると、1つの質問に3分以上かかり、実務には使い物になりません。

APIを利用する場合、`text-embedding-3-small`（検索用モデル）は100万トークンあたり約$0.02と極めて安価です。
一方で、回答用の`gpt-4o`は100万入力トークンあたり$5かかります。
大量のドキュメントを読み込ませる際、埋め込み（Embedding）のコストは無視できますが、LLMの呼び出し回数が増えると月額$20〜50程度はすぐに行くことを覚悟してください。

## なぜこの方法を選ぶのか

RAGの実装には、LangChain、LlamaIndex、Haystackなど多くのフレームワークが存在します。
その中で、私が今回の実装に「LlamaIndex」を選ぶ理由は、データ接続（データコネクタ）の豊富さと、RAGに特化した抽象化のバランスが最も優れているからです。

LangChainは汎用性が高すぎて、デバッグ時に「どこで何が起きているか」を追うのが非常に苦労します。
SIer時代に数十件のAI案件をこなした経験から言えば、RAGのプロトタイプ構築から実運用への移行スピードはLlamaIndexが圧倒的に速いです。
また、今回はベクトルデータベースに「Qdrant」をメモリモードで使用します。
最初から複雑なDBサーバーを立てると挫折するため、まずはコード内で完結し、かつ将来的にサーバー化が容易な構成を選択します。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
Python 3.9以上が必要です。それ未満だとライブラリの依存関係でエラーが出る可能性が高いです。

```bash
# LlamaIndex本体とOpenAI連携用のパッケージ
pip install llama-index llama-index-llms-openai llama-index-embeddings-openai

# ベクトルデータベース（Qdrant）のクライアント
pip install qdrant-client llama-index-vector-stores-qdrant

# PDFの読み込みに必要なパッケージ
pip install pypdf
```

`llama-index`はバージョン0.10以降、プラグイン形式に変更されました。
以前のバージョンで書かれたネットの記事（`from llama_index import ...`）は、現在のバージョンでは動かないことが多いため注意してください。
今回は最新のインテグレーション方式を採用しています。

⚠️ **落とし穴:**
Windows環境でPythonをインストールしている場合、パス（PATH）が通っていないと`pip`が使えないことがあります。
その場合は`python -m pip install ...`として実行してください。
また、複数のPython環境が混在していると、インストールしたはずのライブラリが「ModuleNotFoundError」になるのが初心者の最初の関門です。
必ず「仮想環境（venv）」を作成してから作業を開始しましょう。

## Step 2: 基本の設定

RAGを構築するために、まずはAPIキーの設定とデータの準備を行います。
スクリプトと同じディレクトリに `data` というフォルダを作成し、適当なテキストファイルやPDFを1枚入れておいてください。

```python
import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client

# 1. APIキーの設定
# 実際の業務では .env ファイルを使用しますが、まずは動作確認のために環境変数へセットします
os.environ["OPENAI_API_KEY"] = "sk-xxxxxxxxxxxxxxxx"

# 2. モデルの定義
# 回答用LLMにはコスパに優れた gpt-4o-mini を、
# 検索用モデル（Embedding）には text-embedding-3-small を指定します。
# なぜ small かと言うと、large にしても検索精度が劇的に変わるケースは稀で、
# トークン消費を抑える方が実務上のメリットが大きいからです。
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# 3. データの読み込み
# SimpleDirectoryReaderは指定したフォルダ内のファイルを自動判別して読み込みます。
# これが LlamaIndex の最も強力な「武器」の一つです。
documents = SimpleDirectoryReader("./data").load_data()

# 4. ベクトルDB（Qdrant）の初期化
# メモリ上で動作させる設定（:memory:）にします。
# 実運用時は、ここをURL（localhost等）に変更するだけで済みます。
client = qdrant_client.QdrantClient(location=":memory:")
vector_store = QdrantVectorStore(client=client, collection_name="my_rag_collection")
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# 5. インデックス（検索エンジン）の作成
# ここでテキストがベクトル化され、DBに保存されます。
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
)
```

`Settings.llm` で `temperature=0.1` としているのは、RAGにおいて「嘘（ハルシネーション）」を最小限にするためです。
0.7などの高い値にすると、検索した事実に基づかない「AIの創作」が混ざりやすくなり、業務システムとしては致命的な欠陥になります。

## Step 3: 動かしてみる

設定が終わったら、実際に質問を投げてみましょう。

```python
# 6. クエリエンジンの作成
# similarity_top_k=3 は、「質問に関連する箇所を上位3つ探してくる」という意味です。
query_engine = index.as_query_engine(similarity_top_k=3)

# 7. 質問の実行
question = "読み込ませたドキュメントに基づいて、〇〇の注意点を要約してください"
response = query_engine.query(question)

print(f"【質問】: {question}")
print("-" * 30)
print(f"【回答】: {response}")

# 8. 根拠となったソースの確認
# 「なぜその回答をしたか」を追跡できるのがRAGのメリットです。
for node in response.source_nodes:
    print(f"\n[ソース（スコア: {node.score:.4f}）]:")
    print(node.node.get_content()[:100] + "...")
```

### 期待される出力

```
【質問】: 読み込ませたドキュメントに基づいて、〇〇の注意点を要約してください
------------------------------
【回答】: ドキュメントによると、〇〇に関する主な注意点は以下の3点です...

[ソース（スコア: 0.8542）]:
〇〇を使用する際は、必ず電源を切ってから作業を行ってください。また、湿気の多い場所での保管は...
```

検索された「スコア」は、質問文とドキュメントの類似度を示します。
0.7を下回る場合は、全く関係のない箇所を拾っている可能性が高いため、フィルタリングの基準にするのが実務上の定石です。

## Step 4: 実用レベルにする

初期のRAG実装で最も多い悩みは「検索精度が悪い」ことです。
これを解決するために、「チャンクサイズ」の調整と「メタデータ」の活用を導入します。
LlamaIndexでは、1つのドキュメントをどれくらいの細かさで切り分けるかを制御できます。

```python
from llama_index.core.node_parser import SentenceSplitter

# チャンクサイズの最適化
# デフォルトでは1024トークンですが、これだと情報が混ざりすぎることがあります。
# 512トークン程度に細分化し、前後の文脈（オーバーラップ）を50トークン持たせるのが
# 経験上、最もバランスが良いです。
node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)

# インデックス作成時にこのパーサーを適用
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    transformations=[node_parser]
)

# 検索を強化する「ハイブリッド検索」や「リランク（再ランク付け）」
# 予算があるなら、CohereのRerank APIを挟むと劇的に精度が上がります。
# 今回は無料でできる工夫として、プロンプトに「根拠が見つからない場合は知らないと答えて」と明示します。
from llama_index.core import PromptTemplate

qa_prompt_tmpl_str = (
    "コンテキスト情報は以下の通りです。\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "この情報のみに基づいて、質問に答えてください。答えが見つからない場合は「該当する情報がありません」と回答してください。\n"
    "質問: {query_str}\n"
    "回答: "
)
qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)
query_engine.update_prompts({"response_synthesizer:text_qa_template": qa_prompt_tmpl})
```

この「情報がない場合に正直に答える」ためのプロンプト調整は、ユーザーの信頼を得るために不可欠です。
AIが無理に答えて間違った指示を出すリスクを、エンジニア側でコントロールする必要があります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| RateLimitError | OpenAIの無料枠超過、または支払い設定漏れ | API管理画面でクレジットをチャージするか、ティアを上げてください。 |
| ModuleNotFoundError | 仮想環境にライブラリが入っていない | `pip list` でインストール済みか確認し、正しいPython環境で実行してください。 |
| 検索結果が空 | チャンクサイズが大きすぎて意味が分散している | `chunk_size` を小さくし、`similarity_top_k` を増やしてみてください。 |

## 次のステップ

RAGパイプラインが動くようになったら、次は「評価」と「ローカル化」に挑戦してください。
RAGの精度は「勘」で調整するものではありません。
RagasやTruLensといった評価フレームワークを使い、どの設定が最も正解率が高いかを数値で測定するのがプロの現場です。

また、セキュリティ要件が厳しい案件では、OpenAIを使わず「Ollama」を利用して完全にオフラインで動かす構成が求められます。
LlamaIndexは `Settings.llm = Ollama(model="llama3")` と書き換えるだけでモデルを差し替えられる設計になっています。
RTX 4090などの強力なGPUがあるなら、ローカルLLMの方がレスポンスも速く、何よりAPIコストを気にせず数万件のドキュメントを読み込ませることができます。
まずは100ページのPDFを読み込ませて、どこまで正確に答えられるか限界を試してみてください。

## よくある質問

### Q1: PDFの中に画像や表がある場合、そのまま読み込めますか？

標準の `SimpleDirectoryReader` だけでは、画像内のテキストや複雑な表構造を正しく認識できません。
その場合は「LlamaParse」というクラウドサービスや、ローカルで動く「Unstructured」というライブラリを組み合わせて、Markdown形式に変換してから読み込ませるのが一般的です。

### Q2: データの更新はどうすればいいですか？

今回はメモリ上でインデックスを作成しているため、プログラムを終了するとデータが消えます。
永続化するには、Qdrantの `location` をディレクトリパス（`./qdrant_data`）に指定してください。
データが追加された際は、インデックスを再作成するか、差分のみを `insert` する処理が必要になります。

### Q3: 日本語の検索精度が低い気がします。

Embeddingモデルを日本語に特化したもの（例えば、Hugging Faceで公開されている日本語対応モデル）に変更することを検討してください。
ただし、OpenAIの `text-embedding-3-small` は多言語対応が強力なので、多くの場合、原因はモデルではなく「チャンクの切り方が不自然で文脈が壊れている」ことにあります。

---

## あわせて読みたい

- [Gemma 4 31B 爆速化ガイド Speculative Decoding の導入方法](/posts/2026-04-13-gemma-4-31b-speculative-decoding-guide/)
- [MiniMax API 使い方 入門 - 高性能モデル M2.5 を Python で動かす方法](/posts/2026-04-14-minimax-api-python-m25-tutorial/)
- [PythonとLangChainでRAGパイプラインを自作する方法](/posts/2026-07-05-langchain-rag-local-chroma-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "PDFの中に画像や表がある場合、そのまま読み込めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "標準の SimpleDirectoryReader だけでは、画像内のテキストや複雑な表構造を正しく認識できません。 その場合は「LlamaParse」というクラウドサービスや、ローカルで動く「Unstructured」というライブラリを組み合わせて、Markdown形式に変換してから読み込ませるのが一般的です。"
      }
    },
    {
      "@type": "Question",
      "name": "データの更新はどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "今回はメモリ上でインデックスを作成しているため、プログラムを終了するとデータが消えます。 永続化するには、Qdrantの location をディレクトリパス（./qdrantdata）に指定してください。 データが追加された際は、インデックスを再作成するか、差分のみを insert する処理が必要になります。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の検索精度が低い気がします。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Embeddingモデルを日本語に特化したもの（例えば、Hugging Faceで公開されている日本語対応モデル）に変更することを検討してください。 ただし、OpenAIの text-embedding-3-small は多言語対応が強力なので、多くの場合、原因はモデルではなく「チャンクの切り方が不自然で文脈が壊れている」ことにあります。 ---"
      }
    }
  ]
}
</script>
