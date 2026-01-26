from __future__ import annotations

from pathlib import Path

import typer
from claude_agent_sdk import Agent

from hilo_eda.config import OutputConfig, SnowflakeConfig, TableConfig
from hilo_eda.orchestrator import run_hilo_eda

app = typer.Typer(add_completion=False)


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
    agent = Agent(name="hilo-eda", system_prompt="Run HILO EDA workflows.")
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

    agent.run(lambda: run_hilo_eda(config, table_config, output_config))


if __name__ == "__main__":
    app()
