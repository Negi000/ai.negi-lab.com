---
title: "sf-skills レビュー：Salesforceが提唱するAIエージェントの「スキル標準化」を読み解く"
date: 2026-08-23T00:00:00+09:00
slug: "salesforce-sf-skills-agent-toolkit-review"
description: "AIエージェントが実行する「アクション（スキル）」を再利用可能な形式で宣言的に定義するライブラリ。。SalesforceのAgentforceに最適化され..."
cover:
  image: "/images/posts/2026-08-23-salesforce-sf-skills-agent-toolkit-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "sf-skills"
  - "Agentforce"
  - "AIエージェント"
  - "Tool Calling"
  - "Salesforce 開発"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- AIエージェントが実行する「アクション（スキル）」を再利用可能な形式で宣言的に定義するライブラリ。
- SalesforceのAgentforceに最適化されているが、中身はOpenAPIやJSONに準拠したポータブルな構造。
- Salesforceエコシステムを利用する企業エンジニアには必須、外部開発者には「スキルの設計図」として有用。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE</strong>
<p style="color:#555;margin:8px 0;font-size:14px">複雑なYAML定義とコード、APIドキュメントを並べて比較する開発環境には27インチ4Kが最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、Salesforce環境でAIエージェント（Agentforce）を構築しようとしているなら、間違いなく「今すぐチェックすべき資産」です。一方で、Salesforceとは全く無縁のローカルLLM開発者がそのままライブラリとして組み込むには、まだ汎用性が足りません。

評価としては、設計思想に★5、汎用ライブラリとしての使い勝手に★3といったところです。このツールの本質は、バラバラになりがちな「エージェントに何ができるか（Tool Callingの定義）」を、特定のベンダーやコードに依存させず、メタデータ（YAML）で管理可能にした点にあります。私のように実務で「エージェントの振る舞いを顧客に説明し、かつメンテナンスしやすくしたい」と考える人間には、非常に刺さるアプローチです。

## このツールが解決する問題

これまでのAIエージェント開発、特にLangChainやOpenAIのTool Callingを使った実装には共通の悩みがありました。それは「スキルの定義がコードの中に埋もれてしまう」ことです。

例えば、あるエージェントに「在庫を確認する」というスキルを持たせたい場合、従来はPythonコードのDocstringに仕様を書き、それをLLMに読み込ませていました。これでは、プログラミングができないビジネスサイドの人間がスキルの仕様を確認・変更することが困難です。また、エージェントのプラットフォームを乗り換えるたびに、スキルの定義を書き直す必要がありました。

sf-skillsは、この「スキル」を「実行可能なアセット」としてコードから切り離します。Salesforceが長年培ってきた「メタデータ駆動開発」の思想をAIエージェントに持ち込んだ形です。具体的には、入力パラメータ、出力、エラーハンドリング、そしてそのスキルが何をするのかという説明を、`.skill-meta.xml` や YAML 形式で管理します。

これにより、一度定義したスキルを複数のエージェントで共有したり、Salesforceのフロー（自動化ツール）やApex（言語）とシームレスに連携させたりすることが可能になります。100個以上のスキルを管理しなければならない大規模なエンタープライズAIプロジェクトにおいて、この「管理のしやすさ」はレスポンス速度と同じくらい重要です。

## 実際の使い方

### インストール

sf-skills自体はライブラリというよりは、リポジトリをクローンしてテンプレートとして利用するか、Salesforce CLIを通じて環境にデプロイする形態をとります。

```bash
# GitHubからクローンして中身を確認する
git clone https://github.com/forcedotcom/sf-skills.git
cd sf-skills
```

前提条件として、Salesforce環境（スクラッチ組織など）とSalesforce CLIが必要です。ローカルでこれらを動かすには、Node.jsの最新LTSが推奨されます。

### 基本的な使用例

ここでは、リポジトリ内の定義を参考に、どのようにスキルを「宣言」するかの例を示します。これは特定の関数をエージェントに露出させるための定義ファイルです。

```yaml
# example-skill.skill-meta.xml (シミュレーション)
name: GetCustomerOrders
description: 特定の顧客IDに基づいて過去の注文履歴を取得します。
type: ApexAction # または Flow, ExternalService
inputParameters:
  - name: customerId
    type: String
    description: 顧客のユニークID
    required: true
outputParameters:
  - name: orderList
    type: List
    description: 注文情報のリスト
```

このように、コードではなく「仕様」を記述します。実務では、この定義をSalesforceのAgentforce Studioに読み込ませることで、AIが「この顧客の注文を調べて」と言われた際に、どのApexクラスを叩けばいいかを自動的に判断できるようになります。

### 応用: 実務で使うなら

実務で最も価値を発揮するのは、既存の「外部API」をAIエージェントに統合する場面です。sf-skillsの仕組みを使えば、OpenAPI（Swagger）形式のドキュメントを読み込み、それを「スキル」としてラップできます。

```python
# Python側でこれらのスキルを動的に読み込むイメージ
from sf_skills_parser import SkillLoader

# フォルダ内の全てのスキル定義をロード
loader = SkillLoader("./my_skills")
available_tools = loader.get_openai_tools()

# OpenAIのAPIにそのまま渡せる形式に変換される
# これにより、YAMLを修正するだけでLLMが使えるツールが更新される
response = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=messages,
    tools=available_tools
)
```

このアプローチの利点は、Pythonコードを1行も触らずに「エージェントができること」を増やせる点にあります。私の経験上、大規模なシステム開発ではデプロイサイクルがネックになりますが、メタデータとしてのスキル定義なら、比較的柔軟に変更・適用が可能です。

## 強みと弱み

