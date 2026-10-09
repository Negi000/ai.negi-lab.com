---
title: "Claude CodeとCursorを併用した最強AIコーディング環境の構築と実践"
date: 2026-10-09T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-guide"
cover:
  image: "/images/posts/2026-10-09-claude-code-cursor-ai-coding-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用"
  - "AIコーディング"
  - "自動テスト Python"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- FastAPIを使用した「TODO管理API」のプロトタイプ作成
- Claude Codeによる「全自動テスト実装とバグ修正」の実行
- Cursorによる「UI/UXの微調整とリファクタリング」の同期

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">HHKB Professional HYBRID Type-S</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIとの対話が増えるほど高速で正確な打鍵が重要になるため、エンジニアの必需品。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FHHKB%2520Professional%2520HYBRID%2520Type-S%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FHHKB%2520Professional%2520HYBRID%2520Type-S%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=HHKB%20Professional%20HYBRID%20Type-S&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

この記事を読み進めることで、Cursorという「最強のIDE」と、Claude Codeという「自律型エージェント」をどう使い分けるべきか、実務レベルの最適解が手に入ります。

## 先に確認するスペック・料金

AIコーディングを本気で仕事に使うなら、ケチってはいけないポイントが2つあります。

1. **Claude APIの従量課金:** Claude CodeはAnthropicのAPIキー（ティア2以上推奨）を使用します。初期の実験で$5〜10程度、がっつり開発すると月間$50〜$100程度は見込むべきです。無料枠ではすぐにレートリミットに当たります。
2. **Cursor Proプラン ($20/月):** 無料版でも使えますが、Claude 3.5 Sonnetを無制限に近い感覚で叩けないと、思考の速度が落ちます。これは必要経費です。
3. **ハードウェア:** Node.js 18以上が動く環境なら問題ありませんが、Claude Codeはターミナルを占有し、Cursorはメモリを食います。MacBookであればメモリ16GB以上、WindowsであればRTX 3060以上のGPUがあると、ローカルLLMとの併用（Copilot++の補完など）が快適になります。

もしAPI料金を抑えたい場合は、Claude Codeに渡すコンテキスト（ファイル数）を絞る設定が必須です。

## なぜこの方法を選ぶのか

現在、AIコーディングツールは「IDE一体型（Cursor, GitHub Copilot）」と「CLI・エージェント型（Claude Code, Aider, Cline）」の2陣営に分かれています。

Cursorは「今開いているファイル」の編集や、チャットを通じたUIの微調整には無類の強さを誇ります。しかし、プロジェクト全体に跨る大規模なリファクタリングや、「テストを実行してエラーが出たら直す」というループ処理は、IDEのUIを介すと操作の手間が増えます。

そこで、ターミナル上で自律的にシェルコマンドを実行し、テスト結果を読み取って自己修正を繰り返す「Claude Code」を併用します。
「Cursorで大枠の設計とUIを作り、Claude Codeでロジックの堅牢性を固める」という役割分担が、現時点で最も開発速度を最大化できるアプローチです。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。これはAnthropicが公開した公式のCLIツールです。

```bash
# Node.js 18.x以上が必要です
npm install -g @anthropic-ai/claude-code

# 認証（ブラウザが開きます）
claude auth login
```

次に、プロジェクトディレクトリを作成し、Cursorで開きます。

```bash
mkdir ai-coding-lab
cd ai-coding-lab
cursor .
```

`npm install -g` を使うのは、Claude Codeをどのプロジェクトからも呼び出せる「開発パートナー」として扱うためです。プロジェクトごとにインストールすると、依存関係の解決に時間がかかり、開発のテンポが損なわれます。

⚠️ **落とし穴:**
Windows環境（PowerShell）で実行する場合、実行ポリシーの制限でスクリプトが動かないことがあります。その場合は、管理者権限で `Set-ExecutionPolicy RemoteSigned` を実行してください。また、Claude Codeは内部で `git` を多用するため、`git init` されていないディレクトリでは動作が不安定になります。必ず最初に `git init` を行いましょう。

## Step 2: 基本の設定

Pythonの仮想環境を作り、FastAPIの最小構成を作成します。ここではあえて「少しバグを含んだコード」を書かせます。

```bash
python -m venv .venv
source .venv/bin/activate  # Windowsは .venv\Scripts\activate
pip install "fastapi[standard]" pytest requests
```

次に、`.gitignore` を作成します。これは非常に重要です。

```bash
# .gitignore
.venv/
__pycache__/
.claude/
.cursor/
```

⚠️ **なぜ`.gitignore`を細かく設定するのか:**
Claude Codeはプロジェクト内のファイルをスキャンしてコンテキストを理解します。`.venv` やキャッシュファイルまで読み込ませてしまうと、APIトークンを無駄に消費するだけでなく、LLMが混乱して誤答の原因になります。「AIに読ませる必要のないものは徹底的に隠す」のが、安く・速く動かすコツです。

## Step 3: Claude Codeを動かしてみる

いよいよClaude Codeを起動します。ターミナルで `claude` と打ち込んでください。

```bash
claude
```

対話モードになったら、以下の指示を出します。

```text
FastAPIを使って、TODO管理ができるAPIを作ってください。
ただし、以下の条件を守ってください。
1. main.pyに全てのロジックを書くこと
2. データベースは使わず、メモリ内のリストで管理すること
3. 意図的に「完了済みのTODOを削除できない」というバグを一つ混ぜて作成してください
```

### 期待される出力

Claude Codeがファイルを自動作成します。完了したら、続けてこう指示します。

```text
今のコードに対してpytestを書け。
その後、実際にテストを実行して、失敗することを確認しろ。
失敗を確認したら、コードを修正してテストをパスさせろ。
```

