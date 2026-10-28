---
title: "LlamaIndexで作るRAG入門：手元のPDFを爆速で検索する実装ガイド"
date: 2026-10-29T00:00:00+09:00
slug: "llamaindex-rag-local-pdf-implementation-guide"
cover:
  image: "/images/posts/2026-10-29-llamaindex-rag-local-pdf-implementation-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "LlamaIndex 使い方"
  - "RAG 実装"
  - "Python PDF 検索"
  - "OpenAI API 連携"
---
**所要時間:** 約45分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 指定したフォルダ内のPDFファイルを自動で読み込み、内容について回答するRAG（検索拡張生成）システムを作ります
- 独自のドキュメントに基づいた「嘘（ハルシネーション）の少ない」AIチャット環境をPythonスクリプト1つで構築します
- Pythonの基礎（変数、関数の実行）が理解できていれば、コピペだけでプロトタイプが完成します

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載で将来的な完全ローカルRAG移行に最適な高コスパGPU</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

RAGの実装において最も重要なのは「メモリ（RAM）」と「推論コスト」のバランスです。今回のガイドでは、最も精度が安定するOpenAIのAPIを使用しますが、将来的にローカルLLMへ移行することも見越した構成にします。

PCスペックは、Windowsならメモリ16GB以上、MacならM1チップ以降（メモリ8GBでも動作可）を推奨します。インデックス作成時に一時的にメモリを消費するため、ブラウザを大量に開いている場合は注意してください。

コスト面では、OpenAIの`gpt-4o-mini`と`text-embedding-3-small`を使用する場合、PDF 100枚程度の処理なら1回あたり数円（$0.01以下）で済みます。
もし完全無料で運用したい場合は、本記事のコードのモデル指定部分を「Ollama」に書き換えることで対応可能ですが、まずは「正解の挙動」を知るためにAPI版で試すのが最短ルートです。

## なぜこの方法を選ぶのか

RAGを構築するライブラリは、大きく分けて「LangChain」と「LlamaIndex」の2強です。
私が実務で20件以上のプロジェクトをこなした結論として、検索特化のシステムなら「LlamaIndex」一択だと考えています。

LangChainは「何でもできる」反面、コードが冗長になりがちで、ライブラリのアップデートによる破壊的変更も多いのが難点です。
一方、LlamaIndexは「データとLLMを繋ぐ」ことに特化しており、わずか数行で高精度な検索パイプラインが組めます。
特にPDFのパース（解析）能力や、情報の関連付け（インデックス化）の効率が非常に高く、仕事で即戦力になるのはLlamaIndexの方です。

## Step 1: 環境を整える

まずはプロジェクト用のディレクトリを作成し、必要なライブラリをインストールします。
Python 3.10以上がインストールされていることを前提とします。

```bash
# プロジェクトフォルダを作成して移動
mkdir my-rag-project
cd my-rag-project

# 仮想環境を作成して有効化
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# 必要なライブラリを一括インストール
pip install llama-index openai python-dotenv
```

`llama-index`はRAGの本体、`openai`はLLM接続用、`python-dotenv`はAPIキーを安全に管理するために使用します。
LlamaIndexは非常に多機能なため、インストールには1〜2分ほど時間がかかる場合があります。

⚠️ **落とし穴:**
古いバージョンのPython（3.8未満）を使っていると、ライブラリの依存関係でエラーが出ます。必ず`python --version`で現在の環境を確認してください。また、Windowsユーザーで`pip install`が失敗する場合は、Visual Studioの「C++ によるデスクトップ開発」ツールセットが不足していることが多いです。

## Step 2: 基本の設定

APIキーをコードに直書きするのは、セキュリティ上絶対にNGです。
GitHubなどにうっかりアップロードして、数時間で数万円使われるという事故を私は何度も見てきました。
まずは`.env`ファイルを作成して、そこにAPIキーを記述します。

```text: .env
OPENAI_API_KEY=sk-xxxx...（あなたのAPIキー）
```

次に、LlamaIndexを初期化するためのベースコードを書きます。
ここでは、情報の断片化を防ぐための「チャンクサイズ」の設定がポイントになります。

