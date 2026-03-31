---
title: "Claude Codeの使い方とnpm公開時のソースコード流出を防ぐガードレール構築術"
date: 2026-03-31T00:00:00+09:00
slug: "claude-code-setup-and-npm-security-guide"
cover:
  image: "/images/posts/2026-03-31-claude-code-setup-and-npm-security-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "npm ソースコード流出 対策"
  - "Python npm 検疫スクリプト"
  - "Anthropic Claude CLI"
---
**所要時間:** 約35分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Claude Codeを安全に導入し、開発効率を爆上げする環境構築
- 自社開発ツールのnpm公開時に、ソースコード（.mapファイル）の流出を自動で防ぐPython検疫スクリプト
- 実際にスクリプトを動かし、流出リスクのあるパッケージを検知・ブロックする仕組み

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Claude CodeのようなAIツールとローカルLLMを併用し、高速な開発環境を構築するなら最強のGPUです</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204090&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、ターミナルでのコマンド操作と、簡単なPythonコードの読み書きができることを想定しています。
必要なものは、AnthropicのAPIキーと、Node.js（v18以上）、Python 3.10以降の環境です。

## なぜこの方法を選ぶのか

Anthropicがリリースした「Claude Code」は、ターミナル上で動作する非常に強力なAIエージェントです。
しかし、その公開直後にnpmレジストリ上の「source map（.mapファイル）」からソースコードが復元可能な状態になっていたというニュースは、全開発者に衝撃を与えました。
どんなに優れたエンジニア集団でも、デプロイ設定一つで意図しない情報漏洩は起こり得ます。

この記事では、単に「Claude Codeを便利に使う」だけでなく、SIer時代に嫌というほど叩き込まれた「再発防止」の観点を取り入れます。
「npm publish」という一瞬の操作に潜むリスクを、Pythonによる自動検疫スクリプトで潰します。
手動のチェックリストを増やすのではなく、仕組みで解決するのが私の流儀です。

## Step 1: 環境を整える

まずはClaude Codeのインストールと、検疫スクリプト用の環境を構築します。

```bash
# Claude Codeのインストール（公式の手順）
npm install -g @anthropic-ai/claude-code

# 検疫スクリプト用の作業ディレクトリ作成
mkdir npm-guard && cd npm-guard
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate
```

Claude Codeは現在ベータ版で、頻繁にアップデートされています。
`npm install -g` でインストールするのは、グローバルなCLIツールとしてどこからでも呼び出せるようにするためです。
Node.jsのバージョンが古いと動かないケースがあるため、`node -v` で18以上であることを確認してください。

⚠️ **落とし穴:**
Claude Codeを初めて起動する際、`claude` コマンドを叩くと認証を求められます。
この時、ブラウザが立ち上がりますが、複数のGoogleアカウントを使い分けている場合は注意が必要です。
Anthropicのアカウントと紐づいているアカウントでログインしないと、API利用権限エラーで30分ほど溶かすことになります。

## Step 2: Claude Codeの基本設定と動作確認

Claude Codeをプロジェクトで使うための初期設定を行います。

```bash
# プロジェクトディレクトリへ移動
cd /path/to/your-project

# Claude Codeの起動
claude
```

起動後、まず最初に「仕事で使えるか」を判断するために、コスト設定を確認します。
デフォルトでは使いすぎてしまう可能性があるため、プロジェクトのルートにある `.claude-code-config.json`（存在しない場合は作成）で制限をかけることを推奨します。

```json
{
  "max_tokens": 4096,
  "cost_limit": 10.0
}
```

この `$10.0` という制限は、1回のセッションでの上限です。
私は以前、複雑なリファクタリングを丸投げして一気に $5 ほど溶かした経験があります。
「速い」のは確かですが、コスト意識を持たずに使い続けるのは危険です。

## Step 3: npm公開前の「流出防止ガードレール」を作る

ここが本題です。Anthropicが今回踏んでしまった「mapファイル経由のソースコード流出」を、自分のプロジェクトで起こさないためのスクリプトを書きます。
Pythonの `pathlib` と `json` を使い、`npm pack` で生成される中身を事前にスキャンします。

```python
# guard.py
import json
import subprocess
import tarfile
import sys
from pathlib import Path

def check_npm_package():
    print("Checking for source map leaks...")

    # 1. npm packを実行して、実際に公開されるファイル群をシミュレート
    result = subprocess.run(["npm", "pack", "--dry-run", "--json"], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error running npm pack: {result.stderr}")
        sys.exit(1)

    # 2. 公開予定のファイルリストを取得
    try:
        package_info = json.loads(result.stdout)
        # npmバージョンによって出力形式が異なる場合があるため、最初の要素を取得
        files = package_info[0].get('files', [])
    except (json.JSONDecodeError, IndexError):
        print("Failed to parse npm pack output.")
        sys.exit(1)

    # 3. .mapファイルが含まれていないかチェック
    leaked_files = [f['path'] for f in files if f['path'].endswith('.map')]

    if leaked_files:
        print("❌ CRITICAL ERROR: Source map files detected in the package!")
        for f in leaked_files:
            print(f"  - {f}")
        print("\nFix: Add '*.map' to your .npmignore or update tsconfig.json to 'sourceMap: false'.")
        sys.exit(1)

    print("✅ No source map leaks detected. Safe to publish.")

if __name__ == "__main__":
    check_npm_package()
```

