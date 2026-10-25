---
title: "Claude CodeとCursorを併用する最強のAIコーディング環境構築ガイド"
date: 2026-10-26T00:00:00+09:00
slug: "claude-code-cursor-hybrid-workflow-guide"
cover:
  image: "/images/posts/2026-10-26-claude-code-cursor-hybrid-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AI コーディング"
  - "FastAPI 自動生成"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

FastAPIとSQLiteを使用した、実用的な「AIタスク管理API」を構築します。
単なるコード生成ではなく、Claude Codeによるプロジェクト構成の自動生成と、Cursorによる細かなロジックのブラッシュアップを組み合わせた、2025年最新の開発フローを体験できます。
この記事を読み終える頃には、ターミナルからAIを自在に操り、エディタで詳細を詰める「ハイブリッド開発」が身についているはずです。

- **前提知識:** Pythonの基礎（pipインストールができる程度）、ターミナルの基本操作。
- **必要なもの:** Anthropic APIキー（必須）、Cursor（Proプラン推奨）、Node.js環境（Claude Code実行用）。

## 先に確認するスペック・料金

AIコーディングを本格的に仕事へ取り入れるなら、API料金とツール代の「投資判断」が不可欠です。
まず、CursorのProプラン（月額$20）は必須と考えてください。無料枠のモデルでは、複雑なリファクタリングでコンテキストが維持できず、結局手直しが増えて時間をロスします。

Claude CodeはAnthropicのAPIを直接消費します。
今回のチュートリアルを1回通すだけであれば、$0.5〜$1.0（約150円）程度の消費で済みますが、1日中フル活用すると$5〜$10ほどかかる場合もあります。
「月額$20で使い放題（制限あり）のCursor」と「使った分だけ払うがターミナル操作まで自動化できるClaude Code」の使い分けが、財布を守りつつ生産性を最大化するコツです。

ハードウェアについては、MacBook（M2/M3/M4）ならメモリ24GB以上を推奨します。
AIツールを複数立ち上げ、ブラウザでドキュメントを開き、ローカルサーバーを動かすと、16GBではスワップが発生してレスポンスが悪化するためです。
Windows派であれば、WSL2環境を構築した上で、RTX 3060（VRAM 12GB）以上のGPUがあればローカルLLMとの連携も視野に入りますが、今回はAPIベースなのでCPUスペックがあれば十分です。

## なぜこの方法を選ぶのか

これまで私はCursor単体で開発を完結させてきました。
しかし、CursorのComposer（Ctrl+I）は「開いているファイル」の編集には強いものの、新しいライブラリのインストール、DBマイグレーション、テストの実行といった「ターミナル作業」との行き来に微かな摩擦がありました。

Claude Codeはこの摩擦をゼロにします。
Claude Codeはエージェントとしてローカルのシェルを直接操作できるため、「この仕様に基づいたフォルダ構成を作って、必要なライブラリをインストールし、サーバーを起動して」という指示をワンライナーで実行できます。
「全体構造の構築と環境操作はClaude Code」、「個別の関数の微調整やUIのこだわりはCursor」という役割分担が、現時点で最も開発速度が出るアプローチだと確信しています。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。これはNode.jsベースのツールなので、npmを使用します。

```bash
# Node.jsがインストールされていることを確認（v18以上推奨）
node -v

# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# インストールの確認
claude --version
```

次に、Python環境を構築します。プロジェクトごとに環境を汚さないよう、仮想環境を作成するのがSIer時代からの私の鉄則です。

```bash
mkdir ai-task-app && cd ai-task-app
python -m venv .venv
source .venv/bin/activate  # Windowsの場合は .venv\Scripts\activate
```

⚠️ **落とし穴:** Claude Codeを初めて起動する際、`claude auth` でブラウザが立ち上がり、Anthropicのアカウント連携を求められます。このとき、APIのクレジット（残高）が0だとエラーになります。事前にAnthropicのConsoleから$5でも良いのでチャージしておいてください。無料枠のトークンだけでは、Claude Codeの広範なスキャン機能ですぐに制限がかかります。

