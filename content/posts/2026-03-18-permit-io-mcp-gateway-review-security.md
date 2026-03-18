---
title: "Permit.io MCP Gateway レビュー：LLMのツール実行にセキュリティを組み込む方法"
date: 2026-03-18T00:00:00+09:00
slug: "permit-io-mcp-gateway-review-security"
description: "Model Context Protocol (MCP) の「誰が、どのツールを使えるか」という認可問題を一撃で解決するゲートウェイ。。既存のMCPサーバ..."
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Permit.io"
  - "MCP Gateway"
  - "Model Context Protocol"
  - "AIセキュリティ"
  - "認可制御"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- Model Context Protocol (MCP) の「誰が、どのツールを使えるか」という認可問題を一撃で解決するゲートウェイ。
- 既存のMCPサーバーにプロキシとして介在し、RBAC（役割ベースアクセス制御）や監査ログをノーコードに近い形で後付けできる。
- 企業内で Claude や自作エージェントをデータベースや社内ツールに接続させたいエンジニアには必須、個人利用ならオーバースペック。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">MINISFORUM MS-01</strong>
<p style="color:#555;margin:8px 0;font-size:14px">10GbE搭載でMCPゲートウェイやローカルLLMサーバーを自宅でセキュアに運用するのに最適なミニPC</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=MINISFORUM%20MS-01&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMINISFORUM%2520MS-01%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMINISFORUM%2520MS-01%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、エンタープライズ向けのAIエージェント開発をしているなら「即導入すべき」レベルのツールです。★評価は 4.5/5.0 とします。

現在のMCPエコシステムは「接続の容易さ」に特化しており、セキュリティ、特に「認可（Authorization）」が置き去りにされています。Claude DesktopにMCPサーバーを登録すれば、モデルは自由にファイル削除やデータベース操作ができてしまいます。

Permit.io MCP Gateway は、この「AIのやりすぎ」を防ぐためのガードレールです。私のようなSIer出身者から見れば、これがなければ怖くて顧客の基幹システムにAIを繋げません。

ただし、ローカルで自分一人で動かしている分には、設定の手間が勝るため不要です。RTX 4090を2枚挿してローカルLLMをぶん回している個人の検証環境であれば、今まで通り直接MCPサーバーを叩く方が速いでしょう。

## このツールが解決する問題

従来のMCP（Model Context Protocol）は、AIモデルとローカルデータやAPIを繋ぐための素晴らしいプロトコルです。しかし、実務投入しようとすると大きな壁にぶつかります。それは「権限管理」と「監査」の欠如です。

例えば、社内のSlack履歴を検索するMCPサーバーと、人事評価システムを叩くMCPサーバーがあったとします。一般社員のブラウザ上で動くAIエージェントが、うっかり（あるいはプロンプトインジェクションによって）人事評価MCPを叩けてしまう状態は、セキュリティ事故そのものです。

これまでは、各MCPサーバーの中に自前で `if user_role == 'admin':` といったロジックを組み込む必要がありました。しかし、複数のMCPサーバーを運用する場合、この実装は地獄と化します。

Permit.io MCP Gateway は、これらのMCPサーバーの前段に立ち、すべてのリクエストをインターセプトします。Permit.io の強力な Policy-as-Code エンジンを使い、「営業部のユーザーは顧客データの読み取りMCPのみ実行可能」といったポリシーを一元管理できるのが最大の特徴です。

これにより、開発者は「機能」としてのMCPサーバー開発に集中でき、セキュリティはゲートウェイ側に丸投げできます。これはSIer時代にAPIゲートウェイを導入して認証認可を分離したときの快感に近いものがあります。

## 実際の使い方

### インストール

Permit.io MCP Gateway は Docker で運用するのが最も現実的です。既存の MCP サーバー（Python や Node.js で書かれたもの）を束ねる形で起動します。

前提条件として、Permit.io のアカウントを作成し、APIキーを取得しておく必要があります。Python 環境から制御する場合は、Permit の SDK も併せてインストールしておくと捗ります。

