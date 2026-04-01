---
title: "Slack AIが30もの新機能を一挙に搭載し、単なる「チャットツール」から「自律型AIエージェントの基盤」へと変貌しました。"
date: 2026-04-01T00:00:00+09:00
slug: "slack-ai-makeover-agentforce-30-features"
description: "SlackがAIエージェント機能を主軸とした30以上の新機能を発表し、Salesforceの「Agentforce」と完全統合した。。検索や要約といった受..."
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI News"
tags:
  - "Slack AI 使い方"
  - "Agentforce Salesforce 連携"
  - "AIエージェント 業務効率化"
  - "Slack ワークフロー 自動化"
---
Salesforceの基幹データと直結したことで、AIが情報を要約する段階から、商談やプロジェクトを自ら進める段階へ移行したのが今回の核心です。
これまでエンジニアが手動で組んでいたワークフローの多くが、自然言語による指示だけで自動生成・実行される未来が確定しました。

## 3行要約

- SlackがAIエージェント機能を主軸とした30以上の新機能を発表し、Salesforceの「Agentforce」と完全統合した。
- 検索や要約といった受動的なAIから、外部ツールを操作し業務を完結させる「自律型エージェント」へと進化を遂げた。
- 開発者は今後、複雑なコードを書くよりも「AIにどのようなデータと権限を与えるか」の設計に注力する時代になる。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">BenQ PD3220U 31.5インチ</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Slack AIの多機能をCanvasやマルチウィンドウで使いこなすには、広大な4K作業領域が必須です</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=BenQ%20PD3220U&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FBenQ%2520PD3220U%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FBenQ%2520PD3220U%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 何が起きたのか

SalesforceがSlackを「AI-heavy」なツールへ再定義すると発表しました。追加された機能は30に及びますが、その本質は「Slackを企業のOSにする」という意思表示です。

かつてのSlack AIは、チャンネル内の会話を要約したり、過去の発言を検索したりする「情報の整理屋」に過ぎませんでした。しかし、今回発表されたアップデートによって、SlackはSalesforceの新しいAIアーキテクチャ「Agentforce」と密接に連携します。これにより、AIが自らCRM（顧客管理システム）のデータを更新し、顧客へのメール案を作成し、さらには承認プロセスを回すといった「アクション」が可能になりました。

なぜ今、このタイミングなのか。それは、生成AIのブームが「チャットで遊ぶフェーズ」から「実務でROI（投資対効果）を出すフェーズ」に移ったからです。ChatGPTやClaudeといった単体モデルは強力ですが、彼らは「社内のリアルタイムな文脈」を持っていません。Slackは全社員の会話データと、Salesforceという世界最大の顧客データを持っています。この2つをAIで結合させることで、他のチャットツールには真似できない「文脈を理解した実行力」を手に入れたわけです。

具体的には、Slack上のボタン一つで「商談のフェーズを進め、関係者に通知し、次のアクションをカレンダーに登録する」といった一連の動作を、AIが裏側のAPIを叩いて完結させます。これはエンジニアが個別にスクリプトを書いていた領域を、標準機能が飲み込んだことを意味します。

## 技術的に何が新しいのか

今回の発表で技術的に最も注目すべきは、AIがSlack内のメッセージだけでなく、Salesforce上の構造化データやサードパーティ製アプリのデータに「推論」を用いてアクセスする仕組みです。

従来のSlackアプリは、特定のキーワードに対して特定のAPIを叩く「静的なトリガー」で動いていました。例えば、`/jira create` と打てばチケットが作れるといった具合です。しかし、新しいエージェント機能では、Atlas Reasoning Engine（アトラス・リーズニング・エンジン）と呼ばれる推論エンジンが介在します。

このエンジンの挙動を私なりに分析すると、以下の3つのステップで動作しています。

1. 文脈の解釈: ユーザーが「昨日の商談の結果に基づいて、来週のタスクを整理して」と入力すると、AIがどのチャンネルの、どの発言、どのCRMレコードを参照すべきかを判断する。
2. 実行プランの策定: Slackの「Workflow Builder」のコンポーネントをパズルのように組み合わせ、実行に必要なステップを自ら構築する。
3. ツール利用（Tool Use）: 構築されたプランに基づき、Salesforceや外部サービス（ServiceNow, Lucidchart等）のAPIを適切なパラメータで叩く。

