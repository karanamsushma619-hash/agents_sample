# HILO EDA for Snowflake

Human-in-the-loop agentic EDA for Snowflake with a shared core and framework
adapters for Claude Agent SDK, LangChain, LangGraph, and CrewAI.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Run the Typer CLI:

```bash
hilo-eda --help
```

## Design Principles

- Read-only Snowflake access with SELECT-only safeguards.
- INFORMATION_SCHEMA validation for all tables/columns.
- Mandatory human checkpoints after profiling.
- Safe sampling with strict row limits.
- Shared core for profiling/inference/reporting.
