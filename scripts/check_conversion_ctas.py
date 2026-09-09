#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MID_START = "<!-- CONVERSION_MID_START -->"
MID_END = "<!-- CONVERSION_MID_END -->"
END_START = "<!-- CONVERSION_END_START -->"
END_END = "<!-- CONVERSION_END_END -->"
AFFILIATE_START = "<!-- AFFILIATE_FUNNEL_START -->"
AFFILIATE_END = "<!-- AFFILIATE_FUNNEL_END -->"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def check_generated(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    require(text.count(MID_START) == 1 and text.count(MID_END) == 1, f"mid CTA missing/duplicated: {path}")
    require('data-conversion-cta="career_review"' in text, f"Career Review CTA missing: {path}")
    require(text.count(AFFILIATE_START) == 1 and text.count(AFFILIATE_END) == 1, f"affiliate route missing/duplicated: {path}")
    require('data-affiliate-funnel-link="true"' in text, f"market comparison CTA missing: {path}")


def check_legacy(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    require(text.count(MID_START) == 1 and text.count(MID_END) == 1, f"legacy mid CTA missing/duplicated: {path}")
    require('data-conversion-cta="career_review"' in text, f"legacy Career Review CTA missing: {path}")
    if path.name == "high-class-transition.html":
        require('id="agent-options"' in text, "affiliate gateway missing on high-class-transition")
        return
    require(text.count(END_START) == 1 and text.count(END_END) == 1, f"legacy end CTA missing/duplicated: {path}")
    require('data-conversion-cta="market_compare"' in text, f"legacy market comparison CTA missing: {path}")


def check_topics() -> None:
    for path in sorted((ROOT / "ja" / "topics").glob("*.html")):
        text = path.read_text(encoding="utf-8")
        require("review.html" in text, f"topic Career Review route missing: {path}")
        require(text.count(AFFILIATE_START) == 1 and text.count(AFFILIATE_END) == 1, f"topic affiliate CTA missing/duplicated: {path}")
        require('data-affiliate-funnel-link="true"' in text, f"topic market comparison CTA missing: {path}")


def main() -> None:
    generated = []
    for locale in ("ja", "en"):
        generated.extend(p for p in sorted((ROOT / locale / "articles").glob("*.html")) if p.name != "index.html")
    legacy = sorted((ROOT / "articles").glob("*.html"))
    require(bool(generated), "no generated articles found")
    require(bool(legacy), "no legacy articles found")
    for path in generated:
        check_generated(path)
    for path in legacy:
        check_legacy(path)
    check_topics()
    print(f"Conversion CTA coverage healthy: generated={len(generated)}, legacy={len(legacy)}, topics={len(list((ROOT / 'ja' / 'topics').glob('*.html')))}")


if __name__ == "__main__":
    main()
