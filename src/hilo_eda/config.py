from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SnowflakeConfig:
    account: str
    user: str
    password: str
    warehouse: str
    database: str
    schema: str
    role: str | None = None


@dataclass(frozen=True)
class TableConfig:
    database: str
    schema: str
    table: str


@dataclass(frozen=True)
class OutputConfig:
    output_dir: Path
    write_csv: bool = True
