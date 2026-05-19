---
title: "Qwen2.5-Coder 使い方 | ローカルでコード生成AIを動かす"
date: 2026-05-19T00:00:00+09:00
slug: "qwen-coder-local-setup-python-refactor"
cover:
  image: "/images/posts/2026-05-19-qwen-coder-local-setup-python-refactor.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen2.5-Coder"
  - "Ollama"
  - "Python"
  - "ローカルLLM 構築"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

Qwen2.5-Coder 32Bをローカル環境に構築し、指定したディレクトリ内の全Pythonコードに対して「型ヒントの追加」と「バグチェック」を自動で行うリファクタリングツールを作成します。
既存のコードベースを読み込ませ、AIが修正案を提示し、必要に応じてファイルを上書きする実用的なスクリプトを完成させます。

前提知識として、Pythonの基本的な文法（関数の定義、ファイルの読み書き）と、ターミナル（コマンドプロンプト）の基本操作ができることを想定しています。

必要なものは、ミドルスペック以上のPC（後述するGPU要件参照）と、Python 3.10以上の実行環境のみです。

## 先に確認するスペック・料金

Qwen2.5-Coder 32Bを「仕事で使える速度」で動かすには、ハードウェア選びが全てです。
最も重要なのはVRAM（ビデオメモリ）の容量で、32Bモデルを4bit量子化（Q4_K_M）で動かす場合、最低でも19GB程度の空きVRAMが必要になります。

Windowsユーザーなら、RTX 3090かRTX 4090（VRAM 24GB）がベストな選択です。
RTX 4060 Ti 16GBモデルでも動作はしますが、モデルのパラメータを少し削るか、さらに強い量子化をかける必要があり、回答の精度が目に見えて落ちます。
もし今から買うなら、中古のRTX 3090を探すのが最もコストパフォーマンスが良いでしょう。

Macユーザーの場合、Apple Silicon（M2/M3/M4）の「Max」か「Ultra」モデルで、ユニファイドメモリを32GB以上積んでいることが条件です。
メモリ16GBのMacBook Airでは、スワップが発生してレスポンスが数秒から数十秒遅れるため、実務で使うにはストレスが溜まります。

API料金は一切かかりません。
一度PCを組んでしまえば、電気代だけで24時間365日、機密情報を外部に送信することなくコードを書かせ放題になります。
これがローカルLLMを構築する最大のメリットです。

## なぜこの方法を選ぶのか

コード生成AIといえばGitHub CopilotやCursor、あるいはClaude 3.5 Sonnetが有名ですが、あえてQwen2.5-Coderをローカルで動かす理由は「プライバシー」と「特化性能」です。

顧客のソースコードをクラウドに投げられない案件は、SIerやフリーランスの実務では意外と多いものです。
Qwen2.5-Coder 32Bは、ベンチマークスコアにおいてClaude 3.5 Sonnetに匹敵、あるいは部分的に凌駕する数値を出しており、オープンモデルとしては現在「最強」の部類に入ります。

また、llama.cppを直接叩くのではなく「Ollama」を経由する方法を選びます。
理由は、APIサーバーとしての管理が非常に楽だからです。
Ollamaを使えば、PythonからOpenAI互換のライブラリで簡単にアクセスでき、将来的にモデルをLlama 3.1やMistralに入れ替える際もコードを一行変えるだけで済みます。

## Step 1: 環境を整える

まずは推論エンジンとなるOllamaをインストールし、Qwen2.5-Coder 32Bをダウンロードします。

```bash
# Ollamaのインストール（公式サイト https://ollama.com/ からダウンロードして実行）
# インストール完了後、ターミナルで以下を実行
ollama pull qwen2.5-coder:32b
```

このコマンドは、Qwen2.5-Coder 32Bモデル（約19GB）をダウンロードします。
光回線でも数分から十数分かかるので、その間にPythonの仮想環境を作っておきましょう。

```bash
# 作業ディレクトリの作成
mkdir qwen-refactor && cd qwen-refactor

# 仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# 必要なライブラリのインストール
pip install ollama tqdm
```

`ollama`ライブラリは、PythonからローカルのOllamaサーバーへ指示を出すための公式SDKです。
`tqdm`は、大量のファイルを処理する際の進捗状況をプログレスバーで表示するために使用します。

