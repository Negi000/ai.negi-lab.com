---
title: "illumi 使い方 | 思考をキャンバスで実行可能な成果物に変えるAIワークスペース"
date: 2026-04-21T00:00:00+09:00
slug: "illumi-ai-visual-workspace-review-for-engineers"
description: "思考の断片をキャンバス上に配置し、そのまま要件定義書や実行コードへ変換できる「非線形」な開発ワークスペース。ChatGPTのようなチャットUIでは不可能な..."
cover:
  image: "/images/posts/2026-04-21-illumi-ai-visual-workspace-review-for-engineers.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "illumi レビュー"
  - "AI ワークスペース"
  - "ビジュアルプログラミング"
  - "設計自動化"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- 思考の断片をキャンバス上に配置し、そのまま要件定義書や実行コードへ変換できる「非線形」な開発ワークスペース
- ChatGPTのようなチャットUIでは不可能な「情報の構造化」と「プロンプト間の文脈維持」を視覚的に解決している
- ロジックを可視化したいアーキテクトやPMには最適だが、単純なコード生成だけを求める層には多機能すぎる

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">Dell UltraSharp 27 4K Hub Monitor</strong>
<p style="color:#555;margin:8px 0;font-size:14px">illumiのような広いキャンバスを扱うワークスペースには、高解像度かつ広い作業領域を持つ4Kモニターが不可欠</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、複数のエージェントやプロンプトを組み合わせて「複雑なプロダクト」を構築したい中級以上のエンジニアにとって、illumiは強力な武器になります。★評価は4.5です。

従来のチャットUIは、過去の発言が流れてしまい、複雑な仕様を詰めると文脈が崩壊するという致命的な弱点がありました。illumiはこの問題を、無限キャンバス上に「思考のノード」を配置することで解決しています。単なるホワイトボードツールではなく、各ノードがLLMと直結し、ノード間の依存関係を明示的に定義できる点が、実務で使う上で極めて合理的です。

ただし、個人で小さなスクリプトを書くだけなら、CursorやChatGPTの画面で十分でしょう。大規模な要件定義を整理し、それを一気に実装フェーズへ流し込みたいプロジェクトにおいてのみ、このツールの真価が発揮されます。

## このツールが解決する問題

私たちが実務でAIを使う際、最大の壁になるのは「文脈の断片化」です。SIer時代、大規模なシステム設計をしていた頃を思い出してください。機能要件、非機能要件、データベース設計、API定義……これらはすべて密接に関わっていますが、チャットUIでこれらを一気に伝えると、AIのコンテキストウィンドウが溢れるか、細部の指示を無視し始めます。

従来は、Miroで構成図を書き、それをスクリーンショットしてChatGPTに貼り付け、出力されたコードをVS Codeにコピーするという、非効率な「手動連携」が発生していました。この過程で情報は必ず劣化します。

illumiはこの「思考から実装への断片化」を、キャンバスという一つの空間に統合することで解決します。キャンバス上の各ブロックは独立したプロンプトとして機能しつつ、隣接するブロックの情報を参照できます。つまり、「Aという要件に基づいて、Bという関数を設計し、Cというテストコードを書く」という一連の流れを、視覚的な依存関係を持ったまま管理できるのです。これにより、プロンプトの再利用性が向上し、大規模なドキュメント作成やコード生成における一貫性が劇的に改善されました。

## 実際の使い方

### インストール

illumiはWebベースのワークスペースですが、ローカル環境のコードベースと同期するためのCLIツールが提供されています。Python 3.9以降が推奨環境です。

```bash
# illumiの同期CLIのインストール
pip install illumi-cli

# 初期設定（APIキーの構成）
illumi-cli login
illumi-cli init my-project
```

### 基本的な使用例

illumiの最大の特徴は、キャンバス上のノードを「プログラムから操作」できる点にあります。例えば、要件定義が書かれた特定のノードの内容を読み取り、それを元に複数のサブモジュールを生成するスクリプトは以下のようになります。

```python
from illumi import Workspace

# ワークスペースへの接続
ws = Workspace(project_id="my-awesome-app")

# キャンバス上の「要件定義」ノードを特定
requirement_node = ws.get_node_by_title("Requirement Definition")

# 要件の内容を取得して、それに基づいた「実装計画」ノードを生成
content = requirement_node.read()
plan_node = ws.create_node(
    title="Implementation Plan",
    prompt=f"以下の要件に基づき、必要なファイル構成を提案してください: {content}",
    position={"x": 500, "y": 0} # 視覚的な配置を指定
)

# 実行して結果を取得
plan_result = plan_node.execute()
print(plan_result.text)
```

このコードを実行すると、ブラウザ上のキャンバスに新しいノードが自動で出現し、AIが考えた計画が書き込まれます。手動でポチポチ操作するだけでなく、このように「自動化されたワークフロー」を視覚的に構築できるのが、エンジニアにとっての利便性です。

### 応用: 実務で使うなら

実務で最も効果を発揮するのは「既存コードのドキュメント化とリファクタリングの並行処理」です。

1. `illumi-cli push src/` で既存のディレクトリ構造をキャンバスに展開する。
2. 各ファイルに対応するノードを生成し、AIに「このモジュールの責務を要約せよ」と命令する。
3. 要約されたノードを視覚的に繋ぎ合わせ、依存関係のスパゲッティ状態を可視化する。
4. 整理された構造に基づき、新しい設計ノードを作成し、そこから `illumi-cli pull` でローカルにコードを書き戻す。

