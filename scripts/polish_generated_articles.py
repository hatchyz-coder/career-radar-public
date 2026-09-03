#!/usr/bin/env python3
from __future__ import annotations

import html
from pathlib import Path
import re

from recover_editorial_queue import ROOT, TOPICS

JA_VARIANTS = [
    ("まず基準線を置きます。{heading}を考えるとき、現状・期待値・制約を分け、何が変われば前進とみなすかを先に決めます。評価基準が曖昧なままでは、結果が出ても説明できず、別の職場や案件へ持ち運べる実績になりません。",
     "次に証拠を残します。数字があるなら数字を使い、ない場合は対象人数、期間、部門数、関係者、システム数などで規模を示します。守秘義務がある案件では固有名詞を伏せても、課題の構造、自分の判断、トレードオフ、結果は十分に説明できます。"),
    ("{heading}では、一つのチャネルや一人の評価者の反応を結論にしないことが重要です。求人在庫、顧客事情、タイミング、勤務地、契約形態によって反応は変わるため、複数の経路で同じ仮説を試し、共通して出る反応だけを強いシグナルとして扱います。",
     "記録する項目は、応募先や案件名だけでは足りません。どの実績を前面に出したか、相手が何に反応したか、見送り理由は何だったか、報酬帯はどこだったかまで残すと、次の打ち手を感覚ではなくデータで決められます。"),
    ("{heading}を実績として語るなら、作業内容より意思決定を中心にします。何を選び、何を捨て、どのリスクを引き受け、誰と合意を作ったのかを示すと、単なる担当経験から『任せられる範囲』の証拠へ変わります。",
     "特に高単価領域では、正解を知っていたことより、情報が不十分な状態で判断し、必要な人を巻き込み、途中で前提が崩れたときに立て直した経験が重要です。結果だけでなく、判断の質と回復力まで残してください。"),
    ("{heading}は、数字の大小だけで評価しません。成果額、工数削減、リードタイムだけでなく、意思決定速度、エラー削減、関係者数、再発防止、引き継ぎ可能性など、仕事の質を示す指標も使えます。",
     "測定できない仕事を『評価不能』にしないことがポイントです。改善前と改善後の状態を文章で定義し、比較可能な代理指標を置けば、定量データが少ない案件でも十分にCase Studyとして成立します。"),
    ("{heading}では、関係者調整を補助作業として扱わないでください。利害の違う部門、経営層、現場、外部ベンダーの間で論点を揃え、決めるべきことを決めるのは、それ自体が高い市場価値を持つ仕事です。",
     "面談では『会議を運営した』ではなく、何が対立していたか、どの情報を揃えたか、誰が最終判断者だったか、決定後に何が進んだかまで話します。コミュニケーションを成果へ接続して説明することが重要です。"),
    ("{heading}を考えるときは、成功条件だけでなく失敗条件も置きます。予算、時間、人員、法規制、契約、依存先などの制約を明示すると、その環境でどこまで責任を負ったのかが分かり、実績の難易度を正しく伝えられます。",
     "さらに、問題が起きたときのエスカレーション基準や撤退条件を決めておくと、無理にやり切ることよりも、損失を限定しながら目的を守る能力を示せます。これはPM、PMO、コンサル、事業責任者で共通して評価される要素です。"),
    ("{heading}は、案件が終わった瞬間にCase Cardへ変換します。課題、仮説、自分の役割、意思決定、実行、成果、反対意見、学びを1枚にまとめれば、職務経歴書、面談、LinkedIn、提案資料へ再利用できます。",
     "後から思い出して書くより、終了直後に残した方が具体性が高く、数字や判断理由も失われません。Career Capitalは経験しただけでは資産にならず、外部から確認できる形に変換して初めて持ち運べるようになります。"),
    ("{heading}は、最終的に次の行動へ接続します。30日から90日の単位で、狙う役割、見せる実績、希望報酬、使うチャネルを見直し、市場から返ってきた反応で仮説を更新します。",
     "キャリア探索は一度正解を当てる作業ではありません。小さく試し、反応を取り、証拠を増やし、より良い選択肢へ移る反復プロセスです。評価が弱いときは応募数だけを増やさず、ポジショニングそのものを更新してください。"),
]

