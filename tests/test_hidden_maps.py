"""Bản đồ kiểm tra ẩn: code gõ cứng phải thua, code tổng quát phải thắng."""

from codequest.engine import hidden_levels, run_code
from codequest.levels import all_levels
from codequest.variants import VARIANTS

LEVELS = {level.id: level for level in all_levels()}


def test_variants_refer_to_real_levels():
    assert VARIANTS
    for level_id, entries in VARIANTS.items():
        assert level_id in LEVELS
        assert 1 <= len(entries) <= 2
        assert len(hidden_levels(LEVELS[level_id])) == len(entries)


def test_hard_coded_answer_fails_on_changed_data():
    code = "part = int(scroll[3:5])\nhero.move_right(2)\nhero.enter_code(42)\nhero.move_right(4)\n"
    result = run_code(LEVELS["7-1"], code)
    assert not result.won
    assert result.hidden_failure is not None
    assert "scroll" in result.hidden_failure.changed_data
    assert "kiểm tra ẩn" in result.message


def test_counted_steps_fail_on_stretched_map():
    code = "count = 0\nwhile count < 12:\n    hero.move_right()\n    count += 1\n"
    assert run_code(LEVELS["4-3"], code, check_hidden=False).won
    result = run_code(LEVELS["4-3"], code)
    assert not result.won and result.hidden_failure.index == 1


def test_general_code_passes_hidden_maps():
    code = 'while hero.look("right") != "exit":\n    hero.move_right()\nhero.move_right()\n'
    result = run_code(LEVELS["4-3"], code)
    assert result.won and result.hidden_passed >= 1


def test_player_code_cannot_change_level_data():
    code = "scroll = scroll.upper()\nprint(scroll)\n"
    run_code(LEVELS["7-1"], code)
    assert LEVELS["7-1"].extra_globals["scroll"] == "abc42xyz"
