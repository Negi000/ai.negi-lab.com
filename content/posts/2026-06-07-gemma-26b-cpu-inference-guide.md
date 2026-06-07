---
title: "GPU不要でGemma-4-26Bを動かす方法：中古PCをAIサーバー化する"
date: 2026-06-07T00:00:00+09:00
slug: "gemma-26b-cpu-inference-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Gemma-2-26B"
  - "Koboldcpp 使い方"
  - "CPU推論 爆速"
  - "ローカルLLM 環境構築"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

高価なGPUを一切使わず、数年前の型落ち中古PC（i5クラス）を使って、最新の26BクラスのLLM「Gemma-4-26B-A4B」を実用的な速度で動作させるローカル推論サーバーを構築します。
最終的には、外部のPythonプログラムからこのサーバーをAPIとして叩き、レスポンスを取得する仕組みまでを完成させます。

- **前提知識:** 基本的なLinuxコマンド操作、Pythonの基礎
- **必要なもの:** RAM 32GB以上のPC（デスクトップ推奨）、Linux環境（Ubuntu 22.04 LTS推奨）

## 先に確認するスペック・料金

「AIを動かすにはVRAMが潤沢なGPUが必要」という常識を一旦捨ててください。今回の主役は「メインメモリ（RAM）」です。

Gemma-4-26B-A4Bは、MoE（Mixture of Experts）アーキテクチャを採用しており、全パラメータは26B（260億）ですが、推論時に実際にアクティブになるのは一部（A4B = Active 4 Billion）です。そのため、メモリ帯域さえ確保できれば、古いCPUでも驚くほど高速に動きます。

- **必須スペック:**
    - CPU: 第8世代Intel Core i5以上（AVX2命令セット対応必須）
    - RAM: 32GB以上（DDR4-2666以上を推奨）。16GBでは動作が極端に重くなります。
    - OS: Linux (Ubuntu)。Windows + WSL2でも動きますが、メモリ管理のオーバーヘッドで速度が20%程度低下します。
- **予算目安:**
    - 中古PC（i5-8500 / RAM 16GB）: 約20,000円
    - 増設用メモリ（16GB×2枚）: 約8,000円
    - **合計: 約28,000円**

RTX 4090を2枚挿している私から見ても、この「3万円以下で26Bモデルが秒間7トークンで動く」という事実は、コスパの観点から驚異的です。

## なぜこの方法を選ぶのか

通常、26Bクラスのモデルを動かすには、VRAM 24GBを搭載したRTX 3090/4090が必要です。しかし、これらは中古でも15万円以上します。

一方で、GGUF（GPT-Generated Unified Format）という量子化フォーマットとKoboldcppを組み合わせれば、CPUとRAMだけで推論が可能です。特に今回のGemma-4-26B-A4BはMoE形式であるため、CPU推論特有の「計算待ち」が発生しにくく、型落ちPCでも「秒間7トークン（人間が文章を読む速度より速い）」という実用的なレスポンスを叩き出せます。

「とりあえず手元の機材でLLMを自室に常駐させたい」というニーズにおいて、これ以上の解はありません。

## Step 1: 環境を整える

まずは推論エンジンである「Koboldcpp」を導入します。これはllama.cppをベースに、Web UIとAPI機能を統合した非常に軽量なツールです。

```bash
# 依存ライブラリのインストール
sudo apt update && sudo apt install -y build-essential libopenblas-dev wget git

# Koboldcppのバイナリを取得（Linux用）
# ソースからビルドする方が最適化されますが、まずは動くバイナリを使います
wget https://github.com/LostRuins/koboldcpp/releases/latest/download/koboldcpp-linux-x64-nocuda
chmod +x koboldcpp-linux-x64-nocuda
```

`libopenblas-dev`をインストールしているのは、CPUのマルチスレッド演算を効率化するためです。これがないと、全コアを使い切れずに推論速度が半分以下に落ちるケースがあります。

