from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .compile import compile_registry, generated_files_match
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
    )
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
        if not generated_files_match(registry_root):
            console.print("[red]generated artifacts are stale[/red]")
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