ここで注目すべきは、私が「コマンドを叩け」と言わなくても、Claude Codeが勝手に `pytest` を実行し、その標準出力を読み取り、バグを特定して `main.py` を修正し始める点です。これがCursor単体では難しい「ループの自動化」です。

## Step 4: Cursorで実用レベルにする

Claude Codeがロジックを完成させたら、今度はCursorにバトンタッチします。

Cursorで `main.py` を開くと、Claude Codeが行った修正が反映されています。ここで、人間がUIやコードの可読性をチェックします。

1. **Composer (Ctrl + I) を起動**
2. 以下のプロンプトを入力

```text
現在のmain.pyのロジックを維持したまま、以下のリファクタリングを行ってください。
- schemas.py（Pydanticモデル定義）
- crud.py（ビジネスロジック）
- main.py（APIエンドポイント定義）
の3つのファイルに分割し、メンテナンス性を高めてください。
また、各エンドポイントに適切なdocstringを追加してください。
```

Cursorはファイル構造の変更や、複数ファイルにまたがるコードの移動を視覚的に「差分（Diff）」として提示してくれます。これを一つずつ確認（Accept）していくことで、エージェントが勝手にコードを壊すリスクを防ぎつつ、綺麗な構成へと進化させられます。

### 実用的なコード構成の例（リファクタリング後）

```python
# schemas.py
from pydantic import BaseModel

class TodoBase(BaseModel):
    title: str
    is_completed: bool = False

class Todo(TodoBase):
    id: int

# crud.py
from typing import List
from schemas import Todo

class TodoManager:
    def __init__(self):
        self.todos: List[Todo] = []
        self._counter = 1

    def create(self, title: str) -> Todo:
        todo = Todo(id=self._counter, title=title)
        self.todos.append(todo)
        self._counter += 1
        return todo

    def delete_completed(self):
        # Claude Codeが修正したロジックがここにあるはず
        self.todos = [t for t in self.todos if not t.is_completed]
```

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `claude: command not found` | パスが通っていない | `npm bin -g` でパスを確認し、環境変数に追加する |
| APIのRate Limit到達 | 無料枠、またはティアが低い | AnthropicのDashboardでクレジットをチャージしティアを上げる |
| Claude Codeが無限ループする | 指示が曖昧、または環境が壊れている | `Ctrl+C` で止め、`compact` コマンドで文脈を整理する |

## 次のステップ

ここまでで、「CLIでロジックを固め、IDEで構造を整える」という現代のAI開発の王道パターンが体験できたはずです。

次に挑戦すべきは、**「GitHub Actionsとの連携」**です。Claude CodeはCLIツールなので、CI/CDパイプラインに組み込むことが可能です。PRが作成された際に、Claude Codeを起動して自動でコードレビューをさせ、修正案までコミットさせる。そんな「自律型開発フロー」の構築が次のゴールになります。

また、ローカルLLM（Llama 3やQwen 2.5など）をLM Studio等で立ち上げ、Cursorの外部モデル設定に紐付けることで、プライベートなコードを外部に出さずに補完させる環境作りも、プロのエンジニアとしては押さえておきたい領域です。

## よくある質問

### Q1: Cursorだけで十分ではないのですか？

Cursorは素晴らしいですが、「エージェント」としての自律性はClaude Codeの方が一歩先を行っています。特に、シェルコマンドを実行し、その結果（エラーログなど）を自ら読み取って次のアクションを決める能力は、現時点ではClaude Code（CLI）の方が実用的です。

### Q2: API代が怖いです。節約する方法は？

Claude Codeには `.claudeignore` を作成し、画像や動画、重いドキュメントを読み込ませないようにしてください。また、対話が長くなってきたら一度終了して再起動するか、`/compact` コマンドを使って過去のやり取りを圧縮するのも有効です。

### Q3: どちらのモデルを使うべきですか？

迷わず `claude-3-5-sonnet` です。Opusは賢いですが遅く、Haikuは速いですが複雑なロジック修正には向きません。Sonnet 3.5は速度・知能・コストのバランスが開発において「神」レベルで整っています。

---

## あわせて読みたい

- [Claude CodeとCursorを併用して開発効率を最大化するAIコーディング環境構築ガイド](/posts/2026-07-04-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用し、バックエンドのAPIサーバー構築から自動テスト、Gitコミットまでを完全にAI主導で完結させる手法を解説します。](/posts/2026-10-04-claude-code-cursor-workflow-guide/)
- [Claude CodeとCursorを併用！爆速AIコーディング環境構築ガイド](/posts/2026-07-11-claude-code-cursor-hybrid-workflow-guide/)

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
        "text": "Cursorは素晴らしいですが、「エージェント」としての自律性はClaude Codeの方が一歩先を行っています。特に、シェルコマンドを実行し、その結果（エラーログなど）を自ら読み取って次のアクションを決める能力は、現時点ではClaude Code（CLI）の方が実用的です。"
      }
    },
    {
      "@type": "Question",
      "name": "API代が怖いです。節約する方法は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeには .claudeignore を作成し、画像や動画、重いドキュメントを読み込ませないようにしてください。また、対話が長くなってきたら一度終了して再起動するか、/compact コマンドを使って過去のやり取りを圧縮するのも有効です。"
      }
    },
    {
      "@type": "Question",
      "name": "どちらのモデルを使うべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "迷わず claude-3-5-sonnet です。Opusは賢いですが遅く、Haikuは速いですが複雑なロジック修正には向きません。Sonnet 3.5は速度・知能・コストのバランスが開発において「神」レベルで整っています。 ---"
      }
    }
  ]
}
</script>
