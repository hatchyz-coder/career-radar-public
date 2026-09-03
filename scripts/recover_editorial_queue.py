#!/usr/bin/env python3
from __future__ import annotations

from datetime import date, datetime, timedelta
import html
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CADENCE = ROOT / "data" / "editorial_cadence.json"
INDEX = ROOT / "index.html"
SITEMAP = ROOT / "sitemap.xml"
SITE_URL = "https://career.hdnjapan.com"

PARTNERS = (
    ("jac_recruitment", "accesstrade_290807", "JAC Recruitment", "https://h.accesstrade.net/sp/cc?rk=01004u3700oxbh", "https://h.accesstrade.net/sp/rr?rk=01004u3700oxbh"),
    ("enworld", "accesstrade_961674", "エンワールド", "https://h.accesstrade.net/sp/cc?rk=0100o60a00oxbh", "https://h.accesstrade.net/sp/rr?rk=0100o60a00oxbh"),
    ("enworld_it_saas", "accesstrade_994914", "エンワールド（IT・SaaS向け）", "https://h.accesstrade.net/sp/cc?rk=0100ong600oxbh", "https://h.accesstrade.net/sp/rr?rk=0100ong600oxbh"),
    ("robert_walters", "accesstrade_987767", "ロバート・ウォルターズ", "https://h.accesstrade.net/sp/cc?rk=0100ojgk00oxbh", "https://h.accesstrade.net/sp/rr?rk=0100ojgk00oxbh"),
)

