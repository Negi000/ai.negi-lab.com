---
title: "Pythonで作るローカルRAG入門：自作検索AIを完全オフラインで動かす方法"
date: 2026-08-20T00:00:00+09:00
slug: "local-rag-python-ollama-tutorial"
cover:
  image: "/images/posts/2026-08-20-local-rag-python-ollama-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "LlamaIndex"
  - "Ollama"
  - "RAG"
  - "ローカルLLM"
  - "Python"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 指定したフォルダ内のPDFやテキストファイルを読み込み、その内容に基づいて回答する「ローカルRAGシステム」を作成します。
- Python 3.10以上とOllamaを使用し、外部API（OpenAI等）を一切使わない完全オフライン環境を実現します。
- データのベクトル化（Embedding）からデータベース保存、検索、生成までのパイプラインを一気通貫で構築します。

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

ローカルでLLMを動かす以上、ハードウェアスペックがそのまま体験の質に直結します。
最低でもメモリ（RAM）は16GB、できれば32GB以上を推奨します。
GPUについては、NVIDIA製のVRAM 8GB以上（RTX 3060 / 4060等）があれば、ストレスのないレスポンス（秒間10〜20トークン程度）が得られます。
Macの場合はM1/M2/M3チップを搭載し、ユニファイドメモリが16GB以上あれば十分に実用圏内です。

API料金については、本構成では完全無料です。
OpenAIのAPIを使うと、数千ページのPDFをインデックスするだけで数ドル飛ぶことがありますが、ローカル環境なら電気代以外はかかりません。
「とりあえず試す」ための代替案として、GPUがないノートPCでも動作するように、今回は軽量なモデル（Llama 3.2 3B）を前提に解説します。

## なぜこの方法を選ぶのか

RAG（Retrieval-Augmented Generation）を構築する手段は、今や無数にあります。
DifyやGraphRAGなど便利なツールも増えましたが、私はあえて「LlamaIndex + Ollama」のライブラリ構成を推奨します。
理由は、エンジニアとして「中身をブラックボックスにしたくない」からです。

GUIツールは導入が楽ですが、検索精度のチューニング（チャンクサイズ調整やメタデータフィルタリング）が必要になった際、結局コードを書くことになります。
また、LangChainではなくLlamaIndexを選ぶのは、データ構造の管理が圧倒的に楽だからです。
LlamaIndexは「検索」に特化しており、RAGに必要な機能が最初から疎結合に整理されています。
この構成を一度覚えれば、実務で「自社のドキュメントをセキュアに検索したい」と言われた際に、即座にプロトタイプを提示できる武器になります。

## Step 1: 環境を整える

まずは、推論エンジンとなる「Ollama」のインストールと、Pythonライブラリのセットアップを行います。

```bash
# Ollamaのインストール（Mac/Linux）
curl -fsSL https://ollama.com/install.sh | sh

# 使用するモデルのダウンロード（Llama 3.2 3B）
ollama pull llama3.2
ollama pull nomic-embed-text

# Python仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# 必要なライブラリのインストール
pip install llama-index llama-index-llms-ollama llama-index-embeddings-ollama pypdf
```

Ollamaは、ローカルLLMを簡単にAPIサーバー化してくれるツールです。
`llama3.2`は推論用、`nomic-embed-text`は文章をベクトル（数字の羅列）に変換するための専用モデルです。
RAGにおいて、回答用モデルと埋め込み用モデルを分けるのは、処理速度と精度のバランスを取るための鉄則です。

⚠️ **落とし穴:**
Windows環境でOllamaを動かす場合、WSL2上ではなくWindowsネイティブ版を使用してください。
WSL2経由だとGPUの認識でハマることが多く、パフォーマンスが著しく低下する場合があります。
また、Pythonのバージョンが3.12だと一部のライブラリがビルドエラーを起こすことがあるため、安定している3.10か3.11を推奨します。

## Step 2: 基本の設定

