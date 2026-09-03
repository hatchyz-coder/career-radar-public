#!/usr/bin/env python3
"""Convert scored traffic opportunities into an execution queue.

This does not publish content. It produces deterministic, reviewable actions that
future automation can execute once Search Console has enough signal.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "traffic_opportunities.json"
OUTPUT = ROOT / "data" / "traffic_action_queue.json"

ACTION_MAP = {
    "new_article": ("create_article", "editorial"),
    "existing_page_rewrite": ("rewrite_existing", "editorial"),
    "title_meta_test": ("optimize_snippet", "seo"),
    "refresh_and_internal_link": ("refresh_and_link", "seo"),
    "cluster_or_expand": ("expand_topic_cluster", "editorial"),
    "wait_for_more_data": ("observe", "monitoring"),
}


def main() -> None:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    opportunities = payload.get("top_opportunities", [])
    queue = []
    for rank, item in enumerate(opportunities, 1):
        recommended = item.get("recommended_action", "wait_for_more_data")
        action_type, lane = ACTION_MAP.get(recommended, ("observe", "monitoring"))
        score = float(item.get("priority_score") or 0)
        if score >= 75:
            priority = "P0"
        elif score >= 55:
            priority = "P1"
        elif score >= 35:
            priority = "P2"
        else:
            priority = "P3"
        queue.append({
            "rank": rank,
            "priority": priority,
            "lane": lane,
            "action_type": action_type,
            "query": item.get("query", ""),
            "target_page": item.get("page", ""),
            "priority_score": score,
            "category": item.get("category", "observe"),
            "reason": item.get("reason", ""),
            "guardrail": "No automatic public rewrite until the item has non-zero Search Console impressions and passes content-quality checks.",
            "status": "queued" if action_type != "observe" else "observing",
        })

    out = {
        "schema_version": "traffic-action-queue.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_generated_at": payload.get("generated_at"),
        "site": payload.get("site", "https://career.hdnjapan.com/"),
        "actionable_count": sum(1 for x in queue if x["status"] == "queued"),
        "items": queue[:50],
    }
    OUTPUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Planned {out['actionable_count']} actionable traffic tasks from {len(queue)} opportunities.")


if __name__ == "__main__":
    main()
