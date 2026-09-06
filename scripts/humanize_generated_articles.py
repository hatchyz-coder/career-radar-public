#!/usr/bin/env python3
from __future__ import annotations

import html
from pathlib import Path
import re

from recover_editorial_queue import ROOT, TOPICS

# Reusable editorial templates sometimes interpolate verb-phrase headings into
# Japanese sentence positions where the result is grammatically unnatural.
# Keep the informative H2, but remove the redundant heading echo from the prose.


def humanize_ja(path: Path, article_id: str) -> bool:
    if not path.is_file():
        return False

    text = path.read_text(encoding="utf-8")
    topic = TOPICS[article_id]
    changed = False

    for idx, (ja_heading, _) in enumerate(topic["sections"]):
        heading = html.escape(ja_heading)
        h2 = rf"(<h2>{re.escape(heading)}</h2>\s*<p>)"
        replacements = (
            (
                re.compile(h2 + rf"まず基準線を置きます。{re.escape(heading)}を考えるとき、"),
                r"\1まず基準線を置きます。この論点を考えるときは、",
            ),
            (
                re.compile(h2 + rf"{re.escape(heading)}を実績として語るなら、"),
                r"\1この論点を実績として語るなら、",
            ),
            (
                re.compile(h2 + rf"{re.escape(heading)}は、数字の大小だけで評価しません。"),
                r"\1ここでは、数字の大小だけで評価しません。",
            ),
            (
                re.compile(h2 + rf"{re.escape(heading)}では、"),
                r"\1ここでは、",
            ),
            (
                re.compile(h2 + rf"{re.escape(heading)}を考えるときは、"),
                r"\1この論点を考えるときは、",
            ),
            (
                re.compile(h2 + rf"{re.escape(heading)}は、案件が終わった瞬間に"),
                r"\1この種の経験は、案件が終わった瞬間に",
            ),
            (
                re.compile(h2 + rf"{re.escape(heading)}は、最終的に"),
                r"\1この論点は、最終的に",
            ),
            (
                re.compile(
                    rf'(<p data-editorial-depth="{re.escape(article_id)}-ja-{idx}">)'
                    + rf"{re.escape(heading)}について、"
                ),
                r"\1",
            ),
        )
        for pattern, replacement in replacements:
            text, count = pattern.subn(replacement, text, count=1)
            changed = changed or bool(count)

    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def assert_no_heading_echo(path: Path, article_id: str) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    topic = TOPICS[article_id]
    for idx, (ja_heading, _) in enumerate(topic["sections"]):
        heading = html.escape(ja_heading)
        forbidden = (
            f"{heading}を考えるとき、",
            f"{heading}を実績として語るなら、",
            f"{heading}について、",
        )
        for phrase in forbidden:
            if phrase in text:
                raise SystemExit(f"awkward generated heading echo remains in {path}: {phrase}")
        marker = f'data-editorial-depth="{article_id}-ja-{idx}"'
        if marker in text and f'>{heading}について、' in text:
            raise SystemExit(f"awkward depth heading echo remains in {path}: {heading}")


def main() -> int:
    changed = 0
    for article_id in TOPICS:
        path = ROOT / "ja" / "articles" / f"{article_id}.html"
        if humanize_ja(path, article_id):
            changed += 1
        assert_no_heading_echo(path, article_id)
    print(f"Humanized {changed} generated Japanese article page(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
