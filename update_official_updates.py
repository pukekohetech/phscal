#!/usr/bin/env python3
"""Build updates.json from official NZ education and safety sources.

No third-party packages are required. The script is designed for GitHub Actions.
It keeps the previous data when a source is temporarily unavailable, reads RSS/Atom
sources from rss-feeds.json, and watches NZQA standards by fingerprinting public pages.
"""

from __future__ import annotations

import hashlib
import ipaddress
import html
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "updates.json"
WATCH_CONFIG = ROOT / "standards-watch.json"
RSS_CONFIG = ROOT / "rss-feeds.json"
USER_AGENT = "Mozilla/5.0 (compatible; PHS-Calendar-Official-Updates/1.0; +https://pukekohetech.github.io/phscal/)"
TIMEOUT = 25
MAX_ITEMS = 70

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

TECH_KEYWORDS = {
    "technology", "digital technology", "materials", "processing", "engineering",
    "construction", "building", "food", "manufacturing", "design", "visual communication",
    "dvc", "machinery", "machine", "joinery", "wood", "workshop", "electrical",
    "hazardous substances", "asbestos", "dust", "guarding", "welding", "hswa", "industry-led",
    "vocational", "trades", "working at height", "exposure standards",
}
ASSESSMENT_KEYWORDS = {
    "assessment", "ncea", "achievement standard", "unit standard", "moderation",
    "examination", "exam", "scholarship", "derived grade", "specification",
    "portfolio", "standard", "qualification",
}
CURRICULUM_KEYWORDS = {
    "curriculum", "years 9", "years 10", "years 11", "years 12", "years 13",
    "senior secondary", "subject", "professional learning", "pld", "teacher only",
    "qualification", "industry-led",
}
SAFETY_KEYWORDS = {
    "safety", "health and safety", "hazard", "machinery", "machine", "joinery",
    "manufacturing", "construction", "hazardous substances", "asbestos", "dust",
    "electrical", "guard", "workplace exposure", "working at height", "work-related health", "hswa",
}

DEFAULT_STANDARD_NUMBERS = ("92012", "92014", "92015", "29655")


@dataclass(frozen=True)
class Source:
    name: str
    listing_url: str
    path_fragment: str
    default_tags: tuple[str, ...]
    max_links: int = 12
    filter_irrelevant: bool = False
    fallback_links: tuple[str, ...] = ()


SOURCES = (
    Source(
        "NZQA",
        "https://www2.nzqa.govt.nz/about-us/publications/newsletters-circulars/assessment-matters/",
        "/about-us/publications/newsletters-circulars/assessment-matters/",
        ("Assessment",),
        max_links=12,
        fallback_links=(
            "https://www2.nzqa.govt.nz/about-us/publications/newsletters-circulars/assessment-matters/a2026-4/",
            "https://www2.nzqa.govt.nz/about-us/publications/newsletters-circulars/assessment-matters/a2026-3/",
            "https://www2.nzqa.govt.nz/about-us/publications/newsletters-circulars/assessment-matters/a2026-2/",
        ),
    ),
    Source(
        "NCEA",
        "https://ncea.education.govt.nz/whats-new",
        "/whats-new/",
        ("Curriculum", "Assessment"),
        max_links=14,
        fallback_links=(
            "https://ncea.education.govt.nz/whats-new/revised-achievement-standards-and-supporting-materials-assessment-2027",
            "https://ncea.education.govt.nz/whats-new/additional-senior-secondary-subjects-open-feedback",
            "https://ncea.education.govt.nz/whats-new/new-industry-led-subjects-announced-senior-secondary-students",
        ),
    ),
    Source(
        "Ministry",
        "https://www.education.govt.nz/bulletins/",
        "/bulletins/te-poutahu-curriculum-centre-school-update/",
        ("Curriculum",),
        max_links=8,
        fallback_links=(
            "https://www.education.govt.nz/bulletins/te-poutahu-curriculum-centre-school-update/05-08-26",
            "https://www.education.govt.nz/bulletins/te-poutahu-curriculum-centre-school-update/26-06-26",
            "https://www.education.govt.nz/bulletins/te-poutahu-curriculum-centre-school-update/29-05-26",
        ),
    ),
    Source(
        "WorkSafe",
        "https://www.worksafe.govt.nz/about-us/news-and-media/",
        "/about-us/news-and-media/",
        ("Safety",),
        max_links=18,
        filter_irrelevant=True,
        fallback_links=(
            "https://www.worksafe.govt.nz/about-us/news-and-media/targeted-checks-highlight-opportunities-to-lift-safety-in-joinery-sector/",
            "https://www.worksafe.govt.nz/about-us/news-and-media/work-related-health-newsletter-september-2026/",
            "https://www.worksafe.govt.nz/about-us/news-and-media/food-manufacturing-visits-finding-safety-gaps-in-machinery-and-hazardous-substances/",
        ),
    ),
)


