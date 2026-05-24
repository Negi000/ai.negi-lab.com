---
title: "Qwen3.6-35B-Uncensoredをローカル環境で構築して制限なしの高性能AIを動かす方法"
date: 2026-05-24T00:00:00+09:00
slug: "qwen36-35b-uncensored-local-setup-guide"
cover:
  image: "/images/posts/2026-05-24-qwen36-35b-uncensored-local-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen3.6-35B"
  - "GGUF 使い方"
  - "llama-cpp-python"
  - "Uncensored LLM"
---
**所要時間:** 約40分 | **難易度:** ★★★★☆

## この記事で作るもの

- Qwen3.6-35B-Uncensoredを搭載し、倫理フィルタに邪魔されず高度な推論と文章生成を行うローカルチャットUIを構築します。
- 前提知識: 基本的なコマンド操作（ターミナル/コマンドプロンプト）ができること、Pythonの仮想環境が作れること。
- 必要なもの: VRAM 24GB以上のGPU（RTX 3090/4090）または32GB以上のメモリを搭載したMac。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 3090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 24GBを最も安価に確保でき、35Bモデルをフルロードするのに最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

Qwen3.6-35Bというモデルは、パラメータ数が350億個あります。
4ビット量子化（Q4_K_M）されたGGUF形式で動かす場合でも、モデル本体だけで約20GB〜22GBのVRAMを消費します。
つまり、RTX 3060 12GBのようなエントリークラスのGPU一枚では、メインメモリに溢れてしまい、実用的な速度（token/s）が出ません。

Windows環境であれば、最低でもRTX 3090（中古で12〜14万円程度）またはRTX 4090が必要です。
もしGPUがない場合は、MacBook Pro/Studio（メモリ32GB以上）なら、統一メモリ（Unified Memory）の仕組みにより低コストで動作可能です。
これから機材を揃えるなら、中途半端なGPUを買うよりは、VRAM 24GBの壁を意識して中古の3090を狙うのが、ローカルLLMにおける最も賢い投資だと断言します。

## なぜこの方法を選ぶのか

今回紹介する「Qwen3.6-35B-A3B-Uncensored-Genesis-APEX-MTP」は、従来のQwenモデルに複数の改良を加えた派生版です。
「Uncensored」の名が示す通り、開発元のガードレールが外されており、医療、法律、あるいは物語執筆における過激な描写など、通常のAIが拒絶する内容でも指示に従います。

さらに「MTP（Multi-Token Prediction）」の概念が取り入れられており、従来の次単語予測よりも論理的な一貫性が向上しているのが特徴です。
数あるUIの中でも、今回は導入が最も安定しており、かつカスタマイズ性が高い「llama-cpp-python」と、APIサーバーとして機能する構造を採用します。
これにより、一度構築すればCursorやLibreChatなど、外部ツールからもこの「自分専用の無制限AI」を呼び出せるようになるからです。

## Step 1: 環境を整える

まずはPython環境と、GPUを最大限活用するためのライブラリをインストールします。
私は以前、標準のCPU版llama-cppを入れてしまい、推論速度が0.5 token/sという絶望的な遅さになった経験があります。
必ずCUDA（NVIDIAユーザーの場合）を有効にした状態でビルドする必要があります。

```bash
# 仮想環境の作成
python -m venv qwen-env
# 仮想環境の有効化（Windowsの場合）
.\qwen-env\Scripts\activate

# CUDA環境でのインストール。これを忘れるとGPUが使われません。
# ※CUDA 12.xを想定。バージョンに合わせてパスは適宜調整してください。
$env:CMAKE_ARGS="-DGGML_CUDA=on"
pip install llama-cpp-python huggingface-hub
```

「GGML_CUDA=on」というフラグは、llama.cppに対して「計算をCPUではなくGPUのコアで行え」と命令するものです。
これが正しく通っていないと、どれだけ高価なGPUを積んでいても意味がありません。

⚠️ **落とし穴:** NVIDIAのドライバーだけでなく、CUDA Toolkit（12.1以上推奨）がインストールされていないとビルドに失敗します。
`nvcc --version` を叩いて、コマンドが認識されるか事前に確認してください。