## Step 2: 基本の設定

Claude Codeを起動し、プロジェクトの初期化を行います。

```bash
claude
```

起動したら、まず以下のコマンドをClaudeに投げてください。

「このプロジェクトでFastAPIを使ったタスク管理APIを作りたい。まずは必要なライブラリを特定して、requirements.txtを作成し、インストールまで進めてください」

Claude Codeはカレントディレクトリをスキャンし、以下のような内容を提案・実行してくれます。

```python
# 生成される requirements.txt の例
fastapi
uvicorn
sqlalchemy
pydantic
```

ここで重要なのは、Claude Codeが「自分でコマンドを実行する許可」を求めてくる点です。
yキーを押して許可すると、`pip install -r requirements.txt` が自動で走り、環境が整います。

次に、Cursorを開きます。

```bash
cursor .
```

Cursorの設定（Cmd + Shift + J）を開き、Modelsセクションで「Claude 3.5 Sonnet」が有効になっていることを確認してください。
Claude Codeが作ったファイル構造をCursorが読み取れる状態にすることで、ここから先の「並行作業」が可能になります。

## Step 3: 動かしてみる

Claude Code（ターミナル側）に戻り、一気にコードを生成させます。

「SQLiteをデータベースとして使い、Taskモデル（id, title, description, completed）を持つAPIを作成してください。main.pyに全てのロジックを詰め込まず、models.py, schemas.py, crud.pyに分割して構成してください」

### 期待される出力

Claude Codeが数秒考えたあと、複数のファイルを一括生成します。

```bash
Created models.py
Created schemas.py
Created crud.py
Created main.py
```

生成が終わったら、Claude Codeに「サーバーを起動して」と伝えます。

```bash
# Claude Codeが自動で実行するコマンド
uvicorn main:app --reload
```

ブラウザで `http://121.0.0.1:8000/docs` を開いてみてください。
FastAPIのSwagger UIが表示され、タスクのPOSTやGETが試せるようになっているはずです。
ここまで、私は一度もコードを書いていません。指示を出して「y」を押しただけです。

## Step 4: 実用レベルにする

ここからがCursorの出番です。
Claude Codeは「動くものを作る」のは得意ですが、コードの可読性や、開発者固有の好みを反映させるにはCursorのインライン編集の方が直感的です。

例えば、`schemas.py` をCursorで開き、`completed` フィールドのデフォルト値を変更したり、バリデーションを追加したりします。

```python
# CursorのComposer (Cmd+I) で指示
# 「titleは最低3文字以上、空白のみは不可というバリデーションをPydanticのFieldを使って追加して」

from pydantic import BaseModel, Field

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, strip_whitespace=True)
    description: str | None = None
```

次に、Claude Codeに戻り、実務で不可欠な「ユニットテスト」を自動生成させます。

「pytestを使って、APIの正常系と異常系のテストコードを生成し、tests/ディレクトリに配置してください。その後、テストを実際に実行して結果を報告してください」

私が以前、手動でテストを書いていた時は、モックの設定だけで15分は費やしていましたが、Claude Codeなら15秒です。
テストが失敗した場合、Claude Codeはそのエラーログを読み取り、「あ、models.pyの定義とズレていましたね。修正します」と自己修復を始めます。
この「実行→エラー確認→修正」のループをAIが自律して回すのが、Claude Codeを併用する最大のメリットです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `command not found: claude` | パスが通っていない | `npm list -g` で場所を確認し、PATHを通すか `npx @anthropic-ai/claude-code` を試す |
| APIのQuota超過 | Claude Codeのコンテキストスキャンによる消費 | `.claudignore` ファイルを作成し、`.venv` や `__pycache__` を除外する |
| ファイルが同期されない | Cursorの保存遅延 | Cursorで「Auto Save」を有効にする。Claude Codeはディスク上のファイルを読むため |

