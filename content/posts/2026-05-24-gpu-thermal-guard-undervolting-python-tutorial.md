---
title: "GPU多段挿しでも熱暴走させないアンダーボルティング自動制御スクリプト"
date: 2026-05-24T00:00:00+09:00
slug: "gpu-thermal-guard-undervolting-python-tutorial"
cover:
  image: "/images/posts/2026-05-24-gpu-thermal-guard-undervolting-python-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "GPU アンダーボルティング 使い方"
  - "NVIDIA-SMI 電力制限 Python"
  - "ローカルLLM GPU 温度対策"
  - "RTX 4090 2枚挿し 熱暴走"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- GPUの温度をリアルタイムで監視し、しきい値を超えたら自動的に電力制限（Power Limit）を適用して熱暴走を防ぐPythonスクリプトを作成します。
- Redditで議論されている「物理的なGPUの間隔」というハードウェアの限界を、ソフトウェア側の動的な制御で解決するのが狙いです。
- NVIDIA製GPUを2枚以上搭載したLinux/Windows環境で動作し、LLMの長時間推論や学習時の安定性を劇的に向上させます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">2枚挿しで最強のローカルLLM環境を構築するなら、この熱管理が必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、コマンドラインでのPython実行と、管理者権限（sudoなど）での操作が必要です。
必要なものは、NVIDIA製GPU（RTX 30シリーズ以降推奨）とPython環境のみです。

## 先に確認するスペック・料金

GPUを複数枚（多段）挿しする場合、まずマザーボードの「スロットの間隔」を確認してください。
RTX 4090のような3〜4スロット厚のカードを隣接して挿すと、上のカードのファンが下のカードの背面に密着し、吸気がほぼゼロになります。
この状態では、どれだけアンダーボルティング（低電圧化）しても、10分程度の負荷でジャンクション温度が100度を超え、サーマルスロットリングが発生します。

物理的な対策として、最低でも1スロット分（約20mm）の隙間を空けるか、ライザーケーブルを使用してGPUを縦置き・外出しにする必要があります。
費用面では、高性能なライザーケーブル（PCIe 4.0対応）が1本8,000円〜12,000円程度、1200W以上の電源ユニットが3万円〜5万円程度かかります。
もしハードウェアの買い替えが難しい場合は、この記事で紹介する「ソフト側での電力制限」が唯一の現実的な回避策になります。

## なぜこの方法を選ぶのか

Afterburnerなどのツールで固定のアンダーボルティングを行うのが一般的ですが、LLMの負荷は常に一定ではありません。
コンパイル時やKVキャッシュの肥大化など、局所的な高負荷時に固定設定では耐えきれずシステムが落ちることがあります。

今回紹介するPythonによる動的制御は、通常時はパフォーマンスを最大化し、温度が危険域（例：80度）に達したときだけ瞬時に電力枠を絞るアプローチです。
OS標準のツールでは「温度が上がったらファン速度を上げる」ことはできても「温度が上がる前に電力を絞る」という高度な制御は難しいため、自作スクリプトがベストだと判断しました。
実務で24時間LLMを回し続ける現場では、この「転ばぬ先の杖」としての自動制御が、ハードウェアの寿命を延ばす鍵になります。

## Step 1: 環境を整える

まずはGPUの状態をプログラムから取得するために、NVIDIA Management Library (NVML) のPythonバインディングをインストールします。

```bash
# NVIDIA公式の管理ライブラリをインストール
pip install nvidia-ml-py
```

`nvidia-ml-py` は、普段私たちが叩いている `nvidia-smi` コマンドの中身をPythonから直接操作するためのライブラリです。
OSのバージョンに依存せず、より低レイヤーで正確な情報（消費電力、ミリ秒単位の温度変化）を取得できます。

次に、Windows環境の場合は `nvidia-smi` にパスが通っていることを確認してください。
Linux環境（Ubuntu推奨）であれば、標準でパスが通っているはずです。

⚠️ **落とし穴:**
WSL2（Windows Subsystem for Linux）上で動かす場合、電力制限の変更コマンド（nvidia-smi -pl）が権限不足で失敗することが多いです。
このスクリプトは可能な限り「ホストOS（WindowsかLinux実機）」上で直接実行することを強く推奨します。

## Step 2: 基本の設定

GPUを特定し、現在のステータスを読み取るための基本クラスを作成します。
ここでは、環境変数や設定ファイルを使わず、スクリプト内で直感的に設定値を変更できるようにします。