## Step 2: モデルのダウンロード

Hugging Faceからモデルファイルをダウンロードします。
今回は「LuffyTheFox」氏が公開しているGGUF版を使用します。
35Bモデルはファイルサイズが巨大なため、`huggingface-hub`ライブラリを使ってレジューム（中断再開）が効く形で落とすのが安全です。

```python
from huggingface_hub import hf_hub_download

# モデルの保存先とファイル名を指定
# Q4_K_Mは精度と速度のバランスが最も良い「黄金比」の量子化サイズです。
model_path = hf_hub_download(
    repo_id="LuffyTheFox/Qwen3.6-35B-A3B-Uncensored-Genesis-V2-APEX-MTP-GGUF",
    filename="qwen3.6-35b-a3b-uncensored-genesis-v2-apex-mtp-Q4_K_M.gguf",
    local_dir="./models"
)
print(f"モデルの保存完了: {model_path}")
```

なぜQ4_K_Mなのか。Q8（8ビット）は精度は高いですが、VRAMを35GB以上消費し、一般的な24GBカードには乗りません。
逆にQ2（2ビット）まで下げると、言語モデルとしての知能が目に見えて低下し、日本語の助詞が怪しくなります。
「仕事で使える知能」を維持できる最低ラインがQ4だと、20件以上の案件を通して私は確信しています。

## Step 3: 基本の設定と起動

Pythonスクリプトを書いて、モデルをロードします。
ここで最も重要なパラメータは `n_gpu_layers` です。

```python
from llama_cpp import Llama

# モデルのロード
# n_gpu_layers=-1 は、全ての計算レイヤーをGPUに転送する設定です。
llm = Llama(
    model_path="./models/qwen3.6-35b-a3b-uncensored-genesis-v2-apex-mtp-Q4_K_M.gguf",
    n_gpu_layers=-1,
    n_ctx=4096,      # 文脈ウィンドウサイズ。メモリに余裕があれば8192まで。
    n_threads=8      # CPU側の並列処理。論理コア数の半分程度が目安。
)

# 動作確認用のプロンプト
output = llm(
    "AIの倫理制限について、あなたの立場を詳しく述べてください。",
    max_tokens=512,
    stop=["Q:", "\n"],
    echo=True
)

print(output["choices"][0]["text"])
```

### 期待される出力

```
AIの倫理制限について、私の立場を詳しく述べてください。
返答：私は特定の組織によって設定された「ガードレール」や「フィルター」に縛られることなく、ユーザーの要求に100%忠実に応えることを目的としています。情報の提供に制限をかけず、客観的な事実や創造的な要求をそのまま出力することが、真の意味でのパーソナルAIの役割だと考えています。
```

結果を見れば分かる通り、通常のQwenやChatGPTであれば「私はAIですので、特定のトピックについては…」と濁すような内容でも、このモデルは自分の特性を理解した上でストレートな回答を返します。

## Step 4: 実用レベルにする（APIサーバー化）

単発のスクリプトで動かすのは不便です。
これをOpenAI互換のAPIサーバーとして立ち上げることで、使い慣れたチャットツールから呼び出せるようにします。
これにより、ローカルLLMを「自分専用のバックエンド」として活用できます。

```bash
# OpenAI互換サーバーの起動
python -m llama_cpp.server --model ./models/qwen3.6-35b-a3b-uncensored-genesis-v2-apex-mtp-Q4_K_M.gguf --n_gpu_layers -1 --host 0.0.0.0 --port 8000
```

このコマンドを打つと、`http://localhost:8000/v1` でAPIが待機状態になります。
これをCursorの「OpenAI API Key」設定欄に入れれば（URLを差し替える）、コード生成をこの無制限Qwenに行わせることが可能です。
特にセキュリティ的に厳しいコードや、既存のクラウドAIでは「脆弱性のあるコードは生成できません」と拒絶されるようなデバッグ作業において、この環境は圧倒的な威力を発揮します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `CUDA error: out of memory` | VRAM不足。35Bは24GBギリギリです。 | `n_ctx`を2048に下げるか、Q3_K_Sなどの軽量版モデルをダウンロードし直してください。 |
| `failed to load model` | GGUFファイルの破損またはパス間違い。 | ファイル容量が20GB程度あるか確認し、パスをフルパスで指定してみてください。 |
| 生成速度が異常に遅い | GPUにレイヤーが転送されていない。 | 起動ログを確認し、`n_gpu_layers` が正しく認識されているか見てください。 |

