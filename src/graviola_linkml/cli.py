"""Typer CLI for the Graviola LinkML generator."""

from pathlib import Path
from typing import Optional

import typer

from graviola_linkml.generators.json_schema import GraviolaJsonSchemaGenerator

app = typer.Typer(help="Generate Graviola schemas from LinkML YAML definitions.")


@app.command()
def generate(
    schema: Path = typer.Argument(..., help="Path to the LinkML YAML schema file."),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path. Defaults to <schema-stem>.schema.json next to the input.",
    ),
    indent: int = typer.Option(2, "--indent", help="JSON indentation width."),
) -> None:
    """Generate a Graviola JSON Schema from a LinkML YAML schema."""
    if not schema.exists():
        typer.echo(f"Error: schema file not found: {schema}", err=True)
        raise typer.Exit(1)

    gen = GraviolaJsonSchemaGenerator(str(schema), indent=indent)
    result = gen.serialize()

    out_path = output or schema.with_suffix("").with_suffix(".schema.json")
    out_path.write_text(result, encoding="utf-8")
    typer.echo(f"Written: {out_path}")


if __name__ == "__main__":
    app()
