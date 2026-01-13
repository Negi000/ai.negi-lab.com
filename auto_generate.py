#!/usr/bin/env python3
"""
Negi AI Lab - Auto Article Generator
=====================================
AIトレンド特化型の全自動ニュースサイト記事生成エンジン

カテゴリー構成比率:
  - NEWS (速報): 40%
  - TOOL (ツール検証): 40%
  - GUIDE (解説/ガイド): 20%

フォールバック機能により、ネタ不足時は次カテゴリーで補填し、
必ず指定された合計記事数を確保する。

Usage:
  python auto_generate.py --dry-run          # シミュレーションのみ
  python auto_generate.py --test-one         # 1件だけ生成してテスト
  python auto_generate.py --total 10         # 10記事生成
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, urlencode

import feedparser
import requests
from bs4 import BeautifulSoup

import google.generativeai as genai

# Twitter投稿用 (オプション)
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

# Optional: load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


# ============================================================
# Constants & Configuration
# ============================================================

JST = timezone(timedelta(hours=9))
SLEEP_SECONDS_PER_ARTICLE = 30
DEFAULT_TOTAL_ARTICLES = 2  # 1回の実行で2記事生成

# カテゴリー目標比率 (1日12記事: NEWS 5, TOOL 5, GUIDE 2)
CATEGORY_RATIOS = {
    "NEWS": 0.42,   # 5/12 ≈ 0.42
    "TOOL": 0.42,   # 5/12 ≈ 0.42
    "GUIDE": 0.16,  # 2/12 ≈ 0.16
}

# アフィリエイト設定
AMAZON_ASSOCIATE_TAG = os.environ.get("AMAZON_ASSOCIATE_TAG", "negi3939-22")
RAKUTEN_AFFILIATE_ID = os.environ.get("RAKUTEN_AFFILIATE_ID", "5000cbfd.5f52567b.5000cbff.924460a4")

# User-Agent for requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class Category(Enum):
    NEWS = "NEWS"
    TOOL = "TOOL"
    GUIDE = "GUIDE"


@dataclass
class NewsItem:
    """収集したニュースアイテム"""
    source: str
    title: str
    url: str
    category: Category
    published: str = ""
    summary: str = ""
    extra: Dict = field(default_factory=dict)


# ============================================================
# Processed URLs Store
# ============================================================

class ProcessedURLStore:
    """重複防止用のURL永続化ストア"""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._urls: List[str] = []
        self._dirty = False

    def load(self) -> List[str]:
        if not self.path.exists():
            self._urls = []
            return self._urls
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._urls = [str(x) for x in data] if isinstance(data, list) else []
        except Exception:
            self._urls = []
        return self._urls

    def contains(self, url: str) -> bool:
        if not self._urls:
            self.load()
        return url in self._urls

    def add(self, url: str) -> None:
        if not self._urls:
            self.load()
        if url not in self._urls:
            self._urls.append(url)
            self._dirty = True

    def save(self) -> None:
        if self._dirty:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self._urls, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self._dirty = False


# ============================================================
# News Collector
# ============================================================

class NewsCollector:
    """各ソースからニュースを収集するクラス"""

    def __init__(self, processed_store: ProcessedURLStore) -> None:
        self.processed_store = processed_store
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def _is_fresh(self, url: str) -> bool:
        """URLが未処理かどうか"""
        return not self.processed_store.contains(url)

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    # -------------------------
    # NEWS Sources
    # -------------------------

    def collect_news(self, max_items: int = 20) -> List[NewsItem]:
        """NEWS カテゴリー: Google News RSS から収集"""
        items: List[NewsItem] = []
        items.extend(self._collect_google_news(max_items))
        return items

    def _collect_google_news(self, max_items: int) -> List[NewsItem]:
        query = "Artificial Intelligence OR Gemini OR OpenAI OR Claude"
        rss_url = (
            "https://news.google.com/rss/search?"
            + urlencode({"q": query, "hl": "ja", "gl": "JP", "ceid": "JP:ja"})
        )

        try:
            resp = self.session.get(rss_url, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"  [!] Google News RSS fetch failed: {e}")
            return []

        feed = feedparser.parse(resp.content)
        entries = getattr(feed, "entries", []) or []

        results: List[NewsItem] = []
        for entry in entries[:max_items * 2]:  # 重複考慮して多めに取得
            url = (getattr(entry, "link", "") or "").strip()
            title = (getattr(entry, "title", "") or "").strip()
            published = (getattr(entry, "published", "") or "").strip()
            summary = self._normalize_text(getattr(entry, "summary", "") or "")

            if not url or not title:
                continue
            if not self._is_fresh(url):
                continue

            results.append(NewsItem(
                source="Google News",
                title=title,
                url=url,
                category=Category.NEWS,
                published=published,
                summary=summary[:500],
            ))

            if len(results) >= max_items:
                break

        return results

    # -------------------------
    # TOOL Sources
    # -------------------------

    def collect_tools(self, max_items: int = 20) -> List[NewsItem]:
        """TOOL カテゴリー: Product Hunt + GitHub Trending から収集"""
        items: List[NewsItem] = []

        # Product Hunt (半分)
        ph_items = self._collect_product_hunt(max_items // 2 + 2)
        items.extend(ph_items)

        # GitHub Trending (残り)
        remaining = max_items - len(items) + 5
        gh_items = self._collect_github_trending(remaining)
        items.extend(gh_items)

        return items[:max_items]

    def _collect_product_hunt(self, max_items: int) -> List[NewsItem]:
        """Product Hunt RSS から AI関連ツールを収集"""
        rss_url = "https://www.producthunt.com/feed"

        try:
            resp = self.session.get(rss_url, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"  [!] Product Hunt RSS fetch failed: {e}")
            return []

        feed = feedparser.parse(resp.content)
        entries = getattr(feed, "entries", []) or []

        # AI関連キーワードでフィルタ
        ai_keywords = ["ai", "gpt", "llm", "machine learning", "ml", "neural",
                       "copilot", "chatbot", "automation", "generative"]

        results: List[NewsItem] = []
        for entry in entries:
            url = (getattr(entry, "link", "") or "").strip()
            title = (getattr(entry, "title", "") or "").strip()
            summary = self._normalize_text(getattr(entry, "summary", "") or "")

            if not url or not title:
                continue

            # AI関連チェック
            text_lower = (title + " " + summary).lower()
            if not any(kw in text_lower for kw in ai_keywords):
                continue

            if not self._is_fresh(url):
                continue

            results.append(NewsItem(
                source="Product Hunt",
                title=title,
                url=url,
                category=Category.TOOL,
                summary=summary[:500],
            ))

            if len(results) >= max_items:
                break

        return results

    def _collect_github_trending(self, max_items: int) -> List[NewsItem]:
        """GitHub Trending (machine-learning) をスクレイピング"""
        url = "https://github.com/trending?since=daily&spoken_language_code=en"

        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"  [!] GitHub Trending fetch failed: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        repo_list = soup.select("article.Box-row")

        results: List[NewsItem] = []
        for repo in repo_list[:max_items * 2]:
            try:
                h2 = repo.select_one("h2 a")
                if not h2:
                    continue

                repo_path = h2.get("href", "").strip()
                if not repo_path:
                    continue

                repo_url = f"https://github.com{repo_path}"
                repo_name = repo_path.strip("/")

                # Description
                desc_elem = repo.select_one("p")
                description = self._normalize_text(desc_elem.get_text()) if desc_elem else ""

                # Stars today
                stars_elem = repo.select_one("span.d-inline-block.float-sm-right")
                stars_today = self._normalize_text(stars_elem.get_text()) if stars_elem else ""

                if not self._is_fresh(repo_url):
                    continue

                results.append(NewsItem(
                    source="GitHub Trending",
                    title=repo_name,
                    url=repo_url,
                    category=Category.TOOL,
                    summary=description[:500],
                    extra={"stars_today": stars_today},
                ))

                if len(results) >= max_items:
                    break

            except Exception:
                continue

        return results

    # -------------------------
    # GUIDE Sources
    # -------------------------

    def collect_guides(self, max_items: int = 20) -> List[NewsItem]:
        """GUIDE カテゴリー: Reddit + 定番トピックから収集"""
        items: List[NewsItem] = []

        # Reddit
        reddit_items = self._collect_reddit(max_items)
        items.extend(reddit_items)

        # 足りない場合は定番ガイドトピックで補填
        if len(items) < max_items:
            remaining = max_items - len(items)
            fallback_items = self._generate_guide_topics(remaining)
            items.extend(fallback_items)

        return items[:max_items]

    def _collect_reddit(self, max_items: int) -> List[NewsItem]:
        """Reddit (r/LocalLLaMA, r/OpenAI) の Top posts を収集"""
        subreddits = ["LocalLLaMA", "OpenAI", "MachineLearning", "artificial"]
        results: List[NewsItem] = []

        for subreddit in subreddits:
            if len(results) >= max_items:
                break

            # Reddit JSON API (認証不要)
            url = f"https://www.reddit.com/r/{subreddit}/top.json?t=week&limit=10"

            try:
                resp = self.session.get(url, timeout=20)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"  [!] Reddit r/{subreddit} fetch failed: {e}")
                continue

            posts = data.get("data", {}).get("children", [])
            for post in posts:
                post_data = post.get("data", {})
                title = post_data.get("title", "").strip()
                permalink = post_data.get("permalink", "")
                selftext = post_data.get("selftext", "")[:500]
                score = post_data.get("score", 0)

                if not title or not permalink:
                    continue

                post_url = f"https://www.reddit.com{permalink}"

                if not self._is_fresh(post_url):
                    continue

                # スコアが低すぎるものは除外
                if score < 50:
                    continue

                results.append(NewsItem(
                    source=f"Reddit r/{subreddit}",
                    title=title,
                    url=post_url,
                    category=Category.GUIDE,
                    summary=selftext,
                    extra={"score": score},
                ))

                if len(results) >= max_items:
                    break

        return results

    def _generate_guide_topics(self, count: int) -> List[NewsItem]:
        """定番ガイドトピック（フォールバック用）"""
        topics = [
            ("ローカルLLMのセットアップガイド（2024年版）", "local-llm-setup"),
            ("Ollama + Open WebUIで自宅AIチャットを構築する方法", "ollama-webui-setup"),
            ("RAGパイプラインの基礎と実装入門", "rag-pipeline-intro"),
            ("LoRAファインチューニング完全ガイド", "lora-finetuning-guide"),
            ("LangChainでエージェントを作る方法", "langchain-agent-tutorial"),
            ("Hugging Face Transformersクイックスタート", "hf-transformers-quickstart"),
            ("GPT-4 APIのベストプラクティス", "gpt4-api-best-practices"),
            ("Stable Diffusion XLプロンプトエンジニアリング", "sdxl-prompt-engineering"),
            ("LLMのコンテキスト長を最大限活用するテクニック", "llm-context-length-tips"),
            ("AIコーディングアシスタント徹底比較", "ai-coding-assistant-comparison"),
            ("Gemini API入門：最初のアプリを作る", "gemini-api-getting-started"),
            ("Claude APIの使い方とTips", "claude-api-tips"),
            ("ベクトルデータベース選定ガイド", "vector-db-comparison"),
            ("プロンプトインジェクション対策入門", "prompt-injection-defense"),
            ("マルチモーダルAIの活用事例集", "multimodal-ai-use-cases"),
        ]

        random.shuffle(topics)
        results: List[NewsItem] = []

        for title, slug in topics[:count]:
            # 仮のURLを生成（実際にはURLなしで記事生成）
            fake_url = f"guide://{slug}-{uuid.uuid4().hex[:6]}"

            if not self._is_fresh(fake_url):
                continue

            results.append(NewsItem(
                source="Negi Lab Guide",
                title=title,
                url=fake_url,
                category=Category.GUIDE,
                summary="",
                extra={"is_generated_topic": True},
            ))

        return results


# ============================================================
# Article Result Data Class
# ============================================================

@dataclass
class ArticleResult:
    """記事生成結果を保持するデータクラス"""
    title: str
    body: str
    shopping_keyword: Optional[str] = None
    viral_tags: Optional[str] = None  # "#タグ1 #タグ2" 形式


# ============================================================
# Article Generator
# ============================================================

class ArticleGenerator:
    """Gemini APIを使用してカテゴリー別の記事を生成"""

    def __init__(self, api_key: str, model_name: str = "gemini-3-flash-preview") -> None:
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_article(self, item: NewsItem) -> ArticleResult:
        """
        記事を生成し、ArticleResultを返す。
        """
        prompt = self._build_prompt(item)

        try:
            response = self.model.generate_content(prompt)
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e}")

        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned empty response")

        # 外側の```markdownフェンスのみ除去（内部のコードブロックは保持）
        cleaned = text.strip()
        
        # 先頭のフェンス除去
        if cleaned.startswith("```markdown"):
            cleaned = cleaned[len("```markdown"):].strip()
        elif cleaned.startswith("```md"):
            cleaned = cleaned[len("```md"):].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:].strip()
        
        # 末尾のフェンス除去（本文末の単独```のみ対象）
        lines = cleaned.split("\n")
        while lines and lines[-1].strip() == "```":
            lines.pop()
        cleaned = "\n".join(lines).strip()

        return self._extract_title_and_body(cleaned)

    def _build_prompt(self, item: NewsItem) -> str:
        """カテゴリーに応じたプロンプトを構築"""

        if item.category == Category.NEWS:
            return self._build_news_prompt(item)
        elif item.category == Category.TOOL:
            return self._build_tool_prompt(item)
        else:  # GUIDE
            return self._build_guide_prompt(item)

    def _build_news_prompt(self, item: NewsItem) -> str:
        return f'''あなたは「Negi Lab」所属の辛口だが技術に詳しいAI研究員です。
読者はエンジニアやビジネスマン。実用性と技術的視点を重視して執筆してください。

【元ニュース情報】
- タイトル: {item.title}
- URL: {item.url}
- 出典: {item.source}
{f"- 要約: {item.summary}" if item.summary else ""}

【指示】
速報ニュース記事を書いてください。
- 何が発表されたか
- 競合（ChatGPT, Claude等）との違いは何か
- 業界への影響を論理的に解説

【出力形式】必ず以下のMarkdown構造で出力すること。

1行目: タイトル（装飾なし、## などは付けない）

## 3行要約

- 要約1
- 要約2
- 要約3

## 何が発表されたのか

（詳細な解説）

## 競合との比較

| 項目 | 今回の発表 | ChatGPT | Claude |
|------|-----------|---------|--------|
| ... | ... | ... | ... |

## 業界への影響

（論理的な分析）

## Negi Labの見解

（辛口だが建設的なコメント）

---
### 【重要】キーワード選定タスク
記事執筆後、以下の2種類のキーワードセットを選定し、記事の末尾に指定のフォーマットで追記してください。

**1. 商品検索キーワード (Shopping Keyword)**
読者がAmazonや楽天で検索ボタンを押した際、最も適切な商品一覧が表示されるような「具体的な製品名」や「型番」を選定すること。
- **禁止:** 「PC」「GPU」のような広すぎる1単語（ノイズ商品が混ざる）
- **禁止:** 長すぎる正式名称（検索ヒット0になる）
- **推奨:** **2〜3単語**の組み合わせ（例: "MacBook Air M3", "RTX 4070 Ti", "Python オライリー"）
- フォーマット: `[SHOPPING: キーワード]`

**2. SNS拡散用ハッシュタグ (Viral Tags)**
X (Twitter) でインプレッションを稼ぐための、需要があり記事内容に関連するトレンドワード。
- **日本語で、ハッシュタグ（#）付きで2つだけ**選定
- 商品名ではなく「興味関心軸」で選ぶ（例: RTX4090の記事なら `#自作PC` `#ゲーミングPC`）
- フォーマット: `[HASHTAGS: #タグ1 #タグ2]`
---

【禁止事項】
- YAML/TOML Front Matterは出力しない
- HTMLタグは使わない
'''

    def _build_tool_prompt(self, item: NewsItem) -> str:
        stars_info = f"- 今日のスター数: {item.extra['stars_today']}" if item.extra.get("stars_today") else ""

        return f'''あなたは「Negi Lab」所属の辛口だが技術に詳しいAI研究員です。
読者はエンジニアやビジネスマン。実用性と技術的視点を重視して執筆してください。

【対象ツール情報】
- 名前: {item.title}
- URL: {item.url}
- 出典: {item.source}
{f"- 説明: {item.summary}" if item.summary else ""}
{stars_info}

【指示】
「**検証シミュレーション**」を含むツールレビュー記事を書いてください。
実際にそのツールをインストールして動かしたと仮定し、以下を含めること：
- 具体的なPythonコード例（動作する風のコード）
- 実行結果の例（架空でOK）
- プロンプト例（該当する場合）

※記事冒頭に「これはシミュレーションであり実測ではありません」と明記すること。

【出力形式】必ず以下のMarkdown構造で出力すること。

1行目: タイトル（装飾なし、キャッチーに）

> ⚠️ 本記事の検証パートはシミュレーションであり、実際の測定結果ではありません。

## 3行要約

- 要約1
- 要約2
- 要約3

## このツールは何か

（概要説明）

## 検証シミュレーション：実際に使ってみた

### 環境構築

```bash
pip install xxx
```

### 基本的な使い方

```python
# サンプルコード（架空でOK）
from xxx import YYY

model = YYY()
result = model.run("テスト入力")
print(result)
```

### 実行結果

```
（架空の出力例）
```

## メリット・デメリット

### メリット
- ...

### デメリット
- ...

## 結論：Negi Labの評価

（星評価: ★★★☆☆ のような形式も可）

---
### 【重要】キーワード選定タスク
記事執筆後、以下の2種類のキーワードセットを選定し、記事の末尾に指定のフォーマットで追記してください。

**1. 商品検索キーワード (Shopping Keyword)**
読者がAmazonや楽天で検索ボタンを押した際、最も適切な商品一覧が表示されるような「具体的な製品名」や「型番」を選定すること。
- **禁止:** 「PC」「GPU」のような広すぎる1単語（ノイズ商品が混ざる）
- **禁止:** 長すぎる正式名称（検索ヒット0になる）
- **推奨:** **2〜3単語**の組み合わせ（例: "RTX 4090", "Raspberry Pi 5", "Python 入門書"）
- フォーマット: `[SHOPPING: キーワード]`

**2. SNS拡散用ハッシュタグ (Viral Tags)**
X (Twitter) でインプレッションを稼ぐための、需要があり記事内容に関連するトレンドワード。
- **日本語で、ハッシュタグ（#）付きで2つだけ**選定
- 商品名ではなく「興味関心軸」で選ぶ（例: 開発ツールの記事なら `#プログラミング` `#エンジニア`）
- フォーマット: `[HASHTAGS: #タグ1 #タグ2]`
---

【禁止事項】
- YAML/TOML Front Matterは出力しない
- HTMLタグは使わない
'''

    def _build_guide_prompt(self, item: NewsItem) -> str:
        is_generated = item.extra.get("is_generated_topic", False)
        topic_info = f"- トピック: {item.title}" if is_generated else f'''- タイトル: {item.title}
- URL: {item.url}
- 出典: {item.source}
{f"- 内容: {item.summary}" if item.summary else ""}'''

        return f'''あなたは「Negi Lab」所属の辛口だが技術に詳しいAI研究員です。
読者はエンジニアやビジネスマン。実用性と技術的視点を重視して執筆してください。

【トピック情報】
{topic_info}

【指示】
チュートリアル形式のガイド記事を書いてください。
「〜する方法」「エラー回避手順」など、読者が手元で試せるステップバイステップの手順書として書くこと。
- 具体的なコマンド例
- コード例
- 設定ファイルの例
を必ず含めること。

【出力形式】必ず以下のMarkdown構造で出力すること。

1行目: タイトル（装飾なし、「〜する方法」「〜入門」形式推奨）

## この記事で学べること

- ポイント1
- ポイント2
- ポイント3

## 前提条件

- 必要なもの1
- 必要なもの2

## Step 1: 環境準備

```bash
# コマンド例
```

## Step 2: 基本設定

```python
# 設定コード例
```

## Step 3: 実行と確認

（手順の説明）

## よくあるエラーと対処法

### エラー1: xxx

```
エラーメッセージ例
```

**解決策:** ...

## まとめと次のステップ

（締めの言葉と、次に学ぶべきことへの誘導）

---
### 【重要】キーワード選定タスク
記事執筆後、以下の2種類のキーワードセットを選定し、記事の末尾に指定のフォーマットで追記してください。

**1. 商品検索キーワード (Shopping Keyword)**
読者がAmazonや楽天で検索ボタンを押した際、最も適切な商品一覧が表示されるような「具体的な製品名」や「型番」を選定すること。
- **禁止:** 「PC」「GPU」のような広すぎる1単語（ノイズ商品が混ざる）
- **禁止:** 長すぎる正式名称（検索ヒット0になる）
- **推奨:** **2〜3単語**の組み合わせ（例: "NVIDIA Jetson Nano", "Arduino スターターキット", "機械学習 入門書"）
- フォーマット: `[SHOPPING: キーワード]`

**2. SNS拡散用ハッシュタグ (Viral Tags)**
X (Twitter) でインプレッションを稼ぐための、需要があり記事内容に関連するトレンドワード。
- **日本語で、ハッシュタグ（#）付きで2つだけ**選定
- 商品名ではなく「興味関心軸」で選ぶ（例: チュートリアル記事なら `#プログラミング初心者` `#独学`）
- フォーマット: `[HASHTAGS: #タグ1 #タグ2]`
---

【禁止事項】
- YAML/TOML Front Matterは出力しない
- HTMLタグは使わない
'''

    def _extract_title_and_body(self, text: str) -> ArticleResult:
        """
        Gemini出力からタイトル、本文、キーワード、ハッシュタグを抽出。
        """
        lines = [ln.rstrip() for ln in text.splitlines()]
        title = ""
        body_start = 0

        for i, ln in enumerate(lines):
            stripped = ln.strip()
            if stripped:
                # タイトル行を抽出
                title = stripped.strip('"').strip("'")
                title = re.sub(r"^#{1,6}\s+", "", title).strip()
                body_start = i + 1
                break

        if not title:
            title = "AIトレンド記事（自動生成）"

        body = "\n".join(lines[body_start:]).lstrip("\n")
        if not body:
            body = "(本文生成に失敗しました)"

        # ダブルキーワード抽出とアフィリエイトリンク追加
        body, shopping_keyword, viral_tags = self._extract_keywords_and_add_affiliate(body)

        return ArticleResult(
            title=title,
            body=body,
            shopping_keyword=shopping_keyword,
            viral_tags=viral_tags,
        )

    def _extract_keywords_and_add_affiliate(self, body: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        本文から[SHOPPING: xxx]と[HASHTAGS: xxx]を抽出し、アフィリエイトリンクを追加する。
        
        Returns:
            (処理済み本文, shopping_keyword, viral_tags)
        """
        # 1. Shopping Keyword 抽出
        shopping_pattern = r'\[SHOPPING:\s*(.+?)\]'
        shopping_match = re.search(shopping_pattern, body)
        shopping_keyword = None
        if shopping_match:
            shopping_keyword = shopping_match.group(1).strip()
            # 行全体を削除（前後の空行も含む）
            body = re.sub(r'\n*\[SHOPPING:[^\]]+\]\n*', '\n', body)
        
        # 2. Viral Tags 抽出
        hashtags_pattern = r'\[HASHTAGS:\s*(.+?)\]'
        hashtags_match = re.search(hashtags_pattern, body)
        viral_tags = None
        if hashtags_match:
            viral_tags = hashtags_match.group(1).strip()
            # 行全体を削除（前後の空行も含む）
            body = re.sub(r'\n*\[HASHTAGS:[^\]]+\]\n*', '\n', body)
        
        # 3. 旧形式の[KEYWORD: xxx]も念のため除去（互換性）
        body = re.sub(r'\n*\[KEYWORD:[^\]]+\]\n*', '\n', body)
        
        # 4. 末尾の「---」以降のキーワード選定タスク指示も除去
        body = re.sub(r'\n---\n### 【重要】キーワード選定タスク[\s\S]*$', '', body)
        
        # 5. クリーンアップ（連続する空行を整理）
        body = re.sub(r'\n{3,}', '\n\n', body).strip()
        
        # 6. アフィリエイトリンクを追加
        if shopping_keyword:
            affiliate_section = self._generate_affiliate_links(shopping_keyword)
            body = body + "\n\n" + affiliate_section
        
        return body, shopping_keyword, viral_tags

    def _generate_affiliate_links(self, keyword: str) -> str:
        """
        キーワードからAmazon/楽天のアフィリエイトリンクボタンを生成。
        """
        encoded_keyword = quote(keyword, safe="")
        
        amazon_url = f"https://www.amazon.co.jp/s?k={encoded_keyword}&tag={AMAZON_ASSOCIATE_TAG}"
        rakuten_url = f"https://search.rakuten.co.jp/search/mall/{encoded_keyword}/?scid={RAKUTEN_AFFILIATE_ID}"
        
        # Markdown + インラインCSS でボタン風リンクを生成
        affiliate_html = f'''
---

## 関連商品をチェック

<div style="display: flex; gap: 12px; flex-wrap: wrap; margin: 20px 0;">
  <a href="{amazon_url}" target="_blank" rel="noopener noreferrer sponsored" style="display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; background: linear-gradient(135deg, #ff9900 0%, #ff6600 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: bold; box-shadow: 0 4px 12px rgba(255, 153, 0, 0.3); transition: transform 0.2s;">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
    Amazonで「{keyword}」を検索
  </a>
  <a href="{rakuten_url}" target="_blank" rel="noopener noreferrer sponsored" style="display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; background: linear-gradient(135deg, #bf0000 0%, #8b0000 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: bold; box-shadow: 0 4px 12px rgba(191, 0, 0, 0.3); transition: transform 0.2s;">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
    楽天で「{keyword}」を検索
  </a>
</div>

<small style="color: #888;">※上記リンクはアフィリエイトリンクです。購入により当サイトに収益が発生する場合があります。</small>
'''
        return affiliate_html


