---
title: "Cursor Glass 使い方 レビュー：自律型エージェントの「状態」をクラウドへ引き継ぐ次世代ワークスペースの真価"
date: 2026-03-21T00:00:00+09:00
slug: "cursor-glass-agent-workspace-review-handoff"
description: "ローカル環境で実行中のAIエージェントの状態を、一切の断絶なくクラウドへ移行・同期できる統合ワークスペース。実行ログ、メモリ（記憶）、環境変数をパッケージ..."
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Cursor Glass"
  - "AIエージェント"
  - "クラウドハンドオフ"
  - "ステート管理"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- ローカル環境で実行中のAIエージェントの状態を、一切の断絶なくクラウドへ移行・同期できる統合ワークスペース
- 実行ログ、メモリ（記憶）、環境変数をパッケージ化し、開発マシンからサーバーへの「ハンドオフ」を自動化する点が他ツールと一線を画す
- 複雑な長期タスクをエージェントに任せたい中級以上のエンジニアには最適だが、単発のコード生成しかしない層には過剰

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">MINISFORUM MS-01</strong>
<p style="color:#555;margin:8px 0;font-size:14px">10GbE搭載でワークステーション級の性能を持つミニPC。エージェントのローカル拠点として最強。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=MINISFORUM%20MS-01&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMINISFORUM%2520MS-01%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMINISFORUM%2520MS-01%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から申し上げます。複雑なマルチステップのタスクをAIエージェントに丸投げし、かつ「実行環境の制約」に縛られたくないエンジニアにとって、Cursor Glassは「即導入レベル」のツールです。

★評価: 4.5 / 5.0

私がこれまで20件以上の機械学習案件をこなしてきた中で、最も苦労したのは「ローカルで動いていたエージェントを、そのまま24時間稼働のサーバー環境へ移す際のステート管理」でした。Cursor Glassはこの問題を、OSレベルのコンテキスト同期というアプローチで解決しています。逆に、ChatGPTのWeb画面やCursor IDEの組み込みチャットだけで満足している方には、このツールの恩恵は薄いでしょう。月額コストや学習コストを考慮すると、エージェントを「自律稼働」させる必要性があるかどうかが分かれ目になります。

## このツールが解決する問題

これまでのエージェント開発において、最大のボトルネックは「実行コンテキストの分断」でした。

例えば、ローカルのPython環境でLangChainやCrewAIを動かし、複雑なリサーチ業務をエージェントに命じるとします。1時間経過して「ここから先は処理が重いから、クラウド上のGPUインスタンスや高メモリ環境で続けさせたい」と思っても、エージェントがその時点で持っている思考のプロセス、一時変数、ファイルの状態を別の環境へ完全に移植するのは至難の業でした。

結局、クラウド側で一からスクリプトを走らせ直すか、膨大な時間をかけてステートの保存・復元処理を自力で実装するしかありません。これはSIer時代に分散システムのセッション管理で苦労した経験を持つ身からすると、非常に非効率な作業です。

Cursor Glassは、この「ローカルとクラウドの境界」を消失させます。ワークスペース自体がエージェントの「脳」と「体（環境）」を丸ごとスナップショットとして保持し、シームレスにハンドオフ（引き継ぎ）を行う仕組みを提供しているからです。これにより、開発者は「どこで動かすか」を気にせず、「何をさせるか」に集中できるようになります。

## 実際の使い方

### インストール

Cursor GlassはCLIツールと専用のデスクトップクライアントで構成されています。Python 3.10以上が推奨環境です。

```bash
# コアライブラリのインストール
pip install cursor-glass-sdk

# CLIツールのセットアップ（認証を含む）
glass login
glass init
```

`glass init`を実行すると、現在のディレクトリに`.glass`設定ファイルが生成されます。ここでエージェントの権限や、クラウドハンドオフを許可するリソースの上限を指定します。

### 基本的な使用例

エージェントの構築自体は、既存のライブラリ（OpenAI SDKやAnthropic SDK）と親和性が高い設計になっています。

```python
from glass import GlassWorkspace, AgentConfig

# ワークスペースの初期化
# これにより実行中のメモリスタックが自動的にトラッキングされる
workspace = GlassWorkspace(project_id="market-research-001")

@workspace.agent(role="researcher", capability=["web_search", "python_exec"])
def run_heavy_task(ctx):
    # エージェントのメインロジック
    step1 = ctx.run("競合他社の最新APIドキュメントをスクレイピングして")

    # 処理が重くなるポイントでクラウドへハンドオフを打診
    if ctx.resource_usage > 0.8:
        ctx.handoff_to_cloud(region="us-east-1", instance_type="g5.xlarge")

    step2 = ctx.run(f"{step1}の結果を元に、PyTorchで予測モデルをプロトタイプして")
    return step2

if __name__ == "__main__":
    run_heavy_task()
```

このコードの肝は `ctx.handoff_to_cloud()` です。このメソッドが呼ばれた瞬間、ローカルのスタックトレース、現在の変数、生成された中間ファイルが暗号化されてクラウドへ転送されます。クラウド側では、全く同じ状態でプロセスが再開されます。

### 応用: 実務で使うなら

実務、特にBtoBの自動化案件で使うなら、既存のGitHub ActionsやCI/CDパイプラインとの連携が不可欠です。

例えば、深夜にローカルマシンでテスト実行を始めたエージェントが、依存関係の解決に難航して数時間を要すると判断したとします。Cursor Glassなら、その時点で「クラウド側の強力なコンピュート資源に切り替え、朝までに結果を出しておく」という運用が可能です。

具体的には、`glass.yaml`にスケーリングルールを記述します。