@dataclass(frozen=True)
class RssSource:
    name: str
    feed_url: str
    default_tags: tuple[str, ...]
    max_items: int = 12
    filter_irrelevant: bool = False
    enabled: bool = True


DEFAULT_RSS_SOURCES = (
    RssSource(
        "NCEA on TKI",
        "https://ncea.tki.org.nz/layout/set/rss",
        ("Assessment", "Technology"),
        max_items=12,
        filter_irrelevant=True,
    ),
    RssSource(
        "Technology Online - What's new",
        "https://www.technology.tki.org.nz/rss/feed/whats-new",
        ("Technology", "Curriculum"),
        max_items=10,
    ),
    RssSource(
        "Technology Online - News",
        "https://www.technology.tki.org.nz/rss/feed/technology-news-articles",
        ("Technology",),
        max_items=10,
    ),
    RssSource(
        "Technology Online - Teaching snapshots",
        "https://www.technology.tki.org.nz/rss/feed/teaching-snapshots",
        ("Technology", "Teaching"),
        max_items=10,
    ),
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.meta: dict[str, str] = {}
        self.times: list[str] = []
        self.paragraphs: list[str] = []
        self._anchor_href: str | None = None
        self._anchor_parts: list[str] = []
        self._paragraph_parts: list[str] | None = None
        self._time_parts: list[str] | None = None
        self._skip_depth = 0
        self._all_text: list[str] = []
        self._title_parts: list[str] | None = None
        self._h1_parts: list[str] | None = None
        self.page_title_text = ''
        self.h1_text = ''

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "a":
            self._anchor_href = attrs_d.get("href", "")
            self._anchor_parts = []
        elif tag in {"p", "li", "h2", "h3", "h4", "blockquote"}:
            if self._paragraph_parts is None:
                self._paragraph_parts = []
        elif tag == "time":
            dt = attrs_d.get("datetime", "").strip()
            if dt:
                self.times.append(dt)
            self._time_parts = []
        elif tag == "title":
            self._title_parts = []
        elif tag == "h1":
            self._h1_parts = []
        elif tag == "meta":
            key = (attrs_d.get("property") or attrs_d.get("name") or "").lower().strip()
            content = attrs_d.get("content", "").strip()
            if key and content:
                self.meta[key] = content

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == "a" and self._anchor_href is not None:
            text = clean_text(" ".join(self._anchor_parts))
            if text:
                self.links.append((self._anchor_href, text))
            self._anchor_href = None
            self._anchor_parts = []
        elif tag in {"p", "li", "h2", "h3", "h4", "blockquote"} and self._paragraph_parts is not None:
            text = clean_text(" ".join(self._paragraph_parts))
            if text:
                self.paragraphs.append(text)
            self._paragraph_parts = None
        elif tag == "time" and self._time_parts is not None:
            text = clean_text(" ".join(self._time_parts))
            if text:
                self.times.append(text)
            self._time_parts = None
        elif tag == "title" and self._title_parts is not None:
            self.page_title_text = clean_text(" ".join(self._title_parts))
            self._title_parts = None
        elif tag == "h1" and self._h1_parts is not None:
            if not self.h1_text:
                self.h1_text = clean_text(" ".join(self._h1_parts))
            self._h1_parts = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = clean_text(data)
        if not text:
            return
        self._all_text.append(text)
        if self._anchor_href is not None:
            self._anchor_parts.append(text)
        if self._paragraph_parts is not None:
            self._paragraph_parts.append(text)
        if self._time_parts is not None:
            self._time_parts.append(text)
        if self._title_parts is not None:
            self._title_parts.append(text)
        if self._h1_parts is not None:
            self._h1_parts.append(text)

    @property
    def visible_text(self) -> str:
        return clean_text(" ".join(self._all_text))


class RichReaderParser(HTMLParser):
    """Build a safe, presentation-aware article fragment from an external page.

    The reader intentionally keeps only semantic content tags and safe link/image
    attributes. Scripts, styles, forms, navigation and other page chrome are never
    copied into updates.json.
    """

    SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "aside", "footer", "form", "button", "template", "iframe"}
    TAG_MAP = {"b": "strong", "i": "em"}
    CONTAINER_TAGS = {"h2", "h3", "h4", "p", "ul", "ol", "li", "blockquote", "table", "thead", "tbody", "tr", "th", "td", "a", "strong", "em", "b", "i"}
    VOID_TAGS = {"br", "hr", "img"}

    def __init__(self, base_url: str, *, capture_from_start: bool = False, text_limit: int = 50000) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.capture = capture_from_start
        self.in_main = False
        self.seen_main = False
        self.seen_h1 = False
        self.in_h1 = 0
        self.skip_depth = 0
        self.out: list[str] = []
        self.open_tags: list[str] = []
        self.text_limit = text_limit
        self.text_chars = 0
        self.truncated = False

    def _safe_url(self, raw: str, *, image: bool = False) -> str:
        raw = (raw or "").strip()
        if not raw:
            return ""
        absolute = urljoin(self.base_url, raw)
        parsed = urlparse(absolute)
        allowed = {"http", "https"} if image else {"http", "https", "mailto", "tel"}
        if parsed.scheme.lower() not in allowed:
            return ""
        return absolute

    def _emit_start(self, tag: str, attrs_d: dict[str, str]) -> None:
        mapped = self.TAG_MAP.get(tag, tag)
        if mapped == "a":
            href = self._safe_url(attrs_d.get("href", ""))
            if not href:
                return
            title = clean_text(attrs_d.get("title", ""))
            title_attr = f' title="{html.escape(title, quote=True)}"' if title else ""
            external = urlparse(href).scheme in {"http", "https"}
            target = ' target="_blank" rel="noopener noreferrer"' if external else ""
            self.out.append(f'<a href="{html.escape(href, quote=True)}"{title_attr}{target}>')
            self.open_tags.append("a")
            return
        if mapped in {"th", "td"}:
            extras = []
            for name in ("colspan", "rowspan"):
                value = attrs_d.get(name, "").strip()
                if value.isdigit() and 1 <= int(value) <= 20:
                    extras.append(f'{name}="{value}"')
            suffix = (" " + " ".join(extras)) if extras else ""
            self.out.append(f"<{mapped}{suffix}>")
            self.open_tags.append(mapped)
            return
        self.out.append(f"<{mapped}>")
        self.open_tags.append(mapped)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_d = {k.lower(): (v or "") for k, v in attrs}

        if self.skip_depth:
            if tag in self.SKIP_TAGS:
                self.skip_depth += 1
            return
        if tag in self.SKIP_TAGS:
            self.skip_depth = 1
            return

        if tag == "main":
            self.in_main = True
            self.seen_main = True
            if not self.capture:
                self.capture = True
            return

        if tag == "h1":
            self.seen_h1 = True
            self.in_h1 += 1
            # If we started at <main>, drop breadcrumbs and other chrome before h1.
            if self.capture:
                self.out.clear()
                self.open_tags.clear()
                self.text_chars = 0
            return

        if not self.capture or self.in_h1:
            return

        if self.truncated:
            return

        if tag in self.CONTAINER_TAGS:
            self._emit_start(tag, attrs_d)
        elif tag == "br":
            self.out.append("<br>")
        elif tag == "hr":
            self.out.append("<hr>")
        elif tag == "img":
            src = self._safe_url(attrs_d.get("src", ""), image=True)
            if src:
                alt = clean_text(attrs_d.get("alt", ""))
                self.out.append(
                    f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(alt, quote=True)}" loading="lazy" referrerpolicy="no-referrer">'
                )

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.skip_depth:
            if tag in self.SKIP_TAGS:
                self.skip_depth -= 1
            return

        if tag == "h1":
            if self.in_h1:
                self.in_h1 -= 1
            if self.in_h1 == 0:
                self.capture = True
            return

        if tag == "main":
            self.in_main = False
            if self.seen_main:
                self.capture = False
            return

        if not self.capture or self.in_h1:
            return

        mapped = self.TAG_MAP.get(tag, tag)
        if mapped in self.CONTAINER_TAGS:
            # Close only tags that were actually emitted. If source HTML is messy,
            # close intervening tags too so the saved fragment stays well formed.
            if mapped in self.open_tags:
                while self.open_tags:
                    current = self.open_tags.pop()
                    self.out.append(f"</{current}>")
                    if current == mapped:
                        break

    def handle_data(self, data: str) -> None:
        if self.skip_depth or not self.capture or self.in_h1 or self.truncated:
            return
        normalized = re.sub(r"\\s+", " ", data)
        if not normalized.strip():
            return
        remaining = self.text_limit - self.text_chars
        if remaining <= 0:
            self.truncated = True
            return
        if len(normalized) > remaining:
            normalized = normalized[:remaining].rstrip() + "…"
            self.truncated = True
        self.text_chars += len(normalized)
        self.out.append(html.escape(normalized, quote=False))

    def rich_html(self) -> str:
        while self.open_tags:
            self.out.append(f"</{self.open_tags.pop()}>")
        fragment = "".join(self.out)
        # Drop structurally empty blocks that can be introduced by page chrome.
        fragment = re.sub(r"<(p|li|h2|h3|h4|blockquote)>\\s*</\\1>", "", fragment, flags=re.I)
        return fragment.strip()


