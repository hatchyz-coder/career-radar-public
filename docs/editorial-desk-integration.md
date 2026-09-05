# CareerRadar → HDN Editorial Desk integration

CareerRadar publishes a machine-readable source feed for the separate HDN Editorial Desk.

## Feed

Production URL:

`https://career.hdnjapan.com/editorial-desk-feed.json`

Repository fallback:

`https://raw.githubusercontent.com/hatchyz-coder/career-radar-public/main/editorial-desk-feed.json`

The feed contains CareerRadar social packs from the latest 14 calendar days. Each article includes finished copy for LinkedIn, Facebook, and X plus tracked CareerRadar article URLs.

## Editorial Desk sync contract

- Use `stable_id` as the immutable upsert key.
- Source sync may update copy and URLs for that item.
- The HDN Editorial Desk owns operator state.
- A source refresh must never reset `completed`, carry-over, postponed, scheduled, or locally edited state.
- `content_version` can be used to show that source copy changed without changing the task identity.
- Posting remains manual. The feed never authorizes or performs external SNS publication.
- `redistribution.day_3` and `redistribution.day_7` are review candidates only. They do not authorize automatic reposting.

## Daily operation

The existing HDN Editorial Desk morning sync can fetch this feed alongside HDN Articles. CareerRadar should appear as a separate source label so Hatch can review the day's copy and copy-paste it to the relevant SNS account.

Recommended display order for a new CareerRadar item:

1. LinkedIn (`P0`)
2. Facebook (`P1`)
3. X (`P2`)

The source intentionally carries no completion state. That state belongs to the Editorial Desk and must survive every sync.

## Producer pipeline

CareerRadar's editorial recovery workflow runs:

1. article publication/recovery
2. content polish/depth/discovery
3. analytics injection
4. LinkedIn/Facebook/X social pack generation
5. Editorial Desk feed export
6. traffic dashboard refresh
7. quality/cadence validation
8. race-safe persistence

This keeps the desk feed synchronized with the same final social copy that CareerRadar generates for each published article.