⚠️ **落とし穴:**
もし `ollama pull` でエラーが出る、あるいは極端に遅い場合は、バックグラウンドで動いている他のGPUアプリ（ブラウザのハードウェアアクセラレーションやゲーム）を閉じてください。
また、ディスク容量が20GB以上空いていることも確認してください。

## Step 2: 基本の設定

次に、PythonからQwenを呼び出すための基礎部分を書きます。
ここでは、モデルの挙動を安定させるための「System Prompt」の設定が肝になります。

```python
import os
from ollama import Client

# ローカルのOllamaサーバーに接続
# デフォルトで localhost:11434 で動いているはずです
client = Client(host='http://localhost:11434')

MODEL_NAME = "qwen2.5-coder:32b"

def get_ai_response(prompt, system_message):
    """
    Qwenに指示を送り、回答を得る基本関数
    """
    response = client.chat(model=MODEL_NAME, messages=[
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': prompt},
    ], options={
        'temperature': 0.2,  # コード生成なので低めにして決定論的な挙動を優先
        'num_ctx': 8192      # コンテキスト長。32Bならもっと増やせますが、まずは8kで安定させます
    })
    return response['message']['content']

# 動作確認用のシステムプロンプト
SYSTEM_PROMPT = "あなたは優秀なPythonエンジニアです。提供されたコードを改善し、改善したコードのみを出力してください。"
```

温度設定（temperature）を `0.2` にしているのは、コード生成において「創造性」は不要だからです。
同じ入力に対して、常に同じ、かつ正確なコードを出力させることが実務では求められます。

## Step 3: 動かしてみる

最小限の構成で、Qwenが正しくコードを修正できるかテストします。
わざとバグを含んだPythonコードを投げてみましょう。

```python
test_code = """
def add_numbers(a, b):
    result = a + b
    print("Result is " + result)
    return result

add_numbers(10, "20")
"""

print("--- 修正前 ---")
print(test_code)

print("\n--- Qwenによる修正 ---")
improved_code = get_ai_response(
    f"以下のコードには型エラーがあります。修正してください:\n\n{test_code}",
    SYSTEM_PROMPT
)
print(improved_code)
```

### 期待される出力

```python
def add_numbers(a: int, b: int) -> int:
    result = a + int(b)
    print(f"Result is {result}")
    return result

add_numbers(10, 20)
```

Qwenは文字列と数値の加算エラーを見抜き、さらにf-stringへの書き換えや型ヒントの追加まで行ってくれるはずです。
もし出力に「はい、修正しました」といった余計な解説が含まれる場合は、システムプロンプトで「コードブロックのみを出力せよ」とより厳格に命じる必要があります。

## Step 4: 実用レベルにする

それでは、この記事の本題である「プロジェクト全体の自動リファクタリングツール」を完成させます。
カレントディレクトリ内の `.py` ファイルをスキャンし、一気に型ヒントを付けて保存するスクリプトです。

```python
import os
from pathlib import Path
from tqdm import tqdm

def refactor_project(directory_path):
    # システムプロンプトを実用的に強化
    system_message = (
        "あなたはPythonの静的解析とリファクタリングの専門家です。"
        "提供されたソースコードに対し、以下の修正を行ってください。\n"
        "1. 全ての関数とメソッドに適切な型ヒントを追加する。\n"
        "2. 重複したロジックを整理し、可読性を高める。\n"
        "3. 未使用のインポートを削除する。\n"
        "注意：解説文は一切不要です。修正後のコードのみを、Markdownのコードブロックを使わずに直接出力してください。"
    )

    py_files = list(Path(directory_path).glob("**/*.py"))

    for file_path in tqdm(py_files, desc="Refactoring"):
        # 自分自身のスクリプトを書き換えないように保護
        if file_path.name == os.path.basename(__file__):
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            original_code = f.read()

        # AIに修正を依頼
        prompt = f"以下のファイルをリファクタリングしてください。:\n\n{original_code}"
        try:
            refined_code = get_ai_response(prompt, system_message)

            # 念のため空でないかチェックしてから書き込み
            if refined_code.strip():
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(refined_code)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    # カレントディレクトリの 'src' フォルダなどを指定
    target_dir = "./test_src"
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        with open(f"{target_dir}/sample.py", "w") as f:
            f.write("def greet(name):\n    return 'Hello ' + name")

    refactor_project(target_dir)
```

