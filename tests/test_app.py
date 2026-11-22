"""Smoke tests for the pygame front-end (runs headless with dummy video/audio drivers)."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
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
    # Không tổng hợp nhạc trong test giao diện (tốn vài giây, đã có test_music riêng).
    monkeypatch.setattr(game.MusicPlayer, "_start_worker", lambda self: None)
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


def test_hidden_map_is_replayed_after_main_map(app):
    level = next(lv for lv in app.levels if lv.id == "4-3")
    play(app, level, "count = 0\nwhile count < 12:\n    hero.move_right()\n    count += 1\n")
    assert app.hidden_shown == 1
    for _ in range(2400):
        app.update(1 / 30)
        if app.playback.finished:
            break
    app.draw()
    assert not app.show_win
    app.run()
    assert app.hidden_shown == 0


def test_music_panel_volume_and_track_are_saved(app):
    app.go_menu()
    app.music_panel.open()
    app.draw()
    app.set_music_volume(70)
    app.set_sfx_volume(30)
    app.music_panel._choose(7)
    assert app.music.wanted == 7 and app.music.volume_percent == 70
    app.music_panel.close()
    reopened = game.Progress(app.progress.main_file, None)
    assert (reopened.music_volume, reopened.sfx_volume, reopened.music_track) == (70, 30, 7)
    app.open_level(WORLDS[3].levels[0])
    assert app.music.wanted == 7


def test_music_slider_and_auto_track(app):
    app.music_panel.open()
    slider = app.music_panel.music_slider
    down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(slider.rect.x, slider.rect.centery))
    app.handle_event(down)
    assert app.progress.music_volume == 0 and not app.music.enabled
    app.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(slider.rect.right, slider.rect.centery), rel=(0, 0),
                                        buttons=(1, 0, 0)))
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(slider.rect.right, slider.rect.centery)))
    assert app.progress.music_volume == 100
    app.music_panel._choose(-1)
    app.music_panel.close()
    app.open_level(WORLDS[3].levels[0])
    assert app.music.wanted == game.track_for_world(WORLDS[3].number)
