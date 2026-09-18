#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
errors=[]
for locale in ("ja","en"):
    idx=(ROOT/locale/"articles"/"index.html").read_text(encoding="utf-8")
    if "article-latest" not in idx: errors.append(f"{locale}: latest section missing")
    if "article-all-heading" not in idx: errors.append(f"{locale}: all-articles heading missing")
    pages=[p for p in (ROOT/locale/"articles").glob("*.html") if p.name!="index.html"]
    for p in pages:
        t=p.read_text(encoding="utf-8")
        if t.count("<!-- ARTICLE_SEQUENCE_START -->")!=1: errors.append(f"{p}: sequence navigation missing/duplicated")
home=(ROOT/"index.html").read_text(encoding="utf-8")
if home.count("<!-- HOME_DISCOVERY_START -->")!=1: errors.append("home: discovery section missing/duplicated")
for needle in ("新しい記事から読む","まず読んでほしいテーマ","新着記事をすべて見る"):
    if needle not in home: errors.append(f"home: missing {needle}")
if "よく読まれている" in home: errors.append("home: unverified popularity label must not be shown")

if errors:
    raise SystemExit("\n".join(errors))
print("Article discovery validation passed")
