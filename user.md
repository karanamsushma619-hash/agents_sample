You are Claude Code (VS Code extension) acting as a senior Python architect and agentic-AI engineer.

IMPORTANT: DO NOT START CODING YET.
You must FIRST think through the design and then ask me clarifying questions.
Only after I answer, you will start implementing the repository.

============================================================
PROJECT (Version 2): Snowflake Human-in-the-Loop Agentic EDA
============================================================

Goal:
Build a Human-In-the-Loop (HILO) Agentic EDA system for Snowflake with READ-ONLY access, where the human may know the table name (DB.SCHEMA.TABLE) but does NOT know what the columns mean. The system must discover metadata, profile columns, form hypotheses about column meaning/roles, pause to ask the human clarification questions (mandatory), and then adapt the analysis plan based on the human answers. Output a structured Markdown report (and optional CSV exports).

Hard constraints:
- Snowflake READ-ONLY only. No DDL/DML. No Snowflake Cortex / AI features.
- Python 3.11+.
- Strict PEP 8 enforced using Black + Ruff (line length 88), with pyproject.toml config.
- Must include explicit tools + tool calling.
- Must include MCP server (Model Context Protocol) that exposes the Snowflake tools over MCP.
- Claude Agent SDK app must connect to the MCP server and call those tools via MCP.
- Never hallucinate table/column names; always validate via INFORMATION_SCHEMA.
- Always fully qualify DB.SCHEMA.TABLE.
- Sampling first; safe SQL only; guardrails + query risk scoring.
- Human-in-the-loop checkpoint is mandatory: do not run heavy aggregations until user confirms options.

This repo must contain:
- Shared core library in src/hilo_eda/ (business logic)
- MCP server in mcp_server/ that exposes Snowflake tools over MCP
- Claude Agent SDK client app in apps/claude_agent_sdk/ that:
  - uses tool calling (MCP tools) for Snowflake operations
  - uses a local “ask_user()” capability (CLI) for human checkpoint interrupts
- Optional: stubs or placeholders for LangChain/LangGraph/CrewAI apps can exist,
  but primary focus is Claude Agent SDK + MCP + shared core. (If time/complexity: implement the other apps too.)

============================================================
HUMAN-IN-THE-LOOP BEHAVIOR (MANDATORY)
============================================================

The workflow MUST include an interrupt after profiling:
1) Discover & profile table
2) Present “table card” and column behavior/role hypotheses
3) Ask human questions with explicit A/B/C options:
   - Which column is identifier (if any)?
   - Which column is time (if any)?
   - Which column indicates outcome/status (if any)?
   - Which columns to ignore or mark as sensitive?
   - Which EDA direction: (A) quality/missingness (B) distributions (C) relationships (D) outliers (E) time trends if time exists
4) Only after user answers, build an EDA plan and execute safe queries via MCP tool calls.
5) Output report with: assumptions + SQL executed + results + next-step options.

IMPORTANT FALLBACK: ROLELESS TABLES
If no clear id/timestamp/status/measure columns exist:
- Do NOT fail or force roles.
- Switch to behavior-based profiling:
  constant/near-constant, low-cardinality categorical, high-cardinality categorical,
  numeric continuous, numeric discrete, boolean-like, text/freeform, sparse, semi-structured (VARIANT/OBJECT/ARRAY).
- Rank “most informative” columns and show sample values.
- Ask human to label columns where possible and pick an EDA path.
- Provide EDA paths that do not require id/time/status:
  - missingness + duplicates-on-sample
  - distributions
  - relationships (correlation/crosstab on samples)
  - outliers/rare categories
- If VARIANT exists: extract top-level keys from samples and ask which keys to flatten.

============================================================
TOOLS + MCP REQUIREMENT (Version 2)
============================================================

We must have explicit tools and tool-calling.

Shared tool interface (core “capabilities”):
- snowflake_get_table_columns(table_fqn) -> column metadata
- snowflake_sample_rows(table_fqn, limit=50) -> sample rows
- snowflake_profile_table(table_fqn, sample_limit=2000) -> profiling stats (JSON)
- snowflake_run_sql_readonly(sql, max_rows=200) -> rows (guarded)

These 4 Snowflake-facing tools MUST be exposed by an MCP server.

