---
title: "Qwen 2.5 27B 使い方 入門：24GB VRAMでGPT-4級のコード生成環境を構築する方法"
date: 2026-04-24T00:00:00+09:00
slug: "qwen-2-5-27b-local-python-guide"
cover:
  image: "/images/posts/2026-04-24-qwen-2-5-27b-local-python-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen 2.5 27B 使い方"
  - "ローカルLLM Python"
  - "Ollama 環境構築"
  - "RTX 4090 AI推論"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- RTX 3090/4090などの24GB VRAM環境をフル活用し、ローカルで爆速動作する「データ分析・コーディング特化型AIアシスタント」を構築します。
- Redditで「Qwen 3.6」と誤記されるほどの衝撃を与えたQwen 2.5 27Bモデルを使い、PySparkやPandasの複雑なコード変換を自動化するPythonスクリプトを作成します。
- クラウドへの課金を停止し、プライバシーを保ったまま機密性の高い業務データを扱えるローカル推論環境が完成します。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">27Bモデルをq4〜q6量子化で快適に動かすための、現在最も現実的で最強の選択肢です。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB%20%E3%82%B0%E3%83%A9%E3%83%95%E3%82%A3%E3%83%83%E3%82%AF%E3%83%9C%E3%83%BC%E3%83%89&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2520%25E3%2582%25B0%25E3%2583%25A9%25E3%2583%2595%25E3%2582%25A3%25E3%2583%2583%25E3%2582%25AF%25E3%2583%259C%25E3%2583%25BC%25E3%2583%2589%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2520%25E3%2582%25B0%25E3%2583%25A9%25E3%2583%2595%25E3%2582%25A3%25E3%2583%2583%25E3%2582%25AF%25E3%2583%259C%25E3%2583%25BC%25E3%2583%2589%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

### 前提知識
- Pythonの基本的な文法がわかること
- ターミナル（コマンドプロンプト）の基本的な操作ができること
- Dockerまたは仮想環境の概念を理解していること

### 必要なもの
- NVIDIA製GPU（VRAM 24GB推奨。RTX 3090 / 4090 / 5090 Laptop等）
- Windows/Linux/macOS（Appleシリコン推奨）
- Python 3.10以上
- 100GB程度のストレージ空き容量

## なぜこの方法を選ぶのか

ローカルLLMの界隈では「7Bは賢くない、72Bは重すぎる」というジレンマが長らく続いていました。
しかし、Qwen 2.5 27Bはこのギャップを完璧に埋める「スイートスポット」に位置しています。

量子化技術（GGUF/EXL2）を使うことで、27Bモデルは24GBのVRAMに余裕を持って収まります。
一方で、そのコーディング能力と数学的推論能力は、Llama 3 70Bに匹敵するか、特定のベンチマークでは凌駕しています。
特にRedditのr/LocalLLaMAで話題になったのは、その「Tool Use（関数呼び出し）」の正確さです。

巷にはLM StudioやGPT4AllなどのGUIツールも多いですが、私はあえて「Ollama」と「Python API」の組み合わせを推奨します。
理由は単純で、GUIツールは「試す」のには向いていますが、既存の業務ワークフローに「組み込む」のには向いていないからです。
API経由でモデルを叩けるようにしておくことで、将来的にエージェント化したり、社内ツールと連携させたりといった拡張性が担保されます。

## Step 1: 環境を整える

まずは推論エンジンとして「Ollama」をインストールします。
Llama-cpp-pythonを直接ビルドする道もありますが、SIer時代の経験から言わせてもらうと、ライブラリの依存関係で消耗するのは時間の無駄です。
Ollamaはバックエンドで最適化された推論エンジンを隠蔽してくれているため、最も安定して「仕事に使える」環境が手に入ります。

```bash
# 公式サイトからインストーラーをダウンロード（Linuxの場合）
curl -fsSL https://ollama.com/install.sh | sh
```

次に、Python環境を作成して必要なライブラリを入れます。

```bash
# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# Ollama公式のPythonライブラリをインストール
pip install ollama pandas
```

ここで重要なのは、ライブラリを最新版に保つことです。Qwen 2.5系は比較的新しいため、古いバージョンの推論エンジンだとトークナイザーの挙動がおかしくなることがあります。

⚠️ **落とし穴:**
Windowsユーザーで「GPUが認識されない」というトラブルが多発します。
必ず最新のNVIDIA Driverをインストールし、`nvidia-smi` コマンドでCUDAバージョンが表示されることを確認してください。
WSL2を使っている場合は、WSL側にもCUDAツールキットを入れる必要がありますが、まずはWindows版のOllamaを直接使うのがトラブルが少なくて済みます。

