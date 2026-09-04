#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
CADENCE = ROOT / "data" / "editorial_cadence.json"
OUT_DIR = ROOT / "data" / "social"
SITE = "https://career.hdnjapan.com"

ANGLES = {
    "consulting-market-signal-matrix": (
        "案件が来ないと、市場価値そのものを否定された気持ちになりがちです。ですが、見えているのは市場全体ではなく、特定チャネルの在庫や担当者の得意領域にすぎないことがあります。",
        ["肩書きではなく『何を任せられる人か』で見る", "成果・役割・業界知識・推進力・経営層対応を分けて見る", "1社の評価ではなく複数チャネルの反応を重ねる"],
        "いま受けている評価は、本当に『市場の評価』でしょうか。それとも一つの窓口から見えた景色でしょうか。",
        "A weak response from one channel is not the same thing as weak market value. Recruiter inventory, timing and role fit can distort the signal.",
    ),
    "portfolio-evidence-scorecard": (
        "職務経歴書は長くなるほど強くなるわけではありません。採用側が知りたいのは、経験の量より『この人に任せても再現できそうか』です。",
        ["担当業務ではなく変化を証拠化する", "意思決定と第三者証明を残す", "役割ごとにEvidenceを並び替える"],
        "あなたの実績は、会社名や肩書きを外しても価値が伝わる形になっているでしょうか。",
        "A longer resume is not automatically a stronger one. Buyers need evidence that your results are repeatable and portable.",
    ),
    "ai-assisted-career-research": (
        "AIで転職市場を調べるのは速い。ただし、速いことと正しいことは別です。古い求人、根拠の薄い年収相場、出典不明の要約をそのまま意思決定に使うのは危険です。",
        ["一次情報から始める", "観測とAIの解釈を分ける", "求人の鮮度・サンプル数・報酬条件を検証する"],
        "AIは調査を短縮できますが、最後の検証までAI任せになっていないでしょうか。",
        "AI makes career research faster, but speed is not the same as reliability. Freshness, sample size and source quality still need verification.",
    ),
    "high-value-pmo-deliverables": (
        "PMOで資料をたくさん作っているのに、単価が上がらない。これは珍しくありません。評価されるのは資料の量ではなく、意思決定をどれだけ前に進めたかです。",
        ["進捗表を意思決定につなげる", "課題にオーナーと期限を置く", "経営報告を短くし、判断点を明確にする"],
        "あなたの成果物は『報告のための資料』でしょうか、それとも『決めるための道具』でしょうか。",
        "PMO value does not come from the volume of trackers and minutes. It comes from making decisions faster and risks visible earlier.",
    ),
    "salary-vs-career-capital-tradeoff": (
        "年収が上がる転職が、必ずしも良い転職とは限りません。目先の100万円アップと引き換えに、意思決定権・専門性・社外で通用する実績を失うこともあります。",
        ["年収とCareer Capitalを別々に採点する", "次の3年で持ち運べる実績が増えるかを見る", "報酬だけでなく選択肢の増減を比較する"],
        "次の仕事は、年収だけでなく3年後の選択肢を増やしてくれるでしょうか。",
        "A salary increase can still be a poor career move if the role reduces decision scope, portable evidence or future options.",
    ),
    "direct-client-acquisition-playbook": (
        "紹介会社を使わない＝全部ひとりで営業する、ではありません。重要なのは、仕事の入口を一つの仲介者に握らせないことです。",
        ["実績をCase Card化して見せる", "元同僚・顧客・LinkedIn・専門コミュニティを分散運用する", "反応を記録し、刺さる専門性を絞る"],
        "いま仕事の入口が止まったとき、別の経路から案件を作れる状態でしょうか。",
        "Direct client acquisition is not about doing everything alone. It is about avoiding dependence on a single intermediary for opportunity flow.",
    ),
}


