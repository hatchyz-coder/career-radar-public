#!/usr/bin/env python3
"""Turn Search Console query/page rows into prioritized CareerRadar traffic opportunities.

Input: data/search_console_queries.json
Output: data/traffic_opportunities.json

The scorer is deliberately deterministic and dependency-free so it can run in GitHub Actions.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "search_console_queries.json"
OUTPUT = ROOT / "data" / "traffic_opportunities.json"

EXPECTED_CTR = {
    1: 0.28,
    2: 0.15,
    3: 0.11,
    4: 0.08,
    5: 0.06,
    6: 0.05,
    7: 0.04,
    8: 0.035,
    9: 0.03,
    10: 0.025,
}


def expected_ctr(position: float) -> float:
    p = max(1, int(round(position)))
    if p <= 10:
        return EXPECTED_CTR[p]
    if p <= 20:
        return 0.015
    if p <= 50:
        return 0.008
    return 0.004


def clean_page(page: str) -> str:
    if not page:
        return ""
    parsed = urlparse(page)
    return parsed.path or "/"


def classify(impressions: int, clicks: int, ctr: float, position: float, page: str) -> tuple[str, str]:
    exp = expected_ctr(position)
    ctr_ratio = ctr / exp if exp else 0.0
    path = clean_page(page)
    generic_page = path in {"", "/", "/index.html", "/review.html"}

    if impressions >= 20 and 4 <= position <= 20:
        return "quick_win", "既にGoogleに評価され始めており、上位10位へ押し上げる余地が大きい"
    if impressions >= 30 and position <= 10 and ctr_ratio < 0.65:
        return "ctr_fix", "順位に対してCTRが弱く、タイトル・description改善の費用対効果が高い"
    if impressions >= 20 and position > 20 and generic_page:
        return "content_gap", "検索需要はあるが専用記事への着地が弱く、新規記事候補"
    if impressions >= 50 and position <= 3:
        return "defend", "上位表示済み。内容更新と内部リンクで順位防衛を優先"
    if impressions >= 10 and position > 20:
        return "long_term", "需要シグナルはあるが順位が低く、記事強化または新規クラスタ候補"
    return "observe", "データ量がまだ小さいため継続観測"


def score(row: dict) -> dict:
    query = str(row.get("query", "")).strip()
    page = str(row.get("page", "")).strip()
    impressions = int(row.get("impressions") or 0)
    clicks = int(row.get("clicks") or 0)
    ctr = float(row.get("ctr") or (clicks / impressions if impressions else 0.0))
    position = float(row.get("position") or 100.0)
    category, reason = classify(impressions, clicks, ctr, position, page)

    exp_ctr = expected_ctr(position)
    missed_clicks = max(0.0, impressions * exp_ctr - clicks)
    position_factor = max(0.0, (35.0 - min(position, 35.0)) / 35.0)
    demand = math.log1p(impressions) / math.log(101)
    opportunity = math.log1p(missed_clicks) / math.log(31)
    category_bonus = {
        "quick_win": 0.24,
        "ctr_fix": 0.22,
        "content_gap": 0.18,
        "defend": 0.12,
        "long_term": 0.10,
        "observe": 0.0,
    }[category]
    raw = 0.34 * demand + 0.26 * position_factor + 0.24 * opportunity + category_bonus
    priority_score = round(min(100.0, raw * 100.0), 1)

    action = {
        "quick_win": "existing_page_rewrite",
        "ctr_fix": "title_meta_test",
        "content_gap": "new_article",
        "defend": "refresh_and_internal_link",
        "long_term": "cluster_or_expand",
        "observe": "wait_for_more_data",
    }[category]

    return {
        "query": query,
        "page": page,
        "clicks": clicks,
        "impressions": impressions,
        "ctr": round(ctr, 5),
        "position": round(position, 2),
        "expected_ctr": round(exp_ctr, 5),
        "estimated_missed_clicks": round(missed_clicks, 1),
        "category": category,
        "recommended_action": action,
        "reason": reason,
        "priority_score": priority_score,
    }


def main() -> None:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        raise SystemExit("rows must be a list")

    opportunities = [score(r) for r in rows if str(r.get("query", "")).strip()]
    opportunities.sort(key=lambda x: (-x["priority_score"], -x["impressions"], x["position"], x["query"]))

    summary = {k: 0 for k in ("quick_win", "ctr_fix", "content_gap", "defend", "long_term", "observe")}
    for item in opportunities:
        summary[item["category"]] += 1

    result = {
        "schema_version": "traffic-opportunities.v1",
        "site": payload.get("site", "https://career.hdnjapan.com/"),
        "source_window": payload.get("window", {}),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_rows": len(rows),
        "scored_rows": len(opportunities),
        "summary": summary,
        "top_opportunities": opportunities[:100],
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Traffic Engine scored {len(opportunities)} rows; top priority items written to {OUTPUT}")


if __name__ == "__main__":
    main()
