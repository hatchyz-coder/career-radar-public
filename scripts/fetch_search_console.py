#!/usr/bin/env python3
"""Fetch CareerRadar query/page performance from Google Search Console.

Requires environment variable GSC_SERVICE_ACCOUNT_JSON containing a Google service
account JSON object. The service-account email must be granted access to the
Search Console property https://career.hdnjapan.com/.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "search_console_queries.json"
SITE = "https://career.hdnjapan.com/"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
LAG_DAYS = 3
WINDOW_DAYS = 28
ROW_LIMIT = 25000


def main() -> None:
    raw_secret = os.environ.get("GSC_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw_secret:
        raise SystemExit("GSC_SERVICE_ACCOUNT_JSON is not configured")

    info = json.loads(raw_secret)
    credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    credentials.refresh(Request())

    today = datetime.now(timezone.utc).date()
    end_date = today - timedelta(days=LAG_DAYS)
    start_date = end_date - timedelta(days=WINDOW_DAYS - 1)
    endpoint = (
        "https://www.googleapis.com/webmasters/v3/sites/"
        + quote(SITE, safe="")
        + "/searchAnalytics/query"
    )
    body = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["query", "page"],
        "type": "web",
        "dataState": "final",
        "rowLimit": ROW_LIMIT,
        "startRow": 0,
    }
    response = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    rows = []
    for raw in data.get("rows", []):
        keys = raw.get("keys", [])
        if len(keys) < 2:
            continue
        rows.append(
            {
                "query": keys[0],
                "page": keys[1],
                "clicks": int(raw.get("clicks", 0)),
                "impressions": int(raw.get("impressions", 0)),
                "ctr": round(float(raw.get("ctr", 0.0)), 6),
                "position": round(float(raw.get("position", 0.0)), 3),
            }
        )

    rows.sort(key=lambda row: (-row["impressions"], -row["clicks"], row["position"], row["query"], row["page"]))
    existing = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    payload = {
        "schema_version": "search-console-export.v1",
        "site": SITE,
        "monitoring_started_at": existing.get("monitoring_started_at", "2026-09-03"),
        "warmup_days": int(existing.get("warmup_days", 7)),
        "window": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": WINDOW_DAYS,
        },
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "rows": rows,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Fetched {len(rows)} Search Console query/page rows for {start_date}..{end_date}")


if __name__ == "__main__":
    main()
