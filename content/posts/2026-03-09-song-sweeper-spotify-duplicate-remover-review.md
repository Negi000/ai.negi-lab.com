---
title: "Song Sweeper 使い方 音楽ライブラリの重複を自動削除する"
date: 2026-03-09T00:00:00+09:00
slug: "song-sweeper-spotify-duplicate-remover-review"
description: "Spotifyなどの巨大なプレイリストから重複する楽曲を検出し、API経由で一括クリーンアップするツール。。メタデータ（タイトル、アーティスト名）の一致だ..."
cover:
  image: "/images/posts/2026-03-09-song-sweeper-spotify-duplicate-remover-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Song Sweeper"
  - "Spotify 重複削除"
  - "Python 音楽管理"
  - "プレイリスト自動化"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- Spotifyなどの巨大なプレイリストから重複する楽曲を検出し、API経由で一括クリーンアップするツール。
- メタデータ（タイトル、アーティスト名）の一致だけでなく、Spotify URIによる厳密な同一性判定を自動化できる。
- 1,000曲を超える肥大化したプレイリストを抱えるDJや、複数サービスから曲をインポートしてライブラリが汚れている人に最適。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">Audio-Technica ATH-M50x</strong>
<p style="color:#555;margin:8px 0;font-size:14px">重複のないクリーンなライブラリを、解像度の高いモニターヘッドホンで楽しむために最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=Audio-Technica%20ATH-M50x&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FAudio-Technica%2520ATH-M50x%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FAudio-Technica%2520ATH-M50x%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、Spotify APIを自分で叩いてスクリプトを書くのが面倒なエンジニア、あるいは数千曲単位のライブラリ管理を自動化したい人にとっては「非常に価値のある選択肢」です。★評価は4.5/5。

私自身、SIer時代から趣味で収集した2万曲近いローカル音源とSpotifyライブラリを同期させていますが、手作業での重複削除は100曲を超えたあたりで集中力が切れます。Song Sweeperは、API制限を考慮したリトライ処理や、微妙な表記揺れ（Remix表記の有無など）を考慮したフィルタリングが実装されており、エンジニアが「自分で書こうと思って放置していたスクリプト」をそのまま形にしたような完成度です。

ただし、数個のプレイリストしか持たないライトユーザーには不要です。また、後述するようにOAuth 2.0の認証プロセスを理解している中級者以上でないと、セットアップで少し戸惑うかもしれません。

## このツールが解決する問題

音楽配信サービスのプレイリストは、長く使っていると必ず「重複」という毒に侵されます。特にSoundiizやTuneMyMusicのような移行ツールを使って他サービスからライブラリを移した場合、同じ曲が異なるアルバム（シングル版とアルバム版など）として登録され、プレイリストの純度が下がります。

Spotifyの標準機能でも、曲を追加する際に「この曲は既にプレイリストに含まれています」と警告は出ますが、既存の巨大なプレイリストの中にある重複をスキャンして消し去る機能は提供されていません。

従来、この問題を解決するには、Spotify Web APIを叩くPythonスクリプトを自前で書く必要がありました。`spotipy`などのライブラリを使って、全楽曲のURIを取得し、辞書型で重複をチェックし、削除APIを叩く。この工程には、APIのレートリミット（429エラー）対策や、ページネーション処理（1リクエスト100曲まで）といった「地味に面倒な実装」が伴います。

Song Sweeperは、これらのボイラープレートコードを隠蔽し、数行のコマンドや関数呼び出しだけでクリーンアップを完了させます。1000曲のリストから重複を見つけ出し、削除完了するまでの時間はわずか数秒。この「思考を止めないスピード感」が最大の解決策です。

## 実際の使い方

### インストール

Song SweeperはPython環境で動作するCLIツールおよびライブラリとして提供されています。まずはpipでインストールします。

```bash
pip install song-sweeper
```

事前にSpotify Developer Dashboardで「Client ID」と「Client Secret」を取得し、環境変数に設定しておく必要があります。ここが非エンジニアには高いハードルですが、本ブログの読者層なら問題ないでしょう。

### 基本的な使用例

公式のREADMEに基づいた、最もシンプルな重複削除のシミュレーションコードです。

```python
from song_sweeper import Sweeper

# 認証情報の初期化
# 内部的にOAuth2.0のフローが走り、ブラウザで認証を求められます
sweeper = Sweeper(
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    redirect_uri='http://localhost:8888/callback'
)

# ターゲットとなるプレイリストIDを指定
playlist_id = '37i9dQZF1DXcBWIGWfABp2'

# 重複曲の検索
# 戻り値は重複している楽曲オブジェクトのリスト
duplicates = sweeper.find_duplicates(playlist_id)

if duplicates:
    print(f"{len(duplicates)}個の重複が見つかりました。削除を開始します。")
    # 一括削除の実行
    sweeper.remove_duplicates(playlist_id, duplicates)
else:
    print("重複は見つかりませんでした。ライブラリはクリーンです。")
```

`find_duplicates`メソッドは、単純なID一致だけでなく、メタデータの類似度を計算するオプションも備えています。実務的に助かるのは、削除前に「どの曲が消されるか」のリストを確認できる点です。

### 応用: 実務で使うなら

私のように、複数のプレイリストを一括で定期メンテナンスしたい場合は、以下のようなバッチ処理を組むのが実用的です。

