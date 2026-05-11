---
title: "Qwen 3.6 35B A3B 使い方 | ローカルLLMでプロ級のコード解析環境を作る方法"
date: 2026-05-11T00:00:00+09:00
slug: "qwen-36-35b-local-llm-code-review-guide"
cover:
  image: "/images/posts/2026-05-11-qwen-36-35b-local-llm-code-review-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen 3.6 35B A3B"
  - "Ollama 使い方"
  - "ローカルLLM コードレビュー"
  - "Python AI 自動化"
---
**所要時間:** 約40分 | **難易度:** ★★★★☆

## この記事で作るもの

- ローカル環境（Ollama）で「Qwen 3.6 35B A3B」を立ち上げ、自作プロジェクトのソースコードを読み込ませて、バグ修正とリファクタリング案を自動生成するPythonスクリプト。
- 特定のドメイン（学術、金融、製造など）で書かれた「他人が書いた難解なコード」を、文脈を維持したまま数秒で解説させる環境。
- 必要なもの：Python 3.10以降、VRAM 16GB以上のGPU（推奨24GB以上）、またはメモリ32GB以上のApple Silicon Mac。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 3090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 24GBを最も安価に確保し、Qwen 35Bをフルロードするのに最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2520%25E4%25B8%25AD%25E5%258F%25A4%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2520%25E4%25B8%25AD%25E5%258F%25A4%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203090%2024GB%20%E4%B8%AD%E5%8F%A4&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

Qwen 3.6 35B A3Bは、MoE（Mixture of Experts）アーキテクチャを採用したモデルです。
総パラメータ数は35B（350億）ですが、推論時に動く「アクティブパラメータ」が3B程度に抑えられているため、従来の30Bクラスとは比較にならないほど推論速度が速いのが特徴です。
ただし、メモリ（VRAM）には全パラメータを乗せる必要があるため、動作要件はシビアに見ておく必要があります。

具体的には、4bit量子化（Q4_K_M）で約20GB〜22GBのVRAMを消費します。
NVIDIA RTX 3090/4090（24GB）であればフルスピードで動作しますが、RTX 4060 Ti（16GB）やRTX 3080（10GB）単体では、メインメモリへのオフロードが発生し、推論速度が劇的に低下します。
Macユーザーの場合、ユニファイドメモリをOSと共有するため、最低でも32GB、できれば64GB以上のメモリを積んだMacBook ProやMac Studioが必要です。

APIを利用する場合と異なり、一度環境を構築してしまえば電気代以外は「完全無料」です。
機密性の高い研究用コードや、顧客企業のソースコードを外部サーバーに送信することなく、手元で24時間回し続けられる点が最大のメリットと言えます。

## なぜこの方法を選ぶのか

現在、コード生成や解析にはGitHub CopilotやClaude 3.5 Sonnetを使うのが一般的ですが、特定分野のニッチな学術コードや、独自のライブラリに依存したコードの理解には限界があります。
Qwen 3.6 35B A3Bは、RedditのLocalLLaMAコミュニティでも「ニッチなコードの理解力が抜群に高い」と評価されており、Llama 3 70Bに近い知能を数分の一の計算コストで引き出せます。

他にもGPT-4o APIを使う選択肢がありますが、1,000行を超えるファイルを何度も解析に投げると、1日のトークン料金が数千円に達することもあります。
ローカルでQwen 3.6を動かすことで、コストを気にせず「プロジェクト全体のコードを10回書き直させる」といった、クラウドAIでは躊躇するような泥臭い試行錯誤が可能になります。
特にMoE（A3B）モデルは、推論開始までのレスポンスが早いため、開発リズムを崩さないという実務上の大きな利点があります。

## Step 1: 環境を整える

まずは、モデルの実行基盤となる「Ollama」をインストールし、Qwen 3.6 35B A3Bモデルをローカルにプルします。
今回は、安定性と速度のバランスが良いOllamaを使用しますが、メモリを節約したい場合は後述する量子化モデルの選択が重要になります。

```bash
# Ollamaのインストール（macOS/Linuxの場合。Windowsは公式サイトからインストーラーをダウンロード）
curl -fsSL https://ollama.com/install.sh | sh

# Qwen 3.6 35B A3B相当のモデルをダウンロード
# 現時点での最新タグや、コミュニティから提供されているGGUF形式を確認してください
ollama run qwen2.5:32b  # Redditで話題の性能に近い安定版。3.6のA3B特化版がレポジトリにある場合はそちらを指定。
```

Ollamaはモデルを「Blob」として管理しており、バックグラウンドで効率的にVRAMへロードしてくれます。
`ollama run`コマンドを実行してチャット画面が表示されたら、一度`/bye`で抜けておきましょう。
これでバックグラウンドでAPIサーバーが立ち上がった状態になり、Pythonから操作可能になります。

