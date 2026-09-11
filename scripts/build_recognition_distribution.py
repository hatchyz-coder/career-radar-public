#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SOCIAL_DIR = ROOT / "data" / "social"
OUT_JSON = SOCIAL_DIR / "recognition-plan.json"
OUT_MD = SOCIAL_DIR / "recognition-plan.md"
JST = ZoneInfo("Asia/Tokyo")
ARCHIVE_RE = re.compile(r"^(?P<published>\d{4}-\d{2}-\d{2})-(?P<article>.+)\.md$")
TITLE_RE = re.compile(r"^【([^】]+)】", re.MULTILINE)
URL_RE = re.compile(r"https://career\.hdnjapan\.com/[^\s]+")


def section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*\n\n(.*?)(?=\n\n---\n\n## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def clean_title(copy: str, article_id: str) -> str:
    match = TITLE_RE.search(copy)
    if not match:
        return article_id
    title = match.group(1).split(" / ", 1)[0].strip()
    return title or article_id


def base_url(copy: str, article_id: str) -> str:
    for url in URL_RE.findall(copy):
        if "/ja/articles/" in url:
            return url.split("?", 1)[0]
    return f"https://career.hdnjapan.com/ja/articles/{article_id}.html"


def tracked(url: str, platform: str, article_id: str, phase: str) -> str:
    params = urlencode({
        "utm_source": platform,
        "utm_medium": "social",
        "utm_campaign": "career_radar_recognition",
        "utm_content": f"{article_id}_{phase}",
    })
    return f"{url}?{params}"


def variant(title: str, url: str, platform: str, phase: str) -> str:
    link = tracked(url, platform, title_to_slug_hint(title), phase)
    if phase == "day0":
        hook = f"【{title}】\n\n仕事の入口を一つの会社・一人の担当者に握らせない。CareerRadarでは、今回のテーマを『自分で選択肢を増やせる状態をどう作るか』という視点で整理しました。"
        close = "一つの評価を結論にせず、複数の経路で市場の反応を確かめる。そのための材料として読んでみてください。"
    elif phase == "day3":
        hook = f"【3日後にもう一度考えたい：{title}】\n\nキャリアで怖いのは、断られることより『一つの窓口が止まった瞬間に選択肢がなくなること』です。"
        close = "いま使っている仕事の入口が止まったら、別の経路から機会を作れるでしょうか。"
    else:
        hook = f"【1週間後の問い：{title}】\n\n市場価値は、肩書きや一社の反応ではなく『別の場所でも再現できる実績』として説明できるかで見え方が変わります。"
        close = "この1週間で、自分の実績を外部から確認できる形に一つでも変えられたでしょうか。"

    if platform == "linkedin":
        return f"{hook}\n\n{close}\n\nCareerRadarで深掘り：\n{link}\n\n#CareerRadar #キャリア #市場価値"
    if platform == "facebook":
        return f"{hook}\n\n{close}\n\n記事では、感覚論ではなく、実績・判断・市場反応を分けて考える方法をまとめています。\n\n{link}\n\n#CareerRadar #キャリア"
    return f"【{title}】\n{close}\n{link}\n#CareerRadar"


def title_to_slug_hint(title: str) -> str:
    # UTM content is replaced with the canonical article_id later.
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "article"


def build_copy(title: str, url: str, article_id: str, platform: str, phase: str) -> str:
    copy = variant(title, url, platform, phase)
    hint = title_to_slug_hint(title)
    return copy.replace(f"{hint}_{phase}", f"{article_id}_{phase}")


def main() -> None:
    today = datetime.now(JST).date()
    items: list[dict] = []
    for path in sorted(SOCIAL_DIR.glob("*.md")):
        match = ARCHIVE_RE.match(path.name)
        if not match:
            continue
        published = date.fromisoformat(match.group("published"))
        if published > today or published < today - timedelta(days=14):
            continue
        text = path.read_text(encoding="utf-8")
        linkedin = section(text, "LinkedIn")
        facebook = section(text, "Facebook")
        x_copy = section(text, "X")
        if not all((linkedin, facebook, x_copy)):
            continue
        article_id = match.group("article")
        title = clean_title(facebook, article_id)
        url = base_url(facebook, article_id)
        phases = {
            "day0": published,
            "day3": published + timedelta(days=3),
            "day7": published + timedelta(days=7),
        }
        variants = {}
        for phase, due in phases.items():
            variants[phase] = {
                "due_at": due.isoformat(),
                "posts": {
                    "linkedin": build_copy(title, url, article_id, "linkedin", phase),
                    "facebook": build_copy(title, url, article_id, "facebook", phase),
                    "x": build_copy(title, url, article_id, "x", phase),
                },
            }
        items.append({
            "article_id": article_id,
            "title": title,
            "published_at": published.isoformat(),
            "canonical_url": url,
            "variants": variants,
        })

    due: list[dict] = []
    priority = {"day0": 0, "day3": 1, "day7": 2}
    for item in items:
        for phase, payload in item["variants"].items():
            if payload["due_at"] == today.isoformat():
                due.append({
                    "article_id": item["article_id"],
                    "title": item["title"],
                    "phase": phase,
                    "due_at": payload["due_at"],
                    "posts": payload["posts"],
                })
    due.sort(key=lambda row: (priority[row["phase"]], row["article_id"]))
    selected = due[0] if due else None

    payload = {
        "schema_version": "career-radar-recognition-plan.v1",
        "generated_at": datetime.now(JST).isoformat(),
        "timezone": "Asia/Tokyo",
        "policy": {
            "max_career_radar_topics_per_day": 1,
            "platform_priority": ["linkedin", "facebook", "x"],
            "redistribution_days": [0, 3, 7],
            "manual_publish_only": True,
        },
        "due_count": len(due),
        "selected_today": selected,
        "due_today": due,
        "items": sorted(items, key=lambda row: row["published_at"], reverse=True),
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = ["# CareerRadar Recognition Plan", "", f"Generated: {payload['generated_at']}", ""]
    if selected:
        lines += [f"## Today — {selected['phase']} — {selected['title']}", "", "### LinkedIn", "", selected["posts"]["linkedin"], "", "### Facebook", "", selected["posts"]["facebook"], "", "### X", "", selected["posts"]["x"], ""]
    else:
        lines += ["## Today", "", "No CareerRadar redistribution candidate is due today.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Recognition plan ready: items={len(items)}, due_today={len(due)}, selected={selected['article_id'] if selected else 'none'}")


if __name__ == "__main__":
    main()