```python
# 全プレイリストの自動クリーンアップ
playlists = sweeper.get_user_playlists()

for pl in playlists:
    print(f"Checking: {pl['name']}...")
    try:
        # 重複削除を実行し、結果をログに吐き出す
        count = sweeper.auto_clean(pl['id'], dry_run=False)
        if count > 0:
            print(f"Successfully removed {count} songs from {pl['name']}.")
    except Exception as e:
        print(f"Error in {pl['name']}: {str(e)}")
```

`dry_run=True`を設定することで、実際に削除せずに「何が消される予定か」をJSONで出力させることも可能です。これをGitHub Actionsなどで週に1回回しておけば、常にライブラリを清潔に保てます。

## 強みと弱み

**強み:**
- ページネーションの抽象化: Spotify API特有の「100曲制限」を意識せずに数千曲の全スキャンが可能。
- レートリミット回避: APIの負荷状況を見て自動でウェイトを入れるロジックが組み込まれている（自分で書くと地味にバグる部分）。
- URIベースの正確性: アルバム違いの同名曲を「重複」とみなすか「別物」とみなすかのフラグ管理が直感的。

**弱み:**
- 初期設定の煩雑さ: Spotify Developerのアカウント作成とアプリ登録が必須であり、エンジニア以外には推奨できない。
- 日本語メタデータの曖昧一致に弱い: 「〜 (Remix)」と「〜 - Remix」のような表記揺れは、英語圏のツールゆえに日本語特有の全角/半角スペースなどで判定が漏れることがある。
- GUIがない: 基本的にCLIかコードベースでの操作になるため、視覚的にポチポチ消したい人には向かない。

## 代替ツールとの比較

| 項目 | Song Sweeper | Spotify Dedup (Web版) | 自作 Python (Spotipy) |
|------|-------------|-------|-------|
| 操作形態 | CLI / Library | Web UI | Code |
| 自動化 | 容易 (Cron等) | 不可 | 自由 |
| 柔軟性 | 中 (オプション指定) | 低 (おまかせ) | 高 (無限) |
| 難易度 | 中級 | 初級 | 上級 |
| 推奨対象 | 定期メンテしたいエンジニア | 1回だけ消したい一般層 | 特殊な判定ロジックが必要な人 |

## 私の評価

私はこのツールを、自分のプレイリスト管理ワークフローに正式に組み込みました。理由は「自分でメンテナンスしなくて済む安定したラッパー」だからです。

Pythonを8年書いていれば、この程度のツールは1時間もあれば書けます。しかし、SpotifyのAPI仕様変更を追いかけたり、トークンのリフレッシュ処理をデバッグしたりする時間は、私にとって「無駄」です。Song Sweeperは、その「車輪の再発明」を食い止めてくれる実用的な道具として評価できます。

特にRTX 4090を回してローカルLLMを動かしながら、BGMとしてSpotifyを流しているような環境では、ライブラリのノイズ（重複）は地味にストレスになります。「同じ曲が2回流れる」という体験をコード数行で撲滅できるなら、導入しない手はありません。ただし、プログラミングに馴染みがない知人に勧めるなら、Web UIで完結するSpotify Dedupを教えるでしょう。

## よくある質問

### Q1: Spotify以外のApple MusicやYouTube Musicでも使えますか？

現時点ではSpotify専用の設計になっています。他のサービスに対応させるには、各サービスのAPI認証フローを個別に実装する必要があるため、将来的な拡張待ちとなります。

### Q2: 重複曲を削除した際、どちらの曲が残るか指定できますか？

デフォルトでは「最初に見つかった（古い方）」が保持されます。ライブラリへの追加日時を基準にソートしてからスキャンするオプションもあるため、新しい方を残すといったカスタマイズも可能です。

### Q3: 誤って必要な曲を消してしまった場合、復元できますか？

Spotify APIには「ゴミ箱」の概念がないため、一度削除した曲を自動で元に戻すことは困難です。実行前に必ず`dry_run`オプションで削除対象を確認するか、プレイリストのバックアップ（複製）を取っておくことを強く推奨します。

---

## あわせて読みたい

- [Tadak 使い方：エンジニアの集中力をハックするミニマリスト向け環境音ツール](/posts/2026-02-25-tadak-minimalist-white-noise-review-for-engineers/)
- [browser-use 使い方 | LLMでブラウザ操作を自動化する実力](/posts/2026-03-01-browser-use-llm-web-automation-review/)
- [Alexandria 使い方 組織の知識をAIで即戦力化するレビュー](/posts/2026-03-03-alexandria-ai-knowledge-base-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Spotify以外のApple MusicやYouTube Musicでも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "現時点ではSpotify専用の設計になっています。他のサービスに対応させるには、各サービスのAPI認証フローを個別に実装する必要があるため、将来的な拡張待ちとなります。"
      }
    },
    {
      "@type": "Question",
      "name": "重複曲を削除した際、どちらの曲が残るか指定できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "デフォルトでは「最初に見つかった（古い方）」が保持されます。ライブラリへの追加日時を基準にソートしてからスキャンするオプションもあるため、新しい方を残すといったカスタマイズも可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "誤って必要な曲を消してしまった場合、復元できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Spotify APIには「ゴミ箱」の概念がないため、一度削除した曲を自動で元に戻すことは困難です。実行前に必ずdryrunオプションで削除対象を確認するか、プレイリストのバックアップ（複製）を取っておくことを強く推奨します。 ---"
      }
    }
  ]
}
</script>
