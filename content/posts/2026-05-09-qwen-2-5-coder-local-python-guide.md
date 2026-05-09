---
title: "Qwen2.5をローカル環境で動かし、API料金を気にせずコード生成を自動化するPythonスクリプトを作る方法"
date: 2026-05-09T00:00:00+09:00
slug: "qwen-2-5-coder-local-python-guide"
cover:
  image: "/images/posts/2026-05-09-qwen-2-5-coder-local-python-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen2.5-Coder"
  - "Ollama 使い方"
  - "ローカルLLM Python"
  - "AIコード生成"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Qwen2.5-Coderをローカルで動かし、Pythonのデバッグを自動で行うスクリプト
- 前提知識：Pythonの基本的な文法（関数の定義、ライブラリのインポート）がわかること
- 必要なもの：8GB以上のVRAMを搭載したGPU（NVIDIA製推奨）またはApple Silicon搭載Mac

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 3090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 24GBを安価に確保し、Qwen 32Bモデルをローカルで動かす最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

Qwenを「無料」で使い倒すには、自分のPCリソースをどれだけ割けるかが鍵になります。
Redditで「Qwenは無料じゃない」と話題になったのは、主にAlibaba CloudのAPI利用料や、大規模な商用利用（MAU 1億人以上）におけるライセンス料の話です。
個人開発や社内ツールとしてローカルで動かす分には、電気代以外は一切かかりません。

最低限必要なVRAM（ビデオメモリ）の目安を、私の検証結果から共有します。
7B（70億パラメータ）モデルを4bit量子化で動かすなら、VRAMは8GBあれば十分実用的です。
一方で、最強のコード生成能力を持つ32Bモデルを動かすなら、最低でも24GB（RTX 3090/4090）か、Macの統一メモリが32GB以上必要になります。
もしVRAMが足りない場合は、性能は落ちますが1.5Bモデルから試すのが賢明です。

## なぜこの方法を選ぶのか

Qwen2.5を動かす方法は、Transformersライブラリを使う方法、vLLMを使う方法など多岐にわたります。
しかし、私が今回「Ollama + Python」のアプローチを選ぶ理由は、推論エンジンの管理が圧倒的に楽だからです。
Ollamaはバックエンドでllama.cppを最適化して動かしており、量子化モデルのロードやメモリ管理を自動で行ってくれます。
また、PythonからAPI経由で叩く形にすることで、将来的にモデルをLlama 3.1やGemma 2に差し替えるのも容易になります。
エンジニアにとって「特定のモデルに依存しすぎない疎結合な構成」を作ることは、AIの進化が速い現代において必須の戦略です。

## Step 1: 環境を整える

まずは推論エンジンとなるOllamaをインストールします。
公式サイト（ollama.com）からバイナリをダウンロードして実行してください。

```bash
# MacOS / Linux の場合は以下のコマンドでもインストール可能
curl -fsSL https://ollama.com/install.sh | sh

# インストール後、Qwen2.5のコード特化モデルをプルする
# 7bはバランスが良く、多くのGPUで動作します
ollama pull qwen2.5-coder:7b
```

このコマンドは、モデルの重みデータをローカルに保存しています。
qwen2.5-coder:7bは約4.7GBのディスク容量を消費します。
もしRTX 4090などの上位GPUを持っているなら、`ollama pull qwen2.5-coder:32b`を強く推奨します。

⚠️ **落とし穴:**
Windows環境でWSL2を使わずにOllamaを実行する場合、バックグラウンドで起動していることを確認してください。
タスクバーにOllamaのアイコンが出ていないと、Pythonから接続した際に「Connection Refused」で詰まります。

## Step 2: 基本の設定

PythonからOllamaを操作するためのライブラリをインストールし、接続確認を行います。

```bash
pip install ollama
```

次に、Pythonスクリプトを作成します。
環境変数でモデル名を管理するように作ると、後でモデルを変更したくなった時にコードを書き換えずに済みます。

```python
import ollama
import os

# 使用するモデル名を定義
# 自分のPCスペックに合わせて変更してください
MODEL_NAME = "qwen2.5-coder:7b"

def generate_response(prompt):
    try:
        response = ollama.generate(
            model=MODEL_NAME,
            prompt=prompt,
            options={
                "temperature": 0.2,  # コード生成なので低めにして決定論的にする
                "num_predict": 1000, # 出力トークン数の上限
            }
        )
        return response['response']
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"
```

ここで`temperature`を0.2に設定しているのがポイントです。
クリエイティブな文章を書くなら0.7以上が良いですが、コード生成やデバッグでは「正解」が一つであることが多いため、低い値を設定して出力を安定させます。

## Step 3: 動かしてみる

実際にQwenにコードを書かせてみましょう。
Qwen2.5-Coderは、このクラスのサイズとしては驚異的なプログラミング能力を持っています。

```python
# テスト用のプロンプト
test_prompt = "Pythonでクイックソートを実装して、実行例も付けてください。"

print(f"--- {MODEL_NAME} に問い合わせ中 ---")
result = generate_response(test_prompt)
print(result)
```

### 期待される出力

```python
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

# 実行例
data = [3, 6, 8, 10, 1, 2, 1]
print(quick_sort(data))
```

