---
title: "RTX 5090とvLLMでQwen3.6-27Bを爆速動作させる方法"
date: 2026-04-26T00:00:00+09:00
slug: "qwen3-6-27b-vllm-rtx5090-setup-guide"
cover:
  image: "/images/posts/2026-04-26-qwen3-6-27b-vllm-rtx5090-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "vLLM 使い方"
  - "Qwen3.6-27B"
  - "RTX 5090 ベンチマーク"
  - "ローカルLLM 爆速"
---
**所要時間:** 約40分 | **難易度:** ★★★★☆

## この記事で作るもの

25万トークンを超える超長文コンテキストを維持しながら、秒間100トークンという驚異的な速度で回答を生成するQwen3.6-27Bの推論サーバーを構築します。
具体的には、vLLM v0.19（以降）とINT4量子化モデルを組み合わせ、単一のハイエンドGPUで大規模なドキュメント解析が可能な環境をローカルに作成します。

前提知識
- Linux（Ubuntu等）の基本的なコマンド操作ができること
- DockerまたはPythonの仮想環境（venv/conda）の構築経験
- NVIDIAコンテナツールキットのセットアップができること

必要なもの
- NVIDIA GPU（VRAM 24GB以上推奨。記事のベンチマークはRTX 5090を使用）
- Python 3.10以上
- Hugging Faceのアカウントとアクセストークン（モデルダウンロード用）

## なぜこの方法を選ぶのか

ローカルLLMを動かす選択肢はllama.cppやExLlamaV2など多岐にわたりますが、現時点で「実務投入」を考えるならvLLM一択です。
理由は、スループットの圧倒的な高さとOpenAI互換APIの完成度、そして今回紹介する「マルチトークン予測（MTP）」への対応にあります。

従来の推論エンジンでは、27Bクラスのモデルを単一GPUで動かすと、長文コンテキスト入力時に生成速度が著しく低下（10〜20 tps程度）するのが一般的でした。
しかし、Qwen3.6-27BのINT4量子化版とvLLMの最新機能を組み合わせることで、VRAM消費を抑えつつ256kコンテキストという広大な作業領域を確保できます。
特に、今回のReddit投稿で話題となった「RTX 5090での100 tps超え」は、もはやクラウド経由のGPT-4oよりもレスポンスが速いという逆転現象を起こしています。

私はこれまでRTX 4090を2枚挿して運用してきましたが、このQwen3.6の効率の良さは別格です。
仕事で「大量のソースコードを一気に読み込ませてリファクタリング案を出させる」といった用途には、この構成が現在のベストプラクティスと言えます。

## Step 1: 環境を整える

まずは最新のvLLMをインストールするためのベース環境を作ります。
古いバージョンのvLLMではQwen3.6の特定の最適化（特にMTP周り）が効かないため、必ず最新版をターゲットにします。

```bash
# 仮想環境の作成（依存関係の衝突を防ぐため必須）
python3 -m venv qwen-env
source qwen-env/bin/activate

# 必須ライブラリのインストール
# vLLM 0.19.0以上を指定。AutoRound量子化モデルを扱うための依存関係も含む
pip install --upgrade pip
pip install vllm>=0.19.0
pip install flash-attn --no-build-isolation
```

vLLMはCUDAのバージョンに非常に敏感です。
`nvcc --version`でCUDA 12.1以上がインストールされていることを確認してください。
もしバージョンが古いと、FlashAttentionのビルドで失敗し、推論速度が半分以下に落ちるという最悪の結果を招きます。

⚠️ **落とし穴:**
pipインストール時に`flash-attn`のビルドが走る際、メモリ不足（RAM）でフリーズすることがあります。
ビルド済みのホイール（whl）を探して入れるか、ビルド中は他の重いアプリを閉じておきましょう。
また、VRAM 24GB（RTX 3090/4090/5090）未満のカードを使っている場合、256kコンテキストを指定すると起動時に「Out of Memory」で落ちます。
その場合はStep 2のパラメータ調整が必要です。

## Step 2: 基本の設定

モデルをロードするための起動スクリプト、またはサーバーコマンドを準備します。
ここでは、Redditのレシピに基づき「Lorbus/Qwen3.6-27B-int4-AutoRound」という最適化済みモデルを使用します。

```bash
# vLLMサーバーをOpenAI互換モードで起動する
# 以下の設定値はRTX 5090/4090クラスを想定
python3 -m vllm.entrypoints.openai.api_server \
    --model Lorbus/Qwen3.6-27B-int4-AutoRound \
    --max-model-len 262144 \
    --max-num-seqs 16 \
    --kv-cache-dtype auto \
    --gpu-memory-utilization 0.95 \
    --dtype float16
```

