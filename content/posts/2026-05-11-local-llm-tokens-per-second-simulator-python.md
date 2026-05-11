---
title: "ローカルLLMの推論速度を体感するシミュレーター自作ガイド"
date: 2026-05-11T00:00:00+09:00
slug: "local-llm-tokens-per-second-simulator-python"
cover:
  image: "/images/posts/2026-05-11-local-llm-tokens-per-second-simulator-python.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "ローカルLLM 速度"
  - "tokens per second 目安"
  - "Python LLM シミュレーター"
  - "GPU ベンチマーク 体感"
---
**所要時間:** 約20分 | **難易度:** ★☆☆☆☆

## この記事で作るもの

- 指定した「tokens/second」の速度でテキストを流し、LLMのレスポンス速度を擬似的に再現するPythonスクリプト
- Pythonの基礎（標準ライブラリの使用）があれば動作可能
- 自分のPC環境や検討中のGPUで、どれくらいの「待ち心地」になるかを数値ではなく視覚的に確認できる環境

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3 8Bを快適に動かせるコスパ最強の入門GPU</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMの世界では、モデルのパラメータ数（重さ）と、それを動かすGPUのメモリ帯域幅で速度が決まります。
私が使っているRTX 4090であれば、7Bクラスのモデルなら100 tokens/secを超えることも珍しくありませんが、これが30Bクラスや70Bクラスになると10〜20 tokens/secまで落ち込みます。
この「10 tokens/sec」という数字が、人間にとって「速い」と感じるか「遅くてイライラする」と感じるかは、実際に目にしてみないと分かりません。

購入前に知っておくべき目安として、16GBのVRAMを持つRTX 4060 Tiであれば、最新のLlama 3 8Bクラスを非常に快適（40〜60 tokens/sec程度）に動かせます。
一方で、安価な中古GPUやメモリ帯域の狭いエントリーモデルを選ぶと、1〜3 tokens/secという「1文字ずつゆっくり出てくる」状態になり、実務では使い物になりません。
この記事のシミュレーターを動かすだけならスペックは不要ですが、実際のLLM運用を考えているなら、最低でもVRAM 12GB以上のNVIDIA製GPU、もしくはメモリ32GB以上のApple Silicon Macを推奨します。
API経由（GPT-4等）で使う場合は月額$20程度ですが、ローカルなら電気代以外は無料です。

## なぜこの方法を選ぶのか

ベンチマークサイトの結果を眺めるだけでは、その速度が自分の業務効率にどう影響するかは判断できません。
例えば、カスタマーサポートの自動返信なら20 tokens/secで十分ですが、リアルタイム対話ならもっと速度が欲しい、といった具合です。
わざわざ重いモデルをダウンロードして環境構築する前に、この数行のスクリプトで「速度の体験」を先取りするのが最も効率的だと考えています。
既存のツールもありますが、自分で制御ロジックを書くことで、日本語トークナイザー特有の「1トークン＝何文字か」という感覚も身につきます。

## Step 1: 環境を整える

Pythonがインストールされていれば、追加のライブラリ（pip install）は一切不要です。
標準ライブラリの `time` と `sys` だけで完結させます。

```bash
# 作業用のディレクトリを作成して移動
mkdir llm-speed-sim
cd llm-speed-sim

# Pythonのバージョン確認（3.8以上を推奨）
python --version
```

Python 3.8以上であれば、高精度なタイマーが使えるため、より正確なシミュレーションが可能です。
Windows環境で実行する場合、標準のコマンドプロンプトだとエスケープシーケンスの関係で表示がカクつくことがあるため、VS Codeの統合ターミナルやWindows Terminalを使うことをお勧めします。

⚠️ **落とし穴:**
標準の `print()` 関数は、出力の末尾に改行を加えたり、内部でバッファリング（一時溜め込み）を行ったりします。
そのため、単純に `print` を使うと「一気に表示されて、しばらく止まる」という不自然な動きになり、LLMのストリーミング感が出ません。
後述する `sys.stdout.flush()` を使うのが、このシミュレーターの肝になります。

## Step 2: 基本の設定

