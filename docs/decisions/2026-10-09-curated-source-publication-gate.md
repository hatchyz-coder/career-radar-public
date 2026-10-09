# Decision: fail closed when a due article has no curated bilingual source

- Date: 2026-10-09
- Status: proposed in Draft PR
- Scope: CareerRadar Public editorial publisher

## Context

The extension topic format permits a title, introduction, and headings without `section_copy`.
The renderer then substitutes generic paragraphs. Daily publication can therefore publish a
thin article from `main` while a richer article remains in an unmerged Draft PR. The
published commit also makes that content PR stale.

This happened for `ai-delegation-accountability` on 2026-10-09. Its queued definition on
`main` had no `section_copy`, while the curated copy was still under review.

## Decision

Before any file is rendered or cadence state is changed, the v2 publisher checks every
extension article that is both queued and due. Each section must have a matching
`section_copy` entry, and each entry must contain at least two non-empty Japanese and
English paragraphs. Otherwise the publisher exits with a `STOP` error.

Future queued articles are not rejected before their due date, so editorial work can remain
in progress. Published entries are ignored. Existing collision, duplicate, locale, and
all-articles-first preflight checks remain unchanged.

## Consequences

- Generic fallback text cannot be published for a due extension article.
- A missing curated source becomes a visible CI or scheduled-workflow failure instead of a
  silent public-content regression.
- Editors must merge reviewed source copy before the due date, or deliberately reschedule
  the queue through the existing review process.
- Rolling back is limited to reverting the gate commit; no generated pages, cadence records,
  deployments, or production settings are changed by this decision.
