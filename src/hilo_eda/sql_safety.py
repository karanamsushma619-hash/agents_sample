from __future__ import annotations

import re

FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|MERGE|CALL|PUT|GET|COPY)\b",
    re.IGNORECASE,
)


class UnsafeSQLError(ValueError):
    pass


def ensure_select_only(sql: str) -> None:
    stripped = sql.strip()
    if ";" in stripped:
        raise UnsafeSQLError("Multiple statements are not allowed.")
    if FORBIDDEN_KEYWORDS.search(stripped):
        raise UnsafeSQLError("Only SELECT statements are allowed.")
    if not re.match(r"^(SELECT|WITH)\b", stripped, re.IGNORECASE):
        raise UnsafeSQLError("Only SELECT or WITH statements are allowed.")


def quote_ident(identifier: str) -> str:
    if identifier == "":
        raise ValueError("Identifier cannot be empty.")
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'


def qualify_table(database: str, schema: str, table: str) -> str:
    return ".".join(
        [quote_ident(database), quote_ident(schema), quote_ident(table)]
    )