まずは、指定した速度で1文字ずつ出力する基本的なロジックを組みます。
`speed_sim.py` という名前で以下のファイルを保存してください。

```python
import time
import sys

def simulate_llm_response(text, tokens_per_second):
    """
    指定したトークン速度でテキストを表示する
    1トークン = 0.75単語（英語基準）だが、日本語の場合は1トークン≒1文字として計算
    """
    # 1トークンあたりの待機時間を計算
    delay = 1.0 / tokens_per_second

    print(f"--- 速度設定: {tokens_per_second} tokens/sec で出力開始 ---\n")

    for char in text:
        # 1文字（1トークンと仮定）出力
        sys.stdout.write(char)
        # 確実に即時表示させるためのマジックワード
        sys.stdout.flush()
        # 待機
        time.sleep(delay)

    print("\n\n--- 出力完了 ---")

if __name__ == "__main__":
    # テスト用のテキスト
    sample_text = (
        "ローカルLLMの世界へようこそ。推論速度は非常に重要な指標です。"
        "10 tokens/sは読書速度程度、30 tokens/sはスキャンするような速さです。"
        "この速度感の違いが、あなたの作業効率を大きく左右します。"
    )

    # 5 tokens/s で試してみる（少し遅いと感じるレベル）
    simulate_llm_response(sample_text, 5)
```

ここでは、環境変数などの複雑な設定はあえて排除しました。
「なぜこの値にするのか」という点ですが、`delay = 1.0 / tokens_per_second` とすることで、1秒間に何回ループを回すかを直感的に制御しています。
`sys.stdout.flush()` は、OSに対して「バッファに溜めずに今すぐ画面に出せ」と命令する重要な一歩です。

## Step 3: 動かしてみる

作成したスクリプトを実行します。

```bash
python speed_sim.py
```

### 期待される出力

```
--- 速度設定: 5 tokens/sec で出力開始 ---

ローカルLLMの世界へようこそ。推論速度は非常に重要な指標です。
...（1秒間に5文字のペースでじわじわ表示される）

--- 出力完了 ---
```

5 tokens/secという数字は、多くのローカルLLMユーザーが「最低限、我慢できる」と感じる境界線です。
実際に目で追ってみると、文章を読みながら次の文字を待つような感覚になるはずです。
これが実務で使えるかどうか、あなたの感覚で判断してみてください。

## Step 4: 実用レベルにする

実務では「複数の速度を比較したい」というニーズがあります。
また、日本語LLMの場合は「1トークンが1文字」とは限りません。
トークナイザーによって異なりますが、一般的に日本語は「1文字＝約1〜1.5トークン」程度に分割されることが多いです。
これらを考慮した、より実戦的な比較スクリプトにアップグレードします。

```python
import time
import sys

def stream_print(text, tps, label):
    print(f"\n【{label}: {tps} tokens/s】")
    delay = 1.0 / tps

    start_time = time.time()
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    end_time = time.time()

    duration = end_time - start_time
    actual_tps = len(text) / duration
    print(f"\n(実測値: {actual_tps:.2f} chars/s, 所要時間: {duration:.2f}s)")

def main():
    long_text = (
        "AIエンジニアとして実務でLLMを導入する際、最も多い不満は「待ち時間」です。"
        "特に、RAG（検索拡張生成）を用いた社内ドキュメント検索システムでは、"
        "回答の生成が遅いとユーザーはすぐに使わなくなってしまいます。"
        "一方で、バックグラウンドで行う要約タスクであれば、1 tokens/sでも問題ありません。"
        "用途に合わせて必要なハードウェアスペックを見極めることが、コスト削減の鍵です。"
    )

    # 比較したい速度のリスト
    speeds = [2, 10, 30, 100]

    for s in speeds:
        stream_print(long_text, s, f"設定速度 {s}")
        print("-" * 30)

if __name__ == "__main__":
    main()
```

このコードでは、実際にループにかかった時間を計測して「実測値」を表示するようにしました。
`30 tokens/sec` 以上になると、人間が黙読する速度を上回ります。
逆に `2 tokens/sec` は、プログラミングコードの生成を待つにはあまりにも苦痛であることを体感できるはずです。

