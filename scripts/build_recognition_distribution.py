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

REDISTRIBUTION_ANGLES = {
    "consulting-market-signal-matrix": {
        "day3": (
            "案件が来ないという事実と、市場価値が低いという結論は同じではありません。求人在庫、担当者の得意領域、タイミングを分けて見ないと、一つの窓口の反応を市場全体と誤認します。",
            "いま受けている評価は、本当に市場全体の評価でしょうか。"
        ),
        "day7": (
            "1週間たっても残る問いは、『自分は何ができる人か』ではなく『発注側が何を任せられる人だと理解できるか』です。",
            "成果・役割・業界知識・推進力・経営層対応を分けて、自分のSignalを説明できるでしょうか。"
        ),
    },
    "portfolio-evidence-scorecard": {
        "day3": (
            "職務経歴書に経験を足すだけでは、実績は強くなりません。採用側が知りたいのは、別の環境でも再現できそうかを判断できる証拠です。",
            "肩書きを消しても価値が伝わる実績が、いくつ残るでしょうか。"
        ),
        "day7": (
            "1週間後に見直すなら、実績の数ではなく証拠の質です。数字、意思決定、第三者確認、成果物が同じ事実につながっているかを見ます。",
            "一つの実績を、職務経歴書・面談・ポートフォリオで一貫して説明できる状態でしょうか。"
        ),
    },
    "ai-assisted-career-research": {
        "day3": (
            "AIで転職市場を調べると、答えはすぐ出ます。ただし、求人が古い、年収相場の母数が不明、出典が二次情報ということは珍しくありません。",
            "その数字は、いつ・どの求人群・どの一次情報から出たものか説明できるでしょうか。"
        ),
        "day7": (
            "AIを使った市場調査で本当に差が出るのは、要約の速さではなく検証の設計です。",
            "AIの回答と、自分で確認した一次情報を分けて記録できているでしょうか。"
        ),
    },
    "high-value-pmo-deliverables": {
        "day3": (
            "PMOの成果物は、枚数が多いほど価値が高いわけではありません。意思決定を速め、課題の滞留を減らし、リスクを早く見せるために使われて初めて価値になります。",
            "その資料がなくなったら、意思決定は本当に遅くなるでしょうか。"
        ),
        "day7": (
            "PMO経験を『議事録・進捗管理・課題表』で説明すると、作業経験に見えます。市場価値になるのは、何を決めさせ、何を前に進めたかです。",
            "自分がいたことで、何が決まり、何が動き、何が止まらずに済んだかを説明できるでしょうか。"
        ),
    },
    "salary-vs-career-capital-tradeoff": {
        "day3": (
            "年収が上がる転職でも、意思決定権や希少経験が減れば、3年後の選択肢は狭くなることがあります。",
            "目先の報酬差と、3年後に持ち運べる実績を別々に採点しているでしょうか。"
        ),
        "day7": (
            "転職条件を1週間置いて見直すと、年収以外の差が見えます。権限、専門性、ブランド、学習速度、次の市場への接続性です。",
            "その仕事は、今より高く売れる自分を作るでしょうか。"
        ),
    },
    "direct-client-acquisition-playbook": {
        "day3": (
            "紹介会社を使わないことが目的ではありません。目的は、一つの仲介者の都合で仕事の入口が止まらない状態を作ることです。",
            "元同僚、顧客、LinkedIn、専門コミュニティなど、別経路から案件を作れるでしょうか。"
        ),
        "day7": (
            "直接案件で必要なのは営業トークより、相手が安心して任せられる証拠です。Case Card、成果、第三者評価、再依頼がその役割を持ちます。",
            "『何ができます』ではなく『何を変えました』で説明できる実績があるでしょうか。"
        ),
    },
}


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


def phase_angle(article_id: str, title: str, phase: str) -> tuple[str, str]:
    if phase == "day0":
        return (
            "仕事の入口や市場評価を一つの会社・一人の担当者だけに委ねない。CareerRadarでは、今回のテーマを『自分で選択肢を増やせる状態をどう作るか』という視点で整理しました。",
            "一つの評価を結論にせず、複数の経路で市場の反応を確かめる。そのための材料として読んでみてください。",
        )
    mapped = REDISTRIBUTION_ANGLES.get(article_id, {}).get(phase)
    if mapped:
        return mapped
    if phase == "day3":
        return (
            f"公開から3日たって、もう一度『{title}』を考えます。最初に読んだ時より、自分の経験に置き換えると違う論点が見えることがあります。",
            "記事の主張を一つ、自分の実績や次の行動に置き換えてみてください。",
        )
    return (
        f"1週間後に『{title}』を読み返すなら、知識として理解したかではなく、行動や判断が一つでも変わったかを見ます。",
        "この1週間で、次の選択肢を増やす行動を一つ実行できたでしょうか。",
    )


def build_copy(title: str, url: str, article_id: str, platform: str, phase: str) -> str:
    link = tracked(url, platform, article_id, phase)
    hook, close = phase_angle(article_id, title, phase)
    prefix = f"【{title}】" if phase == "day0" else (f"【3日後にもう一度考えたい：{title}】" if phase == "day3" else f"【1週間後の問い：{title}】")
    if platform == "linkedin":
        return f"{prefix}\n\n{hook}\n\n{close}\n\nCareerRadarで深掘り：\n{link}\n\n#CareerRadar #キャリア #市場価値"
    if platform == "facebook":
        return f"{prefix}\n\n{hook}\n\n{close}\n\nCareerRadarでは、感覚だけで結論を出さず、実績・判断・市場反応を分けて考えます。\n\n{link}\n\n#CareerRadar #キャリア"
    short_prefix = f"【{title}】"
    return f"{short_prefix}\n{close}\n{link}\n#CareerRadar"


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
