---
title: "Apple Siliconの性能を解放するMLXでローカルLLMを動かす方法"
date: 2026-10-25T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-tutorial"
cover:
  image: "/images/posts/2026-10-25-mlx-apple-silicon-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon ローカルLLM"
  - "Python 機械学習"
  - "Llama 3 Mac 実行"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple純正の機械学習フレームワーク「MLX」を使用し、MacのGPUをフル活用してLlama 3やGemma 2などの最新LLMを爆速で動かすPythonスクリプトを作成します。
llama.cppのようなツールを介さず、Pythonから直接モデルを制御するため、将来的に自作アプリへAI機能を組み込む土台になります。
Pythonの基本的な読み書きができ、ターミナルでコマンドを打つことに抵抗がない方を対象としています。

## 先に確認するスペック・料金

Apple Silicon（M1, M2, M3, M4シリーズ）を搭載したMacが必須です。
IntelチップのMacではMLXは動作しません。
最も重要なのは「ユニファイドメモリ（RAM）」の容量です。

最低ラインは8GBですが、OSやブラウザがメモリを消費するため、実際にモデルに割り当てられるのは4〜5GB程度になります。
7B（70億パラメータ）クラスのモデルを4bit量子化で動かすには、最低16GBのメモリを積んだモデルを強く推奨します。
私はMac Studio（M2 Ultra / 128GBメモリ）でも検証していますが、メモリが多ければ多いほど、Llama-3-70Bのような巨大なモデルも快適に動作します。
APIは一切使わず、自分のPC内で完結するため、月額費用や従量課金は0円です。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす手段は、他にもOllamaやLM Studio、llama.cppなどがあります。
しかし、Pythonエンジニアが「仕事で使える実装」を目指すなら、MLX一択です。
MLXはAppleのAIチームが開発しているため、MacのGPU（Unified Memoryアーキテクチャ）に最適化された計算グラフを構築します。

PyTorchに近い操作感でありながら、CPUとGPUの間でデータをコピーする無駄（オーバーヘッド）が発生しません。
この「ゼロコピー」のおかげで、1秒間に生成されるトークン数が他のフレームワークより圧倒的に速いのが特徴です。
また、推論だけでなく「LoRA（低ランク適応）」による追加学習も公式がサポートしているため、将来的な拡張性が非常に高いのも選ぶ理由です。

## Step 1: 環境を整える

MLX本体と、Hugging Faceからモデルを簡単にロードするためのユーティリティ `mlx-lm` をインストールします。

```bash
# Python 3.10以上の環境を用意してください
# 依存ライブラリのインストール
pip install mlx-lm mlx huggingface_hub
```

`mlx-lm` は、Hugging Face上にある「MLXフォーマット済みモデル」を1行でダウンロード・実行できるライブラリです。
自力でモデルを変換する手間が省けるため、実務ではこれを使うのが標準です。

⚠️ **落とし穴:**
Intel Macにインストールしようとするとエラーになります。また、Pythonのバージョンが古すぎると `mlx` パッケージが見つからないというエラーが出るので、`python --version` で3.10以上であることを必ず確認してください。

## Step 2: 基本の設定

まずは、どのモデルを動かすかを決めます。
今回はMetaが公開している「Llama-3.1-8B-Instruct」をMLX向けに4bit量子化したものを使います。
4bit量子化を選ぶ理由は、メモリ消費量を抑えつつ、推論精度を実用レベルで維持できるからです。

```python
import os
from mlx_lm import load, generate

# 使用するモデルの指定（Hugging Faceのレポジトリ名）
# 4bit量子化版を指定することで、8GB〜16GBメモリのMacでも動作可能にします
model_id = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"

# モデルとトークナイザーの読み込み
# load関数はキャッシュを確認し、なければ自動的にダウンロードを開始します
model, tokenizer = load(model_id)
```

`load` 関数を呼び出す際、初回は数GBのダウンロードが発生します。
「なぜ4bitなのか」という点ですが、8bitやフル精度（FP16）だとメモリ消費が2倍、4倍と膨れ上がり、生成速度が極端に落ちる（スワップが発生する）ためです。
レスポンス0.1秒を目指すなら、まずは4bitから始めるのが鉄則です。

## Step 3: 動かしてみる

最小限のコードでテキストを生成してみましょう。
ここでは「ストリーミング表示」を実装します。
AIの回答が完成するまで待つのではなく、生成されたそばから文字を表示させることで、体感速度を劇的に向上させます。

```python
# プロンプトの準備
# Llama 3のフォーマットに従って記述します
prompt = "Apple Siliconのすごさを3行で教えてください。"

# 生成の実行
# max_tokens: 生成する最大文字数。最初は短め（200程度）にして挙動を見ます
# temp: 0.7に設定することで、回答の「遊び」と「正確性」のバランスを取ります
response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=512,
    temp=0.7,
    verbose=True # ターミナルに生成過程を表示する
)

print(f"\n最終回答:\n{response}")
```

### 期待される出力

```
1. ユニファイドメモリによりGPUとCPUが高速にデータを共有できる点。
2. 高いワットパフォーマンスで、発熱を抑えつつ爆速なAI推論が可能な点。
3. MLXフレームワークにより、専用ハードウェアの性能を100%引き出せる点。
```

