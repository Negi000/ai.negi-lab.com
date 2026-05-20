---
title: "Trainer 画面録画でAIエージェントを訓練し実務を自動化する"
date: 2026-05-20T00:00:00+09:00
slug: "trainer-v2-ai-agent-screen-recording-review"
description: "AIエージェント開発における最大の壁である「操作手順の定義」を画面録画によるデモンストレーションで解決する。既存のDOM解析型エージェントと違い、画像認識..."
cover:
  image: "/images/posts/2026-05-20-trainer-v2-ai-agent-screen-recording-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Trainer"
  - "AIエージェント"
  - "Claude Computer Use"
  - "画面録画 自動化"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- AIエージェント開発における最大の壁である「操作手順の定義」を画面録画によるデモンストレーションで解決する
- 既存のDOM解析型エージェントと違い、画像認識ベースで動くため、ブラウザ外のデスクトップアプリや複雑なUIでも学習可能
- 自分のPC操作を「教師データ」として汎用化したいエンジニアには最適だが、定型作業の単純な自動化なら従来のRPAで十分

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4070 Ti Super</strong>
<p style="color:#555;margin:8px 0;font-size:14px">画面録画とLMM推論を並行して行うためのVRAM 16GBを確保できる</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204070%2520Ti%2520Super%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204070%2520Ti%2520Super%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204070%20Ti%20Super%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、AIエージェントを「自社専用の職人」に育て上げたい開発者にとって、Trainerは現時点で最も効率的なデータ収集ツールの一つです。評価は星4つ。

従来のAIエージェント開発では、LLMに対して「このボタンを押して、次にこれを入力して」とテキストで延々と説明するか、Playwrightなどのライブラリでセレクタを特定する必要がありました。しかし、Trainerは「人間が実際に操作してみせる」だけで、その過程をAIが理解可能なステップに分解し、訓練データ（Trajectory）として構造化してくれます。

ただし、これを使いこなすには、録画したデータをどのLMM（Large Multimodal Model）に流し込み、どうやって推論回数を抑えるかというアーキテクチャ設計の知識が求められます。単に「録画すれば明日から仕事がゼロになる」という魔法の杖を期待する層には不要ですが、Claude 3.5 SonnetのComputer Use APIなどを実務に組み込もうとして、プロンプトの肥大化に悩んでいる人には間違いなく「買い」の選択肢です。

## このツールが解決する問題

これまでのAIエージェント、特にWeb操作を中心としたものは、DOM（HTML構造）に依存しすぎていました。そのため、Reactなどのフレームワークで動的に変わるIDや、キャンバス要素、あるいはデスクトップアプリの操作には極めて弱いという課題がありました。

また、エンジニアが手動で「操作ログ」を作成する場合、1つのタスクに対して数百行のJSONを書くこともしばしばあります。これでは開発コストが自動化による利益を上回ってしまいます。Trainerはこの「データ作成のボトルネック」を、人間による画面録画という最も直感的なインターフェースで解決します。

具体的には、マウスのクリック座標、キーボード入力、そしてその前後のスクリーンショットをミリ秒単位で同期させ、一つの「行動シーケンス」としてパッケージ化します。これにより、AIは「なぜこのタイミングでこのボタンを押したのか」というコンテキストを、画像と操作ログの両面から学習できるようになります。これは、複雑な社内ERPシステムや、APIが公開されていない古いソフトウェアの操作をAIに代行させるための唯一の現実的な解と言えるでしょう。

## 実際の使い方

### インストール

TrainerはPython環境をベースに動作します。依存関係に画像処理ライブラリが含まれるため、仮想環境での構築を強く推奨します。

```bash
# Python 3.10以上が必要
python -m venv venv
source venv/bin/activate

# パッケージのインストール
pip install trainer-sdk
# スクリーンキャプチャ用のドライバが必要な場合がある
trainer-sdk setup-drivers
```

注意点として、macOSでは「画面収録」の権限許可、Windowsでは管理者権限での実行が必要になるケースがあります。また、マルチディスプレイ環境ではメインディスプレイの解像度が学習データの基準になるため、録画時の環境固定が重要です。