def page_reader_html(content: str, url: str, limit: int = 50000) -> str:
    parser = RichReaderParser(url, text_limit=limit)
    parser.feed(content)
    return parser.rich_html()


def sanitize_feed_fragment(content: str, base_url: str, limit: int = 12000) -> str:
    if not content:
        return ""
    parser = RichReaderParser(base_url, capture_from_start=True, text_limit=limit)
    parser.feed(content)
    return parser.rich_html()


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(str(value or ""))).strip()


def fetch_html(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-NZ,en;q=0.9",
        },
    )
    with urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def parse_page(content: str) -> PageParser:
    parser = PageParser()
    parser.feed(content)
    return parser


def parse_date_text(value: str) -> str:
    value = clean_text(value)
    if not value:
        return ""
    # ISO / RFC-ish metadata.
    iso_match = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})(?=\D|$)", value)
    if iso_match:
        return "-".join(iso_match.groups())
    # 23 September 2026 / Published 23 September 2026.
    m = re.search(r"\b(\d{1,2})\s+([A-Za-z]+)\s+(20\d{2})\b", value)
    if m:
        month = MONTHS.get(m.group(2).lower())
        if month:
            return f"{int(m.group(3)):04d}-{month:02d}-{int(m.group(1)):02d}"
    # DD/MM/YYYY.
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", value)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return ""


