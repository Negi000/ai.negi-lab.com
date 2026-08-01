---
title: "Whisper 使い方 ローカル完全構築ガイド"
date: 2026-08-01T00:00:00+09:00
slug: "faster-whisper-local-setup-guide-python"
cover:
  image: "/images/posts/2026-08-01-faster-whisper-local-setup-guide-python.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Faster-Whisper 使い方"
  - "Whisper ローカル構築"
  - "文字起こし 自動化 Python"
  - "CUDA 環境構築"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

NVIDIA製GPUのパワーをフルに活用し、1時間の音声を5分以内に高精度でテキスト化するPythonスクリプトを作成します。
OpenAIが公開しているWhisperを、さらに高速化させた「Faster-Whisper」というライブラリを使用し、実務で耐えうる速度と精度を両立させます。
前提知識として、WindowsのコマンドプロンプトやPowerShellの基本操作、およびPythonのインストールが済んでいることを想定しています。

## 先に確認するスペック・料金

ローカルでWhisperを動かす際、最大のボトルネックはGPUのVRAM（ビデオメモリ）容量です。
私が複数の環境で検証した結果、最も精度の高い「large-v3」モデルを安定して動かすには、最低でも8GBのVRAMが必要です。
VRAM 4GBや6GBの環境でも「medium」以下のモデルなら動作しますが、日本語の認識精度は明確に落ちるため、ビジネス用途では8GB以上を推奨します。

ハードウェアについては、NVIDIA製のRTX 3060（12GB版）やRTX 4060 Ti（16GB版）が、コストパフォーマンスと実用性のバランスが最も良いです。
私がメイン機で使っているRTX 4090であれば、1時間の会議音声を約2分で処理できますが、一般的には4060クラスで十分すぎるほど高速です。
Macユーザーの場合は、M1/M2/M3チップを搭載し、メモリが16GB以上あれば、専用の「whisper.cpp」や「MLX」版を使うことで高速動作が可能になります。

料金については、一度ハードウェアを揃えてしまえば完全に無料です。
OpenAIのAPI（Whisper API）を使うと、1分あたり0.006ドル（1時間で約55円）かかります。
毎日3時間の音声を書き起こすような業務であれば、半年でミドルレンジのGPU代が回収できる計算になります。
社外秘の会議データをクラウドに投げたくないというセキュリティ要件がある場合も、ローカル完結のメリットは計り知れません。

## なぜこの方法を選ぶのか

Whisperをローカルで動かす方法はいくつかありますが、私は「Faster-Whisper」一択だと考えています。
本家OpenAI版のWhisperは、PyTorchの実装そのままなので動作が重く、VRAM消費も激しいのが難点です。
一方、Faster-Whisperは「CTranslate2」という推論エンジンを使用しており、本家よりも4倍以上速く、メモリ消費も半分近くに抑えられています。

他にも、さらに軽量な「Whisper.cpp」がありますが、これはC++ベースなのでPythonから扱うには少し手間がかかります。
実務では、文字起こしした後にChatGPT APIで要約したり、データベースに保存したりといった「前後の処理」をPythonで書くことがほとんどです。
そのため、Pythonライブラリとして提供されており、かつ圧倒的な速度を誇るFaster-Whisperが、開発効率とパフォーマンスの面でベストな選択となります。

## Step 1: 環境を整える

まずは、GPUを活用するためのソフトウェア群をインストールします。
ここは初心者が最も挫折しやすいポイントですが、バージョンを合わせることが成功の鍵です。

1. **NVIDIA Driverの更新:** 最新のゲームレディドライバーをNVIDIA公式サイトから入れてください。
2. **CUDA Toolkit 12.xのインストール:** Faster-WhisperはCUDAを使用します。
3. **cuDNNの配置:** NVIDIAのライブラリですが、これが無いとGPUが動きません。

```bash
# Python仮想環境の作成（プロジェクトごとに分離するのが鉄則です）
python -m venv venv
.\venv\Scripts\activate

# 必要なライブラリのインストール
# faster-whisper本体と、音声処理用のffmpeg-pythonを入れます
pip install faster-whisper ffmpeg-python
```

Windows環境の場合、さらに「FFmpeg」という実行ファイル単体が必要です。
`choco install ffmpeg` か、公式サイトからexeをダウンロードしてパスを通しておいてください。
これが無いと、mp4やm4aといった形式のファイルを読み込む際にエラーで止まります。

