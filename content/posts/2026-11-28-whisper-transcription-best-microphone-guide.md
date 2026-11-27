---
title: "Whisperの文字起こし用マイク選び：USB・XLR・ワイヤレスの違い"
date: 2026-11-28T00:00:00+09:00
slug: "whisper-transcription-best-microphone-guide"
description: "Whisper向けの録音を手持ちの機材で改善する方法と、USB・XLR・ワイヤレスを用途に応じて選ぶポイントを整理します。"
cover:
  image: "/images/posts/2026-11-28-whisper-transcription-best-microphone-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Buyer Guide"
tags:
  - "Whisper"
  - "文字起こし"
  - "おすすめマイク"
  - "ダイナミックマイク"
  - "ローカルLLM"
---

Whisper の誤認識を減らしたいなら、まずマイクを買うより、話す位置と録音レベルを整えるのがおすすめです。机で一人が話す、会議で複数人が話す、屋外で動きながら収録する。それぞれ必要なマイクの置き方が違います。この記事は公式仕様に基づく選び方で、機種別の認識率を実測した比較ではありません。

## 買う前に、手持ちのマイクで3分試す

1. 普段使う部屋で、固有名詞と数字を含む短い原稿を録音。普段キーボードを使うなら、入力しながらも試す。
2. 同じ機材で、声が大きすぎて歪まない範囲で口との距離を一定にし、マイクの向きを調整してもう一度録音する。
3. 同じ Whisper モデル・同じ設定で起こし、固有名詞、数字、文の脱落、不要な挿入を見比べる。会議用なら席ごとの聞こえ方と発言の重なりも聴き返す。

距離や置き方だけで誤りが減るなら、そこで十分です。話者の声が重なっているなら、一人用の高価なマイクを机の中央に置くより、話者ごとに近い位置で録る方を先に検討します。

## 接続は、設置と運用で選ぶ

| 用途 | 選ぶ基準 |
|---|---|
| 机で一人のナレーション・音声入力 | 手持ちのマイクか、PCに直接つなげる USB。キーボードから少し離し、口元との距離を保ちやすい位置に |
| 既にミキサーやオーディオインターフェースがある | XLR も候補。入力ゲインやルーティングを自分で調整したいときに便利 |
| 動きながらの取材や対談 | 話者の近くに付けられるワイヤレス機。受信機の接続、充電、予備録音を事前に確認 |

[Shure MV7+ の公式ガイド](https://pubs.shure.com/view/guide/MV7plus/en-US.pdf)では、USB-C 側のソフトウェア調整がパッシブ XLR の音には反映されません。両方の端子が付いていても機能は同じではありません。[DJI Mic 2 の公式サポート](https://www.dji.com/support/product/mic-2)で案内される 32-bit float は送信機の内部録音です。スマートフォンに Bluetooth で直接つないだ状態では内部録音自体が使えません。風切り音や話者の重なりも、録音形式を変えるだけでは防げません。

## Whisperのモデル選びと録音機材は別

[OpenAI の参照実装](https://github.com/openai/whisper/blob/main/whisper/audio.py)は、音声ファイルを読み込む際にモノラルの 16 kHz に変換します。USB か XLR かで Whisper の VRAM が節約されるわけではありません。ローカル実行の目安は [公式 README のモデル別表](https://github.com/openai/whisper#available-models-and-languages)を確認し、使う実装や量子化設定でも変わると考えてください。

## よくある質問

### USBとXLRでWhisperのVRAM使用量は変わりますか？

接続方式は主な決定要因ではありません。Whisperが音声ファイルを読み込んだ後のVRAMは、主にモデルや実行環境の設定で変わります。

### Bluetoothイヤホンのマイクではだめですか？

今ある機材で試して構いません。同じ原稿を録音し、固有名詞や数字の聞き取り、途切れ、周囲の音を比べてから買い足すか判断してください。

### 大きいモデルに替えれば録音の問題を補えますか？

録音で消えた音や、同時に話して聞き分けられない発言を確実に戻すことはできません。先に距離、部屋の反響、録音レベルを見直してください。

{{< rawhtml >}}
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "USBとXLRでWhisperのVRAM使用量は変わりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "接続方式は主な決定要因ではありません。Whisperが音声ファイルを読み込んだ後のVRAMは、主にモデルや実行環境の設定で変わります。"
      }
    },
    {
      "@type": "Question",
      "name": "Bluetoothイヤホンのマイクではだめですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "今ある機材で試して構いません。同じ原稿を録音し、固有名詞や数字の聞き取り、途切れ、周囲の音を比べてから買い足すか判断してください。"
      }
    },
    {
      "@type": "Question",
      "name": "大きいモデルに替えれば録音の問題を補えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "録音で消えた音や、同時に話して聞き分けられない発言を確実に戻すことはできません。先に距離、部屋の反響、録音レベルを見直してください。"
      }
    }
  ]
}
</script>
{{< /rawhtml >}}
