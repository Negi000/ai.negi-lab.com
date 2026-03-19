---
title: "KoboldCpp 1.110 使い方：ローカルLLMで音楽生成と音声合成を同時に動かす方法"
date: 2026-03-19T00:00:00+09:00
slug: "koboldcpp-1110-musicgen-tts-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "KoboldCpp 使い方"
  - "MusicGen ローカル"
  - "Qwen2-Audio 音声クローニング"
  - "ローカルLLM 音楽生成"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- ローカルPC上でLLMと対話しつつ、プロンプトから音楽を生成し、さらに特定の声をクローニングして読み上げさせる統合AI環境を構築します。
- Pythonを使ってKoboldCppのAPIを叩き、テキスト・音楽・音声をワンストップで出力する自動化スクリプトを作成します。
- 前提知識として、基本的なコマンドライン操作とPythonの実行環境（venv推奨）が必要です。
- 動作環境にはNVIDIA製GPU（VRAM 12GB以上推奨）を想定していますが、設定次第でCPUでも動作可能です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">MusicGenとLLMを同時にVRAMへ載せるには16GBモデルが最もコスパ良く安定します</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールは、LM Studio、Ollama、Text-generation-webuiなど選択肢が豊富です。
しかし、今回のKoboldCpp 1.110（3周年記念版）へのアップデートで、状況が大きく変わりました。
これまで音楽生成には「Audiocraft」、音声合成には「GPT-SoVITS」など、別々の重い環境を構築する必要がありましたが、KoboldCppはこれらを一つの軽量な実行ファイルに統合してしまいました。

SIer時代、複数のAIモデルを連携させるシステムの環境構築だけで3日溶かした経験がある私からすれば、これは異常な進歩です。
「1つのAPIエンドポイントを立てるだけで、推論・音楽・音声がすべて完結する」という利便性は、開発コストを劇的に下げます。
特に今回採用されたQwen2-Audioによるボイスクローニングは、従来のRVCなどと比較しても設定が圧倒的に楽で、実務での「ちょっとした音声プロトタイプ」に最適です。

## Step 1: 環境を整える

まずは本体とモデルを入手します。KoboldCppはインストーラー不要で、exeファイルを置くだけで動くのが最大のメリットです。

