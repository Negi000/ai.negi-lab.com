---
title: "Claude CodeとCursorを併用する最強のAIコーディング環境構築ガイド"
date: 2026-08-06T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-workflow-guide"
cover:
  image: "/images/posts/2026-08-06-claude-code-cursor-ai-coding-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AI コーディング"
  - "FastAPI React 構築"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

Claude Code（CLI）とCursor（IDE）を組み合わせ、バックエンドにFastAPI、フロントエンドにReactを用いた「AIテキスト要約Webアプリ」を30分で構築します。
PythonとNode.jsの基本操作ができることを前提に、AIエージェントに「コードを書かせる」のではなく「プロジェクトを完遂させる」フローを体験してもらいます。
APIを叩いて実際に動作するアプリをデプロイ直前の状態まで仕上げるのが今回のゴールです。

## 先に確認するスペック・料金

AIコーディングを実務レベルで回すには、ツールのサブスクリプション費用を「投資」と割り切る必要があります。
まず、CursorのProプラン（月額$20）は必須です。無料枠ではClaude 3.5 Sonnetの利用回数に制限があり、開発のリズムが崩れます。
次にClaude Codeを利用するためのAnthropic APIキーが必要です。これは従量課金ですが、1プロジェクトの立ち上げで$3〜$5程度は消費すると考えてください。

ハードウェア面では、MacBook Air（M2/M3）メモリ16GB以上を推奨します。
AIが裏でインデックスを作成したり、コードを解析したりする際に、8GBメモリだとスワップが発生してIDEの挙動が目に見えて重くなるためです。
Windows機の場合は、WSL2環境が必須となります。Claude CodeはUnixライクな環境での動作を前提として設計されているため、PowerShell直叩きでは本来の性能を発揮できません。

## なぜこの方法を選ぶのか

現在、Cursorだけで開発を完結させる人が多いですが、私はあえてClaude Codeとの併用を推奨します。
Cursorは「エディタ上のコード編集」には最強ですが、ターミナル操作や複雑なディレクトリを跨いだリサーチ、依存関係の解決にはまだ弱さがあるからです。
一方でClaude CodeはCLIネイティブなAIエージェントであり、テストの実行、パッケージのインストール、GitHubとの連携を対話形式で丸投げできます。

「視覚的な微調整はCursor」「構造設計と環境構築、デバッグはClaude Code」と役割を分けることで、開発速度は体感で3倍以上変わります。
既存のClineやAiderといったツールも優秀ですが、Anthropicが公式に提供するClaude Codeの「ファイルの書き換え精度」と「シェル実行の安全性」は群を抜いています。
この2つを組み合わせることが、現時点で最も「手が止まらない」開発環境だと断言します。

## Step 1: 環境を整える

まずはターミナルを開き、Claude Codeをグローバルにインストールします。
Node.jsのバージョンは20以上が必要です。

```bash
# Node.jsのバージョン確認
node -v

# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# 初期設定と認証（ブラウザが開きます）
claude auth login
```

次に、プロジェクト用のディレクトリを作成し、Cursorでそのディレクトリを開きます。

```bash
mkdir ai-summarizer && cd ai-summarizer
cursor .
```

⚠️ **落とし穴:**
Claude Codeのインストール時に`EACCES`エラーが出る場合は、権限の問題です。`sudo`で入れるのではなく、`nvm`（Node Version Manager）を使用してユーザー権限配下にNodeをインストールし直してください。AIツールはシステムファイルを操作することが多いため、権限周りの設定が甘いと後でデバッグ時にAIが「ファイルを保存できない」とループに陥る原因になります。

## Step 2: 基本の設定

Claude Codeを起動する前に、AIへの指示書（CLAUDE.md）を作成します。
これはClaude Codeがプロジェクトのルールを理解するための重要なファイルです。

```markdown
# Project: AI Summarizer

## Tech Stack
- Backend: FastAPI (Python 3.11+)
- Frontend: React (Vite, TypeScript)
- Styling: Tailwind CSS

## Rules
- Use functional components for React.
- Error handling should be explicit.
- Follow PEP8 for Python code.
```

