---
title: "Local LLMベンチマーク測定のやり方！自機モデルと自分の知能を数値で比較する"
date: 2026-05-29T00:00:00+09:00
slug: "local-llm-benchmark-tutorial-lm-eval"
cover:
  image: "/images/posts/2026-05-29-local-llm-benchmark-tutorial-lm-eval.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "lm-evaluation-harness 使い方"
  - "MMLU 測定 方法"
  - "Local LLM ベンチマーク"
  - "Python AI 評価"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

自分のPCで動かしているローカルLLMの性能を、MMLU（大規模多目的言語理解）などの標準的な指標で測定し、さらに自分自身も同じテストを受けて「AIと自分の差」を可視化するベンチマーク・ダッシュボードを作成します。

- 性能測定ツール「lm-evaluation-harness」の構築
- ローカルLLM（Llama 3やGemma 2）のスコア測定実行
- 人間が同じ問題を解くためのStreamlitベースのテスター作成
- AI vs 人間の比較グラフ生成

前提知識として、基本的なPython操作と、コマンドラインでの環境構築に慣れている必要があります。

## 先に確認するスペック・料金

ローカルLLMのベンチマークには、相応のハードウェアスペックが求められます。
推論を回すだけなら低スペックでも動きますが、ベンチマークは何百、何千という質問を投げ続けるため、速度が出ないと数日かかってしまいます。

最低ラインは、VRAM 12GB以上のNVIDIA製GPU（RTX 3060 12GBなど）です。
8GBモデルだと、量子化されたLlama 3 8Bクラスを動かすのが限界で、測定中にメモリ不足（OOM）で落ちるリスクが高いです。
Macユーザーなら、メモリ24GB以上のApple Silicon（M2/M3）があれば、MLXフレームワーク経由で快適に測定できます。

料金については、オープンソースのモデル（Llama 3, Gemma 2, Phi-3など）を使う限り、電気代以外は無料です。
APIを叩いて比較したい場合は、OpenAIやAnthropicのAPI利用料が数百円程度かかります。

私はRTX 4090を2枚挿しして検証していますが、この環境なら1つのベンチマークセット（数千問）を15分程度で完結できます。
これからハードウェアを揃えるなら、VRAMの容量こそが正義であることを忘れないでください。

## なぜこの方法を選ぶのか

LLMの性能を語る際、多くの人が「なんとなく賢い」「回答が自然」といった主観に頼りすぎています。
しかし、仕事でLLMを組み込む場合、その「なんとなく」はリスクでしかありません。

今回、業界標準の「lm-evaluation-harness」を使用するのは、Hugging Faceのリーダーボードと同じ基準で自機モデルを評価できるからです。
また、Redditで話題になったように「自分自身（人間）」を同じ土俵に上げることで、そのタスクがAIに任せられるレベルなのか、人間が介入すべきなのかを数字で判断できるようになります。

他の簡易的な評価スクリプト自作する方法もありますが、評価ロジック（Few-shotの設定や正規化など）が標準化されていないと、他者のデータと比較できません。
「公式と同じルールで測る」ことが、実務においては最も価値があります。

## Step 1: 環境を整える

まずはベンチマーク専用の仮想環境を作成し、必要なライブラリをインストールします。
依存関係が非常にシビアなので、必ず新しい環境を作ってください。

```bash
# Python 3.10以上を推奨
python -m venv benchmark_env
source benchmark_env/bin/activate  # Windowsは .\benchmark_env\Scripts\activate

# lm-evaluation-harnessのインストール
git clone https://github.com/EleutherAI/lm-evaluation-harness
cd lm-evaluation-harness
pip install -e .

# ローカルモデルを動かすためのライブラリ（GPU環境用）
pip install transformers accelerate bitsandbytes streamlit pandas matplotlib
```

`lm-evaluation-harness`は、200以上の評価タスクを統合したフレームワークです。
これを直接インストールすることで、最新のLlama 3などのモデルも即座に評価可能になります。

