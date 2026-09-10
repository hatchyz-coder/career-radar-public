#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = (
    "Career Review",
    "Career Gap",
    "Opportunity Path",
    "Next Action",
    "Career Capital",
    "Evidence-first",
    ">Paths<",
    ">Insights<",
    "Market test",
    "Career paths",
    "How it works",
    "Topic guide",
    "New / JP + EN",
    "Case Card",
    "Signal Matrix",
)


def main() -> None:
    errors: list[str] = []
    checked = 0
    for path in sorted(ROOT.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        if '<html lang="ja"' not in text and "<html lang='ja'" not in text:
            continue
        checked += 1
        for token in FORBIDDEN:
            if token in text:
                errors.append(f"{path.relative_to(ROOT)}: English-first UI token remains: {token}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Japanese UI language healthy: checked_pages={checked}")


if __name__ == "__main__":
    main()
