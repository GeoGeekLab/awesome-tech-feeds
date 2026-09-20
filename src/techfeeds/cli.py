from __future__ import annotations

import asyncio
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Annotated, cast

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .compile import compile_registry, opml_as_text, select_sources, stale_generated_files
from .consumer import ConsumerError, Query, Registry, StatusFilter
from .probe import probe_registry
from .validate import validate_registry

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console()


def _root(path: str) -> Path:
    return Path(path).resolve()


def _consumer_registry(root: str, registry_file: str | None) -> Registry:
    if registry_file is not None:
        return Registry.from_file(registry_file)
    return Registry.from_mapping(compile_registry(_root(root), write=False))


def _version(value: bool) -> None:
    if value:
        console.print(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version,
        is_eager=True,
        help="Show the installed version and exit.",
    ),
) -> None:
    """Validate, compile, and probe the Awesome Tech Feeds registry."""


@app.command()
def validate(root: str = typer.Option(".", help="Registry root.")) -> None:
    """Validate schemas, references, IDs, vocabularies, and duplicates."""
    errors = validate_registry(_root(root))
    if errors:
        for error in errors:
            console.print(f"[red]ERROR[/red] {error}")
        raise typer.Exit(1)
    console.print("[green]registry valid[/green]")


@app.command(name="compile")
def compile_command(
    root: str = typer.Option(".", help="Registry root."),
    check: bool = typer.Option(False, "--check", help="Fail if generated artifacts are stale."),
) -> None:
    """Compile JSON, OPML, and the human-readable catalog."""
    registry_root = _root(root)
    if check:
        stale = stale_generated_files(registry_root)
        if stale:
            console.print("[red]generated artifacts are stale[/red]")
            for path in stale:
                console.print(f"  {path}")
            raise typer.Exit(1)
        console.print("[green]generated artifacts are current[/green]")
        return

    payload = compile_registry(registry_root)
    counts = payload["counts"]
    console.print(
        f"[green]compiled[/green] {counts['sources']} sources · "
        f"{counts['collections']} collections · {counts['profiles']} profiles"
    )


@app.command()
def stats(root: str = typer.Option(".", help="Registry root.")) -> None:
    """Print deterministic registry counts."""
    payload = compile_registry(_root(root), write=False)
    table = Table(show_header=False, box=None)
    for key, value in payload["counts"].items():
        table.add_row(key, str(value))
    console.print(table)


