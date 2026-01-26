from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import snowflake.connector

from hilo_eda.config import SnowflakeConfig
from hilo_eda.sql_safety import ensure_select_only


@dataclass
class SnowflakeClient:
    config: SnowflakeConfig

    def __post_init__(self) -> None:
        self._connection = snowflake.connector.connect(
            account=self.config.account,
            user=self.config.user,
            password=self.config.password,
            warehouse=self.config.warehouse,
            database=self.config.database,
            schema=self.config.schema,
            role=self.config.role,
        )

    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        ensure_select_only(sql)
        with self._connection.cursor(snowflake.connector.DictCursor) as cursor:
            cursor.execute(sql)
            return list(cursor.fetchall())

    def close(self) -> None:
        self._connection.close()