def date_from_url(url: str) -> str:
    # Ministry bulletin URLs use DD-MM-YY.
    m = re.search(r"/(\d{2})-(\d{2})-(\d{2})(?:/|$)", url)
    if m:
        yy = 2000 + int(m.group(3))
        return f"{yy:04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return ""


def item_date(parser: PageParser, url: str) -> str:
    for key in (
        "article:published_time", "date", "datepublished", "publish-date",
        "dc.date", "dcterms.date", "parsely-pub-date",
    ):
        if key in parser.meta:
            parsed = parse_date_text(parser.meta[key])
            if parsed:
                return parsed
    for value in parser.times:
        parsed = parse_date_text(value)
        if parsed:
            return parsed
    parsed = parse_date_text(parser.visible_text[:5000])
    return parsed or date_from_url(url)


def page_title(parser: PageParser, fallback: str) -> str:
    for key in ("og:title", "twitter:title"):
        if parser.meta.get(key):
            return clean_text(parser.meta[key])
    if parser.h1_text:
        return clean_text(parser.h1_text)
    if parser.page_title_text:
        return clean_text(re.sub(r'\s*[|–—-]\s*(NZQA|NCEA|WorkSafe|Ministry of Education).*$','', parser.page_title_text, flags=re.I))
    return clean_text(fallback)


