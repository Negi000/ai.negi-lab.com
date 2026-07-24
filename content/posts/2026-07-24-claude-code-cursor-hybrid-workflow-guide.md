---
title: "Claude CodeとCursorを併用して開発効率を最大化する使い方"
date: 2026-07-24T00:00:00+09:00
slug: "claude-code-cursor-hybrid-workflow-guide"
cover:
  image: "/images/posts/2026-07-24-claude-code-cursor-hybrid-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AIエージェント コーディング"
  - "FastAPI 自動生成"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

GitHubリポジトリの解析からコード生成、テスト自動化、ドキュメント作成までを完結させるAI開発フローを構築します。
具体的には、外部API（OpenWeatherMap）と連携するFastAPIバックエンドを、CursorのUI編集とClaude Codeの自律型デバッグを組み合わせて完成させます。
この記事を読み終える頃には、人間がコードを1行も書かずに、動作確認済みのAPIサーバーが1つ手元に残っているはずです。

## 先に確認するスペック・料金

AIコーディングを本気でやるなら、ハードウェア以上に「API予算」と「サブスクリプション」の整理が最優先です。
まずCursorは「Proプラン（月額$20）」が必須。無料枠ではClaude 3.5 Sonnetの高速な推論が制限されるため、実務レベルの並行開発には耐えられません。
一方のClaude Codeは、Anthropicが提供するCLIツールであり、これ自体に月額料金はかかりませんが「Claude API」の従量課金が発生します。

大規模なリポジトリでClaude Codeを走らせると、1時間で$5〜$10程度溶けることも珍しくありません。
しかし、SIer時代に月額数百万かけていた外注費を考えれば、月数千円〜数万円で「24時間働くシニアエンジニア」を雇えるのは破格です。
ハードウェアについては、MacBook Pro（M2/M3 Max）のメモリ32GB以上を強く推奨します。
AIツールを複数立ち上げ、ローカルでDockerを回しながら開発する場合、16GBだとスワップが発生して作業効率が著しく落ちるからです。

## なぜこの方法を選ぶのか

現在、AIコーディングには「IDE型（Cursor）」と「エージェント型（Claude Code）」の2つの潮流があります。
Cursorはコードの微修正やリファクタリング、UI構築など「目に見える場所」の編集に極めて強い一方で、ターミナルのエラーを自律的に解決し続けるような泥臭い作業はまだ苦手です。
対してClaude Codeは、ターミナル上で「テストが通るまで勝手に修正し続ける」というエージェント的な振る舞いを得意としています。

Cursorだけで開発していると「エラーが出る→プロンプトを投げる→修正コードを適用する→また別のエラーが出る」という往復が発生しますが、Claude Codeに任せればその往復を自動化できます。
つまり、Cursorを「思考のキャンバス」として使い、Claude Codeを「自律的に動く実装担当」として使い分けるのが、現時点で最も生産性が高い組み合わせです。
GitHub Copilotも進化していますが、コンテキストの理解度と自律的なコマンド実行能力において、今のところAnthropicの3.5 Sonnetエンジンを積んだこの2つの併用が頭一つ抜けています。

## Step 1: 環境を整える

まずはClaude Codeのインストールから始めます。これはNode.js環境が必要です。

```bash
# Node.js 18以上が必要です
node -v

# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# 初期設定とログイン
claude
```

Claude Codeは、初回実行時にブラウザが開き、Anthropicアカウントでの認証を求められます。
APIキーの直書きではなく、OAuth方式でのログインになるためセキュリティ面でも安心です。
次に、作業用のディレクトリを作成し、Cursorで開きます。

```bash
mkdir ai-hybrid-app
cd ai-hybrid-app
cursor .
```

⚠️ **落とし穴:** Node.jsのバージョンが古いと、インストール中に不明なエラーで止まることがあります。
`nvm`などを使ってNode.js 18系以上（できれば最新のLTS）にアップデートしてから実行してください。
また、Windows環境のWSL2で動かす場合、ブラウザ認証が自動で開かないことがあるので、ターミナルに表示されるURLをコピーして手動でブラウザに貼り付ける必要があります。

## Step 2: 基本の設定

