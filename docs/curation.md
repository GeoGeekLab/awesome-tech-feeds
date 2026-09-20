# Curation contract

Awesome Tech Feeds curates sources, not individual articles and not popularity.

The registry separates three decisions:

1. **Source admission** — whether a source has durable technical value and fits registry scope.
2. **Collection membership** — why a source belongs in a specific editorial bundle.
3. **Operational health** — whether a feed endpoint is currently reachable and parseable.

These decisions must not be collapsed into one score.

## Source admission

A source should demonstrate recurring value across multiple publications. Reviewers should consider:

- originality and first-party evidence;
- practitioner or research depth;
- durability beyond a single news cycle;
- incremental coverage relative to existing sources;
- a stable public feed endpoint;
- fit with the controlled taxonomy.

Popularity, employer prestige, posting frequency, and temporary feed health are not admission criteria.

Every source now records this decision in `curation.rationale`, together with a schema-defined `admission_basis`, reviewer, and review window. The rationale is an auditable explanation, not a score.

## Source review lifecycle

A source review confirms that identity, scope, rationale, taxonomy, and provenance are still accurate. v2 source records contain `reviewed_at` and `review_after`. The next-review window must be between 30 and 366 days.

CI validates chronology but does not depend on the current date. Maintainers can query review work with:

```bash
techfeeds reviews --as-of 2026-12-19
techfeeds reviews --as-of 2026-12-01 --within-days 30
```

Reviewing a source does not require changing its feed URL or collection membership. Update only assertions that have actually changed.

## Collection policy

Collections may declare deterministic policy in their YAML record.

`max_sources` caps the size of a collection. This is especially important for starter collections where attention cost is part of the product contract.

`require_rationale` requires every selected source to have a matching `selection_rationale`. Rationales explain why that source is useful *in that collection* rather than assigning a global quality score.

`review_interval_days` communicates the intended editorial review cadence. It is documentation, not a wall-clock CI failure condition, so registry validation remains deterministic.

## Essential

`essential` is deliberately opinionated and small. It is capped at 20 sources and currently contains 18.

The goal is breadth with low redundancy: independent practitioners, production engineering, security, systems, AI research, and one focused technical community. A source can be excellent without belonging in `essential`.

When changing `essential`:

- keep the collection at or below its cap;
- preserve cross-discipline breadth;
- prefer complementary sources over near-duplicates;
- add or update the source's collection-specific rationale;
- remove a source when another provides materially better coverage for the same attention budget.

## Review evidence

Source-level admission rationale belongs in `curation.rationale`. Collection-specific rationale belongs in `selection_rationale`. Identity and transport provenance belong in `provenance.evidence`. Network reachability belongs in the health probe.

These evidence classes must remain separate. Machine validation checks consistency; maintainers retain the final editorial decision.
