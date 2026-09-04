#!/usr/bin/env python3
from __future__ import annotations

from datetime import date, datetime, timedelta
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CADENCE = ROOT / "data" / "editorial_cadence.json"


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def business_gap_days(start: date, end: date) -> int:
    """Count scheduled publication days between two dates, excluding weekends.

    The publisher deliberately replenishes on business days. A Friday -> Monday
    transition must therefore count as one publication day, not a three-day outage.
    """
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


def main() -> int:
    payload = json.loads(CADENCE.read_text(encoding="utf-8"))
    target = payload["target"]
    weekly = int(target["publications_per_week"])
    maximum_gap = int(target["maximum_gap_days"])

    if weekly < 5:
        return fail("Publication target must remain at least five articles per week.")
    if maximum_gap > 2:
        return fail("Maximum publication gap must not exceed two business days.")

    queue = payload.get("release_queue", [])
    queued = [item for item in queue if item.get("status") == "queued"]
    if len(queued) < weekly:
        return fail(f"Editorial runway too short: {len(queued)} queued article(s); at least {weekly} required.")

    ids = [item["article_id"] for item in queued]
    if len(ids) != len(set(ids)):
        return fail("Release queue contains duplicate article IDs.")

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

    print(
        f"Editorial health OK. Target={weekly}/week; queued={len(queued)}; "
        f"next={queued[0]['article_id']} ({queued[0]['due_at']})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
