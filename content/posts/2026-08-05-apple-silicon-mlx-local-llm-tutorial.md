---
title: "MLXを使ってApple Silicon MacでローカルLLMを爆速で動かす方法"
date: 2026-08-05T00:00:00+09:00
slug: "apple-silicon-mlx-local-llm-tutorial"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Apple MLX 使い方"
  - "ローカルLLM Mac"
  - "Llama 3 MLX"
  - "Python 機械学習 Mac"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple純正の機械学習フレームワーク「MLX」を使用し、Llama 3やQwenなどの最新LLMをMacのGPUで高速推論させるPythonスクリプトを作成します。
一般的なライブラリよりもメモリ効率が良く、ストリーミング出力（文字がパラパラ出てくる表示）に対応した実践的なチャットプログラムを構築します。

前提知識：Pythonの基本的な文法（pipでのインストールや関数の実行）がわかること
必要なもの：Apple Silicon（M1/M2/M3/M4）搭載のMac、インターネット環境

## 先に確認するスペック・料金

Apple Silicon MacでローカルLLMを動かす際、最も重要なのは「メモリ（ユニファイドメモリ）の容量」です。
LLMの重みデータはすべてメモリ上に展開されるため、メモリが不足するとスワップが発生し、推論速度が極端に低下します。

最低ラインはメモリ16GBですが、これでも7B（70億パラメータ）クラスのモデルを4ビット量子化して動かすのが精一杯です。
仕事でストレスなく複数のモデルを使い分けたいなら、32GB以上のメモリを積んだモデルを強く推奨します。
私は検証用にM2 Ultra（128GBメモリ）とM3 Max（64GBメモリ）を使っていますが、メモリが多ければ多いほど、巨大なモデルを高速に回せるため、投資対効果は非常に高いです。

もしこれからMacを買うなら、MacBook Airのメモリ増設モデルか、中古のMac Studioがコストパフォーマンスに優れています。
GPUコア数も重要ですが、まずは「動くかどうか」の境目であるメモリ容量を優先して選んでください。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす手段には「Ollama」や「LM Studio」といった便利なアプリもあります。
しかし、Pythonエンジニアが実務でAIを組み込むなら、Apple純正の「MLX」一択だと私は考えています。

最大の理由は、MLXがApple Siliconのアーキテクチャに完全に最適化されている点です。
PyTorchやllama.cppと比較しても、メモリの共有効率（Unified Memoryの活用）が非常に高く、モデルのロード時間が短い傾向にあります。
また、Pythonから直接叩けるため、自分の作ったアプリやスクリプトに「オフラインで動くLLM」を組み込むのが容易なのも大きなメリットです。

## Step 1: 環境を整える

まずはMLXを動かすためのPython環境を構築します。
Pythonのバージョンは3.10以上が必要ですが、互換性と速度のバランスが良い3.11か3.12を推奨します。

```bash
# プロジェクト用のディレクトリを作成して移動
mkdir mlx-test && cd mlx-test

# 仮想環境を作成（標準のvenvでOK）
python3 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate

# MLX関連のライブラリをインストール
# mlx-lmは、Hugging Face上のモデルをMLXで簡単に扱うためのパッケージです
pip install mlx-lm huggingface_hub
```

MLX本体だけでなく `mlx-lm` を使うのがポイントです。
これにより、複雑なモデル変換作業なしで、Hugging Faceにある「MLX形式」に変換済みのモデルを直接ロードできるようになります。

⚠️ **落とし穴:**
Xcode Command Line Toolsがインストールされていないと、パッケージのビルドでエラーが出ることがあります。
もしエラーが出た場合は `xcode-select --install` を実行してから再度試してください。
また、Intel MacではMLXは動作しません。M1以降のチップであることを必ず確認してください。

## Step 2: 基本の設定

次に、モデルを読み込んで推論を行うための基本設定を書きます。
今回は、日本語能力が非常に高い「Llama-3-8B」のMLX版を使用します。

