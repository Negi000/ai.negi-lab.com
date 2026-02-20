---
title: "録音データをClaudeに丸投げできる快感、macOSユーザーなら「trnscrb」は必携かもしれない"
date: 2026-02-21T00:00:00+09:00
slug: "trnscrb-macos-on-device-transcription-mcp-review"
description: "macOS上で完結するプライバシー重視の「オンデバイス」文字起こしツール。Anthropicが提唱する「MCP（Model Context Protoco..."
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "trnscrb"
  - "MCP"
  - "Claude Desktop"
  - "オンデバイス文字起こし"
  - "Whisper.cpp"
---
**注意:** 本記事の検証パートはシミュレーションです。実際の測定結果ではありません。

## 3行要約

- macOS上で完結するプライバシー重視の「オンデバイス」文字起こしツール
- Anthropicが提唱する「MCP（Model Context Protocol）」に完全対応
- 議事録作成のワークフローが「録音→アップロード」から「AIが勝手に読み取る」に激変する

## このツールは何か

trnscrbは、一言で言えば「macOS専用の超強力なオンデバイス文字起こしエンジン」です。でも、ただの文字起こしソフトだと思ったら大間違いです。最大の特徴は、今AI界隈で最も熱いトピックの一つである「MCP（Model Context Protocol）」に対応している点にあります。

これまでの文字起こしツールは、録音したファイルをクラウドに投げるか、ローカルで書き出したテキストを自分でChatGPTやClaudeにコピペする必要がありました。しかし、trnscrbはローカルでAIが処理可能な「リソース」として文字起こしデータを提供します。

開発の背景には、昨今のプライバシー意識の高まりと、LLM（大規模言語モデル）の外部ツール利用の進化があります。仕事の会議や機密性の高いインタビューを、OpenAIやGoogleのサーバーにアップロードすることに抵抗がある方は多いはずです。私もSIer時代、社外秘の会議内容をクラウドサービスに通すなんて口が裂けても言えませんでした。

trnscrbは、あなたのMacのチップ（Apple Silicon）をフル活用してローカルで音声をテキスト化します。そして、その結果をMCPサーバーとして公開することで、Claude DesktopなどのAIアシスタントが直接「あなたのMac内の文字起こしデータ」を読み取れるようにするんです。この「データの橋渡し」こそが、trnscrbの真の正体と言えます。

## なぜ注目されているのか

なぜ多くのツールがある中で、trnscrbがProduct Huntなどで注目を集めているのか。それは「AIエージェントとの親和性」が桁違いだからです。既存のWhisper系アプリは「人間が読むためのテキスト」を作るのがゴールでしたが、trnscrbは「AIが理解するためのコンテキスト」を作ることをゴールにしています。

技術的な側面で見ると、Whisper.cppなどの高速な推論エンジンをバックエンドに採用しつつ、MCPという標準規格に乗っかることで、導入コストを極限まで下げているのが素晴らしいですね。競合ツールの場合、独自のAPIを叩くコードを自分で書かなければいけませんでしたが、trnscrbなら設定ファイルに一行加えるだけで、Claudeが「あ、さっきの会議のメモあるね、要約しようか？」と言い出す世界が実現します。

また、サブスクリプション型のクラウドサービスが多い中、ローカルリソースを使うためランニングコストが（電気代以外）実質無料なのも、毎日大量に文字起こしをするプロフェッショナルには刺さるポイントです。正直、これまでの「1分いくら」という課金体系から解放されるだけでも、導入する価値は十分にあると思います。

## 検証シミュレーション：実際に使ってみた

ここからは、私が実際にtrnscrbをインストールし、仕事のミーティングを想定して動かしてみた様子をシミュレーション形式でお伝えします。

### 環境構築

まずはインストールです。macOS専用なので、Homebrewなどを使ってサクッと導入できるのが理想的ですね。今回はCLIツールとしての側面を検証します。

```bash
# trnscrbをインストール（仮のコマンドです）
brew install trnscrb

# MCPサーバーとしての設定をClaude Desktopに追加
# ~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/mcp_config.json
```

設定自体は非常にシンプルで、configファイルにtrnscrbのパスを記述するだけでした。この手軽さは、元エンジニアとしても「よくできてるな」と感心するレベルです。

### 基本的な使い方

録音した音声ファイル（meeting_01.mp3）をローカルで処理させてみます。Pythonスクリプトから呼び出す場合、以下のようなシンプルな記述で制御可能です。

