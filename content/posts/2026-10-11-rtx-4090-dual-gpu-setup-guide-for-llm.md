---
title: "RTX 4090を2枚挿しでVRAM 48GB環境を構築する方法"
date: 2026-10-11T00:00:00+09:00
slug: "rtx-4090-dual-gpu-setup-guide-for-llm"
cover:
  image: "/images/posts/2026-10-11-rtx-4090-dual-gpu-setup-guide-for-llm.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "RTX 4090 2枚挿し"
  - "llama.cpp 使い方"
  - "Llama-3-70B ローカル"
  - "マルチGPU 環境構築"
---
**所要時間:** 約45分 | **難易度:** ★★★★☆

## この記事で作るもの

この記事を読むと、NVIDIA RTX 4090を2枚使ってVRAM計48GBの計算環境を構築し、Llama-3-70Bクラスの巨大なLLMをローカル環境で高速に推論できるようになります。

- 2枚のGPUを認識させるUbuntuの環境構築
- llama.cppを用いたマルチGPU推論の設定
- VRAMを最大限に使い切るためのレイヤー分割の最適化

## 先に確認するスペック・料金

RTX 5090の発売中止や、GB202チップがプロ向け（RTX PROシリーズ）に限定されるという不穏なニュースが流れています。
仮に5090が出たとしても、VRAM 32GBで30万円を超えるなら、現行のRTX 4090（24GB）を2枚並べて48GBを確保するほうが、LLMの実務においては圧倒的にコスパが良いです。

私が運用している「RTX 4090 × 2」構成を再現する場合、以下のスペックが必須になります。

- GPU: RTX 4090 24GB × 2（メーカーは揃えるのが無難ですが、別でも動きます）
- 電源: 1200W以上必須、できれば1600W（1枚あたり最大450W消費するため）
- マザーボード: PCIe 4.0 x16 スロットが物理的に2つ以上離れているもの（3スロット占有カードが多いため、スロット間隔が狭いと詰みます）
- PCケース: フルタワー必須
- OS: Ubuntu 22.04 LTS（Windows + WSL2でも動きますが、オーバーヘッドを嫌う私はネイティブLinux一択です）

予算は中古パーツを混ぜても50〜60万円コースですが、クラウドでH100を借り続けるコストを考えれば数ヶ月でペイします。

## なぜこの方法を選ぶのか

VRAMを増やすには「RTX 6000 Ada」のようなプロ向けカードを買うのが正攻法ですが、1枚で100万円を超えます。
一方、RTX 4090を2枚挿せば、半分のコストで同等の48GBを確保できます。

Apple Silicon（Mac Studioなど）で128GB以上のユニファイドメモリを積む選択肢もありますが、推論速度（トークン生成速度）は依然としてRTX 4090のマルチ構成に軍配が上がります。
特に学習やファインチューニングまで視野に入れるなら、CUDA環境が整っているNVIDIA構成以外に選択肢はありません。

## Step 1: 環境を整える

まずはUbuntu上で2枚のGPUを正しく認識させ、最新のドライバを入れます。

```bash
# 既存のドライバを削除してクリーンな状態にする
sudo apt-get purge nvidia*
sudo apt-get autoremove

# グラフィックドライバのレポジトリを追加
sudo add-apt-repository ppa:graphics-drivers/ppa
sudo apt update

# 推奨ドライバの確認
ubuntu-drivers devices

# ドライバのインストール（執筆時点で安定している550以降を推奨）
sudo apt install nvidia-driver-550
```

インストールが終わったら必ず再起動してください。
その後、以下のコマンドで2枚の4090が見えているか確認します。

```bash
nvidia-smi
```

「GPU 0」と「GPU 1」の両方にRTX 4090と表示され、VRAMがそれぞれ約24GB認識されていれば成功です。

⚠️ **落とし穴:** 電源容量が足りないと、この時点で片方のGPUが認識されない、あるいは負荷をかけた瞬間にPCが落ちます。
1200W電源でも、安価なものだと12V系統の出力不足で安定しません。私は結局1600Wの「80PLUS PLATINUM」認証品に変えてから安定しました。

## Step 2: 基本の設定

次に、LLMを動かすための「llama.cpp」をビルドします。
マルチGPU（CUDA）を有効にするためのフラグを立ててコンパイルするのがポイントです。

```bash
# 必要なビルドツールのインストール
sudo apt install build-essential cmake git

# llama.cppのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# CUDAを有効にしてビルド
mkdir build
cd build
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release -j $(nproc)
```

ここで `-DGGML_CUDA=ON` を忘れると、CPUだけで処理されてしまい、4090のパワーを1ミリも使えません。
ビルドが終わると、`bin` ディレクトリ内に `llama-cli` などの実行ファイルが出来上がります。

## Step 3: 動かしてみる

実際に、Llama-3-70B-InstructのQ4_K_M（4ビット量子化）モデルを動かしてみます。
このモデルは約40GB強のVRAMを消費するため、4090が1枚（24GB）では乗り切りませんが、2枚（48GB）なら余裕で収まります。

```bash
# モデルのダウンロード（HuggingFace等から入手した前提）
# 例: Meta-Llama-3-70B-Instruct-Q4_K_M.gguf

./bin/llama-cli \
  -m ./models/Meta-Llama-3-70B-Instruct-Q4_K_M.gguf \
  -p "あなたは優秀なAIアシスタントです。" \
  -n 512 \
  -ngl 99 \
  --sm row
```

### 期待される出力

```text
llama_print_timings:        load time =   1240.12 ms
llama_print_timings:      sample time =     15.40 ms /   512 runs   (    0.03 ms per token, 33246.75 tokens per second)
llama_print_timings: prompt eval time =    450.20 ms /    21 tokens (   21.44 ms per token,    46.65 tokens per second)
llama_print_timings:        eval time =  12540.30 ms /   511 runs   (   24.54 ms per token,    40.75 tokens per second)
```

