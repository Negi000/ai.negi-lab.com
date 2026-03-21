---
title: "Cursor Composerと外部APIを連携して大規模コード解析ツールを作る方法"
date: 2026-03-22T00:00:00+09:00
slug: "cursor-composer-moonshot-api-tutorial"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Cursor Composer 使い方"
  - "Moonshot AI API"
  - "Fireworks.ai 連携"
  - "大規模コード解析"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- CursorのComposer機能とFireworks/Moonshot APIを連携させ、10万行を超えるような大規模プロジェクトの仕様書を自動生成する環境を構築します。
- Pythonでリポジトリ構成をスキャンし、外部LLMが解釈しやすい形式に整形してComposerへ渡す補助スクリプトを作成します。
- 前提知識：Pythonの基本的な読み書きができること、GitHubのアカウントを持っていること。
- 必要なもの：Cursor（Proプラン推奨だが無料版でも可）、Fireworks.aiのAPIキー（Moonshotモデルを利用するため）。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">BenQ PD3220U</strong>
<p style="color:#555;margin:8px 0;font-size:14px">広大なコードをComposerで俯瞰するには、高精細な32インチ4Kモニターが必須です。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=BenQ%20PD3220U&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FBenQ%2520PD3220U%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FBenQ%2520PD3220U%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

Cursor標準のClaude 3.5 Sonnetは極めて優秀ですが、無料枠やProの高速リクエスト枠には制限があります。
また、特定のタスク、例えば「巨大な既存コードベースの全体像を把握する」場合、Moonshot AI（Kimi）のように長文コンテキストに特化したモデルをFireworks経由で利用する方が、コスト効率と精度のバランスが良いケースがあるからです。

Redditでも話題になった通り、Moonshot側がCursorからのアクセスを正式に認可した（Fireworks経由のパートナーシップ）ことで、API利用の安定性が保証されました。
SIer時代、数千ファイルのJavaソースを前に絶望していた私からすれば、これを外部APIで一気に解析できる環境は、まさに「銀の弾丸」に近いものがあります。
自分のマシン（RTX 4090 2枚挿し）でローカルLLMを回すのも楽しいですが、APIの利便性とスピード、そして「認可済み」という安心感は、実務において何にも代えがたいメリットです。

## Step 1: 環境を整える

まずは外部モデルをCursorで叩くための土台を作ります。
Fireworks.aiにサインアップし、APIキーを取得してください。
Moonshotのモデル（`accounts/fireworks/models/moonshot-v1-128k` など）が利用可能であることを確認します。

```bash
# プロジェクト用ディレクトリの作成
mkdir cursor-moonshot-lab
cd cursor-moonshot-lab

# 依存ライブラリのインストール（解析用スクリプトで利用）
pip install GitPython tiktoken
```

`GitPython`はローカルのリポジトリ情報を取得するために使い、`tiktoken`はコンテキストサイズを計算してAPI制限に引っかからないように調整するために使います。
Python 3.10以上を推奨します。

⚠️ **落とし穴:** Cursorの設定で「OpenAI API」の項目にFireworksのURLを入れる際、末尾の `/v1` を忘れると接続エラーになります。また、モデル名の指定もFireworks独自の形式（ `accounts/...` ）が必要な点に注意してください。

## Step 2: Cursorの外部モデル設定

Cursorを開き、設定（Cmd+Shift+J / Ctrl+Shift+J）から「Models」タブを開きます。
ここで「OpenAI API」を選択し、以下の通り入力します。

1. **API Key:** Fireworksで取得したキー
2. **Base URL:** `https://api.fireworks.ai/inference/v1`
3. **Model Name:** 使用したいモデル名（例: `accounts/fireworks/models/moonshot-v1-128k`）

設定後、Cursorの右サイドバーにある「Composer」タブ（Ctrl+I）を開きます。
モデル選択プルダウンから、今追加した外部モデルが選択できるようになっているはずです。

なぜこの設定にするかというと、CursorのComposerは「複数のファイルを跨いでコードを生成・修正する」という非常に強力な権限を持っているからです。
標準モデルではなく外部APIを使うことで、自分が使いたい「特定の能力（長文読解など）」を持ったAIを、CursorのUIのまま利用できるようになります。

## Step 3: プロジェクト解析補助スクリプトの作成

Composerに巨大なプロジェクトをそのまま読み込ませると、無関係なバイナリファイルやライブラリまで読み込んでトークンを浪費します。
必要なソースコードだけを抽出し、一つのプロンプト用テキストにまとめるスクリプトを書いていきます。

```python
import os
import git
from pathlib import Path

def get_project_structure(root_dir):
    """プロジェクトのファイル構成をツリー形式で取得する"""
    structure = []
    for root, dirs, files in os.walk(root_dir):
        # 除外するディレクトリ
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv']]
        level = root.replace(root_dir, '').count(os.sep)
        indent = ' ' * 4 * level
        structure.append(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            structure.append(f"{sub_indent}{f}")
    return "\n".join(structure)

def collect_source_codes(root_dir, extensions=['.py', '.js', '.ts', '.java']):
    """指定した拡張子のファイルを読み込み、パスと内容をセットにする"""
    content_list = []
    root_path = Path(root_dir)

    for ext in extensions:
        for file_path in root_path.rglob(f'*{ext}'):
            # 除外パスのチェック
            if any(part in str(file_path) for part in ['.git', 'node_modules', '.venv']):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    content_list.append(f"--- FILE: {file_path.relative_to(root_path)} ---\n{code}\n")
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    return "\n".join(content_list)

if __name__ == "__main__":
    target_project = "./"  # 解析したいプロジェクトのパス

    print("プロジェクト構造を解析中...")
    structure = get_project_structure(target_project)

    print("ソースコードを収集中...")
    all_codes = collect_source_codes(target_project)

    # 最終的なプロンプトの構築
    final_prompt = f"""
あなたはシニアエンジニアです。以下のプロジェクト構成とソースコードを読み込み、
全体像を解説した「ARCHITECTURE.md」を作成してください。

# プロジェクト構成
{structure}

# ソースコード
{all_codes}
"""

    with open("prompt_for_composer.txt", "w", encoding="utf-8") as f:
        f.write(final_prompt)

    print("prompt_for_composer.txt が生成されました。これをComposerに貼り付けてください。")
```

