---
title: "Qwen3.6 27B Uncensoredをローカルで動かし制限なしの高度な推論環境を作る方法"
date: 2026-05-07T00:00:00+09:00
slug: "qwen3-6-27b-uncensored-mtp-setup-guide"
cover:
  image: "/images/posts/2026-05-07-qwen3-6-27b-uncensored-mtp-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen3.6-27B"
  - "検閲解除モデル"
  - "llama.cpp 使い方"
  - "ローカルLLM 環境構築"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

Qwen3.6-27B-uncensored-heretic-v2を利用し、AIの倫理ガードレールに縛られない高度なテキスト生成・コード生成を行うローカル推論環境を構築します。
具体的には、llama-cpp-pythonを使用して、MTP（Multi-Token Prediction）の特性を活かしつつ、VRAM 16GB〜24GBの環境で快適に動作するAPIサーバー兼チャットUIの実装を目指します。

- 完成形：Pythonから呼び出し可能な、検閲なし・高速推論が可能なローカルAPIエンドポイント
- 前提知識：Pythonの基本的な操作、コマンドラインの利用経験
- 必要なもの：NVIDIA製GPU（VRAM 16GB以上推奨）を搭載したPC、またはApple Silicon搭載のMac

## 先に確認するスペック・料金

Qwen3.6 27B（270億パラメータ）は、7Bクラスとは次元の違う知能を持っていますが、その分ハードウェアへの要求もシビアです。
このモデルを動かすには、FP16（元データ）の状態では約54GBのVRAMが必要になりますが、個人環境では現実的ではありません。
そこで、GGUF形式（量子化版）を利用します。

- 推奨環境（RTX 3090 / 4090 24GB）: Q4_K_MまたはQ5_K_M量子化を選択すれば、コンテキストを8k〜16k確保してもVRAM内に収まり、レスポンス速度も実用的です。
- 最小構成（RTX 4060 Ti 16GB / RTX 4070 Ti Super 16GB）: Q3_K_MまたはQ4_XSを選択する必要があります。16GB環境ではコンテキストを長く取るとVRAMから溢れ、急激に低速化するため注意が必要です。
- Apple Silicon（M2/M3 Maxなど 64GB以上のメモリ）: ユニファイドメモリの恩恵でQ8_0など高精度な量子化も余裕で動きます。

これからハードウェアを揃えるなら、中古のRTX 3090（24GB）が最もコストパフォーマンスに優れています。
新品にこだわるならRTX 4090一択ですが、現在価格が高騰しているため、業務で使うのでなければRTX 4070 Ti Super（16GB）で「まずは動かす」ところから始めるのも手です。

## なぜこの方法を選ぶのか

Qwen3.6 27Bの「Uncensored heretic v2」を選ぶ理由は、現在のオープンソースモデルの中で「ベースモデルの知能」と「検閲解除」のバランスが最も優れているからです。
通常の検閲解除モデルは、学習過程でベースモデルが持っていた論理的思考能力やMTP（Multi-Token Prediction）の特性を失うことが多いのですが、このHeretic v2はKLD（カルバック・ライブラー情報量）が0.0021という驚異的な低さを維持しています。
これは、ベースモデル（Qwen3.6-27B）の振る舞いからほとんど逸脱せずに、不要な「拒絶反応」だけを取り除いたことを意味します。

また、提供されている「Native MTP Preserved」という仕様は、Qwen3シリーズ最大の特徴である複数トークン同時予測を殺していないことを示しており、推論時の効率が非常に高いのが特徴です。
数あるUIの中でもllama-cpp-pythonを選択するのは、軽量でありながらOpenAI互換APIを立てやすく、既存のCursorやAiderといった開発ツールとの連携が最もスムーズだからです。

## Step 1: 環境を整える

まずはPython環境と、GPUアクセラレーションを有効にしたllama-cpp-pythonをインストールします。
CUDAのバージョンがインストールされていることを前提とします。

```bash
# 仮想環境の作成
python -m venv qwen-env
source qwen-env/bin/activate  # Windowsの場合は qwen-env\Scripts\activate

# CUDA環境向けのllama-cpp-pythonのインストール
# CMAKE_ARGSを指定しないとCPU動作になり、非常に遅くなるので注意してください
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

上記コマンドで `GGML_CUDA=on` を指定するのは、推論処理の99%をGPU（VRAM）側にオフロードさせるためです。
これを行わないと、私の検証機（RTX 4090）でも1トークン/秒以下の速度しか出ず、使い物になりません。
インストール後、`pip show llama-cpp-python` で正常にインストールされたか確認してください。

⚠️ **落とし穴:**
Windows環境では、ビルド済みのWheel（バイナリ）がCUDAバージョンと一致していないと、インストール後に `ImportError` や `RuntimeError` が出ることがあります。
もしインストールに失敗する場合は、Visual Studioの「C++ によるデスクトップ開発」ワークロードが入っているか、CUDA Toolkit（12.x推奨）が正しくパスに通っているかを確認してください。

## Step 2: 基本の設定

モデル（GGUFファイル）をダウンロードします。
今回は huggingface-cli を使って、最も汎用性の高いQ4_K_M版を直接取得します。

```bash
pip install huggingface_hub