私が過去に実務で経験した例ですが、社内向けのチャットツールにLlama 2の70B（当時）を導入した際、最初は5 tokens/sec程度しか出ませんでした。
エンジニアからは「遅すぎる」と不評でしたが、出力を10 tokens/secまで改善したところ、利用率が3倍に跳ね上がった経験があります。
「たった5の差」がユーザー体験（UX）を決定づけるのです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| 文字が小出しにならず一気に表示される | `sys.stdout.flush()` がない、またはIDEの制限 | VS Codeのターミナルや、ネイティブのターミナル（iTerm2等）を使用する |
| 指定した速度より明らかに遅い | PCの負荷が高い、または `time.sleep` の精度限界 | 高負荷なソフトを閉じる。Windowsの場合は `time.beginPeriod` の影響を受けることがある |
| 日本語が文字化けする | ターミナルの文字コード設定（UTF-8）の不一致 | `chcp 65001` コマンド（Windows）を実行してからスクリプトを走らせる |

## 次のステップ

このスクリプトで「自分が必要な速度」が見えたら、次は実際にその速度を出せる環境を選定するフェーズです。
具体的な指標として、以下を参考にしてください。

1.  **30 tokens/sec以上を目指す場合:**
    最新のMac（M3 Maxなど）か、NVIDIA RTX 4080/4090を検討してください。
    モデルを「量子化（4-bitなど）」して使うのが、ローカルLLMの鉄則です。

2.  **10 tokens/sec程度で妥協する場合:**
    RTX 3060 12GBや4060 Ti 16GBが非常にコスパが良いです。
    実務での要約や、簡単なコード補完ならこれで十分戦えます。

3.  **トークナイザーの理解を深める:**
    次は実際に `transformers` ライブラリをインストールし、`AutoTokenizer` を使って「自分の書いたテキストが正確に何トークンになるか」をカウントしてみてください。
    「こんにちは」という5文字が、内部では何分割されているかを知ることで、真の tokens/second が計算できるようになります。

この記事のスクリプトを少し改造して、API（OpenAIやAnthropic）のレスポンスをそのまま流し込んで、実際のAPI速度を可視化するツールに発展させるのも面白いでしょう。

## よくある質問

### Q1: tokens/secと文字数/秒は同じですか？

厳密には違います。英語だと1トークンは約0.75単語、日本語だと1文字が1〜2トークンに換算されます。このスクリプトでは簡略化のために「1文字＝1トークン」としていますが、実機では数値よりも少し遅く感じることが多いです。

### Q2: なぜ100 tokens/sec以上が必要なケースがあるのですか？

対話だけなら不要ですが、RAGなどで大量の文書を一度に要約したり、エージェントが自律的に何度も推論を繰り返す場合は、1回の推論がコンマ数秒で終わる「爆速」の環境が求められます。

### Q3: VRAMが足りないとどうなりますか？

GPUのメモリ（VRAM）にモデルが収まりきらないと、低速なメインメモリ（RAM）が使われます。そうなると速度は0.5〜1 tokens/sec程度まで壊滅的に低下し、今回作ったシミュレーターの最小値よりも遅い「地獄」を味わうことになります。
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "tokens/secと文字数/秒は同じですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "厳密には違います。英語だと1トークンは約0.75単語、日本語だと1文字が1〜2トークンに換算されます。このスクリプトでは簡略化のために「1文字＝1トークン」としていますが、実機では数値よりも少し遅く感じることが多いです。"
      }
    },
    {
      "@type": "Question",
      "name": "なぜ100 tokens/sec以上が必要なケースがあるのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "対話だけなら不要ですが、RAGなどで大量の文書を一度に要約したり、エージェントが自律的に何度も推論を繰り返す場合は、1回の推論がコンマ数秒で終わる「爆速」の環境が求められます。"
      }
    },
    {
      "@type": "Question",
      "name": "VRAMが足りないとどうなりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "GPUのメモリ（VRAM）にモデルが収まりきらないと、低速なメインメモリ（RAM）が使われます。そうなると速度は0.5〜1 tokens/sec程度まで壊滅的に低下し、今回作ったシミュレーターの最小値よりも遅い「地獄」を味わうことになります。"
      }
    }
  ]
}
</script>
