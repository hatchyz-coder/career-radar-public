#!/usr/bin/env python3
from __future__ import annotations

import html
from pathlib import Path
import re

from recover_editorial_queue import ROOT, TOPICS

# `polish_generated_articles.py` intentionally uses reusable structures. Some
# Japanese section headings are verb phrases, so interpolating them directly
# into those structures can produce constructions such as
# “市場評価と求人在庫を分けるを考えるとき”. This pass removes the heading
# echo from the prose while keeping the section heading itself intact.


def humanize_ja(path: Path, article_id: str) -> bool:
    if not path.is_file():
        return False

    text = path.read_text(encoding="utf-8")
    topic = TOPICS[article_id]
    changed = False

    for ja_heading, _ in topic["sections"]:
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
        )
        for pattern, replacement in replacements:
            text, count = pattern.subn(replacement, text, count=1)
            changed = changed or bool(count)

    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def main() -> int:
    changed = 0
    for article_id in TOPICS:
        path = ROOT / "ja" / "articles" / f"{article_id}.html"
        if humanize_ja(path, article_id):
            changed += 1
    print(f"Humanized {changed} generated Japanese article page(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
