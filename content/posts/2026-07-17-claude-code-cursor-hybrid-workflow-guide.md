---
title: "Claude CodeとCursorを併用してGitHub Issueを自動解決する最強のAI開発環境構築ガイド"
date: 2026-07-17T00:00:00+09:00
slug: "claude-code-cursor-hybrid-workflow-guide"
cover:
  image: "/images/posts/2026-07-17-claude-code-cursor-hybrid-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AIエージェント 開発環境"
  - "Anthropic API 活用"
---
**所要時間:** 約40分 | **難易度:** ★★★★☆

## この記事で作るもの

- Cursorでコードを書き、Claude Code（CUIエージェント）で「テスト実行・デバッグ・GitHub Issueの自動修正」を完結させるハイブリッド開発フローを構築します。
- 最終的に、GitHub上のバグ報告（Issue）を検知し、Claude Codeが自律的にコードを修正・テストしてPR（プルリクエスト）を作成するまでの流れを自動化します。
- 前提知識：PythonまたはNode.jsの基礎、ターミナルの基本操作、GitHubリポジトリの運用経験。
- 必要なもの：Claude APIキー、Cursor Proプラン（推奨）、Node.js v18以上。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">複数のAIツールとDockerを同時起動する開発環境には32GB以上のメモリが必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

この環境を構築する前に、コスト面をシビアに見積もる必要があります。
まずCursorは月額$20のProプランが必須です。
無料枠では「Composer」によるマルチファイル編集の回数が制限され、実務ではストレスが溜まります。

次にClaude Codeですが、これはAnthropicの公式APIを直接叩くため、従量課金となります。
1件の複雑なバグ修正（ファイルの読み込み、テスト実行、3〜4回の試行）で、およそ$0.5〜$2.0程度のAPIコストがかかると考えてください。
毎日10回これを行うと、月間で数万円の請求が来る可能性があります。

ハードウェアについては、LLM自体はクラウド側で動くため高価なGPUは不要です。
ただし、Cursorのインデックス作成やローカルでのテスト実行を快適にするため、MacであればApple Silicon（M2/M3/M4）のメモリ32GB以上を強く推奨します。
16GBだと、Dockerとブラウザ、IDEを同時に立ち上げた際にスワップが発生し、AIのレスポンス以前にPCの動作がボトルネックになります。

## なぜこの方法を選ぶのか

現在、AIコーディングツールは「Cursor」と「Claude Code」の2強状態ですが、それぞれに明確な弱点があります。
Cursor（GUI）は直感的なコード編集や全体のディレクトリ構造の把握に優れていますが、ターミナルでの複雑なコマンド実行を伴う自律的なタスク（例：エラーが出るまでテストを回し続ける）には不向きです。

一方で、AnthropicがリリースしたClaude Code（CUI）は、ターミナルそのものをAIが操作するエージェント型です。
「テストが通るまでソースを直して」という丸投げの指示に対し、自分で`pytest`を叩き、ログを読み、修正し、再度テストするループを勝手に回してくれます。

これらを併用し、「人間がCursorで設計し、Claude Codeが現場仕事（デバッグ・修正）を完結させる」体制を組むのが、2025年現在で最も生産性が高いアプローチです。
Aiderなどの他ツールと比較しても、Claude 3.5 Sonnetの性能を100%引き出せる公式ツール（Claude Code）の安定感は群を抜いています。

## Step 1: 環境を整える

まずはClaude Codeをインストールし、Cursorから呼び出せる状態を作ります。

```bash
# Claude Codeのインストール（Node.js環境が必要）
npm install -g @anthropic-ai/claude-code

# インストールの確認
claude --version

# 初回ログインと認証
claude auth login
```

`npm install -g`でグローバルインストールするのは、プロジェクトを横断してどこからでもエージェントを呼び出すためです。
Claude Codeは最新のClaude 3.5 Sonnet（New）をデフォルトで使用するため、APIドキュメントを読み込む必要すらありません。

