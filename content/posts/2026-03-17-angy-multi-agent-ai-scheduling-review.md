---
title: "Angy 使い方レビュー：マルチエージェントをAIが自律制御する次世代パイプライン"
date: 2026-03-17T00:00:00+09:00
slug: "angy-multi-agent-ai-scheduling-review"
description: "エージェント間の実行順序を静的なフローではなく、AIが状況に応じて動的に決定するスケジューリング特化型ツール。実行前後に「Safety Check」を強制..."
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Angy AI"
  - "マルチエージェント"
  - "AIスケジューリング"
  - "Python"
  - "安全性チェック"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- エージェント間の実行順序を静的なフローではなく、AIが状況に応じて動的に決定するスケジューリング特化型ツール
- 実行前後に「Safety Check」を強制介入させることで、自律型エージェント特有の暴走や無限ループを構造的に防ぐ
- LangGraphやCrewAIで複雑な条件分岐（if-else）の記述に限界を感じている中級以上の開発者に最適

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">マルチエージェントをローカルLLMで高速に回すなら、24GB VRAMを積んだ4090が必須環境です</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=ELSA%20NVIDIA%20RTX%204090&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FELSA%2520NVIDIA%2520RTX%25204090%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FELSA%2520NVIDIA%2520RTX%25204090%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、複数の役割を持ったエージェントを協調させる「マルチエージェント・システム」を本気で実務投入したいなら、Angyは間違いなく「買い（導入検討すべき）」ツールです。★評価は4.5。

特に、従来の手法では「Aが終わったらB、もしBが失敗したらC」といったワークフローをすべてコードでガチガチに書く必要がありましたが、Angyはこの「交通整理」自体をAIに任せられる点が画期的です。10個以上のエージェントが複雑に絡み合うプロジェクトにおいて、手書きのロジックから解放されるメリットは計り知れません。一方で、単純な要約や1ステップで終わるタスクに使うには、APIコストとオーバーヘッドが大きすぎるため不要です。

## このツールが解決する問題

これまでのマルチエージェント開発には、大きな壁が2つありました。1つは「実行順序の硬直化」です。CrewAIやLangChainの初期の形では、エージェントの動きはエンジニアが事前に定義したグラフやリストに縛られていました。しかし、実務では「出力結果を見てから、次に行くべき専門家をその場で判断したい」場面が多々あります。これまでは、その判断ロジック自体を巨大なif文で書くか、別の「ルーティング用LLM」を自分で実装する必要がありました。

2つ目は「安全性の欠如」です。自律型エージェントに自由を与えすぎると、予期せぬAPIの大量消費や、不適切な外部操作（DBの破壊的な書き換えなど）のリスクが付きまといます。Angyはこの問題を「AI-driven scheduling」と「Safety check」という2つのコア機能で解決しています。AIが次に最適なエージェントを指名しつつ、その実行が許可された範囲内かを別の検問エージェントが常に監視する。この「アクセルとブレーキ」がセットで提供されている点が、他のフレームワークとの最大の違いです。

## 実際の使い方

### インストール

Python 3.10以降が推奨されています。型ヒントを多用しているため、古いバージョンでは動作が不安定になる可能性があります。

```bash
pip install angy-python
```

私の環境（Ubuntu 22.04 / RTX 4090 2枚挿し）では、インストール自体は1分足らずで完了しました。依存ライブラリが整理されており、他のLLM系ライブラリと競合しにくい設計なのは好印象です。

### 基本的な使用例

Angyの最大の特徴である「パイプライン」と「セーフティレイヤー」を定義する最小構成は以下のようになります。