# ============================================================
# Image Handler
# ============================================================

class ImageHandler:
    """Pollinations.ai を使用した画像生成・ローカル保存"""

    def __init__(self, api_key: str, model_name: str = "gemini-3-flash-preview") -> None:
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_and_save_image(
        self,
        title: str,
        body: str,
        category: Category,
        article_id: str,
        output_dir: Path,
    ) -> str:
        """
        記事内容に基づいた画像を生成しローカルに保存。
        
        Args:
            title: 記事タイトル
            body: 記事本文
            category: カテゴリー
            article_id: 記事ID（ファイル名用）
            output_dir: 画像保存先ディレクトリ (static/images/posts/)
        
        Returns:
            Hugo用の相対パス (例: /images/posts/2026-01-13-abc123.png)
        """
        # プロンプト生成
        prompt_en = self._generate_image_prompt(title, body, category)
        
        # Pollinations.aiから画像をダウンロード
        encoded = quote(prompt_en, safe="")
        image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1200&height=630&nologo=true"
        
        try:
            response = requests.get(image_url, timeout=60)
            response.raise_for_status()
            
            # 保存先ディレクトリ作成
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイル保存
            filename = f"{article_id}.png"
            file_path = output_dir / filename
            file_path.write_bytes(response.content)
            
            # Hugo用相対パス
            return f"/images/posts/{filename}"
            
        except Exception as e:
            print(f"  [Image] Download failed: {e}")
            # フォールバック: URLを返す（レート制限時用）
            return image_url

    def download_image_to_bytes(self, image_path_or_url: str, static_dir: Path) -> Optional[bytes]:
        """
        画像をバイトデータとして取得（Twitter投稿用）。
        
        Args:
            image_path_or_url: ローカルパス（/images/posts/xxx.png）またはURL
            static_dir: staticディレクトリのパス
        
        Returns:
            画像のバイトデータ
        """
        try:
            if image_path_or_url.startswith("http"):
                # URLの場合はダウンロード
                response = requests.get(image_path_or_url, timeout=30)
                response.raise_for_status()
                return response.content
            else:
                # ローカルパスの場合はファイル読み込み
                # /images/posts/xxx.png -> static/images/posts/xxx.png
                local_path = static_dir / image_path_or_url.lstrip("/")
                if local_path.exists():
                    return local_path.read_bytes()
                return None
        except Exception as e:
            print(f"  [Image] Failed to load: {e}")
            return None

    def _generate_image_prompt(self, title: str, body: str, category: Category) -> str:
        style_hint = {
            Category.NEWS: "news broadcast, breaking news style, professional, no text",
            Category.TOOL: "software interface, tech product, modern UI, no text",
            Category.GUIDE: "tutorial, educational diagram, clean design, no text",
        }.get(category, "technology")

        prompt = (
            "Create ONE English image generation prompt for a blog thumbnail.\n"
            "Rules:\n"
            "- Output ONE line only, no quotes\n"
            "- English only\n"
            "- MUST NOT include any text, logos, watermarks, QR codes, or UI elements\n"
            "- Focus on abstract visuals, technology imagery, or symbolic representations\n"
            f"- Style hint: {style_hint}\n"
            "- Make it modern, clean, professional\n\n"
            f"Blog title: {title}\n"
            f"Content preview: {body[:500]}\n"
        )

        try:
            response = self.model.generate_content(prompt)
            text = getattr(response, "text", None)
            if text:
                one_line = text.strip().splitlines()[0].strip().strip('"').strip("'")
                if one_line:
                    return one_line
        except Exception:
            pass

        # Fallback
        return f"Abstract futuristic technology visualization, {style_hint}, minimalist, high quality, 4k, no text"


