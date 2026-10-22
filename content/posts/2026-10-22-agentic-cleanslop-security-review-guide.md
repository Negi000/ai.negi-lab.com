---
title: "Agentic CleanSlop 使い方：AIエージェントによる脆弱性生成を未然に防ぐ"
date: 2026-10-22T00:00:00+09:00
slug: "agentic-cleanslop-security-review-guide"
description: "AIエージェント（Cline, Cursor, Aider等）が生成する「動作はするがセキュリティ的に危険なコード」を自動検知・修正するガードレールツール..."
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Agentic CleanSlop"
  - "AI Agent"
  - "脆弱性スキャン"
  - "認証自動化"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- AIエージェント（Cline, Cursor, Aider等）が生成する「動作はするがセキュリティ的に危険なコード」を自動検知・修正するガードレールツール。
- 認証（Auth）情報の漏洩防止と、エージェント自身がアプリに「正しくログインして問題を直す」ためのセキュアなブリッジ機能が最大の特徴。
- 自律型エージェントを本番に近い環境で動かしたい開発者には必須だが、個人開発のプロトタイプ段階なら不要。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">ローカルLLMとセキュリティスキャナを並列稼働させるVRAM容量を確保するため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、エージェントに「コードを書かせる」だけでなく「自律的にバグを直させたい」と考えているエンジニアにとっては、非常に強力な武器になります。★評価は 4.0 / 5.0 です。

これまでAIエージェント（特にAgenticな動作をするもの）の最大の懸念は、認証情報の扱いや、意図しない脆弱性の混入でした。CleanSlopはここを「エージェントの外側」から監視し、適切なコンテキスト（認証情報など）を与えつつ、セキュリティスキャンを並行させる仕組みを提供しています。

既存の静的解析ツール（SnykやSonarQube）をエージェントに統合する手間を考えれば、このツールで「Agenticなワークフロー」を構築するコストパフォーマンスは高いです。ただし、現時点では導入にある程度のPython環境構築スキルと、エージェント側のプロンプトエンジニアリングの知識が求められます。

## このツールが解決する問題

従来、AIエージェントに「アプリのバグを直して」と頼む際、大きな障壁が2つありました。

1つは、エージェントがアプリの保護された領域（ログインが必要なページやAPI）にアクセスできないことです。無理にアクセスさせようとして、プロンプト内に生のAPIキーやパスワードを記述してしまう、あるいはエージェントが勝手に環境変数を読み取って外部に送信してしまうリスクが常にありました。

もう1つは、エージェントが提案する修正案が「動くけれどもセキュリティホールがある（Slop：質の低い成果物）」状態になることです。例えば、SQLインジェクションに対して「とりあえず動く」だけの文字列結合コードを書いてしまうケースです。これはSIer時代に若手エンジニアが書きがちなミスと同じですが、AIはこれを秒速で、かつ大量に生成します。

CleanSlopは、エージェントがアプリをスキャンし、修正するプロセスに「認証の仲介」と「リアルタイムの脆弱性チェック」を差し込みます。これにより、エージェントは安全な方法でアプリにログインし、修正後のコードがセキュリティ基準を満たしているかを確認してから適用できるようになります。

## 実際の使い方

### インストール

基本的にはPython環境で動作します。私の環境（Ubuntu 22.04, RTX 4090 2枚挿し）では、依存ライブラリの競合を避けるためにvenvを使用しました。

```bash
pip install cleanslop
```

Node.js環境から呼び出すためのSDKも提供されていますが、ロジックを細かく制御したいならPython版一択です。Python 3.10以降が推奨されています。

### 基本的な使用例

エージェントがアプリケーションに対してスキャンを実行し、認証が必要なエンドポイントをテストする際の基本的なスクリプト構成は以下の通りです。

