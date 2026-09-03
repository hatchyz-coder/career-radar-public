#!/usr/bin/env python3
"""Build a bilingual CareerRadar release from private canonical Markdown.

The private repository remains the editorial source of truth.  This script is
intentionally dependency-free so it can run in CI or in a release worktree.
It creates only derived public artifacts: both locale pages, the Japanese
homepage card, and sitemap entries.  ``--check`` is a no-write drift gate;
``--write`` applies the deterministic result to a release branch.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
import html
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://career.hdnjapan.com"
PARTNERS = (
    ("jac_recruitment", "accesstrade_290807", "JAC Recruitment", "https://h.accesstrade.net/sp/cc?rk=01004u3700oxbh", "https://h.accesstrade.net/sp/rr?rk=01004u3700oxbh"),
    ("enworld", "accesstrade_961674", "エンワールド", "https://h.accesstrade.net/sp/cc?rk=0100o60a00oxbh", "https://h.accesstrade.net/sp/rr?rk=0100o60a00oxbh"),
    ("enworld_it_saas", "accesstrade_994914", "エンワールド（IT・SaaS向け）", "https://h.accesstrade.net/sp/cc?rk=0100ong600oxbh", "https://h.accesstrade.net/sp/rr?rk=0100ong600oxbh"),
    ("robert_walters", "accesstrade_987767", "ロバート・ウォルターズ", "https://h.accesstrade.net/sp/cc?rk=0100ojgk00oxbh", "https://h.accesstrade.net/sp/rr?rk=0100ojgk00oxbh"),
)


@dataclass(frozen=True)
class Article:
    article_id: str
    locale: str
    title: str
    body_html: str
    summary: str
    published_at: str


def inline(markdown: str) -> str:
    escaped = html.escape(markdown, quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    return re.sub(
        r"\[([^]]+)]\((https?://[^\s)]+)\)",
        r'<a href="\2" rel="noreferrer noopener">\1</a>',
        escaped,
    )


def markdown_body(markdown: str) -> tuple[str, str, str]:
    """Return title, HTML body, and a plain-text lead from simple Markdown."""
    lines = markdown.replace("\r\n", "\n").split("\n")
    title = ""
    output: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_kind = ""
    first_paragraph = ""

    def flush_paragraph() -> None:
        nonlocal first_paragraph
        if paragraph:
            text = " ".join(part.strip() for part in paragraph).strip()
            if text:
                output.append(f"<p>{inline(text)}</p>")
                if not first_paragraph:
                    first_paragraph = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", inline(text)))
            paragraph.clear()

    def flush_list() -> None:
        nonlocal list_kind
        if list_items:
            output.append(f"<{list_kind}>" + "".join(f"<li>{inline(item)}</li>" for item in list_items) + f"</{list_kind}>")
            list_items.clear()
        list_kind = ""

    for line in lines:
        heading = re.match(r"^(#{1,3})\s+(.+?)\s*$", line)
        unordered = re.match(r"^[-*]\s+(.+?)\s*$", line)
        ordered = re.match(r"^\d+[.)]\s+(.+?)\s*$", line)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            value = heading.group(2)
            if level == 1 and not title:
                title = re.sub(r"\s+", " ", value).strip()
            else:
                output.append(f"<h{level}>{inline(value)}</h{level}>")
        elif unordered or ordered:
            flush_paragraph()
            kind = "ul" if unordered else "ol"
            if list_kind and list_kind != kind:
                flush_list()
            list_kind = kind
            list_items.append((unordered or ordered).group(1))
        elif not line.strip():
            flush_paragraph()
            flush_list()
        else:
            flush_list()
            paragraph.append(line)
    flush_paragraph()
    flush_list()
    if not title:
        raise ValueError("Markdown requires exactly one level-one heading for the article title.")
    if not output:
        raise ValueError("Markdown body is empty.")
    return title, "\n".join(output), first_paragraph


def load_article(source_root: Path, article_id: str, locale: str, published_at: str) -> Article:
    source = source_root / "editorial" / "drafts" / locale / f"{article_id}.md"
    if not source.is_file():
        raise FileNotFoundError(f"Canonical draft is missing: {source}")
    title, body, summary = markdown_body(source.read_text(encoding="utf-8"))
    return Article(article_id, locale, title, body, summary, published_at)


def locale_url(article: Article) -> str:
    return f"{SITE_URL}/{article.locale}/articles/{article.article_id}.html"


def partner_block(locale: str, article_id: str) -> str:
    is_ja = locale == "ja"
    heading = "人材紹介サービスの選択肢を複数社で確認する" if is_ja else "Compare more than one career-support option"
    intro = "求人・支援対象・得意領域は各社で異なります。1社の回答だけを市場評価と考えず、現在の経験と希望に合う選択肢を比較してください。" if is_ja else "Coverage, role focus, and fit differ by provider. Compare options instead of treating one response as the whole market."
    disclosure = "※アフィリエイト広告です。登録前に各社の対象条件と最新情報をご確認ください。" if is_ja else "Advertisement / affiliate links. Confirm each provider's current eligibility and terms before registering."
    action = "選択肢を確認する" if is_ja else "Review this option"
    options = "".join(
        f'<section class="partner-option" data-partner-id="{partner_id}" data-offer-id="{offer_id}"><h3>{html.escape(name)}</h3><p class="partner-cta"><a href="{destination}" rel="nofollow" referrerpolicy="no-referrer-when-downgrade">{html.escape(name)}: {action}<img src="{tracking}" width="1" height="1" border="0" alt=""></a></p></section>'
        for partner_id, offer_id, name, destination, tracking in PARTNERS
    )
    return f'<aside class="partner-action partner-comparison" data-placement="{article_id}_{locale}_market_comparison"><div class="partner-label">Advertisement</div><h2>{heading}</h2><p>{intro}</p><div class="partner-options">{options}</div><p class="small">{disclosure}</p></aside>'


def page(article: Article) -> str:
    peer = "en" if article.locale == "ja" else "ja"
    peer_url = f"{SITE_URL}/{peer}/articles/{article.article_id}.html"
    locale_label = "JP" if article.locale == "ja" else "EN"
    peer_label = "Read in English" if article.locale == "ja" else "日本語で読む"
    description = html.escape(article.summary[:160], quote=True)
    body = article.body_html
    return f'''<!doctype html>
<html lang="{article.locale}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="{description}">
  <title>{html.escape(article.title)} | CareerRadar</title>
  <link rel="canonical" href="{locale_url(article)}">
  <link rel="alternate" hreflang="ja" href="{SITE_URL}/ja/articles/{article.article_id}.html">
  <link rel="alternate" hreflang="en" href="{SITE_URL}/en/articles/{article.article_id}.html">
  <link rel="alternate" hreflang="x-default" href="{SITE_URL}/ja/articles/{article.article_id}.html">
  <link rel="stylesheet" href="../../assets/site.css">
</head>
<body>
  <header class="site-header"><nav class="nav"><a class="brand" href="../../index.html">CareerRadar</a><div class="nav-links"><a href="../../review.html">Career Review</a><a href="../../index.html#insights">Insights</a><a href="{peer_url}">{peer_label}</a></div></nav></header>
  <main><article class="article"><div class="eyebrow">Career Intelligence / {locale_label}</div><h1>{html.escape(article.title)}</h1><p class="article-meta">CareerRadar Editorial / {article.published_at.replace('-', '.')}</p>
{body}
{partner_block(article.locale, article.article_id)}
  <div class="actions"><a class="button primary" href="../../review.html">Career Review</a><a class="button secondary" href="{peer_url}">{peer_label}</a></div></article></main>
  <footer class="footer"><div class="footer-inner"><div><strong>CareerRadar</strong><div class="small">Operated by HDN Co., Ltd.</div></div><div class="footer-links"><a href="../../privacy.html">Privacy</a><a href="../../terms.html">Terms</a><a href="../../disclosure.html">広告・アフィリエイト</a><a href="../../operator.html">運営者情報</a><a href="../../contact.html">お問い合わせ</a></div></div></footer>
</body>
</html>
'''


def homepage_with_card(current: str, article: Article) -> str:
    href = f"ja/articles/{article.article_id}.html"
    if f'href="{href}"' in current:
        return current
    section_start = current.find('<section class="section" id="insights">')
    if section_start < 0:
        raise ValueError("Homepage insights section is missing.")
    grid_start = current.find('<div class="grid">', section_start)
    if grid_start < 0:
        raise ValueError("Homepage insights grid is missing.")
    insert_at = grid_start + len('<div class="grid">')
    summary = html.escape(article.summary[:180] + ("…" if len(article.summary) > 180 else ""))
    card = f'<a class="card" href="{href}"><span class="tag">New / JP + EN</span><h3>{html.escape(article.title)}</h3><p>{summary}</p></a>'
    return current[:insert_at] + card + current[insert_at:]


def sitemap_with_pair(current: str, article_id: str, published_at: str) -> str:
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    xhtml_ns = "http://www.w3.org/1999/xhtml"
    ET.register_namespace("", namespace)
    ET.register_namespace("xhtml", xhtml_ns)
    root = ET.fromstring(current)
    targets = {f"{SITE_URL}/ja/articles/{article_id}.html", f"{SITE_URL}/en/articles/{article_id}.html"}
    for node in list(root):
        loc = node.find(f"{{{namespace}}}loc")
        if loc is not None and loc.text in targets:
            root.remove(node)
    for locale in ("ja", "en"):
        node = ET.SubElement(root, f"{{{namespace}}}url")
        ET.SubElement(node, f"{{{namespace}}}loc").text = f"{SITE_URL}/{locale}/articles/{article_id}.html"
        ET.SubElement(node, f"{{{namespace}}}lastmod").text = published_at
        for alternate in ("ja", "en"):
            ET.SubElement(node, f"{{{xhtml_ns}}}link", {"rel": "alternate", "hreflang": alternate, "href": f"{SITE_URL}/{alternate}/articles/{article_id}.html"})
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def expected_changes(public_root: Path, source_root: Path, article_id: str, published_at: str) -> dict[Path, str]:
    ja = load_article(source_root, article_id, "ja", published_at)
    en = load_article(source_root, article_id, "en", published_at)
    index = public_root / "index.html"
    sitemap = public_root / "sitemap.xml"
    return {
        public_root / "ja" / "articles" / f"{article_id}.html": page(ja),
        public_root / "en" / "articles" / f"{article_id}.html": page(en),
        index: homepage_with_card(index.read_text(encoding="utf-8"), ja),
        sitemap: sitemap_with_pair(sitemap.read_text(encoding="utf-8"), article_id, published_at),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path, help="Private canonical repository checkout")
    parser.add_argument("--article-id", required=True)
    parser.add_argument("--published-at", required=True, help="YYYY-MM-DD")
    parser.add_argument("--public-root", type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Fail if generated release differs from tracked files")
    mode.add_argument("--write", action="store_true", help="Write generated public artifacts")
    args = parser.parse_args()
    try:
        date.fromisoformat(args.published_at)
        changes = expected_changes(args.public_root.resolve(), args.source_root.resolve(), args.article_id, args.published_at)
    except (FileNotFoundError, ValueError, ET.ParseError) as exc:
        print(f"Release builder failed: {exc}", file=sys.stderr)
        return 1
    drift = [path for path, expected in changes.items() if not path.exists() or path.read_text(encoding="utf-8") != expected]
    if args.check:
        if drift:
            print("Release artifacts are not generated or are stale:", file=sys.stderr)
            print("\n".join(str(path.relative_to(args.public_root.resolve())) for path in drift), file=sys.stderr)
            return 1
        print(f"Release artifacts are current for {args.article_id}.")
        return 0
    for path, expected in changes.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding="utf-8")
    print(f"Generated bilingual public release for {args.article_id}: {len(changes)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
