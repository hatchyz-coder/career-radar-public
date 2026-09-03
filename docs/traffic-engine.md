# CareerRadar Traffic Engine

## Purpose

Turn real Google Search Console demand into a deterministic editorial decision queue instead of choosing topics by intuition alone.

Pipeline:

1. Fetch 28 days of final Search Console query/page data, with a 3-day data-lag buffer.
2. Validate freshness and row integrity.
3. Score each query/page pair from 0 to 100.
4. Classify the best next action.
5. Persist the top opportunities for editorial automation.
6. Open a GitHub incident automatically when intake becomes stale or invalid.

## Files

- `scripts/fetch_search_console.py` — optional API collector.
- `data/search_console_queries.json` — normalized Search Console intake.
- `scripts/score_search_demand.py` — deterministic opportunity scorer.
- `data/traffic_opportunities.json` — ranked output consumed by later editorial automation.
- `scripts/check_traffic_engine.py` — schema, freshness, duplicate and score validation.
- `scripts/test_traffic_engine.py` — regression tests for decision rules.
- `.github/workflows/traffic-engine.yml` — daily monitored workflow.

## Decision classes

- `ctr_fix`: Top-10 result whose CTR is materially below the expected CTR for its position. First action is title/meta improvement.
- `quick_win`: Position 4–20 with meaningful impressions. First action is strengthening the existing landing page and internal links.
- `content_gap`: Meaningful demand below position 20 that lands on a generic page. First action is a dedicated article.
- `defend`: High-impression position 1–3 query. First action is refresh and internal-link defense.
- `long_term`: Demand signal exists but ranking is still low. First action is cluster expansion or a deeper page.
- `observe`: Not enough evidence yet.

The scorer estimates missed clicks from a conservative position-based CTR curve, combines demand, current position, missed-click upside and action class, then ranks opportunities from 0–100.

## Monitoring

Monitoring started on 2026-09-03. Search Console is allowed a 7-day warmup because the property was just created. After warmup:

- no Search Console intake is a failure;
- intake older than 4 days is a failure;
- malformed, duplicate or impossible metrics are a failure;
- invalid or unsorted opportunity output is a failure.

Failure opens or updates:

`[Traffic Incident] CareerRadar search-demand pipeline unhealthy`

Recovery closes the incident automatically.

## Search Console API activation

The workflow can operate in warmup mode without credentials. For full daily automation, configure a dedicated Google service account with read-only Search Console access and add its JSON key as the GitHub Actions repository secret:

`GSC_SERVICE_ACCOUNT_JSON`

Required Google API scope is `webmasters.readonly`. The service-account email only needs Search Console access to `https://career.hdnjapan.com/`; it does not need write access to the site.

Once the secret exists, the same daily workflow automatically fetches Search Console data, scores it, validates it and commits refreshed traffic intelligence. No workflow edit is required.