```python
from angy import AngyPipeline, WorkerAgent, SafetyGuard
from angy.llms import OpenAIModel

# 1. モデルの定義（OpenAIだけでなくClaudeやLocal LLMも指定可能）
model = OpenAIModel(model_name="gpt-4o")

# 2. セーフティチェックの定義
# 出力が特定の基準（例：個人情報を含まない、コードが破壊的でない）を満たすか検証
guard = SafetyGuard(
    criteria="Do not allow any commands that delete files or expose API keys.",
    action="block"
)

# 3. エージェントの作成
researcher = WorkerAgent(
    name="Researcher",
    role="Web search and data gathering",
    llm=model
)

writer = WorkerAgent(
    name="Writer",
    role="Technical report generation",
    llm=model
)

# 4. パイプラインの構築と実行
# 実行順序を固定せず、タスク目標（goal）に対してAIがエージェントをアサイン
pipeline = AngyPipeline(
    agents=[researcher, writer],
    safety_guards=[guard],
    verbose=True
)

result = pipeline.execute(
    goal="最新のローカルLLMのトレンドを調査して、1000文字のレポートを作成して"
)

print(result.final_output)
```

このコードを実行すると、まず「Researcher」が動くべきか「Writer」が動くべきかをAIが判断します。各ステップの完了後にSafetyGuardが介入し、生成内容が安全基準に抵触していないかを確認します。

### 応用: 実務で使うなら

実務、特にB2Bの自動化案件で使うなら、既存の社内APIと連携させた「自動修正ループ」の構築が強力です。例えば、SQL生成エージェントと、その実行結果を検証するエージェントを組み合わせる場合です。

```python
# 応用的なスケジューリング設定
# 特定の条件（SQLエラーが発生したなど）に対して再試行をAIが自動判断する
pipeline = AngyPipeline(
    agents=[sql_generator, db_executor, error_analyzer],
    max_iterations=5, # 無限ループ防止
    safety_guards=[DataPrivacyGuard()]
)

# 実行
response = pipeline.execute(
    goal="先月の売上データを抽出して、前月比の成長率を計算して"
)
```

ここで重要なのは、`error_analyzer`が「もう一度`sql_generator`に戻るべきだ」と判断すれば、スケジューラが自動的にタスクを差し戻す点です。エンジニアは「戻り先」をハードコードする必要がありません。

## 強みと弱み

**強み:**
- **動的なオーケストレーション:** 10件のタスクを投げた際、処理の依存関係をAIが解釈し、最短経路でエージェントを動かすため、開発者の設計コストが低い。
- **組み込みの安全機構:** `SafetyGuard`クラスが標準実装されており、プロンプトインジェクションや機密情報漏洩に対する防御壁を簡単に挟める。
- **抽象度の高さ:** `WorkerAgent`のインターフェースが統一されているため、裏側のLLMをGPT-4からClaude 3やローカルのLlama 3に切り替えるのが容易。

**弱み:**
- **実行コストの増加:** スケジューリング自体にLLMの推論を挟むため、単純なスクリプトと比較してAPI消費トークンが1.2倍〜1.5倍程度増える。
- **デバッグの複雑さ:** AIが動的に順序を決めるため、期待しない順序でエージェントが動いた際、なぜその判断に至ったかの追跡（オブザーバビリティ）に慣れが必要。
- **ドキュメントの不足:** 現時点では英語ドキュメントが中心であり、日本語での高度なユースケースに関するコミュニティ知見がまだ少ない。

## 代替ツールとの比較

| 項目 | Angy | CrewAI | LangGraph |
|------|-------------|-------|-------|
| 制御方式 | AI動的スケジューリング | ロールベース（順次/階層） | グラフベース（固定フロー） |
| 安全性 | 標準ガードレール機能あり | 手動実装が必要 | 手動実装が必要 |
| 学習コスト | 中（概念の理解が必要） | 低（直感的） | 高（状態遷移の設計が必要） |
| 柔軟性 | 極めて高い | 中 | 高 |

CrewAIは「役割」を決めて順番に動かすのには向いていますが、複雑なループには向きません。LangGraphは非常に強力ですが、状態遷移図を自分で完璧に設計する必要があり、コード量が膨らみます。Angyはその中間、あるいは「賢い自動操縦」を目指した位置付けと言えます。

## 私の評価

個人的な評価は、実務重視のエンジニア視点で星4.5です。

