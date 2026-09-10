#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# CareerRadar is the product brand and remains in Latin letters.
# Common acronyms/proper nouns such as AI, PMO, DX, SaaS and LinkedIn also remain as-is.
REPLACEMENTS = (
    ("Career Intelligence", "キャリア分析"),
    ("Career intelligence", "キャリア分析"),
    ("Evidence-first career navigation", "根拠重視のキャリア設計"),
    ("Evidence-first", "根拠重視"),
    ("Career Navigation", "キャリアナビゲーション"),
    ("Career Review", "キャリアレビュー"),
    ("Career Gap", "キャリアギャップ"),
    ("Opportunity Path", "到達経路"),
    ("Next Action", "次の行動"),
    ("Career Capital", "キャリア資本"),
    ("Case Card", "実績カード"),
    ("Signal Matrix", "評価マトリクス"),
    ("Portfolio Evidence Scorecard", "実績ポートフォリオ評価表"),
    ("Search guides", "テーマ別ガイド"),
    ("Search Guide", "テーマ別ガイド"),
    ("Topic guide", "テーマ別ガイド"),
    ("Market test", "市場テスト"),
    ("Career paths", "キャリアの選択肢"),
    ("How it works", "使い方"),
    ("Method", "考え方"),
    ("New / JP + EN", "新着 / 日英"),
    (">Paths<", ">選択肢<"),
    (">Insights<", ">記事<"),
    (">High-class<", ">ハイクラス<"),
    (">Independent<", ">独立・業務委託<"),
    (">Portfolio<", ">ポートフォリオ<"),
    (">Consulting<", ">コンサル<"),
    (">Learning<", ">学習<"),
    (">Market<", ">市場<"),
)

# These are especially irritating when left as stand-alone English UI labels on Japanese pages.
# They are intentionally narrower than a generic English-word replacement so company names,
# technical acronyms and source titles are not damaged.
SECONDARY_REPLACEMENTS = (
    ("CareerRadar Editorial", "CareerRadar編集部"),
    ("CareerRadar Search Guide", "CareerRadarテーマ別ガイド"),
    ("CareerRadar action check", "CareerRadar実践チェック"),
    ("CareerRadar Action Check", "CareerRadar実践チェック"),
    ("Evidence and interpretation", "根拠と解釈"),
    ("Evidence", "実績・根拠"),
    ("Signal設計", "評価材料の設計"),
    ("Signal Matrix", "評価マトリクス"),
)


def japanese_pages() -> list[Path]:
    pages = []
    for path in ROOT.rglob("*.html"):
        if any(part in {".git"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        if '<html lang="ja"' in text or "<html lang='ja'" in text:
            pages.append(path)
    return sorted(pages)


def localize(text: str) -> str:
    updated = text
    for old, new in REPLACEMENTS + SECONDARY_REPLACEMENTS:
        updated = updated.replace(old, new)
    # Short English fragments that are safe only in Japanese prose/UI.
    updated = updated.replace("とのGap", "とのギャップ")
    updated = updated.replace("次のAction", "次の行動")
    updated = updated.replace("Gapを", "ギャップを")
    updated = updated.replace("Gapの", "ギャップの")
    updated = updated.replace("Gap、", "ギャップ、")
    updated = updated.replace("Case Study", "事例")
    return updated


def main() -> None:
    changed = 0
    for path in japanese_pages():
        original = path.read_text(encoding="utf-8")
        updated = localize(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    print(f"Japanese UI localization complete: changed_pages={changed}, checked_pages={len(japanese_pages())}")


if __name__ == "__main__":
    main()