### 基本的な使用例

録画を開始し、操作をAIに学習させるためのデータセットとして保存する基本的なフローは以下の通りです。

```python
from trainer import Recorder, Dataset

# 録画セッションの初期化
# fpsは30以上を推奨（細かいマウスの動きを捉えるため）
recorder = Recorder(fps=30, output_dir="./training_data")

# 録画開始
# ここから人間が手動でブラウザやアプリを操作する
recorder.start()

print("操作を記録中... 完了したらCtrl+Cで停止してください")

try:
    while True:
        # 録画を継続
        pass
except KeyboardInterrupt:
    # 録画停止とデータの構造化保存
    session_data = recorder.stop()
    print(f"記録完了: {len(session_data.frames)} フレームのデータを保存しました")

# 保存されたデータをAI訓練用に変換
dataset = Dataset.from_session(session_data)
dataset.export(format="jsonl_with_images")
```

このコードを実行すると、指定したディレクトリにスクリーンショットの連番画像と、それに対応する入力イベント（クリック、タイピング）が記録されたJSONLファイルが生成されます。

### 応用: 実務で使うなら

実務では、この録画データを元に「特定の手順」をプロンプトに動的に注入する、あるいはLoRAなどの手法でLMMをファインチューニングする用途に使います。

例えば、経費精算システムへの入力業務を自動化する場合、まず人間が「ログイン→領収書アップロード→金額入力→承認依頼」という一連の動作を3回ほど繰り返して録画します。Trainerはこれらを正規化し、以下のような「エージェント用マニュアル」を自動生成するイメージです。

```python
# 録画データから推論モデルを呼び出す擬似コード
from trainer import AgentExecutor

# 録画データから作成した「行動ポリシ」をロード
agent = AgentExecutor.load_model("./expense_report_policy")

# 新しい領収書PDFを渡して実行
# AIは録画された「人間の動き」をトレースし、現在の画面状況に合わせて補正しながら操作する
agent.run(input_file="receipt_2023_10.pdf")
```

単なるマクロとの違いは、UIの配置が数ピクセルずれたり、読み込み待ちが発生したりしても、AIが視覚的に状況を判断して「待機」や「再試行」を行える点にあります。

## 強みと弱み

**強み:**
- **ノーコードでのデータ収集:** プログラミングによるスクレイピングコードを書く必要がなく、非エンジニアの業務エキスパートに操作をさせてデータを集めることが可能。
- **マルチモーダル対応:** 座標データだけでなく画像コンテキストを保持するため、GPT-4oやClaude 3.5 Vなどの視覚能力を最大限に引き出せる。
- **高密度なログ:** 1秒間に30回以上のサンプリングを行うため、人間の「迷い」や「ローディング待ち」もデータとして抽出できる。

**弱み:**
- **リソース消費が激しい:** 高画質で録画しながらバックグラウンドでエンコードするため、非力なPCでは操作自体にラグが生じる。RTX 3060以上のGPUを積んだWindows機、あるいはApple SiliconのMacが実質必須。
- **プライバシーリスク:** 録画中に通知ポップアップやパスワード入力が表示されると、それもすべて学習データに含まれてしまう。データのクレンジング作業は避けて通れない。
- **決定論的ではない:** AIエージェント全般の弱みだが、100回中100回同じ動作を保証するのは難しく、リトライ処理の設計が必要。

## 代替ツールとの比較

| 項目 | Trainer | Claude Computer Use | Skyvern |
|------|-------------|-------|-------|
| 核心的機能 | 録画によるティーチング | API経由の直接PC操作 | ブラウザ特化のワークフロー自動化 |
| 学習コスト | 低（やって見せるだけ） | 高（環境構築とプロンプト） | 中（Pythonでの定義が必要） |
| 対応範囲 | デスクトップアプリ全般 | デスクトップアプリ全般 | Webブラウザのみ |
| 実行環境 | ローカル実行が基本 | Docker/クラウド上が主流 | クラウド/セルフホスト |