⚠️ **落とし穴:** `bitsandbytes`のインストールでエラーが出る場合は、Windows環境でのパス設定や、CUDAツールキットのバージョンが古いことが原因です。
特にWindowsの場合、WSL2上で行うのが最もトラブルが少なく、速度も安定します。

## Step 2: ローカルモデルの評価実行

次に、実際にローカルにダウンロードしたモデルのスコアを測定します。
ここでは、軽量ながら高性能な「Llama-3-8B-Instruct」を対象にします。

```bash
# MMLU（知識問題）の1カテゴリ「abstract_algebra」だけを試走
python main.py \
    --model hf \
    --model_args pretrained=meta-llama/Meta-Llama-3-8B-Instruct,load_in_4bit=True \
    --tasks mmlu_abstract_algebra \
    --device cuda:0 \
    --batch_size 1
```

`load_in_4bit=True`を指定する理由は、VRAM消費を抑えるためです。
8Bモデルでも、量子化なし（FP16）では16GB以上のVRAMを消費しますが、4bit量子化なら5GB程度で収まります。
仕事で使う際、デプロイコストを抑えるために量子化は必須なので、ベンチマークもその状態で行うのが実践的です。

各引数の意味：
- `--model hf`: Hugging Faceのモデルを使用。
- `--tasks`: 測定したいベンチマーク名。最初は短時間で終わる1カテゴリのみを推奨。
- `--batch_size`: GPUメモリに合わせて調整。4090なら16程度まで上げられます。

## Step 3: 人間用ベンチマークUIの構築

Redditの投稿のように、自分自身も同じテストを受けてみましょう。
`mmlu`のデータセットを読み込み、クイズ形式で回答できるスクリプトを作成します。

```python
import streamlit as st
from datasets import load_dataset
import pandas as pd

# MMLUのデータセットを読み込む（例として初等数学）
@st.cache_data
def load_data():
    ds = load_dataset("cais/mmlu", "elementary_mathematics", split="test")
    return ds

st.title("Human vs AI Benchmark")

data = load_data()
if 'score' not in st.session_state:
    st.session_state.score = 0
    st.session_state.index = 0

current_q = data[st.session_state.index]

st.write(f"Question {st.session_state.index + 1}:")
st.info(current_q['question'])

options = current_q['choices']
user_choice = st.radio("選択肢を選んでください", options)

if st.button("回答する"):
    correct_idx = current_q['answer']
    if options.index(user_choice) == correct_idx:
        st.success("正解！")
        st.session_state.score += 1
    else:
        st.error(f"不正解。正解は: {options[correct_idx]}")

    st.session_state.index += 1
    st.rerun()

st.sidebar.metric("現在のスコア", f"{st.session_state.score}/{st.session_state.index}")
```

### 期待される出力

Streamlitを起動（`streamlit run app.py`）すると、ブラウザにクイズ画面が表示されます。
問題を解き終えると、自分の正解率が算出されます。
これを、Step 2で得られたAIのスコアと比較するわけです。

## Step 4: 実用レベルの比較分析

単にスコアを並べるだけでなく、カテゴリ別の得意・不得意を可視化します。
実務では「このモデルは論理推論は強いが、歴史知識は弱い」といった特性を把握することが、プロンプト設計の鍵になります。

```python
import matplotlib.pyplot as plt

def plot_comparison(ai_scores, human_scores, labels):
    x = range(len(labels))
    width = 0.35

    fig, ax = plt.subplots()
    ax.bar(x, ai_scores, width, label='Llama-3-8B')
    ax.bar([p + width for p in x], human_scores, width, label='Me')

    ax.set_ylabel('Accuracy')
    ax.set_title('AI vs Human: MMLU Comparison')
    ax.set_xticks([p + width / 2 for p in x])
    ax.set_xticklabels(labels)
    ax.legend()

    plt.savefig('comparison.png')
    plt.show()

# 例としてのデータ
plot_comparison([0.65, 0.42, 0.88], [0.70, 0.30, 0.95], ['Math', 'Coding', 'History'])
```