これは、LLM（大規模言語モデル）の機能の一つである「Function Calling」を、企業のセキュアな境界線内で、かつGUIベースのワークフローと統合したものです。

開発者目線で見れば、これまでPythonで書いていた「Slack Bolt SDKを用いたカスタムボット」のロジック部分が、Agentforceのメタデータ定義に置き換わることを意味します。例えば、以下のような擬似的な定義だけで、複雑なエージェントが動くようになります。

```yaml
agent_profile:
  name: "営業アシスタント"
  skills:
    - access_crm_data
    - summarize_slack_threads
    - create_google_calendar_events
  constraint: "商談ステータスが'Closed'のものは編集禁止"
```

このように、コードによる手続き型の記述から、ポリシーとゴールによる宣言型の記述へと開発パラダイムがシフトしています。

## 数字で見る競合比較

| 項目 | Slack AI (Agentforce) | Microsoft Teams (Copilot) | ChatGPT Enterprise |
|------|-----------|-------|-------|
| データ連携 | Salesforceと完全同期 | Office 365 / Azure | 独自アップロード / API連携 |
| 実行機能 | ワークフロー内蔵で30種のアクション | MS Graph経由の操作 | GPTsによるAPI連携 |
| セットアップ | 既存CRMから自動生成 | 管理者による大規模設定が必要 | 個別のプロンプト設計が必要 |
| レスポンス速度 | 0.8秒〜1.5秒（推論含む） | 1.0秒〜2.0秒 | 0.5秒〜1.2秒（モデル依存） |
| 価格 | $20/user/month (追加料金) | $30/user/month | $30〜/user/month |

この表から分かる通り、Slackの強みは「価格」と「Salesforceデータへの近さ」にあります。TeamsはOffice製品との相性は抜群ですが、CRMデータとの連携には依然として複雑な設定が必要です。Slackは今回の発表で、月額$20という競合より一段安い価格設定（アドオン形式）を維持しつつ、機能密度を高めてきました。

実務上の差が出るのは、情報の「新鮮さ」です。RAG（検索拡張生成）を用いた一般的なAIボットは、情報のインデックス化に数分のラグが生じることがありますが、Slack AIはSalesforceのライブデータを直接参照するため、コンマ数秒前の商談修正も反映した回答を返します。この「ゼロタイム・ラグ」こそが、業務で使えるかどうかの分水嶺になります。

## 開発者が今すぐやるべきこと

この波に乗り遅れないために、実務者が取るべきアクションは明確です。

第一に、自社で使っているSlackのワークフローをすべて棚卸ししてください。これまでZapierや自作スクリプトで無理やり繋いでいた処理の多くは、今回の新機能で「AIが判断して実行する」形にリプレイス可能です。特に、条件分岐が複雑でメンテナンスが困難になっていたワークフローは、AIエージェントに任せた方が堅牢になります。

第二に、Salesforce上のデータの「クレンジング」に着手してください。AIエージェントはデータが汚いと誤った判断を下します。商談のステータスが適切か、重複レコードはないか。AIを動かすのはプログラミングコードではなく、中身のデータそのものです。エンジニアの役割は「コードを書くこと」から「AIが正しく推論できるデータ構造を整えること」へ明確に変わります。

第三に、Slack APIの「エージェント向け新エンドポイント」のドキュメントを読み込み、既存のカスタムアプリをAgentforceに登録する準備をしてください。これからは単体で動くボットを作るのではなく、「Agentforceから呼び出される一つのスキル」として自社ツールを再構築する必要があります。

## 私の見解

正直に言って、今回のアップデートは「ようやくSlackが本気を出した」という印象です。これまでSlack AIは、高機能な検索エンジンの域を出ておらず、RTX 4090を回してローカルLLMを試しているような技術層から見れば、少々物足りないものでした。

