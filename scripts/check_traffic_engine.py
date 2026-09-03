#!/usr/bin/env python3
"""Validate CareerRadar Traffic Engine intake, freshness and scored output."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "search_console_queries.json"
OUTPUT = ROOT / "data" / "traffic_opportunities.json"
MAX_STALE_DAYS = 4


def parse_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def fail(message: str) -> None:
    raise SystemExit(f"Traffic Engine unhealthy: {message}")


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    output = json.loads(OUTPUT.read_text(encoding="utf-8"))

    if source.get("schema_version") != "search-console-export.v1":
        fail("unexpected Search Console intake schema")
    if source.get("site") != "https://career.hdnjapan.com/":
        fail("Search Console site does not match CareerRadar")
    if output.get("schema_version") != "traffic-opportunities.v1":
        fail("unexpected opportunity output schema")

    rows = source.get("rows")
    if not isinstance(rows, list):
        fail("source rows must be a list")

    started = parse_date(source.get("monitoring_started_at", "2026-09-03"))
    warmup_days = int(source.get("warmup_days", 7))
    today = datetime.now(timezone.utc).date()
    generated_at = source.get("generated_at")

    if not generated_at:
        age = (today - started).days
        if age <= warmup_days:
            print(f"Traffic Engine warmup: Search Console data not populated yet ({age}/{warmup_days} days).")
        else:
            fail("Search Console data is still empty after the warmup window")
    else:
        generated = parse_datetime(generated_at).date()
        stale_days = (today - generated).days
        if stale_days > MAX_STALE_DAYS:
            fail(f"Search Console source is stale by {stale_days} days (limit {MAX_STALE_DAYS})")

    required = {"query", "page", "clicks", "impressions", "ctr", "position"}
    seen = set()
    for idx, row in enumerate(rows):
        missing = required - set(row)
        if missing:
            fail(f"row {idx} missing fields: {sorted(missing)}")
        key = (str(row["query"]).strip(), str(row["page"]).strip())
        if key in seen:
            fail(f"duplicate query/page row: {key}")
        seen.add(key)
        clicks = int(row["clicks"])
        impressions = int(row["impressions"])
        ctr = float(row["ctr"])
        position = float(row["position"])
        if clicks < 0 or impressions < 0 or clicks > impressions:
            fail(f"invalid clicks/impressions in row {idx}")
        if not 0 <= ctr <= 1:
            fail(f"invalid CTR in row {idx}")
        if position <= 0:
            fail(f"invalid position in row {idx}")

    if output.get("input_rows") != len(rows):
        fail("scored output input_rows does not match source row count")
    opportunities = output.get("top_opportunities", [])
    if not isinstance(opportunities, list):
        fail("top_opportunities must be a list")
    scores = [float(item.get("priority_score", -1)) for item in opportunities]
    if scores != sorted(scores, reverse=True):
        fail("opportunities are not sorted by descending priority")
    if any(score < 0 or score > 100 for score in scores):
        fail("priority score out of 0-100 range")

    actionable = sum(
        int(output.get("summary", {}).get(category, 0))
        for category in ("quick_win", "ctr_fix", "content_gap", "defend", "long_term")
    )
    print(f"Traffic Engine healthy: {len(rows)} source rows, {actionable} actionable opportunities.")


if __name__ == "__main__":
    main()
