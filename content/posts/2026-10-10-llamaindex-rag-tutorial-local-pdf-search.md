---
title: "PythonとLlamaIndexで作るRAG入門：手元のPDFを即戦力AIにするやり方"
date: 2026-10-10T00:00:00+09:00
slug: "llamaindex-rag-tutorial-local-pdf-search"
cover:
  image: "/images/posts/2026-10-10-llamaindex-rag-tutorial-local-pdf-search.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "LlamaIndex 使い方"
  - "RAG 入門"
  - "Python PDF 検索"
  - "OpenAI API 実装"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 指定したフォルダ内のPDF群を解析し、独自の知識として回答できるRAG（検索拡張生成）スクリプトを作ります。
- 検索エンジンには「LlamaIndex」を使い、ベクトルデータの保存・再利用まで実装します。
- 前提知識として、Pythonの基本的な文法（関数の定義やライブラリのインポート）がわかる必要があります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルEmbeddingや小型LLMを試すのに最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

RAGを構築する上で、最もコストがかかるのは「Embedding（ベクトル化）」と「LLMによる生成」です。
今回は実用性を重視してOpenAIのAPIを使いますが、10ページ程度のPDFを数枚読み込ませる程度なら、1回あたりのコストは1円もかかりません。

PCスペックは、一般的なビジネスノートPC（メモリ8GB以上）で十分動作します。
ただし、将来的にローカルLLM（Llama 3やQwenなど）を動かしたいのであれば、VRAM 12GB以上のGPU（RTX 3060 12GBやRTX 4070以上）を搭載したデスクトップ、あるいはメモリ16GB以上のApple Silicon Macを推奨します。
私はRTX 4090を2枚使っていますが、推論速度0.1秒の世界を一度味わうと、クラウド経由の遅延が気になって仕事にならなくなるのが本音です。

API料金を抑えたい場合は、Embeddingモデルに`text-embedding-3-small`を指定してください。
これまでの`ada-002`に比べて、価格が5分の1程度に抑えられており、精度も実務レベルで申し分ありません。

## なぜこの方法を選ぶのか

RAGを実装するライブラリとして「LangChain」と「LlamaIndex」のどちらを使うべきか、多くの人が悩みます。
結論から言うと、社内文書の検索やデータ連携をメインにするなら「LlamaIndex」がベストです。

LangChainは汎用性が高すぎてコードが冗長になりがちですが、LlamaIndexは「データとLLMを繋ぐ」ことに特化しています。
特にPDFのパース、チャンク分割、ベクトルDBへの保存といった一連の流れが数行で完結するため、実装ミスが減り、メンテナンスコストも下がります。
私が以前、数万件の法務文書を扱うシステムを組んだ際も、最終的にはLlamaIndexの方が圧倒的にコードの見通しが良くなりました。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
LlamaIndexは更新頻度が高いため、バージョンを固定してインストールするのが現場の鉄則です。

```bash
# 仮想環境を作成（推奨）
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# 必要なライブラリを一括インストール
pip install llama-index==0.10.50 openai==1.35.10 python-dotenv==1.0.1
```

`llama-index`は本体だけでなく、内部でさまざまなプラグインを読み込みます。
`python-dotenv`は、APIキーをコード内に直書きせず、`.env`ファイルから安全に読み込むために使用します。

⚠️ **落とし穴:**
LlamaIndexはv0.10から大幅なアーキテクチャ変更（コア分離）が行われました。古いネット記事のコードをコピーしても「No module named 'llama_index.core'」といったエラーで動かないことが多々あります。必ず最新のドキュメントか、この記事のようなv0.10対応のコードを参考にしてください。

## Step 2: 基本の設定

プロジェクトのルートディレクトリに、APIキーを記述した`.env`ファイルと、解析したいPDFを入れる`data`フォルダを作成します。

```text
.
├── .env
├── data/           # ここにPDFファイルを入れる
├── storage/        # ここに作成したインデックスが保存される
└── main.py
```

