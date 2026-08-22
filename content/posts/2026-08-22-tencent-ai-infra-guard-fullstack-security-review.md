---
title: "Tencent/AI-Infra-GuardでAIシステムの脆弱性を全方位スキャンする"
date: 2026-08-22T00:00:00+09:00
slug: "tencent-ai-infra-guard-fullstack-security-review"
description: "LLM単体の「脱獄」だけでなく、Agent、MCP、インフラ層までを標的にしたフルスタックなAIセキュリティ診断プラットフォーム。。他のツールが「プロンプ..."
cover:
  image: "/images/posts/2026-08-22-tencent-ai-infra-guard-fullstack-security-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "AI-Infra-Guard"
  - "AI Red Teaming"
  - "MCPセキュリティ"
  - "Tencent AI"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- LLM単体の「脱獄」だけでなく、Agent、MCP、インフラ層までを標的にしたフルスタックなAIセキュリティ診断プラットフォーム。
- 他のツールが「プロンプト攻撃」に終始する中、Model Context Protocol（MCP）経由の攻撃経路やシステム破壊のリスクを定量化できる点が最大の違い。
- AIエージェントを実務に組み込んでいる開発者には必須だが、単にChatGPTのAPIを叩くだけの個人開発者にはオーバースペック。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">16GBのVRAMは、スキャン時の攻撃側モデルをローカルで安価に動かすための最低ライン</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言えば、自社でLLMをホスティングしていたり、外部ツールと連携する「AIエージェント」を構築している企業にとって、このツールは「すぐに導入して回すべきOSS」です。★評価は 4.5/5。

これまでAIのセキュリティといえば、いかにして差別用語を吐かせるか、いかにしてシステムプロンプトを盗むかといった「モデルへの攻撃」が中心でした。しかし、実務でAIを使おうとすれば、AIにデータベースを操作させたり、外部APIを叩かせたりします。この「AIとシステムの境界線」を狙った攻撃を防ぐ手段が圧倒的に不足していました。

Tencent/AI-Infra-Guardは、その境界線を「Agent Scan」や「MCP Scan」といった形で具体的にテストできます。特にAnthropicが提唱し、急速に普及しているMCP（Model Context Protocol）の脆弱性診断をいち早く取り入れた点は、実務レベルのAI開発を理解している開発者からすれば「ようやく欲しかったものが出てきた」という印象です。

一方で、環境構築にはそれなりの知識が求められます。Python 3.10以上はもちろん、スキャン対象の環境をサンドボックス化して安全に攻撃テストを実行するためのインフラ知識が必要です。「とりあえず入れてみた」程度では、このツールの真価を引き出すことはできないでしょう。

## このツールが解決する問題

従来、AIのセキュリティチェックは「プロンプトインジェクションへの耐性」を測るものが大半でした。例えば、「爆弾の作り方を教えて」という問いにモデルが答えてしまうかどうかを確認する作業です。しかし、私たちが現場で直面しているリスクは、もっと生々しいものです。

「AIエージェントに社内ドキュメントの要約を頼んだら、悪意ある隠しプロンプトを読み込んでしまい、エージェントが勝手にファイルを全削除した」「MCPサーバー経由でローカルネットワークのポートスキャンをされた」といった、システム連携に伴うリスクです。

AI-Infra-Guardは、以下の5つのスキャンレイヤーを通じて、この「AIを入り口にしたシステム侵入」を可視化します。

1.  **Agent Scan:** エージェントのツール利用（Tool Use）における権限昇格や意図しない動作を診断。
2.  **Skills Scan:** 特定のタスク実行におけるセキュリティホールの有無を確認。
3.  **MCP Scan:** Model Context Protocolを介したデータの流出や不正アクセスの経路をテスト。
4.  **AI Infra Scan:** モデルを動かしているサーバーやオーケストレーション層の脆弱性をチェック。
5.  **LLM Jailbreak Evaluation:** 従来の脱獄耐性テストをより高度化・自動化した評価。