Claude Codeをプロジェクトに最適化するための設定ファイルを作成します。
AIに「このプロジェクトのルール」を教えることで、生成されるコードの品質が劇的に変わります。

```bash
# .clauderc ファイルの作成（Claude Code用）
touch .clauderc
```

`.clauderc`には、常に守らせたいルールを記述します。例えば「テストはpytestを使う」「型ヒントは必須」といった指示です。
あわせて、プロジェクトの雛形をClaude Codeに作らせます。

```bash
# ターミナルで実行
claude "FastAPIを使ってOpenWeatherMap APIから天気を取得するプロジェクトを初期化して。
依存関係はPoetryで管理、テストはpytest、型ヒントを厳格に入れてください。"
```

Claude Codeは自動で `pyproject.toml` を作成し、必要なディレクトリ構造を構築します。
「Yes/No」で実行確認を求められるので、内容を確認しながら進めてください。
なぜPoetryを使うのか。それは、AIが依存関係を管理する際、`requirements.txt`よりも厳密なバージョン管理ができる`poetry.lock`があった方が、環境構築エラーをAI自身で自己修復しやすいからです。

## Step 3: 動かしてみる

次に、作成されたプロジェクトをCursorで確認します。
Cursorの「Composer (Ctrl+I / Cmd+I)」を開き、以下の指示を出して実際のロジックを実装させます。

```python
# CursorのComposerへの指示例
@file:main.py に、指定した都市の気温と天気を返すエンドポイントを作成して。
外部APIキーは環境変数 API_KEY から読み込むように。
エラーハンドリング（都市が見つからない場合など）も忘れずに実装してください。
```

### 期待される出力

```json
{
  "city": "Tokyo",
  "temperature": 15.5,
  "description": "clear sky"
}
```

CursorはUI上で複数のファイルを一気に書き換えてくれます。
ここで重要なのは、Cursorが生成したコードに対して「これ動く？」と疑うのではなく、即座にClaude Codeにテストを丸投げすることです。

```bash
# ターミナルでClaude Codeに指示
claude "現状のコードに対してpytestを実行して。エラーが出たらすべて修正し、
完全にグリーンになるまで自律的にデバッグを繰り返して。"
```

これが「併用」の真髄です。Cursorで大枠を作り、Claude Codeに「動く保証」を付けさせる。
私の経験上、人間が1つずつエラーをコピペしてAIに聞くより、この方法なら3倍は速くデバッグが終わります。

## Step 4: 実用レベルにする

単に動くだけでなく、本番環境を見据えたエラーハンドリングとロギング、そしてDockerfileの作成までを一気に進めます。
ここではClaude Codeの「プロジェクト全域を把握する能力」を活用します。

```bash
# ターミナルでClaude Codeに指示
claude "このアプリを本番運用するための構成にアップグレードしてください。
1. structlogを導入してJSON形式でログを出力
2. マルチステージビルドを採用したDockerfileの作成
3. 異常なリクエストを制限するミドルウェアの追加
4. これらすべての変更に伴うテストコードの更新"
```

Claude Codeは、プロジェクト内の全ファイルを読み取り、不整合が起きないように修正をかけます。
例えば、ログ出力を追加したことで既存のテストが壊れた場合も、Claude Codeは自分でテストを実行し、エラーメッセージを見てテストコード側も修正してくれます。

私自身、以前はCursorだけでこれをやっていましたが、ファイル数が増えてくると「Aを直すとBが壊れる」というループに陥ることがありました。
Claude Codeは現在のコンテキスト（ファイル構造、型、テスト結果）を保持したまま「解決するまで止まらない」モードがあるため、こうした全体修正に極めて強いです。

```python
# 最終的に生成される実用的なコードの断片
import os
import structlog
from fastapi import FastAPI, HTTPException
from httpx import AsyncClient

logger = structlog.get_logger()
app = FastAPI()

@app.get("/weather/{city}")
async def get_weather(city: str):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        logger.error("api_key_missing")
        raise HTTPException(status_code=500, detail="API key is not configured")

    async with AsyncClient() as client:
        # ここに詳細な実装が続く...
        pass
```

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `claude` コマンドが見つからない | PATHが通っていない | `npm bin -g` でパスを確認し、環境変数に追加する |
| APIの課金が予想以上に高い | Claude Codeがループしている | `claude` 実行時に `--max-steps 5` などでステップ数を制限する |
| CursorとClaude Codeでコードが競合する | 両方で同時にファイルを編集した | 片方の作業が終わるまでファイルを保存し、gitでコミットしてから次へ進む |

