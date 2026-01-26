from hilo_eda.inference import infer_behavior
from hilo_eda.models import ColumnProfile


def test_infer_numeric_continuous() -> None:
    profile = ColumnProfile(
        name="amount",
        data_type="NUMBER",
        total_count=100,
        null_count=0,
        distinct_count=80,
        min_value=1,
        max_value=100,
        top_values=[],
    )
    result = infer_behavior(profile, row_count=100)
    assert result.behavior_class == "numeric continuous"


def test_infer_constant() -> None:
    profile = ColumnProfile(
        name="status",
        data_type="TEXT",
        total_count=50,
        null_count=0,
        distinct_count=1,
        min_value=None,
        max_value=None,
        top_values=[("OK", 50)],
    )
    result = infer_behavior(profile, row_count=50)
    assert result.behavior_class == "constant"
