# Contributing

Awesome Tech Feeds is curated, not exhaustive.

A contribution should improve durable signal, registry correctness, or verifiability without turning the project into a directory of every technically valid feed.

## Before adding a source

Ask:

- Does it publish substantially original material?
- Is the value durable across multiple posts rather than one viral article?
- Does it add a perspective, domain, practitioner experience, or evidence base not already well covered?
- Is there a stable public feed endpoint?
- Can the source be described with the existing controlled taxonomy?

Popularity is not an admission criterion.

## Add a source

Create one YAML file under the appropriate `sources/` directory. The filename must equal `id`.

```yaml
schema_version: 1
id: example-engineering
name: Example Engineering
kind: company
language: en
website: https://example.com/engineering/
feeds:
  - url: https://example.com/engineering/feed.xml
    format: atom
    role: primary
    official: true
topics:
  - distributed-systems
traits:
  - first-party
  - company-engineering
  - practitioner
status: active
```

If the source belongs in an existing collection, update that collection in the same pull request.

## Collection changes

Collections are editorial products with explicit attention budgets, not arbitrary tags.

When a collection declares `policy.max_sources`, a change that exceeds the cap is invalid. When `policy.require_rationale: true`, every member must have a non-empty entry in `selection_rationale`, and rationales may only reference members of that collection.

For `essential`, preserve cross-discipline breadth and low redundancy. Adding an excellent source is not sufficient reason to expand the starter set; a replacement may be more appropriate.

See [`docs/curation.md`](docs/curation.md) for the review contract.

## Validate locally

Requires Python 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'

ruff check .
ruff format --check .
mypy
techfeeds validate
techfeeds compile
techfeeds compile --check
pytest
```

Never hand-edit generated JSON, OPML, or the generated catalog. Change registry inputs and run `techfeeds compile`.

`generated/health.json` is dynamic probe output and is intentionally not committed.

## Taxonomy changes

Do not invent near-synonyms inside a source file.

If the existing vocabulary cannot describe a source, propose the topic or trait in `registry/` and explain why the new concept is distinct enough to deserve a stable public identifier.

## Network failures

A failed health probe is evidence about an endpoint at one moment, not permission to delete a source.

When repairing a broken feed:

1. verify whether the source moved or changed feed URLs,
2. prefer an official first-party feed,
3. preserve the source ID,
4. update the endpoint,
5. document a fallback only when necessary.

## Pull request scope

Keep the patch coherent.

A source addition should not contain unrelated taxonomy cleanup, code refactoring, or mass formatting. A tooling change should include the tests and generated-artifact updates required by that change.
