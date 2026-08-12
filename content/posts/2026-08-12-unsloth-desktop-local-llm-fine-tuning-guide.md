---
title: "Unsloth Desktop 使い方：ローカルLLMのファインチューニングをGUIで完結させる方法"
date: 2026-08-12T00:00:00+09:00
slug: "unsloth-desktop-local-llm-fine-tuning-guide"
cover:
  image: "/images/posts/2026-08-12-unsloth-desktop-local-llm-fine-tuning-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Unsloth Desktop 使い方"
  - "LLM ファインチューニング 入門"
  - "Llama 3 学習 方法"
  - "ローカルLLM 環境構築"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- プログラミング不要でLlama 3やGemma 2を自分のデータで学習させ、特定の口調や知識を持ったカスタムモデルを作成します。
- Pythonのコードを一行も書かずに、GUI上でデータセットの読み込みからLoRA学習、GGUF形式での書き出しまでを完結させます。
- 学習したモデルをLM StudioやOllamaで即座に動かせる状態にします。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBがこの価格で手に入る唯一の選択肢。LLM学習の入門に最適。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMの学習において、妥協できないのは「VRAM（ビデオメモリ）」の容量です。Unslothはメモリ効率が極めて高いですが、それでも物理的な限界はあります。

最低でも NVIDIA製GPU（RTX 3060 12GB以上）を推奨します。VRAM 8GBでも動作はしますが、モデルサイズが制限され、学習中のクラッシュ（OOM: Out Of Memory）に悩まされることになります。仕事で実用的な精度を求めるなら、RTX 4060 Ti 16GBがエントリークラスとしての正解です。私の環境のようにRTX 4090を積んでいれば、Llama 3 8Bクラスの学習は「爆速」で終わります。

Mac（Apple Silicon）については、UnslothがCUDAに最適化されているため、現時点ではWindows（WSL2）またはLinux環境が必須です。また、ソフトウェア自体は無料ですが、学習用のデータセットを作成するために、上位モデル（GPT-4oやClaude 3.5 Sonnet）のAPIを利用する場合はその料金が発生します。

## なぜこの方法を選ぶのか

これまでLLMのファインチューニング（微調整）を行うには、PyTorchの環境構築、bitsandbytesの依存関係解消、そして複雑な学習スクリプトの記述が必要でした。Axolotlのような優れたツールもありますが、設定ファイル（YAML）の記述ミス一つで数時間が無駄になることも珍しくありません。

Unsloth Desktopを選ぶ最大の理由は「思考のノイズを減らせる」点にあります。Unslothのコアエンジンは、通常のHuggingFaceのスクリプトと比較して、学習速度が2倍速く、メモリ消費を70%削減します。この強力なエンジンをGUIで操作できるようになったことで、エンジニアは「コードのデバッグ」ではなく「データの質」に集中できるようになりました。

「とりあえず動く」状態まで数分で到達できるため、試行錯誤のサイクルが劇的に速くなります。

## Step 1: 環境を整える

Windowsユーザーの場合、まずはWSL2（Windows Subsystem for Linux）と最新のNVIDIAドライバがインストールされていることが前提です。

```bash
# NVIDIAドライバが正常に認識されているか確認
nvidia-smi
```

このコマンドでGPU名とCUDAバージョンが表示されない場合は、まずドライバの再インストールが必要です。Unsloth Desktopはインストーラーを実行するだけで必要なライブラリを内部でセットアップしてくれますが、ベースとなるGPUドライバだけはOS側で用意しておく必要があります。

公式サイトまたはリリースページから `Unsloth_Desktop_Setup.exe` をダウンロードして実行します。インストールパスに日本語（全角文字）が含まれていると、内部のPython実行環境がエラーを吐くケースがあるため、必ず英数字のみのディレクトリを選択してください。

⚠️ **落とし穴:** インストール中に「仮想化機能（VT-x/AMD-V）が無効です」というエラーが出る場合があります。これはPCのBIOS/UEFI設定で仮想化がオフになっていることが原因です。これを有効にしないとWSL2が動かず、結果としてUnslothも起動しません。

## Step 2: データセットの準備

ここが最も重要なステップです。AIの賢さはモデルではなく「データの質」で決まります。Unsloth Desktopでは、JSONL形式のファイルを読み込むのが一般的です。

以下の形式のファイルを `dataset.jsonl` として保存してください。

```json
{"instruction": "あなたの名前は？", "input": "", "output": "私は「ねぎ」のブログを学習した特化型AIです。"}
{"instruction": "おすすめのGPUは？", "input": "予算10万円以内", "output": "その予算ならRTX 4060 Ti 16GB一択です。VRAM容量が学習の要だからです。"}
```

各行が一つの学習サンプルになります。`instruction`（指示）、`input`（補足情報）、`output`（期待される回答）の3つのキーを持つ必要があります。

⚠️ **落とし穴:** データの件数が少なすぎると、モデルは何も学習しません。最低でも50件、理想的には500件以上の高品質なペアを用意してください。10件程度で試すと、既存の知識を忘れる「破滅的忘却」だけが起きて、回答が支離滅裂になるリスクが高いです。

## Step 3: パラメータの設定と学習開始

アプリを起動し、「New Project」から先ほど作成したデータセットを選択します。次にモデルを選択します。初心者なら `Llama-3-8B-Instruct` か `Gemma-2-9B` を選んでおけば間違いありません。

設定画面で以下の3つの数値を調整します。

1. **LoRA Rank (r):** デフォルトは16です。これを増やすとより複雑な知識を学習できますが、VRAM消費が増えます。32程度にするのが実用的です。
2. **Learning Rate (学習率):** `2e-4`（0.0002）が推奨です。これより大きくすると学習が失敗しやすく、小さすぎるといつまで経っても賢くなりません。
3. **Epochs:** データセットを何回繰り返して学習するか。通常は3回程度で十分です。