```python: main.py
import os
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# .envファイルから環境変数を読み込む
load_dotenv()

# LLMの設定: コスパ最強のgpt-4o-miniを指定
# 知識の密度を高めるため、temperatureは低めの0.1に設定
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)

# 埋め込みモデル（ベクトル化）の設定
# 最新のtext-embedding-3-smallは安くて高性能です
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# チャンク設定: 文脈を保持しやすいサイズにする
# 1024は少し大きいと感じるかもしれませんが、日本語の文脈維持にはこれくらいが適切です
Settings.chunk_size = 1024
Settings.chunk_overlap = 50
```

`chunk_overlap`を50に設定しているのは、文章を分割した際に前後の文脈が途切れないようにするためです。
これを0にすると、分割位置によっては意味が通じなくなり、検索精度がガクッと落ちます。

## Step 3: 動かしてみる

次に、PDFを読み込んで検索可能な状態にする「インデックス化」と、実際の問い合せ（Query）の部分を実装します。
プロジェクトフォルダ内に`data`という名前のフォルダを作り、そこに適当なPDFを1つ入れてください。

```python
# main.py の続き

def run_rag():
    # 1. dataフォルダ内のドキュメントを読み込む
    # SimpleDirectoryReaderはPDF, TXT, DOCXなどを自動判別してくれます
    if not os.path.exists("./data"):
        print("dataフォルダが見つかりません。")
        return

    documents = SimpleDirectoryReader("./data").load_data()

    # 2. 読み込んだデータをベクトル化してインデックスを作成
    # ここでOpenAIのAPIに通信が発生します（PDFの量に応じて数秒〜数十秒）
    index = VectorStoreIndex.from_documents(documents)

    # 3. 検索エンジン（Query Engine）の起動
    query_engine = index.as_query_engine(streaming=False)

    # 4. 質問を投げる
    question = "このドキュメントの要約を3行で教えてください。"
    response = query_engine.query(question)

    print(f"\n質問: {question}")
    print(f"回答: {response}")

if __name__ == "__main__":
    run_rag()
```

### 期待される出力

```text
質問: このドキュメントの要約を3行で教えてください。
回答: 1. 本資料は2024年度のAI導入計画に関するガイドラインです。
2. 導入の主な目的は業務効率化とカスタマーサポートの自動化にあります。
3. セキュリティ基準として、個人情報を含むデータの取り扱いルールが定められています。
```

もし「回答にPDFの内容が含まれていない」場合は、PDFが画像形式（スキャンしたもの）である可能性があります。
その場合はOCR（文字認識）が必要になりますが、まずはテキストが選択できるタイプのPDFで試してください。

## Step 4: 実用レベルにする

今のままでは、スクリプトを実行するたびにAPIを叩いてベクトル化を行うため、時間もお金も無駄になります。
実務で使うなら、一度作ったインデックスをローカルに保存（永続化）し、2回目以降はそれを読み込む形にすべきです。

また、回答の根拠となった場所を表示する機能を追加して、信頼性を高めます。

```python: main.py (改良版)
from llama_index.core import StorageContext, load_index_from_storage

def run_practical_rag():
    persist_dir = "./storage"

    if not os.path.exists(persist_dir):
        # 初回実行：インデックスを作成して保存
        print("インデックスを新規作成します...")
        documents = SimpleDirectoryReader("./data").load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=persist_dir)
    else:
        # 2回目以降：保存されたインデックスを読み込み
        print("保存済みインデックスを読み込みます...")
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        index = load_index_from_storage(storage_context)

    query_engine = index.as_query_engine(similarity_top_k=3)

    while True:
        user_input = input("\n質問を入力（exitで終了）: ")
        if user_input.lower() == "exit":
            break

        response = query_engine.query(user_input)
        print(f"\nAI: {response}")

        # 引用元の情報を表示（実務で必須！）
        print("\n--- 参照元 ---")
        for node in response.source_nodes:
            # どのファイルの何ページ目か、類似度はどれくらいかを表示
            file_name = node.metadata.get('file_name', '不明')
            score = node.score
            print(f"File: {file_name} (Score: {score:.4f})")

run_practical_rag()
```