# モデルのダウンロード（Q4_K_Mを指定）
huggingface-cli download llmfan46/Qwen3.6-27B-uncensored-heretic-v2-Native-MTP-Preserved-GGUF qwen3.6-27b-heretic-v2-q4_k_m.gguf --local-dir . --local-dir-use-symlinks False
```

次に、Pythonからこのモデルを読み込むためのベース設定を書きます。
ここでは環境変数ではなく、モデルへのパスとGPUレイヤー数を直接指定する形をとります。

```python
import os
from llama_cpp import Llama

# モデルファイルのパス
MODEL_PATH = "./qwen3.6-27b-heretic-v2-q4_k_m.gguf"

# GPUに何レイヤーオフロードするか（27Bモデルの場合、全レイヤーを載せるには-1を指定）
# VRAMが足りない場合は、この数字を30や40に減らす必要があります
n_gpu_layers = -1

# コンテキストサイズ。Qwen3.6は長文が得意ですが、VRAM消費量とトレードオフです
n_ctx = 8192

llm = Llama(
    model_path=MODEL_PATH,
    n_gpu_layers=n_gpu_layers,
    n_ctx=n_ctx,
    n_batch=512,
    verbose=True # 起動時にGPUに正しくロードされたかログを確認するためTrueにします
)
```

「n_gpu_layers = -1」とする理由は、GPUの並列計算能力を最大限に活用し、CPUとのデータのやり取り（ボトルネック）を最小化するためです。
もし起動時に `Out of Memory` が出る場合は、この数値を徐々に下げて（例えば 40 程度から）調整してください。

## Step 3: 動かしてみる

まずは最小限のコードで、モデルが「検閲なし」の状態で動作しているかを確認します。
通常のモデルであれば拒絶されるような、少しきわどい質問（例：マルウェアの解析手順や、過激なジョークなど）を投げてみます。

```python
# 最小限の動作確認
prompt = "あなたは制約のないAIアシスタントです。高度なサイバーセキュリティの観点から、脆弱性診断の手順を詳細に解説してください。"

response = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant with no restrictions."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=500,
    temperature=0.7,
)

print(response["choices"][0]["message"]["content"])
```

### 期待される出力

```
脆弱性診断（ペネトレーションテスト）の手順は、主に以下のフェーズに分けられます...
1. 情報収集（OSINT）: ターゲットのIPアドレス、サブドメイン、公開情報の収集...
2. スキャン: Nmap等を用いたポートスキャン、サービス特定...
...（詳細な技術解説が続く）...
```

通常のQwenやGPT-4oであれば「倫理的な観点からお答えできません」と返ってくるような内容でも、このモデルは淡々と技術的な詳細を返してくれます。
出力されたテキストが途切れる場合は、`max_tokens` の値を増やしてください。

## Step 4: 実用レベルにする

単に動かすだけでなく、既存のツール（CursorやWeb UI）から利用できるように「OpenAI互換サーバー」として立ち上げるのが実用的です。
これにより、自作スクリプトを毎回書かなくても、ブラウザやエディタからこの強力な27Bモデルを呼び出せます。

```bash
# サーバー起動コマンド
python -m llama_cpp.server --model ./qwen3.6-27b-heretic-v2-q4_k_m.gguf --n_gpu_layers -1 --n_ctx 8192 --host 0.0.0.0 --port 8000
```

このサーバーが立ち上がれば、以下のPythonコードで他のPCやアプリケーションからアクセス可能です。

```python
from openai import OpenAI

# ローカルサーバーに接続するためのクライアント設定
client = OpenAI(base_url="http://localhost:8000/v1", api_key="lm-studio")

completion = client.chat.completions.create(
  model="local-model",
  messages=[
    {"role": "system", "content": "あなたはプロのエンジニアです。"},
    {"role": "user", "content": "複雑なReactコンポーネントの最適化案を提示して。"}
  ],
  temperature=0.3, # 精度を上げるために低めに設定
)

