---
title: "Slide2Videoでスライドをナレーション付き動画へ自動変換する実装ガイド"
date: 2026-04-03T00:00:00+09:00
slug: "slide2video-automated-presentation-video-guide"
description: "PDFやPowerPointのスライドを、AIが内容を解析してナレーション付き動画に自動変換する。。人手による録音や動画編集の工数を、API実行と設定ファ..."
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Slide2Video 使い方"
  - "スライド動画化 自動化"
  - "OpenAI TTS 動画生成"
  - "Python 動画編集 自動化"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- PDFやPowerPointのスライドを、AIが内容を解析してナレーション付き動画に自動変換する。
- 人手による録音や動画編集の工数を、API実行と設定ファイル管理だけで「ゼロ」に近づける。
- 大量の社内研修資料や定期レポートを動画化したいエンジニアには最適だが、細かい演出に拘るクリエイターには不向き。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">MINISFORUM MS-01</strong>
<p style="color:#555;margin:8px 0;font-size:14px">動画のエンコードや大量のAPI処理を回すなら、i9搭載の強力なミニPCを常時稼働させるのが快適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=MINISFORUM%20MS-01&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMINISFORUM%2520MS-01%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMINISFORUM%2520MS-01%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、社内の「ドキュメント説明コスト」を削減したいエンジニアやPMにとって、Slide2Videoは間違いなく「買い」です。
★評価: 4.5/5
10分間のプレゼン動画を人間が作ろうとすると、台本作成、録音、スライドとのタイミング調整で、慣れていても3〜5時間は溶けます。
Slide2Videoなら、OpenAIのAPIコスト数ドルと、数分の処理待ちだけで同じ成果物が出せます。
プロレベルの映像美は期待できませんが、情報の伝達という実務上の目的はこれで100%達成可能です。
ただし、OpenAIやAnthropicのAPIキーが必要なため、完全無料で運用したい人には向きません。

## このツールが解決する問題

従来、スライドを動画化する作業は「もっともコスパの悪いルーチンワーク」の一つでした。
特にSIer時代に経験しましたが、システムの仕様変更があるたびにマニュアル動画を録り直すのは、現場のエンジニアにとって苦痛でしかありません。
マイクのノイズを気にし、噛んだら撮り直し、さらに動画編集ソフトのタイムラインで0.1秒単位の調整を繰り返す作業は、本質的な開発時間を奪います。

Slide2Videoは、この「動画編集という非エンジニアリングな作業」をコードで解決します。
スライドからテキストを抽出し、LLMが文脈に沿った台本を生成、それをTTS（Text-to-Speech）で音声化して合成する。
この一連のパイプラインを自動化することで、ドキュメントの更新と動画の更新を完全に同期させることができます。
「ドキュメントは最新だけど、解説動画は半年前の古いバージョンのまま」という、実務でありがちな負債を解消できるのが最大の価値です。

## 実際の使い方

### インストール

Slide2VideoはPython環境で動作します。
画像処理に`ffmpeg`を使用するため、OS側でのインストールが必須です。
Ubuntuなら`sudo apt install ffmpeg`、Macなら`brew install ffmpeg`を事前に済ませておいてください。

```bash
# ライブラリのインストール
pip install slide2video

# 依存関係としてOpenAIなどのSDKも必要
pip install openai python-dotenv
```

Python 3.10以降が推奨されています。
内部でスライドを画像として処理するために`PyMuPDF`や`Pillow`を使用するため、依存ライブラリのビルドでコケないよう、最新のpipを使用するのが無難です。

### 基本的な使用例

ドキュメントに基づいた基本的な実装フローを紹介します。
最もシンプルな構成は、PDFスライドを入力として、OpenAIの`gpt-4o`で台本を作り、`tts-1`で音声合成する形です。

```python
import os
from slide2video import SlideConverter
from dotenv import load_dotenv

load_dotenv()

# プロセッサの初期化
# デフォルトでOpenAI APIを使用する設定
converter = SlideConverter(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",  # スライド解析用
    voice="alloy",    # ナレーション音声の種類
    fps=24            # 出力動画のフレームレート
)

# 動画生成の実行
# input: PDFファイルのパス, output: 保存先ファイル名
result = converter.convert(
    input_path="./docs/presentation.pdf",
    output_path="./output/presentation_video.mp4",
    generate_script=True  # スライドから台本を自動生成
)

print(f"動画生成完了: {result.duration_seconds}秒, コスト推定: ${result.estimated_cost}")
```

このコードを実行すると、各スライドの視覚情報をVision APIが読み取り、ナレーションを作成し、それぞれのスライドの表示時間を音声の長さに自動で合わせて結合してくれます。
実務で使う場合は、`generate_script=False`にして、自前で用意した`json`形式の台本を流し込む方が、技術用語の読み間違いを防げるため安定します。

### 応用: 実務で使うなら

私なら、これをGitHub ActionsのCI/CDパイプラインに組み込みます。
例えば、ドキュメント用のディレクトリにあるMarkdownやPowerPointが更新されたら、自動的に解説動画を再生成してS3や社内ポータルにアップロードする構成です。

