from __future__ import annotations

import csv
from pathlib import Path

from hilo_eda.models import EDAQueryResult, HumanSelections, InferenceResult, TableProfile


def write_markdown_report(
    output_path: Path,
    table_profile: TableProfile,
    inferences: list[InferenceResult],
    human: HumanSelections,
    executed_queries: list[EDAQueryResult],
) -> None:
    lines: list[str] = []
    lines.append(f"# EDA Report: {table_profile.table_fqn}\n")
    lines.append("## Assumptions\n")
    lines.append(f"- Identifier: {human.identifier}\n")
    lines.append(f"- Time column: {human.time_column}\n")
    lines.append(f"- Status column: {human.status_column}\n")
    lines.append(f"- Ignored columns: {', '.join(human.ignore_columns) or 'None'}\n")
    lines.append(f"- EDA direction: {human.eda_direction}\n")

    lines.append("## Column Profiles\n")
    for column in table_profile.columns:
        lines.append(
            f"- **{column.name}** ({column.data_type}): "
            f"null % {column.null_pct:.2%}, distinct {column.distinct_count}\n"
        )

    lines.append("\n## Behavioral Inference\n")
    for inference in inferences:
        lines.append(
            f"- **{inference.column}**: {inference.behavior_class} "
            f"(confidence {inference.confidence:.2f}) — {inference.rationale}\n"
        )

    lines.append("\n## SQL Executed\n")
    for result in executed_queries:
        lines.append(f"### {result.title}\n")
        lines.append("```sql\n")
        lines.append(result.sql)
        lines.append("\n```\n")
        lines.append(f"Rows returned: {len(result.rows)}\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_csv_outputs(
    output_dir: Path,
    table_profile: TableProfile,
    sample_rows: list[dict[str, object]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    profile_path = output_dir / "column_profiles.csv"
    with profile_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "name",
                "data_type",
                "total_count",
                "null_count",
                "null_pct",
                "distinct_count",
                "min_value",
                "max_value",
            ],
        )
        writer.writeheader()
        for profile in table_profile.columns:
            writer.writerow(
                {
                    "name": profile.name,
                    "data_type": profile.data_type,
                    "total_count": profile.total_count,
                    "null_count": profile.null_count,
                    "null_pct": f"{profile.null_pct:.4f}",
                    "distinct_count": profile.distinct_count,
                    "min_value": profile.min_value,
                    "max_value": profile.max_value,
                }
            )

    if sample_rows:
        sample_path = output_dir / "sample_rows.csv"
        fieldnames = list(sample_rows[0].keys())
        with sample_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sample_rows)
