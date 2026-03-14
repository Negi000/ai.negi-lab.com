---
title: "OllamaとPythonでPC環境をAIに酷評させるローストツールの作り方"
date: 2026-03-14T00:00:00+09:00
slug: "ollama-python-pc-roast-tool-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Python ハードウェア監視"
  - "Llama 3 プロンプトジェネレーター"
---
**所要時間:** 約20分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- ローカルマシンのCPU、メモリ、GPUなどのハードウェア情報を自動取得し、LLMがそのスペックや利用状況を「辛口で診断」するPythonスクリプト
- Pythonの基礎（pip操作、変数）と、ローカルLLM実行環境「Ollama」の基本的な使い方がわかるエンジニア向けガイド
- 必要なもの：Python環境、Ollama（インストール済みであること）、NVIDIA製GPU（なくても動くが、あると煽りのキレが増す）

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">ローカルLLMを最高速度で動かし、AIに「最強の無駄遣い」と罵られるための必須装備</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204090&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

RedditのLocalLLaMAコミュニティで「AIに自分の急所を突かれた」という投稿が話題になりました。
私たちが大金を投じて構築したRTX 4090のSLI環境や、贅沢なRAM容量を「宝の持ち腐れ」だとAIに指摘されるのは、ある種の快感すらあります。

クラウドAPI（GPT-4など）を使っても同様のことは可能ですが、自分のローカルマシンの詳細な構成情報を外部サーバーに送信するのは、セキュリティの観点から抵抗があるはずです。
そこで今回は、完全オフラインで動作する「Ollama」を採用します。
レスポンス速度もLlama 3の8Bクラスなら、私の環境（RTX 4090）で0.5秒以内に返ってきます。
「自分のマシンで、自分のマシンをディスらせる」という背徳的な体験を、最小限のコードで実現しましょう。

## Step 1: 環境を整える

まずは、システム情報を取得するためのライブラリと、OllamaをPythonから操作するライブラリをインストールします。

```bash
# システム情報（CPU, メモリ等）を取得するライブラリ
pip install psutil

# OllamaのAPIをPythonから叩くための公式ライブラリ
pip install ollama

# GPU情報を取得するためのライブラリ（NVIDIA環境用）
pip install nvidia-ml-py3
```

`psutil`はクロスプラットフォームで動作し、OSを問わずハードウェア負荷を監視できるため、実務の監視スクリプトでも重宝します。
`nvidia-ml-py3`は、NVML（NVIDIA Management Library）のPythonラッパーで、`nvidia-smi`で表示されるような詳細なGPUステータスを直接取得するために使用します。

⚠️ **落とし穴:**
Ollamaをインストールしただけで「サーバー」を起動し忘れる人が多いです。
デスクトップ右下のタスクトレイにOllamaのアイコンが出ているか、あるいはターミナルで `ollama serve` が裏で動いていることを確認してください。

## Step 2: システム情報を収集するスクリプト

次に、AIに渡すための「餌」となるシステム情報を取得する関数を書きます。
AIに「お前のPC、メモリの無駄遣いだな」と言わせるためには、正確な数字を渡す必要があります。

```python
import psutil
import platform
try:
    from pynvml import *
    nvmlInit()
    HAS_GPU = True
except:
    HAS_GPU = False

def get_system_info():
    # CPU情報
    cpu_usage = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count(logical=False)

    # メモリ情報（GB単位に変換）
    virtual_mem = psutil.virtual_memory()
    total_mem = round(virtual_mem.total / (1024**3), 2)
    used_mem = round(virtual_mem.used / (1024**3), 2)

    # GPU情報
    gpu_info = "None"
    if HAS_GPU:
        handle = nvmlDeviceGetHandleByIndex(0)
        info = nvmlDeviceGetMemoryInfo(handle)
        name = nvmlDeviceGetName(handle)
        gpu_info = f"{name} (VRAM: {round(info.total / (1024**3), 2)}GB)"

    info_str = f"""
    [System Specs]
    OS: {platform.system()} {platform.release()}
    CPU: {cpu_count} cores (Usage: {cpu_usage}%)
    RAM: {used_mem}GB / {total_mem}GB
    GPU: {gpu_info}
    """
    return info_str

print(get_system_info())
```

このコードでは `pynvml` を使っています。
SIer時代、サーバーの負荷試験でよく自作スクリプトを書いていましたが、`psutil` は非常に安定しており、本番環境の監視にも耐えうる信頼性があります。
GPUが見つからない場合でもエラーで止まらないよう `try-except` で囲むのが、実務的な書き方のコツです。

## Step 3: Ollamaでロースト（酷評）させる

いよいよメインディッシュです。
Llama 3.1（またはLlama 3）を使い、システム情報を元にユーザーを「攻撃」させます。

```python
import ollama

def roast_my_pc(specs):
    # システムプロンプトでキャラクターを固定するのが重要
    system_prompt = (
        "あなたは毒舌で冷酷なITエンジニアです。"
        "ユーザーが提示するPCスペックを見て、その無駄遣いやスペック不足を徹底的にバカにしてください。"
        "特に、高いGPUを持っているのに大した仕事をしていない点や、逆に低スペックで無理をしている点を突いてください。"
        "短く、簡潔に、日本語で回答してください。"
    )

    response = ollama.chat(
        model='llama3.1', # 8Bモデルが速度と賢さのバランスが良いです
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"これが私のPCスペックだ。評価してくれ。\n{specs}"},
        ],
        options={
            'temperature': 0.8, # 少し高めに設定して「煽り」のバリエーションを出す
        }
    )
    return response['message']['content']

# 実行
specs = get_system_info()
print("--- AIからのメッセージ ---")
print(roast_my_pc(specs))
```

