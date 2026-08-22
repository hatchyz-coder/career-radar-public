#!/usr/bin/env python3
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
ARTICLES = (
    ROOT / "articles" / "career-navigation.html",
    ROOT / "articles" / "consulting-career-capital.html",
    ROOT / "articles" / "freelance-transition.html",
    ROOT / "articles" / "high-class-transition.html",
)
MIN_JAPANESE_CHARACTERS = 3300
MIN_PARAGRAPHS = 29
MIN_H2 = 12
REQUIRED_MARKERS = ("CareerRadar", "Self Check", "参考にした主な調査")
FORBIDDEN_MARKERS = (
    "PR #",
    "マージ",
    "運営側の都合",
    "収益化のため",
    "広告報酬",
    "Recommendation",
    "Opportunity Path",
)
PARTNER_CONTRACTS = {
    "jac_recruitment": (
        "accesstrade_290807",
        "https://h.accesstrade.net/sp/cc?rk=01004u3700oxbh",
        "https://h.accesstrade.net/sp/rr?rk=01004u3700oxbh",
    ),
    "enworld": (
        "accesstrade_961674",
        "https://h.accesstrade.net/sp/cc?rk=0100o60a00oxbh",
        "https://h.accesstrade.net/sp/rr?rk=0100o60a00oxbh",
    ),
    "enworld_it_saas": (
        "accesstrade_994914",
        "https://h.accesstrade.net/sp/cc?rk=0100ong600oxbh",
        "https://h.accesstrade.net/sp/rr?rk=0100ong600oxbh",
    ),
    "robert_walters": (
        "accesstrade_987767",
        "https://h.accesstrade.net/sp/cc?rk=0100ojgk00oxbh",
        "https://h.accesstrade.net/sp/rr?rk=0100ojgk00oxbh",
    ),
}


class ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text: list[str] = []
        self.h2 = 0
        self.paragraphs = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h2":
            self.h2 += 1
        elif tag == "p":
            self.paragraphs += 1

    def handle_data(self, data: str) -> None:
        self.text.append(data)


def japanese_character_count(text: str) -> int:
    return len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff]", text))


def validate(path: Path) -> list[str]:
    if not path.exists():
        return [f"{path.relative_to(ROOT)}: missing"]
    html = path.read_text(encoding="utf-8")
    parser = ArticleParser()
    parser.feed(html)
    visible_text = " ".join(parser.text)
    errors: list[str] = []
    jp_chars = japanese_character_count(visible_text)
    if jp_chars < MIN_JAPANESE_CHARACTERS:
        errors.append(
            f"{path.name}: Japanese character count {jp_chars} < {MIN_JAPANESE_CHARACTERS}"
        )
    if parser.paragraphs < MIN_PARAGRAPHS:
        errors.append(f"{path.name}: paragraphs {parser.paragraphs} < {MIN_PARAGRAPHS}")
    if parser.h2 < MIN_H2:
        errors.append(f"{path.name}: h2 sections {parser.h2} < {MIN_H2}")
    for marker in REQUIRED_MARKERS:
        if marker not in visible_text:
            errors.append(f"{path.name}: required marker missing: {marker}")
    for marker in FORBIDDEN_MARKERS:
        if marker in visible_text:
            errors.append(f"{path.name}: reader-irrelevant/internal marker found: {marker}")
    if 'class="partner-label">広告<' not in html or "※アフィリエイト広告です。" not in visible_text:
        errors.append(f"{path.name}: affiliate disclosure missing")
    for partner_id, (offer_id, destination, tracking) in PARTNER_CONTRACTS.items():
        section = re.search(
            rf'<section class="partner-option" data-partner-id="{partner_id}" '
            rf'data-offer-id="{offer_id}">(.*?)</section>',
            html,
            re.DOTALL,
        )
        if not section:
            errors.append(f"{path.name}: approved partner missing: {partner_id}")
            continue
        markup = section.group(1)
        if destination not in markup or tracking not in markup:
            errors.append(f"{path.name}: link contract mismatch: {partner_id}")
        if 'rel="nofollow"' not in markup:
            errors.append(f"{path.name}: nofollow missing: {partner_id}")
        if 'referrerpolicy="no-referrer-when-downgrade"' not in markup:
            errors.append(f"{path.name}: referrer policy missing: {partner_id}")
    return errors


def main() -> int:
    errors = [error for path in ARTICLES for error in validate(path)]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated {len(ARTICLES)} evergreen articles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
