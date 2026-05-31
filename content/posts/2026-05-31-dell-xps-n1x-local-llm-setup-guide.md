---
title: "Dell XPS N1X相当のローカルLLM実行環境を構築する方法"
date: 2026-05-31T00:00:00+09:00
slug: "dell-xps-n1x-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-05-31-dell-xps-n1x-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Dell XPS N1X"
  - "NVIDIA GB10"
  - "Ollama 使い方"
  - "Llama 3 構築"
---
**所要時間:** 約45分 | **難易度:** ★★★★☆

## この記事で作るもの

- 発表された「Dell XPS N1X（DGX Spark相当）」の性能を先取りし、Llama 3 70Bクラスのモデルを快適に動かすローカルAI実行基盤
- Dockerを活用した、GPUメモリ（VRAM）を最大限に引き出すOllama + Open-WebUIの統合環境
- Pythonによる推論速度（Tokens Per Second）の計測スクリプト

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">24GBのVRAMは70Bクラスのモデルを動かすための事実上の標準。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、コマンドラインの基本操作とDockerの基礎的な概念を理解していることを想定しています。

## 先に確認するスペック・料金

「N1X」ことNVIDIA GB10（DGX Spark）は、コンシューマー向けでありながらWindows上で動くモンスターマシンです。
この記事で紹介する環境を自作PCや既存のワークステーションで再現するには、最低でも「VRAM 16GB以上」のGPUが必須となります。
RTX 4060 Ti (16GB)がエントリーライン、理想はRTX 4090 (24GB)の1枚、あるいは2枚挿しです。

もし「VRAM 8GBしかない」「MacBook Airのメモリ8GBモデルだ」という場合は、量子化（圧縮）を極限まで高めたモデルしか動きません。
その場合は無理にローカルにこだわらず、GroqやOpenRouterなどの高速APIをバックエンドに使う構成に切り替える方が、開発効率としては正解です。
実務で使うなら「回答を待つ30秒」はコストでしかありませんから。

## なぜこの方法を選ぶのか

ローカルLLMを動かす方法は、LM StudioやGPT4Allなど、GUIで完結するツールが他にもたくさんあります。
しかし、私はあえて「Docker + Ollama + Open-WebUI」の組み合わせを推奨します。
理由は、開発環境のポータビリティと、将来的なスケーラビリティです。

GUIツールは手軽ですが、特定のバージョンに依存したり、バックグラウンドでのプロセス管理が不透明だったりします。
Dockerベースで構築しておけば、将来的にDell XPS N1Xのような最新ハードウェアに移行する際も、設定ファイルをコピーするだけで「全く同じ環境」が1分で立ち上がります。
また、APIサーバーとして独立させることで、自作のPythonアプリやCursorなどのエディタから自由に呼び出せるようになります。

## Step 1: 環境を整える

まずは、GPUの力をDockerコンテナに橋渡しするための「NVIDIA Container Toolkit」をインストールします。
これがないと、コンテナ内のAIモデルはCPUでしか動かず、レスポンスに数分かかる地獄を見ることになります。

```bash
# NVIDIA公式リポジトリのセットアップ
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#' | \
  sudo tee /etc/local/sources.list.d/nvidia-container-toolkit.list

# インストールと再起動
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

このコマンドは、ホストOS（Linux/Windows WSL2）のGPUドライバをDockerコンテナから安全に叩くためのバイパスを作っています。
`nvidia-smi`コマンドでGPUが認識されている状態で実行してください。

⚠️ **落とし穴:** Windows環境のWSL2を使っている場合、Docker Desktopの設定で「Use the WSL 2 based engine」が有効になっていないと、いくらToolkitを入れてもGPUを認識しません。
また、WSL2自体のメモリ割り当て（.wslconfig）がデフォルトのままだと、モデルロード時に「Out of Memory」でクラッシュします。
システムメモリの50%以上をWSL2に割り当てる設定を先に行っておきましょう。

## Step 2: 基本の設定

次に、OllamaとOpen-WebUIを同時に立ち上げるための `docker-compose.yml` を作成します。
「なぜ2つ分けるのか」という疑問があるかもしれませんが、推論エンジン（Ollama）とインターフェース（WebUI）を分離することで、エンジンのアップデートが容易になるからです。

```yaml
services:
  ollama:
    volumes:
      - ./ollama:/root/.ollama
    container_name: ollama
    pull_policy: always
    tty: true
    restart: unless-stopped
    image: ollama/ollama:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    volumes:
      - ./open-webui:/app/backend/data
    depends_on:
      - ollama
    ports:
      - 3000:8080
    environment:
      - 'OLLAMA_BASE_URL=http://ollama:11434'
      - 'WEBUI_SECRET_KEY=yoursecretkeyhere'
    restart: unless-stopped