設定が終わったら「Start Training」をクリックします。

### 期待される出力

画面に「Loss（損失）」のグラフが表示されます。この数値が右肩下がりに、最終的に0.5〜1.0程度まで落ちていれば学習は成功です。

```
Step 10: Loss 2.45
Step 50: Loss 1.20
Step 100: Loss 0.85
...
Training Completed!
```

もしLossが最初から0に近い場合は「過学習」を疑ってください。データセットが単純すぎて、モデルが答えを丸暗記しているだけかもしれません。

## Step 4: 実用レベルにする（GGUFエクスポート）

学習が終わったモデルは、そのままではアプリ内でしか使えません。実務で使うためには、他のツールで読み込める形式に変換する必要があります。

1. 「Export」タブを開きます。
2. 「Format」から `GGUF` を選択します。これはLM StudioやOllamaで広く使われている形式です。
3. 「Quantization（量子化）」は `q4_k_m` または `q8_0` を選びます。4090などの大容量GPUを使わない限り、4bit（q4）量子化が速度と精度のバランスが最も良いです。
4. 「Save」を押すと、数分後に `.gguf` ファイルが生成されます。

このファイルをLM Studioの `Models` フォルダに放り込めば、自分専用にチューニングされたAIとのチャットが始まります。

```python
# Ollamaで動かす場合のModelfile例
FROM ./my-custom-model.gguf
PARAMETER temperature 0.7
SYSTEM "あなたは『ねぎ』のブログの文体で回答する専門家です。"
```

このように、学習したモデルを外部ツールと連携させることで、特定の業務（社内ドキュメントの要約、特定のプログラミングスタイルの強制など）に特化したエージェントが完成します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Out of Memory (OOM) | VRAM不足。設定したモデルが大きすぎる。 | LoRA Rankを下げ、Batch Sizeを1にする。または4bitベースモデルを選択する。 |
| LossがNanになる | 学習率（Learning Rate）が高すぎる。 | 学習率を 1e-5 程度まで下げて再試行する。 |
| 変換後の回答が崩れる | 日本語のトークナイザーが対応していない。 | Llama-3など日本語対応が謳われているベースモデルを選択する。 |

## 次のステップ

Unsloth Desktopで「動くもの」が作れたら、次はデータの質を極めるフェーズです。

1. **合成データ（Synthetic Data）の活用:** 手元にデータが少ない場合は、GPT-4oに「〇〇という口調のサンプルを500件作って」と依頼し、それを学習データにします。これが現在のファインチューニングの主流です。
2. **評価（Evaluation）:** 作成したモデルが、学習前のモデルより本当に賢くなったのか、ベンチマーク用の質問を投げて比較してください。
3. **DPO（Direct Preference Optimization）:** UnslothはDPOという、モデルの「好み」を修正する高度な手法にも対応し始めています。さらに一段上の精度を目指すなら、このキーワードで調査を進めることをお勧めします。

## よくある質問

### Q1: AMDのグラフィックボードでも動きますか？

現時点では推奨しません。UnslothはNVIDIAのCUDAと、Tritonというカーネルに強く依存しています。ROCm（AMD用環境）での動作報告もありますが、セットアップの難易度が跳ね上がるため、仕事で使うなら素直にNVIDIA製を買いましょう。

### Q2: 学習データに個人情報を含めても大丈夫ですか？

ローカル環境で完結しているため、外部にデータが送信されることはありません。これがローカルLLMで学習させる最大のメリットです。ただし、作成したモデルファイルをHuggingFaceなどで公開する際は、モデルの中にデータの内容が「記憶」されている可能性があることに注意してください。

### Q3: ファインチューニングとRAG、どちらが良いですか？

「特定の知識（最新のニュースなど）」を教えたいならRAG（外部検索連携）が適しています。「特定の振る舞い、出力形式、専門的な口調」を身につけさせたいなら、今回のファインチューニングが最適です。実務では、この両方を組み合わせるのが最強の構成になります。

---

## あわせて読みたい

- [Qwen 2.5 27B 使い方 | 16GB以上のVRAMを使い切るローカルLLM構築ガイド](/posts/2026-08-11-qwen-25-27b-local-llm-python-guide/)
- [Minimax 2.7 使い方：ローカル環境で高性能MoEモデルを動かす実践ガイド](/posts/2026-04-05-minimax-2-7-local-llm-guide-python/)
- [Qwen 3.6 27B 使い方 | ローカルLLM環境構築と量子化モデル比較ガイド](/posts/2026-04-28-qwen-36-27b-gguf-quantization-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "AMDのグラフィックボードでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "現時点では推奨しません。UnslothはNVIDIAのCUDAと、Tritonというカーネルに強く依存しています。ROCm（AMD用環境）での動作報告もありますが、セットアップの難易度が跳ね上がるため、仕事で使うなら素直にNVIDIA製を買いましょう。"
      }
    },
    {
      "@type": "Question",
      "name": "学習データに個人情報を含めても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ローカル環境で完結しているため、外部にデータが送信されることはありません。これがローカルLLMで学習させる最大のメリットです。ただし、作成したモデルファイルをHuggingFaceなどで公開する際は、モデルの中にデータの内容が「記憶」されている可能性があることに注意してください。"
      }
    },
    {
      "@type": "Question",
      "name": "ファインチューニングとRAG、どちらが良いですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "「特定の知識（最新のニュースなど）」を教えたいならRAG（外部検索連携）が適しています。「特定の振る舞い、出力形式、専門的な口調」を身につけさせたいなら、今回のファインチューニングが最適です。実務では、この両方を組み合わせるのが最強の構成になります。 ---"
      }
    }
  ]
}
</script>