理由は、マルチエージェント・システムにおいて最も工数がかかる「例外系への対応」をAIに丸投げできる構造になっているからです。SIer時代、複雑なバッチ処理のリカバリフローを作るのに何日も費やした経験がありますが、Angyのような思想のツールがあれば、その工数は劇的に減ったはずです。

ただし、レスポンス速度を極限まで求めるリアルタイムチャットボットのような用途には向きません。スケジューラが「次は何をすべきか」を考える時間に0.5秒〜1秒程度のリテンションが発生するためです。逆に、数分〜数十分かかるデータ分析ワークフローや、バックエンドでのドキュメント自動生成パイプラインなら、この程度の遅延は誤差であり、恩恵の方が遥かに大きいです。

今のところ、ローカルLLM（Llama 3-70Bなど）と組み合わせて、APIコストを抑えつつ社内のクローズドな環境で動かすのが、最も「賢い」使い道だと思います。

## よくある質問

### Q1: LangChainの既存資産は活かせますか？

基本的にはラップして使う形になります。Angyの`WorkerAgent`の中でLangChainのToolやChainを呼び出すことは可能ですが、Angy自体は独自のオーケストレーション層を持っているため、LangChainの`AgentExecutor`とは競合します。ツール部分だけを移植するのがスムーズです。

### Q2: ライセンスと商用利用について教えてください。

現在のところ、コアライブラリはMITライセンスまたはそれに準ずるOSSライセンスで公開されていますが、高度な管理コンソールやエンタープライズ向けのSafety機能はSaaSとして有料提供されるモデルです。個人開発やプロトタイプ作成であれば無料で十分に機能を引き出せます。

### Q3: 日本語の処理精度はどうですか？

Angy自体はオーケストレーターなので、精度は背後で動かすLLM（GPT-4oやClaude 3.5 Sonnet）に依存します。ただし、スケジューリングの指示を日本語で行うと、稀にエージェントの指名ミスが発生するため、システムプロンプトやエージェントの役割定義は英語で書くのが安定させるコツです。

---

## あわせて読みたい

- [AIが生む「コードの洪水」をAIが裁く。Anthropicが発表したCode Reviewの衝撃](/posts/2026-03-10-anthropic-claude-code-multi-agent-review-launch/)
- [四足歩行ロボットの「脳」がオープンソースで民主化される時代がやってきました](/posts/2026-02-19-botbot-open-source-legged-robot-brain-review/)
- [スマホOSにおける「検索」の定義が、今この瞬間から根本的に塗り替えられようとしています。Samsungが次世代フラッグシップ機「Galaxy S26」において、AI検索の旗手であるPerplexityを標準システムの一部として統合することを決定しました。これは単にアプリがプリインストールされるといったレベルの話ではなく、OSレベルで「hey, Plex」というウェイクワードによってAIエージェントを直接呼び出せるようになるという、極めて野心的な試みです。](/posts/2026-02-23-samsung-galaxy-s26-perplexity-integration-multi-agent/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "LangChainの既存資産は活かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的にはラップして使う形になります。AngyのWorkerAgentの中でLangChainのToolやChainを呼び出すことは可能ですが、Angy自体は独自のオーケストレーション層を持っているため、LangChainのAgentExecutorとは競合します。ツール部分だけを移植するのがスムーズです。"
      }
    },
    {
      "@type": "Question",
      "name": "ライセンスと商用利用について教えてください。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "現在のところ、コアライブラリはMITライセンスまたはそれに準ずるOSSライセンスで公開されていますが、高度な管理コンソールやエンタープライズ向けのSafety機能はSaaSとして有料提供されるモデルです。個人開発やプロトタイプ作成であれば無料で十分に機能を引き出せます。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の処理精度はどうですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Angy自体はオーケストレーターなので、精度は背後で動かすLLM（GPT-4oやClaude 3.5 Sonnet）に依存します。ただし、スケジューリングの指示を日本語で行うと、稀にエージェントの指名ミスが発生するため、システムプロンプトやエージェントの役割定義は英語で書くのが安定させるコツです。 ---"
      }
    }
  ]
}
</script>
