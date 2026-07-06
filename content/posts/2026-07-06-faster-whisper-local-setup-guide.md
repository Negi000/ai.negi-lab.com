---
title: "Faster-Whisperを使ってローカル環境で爆速文字起こし環境を構築する方法"
date: 2026-07-06T00:00:00+09:00
slug: "faster-whisper-local-setup-guide"
cover:
  image: "/images/posts/2026-07-06-faster-whisper-local-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "faster-whisper 使い方"
  - "Python 文字起こし 自動化"
  - "ローカルWhisper GPU"
  - "議事録作成 AI"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 1時間の音声ファイルを数分でテキスト化する、実用レベルのPythonスクリプト
- クラウドAPI（Whisper API）に課金せず、データを外部に送らない完全オフラインの書き起こし環境
- 長時間の録音でもメモリ不足で落ちない、ジェネレータを用いた安定した処理フロー

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載で、Whisperの大規模モデルを回しながら他の作業も余裕でこなせる</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

### 前提知識
- Pythonの基本的な文法（pipでのインストールができること）
- コマンドライン（TerminalやPowerShell）の基本操作

### 必要なもの
- NVIDIA製GPU（VRAM 8GB以上推奨）を搭載したWindows/Linux PC、またはApple Silicon（M1/M2/M3）搭載のMac
- Python 3.9〜3.11の実行環境
- FFmpeg（音声のデコードに使用）

## 先に確認するスペック・料金

ローカルで文字起こしを回す際、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
OpenAIが公開している最強モデル「Whisper large-v3」を動かすには、最低でも5GB前後のVRAMを占有します。
OSや他のソフトが使う分を考慮すると、8GB搭載のRTX 3060やRTX 4060 Tiあたりが最低ラインの合格点です。

もしVRAMが4GB以下、あるいはCPUのみで動かそうとしているなら、処理速度は劇的に落ちます。
1時間の音声に対して、RTX 4090なら1分強で終わりますが、一般的なノートPCのCPUでは2時間以上かかることも珍しくありません。
その場合はおとなしくWhisper API（$0.006 / 分）を使ったほうが、時間対効果は高いです。

Macユーザーであれば、メモリ16GB以上のモデルを推奨します。
Apple SiliconはメインメモリとVRAMを共有（ユニファイドメモリ）するため、メモリが8GBしかないモデルだとモデルを読み込んだ瞬間にスワップが発生し、動作が著しく重くなります。

## なぜこの方法を選ぶのか

現在、ローカルでWhisperを動かす選択肢は主に3つあります。

1. **openai/whisper**: 本家。実装がシンプルだが、推論速度が遅くメモリ消費も激しい。
2. **whisper.cpp**: C++実装。非常に軽快でMacやCPU環境には強いが、Pythonからの拡張性がやや低い。
3. **faster-whisper**: 今回採用する方法。CTranslate2という高速化エンジンを使用しており、本家より4倍近く速い。

実務で「大量の会議音声を一気に処理したい」「自作の議事録作成システムに組み込みたい」と考えるなら、速度と精度のバランスが最も取れているfaster-whisper一択です。
同じ精度（large-v3モデル）を使いながら、本家よりも圧倒的に少ないリソースで動くため、開発効率が段違いに変わります。

## Step 1: 環境を整える

まずはライブラリのインストールから始めます。
Python環境が汚れるのを防ぐため、仮想環境（venv）の作成を推奨します。

```bash
# プロジェクト用ディレクトリの作成
mkdir whisper-local
cd whisper-local

# 仮想環境の作成と有効化
python -m venv venv
# Windowsの場合
.\venv\Scripts\activate
# Mac/Linuxの場合
source venv/bin/activate

# faster-whisperのインストール
pip install faster-whisper
```

ここで多くの人がハマるのが「FFmpeg」の未インストールです。
faster-whisperは内部で音声ファイルをデコードするためにFFmpegを利用します。
これがパスに通っていないと、コード実行時に「FileNotFoundError」で即死します。

