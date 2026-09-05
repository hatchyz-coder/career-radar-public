#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SOCIAL_DIR = ROOT / "data" / "social"
OUT = ROOT / "editorial-desk-feed.json"
LOOKBACK_DAYS = 14
JST = ZoneInfo("Asia/Tokyo")
ARCHIVE_RE = re.compile(r"^(?P<published>\d{4}-\d{2}-\d{2})-(?P<article>.+)\.md$")
URL_RE = re.compile(r"https://career\.hdnjapan\.com/[^\s]+")


def section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*\n\n(.*?)(?=\n\n---\n\n## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def first_url(copy: str, locale: str | None = None) -> str | None:
    urls = URL_RE.findall(copy)
    if locale:
        marker = f"/{locale}/articles/"
        for url in urls:
            if marker in url:
                return url
    return urls[0] if urls else None


def title_from_copy(copy: str, fallback: str) -> str:
    match = re.search(r"^【([^】]+)】", copy.strip())
    if not match:
        return fallback
    title = match.group(1)
    if " / " in title:
        title = title.split(" / ", 1)[0]
    return title.strip() or fallback


def build_item(path: Path, published_at: str, article_id: str) -> dict:
    text = path.read_text(encoding="utf-8")
    linkedin = section(text, "LinkedIn")
    facebook = section(text, "Facebook")
    x_copy = section(text, "X")
    if not all((linkedin, facebook, x_copy)):
        raise ValueError(f"missing social section(s): {path}")

    published = date.fromisoformat(published_at)
    digest_source = "\n\0\n".join((linkedin, facebook, x_copy)).encode("utf-8")
    content_version = hashlib.sha256(digest_source).hexdigest()[:16]
    title = title_from_copy(facebook, article_id)

    return {
        "stable_id": f"career_radar:{published_at}:{article_id}",
        "source_id": "career_radar",
        "source_label": "CareerRadar",
        "article_id": article_id,
        "published_at": published_at,
        "title": title,
        "content_version": content_version,
        "default_state": "ready_for_review",
        "manual_publish_only": True,
        "recommended_platform_order": ["linkedin", "facebook", "x"],
        "platforms": {
            "linkedin": {
                "priority": "P0",
                "copy": linkedin,
                "url_ja": first_url(linkedin, "ja"),
                "url_en": first_url(linkedin, "en"),
            },
            "facebook": {
                "priority": "P1",
                "copy": facebook,
                "url": first_url(facebook, "ja") or first_url(facebook),
            },
            "x": {
                "priority": "P2",
                "copy": x_copy,
                "url": first_url(x_copy, "ja") or first_url(x_copy),
            },
        },
        "redistribution": {
            "day_3": (published + timedelta(days=3)).isoformat(),
            "day_7": (published + timedelta(days=7)).isoformat(),
            "mode": "candidate_only_review_before_repost",
        },
    }


def main() -> None:
    now = datetime.now(JST)
    today = now.date()
    cutoff = today - timedelta(days=LOOKBACK_DAYS - 1)
    items: list[dict] = []
    warnings: list[str] = []

    for path in sorted(SOCIAL_DIR.glob("*.md"), reverse=True):
        match = ARCHIVE_RE.match(path.name)
        if not match:
            continue
        published_at = match.group("published")
        published = date.fromisoformat(published_at)
        if published < cutoff or published > today:
            continue
        try:
            items.append(build_item(path, published_at, match.group("article")))
        except ValueError as exc:
            warnings.append(str(exc))

    items.sort(key=lambda item: (item["published_at"], item["article_id"]), reverse=True)
    payload = {
        "schema_version": "hdn-editorial-desk-source.v1",
        "source_id": "career_radar",
        "source_label": "CareerRadar",
        "generated_at": now.isoformat(),
        "timezone": "Asia/Tokyo",
        "lookback_days": LOOKBACK_DAYS,
        "manual_publish_only": True,
        "consumer_state_contract": {
            "owner": "HDN Editorial Desk",
            "upsert_key": "stable_id",
            "rule": "Upsert feed content by stable_id. Never reset local completed, carry-over, scheduled, or postponed state during source sync.",
        },
        "item_count": len(items),
        "warnings": warnings,
        "items": items,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"CareerRadar Editorial Desk feed ready: {len(items)} item(s), {len(warnings)} warning(s)")


if __name__ == "__main__":
    main()
