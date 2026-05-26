---
title: "Qwen3.5 35B A3B 使い方と環境構築ガイド"
date: 2026-05-27T00:00:00+09:00
slug: "qwen35-35b-mtp-local-setup-guide"
cover:
  image: "/images/posts/2026-05-27-qwen35-35b-mtp-local-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen3.5 35B"
  - "MTP"
  - "llama.cpp 使い方"
  - "ローカルLLM 構築"
---
**所要時間:** 約40分 | **難易度:** ★★★★☆

## この記事で作るもの

- Qwen3.5 35B A3B（MTP保持版）をローカル環境で立ち上げ、PythonからAPI経由で高速に推論を行うシステム。
- 35Bという中規模モデルながら、MTP（Multi-Token Prediction）の恩恵で40B〜70Bクラスに匹敵する論理性能を体感できる環境を構築します。
- PythonからOpenAI互換APIサーバーとして呼び出し、実際の業務（コードレビューや長文要約）に即投入できる状態を目指します。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 3090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 24GBを安価に確保し35Bモデルを1枚で完結させる現実解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

Qwen3.5 35Bは「中規模」とはいえ、350億パラメータを持つ巨大なモデルです。
快適に動かすには、VRAM（ビデオメモリ）の量が成否を分けます。
量子化（モデルの軽量化）を行わないFP16状態では約70GBのVRAMが必要になり、H100やA100といったエンタープライズ向けGPUが必須となります。

個人やSOHOレベルで現実的なのは、GGUF形式（Q4_K_Mなど）に量子化されたモデルを使い、VRAM 24GBを搭載したRTX 3090または4090で運用する方法です。
4bit量子化を行えば、モデルサイズは約20GB〜22GB程度に収まるため、24GBのVRAM一枚でコンテキストウィンドウを確保しつつ動作させることが可能です。

Macユーザーであれば、メモリ（ユニファイドメモリ）を32GB以上搭載したM2/M3 Max以降のモデルが推奨です。
VRAMが足りない場合、メインメモリ（RAM）を使って動かすこともできますが、推論速度は1秒間に1〜2トークン程度まで落ち、実用的ではありません。
APIを利用するわけではないため、一度機材を揃えてしまえば月額の利用料金は電気代以外かからないのがローカル運用の最大のメリットです。

## なぜこの方法を選ぶのか

今回のモデル「Qwen3.5 35B A3B uncensored heretic Native MTP Preserved」は、従来のQwenシリーズとは一線を画す特徴を持っています。
特筆すべきは「MTP（Multi-Token Prediction）」が保持されている点です。
通常のLLMは次の一語（1トークン）を予測しますが、MTPは数トークン先まで同時に予測する仕組みで、これにより推論の整合性と速度が飛躍的に向上します。

多くの派生モデルでは、量子化の過程でこのMTPデータが失われがちですが、本モデルはこれを完全に保持しています。
また「Uncensored（検閲解除）」であるため、AI特有の「倫理的な理由でお答えできません」という説教に邪魔されることなく、開発者の指示に100%忠実な回答が得られます。
この「論理性（MTP）」と「自由度（Uncensored）」の両立こそが、業務自動化においてこのモデルを選ぶべき最大の理由です。

## Step 1: 環境を整える

まずはモデルを動かすためのバックエンドとして、最も汎用性が高くMTP対応が進んでいる「llama.cpp」を導入します。

```bash
# リポジトリのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド（CUDA環境：NVIDIA GPU利用の場合）
mkdir build
cd build
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release
```

`-DGGML_CUDA=ON` フラグは、計算をGPUにオフロードするために必須の設定です。
これを忘れるとCPU推論になり、35Bモデルを動かすには絶望的な遅さになります。
ビルドが完了すると、`bin` ディレクトリ内に `llama-server` という実行ファイルが生成されます。

⚠️ **落とし穴:**
CUDA Toolkitのバージョンが古い（12.x未満）と、最新のllama.cppのビルドでエラーが出ることがあります。
また、Windows環境でビルドする場合は、Visual Studioの「C++ によるデスクトップ開発」ワークロードがインストールされているか確認してください。
ここが通らない初心者が非常に多いですが、WSL2（Windows Subsystem for Linux）を使うのが一番トラブルが少ないです。