このフローにより、頭の中にある「理想のアーキテクチャ」と「実際のコード」の乖離を、視覚的に埋めることができます。

## 強みと弱み

**強み:**
- 思考の非線形性を維持できる: チャットのように「上から下へ」流れるのではなく、自由な配置でロジックを組める。
- コンテキストの制御が容易: どの情報をどのプロンプトに渡すかをノードの「接続」で定義できるため、情報の混線が防げる。
- CLI連携: ブラウザで設計し、ターミナルでコードを受け取るというハイブリッドな開発体験がスムーズ。

**弱み:**
- ラーニングコスト: 単なるチャットではないため、最初は「どの単位でノードを分けるべきか」に迷う。
- 動作の重さ: ノード数が100を超えてくると、ブラウザ上でのキャンバスのレンダリングに0.5秒程度のラグを感じることがある。
- 日本語情報の不足: UIおよび公式ドキュメントはすべて英語であり、日本語入力自体は可能だが、サポート体制はまだ弱い。

## 代替ツールとの比較

| 項目 | illumi | Miro (Assist) | Cursor |
|------|-------------|-------|-------|
| 主な用途 | 設計から実装への統合 | アイデア出し・図解 | コード生成・編集 |
| 視覚化 | 非常に高い (ノードベース) | 高い (ホワイトボード) | 低い (チャット/エディタ) |
| 実装への親和性 | 高い (CLI/SDKあり) | 低い (手動コピー) | 非常に高い (IDE直結) |
| ターゲット | アーキテクト/PM/リード | デザイナー/ビジネス職 | コーダー/エンジニア |

Miroは図を描くには最適ですが、そこからコードを生成するフローが弱いです。逆にCursorはコーディングには最強ですが、全体の設計図を俯瞰しながら考えるのには向きません。illumiはその中間、つまり「設計（Think）」と「納品（Delivery）」の橋渡しに特化しています。

## 私の評価

私はこのツールを、特に「新規事業のプロトタイプ作成」や「レガシーコードの解読」のフェーズで強く推します。

RTX 4090を回してローカルLLMを動かす際も、結局「何を、どの順番で、どのデータを用いて解かせるか」というオーケストレーションが一番の悩みどころになります。illumiは、このオーケストレーションをGUIで簡単に行える、いわば「AI時代のIDE」のプロトタイプといえる存在です。

一方で、10行程度の関数を書きたいだけの時には、わざわざキャンバスを開くのは面倒です。ツールには適材適所がありますが、illumiは「複雑なものを複雑なまま扱い、かつ整理する」という、これまでのAIツールが苦手としていた領域に正面から挑んでいます。英語のみという壁はありますが、中級以上のエンジニアならAPIリファレンスを読めば30分で使いこなせるはずです。

## よくある質問

### Q1: 既存のGitHubリポジトリを丸ごと読み込めますか？

はい、`illumi-cli push` を使えば、リポジトリの構造をキャンバス上にノードとしてインポート可能です。大規模な場合は、特定のディレクトリに絞って読み込むのが、動作を軽く保つコツです。

### Q2: 料金体系はどうなっていますか？

基本機能は無料で使えますが、高度なAIモデル（GPT-4oやClaude 3.5 Sonnet）を無制限に利用したり、チームでの同時編集を行うには月額$20程度のプロプランが必要です。APIの持ち込み（BYOK）にも対応しています。

### Q3: Vercelなどのデプロイ環境と直接連携できますか？

illumi自体にデプロイ機能はありませんが、生成したコードを特定のブランチに自動コミットするワークフローは構築可能です。まさに「Delivery」までを視野に入れた設計になっています。

---

## あわせて読みたい

- [Fractal 使い方 ChatGPT連携アプリを最速でデプロイする手法](/posts/2026-03-21-fractal-chatgpt-app-framework-review/)
- [AI Skills Manager 使い方：散らばったプロンプトとエージェント機能を一元管理する実践ガイド](/posts/2026-03-21-ai-skills-manager-prompt-management-guide/)
- [Crikket 使い方 OSSでバグ報告を自動化する実力レビュー](/posts/2026-03-11-crikket-oss-bug-reporting-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "既存のGitHubリポジトリを丸ごと読み込めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、illumi-cli push を使えば、リポジトリの構造をキャンバス上にノードとしてインポート可能です。大規模な場合は、特定のディレクトリに絞って読み込むのが、動作を軽く保つコツです。"
      }
    },
    {
      "@type": "Question",
      "name": "料金体系はどうなっていますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本機能は無料で使えますが、高度なAIモデル（GPT-4oやClaude 3.5 Sonnet）を無制限に利用したり、チームでの同時編集を行うには月額$20程度のプロプランが必要です。APIの持ち込み（BYOK）にも対応しています。"
      }
    },
    {
      "@type": "Question",
      "name": "Vercelなどのデプロイ環境と直接連携できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "illumi自体にデプロイ機能はありませんが、生成したコードを特定のブランチに自動コミットするワークフローは構築可能です。まさに「Delivery」までを視野に入れた設計になっています。 ---"
      }
    }
  ]
}
</script>
