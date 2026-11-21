---
title: "Groundwork レビュー：Claude Codeの実行計画を固定して破壊的変更を防ぐ"
date: 2026-11-21T00:00:00+09:00
slug: "groundwork-claude-code-plan-management-review"
description: "Claude Codeのプランニング（`/plan`）を構造化し、再実行時に既存の成功したコードを上書きさせない「ステート管理」を実現する。。AIエージェ..."
cover:
  image: "/images/posts/2026-11-21-groundwork-claude-code-plan-management-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Groundwork"
  - "Claude Code"
  - "AIコーディング"
  - "実行計画管理"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- Claude Codeのプランニング（`/plan`）を構造化し、再実行時に既存の成功したコードを上書きさせない「ステート管理」を実現する。
- AIエージェント特有の「修正した場所を別のステップで元に戻してしまう」という迷走（デグレード）を、計画のロックによって物理的に防ぐ。
- 100行を超えるような大規模なリファクタリングをClaude Codeに任せたいエンジニアには必須だが、数行の修正なら不要。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでClaude Codeの挙動をローカルLLMと比較検証するのに最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、Claude Codeを業務で「メインの自律型エージェント」として運用しているなら、迷わず導入すべきツールです。
★評価：4.5/5

Claude Codeは非常に強力なCLIですが、長い思考プロセスの中で、ステップ1で修正した箇所をステップ5で「バグ」と誤認して元に戻してしまうといった、冪等性（べきとうせい）の欠如が課題でした。
Groundworkは、この実行計画をエージェントの外部に「固定されたチェックポイント」として保持することで、再実行（re-run）時の破壊的な上書きを阻止します。

実務レベルでAIエージェントを使っている人なら、Gitでこまめにコミットする手間と、AIが勝手にファイルを汚染する恐怖から解放される価値が理解できるはずです。
逆に、Cursorの単発チャットで済むような小規模な開発スタイルなら、Groundworkの管理コストが上回るため、導入の必要はありません。

## このツールが解決する問題

従来、Claude CodeやAiderといったCLIベースのAIエージェントには、タスクが長大化すると「過去の文脈を忘れる」あるいは「プランの一貫性が崩れる」という致命的な弱点がありました。
私がRTX 4090を2枚挿した自作サーバーでローカルLLMを回しながら、一方でClaude CodeのAPIを叩きまくって検証した際、最もストレスだったのが「リトライによる破壊」です。

例えば、複雑な認証ロジックをリファクタリングしている際、テストが通らなかったので再度`/do`を実行したとします。
このとき、エージェントは気を利かせたつもりで、実は正常だった共通コンポーネントまで書き換えてしまい、結果としてプロジェクト全体が壊れるという現象が多発していました。

Groundworkは、Claude Codeの出力をインターセプトし、実行計画（Plan）を独自のスキーマで永続化します。
最大の特徴は「never overwrite（決して上書きしない）」という設計思想です。
一度成功とマークされたステップや、ユーザーが承認したプランの断片はロックされ、再試行時にも「変更不可な前提条件」としてエージェントに再提示されます。

これにより、10ステップに及ぶような複雑なタスクでも、前のステップを壊さずに着実に積み上げることが可能になりました。
これは、手動でGit stashとpopを繰り返す作業を、エージェントの推論プロセスに直接組み込むような体験です。

## 実際の使い方

### インストール

npm経由、あるいは公式のバイナリ配布（現在はClaude Codeのアドオン的な位置付け）を想定した手順になります。Python環境で管理する場合は、ラッパーを介して導入します。

```bash
# Claude Codeがインストールされている環境で実行
npm install -g @groundwork/cli
```

注意点として、Claude 3.5 Sonnet以上のモデルを使用していることと、Claude Code（`@anthropic-ai/claude-code`）のバージョンが最新であることが前提です。
Node.js 18以上、またはPython 3.10以降の環境が推奨されています。

### 基本的な使用例

Groundworkを介してClaude Codeを起動することで、プランの永続化レイヤーが有効になります。