`.env`ファイルの内容：
```text
OPENAI_API_KEY=sk-xxxx...（あなたのAPIキー）
```

次に、`main.py`を作成し、初期設定を書きます。

```python
import os
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.llms.openai import OpenAI

# .envファイルを読み込む
load_dotenv()

# APIキーの確認。設定されていないとLLMが動かない
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEYが設定されていません。.envファイルを確認してください。")

# LLMの設定。実務では「gpt-4o-mini」がコスパ最強です
# 以前はgpt-3.5-turboが主流でしたが、今は価格・精度ともに4o-miniで決まりです
llm = OpenAI(model="gpt-4o-mini", temperature=0.1)
```

`temperature=0.1`に設定しているのは、RAGにおいては「AIの創造性」よりも「文書に基づいた正確性」が求められるからです。
値を大きくすると回答がブレやすくなり、実務では使い物になりません。

## Step 3: 動かしてみる

いよいよPDFを読み込み、検索可能な「インデックス」を作成します。
ここで重要なのは、一度作ったインデックスをディスクに保存する仕組みを入れることです。

```python
# main.py の続き

def get_index():
    PERSIST_DIR = "./storage"

    # すでにインデックスが保存されているかチェック
    if not os.path.exists(PERSIST_DIR):
        print("インデックスを新規作成します...")
        # dataフォルダ内のPDFをすべて読み込む
        documents = SimpleDirectoryReader("./data").load_data()
        # ベクトル化してインデックス作成
        index = VectorStoreIndex.from_documents(documents)
        # フォルダに保存。これで次回からAPI代と時間を節約できる
        index.storage_context.persist(persist_dir=PERSIST_DIR)
    else:
        print("保存されたインデックスを読み込みます...")
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)

    return index

# 実行
index = get_index()
query_engine = index.as_query_engine(llm=llm)

# 質問してみる
response = query_engine.query("この資料の要点を3つでまとめてください。")
print(response)
```

### 期待される出力

```text
保存されたインデックスを読み込みます...
1. 本資料は〇〇プロジェクトの進捗について記述しています。
2. 課題として△△の遅延が指摘されています。
3. 今後の対策として、人員を2名追加する計画が提案されています。
```

`SimpleDirectoryReader`は優秀で、PDFだけでなくテキストファイルやDocxも自動で判別して読み込んでくれます。
まずは手元にあるPDFを`data`フォルダに入れて、このコードを動かしてみてください。

## Step 4: 実用レベルにする

実務でRAGを使う際、一番の課題は「AIの嘘（ハルシネーション）」と「情報の参照元が不明」な点です。
どの資料の何ページ目を参考にしたのかを表示できるように、クエリエンジンを拡張します。

```python
# 実用的な検索関数の例
def ask_ai(question):
    index = get_index()
    # 検索結果（ノード）を5件取得するように設定（デフォルトは2件）
    # 参照元を増やすことで回答の精度が上がりますが、その分トークン消費も増えます
    query_engine = index.as_query_engine(
        llm=llm,
        similarity_top_k=5
    )

    response = query_engine.query(question)

    print(f"\n質問: {question}")
    print(f"回答: {response}")
    print("\n--- 参照元情報 ---")

    # どのファイルのどの部分を参考にしたかを表示
    for node in response.source_nodes:
        file_name = node.metadata.get('file_name', '不明')
        score = node.score
        # 類似度スコアが0.8以上のものだけを表示すると信頼性が上がります
        print(f"File: {file_name} (Score: {score:.4f})")
        # 引用箇所を一部表示
        print(f"Text: {node.text[:100]}...")
        print("-" * 20)

# 実行例
ask_ai("予算の承認フローはどうなっていますか？")
```