# ============================================================
# Twitter (X) Poster
# ============================================================

class TwitterPoster:
    """X (Twitter) への自動投稿を行うクラス（無料プラン対応）"""

    def __init__(self) -> None:
        """
        環境変数から認証情報を読み込み、Tweepy Clientを初期化。
        
        必要な環境変数 (OAuth 1.0a):
          - TWITTER_API_KEY (Consumer Key)
          - TWITTER_API_SECRET (Consumer Secret)
          - TWITTER_ACCESS_TOKEN
          - TWITTER_ACCESS_TOKEN_SECRET
        
        オプション (OAuth 2.0 - 将来の拡張用):
          - TWITTER_CLIENT_ID
          - TWITTER_CLIENT_SECRET
        """
        if not TWEEPY_AVAILABLE:
            raise RuntimeError("tweepy is not installed. Run: pip install tweepy")

        self.api_key = os.getenv("TWITTER_API_KEY", "")
        self.api_secret = os.getenv("TWITTER_API_SECRET", "")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            raise RuntimeError("Twitter API credentials not configured in environment variables")

        # v1.1 API (for media upload - requires Basic plan $100/month)
        auth = tweepy.OAuth1UserHandler(
            self.api_key,
            self.api_secret,
            self.access_token,
            self.access_token_secret,
        )
        self.api_v1 = tweepy.API(auth)

        # v2 API (for tweeting - works with Free plan)
        self.client = tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
        )

    def post_article(
        self,
        title: str,
        url: str,
        category: Category,
        viral_tags: Optional[str] = None,
    ) -> bool:
        """
        記事をTwitterに投稿する（URLのみ、Twitterカードで画像表示）。

        Args:
            title: 記事タイトル
            url: 記事のURL (Twitterカードで自動的にOGP画像が表示される)
            category: 記事カテゴリー
            viral_tags: Geminiが選んだSNS拡散用ハッシュタグ（例: "#自作PC #ゲーミング"）

        Returns:
            投稿成功時True
        """
        try:
            # カテゴリー別アイコン
            category_icons = {
                Category.NEWS: "📰",
                Category.TOOL: "🛠️",
                Category.GUIDE: "📖",
            }
            icon = category_icons.get(category, "📢")

            # タイトルを短縮（80文字制限）
            max_title_len = 80
            short_title = title[:max_title_len] + "..." if len(title) > max_title_len else title

            # ハッシュタグ構成
            # viral_tags が "#タグ1 #タグ2" 形式で来る想定
            # フォールバック: viral_tags がない場合はカテゴリに応じたデフォルト
            if viral_tags:
                # Geminiが選んだタグを使用
                tag_str = viral_tags
            else:
                # フォールバック用デフォルトタグ
                default_tags = {
                    Category.NEWS: "#AI速報 #テック",
                    Category.TOOL: "#開発ツール #エンジニア",
                    Category.GUIDE: "#プログラミング #学習",
                }
                tag_str = default_tags.get(category, "#AI #テック")

            # ツイート本文を構成
            # {icon} {タイトル}
            # 詳細はこちら👇
            # {URL}
            # {viral_tags} #NegiLab
            tweet_text = f"{icon} {short_title}\n\n詳細はこちら👇\n{url}\n\n{tag_str} #NegiLab"

            # テキストのみで投稿（URLからTwitterカードが生成される）
            self.client.create_tweet(text=tweet_text)

            return True

        except Exception as e:
            print(f"  [Twitter] Error: {e}")
            return False


