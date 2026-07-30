---
title: "LlamaIndexとPythonで作るローカルRAG検索システム実装ガイド"
date: 2026-07-30T00:00:00+09:00
slug: "llamaindex-local-rag-python-guide"
cover:
  image: "/images/posts/2026-07-30-llamaindex-local-rag-python-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "LlamaIndex 使い方"
  - "ローカルRAG 実装"
  - "Python AI 検索"
  - "Ollama 連携"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

手元のPDFやテキストファイルを読み込み、その内容に基づいてAIが回答する「ローカルRAG（検索拡張生成）システム」をPythonで構築します。
外部APIにデータを送信せず、ローカル環境で情報の検索から回答生成までを完結させるための最小構成スクリプトを作成します。

前提知識：
- Pythonの基本的な文法（変数、関数、パッケージのインストール）がわかる
- ターミナル（コマンドプロンプト）での操作に抵抗がない

必要なもの：
- Python 3.10以上の環境
- メモリ16GB以上のPC（Windows/Macどちらでも可）
- ローカルLLMを実行するためのツール「Ollama」

## 先に確認するスペック・料金

RAGをローカルで動かす際、ボトルネックになるのは「推論速度」と「メモリ容量」です。
結論から言うと、GPU（VRAM 8GB以上）があれば快適ですが、CPUだけでも数秒待てば回答は得られます。

ハードウェアについて、私はRTX 4090を2枚使っていますが、これから始めるならRTX 4060 Ti (16GB版) が最もコストパフォーマンスが良いです。
Macユーザーなら、メモリ（ユニファイドメモリ）が32GB以上のモデルを強く推奨します。
16GBだと、LLMとブラウザを同時に立ち上げた瞬間にスワップが発生し、レスポンスが極端に低下するためです。

料金面では、今回の手法は完全に無料です。
OpenAIのAPIを使えば月額数千円かかる計算量でも、ローカルなら電気代だけで済みます。
もし「手元のPCが非力すぎて動かない」という場合は、Google Colabの無料枠を使うか、月額20ドルのChatGPT Plusを使う方が賢明です。
自分の環境で「1トークン出すのに何秒かかるか」を計測し、実用性を判断してください。

## なぜこの方法を選ぶのか

RAGの実装にはLangChainを使うのが一般的ですが、私は「LlamaIndex」を推奨します。
LangChainは多機能すぎて構造が複雑になりがちですが、LlamaIndexは「データとLLMを繋ぐ」ことに特化しているため、コードが非常にシンプルにまとまるからです。

また、検索エンジンにはベクトルデータベース（ChromaやQdrant）を使わずに、まずはLlamaIndex標準の「SimpleVectorStore」を使います。
最初からデータベースサーバーを立てると、環境構築の段階で挫折する人が多いためです。
ファイルベースで保存・読み込みができる仕組みを構築し、まずは「自分のデータで回答が返ってくる感動」を最優先します。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
バージョン依存によるエラーを防ぐため、LlamaIndexのコアパッケージと、HuggingFaceの埋め込みモデル（Embedding）用ライブラリを明示的に指定します。

```bash
# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# ライブラリのインストール
pip install llama-index==0.10.50 llama-index-embeddings-huggingface llama-index-llms-ollama
```

`llama-index-embeddings-huggingface`は、テキストを数値ベクトルに変換する「埋め込みモデル」をローカルで動かすために必要です。
`llama-index-llms-ollama`は、ローカルLLM実行基盤であるOllamaと連携するためのアダプターです。

⚠️ **落とし穴:**
Windowsユーザーで「error: Microsoft Visual C++ 14.0 or greater is required」と表示された場合は、ビルドツールが不足しています。
Visual Studio Installerから「C++ によるデスクトップ開発」をインストールしてください。
これを回避しようとするより、指示通りに入れるのが結局一番近道です。

## Step 2: 基本の設定

