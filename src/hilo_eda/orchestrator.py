from __future__ import annotations

from pathlib import Path
from typing import Iterable

import typer

from hilo_eda.config import OutputConfig, SnowflakeConfig, TableConfig
from hilo_eda.discovery import fetch_columns, table_exists
from hilo_eda.human import collect_human_selections
from hilo_eda.inference import infer_all
from hilo_eda.models import EDAQueryResult
from hilo_eda.profiling import profile_table
from hilo_eda.report import write_csv_outputs, write_markdown_report
from hilo_eda.sql_safety import qualify_table, quote_ident
from hilo_eda.snowflake import SnowflakeClient


def _format_inference(inferences: Iterable[str]) -> str:
    return ", ".join(inferences) if inferences else "None"


def _run_query(
    client: SnowflakeClient, title: str, sql: str
) -> EDAQueryResult:
    rows = client.execute_query(sql)
    return EDAQueryResult(title=title, sql=sql, rows=rows)


def _build_eda_queries(
    table: TableConfig,
    numeric_columns: list[str],
    categorical_columns: list[str],
    time_column: str | None,
) -> list[tuple[str, str]]:
    table_fqn = qualify_table(table.database, table.schema, table.table)
    queries: list[tuple[str, str]] = []

    if numeric_columns:
        for column in numeric_columns[:3]:
            col_ident = quote_ident(column)
            queries.append(
                (
                    f"Summary stats for {column}",
                    "SELECT "
                    f"MIN({col_ident}) AS MIN_VALUE, "
                    f"MAX({col_ident}) AS MAX_VALUE, "
                    f"AVG({col_ident}) AS AVG_VALUE, "
                    f"STDDEV({col_ident}) AS STDDEV_VALUE "
                    f"FROM {table_fqn}",
                )
            )

    if categorical_columns:
        for column in categorical_columns[:3]:
            col_ident = quote_ident(column)
            queries.append(
                (
                    f"Top values for {column}",
                    "SELECT "
                    f"{col_ident} AS VALUE, COUNT(*) AS COUNT "
                    f"FROM {table_fqn} "
                    f"GROUP BY {col_ident} "
                    "ORDER BY COUNT DESC NULLS LAST "
                    "LIMIT 10",
                )
            )

    if time_column:
        time_ident = quote_ident(time_column)
        queries.append(
            (
                f"Recent range for {time_column}",
                "SELECT "
                f"MIN({time_ident}) AS MIN_TS, "
                f"MAX({time_ident}) AS MAX_TS "
                f"FROM {table_fqn}",
            )
        )

    if len(numeric_columns) >= 2:
        col_a = quote_ident(numeric_columns[0])
        col_b = quote_ident(numeric_columns[1])
        queries.append(
            (
                f"Correlation {numeric_columns[0]} vs {numeric_columns[1]}",
                f"SELECT CORR({col_a}, {col_b}) AS CORR_VALUE "
                f"FROM {table_fqn}",
            )
        )

    return queries


def run_hilo_eda(
    snowflake: SnowflakeConfig,
    table: TableConfig,
    output: OutputConfig,
) -> None:
    client = SnowflakeClient(snowflake)
    try:
        if not table_exists(client, table):
            raise ValueError("Table not found in INFORMATION_SCHEMA.")

        columns = fetch_columns(client, table)
        if not columns:
            raise ValueError("No columns found for table.")

        table_profile, sample_rows = profile_table(client, table, columns)
        inferences = infer_all(table_profile.columns, table_profile.row_count)

        typer.echo("\nProfiling completed.")
        typer.echo(f"Columns: {[col.name for col in columns]}")
        typer.echo(
            f"Inferred behaviors: {_format_inference(i.behavior_class for i in inferences)}"
        )

        human = collect_human_selections([col.name for col in columns])

        ignore_set = {name.lower() for name in human.ignore_columns}
        filtered_inferences = [
            inference
            for inference in inferences
            if inference.column.lower() not in ignore_set
        ]

        numeric_columns = [
            inf.column
            for inf in filtered_inferences
            if "numeric" in inf.behavior_class
        ]
        categorical_columns = [
            inf.column
            for inf in filtered_inferences
            if "categorical" in inf.behavior_class
        ]

        queries = _build_eda_queries(
            table, numeric_columns, categorical_columns, human.time_column
        )
        executed_queries = [
            _run_query(client, title, sql) for title, sql in queries
        ]

        output.output_dir.mkdir(parents=True, exist_ok=True)
        report_path = Path(output.output_dir) / "eda_report.md"
        write_markdown_report(report_path, table_profile, inferences, human, executed_queries)

        if output.write_csv:
            write_csv_outputs(output.output_dir, table_profile, sample_rows)

        typer.echo(f"Report written to {report_path}")
    finally:
        client.close()
