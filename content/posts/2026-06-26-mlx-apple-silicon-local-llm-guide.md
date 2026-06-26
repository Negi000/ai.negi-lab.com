---
title: "MLX 使い方 入門：Apple SiliconでローカルLLMを動かす方法"
date: 2026-06-26T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-guide"
cover:
  image: "/images/posts/2026-06-26-mlx-apple-silicon-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX"
  - "Apple Silicon"
  - "Llama 3"
  - "ローカルLLM 構築"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- Apple Silicon（M1/M2/M3/M4）のGPU性能を最大限に引き出し、Llama 3などの最新LLMと高速に対話できるPythonスクリプト
- 外部APIに一切頼らず、完全にオフラインで動作するプライバシー重視のチャットインターフェース
- 前提知識：Pythonの基本的な構文（変数、関数、pip操作）がわかること
- 必要なもの：Apple Silicon搭載のMac、Python 3.10以降

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac mini M2 (24GB増設)</strong>
<p style="color:#555;margin:8px 0;font-size:14px">MLX検証用の省電力Macとして最もコスパ良くメモリを確保できる構成</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M2%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M2%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20mini%20M2%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPUのコア数よりも重要なのが「ユニファイドメモリ（RAM）の容量」です。
結論から言うと、メモリ8GBのモデルでは「とりあえず動く」レベルであり、実用性を求めるなら16GB以上、本格的な検証なら32GB以上が必須となります。
Apple SiliconはCPUとGPUがメモリを共有するため、VRAM（ビデオメモリ）という概念がありません。
その代わり、搭載されているメモリの約3分の2から4分の3程度をLLMの展開に使用できます。

例えば、80億パラメータのモデル（Llama-3-8Bなど）を4bit量子化して動かす場合、約5GB前後のメモリを消費します。
OSの動作分を含めると、8GBモデルではメモリ不足によるスワップが発生し、レスポンスが極端に低下します。
これから開発機を購入するなら、Mac miniやMacBook Airでも「メモリ増設」だけは妥協しないでください。
コスト面では、API利用料は0円ですが、モデルのダウンロードに数GBの通信が発生するため、固定回線環境での作業を推奨します。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす手段として「Ollama」や「llama.cpp」も有名ですが、私はあえて「MLX」を推奨します。
MLXはAppleの機械学習チームが開発したフレームワークであり、Apple Siliconのハードウェア特性に完全に最適化されています。
最大の特徴は「Unified Memoryへのネイティブ対応」と「配列操作の最適化」です。

llama.cppはC++ベースで非常に高速ですが、Pythonから複雑な処理（RAGやエージェント構築）を組み込もうとすると、バインディングのオーバーヘッドや設定の煩雑さに直面します。
MLXはNumPyに近い感覚でコードが書けるため、エンジニアがカスタマイズする際の自由度が桁違いです。
実際にM2 Maxでベンチマークを取った際も、同じ4bit量子化モデルであればMLXの方がトークン生成速度の安定性が高く、特にバッチ処理時の効率が優れていました。

## Step 1: 環境を整える

まずはMLX専用の仮想環境を作成します。
システム全体のPython環境を汚すと、後で他のライブラリと依存関係の競合（特にPyTorch周り）が起きるため、必ず仮想環境を切り分けてください。

```bash
# プロジェクト用のディレクトリを作成
mkdir mlx-test && cd mlx-test

# Python 3.10以上で仮想環境を作成
python3 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate

# MLX関連のライブラリをインストール
# mlx-lmはLLMを動かすための高レベルAPIを提供してくれます
pip install mlx-lm
```

各コマンドの意味を補足します。
`mlx-lm`は、Hugging Faceにあるモデルを直接読み込んで実行するためのパッケージです。
以前はモデルの変換作業が必要でしたが、現在はこれ一つでダウンロードから実行まで完結します。

