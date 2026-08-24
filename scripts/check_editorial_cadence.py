#!/usr/bin/env python3
from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CADENCE = ROOT / "data" / "editorial_cadence.json"

def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()

def main() -> int:
    payload = json.loads(CADENCE.read_text(encoding="utf-8"))
    target = payload["target"]
    if target["publications_per_week"] < 5:
        print("Publication target must remain at least five articles per week.", file=sys.stderr)
        return 1
    if target["maximum_gap_days"] > 2:
        print("Maximum publication gap must not exceed two days.", file=sys.stderr)
        return 1
    queued = [item for item in payload["release_queue"] if item["status"] == "queued"]
    if not queued:
        print("Editorial queue is empty.", file=sys.stderr)
        return 1
    due_dates = [parse_date(item["due_at"]) for item in queued]
    if due_dates != sorted(due_dates) or len(due_dates) != len(set(due_dates)):
        print("Release queue dates must be unique and chronological.", file=sys.stderr)
        return 1
    overdue = [item for item in queued if parse_date(item["due_at"]) < date.today()]
    if overdue:
        details = ", ".join(f"{item['article_id']} ({item['due_at']})" for item in overdue)
        print(f"Editorial release overdue: {details}", file=sys.stderr)
        return 1
    last = parse_date(payload["last_publication"]["published_at"])
    first_due = due_dates[0]
    if (first_due - last).days > target["maximum_gap_days"]:
        print("First queued release exceeds maximum publication gap.", file=sys.stderr)
        return 1
    print(
        f"Editorial cadence healthy. Target: {target['publications_per_week']}/week. "
        f"Next release: {queued[0]['article_id']} on {queued[0]['due_at']}."
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
