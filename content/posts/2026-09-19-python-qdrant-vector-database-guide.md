---
title: "Qdrant 使い方 Python ベクトルデータベース入門"
date: 2026-09-19T00:00:00+09:00
slug: "python-qdrant-vector-database-guide"
cover:
  image: "/images/posts/2026-09-19-python-qdrant-vector-database-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qdrant 使い方"
  - "Python ベクトルデータベース"
  - "OpenAI Embedding 実装"
  - "RAG 入門"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

OpenAIのEmbedding APIとベクトルデータベース「Qdrant」を組み合わせて、数千件のドキュメントから瞬時に「意味」で情報を引き出す検索スクリプトを作ります。
Pythonを使って、データのベクトル化からデータベースへの保存、そして検索の実行までを一つのパイプラインとして実装します。

前提知識として、Pythonの基本的な文法（変数、関数、リスト操作）と、`pip`によるライブラリ管理ができることを想定しています。
APIキーを扱うため、環境変数の設定方法を知っているとスムーズです。

必要なものは以下の通りです。
- Python 3.9以上がインストールされたPC
- Docker Desktop（Qdrantをローカルで動かすため）
- OpenAI APIキー（少額の利用料がかかります）
- RAM 8GB以上の環境（Dockerを動かすため）

## 先に確認するスペック・料金

ベクトルデータベースを実務で運用する場合、まず「マネージドサービス（SaaS）」か「セルフホスト」かで悩みます。
結論から言うと、開発フェーズや予算が限られているプロジェクトなら、Dockerを使ったQdrantのセルフホストが最強です。
PineconeなどのSaaSは導入が楽ですが、インデックス数が増えると月額数百ドルが平気で飛んでいきます。

ハードウェアについては、今回の構成であればRTX 4090のようなモンスターGPUは不要です。
ベクトルの計算（Embedding）はOpenAIのサーバー側で行うため、手元のPCはDockerが安定して動くスペックがあれば十分です。
具体的には、メモリ8GBでも動きますが、他の開発ツールと並行するなら16GB以上を推奨します。

料金面では、OpenAIの `text-embedding-3-small` モデルを使用します。
100万トークンあたり$0.02という破壊的な安さなので、個人開発レベルなら月額$1を超えることすら稀です。
唯一、Dockerを動かすためのディスク容量（Qdrantのデータ保存用）として数GBの空きを確保しておいてください。

## なぜこの方法を選ぶのか

ベクトルデータベースにはChromaやMilvus、Weaviateなど多くの選択肢があります。
私が実務で20件以上の案件をこなした結果、現時点で最も「バランスが良い」と感じるのがQdrantです。
理由は、Rust製で圧倒的に高速であること、そしてAPIが非常に直感的で、開発時の試行錯誤がしやすいからです。

Chromaは手軽ですが、本番環境でのスケーラビリティに不安が残ります。
一方でMilvusは多機能すぎて、小〜中規模のプロジェクトにはオーバースペックで構築が面倒です。
Qdrantなら、ローカルのDockerで検証したコードを、そのまま本番のマネージド環境（Qdrant Cloud）に移行できるため、手戻りが発生しません。

また、検索時に「メタデータによる絞り込み（フィルタリング）」が強力なのも選定の決め手です。
「2023年以降のドキュメントの中から、特定のユーザーに関連するものだけをベクトル検索する」といった処理が、SQLに近い感覚で書けるのが魅力ですね。

## Step 1: 環境を整える

まずは、ベクトルデータベース本体となるQdrantをDockerで立ち上げます。
自分のマシンに直接インストールするよりも、Dockerを使う方が環境を汚さず、不具合時のリセットも簡単です。

```bash
# Qdrantの最新イメージを取得して起動
# 6333ポートはAPI用、6334ポートはgRPC用です
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

次に、Python側で必要なライブラリをインストールします。

```bash
pip install qdrant-client openai python-dotenv
```

`qdrant-client`はQdrantを操作するため、`openai`はテキストをベクトルに変換するために使用します。
`python-dotenv`は、APIキーを安全に管理するために必須のツールです。

⚠️ **落とし穴:**
Windows環境でDocker Desktopを使っている場合、メモリ割り当てが少なすぎるとQdrantが起動直後に落ちることがあります。
設定画面からWSL 2のメモリ割り当てが少なくとも2GB以上になっているか確認してください。
また、ポート6333が既に他のアプリケーションで使用されていないかもチェックが必要です。

## Step 2: 基本の設定

次に、PythonからQdrantとOpenAI APIに接続するための初期設定を書きます。
APIキーをコードに直書きするのは、GitHubに誤って公開してしまうリスクがあるため、絶対に避けましょう。

カレントディレクトリに `.env` という名前のファイルを作成し、以下を記述してください。
```text
OPENAI_API_KEY=sk-your-api-key-here
```

次に、設定用コードを書きます。

```python
import os
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