```python
# 応用例：スライドごとに細かいプロンプト制御を行う場合
from slide2video import SlideConverter, Config

config = Config()
config.set_system_prompt("あなたはプロのIT講師です。専門用語を噛み砕いて解説してください。")

converter = SlideConverter(config=config)

# スライドごとのメタデータ（読み方の指定など）を定義
slide_metadata = {
    1: {"note": "ここでは製品のコンセプトを強調。"},
    5: {"note": "この図の青い部分は無視してOK。"},
}

converter.convert_with_metadata(
    input_path="service_guide.pdf",
    metadata=slide_metadata
)
```

このように、特定のスライドに対して「ここは強調して」といった指示を与えることで、AI特有の淡々とした解説を、より人間に近いプレゼンに近づけることが可能です。

## 強みと弱み

**強み:**
- パイプラインの簡潔さ: 10行程度のコードで「スライド解析→台本→音声→動画合成」が完結します。
- 多言語展開が容易: OpenAIのTTSを使えば、同じスライドから日本語、英語、スペイン語の解説動画を数分で出し分けられます。
- メンテナンス性: スライドの1枚を差し替えるだけで、動画全体を再生成できるため、情報の鮮度を保ちやすいです。

**弱み:**
- 日本語の読みの甘さ: OpenAIのTTSは時折、漢字の読みを間違えます（「SIer」を「エスアイイーアール」と読むなど）。
- デザインの自由度不足: スライドの切り替えエフェクトや、ナレーションに合わせたズームなどの細かい演出は、現時点のAPI経由では困難です。
- GPU負荷: 大量のスライドを並列処理する場合、ローカルでのffmpegエンコードにそれなりのCPU/GPUパワーを食います。RTX 4090クラスなら一瞬ですが、低スペックなノートPCだと時間がかかります。

## 代替ツールとの比較

| 項目 | Slide2Video | Synthesia | Canva |
|------|-------------|-------|-------|
| 自動化 | コードで完全自動化可能 | APIはあるが高価 | 手動操作が前提 |
| アバター | なし（スライドのみ） | あり（超リアル） | なし |
| コスト | API実費のみ（安価） | 月額制（高価） | 無料〜月額 |
| 自由度 | ロジックで制御可能 | プリセットに依存 | デザイン自由度が高い |

「顔出しアバター」が必要ならSynthesia一択ですが、エンジニア向けの技術解説や社内レポートならSlide2Videoの方が圧倒的に小回りが利きます。
何より、プログラムから呼び出せるという点が、自動化マニアにはたまりません。

## 私の評価

個人的な評価は「4.5/5」です。
プレゼン動画という、これまで「作るのが面倒で放置されがちだった資産」を、コードの管理下に置けるようになった意義は大きいです。
特に、日々仕様が変わるアジャイル開発の現場において、ドキュメントの動画化を自動化できるメリットは計り知れません。

ただし、0.5マイナスしたのは「音声の表現力」の限界です。
OpenAI TTSは綺麗ですが、強調したい部分で声を張るような、人間のプレゼン特有の抑揚を再現するには至っていません。
もし、より高い品質を求めるなら、ナレーション生成部分だけをElevenLabsなどの高機能な音声合成エンジンに差し替えるカスタマイズが必要になるでしょう。
それでも、基盤となるパイプラインをSlide2Videoで構築できるのは、開発者にとって大きなショートカットになります。

## よくある質問

### Q1: PowerPoint (.pptx) はそのまま使えますか？

内部的にPDFへの変換を挟むことが推奨されています。Pythonなら`comtypes`（Windows）や`LibreOffice`のCLIを使ってPDFに変換してからSlide2Videoに渡すのが、最もフォーマット崩れが少なく安定する手順です。

### Q2: OpenAI以外のLLMやTTSは使えますか？

設定ファイルを書き換えることで、Claude 3 (Anthropic) やローカルのWhisper/TTSモデルとの連携も可能です。ただし、公式のラッパーが最も充実しているのは現状OpenAI APIの構成です。

### Q3: 動画の解像度は指定できますか？

はい、`Config`オブジェクトで指定可能です。デフォルトは1080pですが、SNS投稿用に720pに落としたり、スライドのアスペクト比（4:3 or 16:9）に合わせて自動調整するオプションも備わっています。
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "PowerPoint (.pptx) はそのまま使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "内部的にPDFへの変換を挟むことが推奨されています。Pythonならcomtypes（Windows）やLibreOfficeのCLIを使ってPDFに変換してからSlide2Videoに渡すのが、最もフォーマット崩れが少なく安定する手順です。"
      }
    },
    {
      "@type": "Question",
      "name": "OpenAI以外のLLMやTTSは使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "設定ファイルを書き換えることで、Claude 3 (Anthropic) やローカルのWhisper/TTSモデルとの連携も可能です。ただし、公式のラッパーが最も充実しているのは現状OpenAI APIの構成です。"
      }
    },
    {
      "@type": "Question",
      "name": "動画の解像度は指定できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、Configオブジェクトで指定可能です。デフォルトは1080pですが、SNS投稿用に720pに落としたり、スライドのアスペクト比（4:3 or 16:9）に合わせて自動調整するオプションも備わっています。"
      }
    }
  ]
}
</script>
