#!/usr/bin/env python3
"""Build low-cost SEO topic hubs and related internal links for CareerRadar.

This bootstrap layer is intentionally deterministic. It improves crawl paths and topical
structure while Search Console is still warming up, without inventing keyword-volume data.
"""
from __future__ import annotations

from pathlib import Path
import html
import re

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://career.hdnjapan.com"
TOPICS_DIR = ROOT / "ja" / "topics"
INDEX = ROOT / "index.html"
SITEMAP = ROOT / "sitemap.xml"

HUBS = [
    {
        "slug": "40s-career-market-value",
        "title": "40代の転職で市場価値と年収を上げる方法",
        "description": "40代の転職で市場価値をどう見直し、年収と選択肢を増やすか。実績の証拠化、専門性、転職判断、キャリア資本をCareerRadarの記事から整理します。",
        "lead": "40代の転職では、経験年数そのものより『会社の外でも価値が伝わるか』が重要になります。このハブでは、年収だけでなく、次の10年の選択肢を増やすために、成果・専門性・意思決定・市場テストを一つの経路として整理します。",
        "points": ["過去の経験を市場で伝わる実績へ変える", "年収とCareer Capitalを分けて比較する", "転職・副業・業務委託を複数経路で市場テストする"],
        "articles": [
            ("../articles/midcareer-40s-career-capital.html", "40代から市場価値を上げるCareer Capitalの積み方", "経験を持ち運べる価値へ変換する基本設計。"),
            ("../articles/decision-rights-career-capital.html", "年収を上げる人が積んでいる『意思決定権』", "作業量ではなく、判断と責任の範囲を実績として残す。"),
            ("../articles/career-agent-comparison-framework.html", "転職エージェントを市場評価で比較する方法", "紹介件数ではなく、複数経路から自分の市場評価を測る。"),
            ("../articles/brandless-high-income-path.html", "大手ブランドに頼らず高単価へ到達するキャリア設計", "会社名ではなくEvidenceで信用を作るロードマップ。"),
        ],
    },
    {
        "slug": "pmo-high-rate-career",
        "title": "PMO・PMで高単価案件を取るための実績とスキル",
        "description": "PMO・PMの高単価案件で評価される実績、意思決定、Case Card、業務改善、コンサル案件へのSignal設計をCareerRadarで整理します。",
        "lead": "PMO・PMで単価を上げるには、進捗管理や会議運営の経験だけでは足りません。発注側が確認したいのは、複雑な状況で何を判断し、誰を動かし、どの変化を作ったかです。ここでは高単価につながるEvidenceの作り方をまとめます。",
        "points": ["タスクではなくBefore / Decision / Afterで実績を書く", "PMO経験を意思決定支援のSignalへ変える", "代表案件をCase Card化して面談・提案へ再利用する"],
        "articles": [
            ("../articles/high-value-pm-evidence.html", "高単価PM案件で評価される実績の作り方", "複雑性・判断・成果・回復経験をEvidenceにする。"),
            ("../articles/operations-improvement-case-study.html", "業務改善を高単価案件につなげるCase Studyの作り方", "改善経験を再現可能なケースとして市場へ見せる。"),
            ("../articles/operator-to-consulting-signal.html", "事業会社出身者がコンサル案件へ移るためのSignal設計", "社内実績を外部市場で通じる証拠へ翻訳する。"),
            ("../articles/decision-rights-career-capital.html", "意思決定権というCareer Capital", "責任範囲と判断の質を報酬につながる資産として捉える。"),
        ],
    },
    {
        "slug": "self-directed-job-search",
        "title": "転職エージェントに依存しない仕事の探し方",
        "description": "転職エージェントだけに依存せず、直接応募、LinkedIn、紹介、業務委託など複数経路で仕事を探し、市場価値を検証する方法を整理します。",
        "lead": "転職エージェントは便利な入口ですが、一社や一つの紹介経路にキャリアの選択肢を預ける必要はありません。CareerRadarでは、仕事探しを『応募活動』ではなく、市場との接点を複数持つ探索システムとして設計します。",
        "points": ["紹介会社を一つのチャネルとして位置づける", "直接応募・LinkedIn・人脈・案件市場を並行利用する", "反応データからプロフィールと実績の見せ方を改善する"],
        "articles": [
            ("../articles/self-directed-job-search-system.html", "人材紹介会社に依存しない、自力で仕事を取るキャリア探索システム", "複数チャネルで市場接点を増やす具体的な設計。"),
            ("../articles/career-agent-comparison-framework.html", "転職エージェントを市場評価で比較する方法", "エージェントごとの反応差を市場データとして使う。"),
            ("../articles/freelance-to-employment-return-path.html", "フリーランスから会社員へ戻れる人が先に作っている『戻り道』", "独立と雇用を片道にしない選択肢設計。"),
            ("../articles/brandless-high-income-path.html", "大手ブランドに頼らず高単価へ到達するキャリア設計", "第三者証明と公開実績で信頼を積み上げる。"),
        ],
    },
]

