# Source schema migration: v1 → v2

Source contract v2 makes editorial accountability and provenance part of the machine-readable registry.

## What changed

v1 required identity, feed, taxonomy, and status fields. v2 preserves those semantics and adds required:

- `description`;
- `curation.rationale`;
- `curation.admission_basis`;
- `curation.reviewer`;
- `curation.reviewed_at`;
- `curation.review_after`;
- `provenance.added_by`;
- `provenance.added_at`;
- structured `provenance.evidence`.

Every feed also requires an explicit `format`.

The compiled registry bundle changes from `schema_version: 1` to `schema_version: 2` and publishes `component_schema_versions`.

## Compatibility guarantees

The v2 migration does not intentionally change source IDs, collection membership, primary feed URLs, OPML identity attributes, topics, or traits.

Versioned releases remain immutable. Consumers that require the v1 full-registry shape can pin the v0.2.0 release. Consumers moving to v2 should branch on `schema_version` and ignore unknown fields.

`registry.min.json` keeps the same compact per-source field set but its top-level schema version is 2 so consumers can detect the new release contract.

Stable schemas:

- `schema/source.v1.schema.json` — legacy v1 validation contract;
- `schema/source.v2.schema.json` — stable v2 validation contract;
- `schema/source.schema.json` — latest alias, currently v2.

## Migrating a source record

1. Change `schema_version` from 1 to 2.
2. Add a concise factual `description`.
3. Add a human-reviewed `curation.rationale`.
4. Select one or more schema-defined `admission_basis` values.
5. Record `reviewer`, `reviewed_at`, and `review_after`.
6. Add provenance with `added_by`, `added_at`, and structured evidence.
7. Include an `identity` evidence URL matching `website`.
8. Include a `feed` evidence URL matching the primary feed.
9. Run `techfeeds validate` and `techfeeds compile`.

There is deliberately no automatic tool that invents a rationale. A schema migration can automate syntax, but the admission rationale is an editorial assertion and must remain human-reviewable.

## Review lifecycle

Validation checks chronology without depending on today's date:

```text
added_at ≤ reviewed_at < review_after
30 days ≤ review interval ≤ 366 days
```

To find due reviews for an explicit date:

```bash
techfeeds reviews --as-of 2026-12-19
techfeeds reviews --as-of 2026-12-01 --within-days 30
```

This keeps pull-request validation deterministic while still making review scheduling operational.