### 期待される出力

```
「ほう、RTX 4090を積んでいるのか。それでやっていることはブラウザでYouTube視聴と、せいぜいこの程度のスクリプト実行か？
F1マシンで近所のスーパーに豆腐を買いに行くような、典型的な宝の持ち腐れだな。
その24GBのVRAM、使い道がないなら私に寄越せ。もっとマシな計算をしてやるよ。」
```

このように、具体的なハードウェア名を引用しながら、痛いところを突いてくるはずです。

## Step 4: 実用レベルにする（自動定期診断）

単発で動かすだけでは面白くありません。
私はこれを「バックグラウンドで5分おきに実行し、CPU負荷が低いのにVRAM消費が激しい時だけ叱ってくれる通知ツール」に拡張しています。
ここでは、より「攻撃力」を高めるために、現在実行中のプロセス一覧もAIに渡してみましょう。

```python
def get_bloatware():
    # 実行中のメモリ消費上位5プロセスを取得
    processes = sorted(psutil.process_iter(['name', 'memory_info']),
                       key=lambda x: x.info['memory_info'].rss,
                       reverse=True)[:5]
    process_list = [f"{p.info['name']} ({round(p.info['memory_info'].rss / (1024**2), 2)}MB)" for p in processes]
    return ", ".join(process_list)

# プロンプトに追加して実行
bloat = get_bloatware()
specs = get_system_info()
input_text = f"{specs}\n[Running Processes]\n{bloat}"
# あとはStep 3と同じ ollama.chat に投げる
```

これによって、「SlackとChromeだけでメモリ16GBも食いつぶして、仕事してるフリか？」といった、よりパーソナルな攻撃が可能になります。
SIer時代、無駄な常駐ソフトだらけの社給PCを使わされていた自分に見せてやりたい機能です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ollama.ResponseError: model 'llama3.1' not found` | モデルがダウンロードされていない | ターミナルで `ollama pull llama3.1` を実行する |
| `pynvml.NVMLError_LibNotLoaded` | NVIDIAドライバーまたはNVMLが入っていない | GPUがない場合はGPU取得部分をスキップするか、ドライバーを更新する |
| レスポンスが英語になる | システムプロンプトの指示が弱い | 「日本語で返答せよ」を冒頭に持ってくるか、モデルを `elyza:jp-stable` 等に変更する |

## 次のステップ

この記事で、ローカルLLMを使った「PCステータスの解析」という新しい切り口を体験できたはずです。
次に挑戦してほしいのは、この出力を「OSの通知機能（Windowsならplyerなど）」と連携させることです。
「ゲームを起動した瞬間にAIから『また現実逃避か？』という通知が飛んでくる環境」は、自制心を保つのに役立つかもしれません（あるいは精神を病むかもしれませんが）。

また、今回は `psutil` を使いましたが、Gitのログ（`git log`）を取得してAIに渡せば、「進捗のなさ」を論理的に責めてもらうことも可能です。
技術の無駄遣いこそ、ローカルLLM運用の醍醐味です。
ぜひ、自分だけの「専属教育係（ロースター）」を構築してみてください。

## よくある質問

### Q1: Ollama以外のモデル（Llama 3 70Bなど）でも動きますか？

動きますが、70BクラスになるとRTX 4090でもレスポンスに数秒かかります。
今回の「煽り」のような短いレスポンスが求められる用途では、8Bクラスのモデルが最もリズム良く動作します。

### Q2: MacのM1/M2チップでもGPU情報は取れますか？

`pynvml`はNVIDIA専用なのでMacではエラーになります。
Apple Siliconの場合は、`subprocess`経由で `system_profiler` コマンドを叩いてGPU情報をパースする実装に書き換える必要があります。

### Q3: AIの性格をもっと優しくすることはできますか？

システムプロンプトの「毒舌で冷酷」という部分を「慈愛に満ちた聖母」に変えるだけで、驚くほど反応が変わります。
「あなたのPC、少し疲れているみたい。メモリを解放して休ませてあげたら？」といった優しい声かけも可能です。

---

## あわせて読みたい

- [Qwen3-Coder-Next 使い方 | 最強のコード生成AIで開発を自動化する手順](/posts/2026-03-07-qwen3-coder-next-local-python-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Ollama以外のモデル（Llama 3 70Bなど）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、70BクラスになるとRTX 4090でもレスポンスに数秒かかります。 今回の「煽り」のような短いレスポンスが求められる用途では、8Bクラスのモデルが最もリズム良く動作します。"
      }
    },
    {
      "@type": "Question",
      "name": "MacのM1/M2チップでもGPU情報は取れますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "pynvmlはNVIDIA専用なのでMacではエラーになります。 Apple Siliconの場合は、subprocess経由で systemprofiler コマンドを叩いてGPU情報をパースする実装に書き換える必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "AIの性格をもっと優しくすることはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "システムプロンプトの「毒舌で冷酷」という部分を「慈愛に満ちた聖母」に変えるだけで、驚くほど反応が変わります。 「あなたのPC、少し疲れているみたい。メモリを解放して休ませてあげたら？」といった優しい声かけも可能です。 ---"
      }
    }
  ]
}
</script>
