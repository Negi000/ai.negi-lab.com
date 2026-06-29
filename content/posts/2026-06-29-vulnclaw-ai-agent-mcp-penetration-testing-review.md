---
title: "VulnClaw：AI AgentとMCPで脆弱性診断をフルオート化する実力"
date: 2026-06-29T00:00:00+09:00
slug: "vulnclaw-ai-agent-mcp-penetration-testing-review"
description: "偵察・スキャン・攻撃実証・レポート生成というペネトレーションテストの全工程をAI Agentが自律実行する。Model Context Protocol（..."
cover:
  image: "/images/posts/2026-06-29-vulnclaw-ai-agent-mcp-penetration-testing-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "VulnClaw"
  - "AI Agent"
  - "MCP"
  - "脆弱性診断 自動化"
  - "ペネトレーションテスト"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- 偵察・スキャン・攻撃実証・レポート生成というペネトレーションテストの全工程をAI Agentが自律実行する
- Model Context Protocol（MCP）を採用しており、nmapやsqlmapといった既存ツールをLLMが自在に操れる拡張性が強み
- セキュリティエンジニアの補助ツールとしては極めて優秀だが、破壊的アクションのリスクがあるため「完全放置」は禁物

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">ローカルLLMを推論エンジンとして使い、APIコストを抑えた自律診断環境を構築するのに必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、セキュリティエンジニアやDevSecOpsを推進する開発者にとって、VulnClawは「今すぐ試すべき」ツールです。★評価は4.5。

従来の自動スキャナは、あらかじめ定義されたシグネチャに基づいた「点」の検知しかできませんでした。しかし、VulnClawはLLMを思考エンジンに据えることで、複数のツールを組み合わせて「線」で脆弱性を突いていくという、人間のハッカーに近い挙動を自動化しています。

特にMCP（Model Context Protocol）に対応している点が技術的に筋が良く、特定のLLMに依存せずにセキュリティツール群を統合できる設計は将来性が高いです。一方で、ローカルで動かすにはそれなりの計算資源かAPIコストがかかるため、趣味の範囲を超えた実務での運用を前提とした人に向いています。

## このツールが解決する問題

これまでの脆弱性診断は、職人芸の世界でした。ターゲットに対してnmapでポートを調べ、サービスを特定し、既知の脆弱性を検索し、手動でペイロードを試す。この一連の流れには膨大な時間がかかり、SIer時代に私が関わった案件でも、1サーバーの診断に数日かかることは珍しくありませんでした。

VulnClawは、この「ツール間のコンテキストの受け渡し」をAI Agentが代行することで問題を解決します。例えば、nmapの結果から「このバージョンのWebサーバーならディレクトリトラバーサルの可能性がある」とAIが判断し、自動的に関連するスキャンツールを起動します。

人間が各ツールのコマンドオプションを覚える必要はなく、自然言語で「ターゲットの脆弱性を調べてレポートを出して」と指示するだけで、ツールチェーンがオーケストレーションされるのです。これは、単純なスクリプトによる自動化とは一線を画す、判断を伴う自動化と言えます。

## 実際の使い方

### インストール

VulnClawはPython環境とGo言語のツール群、そしてLLMのAPIキーが必要です。基本的にはレポジトリをクローンしてセットアップします。

```bash
# レポジトリの取得
git clone https://github.com/Unclecheng-li/VulnClaw.git
cd VulnClaw

# 依存パッケージのインストール
pip install -r requirements.txt

# MCPサーバーとツールの設定
# nmapやsqlmapなどのバイナリがパスに通っている必要があります
cp config.example.yaml config.yaml
```

注意点として、Python 3.10以降が推奨されています。また、実際に攻撃コードを生成・実行するため、Dockerコンテナなどの隔離環境（サンドボックス）で動かすことが絶対条件です。ホストマシンで直接実行するのは、自身の環境を破壊するリスクがあるためおすすめしません。

### 基本的な使用例

READMEの構造に基づくと、エージェントをインスタンス化してタスクを投げる形式になります。

```python
from vulnclaw.core.agent import VulnerabilityAgent
from vulnclaw.core.config import LoadConfig

# 設定の読み込み（APIキーやモデル選択）
config = LoadConfig("config.yaml")

# エージェントの初期化
# モデルはGPT-4oやClaude 3.5 Sonnetが推奨されています
agent = VulnerabilityAgent(
    model=config.llm_model,
    api_key=config.api_key,
    mcp_enabled=True
)

# 診断開始
# 自然言語でターゲットと範囲を指定する
prompt = "192.168.1.100に対して脆弱性スキャンを実行し、クリティカルな脆弱性が見つかったらPoCを試行して"
result = agent.execute_task(prompt)

# 結果の確認
print(f"ステータス: {result.status}")
print(f"発見された脆弱性: {result.vulnerabilities}")
```

このコードの裏側では、AIが「まずポートスキャンが必要だ」と判断し、MCP経由でnmapを叩いています。その出力をAIが読み取り、次に試すべきツールを選択するというループが回ります。

### 応用: 実務で使うなら

実務では、CI/CDパイプラインに組み込むのが最も効果的です。例えば、ステージング環境へのデプロイ後にVulnClawを走らせ、自動的にPDFレポートを生成させる運用です。

```python
# レポート生成に特化した実行
report_agent = VulnerabilityAgent(role="reporter")
report_data = report_agent.analyze_logs("./logs/scan_results.json")
report_agent.generate_pdf_report(report_data, output_path="./reports/daily_scan.pdf")
```

このように、診断の各フェーズを個別に呼び出すことも可能です。全ての工程をAIに任せるのが不安な場合は、情報収集と分析だけをAIに任せ、最後の攻撃試行（Exploit）は人間が確認してから実行するように設定するのが現実的な運用案でしょう。

