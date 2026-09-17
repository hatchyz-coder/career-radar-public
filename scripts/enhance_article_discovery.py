#!/usr/bin/env python3
from __future__ import annotations
import html, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
START="<!-- ARTICLE_SEQUENCE_START -->"
END="<!-- ARTICLE_SEQUENCE_END -->"

def clean(v): return html.unescape(re.sub(r"<[^>]+>","",v)).strip()
def meta(path):
    t=path.read_text(encoding="utf-8")
    m=re.search(r"<h1>(.*?)</h1>",t,re.S|re.I)
    d=re.search(r'<p class="article-meta">.*?/\s*([^<]+)</p>',t,re.S|re.I)
    title=clean(m.group(1)) if m else path.stem
    raw=clean(d.group(1)) if d else ""
    dm=re.search(r"(20\d{2})[.\-/](\d{2})(?:[.\-/](\d{2}))?",raw)
    date=f"{dm.group(1)}-{dm.group(2)}-{dm.group(3) or '01'}" if dm else "1970-01-01"
    return {"path":path,"id":path.stem,"title":title,"date":date}

def inject_sequence(locale, items):
    labels=("新しい記事","次の記事") if locale=="ja" else ("Newer article","Next article")
    for n,item in enumerate(items):
        text=item["path"].read_text(encoding="utf-8")
        newer=items[n-1] if n>0 else None
        older=items[n+1] if n+1<len(items) else None
        links=[]
        if newer: links.append(f'<a class="button secondary" href="{newer["id"]}.html">← {labels[0]}：{html.escape(newer["title"])}</a>')
        if older: links.append(f'<a class="button secondary" href="{older["id"]}.html">{labels[1]}：{html.escape(older["title"])} →</a>')
        block=f'{START}<nav class="article-sequence" aria-label="Article sequence"><div class="actions">{"".join(links)}</div></nav>{END}'
        pattern=re.escape(START)+r".*?"+re.escape(END)
        if re.search(pattern,text,re.S): text=re.sub(pattern,block,text,flags=re.S)
        else: text=text.replace("</article>",block+"</article>",1)
        item["path"].write_text(text,encoding="utf-8")

def enhance_index(locale, items):
    path=ROOT/locale/"articles"/"index.html"
    text=path.read_text(encoding="utf-8")
    ja=locale=="ja"
    latest_title="新着記事" if ja else "Latest articles"
    all_title="すべての記事（新しい順）" if ja else "All articles — newest first"
    intro="新しい記事から順番に読み進められます。" if ja else "Read CareerRadar from the newest article onward."
    def card(i):
        return f'<a class="card" href="{i["id"]}.html"><span class="tag">{i["date"]}</span><h3>{html.escape(i["title"])}</h3></a>'
    latest="".join(card(i) for i in items[:6])
    block=f'<section class="section article-latest"><h2>{latest_title}</h2><p class="section-intro">{intro}</p><div class="grid">{latest}</div></section><section class="section article-all-heading"><h2>{all_title}</h2></section>'
    marker='<main>'
    if "article-latest" not in text: text=text.replace(marker,marker+block,1)
    path.write_text(text,encoding="utf-8")

def main():
    count=0
    for locale in ("ja","en"):
        base=ROOT/locale/"articles"
        items=sorted((meta(p) for p in base.glob("*.html") if p.name!="index.html"),key=lambda x:(x["date"],x["id"]),reverse=True)
        if len(items)<5: raise SystemExit(f"Too few {locale} articles: {len(items)}")
        inject_sequence(locale,items); enhance_index(locale,items); count+=len(items)
    print(f"Article discovery enhanced: {count} article pages, 2 newest-first libraries")

if __name__=="__main__": main()
