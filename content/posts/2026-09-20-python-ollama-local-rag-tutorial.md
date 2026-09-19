---
title: "PythonとOllamaで実用的なローカルRAGシステムを構築する方法"
date: 2026-09-20T00:00:00+09:00
slug: "python-ollama-local-rag-tutorial"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "RAG"
  - "Ollama"
  - "LangChain"
  - "ローカルLLM"
  - "Python実装"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- ローカルPC内のPDFファイルを読み込み、その内容についてAIと対話できるPythonスクリプトを作ります。
- 外部API（OpenAI等）を一切使わず、機密情報をネットに流さない「完全オフラインRAG」の実装です。
- 前提知識として、Pythonの基本的な文法（importや関数の定義）を理解している必要があります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的。RAGの検証もスムーズ。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルでRAGを動かす上で、最も重要なのはGPUのVRAM（ビデオメモリ）容量です。
結論から言うと、NVIDIA製GPUでVRAM 12GB以上、またはApple Silicon（M1/M2/M3）のメモリ16GB以上のマシンを推奨します。
VRAM 8GBでも動作はしますが、モデルの量子化サイズを極限まで落とす必要があり、回答の精度が目に見えて低下します。

料金面では、今回紹介する構成はすべてオープンソースを利用するため、電気代を除けば完全に無料です。
クラウドサービスを利用する場合、1000ページのPDFをベクトル化して頻繁に検索すると月額数千円から数万円のAPI利用料がかかることも珍しくありません。
実務で大量のドキュメントを扱うなら、最初にRTX 4060 Ti 16GBモデル（約7万円）を導入したほうが、3ヶ月で元が取れる計算になります。

もし手元に十分なGPUがない場合は、無理にローカルで動かそうとせず、まずはGoogle Colabの無料枠で試すのが賢明です。
「動かない」ストレスで時間を溶かすのが、エンジニアにとって最大の損失だからです。

## なぜこの方法を選ぶのか

RAG（検索拡張生成）を実現する方法は、Difyなどのノーコードツールを使うものから、LangChainのようなフレームワークを使うものまで多岐にわたります。
その中で今回、PythonとLangChain、そしてOllamaを組み合わせた「コードベースの実装」を選ぶ理由は、カスタマイズの自由度と透明性にあります。

ノーコードツールは導入こそ早いですが、内部でどのようなプロンプトが投げられ、どのような検索アルゴリズムが動いているかがブラックボックスになりがちです。
実務では「なぜこの回答になったのか」という根拠を求められる場面が多く、検索スコアの調整やチャンク分割のロジックを自分で制御できるコードベースの知識が不可欠になります。
また、Ollamaを採用することで、LLMの起動や管理という面倒なインフラ作業をコマンド一つに集約できるため、開発者はパイプラインの構築に集中できます。

## Step 1: 環境を整える

まずはLLMの実行基盤となるOllamaのインストールと、必要なPythonライブラリを揃えます。

```bash
# Ollamaのインストール（公式サイトからダウンロードして実行）
# https://ollama.com/

# 動作確認とモデルのプル
# 今回は日本語に強く軽量なLlama 3の日本語調整版を使います
ollama run elly/llama3-70b-japanese-instruct-q4_k_m # 高スペック向け
# または
ollama run calm2:7b # 12GB以下のVRAM向け

# Python仮想環境の作成とライブラリインストール
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate
pip install langchain langchain-community langchain-chroma sentence-transformers pypdf
```

`langchain-chroma` はベクトルデータベースの管理に、`pypdf` はPDFの解析に使用します。
`sentence-transformers` は、テキストをベクトル（数値の羅列）に変換するためのライブラリです。

⚠️ **落とし穴:**
Ollamaをインストールしただけで満足し、バックグラウンドでOllamaのサーバーが起動しているか確認し忘れるケースが多いです。
`ollama list` コマンドを打ってエラーが出る場合は、Ollamaアプリが起動しているか確認してください。
また、Python 3.12以降では一部のライブラリがビルドエラーを起こすことがあるため、安定性を重視するなら3.10か3.11の使用を強く勧めます。

## Step 2: 基本の設定

RAGの心臓部である「埋め込み（Embedding）モデル」と「ベクトルDB」の設定を行います。
APIを使わずにローカルで完結させるため、HuggingFaceのモデルを直接ロードします。

