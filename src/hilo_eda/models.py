from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ColumnInfo:
    name: str
    data_type: str
    is_nullable: bool


@dataclass(frozen=True)
class ColumnProfile:
    name: str
    data_type: str
    total_count: int
    null_count: int
    distinct_count: int
    min_value: Any | None
    max_value: Any | None
    top_values: list[tuple[Any, int]] = field(default_factory=list)

    @property
    def null_pct(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.null_count / self.total_count


@dataclass(frozen=True)
class TableProfile:
    table_fqn: str
    row_count: int
    columns: list[ColumnProfile]


@dataclass(frozen=True)
class InferenceResult:
    column: str
    behavior_class: str
    confidence: float
    rationale: str


@dataclass(frozen=True)
class HumanSelections:
    identifier: str | None
    time_column: str | None
    status_column: str | None
    ignore_columns: list[str]
    eda_direction: str


@dataclass(frozen=True)
class EDAQueryResult:
    title: str
    sql: str
    rows: list[dict[str, Any]]
