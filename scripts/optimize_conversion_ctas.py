#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MID_START = "<!-- CONVERSION_MID_START -->"
MID_END = "<!-- CONVERSION_MID_END -->"
END_START = "<!-- CONVERSION_END_START -->"
END_END = "<!-- CONVERSION_END_END -->"
AFFILIATE_START = "<!-- AFFILIATE_FUNNEL_START -->"


def locale_for(path: Path) -> str:
    parts = path.relative_to(ROOT).parts
    return "en" if parts and parts[0] == "en" else "ja"


def routes_for(path: Path) -> tuple[str, str]:
    rel = path.relative_to(ROOT)
    if rel.parts[0] in {"ja", "en"}:
        return "../../review.html", "../../articles/high-class-transition.html#agent-options"
    return "../review.html", "high-class-transition.html#agent-options"


def replace_marked(text: str, start: str, end: str, block: str) -> str:
    pattern = re.escape(start) + r".*?" + re.escape(end)
    if re.search(pattern, text, re.S):
        return re.sub(pattern, block, text, count=1, flags=re.S)
    return text


def mid_block(path: Path) -> str:
    locale = locale_for(path)
    review, _ = routes_for(path)
    source = path.stem
    if locale == "en":
        headline = "Turn the reading into a market-value check."
        body = "Organize your evidence, decision scope, and target conditions before deciding what to do next."
        label = "Open Career Review"
    else:
        headline = "記事を読むだけで終わらせず、自分の市場価値に置き換える。"
        body = "経験・実績・意思決定範囲・希望条件を整理し、次に検証すべきキャリア仮説を明確にできます。"
        label = "Career Reviewで整理する"
    return (
        f'{MID_START}<aside class="callout conversion-cta conversion-cta-mid" data-conversion-source="{source}">'
        f'<strong>{headline}</strong><p>{body}</p><div class="actions">'
        f'<a class="button primary" href="{review}" data-conversion-cta="career_review" data-conversion-placement="mid_article">{label}</a>'
        f'</div></aside>{MID_END}'
    )


def end_block(path: Path) -> str:
    locale = locale_for(path)
    review, gateway = routes_for(path)
    source = path.stem
    if locale == "en":
        headline = "Choose the next action instead of stopping at information."
        body = "Review your own evidence first. If a job move is relevant, compare more than one market channel rather than treating one provider as the market."
        review_label = "Open Career Review"
        gateway_label = "Compare career-support options"
    else:
        headline = "情報収集で終わらせず、次の行動を一つ決める。"
        body = "まず自分の実績と希望条件を整理する。転職を選択肢に入れる場合は、1社の反応だけで市場価値を決めず、複数の窓口を比較できます。"
        review_label = "Career Reviewを見る"
        gateway_label = "転職支援サービスを比較する"
    return (
        f'{END_START}<aside class="callout conversion-cta conversion-cta-end" data-conversion-source="{source}">'
        f'<strong>{headline}</strong><p>{body}</p><div class="actions">'
        f'<a class="button primary" href="{review}" data-conversion-cta="career_review" data-conversion-placement="article_end">{review_label}</a>'
        f'<a class="button secondary" href="{gateway}" data-affiliate-funnel-link="true" data-affiliate-funnel-source="conversion-end:{locale}:{source}" data-conversion-cta="market_compare" data-conversion-placement="article_end">{gateway_label}</a>'
        f'</div></aside>{END_END}'
    )


def insert_mid(text: str, block: str) -> str:
    updated = replace_marked(text, MID_START, MID_END, block)
    if MID_START in text:
        return updated
    positions = [m.start() for m in re.finditer(r"<h2\b", text, re.I)]
    if len(positions) >= 4:
        pos = positions[len(positions) // 2]
        return text[:pos] + block + text[pos:]
    paragraphs = [m.end() for m in re.finditer(r"</p>", text, re.I)]
    if len(paragraphs) >= 4:
        pos = paragraphs[len(paragraphs) // 2]
        return text[:pos] + block + text[pos:]
    return text


def insert_end(text: str, block: str) -> str:
    updated = replace_marked(text, END_START, END_END, block)
    if END_START in text:
        return updated
    if AFFILIATE_START in text:
        return text.replace(AFFILIATE_START, block + AFFILIATE_START, 1)
    if "</article>" in text:
        return text.replace("</article>", block + "</article>", 1)
    raise SystemExit("No article end anchor")


def editorial_articles() -> list[Path]:
    paths: list[Path] = []
    for locale in ("ja", "en"):
        paths.extend(p for p in sorted((ROOT / locale / "articles").glob("*.html")) if p.name != "index.html")
    return paths


def legacy_articles() -> list[Path]:
    return sorted((ROOT / "articles").glob("*.html"))


def optimize_article(path: Path, *, add_end: bool) -> None:
    text = path.read_text(encoding="utf-8")
    text = insert_mid(text, mid_block(path))
    if add_end:
        text = insert_end(text, end_block(path))
    path.write_text(text, encoding="utf-8")


def main() -> None:
    generated = editorial_articles()
    legacy = legacy_articles()
    for path in generated:
        # Generated articles already receive a dedicated affiliate route and Career Review action at the end.
        # Add a single mid-article conversion point rather than stacking another end block.
        optimize_article(path, add_end=False)
    for path in legacy:
        if path.name == "high-class-transition.html":
            # This page is the approved affiliate gateway itself; add only a Career Review mid-point.
            optimize_article(path, add_end=False)
        else:
            optimize_article(path, add_end=True)
    print(f"Conversion CTA optimization complete: generated={len(generated)}, legacy={len(legacy)}")


if __name__ == "__main__":
    main()
