#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
GATEWAY = "articles/high-class-transition.html#agent-options"
ARTICLE_START = "<!-- AFFILIATE_FUNNEL_START -->"
ARTICLE_END = "<!-- AFFILIATE_FUNNEL_END -->"
HOME_START = "<!-- AFFILIATE_FUNNEL_HOME_START -->"
HOME_END = "<!-- AFFILIATE_FUNNEL_HOME_END -->"
LEGACY_PARTNER_RE = re.compile(
    r'<aside class="partner-action partner-comparison"[^>]*>.*?</aside>',
    re.S,
)
REDUNDANT_GATEWAY_DISCLOSURE_RE = re.compile(
    r'<p class="small">※アフィリエイト広告です。登録前に各社の対象条件と最新情報をご確認ください。</p>'
)

TOPIC_TARGETS = [
    "40s-career-market-value.html",
    "pmo-high-rate-career.html",
    "self-directed-job-search.html",
]

PARTNER_IDS = [
    "jac_recruitment",
    "enworld",
    "enworld_it_saas",
    "robert_walters",
]


def replace_block(text: str, start: str, end: str, block: str) -> str:
    pattern = re.escape(start) + r".*?" + re.escape(end)
    if re.search(pattern, text, re.S):
        return re.sub(pattern, block, text, flags=re.S)
    return text


def article_pages(locale: str):
    for path in sorted((ROOT / locale / "articles").glob("*.html")):
        if path.name != "index.html":
            yield path


def remove_generated_partner_comparisons() -> int:
    """Keep direct ASP creatives on the approved gateway only."""
    removed = 0
    for locale in ("ja", "en"):
        for path in article_pages(locale):
            text = path.read_text(encoding="utf-8")
            updated, count = LEGACY_PARTNER_RE.subn("", text)
            if count:
                path.write_text(updated, encoding="utf-8")
                removed += count
    return removed


def article_block(slug: str, locale: str) -> str:
    href = "../../" + GATEWAY
    if locale == "en":
        headline = "If a job move is one of your options, do not let one company's response define your market value."
        body = (
            "CareerRadar compares currently available career-support options across high-class, "
            "global, and IT/SaaS markets so you can test where your experience is valued."
        )
        button = "Compare career-support options"
    else:
        headline = "転職を選択肢に入れるなら、1社の反応だけで市場価値を決めない。"
        body = (
            "CareerRadarでは、ハイクラス・外資・IT/SaaSなど狙う市場に応じて、"
            "現在利用できる転職支援サービスを比較できます。"
        )
        button = "転職支援サービスを比較する"
    return (
        f'{ARTICLE_START}<aside class="callout affiliate-funnel" data-affiliate-funnel-source="{locale}:{slug}">'
        f'<strong>{headline}</strong>'
        f'<p>{body}</p>'
        f'<div class="actions"><a class="button secondary" href="{href}" '
        f'data-affiliate-funnel-link="true" data-affiliate-funnel-source="{locale}:{slug}">{button}</a></div>'
        f'</aside>{ARTICLE_END}'
    )


def inject_article_block(path: Path, locale: str) -> None:
    text = path.read_text(encoding="utf-8")
    slug = path.stem
    block = article_block(slug, locale)
    updated = replace_block(text, ARTICLE_START, ARTICLE_END, block)
    if updated == text and ARTICLE_START not in text:
        anchor = "<!-- PV_DISCOVERY_START -->"
        if anchor in text:
            updated = text.replace(anchor, block + anchor, 1)
        elif "</article>" in text:
            updated = text.replace("</article>", block + "</article>", 1)
        else:
            raise SystemExit(f"No article insertion anchor: {path}")
    path.write_text(updated, encoding="utf-8")


def inject_all_article_blocks() -> int:
    count = 0
    for locale in ("ja", "en"):
        for path in article_pages(locale):
            inject_article_block(path, locale)
            count += 1
    return count