## Step 2: モデルのダウンロードと配置

次に、Hugging Faceからモデルファイルをダウンロードします。
今回は実用性を重視し、GGUF形式のQ4_K_M（4bit量子化）を使用します。

```bash
# huggingface-cliが入っていない場合はインストール
pip install huggingface_hub

# モデルのダウンロード（特定のブランチやファイルを指定）
# ※リンク先のリポジトリ構造に合わせて適切に指定してください
huggingface-cli download bartowski/Qwen3.5-35B-A3B-uncensored-heretic-GGUF --include "Qwen3.5-35B-A3B-uncensored-heretic-Q4_K_M.gguf" --local-dir ./models
```

ダウンロードする量子化サイズを選ぶ際は、自分のVRAM容量から「マイナス2GB」したサイズを上限にしてください。
24GBのVRAMがあるなら、22GB程度のファイルサイズが限界です。
OSやディスプレイ出力で常に1〜2GBのVRAMが消費されているため、ギリギリのサイズを選ぶとロード時に「Out of Memory（OOM）」で落ちます。

## Step 3: APIサーバーを起動する

モデルの準備ができたら、OpenAI互換のAPIサーバーとして立ち上げます。
これにより、既存のライブラリやCursorなどのエディタから簡単に接続できるようになります。

```bash
./build/bin/llama-server \
  -m ./models/Qwen3.5-35B-A3B-uncensored-heretic-Q4_K_M.gguf \
  --port 8080 \
  --n-gpu-layers 99 \
  --ctx-size 8192 \
  --parallel 1
```

各設定の意図を解説します。
`--n-gpu-layers 99` は、モデルの全レイヤーをGPUにロードする指示です。35Bなら約60〜80レイヤー程度ですが、大きめの数字を入れておけば全ロードされます。
`--ctx-size 8192` は文脈の長さです。35Bクラスなら16kや32kも狙えますが、VRAM消費量が増えるため、まずは8kで安定動作を確認します。
`--parallel 1` は同時リクエスト数です。個人利用なら1で十分であり、メモリを節約できます。

### 期待される出力

起動に成功すると、ターミナルに以下のような表示が出ます。

```
HTTP server listening on http://0.0.0.0:8080
llama_decode: n_past = 0, n_left = 1, n_chunks = 1, n_cur = 1
```

これで、あなたのPCは「自分専用の超高性能GPT」として機能し始めました。

## Step 4: 実用レベルのPythonスクリプトで動かす

それでは、このローカルサーバーに対してPythonから命令を送ってみましょう。
単に「こんにちは」と送るのではなく、実務で使える「複雑なコードの解説」を依頼するスクリプトを作成します。

```python
import openai

# ローカルサーバーの設定
client = openai.OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="sk-no-key-required" # ローカルなので何でもOK
)

def analyze_code(code_snippet):
    try:
        response = client.chat.completions.create(
            model="qwen3.5-35b",
            messages=[
                {"role": "system", "content": "あなたは熟練のシニアエンジニアです。提供されたコードの潜在的なバグと、MTP（Multi-Token Prediction）を意識した最適化案を提示してください。"},
                {"role": "user", "content": f"以下のコードをレビューして：\n\n{code_snippet}"}
            ],
            temperature=0.2, # 実務利用では低めにして決定論的な回答を得る
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

# テスト用の問題のあるコード
sample_code = """
def get_user_data(user_id):
    import sqlite3
    db = sqlite3.connect('users.db')
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cursor.fetchone()
"""

if __name__ == "__main__":
    print("--- レビュー結果 ---")
    result = analyze_code(sample_code)
    print(result)
```

このスクリプトでは、あえてSQLインジェクションの脆弱性があるコードを渡しています。
Qwen3.5 35BはMTPのおかげで、単なるパターンマッチングではなく、文脈から「なぜこれが危険か」を非常に論理的に説明してくれます。
また、`temperature=0.2` に設定しているのは、業務での利用において「もっともらしい嘘（ハルシネーション）」を抑制するためです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `CUDA error: out of memory` | VRAM不足。OSやブラウザがVRAMを消費している。 | `n-gpu-layers` を少しずつ下げて（例: 40）、一部をCPUに逃がす。 |
| `llama_model_load: failed to load model` | ファイルの破損またはGGUFバージョン不一致。 | モデルを再ダウンロードするか、llama.cppを最新版に更新する。 |
| レスポンスが異常に遅い | GPUではなくCPUで推論が走っている。 | 起動ログを確認し `BLAS = 1` または `CUDA = 1` になっているか見る。 |

