---
title: "Claude CodeとCursorを併用したAIコーディング環境構築と実践ガイド"
date: 2026-11-11T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-setup-guide"
cover:
  image: "/images/posts/2026-11-11-claude-code-cursor-ai-coding-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用"
  - "AIコーディング"
  - "FastAPI 自動生成"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

外部の天気API（Open-Meteo）から情報を取得し、特定の都市の天気を表示するFastAPIベースのWebアプリケーションを開発します。
Cursorで全体の設計とボイラープレートを作成し、Claude Codeでテスト実装とデバッグ、Gitコミットまでを自動化するワークフローを構築します。

前提知識：
- 基本的なPythonの文法がわかる
- ターミナルの基本的な操作（cd, lsなど）ができる
- GitHubのアカウントを所有している

必要なもの：
- Anthropic API Key（Tier 2以上の課金実績が必要）
- Cursor（Proプラン推奨）
- Node.js (v18.19.0以上)

## 先に確認するスペック・料金

AIコーディングを本気で行うなら、ツールへの投資を惜しんではいけません。
Claude Codeを利用するには、Anthropic APIのTier 2（累計40ドル以上の支払い）が必要です。
Tier 1だとレートリミットが厳しすぎて、一度の実行でエラーが多発し、使い物になりません。
もし条件を満たしていない場合は、まずコンソールでプリペイドチャージを行い、実績を作ってください。

ハードウェアについては、AI処理自体はクラウドで行われるため、MacBook Air（M1以降、メモリ16GB以上）があれば十分です。
しかし、私は自宅でRTX 4090を2枚挿してローカルLLMも併用していますが、開発効率を最大化するなら画面領域が重要です。
27インチ以上の4Kモニターを2枚並べ、片方にCursor、片方にブラウザとClaude Codeを表示させるのが「仕事で使える」最小構成だと言えます。
API料金は、今回の記事の内容を試すだけであれば、1〜2ドル程度で収まります。

## なぜこの方法を選ぶのか

現在、Cursorだけでも十分にコードは書けます。
しかし、CursorのComposer（Ctrl+I）は「コードの編集」には強いものの、「ターミナルの出力を読み取って何度も試行錯誤する」という自律的なタスク実行において、Claude Codeに一歩譲ります。
Claude CodeはAnthropicが公式に提供するエージェント型CLIであり、ファイル編集だけでなく、コマンド実行結果をループで解釈し、テストが通るまで勝手に修正を繰り返します。

「Cursorで全体の骨組みを作り、Claude Codeで泥臭いデバッグと動作確認を任せる」。
この役割分担が、現時点での開発速度を最も加速させる最適解です。
エディタを行き来する時間を削り、ターミナル内で完結する作業を増やすことが、プログラミングにおける「フロー状態」を維持する鍵になります。

## Step 1: 環境を整える

まずはClaude Codeを動かすためのNode.js環境を確認します。
Claude Codeはnpm経由でインストールするツールですが、バージョン管理が甘いと起動時にエラーを吐きます。

```bash
# Node.jsのバージョン確認。18系、20系、22系が推奨されています。
node -v

# Claude Codeのインストール。グローバルにインストールします。
npm install -g @anthropic-ai/claude-code

# インストールが完了したら、正常に起動するか確認します。
claude --version
```

次に、プロジェクト用のディレクトリを作成し、Cursorで開きます。

```bash
mkdir ai-weather-app
cd ai-weather-app
git init
cursor .
```

⚠️ **落とし穴:**
Claude Codeを起動した際、`CLAUDE_CONFIG_DIR` の権限エラーが出ることがあります。
その場合は `sudo` でインストールするのではなく、`nvm` や `volta` などのバージョン管理ツールを使い、ユーザー権限でnpmパッケージを扱えるようにしてください。
また、APIキーの設定が済んでいない場合は、後ほど初回起動時に認証画面へ飛ばされます。

## Step 2: 基本の設定

FastAPIを動かすための仮想環境を作成し、必要なライブラリを定義します。
ここでのポイントは、AIに「何をさせるか」を明確にするための `requirements.txt` です。

```python
# requirements.txt
fastapi==0.115.0
uvicorn==0.30.6
httpx==0.27.2
pytest==8.3.3
```