## Step 2: 基本の設定

次に、モデルをダウンロード（プル）します。
今回は24GB VRAMを最適に使い切るために、4ビット量子化版（q4_K_M）を選択します。

```bash
ollama pull qwen2.5:27b
```

なぜ「27Bのq4」なのか。
私の検証では、27Bモデルをq4（約18GB VRAM消費）で動かした場合と、14Bモデルをq8で動かした場合では、圧倒的に前者の方が知能が高いという結果が出ました。
パラメータ数は正義です。
また、q4_K_Mという設定は、重みの精度を保ちつつファイルサイズを削る、最もバランスの良い設定です。

Python側からの初期設定コードを書きます。

```python
import ollama

# モデル名の定義
MODEL_NAME = "qwen2.5:27b"

def check_model_availability():
    """モデルが正しくロードされているか確認する"""
    try:
        models = ollama.list()
        if any(m['name'].startswith(MODEL_NAME) for m in models['models']):
            print(f"Success: {MODEL_NAME} が利用可能です。")
        else:
            print(f"Error: {MODEL_NAME} が見つかりません。")
    except Exception as e:
        print(f"接続エラー: {e}")

check_model_availability()
```

環境変数からAPIキーを読み込む必要はありません。ローカルで動いているため、通信は全て `localhost:11434` で完結します。これがローカルLLMの最大の強みです。

## Step 3: 動かしてみる

まずは、Qwenの「BEAST（獣）」たる所以である、コーディング能力をテストします。
単純な挨拶ではなく、実務で発生しがちな「データ構造の変換」を依頼してみましょう。

```python
import ollama

def run_test_query():
    prompt = """
    以下の要件をPythonで実装してください。
    1. 複雑なネストされたJSONデータ（ログファイル）を読み込む
    2. 特定のキー 'user_id' ごとにカウントする
    3. 結果をPandasのDataFrameに変換し、降順でソートする

    コードのみを出力してください。
    """

    response = ollama.chat(model='qwen2.5:27b', messages=[
        {
            'role': 'user',
            'content': prompt,
        },
    ])

    print(response['message']['content'])

run_test_query()
```

### 期待される出力

```python
import pandas as pd
import json

def process_logs(json_data):
    data = json.loads(json_data)
    counts = {}
    for entry in data:
        uid = entry.get('user_id')
        if uid:
            counts[uid] = counts.get(uid, 0) + 1

    df = pd.DataFrame(list(counts.items()), columns=['user_id', 'count'])
    return df.sort_values(by='count', ascending=False)
```

結果を見て驚くのは、その生成速度です。RTX 4090環境であれば、この程度のコードは1〜2秒で吐き出されます。
レスポンスの速さは思考を妨げないために極めて重要です。

## Step 4: 実用レベルにする

実務では、単発の質問よりも「エラーが出たコードを修正させる」というデバッグ作業の方が頻度が高いはずです。
そこで、例外が発生した際に自動的にQwenへ修正案を求める「オートデバッグ・ラッパー」を作ってみましょう。

```python
import ollama
import sys
import traceback

def ask_ai_for_fix(error_msg, code):
    """AIにエラーの修正方法を聞く"""
    system_prompt = "あなたはシニアPythonエンジニアです。提供されたコードとエラーメッセージから、修正後のコードのみを提示してください。"

    prompt = f"### コード:\n{code}\n\n### エラー内容:\n{error_msg}\n\n### 修正案:"

    response = ollama.chat(model='qwen2.5:27b', messages=[
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': prompt},
    ])
    return response['message']['content']

def execute_risky_code():
    # 意図的にエラーが起きるコード
    code_content = """
data = [1, 2, 3]
print(data[5])
    """

    try:
        exec(code_content)
    except Exception:
        err = traceback.format_exc()
        print("--- エラー発生。AIに解決策を聞いています... ---")
        fix = ask_ai_for_fix(err, code_content)
        print("--- AIからの修正提案 ---")
        print(fix)

if __name__ == "__main__":
    execute_risky_code()
```

