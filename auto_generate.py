from __future__ import annotations

import json
import os
import random
import re
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, List, Optional
from urllib.parse import quote

import feedparser
import requests
from bs4 import BeautifulSoup

import google.generativeai as genai

# Optional: load .env if available.
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # If python-dotenv isn't installed (or any load failure), just rely on OS env.
    pass


MAX_ARTICLES_PER_RUN = 2
SLEEP_SECONDS_PER_ARTICLE = 30

JST = timezone(timedelta(hours=9))


@dataclass(frozen=True)
class NewsItem:
    source: str
    title: str
    url: str
    published: str = ""
    summary: str = ""


class ProcessedURLStore:
    """Simple JSON file store for processed URLs."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._urls: List[str] = []

    def load(self) -> List[str]:
        if not self.path.exists():
            self._urls = []
            return self._urls

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                self._urls = [str(x) for x in data]
            else:
                self._urls = []
        except Exception:
            # If the file is corrupted, do not crash the whole script.
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

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._urls, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


class NewsCollector:
    def __init__(self, processed_store: ProcessedURLStore) -> None:
        self.processed_store = processed_store

    def collect(self, max_items: int = 20) -> List[NewsItem]:
        # Prototype priority: Google News RSS
        items: List[NewsItem] = []
        items.extend(self.collect_google_news_rss(max_items=max_items))
        return items

    def collect_google_news_rss(self, max_items: int = 20) -> List[NewsItem]:
        query = "Artificial Intelligence OR Gemini OR OpenAI"
        rss_url = (
            "https://news.google.com/rss/search?q="
            + quote(query)
            + "&hl=ja&gl=JP&ceid=JP:ja"
        )

        try:
            # Use requests to control timeouts/headers.
            resp = requests.get(
                rss_url,
                timeout=20,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; NegiLabBot/0.1; +https://ai.negi-lab.com)"
                },
            )
            resp.raise_for_status()
        except Exception as e:
            print(f"[NewsCollector] Google News RSS fetch failed: {e}")
            return []

        feed = feedparser.parse(resp.content)
        entries = getattr(feed, "entries", []) or []

        results: List[NewsItem] = []
        for entry in entries[:max_items]:
            url = (getattr(entry, "link", "") or "").strip()
            title = (getattr(entry, "title", "") or "").strip()
            published = (getattr(entry, "published", "") or "").strip()
            summary = (getattr(entry, "summary", "") or "").strip()

            if not url or not title:
                continue

            if self.processed_store.contains(url):
                continue

            results.append(
                NewsItem(
                    source="Google News RSS",
                    title=title,
                    url=url,
                    published=published,
                    summary=_normalize_whitespace(summary),
                )
            )

        return results

    # Placeholder for future implementations
    def collect_github_trending_machine_learning(self) -> List[NewsItem]:
        """(TODO) Parse GitHub Trending for topic:machine-learning."""
        return []

    def collect_other_sources(self) -> List[NewsItem]:
        """(TODO) Add more sources (e.g., Hacker News, arXiv, etc.)."""
        return []


class ArticleGenerator:
    def __init__(self, api_key: str, model_name: str = "gemini-3-flash") -> None:
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_article_markdown(self, item: NewsItem) -> str:
        prompt = self._build_article_prompt(item)

        try:
            res = self.model.generate_content(prompt)
        except Exception as e:
            raise RuntimeError(f"Gemini article generation failed: {e}")

        text = getattr(res, "text", None)
        if not text:
            # Some SDK versions return candidates; keep this conservative.
            raise RuntimeError("Gemini returned empty text for article")

        # Safety: enforce "no fenced code blocks" (```)
        cleaned = text.strip().replace("```", "")
        return cleaned

    def extract_title_and_body(self, article_md: str) -> tuple[str, str]:
        # First non-empty line = title.
        lines = [ln.rstrip() for ln in article_md.splitlines()]
        title = ""
        body_start = 0
        for i, ln in enumerate(lines):
            if ln.strip():
                title = ln.strip()
                body_start = i + 1
                break

        # Clean title from surrounding quotes / leading markdown markers.
        title = title.strip().strip('"').strip("'")
        title = re.sub(r"^#{1,6}\s+", "", title).strip()
        if not title:
            title = "AIトレンド速報（自動生成）"

        body = "\n".join(lines[body_start:]).lstrip("\n")
        if not body:
            body = "(本文生成に失敗しました)"

        return title, body

    def _build_article_prompt(self, item: NewsItem) -> str:
        # IMPORTANT: The user requested: output must be pure Markdown text, no HTML, and DO NOT use fenced code blocks.
        # We also ask for the first line to be title-only so we can extract it for Hugo front matter.
        return (
            "あなたはNegi Lab所属の辛口だが技術に詳しいAI研究員です。\n"
            "以下のニュースを元に、日本語でブログ記事を生成してください。\n\n"
            "【元ニュース】\n"
            f"- 出典: {item.source}\n"
            f"- タイトル: {item.title}\n"
            f"- URL: {item.url}\n"
            + (f"- 公開日時: {item.published}\n" if item.published else "")
            + (f"- 要約/抜粋: {item.summary}\n" if item.summary else "")
            + "\n"
            "【厳守ルール】\n"
            "- 出力は“純粋なMarkdownテキストのみ”。HTMLタグは禁止。\n"
            "- YAML/TOMLのFront Matterは出力しない（こちらで付ける）。\n"
            "- コード例が必要な場合でも、``` のフェンスは絶対に使わない。\n"
            "  代わりに、4スペースインデントのコード（Markdownのインデントコード）か、短いインラインコードで示す。\n"
            "- 事実と推測、そしてシミュレーション（捏造）を区別する。\n"
            "  特に“検証シミュレーション”は、冒頭で『これはシミュレーションであり実測ではない』と明記する。\n"
            "\n"
            "【記事構成（必須）】\n"
            "1) 1行目: タイトルのみ（装飾なし、# など見出し記号なし）\n"
            "2) 3行要約（ちょうど3行、箇条書き可）\n"
            "3) 検証シミュレーション: 『実際に使ってみた』体で、具体的なコード例やプロンプト例を“捏造”して提示\n"
            "4) メリット・デメリット\n"
            "5) 結論\n"
            "\n"
            "文体: 辛口だが専門的。無駄に煽らず、技術的に筋の通った批評をする。\n"
        )


class ImageHandler:
    def __init__(self, api_key: str, model_name: str = "gemini-3-flash") -> None:
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_image_prompt_en(self, title: str, body_md: str) -> str:
        # Ask for one English line, no quotes.
        prompt = (
            "Create ONE English image generation prompt for a blog thumbnail.\n"
            "Constraints:\n"
            "- Output ONE line only\n"
            "- English only\n"
            "- No surrounding quotes\n"
            "- Avoid text overlays / logos / watermarks\n"
            "- Style: modern, technical, clean, slightly futuristic\n\n"
            f"Blog title: {title}\n\n"
            "Blog content (markdown):\n"
            f"{body_md[:2000]}\n"
        )

        try:
            res = self.model.generate_content(prompt)
        except Exception as e:
            raise RuntimeError(f"Gemini image prompt generation failed: {e}")

        text = getattr(res, "text", None)
        if not text:
            raise RuntimeError("Gemini returned empty text for image prompt")

        one_line = text.strip().splitlines()[0].strip()
        one_line = one_line.strip('"').strip("'")
        if not one_line:
            one_line = "Futuristic AI lab desk, holographic charts, clean minimal lighting, high quality"
        return one_line

    def build_pollinations_url(self, prompt_en: str) -> str:
        encoded = quote(prompt_en, safe="")
        return f"https://image.pollinations.ai/prompt/{encoded}"


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _safe_filename_fragment(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9\-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:40] if s else "article"


def write_hugo_markdown(
    out_path: Path,
    title: str,
    date_jst: datetime,
    image_url: str,
    categories: List[str],
    tags: List[str],
    body_md: str,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # YAML front matter
    fm_lines = [
        "---",
        f"title: \"{title.replace('\\"', '')}\"",
        f"date: {date_jst.isoformat()}",
        f"image: \"{image_url}\"",
        "categories:",
        *[f"  - \"{c}\"" for c in categories],
        "tags:",
        *[f"  - \"{t}\"" for t in tags],
        "---",
        "",
    ]

    content = "\n".join(fm_lines) + body_md.strip() + "\n"
    out_path.write_text(content, encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parent

    # Ensure logging file exists or is initializable.
    processed_store = ProcessedURLStore(repo_root / "processed_urls.json")
    processed_store.load()

    try:
        api_key = os.environ["GEMINI_API_KEY"]
    except KeyError:
        print("GEMINI_API_KEY is not set. Set it in the environment or in .env.")
        return 2

    collector = NewsCollector(processed_store)
    generator = ArticleGenerator(api_key=api_key, model_name="gemini-3-flash")
    image_handler = ImageHandler(api_key=api_key, model_name="gemini-3-flash")

    news_items = collector.collect(max_items=50)
    if not news_items:
        print("No new items found.")
        return 0

    random.shuffle(news_items)

    out_dir = repo_root / "content" / "posts"

    success_count = 0
    for item in news_items:
        if success_count >= MAX_ARTICLES_PER_RUN:
            break

        print(f"\n[+] Generating article for: {item.title}")
        try:
            article_md = generator.generate_article_markdown(item)
            title, body_md = generator.extract_title_and_body(article_md)

            prompt_en = image_handler.generate_image_prompt_en(title=title, body_md=body_md)
            image_url = image_handler.build_pollinations_url(prompt_en)

            now_jst = datetime.now(JST)
            date_midnight = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)
            ymd = date_midnight.strftime("%Y-%m-%d")

            article_id = uuid.uuid4().hex[:8]
            filename = f"{ymd}-{article_id}.md"
            out_path = out_dir / filename

            write_hugo_markdown(
                out_path=out_path,
                title=title,
                date_jst=date_midnight,
                image_url=image_url,
                categories=["AI News"],
                tags=["GenAI", "Gemini", "Tool"],
                body_md=body_md,
            )

            processed_store.add(item.url)
            processed_store.save()

            print(f"[OK] Wrote: {out_path}")
            print(f"     Source URL logged: {item.url}")

            success_count += 1
            time.sleep(SLEEP_SECONDS_PER_ARTICLE)

        except Exception as e:
            # Do not stop whole script.
            print(f"[ERROR] Failed to generate for URL={item.url}: {e}")
            continue

    print(f"\nDone. Generated {success_count} article(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