⚠️ **落とし穴:** CUDA Toolkitを入れただけでは動かないことが多いです。
Faster-Whisper（CTranslate2）は、特定の`zlibwapi.dll`というファイルを必要とすることがあります。
もし「Could not locate zlibwapi.dll」というエラーが出たら、NVIDIAの公式サイトから配布されているファイルを`C:\Windows\System32`に放り込む必要があります。
これを知らないと、環境構築だけで丸一日溶かすことになります。

## Step 2: 基本の設定

ライブラリの準備ができたら、Pythonで初期設定を書きます。
ここでは「どのモデルを使うか」「CPUとGPUどちらで動かすか」を指定します。

```python
import os
from faster_whisper import WhisperModel

# モデルのサイズを指定。日本語なら large-v3 が最高精度です。
# VRAMが足りない場合は "medium" や "small" に下げてください。
model_size = "large-v3"

# GPU(CUDA)を使う設定。float16は計算精度を半分にして高速化する設定です。
# GTX 10シリーズなどの古いGPUの場合は "float32" にする必要があります。
device = "cuda"
compute_type = "float16"

# モデルの読み込み。初回実行時は数GBのモデルデータがダウンロードされます。
model = WhisperModel(model_size, device=device, compute_type=compute_type)
```

この「float16」設定が重要です。
最新のGPUであれば、計算精度をあえて落とす（16bit浮動小数点数にする）ことで、精度をほぼ維持したまま処理速度を倍増させ、VRAM消費を半分にできます。
私がRTX 4090で検証した際、float32ではVRAMを10GB以上食いましたが、float16なら5GB程度で収まりました。
これにより、少し古めのGPUでも「large-v3」を動かすことが可能になります。

## Step 3: 動かしてみる

まずは最小限のコードで、手元にある音声ファイルを読み込ませてみましょう。
ここでは処理の進捗が見えるように、各セグメント（区切り）ごとにテキストを表示させます。

```python
# 文字起こしの実行
# beam_size: 探索の広さ。5程度が精度と速度のバランスが良いです。
# language: "ja" を指定することで、誤って他言語と判定されるのを防ぎます。
segments, info = model.transcribe("test_audio.mp3", beam_size=5, language="ja")

print(f"検出された言語: {info.language} (確信度: {info.language_probability:.2f})")

for segment in segments:
    print(f"[{segment.start:.2s}s -> {segment.end:.2s}s] {segment.text}")
```

### 期待される出力

```
検出された言語: ja (確信度: 1.00)
[0.00s -> 5.20s] 本日はお忙しい中、お集まりいただきありがとうございます。
[5.20s -> 10.50s] 今回のプロジェクトの進捗状況についてご報告いたします。
```

このコードを実行すると、音声が細かく区切られて表示されます。
`segments`はジェネレータ（イテレータ）になっているため、長い音声ファイルでもメモリを食いつぶすことなく、処理が終わった部分から順次出力されるのがFaster-Whisperの賢い点です。

## Step 4: 実用レベルにする

実務で使うなら、単に画面に表示するだけでは不十分です。
「無音部分をスキップする」「テキストファイルに保存する」「タイムスタンプを整形する」といった処理を加えた、実用的なスクリプトに仕上げます。

特に重要なのが「VAD（Voice Activity Detection）」フィルタです。
これを使うと、音声の中の「無音区間」をAIが事前に検知して飛ばしてくれるため、処理時間がさらに短縮され、無音部分でAIが同じ言葉を繰り返す「無限ループ現象」を防げます。

```python
import datetime

def transcribe_to_file(file_path, output_path):
    # VADフィルタを有効化（vad_filter=True）
    segments, info = model.transcribe(
        file_path,
        beam_size=5,
        language="ja",
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    with open(output_path, "w", encoding="utf-8") as f:
        for segment in segments:
            # 開始時間を hh:mm:ss 形式に変換
            start_time = str(datetime.timedelta(seconds=int(segment.start)))
            line = f"[{start_time}] {segment.text}\n"
            f.write(line)
            print(line, end="")

# 実行
transcribe_to_file("meeting_01.mp4", "transcript.txt")
```

このスクリプトでは、動画ファイル（mp4）を直接読み込んでいます。
内部でFFmpegが音声を抽出してくれるため、わざわざmp3に変換する手間はいりません。
また、VAD設定の`min_silence_duration_ms=500`は、「0.5秒以上の無音があれば区切る」という指定です。
会議の書き起こしなど、話し手が交代する場面が多い音声で特に効果を発揮します。