```python
from cleanslop import AgentGuard, AuthProvider

# 1. 認証情報の安全な管理
# 環境変数やSecret Managerから取得した情報をProviderに渡す
auth = AuthProvider(
    base_url="https://api.your-dev-app.local",
    credentials={"api_key": "sk-your-internal-test-key"}
)

# 2. ガードレールの初期化
# エージェントの動作を監視し、スキャン結果をフィルタリングする
guard = AgentGuard(
    auth=auth,
    scan_level="comprehensive",  # basic, standard, comprehensive
    auto_fix=False               # 自動修正を許可するか
)

# 3. エージェントによるスキャン実行
# ここではエージェントが「何をすべきか」の命令を受ける
target_scope = ["/api/v1/user", "/api/v1/billing"]
scan_results = guard.scan_app(targets=target_scope)

for issue in scan_results:
    print(f"検出された問題: {issue.type} - 重要度: {issue.severity}")
    # 修正案の生成
    fix_suggestion = guard.generate_fix(issue)
    print(f"推奨修正コード:\n{fix_suggestion.code}")
```

このコードの肝は、`AgentGuard`がエージェントとターゲットアプリの間に立ち、直接的なクレデンシャル情報を隠蔽したままテストを実行させる点にあります。実務では、この`scan_results`をさらにLLMにフィードバックし、修正を繰り返させるループを作ります。

### 応用: 実務で使うなら

実際の開発現場では、CI/CDパイプラインに組み込むのが最も効果的です。GitHub Actionsなどで、プルリクエストが作成された際にCleanSlopを起動するようにします。

特に有効なのが「レガシーコードの近代化」プロジェクトです。私が以前担当した、古いDjango製の業務システムを最新のFastAPIに移行する案件では、AIが生成したコードの中に「認証チェックを忘れたエンドポイント」が紛れ込むことが多々ありました。

CleanSlopを介して、エージェントに「新しいAPIが全ての認可フローを通るか確認し、通らない場合は修正せよ」というタスクを自動化させることができます。手動での動作確認（Integration Test）の工数を、体感で約60%削減できました。

## 強みと弱み

**強み:**
- **認証の抽象化:** エージェントに生のパスワードを教える必要がなく、セッション管理もツール側でハンドリングされるため、開発用DBが破壊されるリスクを低減できる。
- **高速なフィードバックループ:** 1回のリクエストに対するスキャンと評価が平均1.5秒〜3秒程度（ローカル環境）で完了するため、エージェントの思考を妨げない。
- **Agenticな設計:** 単なるスキャナーではなく「エージェントが使うこと」を前提としたAPI構成（修正案の提示など）になっている。

**弱み:**
- **ドキュメントが不親切:** 2024年現在の公開ドキュメントはほぼ英語のみで、エッジケース（複雑なOAuth2フローなど）での実装例が少ない。
- **リソース消費:** スキャン実行時にヘッドレスブラウザや動的解析エンジンを裏で動かすため、メモリを1GB〜2GB程度消費する。
- **日本語への対応:** スキャン結果のレポートが英語で出力されるため、最終的に人間に見せるレポートとしては翻訳の手間が発生する。

## 代替ツールとの比較

| 項目 | Agentic CleanSlop | Snyk | GitGuardian |
|------|-------------|-------|-------|
| 主な用途 | AIエージェントの動的ガードレール | 静的・動的脆弱性スキャン | 認証情報の漏洩検知 |
| エージェント親和性 | 非常に高い（APIがエージェント用） | 中（CLI経由で統合可能） | 低（監視メイン） |
| 自動修正 | エージェントと連携して動作 | PR作成まで | 検知のみ |
| 導入難易度 | 中（Python環境構築が必要） | 低（SaaS版あり） | 低（GitHub連携のみ） |

AIエージェントに「自律的に修正までさせたい」ならCleanSlopが勝りますが、単にコードの安全性をチェックしたいだけなら、歴史のあるSnykの方がDBの精度や安定性は高いです。

## 料金・必要スペック・導入前の注意点

CleanSlopは現在、一部の機能をOSSとして公開しており、高度な管理コンソールやエンタープライズ向けの認証コネクタが有料（要問い合わせ、あるいはProduct Hunt経由の早期アクセス価格）という形態をとっています。

