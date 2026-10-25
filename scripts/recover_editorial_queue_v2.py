#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import recover_editorial_queue as legacy

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "data" / "editorial_topic_extension.json"


def topic_is_curated(topic: dict) -> bool:
    sections = topic.get("sections")
    section_copy = topic.get("section_copy")
    if not isinstance(sections, list) or not sections:
        return False
    if not isinstance(section_copy, list) or len(section_copy) != len(sections):
        return False
    for copy in section_copy:
        if not isinstance(copy, dict):
            return False
        for locale in ("ja", "en"):
            paragraphs = copy.get(locale)
            if (
                not isinstance(paragraphs, list)
                or len(paragraphs) < 2
                or any(not isinstance(paragraph, str) or not paragraph.strip() for paragraph in paragraphs)
            ):
                return False
    return True


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

    # Never schedule a topic that cannot pass the curated-source publication gate.
    # Uncurated topics remain in the planning inventory but cannot enter the live queue.
    for article_id in planned:
        if topic_is_curated(topics[article_id]) and article_id not in legacy.PLANNED:
            legacy.PLANNED.append(article_id)
    return payload


def validate_queued_curated_sources(extension: dict, cadence: dict) -> None:
    """Fail before rendering if ANY queued extension topic lacks curated bilingual copy.

    Checking future queue entries prevents tomorrow's release from discovering a
    missing source only after it becomes due.
    """
    topics = extension.get("topics", {})
    failures = []
    for row in cadence.get("release_queue", []):
        if row.get("status") != "queued":
            continue
        article_id = row.get("article_id")
        topic = topics.get(article_id)
        if topic is None:
            continue
        if not topic_is_curated(topic):
            sections = topic.get("sections")
            required = len(sections) if isinstance(sections, list) else 0
            failures.append(
                f"{article_id}: section_copy must contain one bilingual entry per section "
                f"({required} required)"
            )

    if failures:
        detail = "\n- ".join(failures)
        raise SystemExit(
            "STOP: queued editorial release lacks curated bilingual source copy; "
            "generic fallback publication is forbidden:\n- " + detail
        )


# Backward-compatible name retained for tests/importers.
def validate_due_curated_sources(extension: dict, cadence: dict, today: date) -> None:
    del today
    validate_queued_curated_sources(extension, cadence)


def main() -> int:
    extension = load_extension()
    cadence = json.loads(legacy.CADENCE.read_text(encoding="utf-8"))
    validate_queued_curated_sources(extension, cadence)
    return legacy.main()


if __name__ == "__main__":
    raise SystemExit(main())
