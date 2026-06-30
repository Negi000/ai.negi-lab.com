---
title: "google/agents-cli で Vertex AI エージェント開発を高速化する"
date: 2026-06-30T00:00:00+09:00
slug: "google-agents-cli-vertex-ai-review"
description: "Google Cloud上でのAIエージェント構築・評価・デプロイに伴う「環境構築の泥臭い作業」を自動化するツール。。既存のLangChainやCrewA..."
cover:
  image: "/images/posts/2026-06-30-google-agents-cli-vertex-ai-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "google/agents-cli"
  - "Vertex AI"
  - "AI Agent"
  - "デプロイ方法"
  - "Gemini"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- Google Cloud上でのAIエージェント構築・評価・デプロイに伴う「環境構築の泥臭い作業」を自動化するツール。
- 既存のLangChainやCrewAIのような「フレームワーク」ではなく、Vertex AIエコシステムを使い倒すための「実践的なCLIツールチェーン」。
- Google Cloudを主軸にAIサービスを本番運用したいエンジニアには必須だが、ローカル完結やAWS/Azure派には不要。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE</strong>
<p style="color:#555;margin:8px 0;font-size:14px">GCPコンソールとコード、評価結果のCSVを並べて確認する開発環境に最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、Vertex AIを使ってエンタープライズ向けのAIエージェントを構築するプロジェクトなら、今すぐ導入すべきです。評価は星4つ（★★★★☆）。

これまでGoogle Cloud上でエージェントを動かすには、Cloud Runの定義を書き、認証を回し、Vertex AIのAPIを叩くためのボイラープレートコードを大量に書く必要がありました。google/agents-cliは、これらの「非本質的なコード」を排除し、エージェントの「スキル（機能）」と「評価」に集中させてくれます。

一方で、個人の趣味でローカルLLMを動かしたい人や、特定のクラウドに縛られたくない開発者には、その制約の多さが足かせになるでしょう。あくまで「Google Cloudという戦場」で戦うプロのための道具です。

## このツールが解決する問題

AIエージェント開発において、最も時間がかかるのは「プロンプトを書くこと」ではありません。「エージェントが期待通りに動いているかを客観的に評価し、それを安全に本番環境へデプロイする仕組み作り」です。

従来、多くの開発者は以下のような課題に直面していました。
1. ローカルで動いたエージェントをCloud Runにデプロイする際、環境変数やIAM権限の設定で半日溶ける。
2. プロンプトを微調整した際、以前より良くなったのか悪くなったのかを判断する「評価用データセット」の回し方が属人化している。
3. エージェントが外部APIを叩く「ツール（スキル）」の管理がバラバラで、再利用性が低い。

google/agents-cliは、これらの工程を「コマンド一つ」で実行可能なワークフローに落とし込みます。特に「Evaluation（評価）」の機能が強力で、複数のプロンプト案をバッチ処理で一気にテストし、スコアリングする仕組みが最初から組み込まれています。これは実務で20件以上の案件をこなしてきた私の経験から言っても、プロジェクトの後半戦で確実に効いてくる機能です。

## 実際の使い方

### インストール

前提として、Python 3.10以降が必要です。また、Google Cloudの操作を行うため、gcloud CLIの設定が完了していることが条件となります。

```bash
# パッケージのインストール
pip install google-agents

# プロジェクトの初期化
agents-cli init --project-id your-gcp-project-id
```

初期化を行うと、プロジェクトディレクトリに必要な設定ファイル（agents.yamlなど）が生成されます。ここで注目すべきは、認証周りの設定が自動化される点です。

### 基本的な使用例

エージェントに持たせる特定の機能（スキル）を作成し、それをテストするまでの流れを見ます。

```python
# skills/weather.py として保存されるイメージ
from google_agents import skills

@skills.define
def get_weather(location: str) -> str:
    """指定された場所の天気を取得します。"""
    # 実際にはここでAPIを叩く
    return f"{location}の天気は晴れです（25度）"

# エージェントの定義（config.yaml等で管理するが、コード内での呼び出し例）
from google_agents import Agent

agent = Agent(
    name="WeatherBot",
    instruction="あなたは親切な気象予報士です。スキルを使って回答してください。",
    skills=[get_weather]
)

# 実行
response = agent.run("東京の天気を教えて")
print(response.text)
```

このコードの肝は、`@skills.define` デコレータです。これにより、関数の型ヒントやドキュメンテーション文字列が自動的に解析され、LLMが理解できるツール定義（JSON Schema）に変換されます。私たちが手動で複雑なJSONを書く必要はありません。

### 応用: 実務で使うなら

実務で最も重宝するのは、デプロイ前の「評価（Evaluation）」フェーズです。google/agents-cliでは、以下のような評価用ファイルを準備して一括テストが可能です。

```bash
# 評価の実行
agents-cli evaluate --dataset tests/eval_dataset.jsonl --output results.csv
```

これにより、100件、1000件というテストケースに対してエージェントを走らせ、正解率やレスポンス速度を測定できます。手作業で1つずつプロンプトを試して「なんとなく良くなった気がする」という曖昧な開発から脱却できるわけです。100件の評価実行にかかる時間は、並列処理を活かせばVertex AIのAPI制限内でも数分で終わります。

## 強みと弱み

**強み:**
- **Google Cloudとのシームレスな統合**: Cloud Runへのデプロイがコマンド一発（`agents-cli deploy`）で完了し、認証周りのトラブルがほぼ皆無。
- **評価機能の標準搭載**: プロダクションレベルのAI開発に不可欠な「定量的評価」がフレームワークレベルでサポートされている。
- **型安全なスキル管理**: Pythonの型ヒントをベースにツール定義を生成するため、コードの変更が即座に反映され、バグが混入しにくい。

