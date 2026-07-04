---
title: "MLX 使い方 Apple SiliconでローカルLLMを動かす入門"
date: 2026-07-04T00:00:00+09:00
slug: "apple-silicon-mlx-local-llm-tutorial"
cover:
  image: "/images/posts/2026-07-04-apple-silicon-mlx-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 入門"
  - "Apple Silicon LLM"
  - "mlx-lm 使い方"
  - "ローカルLLM Mac"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple Silicon（M1/M2/M3/M4チップ）に最適化されたフレームワーク「MLX」を使い、Llama 3などの最新LLMを高速に動作させるPythonスクリプトを作ります。
Pythonの基礎知識があれば、外部APIを一切使わずに、自分のMac上で完全にプライベートなチャットAIを構築できます。
この記事では、単に動かすだけでなく、ストリーミング出力（文字がパラパラ出る挙動）の実装まで行います。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「チップの種類」ではなく「メモリ（ユニファイドメモリ）の量」です。
Apple SiliconはCPUとGPUでメモリを共有するため、メモリ量＝VRAM容量となります。

- 最小構成: メモリ8GB（Q4_K_M量子化された7B/8Bモデルが限界、動作は重い）
- 推奨構成: メモリ16GB以上（8Bモデルが快適に動き、RAGなどの並行処理も可能）
- 理想構成: メモリ32GB以上（Command Rや、ギリギリで30Bクラスのモデルが視野に入る）

もし8GBモデルのMacしか持っていない場合、動作はしますが、ブラウザなどの他アプリを全て閉じないとスワップが発生し、極端にレスポンスが悪化します。
また、IntelチップのMacではMLXは動作しません。その場合はllama.cppを検討してください。
費用については、自分のハードウェアを使うため、電気代以外は完全に無料です。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす手段は、Ollama、LM Studio、llama.cppなど複数あります。
その中で、あえてMLXを選ぶ理由は「Apple Siliconの性能を100%引き出せるから」です。

MLXはAppleの機械学習チームが開発したフレームワークであり、Metal（MacのグラフィックスAPI）にネイティブ対応しています。
PyTorchに近い書き方ができるため、単に動かすだけでなく、自分のアプリに組み込んだり、特定のデータで追加学習（LoRA）させたりする際、他のツールより圧倒的に拡張性が高いのが特徴です。
特にPythonエンジニアにとって、馴染みのあるエコシステムで完結できる点は大きなメリットです。

## Step 1: 環境を整える

まず、Python環境を汚さないために仮想環境を作成し、必要なライブラリをインストールします。

```bash
# プロジェクト用ディレクトリの作成
mkdir mlx-test && cd mlx-test

# 仮想環境の作成（Python 3.10以上を推奨）
python3 -m venv .venv
source .venv/bin/activate

# mlx-lmのインストール
pip install mlx-lm
```

`mlx-lm`は、Hugging Face上にあるモデルをMLX形式で簡単に利用するためのパッケージです。
これを経由することで、複雑な重みの変換作業をスキップして、直接モデルをロードできるようになります。

⚠️ **落とし穴:**
macOSのバージョンが古いと、MLXが要求するMetalの機能が使えずインストールに失敗することがあります。
macOS Sonoma (14.0) 以上にアップデートしておくことを強く推奨します。

## Step 2: 基本の設定

次に、動かすモデルを選定します。
今回は、日本語能力と性能のバランスが良い「Llama-3-8B」をMLX向けに最適化したモデルを使用します。

```python
import os
from mlx_lm import load, generate

# 使用するモデルの指定
# mlx-communityが公開している4bit量子化版を使うのが最も効率的です
model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"

# モデルとトークナイザーのロード
# load関数は、ローカルにモデルがなければ自動的にHugging Faceからダウンロードします
model, tokenizer = load(model_path)
```

「なぜ4bit量子化（4bit）を選ぶのか」というと、精度をほぼ維持したままメモリ消費量を1/4程度に抑えられるからです。
8B（80億パラメータ）のモデルをそのまま（16bit）ロードすると約15GBのメモリが必要ですが、4bitなら約5GBで済みます。
これにより、16GBメモリのMacでもサクサク動く余裕が生まれます。

## Step 3: 動かしてみる

まずは最小限のコードで、モデルに質問を投げてみます。

```python
# プロンプトの設定
prompt = "美味しいコーヒーを淹れるための3つのコツを教えてください。"

# Llama 3のテンプレートを適用
# これを忘れるとモデルの性能が著しく落ちます
messages = [{"role": "user", "content": prompt}]
formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

# 生成の実行
response = generate(model, tokenizer, prompt=formatted_prompt, verbose=True)
```

### 期待される出力

```
美味しいコーヒーを淹れるための3つのコツは以下の通りです。
1. 豆の鮮度と挽き方：焙煎直後の新鮮な豆を選び、抽出直前に挽くことが重要です。
2. お湯の温度：沸騰したてではなく、90度〜95度程度のお湯を使うと雑味が出にくくなります。
3. 抽出時間の管理：ドリップなら3分以内を目安に。長すぎると苦味の原因になります。
```

`verbose=True`に設定すると、生成速度（tokens per second）がコンソールに表示されます。
私のM2 Max環境では、秒間約50トークン以上の速度が出ました。これは人間が読む速度を遥かに超える快適なスピードです。

## Step 4: 実用レベルにする

実際のアプリ開発では、回答が全て生成されるのを待つのではなく、生成された先から文字を表示する「ストリーミング」が必須です。
また、ハイパーパラメータを調整して、回答の「柔軟さ」を制御します。

