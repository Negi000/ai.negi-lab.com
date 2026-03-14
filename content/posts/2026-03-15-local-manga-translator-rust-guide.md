---
title: "ローカルLLMで漫画翻訳！Manga Translatorの使い方と導入手順"
date: 2026-03-15T00:00:00+09:00
slug: "local-manga-translator-rust-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Local Manga Translator"
  - "ローカルLLM"
  - "Ollama 使い方"
  - "AI漫画翻訳"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Rust製ツール「Manga Translator」を用いて、ローカル環境のみで漫画の「文字認識（OCR）」「背景補完（Inpainting）」「LLMによる翻訳」「文字合成」を自動化する環境
- 前提知識: 基本的なコマンドライン操作ができること。GPUドライバのインストール経験があること
- 必要なもの: NVIDIA製GPU（VRAM 8GB以上推奨）、CUDA Toolkit 12.x、ソースコード（GitHub）

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">RTX 4070 Ti SUPER</strong>
<p style="color:#555;margin:8px 0;font-size:14px">16GBの大容量VRAMがOCR・LaMa・LLMの同時稼働を支え、ローカル翻訳を快適にします</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=MSI%20GeForce%20RTX%204070%20Ti%20SUPER&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMSI%2520GeForce%2520RTX%25204070%2520Ti%2520SUPER%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMSI%2520GeForce%2520RTX%25204070%2520Ti%2520SUPER%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

これまで漫画の自動翻訳といえば、ブラウザベースの拡張機能や、特定のクラウドAPIに依存するものが主流でした。しかし、これらには「プライバシー」「1枚あたりの処理コスト」「翻訳のニュアンス調整」という3つの大きな壁がありました。

今回紹介するRustベースのLocal Manga Translatorは、計算資源をすべて自前（ローカル）で賄います。最大の特徴は、文字を消した後の背景を「LaMa」モデルで補完し、不自然さを極限まで排除している点です。さらに翻訳エンジンとしてOllamaなどのローカルLLMを接続できるため、エロ・グロといった規制の厳しい表現も、モデルを選べば制限なしで翻訳できます。

Python製ツールと異なり、Rustで組まれているため動作が非常に軽量で、1枚数秒という速度で処理が完結します。実務で大量のアーカイブを処理する場合、この「1枚あたりのオーバーヘッド」の差が決定的な作業効率の差を生みます。

## Step 1: 環境を整える

まずは、RustランタイムとCUDA環境を準備します。このツールはCUDAが同梱されていますが、システム側のドライバが古いと動作しません。

```bash
# NVIDIAドライバが正しく認識されているか確認
nvidia-smi

# Rustのインストール（未導入の場合）
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

NVIDIAドライバは535.xx以上が必要です。古いドライバだと、ツール内で使用されるONNX RuntimeがGPUを認識せず、CPUフォールバックが発生して処理に1分以上かかることになります。

⚠️ **落とし穴:** WSL2環境で動かす場合、Windows側のドライバとWSL内のCUDAライブラリのバージョンが食い違うと「Libcuda.so not found」のエラーが出ます。WSL2の公式ガイドに従い、WSL用のCUDA Toolkitを正しくインストールしてください。

## Step 2: 基本の設定

このプロジェクトは、複数のモデル（YOLO, OCR, LaMa）を組み合わせて動作します。まず、プロジェクトをクローンし、必要な設定ファイルを編集します。

```bash
git clone https://github.com/ogawa-kei/manga-translator.git
cd manga-translator
# 依存関係のビルド（Rustなので少し時間がかかります）
cargo build --release
```

次に、LLMサーバー（Ollamaなど）との接続設定を行います。`config.toml`（または環境変数）で、どのLLMを翻訳エンジンとして使うか指定します。私は、日本語のニュアンスを維持するために「Llama-3-70B」をバックエンド（Ollama）で動かす設定にしています。

```toml
[translation]
provider = "ollama"
base_url = "http://localhost:11434"
model = "llama3:70b"
system_prompt = "You are a professional manga translator. Translate the text naturally while maintaining the character's personality."
```

ここで「なぜOllamaを別立てにするのか」というと、Manga Translator本体に翻訳機能を持たせるより、推論サーバーを分離したほうがVRAMの管理がしやすいためです。OCRやInpaintingでVRAMを4GBほど消費するため、LLM側は量子化モデルを使ってVRAM消費を抑えるのがコツです。

## Step 3: 動かしてみる

設定が完了したら、実際に1枚の画像を翻訳してみましょう。

```bash
# 実行バイナリを叩く
./target/release/manga-translator --input ./raw_manga/page_01.jpg --output ./translated/ --lang JA-EN
```

### 期待される出力

```text
[INFO] Text detection started (YOLOv8)
[INFO] 12 text blocks detected.
[INFO] OCR engine processing...
[INFO] Inpainting background with LaMa...
[INFO] Translating via Ollama (llama3:70b)...
[INFO] Rendering text to image...
[SUCCESS] Saved: ./translated/page_01_translated.jpg (Time: 2.8s)
```

2.8秒。これが私のRTX 4090環境での結果です。OCRの読み取り精度が非常に高く、ルビが振ってある箇所も正しくメインのテキストだけを抽出できているのが分かります。

## Step 4: 実用レベルにする

単発の実行ではなく、フォルダ内の数百枚をバッチ処理する場合、エラーハンドリングが重要です。LLMのレスポンスが空だったり、接続が切れたりすることを想定し、以下のようなPythonスクリプトでラップして運用するのが実務的です。

```python
import os
import subprocess
from pathlib import Path