次に、ターミナルで`claude`と入力して起動します。
初回起動時に「このディレクトリをインデックスして良いか」聞かれるので、`yes`を選択してください。

```bash
claude
```

起動したら、まず以下の指示をClaude Codeに投げます。

「FastAPIで`/summarize`エンドポイントを持つバックエンドと、Vite+Reactのフロントエンドの雛形を同じディレクトリ内に作成して。ディレクトリ名は`backend`と`frontend`にして。」

ここでClaude Codeは自動的に`mkdir`、`cd`、`npm create vite@latest`などを実行していきます。
私たちはただ、AIが提案するコマンドに対して「y（実行）」を押し続けるだけです。

## Step 3: 動かしてみる

バックエンドの実装を具体化させます。
今回のキモとなる「テキスト要約ロジック」を、実際にAnthropic APIを叩く形で実装させます。

```python
# backend/main.py の雛形（Claude Codeが生成するコードのイメージ）
import os
from fastapi import FastAPI
from pydantic import BaseModel
import anthropic

app = FastAPI()
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

class SummarizeRequest(BaseModel):
    text: str

@app.post("/summarize")
async def summarize(request: SummarizeRequest):
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": f"以下の文章を3行で要約して:\n\n{request.text}"}
        ]
    )
    return {"summary": message.content[0].text}
```

### 期待される出力

Claude Codeが環境構築を終えたら、以下のコマンドでサーバーを起動させます。

```bash
# Claude Codeの中で指示
> backendを起動して。必要なライブラリが足りなければインストールして。
```

正常に動作すれば、`http://localhost:8000/docs`にアクセスするとFastAPIのSwagger UIが表示されます。
ここでテスト用のテキストを入力し、JSON形式で要約が返ってくれば成功です。

⚠️ **落とし穴:**
ここでよくあるのが、環境変数の読み込み失敗です。Claude Codeに「`.env`ファイルを作成し、`ANTHROPIC_API_KEY`をそこに記述して、`.gitignore`に追記して」と明確に指示してください。これを忘れると、うっかりAPIキーをGitHubに公開してしまうリスクがあります。

## Step 4: 実用レベルにする

ここからがCursorの出番です。Claude Codeが作った無骨なフロントエンドを、Cursorの「Composer（Cmd+I）」を使って一気にリッチにします。

1. Cursorで`frontend/src/App.tsx`を開きます。
2. Composer（Cmd+I）を起動し、以下の指示を出します。
   「今のシンプルなテキストエリアを、Tailwind CSSを使ってモダンなUIにして。左側に原文入力、右側に要約結果を出す2カラム構成にして。読み込み中はローディングアニメーションを出して。」

Cursorは視覚的なデザイン調整が得意です。
コードの変更箇所がサイドバイサイドで見えるため、AIが提案したUIデザインを納得がいくまで「Reject」や「Apply」で調整できます。

次に、エラーハンドリングを追加します。
Claude Codeに戻り、以下の指示を出します。
「APIが429（レートリミット）を返した時や、ネットワークエラーの時に、ユーザーに分かりやすいトースト通知を出すようにフロントエンドを修正して。」

Claude Codeは複数のファイルを同時に検索し、適切なライブラリ（例えば`react-hot-toast`）のインストールから、コンポーネントへの組み込みまでを一気通貫で行います。

```tsx
# 実用的なコードの一部（Cursor/Claude Codeで生成）
import toast, { Toaster } from 'react-hot-toast';

const handleSummarize = async () => {
  setIsLoading(true);
  try {
    const res = await fetch('/api/summarize', { ... });
    if (!res.ok) throw new Error('API Error');
    // ...処理
  } catch (err) {
    toast.error('要約に失敗しました。時間を置いて再度お試しください。');
  } finally {
    setIsLoading(false);
  }
};
```

このように、「ロジックの堅牢性はClaude Code」「UIの心地よさはCursor」と使い分けるのが、私の辿り着いた結論です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Claude Codeが止まる | 巨大なディレクトリのインデックス中 | `.gitignore`に`node_modules`や`venv`が正しく入っているか確認する |
| APIキーが反映されない | ターミナルのセッションが古い | `source .env`を実行するか、`export`コマンドで直接設定する |
| Cursorの補完が遅い | ローカルインデックスの不整合 | CursorのSettingsから「Index Now」を押し直す |

