---
title: "OllamaとOpen WebUIでローカルLLM環境を構築する方法"
date: 2026-06-30T00:00:00+09:00
slug: "ollama-openwebui-local-llm-guide"
cover:
  image: "/images/posts/2026-06-30-ollama-openwebui-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 構築"
  - "Llama 3 ローカル"
  - "Docker LLM 環境"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIを一切使わず、完全にオフラインかつ無料でChatGPT並みの操作感を持つローカルLLM環境を構築します。
- 前提知識：ターミナルの基本的な操作、Dockerの概要がわかること。
- 必要なもの：NVIDIA製GPUを搭載したPC、またはApple Silicon（M1/M2/M3）搭載のMac。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU性能よりも重要なのがGPUのVRAM（ビデオメモリ）容量です。
結論から言うと、VRAMが8GBあればLlama 3の8B（80億パラメータ）モデルがサクサク動きますが、業務で実用的な精度を求めるなら12GB〜16GB以上を強く推奨します。

WindowsユーザーならRTX 3060（12GB版）やRTX 4060 Ti（16GB版）がコスパ最高の選択肢になります。
私はRTX 4090を2枚挿していますが、これは特殊な例なので、まずは1枚のGPUで「VRAMにモデルが収まるか」を基準に選んでください。
Macの場合はユニファイドメモリがVRAMとして機能するため、メモリ32GB以上のモデルを選ぶと中規模モデルも余裕を持って動かせます。

料金については、電気代以外は完全に無料です。
クラウドLLMのように1トークンいくらという課金を気にせず、数万行のコードを流し込んでリファクタリングさせるような使い方が可能になります。
もしスペックが足りない場合は、中古のRTX 3060 12GBを探すのが、最も安価に「使える環境」を手に入れる近道です。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、LM StudioやJanなど他にもありますが、私は「Ollama + Open WebUI」の組み合わせがベストだと確信しています。
理由は、Ollamaが「モデル管理のバックエンド」として極めて軽量かつ安定しており、Open WebUIが「ChatGPTと遜色ないインターフェース」を提供してくれるからです。

特にOpen WebUIは、RAG（ドキュメント読み込み）機能やプロンプトのテンプレート管理、マルチユーザー対応など、実務で必要な機能が標準で備わっています。
エンジニアが自分の開発機で動かすだけでなく、社内サーバーに立ててチームに共有するといった運用にも耐えうる拡張性があります。
この構成に慣れておけば、将来的にAPI経由で自作アプリと連携させる際も、バックエンドが共通なので移行が非常にスムーズです。

## Step 1: 環境を整える

まずは、LLMの推論エンジンとなるOllamaをインストールします。

```bash
# Mac / Linuxの場合
curl -fsSL https://ollama.com/install.sh | sh
```

Windowsの場合は、Ollamaの公式サイト（ollama.com）からインストーラーをダウンロードして実行してください。
インストール後、ターミナルで以下のコマンドを叩き、モデルがダウンロードできるか確認します。

```bash
# Llama 3 (8B) モデルをダウンロードして起動
ollama run llama3
```

Ollamaはデフォルトで11434ポートで待機します。
このエンジンは「モデルの重みをメモリにロードし、リクエストに応じて回答を生成する」役割に特化しています。
CUI（コマンドライン）だけで十分という人はこれだけでも使えますが、画像生成やファイル添付を考慮するとGUIが必要です。

⚠️ **落とし穴:** WindowsでWSL2を使用している場合、GPUが正しく認識されないことがあります。
`nvidia-smi`コマンドでGPUが見えているか確認してください。見えない場合は、NVIDIA Container Toolkitのインストールが必要です。

## Step 2: 基本の設定

次に、GUI部分であるOpen WebUIをDockerで構築します。
Python環境を汚さず、依存関係のトラブルを避けるためにDockerを使うのが正解です。

```bash
# DockerでOpen WebUIを起動（GPU支援なしの場合、またはMacの場合）
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main

# NVIDIA GPUを使用する場合
docker run -d -p 3000:8080 --gpus all --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:cuda
```

ここで重要なのが `--add-host=host.docker.internal:host-gateway` フラグです。
これにより、Dockerコンテナの中からホストマシン上で動いているOllama（11434ポート）にアクセスできるようになります。
これがないと、UIは立ち上がっても「モデルが見つかりません」というエラーで止まってしまいます。

起動後、ブラウザで `http://localhost:3000` にアクセスします。
最初のログイン画面でアカウント作成を求められますが、これはローカルに保存されるだけなので、好きなメールアドレスとパスワードで登録してください。

## Step 3: 動かしてみる

ログインしたら、左上の設定アイコンから「Settings」→「Connections」を開きます。
Ollama API URLが `http://host.docker.internal:11434` になっていることを確認してください。
正しく接続されていれば、トップ画面のモデル選択プルダウンに、先ほどコマンドラインで落とした `llama3` が表示されます。

適当な質問を投げてみましょう。

```bash
# 入力例
Pythonで、指定したディレクトリ内のファイルをサイズ順に並べ替えるスクリプトを書いて。
```

### 期待される出力

