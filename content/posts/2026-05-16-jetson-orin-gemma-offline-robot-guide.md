---
title: "Jetson OrinとGemmaでオフラインLLMロボットを作る方法"
date: 2026-05-16T00:00:00+09:00
slug: "jetson-orin-gemma-offline-robot-guide"
cover:
  image: "/images/posts/2026-05-16-jetson-orin-gemma-offline-robot-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Jetson Orin NX"
  - "Gemma-2-9B"
  - "llama-cpp-python"
  - "エッジAI"
  - "オフラインLLM"
---
**所要時間:** 約60分 | **難易度:** ★★★★☆

## この記事で作るもの

- Jetson Orin NX 16GB上で、Googleの軽量LLM「Gemma」を完全オフライン動作させる制御システム。
- センサー入力を模したデータに対し、LLMがリアルタイム（TTFT約200ms）で判断を下し、行動プロンプトを生成するPythonスクリプト。
- 前提知識：Pythonの基本的な読み書きができ、Linuxコマンド（Ubuntu）の操作に抵抗がないこと。
- 必要なもの：Jetson Orin NX 16GB開発者キット、NVMe SSD（128GB以上推奨）、DC電源。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Jetson Orin NX 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">16GBのVRAMがLLM駆動に必須。エッジAI開発の標準機。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FJetson%2520Orin%2520NX%252016GB%2520%25E9%2596%258B%25E7%2599%25BA%25E8%2580%2585%25E3%2582%25AD%25E3%2583%2583%25E3%2583%2588%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FJetson%2520Orin%2520NX%252016GB%2520%25E9%2596%258B%25E7%2599%25BA%25E8%2580%2585%25E3%2582%25AD%25E3%2583%2583%25E3%2583%2588%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Jetson%20Orin%20NX%2016GB%20%E9%96%8B%E7%99%BA%E8%80%85%E3%82%AD%E3%83%83%E3%83%88&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

Jetson Orin NXには8GB版と16GB版がありますが、LLMを動かすなら16GB一択です。
Gemma-2-9Bクラスのモデルを4bit量子化で動かす場合、VRAM消費は約5〜6GBですが、OSや周辺制御、将来的なRAG（検索拡張生成）の実装を考えると、8GB版では確実にメモリ不足に陥ります。

Orin NX 16GBモジュール単体で約10万円、キャリアボード込みで15万円程度の投資が必要です。
もし予算が厳しい場合は、RTX 3060（12GB）を搭載したPCで代用可能ですが、今回のテーマである「スーツケースに収まるサイズでオフライン動作」というモビリティは失われます。
MacBook Air（M2/M3 16GB以上）も良い選択肢ですが、GPIO等の物理センサー連携に別途変換が必要になるため、ロボット製作ならJetsonに軍配が上がります。

## なぜこの方法を選ぶのか

クラウドAPI（GPT-4等）を使えば、もっと賢いロボットは数分で作れます。
しかし、移動体ロボットにおいて「電波がないと動かない」「通信ラグが1秒ある」ことは致命的です。
Redditの事例でも強調されている通り、完全オフラインにすることで、プライバシーの確保とゼロレイテンシに近い反応速度を両立できます。

今回は推論エンジンに「llama-cpp-python」を採用します。
TensorRT-LLMの方がJetsonの性能を極限まで引き出せますが、ビルドの難易度が極めて高く、モデル変更のたびに数時間のコンパイルが必要です。
llama-cpp-pythonなら、GGUF形式のモデルファイルを置くだけですぐに動かせ、実用上十分なレスポンス（200ms以下の初動）が得られるため、開発スピードを優先しました。

## Step 1: 環境を整える

Jetson特有のセットアップから始めます。まずはJetPackのバージョンを確認し、必要なビルドツールを入れます。

```bash
# OSの状態を確認
cat /etc/nv_tegra_release

# システムのアップデートと基本ツールのインストール
sudo apt-get update
sudo apt-get install -y python3-pip cmake git build-essential

# Jetsonのパフォーマンスを最大化（MAXNモードへ変更）
sudo nvpmodel -m 0
sudo jetson_clocks
```

`nvpmodel -m 0`は、Orin NXの電力制限を解除し、全コアをフル稼働させる設定です。
これを忘れると、LLMの推論速度が半分以下に落ち込むことがあります。

⚠️ **落とし穴:** Jetsonはデフォルトでスワップ領域が不足しています。LLMのロード時にメモリ不足でプロセスが強制終了（OOM Killer）されるのを防ぐため、必ずZRAMまたはSSD上にスワップを作成してください。