次に、ローカルで動かすLLMと埋め込みモデルの設定を行います。
ここでは日本語に強い埋め込みモデル「multilingual-e5-base」を採用します。

```python
import os
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama

# 1. 埋め込みモデルの設定（日本語に強いモデルを選択）
# ローカルのCPU/GPUで動作します
Settings.embed_model = HuggingFaceEmbedding(
    model_name="intfloat/multilingual-e5-base"
)

# 2. LLMの設定（Ollama経由でLlama 3などを利用）
# 事前に `ollama run llama3` 等でモデルをダウンロードしておく必要があります
Settings.llm = Ollama(model="llama3", request_timeout=120.0)

# 3. チャンクサイズの設定
# 文書をどれくらいの長さで区切るか。512が精度と速度のバランスが良いです
Settings.chunk_size = 512
Settings.chunk_overlap = 50
```

`multilingual-e5-base`を使う理由は、日本語の検索精度がOpenAIの「text-embedding-3-small」に匹敵するほど高いからです。
設定値の`chunk_size`を512にしているのは、これ以上大きくするとLLMのコンテキストを圧迫し、小さすぎると文脈が途切れて検索精度が落ちるためです。

## Step 3: 動かしてみる

プロジェクトの直下に `data` というフォルダを作成し、適当なテキストファイル（例: `company_rule.txt`）を置いてください。
そのファイルを読み込んで検索する最小コードを書きます。

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# 1. データの読み込み
# dataフォルダ内のすべてのファイルを自動でスキャンします
documents = SimpleDirectoryReader("./data").load_data()

# 2. インデックスの作成（ここでテキストがベクトル化される）
# 初回実行時はモデルのダウンロードが始まるため時間がかかります
index = VectorStoreIndex.from_documents(documents)

# 3. クエリエンジンの作成
query_engine = index.as_query_engine()

# 4. 質問を投げる
response = query_engine.query("弊社の夏季休暇は何日間ですか？")
print(f"回答: {response}")
```

### 期待される出力

```
回答: 弊社の規定によると、夏季休暇は7月1日から9月30日までの期間内に、合計5日間取得することが可能です。
```

結果が出力されれば成功です。
もし回答が英語になった場合は、`Ollama(model="llama3")`の部分を日本語が得意なモデル（例: `gemma2`）に変更してください。
ローカルLLMはモデル選び一つで、回答の質が劇的に変わります。

## Step 4: 実用レベルにする

今のコードは、実行するたびにすべてのドキュメントをベクトル化しています。
これではファイルが増えたときに時間がかかりすぎるため、作成したベクトルデータをディスクに保存（永続化）するように改良します。

```python
import os
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage
)

STORAGE_DIR = "./storage"

def get_query_engine():
    # 既にインデックスが保存されているかチェック
    if not os.path.exists(STORAGE_DIR):
        print("インデックスを新規作成します...")
        documents = SimpleDirectoryReader("./data").load_data()
        index = VectorStoreIndex.from_documents(documents)
        # ディスクに保存
        index.storage_context.persist(persist_dir=STORAGE_DIR)
    else:
        print("保存済みのインデックスを読み込みます...")
        # ディスクから読み込み
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
        index = load_index_from_storage(storage_context)

    return index.as_query_engine(streaming=True)

# 実行
engine = get_query_engine()
response = engine.query("経費精算の締め日はいつ？")

# ストリーミング表示（文字がパラパラ出てくる実用的なUI）
for token in response.response_gen:
    print(token, end="", flush=True)