⚠️ **落とし穴:**
Macのデフォルトターミナル（Terminal.app）ではなく、iTerm2やCursor内蔵ターミナルを使用してください。
Claude CodeはリッチなUIを表示するため、古いターミナルだと表示が崩れたり、権限不足でコマンド実行がブロックされたりすることがあります。
また、Node.jsのバージョンが古い（v16以下）と、内部で使用しているライブラリが動かないため、必ず`node -v`でv18以上であることを確認してください。

## Step 2: 基本の設定

Claude Codeの挙動を制御するための設定ファイルを作成します。
プロジェクトのルートディレクトリに`.clauderc`（または環境変数）を設定し、AIが「やっていいこと」と「いけないこと」を明確にします。

```bash
# プロジェクトごとに推奨設定を入れる
claude config set auto_approvals false
```

`auto_approvals`を`false`にする理由は、AIが誤って`rm -rf /`のような破壊的なコマンドを実行するのを防ぐためです。
慣れてきたら特定の読み取りコマンド（`ls`, `cat`など）だけを許可することも可能ですが、最初は必ず人間が承認するステップを挟みます。

次に、Cursor側でClaude Codeを効率よく使うための`.cursorrules`を作成します。
これはCursorのAIに対して「ターミナルの操作はClaude Codeに任せるので、お前はコードの全体構造を教えろ」と役割分担を指示するものです。

```text: .cursorrules
- コードの修正案を出す際は、必ずテストコードもセットで提示すること
- ターミナルでのデバッグが必要な場合は、ユーザーに「Claude Codeを起動して XXX を実行してください」と促すこと
- 実装の詳細はClaude Codeに任せ、Cursor側では高レベルなリファクタリング案を優先する
```

## Step 3: 動かしてみる

実際にClaude Codeを起動して、現在のプロジェクトの状況を把握させます。

```bash
# ターミナルで起動
claude
```

起動後、以下のプロンプトを入力してください。

```text
/stats
今のプロジェクトの構成を分析して、不足しているテストケースを3つ挙げて。
```

### 期待される出力

```
[Claude Code]
分析が完了しました。
1. user_auth.py の異常系（パスワード間違い）のテストがありません。
2. APIのタイムアウト時のハンドリングが未検証です。
3. db_connection.py のリトライロジックのテストが不足しています。

テストコードを作成して実行しましょうか？ (y/n)
```

ここで`y`を押すと、Claude Codeは自ら`touch tests/test_auth_edge.py`を実行し、中身を書き込み、`pytest`を実行します。
私たちがコードを1行も書かずに、テストカバレッジが向上する瞬間です。
CursorのGUI上では、Claude Codeが作成したファイルがリアルタイムで反映されるのが確認できるはずです。

## Step 4: 実用レベルにする

ここからが本番です。GitHub Issueを読み取り、修正してPRを送る一連の流れを「AIエージェント」として実行させます。
まず、GitHub CLI（gh）をインストールしておいてください。Claude Codeはローカルのツールを自由に使いこなします。

以下の手順をClaude Codeのプロンプトに流し込みます。

```text
以下の手順を自律的に実行して。
1. `gh issue list` で最新のバグ修正Issueを1件取得。
2. Issueの内容から原因を特定し、再現テストを作成。
3. 再現テストが失敗することを確認。
4. ソースコードを修正してテストをパスさせる。
5. `gh pr create` で修正内容を送信。
```

実際に私がこのフローを試した際、最初は「ライブラリの依存関係」でエラーが出ました。
しかし、Claude Codeはそこで止まらずに、自ら`pip install`を実行して環境を整え、最終的にPRまで漕ぎ着けました。

Cursorで同じことをやろうとすると、「エラーが出ました、どうしますか？」といちいち人間に聞いてきますが、Claude Codeは「エラーが出たのでXXXを試します」と事後報告に近い形で進めてくれます。
この「自律性の差」が、開発速度を3倍以上に引き上げます。

