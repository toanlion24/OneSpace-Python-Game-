import pytest

from codequest.engine import World, run_code
from codequest.levels import all_levels

from .conftest import SOLUTIONS, requires_solutions, solution_for

LEVELS = all_levels()


@requires_solutions
@pytest.mark.parametrize("level", LEVELS, ids=[level.id for level in LEVELS])
def test_solution_wins(level):
    result = run_code(level, solution_for(level.id))
    assert result.won, result.message


@pytest.mark.parametrize("level", LEVELS, ids=[level.id for level in LEVELS])
def test_starter_does_not_win(level):
    result = run_code(level, level.starter)
    assert not result.won


@pytest.mark.parametrize("level", LEVELS, ids=[level.id for level in LEVELS])
def test_map_is_rectangular_with_hero_and_exit(level):
    widths = {len(row) for row in level.rows}
    assert len(widths) == 1
    joined = "".join(level.rows)
    assert joined.count("@") == 1
    assert joined.count("E") == 1
    World(level)


@requires_solutions
@pytest.mark.parametrize("level", LEVELS, ids=[level.id for level in LEVELS])
def test_hints_do_not_reveal_solution_lines(level):
    solution_lines = {line.strip() for line in solution_for(level.id).split("\n") if len(line.strip()) > 12}
    for hint in level.hints:
        for line in solution_lines:
            assert line not in hint, f"{level.id}: gợi ý lộ dòng lời giải '{line}'"


def test_infinite_loop_is_stopped():
    level = LEVELS[0]
    result = run_code(level, "while True:\n    pass\n")
    assert not result.won
    assert "quá lâu" in result.message


def test_syntax_error_reports_line():
    result = run_code(LEVELS[0], "hero.move_right(\n")
    assert not result.won
    assert result.error_line == 1


@requires_solutions
def test_every_level_has_a_solution():
    assert set(SOLUTIONS) == {level.id for level in LEVELS}


def test_levels_do_not_ship_solutions():
    from pathlib import Path

    import codequest.levels as levels_module

    source = Path(levels_module.__file__).read_text(encoding="utf-8")
    assert "solution=" not in source


def test_import_is_blocked():
    result = run_code(LEVELS[0], "import os\n")
    assert not result.won