## 次のステップ

このフローをマスターしたら、次は「MCP（Model Context Protocol）」の導入に挑戦してください。
Claude CodeはMCPサーバーと連携することで、Google検索を実行したり、GitHubのリポジトリを直接操作したり、Slackに通知を飛ばしたりすることが可能になります。

例えば、「最新のFastAPIのベストプラクティスをWebで検索して、今のコードをリファクタリングして」といった、外部知識を前提とした指示が通るようになります。
また、ローカルLLMをバックエンドに据えた「Cline（旧Claude Dev）」との比較検証も面白いでしょう。
RTX 4090などの強力なGPUを持っているなら、機密性の高いコードはローカルのLlama 3等で処理させ、複雑なロジック設計だけをClaude 3.5 Sonnetに任せるという使い分けが、実務における究極のコストパフォーマンスを実現します。

## よくある質問

### Q1: CursorのComposer機能とClaude Code、どちらを優先して使うべきですか？

新規プロジェクトの立ち上げ、ライブラリ導入、テスト実行など「ターミナル操作が絡む作業」はClaude Codeが圧倒的に速いです。一方で、既存の長いコードをスクロールしながら「ここを少し書き換えたい」という微調整は、Cursorの方が視覚的に優れています。8割をClaude Codeで作り、最後の2割の「こだわり」をCursorで仕上げるのが私のおすすめです。

### Q2: API料金を節約するコツはありますか？

Claude Codeに全てのファイルを読み込ませないことです。`.claudignore` を適切に設定し、不要なバイナリファイルや依存ライブラリのディレクトリをスキャン対象から外してください。これだけで、初期スキャンにかかるトークンを数千〜数万節約できます。

### Q3: 完全に自動でプログラミングが完結しますか？

いいえ。AIは「それっぽい嘘」をつくことがあります。特にDBのマイグレーションや認証周りなど、セキュリティに直結する部分は、AIが書いたコードを必ずCursorで開き、自分の目でレビューしてください。AIは「最高のペアプログラマー」であり、「丸投げできる下請け」ではないという認識が、事故を防ぐ唯一の手段です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIツールとエディタ、Dockerを同時並行で動かすには32GB以上のメモリが必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用してAI開発を完全自動化する方法](/posts/2026-07-18-claude-code-cursor-ai-coding-tutorial/)
- [Claude CodeとCursorを併用した最強AIコーディング環境の構築ガイド](/posts/2026-06-17-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用して爆速でアプリ開発する使い方](/posts/2026-09-16-claude-code-cursor-hybrid-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "CursorのComposer機能とClaude Code、どちらを優先して使うべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "新規プロジェクトの立ち上げ、ライブラリ導入、テスト実行など「ターミナル操作が絡む作業」はClaude Codeが圧倒的に速いです。一方で、既存の長いコードをスクロールしながら「ここを少し書き換えたい」という微調整は、Cursorの方が視覚的に優れています。8割をClaude Codeで作り、最後の2割の「こだわり」をCursorで仕上げるのが私のおすすめです。"
      }
    },
    {
      "@type": "Question",
      "name": "API料金を節約するコツはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeに全てのファイルを読み込ませないことです。.claudignore を適切に設定し、不要なバイナリファイルや依存ライブラリのディレクトリをスキャン対象から外してください。これだけで、初期スキャンにかかるトークンを数千〜数万節約できます。"
      }
    },
    {
      "@type": "Question",
      "name": "完全に自動でプログラミングが完結しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ。AIは「それっぽい嘘」をつくことがあります。特にDBのマイグレーションや認証周りなど、セキュリティに直結する部分は、AIが書いたコードを必ずCursorで開き、自分の目でレビューしてください。AIは「最高のペアプログラマー」であり、「丸投げできる下請け」ではないという認識が、事故を防ぐ唯一の手段です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">AIツールとエディタ、Dockerを同時並行で動かすには32GB以上のメモリが必須</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2036GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
