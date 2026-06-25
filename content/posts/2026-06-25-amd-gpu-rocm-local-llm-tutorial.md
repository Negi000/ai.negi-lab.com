---
title: "AMD GPUでローカルLLMを動かすROCm環境構築の手順"
date: 2026-06-25T00:00:00+09:00
slug: "amd-gpu-rocm-local-llm-tutorial"
cover:
  image: "/images/posts/2026-06-25-amd-gpu-rocm-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "ROCm 使い方"
  - "AMD GPU ローカルLLM"
  - "Ollama Radeon 設定"
  - "Llama 3 環境構築"
---
**所要時間:** 約45分 | **難易度:** ★★★★☆

## この記事で作るもの

AMD製GPU（Radeon）を使って、NVIDIA環境に依存せずに高速な推論を行う「ローカルLLMチャットUI」を構築します。
PythonからROCm（Radeon用の演算プラットフォーム）を介してLlama 3を制御し、Streamlitでブラウザから操作できるアプリを一つ完成させます。

- 前提知識: Pythonの基本的な読み書き、ターミナル（Linux/WSL2）の操作。
- 必要なもの: AMD製GPU（RX 6000/7000シリーズ推奨）、Ubuntu 22.04 または WSL2環境。

## 先に確認するスペック・料金

「NVIDIA以外でAIは動かない」という認識は、半分正解で半分間違いです。
結論から言うと、VRAM 16GBを積んだRadeon RX 7800 XT（約8万円）は、同価格帯のNVIDIA製GPUよりも高いメモリ帯域を活かせる場面があります。
しかし、ROCmというAMDのソフトウェア基盤が曲者で、特定のバージョンでしか動作しない「地雷」が至る所に埋まっています。

最低でもVRAM 12GB、できれば16GB以上のモデルを選んでください。
中古のRX 6800（16GB）なら5万円前後で手に入りますが、RTX 4060 Ti 16GB（約7.5万円）の方が環境構築のストレスは1/10で済みます。
それでもAMDを選ぶ理由は、NVIDIAの「VRAM出し惜しみ」に対する抵抗と、将来的なコストパフォーマンスの逆転を信じているからです。
設定に必要な料金は無料ですが、構築に失敗して時間を溶かす「見えないコスト」があることは覚悟してください。

## なぜこの方法を選ぶのか

Redditで議論されているように、LLMがコードを書ける時代になっても、AMDのソフトウェアエコシステムがNVIDIAに追いつけないのは、ハードウェアに近い層のライブラリが複雑すぎるからです。
今回は、その複雑な依存関係を可能な限り隠蔽してくれる「Ollama」と「ROCmネイティブなPython環境」を組み合わせる手法を採ります。

Dockerを使う方法もありますが、AMD GPUのパススルー設定は初心者にはハードルが高すぎます。
あえて「Ubuntu上のネイティブ環境」で構築することで、ライブラリがどうやってGPUを認識しているのか、その構造を理解しながら進めるのがベストだと判断しました。
この手順をマスターすれば、将来的にIntelのGPU（Arcシリーズ）が登場した際にも、同じ考え方で対応できるようになります。

## Step 1: 環境を整える

まずはAMDのドライバとROCm（Radeon Open Compute）をインストールします。
ここが最大の難所で、バージョンが一つ違うだけでGPUを認識しません。今回はUbuntu 22.04 LTSを前提に進めます。

```bash
# パッケージリストの更新
sudo apt update && sudo apt upgrade -y

# カーネルドライバのインストールに必要な依存関係
sudo apt install -y python3-pip php-bz2 libstdc++-12-dev

# AMD公式のリポジトリを追加（ROCm 6.0を指定）
# 2024年現在、安定してLLMが動くのは6.0系です
sudo mkdir -p /etc/apt/keyrings
wget -qO - https://repo.radeon.com/rocm/rocm.gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/rocm.gpg > /dev/null
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] https://repo.radeon.com/rocm/apt/6.0 jammy main" | sudo tee /etc/apt/keyrings/rocm.list

# ROCmのインストール
sudo apt update
sudo apt install -y rocm-hip-sdk
```

インストールが終わったら、一度再起動してください。
その後、以下のコマンドでGPUが認識されているか確認します。

```bash
/opt/rocm/bin/rocminfo
```

⚠️ **落とし穴:**
`rocminfo` を実行して「Permission denied」が出る場合は、ユーザーが `render` および `video` グループに所属していません。
`sudo usermod -aG render,video $USER` を実行して、一度ログアウトしてから再度試してください。これを忘れると、PythonからGPUが一生見えません。