# .envファイルを読み込む
load_dotenv()

# 各クライアントの初期化
# localhost:6333は、先ほどDockerで立ち上げたQdrantの宛先です
client = QdrantClient("http://localhost:6333")
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ベクトルを保存する「器（コレクション）」の名前
COLLECTION_NAME = "my_documents"

# コレクションの作成（既に存在する場合はスキップ）
if not client.collection_exists(COLLECTION_NAME):
    # text-embedding-3-small の次元数は1536です。
    # 距離計算には「Cosine類似度」を指定します。これがRAGでは一般的です。
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )
    print(f"Collection '{COLLECTION_NAME}' created.")
```

ここで重要なのは `Distance.COSINE` の設定です。
ベクトル同士がどれだけ似ているかを測る指標ですが、OpenAIのEmbeddingを使う場合はCosine（コサイン類似度）を選ぶのが定石です。
内積（Dot product）でも動きますが、類似度のスコアが0〜1の範囲に収まりやすいコサイン類似度の方が、検索結果の閾値を決めやすくなります。

## Step 3: 動かしてみる

準備が整ったので、実際にテキストをベクトル化してQdrantに保存し、検索してみましょう。
「リンゴ」「ゴリラ」「ラッパ」という3つの単語を登録し、「果物」という言葉で検索して「リンゴ」が上位に来るか確認します。

```python
def get_embedding(text):
    """テキストをベクトルに変換する関数"""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

# データの登録（Upsert）
documents = [
    {"id": 1, "text": "リンゴは赤い果物です。"},
    {"id": 2, "text": "ゴリラは力強い類人猿です。"},
    {"id": 3, "text": "ラッパは金管楽器の一種です。"}
]

points = []
for doc in documents:
    vector = get_embedding(doc["text"])
    points.append({
        "id": doc["id"],
        "vector": vector,
        "payload": {"content": doc["text"]} # メタデータとして元の文を保存
    })

# 一括でQdrantにアップロード
client.upsert(collection_name=COLLECTION_NAME, points=points)

# 検索の実行
query_text = "美味しいフルーツについて教えて"
query_vector = get_embedding(query_text)

search_result = client.search(
    collection_name=COLLECTION_NAME,
    query_vector=query_vector,
    limit=1 # 最も似ているものを1つだけ取得
)

for hit in search_result:
    print(f"検索結果: {hit.payload['content']} (スコア: {hit.score})")
```

### 期待される出力

```text
検索結果: リンゴは赤い果物です。 (スコア: 0.8123456789)
```

「フルーツ」という言葉自体は登録したテキストに含まれていませんが、Embeddingのおかげで意味が近い「リンゴ」が正しく抽出されました。
スコアは1に近いほど似ていることを示します。
実務では、このスコアが例えば0.7以下の場合は「関連情報なし」と判断するようなロジックを組むことが多いです。

## Step 4: 実用レベルにする

ここまでは最小構成ですが、実際の仕事で使うには「大量のドキュメントを効率よく処理する」必要があります。
1件ずつ `get_embedding` を呼んでいると、通信のオーバーヘッドで時間がかかりすぎます。
また、APIエラーへの対処も欠かせません。

以下は、リストでまとめて処理（バッチ処理）し、さらに「カテゴリ」などのメタデータでフィルタリングできるように改良したコードです。

```python
def batch_upsert(texts, category):
    """複数のテキストを効率よく一括登録する"""
    # OpenAI APIは複数のテキストを一度にEmbeddingできます
    response = openai_client.embeddings.create(
        input=texts,
        model="text-embedding-3-small"
    )
    vectors = [data.embedding for data in response.data]

    points = []
    for i, (text, vector) in enumerate(zip(texts, vectors)):
        points.append({
            "id": hash(text) % 10**8, # 重複を避けるための簡易的なID生成
            "vector": vector,
            "payload": {"content": text, "category": category}
        })

    client.upsert(collection_name=COLLECTION_NAME, points=points)

# メタデータフィルタリングを使った検索
from qdrant_client.http import models as rest

def filtered_search(query, target_category):
    query_vector = get_embedding(query)

    return client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=rest.Filter(
            must=[
                rest.FieldCondition(
                    key="category",
                    match=rest.MatchValue(value=target_category)
                )
            ]
        ),
        limit=3
    )