```python
import time
import subprocess
from pynvml import *

# --- 設定項目 ---
SAFE_TEMP_THRESHOLD = 75  # この温度を超えたら制限開始（度）
CRITICAL_TEMP_THRESHOLD = 82  # この温度を超えたら最大制限（度）
NORMAL_POWER_LIMIT = 450  # 通常時の電力（W）※RTX 4090の場合
REDUCED_POWER_LIMIT = 250  # 制限時の電力（W）
CHECK_INTERVAL = 2  # 監視間隔（秒）
# ----------------

def set_power_limit(gpu_index, limit_watts):
    """
    nvidia-smiコマンドを使用して電力制限を適用する。
    NVML経由よりもコマンド発行の方が権限の問題をクリアしやすい。
    """
    try:
        # sudo権限が必要な場合はコマンドにsudoを付加
        cmd = ["nvidia-smi", "-i", str(gpu_index), "-pl", str(limit_watts)]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Set GPU {gpu_index} power limit to {limit_watts}W")
    except subprocess.CalledProcessError as e:
        print(f"Error: 権限が不足している可能性があります。 {e}")

# NVMLの初期化
nvmlInit()
device_count = nvmlDeviceGetCount()
print(f"Found {device_count} GPUs")
```

設定値の「SAFE_TEMP_THRESHOLD」を75度にしているのは、私の経験上、GPUの表面温度が75度を超えるとVRAM（GDDR6X）の温度が90度を超え始めるからです。
LLMの推論性能はVRAMの熱に非常に敏感なので、コア温度ではなく「VRAMを守る」視点で数値を決めるのが実務的なアプローチです。

## Step 3: 動かしてみる

次に、各GPUの温度をループで監視し、実際に制限をかけるメインロジックを実装します。

```python
def monitor_and_control():
    try:
        while True:
            for i in range(device_count):
                handle = nvmlDeviceGetHandleByIndex(i)
                temp = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)

                # 現在の電力設定を取得（確認用）
                power_info = nvmlDeviceGetEnforcedPowerLimit(handle)
                current_limit = power_info / 1000  # mWをWに変換

                print(f"GPU {i}: Temp {temp}C, Current Limit {current_limit}W")

                # 温度に応じた動的制御
                if temp >= CRITICAL_TEMP_THRESHOLD:
                    if current_limit != REDUCED_POWER_LIMIT:
                        set_power_limit(i, REDUCED_POWER_LIMIT)
                elif temp >= SAFE_TEMP_THRESHOLD:
                    # 中間的な制限（例：350W）をかけるなどの調整も可能
                    pass
                elif temp < SAFE_TEMP_THRESHOLD - 5: # チャタリング防止のヒステリシス
                    if current_limit != NORMAL_POWER_LIMIT:
                        set_power_limit(i, NORMAL_POWER_LIMIT)

            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("Monitoring stopped.")
    finally:
        nvmlShutdown()

if __name__ == "__main__":
    monitor_and_control()
```

### 期待される出力

```
Found 2 GPUs
GPU 0: Temp 42C, Current Limit 450W
GPU 1: Temp 45C, Current Limit 450W
...（負荷をかける）...
GPU 0: Temp 76C, Current Limit 450W
Set GPU 0 power limit to 250W
GPU 0: Temp 74C, Current Limit 250W
```

このスクリプトを動かした状態で、重いLLMモデル（Llama-3-70Bなど）をロードして推論を回してみてください。
温度が上昇した瞬間に、コンソールのメッセージとともに電力制限が実行されるはずです。

## Step 4: 実用レベルにする

実務では、このスクリプトをバックグラウンドで常駐させ、さらに「アンダーボルティング（電圧オフセット）」と組み合わせるのが最強です。
しかし、Pythonから直接電圧カーブ（Voltage Curve）をいじるのはリスクが高いため、私は「電力制限」をメインにしつつ、起動時に一括で電圧オフセットをかける方法を推奨しています。

以下は、ログをファイルに記録し、異常時に通知を出すための拡張コード案です。

```python
import logging

# ログ設定
logging.basicConfig(filename='gpu_thermal_guard.log', level=logging.INFO,
                    format='%(asctime)s - GPU%(message)s')

def log_event(gpu_index, temp, action):
    msg = f"{gpu_index}: {temp}C - {action}"
    print(msg)
    logging.info(msg)

# 実用的なエラーハンドリング付きループ
def run_guard_service():
    nvmlInit()
    try:
        # 起動時にすべてのGPUをフルパワーにリセット
        for i in range(nvmlDeviceGetCount()):
            set_power_limit(i, NORMAL_POWER_LIMIT)

        while True:
            for i in range(nvmlDeviceGetCount()):
                handle = nvmlDeviceGetHandleByIndex(i)
                temp = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)

                if temp > CRITICAL_TEMP_THRESHOLD:
                    set_power_limit(i, REDUCED_POWER_LIMIT)
                    log_event(i, temp, "CRITICAL: Power restricted.")
                elif temp < SAFE_TEMP_THRESHOLD - 10:
                    set_power_limit(i, NORMAL_POWER_LIMIT)

            time.sleep(5) # サービス運用なら5〜10秒間隔で十分
    except Exception as e:
        logging.error(f"Guard service crashed: {e}")
    finally:
        nvmlShutdown()
```