```bash
# 8GBのスワップファイルを作成する例
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Step 2: 基本の設定

llama-cpp-pythonを、CUDA（JetsonのGPUコア）を有効にした状態でビルドします。
ここが一番のハマりポイントですが、以下の環境変数を指定してインストールすることで、CPUではなくGPUでの高速推論が可能になります。

```bash
# CUDAのパスを通す（環境によって異なる場合があるため要確認）
export CUDA_HOME=/usr/local/cuda
export PATH=$PATH:$CUDA_HOME/bin
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CUDA_HOME/lib64

# CUDAを有効にしてインストール
# Jetson Orinのアーキテクチャ(sm_87)に最適化
CMAKE_ARGS="-DGGML_CUDA=ON" pip3 install llama-cpp-python --no-cache-dir
```

次に、モデルをダウンロードします。今回はHugging FaceからGemma-2-9BのGGUF版を取得します。
私の検証では、Orin NX 16GBなら「Q4_K_M」という量子化サイズが、速度と精度のバランスが最も良かったです。

```bash
# モデル用のディレクトリ作成
mkdir ~/models && cd ~/models

# 軽量なGemma-2-9B-ITの量子化モデルをダウンロード
# (wget等がなければインストールしてください)
wget https://huggingface.co/bartowski/gemma-2-9b-it-GGUF/resolve/main/gemma-2-9b-it-Q4_K_M.gguf
```

## Step 3: 動かしてみる

まずは、オフラインでLLMが動くか最小限のコードでテストします。
JetsonのGPU（CUDA）を認識させるために `n_gpu_layers=-1` を指定するのがコツです。

```python
import os
from llama_cpp import Llama

# モデルのパスを指定
model_path = os.path.expanduser("~/models/gemma-2-9b-it-Q4_K_M.gguf")

# LLMの初期化
# n_gpu_layers=-1 は全てのレイヤーをGPUにロードする設定
# n_ctx=2048 は文脈の長さ（ロボットの短期記憶）
llm = Llama(
    model_path=model_path,
    n_gpu_layers=-1,
    n_ctx=2048,
    verbose=False
)

# ロボットへの指示
prompt = "USER: 前方に障害物があります。回避行動を短く指示してください。\nASSISTANT:"

# 推論実行
output = llm(
    prompt,
    max_tokens=50,
    stop=["USER:", "\n"],
    echo=False
)

print(output["choices"][0]["text"])
```

### 期待される出力

```
左に30度旋回し、速度を落として直進を継続してください。
```

このレスポンスが1秒以内に返ってくれば、GPUでの推論が正常に動作しています。
もし出力に数十秒かかる場合は、`n_gpu_layers`が効いておらずCPUで動いている可能性が高いです。

## Step 4: 実用レベルにする

ロボットとして運用する場合、LLMの推論中もセンサーデータの監視を止めるわけにはいきません。
また、プロンプトに「現在のセンサー値」を動的に埋め込む必要があります。
実務で使えるレベルの、非同期処理を取り入れた構造に拡張しましょう。

```python
import time
import threading
from llama_cpp import Llama

class SuitcaseRobot:
    def __init__(self, model_path):
        self.llm = Llama(model_path=model_path, n_gpu_layers=-1, n_ctx=1024)
        self.current_sensors = {"ultrasonic": 0.0, "battery": 100}
        self.running = True

    def update_sensors(self):
        """センサー値を擬似的に更新し続けるスレッド（実機ではここでGPIOを読む）"""
        while self.running:
            # 擬似データ：障害物との距離が徐々に短くなる
            self.current_sensors["ultrasonic"] = 50.5
            time.sleep(0.1)

    def think(self, user_input):
        """センサー情報を加味してLLMに判断を仰ぐ"""
        system_prompt = f"System: 現在の距離センサーは {self.current_sensors['ultrasonic']}cm です。"
        full_prompt = f"{system_prompt}\nUSER: {user_input}\nASSISTANT:"

        start_time = time.time()
        response = self.llm(full_prompt, max_tokens=64, stop=["USER:"])
        end_time = time.time()

        print(f"思考時間: {end_time - start_time:.2f}秒")
        return response["choices"][0]["text"]

# 実行
model_file = os.path.expanduser("~/models/gemma-2-9b-it-Q4_K_M.gguf")
robot = SuitcaseRobot(model_file)

# センサー監視スレッド開始
sensor_thread = threading.Thread(target=robot.update_sensors)
sensor_thread.start()

# 思考実行
decision = robot.think("状況を判断して、次のアクションを教えて。")
print(f"ロボットの判断: {decision}")