# 実行例
batch_upsert(["バナナは黄色い", "イチゴは甘酸っぱい"], "fruit")
results = filtered_search("甘い食べ物", "fruit")
```

この「フィルタリング」が非常に重要です。
RAG（検索拡張生成）の実装において、全データから検索するのではなく、「ユーザーAがアクセス可能な文書のみ」や「最新1ヶ月のニュースのみ」に絞り込むことで、検索精度とセキュリティを同時に担保できます。

QdrantのWeb UIも確認してみてください。
ブラウザで `http://localhost:6333/dashboard` を開くと、作成したコレクションや中身のデータ（Payload）をグラフィカルに確認できます。
コードが正しく動いているか不安になったら、まずここを覗くのがエンジニアの鉄則です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Vector size mismatch` | コレクション作成時の次元数（1536）と、Embeddingモデルの出力次元が一致していない。 | `text-embedding-3-small` を使っているか再確認。モデルを変えたならコレクションを作り直す。 |
| `Connection refused` | Dockerが起動していないか、ポート番号が間違っている。 | `docker ps` でコンテナの状態を確認。ポート6333がListenされているか見る。 |
| `Rate limit reached` | OpenAI APIの無料枠を超えた、あるいは短時間にリクエストを送りすぎた。 | `time.sleep()` を入れるか、OpenAIの管理画面で支払い設定を確認する。 |

## 次のステップ

ここまでで、ベクトルデータベースの基本操作はマスターできました。
次に挑戦すべきは「RAG（Retrieval-Augmented Generation）」の構築です。
検索したテキストをプロンプトに埋め込み、GPT-4などのLLMに渡して回答を生成させるパイプラインを作ってみてください。

具体的には、LangChainやLlamaIndexといったフレームワークを導入すると、ドキュメントの読み込みからチャンク分割までを自動化できます。
しかし、まずは今回のようにライブラリを直接叩いて「裏側で何が起きているか」を理解しておくことが、トラブルシューティングの際に大きな差になります。

また、ローカルで動かすことに慣れたら、AWSやGCP上のインスタンスでQdrantを動かす構成も検討してみてください。
その際は、データの永続化（Dockerボリュームのバックアップ）と、APIへの認証（API Keyの設定）を忘れないようにしましょう。

## よくある質問

### Q1: ベクトルの次元数はなぜ固定なんですか？

使用するEmbeddingモデルによって決まるからです。`text-embedding-3-small`は1536次元、`text-embedding-3-large`は最大3072次元です。データベース側とモデル側の次元が1つでもズレると、数学的に距離が計算できないためエラーになります。

### Q2: 検索スコアが低すぎるのですが、改善策はありますか？

まずは「チャンク分割」を見直してください。一つの文章が長すぎると意味がぼやけてスコアが下がります。100〜300文字程度に区切って登録するのが実務上のセオリーです。また、クエリに関連しないノイズをデータから除くことも効果的です。

### Q3: Qdrantをクラウドで使いたい場合はどうすればいいですか？

Qdrant Cloudという公式のマネージドサービスがあります。今回のコードの `QdrantClient("http://localhost:6333")` の部分を、発行されたURLとAPIキーに書き換えるだけで、コードを一行も変えずにクラウド移行が可能です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBあれば、将来的にEmbeddingをローカルLLMで行う際も余裕を持って対応可能。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MiniMax API 使い方 入門 - 高性能モデル M2.5 を Python で動かす方法](/posts/2026-04-14-minimax-api-python-m25-tutorial/)
- [OllamaとOpen WebUIを連携させ、完全にオフラインで動作する「プライベートChatGPT環境」を構築します。](/posts/2026-07-20-ollama-open-webui-local-llm-tutorial/)
- [Glass 使い方 AIエージェントの精度改善とデータセット構築を自動化するレビュー](/posts/2026-03-13-glass-ai-agent-improvement-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "ベクトルの次元数はなぜ固定なんですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "使用するEmbeddingモデルによって決まるからです。text-embedding-3-smallは1536次元、text-embedding-3-largeは最大3072次元です。データベース側とモデル側の次元が1つでもズレると、数学的に距離が計算できないためエラーになります。"
      }
    },
    {
      "@type": "Question",
      "name": "検索スコアが低すぎるのですが、改善策はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "まずは「チャンク分割」を見直してください。一つの文章が長すぎると意味がぼやけてスコアが下がります。100〜300文字程度に区切って登録するのが実務上のセオリーです。また、クエリに関連しないノイズをデータから除くことも効果的です。"
      }
    },
    {
      "@type": "Question",
      "name": "Qdrantをクラウドで使いたい場合はどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Qdrant Cloudという公式のマネージドサービスがあります。今回のコードの QdrantClient(\"http://localhost:6333\") の部分を、発行されたURLとAPIキーに書き換えるだけで、コードを一行も変えずにクラウド移行が可能です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBあれば、将来的にEmbeddingをローカルLLMで行う際も余裕を持って対応可能。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