ARTICLE_TO_HUBS = {
    "midcareer-40s-career-capital.html": ["40s-career-market-value"],
    "decision-rights-career-capital.html": ["40s-career-market-value", "pmo-high-rate-career"],
    "career-agent-comparison-framework.html": ["40s-career-market-value", "self-directed-job-search"],
    "brandless-high-income-path.html": ["40s-career-market-value", "self-directed-job-search"],
    "high-value-pm-evidence.html": ["pmo-high-rate-career"],
    "operations-improvement-case-study.html": ["pmo-high-rate-career"],
    "operator-to-consulting-signal.html": ["pmo-high-rate-career"],
    "self-directed-job-search-system.html": ["self-directed-job-search"],
    "freelance-to-employment-return-path.html": ["self-directed-job-search"],
}

HUB_BY_SLUG = {h["slug"]: h for h in HUBS}
START = "<!-- SEARCH_HUBS_START -->"
END = "<!-- SEARCH_HUBS_END -->"
RELATED_START = "<!-- RELATED_TOPIC_HUBS_START -->"
RELATED_END = "<!-- RELATED_TOPIC_HUBS_END -->"


def render_hub(hub: dict) -> str:
    cards = "".join(
        f'<a class="card" href="{html.escape(url)}"><span class="tag">関連記事</span><h3>{html.escape(title)}</h3><p>{html.escape(desc)}</p></a>'
        for url, title, desc in hub["articles"]
    )
    points = "".join(f"<li>{html.escape(p)}</li>" for p in hub["points"])
    canonical = f'{SITE}/ja/topics/{hub["slug"]}.html'
    return (
        '<!doctype html><html lang="ja"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta name="description" content="{html.escape(hub["description"])}">'
        f'<title>{html.escape(hub["title"])} | CareerRadar</title>'
        f'<link rel="canonical" href="{canonical}"><link rel="stylesheet" href="../../assets/site.css">'
        '<script defer src="/assets/analytics.js"></script></head><body>'
        '<header class="site-header"><nav class="nav"><a class="brand" href="../../index.html">CareerRadar</a>'
        '<div class="nav-links"><a href="../../review.html">Career Review</a><a href="../../index.html#topics">Topics</a><a href="../../index.html#insights">Insights</a></div></nav></header>'
        '<main><article class="article"><div class="eyebrow">CareerRadar Search Guide / JP</div>'
        f'<h1>{html.escape(hub["title"])}</h1><p>{html.escape(hub["lead"])}</p>'
        '<h2>このテーマで最初に確認する3点</h2>'
        f'<ol>{points}</ol>'
        '<h2>深掘り記事</h2><div class="grid">'
        f'{cards}</div>'
        '<h2>CareerRadarでの使い方</h2><p>一つの記事だけで結論を出さず、複数の記事を横断して自分の実績・希望条件・市場からの反応を比較してください。転職、業務委託、副業、学習を別々に考えるのではなく、次の選択肢を増やす一つの経路として扱います。</p>'
        '<p><a class="button primary" href="../../review.html">Career Reviewを見る</a></p>'
        '</article></main><footer class="footer"><div class="footer-inner"><div><strong>CareerRadar</strong></div><div class="small">Operated by HDN Co., Ltd.</div></div></footer></body></html>'
    )


