"""Smoke tests for the pygame front-end (runs headless with dummy video/audio drivers)."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

from codequest import game, rewards
from codequest.levels import WORLDS

from .conftest import requires_solutions, solution_for


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(game, "PROGRESS_FILE", tmp_path / "progress.json")
    monkeypatch.setattr(game, "backup_dir", lambda: None)
    return game.App()


def play(app, level, code, max_frames=2400):
    app.open_level(level)
    app.show_theory = False
    app.editor.set_text(code)
    app.run()
    for _ in range(max_frames):
        app.update(1 / 30)
        if app.playback.finished:
            break
    app.draw()


@requires_solutions
def test_winning_a_world_gives_stars_coins_and_chest(app):
    world = WORLDS[0]
    for level in world.levels:
        play(app, level, solution_for(level.id))
        assert app.show_win
        assert app.win_summary.stars == (True, True, True)
    assert app.progress.chests == {world.number}
    assert app.win_summary.chest_world == world.number
    expected = 3 * rewards.STAR_COINS * len(world.levels) + rewards.WORLD_CHEST_COINS
    assert app.progress.coins == expected


def test_failed_run_gives_nothing(app):
    level = WORLDS[0].levels[0]
    play(app, level, level.starter)
    assert not app.show_win
    assert app.progress.coins == 0 and not app.progress.stars


def test_store_buy_and_equip(app):
    app.progress.coins = 500
    app.open_store()
    app.draw()
    app.store._buy(rewards.ITEMS_BY_ID["skin3"])
    assert "skin3" in app.progress.owned and app.progress.skin == "skin3"
    app.store._equip("skin1")
    assert app.progress.skin == "skin1"
    app.store._buy(rewards.ITEMS_BY_ID["shield"])
    assert "shield" in app.progress.owned
    assert app.progress.coins == 500 - 220 - 250
    app.store._buy(rewards.ITEMS_BY_ID["heart1"])
    assert "heart1" not in app.progress.owned
    assert app.progress.coins == 30
    app.go_menu()
    app.draw()


def test_sound_toggle_is_saved(app):
    app.toggle_sound()
    assert app.progress.muted and app.sound.muted