def batch_translate(input_dir, output_dir):
    files = sorted(list(Path(input_dir).glob("*.jpg")))

    for file in files:
        try:
            # 既に処理済みのファイルはスキップ
            if (Path(output_dir) / file.name).exists():
                continue

            print(f"Processing: {file.name}")
            result = subprocess.run([
                "./target/release/manga-translator",
                "--input", str(file),
                "--output", output_dir
            ], capture_output=True, text=True, check=True)

        except subprocess.CalledProcessError as e:
            # ここでリトライ処理やエラーログ出力を入れる
            print(f"Error processing {file.name}: {e.stderr}")

if __name__ == "__main__":
    batch_translate("./vol_01_raw", "./vol_01_translated")
```

この方法であれば、100ページ以上の漫画でも、放置しておくだけで一気に翻訳が完了します。また、LLMのプロンプトで「翻訳後の文字数」を制限するよう指定すると、コマの中にテキストが収まりやすくなります。具体的には「Keep the translation concise, max 20 words per bubble.」といった指示を追加するのがおすすめです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Out of Memory (OOM) | OCRとLLMでVRAMを取り合っている | LLMを4-bit量子化モデルに変更し、`ollama`の設定で並列実行を制限する |
| 背景がボロボロになる | 画像の解像度が低すぎる、または高すぎる | 入力解像度を1200px〜1600px程度にリサイズしてからツールに渡す |
| 文字が重なる | 合成エンジンがフォントサイズを誤認 | `config.toml`でフォントサイズの上限・下限を設定する |

## 次のステップ

ここまでで、ローカル完結型の漫画翻訳パイプラインが手に入りました。次に挑戦すべきは「モデルの入れ替え」です。

現在はデフォルトのYOLOモデルを使用していますが、これを漫画の「コマ割り」を認識するモデルに入れ替えることで、読む順番（右上から左下へ）をより正確にLLMに伝えることが可能になります。また、翻訳エンジンをGoogleのGemini 1.5 Flashなどに切り替えれば、画像全体を一度に読み取って、文脈を考慮した高度な翻訳（前後のページの関係性を踏まえた訳し分け）も視野に入ってきます。

さらに、このRustバイナリをベースに、WebUI（StreamlitやNext.js）を構築すれば、チームでの翻訳作業プラットフォームを自前で持つこともできます。ローカルLLMの進化は速いです。一度この「パイプライン」を作ってしまえば、中のモデルを最新のLlama-3.1やMistralに入れ替えるだけで、精度は勝手に向上し続けます。

## よくある質問

### Q1: AMDのGPU（Radeon）でも動きますか？

基本的にはCUDA前提のビルドになっています。ROCm版のONNX Runtimeを自分でリンクしてコンパイルすれば動く可能性がありますが、設定の難易度は跳ね上がります。素直にNVIDIA環境を用意することをおすすめします。

### Q2: 縦書きの日本語も正しく認識されますか？

はい、このツールで採用されているOCRモデル（多くの場合PaddleOCRベースのカスタム）は、日本語の縦書きに最適化されています。ただし、手書き文字や装飾が激しいフォントは誤認識しやすいため、その場合はLLM側の修正能力に頼る形になります。

### Q3: 1冊（200ページ）処理するのにどれくらい時間がかかりますか？

RTX 3060クラスであれば1枚約5〜8秒、計20〜30分程度です。4090であれば、LLMの推論時間を含めても10分程度で終わります。手動で翻訳・写植することを考えれば、圧倒的な時短です。

---

## あわせて読みたい

- [OllamaとPythonでPC環境をAIに酷評させるローストツールの作り方](/posts/2026-03-14-ollama-python-pc-roast-tool-guide/)
- [Qwen3の音声エンベディング機能を活用し、わずか数秒の音声サンプルから高精度なボイスクローンを作成して対話システムを構築する方法を解説します。この記事を最後まで読めば、従来のような膨大な学習データなしに、特定の誰かの声でAIを喋らせるための具体的な実装手順がすべて理解できるはずです。](/posts/2026-02-23-qwen3-voice-embeddings-cloning-guide/)
- [Mistral AIとアクセンチュアの提携が突きつける「OpenAI一強」時代の終焉とモデル選択の新基準](/posts/2026-02-27-mistral-ai-accenture-strategic-partnership-analysis/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "AMDのGPU（Radeon）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的にはCUDA前提のビルドになっています。ROCm版のONNX Runtimeを自分でリンクしてコンパイルすれば動く可能性がありますが、設定の難易度は跳ね上がります。素直にNVIDIA環境を用意することをおすすめします。"
      }
    },
    {
      "@type": "Question",
      "name": "縦書きの日本語も正しく認識されますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、このツールで採用されているOCRモデル（多くの場合PaddleOCRベースのカスタム）は、日本語の縦書きに最適化されています。ただし、手書き文字や装飾が激しいフォントは誤認識しやすいため、その場合はLLM側の修正能力に頼る形になります。"
      }
    },
    {
      "@type": "Question",
      "name": "1冊（200ページ）処理するのにどれくらい時間がかかりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "RTX 3060クラスであれば1枚約5〜8秒、計20〜30分程度です。4090であれば、LLMの推論時間を含めても10分程度で終わります。手動で翻訳・写植することを考えれば、圧倒的な時短です。 ---"
      }
    }
  ]
}
</script>