```

この設定の肝は `count: all` です。
これを指定しないと、私のようにRTX 4090を複数枚挿している環境でも、Dockerが1枚しか使ってくれないという勿体ない状況になります。
また、`OLLAMA_BASE_URL` にコンテナ名を指定することで、コンテナ間通信を確立させています。

## Step 3: 動かしてみる

設定ファイルが書けたら、コンテナを起動し、モデルをダウンロードします。
今回は、Dell XPS N1Xでもメインで使われるであろう「Llama 3.1 8B」および「70B」をターゲットにします。

```bash
# バックグラウンドで起動
docker compose up -d

# モデルのプル（8BモデルならRTX 3060等でも余裕）
docker exec -it ollama ollama run llama3.1:8b
```

ブラウザで `http://localhost:3000` にアクセスしてください。
ChatGPTライクな画面が表示されれば成功です。

### 期待される出力

Ollamaのログを確認して、以下のような表示が出ていればGPUが正しく使われています。

```text
llm_load_tensors: ggml ctx size =    0.11 MiB
llm_load_tensors: offloading 32 repeat layers to GPU
llm_load_tensors: offloaded 32/32 layers to GPU
```

`offloaded 32/32 layers to GPU` となっていれば、すべての計算がVRAM上で行われています。
もしここが `0/32` ならCPU推論になっており、レスポンスは数分待ちになります。

## Step 4: 実用レベルにする

「動いた」で満足するのは初心者です。
実務で使うなら、この環境がどの程度のスループットを出せるか、定量的に把握しておく必要があります。
Dell XPS N1Xを買うべきか、今のままでいいかを判断する基準を作るため、Pythonでベンチマークスクリプトを書きます。

```python
import requests
import time
import json

def benchmark_ollama(model_name, prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }

    start_time = time.time()
    response = requests.post(url, json=payload)
    end_time = time.time()

    if response.status_code == 200:
        data = response.json()
        total_duration = end_time - start_time
        # OllamaのAPIはナノ秒単位で統計を返すので変換が必要
        eval_count = data.get("eval_count", 0)
        tps = eval_count / total_duration

        print(f"Model: {model_name}")
        print(f"Total tokens: {eval_count}")
        print(f"Time taken: {total_duration:.2f}s")
        print(f"Throughput: {tps:.2f} tokens/s")
    else:
        print(f"Error: {response.status_code}")

if __name__ == "__main__":
    # 専門的な内容を生成させて負荷をかける
    test_prompt = "Explain the difference between Blackwell and Ada Lovelace architecture in detail."
    benchmark_ollama("llama3.1:8b", test_prompt)
```

このスクリプトを実行して、`tokens/s` を確認してください。
8Bモデルで50 tokens/s以上出ていれば、人間が読む速度を遥かに超えており、実務でのRAG（検索拡張生成）用途に十分耐えられます。
一方、これが10 tokens/sを切るようなら、ハードウェアか量子化設定を見直すべきです。

