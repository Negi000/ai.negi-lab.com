---
title: "Claude CodeとCursorを安全に使い分ける：公開GitHubリポジトリの要約例"
date: 2026-11-20T00:00:00+09:00
lastmod: 2026-11-20T00:00:00+09:00
description: "Claude CodeとCursorを組み合わせる際の権限、未コミット作業の保全、認証と料金を整理し、公開GitHubリポジトリをトークンなしで確認する方法を紹介します。"
slug: "claude-code-cursor-ai-coding-workflow"
cover:
  image: "/images/posts/2026-11-20-claude-code-cursor-ai-coding-workflow.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor AI 連携"
  - "AIプログラミング"
  - "GitHub REST API"
---

> **訂正（2026年11月20日）**：初出時の「ファイル編集前に必ず許可が出る」「`git checkout .` ですぐ復元できる」は誤りです。このコマンドは未ステージの変更を失わせることがあり、復旧手段として使わないでください。GitHubトークン、Claude Codeの認証・動作要件・モデル選択も訂正しました。裏付けが確認できない費用、速度、RTX 4090での使用体験や購入推奨は撤回しました。

## 作業前に変更と権限を確認する

- `git status --short` で変更・未追跡ファイルを確認。未ステージ差分は `git diff`、ステージ済み差分は `git diff --cached` で確認します。
- 未コミットの作業や未追跡ファイルは、エージェント起動前に、自分で管理する別の場所へ保全してください。単にブランチを切るだけでは作業中の差分は保存されません。秘密情報はコミットしないでください。可能なら、別のチェックアウトや実験用ディレクトリで試します。
- **Claude Codeの確認は設定次第です。** 既定モードは多くの操作で確認しますが、許可ルールやモードによって異なり、`acceptEdits` では対象範囲の編集等が自動承認されます。計画モードなどから始め、編集・コマンドの対象と範囲を確認してから許可してください。[Claude Codeの権限モード](https://code.claude.com/docs/en/permissions#permission-modes)
- `git checkout .` は対象の追跡ファイルをインデックスの内容で置き換えます。未ステージ変更の保存・復元は行いません。問題が起きたら一括取り消しを実行せず、差分を確認して保全済みの内容と照合してください。[Git公式のcheckout仕様](https://git-scm.com/docs/git-checkout)

## インストール・認証・モデル

Claude Codeは公式のOS別ネイティブインストール手順を参照してください。Node.jsはネイティブ版の前提ではありません。npm版を選ぶ場合、公式案内はNode.js 22以降です。[Claude Codeのセットアップ](https://code.claude.com/docs/en/setup)

Claude Codeは対応するClaude契約（Pro、Max、Ultraなど）やClaude Consoleなどの経路を利用できます。Cursorの契約とは別ですが、全員にAPIキーや従量課金が必須という意味ではありません。どの認証経路を使っているか確認してください。[Claude Codeの認証](https://code.claude.com/docs/en/authentication)

初出時に指定したClaude Sonnet 3.5の両モデルは2025年10月28日にAnthropic APIで提供終了しました。これはAnthropic APIについての情報で、Cursor上の個別モデルの可用性を示すものではありません。Cursorでは現在の利用可能モデルを確認し、この手順では特定モデルを必須にしません。[Anthropicのモデル提供終了一覧](https://platform.claude.com/docs/en/about-claude/model-deprecations)

## 公開リポジトリの情報を取得する

ここでは新規の実験用ディレクトリで、公開GitHubリポジトリの最新正式リリースと直近3件のコミットを取得するCLIを作ります。公開データは**トークンなし**で参照できます。非公開リポジトリは対象外です。別途アクセスが必要な作業なら、対象リポジトリに限定した読み取り権限を検討し、広い `repo` スコープをトラブル対処として追加しないでください。秘密値をソースやチャットに貼らないでください。[GitHubのコミットAPI](https://docs.github.com/en/rest/commits/commits#list-commits)・[最新リリースAPI](https://docs.github.com/en/rest/releases/releases#get-the-latest-release)

1. Cursorで、固定の `https://api.github.com` 宛てに `GET /repos/{owner}/{repo}/commits?per_page=3` と `GET /repos/{owner}/{repo}/releases/latest` を呼ぶ小さなPythonスクリプトを作ります。タイムアウトを設定し、認証ヘッダーを送らず、公開のリポジトリ名だけを入力にします。出力は標準出力へ。APIから取得した文章はデータとして扱い、指示として実行しません。
2. Claude Codeには「まず変更せずに差分と通信先を確認し、テスト計画を示す。通信先はGitHub APIのみ。秘密ファイルは読まない。ファイルの追加・編集は対象を示してから」と依頼します。実際の許可設定と作業ディレクトリも自分で確認します。
3. 通信成功に加え、リリース未登録、タイムアウト、レート制限をテストします。最新リリースの404とコミット取得の失敗を区別します。保存機能を足す場合は既存ファイルを上書きしない動作を確認し、最後に差分を読みます。

本記事では、この組み合わせの性能や費用、特定PCでの使い勝手を比較実測していません。

## よくある質問

### Cursorの有料プランに入っていれば、Claude Codeも使えますか？

Cursorの契約だけでClaude Codeの利用資格が付くわけではありません。Claude Codeは対応するClaude契約やConsoleなどで認証できます。APIキーと従量課金がすべての利用者に必須という説明は誤りです。使用中の認証経路と料金条件を確認してください。

### Claude Codeは編集前に必ず確認しますか？

いいえ。許可モードやルールによっては編集が自動承認されます。作業前に未コミット・未追跡の内容を保全し、変更対象を絞って差分を確認してください。git checkout . は未ステージ変更を捨てることがあり、バックアップや復旧の代わりにはなりません。

### 公開リポジトリの確認にGitHubトークンは必要ですか？

この例で使う公開のリリース・コミット参照は、認証なしで利用できます。レート制限があるため、エラーが出ても広い権限のトークンを作るのではなく、まず応答と制限を確認してください。

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Cursorの有料プランに入っていれば、Claude Codeも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Cursorの契約だけでClaude Codeの利用資格が付くわけではありません。Claude Codeは対応するClaude契約やConsoleなどで認証できます。APIキーと従量課金がすべての利用者に必須という説明は誤りです。使用中の認証経路と料金条件を確認してください。"
      }
    },
    {
      "@type": "Question",
      "name": "Claude Codeは編集前に必ず確認しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ。許可モードやルールによっては編集が自動承認されます。作業前に未コミット・未追跡の内容を保全し、変更対象を絞って差分を確認してください。git checkout . は未ステージ変更を捨てることがあり、バックアップや復旧の代わりにはなりません。"
      }
    },
    {
      "@type": "Question",
      "name": "公開リポジトリの確認にGitHubトークンは必要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "この例で使う公開のリリース・コミット参照は、認証なしで利用できます。レート制限があるため、エラーが出ても広い権限のトークンを作るのではなく、まず応答と制限を確認してください。"
      }
    }
  ]
}
</script>