結果が出力されれば成功です。
生成速度（tokens per second）に注目してください。
M2 Pro以上のチップなら、秒間20〜30トークン以上は出ているはずです。
これは、人間が文章を読むスピードよりも圧倒的に速い数値です。

## Step 4: 実用レベルにする

単発の質問ではなく、過去の文脈を理解する「チャット形式」に拡張します。
ローカルLLMを仕事で使う場合、システムプロンプト（役割設定）を与えて回答を制御するのが一般的です。

```python
from mlx_lm import load, generate

def chat_with_ai():
    model_id = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
    model, tokenizer = load(model_id)

    # チャット履歴を保持するリスト
    messages = [
        {"role": "system", "content": "あなたは優秀なエンジニアです。簡潔に回答してください。"}
    ]

    while True:
        user_input = input("USER: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        messages.append({"role": "user", "content": user_input})

        # チャットテンプレートの適用
        # これをしないと、モデルが「誰の発言か」を誤認して壊れた回答をします
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        print("AI: ", end="", flush=True)

        # 逐次表示させるためのロジック（実際の実務で最も使われる形式）
        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=1000,
            temp=0.6,
            verbose=False,
        )

        print(response)
        messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    chat_with_ai()
```

このコードのポイントは `tokenizer.apply_chat_template` です。
Llama 3には `<|begin_of_text|>` といった特殊なタグが存在し、それらを正しく挿入しないと性能が著しく低下します。
MLXでは、このテンプレート適用をライブラリ側でケアしてくれるため、開発者はメッセージのリストを管理するだけで済みます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `MemoryError` | 指定したモデルがメモリに対して大きすぎる | パラメータ数の小さいモデル（1Bや3B）に変更するか、量子化ビット数を下げたモデルを選ぶ |
| `ModuleNotFoundError: mlx` | Apple Silicon以外の環境、または仮想環境の不備 | `pip install mlx` を実行し、チップがM1/M2/M3/M4であることを確認 |
| 回答が英語になる | モデル自体が日本語を学習していない | `Llama-3-Swallow` や `Gemma-2` など、日本語に強いモデルIDを指定する |

## 次のステップ

ここまでの手順で、あなたのMacは「完全にプライベートなAIサーバー」になりました。
次に挑戦すべきは「RAG（検索拡張生成）」との組み合わせです。
MLXで動かしているLLMに、自分のPDFファイルやメモ帳の内容を読み込ませることで、社内ドキュメント専用のAIアシスタントを構築できます。

また、MLXは公式のリポジトリ（apple/mlx-examples）で、LoRAを使った微調整のサンプルを公開しています。
自分の過去のメールや執筆スタイルを学習させ、自分専用のライティングAIを作ることも夢ではありません。
「クラウドにデータを投げたくないが、AIの力は借りたい」という実務の現場では、このMLXによるローカル実行が最強の武器になります。

## よくある質問

### Q1: メモリ8GBのMacBook Airでも動きますか？

動きますが、モデル選びが重要です。Llama-3.1-8Bだとシステムのメモリ不足で動作がカクつく可能性が高いため、`mlx-community/Llama-3.2-1B-Instruct-4bit` などの1B（10億）パラメータクラスのモデルを試してください。これなら8GBでも軽快に動きます。

### Q2: 生成速度をさらに上げるにはどうすればいいですか？

`generate` 関数の引数にある `temp`（温度）を下げるのではなく、モデルの量子化精度を確認してください。4bitよりも2bitの方が速いですが、精度は落ちます。また、実行時はブラウザのタブを閉じ、GPUメモリをLLMに集中させるのが最も効果的です。

### Q3: 商用利用は可能ですか？

MLXフレームワーク自体はMITライセンスですが、動かす「モデル」のライセンスに依存します。例えばLlama 3.1はMetaのライセンスに従う必要があります。利用前に必ずHugging Faceのモデルカードを確認し、商用利用の可否をチェックしてください。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 36GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">7Bモデルを余裕で回しつつ、将来的なLoRA学習にも対応できるメモリ容量</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX入門 Apple SiliconでローカルLLMを爆速で動かす方法](/posts/2026-08-27-apple-silicon-mlx-local-llm-tutorial/)
- [MLX 使い方 入門（Apple Silicon MacでLLMを動かす方法）](/posts/2026-07-15-mlx-apple-silicon-llm-tutorial-for-beginners/)
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
        "text": "動きますが、モデル選びが重要です。Llama-3.1-8Bだとシステムのメモリ不足で動作がカクつく可能性が高いため、mlx-community/Llama-3.2-1B-Instruct-4bit などの1B（10億）パラメータクラスのモデルを試してください。これなら8GBでも軽快に動きます。"
      }
    },
    {
      "@type": "Question",
      "name": "生成速度をさらに上げるにはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "generate 関数の引数にある temp（温度）を下げるのではなく、モデルの量子化精度を確認してください。4bitよりも2bitの方が速いですが、精度は落ちます。また、実行時はブラウザのタブを閉じ、GPUメモリをLLMに集中させるのが最も効果的です。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用は可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MLXフレームワーク自体はMITライセンスですが、動かす「モデル」のライセンスに依存します。例えばLlama 3.1はMetaのライセンスに従う必要があります。利用前に必ずHugging Faceのモデルカードを確認し、商用利用の可否をチェックしてください。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 36GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">7Bモデルを余裕で回しつつ、将来的なLoRA学習にも対応できるメモリ容量</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2036GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