def inject_topic_block(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    slug = path.stem
    href = "../../" + GATEWAY
    block = (
        f'{ARTICLE_START}<aside class="callout affiliate-funnel" data-affiliate-funnel-source="topic:{slug}">'
        '<strong>実際に転職市場の反応も確認したい方へ</strong>'
        '<p>求人件数だけでなく、どの市場・役割で評価されるかを複数の窓口で確かめるための転職支援サービス比較へ進めます。</p>'
        f'<div class="actions"><a class="button secondary" href="{href}" data-affiliate-funnel-link="true" '
        f'data-affiliate-funnel-source="topic:{slug}">転職支援サービスを比較する</a></div>'
        f'</aside>{ARTICLE_END}'
    )
    updated = replace_block(text, ARTICLE_START, ARTICLE_END, block)
    if updated == text and ARTICLE_START not in text:
        if "</main>" in text:
            updated = text.replace("</main>", block + "</main>", 1)
        else:
            raise SystemExit(f"No topic insertion anchor: {path}")
    path.write_text(updated, encoding="utf-8")


def update_home() -> None:
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    block = (
        f'{HOME_START}<section class="section" id="career-agent-options">'
        '<div class="eyebrow">Market test</div>'
        '<h2>転職を考えるなら、紹介件数ではなく「どこで評価されるか」を比べる。</h2>'
        '<p class="section-intro">転職エージェントは市場全体そのものではありません。ハイクラス、外資、IT/SaaSなど複数の窓口を使い、自分の経験がどこで評価されるかを観測するための選択肢として使います。</p>'
        f'<div class="actions"><a class="button primary" href="{GATEWAY}" data-affiliate-funnel-link="true" '
        'data-affiliate-funnel-source="home">転職支援サービスを比較する</a><a class="button secondary" href="review.html">Career Reviewを見る</a></div>'
        f'</section>{HOME_END}'
    )
    updated = replace_block(text, HOME_START, HOME_END, block)
    if updated == text and HOME_START not in text:
        anchor = "<!-- SEARCH_HUBS_START -->"
        if anchor in text:
            updated = text.replace(anchor, block + anchor, 1)
        else:
            updated = text.replace("</main>", block + "</main>", 1)
    path.write_text(updated, encoding="utf-8")


def update_gateway() -> int:
    path = ROOT / "articles" / "high-class-transition.html"
    text = path.read_text(encoding="utf-8")
    for partner_id in PARTNER_IDS:
        if f'data-partner-id="{partner_id}"' not in text:
            raise SystemExit(f"Gateway missing production partner: {partner_id}")
    old = '<aside class="partner-action partner-comparison" data-placement="high_class_transition_after_action">'
    new = '<aside id="agent-options" class="partner-action partner-comparison" data-affiliate-funnel-gateway="true" data-placement="high_class_transition_after_action">'
    if old in text:
        text = text.replace(old, new, 1)
    elif 'id="agent-options"' not in text:
        raise SystemExit("Gateway partner comparison anchor not found")

    text, removed_disclosure = REDUNDANT_GATEWAY_DISCLOSURE_RE.subn("", text)
    if '<div class="partner-label">広告</div>' not in text:
        raise SystemExit("Gateway advertising label missing")
    path.write_text(text, encoding="utf-8")
    return removed_disclosure


def main() -> None:
    removed = remove_generated_partner_comparisons()
    removed_disclosure = update_gateway()
    update_home()
    article_routes = inject_all_article_blocks()
    for name in TOPIC_TARGETS:
        path = ROOT / "ja" / "topics" / name
        if not path.exists():
            raise SystemExit(f"Missing monetization target: {path}")
        inject_topic_block(path)
    print(
        "Affiliate funnel ready: gateway=1, home=1, "
        f"article_routes={article_routes}, topic_routes={len(TOPIC_TARGETS)}, "
        f"legacy_direct_blocks_removed={removed}, redundant_disclosure_removed={removed_disclosure}"
    )


if __name__ == "__main__":
    main()
