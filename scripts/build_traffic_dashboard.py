#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOCIAL = ROOT / "data" / "social" / "latest.json"
CADENCE = ROOT / "data" / "editorial_cadence.json"
SEARCH = ROOT / "data" / "search_console_queries.json"
ACTIONS = ROOT / "data" / "traffic_action_queue.json"
OUT = ROOT / "traffic-dashboard.html"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def main() -> None:
    social = load(SOCIAL)
    cadence = load(CADENCE)
    search = load(SEARCH)
    actions = load(ACTIONS)

    article = social["article"]
    posts = social["posts"]
    urls = social["urls"]
    queued = sorted(
        [item for item in cadence.get("release_queue", []) if item.get("status") == "queued"],
        key=lambda item: item["due_at"],
    )
    next_item = queued[0] if queued else None
    rows = search.get("rows", [])
    warmup_days = search.get("warmup_days", 7)
    monitoring_started = search.get("monitoring_started_at", "-")
    actionable = int(actions.get("actionable_count", 0))

    if rows:
        search_status = f"Search Console実データ {len(rows)}行を取得済み"
        search_detail = f"Traffic Action Queue: {actionable}件"
    else:
        search_status = "Search Consoleウォームアップ中"
        search_detail = f"開始 {monitoring_started} / 最大{warmup_days}日間は0件でも正常"

    next_title = "予定なし"
    next_due = "-"
    if next_item:
        next_title = next_item["article_id"]
        next_due = next_item["due_at"]

    def post_card(label: str, key: str, priority: str) -> str:
        text = posts[key]
        return f'''<section class="post-card">
          <div class="post-head"><div><span class="priority">{esc(priority)}</span><h2>{esc(label)}</h2></div><button class="copy" data-copy="{esc(key)}">コピー</button></div>
          <textarea id="copy-{esc(key)}" readonly>{esc(text)}</textarea>
        </section>'''

    page = f'''<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <meta name="description" content="CareerRadar daily traffic operations dashboard">
  <title>CareerRadar Traffic Dashboard</title>
  <link rel="stylesheet" href="assets/site.css">
  <style>
    :root {{ color-scheme: light; }}
    body {{ background:#f6f7f9; }}
    .dash {{ max-width:1180px; margin:0 auto; padding:28px 20px 56px; }}
    .dash-header {{ display:flex; justify-content:space-between; gap:20px; align-items:flex-start; margin-bottom:22px; }}
    .dash-header h1 {{ margin:.15rem 0 .4rem; }}
    .muted {{ color:#667085; }}
    .status-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:18px 0 26px; }}
    .status-card, .post-card, .today-card {{ background:#fff; border:1px solid #e4e7ec; border-radius:16px; padding:18px; box-shadow:0 1px 2px rgba(16,24,40,.04); }}
    .status-card strong {{ display:block; font-size:1.02rem; margin-top:5px; overflow-wrap:anywhere; }}
    .kicker {{ font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; color:#667085; }}
    .today-card {{ margin-bottom:18px; }}
    .today-card h2 {{ margin:.25rem 0 .5rem; }}
    .today-actions {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:14px; }}
    .today-actions a {{ text-decoration:none; }}
    .post-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
    .post-card:first-child {{ grid-column:1 / -1; }}
    .post-head {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom:10px; }}
    .post-head h2 {{ margin:.25rem 0 0; }}
    .priority {{ display:inline-block; font-size:.74rem; font-weight:700; background:#101828; color:#fff; border-radius:999px; padding:4px 8px; }}
    textarea {{ width:100%; min-height:280px; border:1px solid #d0d5dd; border-radius:12px; padding:14px; box-sizing:border-box; resize:vertical; font:inherit; line-height:1.6; background:#fcfcfd; }}
    .post-card:first-child textarea {{ min-height:360px; }}
    button.copy {{ border:0; border-radius:10px; padding:10px 14px; font-weight:700; cursor:pointer; background:#111827; color:#fff; }}
    button.copy.done {{ background:#027a48; }}
    .footer-note {{ margin-top:18px; color:#667085; font-size:.9rem; }}
    @media (max-width:800px) {{
      .status-grid {{ grid-template-columns:1fr 1fr; }}
      .post-grid {{ grid-template-columns:1fr; }}
      .post-card:first-child {{ grid-column:auto; }}
      .dash-header {{ display:block; }}
    }}
    @media (max-width:520px) {{ .status-grid {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
<main class="dash">
  <header class="dash-header">
    <div>
      <div class="kicker">CareerRadar Operator</div>
      <h1>Traffic Dashboard</h1>
      <div class="muted">今日やることを1画面に集約。投稿文はそのままコピーできます。</div>
    </div>
    <a class="button secondary" href="index.html">CareerRadar本体を見る</a>
  </header>

  <section class="status-grid">
    <div class="status-card"><span class="kicker">Latest publication</span><strong>{esc(social['published_at'])}</strong><span class="muted">{esc(social['article_id'])}</span></div>
    <div class="status-card"><span class="kicker">Next release</span><strong>{esc(next_due)}</strong><span class="muted">{esc(next_title)}</span></div>
    <div class="status-card"><span class="kicker">Search Console</span><strong>{esc(search_status)}</strong><span class="muted">{esc(search_detail)}</span></div>
    <div class="status-card"><span class="kicker">Traffic actions</span><strong>{actionable}件</strong><span class="muted">Search Console由来の優先アクション</span></div>
  </section>

  <section class="today-card">
    <span class="priority">TODAY / 最優先</span>
    <h2>LinkedInへ1投稿</h2>
    <p><strong>{esc(article['ja_title'])}</strong></p>
    <p class="muted">まずLinkedIn。余力があればFacebook → Xの順で配信。各リンクはUTM付きです。</p>
    <div class="today-actions">
      <a class="button primary" href="{esc(urls['linkedin_ja'])}" target="_blank" rel="noopener">日本語記事を開く</a>
      <a class="button secondary" href="{esc(urls['linkedin_en'])}" target="_blank" rel="noopener">英語記事を開く</a>
    </div>
  </section>

  <section class="post-grid">
    {post_card('LinkedIn', 'linkedin', 'P0')}
    {post_card('Facebook', 'facebook', 'P1')}
    {post_card('X', 'x', 'P2')}
  </section>

  <p class="footer-note">このページは検索エンジン向けではなく運用確認用です。Search Consoleの検索語そのものは表示しません。</p>
</main>
<script>
  document.querySelectorAll('button.copy').forEach((button) => {{
    button.addEventListener('click', async () => {{
      const key = button.dataset.copy;
      const text = document.getElementById('copy-' + key).value;
      try {{
        await navigator.clipboard.writeText(text);
        button.textContent = 'コピー済み';
        button.classList.add('done');
        setTimeout(() => {{ button.textContent = 'コピー'; button.classList.remove('done'); }}, 1600);
      }} catch (e) {{
        const area = document.getElementById('copy-' + key);
        area.focus(); area.select(); document.execCommand('copy');
        button.textContent = 'コピー済み';
      }}
    }});
  }});
</script>
</body>
</html>
'''
    OUT.write_text(page, encoding="utf-8")
    print(f"Traffic dashboard ready: {OUT.name}; article={social['article_id']}; actionable={actionable}")


if __name__ == "__main__":
    main()
