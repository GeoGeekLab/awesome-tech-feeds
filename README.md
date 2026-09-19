<div align="center">

# Awesome Tech Feeds

**The web has enough feeds. The scarce resource is attention.**

Human-curated, machine-readable, continuously verified feeds for high-signal technical writing.

[![CI](https://github.com/GeoGeekLab/awesome-tech-feeds/actions/workflows/ci.yml/badge.svg)](https://github.com/GeoGeekLab/awesome-tech-feeds/actions/workflows/ci.yml)
[![Feed Health](https://github.com/GeoGeekLab/awesome-tech-feeds/actions/workflows/feed-health.yml/badge.svg)](https://github.com/GeoGeekLab/awesome-tech-feeds/actions/workflows/feed-health.yml)
[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white)](pyproject.toml)
[![Code License](https://img.shields.io/badge/code-MIT-2ea44f?style=flat-square)](LICENSE)
[![Data License](https://img.shields.io/badge/data-CC%20BY--SA%204.0-8A2BE2?style=flat-square)](DATA-LICENSE.md)

[Catalog](generated/catalog.md) · [Registry JSON](generated/registry.json) · [Essential OPML](generated/essential.opml) · [Contributing](CONTRIBUTING.md) · [Architecture](docs/architecture.md)

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
      └── traits[] ──────── descriptive properties
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

The initial registry contains **50 sources**, **8 collections**, and **4 profiles** spanning independent writers, engineering teams, research labs, communities, programming languages, systems, security, databases, and AI.

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
| [`essential`](collections/essential.yaml) | Small, high-signal starter set across technical disciplines |
| [`ai`](collections/ai.yaml) | AI, LLMs, ML systems, research, and practitioner writing |
| [`systems`](collections/systems.yaml) | Distributed systems, infrastructure, networking, and performance |
| [`security`](collections/security.yaml) | Security engineering, incident analysis, privacy, and research |
| [`databases`](collections/databases.yaml) | Databases, storage engines, query systems, and data infrastructure |
| [`programming-languages`](collections/programming-languages.yaml) | Languages, runtimes, compilers, and software construction |
| [`company-engineering`](collections/company-engineering.yaml) | First-party engineering publications from production teams |
| [`independent`](collections/independent.yaml) | Independent practitioners and long-form technical writers |

Every collection compiles to an importable OPML file under [`generated/`](generated/).

## Profiles

Profiles combine collections for common roles without creating a recommendation engine.

```text
developer
ai-engineer
founder
researcher
```

A profile is an inspectable policy file, not a hidden personalization model.

```yaml
schema_version: 1
id: ai-engineer
name: AI Engineer
collections:
  - ai
  - systems
  - databases
boost_topics:
  - llm
  - machine-learning
  - infrastructure
recommended_daily_budget: 15
```

## Registry contract

Each source has a permanent ID independent of its current domain or feed URL.

```yaml
schema_version: 1
id: simon-willison
name: Simon Willison's Weblog
kind: individual
language: en
website: https://simonwillison.net/
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
status: active
```

`id` is identity. URL is location.

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
- duplicate feed and website URLs;
- collection references;
- profile references;
- deterministic generated artifacts.

A pull request should fail because the registry is inconsistent, not because a third-party website had a bad minute.

Network health is checked separately.

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

The scheduled workflow publishes health as an artifact rather than rewriting editorial metadata.

## Generated artifacts

`generated/` is compiled from the registry and committed for zero-server consumption.

| Artifact | Purpose |
| --- | --- |
| [`registry.json`](generated/registry.json) | Full machine-readable registry |
| [`registry.min.json`](generated/registry.min.json) | Compact client payload |
| [`all.opml`](generated/all.opml) | All active primary feeds |
| [`essential.opml`](generated/essential.opml) | Starter pack for feed readers |
| topic OPML files | Collection-specific imports |
| [`catalog.md`](generated/catalog.md) | Human-readable generated catalog |
| `health.json` | Dynamic probe output; not committed |

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
src/techfeeds/ deterministic validator, compiler, and probe
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