def is_twitter_configured() -> bool:
    """Twitter API認証情報が設定されているか確認"""
    required = [
        "TWITTER_API_KEY",
        "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_TOKEN_SECRET",
    ]
    return all(os.getenv(key) for key in required)


# ============================================================
# Hugo Markdown Writer
# ============================================================

def write_hugo_markdown(
    out_path: Path,
    title: str,
    date_jst: datetime,
    image_url: str,
    category: Category,
    tags: List[str],
    body: str,
) -> None:
    """Hugo形式のMarkdownファイルを出力（PaperModテーマ対応）"""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # カテゴリー名をHugo用に変換
    category_map = {
        Category.NEWS: "AI News",
        Category.TOOL: "AI Tools",
        Category.GUIDE: "AI Guide",
    }
    category_name = category_map.get(category, "AI News")

    # PaperModテーマはcover.imageを使用
    fm_lines = [
        "---",
        f'title: "{title.replace(chr(34), "")}"',
        f"date: {date_jst.isoformat()}",
        "cover:",
        f'  image: "{image_url}"',
        "  alt: \"AI generated thumbnail\"",
        "  relative: false",
        "categories:",
        f'  - "{category_name}"',
        "tags:",
        *[f'  - "{t}"' for t in tags],
        "---",
        "",
    ]

    content = "\n".join(fm_lines) + body.strip() + "\n"
    out_path.write_text(content, encoding="utf-8")