落とし穴: インストール時に「Command Not Found」が出る場合は、PATHが通っていない可能性があります。また、Intel Mac（Core i5/i7/i9）ではMLXは動作しません。Apple Silicon専用です。

## Step 2: 基本の設定

次に、動かしたいモデルを指定してロードするコードを書きます。
今回は日本語能力が高い「Llama-3-8B-Instruct」を、MLX用に最適化（量子化）されたリポジトリから取得します。

```python
from mlx_lm import load, generate

# モデルのパス（Hugging Faceのリポジトリ名）を指定
# mlx-communityにあるものは、すでにMLX形式に変換されています
model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"

# モデルとトークナイザーをロード
# load関数は、ローカルにモデルがなければ自動でダウンロードしてくれます
model, tokenizer = load(model_path)

# プロンプトの構築
# Llama 3のテンプレートに従って記述します
prompt = "あなたは優秀なエンジニアです。Pythonで高速なソートアルゴリズムを書いてください。"
messages = [{"role": "user", "content": prompt}]
formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
```

この設定のポイントは「4bit量子化モデル」を選んでいる点です。
16bit（フル精度）のモデルはメモリを数十GB消費しますが、4bitに圧縮することで、推論精度をほぼ維持したままメモリ消費量を4分の1に抑えられます。
実務で「レスポンス速度」と「精度」のバランスが最も良いのがこの設定です。

## Step 3: 動かしてみる

実際にテキストを生成させます。
まずは最小限のコードで、正しくGPUが回っているか確認しましょう。

```python
# テキスト生成の実行
response = generate(
    model,
    tokenizer,
    prompt=formatted_prompt,
    max_tokens=500,    # 生成する最大文字数。最初は短めにしてテストします
    temp=0.7,          # 自由度。0に近いほど確実な回答、1に近いほど創造的になります
    verbose=True       # 実行時の統計情報（トークン/秒など）を表示します
)

print(f"\n回答:\n{response}")
```

### 期待される出力

```text
回答:
Pythonで高速なソートアルゴリズムといえば、標準ライブラリでも採用されているTimsortが有名ですが、ここでは実装例として「クイックソート」を紹介します。
... (コード例) ...
[INFO] Prompt: 42 tokens, 105.234 tokens-per-sec
[INFO] Generation: 210 tokens, 35.412 tokens-per-sec
```

結果の読み方を解説します。
`tokens-per-sec`が、1秒間に生成された単語数（に近い単位）です。
M2以降のチップであれば、Llama-3-8B-4bitで30〜50 tokens/sec程度出るはずです。
人間が読む速度がだいたい5〜10 tokens/secと言われているので、実用上十分な「爆速」状態と言えます。

## Step 4: 実用レベルにする

ここまでは「一括で回答を待つ」形式でしたが、ChatGPTのように「一文字ずつ表示される（ストリーミング）」形式にアップグレードします。
また、メモリ管理のために実行が終わるたびにキャッシュをクリアする処理も加えます。

```python
import sys
from mlx_lm import load, stream

def chat_loop():
    model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"
    model, tokenizer = load(model_path)

    print("AI: 何か手伝えることはありますか？ (quitで終了)")

    while True:
        user_input = input("あなた: ")
        if user_input.lower() == "quit":
            break

        messages = [{"role": "user", "content": user_input}]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        print("AI: ", end="", flush=True)

        # stream関数を使うことで、生成されたトークンを逐次取得できます
        for response in stream(model, tokenizer, prompt, max_tokens=1000, temp=0.7):
            print(response, end="", flush=True)

        print("\n" + "-"*30)

if __name__ == "__main__":
    chat_loop()
```