TOPICS = {
    "career-agent-comparison-framework": {
        "ja": "転職エージェントを『紹介件数』ではなく市場評価で比較する方法",
        "en": "How to Compare Career Agents by Market Signal, Not Introduction Volume",
        "ja_intro": "転職エージェントの価値を、送られてくる求人件数だけで測ると判断を誤ります。重要なのは、自分の経験がどの市場・役割・報酬帯で評価されているかを複数の経路から確かめることです。",
        "en_intro": "Counting introductions is a poor way to judge a career agency. The stronger question is how your experience is positioned across markets, role levels, and compensation bands, and whether that assessment is confirmed by more than one channel.",
        "sections": [("市場評価と求人在庫を分ける", "Separate market value from recruiter inventory"),("紹介ゼロを能力ゼロと解釈しない", "Do not equate zero introductions with zero capability"),("比較軸を5つに分解する", "Use five comparison dimensions"),("面談で評価根拠を聞く", "Ask for the basis of the evaluation"),("複数社の差分を記録する", "Record differences across agencies"),("ブランド依存を避ける", "Avoid pedigree-only signaling"),("見送り理由をデータ化する", "Turn rejection reasons into data"),("自力応募と併用する", "Run self-directed channels in parallel")],
    },
    "self-directed-job-search-system": {
        "ja": "人材紹介会社に依存しない、自力で仕事を取るキャリア探索システム",
        "en": "A Self-Directed Job Search System That Does Not Depend on Recruiters",
        "ja_intro": "紹介会社は有力なチャネルの一つですが、キャリアの入口を一社に握らせる必要はありません。直接応募、LinkedIn、知人紹介、専門コミュニティ、業務委託プラットフォームを組み合わせ、市場への接点を自分で増やします。",
        "en_intro": "Recruiters can be useful, but they should not control the entire entry point to your market. Direct applications, LinkedIn, referrals, specialist communities, and contract platforms can be combined into a repeatable search system.",
        "sections": [("探索チャネルを分散する", "Diversify search channels"),("応募ではなく仮説を管理する", "Manage hypotheses, not just applications"),("職務経歴書を役割別に変える", "Tailor evidence to the target role"),("実績をCase Card化する", "Turn experience into case cards"),("LinkedInを公開ポートフォリオにする", "Use LinkedIn as a public portfolio"),("週次で市場反応を測る", "Measure market response weekly"),("断られ方をデータ化する", "Turn rejection patterns into data"),("90日で探索戦略を更新する", "Reset the strategy every 90 days")],
    },
    "decision-rights-career-capital": {
        "ja": "年収を上げる人が積んでいる『意思決定権』というCareer Capital",
        "en": "Decision Rights as Career Capital: Why Ownership Raises Market Value",
        "ja_intro": "高い報酬につながる経験は、作業量の多さだけでは説明できません。何を決め、何に責任を持ち、どの不確実性を引き受けたか。意思決定権は経験を市場価値へ変換する重要なCareer Capitalです。",
        "en_intro": "High compensation is not explained by workload alone. What you were allowed to decide, what you were accountable for, and which uncertainties you owned often matter more than the number of tasks completed.",
        "sections": [("作業と意思決定を分ける", "Separate execution from decision ownership"),("予算・人・優先順位の権限を見る", "Map budget, people, and prioritization rights"),("失敗時の責任範囲を確認する", "Identify accountability when things fail"),("曖昧な状況での判断を残す", "Document decisions under ambiguity"),("経営層との接点を証拠化する", "Translate executive exposure into evidence"),("PM経験を年数ではなく判断で語る", "Describe PM work through decisions, not years"),("AI時代に残る価値を見る", "Focus on value that survives automation"),("次の職場では権限を条件にする", "Negotiate decision scope in the next role")],
    },
    "operations-improvement-case-study": {
        "ja": "業務改善を高単価案件につなげるCase Studyの作り方",
        "en": "How to Turn Operations Improvement Work into a High-Value Case Study",
        "ja_intro": "業務改善は、社内では評価されても外部市場では伝わりにくい経験です。『効率化しました』では弱く、何が詰まり、どう測り、何を変え、どの成果を出したかまで構造化して初めて持ち運べる実績になります。",
        "en_intro": "Operations improvement is often valuable inside a company but difficult to sell outside it. A portable case study needs the bottleneck, evidence, intervention, governance, stakeholder work, and measurable result.",
        "sections": [("改善前の構造を描く", "Describe the before-state"),("症状と原因を分ける", "Separate symptoms from causes"),("数字がない場合も測る", "Measure even when data is incomplete"),("関係者調整を成果として残す", "Capture stakeholder alignment"),("ツール導入を成果と混同しない", "Do not confuse tool implementation with improvement"),("リスクと制約を書く", "State risks and constraints"),("再現可能な方法論にする", "Turn work into a repeatable method"),("3分で話せるCaseにする", "Make the case explainable in three minutes")],
    },
    "freelance-to-employment-return-path": {
        "ja": "フリーランスから会社員へ戻れる人が先に作っている『戻り道』",
        "en": "Designing a Return Path from Freelance Work to Employment",
        "ja_intro": "独立は片道切符ではありません。問題は戻ることではなく、戻りたい時に選択肢が残っているかです。フリーランス期間を空白ではなく、成果・責任・顧客価値として説明できる設計が必要です。",
        "en_intro": "Freelancing does not have to be a one-way move. The real risk is discovering later that you failed to preserve options. Independent work should remain legible as outcomes, ownership, and client value rather than as a career gap.",
        "sections": [("独立前に撤退条件を決める", "Set exit conditions before going independent"),("顧客集中リスクを管理する", "Control client concentration"),("案件単価と年収を同一視しない", "Do not equate project rate with salary"),("会社員に伝わる実績形式を保つ", "Keep employment-legible evidence"),("肩書きより責任範囲を残す", "Preserve scope of responsibility"),("学習と営業を止めない", "Keep learning and business development active"),("再就職のタイミングを数値化する", "Use quantitative re-entry triggers"),("選択肢を持ったまま独立する", "Make independence increase optionality")],
    },
    "consulting-market-signal-matrix": {"ja":"コンサル案件で市場評価を見誤らないSignal Matrix","en":"A Signal Matrix for Reading Your Consulting Market Value","ja_intro":"コンサル案件では肩書きより、何を任せられると市場が判断しているかを分解する必要があります。","en_intro":"Consulting market value is easier to read when you separate the signals that buyers actually use to reduce hiring risk.","sections":[("案件化する経験を分ける","Separate experiences that convert into engagements"),("成果と役割を分ける","Separate outcome from role"),("業界知識の深さを見る","Measure domain depth"),("推進力を証拠化する","Evidence execution leadership"),("経営層対応を残す","Capture executive communication"),("曖昧さへの耐性を見る","Show ambiguity tolerance"),("報酬帯別に期待値を知る","Map expectations by rate band"),("市場反応で更新する","Update the matrix from market feedback")]},
    "portfolio-evidence-scorecard": {"ja":"職務経歴書より強いPortfolio Evidence Scorecardの作り方","en":"Build a Portfolio Evidence Scorecard Stronger Than a Resume","ja_intro":"経験を並べるだけでは、採用側は再現性を判断できません。証拠の強さを採点できる形にします。","en_intro":"A list of responsibilities is not enough for a buyer to judge repeatability. A scorecard makes the strength of your evidence visible.","sections":[("成果の客観性を見る","Measure outcome objectivity"),("意思決定を記録する","Record decision ownership"),("第三者証明を増やす","Add third-party validation"),("成果物を残す","Preserve artifacts"),("数字の質を確認する","Assess metric quality"),("守秘義務と両立する","Work within confidentiality"),("役割別に並び替える","Reorder evidence by target role"),("四半期ごとに更新する","Refresh the scorecard quarterly")]},
    "ai-assisted-career-research": {"ja":"AIを使って転職市場を調べるときに外してはいけない検証手順","en":"A Verification Workflow for AI-Assisted Career Market Research","ja_intro":"AIは市場調査を速くしますが、求人の鮮度や報酬の根拠まで保証してくれるわけではありません。","en_intro":"AI can accelerate career research, but it does not guarantee freshness, coverage, or the validity of compensation claims.","sections":[("一次情報を起点にする","Start from primary sources"),("求人サンプル数を記録する","Record sample size"),("観測と解釈を分ける","Separate observation from interpretation"),("古い情報を除く","Remove stale evidence"),("報酬を条件付きで読む","Read compensation conditionally"),("複数市場を比較する","Compare multiple markets"),("AIの要約を検証する","Verify AI summaries"),("意思決定ログを残す","Keep a decision log")]},
    "high-value-pmo-deliverables": {"ja":"高単価PMOで評価される成果物と評価されない成果物","en":"PMO Deliverables That Signal High Value—and Those That Do Not","ja_intro":"PMOの価値は議事録や進捗表の量ではなく、意思決定と問題解決をどれだけ前へ進めたかで決まります。","en_intro":"PMO value is not the volume of minutes and trackers. It is the degree to which governance artifacts accelerate decisions and problem resolution.","sections":[("進捗表を意思決定につなげる","Connect status reporting to decisions"),("課題管理にオーナーを置く","Put owners on issues"),("リスクを早期に見せる","Expose risk early"),("会議体を減らす","Reduce unnecessary governance"),("経営報告を短くする","Make executive reporting concise"),("成果物の利用者を決める","Define the user of each artifact"),("エスカレーション基準を作る","Create escalation thresholds"),("PMOの成果を数字で残す","Quantify PMO outcomes")]},
    "salary-vs-career-capital-tradeoff": {"ja":"年収アップとCareer Capital、どちらを優先すべきか","en":"Salary Increase vs Career Capital: How to Evaluate the Trade-off","ja_intro":"次の仕事を年収だけで選ぶと、数年後の選択肢を減らすことがあります。報酬と将来の市場価値を同時に評価します。","en_intro":"Choosing the next role on salary alone can reduce future options. Compensation and portable career capital should be evaluated together.","sections":[("現在の報酬差を計算する","Calculate the immediate compensation gap"),("意思決定権を評価する","Value decision rights"),("希少経験を見る","Identify scarce experience"),("市場横断性を見る","Measure portability across markets"),("学習速度を見る","Assess learning velocity"),("ブランドの価値を分解する","Unbundle employer brand value"),("3年後の選択肢を置く","Model three-year options"),("撤退基準を決める","Set exit criteria")]},
    "direct-client-acquisition-playbook": {"ja":"人材紹介会社を介さず直接案件を取るための実績設計","en":"An Evidence Playbook for Winning Direct Client Work","ja_intro":"直接案件では、仲介会社が代わりに作ってくれる信頼を自分で設計する必要があります。","en_intro":"Direct client work requires you to build the trust layer that an intermediary would otherwise provide.","sections":[("専門領域を狭く言う","Define a narrow problem space"),("Case Cardを公開する","Publish case cards"),("初回相談の型を作る","Structure the first consultation"),("課題を診断する","Diagnose before proposing"),("小さく受注する","Start with a small engagement"),("成果を証拠化する","Convert outcomes into proof"),("紹介が生まれる設計にする","Design for referrals"),("単価を段階的に上げる","Raise rates in stages")]},
    "midcareer-skill-obsolescence-audit": {"ja":"40代から始めるスキル陳腐化Audit","en":"A Mid-Career Skill Obsolescence Audit","ja_intro":"経験年数が増えるほど、強みと古くなった能力を分けて棚卸しする必要があります。","en_intro":"As experience accumulates, professionals need to distinguish durable strengths from skills that are becoming obsolete.","sections":[("作業スキルと判断スキルを分ける","Separate execution skills from judgment"),("市場需要を確認する","Check current market demand"),("AI代替リスクを見る","Assess AI exposure"),("業界固有知識を測る","Measure domain depth"),("学習コストを見積もる","Estimate reskilling cost"),("実務で補う","Use work to close gaps"),("証拠化できる学習を選ぶ","Choose learning that produces evidence"),("半年ごとに再監査する","Repeat the audit every six months")]},
    "project-rate-risk-adjustment": {"ja":"月100万円案件を年収1000万円と考えてはいけない理由","en":"Why a ¥1M Monthly Project Is Not the Same as a ¥10M Salary","ja_intro":"業務委託単価と会社員年収は構造が違います。稼働率、営業、空白期間、保険・税、集中リスクを含めて比較します。","en_intro":"Contract rates and employment salaries have different economics. Utilization, sales time, gaps, benefits, tax structure, and concentration risk all matter.","sections":[("稼働率を入れる","Model utilization"),("営業時間をコスト化する","Price business-development time"),("空白期間を置く","Include bench periods"),("福利厚生を換算する","Value benefits"),("入金サイトを見る","Model payment timing"),("顧客集中を測る","Measure client concentration"),("再契約確率を置く","Estimate renewal probability"),("撤退ラインを決める","Set a walk-away threshold")]},
    "executive-communication-career-signal": {"ja":"経営層への報告経験をCareer Capitalに変える方法","en":"Turn Executive Communication into Portable Career Capital","ja_intro":"経営層への報告は、資料作成ではなく、複雑な状況を意思決定可能な形に圧縮する仕事です。","en_intro":"Executive communication is not slide production. It is the work of compressing complexity into decision-ready information.","sections":[("論点を一文にする","State the issue in one sentence"),("選択肢を並べる","Frame alternatives"),("リスクを比較可能にする","Make risks comparable"),("推奨案を明確にする","Make the recommendation explicit"),("数字の前提を書く","State metric assumptions"),("反対意見を先に扱う","Address counterarguments early"),("決定事項を追跡する","Track decisions"),("実績として証拠化する","Convert communication into evidence")]},
    "career-optionality-portfolio": {"ja":"転職・副業・業務委託を同時に持つCareer Optionalityの作り方","en":"Build Career Optionality Across Employment, Side Work, and Contracting","ja_intro":"キャリアの強さは一つの肩書きではなく、複数の収入・経験・接点へ移れる選択肢の数でも決まります。","en_intro":"Career strength is partly the number of credible options you can move between—not just the title you hold today.","sections":[("収入源を分ける","Diversify income sources"),("実績の用途を増やす","Make evidence reusable"),("ネットワークを分散する","Diversify network access"),("本業と副業の競合を避ける","Avoid conflicts between roles"),("時間の上限を決める","Set time limits"),("学習を案件に接続する","Connect learning to paid work"),("撤退可能性を保つ","Preserve reversibility"),("年1回ポートフォリオを組み替える","Rebalance the portfolio annually")]},
}

