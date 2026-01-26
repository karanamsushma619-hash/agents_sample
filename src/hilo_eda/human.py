from __future__ import annotations

import typer

from hilo_eda.models import HumanSelections


def _parse_optional(value: str) -> str | None:
    cleaned = value.strip()
    return cleaned if cleaned else None


def _parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def collect_human_selections(columns: list[str]) -> HumanSelections:
    typer.echo("\nHuman-in-the-loop checkpoint: confirm column roles.")
    typer.echo(f"Available columns: {', '.join(columns)}")

    identifier = _parse_optional(
        typer.prompt("Identifier column (blank if none)", default="")
    )
    time_column = _parse_optional(
        typer.prompt("Time column (blank if none)", default="")
    )
    status_column = _parse_optional(
        typer.prompt("Status/outcome column (blank if none)", default="")
    )
    ignore_columns = _parse_list(
        typer.prompt("Columns to ignore (comma-separated)", default="")
    )
    eda_direction = typer.prompt(
        "EDA direction (e.g., quality, outcomes, relationships)",
        default="behavior-based exploration",
    )

    return HumanSelections(
        identifier=identifier,
        time_column=time_column,
        status_column=status_column,
        ignore_columns=ignore_columns,
        eda_direction=eda_direction,
    )