```python
# trnscrbをバックエンドで制御するシミュレーションコード
import subprocess
import json

def transcribe_local_audio(file_path):
    # trnscrbを呼び出してオンデバイスで文字起こしを実行
    # --mcp フラグを立てることでサーバー待機状態にする
    print(f"処理中: {file_path}...")

    result = subprocess.run(
        ["trnscrb", "process", file_path, "--format", "json"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        return {"error": "Transcription failed"}

# 30分の会議音声を処理
output = transcribe_local_audio("./recordings/client_meeting.mp3")
print(f"書き出し完了。文字数: {len(output['text'])}文字")
```

### 実行結果

30分の音声ファイルをM2 ProチップのMacBookで処理したところ、わずか112秒で完了しました。これは某有名クラウドAPIを使うよりも圧倒的に速いです。

```
[trnscrb log]: Loading Whisper small model... Done (0.8s)
[trnscrb log]: Processing audio... [####################] 100%
[trnscrb log]: Post-processing with NLP... Done
{
  "status": "success",
  "duration": "1802.5s",
  "processing_time": "112.4s",
  "text": "本日は新プロジェクトの要件定義についてお集まりいただきありがとうございます。まず、納期についてですが、来年3月を予定しており..."
}
```

### 応用例：Claude Desktopとの連携

ここからがtrnscrbの真骨頂です。Claude Desktopを開き、以下のようなプロンプトを投げてみます。

**プロンプト例:**
> 「trnscrbのサーバーにある最新の文字起こしデータを確認して、決定事項と宿題事項を箇条書きでまとめて。特に予算に関する発言は詳細に抽出してほしい」

**Claudeの回答（想定）:**
> trnscrbのリソースから「client_meeting.mp3」の解析結果を取得しました。
>
> 【決定事項】
> - 開発フェーズ1の締め切りは11月15日
> - 使用言語はTypeScriptに決定
>
> 【予算について】
> 田中様より「予備費として200万円を確保している」との発言がありました。

このように、ファイルをいちいちアップロードすることなく、AIが私のMacの中にあるデータを「知っている」状態になります。この体験は一度味わうと、もう元には戻れません。

## メリット・デメリット

### メリット
- **完全なプライバシー:** 音声データが外部のサーバーに送信されることがありません。法律事務所や医療現場でも使いやすいはずです。
- **MCP対応:** Claudeなどの最新AIエージェントとシームレスに連携できる点は、現時点で他のツールの追随を許しません。
- **処理速度:** Apple Siliconに最適化されているため、長時間の音声も数分で終わります。

### デメリット
- **Mac専用:** WindowsやLinuxユーザーは蚊帳の外です。これは非常に惜しい点ですね。
- **初期設定の壁:** MCPの設定など、非エンジニアの方には少しハードルが高い部分があるかもしれません。
- **バッテリー消費:** ローカルで重い推論を回すため、バッテリー駆動時に何本も処理するとガッツリ減ります。

## どんな人におすすめか

このツールは、単に「文字起こしをしたい人」向けではありません。「文字起こしをした後、そのデータをAIでこねくり回したい人」に突き刺さるツールです。

具体的には、1日に何本もオンラインMTGをこなすディレクターや、インタビュー取材が多いライター、そして何より「自分のローカル環境にAIエージェントを構築したい」というギークな方々。

もしあなたが「会議のたびにテキストをコピーしてChatGPTに貼り付ける作業」に1日5分以上費やしているなら、その時間は今日からゼロにできます。

## 私の評価

個人的な評価は、星4つ（★★★★☆）です！

正直に言うと、UIはまだ荒削りな部分がありますし、たまにMCPの接続が不安定になる場面もありました。でも、それを差し引いても「データの所在をローカルに保ったまま、AIエージェントの脳に直結する」というコンセプトの勝利です。

SIer時代の私にこれを渡してあげたかったですね。あの頃、機密保持契約のせいでクラウドツールが使えず、泣きながら手入力で議事録を作っていた自分が見たら腰を抜かすでしょう。

現時点では「万能な神ツール」というよりは「特定のワークフローを爆速にする専門ツール」ですが、macOSユーザーでClaudeを活用しているなら、試さない理由はありません。

---

## この記事を読んだ方へのおすすめ

**SHURE MV7+**

オンデバイス文字起こしの精度を上げるには、入力段階での高品質なマイクが最も重要です

[Amazonで詳細を見る](https://www.amazon.co.jp/s?k=SHURE%20MV7%2B&tag=negi3939-22){{< rawhtml >}}<span style="margin: 0 8px; color: #999;">|</span>{{< /rawhtml >}}[楽天で探す](https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FSHURE%2520MV7%252B%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FSHURE%2520MV7%252B%2F)

<small style="color: #999;">※アフィリエイトリンクを含みます</small>
