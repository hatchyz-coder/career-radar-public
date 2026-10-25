#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CADENCE = ROOT / "data" / "editorial_cadence.json"
EXT = ROOT / "data" / "editorial_topic_extension.json"
MIN_FORWARD_RUNWAY = 4
MIN_CURATED_RESERVE = 4


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def business_gap_days(start: date, end: date) -> int:
    if end <= start:
        return 0
    return sum(
        1
        for offset in range(1, (end - start).days + 1)
        if (start + timedelta(days=offset)).weekday() < 5
    )


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def topic_is_curated(topic: dict) -> bool:
    sections = topic.get("sections")
    copy = topic.get("section_copy")
    if not isinstance(sections, list) or not sections:
        return False
    if not isinstance(copy, list) or len(copy) != len(sections):
        return False
    return all(
        isinstance(row, dict)
        and all(
            isinstance(row.get(locale), list)
            and len(row[locale]) >= 2
            and all(isinstance(p, str) and p.strip() for p in row[locale])
            for locale in ("ja", "en")
        )
        for row in copy
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict-reserve", action="store_true")
    args = parser.parse_args()

    payload = json.loads(CADENCE.read_text(encoding="utf-8"))
    extension = json.loads(EXT.read_text(encoding="utf-8"))
    topics = extension.get("topics", {})
    target = payload["target"]
    weekly = int(target["publications_per_week"])
    maximum_gap = int(target["maximum_gap_days"])

    if weekly < 5:
        return fail("Publication target must remain at least five articles per week.")
    if maximum_gap > 2:
        return fail("Maximum publication gap must not exceed two business days.")

    queue = payload.get("release_queue", [])
    queued = [item for item in queue if item.get("status") == "queued"]
    if len(queued) < MIN_FORWARD_RUNWAY:
        return fail(
            f"Editorial runway too short: {len(queued)} queued article(s); "
            f"at least {MIN_FORWARD_RUNWAY} future business-day releases required."
        )

    ids = [item["article_id"] for item in queued]
    if len(ids) != len(set(ids)):
        return fail("Release queue contains duplicate article IDs.")

    for item in queued:
        topic = topics.get(item["article_id"])
        if topic is not None and not topic_is_curated(topic):
            return fail(f"Queued article lacks curated bilingual source: {item['article_id']}")

    due_dates = [parse_date(item["due_at"]) for item in queued]
    if due_dates != sorted(due_dates) or len(due_dates) != len(set(due_dates)):
        return fail("Release queue dates must be unique and chronological.")

    overdue = [item for item in queued if parse_date(item["due_at"]) < date.today()]
    if overdue:
        details = ", ".join(f"{item['article_id']} ({item['due_at']})" for item in overdue)
        return fail(f"Editorial release overdue: {details}")

    for item in queue:
        if item.get("status") != "published":
            continue
        for locale in item.get("locales", ["ja", "en"]):
            path = ROOT / locale / "articles" / f"{item['article_id']}.html"
            if not path.is_file():
                return fail(f"Published release missing public artifact: {path.relative_to(ROOT)}")

    last = parse_date(payload["last_publication"]["published_at"])
    first_due = due_dates[0]
    if business_gap_days(last, first_due) > maximum_gap:
        return fail("First queued release exceeds maximum business-day publication gap.")

    if business_gap_days(last, date.today()) > maximum_gap and first_due <= date.today():
        return fail("Last publication is stale and no current release has replaced it.")

    known = {item["article_id"] for item in queue}
    curated_reserve = [
        article_id for article_id in extension.get("planned", [])
        if article_id not in known and topic_is_curated(topics.get(article_id, {}))
    ]
    if len(curated_reserve) < MIN_CURATED_RESERVE:
        message = (
            f"Editorial curated reserve low: {len(curated_reserve)} unused curated article(s); "
            f"target reserve is {MIN_CURATED_RESERVE}. Live queued releases remain publishable."
        )
        if args.strict_reserve:
            return fail(message)
        print(f"WARNING: {message}", file=sys.stderr)

    print(
        f"Editorial health OK. Target={weekly}/week; queued={len(queued)}; "
        f"curated_reserve={len(curated_reserve)}; "
        f"next={queued[0]['article_id']} ({queued[0]['due_at']})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