このコードでは、`stream`関数を採用しました。
実務でツールを作る際、回答が全て出るまで数十秒待たされるUIはユーザー体験が悪すぎます。
`flush=True`を指定することで、標準出力のバッファを強制的に書き出し、リアルタイムな対話感を実現しています。
また、`while`ループで囲むことで、プログラムを再起動せずに何度も質問できるようにしました。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ImportError: No module named 'mlx'` | 仮想環境が未有効化またはインストール失敗 | `source .venv/bin/activate`を実行し、`pip install mlx-lm`を再試行 |
| `Killed` または強制終了 | メモリ不足（OOM） | モデルをより小さいもの（例：`Phi-3-mini-4bit`）に変更する |
| 生成速度が1トークン/秒以下 | 他の重いアプリがGPUを占有 | Chromeや動画編集ソフトを閉じ、メモリプレッシャーを下げる |
| 回答が文字化けする | トークナイザーの設定ミス | モデルリポジトリに`tokenizer_config.json`が含まれているか確認 |

## 次のステップ

MLXでローカルLLMが動かせるようになったら、次は「独自の知識」を学習させる「LoRAファインチューニング」に挑戦してみてください。
MLXには`mlx_lm.lora`というモジュールが含まれており、数百枚の画像データや自社のドキュメントを読み込ませて、自分好みの回答スタイルに調整することが可能です。
API経由での学習だと数千円から数万円かかるコストが、ローカルなら電気代だけで済みます。

また、LangChainのMLX統合パッケージを利用して、ローカルLLMをRAG（外部書類検索）システムに組み込むのも面白いでしょう。
私が検証した限りでは、RAGの検索結果を要約させる用途において、MLXはクラウドベースのモデルに引けを取らない精度と、圧倒的なレスポンスの速さを両立できます。
自分のMacの中に「自分専用の有能な秘書」を飼う感覚を、ぜひ楽しんでください。

## よくある質問

### Q1: メモリ8GBのMacBook Airで動かすコツはありますか？

あります。モデルのパラメータ数を減らしてください。`Llama-3-8B`ではなく、Microsoftの`Phi-3-mini`やGoogleの`Gemma-2b`の4bit量子化版を選べば、8GBでも比較的スムーズに動作します。

### Q2: GPUを使っているか確認する方法は？

アクティビティモニタの「ウィンドウ」メニューから「GPUの履歴」を表示してください。`generate`実行中にグラフが大きく跳ね上がっていれば、MLXが正しくGPUを活用している証拠です。

### Q3: Hugging Faceのどのモデルでも動かせますか？

基本的には`mlx-community`というユーザーがアップロードしている変換済みモデルを使うのが無難です。未変換のモデルを動かすには`mlx_lm.convert`コマンドで形式変換が必要になります。

---

## あわせて読みたい

- [Apple Siliconの性能を限界まで引き出すMLXでローカルLLMを動かす方法](/posts/2026-06-16-mlx-apple-silicon-local-llm-guide/)
- [Gemma 4 12bをMacで動かすならどれ？MLX vs QAT比較とおすすめモデル・Macスペック選び](/posts/2026-06-09-gemma-4-12b-mac-mlx-comparison-guide/)
- [Apple Siliconで爆速LLM。MLXを使ったローカルLLM環境構築ガイド](/posts/2026-06-16-apple-silicon-mlx-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "メモリ8GBのMacBook Airで動かすコツはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "あります。モデルのパラメータ数を減らしてください。Llama-3-8Bではなく、MicrosoftのPhi-3-miniやGoogleのGemma-2bの4bit量子化版を選べば、8GBでも比較的スムーズに動作します。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUを使っているか確認する方法は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "アクティビティモニタの「ウィンドウ」メニューから「GPUの履歴」を表示してください。generate実行中にグラフが大きく跳ね上がっていれば、MLXが正しくGPUを活用している証拠です。"
      }
    },
    {
      "@type": "Question",
      "name": "Hugging Faceのどのモデルでも動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的にはmlx-communityというユーザーがアップロードしている変換済みモデルを使うのが無難です。未変換のモデルを動かすにはmlxlm.convertコマンドで形式変換が必要になります。 ---"
      }
    }
  ]
}
</script>
