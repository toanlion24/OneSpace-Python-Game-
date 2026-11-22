"""Nhạc nền tổng hợp: đủ dài, có tiếng, vòng lặp không bị giật, không lỗi khi không có loa."""

import numpy as np

from codequest.music import (
    GENRE_NAMES,
    SAMPLE_RATE,
    TRACKS,
    MusicPlayer,
    TrackSpec,
    compose,
    track_for_world,
)

# Bài ngắn (1 hợp âm x 4 ô nhịp) để test chạy nhanh; bài thật dùng cùng hàm compose.
SHORT = TrackSpec("Thử", "lofi", 90, (TRACKS[0].chords[0],), seed=5, rain=True)


def test_track_is_a_long_quiet_stereo_loop():
    data = compose(SHORT)
    assert data.dtype == np.int16 and data.shape[1] == 2
    assert data.shape[0] / SAMPLE_RATE > 10
    level = float(np.sqrt((data.astype(float) ** 2).mean())) / 32767
    assert 0.03 < level < 0.4
    seam_jump = abs(int(data[0, 0]) - int(data[-1, 0])) / 32767
    assert seam_jump < 0.1


def test_tracks_are_reproducible():
    assert np.array_equal(compose(SHORT)[:5000], compose(SHORT)[:5000])


def test_worlds_use_level_tracks_not_menu_track():
    numbers = {track_for_world(world) for world in range(1, 24)}
    assert 0 not in numbers and numbers <= set(range(len(TRACKS)))


def test_player_without_audio_device_does_nothing():
    player = MusicPlayer(40)
    player._channel = None
    player.select(2)
    player.update()
    player.set_volume(0)
    assert player.playing is None and not player.enabled


def test_every_genre_has_a_track():
    assert {track.style for track in TRACKS} == set(GENRE_NAMES)


def test_old_music_off_setting_becomes_zero_percent(tmp_path):
    import json

    from codequest.progress import Progress

    save_file = tmp_path / "progress.json"
    save_file.write_text(json.dumps({"format": 3, "music_on": False}), encoding="utf-8")
    progress = Progress(save_file, None)
    assert progress.music_volume == 0 and progress.sfx_volume == 80 and progress.music_track == -1
