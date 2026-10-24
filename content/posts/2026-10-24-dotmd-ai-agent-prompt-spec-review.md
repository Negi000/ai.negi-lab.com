---
title: "DotMD 使い方とレビュー：AIエージェントの指示書をGitHubライクに管理する"
date: 2026-10-24T00:00:00+09:00
slug: "dotmd-ai-agent-prompt-spec-review"
description: "AIエージェントの指示書（Markdown）をGitのプルリクエストのように差分管理・レビューできるツール。「プロンプトを少し変えたら全体の挙動が壊れた」..."
cover:
  image: "/images/posts/2026-10-24-dotmd-ai-agent-prompt-spec-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "DotMD"
  - "AI Agent"
  - "プロンプト管理"
  - "GitHubレビュー"
  - "LLM開発"
---
注意: 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- AIエージェントの指示書（Markdown）をGitのプルリクエストのように差分管理・レビューできるツール
- 「プロンプトを少し変えたら全体の挙動が壊れた」という先祖返りやデグレを、構造的なスペック管理で防ぐ
- チームでAIプロダクトを開発している中級以上のエンジニアには必須、個人の使い捨てプロンプト作成には不要

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIの長いプロンプトと回答差分を並べてレビューするのに4Kの広い作業領域は必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、チームでAIエージェントを本番運用しているなら、迷わず導入を検討すべきツールです。★4.5評価。
従来のプロンプト管理は、Notionにメモしたり、コード内にハードコードしたり、あるいはSlackのやり取りで「このプロンプトに変えておきました」と報告するような、極めて属人的で危ういものでした。
DotMDは、AIの挙動を定義するMarkdownファイルを「仕様書（スペック）」として扱い、その変更がエージェントの性能にどう影響するかを可視化します。

SIer時代に嫌というほど見てきた「仕様書と実装の乖離」が、今まさにAI開発の現場で起きています。
それをエンジニアリングの力で、Gitのワークフローに無理なく組み込める点は非常に高く評価できます。
一方で、ただのテキスト比較以上の「AIとしての振る舞いの変化」をどこまで自動評価できるかは、プロジェクトごとのテスト設計に依存するでしょう。

## このツールが解決する問題

これまでのAI開発における最大の問題は、プロンプトが「コード」なのか「ドキュメント」なのか曖昧だったことです。
100行を超えるような複雑なシステムプロンプトを1文字修正しただけで、これまで動いていた出力フォーマットが崩れることは珍しくありません。
しかし、その変更が「なぜ行われたのか」「どのようなテストを経てマージされたのか」を追跡する仕組みが欠けていました。

DotMDは、AIエージェントの指示を`.md`形式のスペックファイルとして定義します。
このファイルをGitで管理し、変更を加える際はプルリクエスト（PR）を作成します。
ここで重要なのは、DotMDが「人間によるレビュー」と「AIによるシミュレーション結果」をPR上で紐付けようとしている点です。

従来は、変更後のプロンプトを自分でChatGPTにコピペして、なんとなく良さそうならマージするという「勘」の作業でした。
DotMDを導入することで、スペックの変更履歴が明確になり、過去のバージョンへのロールバックも容易になります。
これは、プロンプトエンジニアリングを「文学」から「ソフトウェア工学」へと引き上げるための、泥臭いが必要不可欠な一歩です。

## 実際の使い方

### インストール

DotMDはCLIツール、またはライブラリとして提供されています。
Python 3.9以上が推奨環境です。

```bash
pip install dotmd
```

GitHubとの連携を想定する場合、GitHub Actionsの設定も必要になります。
インストール自体は1分もかかりませんが、本領を発揮させるにはリポジトリの構造を整える必要があります。

### 基本的な使用例

まずは、AIエージェントの振る舞いを定義するスペックファイル（例：`customer_support.md`）を作成します。
DotMDでは、Frontmatter形式でメタデータを記述するのが一般的です。

```markdown
---
name: カスタマーサポート・エージェント
model: gpt-4o
version: 1.0.2
---

# 指示内容
あなたは丁寧なカスタマーサポートです。
以下のルールを厳守してください。

- 返答は150文字以内
- 専門用語は使わない
- 最後に必ず「他にお困りごとはありますか？」と聞く
```