def extract(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    h1 = re.search(r"<h1>(.*?)</h1>", text, re.S)
    desc = re.search(r'<meta name="description" content="(.*?)">', text, re.S)
    if not h1 or not desc:
        raise SystemExit(f"missing title/description: {path}")
    clean = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
    return clean(h1.group(1)), clean(desc.group(1))


def tracked_url(article_id: str, platform: str, locale: str = "ja") -> str:
    params = {"utm_source": platform, "utm_medium": "social"}
    if platform != "x":
        params.update({"utm_campaign": "career_radar_editorial", "utm_content": f"{article_id}_{locale}"})
    return f"{SITE}/{locale}/articles/{article_id}.html?{urlencode(params)}"


def main() -> None:
    cadence = json.loads(CADENCE.read_text(encoding="utf-8"))
    last = cadence["last_publication"]
    article_id, published_at = last["article_id"], last["published_at"]
    ja_title, ja_desc = extract(ROOT / "ja" / "articles" / f"{article_id}.html")
    en_title, en_desc = extract(ROOT / "en" / "articles" / f"{article_id}.html")

    hook, points, question, en_hook = ANGLES.get(article_id, (
        ja_desc,
        ["市場の反応を一つの評価で決めない", "実績を外部から確認できる形へ変える", "次の行動を小さく試して更新する"],
        "このテーマを、自分の次のキャリア判断にどう使えるでしょうか。",
        en_desc,
    ))
    bullets = "\n".join(f"・{p}" for p in points)
    linkedin_url_ja = tracked_url(article_id, "linkedin", "ja")
    linkedin_url_en = tracked_url(article_id, "linkedin", "en")
    facebook_url = tracked_url(article_id, "facebook", "ja")
    x_url = tracked_url(article_id, "x", "ja")

    linkedin = f"""【{ja_title} / {en_title}】\n\n{hook}\n\nCareerRadarでは今回、次の3点に分けて整理しました。\n{bullets}\n\n{question}\n\n記事はこちら\n{linkedin_url_ja}\n\nEnglish follows below.\n\n{en_hook}\n\nRead the full article:\n{linkedin_url_en}\n\n#CareerRadar #キャリア #転職 #市場価値"""

    facebook = f"""【{ja_title}】\n\n{hook}\n\nキャリアの話になると、私たちはつい『紹介が来た／来ない』『年収が上がった／下がった』『肩書きが強い／弱い』のように、一つの数字や一人の評価者で結論を出しがちです。\n\nでも本当に知りたいのは、別の会社、別の案件、別の働き方でも、自分の経験が価値として通用するかどうかです。\n\n今回のCareerRadarでは、\n{bullets}\nという視点で整理しました。\n\n{question}\n\n転職エージェントも求人サイトも便利です。ただ、キャリアの主導権まで預ける必要はありません。市場を観測し、自分の仮説を持ち、複数の経路で確かめる。そのための材料として使っていただければと思います。\n\n{facebook_url}\n\n#CareerRadar #キャリア #転職 #市場価値"""

    x = f"【{ja_title}】\n一つの評価だけで市場価値を決めない。市場の反応を分解して見るためのフレームです。\n{x_url}\n#CareerRadar"

    if len(linkedin) > 3000:
        raise SystemExit(f"LinkedIn copy too long: {len(linkedin)}")
    if len(x) > 280:
        raise SystemExit(f"X copy too long: {len(x)}")

    payload = {
        "schema_version": "career-radar-social-pack.v1",
        "article_id": article_id,
        "published_at": published_at,
        "article": {"ja_title": ja_title, "en_title": en_title, "ja_description": ja_desc, "en_description": en_desc},
        "posts": {"linkedin": linkedin, "facebook": facebook, "x": x},
        "urls": {"linkedin_ja": linkedin_url_ja, "linkedin_en": linkedin_url_en, "facebook": facebook_url, "x": x_url},
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = f"# CareerRadar Social Pack — {published_at}\n\nArticle: `{article_id}`\n\n## LinkedIn\n\n{linkedin}\n\n---\n\n## Facebook\n\n{facebook}\n\n---\n\n## X\n\n{x}\n"
    (OUT_DIR / f"{published_at}-{article_id}.md").write_text(md, encoding="utf-8")
    (OUT_DIR / "latest.md").write_text(md, encoding="utf-8")
    (OUT_DIR / "latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Social pack ready for {article_id}: LinkedIn={len(linkedin)}, Facebook={len(facebook)}, X={len(x)}")


if __name__ == "__main__":
    main()