def page_summary(parser: PageParser) -> str:
    for key in ("description", "og:description", "twitter:description"):
        text = clean_text(parser.meta.get(key, ""))
        if len(text) >= 35:
            return text[:360]
    for text in parser.paragraphs:
        low = text.lower()
        if len(text) >= 55 and not any(skip in low for skip in ("cookie", "privacy", "subscribe", "skip to", "contact us")):
            return text[:360]
    return ""


def page_reader_text(parser: PageParser, limit: int = 5000) -> str:
    parts: list[str] = []
    seen: set[str] = set()
    for text in parser.paragraphs:
        clean = clean_text(text)
        low = clean.lower()
        if len(clean) < 40 or any(skip in low for skip in ("cookie", "privacy", "subscribe", "skip to", "contact us", "copyright")):
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        parts.append(clean)
        if sum(len(part) for part in parts) >= limit:
            break
    joined = "\n\n".join(parts)
    return joined[:limit]


def tags_for(source: Source, title: str, summary: str) -> list[str]:
    haystack = (title + " " + summary).lower()
    tags = list(source.default_tags)
    if any(word in haystack for word in TECH_KEYWORDS):
        tags.append("Technology")
    if any(word in haystack for word in ASSESSMENT_KEYWORDS):
        tags.append("Assessment")
    if any(word in haystack for word in CURRICULUM_KEYWORDS):
        tags.append("Curriculum")
    if any(word in haystack for word in SAFETY_KEYWORDS):
        tags.append("Safety")
    return list(dict.fromkeys(tags))


def is_technology_relevant(text: str) -> bool:
    low = text.lower()
    return any(word in low for word in TECH_KEYWORDS | SAFETY_KEYWORDS)


def make_id(source: str, url: str, title: str) -> str:
    digest = hashlib.sha256(f"{source}|{url}|{title}".encode("utf-8")).hexdigest()[:18]
    return f"{source.lower().replace(' ', '-')}-{digest}"


def discover_links(source: Source) -> list[tuple[str, str]]:
    content = fetch_html(source.listing_url)
    parser = parse_page(content)
    base_path = urlparse(source.listing_url).path.rstrip("/") + "/"
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for href, text in parser.links:
        absolute = urljoin(source.listing_url, href)
        parsed = urlparse(absolute)
        if source.path_fragment not in parsed.path:
            continue
        if parsed.path.rstrip("/") + "/" == base_path:
            continue
        if absolute in seen:
            continue
        if len(text) < 8:
            continue
        if source.filter_irrelevant and not is_technology_relevant(text):
            continue
        seen.add(absolute)
        found.append((absolute, text))
        if len(found) >= source.max_links:
            break
    for fallback in source.fallback_links:
        if fallback not in seen and len(found) < source.max_links:
            found.append((fallback, ""))
            seen.add(fallback)
    return found


def scrape_source(source: Source) -> list[dict]:
    links = discover_links(source)
    items: list[dict] = []
    for index, (url, discovered_title) in enumerate(links):
        try:
            raw_page = fetch_html(url)
            page = parse_page(raw_page)
            title = page_title(page, discovered_title)
            if not title:
                continue
            summary = page_summary(page)
            date = item_date(page, url)
            tags = tags_for(source, title, summary + ' ' + page.visible_text[:6000])
            if source.filter_irrelevant and "Technology" not in tags and "Safety" not in tags:
                continue
            items.append({
                "id": make_id(source.name, url, title),
                "source": source.name,
                "title": title,
                "date": date,
                "url": url,
                "summary": summary,
                "readerText": page_reader_text(page, limit=12000),
                "readerHtml": page_reader_html(raw_page, url, limit=50000),
                "tags": tags,
            })
        except Exception as exc:  # keep one bad article from breaking the whole source
            print(f"WARN {source.name} article {url}: {exc}", file=sys.stderr)
        # Small pause is polite and reduces the chance of rate limiting.
        if index + 1 < len(links):
            time.sleep(0.12)
    return items