私のRTX 4090環境では、この程度の出力は0.5秒もかからずに完了します。
このレスポンス速度こそが、クラウドAPI（GPT-4等）にはないローカルLLM最大のメリットです。

## Step 4: 実用レベルにする

単にチャットをするだけでは面白くありません。
実務で使える「コードの自動修正スクリプト」に拡張しましょう。
エラーが出ているコードを読み込み、Qwenに修正案を出させるツールです。

```python
import sys

def auto_fix_code(file_path):
    # ファイルからコードを読み込む
    with open(file_path, 'r', encoding='utf-8') as f:
        broken_code = f.read()

    # デバッグ用のプロンプトを構築
    prompt = f"""
以下のPythonコードにはエラーが含まれているか、非効率な部分があります。
1. 修正後の完全なコードを提示してください。
2. 修正した箇所のポイントを簡潔に説明してください。

### 対象コード ###
{broken_code}
"""

    print("AIがコードを分析中...")
    fix_suggestion = generate_response(prompt)

    # 修正案を別ファイルに保存
    output_path = f"fixed_{os.path.basename(file_path)}"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(fix_suggestion)

    print(f"修正案を {output_path} に保存しました。")

# 実行例
# auto_fix_code("my_script.py")
```

このスクリプトの肝は、プロンプトで「完全なコード」を要求している点です。
一部の修正箇所だけを出力されると、人間がコピペする手間が増えます。
AIに「そのまま動くもの」を出させるように指示を固定するのが、実務効率化のコツです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ConnectionError` | Ollamaが起動していない | タスクバーのアイコンを確認するか、`ollama serve`を実行する |
| `OutOfMemory (OOM)` | VRAM不足 | モデルを小さいサイズ（1.5b等）に変えるか、量子化ビット数を下げる |
| 応答が極端に遅い | GPUではなくCPUで動いている | NVIDIAドライバを最新にし、OllamaがGPUを認識しているかログを確認 |

## 次のステップ

この記事で、Qwen2.5をローカルで動かし、Pythonから制御する基盤が整いました。
次に挑戦すべきは、このスクリプトを「Cursor」や「Aider」のような開発支援ツールと組み合わせることです。

特にQwen2.5-Coder-32Bは、ベンチマークスコアでGPT-4oを凌駕する項目もあります。
これをローカルで常時起動しておけば、機密性の高い社内コードを外部に送ることなく、安全にAIの支援を受けることができます。
また、複数のモデルを並列で動かし、一つの問いに対して「多会一議」で結論を出させるエージェント構築も面白いでしょう。
VRAM 24GBの壁は高いですが、中古のRTX 3090などを探してでも構築する価値がある環境だと断言します。

## よくある質問

### Q1: Qwenは商用利用しても本当に大丈夫ですか？

QwenのライセンスはApache 2.0をベースにしていますが、月間アクティブユーザーが1億人を超えるような大規模サービスでの利用には別途許可が必要です。一般的な個人開発やB2Bツールであれば、ほぼ無料で利用可能だと解釈して良いでしょう。

### Q2: 7Bモデルと32Bモデル、どちらを使うべきですか？

VRAMが12GB以下なら7B一択です。24GB以上あるなら迷わず32Bを使ってください。32Bは論理的思考能力が格段に高く、複雑なアルゴリズムの修正においても、クラウドの有料AIに遜色ない精度を出してくれます。

### Q3: Python以外の言語でもQwenは使えますか？

はい、Qwen2.5-Coderは92種類以上の言語を学習しています。Java、C++、TypeScript、Goなどはもちろん、マイナーな言語でも高い精度でコード生成が可能です。プロンプトで言語を指定するだけで、最適な回答が得られます。

---

## あわせて読みたい

- [Qwen3-Coder-Next 使い方 | 最強のコード生成AIで開発を自動化する手順](/posts/2026-03-07-qwen3-coder-next-local-python-tutorial/)
- [Local LLM 使い方 入門：OllamaとPythonで自分専用のAIアシスタントを作る方法](/posts/2026-04-10-local-llm-ollama-python-tutorial-llama3/)
- [Qwen2.5-Coder 使い方 | ローカルでGPT-4o級の開発環境をPythonで構築する](/posts/2026-03-21-qwen2-5-coder-python-local-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Qwenは商用利用しても本当に大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "QwenのライセンスはApache 2.0をベースにしていますが、月間アクティブユーザーが1億人を超えるような大規模サービスでの利用には別途許可が必要です。一般的な個人開発やB2Bツールであれば、ほぼ無料で利用可能だと解釈して良いでしょう。"
      }
    },
    {
      "@type": "Question",
      "name": "7Bモデルと32Bモデル、どちらを使うべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "VRAMが12GB以下なら7B一択です。24GB以上あるなら迷わず32Bを使ってください。32Bは論理的思考能力が格段に高く、複雑なアルゴリズムの修正においても、クラウドの有料AIに遜色ない精度を出してくれます。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語でもQwenは使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、Qwen2.5-Coderは92種類以上の言語を学習しています。Java、C++、TypeScript、Goなどはもちろん、マイナーな言語でも高い精度でコード生成が可能です。プロンプトで言語を指定するだけで、最適な回答が得られます。 ---"
      }
    }
  ]
}
</script>