### 期待される出力

実行すると、カレントディレクトリに `prompt_for_composer.txt` が生成されます。
中身には、プロジェクト内の全ファイルのパスとコードが整理された状態で格納されています。

なぜ「ファイルごと」に読み込ませるのではなく、一旦テキストにまとめるのか。
それは、CursorのComposer（Ctrl+I）において、一つの巨大な「文脈」としてAIにプロジェクト全体を叩き込む方が、ファイル間の依存関係や設計意図を正確に把握させやすいからです。

## Step 4: Composerで実行する

1. 生成された `prompt_for_composer.txt` を開いて全選択・コピーします。
2. Cursorで `Ctrl + I` を押し、Composerを起動します。
3. モデルに先ほど設定した `moonshot-v1-128k` を選択します。
4. コピーした内容を貼り付け、「このプロジェクトの全体像をARCHITECTURE.mdとして新規作成し、各モジュールの役割を詳細に書いてください」と指示します。

Composerが動き出し、Moonshotの長いコンテキスト許容量を活かして、プロジェクト全体を俯瞰したドキュメントが一気に書き上げられます。
私が実際に試したところ、小規模なマイクロサービス程度であれば30秒ほどで完璧なドキュメントが生成されました。
レスポンスの速さと、複数のファイルを同時に認識している感覚は、単なるチャットUIでのやり取りとは一線を画します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| API接続エラー (401) | FireworksのAPIキーが正しくない、または有効化されていない | APIキーの再発行を試し、利用枠（クレジット）があるか確認してください。 |
| Context Length Exceeded | プロンプトが128kトークンを超えている | 解析スクリプトの `extensions` を絞り込むか、特定のディレクトリを除外してください。 |
| Composerが動かない | Cursor側のプロトコル制限 | Cursorを最新版にアップデートし、モデル名がFireworksの指定形式と一致しているか確認してください。 |

## 次のステップ

今回はドキュメント生成を例にしましたが、この構成の真価は「大規模なリファクタリング」で発揮されます。
例えば「プロジェクト全体のロギングを、標準出力から特定のライブラリに一括置換して」という指示を、128kのコンテキストを持つMoonshotに投げれば、ファイル間の依存を壊すことなく一気通貫で修正案を提示してくれます。

次は、自作のPythonスクリプトと組み合わせて「コードの品質チェック（静的解析）を外部APIに依頼し、その結果をComposer経由で自動修正させる」といったパイプラインの構築に挑戦してみてください。
実務においては、単にコードを書かせるだけでなく「既存の負債をどう効率的に返済するか」という視点でAIを使うのが、エンジニアとしての価値を高める近道です。
RTX 4090を回すのも良いですが、こうしたクラウドAPIの「公認」された連携を使いこなすのも、プロの道具選びの醍醐味ですよ。

## よくある質問

### Q1: 無料版のCursorでもこの方法は使えますか？

はい、使えます。設定画面で「OpenAI API」の項目を埋めることで、Cursor側の制限（リクエスト回数など）とは別に、Fireworks側のAPI課金でいくらでも回すことが可能です。むしろ無料枠を使い切った後にこそ有効な手段です。

### Q2: Moonshot以外のモデル（Llama-3等）でも同じことができますか？

可能です。Fireworksで提供されているモデルであれば、モデルIDを書き換えるだけで同じように使えます。ただし、今回Moonshotを推奨したのは、その圧倒的なコンテキスト長（128k〜）が大規模解析に向いているからです。

### Q3: 会社のコードを外部APIに投げても大丈夫でしょうか？

ここが一番の注意点です。FireworksやMoonshotの利用規約を確認し、データが学習に利用されない設定（Opt-out）になっているか、あるいは企業のセキュリティポリシーに反しないかを必ず確認してください。個人開発や認可された環境での利用を前提としています。

---

## あわせて読みたい

- [Cursor Glass 使い方 レビュー：自律型エージェントの「状態」をクラウドへ引き継ぐ次世代ワークスペースの真価](/posts/2026-03-21-cursor-glass-agent-workspace-review-handoff/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "無料版のCursorでもこの方法は使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、使えます。設定画面で「OpenAI API」の項目を埋めることで、Cursor側の制限（リクエスト回数など）とは別に、Fireworks側のAPI課金でいくらでも回すことが可能です。むしろ無料枠を使い切った後にこそ有効な手段です。"
      }
    },
    {
      "@type": "Question",
      "name": "Moonshot以外のモデル（Llama-3等）でも同じことができますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Fireworksで提供されているモデルであれば、モデルIDを書き換えるだけで同じように使えます。ただし、今回Moonshotを推奨したのは、その圧倒的なコンテキスト長（128k〜）が大規模解析に向いているからです。"
      }
    },
    {
      "@type": "Question",
      "name": "会社のコードを外部APIに投げても大丈夫でしょうか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ここが一番の注意点です。FireworksやMoonshotの利用規約を確認し、データが学習に利用されない設定（Opt-out）になっているか、あるいは企業のセキュリティポリシーに反しないかを必ず確認してください。個人開発や認可された環境での利用を前提としています。 ---"
      }
    }
  ]
}
</script>
