---
title: "Qwen2.5 32B 使い方 入門：ローカル環境で爆速RAGシステムを構築する方法"
date: 2026-04-13T00:00:00+09:00
slug: "local-rag-qwen2-5-32b-ollama-tutorial"
cover:
  image: "/images/posts/2026-04-13-local-rag-qwen2-5-32b-ollama-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen2.5-32B"
  - "ローカルRAG"
  - "Ollama 使い方"
  - "LangChain Python"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 手元のPDFドキュメントの内容を、完全にオフラインで解析・回答する「ローカルRAG（検索拡張生成）システム」
- 前提知識：Pythonの基本的な文法（変数、関数）がわかり、ターミナルでコマンド操作ができること
- 必要なもの：メモリ32GB以上のPC（GPUはRTX 3060 12GB以上推奨。MacならM2/M3搭載機）、Python 3.10以上

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 3090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">32Bモデルを快適に動かすには24GBのVRAMが最もコストパフォーマンスに優れています</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%203090%2024GB%20%E4%B8%AD%E5%8F%A4&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2520%25E4%25B8%25AD%25E5%258F%25A4%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2520%25E4%25B8%25AD%25E5%258F%25A4%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

これまでローカルLLMの世界では「軽量だが賢くない7B」か「賢いが動かすのが困難な70B」の二択でした。しかし、Qwen2.5で登場した「32B」というウェイトクラスは、この常識を破壊しました。RTX 3090や4090といった消費者向けハイエンドGPUの24GB VRAMに、4-bit量子化なら余裕で収まりつつ、性能は旧世代の70Bモデルを凌駕します。

クラウドAPIを使えば数分で実装できますが、業務データや機密文書を扱う場合、データ流出のリスクをゼロにはできません。本記事では、推論エンジンに「Ollama」、オーケストレーションに「LangChain」を採用します。この組み合わせは、現在最もエコシステムが成熟しており、一度構築すればモデルを入れ替えるだけで最新の技術を追いかけられるからです。

## Step 1: 環境を整える

まずは、推論エンジンであるOllamaをインストールし、32Bモデルをダウンロードします。

```bash
# Ollamaのインストール（公式サイトからダウンロードも可能）
# macOS/Linuxの場合
curl -fsSL https://ollama.com/install.sh | sh

# Qwen2.5 32Bモデルのプル（ダウンロード）
# 4-bit量子化版であれば約19GBの容量が必要です
ollama pull qwen2.5:32b

# 動作確認
ollama run qwen2.5:32b "AIのウェイトクラスについて3行で説明して"
```

Ollamaは内部でllama.cppを動かしており、OSやハードウェアに合わせて最適な命令セット（AVX2やCUDAなど）を自動選択してくれます。自分自身でビルドする手間を省きつつ、最高速の推論環境を手に入れられるのが最大のメリットです。

⚠️ **落とし穴:** VRAMが16GB以下のGPUで32Bモデルを動かそうとすると、処理が極端に遅くなる（1トークン/秒以下）ことがあります。これはVRAMから溢れたデータがメインメモリ（RAM）にスワップされるためです。その場合は、モデルを「qwen2.5:14b」や「qwen2.5:7b」に下げて試してください。

## Step 2: Python環境とライブラリの設定

次に、RAGを構成するためのPythonライブラリをインストールします。仮想環境（venvやconda）を作成してから実行することを強く推奨します。

```bash
# ライブラリのインストール
pip install langchain langchain-ollama langchain-community pypdf faiss-cpu
```

Pythonコードを作成します。APIキーを直書きする必要はありませんが、ライブラリのバージョン依存が激しいため、最新版を入れるようにしてください。

```python
import os
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

# モデル名の定義。Ollamaでプルした名前と一致させる
MODEL_NAME = "qwen2.5:32b"

# 1. LLMの初期化
# temperature=0にするのは、RAGにおいてモデルの「創作」を抑え、事実に忠実にさせるためです
llm = ChatOllama(model=MODEL_NAME, temperature=0)

# 2. 埋め込みモデル（Embedding）の初期化
# 本来は専用モデルが良いですが、今回は手軽にOllamaのモデルを流用します
embeddings = OllamaEmbeddings(model=MODEL_NAME)
```

「なぜ埋め込みモデルも32Bにするのか」と疑問に思うかもしれません。本来は`mxbai-embed-large`などの軽量な専用モデルを使うのが定石ですが、最初は同じモデルで完結させたほうが設定ミスが減り、ベクトル空間の整合性も取りやすいためです。

## Step 3: PDFを読み込んでベクトル化する

RAGの肝となる、ドキュメントの「ベクトル化」と「保存」を行います。

```python
# PDFの読み込み（カレントディレクトリに sample.pdf を置いてください）
loader = PyPDFLoader("sample.pdf")
docs = loader.load()

# テキストの分割
# chunk_sizeは、一度にLLMに渡す情報の塊のサイズです
# 32Bモデルは文脈理解が強いため、少し大きめの1000トークン程度に設定します
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
splits = text_splitter.split_documents(docs)

# ベクトルストア（FAISS）の構築
# ここでPDFの内容が数値化され、検索可能な状態になります
vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
```

### 期待される出力
このコードを実行すると、バックグラウンドでOllamaが動き出し、GPUの使用率が跳ね上がります。数秒から数十秒で完了し、エラーが出なければ成功です。