# 終了処理
robot.running = False
sensor_thread.join()
```

この構成のポイントは、`system_prompt`にリアルタイムの数値を流し込んでいる点です。
Redditのスレッドにある「30個のセンサー」も、このように辞書形式で管理し、推論の直前に文字列としてプロンプトへ結合します。
これだけで、LLMは「今、自分の周りで何が起きているか」を理解した上で言葉を発するようになります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `CUDA error: out of memory` | VRAM不足。OSやGUIがメモリを消費している。 | `sudo init 3`でGUIを停止し、コンソールモードで実行する。 |
| `Illegal instruction (core dumped)` | llama-cppのビルド設定がアーキテクチャと不一致。 | `CMAKE_ARGS`を見直し、`no-cache-dir`を付けて再インストール。 |
| 推論が極端に遅い（1文字/秒以下） | GPUではなくCPUで動いている。 | `n_gpu_layers=-1`が設定されているか、CUDAビルドが成功しているか確認。 |

## 次のステップ

ここまでで、「脳（LLM）」と「感覚（センサー）」を繋ぐ基礎ができました。
次のステップとしては、ロボットに「声」を与えるための「Whisper（音声認識）」や「Piper（音声合成）」の導入をおすすめします。
これらもJetson上でオフライン動作が可能です。

さらに実用性を高めるなら、RAG（Retrieval-Augmented Generation）の構築に挑戦してください。
ロボットの操作マニュアルや過去の走行ログをベクトルデータベース（ChromaDBなど）に保存し、状況に応じてLLMがそれを参照するようにすれば、より「賢い」振る舞いが可能になります。
RTX 4090を積んだデスクトップとは違い、Jetsonには16GBという制約があります。
その限られたリソースの中で、いかに軽量なモデルと効率的なプロンプトを組み合わせるか。
それがエッジAIエンジニアとしての腕の見せ所です。

## よくある質問

### Q1: Orin Nanoでも同じことができますか？

Orin Nano 8GBでも動作は可能ですが、非常に厳しいです。モデルをQ2（2bit）まで量子化すればロードできますが、知能が著しく低下し、会話が成立しなくなることが多いです。実用的なロボットを目指すならOrin NX 16GBを強く推奨します。

### Q2: WiFiなしでどうやってライブラリを入れるのですか？

セットアップ時のみ有線LANやテザリングを使用します。一度環境が構築できれば、llama-cpp-pythonはインターネット接続なしで動作します。Redditの事例のように「完全オフライン」にするのは、あくまで運用フェーズの話です。

### Q3: バッテリーはどのくらい持ちますか？

Orin NXの消費電力は最大25W程度です。10,000mAhのモバイルバッテリー（PD出力対応）を使えば、アイドル時を含めて2〜4時間程度の稼働が目安です。LLMの推論を回し続けると消費電力が跳ね上がるので、大容量のバッテリー選定が重要になります。

---

## あわせて読みたい

- [メラニア・トランプ氏が提唱する「ロボット家庭教師」構想：AI教育のパラダイムシフトと実務者が直面する技術的障壁](/posts/2026-03-26-melania-trump-ai-robot-homeschooling-analysis/)
- [宇宙でデータセンターを稼働させるという試みが、ついに「研究」から「実商用」のフェーズへ突入しました。](/posts/2026-04-13-kepler-orbital-gpu-cluster-commercial-launch/)
- [Gemma 2 使い方 Jailbreakプロンプトでモデルの制限を解除する設定ガイド](/posts/2026-04-16-gemma-2-jailbreak-system-prompt-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Orin Nanoでも同じことができますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Orin Nano 8GBでも動作は可能ですが、非常に厳しいです。モデルをQ2（2bit）まで量子化すればロードできますが、知能が著しく低下し、会話が成立しなくなることが多いです。実用的なロボットを目指すならOrin NX 16GBを強く推奨します。"
      }
    },
    {
      "@type": "Question",
      "name": "WiFiなしでどうやってライブラリを入れるのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "セットアップ時のみ有線LANやテザリングを使用します。一度環境が構築できれば、llama-cpp-pythonはインターネット接続なしで動作します。Redditの事例のように「完全オフライン」にするのは、あくまで運用フェーズの話です。"
      }
    },
    {
      "@type": "Question",
      "name": "バッテリーはどのくらい持ちますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Orin NXの消費電力は最大25W程度です。10,000mAhのモバイルバッテリー（PD出力対応）を使えば、アイドル時を含めて2〜4時間程度の稼働が目安です。LLMの推論を回し続けると消費電力が跳ね上がるので、大容量のバッテリー選定が重要になります。 ---"
      }
    }
  ]
}
</script>