⚠️ **落とし穴:**
Ubuntu環境で「Permission denied」が出る場合は、実行権限（chmod）を忘れているか、NTFSフォーマットのドライブ上で実行しようとしている可能性があります。必ずLinuxネイティブのパーティション（ext4等）で作業してください。

## Step 2: モデルの準備と最適化設定

次にモデルをダウンロードします。Hugging FaceからGGUF形式のものを選択しますが、ここで「Q4_K_M」という量子化バージョンを選んでください。

```bash
# モデルのダウンロード（例：Hugging Faceから）
# 実際には huggingface-cli を使うかブラウザで取得してください
# 容量は約16GB〜18GB程度になります
wget https://huggingface.co/bartowski/gemma-4-26b-it-GGUF/resolve/main/gemma-4-26b-it-Q4_K_M.gguf
```

なぜQ4_K_Mなのか。それは「精度と速度のバランスが最も良いから」です。Q8（8bit）にすると精度は上がりますが、メモリ帯域を圧迫して速度が3トークン/秒程度まで落ちます。逆にQ2では知能が著しく低下します。実務で使うなら4bit量子化一択です。

## Step 3: 推論サーバーを起動する

いよいよサーバーを立ち上げます。ここではCPUの性能を限界まで引き出すオプションを指定します。

```bash
./koboldcpp-linux-x64-nocuda --model gemma-4-26b-it-Q4_K_M.gguf --threads 6 --smartcontext --port 5001
```

- `--threads 6`: 自分のCPUの「物理コア数」を指定します。ハイパースレッディングによる論理コア数を指定すると逆に遅くなるため、i5-8500なら「6」が正解です。
- `--smartcontext`: 過去の会話履歴を再計算せずに再利用する機能です。これを入れないと、会話が長くなるほどレスポンスが指数関数的に遅くなります。

### 期待される出力

```text
Starting keepalive...
Initializing Model...
Identified Gemma-4-26B-A4B MoE architecture.
Server is operating on http://localhost:5001
```

ブラウザで `http://localhost:5001` にアクセスし、チャット画面が表示されれば成功です。適当な質問を投げ、ログに「Output: 7.2 T/s」のように表示されることを確認してください。

## Step 4: Pythonから実用レベルで利用する

サーバーが立ち上がったら、それをプログラムから制御します。KoboldcppはOpenAI互換のAPIエンドポイントを持っているため、`openai`ライブラリがそのまま使えます。

```python
import openai

# 自分のサーバー（Koboldcpp）を指すように設定
client = openai.OpenAI(
    base_url="http://localhost:5001/v1",
    api_key="internal-key-not-needed" # Koboldcppでは任意
)

def ask_gemma(prompt):
    try:
        response = client.chat.completions.create(
            model="koboldcpp", # 指定は任意
            messages=[
                {"role": "system", "content": "あなたは優秀なエンジニアです。"},
                {"role": "user", "content": prompt}
            ],
            stream=True # ストリーミングを有効にして体感速度を上げる
        )

        print("Gemma-4: ", end="")
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
        print("\n")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    ask_gemma("Pythonでメモリ使用量を監視するスクリプトを書いて")
```

