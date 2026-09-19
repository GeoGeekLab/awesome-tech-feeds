# Architecture

Awesome Tech Feeds separates editorial judgment from deterministic registry mechanics and from volatile network observations.

## Layers

```text
editorial metadata        deterministic tooling          network observations
------------------        ---------------------          --------------------
sources/             ───► validate                  ───► scheduled probe
collections/         ───► compile                        ETag / Last-Modified
profiles/                 JSON / OPML / catalog           health.json
registry/ taxonomy
```

The boundaries are deliberate.

- `sources/` describes durable identity and subscription endpoints.
- `collections/` expresses human curation.
- `profiles/` combines collections for a role.
- `registry/` prevents uncontrolled taxonomy drift.
- `generated/` is reproducible output.
- feed health is observational and must not silently rewrite editorial metadata.

## Invariants

### Source is not feed

A source is the durable identity of a person, organization, project, publication, or community. A feed is one transport endpoint exposed by that source.

One source may have multiple feeds. An endpoint may move without changing source identity.

### Health is not quality

Operational reachability is measured. Editorial quality is curated.

The health probe may say `broken`; it may not say a source is low quality.

### Registry validation is deterministic

Pull-request validation must not depend on arbitrary third-party network uptime. Network checks run in a separate scheduled workflow.

### Generated artifacts are reproducible

`techfeeds compile` contains no current timestamp, random identifier, or environment-specific path. Running it twice on the same registry produces the same committed artifacts.

### Controlled vocabularies are contracts

Topics, traits, and languages are registry-level values. A contributor cannot create a synonym by accident inside one source file.

## Consumer boundary

The registry is intentionally unaware of article-ranking and summarization systems.

A downstream system may implement:

```text
registry.json
    ↓
feed polling
    ↓
article normalization
    ↓
deduplication
    ↓
ranking
    ↓
summarization
    ↓
Telegram / RSS / email / web
```

Those concerns should not leak back into source identity or health semantics.
