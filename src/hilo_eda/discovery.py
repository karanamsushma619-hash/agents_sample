from __future__ import annotations

from hilo_eda.config import TableConfig
from hilo_eda.models import ColumnInfo
from hilo_eda.sql_safety import quote_ident
from hilo_eda.snowflake import SnowflakeClient


def fetch_columns(client: SnowflakeClient, table: TableConfig) -> list[ColumnInfo]:
    sql = (
        "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE "
        "FROM INFORMATION_SCHEMA.COLUMNS "
        f"WHERE TABLE_SCHEMA = '{table.schema}' "
        f"AND TABLE_NAME = '{table.table}' "
        "ORDER BY ORDINAL_POSITION"
    )
    rows = client.execute_query(sql)
    return [
        ColumnInfo(
            name=row["COLUMN_NAME"],
            data_type=row["DATA_TYPE"],
            is_nullable=row["IS_NULLABLE"] == "YES",
        )
        for row in rows
    ]


def table_exists(client: SnowflakeClient, table: TableConfig) -> bool:
    sql = (
        "SELECT COUNT(*) AS COUNT "
        "FROM INFORMATION_SCHEMA.TABLES "
        f"WHERE TABLE_SCHEMA = '{table.schema}' "
        f"AND TABLE_NAME = '{table.table}'"
    )
    rows = client.execute_query(sql)
    return rows[0]["COUNT"] > 0


def column_in_table(columns: list[ColumnInfo], name: str) -> bool:
    normalized = name.lower()
    return any(col.name.lower() == normalized for col in columns)


def quoted_columns(columns: list[ColumnInfo]) -> list[str]:
    return [quote_ident(column.name) for column in columns]