PLANNED = [
    "consulting-market-signal-matrix",
    "portfolio-evidence-scorecard",
    "ai-assisted-career-research",
    "high-value-pmo-deliverables",
    "salary-vs-career-capital-tradeoff",
    "direct-client-acquisition-playbook",
    "midcareer-skill-obsolescence-audit",
    "project-rate-risk-adjustment",
    "executive-communication-career-signal",
    "career-optionality-portfolio",
]

JA_P1 = "この論点で最初に必要なのは、肩書きや自己評価ではなく、観測できる事実を分解することです。担当した仕事、判断した内容、関係者、制約、結果を並べると、経験のどこに市場価値があるかが見えてきます。『幅広く対応した』『頑張った』だけでは、外部の採用担当や発注者は再現性を判断できません。"
JA_P2 = "実務では証拠を一つにしないことが有効です。職務経歴書の一文、面談で話す具体例、第三者が確認できる成果物、数字や期間を同じ事実に結び付けます。守秘義務がある場合は固有名詞や機密数値を伏せ、課題の構造、自分の判断、トレードオフ、結果を中心に表現すれば、機密を守りながら実績を伝えられます。"
JA_P3 = "市場の反応は、能力だけでなく、求人在庫、タイミング、顧客事情、営業担当の得意領域、勤務地、契約形態にも左右されます。一つのチャネルの反応を自分の総合的な市場価値と混同せず、複数の経路で仮説を検証することが重要です。"
EN_P1 = "Start by separating observable facts from labels and self-assessment. List what you owned, what decisions you made, which stakeholders were involved, what constraints existed, and what changed. External buyers of talent cannot price vague statements such as 'supported the project' or 'handled a wide range of work.' They need evidence that helps them predict what you can repeat in a new environment."
EN_P2 = "Build more than one proof point around the same underlying fact. Connect a resume bullet, an interview story, a portfolio artifact, and a measurable boundary such as time, scale, or scope. Where confidentiality applies, remove names and sensitive figures but preserve the structure of the problem, the trade-off, the decision you owned, and the result. This makes the evidence consistent across recruiters, hiring managers, and clients."
EN_P3 = "Market response is shaped by capability, but also by inventory, timing, client preferences, geography, contract structure, and channel incentives. A weak response in one channel should trigger another test, not an immediate conclusion about your total market value. Use multiple channels and record the pattern of feedback."


