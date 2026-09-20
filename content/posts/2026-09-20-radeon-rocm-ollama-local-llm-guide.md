---
title: "RadeonでローカルLLMを動かすROCm環境構築とAPIサーバー作成"
date: 2026-09-20T00:00:00+09:00
slug: "radeon-rocm-ollama-local-llm-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Radeon RX 10800 XT"
  - "ROCm 使い方"
  - "Ollama 入門"
  - "AMD GPU AI環境構築"
---
**所要時間:** 約45分 | **難易度:** ★★★★☆

## この記事で作るもの

AMD製GPU（Radeon）の性能を最大限に引き出し、Llama 3やGemma 2などの最新AIモデルを爆速で動かすローカルAPIサーバーを構築します。
Pythonからこのサーバーを呼び出し、RadeonのVRAMをフル活用して推論処理を行うスクリプトまでを完成させます。

- **前提知識:** Linuxの基本的なコマンド操作ができること、Pythonの基礎（変数、関数、pip）を理解していること。
- **必要なもの:** AMD製GPU（RX 6000/7000シリーズ推奨）、Ubuntu 22.04 LTS（推奨環境）、インターネット接続。

## 先に確認するスペック・料金

RadeonでAIを動かすなら、最も重要なのは「VRAM（ビデオメモリ）の容量」です。
Redditで話題のRX 10800 XTがRTX 5090を凌駕するという噂の根拠も、4KゲーミングとAI処理に不可欠なメモリ帯域と計算性能の向上にあります。
現時点で構築を始めるなら、最低でもVRAM 12GB、できればRX 7900 XTXのような24GBモデルを選んでください。

NVIDIAのRTX 4090（24GB）が30万円を超える現状に対し、Radeonのフラグシップは15万円前後と半額に近い価格で購入できます。
ただし、Windows環境ではROCm（AMDの対CUDAライブラリ）のサポートが限定的であるため、基本的にはUbuntuなどのLinux環境が必須だと考えてください。
WSL2でも動作しますが、パフォーマンスを100%引き出すなら物理マシンへのUbuntuインストールを強く推奨します。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段として「LM Studio」や「GPT4All」といったデスクトップアプリがありますが、仕事で使うなら「Ollama」をROCm環境で動かすのがベストです。
理由は、Ollamaが内部でllama.cppを最適化して使用しており、APIサーバーとしての完成度が非常に高いためです。

また、Dockerを使用せずに直接ライブラリを入れようとすると、OSのバージョンや依存関係の競合で高確率で詰まります。
そのため、今回は「公式のROCm対応Dockerイメージ」を使用し、環境を汚さずに再現性の高い構築手順を採用します。
この方法は、将来的にRX 10800 XTなどの新世代GPUに乗り換えた際も、コンテナを差し替えるだけで済むというメリットがあります。

## Step 1: ROCmドライバとDockerの環境を整える

まずはUbuntu OS側でGPUを認識させるためのカーネルドライバをインストールします。
AMDの公式リポジトリからインストーラーを取得し、AI処理に必要なROCmコンポーネントをセットアップします。

```bash
# パッケージリストの更新
sudo apt update && sudo apt upgrade -y

# AMD GPUインストーラーのダウンロード（Ubuntu 22.04用）
wget https://repo.radeon.com/amdgpu-install/6.1.1/ubuntu/jammy/amdgpu-install_6.1.60101-1_all.deb
sudo apt install ./amdgpu-install_6.1.60101-1_all.deb

# AI/機械学習向けのスタックをインストール
# --usecase=rocm,hiplibsdk はAI開発に必須のセットです
sudo amdgpu-install --usecase=rocm,hiplibsdk --no-dkms -y

# ユーザーをrenderおよびvideoグループに追加して権限を付与
sudo usermod -aG render $USER
sudo usermod -aG video $USER
```

ここで一度再起動が必要です。再起動後、以下のコマンドでGPUが認識されているか確認してください。

```bash
rocm-smi
```

GPUの名前や温度が表示されれば成功です。表示されない場合は、セキュアブートが有効になっていてドライバの読み込みが拒否されている可能性があります。

⚠️ **落とし穴:**
ノートPC版のRadeonや、少し古いモデル（RX 500シリーズなど）を使っている場合、`rocm-smi` で認識されてもAI処理が走らないことがあります。
その場合は、実行時の環境変数に `HSA_OVERRIDE_GFX_VERSION=10.3.0`（RX 6000系の場合）などを設定して「互換モデルのふり」をさせる必要があります。