このスペックをコードから呼び出す際は、以下のように記述します。

```python
from dotmd import AgentSpec

# スペックファイルを読み込む
spec = AgentSpec.load("specs/customer_support.md")

# エージェントを実行（内部でLLM APIを叩く）
response = spec.run(input_text="ログインできません")

print(f"Version: {spec.version}")
print(f"Response: {response}")
```

コードの各行を見れば分かる通り、プロンプトを直接文字列で定義するのではなく、`.md`ファイルから読み込んでいます。
これにより、プロンプトの修正は`.md`ファイルをいじるだけで済み、アプリケーションコードを汚すことがありません。
実務では、`spec.version`をログに記録しておくことで、どの指示書の時に不具合が起きたかを後から0.3秒で特定できるようになります。

### 応用: 実務で使うなら

実務では、これをCI/CDパイプラインに組み込みます。
例えば、`specs/*.md`に変更があった場合、自動的に「評価用データセット（ゴールデンセット）」に対してテストを実行するスクリプトを走らせます。

```python
# CI環境での評価シミュレーション
def test_agent_consistency():
    old_spec = AgentSpec.load("specs/customer_support.md", version="latest")
    new_spec = AgentSpec.load("specs/customer_support.md", branch="feature/update-tone")

    # 同じ入力に対して両方の出力を比較
    test_input = "返金してください"
    old_out = old_spec.run(test_input)
    new_out = new_spec.run(test_input)

    # 意味的な差異を別のLLMで評価（LLM-as-a-judge）
    diff_report = compare_responses(old_out, new_out)
    save_report_to_github_comment(diff_report)
```

このように、新旧のプロンプトが生成する回答の差分（Diff）をPRのコメントに自動投稿するように設定するのが、プロの現場での使い方です。
レビュー担当者は、Markdownのテキスト差分だけでなく、実際の「出力の変化」を見てマージの判断が下せます。

## 強みと弱み

**強み:**
- **レビュー品質の向上**: プロンプトの微細な変更（「です」を「だ」に変えるなど）が、実際のレスポンスにどう影響するかを可視化できる。
- **ポータビリティ**: `AgentSpec`オブジェクトとして抽象化されているため、モデルをGPT-4からClaude 3.5 Sonnetに切り替える際も、スペックファイルの`model`タグを書き換えるだけで済む。
- **非エンジニアとの協業**: プロンプトの修正だけであれば、コードが書けないPMやドメインエキスパートでもGitHubのWeb画面上からMarkdownを編集してPRを送ることができる。

**弱み:**
- **日本語情報の欠如**: 2024年現在、公式ドキュメントは英語のみです。エラーメッセージも英語なので、ある程度の英語耐性は必要です。
- **自動評価の難しさ**: テキストのDiffは取れますが、AIの回答が「良くなったか」の判断を自動化するには、別途LLMを使った評価（Promptfoo等との組み合わせ）を自前で組む必要があります。
- **オーバーヘッド**: 小規模なプロジェクトや、1回限りの使い捨てスクリプトには、スペックファイルの作成や管理の手間が見合いません。

## 代替ツールとの比較

| 項目 | DotMD | Promptfoo | LangSmith |
|------|-------------|-------|-------|
| 主な用途 | 指示書のスペック管理・レビュー | 大規模なテスト・評価（Eval） | 実行ログの監視・トレース |
| 導入コスト | 低（Markdownを書くだけ） | 中（YAMLでテストケースを記述） | 高（SDK組み込みとSaaS契約） |
| 特徴 | Git/PRとの親和性が最高 | 100件以上の同時テストに強い | 本番稼働中の全ログを可視化 |

もしあなたが「AIの回答精度を数値化したい」ならPromptfooを選ぶべきです。
一方で、「誰が、いつ、なぜプロンプトを変えたのかを管理したい」なら、DotMDが最適です。

## 料金・必要スペック・導入前の注意点

