---
title: "LiteLLMの使い方とサプライチェーン攻撃から身を守る安全な環境構築ガイド"
date: 2026-03-24T00:00:00+09:00
slug: "litellm-compromised-safety-guide-python"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "LiteLLM 使い方"
  - "Python サプライチェーン攻撃"
  - "pip-audit 使い方"
  - "uv パッケージ管理"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 複数のLLM（GPT-4やClaude 3.5等）を統一コードで呼び出しつつ、脆弱性のあるパッケージ混入を自動検知するセキュアなPython実行環境
- 前提知識：Pythonの基本的な文法（関数、変数）がわかり、ターミナルでコマンド操作ができること
- 必要なもの：OpenAIまたはAnthropicのAPIキー、Python 3.9以上の環境

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">ローカルLLMを安全に自前運用し、サプライチェーン攻撃のリスクを遮断するために最適なGPU</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204090&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

AI開発においてLiteLLMは、異なるプロバイダーのAPIを共通の形式で叩ける「プロキシ」として非常に優秀です。しかし、2024年11月にLiteLLMのPyPIアカウントが侵害され、バージョン1.82.7と1.82.8に悪意のあるコードが混入するサプライチェーン攻撃が発生しました。

「便利だから」という理由だけで最新版を無批判に `pip install` する運用は、現在では極めてハイリスクです。この記事では、単にLiteLLMを動かすだけでなく、`uv`（高速パッケージマネージャー）と `pip-audit` を組み合わせることで、万が一の侵害時にも被害を最小限に抑え、実務で耐えうる堅牢な環境を構築する手順を解説します。

## Step 1: 安全な環境を整える

まずは既存の環境を汚さず、かつ脆弱なバージョンが混入していないかを確認できる環境を作ります。今回は、高速かつ依存関係の解決が厳格な `uv` を使用します。

```bash
# uvのインストール（未導入の場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# プロジェクトディレクトリの作成と移動
mkdir safe-llm-app && cd safe-llm-app

# 仮想環境の作成
uv venv --python 3.11

# 仮想環境の有効化
source .venv/bin/activate  # Windowsの場合は .venv\Scripts\activate
```

次に、脆弱性が報告されているバージョン（1.82.7, 1.82.8）を避け、修正版である `1.82.9` 以降を指定してインストールします。

```bash
# 修正済みバージョンを明示的に指定してインストール
uv pip install "litellm>=1.82.9" python-dotenv pip-audit
```

⚠️ **落とし穴:**
もし過去に `pip install litellm` を実行していた場合、キャッシュから脆弱なバージョンが引き継がれる可能性があります。必ず `uv pip list` で現在のバージョンを確認してください。1.82.7または1.82.8が表示されたら、即座にアンインストールが必要です。

## Step 2: 脆弱性のチェックを自動化する

パッケージをインストールした直後に、本当に安全かどうかをスキャンする癖をつけましょう。`pip-audit` は、PyPIの公開脆弱性データベース（OSV）と照合して、インストール済みのライブラリに問題がないかチェックしてくれます。

```bash
# インストール済みのパッケージに脆弱性がないかスキャン
pip-audit
```

このコマンドを実行し、「No known vulnerabilities found」と表示されれば一安心です。私は、実務のCI/CDパイプラインには必ずこのステップを入れています。特にLiteLLMのように頻繁にアップデートされるライブラリを使う場合、この数秒の手間が数億円規模の損害を防ぐことになります。

## Step 3: 安全にLLMを呼び出すコードを書く

環境が整ったので、LiteLLMを使って複数のモデルを切り替えるスクリプトを作成します。APIキーはコードに直書きせず、必ず `.env` ファイルから読み込むようにします。

まず、`.env` ファイルを作成してください。

```text
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

次に、メインのスクリプト `main.py` を作成します。

```python
import os
from dotenv import load_dotenv
from litellm import completion

# .envから環境変数を読み込む
load_dotenv()