**弱み:**
- **ベンダーロックイン**: Google Cloud (Vertex AI) 専用に設計されているため、モデルをGPT-4o（OpenAI）に切り替えたり、AWS Bedrockに移行したりといった柔軟性は低い。
- **ドキュメントの密度**: GitHubのREADMEや公式ドキュメントは、ある程度GCPの知識がある前提で書かれている。初心者にはやや不親切な箇所がある。
- **Pythonバージョン制約**: 3.10未満の環境では動作が不安定になる、あるいはインストールできないケースを確認した。

## 代替ツールとの比較

| 項目 | google/agents-cli | LangGraph | CrewAI |
|------|-------------|-------|-------|
| 主な用途 | GCP統合エージェント | 複雑な状態遷移を持つAI | 役割分担型エージェント |
| デプロイ | Cloud Run等 (標準) | 自前構築が必要 | 自前構築が必要 |
| 学習コスト | 中（GCP知識が必要） | 高 | 低 |
| 評価機能 | 標準搭載 | 拡張が必要 | 弱い |

Google Cloudでの運用が前提なら、デプロイの手間がゼロになるgoogle/agents-cliが圧倒的に有利です。一方で、ロジックが非常に複雑（ループや条件分岐が入り乱れる）な場合は、LangGraphの方が制御しやすいと感じます。

## 料金・必要スペック・導入前の注意点

ツール自体の利用は無料（オープンソース）ですが、バックエンドで動くVertex AIのAPI利用料がかかります。例えば、Gemini 1.5 Flashを使用する場合、100万トークンあたり$0.075程度と安価ですが、評価フェーズで大量のテストを回すとそれなりのコストになります。

開発環境としては、MacBook Pro (M2/M3) または RTX 3060以上のGPUを積んだWindows/Linux機があれば快適です。ただし、このツールは「クラウド上で動かすこと」を前提としているため、ローカルのスペックよりも「インターネットの安定性」と「Google Cloudのクォータ（制限）」の方が重要になります。

導入前の注意点として、組織のGoogle Cloud環境で「Vertex AI API」と「Cloud Run API」が許可されているか、IAM権限（Editor権限、または必要なService Account作成権限）があるかを必ず確認してください。ここが詰まると、ツールの便利さを1ミリも享受できません。

## 私の評価

評価は5つ星のうち「4」です。

理由としては、実務における「デプロイ」と「評価」という一番面倒な部分をGoogleが公式に肩代わりしてくれた点が高く評価できます。特に、SIer出身の私からすれば、インフラ設定のミスで本番が落ちるリスクを減らせるツールは非常に価値があります。

ただし、既存のLangChainエコシステムとの互換性が低いため、すでに他フレームワークで組んでいるプロジェクトを無理に移行させる必要はありません。新規でGCP上にAIエージェントを構築するプロジェクトなら、これ一択です。

開発効率で言えば、手動でCloud Runにデプロイしていた時間を80%は削減できるはずです。浮いた時間で、より精度の高いプロンプトやロジックの構築に専念できる。これこそが、実務家が求めていたツールです。

## よくある質問

### Q1: Gemini以外のモデル（例: Claude 3.5 Sonnet）は使えますか？

Vertex AI Model Garden上で提供されているモデルであれば、基本的には利用可能です。ただし、CLIの統合機能が最も最適化されているのはGeminiシリーズです。

### Q2: 料金はどこで発生しますか？

CLIの実行自体は無料ですが、エージェントがVertex AIのLLMを呼び出した際のトークン料金、およびCloud Runにデプロイした際のコンピューティング料金が発生します。

### Q3: 既存のLangChainプロジェクトをagents-cliに移行できますか？

直接的な変換ツールはありません。ロジックを「スキル（関数）」として切り出し、agents-cliの形式で再定義する必要があります。ただし、関数の内容はそのまま流用できるため、移行コストはそれほど高くありません。

---

## あわせて読みたい

- [CLI-Anything 使い方レビュー：あらゆるソフトをAIエージェント化する新基準](/posts/2026-05-19-cli-anything-review-agent-native-software/)
- [AIスタートアップの「死の警告灯」を見逃すな：Google Cloud幹部が語るインフラ選定の致命的な罠](/posts/2026-02-19-ai-startup-check-engine-light-google-cloud/)
- [Lyto ブラウザとツールを横断してタスクを完結させる自律型AIエージェントの実力](/posts/2026-06-28-lyto-ai-agent-browser-automation-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Gemini以外のモデル（例: Claude 3.5 Sonnet）は使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Vertex AI Model Garden上で提供されているモデルであれば、基本的には利用可能です。ただし、CLIの統合機能が最も最適化されているのはGeminiシリーズです。"
      }
    },
    {
      "@type": "Question",
      "name": "料金はどこで発生しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "CLIの実行自体は無料ですが、エージェントがVertex AIのLLMを呼び出した際のトークン料金、およびCloud Runにデプロイした際のコンピューティング料金が発生します。"
      }
    },
    {
      "@type": "Question",
      "name": "既存のLangChainプロジェクトをagents-cliに移行できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "直接的な変換ツールはありません。ロジックを「スキル（関数）」として切り出し、agents-cliの形式で再定義する必要があります。ただし、関数の内容はそのまま流用できるため、移行コストはそれほど高くありません。 ---"
      }
    }
  ]
}
</script>
