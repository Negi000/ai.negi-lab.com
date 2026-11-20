---
title: "PythonとChromaDBで作る実用RAGシステム実装入門"
date: 2026-11-21T00:00:00+09:00
slug: "python-rag-chromadb-openai-tutorial"
cover:
  image: "/images/posts/2026-11-21-python-rag-chromadb-openai-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "RAG"
  - "Python"
  - "ChromaDB"
  - "OpenAI API"
  - "ベクトルデータベース"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

独自のテキストファイルを読み込み、その内容に基づいてAIが回答する「ローカル検索型のRAG（検索拡張生成）パイプライン」をPythonで構築します。
既存のライブラリに頼り切るのではなく、検索（Retrieval）と生成（Generation）の工程を分離して実装することで、実務でカスタマイズ可能なコードを作成します。

- 前提知識: Pythonの基本的な文法（リスト、辞書、関数）がわかること
- 必要なもの: OpenAI APIキー、Python 3.10以上の環境

## 先に確認するスペック・料金

RAGの実装において、最もコストとパフォーマンスに直結するのが「Embedding（ベクトル化）」と「ベクトルデータベース」の選択です。
今回は開発のしやすさを優先し、ベクトルDBに「ChromaDB」、EmbeddingにOpenAIの「text-embedding-3-small」を使用します。

OpenAIのAPI料金は、100万トークンあたり約3円（$0.02）と極めて安価です。
数千ページのドキュメントを読み込んでも、個人開発レベルなら月額数百円もかかりません。
一方で、完全にオフラインで動かしたい場合は、RTX 3060（VRAM 12GB）以上のGPUがあれば、HuggingFaceのモデルを使ってローカルでEmbeddingを行うことも可能です。
今回はまず「APIで動くもの」を作り、構造を理解することに集中してください。

## なぜこの方法を選ぶのか

RAGを作る際、LangChainやLlamaIndexといったフレームワークを使うのが一般的ですが、私はあえて「素のPythonに近い形」で組むことを推奨しています。
理由は、フレームワークが裏側で行っている処理（チャンク分割やプロンプト構成）がブラックボックスになりやすく、精度が出ない時にどこを直すべきか分からなくなるからです。

今回はChromaDBという軽量なベクトルDBを直接叩きます。
これにより、データの登録・検索のプロセスが透明化され、実務で必要になる「検索結果のスコア調整」や「プロンプトの微調整」が容易になります。
一度この構造で組めば、後からLangChainに移行するのは簡単ですが、逆は困難です。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
ターミナルまたはコマンドプロンプトで以下のコマンドを実行してください。

```bash
pip install openai chromadb python-dotenv
```

各ライブラリの役割は以下の通りです。
- `openai`: LLM（GPT-4o等）とEmbeddingモデルを利用するために必要です。
- `chromadb`: ベクトルデータベース。テキストを数値化して保存し、高速に検索するために使います。
- `python-dotenv`: APIキーなどの機密情報を`.env`ファイルから読み込むために使用します。

⚠️ **落とし穴:**
SQLiteのバージョンが古い環境（一部の古いLinuxや古いPython環境）では、ChromaDBのインストールでエラーが出ることがあります。その場合は、`pip install pysqlite3-binary`を入れ、実行コードの冒頭でSQLiteを差し替える処理が必要になります。最新のWindows/Mac環境であれば問題ありません。

## Step 2: 基本の設定

プロジェクトのルートディレクトリに`.env`という名前のファイルを作成し、APIキーを書き込みます。

```text
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

次に、Pythonスクリプト（`main.py`）を作成し、初期設定を行います。

```python
import os
from dotenv import load_dotenv
import chromadb
from openai import OpenAI

# 環境変数の読み込み
load_dotenv()

# OpenAIクライアントの初期化
# APIキーが設定されていない場合はエラーを出すようにします
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEYが設定されていません。.envファイルを確認してください。")

client = OpenAI(api_key=api_key)