次に、Claude Codeを起動して初期設定を行います。
ターミナル（Cursor内のターミナルでOK）で以下のコマンドを打ちます。

```bash
claude
```

初回起動時はブラウザが開くので、Anthropicアカウントでログインして認証してください。
認証後、プロジェクトのインデックス作成が始まります。
これはプロジェクト内のファイルをClaudeが理解するためのステップです。

なぜこの設定にするのか：
`httpx` を入れているのは、外部API（Open-Meteo）を非同期で叩くためです。
FastAPIは非同期処理が得意なため、同期型の `requests` を使うのは悪手です。
こうした「技術選定の意図」をAIに伝えずとも、適切なライブラリを組み合わせてくれるのがClaude Codeの強みです。

## Step 3: 動かしてみる

ここからが本番です。
Cursorで空の `main.py` を作成し、Claude Codeに対して以下のプロンプトを投げます。
「/」から始まるスラッシュコマンドではなく、自然言語で指示を出します。

```text
Open-Meteo APIを使って、東京の現在の気温を返すFastAPIアプリを作ってください。
エンドポイントは /weather とし、City名を受け取れるようにしてください。
バリデーションもしっかりお願いします。
```

### 期待される出力

Claude Codeが勝手にファイルを書き換え、以下のようなログが流れます。

```text
Thinking: Creating main.py with FastAPI and httpx...
Done: main.py created.
Thinking: Testing the implementation...
Ran: uvicorn main:app --reload
...
```

コード例（Claude Codeが生成する内容のイメージ）：

```python
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class WeatherResponse(BaseModel):
    city: str
    temperature: float

@app.get("/weather", response_model=WeatherResponse)
async def get_weather(city: str):
    # 東京の固定座標（デモ用）
    lat, lon = 35.6895, 139.6917

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Weather API error")

        data = response.json()
        temp = data["current_weather"]["temperature"]

    return WeatherResponse(city=city, temperature=temp)
```

この時点で、別のターミナルで `uvicorn main:app --reload` を実行し、ブラウザで `http://localhost:8000/weather?city=Tokyo` にアクセスすれば、温度が返ってくるはずです。

## Step 4: 実用レベルにする

今のままでは「東京の座標」がハードコードされています。
これを「都市名から座標を検索し、その天気を返す」という実用的な形にアップグレードさせます。
ここでのデバッグをClaude Codeに丸投げします。

Claude Codeにこう指示してください。
「都市名から座標を取得するジオコーディング機能を追加してください。エラーハンドリングとして、存在しない都市名が渡された場合は404を返すように。あと、これに対するpytestも書いて実行して。」

```bash
# Claude Codeのプロンプト
都市名から座標を取得する機能を追加して、プロジェクトを完成させてください。
テストコードも作成し、実際にテストがパスすることを確認してください。
```

Claude Codeは以下のステップを勝手に行います：
1. `main.py` を修正してジオコーディングAPI（Open-MeteoのGeocoding APIなど）を叩く処理を追加。
2. `tests/test_main.py` を作成。
3. `pytest` コマンドを実行。
4. もしテストが落ちたら（例：非同期の扱いミスなど）、エラーメッセージを読んでコードを修正。
5. テストが通るまでループ。

これが、Cursorにはできない「実行を伴う開発」です。
最後に、Claude Codeの中で以下のコマンドを打ち、これまでの変更を記録します。

```bash
/commit "Add geocoding support and comprehensive error handling"
```

Gitのメッセージまで、変更内容を反映した正確なものを生成してくれます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Rate limit reached | API Tierが低い、または短時間にプロンプトを投げすぎ | Tier 2へのアップグレードを確認し、少し時間を置く。 |
| Command not found: claude | パスが通っていない | `npm bin -g` で場所を確認し、PATHに追加するか、Node環境を再構築する。 |
| Test failed (Async) | FastAPIのテストで `httpx.AsyncClient` の扱いが古い | Claude Codeに「pytest-asyncioを使って非同期テストを修正して」と指示する。 |

## 次のステップ

おめでとうございます。Claude CodeとCursorを組み合わせた次世代の開発スタイルを体験できました。
この環境をマスターした後は、以下の課題に挑戦してみてください。

