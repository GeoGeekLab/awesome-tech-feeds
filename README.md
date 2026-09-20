<div align="center">

# Awesome Tech Feeds

**The web has enough feeds. The scarce resource is attention.**

Human-curated, machine-readable, continuously verified feeds for high-signal technical writing — with auditable curation and provenance.

[![CI](https://github.com/GeoGeekLab/awesome-tech-feeds/actions/workflows/ci.yml/badge.svg)](https://github.com/GeoGeekLab/awesome-tech-feeds/actions/workflows/ci.yml)
[![Feed Health](https://github.com/GeoGeekLab/awesome-tech-feeds/actions/workflows/feed-health.yml/badge.svg)](https://github.com/GeoGeekLab/awesome-tech-feeds/actions/workflows/feed-health.yml)
[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white)](pyproject.toml)
[![Code License](https://img.shields.io/badge/code-MIT-2ea44f?style=flat-square)](LICENSE)
[![Data License](https://img.shields.io/badge/data-CC%20BY--SA%204.0-8A2BE2?style=flat-square)](DATA-LICENSE.md)

[Catalog](generated/catalog.md) · [Registry JSON](generated/registry.json) · [Consumer SDK](docs/consumer-sdk.md) · [Essential OPML](generated/essential.opml) · [Latest Health](https://github.com/GeoGeekLab/awesome-tech-feeds/releases/download/health-latest/health.json) · [Curation](docs/curation.md) · [Contributing](CONTRIBUTING.md) · [Architecture](docs/architecture.md)

</div>

---

A feed can be technically valid and still waste your time.

A famous blog can publish a weak post.

A low-frequency independent writer can be worth more than a hundred news feeds.

**Awesome Tech Feeds is a registry of sources, not a popularity chart.** Humans curate durable signal. Deterministic tooling validates identity, taxonomy, references, duplicates, generated artifacts, and network health.

No article mirroring. No black-box quality score. No AI deciding what deserves to enter the registry.

## Mental model

```text
human curation
      │
      ▼
   sources/ ─────────────── durable identity
      │
      ├── feeds[] ───────── transport endpoints
      ├── topics[] ──────── controlled taxonomy
      ├── traits[] ──────── descriptive properties
      ├── curation ───────── rationale + review lifecycle
      └── provenance ─────── identity/feed evidence
      │
      ▼
 collections/ ───────────── editorial bundles
      │
      ▼
  profiles/ ─────────────── role-oriented starting points
      │
      ▼
 deterministic compiler
      │
      ├── registry.json
      ├── registry.min.json
      ├── *.opml
      └── catalog.md

scheduled probes ──────────► health.json
```

The operating rules are simple:

```text
source ≠ feed
health ≠ quality
curation ≠ popularity
metadata ≠ article content
observed failure ≠ permanent removal
```

## What ships

The registry contains **50 sources**, **8 collections**, and **4 profiles** spanning independent writers, engineering teams, research labs, communities, programming languages, systems, security, databases, and AI. The deliberately opinionated `essential` starter set contains **18 sources** and is hard-capped at **20**.

Representative sources include:

- Simon Willison
- Julia Evans
- Martin Fowler
- Brendan Gregg
- Cloudflare
- Stripe
- Netflix TechBlog
- Uber Engineering
- Anthropic
- Google DeepMind
- Hugging Face
- Hacker News

The complete list is generated at [`generated/catalog.md`](generated/catalog.md).

## Choose a collection, not fifty URLs

A registry is useful to machines. Collections are useful to people.

| Collection | Intent |
| --- | --- |
| [`essential`](collections/essential.yaml) | 18-source high-signal starter set, capped at 20 with an explicit rationale for every member |
| [`ai`](collections/ai.yaml) | AI, LLMs, ML systems, research, and practitioner writing |
| [`systems`](collections/systems.yaml) | Distributed systems, infrastructure, networking, and performance |
| [`security`](collections/security.yaml) | Security engineering, incident analysis, privacy, and research |
| [`databases`](collections/databases.yaml) | Databases, storage engines, query systems, and data infrastructure |
| [`programming-languages`](collections/programming-languages.yaml) | Languages, runtimes, compilers, and software construction |
| [`company-engineering`](collections/company-engineering.yaml) | First-party engineering publications from production teams |
| [`independent`](collections/independent.yaml) | Independent practitioners and long-form technical writers |

Every collection compiles to an importable OPML file under [`generated/`](generated/).

Collections may declare policy such as `max_sources` and `require_rationale`. The validator enforces those contracts, and the generated catalog exposes collection-specific rationales where present. See [`docs/curation.md`](docs/curation.md).

## Export subsets

The CLI can export machine- or reader-ready subsets without requiring consumers to reimplement registry filtering.

```bash
# Importable starter pack
techfeeds export --collection essential --format opml -o essential.opml

# Independent security sources as JSON
techfeeds export --topic security --trait independent --format json

# Multiple topic/trait options compose with AND semantics
techfeeds export --topic ai --topic llm --trait research --format json
```

Filters are available for collection, topic, trait, language, and source kind. Unknown filter values fail explicitly instead of silently producing an empty export.

## Consumer SDK

Version 0.4 exposes a typed Python consumer API over compiled `registry.json`. Consumers no longer need to understand the repository's YAML layout.

Install the pinned v0.4 package directly from the GitHub Release wheel:

```bash
python -m pip install \
  https://github.com/GeoGeekLab/awesome-tech-feeds/releases/download/v0.4.1/awesome_tech_feeds-0.4.1-py3-none-any.whl
```

```python
from techfeeds import Query, Registry

registry = Registry.from_url()
result = registry.query(
    Query(
        collection="essential",
        topics=("ai",),
        traits=("research",),
    )
)

for source in result.sources:
    print(source.id, source.website)
```

For pinned workflows, load a downloaded release asset and verify its SHA-256 before parsing:

```python
registry = Registry.from_file(
    "registry.json",
    expected_sha256="<digest from SHA256SUMS>",
)
```

The SDK has explicit compatibility failures, deterministic ordering, immutable query objects, defensive source records, stable JSON error codes, and PEP 561 typing metadata.

The CLI exposes the same Query Contract v1 engine:

```bash
techfeeds query --registry registry.json --topic security --trait independent
```

Success is Query Result Contract v1 JSON. Query failures are Query Error Contract v1 JSON on stderr. The legacy `techfeeds export` surface remains compatible and delegates filtering to the same engine.

See [`docs/consumer-sdk.md`](docs/consumer-sdk.md) for request/result/error schemas, ordering guarantees, and compatibility rules.

## Profiles 2.0

Profiles are executable, inspectable consumption policies — not hidden personalization models.

```text
developer
ai-engineer
founder
researcher
```

A v2 profile unions collections, applies explicit exclusions, computes explainable boost priority, and preserves deterministic tie order.

```yaml
schema_version: 2
id: researcher
name: Researcher
description: >-
  Research-focused AI and machine-learning sources emphasizing primary research and
  technical research explanations over community aggregation.
collections:
  - ai
boost:
  topics:
    - research
    - machine-learning
  traits: []
exclude:
  topics: []
  traits:
    - community
  sources: []
budget:
  recommended_daily_items: 12
```

The daily-item budget is downstream reading/article-processing metadata; it does not truncate the source set.

Resolve a profile directly:

```bash
techfeeds profile researcher --registry registry.json
techfeeds profile developer --registry registry.json --format opml -o developer.opml
```

Or through Python:

```python
registry = Registry.from_url()
result = registry.resolve_profile("researcher")

for item in result.sources:
    print(item.source.id, item.priority_score, item.matched_boost_topics)
```

See [`docs/profiles.md`](docs/profiles.md) for resolution semantics and generated artifacts.

## Registry contract

Each source has a permanent ID independent of its current domain or feed URL.

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

`id` is identity. URL is location. `curation` explains why the source belongs; `provenance` records the evidence for identity and transport.

If a domain changes, the ID stays stable. If a source is retired, the historical record can remain and point to a replacement.

See [`docs/registry.md`](docs/registry.md) for the field-level contract.

## Validation

The registry is data as code.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'

techfeeds validate
techfeeds compile --check
pytest
```

Validation checks:

- JSON Schema compliance;
- stable ID and filename agreement;
- controlled topics, traits, and languages;
- exactly one primary feed for every active source;
- source curation rationale and review-window chronology;
- provenance coverage for canonical identity and primary feed;
- duplicate feed and website URLs;
- collection references;
- collection size budgets and required selection rationales;
- profile references;
- deterministic generated artifacts.

A pull request should fail because the registry is inconsistent, not because a third-party website had a bad minute.

Network health is checked separately.

Editorial review scheduling is also queryable without making CI depend on wall-clock time:

```bash
techfeeds reviews --as-of 2026-12-19
techfeeds reviews --as-of 2026-12-01 --within-days 30
```

The current full registry is contract v2; collection and profile component schemas remain v1. See [`docs/registry.md`](docs/registry.md) and the [v1→v2 migration guide](docs/migrations/source-v1-to-v2.md).

## Health is operational evidence, not editorial judgment

```bash
techfeeds probe --concurrency 8
```

The probe uses conditional requests when previous `ETag` or `Last-Modified` values are available and records observations in `generated/health.json`.

Health states are intentionally narrow:

| State | Meaning |
| --- | --- |
| `healthy` | Fetch succeeded and the feed parsed with entries |
| `degraded` | Reachable but blocked, rate-limited, or otherwise impaired |
| `stale` | Feed parsed but returned no entries |
| `broken` | Network or parse failure |

A stale feed is not a bad source. A fast feed is not a good source.

The scheduled workflow publishes health as both a retained Actions artifact and a stable release asset rather than rewriting editorial metadata.

The latest machine-readable snapshot is available at:

`https://github.com/GeoGeekLab/awesome-tech-feeds/releases/download/health-latest/health.json`

## Generated artifacts

`generated/` is compiled from the registry and committed for zero-server consumption.

| Artifact | Purpose |
| --- | --- |
| [`registry.json`](generated/registry.json) | Full machine-readable registry |
| [`registry.min.json`](generated/registry.min.json) | Compact client payload |
| [`all.opml`](generated/all.opml) | All active primary feeds |
| [`essential.opml`](generated/essential.opml) | Starter pack for feed readers |
| topic OPML files | Collection-specific imports |
| `profile-*.json` | Resolved profile policy with explainable priority metadata |
| `profile-*.opml` | Resolved profile imports for feed readers |
| [`catalog.md`](generated/catalog.md) | Human-readable generated catalog |
| `health.json` | Dynamic probe output; not committed, with the latest snapshot published at the stable `health-latest` release URL |

This makes GitHub itself the distribution layer. No database or application server is required to consume the registry.

## Add a source

Do not add a source because one post went viral.

Add it because the source has a durable reason to deserve attention.

A useful submission answers:

```text
Who produces it?
What does it consistently teach or reveal?
Is the content substantially original?
Is there a stable feed endpoint?
Which controlled topics and traits describe it?
What would be lost if this source disappeared from the registry?
```

The CI checks mechanics. Maintainers review editorial fit.

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Non-goals

Awesome Tech Feeds does not:

- mirror article text or images;
- rank individual articles;
- score people or publications from 0–100;
- become a universal directory of every available RSS feed;
- use LLM output as an admission decision;
- track readers or build behavioral profiles;
- treat network uptime as content quality.

A separate consumer can fetch `registry.json`, deduplicate new entries, rank articles, summarize them, and publish to Telegram, email, RSS, or the web without mixing those concerns into source governance.

## Repository layout

```text
sources/       durable source records
collections/   curated bundles
profiles/      role-oriented starting points
registry/      controlled vocabularies
schema/        versioned JSON Schemas
generated/     compiled JSON, OPML, and catalog
src/techfeeds/ validator, compiler, consumer SDK, CLI, and probe
tests/         contract tests
docs/          architecture and registry semantics
```

## Licensing

Code and tooling are released under the [MIT License](LICENSE).

Registry metadata is released under [CC BY-SA 4.0](DATA-LICENSE.md). The repository stores metadata and feed endpoints, not copyrighted article bodies.

---

<div align="center">

**Curate the source. Verify the feed. Keep the boundary clear.**

`signal ≠ popularity`

**Geo to see. Geek to build.**

</div>
