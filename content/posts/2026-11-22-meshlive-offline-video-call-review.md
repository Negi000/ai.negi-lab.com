---
title: "MeshLiveの使い方と限界：Bluetoothで近くの端末と通話・配信"
date: 2026-11-22T00:00:00+09:00
slug: "meshlive-offline-video-call-review"
description: "MeshLiveは近くの対応端末とBluetoothで通話・配信できる無料のオープンソースアプリです。対応機種と、緊急連絡に頼れない理由を整理します。"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "MeshLive 使い方"
  - "オフライン通信"
  - "Bluetooth Mesh"
  - "P2Pビデオ通話"
---

MeshLiveは、近くの対応端末同士で、インターネットを使わずに音声・ビデオ通話やライブ配信を試せるアプリです。[開発元](https://meshlive.github.io/)によると、アカウントやSIMは不要で、近くの端末が配信を中継します。アプリは無料で、コードは GPL-3.0-or-later で公開されています。

**安全を左右する場面ではMeshLiveに頼らないでください。** 開発元は独立したセキュリティ監査を受けていないと明記しています。災害時や登山で、緊急通報や事前に決めた連絡手段の代わりにするものではありません。

## 試すなら、対応端末2台で

1. [公式のダウンロード案内](https://meshlive.github.io/#download)から機種に合った版を選びます。11月22日の確認時点では iOS 17以降、Android 10以降、Bluetooth対応のWindows 11が案内されています。AndroidとWindowsはベータです。Mac版は公開予定とされています。
2. 近くに置いた2台でアプリを開き、公式ガイドに従ってBluetoothや通話に必要な権限を確認します。個人情報を含まない会話で通話を試し、配信を試すなら周りの人が映らないようにします。
3. 使いたい場所で距離や遮蔽物を変え、接続や音声がどう変わるか確かめます。一度つながった距離は、別の端末や場所でも届く保証ではありません。

## 通話と配信で違うプライバシー

開発元は通話をエンドツーエンドで暗号化すると説明しています。一方、通話相手やライブ配信の視聴者には、発信元が分かる場合があります。サーバーを介さないことを、匿名性や安全性の保証と考えないでください。

本記事は開発元の公開資料に基づく紹介です。端末ごとの画質、遅延、到達距離は独自に実測していません。

## よくある質問

### どこからインストールしますか？

開発元のダウンロード案内から、端末に対応する版を選びます。AndroidとWindowsは確認時点でベータです。

### 緊急連絡に使えますか？

安全を左右する連絡では頼らないでください。独立したセキュリティ監査を受けていないと開発元が明記しています。

### 到達距離は保証されていますか？

保証されていません。端末や遮蔽物など利用環境が変わると、到達距離や接続状況も変わります。

{{< rawhtml >}}
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "どこからインストールしますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "開発元のダウンロード案内から、端末に対応する版を選びます。AndroidとWindowsは確認時点でベータです。"
      }
    },
    {
      "@type": "Question",
      "name": "緊急連絡に使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "安全を左右する連絡では頼らないでください。独立したセキュリティ監査を受けていないと開発元が明記しています。"
      }
    },
    {
      "@type": "Question",
      "name": "到達距離は保証されていますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "保証されていません。端末や遮蔽物など利用環境が変わると、到達距離や接続状況も変わります。"
      }
    }
  ]
}
</script>
{{< /rawhtml >}}