```python
from mlx_lm import load, generate

# 使用するモデルの指定
# Hugging Face上のレポジトリ名を指定します
# 4bit量子化版を選ぶことで、メモリ消費を抑えつつ高速に動作させます
model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"

# モデルとトークナイザーのロード
# load関数は初回実行時にモデルを自動的にダウンロードしてキャッシュします
model, tokenizer = load(model_path)

print("モデルの読み込みが完了しました。")
```

ここで `4bit` 版を選択している理由は、精度を維持しつつメモリ使用量を約1/4に抑えるためです。
8Bモデル（約80億パラメータ）の場合、量子化なしだと16GB以上のメモリを専有しますが、4bit版なら約5GB程度で収まります。
「仕事で使えるか」という基準で見ると、この省メモリ性能こそがローカルLLM運用の現実的な解になります。

## Step 3: 動かしてみる

まずは最小限のコードで、モデルが正しく応答するかテストしてみましょう。

```python
# プロンプトの作成
# Llama-3のフォーマットに従って記述します
prompt = "MacでAIを動かすメリットを3つ教えてください。"
messages = [{"role": "user", "content": prompt}]
input_ids = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
formatted_prompt = tokenizer.decode(input_ids)

# 推論の実行
response = generate(
    model,
    tokenizer,
    prompt=formatted_prompt,
    max_tokens=500,
    verbose=False # 途中経過をコンソールに出さない設定
)

print(f"回答:\n{response}")
```

### 期待される出力

```
回答:
MacでAIを動かすメリットは以下の3点です。
1. プライバシーの確保：データが外部サーバーに送信されず、手元で完結します。
2. オフライン動作：インターネット接続なしで推論が可能です。
3. 低遅延：Apple Siliconのユニファイドメモリにより、高速な推論が実現できます。
```

結果が出力されるまで、M2チップなら数秒、M3以上なら1秒かからないはずです。
レスポンスの速さを体感できたら、環境構築は成功です。

## Step 4: 実用レベルにする

実務で使う場合、回答がすべて生成されるまで待つのは時間がもったいないです。
ChatGPTのように、生成された文字から順に表示される「ストリーミング出力」を実装しましょう。
また、パラメータを調整して、回答の「遊び（創造性）」を制御できるようにします。

```python
import sys
from mlx_lm import load, stream

def chat_with_mlx(model_name):
    model, tokenizer = load(model_name)

    print(f"--- {model_name} Chat System (exitで終了) ---")

    while True:
        user_input = input("\nあなた: ")
        if user_input.lower() == "exit":
            break

        messages = [{"role": "user", "content": user_input}]
        prompt = tokenizer.apply_chat_template(messages, add_generation_prompt=True)

        print("AI: ", end="", flush=True)

        # stream関数を使うことで、トークンが生成されるたびに出力可能
        # temp (temperature) は0.7に設定。
        # 0に近いほど決定的（真面目）、1に近いほど多様（創造的）な回答になります。
        occurrence = 0
        for response in stream(model, tokenizer, prompt=prompt, temp=0.7, max_tokens=1000):
            print(response, end="", flush=True)
            occurrence += 1

        print(f"\n\n[生成速度: {occurrence} トークン]")

if __name__ == "__main__":
    # 日本語に強いQwen2.5の7Bモデル（MLX版）を試してみるのもおすすめです
    target_model = "mlx-community/Qwen2.5-7B-Instruct-4bit"
    chat_with_mlx(target_model)
```