def load_watch_standards() -> list[str]:
    try:
        data = json.loads(WATCH_CONFIG.read_text(encoding="utf-8"))
        raw = data.get("standards", []) if isinstance(data, dict) else []
    except Exception:
        raw = list(DEFAULT_STANDARD_NUMBERS)
    standards: list[str] = []
    for value in raw:
        standard = str(value).strip()
        if re.fullmatch(r"\d{3,6}", standard) and standard not in standards:
            standards.append(standard)
        if len(standards) >= 24:
            break
    return standards or list(DEFAULT_STANDARD_NUMBERS)


def safe_feed_url(url: str) -> bool:
    try:
        parsed = urlparse(str(url or "").strip())
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        host = parsed.hostname.lower().strip(".")
        if host in {"localhost", "metadata.google.internal"} or host.endswith(".local"):
            return False
        try:
            addr = ipaddress.ip_address(host)
            if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
                return False
        except ValueError:
            pass
        return True
    except Exception:
        return False


def load_rss_sources() -> list[RssSource]:
    try:
        data = json.loads(RSS_CONFIG.read_text(encoding="utf-8"))
        raw = data.get("feeds", []) if isinstance(data, dict) else []
    except Exception:
        return list(DEFAULT_RSS_SOURCES)

    sources: list[RssSource] = []
    seen_urls: set[str] = set()
    for row in raw:
        if not isinstance(row, dict) or row.get("enabled", True) is False:
            continue
        name = clean_text(row.get("name", ""))[:80]
        url = str(row.get("url", "")).strip()
        if not name or not safe_feed_url(url) or url in seen_urls:
            continue
        tags_raw = row.get("tags", [])
        if isinstance(tags_raw, str):
            tags_raw = re.split(r"[,;]+", tags_raw)
        tags: list[str] = []
        for value in tags_raw if isinstance(tags_raw, list) else []:
            tag = clean_text(value)[:40]
            if tag and tag not in tags:
                tags.append(tag)
        max_items = row.get("maxItems", 12)
        try:
            max_items = max(1, min(30, int(max_items)))
        except Exception:
            max_items = 12
        sources.append(RssSource(
            name=name,
            feed_url=url,
            default_tags=tuple(tags or ["Technology"]),
            max_items=max_items,
            filter_irrelevant=bool(row.get("filterTechnology", False)),
            enabled=True,
        ))
        seen_urls.add(url)
        if len(sources) >= 30:
            break
    return sources


def standard_url(standard: str) -> str:
    return "https://www.nzqa.govt.nz/ncea/assessment/view-detailed.do?standardNumber=" + standard


def rss_date(value: str) -> str:
    text = clean_text(value)
    if not text:
        return ""
    try:
        dt = parsedate_to_datetime(text)
        if dt:
            return dt.date().isoformat()
    except Exception:
        pass
    return parse_date_text(text)


def strip_markup(value: str) -> str:
    return clean_text(re.sub(r"<[^>]+>", " ", html.unescape(value or "")))


def _xml_local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(node: ET.Element, names: set[str]) -> str:
    for child in list(node):
        if _xml_local(child.tag) in names:
            return "".join(child.itertext()).strip()
    return ""


def _entry_link(node: ET.Element) -> str:
    for child in list(node):
        if _xml_local(child.tag) != "link":
            continue
        href = (child.attrib.get("href") or "").strip()
        rel = (child.attrib.get("rel") or "alternate").strip().lower()
        if href and rel in {"", "alternate"}:
            return href
        text = "".join(child.itertext()).strip()
        if text:
            return text
    return ""