`similarity_top_k=3`の設定は、質問に関連する上位3つのブロックをLLMに渡すという意味です。
ここを増やすと精度は上がりますが、LLMに渡す文字数が増えて料金が高くなるため、3〜5程度が実務上のスイートスポットです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| RateLimitError | OpenAIの無料枠終了、または支払設定ミス | API利用料を$5以上チャージする |
| Empty input | PDFが画像データのみでテキストがない | Adobe Acrobat等でOCR処理をする |
|ModuleNotFoundError| ライブラリのインストール失敗 | `pip install`時に仮想環境が有効か確認 |
| 回答が一般論になる | 関連情報が見つかっていない | `chunk_size`を小さくして検索密度を上げる |

## 次のステップ

ここまでで、ローカルのPDFを読み込んで回答する基本のRAGは完成です。
これをさらに実務で使い倒すなら、以下の3つの方向に拡張することをおすすめします。

1. **データベースの変更**: 今回はローカルフォルダに保存しましたが、データ量が増えて数万件になるなら「Chroma」や「Qdrant」といったベクトルデータベースに移行してください。
2. **UIの実装**: `Streamlit`を使えば、このPythonコードに10行足すだけでブラウザ上で動くチャット画面が作れます。
3. **ハイブリッド検索**: 単純なベクトル検索だけでなく、キーワード一致（BM25）を組み合わせることで、専門用語の検索精度が飛躍的に向上します。

特にLlamaIndexの公式ドキュメントにある「Recursive Retriever」という手法は、複雑な表組みを含むドキュメントを読み解くのに非常に強力です。
次は、ぜひ「表が含まれるPDF」をどう精度良く読み取らせるかに挑戦してみてください。

## よくある質問

### Q1: PDF以外のファイル（ExcelやPowerPoint）も読み込めますか？

はい、LlamaIndexの`SimpleDirectoryReader`は拡張子を自動判別します。ただしExcelは構造が複雑なため、`LlamaParse`という専用のパーサーを組み合わせる方が、表の構造を正しく理解できるのでおすすめです。

### Q2: 会社で使うのでAPI経由でデータを送るのが不安です。

その場合は、LLM部分を`Ollama`を使用してローカルで動かすモデル（Llama 3やGemmaなど）に変更してください。SettingsのLLMとEmbedModelの設定を書き換えるだけで、外部にデータを送らない「完全オフラインRAG」が構築可能です。

### Q3: 検索精度がどうしても上がらないのですが、どこを疑うべきですか？

まずは「PDFのテキストが正しく抽出できているか」を疑ってください。LlamaIndexの`documents`の中身をprintして、文字化けや改行の崩れがないか確認しましょう。データの掃除（クリーニング）が、RAGの精度の8割を決めます。

---

## あわせて読みたい

- [PythonとLlamaIndexで作るRAG入門：手元のPDFを即戦力AIにするやり方](/posts/2026-10-10-llamaindex-rag-tutorial-local-pdf-search/)
- [PythonとLlamaIndexで作るRAGローカル検索の実装ガイド](/posts/2026-08-30-llamaindex-rag-local-search-guide/)
- [Perplexity Computer 検索と計算を融合したAI検索エンジンの実力と活用法](/posts/2026-02-28-perplexity-computer-practical-review-and-api-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "PDF以外のファイル（ExcelやPowerPoint）も読み込めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、LlamaIndexのSimpleDirectoryReaderは拡張子を自動判別します。ただしExcelは構造が複雑なため、LlamaParseという専用のパーサーを組み合わせる方が、表の構造を正しく理解できるのでおすすめです。"
      }
    },
    {
      "@type": "Question",
      "name": "会社で使うのでAPI経由でデータを送るのが不安です。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "その場合は、LLM部分をOllamaを使用してローカルで動かすモデル（Llama 3やGemmaなど）に変更してください。SettingsのLLMとEmbedModelの設定を書き換えるだけで、外部にデータを送らない「完全オフラインRAG」が構築可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "検索精度がどうしても上がらないのですが、どこを疑うべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "まずは「PDFのテキストが正しく抽出できているか」を疑ってください。LlamaIndexのdocumentsの中身をprintして、文字化けや改行の崩れがないか確認しましょう。データの掃除（クリーニング）が、RAGの精度の8割を決めます。 ---"
      }
    }
  ]
}
</script>
