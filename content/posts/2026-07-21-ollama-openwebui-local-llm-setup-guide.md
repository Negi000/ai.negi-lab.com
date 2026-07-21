---
title: "OllamaとOpen WebUIで自分専用のChatGPTをローカル構築する方法"
date: 2026-07-21T00:00:00+09:00
slug: "ollama-openwebui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-07-21-ollama-openwebui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI インストール"
  - "ローカルLLM 環境構築"
  - "Llama 3.1 日本語"
---
**所要時間:** 約20分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIを一切使わず、手元のPCだけでChatGPTと同等のUIを備えた生成AI環境を構築します。
- ネット環境がなくても動作し、入力データが外部に漏れない「完全プライベートなLLM」が手に入ります。
- 前提知識：Dockerの基本的なコマンド（コピペでOK）が叩けること。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでこの価格は、ローカルLLMを安価に最速で動かすための最適解です。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU性能よりも重要なのが「VRAM（ビデオメモリ）」の容量です。
結論から言うと、NVIDIA製のGPUでVRAMが12GB以上あれば、現在主流の「Llama 3.1 8B」や「Gemma 2 9B」クラスが爆速で動きます。
私がメインで使っているRTX 4090（24GB）なら、より高精度な30Bクラスのモデルも実用的な速度で動作しますが、まずは手持ちの機材で試してください。

Macユーザーの場合、メモリ（ユニファイドメモリ）が16GB以上あれば合格点です。
8GBモデルでも動かないことはないですが、推論速度が「1秒間に3〜5文字」程度まで落ち込み、実用性は低くなります。
料金面では、ソフトウェア自体はすべて無料のオープンソースなので、かかるのは電気代だけです。
クラウドのAPI料金を気にせず、1日中10万トークン投げ続けても、請求書におびえる必要はありません。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールには「LM Studio」や「AnythingLLM」など、多くの選択肢があります。
しかし、私が最終的に「Ollama + Open WebUI」の組み合わせに落ち着いたのは、拡張性とUIの完成度が桁違いだからです。

Ollamaはバックエンドとして軽量かつモデル管理が非常に楽で、コマンド一つで最新モデルを落とせます。
そこにOpen WebUIを組み合わせることで、ChatGPTそっくりのインターフェース、過去ログの保存、さらにはRAG（PDFなどの読み込み）までが手に入ります。
他のツールは「動かすこと」に特化していますが、この構成は「日常的に仕事で使うこと」に特化しているのが最大のメリットです。

## Step 1: Ollamaをインストールしてエンジンを起動する

まずはLLMを動かすためのエンジンである「Ollama」を導入します。
これはWebサーバーのような役割を果たし、バックグラウンドでAIの計算を担います。