## 強みと弱み

**強み:**
- MCP採用による拡張性: 既存のセキュリティツールをプラグイン感覚で追加でき、LLMとの連携がスムーズです。
- ワークフローの自律性: 「次はこれをする」という判断をAIが行うため、エンジニアの拘束時間を大幅に削減できます。
- レポート品質: LLMが得意とする要約・解説能力により、非技術者にも分かりやすい診断レポートが即座に生成されます。

**弱み:**
- 実行コスト: GPT-4クラスのモデルを何度も呼び出すため、1回のフルスキャンで数ドル〜十数ドルのAPI費用がかかる場合があります。
- 誤検知と破壊リスク: AIが生成したペイロードがターゲットサーバーをダウンさせる可能性は否定できません。本番環境への使用は厳禁です。
- ドキュメントの不足: 現時点では中国語と英語がメインであり、日本語での詳細な解説はほとんどありません。

## 代替ツールとの比較

| 項目 | VulnClaw | Metasploit Framework | Nuclei |
|------|-------------|-------|-------|
| 動作方式 | AI Agentによる自律推論 | 手動またはスクリプト実行 | テンプレートベースの自動スキャン |
| 学習コスト | 低（自然言語で指示） | 高（専門知識必須） | 中（YAML定義の理解） |
| 柔軟性 | 非常に高い | 高い | 低い（定義済みのみ） |
| 導入難易度 | 中（環境構築が必要） | 低 | 低 |

Metasploitは強力ですが、使いこなすにはプロ並みの知識が必要です。一方でNucleiは高速ですが、未知の脆弱性の組み合わせには対応できません。VulnClawはその中間、つまり「知識をAIが補いながら、柔軟にツールを使い分ける」というポジションを確立しています。

## 料金・必要スペック・導入前の注意点

VulnClaw自体はオープンソース（OSS）であり、利用料は無料ですが、バックエンドで動かすLLMのコストがかかります。

推奨スペック：
- 推論をローカルで行う場合：VRAM 24GB以上のGPU（RTX 3090 / 4090）が必須です。
- API経由の場合：メモリ16GB以上の一般的なPCで十分です。
- ストレージ：スキャンログやツール類で数GB程度。

APIコストを抑えたい場合は、Llama 3やQwen 2.5などの高性能なオープンモデルをローカルで動かし、それをVulnClawから呼び出す構成がベストです。これから本格的にローカルLLMを動かしたいなら、RTX 4090を搭載したPCを組むか、VRAMを積んだワークステーションを検討してください。私はRTX 4090を2枚挿していますが、これなら大規模なエージェントワークフローもストレスなく検証できます。

## 私の評価

私の評価は星5つ中「4」です。

SIer時代の私がこれを持っていたら、残業時間は半分になっていたでしょう。単なる自動化ツールではなく、MCPという共通規格の上でセキュリティツールを統合した点は、現在のAIトレンドを正確に捉えています。

ただし、セキュリティという「間違いが許されない」分野において、LLMの不確実性をどう制御するかという課題は残っています。現時点では、社内ツールや開発環境のセキュリティチェックを高速化するための「強力な助手」として使うのが最も賢い選択です。逆に、ツールに任せきりにして法的な責任やシステムトラブルのリスクを負えない人は、まだ手を出さないほうが無難です。

## よくある質問

### Q1: 初心者でも使えますか？

コマンドライン操作とPythonの基本的な知識は必須です。また、セキュリティの基礎概念（ポート、プロトコル、脆弱性の種類）がわからないと、AIが出した結果が正しいかどうか判断できないため、中級者以上向けと言えます。

### Q2: OpenAIのAPIキー以外でも動きますか？

はい、MCPを経由しているため、互換性のあるモデルであればAnthropicのClaudeや、Ollamaでホストしたローカルモデルでも動作可能です。ただし、推論能力が低いモデルだと正確な判断ができず、エラーを連発する可能性があります。

### Q3: 攻撃ツールとして悪用される心配はありませんか？

このツールはあくまでペネトレーションテスト（防御のための攻撃演習）を目的としています。許可されていないネットワークへの使用は法律で禁じられており、自己責任での利用が原則です。利用時は必ずクローズドな環境で試してください。

---

## あわせて読みたい

- [AIエージェントがSaaSを飲み込む。SaaSpocalypseの正体と開発者の生存戦略](/posts/2026-03-02-saaspocalypse-ai-agent-supreme-dominance/)
- [Lyto ブラウザとツールを横断してタスクを完結させる自律型AIエージェントの実力](/posts/2026-06-28-lyto-ai-agent-browser-automation-review/)
- [anthropics/knowledge-work-plugins 使い方とMCP連携の実践ガイド](/posts/2026-05-26-anthropic-mcp-knowledge-work-plugins-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "初心者でも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "コマンドライン操作とPythonの基本的な知識は必須です。また、セキュリティの基礎概念（ポート、プロトコル、脆弱性の種類）がわからないと、AIが出した結果が正しいかどうか判断できないため、中級者以上向けと言えます。"
      }
    },
    {
      "@type": "Question",
      "name": "OpenAIのAPIキー以外でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、MCPを経由しているため、互換性のあるモデルであればAnthropicのClaudeや、Ollamaでホストしたローカルモデルでも動作可能です。ただし、推論能力が低いモデルだと正確な判断ができず、エラーを連発する可能性があります。"
      }
    },
    {
      "@type": "Question",
      "name": "攻撃ツールとして悪用される心配はありませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "このツールはあくまでペネトレーションテスト（防御のための攻撃演習）を目的としています。許可されていないネットワークへの使用は法律で禁じられており、自己責任での利用が原則です。利用時は必ずクローズドな環境で試してください。 ---"
      }
    }
  ]
}
</script>