各パラメータの設定理由を解説します。
`--model` に指定しているAutoRound版は、量子化による精度劣化を最小限に抑えつつ、VRAM使用量を1/4近くに削減したモデルです。
`--max-model-len 262144` は256kコンテキストを有効にする設定です。
これにより、技術書数冊分のテキストを一度にメモリへ載せることが可能になります。
`--gpu-memory-utilization 0.95` は、VRAMの95%をvLLMのKVキャッシュ管理下に置くことを意味します。
デスクトップGUI（Windows等）を動かしている場合は、ここを0.85程度に下げないと画面がカクついたり、クラッシュの原因になります。

## Step 3: 動かしてみる

サーバーが立ち上がったら、別のターミナルからPythonスクリプトでリクエストを送ってみます。
OpenAIのSDKがそのまま使えるので、既存のアプリをローカルLLMに差し替えるのも簡単です。

```python
import os
from openai import OpenAI

# ローカルで起動したvLLMサーバーに接続
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="token-is-ignored" # vLLMではキーは何でもOK
)

# 256kコンテキストの威力を試すため、あえて長文の後に質問を投げる
response = client.chat.completions.create(
    model="Lorbus/Qwen3.6-27B-int4-AutoRound",
    messages=[
        {"role": "system", "content": "あなたは優秀なエンジニアです。"},
        {"role": "user", "content": "（ここに数万文字のログやコードを貼り付ける想定）\n\n上記のデータを踏まえて、システムの問題点を3点挙げてください。"}
    ],
    temperature=0.7,
    max_tokens=1024
)

print(f"回答速度: {response.usage.completion_tokens} tokens")
print(f"回答内容:\n{response.choices[0].message.content}")
```

### 期待される出力

```text
回答速度: 156 tokens
回答内容:
1. データベースのコネクションプールが枯渇しています。ログの234行目でタイムアウトが発生しています。
2. 特定のAPIエンドポイントでリトライループが発生しており、CPU負荷を押し上げています。
3. ...
```

この時、ターミナル側のvLLMログを見てください。
「Avg generation throughput: 100.5 tokens/s」といった数字が出ていれば成功です。
もし20〜30 tpsしか出ていない場合は、量子化モデルが正しくロードされていないか、FlashAttentionが有効になっていない可能性があります。

## Step 4: 実用レベルにする

単にチャットするだけでなく、実務で使うための「エラーハンドリング」と「ストリーミング出力」を実装しましょう。
特に長文コンテキストを扱う場合、一度にすべての回答を待つと体感速度が落ちるため、ストリーミングは必須です。

```python
import sys
from openai import OpenAI

def safe_query(prompt, context=""):
    client = OpenAI(base_url="http://localhost:8000/v1", api_key="local")

    full_prompt = f"コンテキスト:\n{context}\n\n質問: {prompt}"

    try:
        stream = client.chat.completions.create(
            model="Lorbus/Qwen3.6-27B-int4-AutoRound",
            messages=[{"role": "user", "content": full_prompt}],
            stream=True,
            timeout=300 # 長文処理のためタイムアウトを5分に設定
        )

        print("AI: ", end="")
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
        print("\n")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

# 実戦例: 巨大なログファイルの解析
with open("large_system.log", "r") as f:
    log_data = f.read()

safe_query("このログの中で、致命的なエラーが発生している箇所を特定して", context=log_data)
```

このコードでは、`stream=True` を使うことで最初の1文字が出るまでの待機時間を最小化しています。
また、`timeout` を長めに設定しているのがポイントです。
256kトークンをフルに読み込む際の「Prefill（入力処理）」フェーズでは、GPUが全力で計算するため、数十秒の沈黙が発生することがあります。
デフォルトの30秒設定だと、答えが出る前にクライアント側でタイムアウトしてしまいます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `OutOfMemoryError` | コンテキスト長がVRAM容量を超えている | `--max-model-len` を 131072 (128k) 等に下げる |
| `FlashAttention not found` | インストール失敗またはGPU非対応 | `pip install flash-attn` を再実行。Ampere世代(RTX 30)以降が必要 |
| `Model not found` | HFトークンの未設定またはパスミス | `huggingface-cli login` でログイン済みか確認 |
| `Illegal Instruction` | CPUの命令セット不足（古いCPU） | 最新のAVX対応CPUを使用するか、Docker版vLLMを使用 |

## 次のステップ

ここまで構築できれば、あなたのデスクには「世界最高クラスの速度で動く、プライバシーが完全に保護された25k超長文解析マシン」があることになります。
次に挑戦すべきは、この高速推論環境をバックエンドにした「ローカルRAG（検索拡張生成）」の構築です。

