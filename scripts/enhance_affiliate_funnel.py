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

ARTICLE_TARGETS = [
    "brandless-high-income-path.html",
    "career-agent-comparison-framework.html",
    "consulting-market-signal-matrix.html",
    "midcareer-40s-career-capital.html",
    "self-directed-job-search-system.html",
]

TOPIC_TARGETS = [
    "40s-career-market-value.html",
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


def remove_generated_partner_comparisons() -> int:
    """Keep direct ASP creatives on the approved gateway only.

    Older generated JA/EN editorial pages embedded the full partner comparison.
    Current partner policy records the production placement at the legacy
    high-class transition gateway, so generated articles must route there
    rather than duplicate direct ASP creatives.
    """
    removed = 0
    for locale in ("ja", "en"):
        for path in (ROOT / locale / "articles").glob("*.html"):
            text = path.read_text(encoding="utf-8")
            updated, count = LEGACY_PARTNER_RE.subn("", text)
            if count:
                path.write_text(updated, encoding="utf-8")
                removed += count
    return removed


def inject_article_block(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    slug = path.stem
    href = "../../" + GATEWAY
    block = (
        f'{ARTICLE_START}<aside class="callout affiliate-funnel" data-affiliate-funnel-source="{slug}">'
        '<strong>転職を選択肢に入れるなら、1社の反応だけで市場価値を決めない。</strong>'
        '<p>CareerRadarでは、ハイクラス・外資・IT/SaaSなど狙う市場に応じて、現在利用できる転職支援サービスを比較できます。</p>'
        f'<div class="actions"><a class="button secondary" href="{href}" data-affiliate-funnel-link="true" data-affiliate-funnel-source="{slug}">転職支援サービスを比較する</a></div>'
        f'</aside>{ARTICLE_END}'
    )
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


def inject_topic_block(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    slug = path.stem
    href = "../../" + GATEWAY
    block = (
        f'{ARTICLE_START}<aside class="callout affiliate-funnel" data-affiliate-funnel-source="topic:{slug}">'
        '<strong>実際に転職市場の反応も確認したい方へ</strong>'
        '<p>求人件数だけでなく、どの市場・役割で評価されるかを複数の窓口で確かめるための転職支援サービス比較へ進めます。</p>'
        f'<div class="actions"><a class="button secondary" href="{href}" data-affiliate-funnel-link="true" data-affiliate-funnel-source="topic:{slug}">転職支援サービスを比較する</a></div>'
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
        f'<div class="actions"><a class="button primary" href="{GATEWAY}" data-affiliate-funnel-link="true" data-affiliate-funnel-source="home">転職支援サービスを比較する</a><a class="button secondary" href="review.html">Career Reviewを見る</a></div>'
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

    # A single, clear "広告" label is sufficient UI disclosure here. Remove
    # the redundant explanatory sentence below the comparison block.
    text, removed_disclosure = REDUNDANT_GATEWAY_DISCLOSURE_RE.subn("", text)
    if '<div class="partner-label">広告</div>' not in text:
        raise SystemExit("Gateway advertising label missing")
    path.write_text(text, encoding="utf-8")
    return removed_disclosure


def main() -> None:
    removed = remove_generated_partner_comparisons()
    removed_disclosure = update_gateway()
    update_home()
    for name in ARTICLE_TARGETS:
        path = ROOT / "ja" / "articles" / name
        if not path.exists():
            raise SystemExit(f"Missing monetization target: {path}")
        inject_article_block(path)
    for name in TOPIC_TARGETS:
        path = ROOT / "ja" / "topics" / name
        if not path.exists():
            raise SystemExit(f"Missing monetization target: {path}")
        inject_topic_block(path)
    print(
        "Affiliate funnel ready: gateway=1, home=1, "
        f"article_routes={len(ARTICLE_TARGETS)}, topic_routes={len(TOPIC_TARGETS)}, "
        f"legacy_direct_blocks_removed={removed}, redundant_disclosure_removed={removed_disclosure}"
    )


if __name__ == "__main__":
    main()