次に、PythonスクリプトでLlamaIndexがOllamaを経由して各モデルを使えるように設定します。
ここでは、単にモデルを指定するだけでなく、RAGの挙動を左右する「Settings」クラスを正しく定義します。

```python
import os
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

# 1. LLMの設定（回答生成用）
# timeoutを長めに設定しているのは、初回起動時やモデルのロードに時間がかかる場合があるためです
Settings.llm = Ollama(model="llama3.2", request_timeout=120.0)

# 2. Embeddingモデルの設定（ベクトル化用）
# nomic-embed-textは8192トークンのコンテキスト長を持ち、ローカルRAGに最適です
Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")

# 3. チャンクサイズの設定
# 文書をどれくらいの長さで区切るか。512が精度と速度のバランスが良いです
Settings.chunk_size = 512
Settings.chunk_overlap = 50
```

`chunk_size`を512に設定している理由ですが、これは一度に検索する情報の密度を高めるためです。
大きすぎるとノイズが混ざり、小さすぎると文脈が途切れます。
また、`chunk_overlap`を50にすることで、分割された文章同士のつながりを維持し、検索漏れを防いでいます。

## Step 3: 動かしてみる

設定が終わったら、実際にデータを読み込ませてみましょう。
カレントディレクトリに `data` という名前のフォルダを作成し、適当なPDFファイルを1つ入れておいてください。

```python
# dataフォルダ内のすべてのドキュメントを読み込む
documents = SimpleDirectoryReader("./data").load_data()

# インデックス（検索用データベース）の作成
# ここでEmbeddingモデルが動き、文章がベクトル化されます
index = VectorStoreIndex.from_documents(documents)

# クエリエンジンの作成
query_engine = index.as_query_engine()

# 質問の実行
response = query_engine.query("このドキュメントの要点を3つ教えてください。")
print(response)
```

### 期待される出力

```
提供されたドキュメントに基づくと、主要なポイントは以下の3点です。
1. ○○プロジェクトの目的は、AIによる業務効率化である。
2. 導入によるコスト削減効果は、年間で約20%と試算されている。
3. 2024年度中に全部署への展開を予定している。
```

結果が返ってくるまで、初回はモデルのロード等で10秒〜20秒ほどかかるかもしれません。
2回目以降は、GPUが効いていれば数秒で回答が生成されます。

## Step 4: 実用レベルにする

Step 3のコードには致命的な欠陥があります。
実行するたびに全てのドキュメントをベクトル化（Embedding）し直している点です。
ドキュメントが100枚を超えると、起動するたびに数分待たされることになります。
実務では、一度作成したインデックスをディスクに保存し、2回目以降はそれをロードするのが常識です。

また、回答のソース（どのファイルのどのページを参考にしたか）を表示する機能も追加しましょう。
これがないと、AIが嘘をついた（ハルシネーション）ときに確認のしようがありません。

```python
import os
from llama_index.core import StorageContext, load_index_from_storage

PERSIST_DIR = "./storage"

def get_query_engine():
    # インデックス保存用のディレクトリが存在するかチェック
    if not os.path.exists(PERSIST_DIR):
        print("新規インデックスを作成中...")
        documents = SimpleDirectoryReader("./data").load_data()
        index = VectorStoreIndex.from_documents(documents)
        # ディスクに保存
        index.storage_context.persist(persist_dir=PERSIST_DIR)
    else:
        print("既存のインデックスをロード中...")
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)

    # 類似度上位3つのチャンクを取得する設定
    return index.as_query_engine(similarity_top_k=3)

# 実行
engine = get_query_engine()
question = "システム構成図のサーバースペックについて教えて"
response = engine.query(question)

print(f"--- 質問: {question} ---")
print(f"回答: {response}")

print("\n--- 参照ソース ---")
for node in response.source_nodes:
    print(f"File: {node.metadata.get('file_name')} (Score: {node.score:.4f})")
    # 内容の一部を表示
    print(f"Text Snippet: {node.text[:100]}...")
```