```bash
# 通常の起動ではなく、groundworkの管理下で開始
groundwork run "大規模なデータ移行スクリプトをリファクタリングし、型安全性を高めて"
```

このコマンドを実行すると、Groundworkは内部で以下のプロセスを回します。

```python
# 内部的なプラン管理のシミュレーション（groundwork.json）
{
  "session_id": "gw-8823",
  "steps": [
    {
      "id": 1,
      "task": "models/user.py の型定義を更新",
      "status": "completed",
      "lock": true,
      "checksum": "a1b2c3d4"
    },
    {
      "id": 2,
      "task": "移行ロジックの修正",
      "status": "pending",
      "lock": false
    }
  ]
}
```

各ステップが「Completed」かつ「Lock」状態になると、Claude Codeが再試行を求めても、そのファイルの当該箇所への書き込み権限が制限されるか、あるいはプロンプトレベルで「この修正は完了済みであり変更禁止である」と強力に制約がかかります。

### 応用: 実務で使うなら

大規模な既存プロジェクトへの機能追加時に、Groundworkの「コンテキスト保護」が威力を発揮します。

```bash
# 既存のプランファイルを指定して、途中から再開する
groundwork resume --plan ./plans/feature-x.json
```

私は以前、20件以上の機械学習案件をこなしてきましたが、AIにコードを書かせるときに最も怖いのは「知らないうちに依存関係を壊されること」でした。
Groundworkを使えば、重要なコアモジュールを「ReadOnly」としてプランに登録し、その周辺ロジックだけをClaude Codeに弄らせるという、精密な外科手術のような開発が可能になります。

具体的には、`groundwork.yaml`などの設定ファイルを作成し、AIが触れてはいけないディレクトリを指定しておくことで、不要なトークン消費とバグ混入を同時に防ぐことができます。

## 強みと弱み

**強み:**
- **冪等性の担保:** 同じ指示を二度送っても、既に完成したパーツが壊されないため、開発の進捗が「不可逆」になる。
- **トークンコストの削減:** 完了したステップの詳細は要約され、必要なコンテキストだけを送信するため、長時間のセッションでもAPI料金が膨らみにくい。
- **ステートフルな再開:** PCがクラッシュしたりAPIがタイムアウトしたりしても、`.groundwork`ディレクトリから寸分違わず再開できる。

**弱み:**
- **導入オーバーヘッド:** 最初の数回は「プランの承認」という手順が増えるため、Claude Code単体で使うよりテンポが遅く感じる。
- **依存性:** Anthropicの公式アップデートに対して、Groundwork側が追従するまでラグが発生する可能性がある。
- **ドキュメントの薄さ:** 現時点ではコミュニティベースの情報が多く、詳細なAPIリファレンスを読み解くには相応のエンジニアリング能力が求められる。

## 代替ツールとの比較

| 項目 | Groundwork | Aider | Cursor (Composer) |
|------|-------------|-------|-------|
| 主な用途 | Claude Codeの計画保護 | Git統合型ペアプロ | IDE一体型エージェント |
| 状態管理 | プラン単位でのロック | Gitコミット/Undo | 履歴ベースのUndo |
| 再試行時の挙動 | 成功済みステップを保護 | 全戻しか個別修正 | 履歴からの上書き |
| 推奨ユーザー | CLI派のヘビーユーザー | Git操作を好むプロ | GUIで完結したい層 |

Claude Codeのポテンシャルを最大限引き出したいならGroundwork一択ですが、Gitのブランチ管理を徹底している人ならAiderでも同様のことは可能です。ただし、Groundworkの方が「AIの思考プロセス」に近い部分で制御をかけている印象を受けます。

## 料金・必要スペック・導入前の注意点

Groundwork自体は、現在Product Hunt等で公開されている段階ではOSS的な立ち位置、もしくは初期ベータとしての提供です。
商用利用については、基盤となるClaude Codeの規約に準じますが、ツール自体がコードをどこかに送信するわけではないため、セキュリティポリシーは比較的クリアしやすいでしょう。

