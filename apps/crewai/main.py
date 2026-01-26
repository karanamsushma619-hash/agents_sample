from __future__ import annotations

from pathlib import Path

import typer
from crewai import Agent, Crew, Task

from hilo_eda.config import OutputConfig, SnowflakeConfig, TableConfig
from hilo_eda.orchestrator import run_hilo_eda

app = typer.Typer(add_completion=False)


def build_crew() -> Crew:
    analyst = Agent(
        role="EDA Analyst",
        goal="Run the HILO EDA workflow using the shared core.",
        backstory="Specialized in Snowflake read-only exploration.",
    )
    task = Task(
        description="Execute the shared HILO EDA workflow.",
        expected_output="Markdown report and CSV outputs.",
    )
    return Crew(agents=[analyst], tasks=[task])


@app.command()
def run(
    table: str = typer.Option(..., help="Table name"),
    database: str = typer.Option(..., help="Database name"),
    schema: str = typer.Option(..., help="Schema name"),
    output_dir: Path = typer.Option(Path("outputs"), help="Output directory"),
    write_csv: bool = typer.Option(True, help="Write CSV outputs"),
    account: str = typer.Option(..., envvar="SNOWFLAKE_ACCOUNT"),
    user: str = typer.Option(..., envvar="SNOWFLAKE_USER"),
    password: str = typer.Option(..., envvar="SNOWFLAKE_PASSWORD"),
    warehouse: str = typer.Option(..., envvar="SNOWFLAKE_WAREHOUSE"),
    role: str | None = typer.Option(None, envvar="SNOWFLAKE_ROLE"),
) -> None:
    crew = build_crew()
    config = SnowflakeConfig(
        account=account,
        user=user,
        password=password,
        warehouse=warehouse,
        database=database,
        schema=schema,
        role=role,
    )
    table_config = TableConfig(database=database, schema=schema, table=table)
    output_config = OutputConfig(output_dir=output_dir, write_csv=write_csv)

    crew.kickoff(
        inputs={
            "snowflake": config,
            "table": table_config,
            "output": output_config,
            "run": lambda: run_hilo_eda(config, table_config, output_config),
        }
    )


if __name__ == "__main__":
    app()