24.54 ms per token、つまり毎秒40トークン以上出ていれば、4090 2枚のパワーがフルに発揮されています。

## Step 4: 実用レベルにする

実務で使うには、コマンドラインではなくAPIサーバーとして起動させ、外部（Cursorや自作アプリ）から叩けるようにします。
また、VRAMの割り当て比率を明示的に指定して、システムの安定性を高めます。

```bash
./bin/llama-server \
  -m ./models/Meta-Llama-3-70B-Instruct-Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -ngl 81 \
  --tensor-split 1,1
```

- `-ngl 81`: Llama-3-70Bの全レイヤー（81個）をGPUにオフロードします。
- `--tensor-split 1,1`: 2枚のGPUに均等（50%:50%）に負荷を分散させます。

私は片方のGPUをディスプレイ出力に使っているため、VRAM消費を抑えるために `--tensor-split 10,12` のように、メインじゃない方のGPU（GPU 1）に少し多めに割り振る設定をよく使います。
これで、ブラウザを開きながら裏でLLMを回してもVRAM不足（OOMエラー）で落ちることがなくなります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| out of memory | VRAM不足 | `-ngl` の値を下げるか、量子化率の高いモデル（Q3_K_L等）を使う |
| CUDA error: peer access is not supported | マザーボードの設定 | BIOSで「Above 4G Decoding」を有効にし、「Resizable BAR」をオンにする |
| GPUの温度が90度を超える | 排熱不足 | 2枚の間に隙間がない場合、ファン速度を固定するか、外排気（ブロワーファン）モデルを検討する |

## 次のステップ

48GBのVRAMがあれば、推論だけでなく「LoRA（Low-Rank Adaptation）」を用いたファインチューニングも現実的になります。
`unsloth` などのライブラリを使えば、Llama-3-8Bなら数分、70Bでも数時間で自分の業務に特化したモデルを学習可能です。

次は、PythonからこのAPIを叩いて、自分のローカルファイル（PDFやソースコード）を読み込ませる「RAG（検索拡張生成）」の構築に挑戦してみてください。
DifyやAnythinLLMを使えば、ノーコードでこの48GBサーバーをバックエンドに指定して自分専用のChatGPTが作れます。

RTX 5090を待って数ヶ月指をくわえているより、今ある4090を2枚手に入れて「実戦」を始めるほうが、AIエンジニアとしての成長スピードは圧倒的に速い。
私はそう確信しています。

## よくある質問

### Q1: RTX 4090の2枚挿しにNVLinkブリッジは必要ですか？

4000シリーズは物理的にNVLinkをサポートしていません。
データ通信はPCIeバス経由で行われます。そのため、マザーボードのPCIeスロットが「x8/x8」以上の帯域を維持できるものを選ぶのが速度低下を防ぐコツです。

### Q2: 電源ユニットが1個で足りない場合はどうすればいいですか？

1600Wの電源が手に入らない、あるいは高価すぎる場合は、「ADD2PSU」のようなアダプタを使って2つの電源ユニットを連動させる裏技もあります。
ただし配線が複雑になり、火災のリスクもゼロではないため、基本的には大容量電源1本を推奨します。

### Q3: WindowsのWSL2でも同じ速度が出ますか？

推論速度自体はほぼ変わりませんが、Windows OS自体がVRAMを数GB消費してしまうのが難点です。
Llama-3-70BをQ4量子化で動かす際、48GBギリギリの戦いになるため、OSのVRAM消費をゼロにできるUbuntuの方が、より巨大なコンテキスト（記憶保持量）を扱えます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">2枚挿しでVRAM 48GBを実現。5090待ちより今の実務を優先すべき</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [RTX 5070 TiでQwen3.6-35B-A3Bを秒間79トークンで動かすllama.cpp最適化ガイド](/posts/2026-04-19-rtx-5070ti-qwen-moe-optimization-guide/)
- [ローカルLLM用PCの選び方比較：RTX 4090かMac Studioか？後悔しないVRAM選定ガイド](/posts/2026-05-12-local-llm-pc-selection-guide-rtx-vs-mac/)
- [llama.cppとGGUF量子化でローカルLLMを爆速動かす方法](/posts/2026-09-27-llamacpp-gguf-quantization-tutorial-python/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 4090の2枚挿しにNVLinkブリッジは必要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "4000シリーズは物理的にNVLinkをサポートしていません。 データ通信はPCIeバス経由で行われます。そのため、マザーボードのPCIeスロットが「x8/x8」以上の帯域を維持できるものを選ぶのが速度低下を防ぐコツです。"
      }
    },
    {
      "@type": "Question",
      "name": "電源ユニットが1個で足りない場合はどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "1600Wの電源が手に入らない、あるいは高価すぎる場合は、「ADD2PSU」のようなアダプタを使って2つの電源ユニットを連動させる裏技もあります。 ただし配線が複雑になり、火災のリスクもゼロではないため、基本的には大容量電源1本を推奨します。"
      }
    },
    {
      "@type": "Question",
      "name": "WindowsのWSL2でも同じ速度が出ますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "推論速度自体はほぼ変わりませんが、Windows OS自体がVRAMを数GB消費してしまうのが難点です。 Llama-3-70BをQ4量子化で動かす際、48GBギリギリの戦いになるため、OSのVRAM消費をゼロにできるUbuntuの方が、より巨大なコンテキスト（記憶保持量）を扱えます。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">NVIDIA GeForce RTX 4090</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">2枚挿しでVRAM 48GBを実現。5090待ちより今の実務を優先すべき</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