1. **MCP（Model Context Protocol）の導入**: Claude Codeに独自のツールを教え込むことができます。例えば、社内DBのスキーマを教えたり、特定のデプロイコマンドを教えたりして、さらに自律性を高めることが可能です。
2. **Cline (旧Devins) との比較**: VS Code拡張機能であるClineも同様のことができます。Cursor + Claude Codeという「公式ツール併用」と、VS Code + Clineという「拡張機能完結」のどちらが自分の指に馴染むか検証する価値があります。
3. **ローカルLLMとの接続**: 私のようにRTX 4090を持っているなら、機密性の高いコードはOllama経由でローカルLLMに、複雑なロジックはClaude 3.5 Sonnetに、と使い分けるプロキシを構築してみてください。

AIは「下書き」をさせるツールから、今や「実行」を任せるエージェントへと進化しました。
「自分で書いたほうが早い」というプライドを捨て、いかにAIに「正しく動かさせるか」に注力することが、今後のエンジニアの生存戦略です。

## よくある質問

### Q1: CursorのComposer機能があるのに、なぜわざわざClaude Codeを使うのですか？

CursorのComposerは、コードベース全体の書き換えやUIのプレビューには非常に優れています。
一方でClaude Codeは、ターミナルで発生したコンパイルエラーやテストの失敗ログを「直接読み取り、コマンドを実行して修正する」というループが圧倒的に速いです。
設計はCursor、泥臭いデバッグと動作確認はClaude Code、という使い分けが現状ベストです。

### Q2: API料金が怖いです。節約する方法はありますか？

Claude Code内で `/compact` コマンドを定期的に使いましょう。
会話のコンテキストが長くなりすぎると、送信されるトークン量が増えて課金額が跳ね上がります。
また、`.claudeignore` ファイルを作成し、不要な node_modules やログファイルをスキャン対象から外すことも重要です。

### Q3: Windowsでも同じように動きますか？

WSL2（Windows Subsystem for Linux）上であれば、この記事の内容はそのまま動きます。
PowerShell直上での運用は、パスの扱いやシェルコマンドの差異でClaude Codeが混乱することがあるため、おすすめしません。
本格的なAI開発環境を作るなら、WSL2またはMacを選択してください。

---

### 【重要】メタデータ出力

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">複数のAIエージェントとIDEを同時に動かすためのメモリと処理能力を確保するため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用して開発効率を3倍に引き上げるAIコーディング環境構築ガイド](/posts/2026-11-09-claude-code-cursor-ai-coding-setup-guide/)
- [Claude CodeとCursorを併用した最強AIコーディング環境構築ガイド](/posts/2026-10-30-claude-code-cursor-setup-guide-2025/)
- [Claude CodeとCursorを併用する最強のAIコーディング環境構築ガイド](/posts/2026-10-19-claude-code-cursor-ai-coding-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "CursorのComposer機能があるのに、なぜわざわざClaude Codeを使うのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "CursorのComposerは、コードベース全体の書き換えやUIのプレビューには非常に優れています。 一方でClaude Codeは、ターミナルで発生したコンパイルエラーやテストの失敗ログを「直接読み取り、コマンドを実行して修正する」というループが圧倒的に速いです。 設計はCursor、泥臭いデバッグと動作確認はClaude Code、という使い分けが現状ベストです。"
      }
    },
    {
      "@type": "Question",
      "name": "API料金が怖いです。節約する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Code内で /compact コマンドを定期的に使いましょう。 会話のコンテキストが長くなりすぎると、送信されるトークン量が増えて課金額が跳ね上がります。 また、.claudeignore ファイルを作成し、不要な nodemodules やログファイルをスキャン対象から外すことも重要です。"
      }
    },
    {
      "@type": "Question",
      "name": "Windowsでも同じように動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "WSL2（Windows Subsystem for Linux）上であれば、この記事の内容はそのまま動きます。 PowerShell直上での運用は、パスの扱いやシェルコマンドの差異でClaude Codeが混乱することがあるため、おすすめしません。 本格的なAI開発環境を作るなら、WSL2またはMacを選択してください。 ---"
      }
    }
  ]
}
</script>
