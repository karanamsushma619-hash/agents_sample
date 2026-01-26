from __future__ import annotations

from typing import Any

from hilo_eda.config import TableConfig
from hilo_eda.models import ColumnInfo, ColumnProfile, TableProfile
from hilo_eda.sql_safety import qualify_table, quote_ident
from hilo_eda.snowflake import SnowflakeClient

NUMERIC_TYPES = {"NUMBER", "INT", "INTEGER", "FLOAT", "DOUBLE", "DECIMAL"}
DATE_TYPES = {"DATE", "TIMESTAMP", "TIMESTAMP_NTZ", "TIMESTAMP_LTZ", "TIMESTAMP_TZ"}


def _is_numeric(data_type: str) -> bool:
    upper = data_type.upper()
    return any(token in upper for token in NUMERIC_TYPES)


def _is_date(data_type: str) -> bool:
    upper = data_type.upper()
    return any(token in upper for token in DATE_TYPES)


def profile_table(
    client: SnowflakeClient,
    table: TableConfig,
    columns: list[ColumnInfo],
    sample_limit: int = 50,
    top_k: int = 5,
) -> tuple[TableProfile, list[dict[str, Any]]]:
    table_fqn = qualify_table(table.database, table.schema, table.table)
    row_count_sql = f"SELECT COUNT(*) AS ROW_COUNT FROM {table_fqn}"
    row_count = client.execute_query(row_count_sql)[0]["ROW_COUNT"]

    profiles: list[ColumnProfile] = []
    for column in columns:
        col_ident = quote_ident(column.name)
        base_sql = (
            "SELECT COUNT(*) AS TOTAL_COUNT, "
            f"COUNT({col_ident}) AS NON_NULL_COUNT, "
            f"COUNT(DISTINCT {col_ident}) AS DISTINCT_COUNT "
            f"FROM {table_fqn}"
        )
        base_row = client.execute_query(base_sql)[0]
        total_count = int(base_row["TOTAL_COUNT"])
        non_null_count = int(base_row["NON_NULL_COUNT"])
        null_count = total_count - non_null_count
        distinct_count = int(base_row["DISTINCT_COUNT"])

        min_value = None
        max_value = None
        if _is_numeric(column.data_type) or _is_date(column.data_type):
            min_max_sql = (
                f"SELECT MIN({col_ident}) AS MIN_VALUE, "
                f"MAX({col_ident}) AS MAX_VALUE "
                f"FROM {table_fqn}"
            )
            min_max_row = client.execute_query(min_max_sql)[0]
            min_value = min_max_row["MIN_VALUE"]
            max_value = min_max_row["MAX_VALUE"]

        top_values_sql = (
            f"SELECT {col_ident} AS VALUE, COUNT(*) AS COUNT "
            f"FROM {table_fqn} "
            f"GROUP BY {col_ident} "
            f"ORDER BY COUNT DESC NULLS LAST "
            f"LIMIT {top_k}"
        )
        top_rows = client.execute_query(top_values_sql)
        top_values = [(row["VALUE"], int(row["COUNT"])) for row in top_rows]

        profiles.append(
            ColumnProfile(
                name=column.name,
                data_type=column.data_type,
                total_count=total_count,
                null_count=null_count,
                distinct_count=distinct_count,
                min_value=min_value,
                max_value=max_value,
                top_values=top_values,
            )
        )

    sample_sql = f"SELECT * FROM {table_fqn} LIMIT {sample_limit}"
    sample_rows = client.execute_query(sample_sql)

    table_profile = TableProfile(
        table_fqn=table_fqn, row_count=row_count, columns=profiles
    )
    return table_profile, sample_rows