## Step 2: ROCm版OllamaをDockerで起動する

次に、AMD GPUをコンテナ内で直接叩けるようにDockerを設定します。
NVIDIAの場合は `nvidia-container-toolkit` が必要ですが、AMDの場合はDockerの `--device` オプションで直接 `/dev/kfd` と `/dev/dri` をマッピングするだけで動きます。

```bash
# OllamaのROCm対応イメージをプルして起動
# ポート11434でAPIを受け付け、モデルデータはカレントディレクトリの ollama フォルダに保存します
docker run -d \
  --device /dev/kfd \
  --device /dev/dri \
  -v $(pwd)/ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama-rocm \
  ollama/ollama:rocm
```

このコマンドのポイントは `--device /dev/kfd` です。
これは「Kernel Fusion Driver」の略で、AMD GPUの計算能力をユーザー空間のアプリケーション（今回の場合はLLM）に開放するための通り道になります。
これがないと、どんなに高性能なGPUを積んでいてもCPU推論になってしまい、レスポンスが数分単位で遅くなります。

## Step 3: モデルをロードして動かしてみる

コンテナが起動したら、実際にモデルをダウンロードして動かしてみましょう。
ここでは性能と軽さのバランスが良い「Llama 3 (8B)」を使用します。

```bash
# コンテナ内でモデルを実行
docker exec -it ollama-rocm ollama run llama3
```

コマンドを実行すると、モデルのダウンロードが始まります。
完了すると対話モードになります。ここで何か質問を入力してみてください。

### 期待される出力

```
>>> Why is Radeon good for AI?
Radeon GPUs, especially with the ROCm open software platform, offer a compelling alternative
to NVIDIA by providing high VRAM capacity at a lower price point...
```

レスポンスが1秒間に数十トークン（パラパラと文字が出てくる速さ）であれば、GPUが正常に機能しています。
もし1文字ずつゆっくり出力される場合は、GPUではなくCPUで動いている証拠です。その場合は `docker logs ollama-rocm` を確認し、ドライバの認識エラーが出ていないかチェックしてください。

## Step 4: Pythonから実用的なAPIとして利用する

ローカルで動いているOllamaはOpenAI互換のAPIエンドポイントを持っています。
これを利用して、自作のPythonアプリや自動化スクリプトからAIを呼び出せるようにしましょう。

まず、ライブラリをインストールします。

```bash
pip install openai
```

次に、以下のスクリプトを `ai_agent.py` として保存します。

```python
import os
from openai import OpenAI

# ローカルで動いているOllamaサーバーを指定
# APIキーは不要ですが、ライブラリの仕様上空文字を入れる必要があります
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

def ask_ai(prompt):
    try:
        response = client.chat.completions.create(
            model="llama3",
            messages=[
                {"role": "system", "content": "あなたは優秀なエンジニアです。簡潔に回答してください。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7, # 自由度を調整（0.1で堅実、1.0で創造的）
            max_tokens=500,  # 出力の長さ制限
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

if __name__ == "__main__":
    user_input = "Radeon RX 7900 XTXの推論速度を上げるためのコツを3つ教えて"
    print(f"質問: {user_input}\n")
    answer = ask_ai(user_input)
    print(f"回答:\n{answer}")
```

このコードでは、`base_url` をローカルのOllamaサーバー（ポート11434）に向けています。
これにより、高価なOpenAIのAPI料金を一切気にすることなく、数千回、数万回のプロンプトを「無料」かつ「爆速」で実行できる環境が手に入りました。

仕事で使う場合、機密情報を外部のサーバー（OpenAIなど）に送信できないケースが多いですが、この構成ならデータは自分のPC内から一歩も外に出ません。
これが、実務家がローカルLLM環境を構築する最大の理由です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `amdgpu` driver not found | Secure Bootが有効 | BIOS設定でSecure BootをDisableにする |
| 推論が極端に遅い | CPUで動作している | Docker実行時に `--device /dev/kfd` が抜けていないか確認 |
| `HSA_STATUS_ERROR_OUT_OF_RESOURCES` | VRAM不足 | モデルを小さいもの（Gemma-2bなど）に変更するか、量子化版（Q4_K_M等）を使う |

## 次のステップ

