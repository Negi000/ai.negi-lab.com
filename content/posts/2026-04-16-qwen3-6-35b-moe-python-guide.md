---
title: "Qwen3.6-35B-A3B 使い方 入門：MoEモデルをローカル環境で爆速動作させる方法"
date: 2026-04-16T00:00:00+09:00
slug: "qwen3-6-35b-moe-python-guide"
cover:
  image: "/images/posts/2026-04-16-qwen3-6-35b-moe-python-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen3.6-35B-A3B"
  - "Sparse MoE"
  - "llama-cpp-python"
  - "ローカルLLM 構築"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

この記事では、最新のSparse MoE（混合エキスパート）モデル「Qwen3.6-35B-A3B」をローカルPCに導入し、ソースコードの修正案を自動生成する「AIコーディングレビュー・スクリプト」を作成します。
PythonからLlama-cpp-pythonを経由してモデルを制御し、35Bクラスの知能を3Bクラスの速度で引き出す実装を目指します。

### 前提知識
- Pythonの基本的な文法（関数の定義、import文）がわかること
- ターミナル（PowerShellやbash）でのコマンド操作に抵抗がないこと

### 必要なもの
- OS: Windows, macOS, Linux
- GPU: NVIDIA製GPU（VRAM 16GB以上推奨） または Mac (M2/M3等 メモリ24GB以上)
- Python 3.10以上
- インターネット環境（モデルのダウンロードに約20GB程度必要）

## なぜこの方法を選ぶのか

Qwen3.6-35B-A3Bは「トータル35Bパラメータ、推論時のアクティブパラメータは3B」という非常に特殊なMoE（Mixture of Experts）構成を採用しています。
一般的な35Bの密なモデルを動かそうとすると、私のRTX 4090でもレスポンスが重く感じることがありますが、このA3Bモデルは計算量が1/10以下になるため、驚くほど高速に動作します。

今回は実行エンジンとして「llama-cpp-python」を選択しました。
他にもOllamaやTransformersを使う選択肢がありますが、llama-cpp-pythonは量子化（GGUF形式）の扱いが最も枯れており、限られたVRAM環境でモデルを動かす際に「どの層をGPUに載せるか」を細かく制御できるため、実務上の柔軟性が最も高いからです。
また、Apache 2.0ライセンスという商用利用しやすいライセンス形態を活かすためにも、特定のプラットフォームに依存しないライブラリ構成で組むのがベストだと判断しました。

## Step 1: 環境を整える

まずは、GPUアクセラレーションを有効にした状態でllama-cpp-pythonをインストールします。
ここを適当に済ませると、推論がCPUで実行されてしまい「1文字出すのに5秒かかる」といった悲惨な状況になります。

```bash
# Windows (NVIDIA GPU) の場合。CUDA Toolkitがインストールされていることが前提です。
$env:CMAKE_ARGS = "-DGGML_CUDA=on"
pip install llama-cpp-python huggingface_hub

# Mac (Apple Silicon) の場合。Metalを有効にします。
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python huggingface_hub
```

`huggingface_hub` は、Hugging Faceからモデルファイルをコマンドラインで安全に取得するために使用します。
ブラウザから手動で落とすよりも、チェックサム確認が自動で行われるため、ファイルの破損リスクを最小限に抑えられます。

⚠️ **落とし穴:**
Windowsユーザーは、ビルドツール（Visual StudioのC++ビルド環境）が入っていないとインストールに失敗します。「Failed building wheel for llama-cpp-python」と出たら、ほぼ確実にコンパイラ不足です。Microsoftの公式サイトから「Build Tools for Visual Studio」を入れましょう。

## Step 2: モデルのダウンロードと量子化の選択

次に、Qwen3.6-35B-A3BのGGUF形式ファイルをダウンロードします。
35Bのモデルをそのまま（FP16）で読み込むと約70GBのVRAMが必要になり、一般的な環境では動きません。
そこで、精度を保ちつつサイズを削った「Q4_K_M」という量子化バージョンを使用します。

