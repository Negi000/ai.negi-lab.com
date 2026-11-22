---
title: "Signalのスクリーンショット制限：iPhoneとAndroidの違い"
date: 2026-11-22T00:00:00+09:00
slug: "signal-screenshot-restriction-ai-surveillance-defense"
description: "Signalの画面保護は、対応iPhoneでは既定で有効、対応AndroidではAIアシスタントの画面読み取りを初めて検知したときに有効になります。"
cover:
  image: "/images/posts/2026-11-22-signal-screenshot-restriction-ai-surveillance-defense.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI News"
tags:
  - "Signal スクショ制限"
  - "AI Surveillance"
  - "プライバシー保護"
---

Signalは2026年11月、端末のAIアシスタントによる画面読み取りへの対策を[発表しました](https://signal.org/blog/protecting-your-privacy/)。画面保護が有効な間は、Signal内のスクリーンショットや画面収録、アプリ切り替え画面のプレビュー、対象となるAIアシスタントからの読み取りが制限されます。

## どの機種で、いつ有効になるか

| 対象 | 有効になる条件 |
| --- | --- |
| iPhone：iOS 27以降、Signal 8.37以降 | 「Block Siri AI」が既定でオン |
| Android：Signal 8.35.1以降 | AIアシスタントによる読み取りを初めて検知した際に「Screen security」がオン。設定から先にオンにもできる |

条件と設定名は[Signal公式ヘルプ](https://support.signal.org/hc/en-us/articles/11338514641306-Screen-security-blocking-Google-Gemini-and-Siri-AI)に基づきます。Androidも全端末で初めから一律オン、という変更ではありません。

## メッセージの暗号化とは別の対策

暗号化は通信を保護します。この設定は端末に表示された後の画面を対象とし、メッセージの暗号化方式は変わりません。ほかの端末で画面そのものを撮影することや、相手による情報の再共有まで防ぐものではありません。

[Windows 11版のMicrosoft Recall対策](https://signal.org/blog/signal-doesnt-recall/)は2025年5月に案内されたデスクトップ版の別の変更です。今回のスマートフォン版とは、対象も設定も区別して考えると分かりやすいです。

## よくある質問

### Androidでも最初からオンですか？

対応版ではAIアシスタントによる読み取りを初めて検知したときに有効になります。自分で先に設定を有効にすることもできます。

### 画面保護をオンにすると暗号化方式も変わりますか？

変わりません。今回の設定は端末の画面取得や対応するAIアシスタントによる画面読み取りを制限するものです。

{{< rawhtml >}}
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Androidでも最初からオンですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "対応版ではAIアシスタントによる読み取りを初めて検知したときに有効になります。自分で先に設定を有効にすることもできます。"
      }
    },
    {
      "@type": "Question",
      "name": "画面保護をオンにすると暗号化方式も変わりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "変わりません。今回の設定は端末の画面取得や対応するAIアシスタントによる画面読み取りを制限するものです。"
      }
    }
  ]
}
</script>
{{< /rawhtml >}}