## Step 4: 実用レベルのQAシステムにする

最後に、ユーザーの質問に対して「関連情報を検索し、それを踏まえて回答する」処理を実装します。

```python
# 検索機能の作成
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# チェーン（一連の処理）の構築
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True
)

# 実際の質問
query = "この資料に記載されている主なリスクと対策は何ですか？"

try:
    response = qa_chain.invoke(query)
    print("--- 回答 ---")
    print(response["result"])
    print("\n--- 参照元ドキュメント ---")
    for doc in response["source_documents"]:
        print(f"ページ: {doc.metadata['page']} / 内容の一部: {doc.page_content[:50]}...")
except Exception as e:
    print(f"エラーが発生しました: {e}")
    print("Ollamaが起動しているか、VRAMが不足していないか確認してください。")
```

実務で使えるレベルにするために、`return_source_documents=True`を設定しています。これにより、AIが「どこを読んでそう答えたか」の根拠を表示でき、ハルシネーション（嘘）のチェックが容易になります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ConnectionError: Ollama not found` | Ollamaサービスが未起動 | `ollama serve` を実行するかアプリを起動 |
| `OutOfMemoryError` (CUDA) | VRAM容量不足 | 14bや7bなど、より小さいモデルに変更する |
| 回答が英語になる | システムプロンプトが未設定 | プロンプトに「日本語で答えて」と明示的に追加 |

## 次のステップ

ここまでの内容で、32Bモデルという「新しい武器」を使ったローカルRAGの基礎は完成です。次は、以下のステップに挑戦してみてください。

1. **プロンプトエンジニアリングの最適化**: `PromptTemplate`を使い、AIに対して「あなたはプロの法務担当者です」といった役割を与えると、回答の精度が劇的に向上します。
2. **高速化（GGUF量子化の検討）**: Ollamaは標準で4-bitですが、さらに軽量な3-bitや2-bitの量子化モデルを自作して読み込むことも可能です。
3. **UIの実装**: Streamlitを使えば、このPythonコードをわずか10行程度の追加でブラウザから使えるウェブアプリに進化させられます。

32Bクラスの登場により、もはや「個人や小規模チームでは性能不足」という言い訳は通用しなくなりました。実務で使えるAIは、今やあなたのローカルPCの中にあります。

## よくある質問

### Q1: 32Bモデルを動かすのにRTX 4090は必須ですか？

必須ではありません。RTX 3060(12GB)でも、4-bit量子化なら14Bモデルまでは快適に、32Bモデルも低速（数トークン/秒）ながら動作します。実務的な速度を求めるなら、VRAM 16GB以上のRTX 4080や、24GBの3090/4090が推奨されます。

### Q2: PDFが100ページ以上ある場合でも動きますか？

動きますが、ベクトル化（Step 3）に時間がかかります。大規模なドキュメントを扱う場合は、一度構築したFAISSのインデックスを `vectorstore.save_local("faiss_index")` で保存し、次回からロードするようにコードを修正すると効率的です。

### Q3: 会社の機密書類を読み込ませても本当に安全ですか？

本記事の手順通り、OllamaとローカルのPython環境で完結していれば、データが外部サーバー（OpenAI等）に送信されることはありません。ただし、ライブラリの更新チェックなどでインターネット通信が発生する場合があるため、完全なエアギャップ環境（ネット遮断）で運用する場合は、依存関係をすべてオフラインでインストールする必要があります。

---

## あわせて読みたい

- [Qwen2.5-Coder 使い方 | ローカルでGPT-4o級の開発環境をPythonで構築する](/posts/2026-03-21-qwen2-5-coder-python-local-guide/)
- [Qwen3-Coder-Next 使い方 | 最強のコード生成AIで開発を自動化する手順](/posts/2026-03-07-qwen3-coder-next-local-python-tutorial/)
- [Local LLM 使い方 入門：OllamaとPythonで自分専用のAIアシスタントを作る方法](/posts/2026-04-10-local-llm-ollama-python-tutorial-llama3/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "32Bモデルを動かすのにRTX 4090は必須ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "必須ではありません。RTX 3060(12GB)でも、4-bit量子化なら14Bモデルまでは快適に、32Bモデルも低速（数トークン/秒）ながら動作します。実務的な速度を求めるなら、VRAM 16GB以上のRTX 4080や、24GBの3090/4090が推奨されます。"
      }
    },
    {
      "@type": "Question",
      "name": "PDFが100ページ以上ある場合でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、ベクトル化（Step 3）に時間がかかります。大規模なドキュメントを扱う場合は、一度構築したFAISSのインデックスを vectorstore.savelocal(\"faissindex\") で保存し、次回からロードするようにコードを修正すると効率的です。"
      }
    },
    {
      "@type": "Question",
      "name": "会社の機密書類を読み込ませても本当に安全ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "本記事の手順通り、OllamaとローカルのPython環境で完結していれば、データが外部サーバー（OpenAI等）に送信されることはありません。ただし、ライブラリの更新チェックなどでインターネット通信が発生する場合があるため、完全なエアギャップ環境（ネット遮断）で運用する場合は、依存関係をすべてオフラインでインストールする必要があります。 ---"
      }
    }
  ]
}
</script>