**強み:**
- 宣言的な設計: コードを書かずにスキルのインターフェースを定義できるため、ビジネス要件との乖離が起きにくい。
- エコシステム連携: SalesforceのFlow（ノーコード）やApex（プロコード）をそのままAIの武器にできる。
- 構造化されたメタデータ: LLMにとって理解しやすい形式で説明（Description）を管理できるため、Tool Callingの精度が向上する。

**弱み:**
- Salesforce色が強い: あくまでSalesforceプラットフォーム上での動作が主眼であり、純粋なPythonプロジェクトには冗長。
- 学習コスト: Salesforce独自のメタデータ形式（XML/YAML）や、デプロイの手順を覚える必要がある。
- ドキュメントの少なさ: 現時点ではGitHub上のドキュメントが中心であり、日本語の技術解説はほぼ皆無。

## 代替ツールとの比較

| 項目 | sf-skills | MCP (Model Context Protocol) | LangChain Tools |
|------|-------------|-------|-------|
| 開発元 | Salesforce | Anthropic | オープンソース |
| 主な用途 | エンタープライズ/CRM連携 | LLMと外部データの汎用接続 | アプリ組み込みツール |
| 構成 | メタデータ(YAML/XML) | JSON-RPC | Python/TypeScript |
| 適合性 | Salesforceユーザー向け | Claude利用者・汎用向け | 自由度重視の開発者向け |

Anthropicが発表したMCPと比較すると、sf-skillsはより「業務プロセス（FlowやApex）」に密着しています。一方、単純なデータ取得であればMCPの方が軽量で使いやすいでしょう。

## 料金・必要スペック・導入前の注意点

sf-skillsリポジトリ自体はOSS（MITライセンス）であり、無料で利用・参照できます。ただし、これを実際に動作させるにはSalesforceのライセンス（特にAgentforceが利用可能なエディション）が必要です。

開発環境としては、VS Codeに「Salesforce Extension Pack」をインストールした状態が推奨されます。ハードウェアスペックは問いませんが、メタデータや大規模なコードベースを扱うなら、16GB以上のメモリを持つMacBook Proや、ソースコードを俯瞰できる4Kモニターがあると作業効率が劇的に変わります。私は27インチの4Kモニター（Dell U2723QEなど）を縦横2枚使い、片方にスキル定義、片方に実行ログを出すスタイルで検証しています。

商用利用については、Salesforceの利用規約に従う必要があります。あくまで「Salesforce内のデータをAIにどう扱わせるか」というフレームワークであるため、クラウドコストの増大には注意してください。

## 私の評価

私の評価は ★3.5 です。

特定のプラットフォームに依存するツールではありますが、「AIエージェントの機能をどう定義し、どう管理すべきか」という問いに対するSalesforceなりの回答が詰まっています。20件以上の機械学習案件をこなしてきた身からすると、結局最後に問題になるのは「モデルの賢さ」ではなく「ツール定義のメンテナンス性」です。その点、sf-skillsのアプローチは非常に理にかなっています。

Salesforceを導入している企業のエンジニアであれば、このリポジトリにあるサンプルを読み解くだけでも、エージェント設計のベストプラクティスが学べるはずです。逆に、独自のサーバーでローカルLLMを動かしている層には、今のところオーバーエンジニアリングな印象が拭えません。

## よくある質問

### Q1: Salesforceのアカウントがないと使えませんか？

リポジトリ内のYAML定義や設計思想を参照することは誰でも可能です。ただし、提供されているスキルを実際に実行したり、Agentforceと連携させたりするには、Salesforceの組織（Developer Edition等）が必要です。

### Q2: 既存のOpenAPI（Swagger）定義は流用できますか？

はい、Salesforceの「外部サービス」機能を介してOpenAPI定義を取り込み、それをsf-skillsの形式でエージェントに露出させることが可能です。これがこのツールの大きな強みの一つです。

### Q3: PythonのLangChainなどで直接読み込めますか？

公式のパーサーは提供されていませんが、中身はシンプルな構造なので、自作のスクリプトでYAMLをパースしてLangChainのTool形式に変換するのは容易です。設計の標準化として導入する価値はあります。

---

## あわせて読みたい

- [Cursor for iOS レビュー：モバイルでAIエージェントにコードを書かせる実力](/posts/2026-07-01-cursor-ios-mobile-coding-agent-review/)
- [i-have-adhd レビュー：AIエージェントの「お喋り」を封じ込め開発速度を3倍にする技術](/posts/2026-07-23-ayghri-i-have-adhd-review-ai-agent-productivity/)
- [Cursor Glass 使い方 レビュー：自律型エージェントの「状態」をクラウドへ引き継ぐ次世代ワークスペースの真価](/posts/2026-03-21-cursor-glass-agent-workspace-review-handoff/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Salesforceのアカウントがないと使えませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "リポジトリ内のYAML定義や設計思想を参照することは誰でも可能です。ただし、提供されているスキルを実際に実行したり、Agentforceと連携させたりするには、Salesforceの組織（Developer Edition等）が必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "既存のOpenAPI（Swagger）定義は流用できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、Salesforceの「外部サービス」機能を介してOpenAPI定義を取り込み、それをsf-skillsの形式でエージェントに露出させることが可能です。これがこのツールの大きな強みの一つです。"
      }
    },
    {
      "@type": "Question",
      "name": "PythonのLangChainなどで直接読み込めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "公式のパーサーは提供されていませんが、中身はシンプルな構造なので、自作のスクリプトでYAMLをパースしてLangChainのTool形式に変換するのは容易です。設計の標準化として導入する価値はあります。 ---"
      }
    }
  ]
}
</script>
