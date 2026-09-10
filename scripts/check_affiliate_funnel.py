#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / "articles" / "high-class-transition.html"
TOPIC_TARGETS = [
    ROOT / "ja" / "topics" / "40s-career-market-value.html",
    ROOT / "ja" / "topics" / "pmo-high-rate-career.html",
    ROOT / "ja" / "topics" / "self-directed-job-search.html",
]
PARTNERS = {
    "jac_recruitment": "01004u3700oxbh",
    "enworld": "0100o60a00oxbh",
    "enworld_it_saas": "0100ong600oxbh",
    "robert_walters": "0100ojgk00oxbh",
}
NON_JAC_TOKENS = {
    "enworld": "0100o60a00oxbh",
    "enworld_it_saas": "0100ong600oxbh",
    "robert_walters": "0100ojgk00oxbh",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def validate_route(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    require(text.count("<!-- AFFILIATE_FUNNEL_START -->") == 1, f"funnel block missing/duplicated: {path}")
    require("high-class-transition.html#agent-options" in text, f"gateway route missing: {path}")
    require('data-affiliate-funnel-link="true"' in text, f"funnel tracking attribute missing: {path}")
    require("アフィリエイト報酬額では決めていません" not in text, f"unnecessary defensive copy remains: {path}")
    start = text.index("<!-- AFFILIATE_FUNNEL_START -->")
    end = text.index("<!-- AFFILIATE_FUNNEL_END -->", start)
    block = text[start:end]
    require("h.accesstrade.net" not in block, f"direct affiliate placement leaked into route block: {path}")


def routed_articles() -> list[Path]:
    pages: list[Path] = []
    for locale in ("ja", "en"):
        for path in sorted((ROOT / locale / "articles").glob("*.html")):
            if path.name != "index.html":
                pages.append(path)
    return pages


def main() -> None:
    gateway = GATEWAY.read_text(encoding="utf-8")
    require('id="agent-options"' in gateway, "affiliate gateway anchor missing")
    require('data-affiliate-funnel-gateway="true"' in gateway, "affiliate gateway marker missing")
    require('data-placement="high_class_transition_after_action"' in gateway, "approved placement marker missing")
    require('<div class="partner-label">広告</div>' in gateway, "clear advertising label missing")
    require(
        "※アフィリエイト広告です。登録前に各社の対象条件と最新情報をご確認ください。" not in gateway,
        "redundant affiliate disclosure copy remains",
    )

    for partner_id, token in PARTNERS.items():
        require(f'data-partner-id="{partner_id}"' in gateway, f"partner missing: {partner_id}")
        require(f"https://h.accesstrade.net/sp/cc?rk={token}" in gateway, f"destination missing: {partner_id}")
        require(f"https://h.accesstrade.net/sp/rr?rk={token}" in gateway, f"ASP creative/tracking missing: {partner_id}")

    require(
        '<img src="https://h.accesstrade.net/sp/rr?rk=0100ong600oxbh" alt="エンワールド　（IT、SaaS向け）" border="0" width="300" height="250">' in gateway,
        "exact enworld IT/SaaS 300x250 ASP creative missing",
    )

    home = (ROOT / "index.html").read_text(encoding="utf-8")
    require(home.count("<!-- AFFILIATE_FUNNEL_HOME_START -->") == 1, "home affiliate funnel marker missing/duplicated")
    require('data-affiliate-funnel-link="true"' in home, "home funnel tracking attribute missing")

    generated_articles = routed_articles()
    require(bool(generated_articles), "no generated articles found")
    for path in generated_articles:
        validate_route(path)
        text = path.read_text(encoding="utf-8")
        require(
            'class="partner-action partner-comparison"' not in text,
            f"unapproved direct partner comparison remains in generated article: {path}",
        )
        for partner_id, token in NON_JAC_TOKENS.items():
            require(
                f"h.accesstrade.net/sp/cc?rk={token}" not in text,
                f"direct {partner_id} destination leaked outside approved gateway: {path}",
            )

    for path in TOPIC_TARGETS:
        validate_route(path)

    analytics = (ROOT / "assets" / "analytics.js").read_text(encoding="utf-8")
    require("affiliate_gateway_view" in analytics, "affiliate gateway view event missing")
    require("affiliate_funnel_click" in analytics, "affiliate funnel event missing")
    require("affiliate_partner_click" in analytics, "affiliate partner event missing")
    require("partner_id" in analytics and "offer_id" in analytics and "placement" in analytics, "affiliate event context incomplete")

    print(
        f"Affiliate funnel healthy: partners={len(PARTNERS)}, routed_articles={len(generated_articles)}, "
        f"topic_routes={len(TOPIC_TARGETS)}, gateway=1"
    )


if __name__ == "__main__":
    main()