```python
# 参考：Claude Codeが自動生成した再現テストの例
import pytest
from app.services import payment_processor

def test_insufficient_funds_fix():
    # Issue #142 で報告された「残高不足時に500エラーになる」問題を再現
    with pytest.raises(ValueError) as excinfo:
        payment_processor.charge(user_id=999, amount=1000000)
    assert "Insufficient funds" in str(excinfo.value)
```

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Command not found: claude` | パスが通っていない | `npm bin -g`でパスを確認し、PATHに追加する |
| `Context window exceeded` | ファイルを読み込みすぎ | `.claudeignore`を作成し、`node_modules`やログを除外する |
| APIの応答が遅い | トラフィックの混雑 | `claude config set model claude-3-5-haiku`で一時的にモデルを軽くする |

## 次のステップ

この環境が構築できたら、次は「MCP（Model Context Protocol）」の導入を検討してください。
MCPを使えば、Claude CodeにGoogle検索権限を与えたり、Slackのメッセージを読み取らせたりすることが可能になります。

例えば、「Slackで報告されたバグをClaude Codeが検知し、自動でローカル環境にブランチを切って修正を始める」という、真の意味でのAIエンジニアをチームに迎え入れることができます。
まずはGitHubの特定ラベルが付いたIssueを自動で処理するスクリプトを、Claude Code自身に書かせてみることから始めてみてください。
「自分の仕事を自分で自動化させる」というループに入ったとき、エンジニアの生産性は指数関数的に向上します。

## よくある質問

### Q1: Cursorだけで十分ではないのですか？

CursorのComposerは、ファイル編集には非常に強力です。しかし「ターミナルでテストを回し、その結果を受けて再度考え直す」というループの速度と自律性は、現在のClaude Codeの方が圧倒的に上です。エディタ（Cursor）と、実行エージェント（Claude Code）という使い分けが最適解です。

### Q2: API料金が高くなりそうで怖いです。

Claude Code内で`/usage`コマンドを打つと、そのセッションで消費したトークン量と金額の目安が表示されます。作業が終わるたびに確認する癖をつければ、数万円の使いすぎを防げます。また、簡単なタスクにはHaikuモデルを指定するのも手です。

### Q3: セキュリティ的にソースコードを送信しても大丈夫ですか？

AnthropicのAPI利用規約では、API経由で送信されたデータはモデルの学習に利用されません。ただし、社内規定で外部クラウドへのコード送信が禁止されている場合は、以前私が紹介した「Llama.cpp + Continue」による完全ローカル環境の構築を検討してください。

---

## あわせて読みたい

- [Claude Code 使い方とCursor併用の最強コーディング環境構築ガイド](/posts/2026-07-08-claude-code-cursor-workflow-guide/)
- [Claude CodeとCursorを使い分け！最強のAI開発環境構築ガイド](/posts/2026-06-27-claude-code-cursor-workflow-guide/)
- [Claude CodeとCursorを併用する最強のAIコーディング環境構築ガイド](/posts/2026-07-13-claude-code-cursor-hybrid-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Cursorだけで十分ではないのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "CursorのComposerは、ファイル編集には非常に強力です。しかし「ターミナルでテストを回し、その結果を受けて再度考え直す」というループの速度と自律性は、現在のClaude Codeの方が圧倒的に上です。エディタ（Cursor）と、実行エージェント（Claude Code）という使い分けが最適解です。"
      }
    },
    {
      "@type": "Question",
      "name": "API料金が高くなりそうで怖いです。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Code内で/usageコマンドを打つと、そのセッションで消費したトークン量と金額の目安が表示されます。作業が終わるたびに確認する癖をつければ、数万円の使いすぎを防げます。また、簡単なタスクにはHaikuモデルを指定するのも手です。"
      }
    },
    {
      "@type": "Question",
      "name": "セキュリティ的にソースコードを送信しても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "AnthropicのAPI利用規約では、API経由で送信されたデータはモデルの学習に利用されません。ただし、社内規定で外部クラウドへのコード送信が禁止されている場合は、以前私が紹介した「Llama.cpp + Continue」による完全ローカル環境の構築を検討してください。 ---"
      }
    }
  ]
}
</script>
