# Deterministic editorial release builder

`scripts/build_editorial_release.py` turns one approved private canonical
Markdown pair into the public derived artifacts required for a release:

- Japanese and English article pages;
- the Japanese homepage card;
- the two sitemap entries with alternate-language links;
- all four approved ACCESS TRADE partner contracts, disclosure, `nofollow`, and
  the required referrer policy.

The source repository is never copied into this public repository. Run the
builder in a disposable release worktree that has both repositories checked
out. For example:

```bash
python scripts/build_editorial_release.py \
  --source-root ../career-radar \
  --article-id career-agent-comparison-framework \
  --published-at 2026-08-26 \
  --write
python scripts/build_editorial_release.py \
  --source-root ../career-radar \
  --article-id career-agent-comparison-framework \
  --published-at 2026-08-26 \
  --check
python scripts/check_content_quality.py
python scripts/check_editorial_cadence.py
```

`--check` is the release-branch gate: it fails if tracked output diverges from
what the canonical Markdown pair would generate. It makes a manual HTML,
homepage, or sitemap edit observable before the public PR is created. The
public-main merge remains the only production publication gate.