# ============================================================
# Twitter Posting Queue (デプロイ後投稿用)
# ============================================================

@dataclass
class TwitterQueueItem:
    """X投稿キューのアイテム"""
    article_id: str
    title: str
    url: str
    category: str  # "NEWS", "TOOL", "GUIDE"
    viral_tags: Optional[str]
    created_at: str


class TwitterPostingQueue:
    """X投稿キューの管理（JSON永続化）"""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._queue: List[Dict] = []

    def load(self) -> List[Dict]:
        if not self.path.exists():
            self._queue = []
            return self._queue
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._queue = data if isinstance(data, list) else []
        except Exception:
            self._queue = []
        return self._queue

    def add(self, item: TwitterQueueItem) -> None:
        if not self._queue:
            self.load()
        self._queue.append({
            "article_id": item.article_id,
            "title": item.title,
            "url": item.url,
            "category": item.category,
            "viral_tags": item.viral_tags,
            "created_at": item.created_at,
            "posted": False,
        })
        self._save()

    def get_pending(self) -> List[Dict]:
        if not self._queue:
            self.load()
        return [item for item in self._queue if not item.get("posted", False)]

    def mark_posted(self, article_id: str) -> None:
        if not self._queue:
            self.load()
        for item in self._queue:
            if item["article_id"] == article_id:
                item["posted"] = True
        self._save()

    def get_by_id(self, article_id: str) -> Optional[Dict]:
        if not self._queue:
            self.load()
        for item in self._queue:
            if item["article_id"] == article_id:
                return item
        return None

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._queue, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def post_single_article_to_twitter(article_id: str) -> int:
    """
    指定した記事IDをXに投稿する（デプロイ完了後に使用）。
    
    Usage: python auto_generate.py --post-twitter 2026-01-14-abc12345
    """
    print("=" * 60)
    print("Negi AI Lab - Post to X (Twitter)")
    print("=" * 60)
    print(f"Article ID: {article_id}")
    print()

    # キューから記事情報を取得
    repo_root = Path(__file__).resolve().parent
    queue = TwitterPostingQueue(repo_root / "twitter_queue.json")
    queue.load()

    item = queue.get_by_id(article_id)
    if not item:
        print(f"[ERROR] Article ID '{article_id}' not found in queue.")
        print("  Run article generation first, or check twitter_queue.json")
        return 1

    if item.get("posted", False):
        print(f"[WARN] Article already posted to X.")
        return 0

    # Twitter認証チェック
    if not is_twitter_configured():
        print("[ERROR] Twitter API credentials not configured.")
        return 2

    if not TWEEPY_AVAILABLE:
        print("[ERROR] tweepy is not installed.")
        return 2

    try:
        poster = TwitterPoster()
        
        # カテゴリー文字列をEnumに変換
        category_map = {
            "NEWS": Category.NEWS,
            "TOOL": Category.TOOL,
            "GUIDE": Category.GUIDE,
        }
        category = category_map.get(item["category"], Category.NEWS)

        success = poster.post_article(
            title=item["title"],
            url=item["url"],
            category=category,
            viral_tags=item.get("viral_tags"),
        )

        if success:
            queue.mark_posted(article_id)
            print(f"✓ Successfully posted to X!")
            print(f"  Title: {item['title'][:50]}...")
            print(f"  URL: {item['url']}")
            return 0
        else:
            print("✗ Failed to post to X.")
            return 1

    except Exception as e:
        print(f"[ERROR] {e}")
        return 1


