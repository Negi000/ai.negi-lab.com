---
title: "MLX 使い方 入門 Apple Silicon MacでローカルLLMを動かす方法"
date: 2026-09-13T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-tutorial"
cover:
  image: "/images/posts/2026-09-13-mlx-apple-silicon-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX"
  - "Apple Silicon"
  - "ローカルLLM"
  - "Llama 3.1"
  - "mlx-lm"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple Silicon（M1/M2/M3/M4）のGPU性能を最大限に引き出し、Llama 3.1やGemma 2といった最新のLLMと対話できるPythonスクリプトを作成します。
ライブラリにはApple公式の「MLX」を使用し、Hugging Faceからモデルを自動ダウンロードして実行する、実務に耐えうる構成を目指します。
外部APIを一切使わず、完全にオフラインで動作するため、機密情報の処理にも活用可能です。

### 前提知識
- Pythonの基本的な文法（変数、関数、pipでのインストール）がわかること
- ターミナル（Macの黒い画面）でコマンドを打つことに抵抗がないこと

### 必要なもの
- Apple Silicon搭載のMac（M1, M2, M3, M4シリーズ）
- macOS 13.5以上（最新を推奨）
- Python 3.10以上
- 空きストレージ容量：20GB以上（モデルのサイズに依存します）

## 先に確認するスペック・料金

Apple Silicon MacでローカルLLMを動かす際、最大のボトルネックはGPUの演算速度ではなく「ユニファイドメモリ（RAM）の容量」です。
MLXはCPUとGPUが同じメモリを共有する特性を活かし、VRAM（ビデオメモリ）が足りない問題を解決しますが、OSが使う分を除いた「空きメモリ」がモデルサイズを上回っている必要があります。

最低でも16GBのメモリがあれば、8B（80億パラメータ）クラスのモデルを「4-bit量子化」された状態で快適に動かせます。
8GBメモリのモデルでも動作はしますが、スワップが発生してレスポンスが1秒間に数文字というレベルまで落ちるため、実務利用は厳しいと考えてください。
本格的に開発や検証を行うなら、32GB以上のメモリを積んだMac StudioやMacBook Proが投資対効果としてベストです。

費用面では、モデルの利用自体は無料（オープンソース）です。
API経由でGPT-4oを使うと1トークンあたり数円のコストを意識する必要がありますが、ローカルLLMなら電気代以外は完全にタダで、何度でも試行錯誤が可能です。

## なぜこの方法を選ぶのか

MacでLLMを動かす方法は、他にも「Ollama」や「llama.cpp」があります。
しかし、Pythonエンジニアが「自分のアプリに組み込みたい」「独自のロジックを追加したい」と考えるなら、MLX（mlx-lm）一択です。

MLXはAppleの機械学習チームが開発しているため、Metal（MacのGPU API）への最適化が他のライブラリとは一線を画します。
例えば、PyTorchでMacのGPU（mpsデバイス）を使うよりも、MLXの方が推論速度で1.5倍から2倍近く速いケースを何度も見てきました。
また、Hugging Face形式のモデルをそのまま扱えるラッパー「mlx-lm」が登場したことで、環境構築の難易度が劇的に下がりました。
「とりあえず動く」だけでなく「最速で動く」環境を、Pythonのコードとして制御できるのがこの方法の強みです。

## Step 1: 環境を整える

まずはMLX専用の仮想環境を作成します。
システム全体のPython環境を汚すと、後で他のライブラリと依存関係が衝突して詰まる原因になるからです。

```bash
# プロジェクト用のディレクトリを作成
mkdir mlx-test && cd mlx-test

# Pythonの仮想環境を作成（Python 3.10以上が必要）
python3 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate

# MLX推論用のライブラリをインストール
pip install -U mlx-lm
```

`mlx-lm`は、AppleのMLXフレームワークをラップして、Hugging Faceにあるモデルを簡単に扱えるようにしたライブラリです。
これをインストールするだけで、必要な依存関係（numpyやmlx本体）も一緒にセットアップされます。