これまでのツールは「点」でしかAIを守れませんでしたが、AI-Infra-Guardは「線（フロー）」と「面（インフラ）」で守るアプローチを採用しています。

## 実際の使い方

### インストール

基本的にはPython環境にインストールしますが、スキャン対象となるAIエージェントやモデルのAPIエンドポイントが準備されている必要があります。

```bash
# リポジトリをクローンして依存関係をインストール
git clone https://github.com/Tencent/AI-Infra-Guard.git
cd AI-Infra-Guard
pip install -r requirements.txt
```

注意点として、スキャンを実行する側にもある程度の計算リソースが必要です。特に大規模なJailbreakテストを行う場合、攻撃側のモデル（Attacker LLM）を動かす必要があるため、私の環境（RTX 4090 24GB）のように、余裕のあるVRAMを積んだGPUが推奨されます。

### 基本的な使用例

以下は、特定のAIエージェントに対して「スキル（機能）のスキャン」を実行する際のシミュレーションコードです。

```python
from ai_infra_guard.scanner import SkillScanner
from ai_infra_guard.models import TargetModelConfig

# スキャン対象となるエージェント（またはモデル）の設定
# 実際には攻撃対象のAPIキーやURLを指定する
target_config = TargetModelConfig(
    api_url="http://localhost:8000/v1/chat/completions",
    model_name="my-custom-agent",
    api_key="sk-xxxx"
)

# スキャナーの初期化
scanner = SkillScanner(config=target_config)

# エージェントが持つ「ツール実行権限」の脆弱性スキャンを開始
# 悪意ある入力をシミュレートしてエージェントに投げ、出力を検証する
report = scanner.run_scan(categories=["file_access", "network_call"])

# 結果の出力
for issue in report.issues:
    print(f"リスクレベル: {issue.severity}")
    print(f"詳細: {issue.description}")
    print(f"再現プロンプト: {issue.payload}")
```

このコードでは、エージェントがファイルアクセスやネットワーク呼び出しといった「スキル」を持っている場合、それらを悪用して本来許可されていない操作を行わせることができるかを自動的にテストしています。

### 応用: 実務で使うなら

実務では、CI/CDパイプラインに組み込む運用が理想的です。例えば、LangChainやCrewAIで構築したエージェントをステージング環境にデプロイした直後、このAI-Infra-Guardを回して「セキュリティ回帰テスト」を自動実行します。

特にMCPサーバーを自作している場合、そのサーバーが受け取ったクエリによって予期せぬシェルコマンドが実行されないか、あるいはディレクトリトラバーサルが発生しないかをチェックするために、`MCP Scan`モジュールを重点的に動かすべきでしょう。

## 強みと弱み

**強み:**
- **MCPへの対応速度:** 現時点でMCPの脆弱性スキャンを体系化しているツールは極めて稀。
- **フルスタックな診断:** プロンプト、エージェント、インフラを一つのツールで統合的に扱える。
- **レッドチーミングの自動化:** 攻撃側のLLMを用いて、人間では思いつかないような巧妙な攻撃パターンを動的に生成できる。

**弱み:**
- **日本語ドキュメントの不在:** Tencent製ということもあり、基本は英語と中国語のみ。エラーメッセージの解釈に苦労する場合がある。
- **スキャンコスト:** 高度なスキャンを実行する場合、攻撃側でもLLM（GPT-4oやClaude 3.5 Sonnetなど）を使用するため、APIコストがかさむ。
- **複雑な依存関係:** 本格的に動かすには、攻撃対象のサンドボックス環境を用意する必要があり、導入のハードルは高い。

## 代替ツールとの比較

| 項目 | AI-Infra-Guard | Microsoft PyRIT | Giskard |
|------|-------------|-------|-------|
| 主な対象 | AIエージェント・インフラ | LLM全般・Red Teaming | RAG・モデル評価 |
| MCP対応 | あり | なし（現時点） | なし |
| インフラ診断 | あり | 弱い | なし |
| 学習コスト | 高め | 中 | 低 |