def scrape_rss_source(source: RssSource) -> list[dict]:
    content = fetch_html(source.feed_url)
    root = ET.fromstring(content)
    nodes = [node for node in root.iter() if _xml_local(node.tag) in {"item", "entry"}]
    items: list[dict] = []
    # Fetch a limited number of linked articles so Reader mode has useful text
    # without turning each scheduled run into dozens of page requests.
    article_fetch_budget = min(source.max_items, 10)
    article_fetches = 0

    for node in nodes:
        title = clean_text(_child_text(node, {"title"}))
        raw_url = clean_text(_entry_link(node) or _child_text(node, {"link", "guid", "id"}))
        url = urljoin(source.feed_url, raw_url) if raw_url else ""
        summary_raw = _child_text(node, {"description", "summary", "content", "encoded"})
        summary = strip_markup(summary_raw)[:360]
        reader_text = strip_markup(summary_raw)[:6000]
        reader_html = sanitize_feed_fragment(summary_raw, source.feed_url, limit=12000)
        date = rss_date(_child_text(node, {"pubdate", "date", "published", "updated"}))
        haystack = title + " " + summary
        if source.filter_irrelevant and not is_technology_relevant(haystack):
            continue
        if not title or not url:
            continue

        # Many source sites block iframe embedding. Save a fuller article snapshot
        # at update time so the PHS Calendar can render it locally in Reader mode.
        if article_fetches < article_fetch_budget and safe_feed_url(url):
            article_fetches += 1
            try:
                raw_page = fetch_html(url)
                page = parse_page(raw_page)
                fuller_text = page_reader_text(page, limit=12000)
                fuller_html = page_reader_html(raw_page, url, limit=50000)
                fuller_summary = page_summary(page)
                if len(fuller_text) >= 120:
                    reader_text = fuller_text
                if len(strip_markup(fuller_html)) >= 120:
                    reader_html = fuller_html
                if len(fuller_summary) >= 50:
                    summary = fuller_summary[:360]
                if not date:
                    date = item_date(page, url)
            except Exception as exc:
                print(f"WARN {source.name} reader snapshot {url}: {exc}", file=sys.stderr)

        tags = tags_for(source, title, summary + " " + reader_text[:2500])
        items.append({
            "id": make_id(source.name, url, title),
            "source": source.name,
            "sourceType": "rss",
            "feedUrl": source.feed_url,
            "title": title,
            "date": date,
            "url": url,
            "summary": summary,
            "readerText": reader_text or summary,
            "readerHtml": reader_html,
            "tags": tags,
        })
        if len(items) >= source.max_items:
            break
    return items

def normalize_standard_text(text: str) -> str:
    low_noise = re.sub(r"Data as at\s+\d{4}-\d{2}-\d{2}[^ ]*", "Data as at", text, flags=re.I)
    low_noise = re.sub(r"Page last updated:\s*\d{1,2}\s+[A-Za-z]+\s+20\d{2}", "Page last updated", low_noise, flags=re.I)
    return clean_text(low_noise)


def watch_standards(previous: dict, standards: list[str]) -> tuple[list[dict], list[dict]]:
    old = {str(row.get("standard")): row for row in previous.get("standardSnapshots", []) if row.get("standard")}
    snapshots: list[dict] = []
    alerts: list[dict] = []
    today = datetime.now(timezone.utc).date().isoformat()
    for standard in standards:
        url = standard_url(standard)
        prior = old.get(standard, {})
        try:
            parser = parse_page(fetch_html(url))
            normalized = normalize_standard_text(parser.visible_text)
            if len(normalized) < 150:
                raise ValueError("standard page content was unexpectedly short")
            fingerprint = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            changed = bool(prior.get("fingerprint") and prior.get("fingerprint") != fingerprint)
            snapshots.append({
                "standard": standard,
                "url": url,
                "fingerprint": fingerprint,
                "changed": changed,
                "status": "ok",
            })
            if changed:
                title = f"NZQA page changed for standard {standard}"
                alerts.append({
                    "id": f"standard-{standard}-{fingerprint[:12]}",
                    "source": "NZQA Standards",
                    "title": title,
                    "date": today,
                    "url": url,
                    "summary": "The public NZQA page for this watched standard changed since the previous check. Open it to review the current standard or supporting materials.",
                    "readerText": "The public NZQA page for this watched standard changed since the previous check. Review the live NZQA page for the current wording, version and supporting materials.",
                    "tags": ["Standards Watch", "Assessment", "Technology"],
                })
        except Exception as exc:
            snapshots.append({
                "standard": standard,
                "url": url,
                "fingerprint": prior.get("fingerprint", ""),
                "changed": False,
                "status": "error",
            })
            print(f"WARN standard {standard}: {exc}", file=sys.stderr)
    return snapshots, alerts