# ChromaDBの初期化（データをローカルの ./chroma_db フォルダに保存します）
# 永続化（Persist）設定にすることで、一度登録したデータを次回以降も使い回せます
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# コレクション（テーブルのようなもの）の作成
# 既に存在する場合はそれを取得します
collection = chroma_client.get_or_create_collection(name="my_knowledge_base")
```

各設定の理由を解説します。
ChromaDBで`PersistentClient`を使うのは、メモリ上だけでなくディスクにデータを保存するためです。
これにより、スクリプトを終了しても学習させたデータが消えず、商用環境に近い運用が可能になります。

## Step 3: 動かしてみる

RAGの肝となる「データの登録」と「検索」の最小構成を実装します。
ここでは、社内規定やマニュアルを模したテキストデータをベクトル化して保存します。

```python
def add_documents(texts, ids):
    """テキストをベクトル化してChromaDBに登録する"""
    # text-embedding-3-smallを使用してベクトル化（Embedding）を行う
    # 1536次元のベクトルが生成されます
    response = client.embeddings.create(
        input=texts,
        model="text-embedding-3-small"
    )
    embeddings = [e.embedding for e in response.data]

    collection.add(
        embeddings=embeddings,
        documents=texts,
        ids=ids
    )
    print(f"{len(texts)}件のドキュメントを登録しました。")

# テストデータの登録
sample_docs = [
    "弊社の夏季休暇は8月10日から8月15日までです。",
    "経費精算の締め切りは、毎月25日の18時までとなります。",
    "リモートワークを行う際は、前日までにSlackの#attendanceチャンネルで報告してください。"
]
sample_ids = ["doc1", "doc2", "doc3"]

add_documents(sample_docs, sample_ids)

# 検索の実行
def query_knowledge_base(query_text, n_results=1):
    """クエリに似たドキュメントを検索する"""
    # クエリ自体も同じモデルでベクトル化する必要がある
    query_embedding_res = client.embeddings.create(
        input=[query_text],
        model="text-embedding-3-small"
    )
    query_embedding = query_embedding_res.data[0].embedding

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return results["documents"][0]

# テスト検索
question = "夏休みはいつから？"
context = query_knowledge_base(question)
print(f"検索結果: {context}")
```

### 期待される出力

```
3件のドキュメントを登録しました。
検索結果: ['弊社の夏季休暇は8月10日から8月15日までです。']
```

検索結果が「夏休み」という言葉を含んでいなくても、「夏季休暇」という文脈上の意味を捉えてヒットしている点に注目してください。これがベクトル検索の威力です。

## Step 4: 実用レベルにする

単に検索結果を表示するだけではRAGとは言えません。
検索結果を「コンテキスト」としてLLMに渡し、自然な回答を生成させます。
また、実務では大量の文章を扱うため、適切に「チャンク分割（文章の細分化）」を行う必要があります。

```python
def generate_answer(question):
    """検索結果を元に回答を生成する"""
    # 1. 関連情報を検索
    retrieved_docs = query_knowledge_base(question, n_results=2)
    context_text = "\n".join(retrieved_docs)

    # 2. プロンプトの構築
    # システムプロンプトで「コンテキストに基づかない回答を禁止」するのが精度を上げるコツです
    prompt = f"""
以下の「提供された情報」のみに基づいて、質問に答えてください。
提供された情報の中に答えがない場合は「分かりません」と答えてください。

# 提供された情報:
{context_text}

# 質問:
{question}
"""

    # 3. LLMで回答生成（GPT-4o miniを使用。安くて速いためRAGに最適）
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたは誠実な社内アシスタントです。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0 # 創作を抑えるために0に設定
    )

    return response.choices[0].message.content

# 実行
final_answer = generate_answer("リモートワークのルールを教えて")
print(f"AIの回答:\n{final_answer}")
```

この実装で重要なのは、`temperature=0`の設定です。
実務用のRAGにおいて、AIの「もっともらしい嘘（ハルシネーション）」は致命的な問題になります。
温度パラメータを最小にすることで、検索された事実に基づいた、一貫性のある回答を得やすくなります。

また、今回は単純なリストを使いましたが、実際の業務ではPDFやMarkdownファイルを読み込むはずです。
その際は、`langchain-text-splitters`などのライブラリを「チャンク分割のためだけに」活用し、1チャンクあたり500文字程度、かつ100文字程度の「重なり（overlap）」を持たせて分割するのが、検索精度を落とさないための黄金律です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Collection not found` | 永続化パスが間違っている、または初期化前にアクセスした | `get_or_create_collection`を使い、パスが正しいか確認する |
| `Dimension mismatch` | 登録時と検索時で異なるEmbeddingモデルを使っている | `text-embedding-3-small`など、モデルを統一する |
| `API Rate Limit` | 短時間に大量のEmbeddingリクエストを送信した | `time.sleep`を入れるか、バッチ処理（一度に複数テキストを送る）を実装する |