この実装にすることで、1,000枚のPDFがあっても起動は一瞬で終わります。
`similarity_top_k=3` としているのは、質問に関連する上位3つの箇所をLLMに渡すという意味です。
ここを増やすと精度が上がる可能性がありますが、LLMが一度に読める量（コンテキスト窓）には限界があるため、3〜5程度が適正値です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ConnectionError: Ollama not found` | Ollamaが起動していない | Ollamaアプリを立ち上げるか、`ollama serve`コマンドを実行する |
| `OutOfMemoryError` | VRAM不足 | モデルを `llama3.2:3b` から `1b` などの軽量版に変更するか、CPUモードで実行する |
| 回答が英語になる | システムプロンプト未設定 | `as_query_engine`の引数で「日本語で回答してください」とプロンプトを追加する |
| 検索精度が極端に低い | Embeddingモデルの不一致 | `nomic-embed-text`が正しくインストールされているか再確認する |

## 次のステップ

この記事のRAGパイプラインが完成したら、次は「データの質」に向き合う番です。
実務でよくある課題は、表形式のデータがうまく読み込めないことです。
その場合は、`LlamaParse`のようなPDF解析に特化したツールを組み込むのが一般的です。

また、今回は単純なベクトル検索（Semantic Search）のみを扱いましたが、キーワード一致を組み合わせた「ハイブリッド検索」や、質問をLLM自身が再構成する「Query Rewriting」といった手法を学ぶと、検索精度は劇的に向上します。
まずは、自分の持っている議事録や技術メモを100個くらい放り込んで、どこまで正確に答えられるかテストしてみてください。
そこでの「失敗」こそが、実務で使えるAIエンジニアになるための最高の教材になります。

## よくある質問

### Q1: 社外秘のドキュメントを読み込ませても本当に安全ですか？

はい、安全です。Ollamaとこのスクリプトはインターネットへの送信を行いません。パケットキャプチャで確認すれば分かりますが、すべての推論処理はあなたのPC内部で完結しています。

### Q2: PDF内の図表や画像の内容も検索できますか？

今回の構成ではテキストのみを抽出するため、図表の中身は無視されます。画像を含めた検索を行いたい場合は、モデルを「Llama 3.2 Vision」などのマルチモーダルモデルに変更し、OCR処理をパイプラインに挟む必要があります。

### Q3: 回答が「情報が見当たりません」ばかりになります。

Embeddingモデルが、質問とドキュメントの文脈をうまく結びつけられていない可能性があります。チャンクサイズを小さくする（256など）か、ドキュメント自体のテキストを、AIが理解しやすいようにMarkdown形式で整理してみてください。

---

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [PythonとLangChainで自分専用のPDF検索AIチャットボットを作る方法](/posts/2026-06-28-local-rag-langchain-faiss-tutorial/)
- [MemPalace 使い方：AIエージェントの長期記憶を劇的に改善するオープンソース実装](/posts/2026-06-07-mempalace-ai-memory-system-review/)
- [ローカルLLM環境の選び方と比較：RTX 4090かMacか？失敗しないGPU・メモリ選び](/posts/2026-07-28-local-llm-gpu-buying-guide-rtx-mac/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "社外秘のドキュメントを読み込ませても本当に安全ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、安全です。Ollamaとこのスクリプトはインターネットへの送信を行いません。パケットキャプチャで確認すれば分かりますが、すべての推論処理はあなたのPC内部で完結しています。"
      }
    },
    {
      "@type": "Question",
      "name": "PDF内の図表や画像の内容も検索できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "今回の構成ではテキストのみを抽出するため、図表の中身は無視されます。画像を含めた検索を行いたい場合は、モデルを「Llama 3.2 Vision」などのマルチモーダルモデルに変更し、OCR処理をパイプラインに挟む必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "回答が「情報が見当たりません」ばかりになります。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Embeddingモデルが、質問とドキュメントの文脈をうまく結びつけられていない可能性があります。チャンクサイズを小さくする（256など）か、ドキュメント自体のテキストを、AIが理解しやすいようにMarkdown形式で整理してみてください。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>