この比較を行うことで、AIが自分を超えている分野を特定できます。
私の場合、単純な暗記問題や数学の計算スピードではAIに勝てませんが、文脈の裏にある意図を汲み取る問題ではまだ優位に立てていることが分かりました。

仕事でAIを導入する際、この「差分」を知っておくことで、AIに下調べをさせ、人間が最終確認するというワークフローの正当性を数字で証明できるようになります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `OutOfMemoryError` | GPUメモリ不足 | `batch_size=1`にするか、モデルをより小さいもの（Phi-3等）に変える。 |
| `ModuleNotFoundError: lm_eval` | パスが通っていない | `pip install -e .` を実行したディレクトリを確認。 |
| `Dataset not found` | ネットワーク制限 | プロキシ環境下ではHugging Faceへの接続設定が必要。 |

## 次のステップ

ベンチマーク環境が整ったら、次は「プロンプトによるスコアの変化」を測定してみてください。
「あなたは専門家です」と一行加えるだけで、MMLUのスコアが数パーセント変動する様子を目の当たりにすると、プロンプトエンジニアリングの重要性が腑に落ちるはずです。

また、今回はMMLUのみを扱いましたが、実際の業務に近い「自社独自の評価セット」を作ってみるのも良いでしょう。
過去のQAデータなどをベースにベンチマークを自作し、モデルを更新するたびにスコアを自動測定する仕組み（LLMOps）への第一歩となります。

数字は嘘をつきません。
自分のPCで、自分の手で、AIの限界を測定し続けることが、この変化の激しい分野でエンジニアとして生き残る唯一の道だと私は確信しています。

## よくある質問

### Q1: 4-bit量子化するとベンチマークスコアはどれくらい落ちますか？

モデルにもよりますが、Llama 3 8Bの場合、FP16と4bit（GPTQやAWQ）の差は1〜2%程度に収まることが多いです。この僅かな劣化よりも、VRAMを節約して高速に推論できるメリットの方が、実務では遥かに大きいです。

### Q2: 自作のモデルやFine-tuningしたモデルも測定できますか？

はい、可能です。Hugging Faceの形式で保存されていれば、`--model_args pretrained=./path/to/your/model`とパスを指定するだけで、全く同じ基準で評価できます。学習の成果を定量化するのに最適です。

### Q3: ベンチマーク結果が公開されている数字より低いのですが。

公開スコアは、多くの場合「Few-shot（いくつか例題を見せる）」の設定で測定されています。引数に`--num_fewshot 5`などを追加して条件を揃えてみてください。設定一つで数字は大きく変わります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLMのベンチマーク実行に最もコスパが良い選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Local LLM 使い方 入門：OllamaとPythonで自分専用のAIアシスタントを作る方法](/posts/2026-04-10-local-llm-ollama-python-tutorial-llama3/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "4-bit量子化するとベンチマークスコアはどれくらい落ちますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデルにもよりますが、Llama 3 8Bの場合、FP16と4bit（GPTQやAWQ）の差は1〜2%程度に収まることが多いです。この僅かな劣化よりも、VRAMを節約して高速に推論できるメリットの方が、実務では遥かに大きいです。"
      }
    },
    {
      "@type": "Question",
      "name": "自作のモデルやFine-tuningしたモデルも測定できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、可能です。Hugging Faceの形式で保存されていれば、--modelargs pretrained=./path/to/your/modelとパスを指定するだけで、全く同じ基準で評価できます。学習の成果を定量化するのに最適です。"
      }
    },
    {
      "@type": "Question",
      "name": "ベンチマーク結果が公開されている数字より低いのですが。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "公開スコアは、多くの場合「Few-shot（いくつか例題を見せる）」の設定で測定されています。引数に--numfewshot 5などを追加して条件を揃えてみてください。設定一つで数字は大きく変わります。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでローカルLLMのベンチマーク実行に最もコスパが良い選択肢</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