このスクリプトでは `stream` 関数を利用しています。
仕事でAIエージェントを作る際、ユーザーを待たせないUIを作るにはこのストリーミング処理が必須となります。
また、モデルを `Qwen2.5` に変更しましたが、MLXならレポジトリ名を変えるだけで別のモデルに一瞬で切り替えられるのが強みです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Killed: 9` | メモリ不足によるOSの強制終了 | より小さいモデル（3Bなど）を使うか、4bit量子化版を選ぶ |
| `ModuleNotFoundError` | 仮想環境が未有効、またはインストール失敗 | `source .venv/bin/activate` を実行してから `pip install` し直す |
| 推論が極端に遅い | バッテリー節電モードがオン | 電源に接続し、高エネルギーモード（対応機種のみ）を検討する |

## 次のステップ

MLXでローカルLLMを動かせるようになったら、次は「自分の業務データ」を食べさせてみましょう。
具体的には「RAG（検索拡張生成）」の構築です。
PDFファイルやソースコードをベクトル化して保存し、MLX経由でLLMに読み込ませれば、機密情報を一切外に出さない「社内専用AIアシスタント」が完成します。

また、MLXには `mlx-examples` という公式リポジトリがあり、そこにはLoRA（低ランク適応）によるファインチューニングのサンプルも豊富にあります。
Mac1台で、自分好みの話し方や特定のタスクに特化したモデルを学習させることが可能です。
PythonとApple Siliconの組み合わせは、今のローカルAI開発において最強の布陣と言っても過言ではありません。

## よくある質問

### Q1: Ollamaがあるのに、なぜわざわざMLXをPythonで書くのですか？

Ollamaは非常に優秀なツールですが、推論エンジンがブラックボックス化されがちです。
MLXを直接叩くことで、トークンごとの確率を取得したり、特定のレイヤーの挙動を調整したりといった、エンジニアリングの自由度が格段に上がります。
また、Pythonの既存システム（DjangoやFastAPIなど）への組み込みが非常にスムーズなのも理由です。

### Q2: 8GBメモリのMacBook Airでも動きますか？

結論から言うと、かなり厳しいです。
4bit量子化した3Bクラスのモデル（Llama-3.2-3Bなど）なら動きますが、OSやブラウザがメモリを消費しているとすぐにスワップが発生します。
「実用」を考えるなら、16GBが最低ライン、24GB以上あれば快適に開発ができるというのが私の実感です。

### Q3: モデルのダウンロード先を変更したいのですが。

デフォルトでは `~/.cache/huggingface/` に保存されます。
変更したい場合は、環境変数 `HF_HOME` を設定してください。
大容量のモデルを扱うとディスクを圧迫するため、外付けSSDなどを指定するのも一つの手ですね。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac Studio M2 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">32GB超のメモリで70Bクラスのモデルも視野に入る、ローカルLLM開発の決定版</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを高速に動かす方法](/posts/2026-08-04-mlx-apple-silicon-local-llm-tutorial/)
- [MLX 使い方 入門：Apple SiliconでLLMを爆速動作させる](/posts/2026-07-22-mlx-apple-silicon-local-llm-guide/)
- [MLX入門：Apple SiliconでローカルLLMを爆速で動かす方法](/posts/2026-08-02-apple-silicon-mlx-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Ollamaがあるのに、なぜわざわざMLXをPythonで書くのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaは非常に優秀なツールですが、推論エンジンがブラックボックス化されがちです。 MLXを直接叩くことで、トークンごとの確率を取得したり、特定のレイヤーの挙動を調整したりといった、エンジニアリングの自由度が格段に上がります。 また、Pythonの既存システム（DjangoやFastAPIなど）への組み込みが非常にスムーズなのも理由です。"
      }
    },
    {
      "@type": "Question",
      "name": "8GBメモリのMacBook Airでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "結論から言うと、かなり厳しいです。 4bit量子化した3Bクラスのモデル（Llama-3.2-3Bなど）なら動きますが、OSやブラウザがメモリを消費しているとすぐにスワップが発生します。 「実用」を考えるなら、16GBが最低ライン、24GB以上あれば快適に開発ができるというのが私の実感です。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルのダウンロード先を変更したいのですが。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "デフォルトでは ~/.cache/huggingface/ に保存されます。 変更したい場合は、環境変数 HFHOME を設定してください。 大容量のモデルを扱うとディスクを圧迫するため、外付けSSDなどを指定するのも一つの手ですね。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Mac Studio M2 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">32GB超のメモリで70Bクラスのモデルも視野に入る、ローカルLLM開発の決定版</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