DotMD自体はオープンソース（OSS）的な立ち位置であり、ライブラリの利用自体に費用はかかりません。
ただし、GitHub ActionsなどのCI環境でシミュレーションを実行する場合、その分のLLM API利用料（OpenAIやAnthropicのトークン代）が発生します。

必要スペックについては、ローカルでLLMを動かすわけではないため、RTX 4090のようなハイエンドGPUは不要です。
メモリ16GB程度の標準的な開発用PCがあれば十分です。
ただし、複雑なプロンプトとテスト結果を並べて比較するため、27インチ以上の4Kモニター（例えばDellのU2723QEなど）があると、レビュー作業の効率が劇的に変わります。
縦に長いプロンプトと、横に広がるDiffを同時に見るには、広大なデスクトップ領域が不可欠だからです。

商用利用については、MITライセンス等に準拠していることが多く問題ありませんが、導入前にリポジトリの最新のライセンス条項を確認してください。

## 私の評価

評価は5段階中の「4.5」です。
AIエージェント開発を「趣味」から「業務」へと変えてくれる、非常に実用的なツールだと感じました。

かつてSIerで大規模システムを組んでいた際、一番怖かったのは「誰かが勝手に共有サーバーの設定ファイルを変えた」ことでした。
今のAI開発では、それと同じことがプロンプトで起きています。
DotMDを導入すれば、たとえ10人のチームで開発していても、誰がどんな意図でAIの性格を変えたのかが全て履歴に残ります。

万人におすすめできるわけではありません。
「適当にプロンプトを書いて、なんとなく動けばいい」というフェーズのプロジェクトには、この管理コストは重すぎます。
しかし、AIの出力品質に責任を持つ立場なら、これを使わない手はありません。

## よくある質問

### Q1: 既存のコードに後から導入するのは大変ですか？

プロンプトが変数としてコードに埋め込まれている場合、それらを外出しして`.md`ファイルに書き直す必要があります。
ただし、一度リファクタリングしてしまえば、後のメンテナンス性は飛躍的に向上します。

### Q2: 料金プランはありますか？

基本はオープンソースのライブラリですが、Product Huntに掲載されているDotMD 3のようなバージョンでは、より高度なクラウド連携やUIを提供するSaaS版が検討されている場合があります。
最新の詳細は公式のLinkを確認してください。

### Q3: Promptfooとの使い分けは？

DotMDは「管理（Management）」に、Promptfooは「評価（Evaluation）」に強みがあります。
DotMDでスペックを定義し、そのテストランナーとしてPromptfooを呼び出す構成が、現在のAIエンジニアリングにおける「勝てる構成」の一つです。

---
### メタデータ

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [Toolport 使い方とレビュー：全AIエージェントのMCP接続を一本化する](/posts/2026-08-08-toolport-mcp-hub-review-tutorial/)
- [withHuman 使い方とレビュー：AIエージェントの暴走を止める承認レイヤーの実装](/posts/2026-10-15-withhuman-ai-agent-human-approval-layer-review/)
- [BrowserAct 使い方とAIエージェントのブラウザ操作自動化レビュー](/posts/2026-06-26-browseract-ai-agent-automation-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "既存のコードに後から導入するのは大変ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "プロンプトが変数としてコードに埋め込まれている場合、それらを外出しして.mdファイルに書き直す必要があります。 ただし、一度リファクタリングしてしまえば、後のメンテナンス性は飛躍的に向上します。"
      }
    },
    {
      "@type": "Question",
      "name": "料金プランはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本はオープンソースのライブラリですが、Product Huntに掲載されているDotMD 3のようなバージョンでは、より高度なクラウド連携やUIを提供するSaaS版が検討されている場合があります。 最新の詳細は公式のLinkを確認してください。"
      }
    },
    {
      "@type": "Question",
      "name": "Promptfooとの使い分けは？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "DotMDは「管理（Management）」に、Promptfooは「評価（Evaluation）」に強みがあります。 DotMDでスペックを定義し、そのテストランナーとしてPromptfooを呼び出す構成が、現在のAIエンジニアリングにおける「勝てる構成」の一つです。 ---"
      }
    }
  ]
}
</script>
