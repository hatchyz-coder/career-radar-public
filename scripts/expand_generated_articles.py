#!/usr/bin/env python3
from __future__ import annotations

import html
from pathlib import Path
import re

from recover_editorial_queue import ROOT, TOPICS


def depth_text(locale: str, heading: str, idx: int) -> str:
    if locale == "ja":
        variants = [
            "この観点を実務へ落とすときは、直近3件の経験を並べ、同じ評価軸で比較してください。強い経験だけを選ぶのではなく、うまくいかなかった案件も含めて、判断材料、関係者、制約、結果を書き出します。共通して再現できた行動が見つかれば、それが次の職場でも使えるCareer Capitalの候補です。",
            "次の面談までに、相手へ確認する質問を3つ用意します。期待成果、意思決定権、評価方法を聞けば、その仕事が単なる作業なのか、将来の市場価値につながる経験なのかを見分けやすくなります。条件面だけでなく、何を任されるかまで比較することが重要です。",
            "改善するときは、応募数や作業量だけを増やさず、仮説を一つ変えて反応を見ます。見せる実績、狙う役割、報酬帯、チャネルのどれを変えたかを記録し、前回との差を確認します。複数の変数を同時に変えない方が、市場が何に反応したのかを判断しやすくなります。",
            "証拠化の最低単位は、課題、判断、行動、結果、学びの5点です。これを1枚のCase Cardにすると、職務経歴書の箇条書きより情報量が増え、面談でも具体例を短時間で説明できます。成果を誇張せず、確認可能な範囲だけを書くことが長期的な信頼につながります。",
        ]
        return f"{heading}について、{variants[idx % len(variants)]}"
    variants = [
        "Translate this point into a small evidence audit. Take the three most recent engagements and compare them using the same fields: problem, decision, stakeholders, constraints, result, and lesson. Include one case that did not go as planned. Repeated patterns across successful and difficult work are often more useful than a single impressive outcome because they show what you can reproduce in another environment.",
        "Prepare three questions before the next interview or client conversation: what outcome is expected, what decision rights come with the role, and how success will be measured. Those questions reveal whether the opportunity mainly buys execution capacity or gives you ownership that can build future career capital. Compensation should be compared together with the quality of the experience you will be allowed to accumulate.",
        "When market response is weak, change one variable at a time. Test a different proof point, role level, compensation band, or access channel and record what changed. If several variables move together, the feedback becomes difficult to interpret. A disciplined search process treats each application cycle as an experiment rather than simply increasing volume and hoping that probability will solve a positioning problem.",
        "Use a five-part minimum for portable evidence: problem, decision, action, result, and lesson. A one-page case card built around those fields is easier to reuse in a resume, portfolio, proposal, or interview than a long list of responsibilities. Keep claims within what can be defended, especially when confidentiality limits detail. Durable trust is more valuable than an exaggerated story that cannot survive follow-up questions.",
    ]
    return f"For {heading.lower()}, {variants[idx % len(variants)]}"


def expand(path: Path, article_id: str, locale: str) -> bool:
    if not path.is_file():
        return False
    topic = TOPICS[article_id]
    text = path.read_text(encoding="utf-8")
    changed = False
    for idx, pair in enumerate(topic["sections"]):
        marker = f'data-editorial-depth="{article_id}-{locale}-{idx}"'
        if marker in text:
            continue
        heading = pair[0] if locale == "ja" else pair[1]
        escaped_heading = html.escape(heading)
        pattern = re.compile(rf"(<h2>{re.escape(escaped_heading)}</h2>\s*<p>.*?</p>\s*<p>.*?</p>)", re.DOTALL)
        extra = html.escape(depth_text(locale, heading, idx))
        replacement = rf'\1\n<p {marker}>{extra}</p>'
        text, n = pattern.subn(replacement, text, count=1)
        changed = changed or bool(n)
    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def main() -> int:
    changed = 0
    for article_id in TOPICS:
        for locale in ("ja", "en"):
            if expand(ROOT / locale / "articles" / f"{article_id}.html", article_id, locale):
                changed += 1
    print(f"Expanded {changed} generated locale page(s) with section-specific depth notes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
