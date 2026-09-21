#!/usr/bin/env python3
"""Fail-closed quality gate for the four scheduled September editorial releases.

This is a mechanical rejection gate, not a substitute for human semantic review.
"""
from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

from check_content_quality import validate as baseline_validate

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://career.hdnjapan.com"
TARGETS = (
    "resume-achievement-evidence",
    "side-job-career-capital",
    "consulting-scope-creep-risk",
    "ai-automation-role-redesign",
)


class Sections(HTMLParser):
    def __init__(self):
        super().__init__()
        self.headings = []
        self.paragraphs = []
        self._capture = None
        self._buf = []
        self._section = -1
        self.h1 = 0

    def handle_starttag(self, tag, attrs):
        if tag == "h1":
            self.h1 += 1
        if tag in ("h2", "p"):
            self._capture = tag
            self._buf = []

    def handle_data(self, data):
        if self._capture:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag == self._capture:
            value = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if tag == "h2":
                self.headings.append(value)
                self._section = len(self.headings) - 1
            elif value:
                self.paragraphs.append((self._section, value))
            self._capture = None
            self._buf = []


def repetition_errors(parsed, core_indexes, locale, aid):
    by_sentence = {}
    for section, text in parsed.paragraphs:
        if section not in core_indexes:
            continue
        # Keep sentence boundaries; generic filler is repeated as identical sentences.
        sentences = (re.split(r"(?<=[。！？])", text) if locale == "ja"
                     else re.split(r"(?<=[.!?])\s+", text))
        for sentence in sentences:
            sentence = re.sub(r"\s+", " ", sentence).strip().lower()
            if len(sentence) >= (70 if locale == "ja" else 110):
                by_sentence.setdefault(sentence, set()).add(section)
    counts = sorted(((len(sections), sentence) for sentence, sections in by_sentence.items()
                     if len(sections) >= 3), reverse=True)
    return [f"{aid}/{locale}: same long-form sentence appears in {count} different core sections: {sentence[:90]}"
            for count, sentence in counts[:3]]


def validate_article(root, topic, aid, locale, cadence, index, sitemap):
    path = root / locale / "articles" / f"{aid}.html"
    if not path.is_file():
        return [f"{aid}/{locale}: missing HTML"]
    source = path.read_text(encoding="utf-8")
    parsed = Sections()
    parsed.feed(source)
    errors = []
    headings = [pair[0 if locale == "ja" else 1] for pair in topic["sections"]]
    indexes = []
    for heading in headings:
        found = [i for i, actual in enumerate(parsed.headings) if actual == heading]
        if len(found) != 1:
            errors.append(f"{aid}/{locale}: expected one H2 named {heading!r}, found {len(found)}")
        else:
            indexes.append(found[0])
    if len(indexes) == len(headings) and indexes != sorted(indexes):
        errors.append(f"{aid}/{locale}: core H2 order differs from topic definition")
    for section in indexes:
        if sum(section == i for i, _ in parsed.paragraphs) < 2:
            errors.append(f"{aid}/{locale}: core H2 {parsed.headings[section]!r} has fewer than two paragraphs")
    errors.extend(repetition_errors(parsed, set(indexes), locale, aid))
    errors.extend(str(err) for err in baseline_validate(path, locale))
    expected = f"{SITE}/{locale}/articles/{aid}.html"
    for marker in (
        f'<link rel="canonical" href="{expected}">',
        f'<link rel="alternate" hreflang="ja" href="{SITE}/ja/articles/{aid}.html">',
        f'<link rel="alternate" hreflang="en" href="{SITE}/en/articles/{aid}.html">',
        f'<link rel="alternate" hreflang="x-default" href="{SITE}/ja/articles/{aid}.html">',
        '../../review.html', f"{SITE}/{'en' if locale == 'ja' else 'ja'}/articles/{aid}.html",
    ):
        if marker not in source:
            errors.append(f"{aid}/{locale}: expected canonical/hreflang/CTA/peer-link missing: {marker}")
    if f'ja/articles/{aid}.html' not in index:
        errors.append(f"{aid}/{locale}: Japanese homepage article card missing")
    if f"{SITE}/ja/articles/{aid}.html" not in sitemap or f"{SITE}/en/articles/{aid}.html" not in sitemap:
        errors.append(f"{aid}/{locale}: bilingual sitemap entry missing")
    rows = [x for x in cadence.get("release_queue", []) if x["article_id"] == aid]
    if len(rows) != 1 or rows[0].get("status") != "published":
        errors.append(f"{aid}/{locale}: publication status is not published exactly once")
    return errors


def evaluate(root, *, only_published=True):
    cadence = json.loads((root / "data" / "editorial_cadence.json").read_text(encoding="utf-8"))
    topic_extension = json.loads((root / "data" / "editorial_topic_extension.json").read_text(encoding="utf-8"))["topics"]
    index = (root / "index.html").read_text(encoding="utf-8")
    sitemap = (root / "sitemap.xml").read_text(encoding="utf-8")
    errors = []
    for aid in TARGETS:
        rows = [row for row in cadence.get("release_queue", []) if row.get("article_id") == aid]
        if not rows:
            errors.append(f"{aid}: missing from release_queue")
            continue
        if only_published and not any(row.get("status") == "published" for row in rows):
            continue
        if aid not in topic_extension:
            errors.append(f"{aid}: topic extension missing")
            continue
        for locale in ("ja", "en"):
            errors.extend(validate_article(root, topic_extension[aid], aid, locale, cadence, index, sitemap))
    return errors


def main():
    errors = evaluate(ROOT)
    if errors:
        print("RELEASE QUALITY GATE FAILED - no publication commit allowed:", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("RELEASE QUALITY GATE PASSED for all currently published target articles (mechanical checks only).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
