"""Smoke tests for the pygame front-end (runs headless with dummy video/audio drivers)."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

from codequest import game, rewards
from codequest.heroes import HEROES, HEROES_BY_NUMBER
from codequest.levels import WORLDS
from codequest.themes import THEMES

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
    app.store._buy(rewards.ITEMS_BY_ID["skin14"])
    assert "skin14" in app.progress.owned and app.progress.skin == "skin14"
    app.store._equip("skin1")
    assert app.progress.skin == "skin1"
    app.store._buy(rewards.ITEMS_BY_ID["shield"])
    assert "shield" in app.progress.owned
    assert app.progress.coins == 500 - 200 - 250
    app.store._buy(rewards.ITEMS_BY_ID["heart1"])
    assert "heart1" not in app.progress.owned
    assert app.progress.coins == 50
    app.go_menu()
    app.draw()


def test_sound_toggle_is_saved(app):
    app.toggle_sound()
    assert app.progress.muted and app.sound.muted


def test_first_launch_opens_hero_picker(app):
    assert app.scene == "heroes"
    app.draw()
    app.hero_view.choose(HEROES_BY_NUMBER[7])
    assert app.progress.skin == "skin7"
    app.hero_view.choose(HEROES_BY_NUMBER[15])
    assert "skin15" not in app.progress.owned and app.progress.skin == "skin7"
    app.hero_view.finish()
    assert app.scene == "menu" and app.progress.hero_picked


def test_every_hero_and_theme_renders(app):
    for hero in HEROES:
        frames = app.assets.hero_skin(hero.number)
        assert all(frames[state] for state in ("idle", "run", "hit", "jump"))
    for theme in THEMES:
        floor, wall = app.assets.theme_tiles(theme)
        assert floor.get_size() == wall.get_size()
