"""Tests for in-level objects: crates, keys, lock doors and treasure chests."""

from codequest import rewards
from codequest.engine import Level, run_code
from codequest.progress import Progress


def make_level(rows: list[str], need_chests: int = 0) -> Level:
    return Level(
        id="T-1",
        title="Thử",
        story="",
        goal="",
        rows=rows,
        starter="",
        hints=[],
        need_chests=need_chests,
    )


CRATE_ROOM = make_level(["#######", "#@.O.E#", "#######"])
GEM_CRATE_ROOM = make_level(["#######", "#@Q..E#", "#######"])
KEY_ROOM = make_level(["#######", "#@kL.E#", "#######"])
LOCKED_ROOM = make_level(["######", "#@L.E#", "######"])
CHEST_ROOM = make_level(["######", "#.C..#", "#@..E#", "######"], need_chests=1)


def event_kinds(result) -> list[str]:
    return [event["type"] for event in result.events]


def test_crate_blocks_until_attacked():
    blocked = run_code(CRATE_ROOM, "hero.move_right(4)\n")
    assert not blocked.won

    result = run_code(CRATE_ROOM, 'hero.move_right()\nhero.attack("right")\nhero.move_right(3)\n')
    assert result.won
    assert "box_break" in event_kinds(result)


def test_crate_with_gem_reveals_gem():
    result = run_code(GEM_CRATE_ROOM, 'hero.attack("right")\nhero.move_right(4)\nprint(hero.gems_collected)\n')
    assert result.won
    assert "gem_reveal" in event_kinds(result)


def test_look_reports_objects():
    result = run_code(KEY_ROOM, 'print(hero.look("right"))\nhero.move_right()\nprint(hero.look("right"))\n')
    printed = [event["text"] for event in result.events if event["type"] == "print"]
    assert printed == ["key", "lock"]


def test_unlock_needs_key():
    without_key = run_code(LOCKED_ROOM, 'hero.unlock("right")\n')
    assert not without_key.won
    assert "ValueError" in without_key.message or "chìa" in without_key.message

    result = run_code(KEY_ROOM, 'hero.move_right()\nprint(hero.keys)\nhero.unlock("right")\nhero.move_right(3)\n')
    assert result.won
    assert {"key", "unlock"} <= set(event_kinds(result))


def test_chest_counts_and_is_required():
    skipped = run_code(CHEST_ROOM, "hero.move_right(3)\n")
    assert not skipped.won
    assert "rương" in skipped.message

    result = run_code(CHEST_ROOM, 'hero.move_right()\nhero.open_chest("up")\nhero.move_right(2)\n')
    assert result.won
    assert result.chests_opened == 1


def test_find_objects_lists_coordinates():
    result = run_code(CRATE_ROOM, 'print(hero.find_objects("box"))\n')
    printed = [event["text"] for event in result.events if event["type"] == "print"]
    assert printed == ["[{'x': 3, 'y': 1}]"]


def test_loot_coins_paid_once(tmp_path):
    progress = Progress(tmp_path / "progress.json")
    first = rewards.apply_win(progress, CHEST_ROOM, [CHEST_ROOM], 99, (True, False, False), chests_opened=1)
    assert first.loot_coins == rewards.LOOT_COINS
    again = rewards.apply_win(progress, CHEST_ROOM, [CHEST_ROOM], 99, (True, False, False), chests_opened=1)
    assert again.loot_coins == 0