```python
from huggingface_hub import hf_hub_download

# モデルのリポジトリ名とファイル名を指定
# Bartowski氏などが公開している量子化版を利用するのが一般的です
model_name = "bartowski/Qwen3.6-35B-A3B-GGUF"
model_file = "Qwen3.6-35B-A3B-Q4_K_M.gguf"

# ダウンロード実行（ローカルにキャッシュされます）
model_path = hf_hub_download(repo_id=model_name, filename=model_file)
print(f"Model downloaded to: {model_path}")
```

「Q4_K_M」を選択した理由は、モデルサイズが約20GBに収まりつつ、知能指数の低下が体感レベルでほとんど無視できるからです。
RTX 3060（12GB）などを使っている場合は「Q3_K_M」以下を検討してください。
私の経験上、MoEモデルは量子化による劣化が密なモデルよりわずかに大きい傾向にありますが、Q4なら実務で使える品質を維持できます。

## Step 3: 動かしてみる

モデルが手に入ったら、まずは最小限のコードで推論を確認します。
ここで重要なのは `n_gpu_layers` の設定です。

```python
from llama_cpp import Llama

# モデルの初期化
llm = Llama(
    model_path=model_path,
    n_gpu_layers=-1, # -1はすべての層をGPUにオフロードする設定
    n_ctx=4096,      # コンテキスト長。コード解析なら長めが理想
    verbose=False
)

# 実行
output = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "あなたは優秀なエンジニアです。"},
        {"role": "user", "content": "Pythonで素数を判定する効率的な関数を書いて。"}
    ]
)

print(output["choices"][0]["message"]["content"])
```

### 期待される出力
```text
def is_prime(n):
    if n <= 1: return False
    if n <= 3: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True
```

`n_gpu_layers=-1` を指定するのは、中途半端にCPUへ処理を戻すとPCIeの帯域がボトルネックになり、推論速度が極端に落ちるからです。
VRAMが足りない場合のみ、この数値を徐々に下げて調整してください。

## Step 4: 実用レベルにする：AIコーディングレビュー機能の実装

単にチャットをするだけでは面白くありません。
実務で使える「指定したファイルのバグを探し、修正案を出す」スクリプトへ拡張します。
ここでは、エラーハンドリングと、プロンプトエンジニアリングの工夫を加えます。

```python
import sys
import os
from llama_cpp import Llama

class CodeReviewer:
    def __init__(self, model_path):
        # MoEモデルは初期化に時間がかかるため、インスタンス化を1回に留める
        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,
            n_ctx=8192, # 長いソースコードを読み込むため拡張
            seed=42      # 出力の再現性を高める
        )

    def review_file(self, file_path):
        if not os.path.exists(file_path):
            return "Error: ファイルが見つかりません。"

        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        prompt = f"""以下のソースコードをレビューし、修正案を提示してください。
特に「セキュリティ上の脆弱性」「パフォーマンスの改善点」「可読性」に注目してください。

### 対象コード
```python
{code}
```

### 修正案
"""

        # ストリーミング出力を有効にして、生成過程をリアルタイムに表示する
        stream = self.llm.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )

        print(f"--- {file_path} のレビュー結果 ---")
        for chunk in stream:
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                print(delta["content"], end="", flush=True)
        print("\n------------------------------")

# 実行
if __name__ == "__main__":
    # ここにレビューしたいファイル名を指定
    reviewer = CodeReviewer(model_path)
    reviewer.review_file("sample_script.py")
```

この実装のポイントは `stream=True` です。
35Bクラスのモデルは、最初の1文字が出るまでに1〜2秒かかることがありますが、ストリーミングを有効にすることで「考えている最中」から結果を読み取ることができ、ユーザー体験が大幅に向上します。
また、`n_ctx` を8192に増やしています。MoEモデルは長いコンテキストを扱う際の計算コスト増大が比較的緩やかなため、積極的な活用が推奨されます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| CUDA out of memory | VRAM容量不足 | 量子化ビット数を下げる（Q4→Q3やQ2）か、n_gpu_layersを減らす |
| Python crashed (Segmentation fault) | メモリ不足またはライブラリの不整合 | llama-cpp-pythonを最新版にアップデートし、モデルを再度DLする |
| 出力が非常に遅い（0.1 tok/s） | CPUで動作している | CMAKE_ARGSを確認して、ビルド済みキャッシュを消して再インストールする |

## 次のステップ