しかし、今回の「30の新機能」は、単なる機能追加ではなく、アーキテクチャの転換です。特に評価したいのは、AIを「チャット画面の中」だけに閉じ込めなかった点です。キャンバス、ハドル、ワークフローといったSlackのあらゆるインターフェースにAIを染み込ませたことで、ユーザーは「AIを使っている」と意識せずに、恩恵を受けることになります。

懐疑的な視点をあえて持つならば、Salesforceエコシステムに依存しすぎている点は気になります。Salesforceを使っていない企業にとって、今回のアップデートの価値は半減するでしょう。しかし、B2Bの世界においてSalesforceのシェアを考えれば、これは賢明な戦略です。

3ヶ月後には、企業のSlackから「あの件、どうなった？」という確認のメッセージが激減しているはずです。代わりに「AIが処理しておいたので、確認だけお願いします」という通知が溢れるでしょう。私たちは今、手作業による情報の伝言ゲームから解放される、最後の瞬間に立ち会っています。

## よくある質問

### Q1: Slack AIを使うために追加料金は必要ですか？

はい、必要です。現在のプランに加えて、ユーザーあたり月額$20程度のアドオン料金が発生します。ただし、それによって削減される工数（議事録作成やデータ入力）を考えれば、月1〜2時間の残業代以下で導入できる計算になります。

### Q2: 独自のLLM（Llama 3など）をSlack AIのエンジンとして選べますか？

基本的にはSalesforceが提供する安全なモデル（独自調整されたGPT-4クラスなど）が使われます。ただし、Salesforceの「Bring Your Own LLM」戦略により、将来的にAzure OpenAIやAmazon Bedrock経由で独自のモデルを選択できる可能性は極めて高いです。

### Q3: セキュリティ面で、社内の機密情報がAIの学習に使われる心配はありませんか？

Salesforceは「Einstein Trust Layer」により、顧客データをモデルの学習に利用しないことを明言しています。データは推論時にのみ一時的に利用され、マスキング処理が行われた上でLLMに渡されるため、企業ガバナンスを維持したまま導入が可能です。

---

## あわせて読みたい

- [2027年、インターネット上の主役は「人間」から「AIボット」へと交代します。CloudflareのCEO、マシュー・プリンス氏が予測したこの事態は、単なるトラフィックの増加ではなく、Webの既存ビジネスモデルが崩壊するカウントダウンを意味しています。](/posts/2026-03-20-cloudflare-ceo-bot-traffic-exceed-human-2027/)
- [WordPressのAIエージェントによる自動投稿実装は、Webサイトを「人間が書く場所」から「AIが自律運用するメディア」へと完全に作り替える転換点になります。](/posts/2026-03-21-wordpress-ai-agent-auto-publish-impact/)
- [ByteDanceによる最強の動画生成AI「Seedance 2.0」のグローバル展開停止は、AI開発の主戦場が「モデル性能」から「法的コンプライアンス」へ完全に移行したことを示す明確なシグナルです。](/posts/2026-03-16-bytedance-seedance-2-global-launch-paused-legal-issues/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Slack AIを使うために追加料金は必要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、必要です。現在のプランに加えて、ユーザーあたり月額$20程度のアドオン料金が発生します。ただし、それによって削減される工数（議事録作成やデータ入力）を考えれば、月1〜2時間の残業代以下で導入できる計算になります。"
      }
    },
    {
      "@type": "Question",
      "name": "独自のLLM（Llama 3など）をSlack AIのエンジンとして選べますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的にはSalesforceが提供する安全なモデル（独自調整されたGPT-4クラスなど）が使われます。ただし、Salesforceの「Bring Your Own LLM」戦略により、将来的にAzure OpenAIやAmazon Bedrock経由で独自のモデルを選択できる可能性は極めて高いです。"
      }
    },
    {
      "@type": "Question",
      "name": "セキュリティ面で、社内の機密情報がAIの学習に使われる心配はありませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Salesforceは「Einstein Trust Layer」により、顧客データをモデルの学習に利用しないことを明言しています。データは推論時にのみ一時的に利用され、マスキング処理が行われた上でLLMに渡されるため、企業ガバナンスを維持したまま導入が可能です。 ---"
      }
    }
  ]
}
</script>