def post_all_pending_to_twitter() -> int:
    """
    キュー内の未投稿記事をすべてXに投稿する。
    
    Usage: python auto_generate.py --post-all-twitter
    """
    print("=" * 60)
    print("Negi AI Lab - Post All Pending to X")
    print("=" * 60)

    repo_root = Path(__file__).resolve().parent
    queue = TwitterPostingQueue(repo_root / "twitter_queue.json")
    pending = queue.get_pending()

    if not pending:
        print("No pending articles to post.")
        return 0

    print(f"Found {len(pending)} pending articles.")
    print()

    if not is_twitter_configured() or not TWEEPY_AVAILABLE:
        print("[ERROR] Twitter not configured or tweepy not installed.")
        return 2

    poster = TwitterPoster()
    success_count = 0

    for item in pending:
        print(f"Posting: {item['title'][:40]}...")
        
        category_map = {
            "NEWS": Category.NEWS,
            "TOOL": Category.TOOL,
            "GUIDE": Category.GUIDE,
        }
        category = category_map.get(item["category"], Category.NEWS)

        if poster.post_article(
            title=item["title"],
            url=item["url"],
            category=category,
            viral_tags=item.get("viral_tags"),
        ):
            queue.mark_posted(item["article_id"])
            print(f"  ✓ Posted!")
            success_count += 1
        else:
            print(f"  ✗ Failed")
        
        # レート制限対策
        time.sleep(5)

    print()
    print(f"Posted {success_count}/{len(pending)} articles.")
    return 0 if success_count == len(pending) else 1