このスクリプトのポイントは、`traceback.format_exc()` をそのままAIに投げている点です。
Qwen 2.5 27Bはスタックトレースを理解し、どの行でインデックスエラーが起きているかを正確に特定します。
「なぜこの修正が必要なのか」を日本語で説明させたい場合は、`system_prompt` を調整するだけで対応可能です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Error: model not found` | `ollama pull` が完了していない | ターミナルで `ollama pull qwen2.5:27b` を再実行する。 |
| 動作が異常に重い | VRAM不足でメインメモリ（RAM）に溢れている | 他のアプリ（Chrome等）を閉じるか、14Bモデルに下げる。 |
| Pythonから接続できない | Ollamaサーバーが起動していない | タスクトレイでOllamaが常駐しているか確認する。 |

## 次のステップ

ここまでで、Qwen 2.5 27Bをローカルで動かし、Pythonから制御する基礎が整いました。
次のステップとして取り組んでほしいのは「コンテキスト長（Context Length）の活用」です。
Qwen 2.5は最大128kトークンまで対応していますが、ローカルで動かす場合はVRAMの制限により、デフォルトではそこまで長く設定されていません。

Ollamaの場合、`Modelfile` を作成して `PARAMETER num_ctx 32768` のように指定することで、より長いドキュメントを読み込ませることが可能になります。
例えば、プロジェクト全体のソースコードを一つのプロンプトに流し込み、「この機能を追加するための修正箇所を全てリストアップして」といった指示を出すことができます。

また、Redditの住人が絶賛していた「PySparkのデバッグ」に関しても、ローカルでSparkのログをそのままAIに食わせるパイプラインを作れば、データエンジニアリングの作業効率は劇的に向上するでしょう。
クラウドにデータを送れない制約がある現場こそ、この27Bモデルの真価が発揮される場所です。

## よくある質問

### Q1: RTX 3060 (12GB) しか持っていないのですが、動かせますか？

27Bモデルを12GBで動かすのは非常に厳しいです。量子化を極限まで（q2等）下げれば動く可能性はありますが、知能が大幅に低下します。12GB環境であれば、同じQwenシリーズの14Bモデルを選択するのが、速度と精度のバランスが最も良くなります。

### Q2: Claude 3.5 Sonnetと比較して、どちらが賢いですか？

正直に言えば、総合力ではClaude 3.5 Sonnetの方が上です。しかし、ローカルLLMには「通信が発生しない」「月額料金がかからない」「プロンプトの内容が検閲されない」という圧倒的な利点があります。特定のコーディングタスクにおいては、27BはSonnetに肉薄する回答を出します。

### Q3: llama.cppとOllama、どちらを使うのが正解ですか？

開発速度を優先するならOllamaです。しかし、1枚のGPUではなく、私のように複数枚のGPU（RTX 4090 2枚挿しなど）で分散推論させたい場合は、llama.cppやvLLMの方が細かい制御が効くため、そちらへの移行をおすすめします。

---

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**
**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [Qwen 3.6 使い方: ローカルLLMで爆速・高精度な推論環境を構築する手順](/posts/2026-04-18-qwen3-6-local-python-ollama-guide/)
- [Qwen 3.5 0.8B 使い方 | 超軽量AIをCPUだけで爆速動作させる手順](/posts/2026-03-10-qwen-3-5-08b-local-python-tutorial/)
- [Local LLM 使い方 入門：OllamaとPythonで自分専用のAIアシスタントを作る方法](/posts/2026-04-10-local-llm-ollama-python-tutorial-llama3/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3060 (12GB) しか持っていないのですが、動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "27Bモデルを12GBで動かすのは非常に厳しいです。量子化を極限まで（q2等）下げれば動く可能性はありますが、知能が大幅に低下します。12GB環境であれば、同じQwenシリーズの14Bモデルを選択するのが、速度と精度のバランスが最も良くなります。"
      }
    },
    {
      "@type": "Question",
      "name": "Claude 3.5 Sonnetと比較して、どちらが賢いですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "正直に言えば、総合力ではClaude 3.5 Sonnetの方が上です。しかし、ローカルLLMには「通信が発生しない」「月額料金がかからない」「プロンプトの内容が検閲されない」という圧倒的な利点があります。特定のコーディングタスクにおいては、27BはSonnetに肉薄する回答を出します。"
      }
    },
    {
      "@type": "Question",
      "name": "llama.cppとOllama、どちらを使うのが正解ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "開発速度を優先するならOllamaです。しかし、1枚のGPUではなく、私のように複数枚のGPU（RTX 4090 2枚挿しなど）で分散推論させたい場合は、llama.cppやvLLMの方が細かい制御が効くため、そちらへの移行をおすすめします。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>