def partner_block(locale: str, article_id: str) -> str:
    is_ja = locale == "ja"
    heading = "人材紹介サービスの選択肢を複数社で確認する" if is_ja else "Compare more than one career-support option"
    intro = "求人・支援対象・得意領域は各社で異なります。1社の回答だけを市場評価と考えず、現在の経験と希望に合う選択肢を比較してください。" if is_ja else "Coverage, role focus, and fit differ by provider. Compare options instead of treating one response as the whole market."
    disclosure = "※アフィリエイト広告です。登録前に各社の対象条件と最新情報をご確認ください。" if is_ja else "Advertisement / affiliate links. Confirm each provider's current eligibility and terms before registering."
    action = "選択肢を確認する" if is_ja else "Review this option"
    options = "".join(f'<section class="partner-option" data-partner-id="{pid}" data-offer-id="{offer}"><h3>{html.escape(name)}</h3><p class="partner-cta"><a href="{dest}" rel="nofollow" referrerpolicy="no-referrer-when-downgrade">{html.escape(name)}: {action}<img src="{track}" width="1" height="1" border="0" alt=""></a></p></section>' for pid, offer, name, dest, track in PARTNERS)
    return f'<aside class="partner-action partner-comparison" data-placement="{article_id}_{locale}_market_comparison"><div class="partner-label">Advertisement</div><h2>{heading}</h2><p>{intro}</p><div class="partner-options">{options}</div><p class="small">{disclosure}</p></aside>'