## 次のステップ

ここまでで、AIをフル活用したアプリ開発の基礎ができました。
次に挑戦すべきは、このアプリに「履歴保存機能」を追加することです。
SQLiteなどの軽量データベースを導入し、過去の要約結果をブラウザのリロード後も保持できるようにしてみてください。

また、Claude Codeの真価は「既存コードのバグ修正」にあります。
わざとコードにバグを仕込み、`claude`を起動して「このプロジェクトのバグを見つけて修正して」と指示してみてください。
AIがテストコードを生成し、実行し、エラーを特定して修正するプロセスを目の当たりにすると、もうAIなしの開発には戻れなくなるはずです。

実務においては、このワークフローをチームに導入する際の「プロンプトの共通化」も重要です。
`.cursorrules`や`CLAUDE.md`をGit管理し、チーム全員が同じ「AIの癖」を共有できるように設定を煮詰めてみてください。

## よくある質問

### Q1: Claude CodeとCursor、どちらか片方ではダメですか？

可能です。しかし、Cursorのターミナル（Ctrl + `）は標準的なシェルに過ぎず、Claude Codeのような「エージェント機能（自律的なコマンド実行と修正）」がありません。逆にClaude Codeはコードの微調整を視覚的に確認するのが難しいため、併用が最もストレスがありません。

### Q2: API代が高くなりそうで怖いのですが。

Claude Codeを使用する際は、`claude compact`モードや、トークン制限を意識した指示を出すことで節約可能です。まずは$5程度のプリペイド枠で始め、AIがどれだけのファイルを読み書きしているかログを観察することをお勧めします。

### Q3: 会社のプロジェクトで使っても大丈夫ですか？

多くの企業では、AIツールへのコード送信が制限されています。Cursorの「Privacy Mode」や、Anthropicの「Commercial Terms」を確認し、データがモデルの学習に使われない設定になっているか、必ず法務や情報システム部門と相談してください。私個人は、個人開発と割り切って最新ツールを使い倒しています。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">HHKB Studio</strong>
<p style="color:#555;margin:8px 0;font-size:14px">CLIとIDEを頻繁に行き来するAI開発では、ホームポジションを崩さないポインティングスティックが効く</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FHHKB%2520Studio%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FHHKB%2520Studio%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=HHKB%20Studio&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用した最強AIコーディング環境の構築ガイド](/posts/2026-06-17-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用する最強AIコーディング環境の使い方](/posts/2026-07-31-claude-code-cursor-setup-guide/)
- [Claude CodeとCursorを併用する最強のAI開発環境の作り方](/posts/2026-07-27-claude-code-cursor-hybrid-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude CodeとCursor、どちらか片方ではダメですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。しかし、Cursorのターミナル（Ctrl + ）は標準的なシェルに過ぎず、Claude Codeのような「エージェント機能（自律的なコマンド実行と修正）」がありません。逆にClaude Codeはコードの微調整を視覚的に確認するのが難しいため、併用が最もストレスがありません。"
      }
    },
    {
      "@type": "Question",
      "name": "API代が高くなりそうで怖いのですが。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeを使用する際は、claude compactモードや、トークン制限を意識した指示を出すことで節約可能です。まずは$5程度のプリペイド枠で始め、AIがどれだけのファイルを読み書きしているかログを観察することをお勧めします。"
      }
    },
    {
      "@type": "Question",
      "name": "会社のプロジェクトで使っても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "多くの企業では、AIツールへのコード送信が制限されています。Cursorの「Privacy Mode」や、Anthropicの「Commercial Terms」を確認し、データがモデルの学習に使われない設定になっているか、必ず法務や情報システム部門と相談してください。私個人は、個人開発と割り切って最新ツールを使い倒しています。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">HHKB Studio</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">CLIとIDEを頻繁に行き来するAI開発では、ホームポジションを崩さないポインティングスティックが効く</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FHHKB%2520Studio%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FHHKB%2520Studio%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=HHKB%20Studio&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