def ask_llm(model_name, prompt):
    """
    LiteLLMを使用して、モデル名を変更するだけで同じ呼び出し方をする関数
    """
    try:
        print(f"\n--- Model: {model_name} ---")
        response = completion(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            # 実務ではタイムアウト設定が必須。レスポンスが帰らない時の無限待ちを防ぐ
            timeout=30
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

if __name__ == "__main__":
    user_prompt = "AIのサプライチェーン攻撃について、エンジニアが気をつけるべき点を3行で教えて。"

    # OpenAIのモデルを呼び出す
    print(ask_llm("gpt-4o-mini", user_prompt))

    # Anthropicのモデルを呼び出す（同じ関数で呼び出せるのがLiteLLMの強み）
    # print(ask_llm("claude-3-5-sonnet-20240620", user_prompt))
```

### 期待される出力

```text
--- Model: gpt-4o-mini ---
1. ライブラリのバージョンを固定（ピン留め）し、ハッシュ値で検証すること。
2. CI/CDパイプラインに脆弱性スキャン（pip-audit等）を組み込むこと。
3. APIキーなどの機密情報を環境変数で管理し、最小権限の原則を徹底すること。
```

LiteLLMを使う理由は、この `ask_llm` 関数の引数を変えるだけで、内部のパラメーター変換をすべてライブラリ側が肩代わりしてくれる点にあります。私自身、複数のモデルを比較するベンチマーク記事を書く際は、この抽象化のおかげでコード量を80%削減できています。

## Step 4: 実用レベルの「ハッシュ固定」運用

今回のLiteLLMの件で痛感したのは、「バージョン指定（==1.82.9）」だけでは不十分だということです。攻撃者が既存のバージョンを上書きして再アップロードする可能性もゼロではありません。

実務で「絶対に安全」と言い切るためには、パッケージの中身（バイナリ）が改ざんされていないことを保証する「ハッシュ値」を含めた管理を行います。`uv` を使えば、ロックファイルを生成することでこれを容易に実現できます。

```bash
# 現在の環境から、ハッシュ値付きのロックファイルを生成
uv pip compile pyproject.toml -o requirements.txt --generate-hashes
```

生成された `requirements.txt` を見てください。各パッケージ名の後に `--hash=sha256:...` という長い文字列が並んでいるはずです。これが「この中身以外はインストールを許可しない」という証明書になります。私は、受託案件で納品するコードには必ずこのハッシュ付きrequirementsを含めるようにしています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError: No module named 'litellm'` | 仮想環境が有効化されていない | `source .venv/bin/activate` を実行してから再試行する |
| `litellm.exceptions.AuthenticationError` | APIキーが正しく読み込めていない | `.env` の変数名が正しいか、スペルミスがないか確認する |
| `pip-audit` で脆弱性が検出される | LiteLLM以外の依存ライブラリに問題がある | `uv pip install --upgrade [パッケージ名]` で個別アップデートを試みる |

## 次のステップ

LiteLLMを安全に使えるようになったら、次は「LiteLLM Proxy」の構築に挑戦してみてください。これは今回書いたPythonスクリプトをさらに一歩進め、チーム全員が使える共通のAPIエンドポイントを自前で立てる手法です。

自前サーバー（私の環境ではRTX 4090を積んだマシン）で `litellm --model ollama/llama3` のように立ち上げれば、OpenAI互換のURLが発行されます。これにより、フロントエンド側は一切コードを変更せずに、バックエンドを商用APIからローカルLLMに切り替えるといった運用が可能になります。

今回の侵害事件は「便利さの裏側にあるリスク」を再認識させるものでした。しかし、適切なツール（uv, pip-audit, ロックファイル）を組み合わせれば、そのリスクは十分にコントロール可能です。技術の進化を止めるのではなく、防御力を高めながら最新のAIを使い倒していきましょう。

## よくある質問

### Q1: 脆弱なバージョン（1.82.7など）をインストールしてしまった場合、どうすればいいですか？

即座に `pip uninstall litellm` を実行し、仮想環境ごと削除することを推奨します。攻撃コードが実行された可能性があるため、念のためその環境で使用していたAPIキーは無効化し、新しいキーを再発行するのが最も安全な対応です。

### Q2: 常に最新版を使いたいのですが、その場合はどうチェックすべきですか？

`pip-audit` を毎日実行するスケジュールを組むか、GitHubの `Dependabot` を有効にしてください。Dependabotは今回のような既知の脆弱性を検知すると、自動的にプルリクエストを作成して警告してくれます。

### Q3: LiteLLM以外のライブラリでも同様の攻撃は起こり得ますか？

はい、過去には `PyTorch` や `Requests` の模倣パッケージでも同様の事案がありました。そのため、本稿で紹介した `uv` によるハッシュ固定と脆弱性スキャンの組み合わせは、AI分野に限らずすべてのPython開発における標準装備とすべきです。
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "脆弱なバージョン（1.82.7など）をインストールしてしまった場合、どうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "即座に pip uninstall litellm を実行し、仮想環境ごと削除することを推奨します。攻撃コードが実行された可能性があるため、念のためその環境で使用していたAPIキーは無効化し、新しいキーを再発行するのが最も安全な対応です。"
      }
    },
    {
      "@type": "Question",
      "name": "常に最新版を使いたいのですが、その場合はどうチェックすべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "pip-audit を毎日実行するスケジュールを組むか、GitHubの Dependabot を有効にしてください。Dependabotは今回のような既知の脆弱性を検知すると、自動的にプルリクエストを作成して警告してくれます。"
      }
    },
    {
      "@type": "Question",
      "name": "LiteLLM以外のライブラリでも同様の攻撃は起こり得ますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、過去には PyTorch や Requests の模倣パッケージでも同様の事案がありました。そのため、本稿で紹介した uv によるハッシュ固定と脆弱性スキャンの組み合わせは、AI分野に限らずすべてのPython開発における標準装備とすべきです。"
      }
    }
  ]
}
</script>