このコードにより、「なぜその回答になったのか」を人間が検証できるようになります。
私が以前構築した社内QAシステムでは、この参照元リンク機能があるだけで、現場の安心感が劇的に向上しました。
スコア（`node.score`）を表示するのもコツです。0.7を切っているような回答は、AIが無理やり関係ない文書を結びつけている可能性が高いと判断できます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `RateLimitError` | OpenAIの無料枠超過、または支払い未完了 | APIの利用制限を確認し、クレジットをチャージする |
| `NotImplementedError` | PDFの暗号化や特殊形式 | `pip install pypdf` を実行して、PDFリーダーを明示的に指定する |
| 回答が「わかりません」になる | チャンクサイズが不適切、またはPDFの文字が画像化されている | OCR済みのPDFを使うか、`LlamaParse`などの高度なパーサーを検討する |

## 次のステップ

この記事で作成したRAGシステムは、あくまでも「基本形」です。
実務でさらに精度を追求したいのであれば、以下の3点に挑戦してください。

1. **LlamaParseの導入:** LlamaIndex公式が提供するPDFパーサーです。標準のリーダーでは崩れがちな「複雑な表」や「2段組みのレイアウト」を驚くほど正確に読み取ります。
2. **ハイブリッド検索の実装:** ベクトル検索（意味で探す）と、BM25（キーワードで探す）を組み合わせる手法です。製品番号や固有名詞で検索する際、精度が劇的に向上します。
3. **ストリーミング出力:** `query_engine.query` を `query_engine.stream_query` に変更して、ChatGPTのように一文字ずつ回答を表示させるUIを構築してみましょう。

RAGの構築は「一度作って終わり」ではありません。
ユーザーの質問をログに溜め、どのドキュメントがヒットしなかったのかを分析し、データを整理し直す地道な作業が、最強のAIを作る唯一の道です。

## よくある質問

### Q1: PDFではなくWebサイトのURLを読み込ませることはできますか？

可能です。LlamaIndexには`BeautifulSoupWebReader`というツールが用意されています。PDFの代わりにURLリストを渡すだけで、今回と同じ仕組みでサイト内検索AIが作れます。

### Q2: 会社で使うのでデータを外部に送りたくありません。

その場合は、EmbeddingモデルをHuggingFaceの日本語モデル（`intfloat/multilingual-e5-small`など）に、LLMをOllama経由のローカルLLMに差し替えることで、完全オフラインでの動作が可能です。

### Q3: インデックスを更新するには、毎回フォルダを削除して作り直しですか？

いいえ。`SimpleDirectoryReader`には、ファイルの更新日時を見て差分だけを取り込む機能があります。大規模なドキュメント群を扱う場合は、再作成ではなく差分更新を実装するのが一般的です。

---

## あわせて読みたい

- [OllamaとOpen WebUIを連携させ、完全にオフラインで動作する「プライベートChatGPT環境」を構築します。](/posts/2026-07-20-ollama-open-webui-local-llm-tutorial/)
- [PythonとLlamaIndexで作るRAGローカル検索の実装ガイド](/posts/2026-08-30-llamaindex-rag-local-search-guide/)
- [PythonとLlamaIndexでRAGパイプラインを自作する方法](/posts/2026-07-31-llamaindex-rag-local-embedding-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "PDFではなくWebサイトのURLを読み込ませることはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。LlamaIndexにはBeautifulSoupWebReaderというツールが用意されています。PDFの代わりにURLリストを渡すだけで、今回と同じ仕組みでサイト内検索AIが作れます。"
      }
    },
    {
      "@type": "Question",
      "name": "会社で使うのでデータを外部に送りたくありません。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "その場合は、EmbeddingモデルをHuggingFaceの日本語モデル（intfloat/multilingual-e5-smallなど）に、LLMをOllama経由のローカルLLMに差し替えることで、完全オフラインでの動作が可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "インデックスを更新するには、毎回フォルダを削除して作り直しですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ。SimpleDirectoryReaderには、ファイルの更新日時を見て差分だけを取り込む機能があります。大規模なドキュメント群を扱う場合は、再作成ではなく差分更新を実装するのが一般的です。 ---"
      }
    }
  ]
}
</script>
