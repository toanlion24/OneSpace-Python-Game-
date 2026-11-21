import ast

import pytest

from codequest.levels import all_levels
from codequest.theory import THEORY

from .conftest import SOLUTIONS

LEVELS = all_levels()


@pytest.mark.parametrize("level", LEVELS, ids=[level.id for level in LEVELS])
def test_every_level_has_theory(level):
    theory = THEORY[level.id]
    assert theory.concept
    assert theory.example


@pytest.mark.parametrize("level", LEVELS, ids=[level.id for level in LEVELS])
def test_starter_notes_match_starter_code(level):
    starter_lines = level.starter.split("\n")
    for code_line, _note in THEORY[level.id].starter_notes:
        assert code_line in starter_lines, f"{level.id}: '{code_line}' không có trong code ban đầu"


@pytest.mark.parametrize("level", LEVELS, ids=[level.id for level in LEVELS])
def test_example_is_valid_python_and_not_the_solution(level):
    example = "\n".join(code for code, _note in THEORY[level.id].example)
    ast.parse(example)
    if SOLUTIONS is not None:
        assert example.strip() != SOLUTIONS[level.id].strip()