```python
import os

def list_files_by_size(directory):
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    files.sort(key=lambda x: os.path.getsize(x), reverse=True)

    for file in files:
        print(f"{os.path.basename(file)}: {os.path.getsize(file)} bytes")

list_files_by_size('.')
```

レスポンス速度に注目してください。
私の環境（RTX 4090）では一瞬ですが、RTX 3060クラスでも日本語で秒間15〜20トークン程度は出ます。
このスピード感が得られない場合は、VRAMからメインメモリにはみ出している（オフロードに失敗している）可能性があります。

## Step 4: 実用レベルにする

単なるチャットで終わらせないために、特定のタスクに特化した「Modelfile」を作成します。
例えば、私は「SIer時代の厳しいコードレビュー」を再現する専用モデルを作っています。
Open WebUIの「Workspace」→「Models」から「Create a model」を選択し、以下のような設定を入力します。

```dockerfile
# Base Model
FROM llama3

# System Prompt
SYSTEM """
あなたは非常に厳格なシニアエンジニアです。
提出されたコードに対し、パフォーマンス、可読性、セキュリティの観点から容赦なく指摘を行ってください。
回答は必ず日本語で行い、修正後のコードも提示してください。
"""

# Parameters
PARAMETER temperature 0.2
PARAMETER top_p 0.9
```

`temperature`（温度感）を0.2まで下げているのは、コードレビューにおいてAIの「創作性」は不要だからです。
低く設定することで、同じコードに対して常に安定した指摘を返させることができます。
これを「コードレビュアー君」として保存しておけば、いつでもワンクリックで専門的なフィードバックが得られるようになります。

また、Open WebUIの「Documents」機能を使って、社内のPDFマニュアルなどをアップロードしてみてください。
「#」を入力してからファイル名を選ぶだけで、そのドキュメントの内容に基づいたRAG（検索拡張生成）が簡単に実現できます。
外部クラウドに社外秘情報を投げたくない業務において、これが最強の解決策になります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error | DockerからOllamaが見えていない | host.docker.internalの設定を再確認する |
| 生成速度が異常に遅い | CPUで推論している | GPUドライバを最新にし、CUDA版Dockerイメージを使う |
| 日本語が不自然 | モデルの学習データ不足 | Llama 3の日本語強化版や、Qwen2 7Bなどを試す |

## 次のステップ

ここまでできれば、あなたのPCは「プライベートなAI研究所」に進化しました。
次にやるべきことは、用途に応じたモデルの使い分けです。
コーディングなら `DeepSeek-Coder`、一般的な日本語の対話なら `Gemma 2` や `Qwen 2` を `ollama pull` コマンドで追加してみてください。

さらに、Open WebUIのAPI機能を使えば、これをバックエンドにして「自社専用のAIチャットツール」を作ることも可能です。
私はPythonの `requests` ライブラリを使って、ローカルLLMに大量のログファイルを解析させ、異常検知を自動化するスクリプトを運用しています。
ローカルLLMは「遅い」「精度が低い」と言われた時代は終わりました。
今のハードウェアと最適化技術なら、実務の相棒として十分なパフォーマンスを発揮してくれます。

## よくある質問

### Q1: ノートPCでも動きますか？

ゲーミングノート（RTX 3050等搭載）やMacBook Air（M1以降、メモリ16GB以上）なら十分動きます。ただし、長時間動かすとファンがフル回転して熱を持つので、冷却台などの対策を検討してください。

### Q2: 4bit量子化モデルって何ですか？

モデルの重みを圧縮してメモリ消費を抑えたものです。Ollamaが提供しているモデルの多くはデフォルトで4bit量子化されており、精度を大きく落とさずにVRAM消費を1/4程度に抑えています。初心者はこれをそのまま使えば問題ありません。

### Q3: 複数のGPUを搭載している場合、どうなりますか？

Ollamaは自動的に複数のGPUを認識して、モデルを分割してロードしてくれます。例えば、VRAM 8GBのカードが2枚あれば、合計16GBのモデルを動かせる可能性があります。設定で特定のGPUだけを使うように制限することも可能です。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のChatGPT環境を作る方法](/posts/2026-05-31-ollama-openwebui-local-llm-setup-guide/)
- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-06-28-ollama-open-webui-local-llm-tutorial/)
- [ローカルLLM構築入門 OllamaとPythonでAIを自前運用する方法](/posts/2026-06-02-ollama-python-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "ノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ゲーミングノート（RTX 3050等搭載）やMacBook Air（M1以降、メモリ16GB以上）なら十分動きます。ただし、長時間動かすとファンがフル回転して熱を持つので、冷却台などの対策を検討してください。"
      }
    },
    {
      "@type": "Question",
      "name": "4bit量子化モデルって何ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデルの重みを圧縮してメモリ消費を抑えたものです。Ollamaが提供しているモデルの多くはデフォルトで4bit量子化されており、精度を大きく落とさずにVRAM消費を1/4程度に抑えています。初心者はこれをそのまま使えば問題ありません。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のGPUを搭載している場合、どうなりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaは自動的に複数のGPUを認識して、モデルを分割してロードしてくれます。例えば、VRAM 8GBのカードが2枚あれば、合計16GBのモデルを動かせる可能性があります。設定で特定のGPUだけを使うように制限することも可能です。 ---"
      }
    }
  ]
}
</script>