Radeonでの環境構築、お疲れ様でした。
ここからが本番です。Redditの噂にあるRX 10800 XTのような次世代GPUが登場した際、その真価を発揮させるには「RAG（検索拡張生成）」の構築が欠かせません。

次は、今回作ったAPIサーバーをバックエンドにして、自分のPC内にあるPDFやドキュメントを読み込ませる「Danswer」や「AnythingLLM」との連携に挑戦してみてください。
また、Pythonスクリプトを拡張し、GitHubの特定リポジトリを監視して、新しいコードがプッシュされるたびに自動でコードレビューを行う「AIレビューエージェント」を作るのも実用的です。

NVIDIA一強の時代は、ソフトウェア（CUDA）の壁によって守られてきました。
しかし、ROCmの進化とOllamaのようなツールの登場で、その壁は崩れつつあります。
今のうちにRadeon環境を使いこなせるようになっておけば、将来のハードウェア選択肢が広がり、よりコスト効率の高いAI開発が可能になるはずです。

## よくある質問

### Q1: Windowsでそのまま動かすことはできないのでしょうか？

WSL2を使えば動きますが、ドライバのパススルー設定が複雑で、ネイティブのLinuxに比べて10-15%ほどパフォーマンスが低下する傾向があります。また、ROCmのバージョンアップ時にWindows側のドライバと不整合を起こしやすいので、本気で使うならUbuntuとのデュアルブートをおすすめします。

### Q2: 複数のRadeon GPUを積んでいる場合はどう設定すればいいですか？

Dockerの起動時に `--device /dev/dri/renderD128 --device /dev/dri/renderD129` のように、デバイス番号を個別に指定します。Ollama側で自動的に負荷分散してくれますが、VRAMが合算されるわけではなく、各GPUにモデルの層が分割してロードされる仕組みです。

### Q3: 量子化（Quantization）モデルとは何ですか？

16ビットの重みデータを4ビットなどに圧縮したモデルのことです。例えば8Bモデルをそのまま読み込むと約15GBのVRAMを消費しますが、4ビット量子化（Q4_K_M）なら約5GBで済みます。精度を極端に落とさずに、RX 7600などのミドルクラスGPUでも動かせるようになります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Radeon RX 7900 XTX</strong>
<p style="color:#555;margin:8px 0;font-size:14px">24GBのVRAMを搭載し、ローカルLLMのフル推論に現時点で最もコスパが良い</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRadeon%2520RX%25207900%2520XTX%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRadeon%2520RX%25207900%2520XTX%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Radeon%20RX%207900%20XTX%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Qwen 3.7 使い方と最強ローカルLLM環境の作り方](/posts/2026-05-19-qwen-3-7-local-llm-setup-guide/)
- [AMD GPUでローカルLLMを動かすROCm環境構築の手順](/posts/2026-06-25-amd-gpu-rocm-local-llm-tutorial/)
- [OllamaとPydanticAIで自律型ローカルエージェントを構築する方法](/posts/2026-06-21-local-llm-agent-pydantic-ai-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Windowsでそのまま動かすことはできないのでしょうか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "WSL2を使えば動きますが、ドライバのパススルー設定が複雑で、ネイティブのLinuxに比べて10-15%ほどパフォーマンスが低下する傾向があります。また、ROCmのバージョンアップ時にWindows側のドライバと不整合を起こしやすいので、本気で使うならUbuntuとのデュアルブートをおすすめします。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のRadeon GPUを積んでいる場合はどう設定すればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Dockerの起動時に --device /dev/dri/renderD128 --device /dev/dri/renderD129 のように、デバイス番号を個別に指定します。Ollama側で自動的に負荷分散してくれますが、VRAMが合算されるわけではなく、各GPUにモデルの層が分割してロードされる仕組みです。"
      }
    },
    {
      "@type": "Question",
      "name": "量子化（Quantization）モデルとは何ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "16ビットの重みデータを4ビットなどに圧縮したモデルのことです。例えば8Bモデルをそのまま読み込むと約15GBのVRAMを消費しますが、4ビット量子化（Q4KM）なら約5GBで済みます。精度を極端に落とさずに、RX 7600などのミドルクラスGPUでも動かせるようになります。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Radeon RX 7900 XTX</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">24GBのVRAMを搭載し、ローカルLLMのフル推論に現時点で最もコスパが良い</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRadeon%2520RX%25207900%2520XTX%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRadeon%2520RX%25207900%2520XTX%252024GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Radeon%20RX%207900%20XTX%2024GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