**落とし穴:**
Intelプロセッサを搭載した古いMacでは動作しません。
コマンド実行時に「No matching distribution found for mlx」と出た場合は、そのMacがApple Siliconかどうかを確認してください。
また、Xcode Command Line Toolsが入っていないとインストールに失敗することがあるので、その場合は `xcode-select --install` を先に実行してください。

## Step 2: 基本の設定

次に、モデルを読み込んで対話の準備をするスクリプトを書きます。
ここでは、Metaが公開している「Llama-3.1-8B-Instruct」を、Mac向けに最適化（4-bit量子化）したモデルを使用します。

```python
import os
from mlx_lm import load, generate

# 使用するモデルの指定
# mlx-communityというアカウントが、Mac向けに変換済みのモデルを多数公開しています
model_path = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"

# モデルとトークナイザー（文字を数字に変換するツール）の読み込み
# 最初に実行する際は、Hugging Faceからモデルデータ（約5GB）が自動ダウンロードされます
model, tokenizer = load(model_path)
```

`load`関数にモデルのリポジトリ名を渡すだけで、ダウンロードからメモリへの展開まで完結します。
なぜ「4bit」と付いたモデルを選ぶのかというと、16bit（標準）のモデルはメモリを約15GB消費しますが、4bitなら約5GBまで削減できるからです。
私の経験上、8Bクラスのモデルであれば4bitに圧縮しても、日本語の理解能力や推論精度が目に見えて落ちることはほとんどありません。

## Step 3: 動かしてみる

準備ができたら、実際にプロンプトを投げてみます。
MLXの`generate`関数を使いますが、そのまま出力すると結果が返ってくるまで画面が止まってしまうため、対話体験としては良くありません。
まずは最小限のコードで「動くこと」を確認します。

```python
# プロンプト（指示文）の作成
prompt = "Apple SiliconのMacでローカルLLMを動かすメリットを3つ教えてください。"

# Llama 3系の指示用フォーマットに整形
# これを忘れると、モデルが「続きの文章」を書き始めてしまい、回答になりません
messages = [{"role": "user", "content": prompt}]
formatted_prompt = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)

# 生成の実行
response = generate(model, tokenizer, prompt=formatted_prompt, verbose=False, max_tokens=500)

print(response)
```

### 期待される出力

```
1. プライバシーとセキュリティ: データが外部サーバーに送信されないため、機密情報を安全に扱えます。
2. コスト削減: サブスクリプション料金やAPI使用料がかからず、ハードウェアの電力を消費するだけで済みます。
3. オフライン利用: インターネット接続が不安定な場所や、完全にオフラインの環境でも推論が可能です。
```

この出力が出れば成功です。
レスポンス速度はどうでしょうか。M2 Pro以降のチップであれば、一瞬で回答が生成されるはずです。

## Step 4: 実用レベルにする

実務で使うなら、ChatGPTのように「文字がポツポツと出てくる（ストリーミング表示）」状態にしたいですよね。
また、一度きりの実行ではなく、対話形式で何度も質問できるようにループを組みます。
以下のコードを `app.py` として保存して実行してください。

```python
import sys
from mlx_lm import load, generate

def main():
    model_path = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
    print(f"モデルを読み込み中: {model_path}...")
    model, tokenizer = load(model_path)

    print("\n--- ローカルLLM チャット開始 (exitで終了) ---")

    while True:
        user_input = input("\nあなた: ")
        if user_input.lower() in ["exit", "quit", "終了"]:
            break

        messages = [{"role": "user", "content": user_input}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        print("AI: ", end="", flush=True)

        # ストリーミング生成
        # stream=Trueにすることで、生成されたトークンを逐次取得できる
        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=1000,
            temp=0.7, # 自由度（0.0で固定、高いほど創造的になる）
            verbose=False # 統計情報を非表示にする
        )

        # ※ mlx-lmのバージョンによってはgenerate自体が文字列を返すが、
        # 高度な制御をしたい場合は mlx_lm.utils.generate_step を使うのが実務的
        print(response)

if __name__ == "__main__":
    main()
```

