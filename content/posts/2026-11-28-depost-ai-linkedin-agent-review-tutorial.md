---
title: "Depost AIの使い方：LinkedInの下書き・承認・公開を分けて運用する"
date: 2026-11-28T00:00:00+09:00
slug: "depost-ai-linkedin-agent-review-tutorial"
description: "Depost AIでLinkedInの投稿案を作る流れ、公開前の承認、任意のMCP連携の権限と、公式の月額料金を整理します。"
categories:
  - "AI Tools"
tags:
  - "Depost AI"
  - "LinkedIn"
  - "投稿管理"
  - "MCP"
---

> 訂正：初出で紹介したPython SDK、LinkedIn APIキーの発行手順、実機での検証結果は確認できなかったため削除しました。以下は公式資料に基づく紹介です。

## 投稿案を作り、人が確認してから公開する

Depost AIは、LinkedInの過去投稿や反応を参照して、投稿案、画像、投稿カレンダーなどを作るWebサービスです。公式の運用フローでは、AIが作成した下書きを担当者が確認し、承認後に予約や公開へ進めます。[Depost AIの機能と承認フロー](https://depost.ai/)

初めて試すなら、投稿1本を下書きにするところからで十分です。

1. LinkedInとの接続を開始し、LinkedInの公式認証画面に表示されたアカウントと権限を確認します。通常の接続に、利用者が発行したLinkedIn APIキーを貼り付ける手順は案内されていません。
2. 公開して問題のない情報だけを材料にし、伝えたい要点を一つ決めて下書きを作ります。料金や実績、顧客の情報などは公開前に原資料と照合します。
3. 本文、添付画像、公開先と日時を確認し、必要な場合だけ承認・予約します。過去投稿の反応が分かっても、次の投稿で同じ成果が出るとは限りません。

## MCP連携は必要になってから

外部のAIアシスタントから使う場合、Depost AI側で発行するMCP用キーを利用します。公式案内では、キーの範囲は一つのブランドまたはワークスペースに絞れます。下書きの作成までで十分なら、予約・公開の権限は付けない方が確認しやすくなります。[公式MCPガイド](https://depost.ai/mcp)

## 料金は月払いの表示で比較する

2026年11月28日の公式料金ページでは、月払いはSoloが**59米ドル**（LinkedIn 1アカウント）、Teamが**199米ドル**（3アカウントを含む）でした。年払い、試用、追加アカウントの条件は別なので、契約前に[公式料金ページ](https://depost.ai/pricing)を確認してください。このWebサービスを使うためだけにGPUやPCを買い替える必要はありません。

## よくある質問

### LinkedInのAPIキーを自分で発行しますか？

通常の接続ではLinkedInの公式認証画面で連携を許可します。任意のMCP連携で使うキーはDepost AI側で発行するもので、LinkedInのAPIキーとは別です。

### AIが勝手にLinkedInへ投稿しますか？

通常は下書きを人が確認し、承認してから公開や予約に進みます。MCPで予約・投稿を操作するには、別途その権限を付ける必要があります。

### 料金はいくらですか？

2026年11月28日に確認した公式の月払い表示は、LinkedIn 1アカウントのSoloが59米ドル、3アカウントを含むTeamが199米ドルです。契約前に公式料金ページで最新の条件を確認してください。

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "LinkedInのAPIキーを自分で発行しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "通常の接続ではLinkedInの公式認証画面で連携を許可します。任意のMCP連携で使うキーはDepost AI側で発行するもので、LinkedInのAPIキーとは別です。"
      }
    },
    {
      "@type": "Question",
      "name": "AIが勝手にLinkedInへ投稿しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "通常は下書きを人が確認し、承認してから公開や予約に進みます。MCPで予約・投稿を操作するには、別途その権限を付ける必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "料金はいくらですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "2026年11月28日に確認した公式の月払い表示は、LinkedIn 1アカウントのSoloが59米ドル、3アカウントを含むTeamが199米ドルです。契約前に公式料金ページで最新の条件を確認してください。"
      }
    }
  ]
}
</script>
