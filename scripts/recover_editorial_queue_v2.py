#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import recover_editorial_queue as legacy

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "data" / "editorial_topic_extension.json"


def load_extension() -> dict:
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
    return payload


def validate_due_curated_sources(extension: dict, cadence: dict, today: date) -> None:
    """Stop before rendering when a due extension topic would use generic fallback copy."""
    topics = extension.get("topics", {})
    failures = []
    for row in cadence.get("release_queue", []):
        if row.get("status") != "queued":
            continue
        article_id = row.get("article_id")
        due_at = row.get("due_at")
        if not isinstance(due_at, str) or due_at > today.isoformat():
            continue
        topic = topics.get(article_id)
        if topic is None:
            continue

        sections = topic.get("sections")
        section_copy = topic.get("section_copy")
        if not isinstance(sections, list) or not sections:
            failures.append(f"{article_id}: sections must be a non-empty list")
            continue
        if not isinstance(section_copy, list) or len(section_copy) != len(sections):
            failures.append(
                f"{article_id}: section_copy must contain one bilingual entry per section "
                f"({len(sections)} required)"
            )
            continue

        for index, copy in enumerate(section_copy, start=1):
            if not isinstance(copy, dict):
                failures.append(f"{article_id}: section_copy[{index}] must be an object")
                continue
            for locale in ("ja", "en"):
                paragraphs = copy.get(locale)
                if (
                    not isinstance(paragraphs, list)
                    or len(paragraphs) < 2
                    or any(not isinstance(paragraph, str) or not paragraph.strip() for paragraph in paragraphs)
                ):
                    failures.append(
                        f"{article_id}: section_copy[{index}].{locale} must contain "
                        "at least two non-empty paragraphs"
                    )

    if failures:
        detail = "\n- ".join(failures)
        raise SystemExit(
            "STOP: due editorial release lacks curated bilingual source copy; "
            "generic fallback publication is forbidden:\n- " + detail
        )


def main() -> int:
    extension = load_extension()
    cadence = json.loads(legacy.CADENCE.read_text(encoding="utf-8"))
    validate_due_curated_sources(extension, cadence, legacy.date.today())
    return legacy.main()


if __name__ == "__main__":
    raise SystemExit(main())