使い分けとしては、Webサイトのデータ抽出が目的なら**Skyvern**、最新のLLM機能を直接試したいなら**ClaudeのComputer Use**、社内の独自システムを「手っ取り早く」AIに覚えさせたいなら**Trainer**が最適です。

## 料金・必要スペック・導入前の注意点

Trainer自体の価格体系は現在開発者向けに公開されている段階（v2）ですが、この手のツールは「記録は無料、実行やホスティングは従量課金」というモデルが多いです。

導入にあたって最も注意すべきはハードウェアスペックです。画面録画とAIによるリアルタイム解析を並行して行うため、GPU性能が作業効率を直結します。
最低でもVRAM 12GB以上のグラフィックボード（RTX 3060 12GBや、予算があるならRTX 4070 Ti Super 16GBなど）を推奨します。Macならメモリ32GB以上のM2/M3チップが妥当なラインです。

また、商用利用においては、録画データが外部サーバー（SaaSベンダー側）にアップロードされて再学習に使われないか、プライバシーポリシーを精査する必要があります。機密情報を扱う場合は、ローカル完結型のモデルと組み合わせて運用する設計が不可欠です。

## 私の評価

個人的な評価は **4 / 5** です。

これまで「AIエージェントを作ろう」と思って挫折した人の多くは、プログラミングよりも「AIに何をさせるか」の定義で力尽きていました。Trainerはその泥臭い作業を「録画」という日常的なアクションに置き換えた点で、非常に優れたUXを提供しています。

私が特に評価しているのは、このツールが「エンジニアのためのデータ作成支援」に徹している点です。吐き出されるデータが構造化されているため、自分の好きなモデル（Llama-3-VやQwen-VLなど）に組み込みやすい。

一方で、現状では録画データのノイズ除去（不要なブラウザタブの映り込みなど）に手作業が発生するため、完全な自動化パイプラインにはあと一歩という印象です。それでも、自社独自の「AI社員」を作りたいと考えているチームにとっては、初期データを集めるための「最強のバケツ」になるでしょう。

## よくある質問

### Q1: 録画したデータはどのLLMで使えますか？

標準でJSONL形式や画像セットとして出力されるため、OpenAIのFine-tuning API（GPT-4o）や、オープンソースのマルチモーダルモデル（LLaVAなど）の学習データとしてそのまま利用可能です。

### Q2: セキュリティ面で、パスワード入力を隠す機能はありますか？

現時点では自動でマスキングする機能は限定的です。録画後に特定の座標範囲を黒塗りにする、あるいは機密情報を入力するプロセスだけを録画から除外する運用上の工夫が必要です。

### Q3: 日本語のUIも認識できますか？

はい。Trainer自体は座標と画像で判断しているため、UIの言語には依存しません。ただし、その後の処理を行うLMM（GPT-4oなど）の日本語認識能力に依存することになります。

---

## あわせて読みたい

- [Co-Tasker 使い方と実世界API連携の可能性を評価](/posts/2026-04-21-co-tasker-real-world-api-review-for-ai-developers/)
- [Claude CodeのPRレビューを強化するadamsreview活用術｜AI開発に最適なMac・RTX選び方と比較](/posts/2026-05-12-claudecode-adamsreview-hardware-guide/)
- [Google Workspace Intelligenceが変える業務自動化のリアルとMicrosoft Copilotへの対抗策](/posts/2026-04-23-google-workspace-intelligence-ai-intern-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "録画したデータはどのLLMで使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "標準でJSONL形式や画像セットとして出力されるため、OpenAIのFine-tuning API（GPT-4o）や、オープンソースのマルチモーダルモデル（LLaVAなど）の学習データとしてそのまま利用可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "セキュリティ面で、パスワード入力を隠す機能はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "現時点では自動でマスキングする機能は限定的です。録画後に特定の座標範囲を黒塗りにする、あるいは機密情報を入力するプロセスだけを録画から除外する運用上の工夫が必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語のUIも認識できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。Trainer自体は座標と画像で判断しているため、UIの言語には依存しません。ただし、その後の処理を行うLMM（GPT-4oなど）の日本語認識能力に依存することになります。 ---"
      }
    }
  ]
}
</script>