このスクリプトは、指定されたフォルダ内のファイルを逐次処理します。
`num_ctx: 8192` を設定しているため、数千行ある巨大なファイルは処理しきれない場合があります。
その場合は、関数単位で分割してAIに投げるようなロジックを追加するのが次のステップです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Ollama not found` | Ollamaサーバーが起動していない | タスクバーでOllamaが常駐しているか確認。`ollama serve`を手動実行。 |
| 出力が遅すぎる | VRAM不足でCPU推論になっている | モデルを `qwen2.5-coder:7b` など小さいものに変えて試す。 |
| 回答に解説が入る | システムプロンプトの指示が弱い | 「Output ONLY source code」と英語で念押しすると安定します。 |
| Pythonの型エラー | AIが架空のライブラリを推論した | `temperature` をさらに下げ、コンテキスト情報を詳しく渡す。 |

## 次のステップ

この記事の内容が動いたら、次は「ローカルRAG（検索拡張生成）」との組み合わせに挑戦してください。
Qwenは賢いですが、あなたのプロジェクト独自のライブラリや規約は知りません。
既存のコードベースをベクトルデータベース（ChromaやQdrant）に保存し、リファクタリング時に「関連するコード」を参考情報として添えるだけで、精度は劇的に向上します。

また、RTX 4090を2枚挿ししているような環境であれば、Ollamaの代わりに `vLLM` や `sglang` を使うことで、並列処理による超高速レスポンスを実現できます。
1ファイル数秒でリファクタリングが終わる快感は、一度味わうとクラウドのAIには戻れません。

実務においては、このスクリプトを `pre-commit` フックに組み込み、コミット前にAIが自動で型ヒントをチェックする仕組みを作るのが非常に強力です。
AIを単なる「チャット相手」ではなく「自動化パイプラインの一部」として組み込むことこそが、これからのエンジニアに求められるスキルだと確信しています。

## よくある質問

### Q1: Qwen2.5-Coder 32Bと7B、どちらを使うべきですか？

論理的思考が必要なリファクタリングなら32B一択です。7Bは記述速度は速いですが、複雑な型推論でミスが目立ちます。VRAMが8GBしかない場合のみ7Bを選んでください。

### Q2: 実行中にPCが非常に重くなるのですが、解消できますか？

ローカルLLMはGPUリソースを100%近く消費します。`ollama`の設定でGPUレイヤー数を調整するか、推論実行中のみブラウザのタブを閉じる、あるいは別のPCからAPI経由で叩くのが現実的です。

### Q3: 修正されたコードが動かなくなるリスクはありませんか？

あります。AIによる修正は100%完璧ではありません。必ずGitなどでバージョン管理を行い、修正後にpytestなどの自動テストを実行するパイプラインをセットで運用するのが鉄則です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 3090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 24GBで32Bモデルを余裕を持って動かせる最高コスパの選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Qwen2.5-Coder 使い方 | ローカルでGPT-4o級の開発環境をPythonで構築する](/posts/2026-03-21-qwen2-5-coder-python-local-guide/)
- [Qwen3-Coder-Next 使い方 | 最強のコード生成AIで開発を自動化する手順](/posts/2026-03-07-qwen3-coder-next-local-python-tutorial/)
- [ローカルLLM Qwen 2.5 Coder 使い方](/posts/2026-05-17-local-qwen-coder-html-canvas-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Qwen2.5-Coder 32Bと7B、どちらを使うべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "論理的思考が必要なリファクタリングなら32B一択です。7Bは記述速度は速いですが、複雑な型推論でミスが目立ちます。VRAMが8GBしかない場合のみ7Bを選んでください。"
      }
    },
    {
      "@type": "Question",
      "name": "実行中にPCが非常に重くなるのですが、解消できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ローカルLLMはGPUリソースを100%近く消費します。ollamaの設定でGPUレイヤー数を調整するか、推論実行中のみブラウザのタブを閉じる、あるいは別のPCからAPI経由で叩くのが現実的です。"
      }
    },
    {
      "@type": "Question",
      "name": "修正されたコードが動かなくなるリスクはありませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "あります。AIによる修正は100%完璧ではありません。必ずGitなどでバージョン管理を行い、修正後にpytestなどの自動テストを実行するパイプラインをセットで運用するのが鉄則です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">GeForce RTX 3090</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 24GBで32Bモデルを余裕を持って動かせる最高コスパの選択肢</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%203090%2024GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
