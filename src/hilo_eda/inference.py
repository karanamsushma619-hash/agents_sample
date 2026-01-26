from __future__ import annotations

from hilo_eda.models import ColumnProfile, InferenceResult


def infer_behavior(profile: ColumnProfile, row_count: int) -> InferenceResult:
    null_pct = profile.null_pct
    distinct = profile.distinct_count
    dtype = profile.data_type.upper()

    if "VARIANT" in dtype or "OBJECT" in dtype:
        return InferenceResult(profile.name, "semi-structured", 0.8, "VARIANT type")

    if row_count == 0:
        return InferenceResult(profile.name, "empty", 0.5, "Empty table")

    if distinct == 1:
        return InferenceResult(profile.name, "constant", 0.9, "Single distinct")

    if null_pct >= 0.9:
        return InferenceResult(profile.name, "sparse", 0.8, "High null rate")

    if dtype in {"BOOLEAN"}:
        return InferenceResult(profile.name, "boolean-like", 0.9, "Boolean type")

    if "TEXT" in dtype or "CHAR" in dtype or "STRING" in dtype:
        if distinct <= 20:
            return InferenceResult(
                profile.name, "low-cardinality categorical", 0.7, "Low distinct"
            )
        return InferenceResult(profile.name, "text", 0.6, "Text type")

    if "DATE" in dtype or "TIMESTAMP" in dtype:
        return InferenceResult(profile.name, "datetime", 0.85, "Date/time type")

    if "NUMBER" in dtype or "INT" in dtype or "FLOAT" in dtype:
        if distinct <= 20:
            return InferenceResult(
                profile.name, "numeric discrete", 0.7, "Low distinct"
            )
        return InferenceResult(profile.name, "numeric continuous", 0.7, "Numeric type")

    if distinct <= 20:
        return InferenceResult(
            profile.name, "low-cardinality categorical", 0.6, "Low distinct"
        )

    if distinct / max(row_count, 1) > 0.9:
        return InferenceResult(
            profile.name, "high-cardinality categorical", 0.6, "High distinct ratio"
        )

    return InferenceResult(profile.name, "unknown", 0.4, "Fallback")


def infer_all(profiles: list[ColumnProfile], row_count: int) -> list[InferenceResult]:
    return [infer_behavior(profile, row_count) for profile in profiles]