def body_html(topic: dict, locale: str) -> str:
    intro = topic[f"{locale}_intro"]
    parts = [f"<p>{html.escape(intro)}</p>"]
    for ja, en in topic["sections"]:
        heading = ja if locale == "ja" else en
        if locale == "ja":
            p1 = f"{heading}。{JA_P1}"
            p2 = f"{JA_P2} {JA_P3}"
        else:
            p1 = f"{heading}. {EN_P1}"
            p2 = f"{EN_P2} {EN_P3}"
        parts.extend([f"<h2>{html.escape(heading)}</h2>", f"<p>{html.escape(p1)}</p>", f"<p>{html.escape(p2)}</p>"])
    if locale == "ja":
        parts.extend([
            "<h2>根拠の扱い方</h2>",
            "<p>CareerRadarでは、公開資料が示す事実と、そこから導く解釈を分けます。World Economic ForumのFuture of Jobs Report 2025は、分析的思考、AI・ビッグデータ、技術リテラシーに加え、リーダーシップや柔軟性など人間側の能力も重要だと整理しています。OECD Employment Outlook 2025も、中高年を含む労働移動、キャリアガイダンス、学び直しの重要性を論じています。</p>",
            "<p>PMIのProject Management Salary Survey 14th Editionに見られる資格と報酬の関連は、因果関係の証明ではありません。またUpworkの調査は米国の知識労働者を中心とするプラットフォーム系調査です。CareerRadarでは、こうした数字を個人の年収保証として使わず、方向性を考える背景情報として扱います。</p>",
            "<h2>CareerRadarの実践チェック</h2>",
            "<p>次の応募や面談の前に、①市場価値と求人在庫を分けているか、②成果・判断・複雑性・影響・再現性を説明できるか、③一つのチャネルだけで結論を出していないか、④見送り理由を記録しているか、⑤30日から90日で戦略を更新する仕組みがあるかを確認してください。</p>",
            "<p>目的は、紹介会社や肩書きに選んでもらうことではありません。自分のCareer Capitalを市場が理解できる形に変換し、複数の経路から選択肢を作れる状態を増やすことです。</p>",
        ])
    else:
        parts.extend([
            "<h2>Evidence and interpretation</h2>",
            "<p>CareerRadar separates source-supported facts from interpretation. The World Economic Forum's Future of Jobs Report 2025 emphasizes analytical thinking and growing technology skills while also highlighting resilience, leadership, and social influence. The OECD Employment Outlook 2025 discusses mobility, career guidance, and training as skill needs change. These sources provide context; they do not guarantee an individual compensation outcome.</p>",
            "<p>PMI salary-survey findings should be read as associations rather than proof that a credential causes higher pay. Upwork research is useful as directional evidence about U.S. skilled knowledge work, but it is platform-sponsored and U.S.-specific. CareerRadar uses such evidence to inform hypotheses, then expects the reader to test those hypotheses against current target roles and markets.</p>",
            "<h2>CareerRadar action check</h2>",
            "<p>Before the next application or interview, ask whether you are separating market value from a particular platform's inventory, whether you can explain outcomes and decisions, whether you are testing more than one channel, whether rejection reasons are being recorded, and whether you have a 30- to 90-day review point.</p>",
            "<p>The objective is not to be selected by one recruiter or rely on one employer brand. The objective is to make your career capital legible enough that multiple routes can create real options.</p>",
        ])
    return "\n".join(parts)