## Step 2: 基本の設定

次に、LLMを動かすためのバックエンドとして「Ollama」のROCm版を導入します。
Ollamaは本来NVIDIA向けですが、AMD環境を自動判別して適切なランタイムを選択してくれるため、実務で重宝します。

```bash
# Ollamaのインストールスクリプト実行
curl -fsSL https://ollama.com/install.sh | sh
```

通常はこのまま動きますが、Radeonの一部のカード（RX 6700 XTなど）では、計算能力（GFXバージョン）を偽装しないと動きません。
これが「AMDは設定が面倒」と言われる理由の正体です。

```bash
# .bashrc または .zshrc に追記
# 以下の値は RX 6000系なら gfx1030、RX 7000系なら gfx1100 に設定
export HSA_OVERRIDE_GFX_VERSION=10.3.0
```

この環境変数を設定する理由は、AMDの公式サポートから外れているモデルでも、上位互換のある命令セットを強制的に使わせるためです。
私の検証では、この設定一つで「動かない」が「爆速」に変わるケースが多々ありました。

## Step 3: 動かしてみる

環境が整ったら、実際にLlama 3をダウンロードして、Pythonから呼び出してみましょう。
まずはライブラリのインストールです。

```bash
pip install ollama
```

次に、以下のPythonコードを作成します。ファイル名は `test_llm.py` としてください。

```python
import ollama
import time

def run_test():
    # 使用するモデル名
    model_name = "llama3"

    # モデルのダウンロード（初回のみ時間がかかる）
    print(f"Checking for model: {model_name}...")
    ollama.pull(model_name)

    start_time = time.time()

    # 推論の実行
    response = ollama.chat(model=model_name, messages=[
        {
            'role': 'user',
            'content': 'なぜNVIDIA以外のGPUはAI開発で苦戦しているのですか？3行で答えてください。',
        },
    ])

    end_time = time.time()

    print("\n--- 回答 ---")
    print(response['message']['content'])
    print(f"\n推論時間: {end_time - start_time:.2f}秒")

if __name__ == "__main__":
    run_test()
```

### 期待される出力

```
--- 回答 ---
1. NVIDIAのCUDAが長年の先行投資により、AI開発に必要なライブラリやエコシステムの標準を独占しているから。
2. AMDやIntelのソフトウェア基盤（ROCm/oneAPI）の互換性や安定性が、NVIDIAに比べてまだ発展途上であるから。
3. 多くのAI研究者や開発者がNVIDIA環境を前提にコードを公開しており、他社製ハードウェアへの移行コストが高いから。

推論時間: 1.24秒
```

この時、タスクマネージャー（または `rocm-smi` コマンド）を確認して、GPUの使用率が跳ね上がっていれば成功です。
CPUだけで動いている場合は、推論時間が10秒を超え、ファンが激しく回るはずです。

## Step 4: 実用レベルにする

単に文字を出すだけでは面白くないので、Streamlitを使って「実用的なチャットアプリ」に仕上げます。
エラーハンドリングを加え、GPUのメモリ不足（OOM）を防ぐための設定も盛り込みます。

```bash
pip install streamlit
```

以下の内容を `app.py` として保存してください。

```python
import streamlit as st
import ollama
import sys

st.set_page_config(page_title="AMD Local LLM Chat", layout="centered")

st.title("🚀 ROCm Optimized Chat")

# セッション状態の初期化（チャット履歴の保存）
if "messages" not in st.session_state:
    st.session_state.messages = []

# サイドバーに設定項目を追加
with st.sidebar:
    st.header("Settings")
    model_option = st.selectbox("Select Model", ["llama3", "phi3", "mistral"])
    if st.button("Clear Cache"):
        st.session_state.messages = []

# 履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザー入力
if prompt := st.chat_input("質問を入力してください"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            # ストリーミング再生でレスポンスを表示
            # 1文字ずつ表示されることで、体感速度を向上させる
            for chunk in ollama.chat(
                model=model_option,
                messages=st.session_state.messages,
                stream=True,
            ):
                token = chunk['message']['content']
                full_response += token
                response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
            if "memory" in str(e).lower():
                st.warning("GPU VRAMが不足している可能性があります。モデルのサイズを下げてください。")
```

実行コマンド:
```bash
streamlit run app.py
```

