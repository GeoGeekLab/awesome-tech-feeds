from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .compile import (
    compile_registry,
    opml_as_text,
    select_sources,
    stale_generated_files,
)
from .probe import probe_registry
from .validate import validate_registry

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console()


def _root(path: str) -> Path:
    return Path(path).resolve()


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
