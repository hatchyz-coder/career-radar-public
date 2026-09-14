#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import recover_editorial_queue as legacy

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "data" / "editorial_topic_extension.json"


def load_extension() -> None:
    payload = json.loads(EXT.read_text(encoding="utf-8"))
    topics = payload.get("topics", {})
    planned = payload.get("planned", [])
    if not isinstance(topics, dict) or not isinstance(planned, list):
        raise SystemExit("Invalid editorial topic extension schema")
    missing = [article_id for article_id in planned if article_id not in topics]
    if missing:
        raise SystemExit(f"Extension planned topic missing definition: {', '.join(missing)}")
    overlap = sorted(set(topics) & set(legacy.TOPICS))
    if overlap:
        raise SystemExit(f"Extension topic collides with legacy topic: {', '.join(overlap)}")
    legacy.TOPICS.update(topics)
    for article_id in planned:
        if article_id not in legacy.PLANNED:
            legacy.PLANNED.append(article_id)


def main() -> int:
    load_extension()
    return legacy.main()


if __name__ == "__main__":
    raise SystemExit(main())