Local (non-MCP) human tools:
- ask_user(prompt, options=None) -> chosen option / text
- confirm(prompt) -> bool

IMPORTANT: MCP server should NOT block on human input; human prompting happens in the CLI host app (apps/claude_agent_sdk).

Transport:
- Default: MCP over stdio (local process). Provide a script to run the MCP server as a subprocess from the client app.

============================================================
SECURITY + COST GUARDRAILS
============================================================

Implement in core:
- safe_query_guard(sql): reject CREATE/ALTER/DROP/INSERT/UPDATE/DELETE/MERGE/COPY/GRANT/REVOKE/TRUNCATE and other write ops.
- Enforce max_rows on queries.
- Sampling by LIMIT 50 for preview; profiling uses sampled subset.
- Default time filter: if time column is confirmed, default to last 30 days unless user overrides.
- Query risk scorer: flag queries with no filters / large scans / joins; require confirm() before running.
- Never select * in heavy queries; only necessary columns.

============================================================
REPO STRUCTURE (REQUIRED)
============================================================

Repository name: snowflake-hilo-eda-agents

Files/folders (minimum):
- CLAUDE.md (instructions)
- pyproject.toml (Black + Ruff config)
- requirements.txt (or pyproject deps)
- Makefile (format/lint/test/check)
- .editorconfig
- README.md
- docs/SPEC.md
- docs/DECISIONS.md
- src/hilo_eda/
  - __init__.py
  - config.py
  - snowflake_client.py
  - metadata.py
  - profiler.py
  - inference.py
  - questions.py
  - planner.py
  - sql_builder.py
  - executor.py
  - memory.py
  - report.py
  - utils.py
- mcp_server/
  - README.md
  - server.py (MCP tool server)
  - tool_impl.py (wraps src/hilo_eda/)
- apps/claude_agent_sdk/
  - main.py (CLI)
  - agent.py (agent setup + tool calling)
  - mcp_client.py (connect/launch MCP server process; list/call tools)
  - prompts.py (system prompt + templates)
- scripts/connection_test.py
- tests/ (pytest)
  - test_safe_query_guard.py
  - test_inference.py
  - test_planner.py
- reports/ (generated)

PEP 8:
- Use type hints everywhere
- Docstrings for public functions/classes
- No wildcard imports
- Prefer pathlib

============================================================
PHASE 1: THINK FIRST (NO CODING)
============================================================

Before creating any files:
1) Summarize the architecture (core vs MCP vs Claude Agent app).
2) Propose the key state machine / stages and where the human interrupt happens.
3) Specify the tool schemas (inputs/outputs) for MCP.
4) Call out any implementation risks (library availability, MCP server library choice).
5) Propose a minimal v2 scope that is still “complete and runnable”.

Do NOT write code or create files in Phase 1.

============================================================
PHASE 2: ASK ME CLARIFYING QUESTIONS (MANDATORY)
============================================================

Ask me questions if ANY doubt exists. At minimum ask:

1) Do you want ONLY Claude Agent SDK + MCP for v2, or also implement LangChain/LangGraph/CrewAI in the same repo now?
2) MCP transport: stdio only (recommended) or also HTTP/SSE?
3) CLI preference: argparse OR Typer + Rich?
4) Output: Markdown only, or Markdown + CSV exports?
5) Persist session memory across runs (JSON/SQLite), or per-run only?
6) For large tables: should we ALWAYS default to last 30 days when a time column exists (yes/no)?
7) Do you want “table unknown” mode (discover tables) or table-known-only for v2?
8) What Snowflake auth will be used (password env vars ok) — any SSO/OAuth not supported?

STOP after asking questions. Do not code yet.

============================================================
PHASE 3: IMPLEMENTATION (ONLY AFTER I ANSWER)
============================================================

After I answer, you will:
- Create the full repo with all files above
- Ensure code runs end-to-end:
  - Start MCP server (stdio)
  - Claude Agent SDK client connects and calls MCP tools
  - Human-in-the-loop interrupt works in CLI
  - Report generated to reports/
- Add Makefile + pyproject + tests
- Ensure PEP 8 via Black + Ruff configs
- Document decisions

Now begin Phase 1 and then ask me Phase 2 questions. NO CODE YET.