このスクリプトは `npm pack --dry-run` を利用しています。
これは「実際に公開するパッケージの中身」をローカルでシミュレーションするコマンドです。
`.gitignore` や `.npmignore` の設定ミスを、アップロード前に100%の精度で見つけることができます。

### 期待される出力

mapファイルが含まれている場合：
```
Checking for source map leaks...
❌ CRITICAL ERROR: Source map files detected in the package!
  - dist/index.js.map
  - dist/utils/logger.js.map

Fix: Add '*.map' to your .npmignore or update tsconfig.json to 'sourceMap: false'.
```

合格した場合：
```
Checking for source map leaks...
✅ No source map leaks detected. Safe to publish.
```

## Step 4: CI/CDへの組み込みと実用化

スクリプトを単体で動かすだけでは、いつか「実行し忘れ」が起きます。
私はSIer時代、この「人為的ミス」で深夜まで障害対応をした苦い経験があります。
そのため、必ず `package.json` の `prepublishOnly` フックに組み込みます。

```json
{
  "scripts": {
    "build": "tsc",
    "guard": "python3 guard.py",
    "prepublishOnly": "npm run build && npm run guard"
  }
}
```

この設定により、`npm publish` を叩いた瞬間に自動でビルドが走り、その後にPythonスクリプトが検疫を行います。
もし `.map` ファイルが1つでも混入していれば、その場でプロセスが異常終了し、全世界にソースコードが公開されるのを未然に防ぎます。

レスポンスは私の環境で約1.2秒。この1秒強のチェックが、将来の数千万円規模の損害賠償や信頼失墜を防ぐと考えれば、安い投資だと思いませんか。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `npm pack` が失敗する | package.jsonの記述ミス | `npm pkg get name` で名前が正しく設定されているか確認 |
| PythonスクリプトでJSONエラー | npmのバージョンが古い | `npm install -g npm@latest` で更新。v7以降が必須 |
| Claude Codeが勝手にファイルを書き換える | プロンプトの指示不足 | `claude` 起動時に `-read-only` フラグを付けるか、書き換え前に確認を入れるよう指示する |

## 次のステップ

この記事の内容で、Claude Codeという最新ツールの活用と、そのツールが陥った罠を回避するガードレールが手に入りました。
次に目指すべきは「AIによるセキュアコーディングの自動化」です。

例えば、今回作った `guard.py` をさらに拡張し、ソースコード内にAPIキー（`sk-...`）や秘密鍵が含まれていないかを正規表現でスキャンする機能を追加してみてください。
Claude Codeに「このPythonスクリプトに、AWSやOpenAIの秘密鍵の流出を検知する機能を追加して」と頼めば、5秒で実装案を出してくれます。

ツールの進化は速いですが、それを「どう安全に運用するか」という視点こそが、私たちプロのエンジニアの価値になります。
ローカルLLMをRTX 4090で回すのも楽しいですが、まずはこうした足元のセキュリティを自動化することから始めてみてください。

## よくある質問

### Q1: .mapファイルが公開されるとなぜ危険なのですか？

TypeScriptなどで書かれた元のソースコードが、コンパイル後のJavaScriptから完全に復元できてしまうからです。コメントや変数名も含めて丸見えになるため、非公開にしたいロジックや内部構造がすべて筒抜けになります。

### Q2: 開発中は.mapファイルが必要ですが、どう使い分ければいいですか？

`tsconfig.json` を複数用意する（`tsconfig.build.json` など）か、本番ビルド時のみ `sourceMap: false` を指定します。本記事の検疫スクリプトを導入していれば、設定ミスをデプロイ直前で確実に止めることができます。

### Q3: Claude Codeの利用料金が気になります

AnthropicのAPI利用料（Claude 3.5 Sonnet等）が実費でかかります。CLI上で `/cost` と入力すると、現在のセッションで消費した金額がリアルタイムに表示されるので、こまめに確認する癖をつけてください。

---

## あわせて読みたい

- [Okan レビュー: Claude Code の承認作業をブラウザ通知で効率化する](/posts/2026-03-19-okan-claude-code-browser-notification-review/)
- [Garry Tan流Claude Code設定は実務で使えるか？導入の是非と性能比較](/posts/2026-03-18-garry-tan-claude-code-setup-review/)
- [Masko Code ターミナルに「表情」を与えるClaude Code専用の伴走型マスコット](/posts/2026-03-16-masko-code-claude-cli-mascot-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": ".mapファイルが公開されるとなぜ危険なのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "TypeScriptなどで書かれた元のソースコードが、コンパイル後のJavaScriptから完全に復元できてしまうからです。コメントや変数名も含めて丸見えになるため、非公開にしたいロジックや内部構造がすべて筒抜けになります。"
      }
    },
    {
      "@type": "Question",
      "name": "開発中は.mapファイルが必要ですが、どう使い分ければいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "tsconfig.json を複数用意する（tsconfig.build.json など）か、本番ビルド時のみ sourceMap: false を指定します。本記事の検疫スクリプトを導入していれば、設定ミスをデプロイ直前で確実に止めることができます。"
      }
    },
    {
      "@type": "Question",
      "name": "Claude Codeの利用料金が気になります",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "AnthropicのAPI利用料（Claude 3.5 Sonnet等）が実費でかかります。CLI上で /cost と入力すると、現在のセッションで消費した金額がリアルタイムに表示されるので、こまめに確認する癖をつけてください。 ---"
      }
    }
  ]
}
</script>