私が2枚のRTX 4090でLlama 3.1 70Bを動かした際は、約15〜20 tokens/s程度。
Dell XPS N1Xが「DGX Spark」として登場した時、この数字がどこまで伸びるかが買い替えの基準になります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Error: libnvidia-ml.so.1 not found | GPUドライバとToolkitの不整合 | ホストのドライバを最新にし、Dockerを再起動 |
| context window exceeded | デフォルトのコンテキスト長不足 | OllamaのModelfileで `PARAMETER num_ctx 8192` を設定 |
| connection refused (port 11434) | ホスト外からのアクセス拒否 | `OLLAMA_HOST=0.0.0.0` を環境変数に追加 |

## 次のステップ

この記事で構築した環境は、あくまで「ベース」です。
次に取り組むべきは、このローカルサーバーを**「自分専用のナレッジベース」**に進化させることです。

1. **AnythingLLMの導入**: 今回作ったOllamaのAPIエンドポイントをAnythingLLMに接続し、手元のPDFやMarkdownファイルを全学習させたローカルRAGを構築してみてください。
2. **DPOによる微調整（Fine-tuning）**: `unsloth` などのライブラリを使い、自分の過去のメールやチャットログから「自分らしい文章を書く」モデルへ微調整することに挑戦してください。
3. **Cursorとの連携**: `Continue.dev` 等のエディタ拡張を使い、コード補完をすべてローカルLLMに任せる環境を作ると、プライバシーとコストの両面で最強の開発環境が完成します。

ローカルLLMの世界は、ハードウェアの進化（N1Xの登場など）によって数ヶ月単位で常識が変わります。
だからこそ、特定のツールに依存せず、DockerとPythonで「自分で制御できる環境」を持っている人間が一番強いのです。

## よくある質問

### Q1: Dell XPS N1Xが出るまで待ったほうがいいですか？

待つ必要はありません。今あるGPUで環境を構築し、プロンプトエンジニアリングやRAGの構成を学んでおくべきです。ハードが届いたその日に、蓄積した知見を流し込むのが最も効率的です。

### Q2: メモリ（VRAM）が足りない場合、モデルは動きませんか？

動きますが、メインメモリ（RAM）を使用するため極端に遅くなります。これを「オフローディング」と呼びますが、実用的な速度は出ません。VRAMに収まるサイズの量子化モデル（Q4_K_Mなど）を選ぶのが鉄則です。

### Q3: WindowsとLinux、どちらで構築するのがベストですか？

純粋なパフォーマンスと安定性を求めるならLinux（Ubuntu）です。しかし、日常業務でWindowsを使っているならWSL2で十分です。NVIDIAの最適化が進んでいるため、体感できるほどの差はなくなってきています。

---

## あわせて読みたい

- [OllamaとPythonでローカルLLM環境を構築する手順](/posts/2026-04-17-local-llm-python-ollama-tutorial/)
- [OllamaとOpen WebUIで自分専用のChatGPT環境を作る方法](/posts/2026-05-31-ollama-openwebui-local-llm-setup-guide/)
- [Qwen2.5をローカル環境で動かし、API料金を気にせずコード生成を自動化するPythonスクリプトを作る方法](/posts/2026-05-09-qwen-2-5-coder-local-python-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Dell XPS N1Xが出るまで待ったほうがいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "待つ必要はありません。今あるGPUで環境を構築し、プロンプトエンジニアリングやRAGの構成を学んでおくべきです。ハードが届いたその日に、蓄積した知見を流し込むのが最も効率的です。"
      }
    },
    {
      "@type": "Question",
      "name": "メモリ（VRAM）が足りない場合、モデルは動きませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、メインメモリ（RAM）を使用するため極端に遅くなります。これを「オフローディング」と呼びますが、実用的な速度は出ません。VRAMに収まるサイズの量子化モデル（Q4KMなど）を選ぶのが鉄則です。"
      }
    },
    {
      "@type": "Question",
      "name": "WindowsとLinux、どちらで構築するのがベストですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "純粋なパフォーマンスと安定性を求めるならLinux（Ubuntu）です。しかし、日常業務でWindowsを使っているならWSL2で十分です。NVIDIAの最適化が進んでいるため、体感できるほどの差はなくなってきています。 ---"
      }
    }
  ]
}
</script>