def build_hubs() -> None:
    TOPICS_DIR.mkdir(parents=True, exist_ok=True)
    for hub in HUBS:
        (TOPICS_DIR / f'{hub["slug"]}.html').write_text(render_hub(hub), encoding="utf-8")


def update_homepage() -> None:
    text = INDEX.read_text(encoding="utf-8")
    cards = "".join(
        f'<a class="card" href="ja/topics/{h["slug"]}.html"><span class="tag">Topic guide</span><h3>{html.escape(h["title"])}</h3><p>{html.escape(h["description"])}</p></a>'
        for h in HUBS
    )
    section = START + '<section class="section" id="topics"><div class="eyebrow">Search guides</div><h2>悩みから探すCareerRadar</h2><p class="section-intro">検索されやすい悩みを入口に、関連する深掘り記事をまとめています。</p><div class="grid">' + cards + '</div></section>' + END
    if START in text and END in text:
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), section, text, flags=re.S)
    else:
        marker = '<section class="section" id="insights">'
        if marker not in text:
            raise SystemExit("homepage insights marker missing")
        text = text.replace(marker, section + marker, 1)
    INDEX.write_text(text, encoding="utf-8")


def update_sitemap() -> None:
    text = SITEMAP.read_text(encoding="utf-8")
    for hub in HUBS:
        url = f'{SITE}/ja/topics/{hub["slug"]}.html'
        if url in text:
            continue
        block = f'  <url>\n    <loc>{url}</loc>\n  </url>\n'
        text = text.replace('</urlset>', block + '</urlset>')
    SITEMAP.write_text(text, encoding="utf-8")


def update_related_links() -> None:
    article_dir = ROOT / "ja" / "articles"
    for filename, slugs in ARTICLE_TO_HUBS.items():
        path = article_dir / filename
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        links = "".join(
            f'<li><a href="../topics/{slug}.html">{html.escape(HUB_BY_SLUG[slug]["title"])}</a></li>'
            for slug in slugs
        )
        block = RELATED_START + '<aside class="callout"><strong>関連テーマガイド</strong><ul>' + links + '</ul></aside>' + RELATED_END
        if RELATED_START in text and RELATED_END in text:
            text = re.sub(re.escape(RELATED_START) + r".*?" + re.escape(RELATED_END), block, text, flags=re.S)
        else:
            marker = '</article>'
            if marker not in text:
                raise SystemExit(f"article closing tag missing: {filename}")
            text = text.replace(marker, block + marker, 1)
        path.write_text(text, encoding="utf-8")


def validate() -> None:
    homepage = INDEX.read_text(encoding="utf-8")
    sitemap = SITEMAP.read_text(encoding="utf-8")
    for hub in HUBS:
        path = TOPICS_DIR / f'{hub["slug"]}.html'
        content = path.read_text(encoding="utf-8")
        canonical = f'{SITE}/ja/topics/{hub["slug"]}.html'
        if canonical not in content or canonical not in sitemap:
            raise SystemExit(f"hub canonical/sitemap validation failed: {hub['slug']}")
        if homepage.count(f'ja/topics/{hub["slug"]}.html') != 1:
            raise SystemExit(f"homepage hub link validation failed: {hub['slug']}")
        if content.count('../articles/') < 4:
            raise SystemExit(f"hub internal link floor failed: {hub['slug']}")
    print(f"Bootstrap search hubs healthy: {len(HUBS)} hubs, homepage discovery, sitemap and related-link graph ready.")


def main() -> None:
    build_hubs()
    update_homepage()
    update_sitemap()
    update_related_links()
    validate()


if __name__ == "__main__":
    main()