```python
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.llms import Ollama

# 1. ドキュメントの読み込み
# 試したいPDFファイルをカレントディレクトリに置いてください
file_path = "manual.pdf"
loader = PyPDFLoader(file_path)
raw_documents = loader.load()

# 2. テキストの分割（チャンク化）
# なぜ分割するのか：LLMには一度に読み込める文字数制限（コンテキスト窓）があるためです
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, # 1つの塊を500文字にする
    chunk_overlap=50, # 文脈を維持するために50文字ずつ重ねる
    add_start_index=True
)
documents = text_splitter.split_documents(raw_documents)

# 3. 埋め込みモデルの設定
# 日本語の検索精度を左右する最重要パーツです
# ここでは軽量で高性能な 'intfloat/multilingual-e5-small' を使用します
model_name = "intfloat/multilingual-e5-small"
embeddings = HuggingFaceEmbeddings(model_name=model_name)

# 4. ベクトルデータベースの構築
# documentsをベクトル化してローカルに保存します
vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory="./chroma_db" # データベースの保存先
)
```

`chunk_size` を500に設定しているのは、日本語の文章構造を考慮した結果です。
これより大きいと検索結果にノイズが混じり、小さいと意味が断片化しすぎてAIが文脈を理解できなくなります。
実務ではドキュメントの種類に合わせて300〜1000の間で調整するのが定石です。

## Step 3: 動かしてみる

構築したベクトルデータベースから情報を検索し、LLMに回答させてみます。

```python
# 5. 検索エンジンの作成
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 6. LLMの設定（Ollama）
llm = Ollama(model="calm2:7b")

# 7. 実行
query = "このマニュアルに記載されている製品の保証期間は何年ですか？"
# 関連する文章を検索
relevant_docs = retriever.invoke(query)

# 検索結果をコンテキストとしてLLMに投げる
context = "\n\n".join([doc.page_content for doc in relevant_docs])
prompt = f"""以下の情報を参考にして、質問に答えてください。
参考情報:
{context}

質問:
{query}
"""

response = llm.invoke(prompt)
print(f"--- 検索された情報の断片 ---\n{context}\n")
print(f"--- AIの回答 ---\n{response}")
```

### 期待される出力

```
--- 検索された情報の断片 ---
本製品の保証期間は、お買い上げの日から3年間です。ただし、バッテリーなどの消耗品は...

--- AIの回答 ---
このマニュアルによると、製品の保証期間はお買い上げの日から3年間です。ただし、バッテリーなどの消耗品は保証対象外となる場合があるため、注意が必要です。
```

結果が出ない場合は、PDFがスキャン画像（文字情報がない状態）でないか確認してください。
その場合はOCR処理が必要になりますが、通常のテキストベースのPDFであれば上記コードで問題なく抽出できるはずです。

## Step 4: 実用レベルにする

実務で使うには「検索の精度」と「回答の安定性」が課題になります。
単純な検索（ベクトル検索）だけでは、専門用語の完全一致に弱いという弱点があります。
これを解決するために、BM25などのキーワード検索と組み合わせる「ハイブリッド検索」や、一度投げられた質問をLLM自身に改善させる「Query Transformation」という手法がありますが、まずは「プロンプトの固定化」から始めましょう。

また、一度作成したデータベースを毎回作り直すのは時間の無駄です。
以下のように、既存のデータベースを読み込む処理を追加して実用性を高めます。

```python
def get_rag_response(user_query: str, db_path: str = "./chroma_db"):
    # 既存のDBを読み込む（埋め込みモデルはStep 2と同じものを使用）
    embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")
    vectorstore = Chroma(persist_directory=db_path, embedding_function=embeddings)

    # 検索（類似度スコアも取得するように設定）
    retriever = vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": 0.5, "k": 5}
    )

    docs = retriever.invoke(user_query)

    if not docs:
        return "関連する情報が見つかりませんでした。質問の内容を変えてみてください。"

    context = "\n".join([f"資料{i+1}: {d.page_content}" for i, d in enumerate(docs)])

    # 指示を明確にするプロンプトエンジニアリング
    system_prompt = f"""あなたは誠実なアシスタントです。提供された資料のみに基づいて回答してください。
資料に記載がない場合は「分かりません」と答え、勝手に推測しないでください。

資料:
{context}

質問: {user_query}
回答:"""

    llm = Ollama(model="calm2:7b", temperature=0) # 0に設定して回答の揺れを抑える
    return llm.invoke(system_prompt)

# 使用例
print(get_rag_response("消耗品の交換時期はいつ？"))
```

