import pytest

from hilo_eda.sql_safety import UnsafeSQLError, ensure_select_only


def test_select_allowed() -> None:
    ensure_select_only("SELECT 1")
    ensure_select_only("WITH t AS (SELECT 1) SELECT * FROM t")


def test_block_non_select() -> None:
    with pytest.raises(UnsafeSQLError):
        ensure_select_only("DELETE FROM table")