## 次のステップ

このフローをマスターしたら、次は「GitHub Actionsとの連携」に挑戦してください。
Claude Codeに「このプロジェクトに最適なCI/CDパイプライン（GitHub Actions）を作成して。コミットごとにpytestとLinterが走るように」と命じるだけで、`.github/workflows/main.yml` が完璧な状態で生成されます。

さらに一歩進むなら、ローカルLLMを併用したハイブリッド構成も面白いです。
機密性の高いドキュメント作成はローカルのLlama 3で、複雑なロジック実装はClaude 3.5 Sonnetで、という使い分けです。
私は自宅のRTX 4090 2枚挿しサーバーでOllamaを動かし、CursorのローカルLLM設定と組み合わせていますが、これによりAPIコストを抑えつつ、深夜のコーディングも快適に行えています。

AIコーディングは「ツールを1つに絞る」のではなく「特性に合わせてオーケストレーションする」フェーズに入りました。
まずは今日の開発から、Cursorで書いて、Claude Codeにデバッグさせる。この快感を一度味わうと、もう以前のやり方には戻れません。

## よくある質問

### Q1: Claude Codeを使うためにAnthropicのProプランは必要ですか？

Proプラン（月額$20）ではなく、APIの「Console」アカウントにクレジットカードを登録し、クレジットを購入しておく必要があります。Claude CodeはAPI経由で動作するため、チャットUIのサブスクリプションとは別枠の料金体系です。

### Q2: 既存の巨大なプロジェクトにClaude Codeを導入しても大丈夫ですか？

可能です。ただし、最初に `claude ignore` ファイルを作成し、`node_modules` や巨大なログファイルなどをスキャン対象から外してください。そうしないと、インデックス作成だけで大量のトークンを消費し、高額な請求が来る恐れがあります。

### Q3: CursorのComposerとClaude Code、どちらを優先すべきですか？

「新しい画面を作る」「UIの微調整をする」といった視覚的な作業はCursorが圧倒的に便利です。一方で「複雑なエラーの解消」「リポジトリ全体の型定義の整理」「一気通貫したテスト作成」はClaude Codeの方が粘り強く完遂してくれます。用途で使い分けてください。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">32GB以上のメモリはAIツール複数起動とDocker併用に必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用した最強AIコーディング環境の構築ガイド](/posts/2026-06-17-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを使い分け！最強のAI開発環境構築ガイド](/posts/2026-06-27-claude-code-cursor-workflow-guide/)
- [Claude Code 使い方とCursor併用の最強コーディング環境構築ガイド](/posts/2026-07-08-claude-code-cursor-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude Codeを使うためにAnthropicのProプランは必要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Proプラン（月額$20）ではなく、APIの「Console」アカウントにクレジットカードを登録し、クレジットを購入しておく必要があります。Claude CodeはAPI経由で動作するため、チャットUIのサブスクリプションとは別枠の料金体系です。"
      }
    },
    {
      "@type": "Question",
      "name": "既存の巨大なプロジェクトにClaude Codeを導入しても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。ただし、最初に claude ignore ファイルを作成し、nodemodules や巨大なログファイルなどをスキャン対象から外してください。そうしないと、インデックス作成だけで大量のトークンを消費し、高額な請求が来る恐れがあります。"
      }
    },
    {
      "@type": "Question",
      "name": "CursorのComposerとClaude Code、どちらを優先すべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "「新しい画面を作る」「UIの微調整をする」といった視覚的な作業はCursorが圧倒的に便利です。一方で「複雑なエラーの解消」「リポジトリ全体の型定義の整理」「一気通貫したテスト作成」はClaude Codeの方が粘り強く完遂してくれます。用途で使い分けてください。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">32GB以上のメモリはAIツール複数起動とDocker併用に必須</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252032GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2032GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