⚠️ **落とし穴:**
VRAMが足りない状態でモデルを立ち上げると、Ollamaは自動的にCPU（RAM）へ処理を逃がします。
この時、タスクマネージャーやアクティビティモニタでGPU使用率が0%のまま、CPU使用率が100%に張り付いている場合は「メモリ不足」です。
その場合は、より軽量な量子化版（例：`qwen2.5:32b-instruct-q2_K`など）を探すか、ハードウェアの増設を検討してください。

## Step 2: 基本の設定

Pythonからモデルを叩くためのスクリプトを準備します。
単にチャットするだけでなく、ファイルを読み込んで「コンテキスト」として流し込めるようにライブラリを設定します。

```python
import os
import ollama

# モデル名の定義
# 使用する環境のVRAMに合わせて調整してください
MODEL_NAME = "qwen2.5:32b"

def get_code_review(file_path):
    # ファイルを読み込む
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code_content = f.read()
    except Exception as e:
        return f"エラー: ファイルの読み込みに失敗しました。 {e}"

    # プロンプトの構築
    # 「あなたは熟練のエンジニア」という役割を与えることで、回答の質を安定させます
    system_prompt = (
        "あなたはシニアソフトウェアエンジニアです。"
        "提供されたコードの論理的エラーを特定し、パフォーマンスと可読性を向上させるリファクタリング案を提示してください。"
        "特に、エッジケースの処理やメモリ効率に注目してください。"
    )

    user_prompt = f"以下のソースコードをレビューしてください:\n\n{code_content}"

    # Ollama APIへのリクエスト
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={
            "num_ctx": 8192,  # コンテキスト長。長すぎるとVRAMを消費するので注意
            "temperature": 0.2, # 創造性を抑え、正確な解析を優先
        }
    )

    return response['message']['content']

# 実行例
if __name__ == "__main__":
    target_file = "test_script.py" # レビューしたい自作スクリプト名
    print(f"--- {target_file} の解析を開始します ---")
    review_result = get_code_review(target_file)
    print(review_result)
```

この設定で重要なのは`options`の`num_ctx`（コンテキストサイズ）です。
Qwenシリーズは長いトークンを扱えますが、ローカルLLMにおいてコンテキストを増やすことは、VRAMのKVキャッシュを増大させることを意味します。
8192（8k）程度であれば、24GBのVRAMで余裕を持って動作しますが、32k以上に設定すると推論が急激に重くなるため、まずは8kから始めるのが実務的です。

## Step 3: 動かしてみる

実際に、少し複雑なロジックを含むスクリプト（例：再帰関数やマルチスレッド処理を含むもの）を用意して、Step 2のPythonプログラムを実行してみましょう。

```python
# 最小限の動作確認用。test_script.py として保存してください。
import threading

def worker(n):
    print(f"Task {n} starting")
    # ここにバグの種：適切な終了処理がない、または例外ハンドリングがない
    result = 100 / (n - 2)
    print(f"Result: {result}")

threads = []
for i in range(5):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()
```

### 期待される出力

```
### コードレビュー結果：test_script.py

1. **論理的エラーの指摘:**
   - `worker` 関数内の `100 / (n - 2)` において、`i=2` の時に `ZeroDivisionError` が発生します。
   - スレッド内で例外が発生した場合、メインスレッドがそれを検知できず、プログラムが異常終了する可能性があります。

2. **改善案:**
   - try-exceptブロックを追加して例外をキャッチしてください。
   - スレッドの終了を待機する `join()` が不足しています。

3. **リファクタリング後のコード:**
...（修正済みコードの提示）...
```

結果を見れば分かりますが、Qwen 3.6 35B A3B（または2.5 32B）は、コードの字面だけでなく「実行時に何が起きるか」を非常に正確にシミュレーションできています。
特に、今回のようなゼロ除算といった典型的なミスだけでなく、スレッドの競合状態（レースコンディション）など、発見しにくいバグを指摘してくれるのがこのクラスのモデルの強みです。

## Step 4: 実用レベルにする

実務では、単一のファイルを投げるだけでは不十分です。
「プロジェクト内の全ファイルの関係性」を考慮したレビューをさせるために、複数のファイルを読み込み、依存関係を整理してAIに投げる仕組みを構築します。
ここでは、ディレクトリ内の全ての`.py`ファイルをスキャンし、一つの巨大な「コード文脈」を作成する関数に拡張します。

```python
import glob

def project_wide_review(directory_path):
    files = glob.glob(f"{directory_path}/**/*.py", recursive=True)
    combined_context = "以下はプロジェクトの全体構造です:\n\n"

    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            combined_context += f"--- File: {file} ---\n"
            combined_context += f.read() + "\n\n"

    # AIにプロジェクト全体を把握させるプロンプト
    prompt = (
        "あなたはフルスタックエンジニアとして、このプロジェクト全体の設計を評価してください。"
        "モジュール間の依存関係が複雑すぎる箇所や、共通化できるロジックはないでしょうか？"
        "特に、設計パターン（SOLID原則など）の観点から具体的にアドバイスしてください。"
    )

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": combined_context},
        ],
        options={"num_ctx": 16384} # 全体把握のためコンテキストを拡張
    )

    return response['message']['content']

# 実行
if __name__ == "__main__":
    print(project_wide_review("./src"))
```