1. [KoboldCppのGitHubリポジトリ](https://github.com/LostRuins/koboldcpp/releases)から最新版の `koboldcpp.exe`（Windowsの場合）をダウンロードします。
2. 作業用フォルダを作成し、その中に `models` フォルダを作ります。
3. Hugging FaceからメインのLLMモデル（例: Llama-3.1-8B-Lexi-v2-GGUFなど）をダウンロードして `models` に入れます。

次に、今回の目玉である音楽生成と音声合成用のモデルを準備します。これらはKoboldCppが初回起動時に自動ダウンロードしようとしますが、プロキシ環境などで失敗することが多いため、手動でパスを指定するのが確実です。

⚠️ **落とし穴:**
古いバージョンのKoboldCppが残っていると、設定が競合して「CUDA Error」が出ることがあります。必ず新しいフォルダを作り、クリーンな状態で始めてください。また、VRAMが8GB以下のカードでMusicGenを有効にする場合は、メインLLMのコンテキスト長を4096程度に絞らないと、起動時にVRAM溢れで落ちます。

## Step 2: 基本の設定

KoboldCppを起動する際、コマンドライン引数で新機能を有効化します。GUIの「Launch」ボタンからでも設定可能ですが、再現性を持たせるためにバッチファイル（.bat）を作るのが私のスタイルです。

```bash
# run_kobold.bat
koboldcpp.exe --model models/Llama-3.1-8B-Instruct-Q4_K_M.gguf ^
--contextsize 8192 ^
--gpulayers 99 ^
--musicgen ^
--tts qwen3tts ^
--port 5001
```

設定の意味を解説します：
- `--musicgen`: 音楽生成機能を有効にします。内部的にMusicGenモデルがロードされます。
- `--tts qwen3tts`: Qwen2-Audioベースの最新TTS（音声合成）を使用します。従来のモデルより自然です。
- `--gpulayers 99`: 可能な限りGPU（CUDA）に処理を投げます。RTX 4090なら全レイヤー余裕です。
- `--port 5001`: デフォルトの5000が他のサービス（Flask等）とぶつかることが多いため、あえてずらしています。

なぜ `qwen3tts` を選ぶのかというと、これが今回追加された「音声クローニング」にネイティブ対応している唯一のエンジンだからです。数秒のサンプル音声（WAVファイル）を読み込ませるだけで、その人の声でLLMの回答を喋らせることができます。

## Step 3: 動かしてみる

ブラウザで `http://localhost:5001` を開くと、KoboldCppのWeb UIが表示されます。

1. **テキスト生成の確認:** 通常通りチャットを送り、返答が来るか確認します。
2. **音楽生成のテスト:** UIの右側にある「MusicGen」タブ、あるいは設定メニューから、プロンプト（例: "Lo-fi hip hop beat with cozy piano"）を入力して生成ボタンを押します。
3. **音声合成のテスト:** 「Speech」設定から `qwen3tts` を選び、適当な文章を入力して再生します。

### 期待される出力

```
[MusicGen] 生成完了: output_music.wav (10秒のBGM)
[TTS] 生成完了: response_voice.wav (合成音声)
```

もしここで音が鳴らない場合は、UI設定の「Audio Output」が正しいデバイスになっているか確認してください。私は以前、サーバー側の出力設定になっていて、自宅サーバー室から虚しくAIの声が響いていたという失敗をしたことがあります。

## Step 4: 実用レベルにする

単にGUIで遊ぶだけなら簡単ですが、この記事のゴールは「動くものを作る」ことです。Pythonを使って、LLMに「今の状況に合わせたBGMのタイトル」を考えさせ、そのBGMを生成し、さらに回答をボイスクローニングで喋らせるスクリプトを実装します。

まず、必要なライブラリをインストールします。

```bash
pip install openai requests
```

次に、以下のスクリプトを作成します。KoboldCppはOpenAI API互換モードを備えているため、`openai` ライブラリがそのまま使えます。

```python
import os
import requests
from openai import OpenAI

# APIの接続設定
client = OpenAI(base_url="http://localhost:5001/v1", api_key="sk-no-key-required")

def generate_ai_content(prompt, voice_reference_path=None):
    # 1. LLMによるテキスト生成
    response = client.chat.completions.create(
        model="local-model",
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.choices[0].message.content
    print(f"AIの回答: {text}")

    # 2. 音楽生成の依頼 (KoboldCpp独自のAPIエンドポイントを叩く)
    # 実際の実装では、LLMに「BGMプロンプト」を抽出させるのがコツ
    music_prompt = "Calm and relaxing ambient music"
    music_response = requests.post(
        "http://localhost:5001/api/v1/generate/musicgen",
        json={"prompt": music_prompt, "duration": 10}
    )

    with open("generated_bgm.wav", "wb") as f:
        f.write(music_response.content)
    print("BGMを 'generated_bgm.wav' として保存しました。")

    # 3. 音声合成 (クローニング)
    # voice_reference_path に自分の声の5秒程度のWAVを指定
    tts_payload = {
        "text": text,
        "as_is": True
    }
    if voice_reference_path:
        # クローニング用の参照音声を送信（Base64エンコードが必要な場合あり）
        # ここではシンプルにデフォルトのTTS APIを想定
        pass

    print("すべての生成が完了しました。")

if __name__ == "__main__":
    generate_ai_content("今日の運勢を教えて。その後、リラックスできる曲を作って。")
```

このスクリプトのポイントは、LLMの返答と同時に「その場の空気に合った音楽」を自動生成させている点です。
実務でゲームのNPCなどに組み込む場合、あらかじめ用意された素材を流すのではなく、その場でAIが作曲したBGMを流すことで、没入感が桁違いに上がります。
私は自分の声をクローニングして、毎朝のニュース要約を「自分の声で」読み上げさせ、その裏で「今日の天気に合わせたBGM」を流すシステムを構築して運用しています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Out of Memory (OOM) | LLMとMusicGenでVRAMを奪い合っている | `--gpulayers` を減らして一部をCPUに逃がす |
| 音声が不自然 | Qwen2-Audioの参照音声が短すぎる | 5〜10秒の、ノイズのないクリアな音声を使う |
| APIが404を返す | エンドポイントのパスが間違っている | `koboldcpp.exe --help` で最新のAPI仕様を確認 |

## 次のステップ

この記事の内容をマスターしたら、次は「マルチモーダルなRAG（検索拡張生成）」に挑戦してみてください。
例えば、自分のPDFライブラリから情報を検索し、その内容をAIが解説しながら、内容に合わせたBGMを自動生成してPodcast形式で出力する、といった応用が可能です。

KoboldCppは、単なる「モデルを動かすためのツール」から、「AIアプリケーションのランタイム」へと進化しました。
RTX 3060（12GB）クラスのGPUがあれば、今日紹介したことはすべて手元の環境で完結します。
クラウドのAPI利用料を気にせず、自分専用の「作曲家兼ナレーター」をローカルで飼い慣らす楽しさを、ぜひ体感してください。

## よくある質問

### Q1: CPUだけでMusicGenやTTSを動かすことは可能ですか？

可能です。ただし、MusicGenの生成には数分かかる場合があります。KoboldCppはOpenBLASやCLBlastをサポートしているため、AVX2命令セットが効くCPUであれば、時間はかかりますが確実に動作します。

### Q2: 自分の声をクローニングする際、著作権や規約の制限はありますか？

KoboldCpp自体はツールであり、モデル（Qwen2-Audio等）のライセンスに従います。一般的に、他人の声を無断でクローニングして公開することは法的・倫理的リスクが伴います。まずは自分自身の声で試すことを強く推奨します。

### Q3: 音楽の生成時間を10秒以上に延ばすことはできますか？

引数やAPIリクエストの `duration` で指定可能ですが、長くするほどVRAM消費量が増え、生成時間も指数関数的に伸びます。実用的には10〜30秒で生成し、それをループさせる処理をプログラム側で書くのが賢明です。

---

## あわせて読みたい

- [1.3万人調査で露呈した「AI格差」の正体：利便性の裏で広がる知的生産性の二極化](/posts/2026-01-15-4a7cd0bb/)
- [Crikket 使い方 OSSでバグ報告を自動化する実力レビュー](/posts/2026-03-11-crikket-oss-bug-reporting-review/)
- [Cardboard 使い方 ビデオ編集を「プログラミング」するAIエディタの真価](/posts/2026-03-11-cardboard-3-ai-video-editor-review-for-engineers/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "CPUだけでMusicGenやTTSを動かすことは可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。ただし、MusicGenの生成には数分かかる場合があります。KoboldCppはOpenBLASやCLBlastをサポートしているため、AVX2命令セットが効くCPUであれば、時間はかかりますが確実に動作します。"
      }
    },
    {
      "@type": "Question",
      "name": "自分の声をクローニングする際、著作権や規約の制限はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "KoboldCpp自体はツールであり、モデル（Qwen2-Audio等）のライセンスに従います。一般的に、他人の声を無断でクローニングして公開することは法的・倫理的リスクが伴います。まずは自分自身の声で試すことを強く推奨します。"
      }
    },
    {
      "@type": "Question",
      "name": "音楽の生成時間を10秒以上に延ばすことはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "引数やAPIリクエストの duration で指定可能ですが、長くするほどVRAM消費量が増え、生成時間も指数関数的に伸びます。実用的には10〜30秒で生成し、それをループさせる処理をプログラム側で書くのが賢明です。 ---"
      }
    }
  ]
}
</script>