```

実務でRAGを運用する場合、この「永続化」と「ストリーミング」は必須です。
特にストリーミングは、回答生成までの「体感時間」を短縮するために極めて重要です。
また、`SimpleDirectoryReader`はPDFやDocxも自動で判別して読み込んでくれますが、PDF内の表形式データは読み取りに失敗しやすいという弱点があります。
表を正確に読み込みたい場合は、`LlamaParse`などの専用ツールを検討すべきですが、まずはこの標準機能で十分実戦投入できます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| ConnectionError | Ollamaが起動していない | ターミナルで `ollama serve` を実行し、起動を確認する |
| Out of Memory (OOM) | VRAMまたはメインメモリ不足 | 1.3bや3bなど、よりパラメータ数の少ないモデルに変更する |
| 回答が「情報がありません」 | 検索精度の不足 | チャンクサイズを調整するか、日本語に特化したEmbeddingモデルを再確認する |

## 次のステップ

ここまでで、ローカル環境におけるRAGの基本骨格は完成しました。
しかし、実務で「本当に使える」レベルにするには、あと2つの壁があります。

一つは「リランク（再順位付け）」の導入です。
ベクトル検索は「似ている文章」を探すのは得意ですが、「正しい回答が含まれている文章」をピンポイントで当てる確率は意外と低いです。
上位10件の候補を出し、それを別の小型モデルで精査させることで、回答の精度を20〜30%向上させることができます。

もう一つは「メタデータフィルタリング」です。
「2023年の資料だけから探して」といった条件指定ができるようにすることで、古い情報に基づいた誤回答を防げます。
これらは LlamaIndex の `VectorStoreIndex` に引数を追加するだけで実装可能です。
まずは手元のドキュメントを100個ほど放り込んで、どこまで正確に答えられるか限界を試してみてください。

## よくある質問

### Q1: 社内の秘密情報を読み込ませても本当に安全ですか？

はい、完全に安全です。今回のコードでは、EmbeddingモデルもLLMも、すべてあなたのPC内で動作しています。インターネットを切断した状態でも動作させることができるため、外部にデータが漏れるリスクは物理的にゼロです。

### Q2: 処理速度を上げるにはどこに投資すべきですか？

最優先はGPUのVRAM容量です。次に「SSDの読み込み速度」です。ベクトルデータの読み書きは頻繁に発生するため、SATA接続のSSDよりはNVMe接続のM.2 SSDを使うことで、起動時のインデックス読み込みが劇的に速くなります。

### Q3: PDF以外のデータ、例えばスプレッドシートなどは読み込めますか？

読み込めますが、そのままでは精度が低いです。Excelやスプレッドシートは、Pandasを使ってCSV形式に変換してから読み込ませるか、LlamaIndexの `PandasQueryEngine` を使うことをおすすめします。構造化データにはベクトル検索よりも、コード生成による集計の方が向いています。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLMとRAGを快適に動かすための最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Parallax 使い方 レビュー：ローカル完結型AI開発オーケストレーターの真価](/posts/2026-03-17-parallax-local-ai-orchestrator-review-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "社内の秘密情報を読み込ませても本当に安全ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、完全に安全です。今回のコードでは、EmbeddingモデルもLLMも、すべてあなたのPC内で動作しています。インターネットを切断した状態でも動作させることができるため、外部にデータが漏れるリスクは物理的にゼロです。"
      }
    },
    {
      "@type": "Question",
      "name": "処理速度を上げるにはどこに投資すべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "最優先はGPUのVRAM容量です。次に「SSDの読み込み速度」です。ベクトルデータの読み書きは頻繁に発生するため、SATA接続のSSDよりはNVMe接続のM.2 SSDを使うことで、起動時のインデックス読み込みが劇的に速くなります。"
      }
    },
    {
      "@type": "Question",
      "name": "PDF以外のデータ、例えばスプレッドシートなどは読み込めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "読み込めますが、そのままでは精度が低いです。Excelやスプレッドシートは、Pandasを使ってCSV形式に変換してから読み込ませるか、LlamaIndexの PandasQueryEngine を使うことをおすすめします。構造化データにはベクトル検索よりも、コード生成による集計の方が向いています。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでローカルLLMとRAGを快適に動かすための最適解</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
