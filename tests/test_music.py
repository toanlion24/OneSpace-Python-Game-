"""Nhạc nền tổng hợp: đủ dài, có tiếng, vòng lặp không bị giật, không lỗi khi không có loa."""

import numpy as np

from codequest.music import (
    SAMPLE_RATE,
    TRACKS,
    MusicPlayer,
    TrackSpec,
    compose,
    track_for_world,
)

# Bài ngắn (1 hợp âm x 4 ô nhịp) để test chạy nhanh; bài thật dùng cùng hàm compose.
SHORT = TrackSpec("Thử", 90, (TRACKS[0].chords[0],), seed=5, rain=True)


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
    player = MusicPlayer(enabled=True)
    player._channel = None
    player.select(2)
    player.update()
    player.set_enabled(False)
    assert player.playing is None