def page(article_id: str, locale: str, published_at: str) -> str:
    topic = TOPICS[article_id]
    title = topic[locale]
    peer = "en" if locale == "ja" else "ja"
    peer_label = "Read in English" if locale == "ja" else "日本語で読む"
    desc = topic[f"{locale}_intro"][:160]
    return f'''<!doctype html>
<html lang="{locale}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="{html.escape(desc, quote=True)}">
  <title>{html.escape(title)} | CareerRadar</title>
  <link rel="canonical" href="{SITE_URL}/{locale}/articles/{article_id}.html">
  <link rel="alternate" hreflang="ja" href="{SITE_URL}/ja/articles/{article_id}.html">
  <link rel="alternate" hreflang="en" href="{SITE_URL}/en/articles/{article_id}.html">
  <link rel="alternate" hreflang="x-default" href="{SITE_URL}/ja/articles/{article_id}.html">
  <link rel="stylesheet" href="../../assets/site.css">
</head>
<body>
<header class="site-header"><nav class="nav"><a class="brand" href="../../index.html">CareerRadar</a><div class="nav-links"><a href="../../review.html">Career Review</a><a href="../../index.html#insights">Insights</a><a href="{SITE_URL}/{peer}/articles/{article_id}.html">{peer_label}</a></div></nav></header>
<main><article class="article"><div class="eyebrow">Career Intelligence / {locale.upper()}</div><h1>{html.escape(title)}</h1><p class="article-meta">CareerRadar Editorial / {published_at.replace('-', '.')}</p>
{body_html(topic, locale)}
{partner_block(locale, article_id)}
<div class="actions"><a class="button primary" href="../../review.html">Career Review</a><a class="button secondary" href="{SITE_URL}/{peer}/articles/{article_id}.html">{peer_label}</a></div></article></main>
<footer class="footer"><div class="footer-inner"><div><strong>CareerRadar</strong><div class="small">Operated by HDN Co., Ltd.</div></div><div class="footer-links"><a href="../../privacy.html">Privacy</a><a href="../../terms.html">Terms</a><a href="../../disclosure.html">広告・アフィリエイト</a><a href="../../operator.html">運営者情報</a><a href="../../contact.html">お問い合わせ</a></div></div></footer>
</body></html>\n'''