1. [Ollama公式サイト](https://ollama.com/)からインストーラーをダウンロードし、実行します。
2. インストール完了後、ターミナル（Macはターミナル.app、WindowsはPowerShell）を開き、以下のコマンドを入力してください。

```bash
# Ollamaが正しく動いているか確認
ollama --version
```

バージョンが表示されたら、日本語能力が高いことで定評のあるMetaのモデル「Llama 3.1」をダウンロードします。

```bash
# モデルのダウンロードと起動
ollama run llama3.1
```

ダウンロードが終わると対話モードになります。
ここで「こんにちは」と打って返ってくれば、エンジン部分は完成です。
`/exit` と打って一度終了しましょう。

⚠️ **落とし穴:**
Windows環境でWSL2を使っている場合、GPUを認識させるためにNVIDIA Container Toolkitのインストールが必要です。
基本的にはWindows版のインストーラーをそのまま使うのが、トラブルが少なくて最も確実です。

## Step 2: Open WebUIをDockerで立ち上げる

Ollama単体では黒い画面（CUI）での操作になりますが、これでは不便です。
そこで、Dockerを使って最高峰のUIである「Open WebUI」を導入します。
なぜDockerを使うかというと、Pythonの依存関係で環境を汚すことなく、コマンド一つでアップデートや削除ができるからです。

以下のコマンドをターミナルに貼り付けて実行してください。

```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

各設定の意味は以下の通りです。
- `-p 3000:8080`: PCのブラウザから `localhost:3000` でアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: Dockerコンテナの中から、外側にいるOllamaと通信するための設定です。
- `-v open-webui:/app/data`: チャット履歴や設定を保存する領域を確保します。これがないと、Dockerを止めるたびに履歴が消えます。

## Step 3: ブラウザからAIと対話する

Dockerコマンドの実行が終わったら、ブラウザ（Chrome等）を開き、アドレスバーに `http://localhost:3000` と入力してください。

1. 最初の画面でアカウント作成を求められますが、これは「自分のPC内に保存されるアカウント」なので、好きな名前とメールアドレスで登録してください（外部には送信されません）。
2. ログイン後、画面上部の「モデルを選択」をクリックします。
3. 先ほどダウンロードした `llama3.1:latest` を選択します。

これで、見た目はほぼChatGPTなローカルAI環境が整いました。

### 期待される出力

チャット欄に「Pythonで素数を判定する関数を書いて」と入力してみてください。

```python
def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
```

私の環境（RTX 4090）では、この回答が0.5秒以内に生成され始めます。
もし生成が極端に遅い（1文字ずつゆっくり出る）場合は、OllamaがGPUではなくCPUを使って計算している可能性があります。
その場合はタスクマネージャーの「パフォーマンス」タブで、GPUの専用メモリが使われているか確認してください。

## Step 4: 実用レベルにカスタマイズする（Modelfileの活用）

素のLlama 3.1は英語寄りな性格をしています。
これを「常に丁寧な日本語で回答するプロのエンジニア」に固定するために、自分専用のモデル（Modelfile）を作成しましょう。

Open WebUIの左サイドバーにある「ワークスペース」→「モデル」から「モデルを作成」を選択します。

```dockerfile
# ベースにするモデル
FROM llama3.1

# システムプロンプトの設定
PARAMETER system """
あなたは非常に優秀なシニアエンジニアです。
回答はすべて日本語で行い、コード例には必ず丁寧な解説を添えてください。
また、簡潔さよりも正確さと、ベストプラクティスに基づいた解説を優先してください。
"""

# 創造性の調整（0に近いほど正確、1に近いほど独創的）
PARAMETER temperature 0.7
```

この設定で「My-Engineer」という名前で保存すると、次からはこのカスタマイズされたAIを選択できるようになります。
これは、ChatGPTでいうところの「GPTs」を自分で作っているようなものです。
私はここに「翻訳専用モデル」や「コードレビュー専用モデル」を10種類以上作り込んで使い分けています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| WebUIにモデルが出てこない | DockerからOllamaが見えていない | Docker起動時の `--add-host` 設定が正しいか確認してください。 |
| 回答がめちゃくちゃ遅い | VRAM不足でCPU推論になっている | モデルのサイズを落とす（8Bから3Bのモデルに変える等）か、VRAMの多いGPUを検討してください。 |
| Dockerが起動しない | ポート3000が他で使われている | `-p 3001:8080` のように左側の数字を変えて試してください。 |

## 次のステップ

環境が整ったら、次は「RAG（検索拡張生成）」に挑戦してみてください。
Open WebUIのチャット欄にPDFファイルをドラッグ＆ドロップするだけで、その資料の内容に基づいた回答が可能になります。
会社の内部規定や、最新の技術ドキュメントを読み込ませることで、ネットに落ちていない情報についてAIと相談できるようになります。

また、より高い精度を求めるなら、Googleの「Gemma 2 27B」や、中国Alibabaが公開している「Qwen 2.5 32B」などの、少し大きめのモデルを試すのが面白いです。
これらが不自由なく動くようになると、月額$20の有料LLMサービスを解約しても困らないレベルに到達します。
自分のハードウェアの限界を攻めるのは、自作PCユーザーにとって最高に楽しい時間ですよ。

## よくある質問

### Q1: 外部のPCやスマホからこのUIを使うことはできますか？

可能です。Dockerを実行しているPCのローカルIPアドレス（例: 192.168.1.5）を使い、同じWi-Fi内のデバイスから `http://192.168.1.5:3000` にアクセスすれば、スマホからもローカルAIと会話できます。

### Q2: 途中でモデルのダウンロードが止まってしまいます。

Ollamaのサーバーが混んでいるか、ネットワークが不安定な場合があります。一度中断して `ollama pull llama3.1` を再実行すれば、途中から再開されます。ディスク容量が数GB空いているかも確認してください。

### Q3: データのプライバシーは本当に守られていますか？

はい。この構成では、インターネットを切断した状態でも動作します。Open WebUI内で作成したアカウント情報も、チャットログも、すべてStep 2で作成したDockerボリューム（自分のストレージ）内にしか保存されません。

---

## あわせて読みたい

- [OllamaとOpen WebUIを組み合わせて自分専用のローカルChatGPT環境を構築する方法](/posts/2026-07-08-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIの使い方！完全プライベートなローカルLLM環境を構築する方法](/posts/2026-07-07-ollama-openwebui-local-llm-guide/)
- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-06-28-ollama-open-webui-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "外部のPCやスマホからこのUIを使うことはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Dockerを実行しているPCのローカルIPアドレス（例: 192.168.1.5）を使い、同じWi-Fi内のデバイスから http://192.168.1.5:3000 にアクセスすれば、スマホからもローカルAIと会話できます。"
      }
    },
    {
      "@type": "Question",
      "name": "途中でモデルのダウンロードが止まってしまいます。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaのサーバーが混んでいるか、ネットワークが不安定な場合があります。一度中断して ollama pull llama3.1 を再実行すれば、途中から再開されます。ディスク容量が数GB空いているかも確認してください。"
      }
    },
    {
      "@type": "Question",
      "name": "データのプライバシーは本当に守られていますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。この構成では、インターネットを切断した状態でも動作します。Open WebUI内で作成したアカウント情報も、チャットログも、すべてStep 2で作成したDockerボリューム（自分のストレージ）内にしか保存されません。 ---"
      }
    }
  ]
}
</script>