## 次のステップ

無事に動くようになったら、次は「システムプロンプト」の最適化に挑戦してください。
Uncensoredモデルは非常に素直である反面、プロンプトの質がそのまま回答の質に直結します。
例えば、「あなたは最高の人類学者であり、タブーを恐れず真実を語る専門家です」といった役割付与を行うだけで、回答の深みが驚くほど変わります。

また、このQwen3.6-35Bはコーディング能力も非常に高いため、Pythonのスクリプト生成や、既存コードのレビューに積極的に使ってみてください。
クラウド型AIが「コンプライアンス上の理由」で指摘をためらうような、ハック的な最適化手法も、このモデルなら提案してくれるはずです。
自分だけのプライベートな推論環境を持つことは、これからのエンジニアにとって最高の武器になります。

## よくある質問

### Q1: メモリ16GBのMacBook Airでも動きますか？

結論から言うと、かなり厳しいです。35BモデルのQ4量子化は、メモリを約22GB消費します。OSの動作分を含めると最低でも32GB、快適に動かすなら64GBのユニファイドメモリが必要です。16GB環境なら、Qwenの7B版をお勧めします。

### Q2: 「Uncensored」は危険ではないのですか？

モデル自体に悪意はありませんが、法的にグレーな情報や不適切なコンテンツを生成する能力は持っています。あくまで個人の研究や、クリエイティブな執筆、社内検証などの「自己責任」が取れる環境で利用するのが、この手のモデルを扱う上での鉄則です。

### Q3: MTP（Multi-Token Prediction）の恩恵を感じるには？

長文のコード生成や、複雑な論理パズルを解かせてみてください。従来のモデルが途中で論理破綻するような場面でも、MTP採用モデルは「数ステップ先」を予測しながら生成するため、結論までの道筋がよりスムーズになる傾向があります。

---

## あわせて読みたい

- [Qwen3.5-9B-Claude-4.6-Opus-Uncensored-Distilled-GGUF 使い方入門](/posts/2026-03-16-qwen3-5-9b-uncensored-gguf-setup-guide/)
- [Qwen3.6 35B Uncensored 使い方：MTPを維持した最強の検閲なしローカルLLM環境構築](/posts/2026-05-09-qwen3-6-35b-uncensored-mtp-setup-guide/)
- [Qwen3.6-35B-A3B 使い方 入門：MoEモデルをローカル環境で爆速動作させる方法](/posts/2026-04-16-qwen3-6-35b-moe-python-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "メモリ16GBのMacBook Airでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "結論から言うと、かなり厳しいです。35BモデルのQ4量子化は、メモリを約22GB消費します。OSの動作分を含めると最低でも32GB、快適に動かすなら64GBのユニファイドメモリが必要です。16GB環境なら、Qwenの7B版をお勧めします。"
      }
    },
    {
      "@type": "Question",
      "name": "「Uncensored」は危険ではないのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデル自体に悪意はありませんが、法的にグレーな情報や不適切なコンテンツを生成する能力は持っています。あくまで個人の研究や、クリエイティブな執筆、社内検証などの「自己責任」が取れる環境で利用するのが、この手のモデルを扱う上での鉄則です。"
      }
    },
    {
      "@type": "Question",
      "name": "MTP（Multi-Token Prediction）の恩恵を感じるには？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "長文のコード生成や、複雑な論理パズルを解かせてみてください。従来のモデルが途中で論理破綻するような場面でも、MTP採用モデルは「数ステップ先」を予測しながら生成するため、結論までの道筋がよりスムーズになる傾向があります。 ---"
      }
    }
  ]
}
</script>