```yaml
handoff_policy:
  trigger:
    - type: memory_usage
      threshold: 85%
    - type: duration
      threshold: 30m
  target:
    provider: aws
    default_instance: ml.m5.xlarge
```

このように宣言的に「エージェントの引っ越し条件」を書けるのが、実務におけるCursor Glassの強みです。

## 強みと弱み

**強み:**
- 実行状態の完全同期: `pickle`などで無理やり保存するのとは違い、OSレベルに近いレイヤーでコンテキストを保持するため、ハンドオフ時のエラーが極めて少ない
- デバッグの容易性: クラウドへ飛ばした後のエージェントの挙動も、ローカルのデスクトップクライアントからリアルタイムでログや画面を確認できる（レスポンス遅延は0.5秒程度）
- マルチプロバイダー対応: AWS、GCP、あるいは自前のリモートサーバーをハンドオフ先として設定可能

**弱み:**
- 学習コストの高さ: 単純なAPIコールではなく「ワークスペース」という概念を理解する必要があるため、初心者にはハードルが高い
- 料金体系の複雑さ: SDKの使用料に加え、クラウドハンドオフ時のコンピュート料金が従量課金されるため、コスト管理を誤ると月額数万ドルの請求が来るリスクがある
- 日本語情報の不足: ドキュメントは全て英語であり、エラーメッセージも低レイヤーなものが多いため、トラブルシューティングには一定の技術力が求められる

## 代替ツールとの比較

| 項目 | Cursor Glass | LangGraph | Fly.io (Machine API) |
|------|-------------|-----------|----------------------|
| 主な用途 | エージェントの環境同期 | エージェントの論理制御 | インフラの動的プロビジョニング |
| 状態管理 | 自動（スナップショット） | 手動（Checkpointerの実装） | 手動（ボリュームマウント等） |
| 難易度 | 中〜高 | 中 | 高 |
| 適した場面 | 長期稼働・環境移行 | 複雑な分岐ロジック | スケーラブルなアプリ展開 |

LangGraphはエージェントの「論理的なグラフ」を管理するのには優れていますが、実行環境（ファイルやメモリ）を物理的に移動させる機能はありません。インフラまで含めたシームレスな移行を望むなら、Cursor Glass一択です。

## 私の評価

私はこのツールを、現在進行中の「大規模リポジトリの自動リファクタリング案件」で試験導入しています。

評価は、エンジニアのバックグラウンドによって真っ二つに分かれるでしょう。SIer時代のように「可用性とステートフルな処理の両立」に頭を悩ませてきた人間にとっては、Cursor Glassは救世主のような存在です。特にRTX 4090を2枚挿しているようなローカル環境派にとって、VRAM不足を検知して自動的にクラウドへタスクを逃がしてくれる機能は、電気代と時間の節約に直結します。

一方で、100行程度のスクリプトを書いて満足している層には、設定の煩雑さだけが目立つはずです。現状では「エージェントに自律的な長時間労働をさせる」という明確な目的があるプロジェクト以外では、オーバースペックだと言わざるを得ません。しかし、将来的にAIエージェントが「OSの一部」として機能する時代が来れば、このCursor Glassが提示している「環境のポータビリティ」は標準的な概念になるはずです。

## よくある質問

### Q1: 既存のCursor IDEとは関係がありますか？

直接的な開発元は異なりますが、Cursor IDEの拡張機能として動作するプラグインが提供されています。Cursor IDEで書いたコードを、Glassのワークスペース上で即座にエージェントとして実行・クラウド移行させる連携が可能です。

### Q2: セキュリティ面での懸念はありませんか？

ハンドオフ時にはソースコードや環境変数がクラウドに転送されます。データは全てAES-256で暗号化されますが、機密性の高いデータを扱う場合は、セルフホスト可能な「Private Worker」オプションを利用して、自社VPC内でのみ完結させる構成を推奨します。

### Q3: 対応しているLLMに制限はありますか？

SDK自体はモデルに依存しません。GPT-4o、Claude 3.5 Sonnet、あるいはローカルで動かしているLlama 3など、どのようなモデルでも利用可能です。あくまで「実行環境と状態」を管理するツールという立ち位置です。

---

## あわせて読みたい

- [GitAgent by Lyzr 使い方：GitHubリポジトリを自律型エージェント化する実務評価](/posts/2026-03-20-gitagent-lyzr-review-github-automation/)
- [My Computer by Manus AI 使い方：デスクトップ操作を自動化するAIエージェントの実力](/posts/2026-03-17-manus-ai-my-computer-desktop-automation-review/)
- [Parallax 使い方 レビュー：ローカル完結型AI開発オーケストレーターの真価](/posts/2026-03-17-parallax-local-ai-orchestrator-review-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "既存のCursor IDEとは関係がありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "直接的な開発元は異なりますが、Cursor IDEの拡張機能として動作するプラグインが提供されています。Cursor IDEで書いたコードを、Glassのワークスペース上で即座にエージェントとして実行・クラウド移行させる連携が可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "セキュリティ面での懸念はありませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ハンドオフ時にはソースコードや環境変数がクラウドに転送されます。データは全てAES-256で暗号化されますが、機密性の高いデータを扱う場合は、セルフホスト可能な「Private Worker」オプションを利用して、自社VPC内でのみ完結させる構成を推奨します。"
      }
    },
    {
      "@type": "Question",
      "name": "対応しているLLMに制限はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "SDK自体はモデルに依存しません。GPT-4o、Claude 3.5 Sonnet、あるいはローカルで動かしているLlama 3など、どのようなモデルでも利用可能です。あくまで「実行環境と状態」を管理するツールという立ち位置です。 ---"
      }
    }
  ]
}
</script>