def add_card(index: str, article_id: str) -> str:
    href = f"ja/articles/{article_id}.html"
    if f'href="{href}"' in index:
        return index
    topic = TOPICS[article_id]
    marker = '<section class="section" id="insights">'
    section = index.find(marker)
    grid = index.find('<div class="grid">', section)
    if section < 0 or grid < 0:
        raise ValueError("Homepage insights grid missing")
    insert_at = grid + len('<div class="grid">')
    summary = html.escape(topic['ja_intro'][:180])
    card = f'<a class="card" href="{href}"><span class="tag">New / JP + EN</span><h3>{html.escape(topic["ja"])}</h3><p>{summary}</p></a>'
    return index[:insert_at] + card + index[insert_at:]


def update_sitemap(xml: str, article_id: str, published_at: str) -> str:
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    xhtml = "http://www.w3.org/1999/xhtml"
    ET.register_namespace("", ns)
    ET.register_namespace("xhtml", xhtml)
    root = ET.fromstring(xml)
    existing = {n.find(f"{{{ns}}}loc").text for n in root if n.find(f"{{{ns}}}loc") is not None}
    for locale in ("ja", "en"):
        url = f"{SITE_URL}/{locale}/articles/{article_id}.html"
        if url in existing:
            continue
        node = ET.SubElement(root, f"{{{ns}}}url")
        ET.SubElement(node, f"{{{ns}}}loc").text = url
        ET.SubElement(node, f"{{{ns}}}lastmod").text = published_at
        for alt in ("ja", "en"):
            ET.SubElement(node, f"{{{xhtml}}}link", {"rel":"alternate","hreflang":alt,"href":f"{SITE_URL}/{alt}/articles/{article_id}.html"})
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def next_business_day(value: date) -> date:
    value += timedelta(days=1)
    while value.weekday() >= 5:
        value += timedelta(days=1)
    return value


def replenish(payload: dict, today: date) -> None:
    queue = payload.setdefault("release_queue", [])
    queued = [i for i in queue if i.get("status") == "queued"]
    known = {i["article_id"] for i in queue}
    cursor = max([today] + [date.fromisoformat(i["due_at"]) for i in queued])
    for article_id in PLANNED:
        if len([i for i in queue if i.get("status") == "queued"]) >= payload["target"]["publications_per_week"]:
            break
        if article_id in known:
            continue
        cursor = next_business_day(cursor)
        queue.append({"article_id": article_id, "due_at": cursor.isoformat(), "locales": ["ja", "en"], "status": "queued"})
        known.add(article_id)


def main() -> int:
    today = date.today()
    payload = json.loads(CADENCE.read_text(encoding="utf-8"))
    index = INDEX.read_text(encoding="utf-8")
    index = index.replace('href="ja/articles/brandless-high-income-path.html"<span', 'href="ja/articles/brandless-high-income-path.html"><span')
    sitemap = SITEMAP.read_text(encoding="utf-8")
    published = []

    for item in payload.get("release_queue", []):
        if item.get("status") != "queued":
            continue
        if date.fromisoformat(item["due_at"]) > today:
            continue
        article_id = item["article_id"]
        if article_id not in TOPICS:
            print(f"No deterministic topic definition for queued article: {article_id}", file=sys.stderr)
            return 1
        published_at = today.isoformat()
        for locale in item.get("locales", ["ja", "en"]):
            path = ROOT / locale / "articles" / f"{article_id}.html"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(page(article_id, locale, published_at), encoding="utf-8")
        index = add_card(index, article_id)
        sitemap = update_sitemap(sitemap, article_id, published_at)
        item["status"] = "published"
        item["published_at"] = published_at
        published.append(article_id)

    if published:
        payload["last_publication"] = {"article_id": published[-1], "published_at": today.isoformat(), "article_count": len(published), "locale_page_count": len(published) * 2}

    replenish(payload, today)
    INDEX.write_text(index, encoding="utf-8")
    SITEMAP.write_text(sitemap, encoding="utf-8")
    CADENCE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Editorial recovery complete. Published={len(published)}; queued={len([i for i in payload['release_queue'] if i.get('status') == 'queued'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
