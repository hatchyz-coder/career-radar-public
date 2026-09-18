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
if errors:
    raise SystemExit("\n".join(errors))
print("Article discovery validation passed")