@app.command(name="export")
def export_command(
    root: str = typer.Option(".", help="Registry root."),
    collection: str | None = typer.Option(None, "--collection", help="Collection ID to export."),
    topic: Annotated[
        list[str] | None,
        typer.Option("--topic", help="Require a topic; repeat for AND filtering."),
    ] = None,
    trait: Annotated[
        list[str] | None,
        typer.Option("--trait", help="Require a trait; repeat for AND filtering."),
    ] = None,
    language: str | None = typer.Option(None, "--language", help="Language code filter."),
    kind: str | None = typer.Option(None, "--kind", help="Source kind filter."),
    format: str = typer.Option("opml", "--format", help="Output format: opml or json."),
    output: str = typer.Option("-", "--output", "-o", help="'-' for stdout or a file path."),
) -> None:
    """Export an active subset of the registry for readers, scripts, or agents."""
    if format not in {"opml", "json"}:
        console.print(f"[red]ERROR[/red] unsupported export format: {format}")
        raise typer.Exit(2)

    try:
        sources = select_sources(
            _root(root),
            collection_id=collection,
            topics=tuple(topic or ()),
            traits=tuple(trait or ()),
            language=language,
            kind=kind,
        )
    except ValueError as exc:
        console.print(f"[red]ERROR[/red] {exc}")
        raise typer.Exit(2) from exc

    if format == "opml":
        title = "Awesome Tech Feeds — " + (collection if collection is not None else "Export")
        content = opml_as_text(title, sources)
    else:
        content = (
            json.dumps(
                {
                    "schema_version": 2,
                    "component_schema_versions": {"source": 2},
                    "count": len(sources),
                    "sources": sources,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    if output == "-":
        typer.echo(content, nl=False)
        return

    target = Path(output).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    console.print(f"[green]exported[/green] {len(sources)} sources to {target}")


@app.command(name="query")
def query_command(
    root: str = typer.Option(".", help="Registry root when --registry is not supplied."),
    registry_file: str | None = typer.Option(
        None,
        "--registry",
        help="Compiled registry.json file; avoids requiring a repository checkout.",
    ),
    collection: str | None = typer.Option(None, "--collection", help="Collection ID."),
    topic: Annotated[
        list[str] | None,
        typer.Option("--topic", help="Require a topic; repeat for AND filtering."),
    ] = None,
    trait: Annotated[
        list[str] | None,
        typer.Option("--trait", help="Require a trait; repeat for AND filtering."),
    ] = None,
    language: str | None = typer.Option(None, "--language", help="Language code filter."),
    kind: str | None = typer.Option(None, "--kind", help="Source kind filter."),
    status: str = typer.Option(
        "active",
        "--status",
        help="Source status: active, retired, or all.",
    ),
) -> None:
    """Run Query Contract v1 and emit Query Result Contract v1 JSON."""
    try:
        registry = _consumer_registry(root, registry_file)
        result = registry.query(
            Query(
                collection=collection,
                topics=tuple(topic or ()),
                traits=tuple(trait or ()),
                language=language,
                kind=kind,
                status=cast(StatusFilter, status),
            )
        )
    except ConsumerError as exc:
        typer.echo(exc.to_json(), err=True, nl=False)
        raise typer.Exit(2) from exc

    typer.echo(result.to_json(), nl=False)


@app.command(name="profile")
def profile_command(
    profile_id: str = typer.Argument(..., help="Profile ID to resolve."),
    root: str = typer.Option(".", help="Registry root when --registry is not supplied."),
    registry_file: str | None = typer.Option(
        None,
        "--registry",
        help="Compiled registry.json file; avoids requiring a repository checkout.",
    ),
    format: str = typer.Option("json", "--format", help="Output format: json or opml."),
    output: str = typer.Option("-", "--output", "-o", help="'-' for stdout or a file path."),
) -> None:
    """Resolve Profile Contract v2 into deterministic JSON or OPML."""
    if format not in {"json", "opml"}:
        console.print(f"[red]ERROR[/red] unsupported profile format: {format}")
        raise typer.Exit(2)

    try:
        registry = _consumer_registry(root, registry_file)
        result = registry.resolve_profile(profile_id)
    except ConsumerError as exc:
        typer.echo(exc.to_json(), err=True, nl=False)
        raise typer.Exit(2) from exc

    content = result.to_json() if format == "json" else result.to_opml()
    if output == "-":
        typer.echo(content, nl=False)
        return

    target = Path(output).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    console.print(f"[green]resolved[/green] profile {profile_id} to {target}")


@app.command()
def reviews(
    root: str = typer.Option(".", help="Registry root."),
    as_of: str = typer.Option(..., "--as-of", help="Review date in YYYY-MM-DD form."),
    within_days: int = typer.Option(
        0,
        "--within-days",
        min=0,
        max=366,
        help="Also include reviews due within this many days after --as-of.",
    ),
) -> None:
    """List active sources whose editorial review is due by a deterministic date."""
    try:
        as_of_date = date.fromisoformat(as_of)
    except ValueError as exc:
        console.print(f"[red]ERROR[/red] invalid --as-of date: {as_of}")
        raise typer.Exit(2) from exc

    cutoff = as_of_date + timedelta(days=within_days)
    payload = compile_registry(_root(root), write=False)
    due = []
    for source in payload["sources"]:
        if source["status"] != "active":
            continue
        review_after = date.fromisoformat(source["curation"]["review_after"])
        if review_after <= cutoff:
            due.append(source)

    if not due:
        console.print("[green]no reviews due[/green]")
        return

    table = Table("source", "reviewer", "reviewed", "review after")
    for source in due:
        curation = source["curation"]
        table.add_row(
            str(source["id"]),
            str(curation["reviewer"]),
            str(curation["reviewed_at"]),
            str(curation["review_after"]),
        )
    console.print(table)


@app.command()
def probe(
    root: str = typer.Option(".", help="Registry root."),
    concurrency: int = typer.Option(8, min=1, max=32, help="Maximum concurrent requests."),
) -> None:
    """Probe active feeds and write generated/health.json."""
    payload = asyncio.run(probe_registry(_root(root), concurrency))
    table = Table("state", "count")
    for state, count in payload["counts"].items():
        table.add_row(state, str(count))
    console.print(table)


if __name__ == "__main__":
    app()
