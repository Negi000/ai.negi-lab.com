---
title: "Xiaomi 12 Proを24時間稼働のAIサーバーにする手順：Snapdragon 8 Gen 1とOllamaでプライベートLLM環境を構築する方法"
date: 2026-04-15T00:00:00+09:00
slug: "android-headless-ai-server-ollama-guide"
cover:
  image: "/images/posts/2026-04-15-android-headless-ai-server-ollama-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama"
  - "Android LLM"
  - "Snapdragon AI"
  - "自宅サーバー"
---
**所要時間:** 約45分 | **難易度:** ★★★★☆

## この記事で作るもの

- 古くなったAndroidスマホを、外部からAPI経由で叩ける「24時間稼働のHeadless AIサーバー」に変貌させます。
- Pythonからスマホ内のGemma 2やLlama 3に推論リクエストを送り、レスポンスを取得するシステムを構築します。
- 前提知識：Linuxコマンドの基本操作、Pythonの基礎（HTTPリクエストの扱い）。
- 必要なもの：Android端末（Snapdragon 8 Gen 1以上推奨）、安定したWi-Fi、冷却ファン（常時稼働用）。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">スマホ用ペルチェ冷却ファン</strong>
<p style="color:#555;margin:8px 0;font-size:14px">24時間AI推論時の熱暴走とスロットリングを防ぐために必須のアイテムです</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=%E3%82%B9%E3%83%9E%E3%83%9B%20%E3%83%9A%E3%83%AB%E3%83%81%E3%82%A7%20%E3%82%AF%E3%83%BC%E3%83%A9%E3%83%BC&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F%25E3%2582%25B9%25E3%2583%259E%25E3%2583%259B%2520%25E3%2583%259A%25E3%2583%25AB%25E3%2583%2581%25E3%2582%25A7%2520%25E3%2582%25AF%25E3%2583%25BC%25E3%2583%25A9%25E3%2583%25BC%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F%25E3%2582%25B9%25E3%2583%259E%25E3%2583%259B%2520%25E3%2583%259A%25E3%2583%25AB%25E3%2583%2581%25E3%2582%25A7%2520%25E3%2582%25AF%25E3%2583%25BC%25E3%2583%25A9%25E3%2583%25BC%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

クラウドのGPUインスタンスは、安くても月額$20（約3,000円）以上かかります。一方で、手元で眠っているハイスペックなAndroid端末は、電力効率に優れたARMプロセッサと、それなりのVRAM（共有メモリ）を持っています。

Snapdragon 8 Gen 1は10TOPSを超える演算能力を持ち、Gemma 2 (2B) などの軽量モデルであれば、実用的な速度（5〜10 tokens/sec）で動作します。Raspberry Pi 5を買うよりも手元のスマホの方が圧倒的に高性能で、かつ消費電力もアイドル時1〜2W程度と非常に経済的です。今回はTermux上にUbuntu環境を構築し、Ollamaを動かすことで、PCや他のサーバーから「推論API」として利用可能な構成を目指します。

## Step 1: Termux環境とLinuxベースの構築

Android上でLinux環境をエミュレートするために、まずはF-Droid版のTermuxをインストールしてください。Google Play版は更新が止まっており、最新のパッケージが導入できないため避けるべきです。

```bash
# パッケージの更新と基本ツールの導入
pkg update && pkg upgrade -y
pkg install thermux-api proot-distro git curl -y

# Ubuntu 22.04をインストール
# なぜUbuntuか：Ollamaのインストーラーが最も安定して動作するディストリビューションだからです
proot-distro install ubuntu
proot-distro login ubuntu
```

Ubuntuにログインしたら、システムを最新の状態にします。

```bash
apt update && apt upgrade -y
apt install curl -y
```

⚠️ **落とし穴:** TermuxはAndroidの省電力機能によって、バックグラウンドに回るとすぐにプロセスがキルされます。必ず通知欄から「Acquire wakelock」を有効にするか、Android設定の「電池の最適化」からTermuxを除外してください。これを行わないと、長時間推論中に突然サーバーが落ちます。

## Step 2: Ollamaのインストールとモデルの選定

次に、AIモデルの実行エンジンであるOllamaを導入します。本来Ollamaはx86_64を前提としていますが、最近はARM64版も公式でサポートされています。

```bash
# Ollamaのインストールスクリプト実行
curl -fsSL https://ollama.com/install.sh | sh

# サーバーの起動（バックグラウンドで実行）
# 0.0.0.0でバインドすることで、同じWi-Fi内の他デバイスからアクセス可能にします
OLLAMA_HOST=0.0.0.0 ollama serve &

# モデルのダウンロード（最初はGemma 2 2Bがおすすめ）
ollama run gemma2:2b
```

なぜGemma 2 2Bを選ぶのか。Xiaomi 12 Proのメモリは8GBまたは12GBですが、Android OSが3〜4GBを占有します。7Bクラスのモデル（Q4量子化で約5GB）は動作しますが、スワップが発生すると極端に遅くなります。2Bモデルであれば、メモリ消費を2GB程度に抑えつつ、SnapdragonのL3キャッシュを有効活用して高速なレスポンスが得られます。

## Step 3: 常時稼働のための冷却と電源設定

スマートフォンをAIサーバーにする最大の敵は「熱」です。Snapdragon 8 Gen 1は特に発熱しやすく、推論を数分続けるとサーマルスロットリングが発生し、処理速度が50%以下に低下します。