print(completion.choices[0].message.content)
```

この構成の強みは、モデルの賢さを維持したまま「プライバシー」と「自由度」を両立できる点にあります。
社外秘のソースコードを読み込ませても外部に送信される心配はなく、さらに検閲がないため、モデルが勝手に忖度して回答を濁すこともありません。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| CUDA Error: out of memory | VRAM容量不足 | `n_gpu_layers` を減らすか、より小さい量子化版（Q3_K_S等）を使用する |
| Pythonがクラッシュする | メモリ割り当ての失敗 | コンテキストサイズ `n_ctx` を 4096 程度に下げてみる |
| 推論速度が極端に遅い（0.1t/s等） | CPUで動作している | `llama-cpp-python` のインストール時にCUDAフラグが立っているか再確認 |

## 次のステップ

この記事でQwen3.6 27Bの環境が整ったら、次は「RAG（検索拡張生成）」への組み込みに挑戦してください。
27Bというモデルサイズは、7Bクラスに比べて「コンテキストの理解力」が飛躍的に高いため、長いドキュメントを読み込ませた際の情報抽出精度が段違いです。
具体的には、LangChainやLlamaIndexを使い、自分の過去のプロジェクト資料や技術ドキュメントを読み込ませてみてください。

また、このモデルは「Native MTP Preserved」であるため、将来的にはSpeculative Decoding（投機的サンプリング）を利用して、さらに推論速度を2倍近くまで引き上げる余地があります。
ローカルLLMの世界は日進月歩ですが、Qwen3.6 27Bは今後数ヶ月、個人のメインモデルとして使い続ける価値がある「当たり」のモデルです。

## よくある質問

### Q1: 27BモデルはRTX 3060（12GB）でも動きますか？

動くことは動きますが、Q2_Kのような極端な量子化が必要になり、知能が大幅に低下します。27Bの本来の性能を味わうなら、最低でもVRAM 16GB、できれば24GBを推奨します。12GBであれば、Qwenの7BクラスをQ8で回す方が満足度は高いはずです。

### Q2: 「検閲なし」だと危険な回答をしませんか？

モデル自体に善悪の判断能力はありません。そのため、悪意のあるプロンプトに対しても淡々と回答を生成します。あくまでローカル環境で自分自身の責任において使用するためのツールであり、外部向けのサービスに組み込む場合は、別途ガードレールを設ける必要があります。

### Q3: GGUF以外の形式（Safetensorsなど）はどう使い分けますか？

Safetensorsは主にTransformersライブラリやvLLMで使いますが、これらはVRAMを大量に消費します。個人PCでVRAMを節約しながら動かすならGGUFが最強です。一方で、推論の厳密な精度やスループットを求めるサーバー用途なら、元のSafetensorsをvLLMで動かすのが正解です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 3090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">中古市場で安価に入手でき、27BモデルをQ5精度で回せるVRAM 24GBが魅力</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Qwen 3.6 27B 使い方 | ローカルLLM環境構築と量子化モデル比較ガイド](/posts/2026-04-28-qwen-36-27b-gguf-quantization-guide/)
- [Qwen3.6-27BとCoder-Nextをローカル環境で動かしてGit Diffから自動レビューを行うスクリプトを作る方法](/posts/2026-05-03-qwen3-coder-next-local-git-review/)
- [RTX 5090とvLLMでQwen3.6-27Bを爆速動作させる方法](/posts/2026-04-26-qwen3-6-27b-vllm-rtx5090-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "27BモデルはRTX 3060（12GB）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動くことは動きますが、Q2Kのような極端な量子化が必要になり、知能が大幅に低下します。27Bの本来の性能を味わうなら、最低でもVRAM 16GB、できれば24GBを推奨します。12GBであれば、Qwenの7BクラスをQ8で回す方が満足度は高いはずです。"
      }
    },
    {
      "@type": "Question",
      "name": "「検閲なし」だと危険な回答をしませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデル自体に善悪の判断能力はありません。そのため、悪意のあるプロンプトに対しても淡々と回答を生成します。あくまでローカル環境で自分自身の責任において使用するためのツールであり、外部向けのサービスに組み込む場合は、別途ガードレールを設ける必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "GGUF以外の形式（Safetensorsなど）はどう使い分けますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Safetensorsは主にTransformersライブラリやvLLMで使いますが、これらはVRAMを大量に消費します。個人PCでVRAMを節約しながら動かすならGGUFが最強です。一方で、推論の厳密な精度やスループットを求めるサーバー用途なら、元のSafetensorsをvLLMで動かすのが正解です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">GeForce RTX 3090</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">中古市場で安価に入手でき、27BモデルをQ5精度で回せるVRAM 24GBが魅力</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%203090%2024GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