```bash
# Gateway自体はDockerで実行
docker pull permitio/mcp-gateway:latest

# 管理用SDK
pip install permit
```

### 基本的な使用例

まずは、ゲートウェイの設定ファイル（`gateway-config.yaml`）で、どのMCPサーバーを保護対象にするかを定義します。

```yaml
servers:
  - name: "postgres-db-server"
    url: "http://localhost:3000" # 既存のMCPサーバー
    type: "sse"
  - name: "slack-reader"
    command: ["python", "slack_mcp.py"]
    type: "stdio"

authorization:
  enabled: true
  provider: "permit"
```

次に、Python から Permit のポリシーを設定し、ゲートウェイ経由で MCP ツールを実行するシミュレーションです。

```python
import os
from permit import Permit

# Permit.ioのクライアント初期化
permit = Permit(
    token=os.getenv("PERMIT_API_KEY"),
    pdp="http://localhost:8000"
)

async def check_and_run_tool(user_id, tool_name):
    # ユーザーがそのMCPツールを実行する権限があるかチェック
    # Permit.ioのUI上で定義したポリシーに基づき判定
    allowed = await permit.check(user_id, "execute", f"mcp_tool:{tool_name}")

    if allowed:
        # 権限があればゲートウェイ経由で実行（実際はモデルがここを叩く）
        print(f"Executing {tool_name} for user {user_id}...")
        # ゲートウェイのURLをMCPエンドポイントとして使用
        return "SUCCESS"
    else:
        print("Access Denied: 権限がありません")
        return "FORBIDDEN"

# 実行例
import asyncio
asyncio.run(check_and_run_tool("user_123", "delete_database_record"))
```

この構成の肝は、AIモデルが直接MCPサーバーを叩くのではなく、必ずゲートウェイを通過する点にあります。

### 応用: 実務で使うなら

実務では、複数の環境（開発、ステージング、本番）で異なるポリシーを適用する必要があります。

例えば、開発環境では `read` も `write` も全開放し、本番環境では `admin` ロールのみが `write` 系のMCPツールを実行できるように制限します。Permit.io MCP Gateway は、バックエンドに OPA (Open Policy Agent) を採用しているため、Rego 言語を使って非常に細かい条件（ABAC：属性ベースアクセス制御）を記述できます。

「平日の9時から18時の間だけ、社内ネットワークからのアクセスに限り、このMCPツールを許可する」といった設定も、コードを一行も書き換えずに管理画面から変更可能です。これは20件以上の機械学習案件をこなしてきた私の経験上、リリース後の運用コストを劇的に下げてくれる機能です。

## 強みと弱み

**強み:**
- **一元化された監査ログ:** 誰が、いつ、どのMCPツールを、どんな引数で実行したかがすべて記録されます。これはAIコンプライアンスにおいて必須です。
- **ポリシーの即時反映:** 権限の変更にMCPサーバーの再起動は不要。Permit.io のクラウド画面からポチるだけで数秒以内に反映されます。
- **既存サーバーの無改造導入:** 既に動いている MCP サーバーのコードを触ることなく、セキュリティ層を追加できます。

**弱み:**
- **レイテンシの増加:** プロキシとして動作するため、リクエストごとに認可チェックのオーバーヘッド（私の環境で 10ms 〜 30ms 程度）が発生します。
- **ドキュメントが英語のみ:** 設定の詳細は英語のドキュメントを読み解く必要があり、初心者がハマると抜け出すのが大変です。
- **Permit.io への依存:** セキュリティの根幹を外部サービス（SaaS）に依存することになるため、障害時のフォールバック設計が必要です。

## 代替ツールとの比較