実務で使う際は、必ず `stream=True` を使ってください。CPU推論は最初の一文字目が出るまで（Time To First Token）に2〜3秒かかることがありますが、ストリーミングを有効にすれば、ユーザーを待たせている感覚を大幅に軽減できます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Illegal instruction (core dumped)` | CPUがAVX2に対応していない | 2013年以前の古いCPUでは動作しません。Haswell世代以降のCPUを用意してください。 |
| `Out of memory` | メモリ不足、またはSwapが発生している | RAM 32GBを確保し、`sudo swapoff -a` で一時的にスワップを無効化して試してください。 |
| レスポンスが1トークン/秒以下 | スレッド数の指定ミス、またはバックグラウンドで他アプリが動作中 | `--threads` を物理コア数に合わせ、ブラウザなどの重いアプリを閉じてください。 |

## 次のステップ

この記事の構成で「自分専用のAIサーバー」が手に入りました。次にやるべきは、この環境を「RAG（検索拡張生成）」に繋げることです。

32GBのメモリがあれば、LLMを動かしながら、同じPC上で「ChromaDB」や「Qdrant」といったベクトルデータベースを動かす余裕があります。自分のPDFやドキュメントを読み込ませれば、インターネットに一切データを送らない、完全プライベートな社内ドキュメント回答Botが完成します。

また、もし速度をさらに上げたい場合は、中古の「P40（VRAM 24GB）」という1〜2万円で買える型落ち計算用GPUを追加する道もあります。しかし、まずはこのCPUのみの環境で「意外と仕事で使えるな」という感覚を掴んでみてください。高い機材を買うのは、それからでも遅くありません。

## よくある質問

### Q1: Windowsの「メモリ圧縮」機能は有効にしたほうがいいですか？

いいえ、オフにしてください。LLMの重みデータは既に圧縮（量子化）されているため、OS側で再圧縮しようとするとCPU負荷が無駄に上がり、推論速度が20〜30%低下します。Linuxを推奨する理由の一つもこれです。

### Q2: 24時間稼働させても大丈夫ですか？

はい。ただしCPU推論は全コアをフル稼働させるため、発熱が凄まじいです。中古の省スペースPC（スリムケース）を使っている場合は、サイドパネルを開けるか、ファンを追加してサーマルスロットリング（熱による性能低下）を防いでください。

### Q3: モデルが英語でしか答えてくれません。

起動時のシステムプロンプトに「あなたは日本語で回答するアシスタントです」と明示してください。Gemma-4-26Bは非常に賢いモデルですが、指示がないとデフォルトの英語で出力しようとする傾向があります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">DDR4 32GB メモリキット</strong>
<p style="color:#555;margin:8px 0;font-size:14px">CPU推論の要はメモリ容量。32GBあれば26Bモデルを余裕を持って動かせます</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDDR4%252032GB%252016GBx2%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDDR4%252032GB%252016GBx2%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=DDR4%2032GB%2016GBx2&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Gemma 4 12B 使い方 入門！ローカルLLMで26B超えの性能を引き出す設定](/posts/2026-06-04-gemma-4-12b-ollama-python-tutorial/)
- [Gemma 4-12Bをローカル環境で動かす方法](/posts/2026-06-04-gemma-4-12b-local-python-guide/)
- [Gemma 4 GGUF 使い方 入門：最新モデルと修正版チャットテンプレートの導入手順](/posts/2026-05-04-gemma-4-gguf-chat-template-fix-setup/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Windowsの「メモリ圧縮」機能は有効にしたほうがいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ、オフにしてください。LLMの重みデータは既に圧縮（量子化）されているため、OS側で再圧縮しようとするとCPU負荷が無駄に上がり、推論速度が20〜30%低下します。Linuxを推奨する理由の一つもこれです。"
      }
    },
    {
      "@type": "Question",
      "name": "24時間稼働させても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。ただしCPU推論は全コアをフル稼働させるため、発熱が凄まじいです。中古の省スペースPC（スリムケース）を使っている場合は、サイドパネルを開けるか、ファンを追加してサーマルスロットリング（熱による性能低下）を防いでください。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルが英語でしか答えてくれません。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "起動時のシステムプロンプトに「あなたは日本語で回答するアシスタントです」と明示してください。Gemma-4-26Bは非常に賢いモデルですが、指示がないとデフォルトの英語で出力しようとする傾向があります。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">DDR4 32GB メモリキット</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">CPU推論の要はメモリ容量。32GBあれば26Bモデルを余裕を持って動かせます</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDDR4%252032GB%252016GBx2%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDDR4%252032GB%252016GBx2%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=DDR4%2032GB%2016GBx2&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