今回、Qwen3.6-35B-A3Bを動かしてみて驚いたのは、関数の依存関係を追う「Agentic coding」の適性の高さです。
私が以前、 dense（密）なモデルで試した際は、30Bを超えるとレスポンスの遅延が思考を遮り、開発のテンポが崩れてしまいました。
しかし、このMoEモデルなら、ローカル環境でもストレスなくサブ秒のレスポンスが得られます。

次のステップとしては、このスクリプトをGitの `pre-commit hook` に組み込んでみることをお勧めします。
コミットする直前にAIがコードを自動チェックし、指摘があればコミットを中断させる仕組みです。
また、Qwenシリーズはツールの呼び出し（Function Calling）も得意なので、ローカルファイルを実際に書き換える「自律型コーディングエージェント」への改造にも挑戦してみてください。
Apache 2.0ライセンスなので、社内サーバーに立ててチーム全員で使う「プライベートAIエンジニア」を構築するのも現実的です。

## よくある質問

### Q1: 35Bモデルなのに、なぜ私の8GB VRAMのビデオカードで動かないのですか？

MoEは「計算量」は3B分で済みますが、「モデルの重み（パラメータ）」自体は35B分すべてメモリに載せる必要があります。Q4量子化でも約20GBは消費するため、8GBカードの場合はモデルの半分以上をシステムメモリ（RAM）に逃がす必要があり、推論速度が著しく低下します。

### Q2: Qwen3.6はQwen2.5と比べて何が一番変わったのですか？

最大の変更点は、このMoEアーキテクチャの洗練度です。同じ計算リソース（3Bアクティブ）を使いながら、以前のモデルよりも知識量と推論能力が劇的に向上しています。特にプログラミングに関しては、複雑なロジックの整理能力が一段階上のレベルに達したと感じます。

### Q3: 日本語の精度はどうですか？仕事で使えますか？

Qwenシリーズは多言語対応が非常に強力で、日本語も極めて自然です。SIer時代の複雑な仕様書を読み込ませても、文脈を外さない要約が可能です。ただし、専門用語が多すぎる場合は「システムプロンプト」で用語集を渡すなどの工夫をすると、より精度が安定します。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">35Bモデルを量子化なし、あるいは高速に動かすなら24GB VRAMは必須の選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Gemma 2 使い方 Jailbreakプロンプトでモデルの制限を解除する設定ガイド](/posts/2026-04-16-gemma-2-jailbreak-system-prompt-guide/)
- [Qwen2.5-Coder 使い方 | ローカルでGPT-4o級の開発環境をPythonで構築する](/posts/2026-03-21-qwen2-5-coder-python-local-guide/)
- [MiniMax M2.7 使い方 入門：オープンソース版をローカル環境で動かす手順](/posts/2026-03-23-minimax-m27-open-weights-local-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "35Bモデルなのに、なぜ私の8GB VRAMのビデオカードで動かないのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MoEは「計算量」は3B分で済みますが、「モデルの重み（パラメータ）」自体は35B分すべてメモリに載せる必要があります。Q4量子化でも約20GBは消費するため、8GBカードの場合はモデルの半分以上をシステムメモリ（RAM）に逃がす必要があり、推論速度が著しく低下します。"
      }
    },
    {
      "@type": "Question",
      "name": "Qwen3.6はQwen2.5と比べて何が一番変わったのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "最大の変更点は、このMoEアーキテクチャの洗練度です。同じ計算リソース（3Bアクティブ）を使いながら、以前のモデルよりも知識量と推論能力が劇的に向上しています。特にプログラミングに関しては、複雑なロジックの整理能力が一段階上のレベルに達したと感じます。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の精度はどうですか？仕事で使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Qwenシリーズは多言語対応が非常に強力で、日本語も極めて自然です。SIer時代の複雑な仕様書を読み込ませても、文脈を外さない要約が可能です。ただし、専門用語が多すぎる場合は「システムプロンプト」で用語集を渡すなどの工夫をすると、より精度が安定します。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品</p> <strong style=\"font-size:16px\">NVIDIA GeForce RTX 4090</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">35Bモデルを量子化なし、あるいは高速に動かすなら24GB VRAMは必須の選択肢</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonで見る</a> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">楽天で見る</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