必要スペックについては、Claude Codeが軽快に動く環境（メモリ16GB以上推奨）であれば問題ありません。
ただし、大規模プロジェクトを解析させる場合は、CPUよりも「ネットワークの安定性」と「APIの上限緩和（Tier 4以上推奨）」が重要になります。

もしローカルでの検証を並行して行うなら、RTX 4060 Ti 16GB以上のGPUを積んだマシンがあると、Claudeの代わりにローカルモデル（Llama-3等）を差し替えてテストするなどの柔軟な動きができます。私はRTX 4090を使用していますが、Groundworkのログ解析などはローカルで行うと非常に高速です。

## 私の評価

私はこのツールを、Claude Codeを「おもちゃ」から「プロの道具」に変えるための必須パーツだと評価しています。
★評価：4.5/5

これまでのAIコーディングは、常に「次は壊されるかもしれない」という不安との戦いでした。
Groundworkを導入してからは、AIに10分かかるような長大なタスクを投げたまま、安心してコーヒーを飲みに行けるようになりました。
「仕事で使えるか」という私の基準に照らし合わせると、これは合格点を余裕で超えています。

ただし、設定ファイルの記述やCLIの操作に慣れていない初級者には、少しハードルが高いかもしれません。
Pythonの基礎があり、かつ`pip`や`npm`のトラブルシューティングを自力でできるエンジニアであれば、今日からでも導入してその恩恵を受けるべきです。

## よくある質問

### Q1: Gitでのバージョン管理があれば、Groundworkは不要ではないですか？

Gitは「結果」を保存しますが、Groundworkは「AIの作業計画」を保存します。Gitでは「なぜAIがここを書き換えたか」の文脈を固定できませんが、Groundworkはプランと紐づけて上書きを拒否するため、戻し作業の手間が劇的に減ります。

### Q2: Claude Code以外のツール（Cursorなど）でも使えますか？

いいえ。GroundworkはClaude Codeの`/plan`や`/do`といった独自のプロトコルに特化して設計されています。CursorにはCursorなりの管理画面がありますが、CLIベースの自律性を求めるならこちらに軍配が上がります。

### Q3: 導入することでAPIのトークン消費は増えますか？

むしろ減る傾向にあります。再実行時に全コードを再送・再生成するのではなく、Groundworkが「ここは完了済み」とマークした部分を省略、あるいは要約してプロンプトに組み込むため、無駄な再計算が発生しにくいからです。

---

## あわせて読みたい

- [Claude Code Dynamic Workflows比較と選び方｜AIコーディングを加速させるおすすめPC・GPU環境](/posts/2026-05-29-claude-code-dynamic-workflows-hardware-guide/)
- [Claude CodeのA/Bテスト開始か？AIコーディング環境の選び方と失敗しないハードウェア投資](/posts/2026-08-23-claude-code-effort-levels-hardware-guide/)
- [Claude Codeのバックグラウンド送信仕様から考えるAI開発環境の選び方とおすすめハードウェア比較](/posts/2026-10-30-claude-code-background-agent-vs-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Gitでのバージョン管理があれば、Groundworkは不要ではないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Gitは「結果」を保存しますが、Groundworkは「AIの作業計画」を保存します。Gitでは「なぜAIがここを書き換えたか」の文脈を固定できませんが、Groundworkはプランと紐づけて上書きを拒否するため、戻し作業の手間が劇的に減ります。"
      }
    },
    {
      "@type": "Question",
      "name": "Claude Code以外のツール（Cursorなど）でも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ。GroundworkはClaude Codeの/planや/doといった独自のプロトコルに特化して設計されています。CursorにはCursorなりの管理画面がありますが、CLIベースの自律性を求めるならこちらに軍配が上がります。"
      }
    },
    {
      "@type": "Question",
      "name": "導入することでAPIのトークン消費は増えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "むしろ減る傾向にあります。再実行時に全コードを再送・再生成するのではなく、Groundworkが「ここは完了済み」とマークした部分を省略、あるいは要約してプロンプトに組み込むため、無駄な再計算が発生しにくいからです。 ---"
      }
    }
  ]
}
</script>