EN_VARIANTS = [
    ("Start by defining a baseline for {heading}. Separate the current state, the target state, and the constraints. Decide in advance what evidence would count as progress. Without a clear baseline, even a successful result is difficult to explain and almost impossible to transfer into another hiring process or client conversation.",
     "Then preserve the evidence. Use financial or operational metrics where they exist, and use scope measures such as duration, team size, departments, systems, stakeholder groups, or regulatory constraints where they do not. Confidentiality does not prevent a strong case study; remove sensitive names and figures while keeping the structure of the problem, your decision, the trade-off, and the outcome."),
    ("For {heading}, never let one channel or one evaluator define the whole market. Inventory, timing, geography, contract model, client preference, and recruiter specialization all affect the response. Test the same positioning through several routes and treat patterns that repeat across channels as stronger evidence than a single rejection or introduction.",
     "Track more than applications. Record which proof points you led with, what the other side reacted to, why an opportunity stopped, what compensation band was discussed, and what role level was considered. That turns career search from an emotional sequence into a data set that can improve the next decision."),
    ("When presenting {heading}, move from task descriptions to decision ownership. Explain what you chose, what you rejected, which risks you accepted, who had to be aligned, and what changed after the decision. This transforms experience from 'I was involved' into evidence of the scope that another organization can safely delegate to you.",
     "In higher-value work, the premium often comes from judgment under incomplete information. Show how you handled ambiguity, what assumptions you used, how you escalated uncertainty, and how you recovered when the original plan stopped working. Buyers of senior talent are often purchasing risk reduction as much as execution capacity."),
    ("Do not evaluate {heading} only through one headline metric. Revenue, cost, cycle time, and utilization are useful, but so are decision speed, error reduction, handoff quality, repeatability, stakeholder coverage, and reduction of operational risk. Choose measures that reflect the actual purpose of the work.",
     "If perfect data is unavailable, define the before-state and after-state carefully and use reasonable proxy measures. A case does not become invalid because the organization lacked mature analytics. What matters is whether the reader can understand the scale, the intervention, and why the observed change is relevant."),
    ("Stakeholder work is central to {heading}, not administrative overhead. Aligning executives, operating teams, vendors, and specialist functions around a decision can be the most valuable part of a transformation. Describe the disagreement, the information gap, the decision owner, and the mechanism that moved the group forward.",
     "In an interview, replace 'facilitated meetings' with a decision narrative. State which conflict or dependency existed, what you clarified, what decision was made, and what became possible afterward. Communication becomes marketable career capital when it is connected to organizational movement and measurable outcomes."),
    ("A credible explanation of {heading} includes failure conditions as well as success conditions. State the limits created by budget, time, staffing, regulation, contract structure, legacy systems, or external dependencies. Constraints help a buyer understand the difficulty of the work and the quality of the judgment involved.",
     "Also explain escalation thresholds and exit criteria. Senior operators are not valuable because they force every plan to completion; they are valuable because they know when to change course, when to escalate, and how to protect the objective while limiting downside. That is portable evidence for PM, PMO, consulting, and leadership roles."),
    ("Convert {heading} into a case card as soon as the engagement ends. Capture the problem, hypothesis, your role, key decisions, execution path, result, counterarguments, and lessons. A one-page case can later feed a resume, LinkedIn profile, interview story, proposal, or portfolio without rewriting the underlying evidence each time.",
     "Continuous evidence capture is stronger than reconstructing a career years later. Career capital becomes portable only after experience has been translated into a form another person can inspect. The habit of documenting cases therefore has direct value in both employment and independent markets."),
    ("Finally, connect {heading} to a review cycle. Every 30 to 90 days, revisit the target role, the proof you lead with, compensation expectations, and the channels you use. Use market response to update the hypothesis instead of simply increasing application volume.",
     "Career navigation is an iterative system, not a one-time prediction. Run small tests, collect feedback, strengthen evidence, and move toward better options. When response remains weak, change the positioning or the evidence architecture before concluding that the market has permanently rejected the underlying capability."),
]


def polish_page(path: Path, article_id: str, locale: str) -> bool:
    if not path.is_file():
        return False
    topic = TOPICS[article_id]
    text = path.read_text(encoding="utf-8")
    changed = False
    for idx, pair in enumerate(topic["sections"]):
        heading = pair[0] if locale == "ja" else pair[1]
        escaped_heading = html.escape(heading)
        pattern = re.compile(rf"<h2>{re.escape(escaped_heading)}</h2>\s*<p>.*?</p>\s*<p>.*?</p>", re.DOTALL)
        templates = JA_VARIANTS if locale == "ja" else EN_VARIANTS
        p1, p2 = templates[idx % len(templates)]
        replacement = f"<h2>{escaped_heading}</h2>\n<p>{html.escape(p1.format(heading=heading))}</p>\n<p>{html.escape(p2.format(heading=heading))}</p>"
        text, n = pattern.subn(replacement, text, count=1)
        changed = changed or bool(n)
    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def main() -> int:
    changed = 0
    for article_id in TOPICS:
        for locale in ("ja", "en"):
            path = ROOT / locale / "articles" / f"{article_id}.html"
            if polish_page(path, article_id, locale):
                changed += 1
    print(f"Polished {changed} generated locale page(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