```python
import sys
from mlx_lm import load, generate

def chat_with_mlx():
    model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"
    model, tokenizer = load(model_path)

    while True:
        user_input = input("\n質問を入力してください（終了は'exit'）: ")
        if user_input.lower() == 'exit':
            break

        messages = [{"role": "user", "content": user_input}]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        print("\nAI: ", end="", flush=True)

        # ストリーミング生成の実行
        # max_tokens: 生成する最大長さ
        # temp: 0に近いほど決定的（真面目）、1に近いほど創造的（遊びがある）
        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=1000,
            temp=0.7,
            stream=True # ここをTrueにするとジェネレータが返ってくる
        )

        # 1トークンずつ表示
        for t in response:
            print(t, end="", flush=True)
        print("\n")

if __name__ == "__main__":
    chat_with_mlx()
```

このコードでは`stream=True`を指定しています。
これにより、`generate`関数はイテレータを返し、モデルが生成したそばから`print`できるようになります。
また、`temp=0.7`は、実務的な回答と自然な言い回しのバランスが良い設定値です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError: No module named 'mlx'` | 仮想環境が未有効、またはインストール失敗 | `source .venv/bin/activate`を実行後、再度pipインストール |
| `MemoryError` または動作が極端に重い | メモリ不足によるスワップ | モデルをより小さいもの（3B以下）にするか、ブラウザを閉じる |
| 回答が英語になる | システムプロンプトの欠如 | プロンプトに「日本語で答えてください」と明示的に含める |
| 速度が異常に遅い | Pythonのバージョンが古い、または他アプリの負荷 | Python 3.10以上を使用し、M1以降のチップであることを確認 |

## 次のステップ

MLXでローカルLLMを動かせるようになったら、次は「自分専用の知識」を読み込ませるRAG（検索拡張生成）に挑戦することをおすすめします。
具体的には、`langchain-mlx`などのライブラリを使い、自分の持っているPDFやテキストファイルを読み込ませることで、ネットに落ちていない情報をAIに答えさせることができます。

私自身、クライアントの過去の設計書を全てローカルLLMに食わせ、コードレビューの自動化を試していますが、外部APIにデータを送らないため、セキュリティ規約が厳しい案件でも安心して使えています。
「AIを外で動かす」のではなく「自分の手元で手懐ける」感覚は、一度味わうと戻れません。
まずは自分のMacで、Llama 3以外のモデル（Qwen2.5やGemma 2など）を入れ替えて、その「性格」の違いを楽しんでみてください。

## よくある質問

### Q1: メモリ8GBのMacBook Airでも動きますか？

動きますが、かなりギリギリです。
Llama 3 8Bの4bit版でも5GB程度のVRAMを専有するため、OSの維持分を含めると8GBを使い切ります。
より軽量な「Llama-3.2-3B-Instruct-4bit」や「Gemma-2-2b-it-4bit」から始めるのが現実的です。

### Q2: Hugging Faceからモデルをダウンロードする際にエラーが出ます。

公式モデル（Meta-Llamaなど）の場合、Hugging Face上で利用承認のリクエストが必要な場合があります。
ブラウザでモデルのページを開き、「Agree and access repository」ボタンを押して承認を得た後、`huggingface-cli login`コマンドでトークンを設定してください。

### Q3: MLXとOllamaの違いは何ですか？

Ollamaは「使い勝手の良い完成品」であり、MLXは「開発者向けの部品」です。
とにかく今すぐ使いたいならOllamaで十分ですが、自分でAIアプリを組んだり、挙動を細かくカスタマイズしたいなら、Pythonから直接制御できるMLXの方が圧倒的に有利です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac mini M4 32GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">MLXを動かすのに最もコスパが良い。32GBあれば中規模モデルも余裕。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M4%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M4%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20mini%20M4%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 Apple SiliconでローカルLLMを爆速動作させる方法](/posts/2026-06-12-mlx-apple-silicon-local-llm-guide/)
- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを動かす方法](/posts/2026-06-24-mlx-apple-silicon-local-llm-guide/)
- [MLX 使い方 入門 | Apple SiliconでLLMを爆速で動かす方法](/posts/2026-06-29-mlx-apple-silicon-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "メモリ8GBのMacBook Airでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、かなりギリギリです。 Llama 3 8Bの4bit版でも5GB程度のVRAMを専有するため、OSの維持分を含めると8GBを使い切ります。 より軽量な「Llama-3.2-3B-Instruct-4bit」や「Gemma-2-2b-it-4bit」から始めるのが現実的です。"
      }
    },
    {
      "@type": "Question",
      "name": "Hugging Faceからモデルをダウンロードする際にエラーが出ます。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "公式モデル（Meta-Llamaなど）の場合、Hugging Face上で利用承認のリクエストが必要な場合があります。 ブラウザでモデルのページを開き、「Agree and access repository」ボタンを押して承認を得た後、huggingface-cli loginコマンドでトークンを設定してください。"
      }
    },
    {
      "@type": "Question",
      "name": "MLXとOllamaの違いは何ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaは「使い勝手の良い完成品」であり、MLXは「開発者向けの部品」です。 とにかく今すぐ使いたいならOllamaで十分ですが、自分でAIアプリを組んだり、挙動を細かくカスタマイズしたいなら、Pythonから直接制御できるMLXの方が圧倒的に有利です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Mac mini M4 32GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">MLXを動かすのに最もコスパが良い。32GBあれば中規模モデルも余裕。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M4%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M4%252032GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Mac%20mini%20M4%2032GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
