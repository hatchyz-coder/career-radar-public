#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime
import html
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://career.hdnjapan.com"
SEO_START = "<!-- PV_SEO_START -->"
SEO_END = "<!-- PV_SEO_END -->"
REL_START = "<!-- PV_DISCOVERY_START -->"
REL_END = "<!-- PV_DISCOVERY_END -->"
HOME_START = "<!-- PV_INDEX_LINK_START -->"
HOME_END = "<!-- PV_INDEX_LINK_END -->"

STOP = {"career", "high", "value", "market", "system", "path", "framework", "case", "study", "to", "the", "and", "of"}


def strip_tags(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def extract(pattern: str, text: str, default: str = "") -> str:
    m = re.search(pattern, text, re.S | re.I)
    return strip_tags(m.group(1)) if m else default


def article_date(text: str) -> str:
    raw = extract(r'<p class="article-meta">.*?/\s*([^<]+)</p>', text)
    m = re.search(r"(20\d{2})[.\-/](\d{2})[.\-/](\d{2})", raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"(20\d{2})[.\-/](\d{2})", raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-01"
    return "1970-01-01"


def load_articles(locale: str) -> list[dict]:
    items = []
    base = ROOT / locale / "articles"
    for path in sorted(base.glob("*.html")):
        if path.name == "index.html":
            continue
        text = path.read_text(encoding="utf-8")
        title = extract(r"<h1>(.*?)</h1>", text)
        desc = extract(r'<meta name="description" content="(.*?)">', text)
        if not title or not desc:
            continue
        items.append({
            "id": path.stem,
            "path": path,
            "text": text,
            "title": title,
            "desc": desc,
            "date": article_date(text),
            "url": f"{SITE}/{locale}/articles/{path.stem}.html",
        })
    return sorted(items, key=lambda x: (x["date"], x["id"]), reverse=True)


def words(slug: str) -> set[str]:
    return {w for w in re.split(r"[^a-z0-9]+", slug.lower()) if len(w) > 2 and w not in STOP}


def cluster(slug: str) -> str:
    if any(k in slug for k in ("pmo", "pm-", "consulting", "operator", "operations")):
        return "consulting"
    if any(k in slug for k in ("agent", "job-search", "direct-client", "freelance")):
        return "search"
    if any(k in slug for k in ("career-capital", "salary", "portfolio", "midcareer", "decision-rights", "brandless")):
        return "capital"
    if "ai-" in slug:
        return "ai"
    return "general"


def related(current: dict, items: list[dict], limit: int = 3) -> list[dict]:
    cw = words(current["id"])
    cc = cluster(current["id"])
    scored = []
    for item in items:
        if item["id"] == current["id"]:
            continue
        overlap = len(cw & words(item["id"]))
        same = 3 if cluster(item["id"]) == cc and cc != "general" else 0
        recency = int(item["date"].replace("-", "")) / 100000000
        scored.append((same + overlap * 2 + recency, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]


def replace_block(text: str, start: str, end: str, block: str) -> str:
    pattern = re.escape(start) + r".*?" + re.escape(end)
    if re.search(pattern, text, re.S):
        return re.sub(pattern, block, text, flags=re.S)
    return text


def inject_seo(item: dict, locale: str) -> str:
    text = item["text"]
    lang = "ja" if locale == "ja" else "en"
    feed = f"{SITE}/{locale}/feed.xml"
    payload = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": item["title"],
        "description": item["desc"],
        "url": item["url"],
        "mainEntityOfPage": item["url"],
        "inLanguage": lang,
        "datePublished": item["date"],
        "dateModified": item["date"],
        "publisher": {"@type": "Organization", "name": "HDN Co., Ltd.", "url": "https://hdnjapan.com/"},
        "isPartOf": {"@type": "WebSite", "name": "CareerRadar", "url": SITE + "/"},
    }
    block = (
        f'{SEO_START}\n'
        f'<meta property="og:type" content="article">\n'
        f'<meta property="og:site_name" content="CareerRadar">\n'
        f'<meta property="og:title" content="{html.escape(item["title"], quote=True)}">\n'
        f'<meta property="og:description" content="{html.escape(item["desc"], quote=True)}">\n'
        f'<meta property="og:url" content="{item["url"]}">\n'
        f'<meta name="twitter:card" content="summary">\n'
        f'<meta name="twitter:title" content="{html.escape(item["title"], quote=True)}">\n'
        f'<meta name="twitter:description" content="{html.escape(item["desc"], quote=True)}">\n'
        f'<link rel="alternate" type="application/rss+xml" title="CareerRadar {locale.upper()}" href="{feed}">\n'
        f'<script type="application/ld+json">{json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}</script>\n'
        f'{SEO_END}'
    )
    pattern = re.escape(SEO_START) + r".*?" + re.escape(SEO_END)
    if re.search(pattern, text, re.S):
        return re.sub(pattern, block, text, flags=re.S)
    return text.replace("</head>", block + "\n</head>", 1)


def inject_related(item: dict, locale: str, items: list[dict], text: str) -> str:
    rels = related(item, items)
    if locale == "ja":
        heading, intro, all_label = "次に読む", "このテーマを別の角度から深掘りできます。", "すべての記事を見る"
        tag = "関連記事"
    else:
        heading, intro, all_label = "Read next", "Continue the topic from a different angle.", "Browse all articles"
        tag = "Related"
    cards = "".join(
        f'<a class="card" href="{r["id"]}.html"><span class="tag">{tag}</span><h3>{html.escape(r["title"])}</h3><p>{html.escape(r["desc"])}</p></a>'
        for r in rels
    )
    block = f'{REL_START}<section class="section pv-related"><div class="eyebrow">Discovery</div><h2>{heading}</h2><p class="section-intro">{intro}</p><div class="grid">{cards}</div><div class="actions"><a class="button secondary" href="index.html">{all_label}</a></div></section>{REL_END}'
    pattern = re.escape(REL_START) + r".*?" + re.escape(REL_END)
    if re.search(pattern, text, re.S):
        return re.sub(pattern, block, text, flags=re.S)
    anchors = ['<aside class="partner-action', '<div class="actions">']
    for anchor in anchors:
        pos = text.find(anchor)
        if pos >= 0:
            return text[:pos] + block + text[pos:]
    return text.replace("</article>", block + "</article>", 1)


def build_index(locale: str, items: list[dict]) -> None:
    ja = locale == "ja"
    title = "CareerRadar 記事一覧" if ja else "CareerRadar Article Library"
    desc = "転職、業務委託、PMO、コンサル、Career Capital、市場価値に関するCareerRadarの記事一覧です。" if ja else "Browse CareerRadar articles on career capital, consulting, PMO, independent work and market value."
    lead = "最新記事からテーマを横断して探せます。1本で結論を出さず、複数の視点を比較してください。" if ja else "Browse the latest research and frameworks across CareerRadar. Compare multiple perspectives rather than relying on one article."
    other = "English" if ja else "日本語"
    other_href = "../../en/articles/index.html" if ja else "../../ja/articles/index.html"
    cards = "".join(
        f'<a class="card" href="{i["id"]}.html"><span class="tag">{i["date"][:7]}</span><h2>{html.escape(i["title"])}</h2><p>{html.escape(i["desc"])}</p></a>'
        for i in items
    )
    canonical = f"{SITE}/{locale}/articles/"
    page = f'''<!doctype html><html lang="{locale}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{html.escape(desc, quote=True)}"><title>{html.escape(title)} | CareerRadar</title><link rel="canonical" href="{canonical}"><link rel="alternate" hreflang="ja" href="{SITE}/ja/articles/"><link rel="alternate" hreflang="en" href="{SITE}/en/articles/"><link rel="alternate" type="application/rss+xml" title="CareerRadar {locale.upper()}" href="{SITE}/{locale}/feed.xml"><link rel="stylesheet" href="../../assets/site.css"></head><body><header class="site-header"><nav class="nav"><a class="brand" href="../../index.html">CareerRadar</a><div class="nav-links"><a href="../../review.html">Career Review</a><a href="../../index.html#topics">Topics</a><a href="{other_href}">{other}</a></div></nav></header><main><section class="section"><div class="eyebrow">CareerRadar Library</div><h1>{html.escape(title)}</h1><p class="section-intro">{html.escape(lead)}</p><div class="grid">{cards}</div></section></main><footer class="footer"><div class="footer-inner"><div><strong>CareerRadar</strong><div class="small">Operated by HDN Co., Ltd.</div></div><div class="footer-links"><a href="../../privacy.html">Privacy</a><a href="../../terms.html">Terms</a><a href="../../operator.html">Operator</a></div></div></footer></body></html>'''
    (ROOT / locale / "articles" / "index.html").write_text(page, encoding="utf-8")


def build_feed(locale: str, items: list[dict]) -> None:
    ja = locale == "ja"
    channel_title = "CareerRadar 最新記事" if ja else "CareerRadar Latest Articles"
    channel_desc = "CareerRadarの最新キャリア記事" if ja else "Latest CareerRadar career intelligence articles"
    feed_items = []
    for i in items:
        if i["date"] == "1970-01-01":
            continue
        dt = datetime.strptime(i["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        feed_items.append(
            f'<item><title>{html.escape(i["title"])}</title><link>{i["url"]}</link><guid isPermaLink="true">{i["url"]}</guid><pubDate>{format_datetime(dt)}</pubDate><description>{html.escape(i["desc"])}</description></item>'
        )
    xml = f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{html.escape(channel_title)}</title><link>{SITE}/{locale}/articles/</link><description>{html.escape(channel_desc)}</description><language>{"ja-JP" if ja else "en"}</language>{"".join(feed_items[:20])}</channel></rss>'
    (ROOT / locale / "feed.xml").write_text(xml, encoding="utf-8")


def update_home() -> None:
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    block = f'{HOME_START}<section class="section"><div class="actions"><a class="button secondary" href="ja/articles/index.html">すべての記事を見る</a><a class="button secondary" href="ja/feed.xml">RSS</a></div></section>{HOME_END}'
    pattern = re.escape(HOME_START) + r".*?" + re.escape(HOME_END)
    if re.search(pattern, text, re.S):
        text = re.sub(pattern, block, text, flags=re.S)
    else:
        text = text.replace("</main>", block + "</main>", 1)
    if "application/rss+xml" not in text:
        text = text.replace("</head>", f'<link rel="alternate" type="application/rss+xml" title="CareerRadar JP" href="{SITE}/ja/feed.xml"></head>', 1)
    path.write_text(text, encoding="utf-8")


def update_sitemap() -> None:
    path = ROOT / "sitemap.xml"
    tree = ET.parse(path)
    root = tree.getroot()
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    existing = {el.text for el in root.findall(f".//{ns}loc")}
    for loc in (f"{SITE}/ja/articles/", f"{SITE}/en/articles/"):
        if loc not in existing:
            node = ET.SubElement(root, f"{ns}url")
            ET.SubElement(node, f"{ns}loc").text = loc
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    ET.register_namespace("xhtml", "http://www.w3.org/1999/xhtml")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def main() -> None:
    total = 0
    for locale in ("ja", "en"):
        items = load_articles(locale)
        if len(items) < 5:
            raise SystemExit(f"Too few {locale} articles for discovery layer: {len(items)}")
        for item in items:
            text = inject_seo(item, locale)
            text = inject_related(item, locale, items, text)
            if text.count(SEO_START) != 1 or text.count(REL_START) != 1:
                raise SystemExit(f"Discovery marker failure: {item['path']}")
            item["path"].write_text(text, encoding="utf-8")
            total += 1
        build_index(locale, items)
        build_feed(locale, items)
    update_home()
    update_sitemap()
    print(f"PV discovery layer healthy: enriched={total}, article indexes=2, feeds=2, related-links=3/article")


if __name__ == "__main__":
    main()