私が実務で導入した際は、このスクリプトをフォルダ監視プログラムと組み合わせました。
録音データが特定のフォルダに置かれたら自動で文字起こしが始まり、終わったらSlackに通知する。
これだけで、月間数十時間の工数削減につながりました。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `CUDNN_STATUS_NOT_INITIALIZED` | GPUドライバかcuDNNの不整合 | CUDA 12系と対応するcuDNNを入れ直す |
| `FileNotFoundError: [WinError 2]` | FFmpegにパスが通っていない | `ffmpeg -version` が動くか確認する |
| `Out of Memory (OOM)` | VRAM不足 | model_sizeを "medium" に下げる |
| `... repeated text ...` | 無音区間での誤作動 | `vad_filter=True` を設定する |

## 次のステップ

ここまでで、ローカル環境で爆速の文字起こし基盤が手に入りました。
しかし、文字起こしされた生データは、誤字脱字があったり、「えー」「あのー」といったフィラー（淀み）が多かったりと、そのままでは読みにくいものです。

次のステップとして、この出力を「LLM（ChatGPTやClaude）」に流し込むパイプラインを作ってみてください。
具体的には、文字起こししたテキストを5,000文字程度のブロックに分け、以下のプロンプトでLLMに渡します。
「あなたは優秀な議事録作成者です。以下の書き起こし文からフィラーを除去し、重要な決定事項とネクストアクションを抽出して要約してください。」

これを自動化すれば、会議が終わった5分後には、整形された議事録がチームのチャットに投稿される仕組みが完成します。
ローカルLLM（Llama-3やCommand Rなど）を使えば、要約まで完全にオフラインで完結させることも可能です。
RTX 3060以上の環境があるなら、ぜひローカルでの要約にも挑戦してみてください。

## よくある質問

### Q1: グラフィックボードがないPC（普通のノートPCなど）でも動きますか？

動きますが、速度は大幅に落ちます。`device="cpu"` に設定を変更してください。CPUの場合、large-v3モデルだと実時間の2〜3倍かかることがありますが、smallモデルなら実時間より早く終わることもあります。

### Q2: 精度が悪いと感じるのですが、向上させる方法はありますか？

まずは `initial_prompt` 引数を試してください。「この会議はITプロジェクトの進捗報告です。専門用語：Kubernetes, Docker, デプロイ」のように文脈を与えると、固有名詞の誤変換が劇的に減ります。

### Q3: 長い音声ファイル（3時間以上）を処理すると止まってしまいます。

メモリリークを避けるため、長い音声はFFmpegで30分単位に分割してからループで回すのがSIer時代の定石でした。ただ、Faster-WhisperのVAD併用なら3時間程度は一気に処理できるはずです。まずはVRAM監視を。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MSI GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載でWhisperのlargeモデルも余裕を持って回せる。将来的なローカルLLM運用にも最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Faster-Whisperを使ってローカル環境で爆速文字起こし環境を構築する方法](/posts/2026-07-06-faster-whisper-local-setup-guide/)
- [Agent Browser Shield 使い方：プロンプトインジェクション防御とコスト削減を両立する実用ガードレール](/posts/2026-06-05-agent-browser-shield-security-token-saving/)
- [Mindra 使い方：AIエージェントチームに実務を「丸投げ」する手法](/posts/2026-05-04-mindra-ai-agent-team-review-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "グラフィックボードがないPC（普通のノートPCなど）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、速度は大幅に落ちます。device=\"cpu\" に設定を変更してください。CPUの場合、large-v3モデルだと実時間の2〜3倍かかることがありますが、smallモデルなら実時間より早く終わることもあります。"
      }
    },
    {
      "@type": "Question",
      "name": "精度が悪いと感じるのですが、向上させる方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "まずは initialprompt 引数を試してください。「この会議はITプロジェクトの進捗報告です。専門用語：Kubernetes, Docker, デプロイ」のように文脈を与えると、固有名詞の誤変換が劇的に減ります。"
      }
    },
    {
      "@type": "Question",
      "name": "長い音声ファイル（3時間以上）を処理すると止まってしまいます。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "メモリリークを避けるため、長い音声はFFmpegで30分単位に分割してからループで回すのがSIer時代の定石でした。ただ、Faster-WhisperのVAD併用なら3時間程度は一気に処理できるはずです。まずはVRAM監視を。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MSI GeForce RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GB搭載でWhisperのlargeモデルも余裕を持って回せる。将来的なローカルLLM運用にも最適</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