具体的には、DifyやAnythingLLMといったノーコードツールを使い、API接続先を `http://localhost:8000/v1` に向けてみてください。
社内の全ドキュメントをベクトル化して、Qwen3.6-27Bに食わせるのです。
このモデルの27Bというサイズは、日本語のニュアンス理解においても7Bや14Bモデルとは比較にならないほど洗練されています。

また、Redditのレシピにある「マルチトークン予測（MTP）」の挙動をさらにチューニングすることで、120 tpsといったさらなる高みを目指すことも可能です。
自宅サーバーにRTX 4090を2枚挿しているような私のような変態エンジニア（褒め言葉です）なら、2つのGPUで並列推論させ、複数のリクエストを同時に100 tpsで捌くシステムを組むのも面白いでしょう。
この速度を一度体験してしまうと、クラウドLLMの「待たされる時間」が苦痛に感じるはずです。

## よくある質問

### Q1: RTX 3060（12GB VRAM）でも動かせますか？

27BのINT4モデルはモデル本体だけで約15GB程度のVRAMを消費します。
3060ではモデルをロードした瞬間にメモリ不足になるため、動かすならモデルをさらに圧縮したAWQ版や、コンテキスト長を数kまで絞る必要があります。
現実的にはVRAM 24GB以上のカードがスタートラインです。

### Q2: 100 tpsも出ていないのですが、何が原因でしょうか？

推論速度はGPUの性能だけでなく、CPUからGPUへのデータ転送速度（PCIeの世代）にも依存します。
もしPCIe Gen3を使っている場合、ボトルネックになっている可能性があります。
また、vLLM起動時のログに `Computation is slowed down because FlashAttention is not installed` と出ていないか確認してください。

### Q3: 日本語の精度はどうですか？

Qwen3.6シリーズは中国アリババグループの開発ですが、日本語の対応能力は非常に高いです。
特に技術用語やプログラミングコードの理解は、同クラスのLlama 3などと比較しても遜色ありません。
INT4量子化による知能低下も、AutoRound手法のおかげで体感できるレベルではありません。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">27Bモデルを256kコンテキストで動かすための最低ラインであり、現状最も現実的な選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=NVIDIA%20GeForce%20RTX%204090&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FNVIDIA%2520GeForce%2520RTX%25204090%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FNVIDIA%2520GeForce%2520RTX%25204090%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [RTX 5070 TiでQwen3.6-35B-A3Bを秒間79トークンで動かすllama.cpp最適化ガイド](/posts/2026-04-19-rtx-5070ti-qwen-moe-optimization-guide/)
- [Qwen3.6-35B-A3B 使い方 入門：MoEモデルをローカル環境で爆速動作させる方法](/posts/2026-04-16-qwen3-6-35b-moe-python-guide/)
- [Qwen3.5-9B-Claude-4.6-Opus-Uncensored-Distilled-GGUF 使い方入門](/posts/2026-03-16-qwen3-5-9b-uncensored-gguf-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3060（12GB VRAM）でも動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "27BのINT4モデルはモデル本体だけで約15GB程度のVRAMを消費します。 3060ではモデルをロードした瞬間にメモリ不足になるため、動かすならモデルをさらに圧縮したAWQ版や、コンテキスト長を数kまで絞る必要があります。 現実的にはVRAM 24GB以上のカードがスタートラインです。"
      }
    },
    {
      "@type": "Question",
      "name": "100 tpsも出ていないのですが、何が原因でしょうか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "推論速度はGPUの性能だけでなく、CPUからGPUへのデータ転送速度（PCIeの世代）にも依存します。 もしPCIe Gen3を使っている場合、ボトルネックになっている可能性があります。 また、vLLM起動時のログに Computation is slowed down because FlashAttention is not installed と出ていないか確認してください。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の精度はどうですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Qwen3.6シリーズは中国アリババグループの開発ですが、日本語の対応能力は非常に高いです。 特に技術用語やプログラミングコードの理解は、同クラスのLlama 3などと比較しても遜色ありません。 INT4量子化による知能低下も、AutoRound手法のおかげで体感できるレベルではありません。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品</p> <strong style=\"font-size:16px\">NVIDIA GeForce RTX 4090</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">27Bモデルを256kコンテキストで動かすための最低ラインであり、現状最も現実的な選択肢</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://www.amazon.co.jp/s?k=NVIDIA%20GeForce%20RTX%204090&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonで見る</a> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FNVIDIA%2520GeForce%2520RTX%25204090%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FNVIDIA%2520GeForce%2520RTX%25204090%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">楽天で見る</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