## 次のステップ

無事にQwen3.5 35Bが動いたら、次は「RAG（検索拡張生成）」への組み込みに挑戦してください。
このモデルは日本語の理解力も非常に高く、かつ35Bというサイズのおかげで、外部知識を注入した際の要約精度が7Bや8Bモデルとは比較にならないほど安定しています。

具体的には、LangChainやLlamaIndexを使って、自分の過去のプロジェクト資料やPDFを読み込ませ、このローカルQwenに「社内専用のドキュメント相談役」をさせるのが最も価値が出る使い方です。
また、RTX 4090を2枚挿している環境であれば、4bitではなく8bit量子化（Q8_0）での運用を試してみてください。
推論の「厚み」がさらに増し、GPT-4に近い手応えを感じられるはずです。

## よくある質問

### Q1: 35Bモデルを12GBのVRAM（RTX 4070等）で動かせますか？

4bit量子化モデル（約20GB）は12GBのVRAMには収まりません。一部のレイヤーをCPUに送れば動きますが、速度は劇的に低下します。その場合は、Qwen2.5 7Bや14Bといった、より小さいモデルをフルGPUロードで動かす方が体験は良くなります。

### Q2: 「Uncensored」モデルは悪意のある回答をしませんか？

「Uncensored」はガードレールが外されているという意味ですが、AI自体に意志があるわけではありません。プロンプトで指示しない限り、勝手に悪意のある回答を生成することはありません。むしろ、業務上のデリケートな話題（医療、法律、セキュリティ等）に対して「お答えできません」という拒絶を回避できるメリットの方が大きいです。

### Q3: MTPが効いているかどうか、どうやって確認すればいいですか？

MTPの効果は、特に「長い推論」において顕著です。コード生成や、論理パズル、複雑な要約を依頼した際に、文の途中で矛盾が生じにくくなっているはずです。また、llama.cppの最新版ではMTPによる投機的サンプリングがサポートされており、対応するフラグ（`--speculative`）を立てることで、推論速度の数値的な向上としても確認できます。

---

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [Qwen3.6 35B Uncensored 使い方：MTPを維持した最強の検閲なしローカルLLM環境構築](/posts/2026-05-09-qwen3-6-35b-uncensored-mtp-setup-guide/)
- [Qwen3.6-35B-A3B 使い方 入門：MoEモデルをローカル環境で爆速動作させる方法](/posts/2026-04-16-qwen3-6-35b-moe-python-guide/)
- [Qwen3.5-35BをVRAM 16GBで爆速動作させるローカルLLM構築術](/posts/2026-02-27-qwen35-35b-local-setup-16gb-vram/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "35Bモデルを12GBのVRAM（RTX 4070等）で動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "4bit量子化モデル（約20GB）は12GBのVRAMには収まりません。一部のレイヤーをCPUに送れば動きますが、速度は劇的に低下します。その場合は、Qwen2.5 7Bや14Bといった、より小さいモデルをフルGPUロードで動かす方が体験は良くなります。"
      }
    },
    {
      "@type": "Question",
      "name": "「Uncensored」モデルは悪意のある回答をしませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "「Uncensored」はガードレールが外されているという意味ですが、AI自体に意志があるわけではありません。プロンプトで指示しない限り、勝手に悪意のある回答を生成することはありません。むしろ、業務上のデリケートな話題（医療、法律、セキュリティ等）に対して「お答えできません」という拒絶を回避できるメリットの方が大きいです。"
      }
    },
    {
      "@type": "Question",
      "name": "MTPが効いているかどうか、どうやって確認すればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MTPの効果は、特に「長い推論」において顕著です。コード生成や、論理パズル、複雑な要約を依頼した際に、文の途中で矛盾が生じにくくなっているはずです。また、llama.cppの最新版ではMTPによる投機的サンプリングがサポートされており、対応するフラグ（--speculative）を立てることで、推論速度の数値的な向上としても確認できます。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>
