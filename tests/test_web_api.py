import io
import json
import urllib.error
import urllib.request
import wave

import numpy as np
import pytest

from codequest import web_api
from codequest.web_api import LEVELS_BY_ID, WebApi
from codequest.web_app import TOKEN_HEADER, start_server


@pytest.fixture
def api(tmp_path):
    return WebApi(tmp_path / "progress.json")


def test_bootstrap_lists_every_world_and_level(api):
    data = api.bootstrap()
    level_count = sum(len(world["levels"]) for world in data["worlds"])
    assert level_count == len(LEVELS_BY_ID)
    assert data["continueLevel"] == "1-1"
    assert data["player"]["coins"] == 0


def test_level_payload_has_theory_and_map(api):
    data = api.level("4-1")
    assert data["rows"] and data["code"] == data["starter"]
    assert data["theory"]["lesson"]["walkthrough"]
    assert data["theory"]["terms"]
    assert data["nextLevel"] == "4-2"
    json.dumps(data)


def test_run_failure_saves_code_without_reward(api, tmp_path):
    result = api.run("1-1", "hero.move_right(1)")
    assert not result["won"]
    assert result["reward"] is None
    assert any(event["type"] == "move" for event in result["events"])
    assert WebApi(tmp_path / "progress.json").level("1-1")["code"] == "hero.move_right(1)"


def test_run_syntax_error_reports_line(api):
    result = api.run("1-1", "hero.move_right(\n")
    assert not result["won"]
    assert result["errorLine"] == 1


def test_win_gives_stars_and_coins(api):
    rows = LEVELS_BY_ID["1-1"].rows
    hero_row = next(row for row in rows if "@" in row)
    steps = hero_row.index("E") - hero_row.index("@")
    result = api.run("1-1", f"hero.move_right({steps})")
    assert result["won"]
    assert result["reward"]["stars"][0]
    assert result["reward"]["coins"] > 0
    assert api.bootstrap()["player"]["stars"] >= 1


def test_collection_lists_heroes_items_and_badges(api):
    data = api.collection()
    assert len(data["heroes"]) == 15
    assert sum(hero["selected"] for hero in data["heroes"]) == 1
    assert any(item["kind"] == "shield" for item in data["items"])
    assert len(data["badges"]) == 23


def test_choose_free_hero_and_refuse_rare_without_coins(api):
    assert api.choose_hero(4)["ok"]
    assert api.bootstrap()["player"]["hero"]["number"] == 4
    rare = api.choose_hero(15)
    assert not rare["ok"]
    assert "xu" in rare["message"]


def test_buy_item_needs_enough_coins(api):
    assert not api.buy_item("shield")["ok"]
    api.progress.coins = 1000
    assert api.buy_item("shield")["ok"]
    assert api.level("1-1")["shield"]
    assert not api.buy_item("shield")["ok"]


def test_settings_are_clamped_and_saved(api, tmp_path):
    saved = api.save_settings(150, -5, 99)
    assert saved == {"musicVolume": 100, "sfxVolume": 0, "musicTrack": -1}
    reloaded = WebApi(tmp_path / "progress.json").bootstrap()["settings"]
    assert reloaded["musicVolume"] == 100


def test_hero_pick_is_remembered(api, tmp_path):
    assert not api.bootstrap()["player"]["heroPicked"]
    api.finish_hero_pick()
    assert WebApi(tmp_path / "progress.json").bootstrap()["player"]["heroPicked"]


def test_backup_without_folder_explains(api):
    result = api.backup()
    assert not result["ok"]
    assert not api.restore()["ok"]


def test_completions_include_hero_methods(api):
    data = api.completions()
    assert any(item["insert"] == "move_right()" for item in data["hero"])
    assert "math" in data["modules"]


def test_handbook_covers_every_level_without_starter_code(api):
    data = api.handbook()
    level_ids = [level["id"] for world in data["worlds"] for level in world["levels"]]
    assert sorted(level_ids) == sorted(LEVELS_BY_ID)
    assert all(world["lesson"] for world in data["worlds"])
    assert len(data["glossary"]) > 80
    text = json.dumps(data, ensure_ascii=False)
    assert "starter" not in text
    for level in LEVELS_BY_ID.values():
        if len(level.starter.strip()) > 40:
            assert level.starter.strip() not in text


def test_music_returns_wav(api, monkeypatch):
    def tiny_track(_spec):
        return np.zeros((2205, 2), dtype=np.int16)

    monkeypatch.setattr(web_api, "compose", tiny_track)
    monkeypatch.setattr(web_api, "COMPOSED", {})
    data = api.music(3)
    assert data[:4] == b"RIFF"
    with wave.open(io.BytesIO(data)) as wav_file:
        assert wav_file.getnchannels() == 2
        assert wav_file.getnframes() == 2205


def test_server_rejects_requests_without_token(api, tmp_path):
    server = start_server(api)
    try:
        url = f"http://127.0.0.1:{server.port}/api/bootstrap"
        request = urllib.request.Request(url, data=b"[]", method="POST")
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request, timeout=5)
        assert error.value.code == 403

        request = urllib.request.Request(url, data=b"[]", method="POST", headers={TOKEN_HEADER: server.token})
        with urllib.request.urlopen(request, timeout=5) as response:
            assert json.loads(response.read())["continueLevel"] == "1-1"

        for blocked_path in ("/solutions/", "/progress.json", "/codequest/engine.py", "/webui/../.env"):
            with pytest.raises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(f"http://127.0.0.1:{server.port}{blocked_path}", timeout=5)
            assert error.value.code == 404

        with urllib.request.urlopen(f"http://127.0.0.1:{server.port}/webui/index.html", timeout=5) as response:
            assert b"CodeQuest" in response.read()
    finally:
        server.shutdown()
