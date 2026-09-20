# Registry contract

The JSON Schemas in [`schema/`](../schema/) are the executable data contract. This document defines the semantics and compatibility rules that schema validation alone cannot express.

## Contract versions

The current compiled registry contract is version 2.

| Component | Current schema |
| --- | ---: |
| Compiled registry bundle | 2 |
| Source record | 2 |
| Collection record | 1 |
| Profile record | 2 |

Stable source schema snapshots are published as `schema/source.v1.schema.json` and `schema/source.v2.schema.json`. Stable profile snapshots are published as `schema/profile.v1.schema.json` and `schema/profile.v2.schema.json`. The unversioned `source.schema.json` and `profile.schema.json` files are latest aliases.

A released versioned schema is immutable. A future incompatible source contract must publish a new versioned schema rather than rewriting v2 semantics.

## Source identity

`id` is a permanent public identity. It is lowercase ASCII letters, digits, and hyphens; it matches the YAML filename; and it does not change merely because a domain, brand, or feed URL changes.

A source is not a feed. A feed is a transport endpoint attached to a durable source identity.

## Source contract v2

Every source record requires four groups of information:

1. identity and transport;
2. descriptive taxonomy;
3. editorial curation;
4. provenance.

Example:

```yaml
schema_version: 2
id: simon-willison
name: "Simon Willison’s Weblog"
kind: individual
language: en
website: https://simonwillison.net/
description: "Independent technical writing covering AI, LLMs, Python, databases, and the web."
feeds:
  - url: https://simonwillison.net/atom/everything/
    format: atom
    role: primary
    official: true
topics:
  - ai
  - llm
  - python
  - databases
  - web
traits:
  - original
  - practitioner
  - deep-dive
  - independent
  - high-frequency
curation:
  rationale: "Admitted for recurring practitioner writing with reproducible technical detail."
  admission_basis:
    - independent-practitioner
  reviewer: GeoGeekLab
  reviewed_at: "2026-09-20"
  review_after: "2026-12-19"
provenance:
  added_by: GeoGeekLab
  added_at: "2026-09-20"
  evidence:
    - type: identity
      url: https://simonwillison.net/
    - type: feed
      url: https://simonwillison.net/atom/everything/
status: active
```

## Curation

`curation.rationale` explains why the source belongs in the registry. It is source-level and must not be confused with a collection-specific `selection_rationale`.

`admission_basis` uses a small schema-controlled vocabulary: `first-party-engineering`, `first-party-technical`, `independent-practitioner`, `independent-analysis`, `primary-research`, `official-project`, `technical-community`, or `technical-publication`.

`reviewed_at` records the editorial review represented by the current rationale. `review_after` schedules the next review. Validation requires a review interval of 30–366 days. CI does not compare these dates with wall-clock time; use `techfeeds reviews --as-of YYYY-MM-DD` to query due reviews deterministically.

## Provenance

`provenance` records where the registry's identity and transport assertions came from.

Every v2 source must include at least two evidence entries. Semantic validation requires:

- an `identity` evidence URL matching the canonical `website`;
- a `feed` evidence URL matching the current primary feed.

Additional evidence types are `representative-work`, `about`, and `repository`.

`added_at` may not be later than `curation.reviewed_at`.

Provenance evidence is not feed-health evidence. Reachability and parse status remain in `health.json`.

## Feeds

Every active source must expose exactly one `primary` feed. In v2 every feed also declares a `format`.

`official: true` means the endpoint is published or controlled by the source. A community-maintained endpoint may be primary when necessary, but it must be marked `false`.

## Topics and traits

Topics and traits remain controlled vocabularies in [`registry/`](../registry/). Topics describe subject matter. Traits describe recurring properties such as `deep-dive`, `practitioner`, or `company-engineering`.

They are descriptive metadata, not quality scores.

## Status and retirement

`active` means the registry expects the source identity to remain consumable. `retired` preserves history when a source has ended, merged, or moved to another identity and requires `redirect_to`.

A failed network probe never automatically retires a source.

## Compiled registry v2

`generated/registry.json` now declares:

```json
{
  "schema_version": 2,
  "component_schema_versions": {
    "source": 2,
    "collection": 1,
    "profile": 2
  }
}
```

Consumers should branch on these version fields rather than infer capabilities from field presence.

See [`docs/migrations/source-v1-to-v2.md`](migrations/source-v1-to-v2.md) for the v1 migration and compatibility policy.


## Profile contract v2

Profiles are deterministic consumer policies over collections. Profile v2 separates collection selection, boost rules, exclusion rules, and downstream item budget. The compiled registry publishes `component_schema_versions.profile: 2`.

Profile resolution semantics are documented in [`docs/profiles.md`](profiles.md), with migration guidance in [`docs/migrations/profile-v1-to-v2.md`](migrations/profile-v1-to-v2.md).