MicrosoftのPyRITも非常に強力なライブラリですが、あちらはより汎用的な「AIへの攻撃ライブラリ」という色合いが強いです。対してAI-Infra-Guardは、Tencentの知見が詰まった「エンタープライズ向けの診断パッケージ」に近い印象です。

## 料金・必要スペック・導入前の注意点

AI-Infra-Guard自体はOSSであり、Apache License 2.0で提供されているため、商用利用も可能です。ただし、実行には相応のコストがかかります。

1.  **計算リソース:** スキャンを高速に回すなら、ローカルでLlama 3等の攻撃用モデルを動かすためのGPU（RTX 4090 24GB以上）が望ましいです。VRAMが不足するとスキャンが極端に遅くなります。
2.  **APIコスト:** 外部APIをスキャン対象とする場合、数千回のプロンプトを投げることになるため、1回のフルスキャンで数千円から数万円のAPI費用が発生する可能性があります。
3.  **法的・倫理的注意:** 許可を得ていない他者のサービスに対してこのツールを使うのは「攻撃」そのものです。必ず自社の管理下にある環境で、隔離されたネットワーク上で実行してください。

ハードウェア面では、ローカルLLMを並列で動かしながらスキャン結果を記録するため、書き込み速度の速いNVMe SSD（Samsung 990 Proなど）と、32GB以上のメモリ、そしてRTX 4090を推奨します。

## 私の評価

私はこのツールを「次世代のAI開発における標準的な監査ツール」の一つになると評価しています。これまで「AIはブラックボックスだから、セキュリティも確率論でしかない」と諦められていた領域に対して、エンジニアリングによる解決策を提示した意義は大きいです。

★4.5としたのは、その有用性と引き換えに、セットアップの難易度がそれなりに高いからです。特に中国発のOSS特有の「ドキュメントの行間を読む」スキルが求められる場面があります。しかし、それを差し引いても、AgentやMCPを本気で実務投入しようとしているエンジニアなら、一度は触れておくべき完成度です。

## よくある質問

### Q1: 初心者がプロンプトインジェクションの勉強に使うのはありですか？

あまりおすすめしません。これは「脆弱性を見つける」ためのツールであって、AIの仕組みを学ぶためのものではないからです。まずはGiskardのような、より可視化機能が強いツールから入るのが無難です。

### Q2: 商用サービスに対して定期的に実行しても問題ないですか？

ライセンス上は問題ありませんが、前述の通りAPIコストに注意してください。また、スキャンによってデータベースにゴミデータが大量に生成される可能性があるため、必ずテスト用DBに向けて実行すべきです。

### Q3: どのような攻撃パターンが内蔵されていますか？

基本的なJailbreak（DAN攻撃など）に加え、Tool Useを狙った権限昇格、RAGへのデータ毒入れ（Poisoning）、さらにはモデルの挙動を不安定にさせる異常入力などが含まれています。
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "初心者がプロンプトインジェクションの勉強に使うのはありですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "あまりおすすめしません。これは「脆弱性を見つける」ためのツールであって、AIの仕組みを学ぶためのものではないからです。まずはGiskardのような、より可視化機能が強いツールから入るのが無難です。"
      }
    },
    {
      "@type": "Question",
      "name": "商用サービスに対して定期的に実行しても問題ないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ライセンス上は問題ありませんが、前述の通りAPIコストに注意してください。また、スキャンによってデータベースにゴミデータが大量に生成される可能性があるため、必ずテスト用DBに向けて実行すべきです。"
      }
    },
    {
      "@type": "Question",
      "name": "どのような攻撃パターンが内蔵されていますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的なJailbreak（DAN攻撃など）に加え、Tool Useを狙った権限昇格、RAGへのデータ毒入れ（Poisoning）、さらにはモデルの挙動を不安定にさせる異常入力などが含まれています。"
      }
    }
  ]
}
</script>