- **Windows**: [Gyan.dev](https://www.gyan.dev/ffmpeg/builds/)からrelease-fullをダウンロードし、binフォルダを環境変数PATHに追加してください。
- **Mac**: `brew install ffmpeg` で一発です。

⚠️ **落とし穴:**
NVIDIA GPUを使う場合、CUDA ToolkitとcuDNNのバージョンがfaster-whisperの要求（現在はCTranslate2 v4系が主流）と一致している必要があります。
「GPUを積んでいるのにCPUで動いてしまう」ときは、大抵cuDNNのDLLファイルが足りないか、パスが通っていません。
特にzlibwapi.dllなどのライブラリ不足は、Windows環境での「あるある」です。

## Step 2: 基本の設定

まずは最小構成でモデルをロードするコードを書きます。
ここでは「なぜその設定にするのか」に注力して解説します。

```python
import os
from faster_whisper import WhisperModel

# モデルサイズの指定
# 'large-v3' は最高精度だが重い。速度優先なら 'distil-large-v3' がおすすめ
model_size = "large-v3"

# デバイスの設定
# GPUなら "cuda"、MacやCPUなら "cpu" を指定
# compute_type は計算精度。 "float16" にすると速度とメモリ効率が最大化する
device = "cuda" if os.name == "nt" else "cpu" # 簡易的な判定
model = WhisperModel(model_size, device=device, compute_type="float16")

print(f"Model {model_size} loaded on {device}")
```

`compute_type="float16"` を指定する理由は、最新のGPUなら半精度浮動小数点演算が得意だからです。
これを `int8` にすると精度はわずかに落ちますが、さらにメモリ消費を抑えられます。
SIer時代の経験から言うと、まずは `float16` で試し、VRAM不足エラー（OOM）が出た場合のみ `int8_float16` に落とすのが定石です。

## Step 3: 動かしてみる

実際に音声ファイルを読み込んで、テキストを出力させます。
faster-whisperの優れた点は、ジェネレータ（`segments`）を返すため、長い音声でも少しずつ処理結果を受け取れることです。

```python
# 文字起こしの実行
# beam_size: 探索の幅。5〜10が精度と速度のバランスが良い
# language: 日本語なら "ja"。指定しないと自動検知で数秒ロスする
segments, info = model.transcribe("test_audio.mp3", beam_size=5, language="ja")

print(f"Detected language '{info.language}' with probability {info.language_probability:.2f}")

for segment in segments:
    # [開始時間 -> 終了時間] テキスト の形式で表示
    print(f"[{segment.start:.2s}s -> {segment.end:.2s}s] {segment.text}")
```

### 期待される出力

```
Detected language 'ja' with probability 1.00
[0.0s -> 5.2s] こんにちは。本日の会議を始めます。
[5.2s -> 10.5s] 議題は、次世代AIモデルの導入についてです。
```

結果の読み方のポイントは、`segment.text` の前後にあるタイムスタンプです。
実務で使う場合、このタイムスタンプがないと「どの部分の発言か」を動画や録音と照らし合わせるのが不可能になります。
本家Whisperよりも、このセグメント分割の安定性が高いのがfaster-whisperの特徴です。

## Step 4: 実用レベルにする

単に画面に表示するだけでは仕事に使えません。
「フォルダ内のファイルを一括処理し、テキストファイルとして保存する」実用スクリプトに拡張します。
エラーハンドリングと、進捗確認のためのプログレスバー（tqdm）を追加した「現場仕様」の構成です。

```python
import os
import time
from faster_whisper import WhisperModel
from tqdm import tqdm

def transcribe_folder(input_dir, output_dir, model_size="large-v3"):
    # 出力フォルダがなければ作成
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # モデルの初期化（一度だけ行う）
    print("Loading model...")
    model = WhisperModel(model_size, device="cuda", compute_type="float16")

    # 指定フォルダ内の音声ファイルをスキャン
    extensions = [".mp3", ".wav", ".m4a", ".flac"]
    audio_files = [f for f in os.listdir(input_dir) if os.path.splitext(f)[1].lower() in extensions]

    for file_name in audio_files:
        input_path = os.path.join(input_dir, file_name)
        output_path = os.path.join(output_dir, f"{os.path.splitext(file_name)[0]}.txt")

        print(f"\nProcessing: {file_name}")
        start_time = time.time()

        # 書き起こし実行
        segments, info = model.transcribe(input_path, beam_size=5, language="ja")

        with open(output_path, "w", encoding="utf-8") as f:
            # tqdmで進捗を表示。duration（音声の長さ）を基準にする
            with tqdm(total=info.duration, unit="sec") as pbar:
                last_pos = 0
                for segment in segments:
                    f.write(f"[{segment.start:>8.2f}f -> {segment.end:>8.2f}f] {segment.text}\n")
                    pbar.update(segment.end - last_pos)
                    last_pos = segment.end

        elapsed = time.time() - start_time
        print(f"Done! Saved to {output_path} (Time: {elapsed:.1f}s)")

if __name__ == "__main__":
    # 実行例
    transcribe_folder(input_dir="./input", output_dir="./output")
```

このスクリプトのミソは、`tqdm`（プログレスバー）の更新に `segment.end` を使っている点です。
音声の総時間に対して、今どこまで処理が終わったかが可視化されるため、長時間放置していても安心感があります。
また、SIer的な視点で見ると、`encoding="utf-8"` を明示的に指定するのは必須です。これを忘れると、Windows環境で日本語が文字化けして悲惨なことになります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `cudnn_ops_infer64_8.dll not found` | cuDNNが正しくインストールされていない | NVIDIAからcuDNNを落とし、bin内のDLLをPythonのLibrary/binかシステムPATHに入れる |
| `Out of memory (OOM)` | VRAM容量を超過した | `model_size`を"medium"にするか、`compute_type="int8_float16"`を試す |
| `FileNotFoundError: ffmpeg` | FFmpegにパスが通っていない | FFmpegをインストールし、ターミナルで `ffmpeg -version` が動くことを確認する |
| 書き起こしがループする | Whisper特有のバグ（無音区間の誤検知） | `no_speech_threshold` や `condition_on_previous_text=False` のオプションを調整する |

## 次のステップ

ここまでで、高性能なローカル書き起こし環境は手に入りました。
しかし、出力されたテキストはまだ「話し言葉」のままです。
実務で「議事録」として成立させるには、ここからさらにAIによる加工が必要です。

次のステップとしては、今回出力したテキストを **Claude 3.5 Sonnet** や **GPT-4o** のAPIに流し込み、「フィラー（えー、あのー）の除去」「箇条書きでの要約」「ネクストアクションの抽出」を自動化するパイプラインを作ってみてください。

また、複数人の会話を識別したい場合は「Pyannote.audio」などの話者分離ライブラリと組み合わせるのが王道です。
ローカルLLMを並行して動かし、書き起こしから要約までを完全にオフラインで完結させる「究極のプライバシー重視型議事録システム」を構築するのも、RTX 4090を2枚挿しているような私のような層にはたまらない遊びになるはずです。

## よくある質問

### Q1: AMDのGPU（Radeon）でも動きますか？

基本的にはNVIDIAのCUDAに最適化されているため、そのままでは動きません。
ただし、Linux環境であればROCm経由で動かすことが可能です。
Windowsの場合は、素直に `device="cpu"` を使うか、WSL2で苦労して環境を作るより、NVIDIA製GPUへの買い替えを検討したほうが幸せになれます。

### Q2: 文字起こしの精度が Whisper API より低い気がします。

API版は内部的に `large-v2` や `v3` を使用していますが、さらに独自の音声前処理が入っている可能性があります。
faster-whisperで精度を上げるには、`beam_size` を 10 程度まで上げることと、録音時のノイズをあらかじめ `ffmpeg` 等でカットしておくのが有効です。

### Q3: 動画ファイル（mp4）を直接読み込めますか？

はい、FFmpegがインストールされていれば、faster-whisperは内部で自動的に音声ストリームを抽出して読み込んでくれます。
わざわざ音声ファイル（mp3等）に変換する手間は不要です。
これは大量の動画教材をテキスト化したいときに非常に重宝する仕様です。
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
        "text": "基本的にはNVIDIAのCUDAに最適化されているため、そのままでは動きません。 ただし、Linux環境であればROCm経由で動かすことが可能です。 Windowsの場合は、素直に device=\"cpu\" を使うか、WSL2で苦労して環境を作るより、NVIDIA製GPUへの買い替えを検討したほうが幸せになれます。"
      }
    },
    {
      "@type": "Question",
      "name": "文字起こしの精度が Whisper API より低い気がします。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "API版は内部的に large-v2 や v3 を使用していますが、さらに独自の音声前処理が入っている可能性があります。 faster-whisperで精度を上げるには、beamsize を 10 程度まで上げることと、録音時のノイズをあらかじめ ffmpeg 等でカットしておくのが有効です。"
      }
    },
    {
      "@type": "Question",
      "name": "動画ファイル（mp4）を直接読み込めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、FFmpegがインストールされていれば、faster-whisperは内部で自動的に音声ストリームを抽出して読み込んでくれます。 わざわざ音声ファイル（mp3等）に変換する手間は不要です。 これは大量の動画教材をテキスト化したいときに非常に重宝する仕様です。"
      }
    }
  ]
}
</script>
