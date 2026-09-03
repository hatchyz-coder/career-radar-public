#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
EVERGREEN = (
    ROOT / "articles" / "career-navigation.html",
    ROOT / "articles" / "consulting-career-capital.html",
    ROOT / "articles" / "freelance-transition.html",
    ROOT / "articles" / "high-class-transition.html",
)
BASELINE_BILINGUAL_IDS = (
    "midcareer-40s-career-capital",
    "ai-era-high-value-experience",
    "freelance-transition-risk",
    "operator-to-consulting-signal",
    "high-value-pm-evidence",
)
PARTNER_CONTRACTS = {
    "jac_recruitment": ("accesstrade_290807", "https://h.accesstrade.net/sp/cc?rk=01004u3700oxbh", "https://h.accesstrade.net/sp/rr?rk=01004u3700oxbh"),
    "enworld": ("accesstrade_961674", "https://h.accesstrade.net/sp/cc?rk=0100o60a00oxbh", "https://h.accesstrade.net/sp/rr?rk=0100o60a00oxbh"),
    "enworld_it_saas": ("accesstrade_994914", "https://h.accesstrade.net/sp/cc?rk=0100ong600oxbh", "https://h.accesstrade.net/sp/rr?rk=0100ong600oxbh"),
    "robert_walters": ("accesstrade_987767", "https://h.accesstrade.net/sp/cc?rk=0100ojgk00oxbh", "https://h.accesstrade.net/sp/rr?rk=0100ojgk00oxbh"),
}
FORBIDDEN = ("PR #", "マージ", "運営側の都合", "収益化のため", "広告報酬", "production_active")


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text: list[str] = []
        self.h1 = self.h2 = self.paragraphs = 0
        self._in_p = False
        self._p: list[str] = []
        self.paragraph_texts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h1":
            self.h1 += 1
        elif tag == "h2":
            self.h2 += 1
        elif tag == "p":
            self.paragraphs += 1
            self._in_p = True
            self._p = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self._in_p:
            value = re.sub(r"\s+", " ", " ".join(self._p)).strip()
            if value:
                self.paragraph_texts.append(value)
            self._in_p = False
            self._p = []

    def handle_data(self, data: str) -> None:
        self.text.append(data)
        if self._in_p:
            self._p.append(data)


def partner_errors(path: Path, source: str) -> list[str]:
    errors: list[str] = []
    if 'class="partner-label"' not in source:
        errors.append(f"{path}: affiliate label missing")
    for partner_id, (offer_id, destination, tracking) in PARTNER_CONTRACTS.items():
        match = re.search(
            rf'<section class="partner-option" data-partner-id="{partner_id}" data-offer-id="{offer_id}">(.*?)</section>',
            source,
            re.DOTALL,
        )
        if not match:
            errors.append(f"{path}: approved partner missing: {partner_id}")
            continue
        markup = match.group(1)
        for required in (destination, tracking, 'rel="nofollow"', 'referrerpolicy="no-referrer-when-downgrade"'):
            if required not in markup:
                errors.append(f"{path}: partner contract mismatch: {partner_id}: {required}")
    return errors


def duplicate_errors(path: Path, paragraphs: list[str]) -> list[str]:
    normalized = [re.sub(r"\s+", " ", p).strip().lower() for p in paragraphs if len(p) >= 120]
    counts = Counter(normalized)
    repeated = [(text, count) for text, count in counts.items() if count >= 3]
    if not repeated:
        return []
    max_count = max(count for _, count in repeated)
    return [f"{path}: repeated long-form paragraph detected ({max_count} occurrences)"]


def validate(path: Path, locale: str, *, evergreen: bool = False) -> list[str]:
    if not path.exists():
        return [f"{path.relative_to(ROOT)}: missing"]
    source = path.read_text(encoding="utf-8")
    parser = Parser()
    parser.feed(source)
    visible = " ".join(parser.text)
    errors: list[str] = []
    if parser.h1 != 1:
        errors.append(f"{path}: h1 count {parser.h1} != 1")
    if parser.h2 < (12 if evergreen else 8):
        errors.append(f"{path}: h2 count {parser.h2} below content floor")
    if parser.paragraphs < (29 if evergreen else 22):
        errors.append(f"{path}: paragraph count {parser.paragraphs} below content floor")
    if locale == "ja":
        jp_chars = len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff]", visible))
        if jp_chars < (3300 if evergreen else 3200):
            errors.append(f"{path}: Japanese character count {jp_chars} below floor")
    else:
        words = len(re.findall(r"\b[\w’'-]+\b", visible))
        if words < 1750:
            errors.append(f"{path}: English word count {words} below floor")
    for marker in FORBIDDEN:
        if marker in visible:
            errors.append(f"{path}: reader-irrelevant/internal marker found: {marker}")
    if "https://career.hdnjapan.com/" in source and 'rel="canonical"' not in source and not evergreen:
        errors.append(f"{path}: canonical missing")
    if not evergreen:
        for hreflang in ('hreflang="ja"', 'hreflang="en"', 'hreflang="x-default"'):
            if hreflang not in source:
                errors.append(f"{path}: {hreflang} missing")
        errors.extend(duplicate_errors(path, parser.paragraph_texts))
    errors.extend(partner_errors(path, source))
    return errors


def generated_published_ids() -> list[str]:
    cadence = ROOT / "data" / "editorial_cadence.json"
    if not cadence.is_file():
        return []
    payload = json.loads(cadence.read_text(encoding="utf-8"))
    result = []
    for item in payload.get("release_queue", []):
        if item.get("status") != "published":
            continue
        if item.get("published_at", "") >= "2026-09-03":
            result.append(item["article_id"])
    return result


def main() -> int:
    errors: list[str] = []
    for path in EVERGREEN:
        errors.extend(validate(path, "ja", evergreen=True))

    ids = list(dict.fromkeys([*BASELINE_BILINGUAL_IDS, *generated_published_ids()]))
    for article_id in ids:
        errors.extend(validate(ROOT / "ja" / "articles" / f"{article_id}.html", "ja"))
        errors.extend(validate(ROOT / "en" / "articles" / f"{article_id}.html", "en"))

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated {len(EVERGREEN)} evergreen articles and {len(ids)} bilingual article pairs with duplication guard.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