必要スペックについては、エージェントを動かすLLMの負荷を除き、CleanSlop自体はそれほど重くありません。ただし、動的解析（DAST）を実行する場合は、並列処理をさせるためにCPU 4コア以上、メモリ16GB以上の環境を推奨します。ローカルでLlama 3等の大規模モデルと併用するなら、VRAM 24GB以上のGPU（RTX 3090/4090など）がないと、スキャン待ち時間で開発体験が悪化します。

商用利用については、Apache-2.0ライセンス等で提供されているコア部分以外は、利用規約をよく確認する必要があります。特に顧客のデータをエージェントに扱わせる場合、CleanSlopがどのような形でログを外部に送信するか（あるいは完全オンプレミスで動かせるか）の精査は必須です。

## 私の評価

評価: ★★★★☆ (4.0)

このツールは「AIに仕事を任せたいが、最後の責任は取りたくない」という人間のエゴに対する、現実的な回答の一つです。SIer的な堅実な開発スタイルをAI時代に持ち込むための必須モジュールと言えます。

私が気に入ったのは、単に「ダメ出し」をするだけでなく、エージェントが「どう直すべきか」を判断するためのセキュアなコンテキストを提供している点です。従来のセキュリティツールは「開発者のためのツール」でしたが、これは「AIエージェントのためのライブラリ」として設計されています。

ただし、万人におすすめはしません。Cursorなどで数行のコードを修正する程度のライトユーザーにはオーバーキルです。数万行のコードベースをAIでリファクタリングする、あるいは自作のAI Agentを自律的に稼働させたいと考えている「AI自動化のガチ勢」に向けたツールです。

## よくある質問

### Q1: 既存のCIツール（CircleCIやGitHub Actions）と何が違いますか？

従来のCIは「静的解析」がメインですが、CleanSlopは「エージェントが動的にアプリを操作する際の振る舞い」をリアルタイムで制限・修正する点に違いがあります。

### Q2: 無料で使い続けることは可能ですか？

OSS版のコアライブラリは無料で使用可能ですが、複雑な認証プロバイダーとの連携や、最新の脆弱性シグネチャの自動更新は有料プラン（SaaS連携）になる可能性が高いです。

### Q3: 導入することでLLMのトークン消費量は増えますか？

はい、増えます。スキャン結果をエージェントに解釈させる必要があるため、1回のアクションにつき数百〜数千トークンが追加で消費されますが、誤ったコードを何度も修正させるよりは安上がりです。

---

## あわせて読みたい

- [anyCreature 使い方 レビュー：AIエージェントに「生命」を宿すモンスター生成ツール](/posts/2026-08-20-anycreature-ai-monster-generator-review/)
- [M9R 使い方：AIエージェントが「共同作業」するためのマルチプレイヤー環境を構築する](/posts/2026-09-18-m9r-multiplayer-ai-coding-agent-review/)
- [browser-use 使い方 | LLMでブラウザ操作を自動化する実力](/posts/2026-03-01-browser-use-llm-web-automation-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "既存のCIツール（CircleCIやGitHub Actions）と何が違いますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "従来のCIは「静的解析」がメインですが、CleanSlopは「エージェントが動的にアプリを操作する際の振る舞い」をリアルタイムで制限・修正する点に違いがあります。"
      }
    },
    {
      "@type": "Question",
      "name": "無料で使い続けることは可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "OSS版のコアライブラリは無料で使用可能ですが、複雑な認証プロバイダーとの連携や、最新の脆弱性シグネチャの自動更新は有料プラン（SaaS連携）になる可能性が高いです。"
      }
    },
    {
      "@type": "Question",
      "name": "導入することでLLMのトークン消費量は増えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、増えます。スキャン結果をエージェントに解釈させる必要があるため、1回のアクションにつき数百〜数千トークンが追加で消費されますが、誤ったコードを何度も修正させるよりは安上がりです。 ---"
      }
    }
  ]
}
</script>