# ============================================================
# Fallback Logic Calculator
# ============================================================

def calculate_targets_with_fallback(
    total: int,
    available: Dict[Category, int],
) -> Dict[Category, int]:
    """
    フォールバックロジック付きの目標数計算。

    Args:
        total: 合計目標記事数
        available: 各カテゴリーで利用可能な記事数

    Returns:
        各カテゴリーで実際に生成する記事数
    """
    # 初期目標
    targets = {
        Category.NEWS: int(total * CATEGORY_RATIOS["NEWS"]),
        Category.TOOL: int(total * CATEGORY_RATIOS["TOOL"]),
        Category.GUIDE: total,  # GUIDEは残り全部を受け持つ
    }

    # 端数調整（NEWSとTOOLの合計がtotalを超えないように）
    targets[Category.GUIDE] = total - targets[Category.NEWS] - targets[Category.TOOL]

    final = {}
    carryover = 0

    # 優先順: NEWS → TOOL → GUIDE
    for cat in [Category.NEWS, Category.TOOL, Category.GUIDE]:
        target_with_carry = targets[cat] + carryover
        actual = min(target_with_carry, available.get(cat, 0))
        final[cat] = actual
        carryover = target_with_carry - actual

    return final


# ============================================================
# Main Entry Point
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Negi AI Lab - Auto Article Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--total", "-n",
        type=int,
        default=DEFAULT_TOTAL_ARTICLES,
        help=f"合計生成記事数 (default: {DEFAULT_TOTAL_ARTICLES})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="APIを叩かず、収集とフォールバック計算のシミュレーションのみ実行",
    )
    parser.add_argument(
        "--test-one",
        action="store_true",
        help="最初の1件だけ実際に生成して品質確認",
    )
    parser.add_argument(
        "--skip-twitter",
        action="store_true",
        help="X (Twitter) への投稿をスキップ（GitHub Actions用）",
    )
    parser.add_argument(
        "--post-twitter",
        type=str,
        metavar="ARTICLE_ID",
        help="指定した記事IDをXに投稿（デプロイ完了後に使用）",
    )
    parser.add_argument(
        "--post-all-twitter",
        action="store_true",
        help="キュー内の未投稿記事をすべてXに投稿",
    )

    args = parser.parse_args()
    
    # --post-twitter モードの場合は専用処理
    if args.post_twitter:
        return post_single_article_to_twitter(args.post_twitter)
    
    # --post-all-twitter モードの場合は専用処理
    if args.post_all_twitter:
        return post_all_pending_to_twitter()
    
    total = args.total
    dry_run = args.dry_run
    test_one = args.test_one
    skip_twitter = args.skip_twitter

    print("=" * 60)
    print("Negi AI Lab - Auto Article Generator")
    print("=" * 60)
    print(f"Total target: {total} articles")
    print(f"Mode: {'DRY-RUN' if dry_run else ('TEST-ONE' if test_one else 'FULL')}")
    print()

    repo_root = Path(__file__).resolve().parent
    processed_store = ProcessedURLStore(repo_root / "processed_urls.json")
    processed_store.load()

    # API Key check (dry-run以外で必須)
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key and not dry_run:
        print("[ERROR] GEMINI_API_KEY is not set.")
        return 2

    # -------------------------
    # Step 1: Collect items
    # -------------------------
    print("[Step 1] Collecting news items...")
    collector = NewsCollector(processed_store)

    news_items = collector.collect_news(max_items=total)
    tool_items = collector.collect_tools(max_items=total)
    guide_items = collector.collect_guides(max_items=total)

    available = {
        Category.NEWS: len(news_items),
        Category.TOOL: len(tool_items),
        Category.GUIDE: len(guide_items),
    }

    print(f"  NEWS:  {available[Category.NEWS]} items found")
    print(f"  TOOL:  {available[Category.TOOL]} items found")
    print(f"  GUIDE: {available[Category.GUIDE]} items found")
    print()

    # -------------------------
    # Step 2: Calculate with fallback
    # -------------------------
    print("[Step 2] Calculating targets with fallback...")
    targets = calculate_targets_with_fallback(total, available)

    print(f"  NEWS:  {targets[Category.NEWS]} (target: {int(total * 0.4)})")
    print(f"  TOOL:  {targets[Category.TOOL]} (target: {int(total * 0.4)})")
    print(f"  GUIDE: {targets[Category.GUIDE]} (target: {total - int(total * 0.4) * 2})")
    print(f"  Total: {sum(targets.values())}")
    print()

    # -------------------------
    # Build final item list
    # -------------------------
    final_items: List[NewsItem] = []
    final_items.extend(news_items[:targets[Category.NEWS]])
    final_items.extend(tool_items[:targets[Category.TOOL]])
    final_items.extend(guide_items[:targets[Category.GUIDE]])

    # -------------------------
    # Dry-run: Show simulation and exit
    # -------------------------
    if dry_run:
        print("[DRY-RUN] Simulation Results:")
        print("-" * 60)
        for i, item in enumerate(final_items, 1):
            print(f"{i:2}. [{item.category.value:5}] {item.title[:50]}...")
            print(f"     Source: {item.source}")
            print(f"     URL: {item.url[:60]}...")
            print(f"     [DryRun] Would post to X: {item.title[:40]}...")
            print()
        print("-" * 60)
        print(f"Total: {len(final_items)} articles would be generated.")
        print("(No files written, no URLs logged, no X posts)")
        return 0

    # -------------------------
    # Step 3: Generate articles
    # -------------------------
    if not final_items:
        print("[!] No items to generate.")
        return 0

    generator = ArticleGenerator(api_key=api_key, model_name="gemini-3-flash-preview")
    image_handler = ImageHandler(api_key=api_key, model_name="gemini-3-flash-preview")
    out_dir = repo_root / "content" / "posts"
    static_dir = repo_root / "static"
    images_dir = static_dir / "images" / "posts"

    # Twitter Poster (optional)
    twitter_poster: Optional[TwitterPoster] = None
    twitter_enabled = is_twitter_configured() and TWEEPY_AVAILABLE
    if twitter_enabled:
        try:
            twitter_poster = TwitterPoster()
            print("[Twitter] API configured and ready.")
        except Exception as e:
            print(f"[Twitter] Disabled: {e}")
            twitter_poster = None
    else:
        if not TWEEPY_AVAILABLE:
            print("[Twitter] Disabled: tweepy not installed")
        else:
            print("[Twitter] Disabled: API credentials not configured")

    # test-one: 1件だけ
    if test_one:
        final_items = final_items[:1]
        print("[TEST-ONE] Generating 1 article only...")
    else:
        print(f"[Step 3] Generating {len(final_items)} articles...")

    print()

    # サイトのベースURL (デプロイ後のURL)
    base_url = "https://ai.negi-lab.com"

    success_count = 0
    twitter_success = 0
    for idx, item in enumerate(final_items, 1):
        print(f"[{idx}/{len(final_items)}] Generating: {item.title[:40]}...")

        try:
            # Generate article (returns ArticleResult)
            result = generator.generate_article(item)

            # Prepare output
            now_jst = datetime.now(JST)
            date_midnight = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)
            ymd = date_midnight.strftime("%Y-%m-%d")

            article_id = f"{ymd}-{uuid.uuid4().hex[:8]}"
            filename = f"{article_id}.md"
            out_path = out_dir / filename

            # Generate and save image locally
            print(f"  Generating image...")
            image_path = image_handler.generate_and_save_image(
                title=result.title,
                body=result.body,
                category=item.category,
                article_id=article_id,
                output_dir=images_dir,
            )

            # Determine tags for Hugo front matter
            tags = ["GenAI"]
            if item.category == Category.NEWS:
                tags.extend(["速報", "AIニュース"])
            elif item.category == Category.TOOL:
                tags.extend(["ツール", "レビュー"])
            else:
                tags.extend(["ガイド", "チュートリアル"])

            # Write file
            write_hugo_markdown(
                out_path=out_path,
                title=result.title,
                date_jst=date_midnight,
                image_url=image_path,
                category=item.category,
                tags=tags,
                body=result.body,
            )

            # Mark as processed
            processed_store.add(item.url)
            processed_store.save()

            # ログ出力
            print(f"  ✓ Saved: {filename}")
            if result.shopping_keyword:
                print(f"    Shopping keyword: {result.shopping_keyword}")
            if result.viral_tags:
                print(f"    Viral tags: {result.viral_tags}")
            success_count += 1

            # X投稿用のキューに追加（デプロイ後投稿用）
            article_url = f"{base_url}/posts/{article_id}/"
            twitter_queue = TwitterPostingQueue(repo_root / "twitter_queue.json")
            twitter_queue.add(TwitterQueueItem(
                article_id=article_id,
                title=result.title,
                url=article_url,
                category=item.category.value,
                viral_tags=result.viral_tags,
                created_at=now_jst.isoformat(),
            ))
            print(f"    Queued for X posting: {article_id}")

            # Twitter投稿（--skip-twitter でなければ即時投稿）
            if twitter_poster and not skip_twitter:
                if twitter_poster.post_article(
                    title=result.title,
                    url=article_url,
                    category=item.category,
                    viral_tags=result.viral_tags,
                ):
                    twitter_queue.mark_posted(article_id)
                    print(f"  ✓ Posted to X (Twitter Card)")
                    twitter_success += 1
                else:
                    print(f"  ✗ X post failed (queued for later)")
            elif skip_twitter:
                print(f"    [--skip-twitter] X posting skipped (use --post-twitter {article_id} later)")

            # Rate limit
            if idx < len(final_items):
                print(f"  (Sleeping {SLEEP_SECONDS_PER_ARTICLE}s for rate limit...)")
                time.sleep(SLEEP_SECONDS_PER_ARTICLE)

        except Exception as e:
            print(f"  ✗ Failed: {e}")
            continue

    print()
    print("=" * 60)
    print(f"Done. Generated {success_count}/{len(final_items)} articles.")
    if twitter_poster and not skip_twitter:
        print(f"      Posted to X: {twitter_success}/{success_count}")
    elif skip_twitter:
        print(f"      X posting skipped. Run with --post-all-twitter after deploy.")
    print("=" * 60)

    return 0 if success_count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