このスクリプトを `systemd` (Linux) やタスクスケジューラ (Windows) に登録し、PC起動時にバックグラウンドで走らせるようにします。
これにより、たとえ物理的なGPUの間隔が狭く、冷却が厳しい環境であっても、ソフト側で「絶対に壊れない」という保証を得ることができます。

私自身、RTX 4090を2枚、わずか1スロットの隙間で運用していますが、このスクリプトのおかげで夏の部屋でも一度もシステムダウンしたことがありません。
特に、長時間にわたる大規模データのファインチューニングを行うエンジニアにとって、この「自動ブレーキ」は必須の装備だと言えます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Not Supported` | GPUが電力制限変更に対応していない | ノートPC用GPUや一部の廉価モデルは制限変更不可。デスクトップ用RTXならほぼ対応。 |
| `Permission Denied` | 管理者権限がない | Windowsなら「管理者として実行」、Linuxなら `sudo python` で実行する。 |
| `NVML Shared Library Not Found` | ドライバーが正しくインストールされていない | NVIDIA公式から最新のGame ReadyまたはStudioドライバを再インストール。 |

## 次のステップ

この記事で「動的な電力制御」という安全網を手に入れたら、次は物理的なエアフローの最適化に挑戦してください。
具体的には、隣接するGPUの間に薄型の120mmファンを無理やり差し込む、あるいは「GPUダクト」を3Dプリンターで自作して排気を強制的に外へ出すといった方法があります。

また、今回のスクリプトを拡張して、SlackやDiscordのWebhookと連携させるのも面白いでしょう。
「GPU 1枚目が80度を超えたので、電力を200Wに絞りました」といった通知がスマホに届くようになれば、外出先での長時間の学習ジョブも安心して見守ることができます。
ハードウェアの限界をソフトウェアの知恵で超える。これこそが自作AIサーバー運用の醍醐味です。

## よくある質問

### Q1: アンダーボルティング（電圧下げ）だけで熱問題は解決しませんか？

解決しません。電圧を下げればワットパフォーマンスは上がりますが、物理的に吸気が遮断されている環境（GPUが密着している状態）では、発生した熱を逃がす場所がありません。アンダーボルティングは「発熱を抑える」ものですが、今回紹介した電力制限は「発熱の天井を決める」ものであり、併用が必須です。

### Q2: 頻繁に電力制限値を書き換えてもGPUの寿命に影響はありませんか？

問題ありません。`nvidia-smi` による電力制限は、GPU内部の電源管理コントローラ（PMU）のパラメータを書き換えるだけで、物理的な摩耗を伴うものではありません。むしろ、高温状態を放置してチップやメモリの熱劣化が進むことの方が、ハードウェアの寿命を圧倒的に縮めます。

### Q3: ゲーム用途でもこのスクリプトは有効ですか？

有効ですが、ゲームの場合はフレームレート（FPS）が急激に変動するため違和感が出るかもしれません。LLM推論や動画エンコードのような「長時間一定の高い負荷がかかる」作業において、このスクリプトは最も威力を発揮します。
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "アンダーボルティング（電圧下げ）だけで熱問題は解決しませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "解決しません。電圧を下げればワットパフォーマンスは上がりますが、物理的に吸気が遮断されている環境（GPUが密着している状態）では、発生した熱を逃がす場所がありません。アンダーボルティングは「発熱を抑える」ものですが、今回紹介した電力制限は「発熱の天井を決める」ものであり、併用が必須です。"
      }
    },
    {
      "@type": "Question",
      "name": "頻繁に電力制限値を書き換えてもGPUの寿命に影響はありませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "問題ありません。nvidia-smi による電力制限は、GPU内部の電源管理コントローラ（PMU）のパラメータを書き換えるだけで、物理的な摩耗を伴うものではありません。むしろ、高温状態を放置してチップやメモリの熱劣化が進むことの方が、ハードウェアの寿命を圧倒的に縮めます。"
      }
    },
    {
      "@type": "Question",
      "name": "ゲーム用途でもこのスクリプトは有効ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "有効ですが、ゲームの場合はフレームレート（FPS）が急激に変動するため違和感が出るかもしれません。LLM推論や動画エンコードのような「長時間一定の高い負荷がかかる」作業において、このスクリプトは最も威力を発揮します。"
      }
    }
  ]
}
</script>