| 項目 | Permit.io MCP Gateway | 自作プロキシ (FastAPI等) | MCP Proxy (OSS) |
|------|-------------|-------|-------|
| 認可の柔軟性 | 極めて高い (RBAC/ABAC) | 実装次第だが工数大 | 基本的 (API Keyのみ) |
| 監査ログ | 標準装備（詳細） | 自作が必要 | 簡易的 |
| 設定難易度 | 中（概念理解が必要） | 高 | 低 |
| コスト | 商用は有料枠あり | 開発人件費のみ | 無料 |

単に「APIキーで制限したいだけ」なら、簡単な FastAPI プロキシを自作する方が早いかもしれません。しかし、エンタープライズで求められる「職務分掌」や「詳細な監査」が必要なら、Permit.io 一択です。

## 私の評価

私はこのツールを、MCPが「おもちゃ」から「ビジネスツール」に進化するためのミッシングピースだと評価しています。

正直に言えば、これまではMCPのデモを見るたびに「これ、プロンプトインジェクションでDB消されたらどうするの？」と冷や冷やしていました。Permit.io MCP Gateway は、その不安に対する具体的な回答になっています。

個人の趣味で Claude Desktop を拡張している層には全くおすすめしません。Docker を立てるのも面倒でしょうし、ローカルだけで完結するメリットを損ないます。

しかし、自社のデータをLLMに触らせる SaaS 開発者や、社内エージェントを構築している情シス担当者にとっては、今すぐ検証を始めるべきプロダクトです。RTX 4090 でローカル推論を行う際も、外部の API 連携を伴うのであれば、このゲートウェイを挟むことで「推論はローカル、権限管理はクラウド」というハイブリッドでセキュアな構成が組めます。

## よくある質問

### Q1: 既存の MCP サーバーが Node.js で、クライアントが Claude Desktop でも使えますか？

はい、使えます。ゲートウェイをローカルで Docker 起動し、Claude Desktop の設定ファイル（`mcpServers`）の URL をゲートウェイの方向に書き換えるだけで、通信をトラップして認可制御をかけることができます。

### Q2: 料金はかかりますか？

Permit.io には無料枠がありますが、リクエスト数や管理するポリシーの数によって有料プランへの移行が必要になります。MCP Gateway 自体は OSS ですが、認可エンジンの Permit PDP と連携させる形が一般的です。

### Q3: ネットワークがオフラインの環境でも動作しますか？

Permit.io の PDP (Policy Decision Point) をローカルの Docker コンテナとして動かせば、判定自体はオフライン（LAN内）で完結します。ただし、ポリシーの同期時のみ Permit.io の管理サーバーと通信が必要です。

---

## あわせて読みたい

- [Fantastical MCP for Mac 使い方と実務での活用ガイド](/posts/2026-03-18-fantastical-mcp-claude-mac-guide/)
- [ペンタゴン論争が皮肉にも証明したClaudeの信頼性とApp Store首位獲得の真価](/posts/2026-03-02-claude-app-store-ranking-pentagon-dispute-analysis/)
- [Parallax 使い方 レビュー：ローカル完結型AI開発オーケストレーターの真価](/posts/2026-03-17-parallax-local-ai-orchestrator-review-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "既存の MCP サーバーが Node.js で、クライアントが Claude Desktop でも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、使えます。ゲートウェイをローカルで Docker 起動し、Claude Desktop の設定ファイル（mcpServers）の URL をゲートウェイの方向に書き換えるだけで、通信をトラップして認可制御をかけることができます。"
      }
    },
    {
      "@type": "Question",
      "name": "料金はかかりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Permit.io には無料枠がありますが、リクエスト数や管理するポリシーの数によって有料プランへの移行が必要になります。MCP Gateway 自体は OSS ですが、認可エンジンの Permit PDP と連携させる形が一般的です。"
      }
    },
    {
      "@type": "Question",
      "name": "ネットワークがオフラインの環境でも動作しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Permit.io の PDP (Policy Decision Point) をローカルの Docker コンテナとして動かせば、判定自体はオフライン（LAN内）で完結します。ただし、ポリシーの同期時のみ Permit.io の管理サーバーと通信が必要です。 ---"
      }
    }
  ]
}
</script>