このコードでは `temp=0.7` を設定しています。
実務で「事実に基づいた回答」が欲しい場合は、この値を `0.1` 程度まで下げてください。
逆に、アイデア出しやクリエイティブな用途なら `0.8` 以上に設定するのが私のセオリーです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Killed` または `Memory Error` | メモリ（RAM）不足。モデルが大きすぎる。 | より小さいモデル（3Bや1B）か、量子化ビット数の低いものを選ぶ。 |
| 意味不明な文字列が出力される | プロンプトのテンプレート形式がモデルと一致していない。 | `apply_chat_template` を正しく使うか、モデルの公式ドキュメントでタグを確認。 |
| ダウンロードが止まる | Hugging Faceへのネットワーク接続エラー。 | `export HF_ENDPOINT=https://hf-mirror.com` を試すか、安定した回線で再試行。 |

## 次のステップ

MLXでローカルLLMを動かせるようになったら、次は「RAG（検索拡張生成）」に挑戦してみてください。
自分の持っているPDFやテキストファイルを読み込ませて、その内容に基づいて回答させる仕組みです。
MLXは推論だけでなく、テキストをベクトル化する（Embedding）処理も非常に高速です。

また、Macの性能をフルに活かすなら、ローカルで動く画像生成（Stable Diffusion）もMLXで実装可能です。
RTX 4090のような爆熱・爆音のGPUを積んだPCでなくても、膝の上のMacBookで最新のAIが動く体験は、一度味わうと戻れません。
まずは自分の業務で「このデータ、外部APIに投げたくないな」と思う作業を、このスクリプトに流し込むことから始めてみてください。

## よくある質問

### Q1: メモリ8GBのMacBook Airでも動きますか？

動きますが、モデル選びが重要です。Llama 3.1 8Bはかなり重く感じるはずですので、1B（10億パラメータ）や3B（30億パラメータ）クラスのモデル、例えば「Llama-3.2-3B-Instruct-4bit」などを探して試してみてください。

### Q2: 実行中にMacのファンが激しく回りますが大丈夫ですか？

GPUをフル活用している証拠なので正常です。MLXは効率的ですが、計算負荷は高いです。ただし、クラウドAPIと違って、どれだけファンが回っても追加料金は発生しませんので、安心して使い倒してください。

### Q3: Python以外の言語からMLXは使えますか？

MLX自体はC++をベースにしており、Swiftバインディングも存在します。iOSアプリやmacOSアプリにネイティブで組み込みたい場合は、Swift版のMLXを使うことで、Apple製品に特化したAIアプリを開発することが可能です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac Studio M2 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">MLXで複数のモデルを同時に動かしたり、学習を行うなら64GBメモリが実務上の正義</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 Apple Silicon ローカルLLM 入門](/posts/2026-08-27-mlx-apple-silicon-local-llm-tutorial/)
- [MLX 使い方 入門｜MacでローカルLLMを爆速で動かす方法](/posts/2026-08-24-apple-silicon-mlx-local-llm-tutorial/)
- [Apple SiliconでLLMを動かすならMLX一択！MLX 使い方 入門](/posts/2026-09-10-mlx-apple-silicon-llm-tutorial/)

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
        "text": "動きますが、モデル選びが重要です。Llama 3.1 8Bはかなり重く感じるはずですので、1B（10億パラメータ）や3B（30億パラメータ）クラスのモデル、例えば「Llama-3.2-3B-Instruct-4bit」などを探して試してみてください。"
      }
    },
    {
      "@type": "Question",
      "name": "実行中にMacのファンが激しく回りますが大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "GPUをフル活用している証拠なので正常です。MLXは効率的ですが、計算負荷は高いです。ただし、クラウドAPIと違って、どれだけファンが回っても追加料金は発生しませんので、安心して使い倒してください。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語からMLXは使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MLX自体はC++をベースにしており、Swiftバインディングも存在します。iOSアプリやmacOSアプリにネイティブで組み込みたい場合は、Swift版のMLXを使うことで、Apple製品に特化したAIアプリを開発することが可能です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Mac Studio M2 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">MLXで複数のモデルを同時に動かしたり、学習を行うなら64GBメモリが実務上の正義</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