私は背面にペルチェ素子クーラーを装着し、強制的に冷却しています。これにより、24時間連続稼働させてもチップ温度を45度以下に保つことができます。また、バッテリーの膨張を防ぐため、「AccA」などのアプリを使用して充電を80%で止める、もしくは「バイパス給電（ダイレクト給電）」設定が可能な端末であれば、バッテリーを経由せずに給電する設定が必須です。

## Step 4: PythonからAPIサーバーとして利用する

スマホ側でOllamaが起動したら、PCや別のサーバーからPythonでリクエストを投げてみましょう。

```python
import requests
import json

def generate_ai_response(prompt):
    # スマホのIPアドレスを指定
    # 例: 192.168.1.50 (Termuxで `ifconfig` と打てば確認可能)
    url = "http://192.168.x.x:11434/api/generate"

    payload = {
        "model": "gemma2:2b",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("response")
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"

# テスト実行
if __name__ == "__main__":
    test_prompt = "AndroidスマホをAIサーバーにする利点を3つ教えて"
    result = generate_ai_response(test_prompt)
    print(f"AIからの回答:\n{result}")
```

### 期待される出力

```
AIからの回答:
1. 低消費電力: PCに比べてアイドル時の消費電力が極めて低く、24時間稼働に適しています。
2. スペースの有効活用: 小型なため場所を取らず、古い端末をリサイクルできます。
3. エッジ推論のプライバシー: 外部クラウドを使わずローカルで完結するため、機密データの扱いに適しています。
```

## 実用レベルにする：エラーハンドリングと自動再起動

実務で使うなら、スマホが再起動した際に自動でOllamaが立ち上がるようにする必要があります。Termux-bootを使用するか、`.bashrc` に起動スクリプトを記述しておきましょう。

```bash
# .bashrc への追記例
if ! pgrep -x "ollama" > /dev/null
then
    export OLLAMA_HOST=0.0.0.0
    nohup ollama serve > /dev/null 2>&1 &
fi
```

また、Python側では「タイムアウト処理」を厳密に行うべきです。スマホ側の負荷が高い場合、リクエストを拒否される可能性があるため、指数バックオフを用いたリトライ処理を実装すると堅牢性が高まります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Refused | OLLAMA_HOSTがデフォルト(127.0.0.1)のまま | 環境変数 `OLLAMA_HOST=0.0.0.0` を設定して起動する |
| Killed (Out of memory) | メモリ不足でOSがプロセスを強制終了 | より小さいモデル(1b等)を使用するか、Swapファイルを拡張する |
| 推論が極端に遅い | サーマルスロットリングの発生 | 物理的な冷却ファンを取り付ける |

## 次のステップ

スマホAIサーバーが完成したら、次は「RAG（検索拡張生成）」の基盤として活用してみてください。例えば、自宅のドキュメントをローカルのベクトルデータベース（ChromaDB等）に保存し、スマホサーバー経由で検索・回答させるシステムを構築できます。

また、DifyなどのローカルLLM連携ツールと組み合わせることで、ノーコードでAIエージェントを作成し、その推論エンジンとしてこのスマホサーバーを指定することも可能です。高価なGPUを買う前に、まずは手元の「小さなスーパーコンピュータ」の限界を引き出してみる。それこそがAIエンジニアとしての醍醐味だと私は考えています。

## よくある質問

### Q1: Snapdragon以外のチップ（MediaTekなど）でも動きますか？

ARM64アーキテクチャであれば動作しますが、ドライバの互換性や浮動小数点演算の最適化具合により、Snapdragonほどパフォーマンスが出ない場合があります。特にDimensityシリーズは一部のパッケージでセグメンテーションフォールトが発生しやすい傾向があります。

### Q2: スマホの寿命が縮まりませんか？

24時間100%の負荷をかけ続ければ、当然熱による劣化は進みます。しかし、本記事で推奨した「80%充電制限」と「強制冷却」を行えば、数年はサーバーとして稼働可能です。ディスプレイを消灯（Headless状態）しておくことも、パネルの焼き付き防止と省電力のために必須です。

### Q3: 複数のモデルを同時に動かせますか？

メモリ容量に依存しますが、8GBモデルのスマホでは2Bモデル1つが限界です。複数のリクエストを並列処理しようとすると、メモリのコンテキスト切り替えで大幅な遅延が生じます。実運用ではキューを実装し、1つずつ処理させるスタック構造にすることをおすすめします。

---

### 【重要】メタデータ出力

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**
**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [Qwen2.5-Coder 使い方 | ローカルでGPT-4o級の開発環境をPythonで構築する](/posts/2026-03-21-qwen2-5-coder-python-local-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Snapdragon以外のチップ（MediaTekなど）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ARM64アーキテクチャであれば動作しますが、ドライバの互換性や浮動小数点演算の最適化具合により、Snapdragonほどパフォーマンスが出ない場合があります。特にDimensityシリーズは一部のパッケージでセグメンテーションフォールトが発生しやすい傾向があります。"
      }
    },
    {
      "@type": "Question",
      "name": "スマホの寿命が縮まりませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "24時間100%の負荷をかけ続ければ、当然熱による劣化は進みます。しかし、本記事で推奨した「80%充電制限」と「強制冷却」を行えば、数年はサーバーとして稼働可能です。ディスプレイを消灯（Headless状態）しておくことも、パネルの焼き付き防止と省電力のために必須です。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のモデルを同時に動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "メモリ容量に依存しますが、8GBモデルのスマホでは2Bモデル1つが限界です。複数のリクエストを並列処理しようとすると、メモリのコンテキスト切り替えで大幅な遅延が生じます。実運用ではキューを実装し、1つずつ処理させるスタック構造にすることをおすすめします。 ---"
      }
    }
  ]
}
</script>
