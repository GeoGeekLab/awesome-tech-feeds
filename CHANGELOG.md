# Changelog

## 0.4.0 - 2026-09-20

Consumer SDK and Query Contract.

- Added a public typed Python SDK that consumes compiled `registry.json` without a repository checkout.
- Added immutable `Query`, `QueryResult`, `SourceRecord`, and `Registry` consumer types.
- Added local-file and HTTPS registry loading with optional SHA-256 integrity verification.
- Added Query Request, Result, and Error Contract v1 JSON Schemas with stable error codes.
- Defined deterministic AND-filter semantics and stable ordering guarantees.
- Added `techfeeds query` for machine-readable queries against a repository or downloaded registry.
- Routed the legacy `techfeeds export` selector through the same query engine without changing its output shape.
- Added PEP 561 `py.typed` metadata and wheel-level public SDK smoke tests.
- Added query-contract schemas to checksum-covered GitHub release assets.

## 0.3.0 - 2026-09-20

Registry Contract 2.0.

- Migrated all 50 source records to source schema v2.
- Made source descriptions, admission rationales, admission basis, reviewer, and review dates mandatory.
- Added structured provenance evidence with deterministic canonical-website and primary-feed checks.
- Added deterministic review chronology rules and a `techfeeds reviews --as-of` workflow.
- Published immutable source schema snapshots for v1 and v2 plus a latest-schema alias.
- Bumped the compiled registry contract to v2 with explicit component schema versions.
- Added a formal v1→v2 migration and compatibility policy.

## 0.2.0 - 2026-09-20

Curation and consumption contracts.

- Reduced the `essential` starter set from 50 sources to 18 and capped it at 20.
- Added enforceable collection policies and per-member selection rationales.
- Added `techfeeds export` with collection/topic/trait/language/kind filters for JSON and OPML.
- Published scheduled `health.json` snapshots at a stable `health-latest` release URL.
- Added a documented curation contract and surfaced rationales in the generated catalog.

## 0.1.0 - 2026-09-20

Initial registry release.

- 50 curated technical sources.
- 8 topic/editorial collections.
- 4 role-oriented profiles.
- Versioned JSON Schemas and controlled vocabularies.
- Deterministic JSON, OPML, and catalog compiler.
- Feed health probing with conditional HTTP support.
- CI validation and scheduled health workflow.
