---
title: "ExtraOrbital入門：AIエージェント用のDBとストレージをまとめて用意する"
date: 2026-11-27T00:00:00+09:00
slug: "extraorbital-ai-agent-infrastructure-review"
description: "ExtraOrbitalの公式資料をもとに、CLIでの導入、OpenRouterゲートウェイ、無料枠の保持条件と有料プランを整理します。"
cover:
  image: "/images/posts/2026-11-27-extraorbital-ai-agent-infrastructure-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "ExtraOrbital"
  - "AI Agent"
  - "インフラ自動化"
  - "サンドボックス"
---

ExtraOrbital は、AI エージェントの試作に必要なデータベースやストレージを、プロジェクト単位でまとめて用意するクラウドサービスです。何を用意するかを CLI で確認し、作成後は Postgres や S3 などの標準クライアントで接続できます。この記事は 2026 年 11 月 27 日に確認した公式資料に基づく紹介です。実機の速度測定や負荷試験は行っていません。

## 何を任せられるか

たとえば、エージェントが作ったレポートを S3 互換ストレージに置き、実行状態を Postgres に記録するデモなら、別々の管理画面でリソースを作る手間を減らせます。Redis やベクトルストアなども選べますが、エージェントの記憶やアクセス権が自動で設計されるわけではありません。

入口は [CLI](https://extraorbital.dev/docs/cli)、[ホスト型 MCP](https://extraorbital.dev/docs/mcp)、[REST API](https://extraorbital.dev/docs/api) です。リソースを用意する操作と、アプリがそのリソースを使う操作は別です。アプリ側を標準クライアントに寄せておくと、接続先を後で替えやすくなります。

## まずは作成予定だけを確認する

CLI には Node.js 20 以降が必要です。対象のプロジェクトを開き、`.env.example` などの定義から何が検出されるかを確認できます。

```bash
npx extraorbital provision . --dry-run
```

公式 CLI では `--dry-run` は予定を表示するだけで、リソースを作成しません。実際に作成すると接続情報が環境ファイルに書かれるので、`.env` をコミットしたり、ログやチャットに貼ったりしないようにします。初回の流れは [公式クイックスタート](https://extraorbital.dev/docs/quickstart) を参照してください。

## AI Gateway と外部サービスの認証は別

[公式 AI Gateway](https://extraorbital.dev/docs/resources/ai-gateway) は、OpenRouter のエンドポイントとキーを払い出す機能です。OpenAI 互換クライアントで使えますが、OpenAI から直接発行されるキーではありません。Slack や GitHub などの外部ツールは、それぞれのサービスで権限を設定してください。

## 料金とデータ保持

| プラン | 公式料金 | データ保持の注意点 |
|---|---|---|
| Free | $0。リソースごとの無料枠はアカウント全体で共有 | バックアップ・復元なし。未使用のリソースは 30 日で削除。バケット内ファイルにも別の保持条件あり |
| Pay-as-you-go | 月 $20／メンバー。リソース使用料は別 | 定期バックアップ・復元あり。未使用によるリソース失効なし |

[公式料金表](https://extraorbital.dev/pricing) と使うリソースの個別ページを両方確認してください。Free のバケットにはアップロード後 30 日の削除条件が掲載されています。リソースを日常的に使っていても、バケット内ファイルの保持が延びると考えない方が安全です。

## 試すなら、消えてもよいデータから

まずはサンプルデータで、接続、読み書き、エクスポートまで一周させるのがおすすめです。長期運用を考えるなら、料金だけでなく、保存先、復元手順、障害時の切替にかかる時間も比較してください。無料枠を本番データの唯一の置き場所にはしないでください。

## よくある質問

### Python SDK はありますか？

公式の導入手順は Node.js 20 以降の CLI、ホスト型 MCP、REST API です。Python アプリからデータを読み書きするときは、Postgres や S3 など、選んだリソースに対応するライブラリを使います。

### 無料枠に本番データを置いてもよいですか？

消えてもよい試作データに限るのが無難です。無料枠にはバックアップと復元がなく、未使用リソースとバケット内のファイルにはそれぞれ削除条件があります。

### AI Gateway は Slack や GitHub のキーも扱えますか？

AI Gateway が発行するのは OpenRouter 経由でモデルを使うためのキーです。Slack、GitHub、Google 検索のキーをまとめて代理利用する機能ではありません。

{{< rawhtml >}}
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Python SDK はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "公式の導入手順は Node.js 20 以降の CLI、ホスト型 MCP、REST API です。Python アプリからデータを読み書きするときは、Postgres や S3 など、選んだリソースに対応するライブラリを使います。"
      }
    },
    {
      "@type": "Question",
      "name": "無料枠に本番データを置いてもよいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "消えてもよい試作データに限るのが無難です。無料枠にはバックアップと復元がなく、未使用リソースとバケット内のファイルにはそれぞれ削除条件があります。"
      }
    },
    {
      "@type": "Question",
      "name": "AI Gateway は Slack や GitHub のキーも扱えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "AI Gateway が発行するのは OpenRouter 経由でモデルを使うためのキーです。Slack、GitHub、Google 検索のキーをまとめて代理利用する機能ではありません。"
      }
    }
  ]
}
</script>
{{< /rawhtml >}}