## 次のステップ

この記事の内容で、RAGの「基本骨格」は完成しました。
しかし、本気で実務に投入するなら、以下の3点に挑戦してみてください。

1. **ハイブリッド検索の実装**:
ベクトル検索は「概念」には強いですが、「型番」や「固有名詞」の完全一致には弱いです。BM25というキーワード検索と組み合わせることで、精度は劇的に向上します。
2. **メタデータフィルタリング**:
「2023年の資料だけから探す」といった条件を付けたい場合、ChromaDBの`where`句を使えるようにコードを拡張してください。
3. **リランク（Re-ranking）の導入**:
検索でヒットした上位10件を、さらに「本当に質問に関連しているか」で並び替える工程です。Cohere RerankなどのAPIを使うと、驚くほど回答精度が上がります。

まずは身近なメモ書きや、自分が書いた過去のブログ記事などをこのスクリプトに読み込ませて、自分専用の「外部脳」を作るところから始めてみてください。

## よくある質問

### Q1: OpenAI以外のEmbeddingモデルは使えますか？

はい、使えます。
プライバシーの懸念がある場合は、`sentence-transformers`ライブラリを使ってローカル（自分のPC内）でベクトル化することも可能です。ただし、モデルの管理やGPUメモリの消費を考慮する必要があります。

### Q2: データベースのデータが増えても速度は落ちませんか？

ChromaDBは内部でHNSWというインデックスアルゴリズムを使用しており、数万件程度のドキュメントであればミリ秒単位で検索可能です。
数百万件を超える場合は、PineconeやMilvusといった、よりスケーラブルなクラウド型ベクトルDBへの移行を検討してください。

### Q3: 日本語の長い文章をそのまま登録しても大丈夫ですか？

おすすめしません。
LLMには「コンテキストウィンドウ（一度に読み込める量）」の限界があります。
長い文章は意味の区切り（句点や段落）で100〜500文字程度に分割して登録するのが、RAGを成功させるための鉄則です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルEmbeddingや軽量LLMの推論を高速化できるため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [PythonとLangChainを使って、手元のPDFやテキストファイルを知識源として回答する「RAG（検索拡張生成）システム」をゼロから構築します。](/posts/2026-09-02-python-rag-local-implementation-guide/)
- [Python RAG入門 ローカル検索の実装方法](/posts/2026-09-15-langchain-rag-local-pdf-tutorial/)
- [Pythonで作るローカルRAG入門：自作検索AIを完全オフラインで動かす方法](/posts/2026-08-20-local-rag-python-ollama-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "OpenAI以外のEmbeddingモデルは使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、使えます。 プライバシーの懸念がある場合は、sentence-transformersライブラリを使ってローカル（自分のPC内）でベクトル化することも可能です。ただし、モデルの管理やGPUメモリの消費を考慮する必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "データベースのデータが増えても速度は落ちませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ChromaDBは内部でHNSWというインデックスアルゴリズムを使用しており、数万件程度のドキュメントであればミリ秒単位で検索可能です。 数百万件を超える場合は、PineconeやMilvusといった、よりスケーラブルなクラウド型ベクトルDBへの移行を検討してください。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の長い文章をそのまま登録しても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "おすすめしません。 LLMには「コンテキストウィンドウ（一度に読み込める量）」の限界があります。 長い文章は意味の区切り（句点や段落）で100〜500文字程度に分割して登録するのが、RAGを成功させるための鉄則です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでローカルEmbeddingや軽量LLMの推論を高速化できるため</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
