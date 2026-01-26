# Architecture

## Shared Core

The core lives in `src/hilo_eda/` and provides:

- Snowflake connector (read-only).
- Schema discovery through `INFORMATION_SCHEMA`.
- Profiling and behavioral inference.
- Human-in-the-loop checkpoints.
- Report and CSV output.

## Framework Adapters

Adapters in `apps/` wrap the core with each framework's orchestration model.
Each adapter passes through to the shared core without duplicating logic.
