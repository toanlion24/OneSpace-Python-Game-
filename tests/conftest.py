import pytest

from codequest.selftest import load_solutions

SOLUTIONS = load_solutions()

requires_solutions = pytest.mark.skipif(
    SOLUTIONS is None,
    reason="Lời giải mẫu (solutions/level_solutions.py) chỉ có trên máy giáo viên.",
)


def solution_for(level_id: str) -> str:
    assert SOLUTIONS is not None
    return SOLUTIONS[level_id]