def load_previous() -> dict:
    try:
        return json.loads(OUTPUT.read_text(encoding="utf-8"))
    except Exception:
        return {"generatedAt": "", "items": [], "standardSnapshots": [], "sources": []}


def parse_sort_date(value: str) -> tuple[int, int, int]:
    try:
        d = datetime.strptime(value, "%Y-%m-%d")
        return d.year, d.month, d.day
    except Exception:
        return (0, 0, 0)


def merge_source_items(previous_items: list[dict], source: Source, fresh: list[dict], ok: bool) -> list[dict]:
    if ok:
        return [item for item in previous_items if item.get("source") != source.name] + fresh
    return previous_items


def semantic_payload(data: dict) -> dict:
    return {
        "items": data.get("items", []),
        "standardSnapshots": [
            {k: row.get(k) for k in ("standard", "url", "fingerprint", "changed", "status")}
            for row in data.get("standardSnapshots", [])
        ],
        "sources": [
            {k: row.get(k) for k in ("name", "url", "status")}
            for row in data.get("sources", [])
        ],
    }


def main() -> int:
    previous = load_previous()
    items = list(previous.get("items", []))
    statuses: list[dict] = []
    rss_sources = load_rss_sources()
    configured_rss_urls = {source.feed_url for source in rss_sources}
    configured_rss_names = {source.name for source in rss_sources}
    items = [
        item for item in items
        if not (
            item.get("sourceType") == "rss" and item.get("feedUrl") not in configured_rss_urls
        ) and not (
            item.get("source") == "NCEA on TKI" and "NCEA on TKI" not in configured_rss_names
        )
    ]

    for source in SOURCES:
        try:
            fresh = scrape_source(source)
            if not fresh:
                raise ValueError("no matching update links found")
            items = merge_source_items(items, source, fresh, True)
            statuses.append({"name": source.name, "url": source.listing_url, "status": "ok"})
            print(f"{source.name}: {len(fresh)} items")
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            statuses.append({"name": source.name, "url": source.listing_url, "status": "error"})
            print(f"WARN {source.name}: {exc}; keeping previous items", file=sys.stderr)

    for source in rss_sources:
        try:
            fresh = scrape_rss_source(source)
            if fresh:
                items = merge_source_items(items, source, fresh, True)
            statuses.append({"name": source.name, "url": source.feed_url, "status": "ok"})
            print(f"{source.name}: {len(fresh)} relevant RSS items")
        except (HTTPError, URLError, TimeoutError, ValueError, OSError, ET.ParseError) as exc:
            statuses.append({"name": source.name, "url": source.feed_url, "status": "error"})
            print(f"WARN {source.name}: {exc}; keeping previous items", file=sys.stderr)

    successful_sources = sum(1 for row in statuses if row.get("status") == "ok")
    if successful_sources == 0:
        print("ERROR: none of the official update sources could be refreshed", file=sys.stderr)
        return 1

    standards = load_watch_standards()
    print("Standards watch: " + ", ".join(standards))
    snapshots, alerts = watch_standards(previous, standards)
    previous_alert_ids = {item.get("id") for item in items if "Standards Watch" in item.get("tags", [])}
    for alert in alerts:
        if alert["id"] not in previous_alert_ids:
            items.append(alert)

    # Dedupe and keep newest, prioritising Technology / Standards Watch items on equal dates.
    deduped: dict[str, dict] = {}
    for item in items:
        item_id = item.get("id") or make_id(item.get("source", ""), item.get("url", ""), item.get("title", ""))
        item["id"] = item_id
        deduped[item_id] = item
    items = list(deduped.values())
    items.sort(
        key=lambda item: (
            parse_sort_date(item.get("date", "")),
            int("Standards Watch" in item.get("tags", [])),
            int("Technology" in item.get("tags", [])),
            item.get("title", ""),
        ),
        reverse=True,
    )
    items = items[:MAX_ITEMS]

    output = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "items": items,
        "standardSnapshots": snapshots,
        "sources": statuses,
    }

    if semantic_payload(output) == semantic_payload(previous):
        print("No official update changes detected; leaving updates.json unchanged.")
        return 0

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.name}: {len(items)} items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