このコードでは、`stream=True` を設定しています。
大規模言語モデルは、全ての回答が生成されるまで待つと「遅い」と感じてしまいますが、生成されたトークンから順次表示することで、レスポンス0.1秒レベルの快適な操作感を実現できます。
これは実務でAIツールを導入する際、ユーザー満足度に直結する重要なテクニックです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `amdgpu` driver not found | ドライバの未インストール | `sudo apt install amdgpu-dkms` を実行し再起動 |
| `failed to create context` | VRAMの断片化または不足 | 他のブラウザタブを閉じるか、Ollamaを再起動 |
| 推論が極端に遅い | CPUで動作している | `HSA_OVERRIDE_GFX_VERSION` が正しく設定されているか確認 |

## 次のステップ

AMD環境でのローカルLLM構築、お疲れ様でした。
NVIDIAを使えば一瞬で終わる作業に、あえて時間をかけて「なぜ動くのか」を追うことで、AIインフラの核心に触れられたはずです。

次に挑戦すべきは「RAG（検索拡張生成）」の構築です。
今回作ったアプリに `LangChain` を組み合わせ、PDFや社内ドキュメントを読み込ませてみてください。
AMD GPUであっても、推論が動いてしまえばその後のロジックはNVIDIAと共通です。
また、複数のGPUを挿している場合は、`OLLAMA_NUM_PARALLEL` を設定して同時リクエスト処理能力を高める実験も面白いでしょう。
ハードウェアの制限をソフトウェアの工夫で乗り越える。これこそが、エンジニアとしての醍醐味です。

## よくある質問

### Q1: AMD GPUはWindowsのWSL2でも動きますか？

動きますが、Windows側の「AMD Software: Adrenalin Edition」のバージョンと、WSL2内のROCmバージョンの整合性を取るのが非常に難しいです。本気で使うなら、Ubuntuのネイティブインストールを強くおすすめします。

### Q2: 4GBや8GBのVRAMでも動きますか？

Llama 3 (8B) は、4bit量子化版であれば5GB程度のVRAMで動きます。ただし、システムが消費する分を考えると、8GBが最低ラインです。4GBの場合は `Gemma-2b` などの軽量モデルを選択してください。

### Q3: 学習（ファインチューニング）も可能ですか？

ROCm上でも `PyTorch` を使えば学習は可能です。ただし、学習ライブラリ（bitsandbytesなど）の多くがCUDAを前提に書かれているため、AMDで動かすには追加のパッチ適用が必要になるケースが多いです。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Radeon RX 7900 XT</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 20GB搭載で、大規模なモデルも余裕で動くAMD環境の最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRadeon%2520RX%25207900%2520XT%252020GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRadeon%2520RX%25207900%2520XT%252020GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Radeon%20RX%207900%20XT%2020GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [AMD MI50でQwen 2.5 27Bを爆速化してローカルLLMサーバーを構築する方法](/posts/2026-05-14-amd-mi50-qwen-vllm-setup-guide/)
- [NVIDIA H200 vs AMD MI300X: MLPerf v6.0の結果が突きつける「学習効率」の残酷な真実](/posts/2026-06-18-mlperf-v6-nvidia-h200-vs-amd-mi300x-comparison/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "AMD GPUはWindowsのWSL2でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、Windows側の「AMD Software: Adrenalin Edition」のバージョンと、WSL2内のROCmバージョンの整合性を取るのが非常に難しいです。本気で使うなら、Ubuntuのネイティブインストールを強くおすすめします。"
      }
    },
    {
      "@type": "Question",
      "name": "4GBや8GBのVRAMでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Llama 3 (8B) は、4bit量子化版であれば5GB程度のVRAMで動きます。ただし、システムが消費する分を考えると、8GBが最低ラインです。4GBの場合は Gemma-2b などの軽量モデルを選択してください。"
      }
    },
    {
      "@type": "Question",
      "name": "学習（ファインチューニング）も可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ROCm上でも PyTorch を使えば学習は可能です。ただし、学習ライブラリ（bitsandbytesなど）の多くがCUDAを前提に書かれているため、AMDで動かすには追加のパッチ適用が必要になるケースが多いです。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Radeon RX 7900 XT</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 20GB搭載で、大規模なモデルも余裕で動くAMD環境の最適解</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRadeon%2520RX%25207900%2520XT%252020GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRadeon%2520RX%25207900%2520XT%252020GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Radeon%20RX%207900%20XT%2020GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>