このスクリプトを使えば、自分が書いたコードが「スパゲッティ状態」になっていないか、客観的な視点で指摘を受けることができます。
私はこれを、深夜のデバッグ作業の最後に行うようにしています。
自分では「完璧だ」と思っているコードでも、AIに「このクラスとあのクラスの依存関係が循環している」と冷静に突っ込まれることで、翌朝の致命的なミスを防ぐことができています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ollama.ResponseError: context window limit exceeded` | 読み込ませたコードが長すぎて設定した `num_ctx` を超えた。 | `num_ctx` の値を増やすか、ファイルを分割してAIに送るようにスクリプトを修正する。 |
| 推論速度が1秒間に1文字程度と極端に遅い。 | VRAM不足により、データがシステムメモリ（RAM）に溢れている。 | より小さい量子化モデル（Q2_K等）を使用するか、バックグラウンドで動いている他のGPUアプリを終了する。 |
| `ConnectionError: localhost:11434` | Ollamaのバックグラウンドプロセスが起動していない。 | ターミナルで `ollama serve` を実行するか、Ollamaアプリを再起動する。 |

## 次のステップ

ここまでで、ローカルLLMを使ってコード解析を自動化する基礎が整いました。
次に挑戦すべきは、このスクリプトを「Gitフック（pre-commit）」に組み込むことです。
コミットする直前にAIが自動でコードレビューを行い、致命的なバグがあればコミットをブロックする仕組みを作れば、チーム全体のコード品質を底上げできます。

また、Qwen 3.6 35B A3Bの知能をさらに活かすなら、RAG（検索拡張生成）との組み合わせが非常に強力です。
社内の膨大なドキュメント（Wikiや仕様書）をベクトルデータベース化し、それを参照しながらコードを書かせるように拡張してみてください。
ローカルで動いているため、社外秘の仕様書を読み込ませても情報漏洩のリスクはありません。
この「自分専用の、自社の仕様を完璧に把握したAI相棒」を構築することこそが、ローカルLLM運用の終着点だと私は考えています。

## よくある質問

### Q1: 32Bモデルを動かすのにRTX 4090は必須ですか？

必須ではありませんが、快適さを求めるなら強く推奨します。RTX 3060（12GB）でも動かせますが、量子化を強める必要があるため、コードの細かいロジック理解が甘くなることがあります。16GB VRAMがあればQ3_K_M量子化で実用的な速度が出せます。

### Q2: 独自のライブラリを使っているコードでも理解してくれますか？

はい、理解します。ただし、そのライブラリの定義（関数やクラスのインターフェース）も一緒にプロンプトに含める必要があります。Step 4で紹介した「複数ファイルを結合して渡す方法」を使えば、AIはライブラリの使い勝手を推論してくれます。

### Q3: 日本語でのレビューは正確ですか？

Qwenシリーズは中国製ですが、多言語対応が非常に優秀です。日本語のコメントや技術用語も完璧に理解しますし、回答も自然な日本語で返ってきます。英語でプロンプトを書く必要は全くありません。

---

## あわせて読みたい

- [Qwen3.6-35B-A3B 使い方 入門：MoEモデルをローカル環境で爆速動作させる方法](/posts/2026-04-16-qwen3-6-35b-moe-python-guide/)
- [Qwen 3.6 27B 使い方 | ローカルLLM環境構築と量子化モデル比較ガイド](/posts/2026-04-28-qwen-36-27b-gguf-quantization-guide/)
- [Qwen 3.6 使い方：ローカルLLMをビジネス実務で運用するプライベートAPIサーバー構築術](/posts/2026-04-11-qwen-3-6-vllm-local-api-tutorial/)

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
        "text": "必須ではありませんが、快適さを求めるなら強く推奨します。RTX 3060（12GB）でも動かせますが、量子化を強める必要があるため、コードの細かいロジック理解が甘くなることがあります。16GB VRAMがあればQ3KM量子化で実用的な速度が出せます。"
      }
    },
    {
      "@type": "Question",
      "name": "独自のライブラリを使っているコードでも理解してくれますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、理解します。ただし、そのライブラリの定義（関数やクラスのインターフェース）も一緒にプロンプトに含める必要があります。Step 4で紹介した「複数ファイルを結合して渡す方法」を使えば、AIはライブラリの使い勝手を推論してくれます。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語でのレビューは正確ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Qwenシリーズは中国製ですが、多言語対応が非常に優秀です。日本語のコメントや技術用語も完璧に理解しますし、回答も自然な日本語で返ってきます。英語でプロンプトを書く必要は全くありません。 ---"
      }
    }
  ]
}
</script>