`temperature=0` の設定は非常に重要です。
クリエイティブな文章を書かせるなら高い値が良いですが、RAGのような「事実に基づく回答」を求める場合は、0に設定してAIの勝手な推論（ハルシネーション）を抑制するのが鉄則です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Ollama not found` | Ollamaがインストールされていない、またはPATHが通っていない | Ollama公式サイトから再インストールし、ターミナルを再起動する |
| `OutOfMemoryError` | GPUのVRAMが不足している | モデルをより小さいもの（3bなど）に変えるか、`ollama run` 時の量子化版を試す |
| 検索結果が的外れ | 埋め込みモデルが日本語に最適化されていない | `multilingual-e5` シリーズや、最新の日本語専用Embeddingモデルを使用する |
| 回答が英語になる | LLMモデルが日本語を十分に学習していない | `calm2` や `elyza` など、日本語に特化したモデルを指定する |

## 次のステップ

ここまでで、基本的なローカルRAGの仕組みは完成しました。
しかし、実務で「本当に使える」レベルにするには、ここからがスタートです。
次に挑戦すべきは、以下の3点です。

1. **評価（Evaluation）の導入:**
RAGの回答が正しいかどうかを、人間が毎回確認するのは不可能です。RAGAS（RAG Assessment）というフレームワークを使って、検索の適合率や回答の正確性を数値化することに挑戦してください。
2. **メタデータフィルタリング:**
「2023年度の資料だけから探す」といった条件付き検索を実装します。ChromaDBの `filter` 機能を使いこなせるようになると、社内システムの検索エンジンとして実用的になります。
3. **ストリーミング表示のUI化:**
今回のコードは回答がすべて生成されてから表示されますが、実用的なアプリにするなら、Streamlitなどを使って文字が1文字ずつ出てくる（ストリーミング）UIを実装しましょう。

ローカルLLMの世界は日進月歩ですが、この「データをベクトル化して検索し、LLMに渡す」という基本構造は変わりません。
まずは自分の手元で1つのPDFを完璧に読み込ませる経験を積んでください。

## よくある質問

### Q1: PDF以外のファイル（WordやExcel）も読み込めますか？

可能です。LangChainには `UnstructuredWordDocumentLoader` や `UnstructuredExcelLoader` が用意されています。ただし、Excelは構造化データなので、単なるテキスト分割よりも「1行1チャンク」にするなどの工夫をしないと精度が出にくいのが特徴です。

### Q2: 検索のレスポンスを速くするにはどうすればいいですか？

埋め込みモデルの次元数を下げるのが最も効果的です。今回使用した `multilingual-e5-small` は非常に高速ですが、さらに速さを求めるなら、ベクトルDBのインデックス設定を `HNSW` に明示的に指定することで、検索アルゴリズムを最適化できます。

### Q3: 社内サーバーに構築する場合、GPUは必須ですか？

推論速度を気にしない（1回答に30秒以上かかっても良い）のであれば、CPUのみでも動作はします。しかし、複数人が同時にアクセスする環境なら、RTX 4090クラス、あるいはA100/H100などのサーバーグレードGPUが実質的に必須となります。

---

## あわせて読みたい

- [PythonとLangChainで自分専用のPDF検索AIチャットボットを作る方法](/posts/2026-06-28-local-rag-langchain-faiss-tutorial/)
- [Pythonで作るローカルRAG入門：自作検索AIを完全オフラインで動かす方法](/posts/2026-08-20-local-rag-python-ollama-tutorial/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法](/posts/2026-09-06-ollama-open-webui-local-llm-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "PDF以外のファイル（WordやExcel）も読み込めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。LangChainには UnstructuredWordDocumentLoader や UnstructuredExcelLoader が用意されています。ただし、Excelは構造化データなので、単なるテキスト分割よりも「1行1チャンク」にするなどの工夫をしないと精度が出にくいのが特徴です。"
      }
    },
    {
      "@type": "Question",
      "name": "検索のレスポンスを速くするにはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "埋め込みモデルの次元数を下げるのが最も効果的です。今回使用した multilingual-e5-small は非常に高速ですが、さらに速さを求めるなら、ベクトルDBのインデックス設定を HNSW に明示的に指定することで、検索アルゴリズムを最適化できます。"
      }
    },
    {
      "@type": "Question",
      "name": "社内サーバーに構築する場合、GPUは必須ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "推論速度を気にしない（1回答に30秒以上かかっても良い）のであれば、CPUのみでも動作はします。しかし、複数人が同時にアクセスする環境なら、RTX 4090クラス、あるいはA100/H100などのサーバーグレードGPUが実質的に必須となります。 ---"
      }
    }
  ]
}
</script>
