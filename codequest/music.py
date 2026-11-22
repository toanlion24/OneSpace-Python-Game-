"""Nhạc nền lo-fi tự tổng hợp (không cần file nhạc, không lo bản quyền).

Mỗi bài là một vòng lặp liền mạch: piano điện chơi hợp âm, bass trầm, trống nhẹ có nhịp "swing",
vài nốt giai điệu ngẫu nhiên (theo hạt giống cố định), tiếng đĩa than rè rè và có bài thêm tiếng mưa.
Âm thanh được làm mềm bằng bộ lọc thông thấp cho cảm giác ấm, không gây xao nhãng khi viết code.

Bài nhạc được tổng hợp trong luồng nền để game mở ngay; máy không có loa thì mọi lệnh đều bỏ qua.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

import numpy as np
import pygame

SAMPLE_RATE = 22050
MUSIC_VOLUME = 0.35
FADE_MILLISECONDS = 1500


@dataclass(frozen=True)
class TrackSpec:
    name: str
    bpm: float
    # Mỗi hợp âm là danh sách số nốt MIDI (60 = Đô giữa); mỗi hợp âm kéo dài một ô nhịp.
    chords: tuple[tuple[int, ...], ...]
    seed: int
    rain: bool = False
    swing: float = 0.18


TRACKS: list[TrackSpec] = [
    TrackSpec(
        "Cà phê code", 80,
        ((53, 57, 60, 64), (52, 55, 59, 62), (50, 53, 57, 60), (48, 52, 55, 59)),
        seed=11,
    ),
    TrackSpec(
        "Mưa đêm", 72,
        ((57, 60, 64, 67), (53, 57, 60, 64), (48, 52, 55, 59), (55, 59, 62, 64)),
        seed=23, rain=True, swing=0.12,
    ),
    TrackSpec(
        "Tập trung", 84,
        ((50, 53, 57, 60, 64), (55, 59, 62, 65, 69), (48, 52, 55, 59, 62), (57, 61, 64, 67)),
        seed=37,
    ),
    TrackSpec(
        "Trạm vũ trụ", 76,
        ((52, 55, 59, 62), (48, 52, 55, 59), (45, 48, 52, 55), (47, 50, 54, 57)),
        seed=41, rain=False, swing=0.1,
    ),
]


def midi_to_hz(note: float) -> float:
    return 440.0 * 2 ** ((note - 69) / 12)


def _time_axis(seconds: float) -> np.ndarray:
    return np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE


def _envelope(seconds: float, attack: float, decay: float) -> np.ndarray:
    time_axis = _time_axis(seconds)
    return np.minimum(1.0, time_axis / attack) * np.exp(-time_axis / decay)


def electric_piano(note: float, seconds: float = 2.4) -> np.ndarray:
    frequency = midi_to_hz(note)
    time_axis = _time_axis(seconds)
    tone = (
        np.sin(2 * np.pi * frequency * time_axis)
        + 0.3 * np.sin(2 * np.pi * 2 * frequency * time_axis) * np.exp(-time_axis / 0.25)
        + 0.08 * np.sin(2 * np.pi * 3.01 * frequency * time_axis)
    )
    tremolo = 1 - 0.12 * (1 + np.sin(2 * np.pi * 4.5 * time_axis)) / 2
    return tone * tremolo * _envelope(seconds, 0.008, 1.1)


def bass_note(note: float, seconds: float = 1.2) -> np.ndarray:
    frequency = midi_to_hz(note)
    time_axis = _time_axis(seconds)
    tone = np.sin(2 * np.pi * frequency * time_axis) + 0.2 * np.sin(2 * np.pi * 2 * frequency * time_axis)
    return tone * _envelope(seconds, 0.012, 0.5)


def pluck(note: float, seconds: float = 1.0) -> np.ndarray:
    frequency = midi_to_hz(note)
    time_axis = _time_axis(seconds)
    tone = np.sin(2 * np.pi * frequency * time_axis) + 0.35 * np.sin(2 * np.pi * 2 * frequency * time_axis)
    return tone * _envelope(seconds, 0.004, 0.32)


def kick() -> np.ndarray:
    time_axis = _time_axis(0.32)
    frequency = 45 + 75 * np.exp(-time_axis / 0.04)
    phase = 2 * np.pi * np.cumsum(frequency) / SAMPLE_RATE
    return np.sin(phase) * np.exp(-time_axis / 0.13)


def snare(random: np.random.Generator) -> np.ndarray:
    time_axis = _time_axis(0.2)
    noise = random.uniform(-1, 1, time_axis.size)
    body = np.sin(2 * np.pi * 185 * time_axis)
    return (0.6 * noise + 0.4 * body) * np.exp(-time_axis / 0.055)


def hi_hat(random: np.random.Generator) -> np.ndarray:
    time_axis = _time_axis(0.05)
    noise = np.diff(random.uniform(-1, 1, time_axis.size + 1))
    return noise * np.exp(-time_axis / 0.012)


def low_pass(samples: np.ndarray, cutoff_hz: float) -> np.ndarray:
    """Lọc thông thấp mềm trong miền tần số (nhanh với numpy, không cần scipy)."""
    spectrum = np.fft.rfft(samples)
    frequencies = np.fft.rfftfreq(samples.size, 1 / SAMPLE_RATE)
    spectrum *= 1 / (1 + (frequencies / cutoff_hz) ** 4)
    return np.fft.irfft(spectrum, samples.size)


def _add(buffer: np.ndarray, start_seconds: float, sound: np.ndarray, gain: float) -> None:
    """Cộng âm vào bản nhạc; phần thừa cuối bài vòng về đầu bài để vòng lặp liền mạch."""
    start = int(start_seconds * SAMPLE_RATE) % buffer.size
    end = min(buffer.size, start + sound.size)
    buffer[start:end] += sound[: end - start] * gain
    overflow = sound.size - (end - start)
    if overflow > 0:
        buffer[:overflow] += sound[end - start:] * gain


def compose(spec: TrackSpec) -> np.ndarray:
    """Tổng hợp một bài thành mảng stereo int16 (số mẫu x 2)."""
    random = np.random.default_rng(spec.seed)
    beat = 60.0 / spec.bpm
    bars = len(spec.chords) * 4
    melody = np.zeros(int(SAMPLE_RATE * bars * 4 * beat))
    harmony = np.zeros_like(melody)
    drums = np.zeros_like(melody)
    kick_sound = kick()

    for bar in range(bars):
        chord = spec.chords[bar % len(spec.chords)]
        bar_start = bar * 4 * beat
        swung_half = beat * (0.5 + spec.swing)
        for note in chord:
            _add(harmony, bar_start, electric_piano(note), 0.13)
            _add(harmony, bar_start + 2 * beat + swung_half, electric_piano(note, 1.4), 0.07)
        root = min(chord) - 12
        _add(harmony, bar_start, bass_note(root), 0.42)
        _add(harmony, bar_start + 2 * beat, bass_note(root + (7 if bar % 2 else 0)), 0.32)

        _add(drums, bar_start, kick_sound, 0.55)
        _add(drums, bar_start + 2 * beat + swung_half, kick_sound, 0.35)
        for beat_index in (1, 3):
            _add(drums, bar_start + beat_index * beat, snare(random), 0.16)
        for eighth in range(8):
            offset = eighth // 2 * beat + (swung_half if eighth % 2 else 0)
            _add(drums, bar_start + offset, hi_hat(random), 0.07 if eighth % 2 else 0.1)

        # Giai điệu thưa: vài nốt của hợp âm ở quãng tám trên, có ô nhịp nghỉ hẳn.
        if bar % 4 == 3:
            continue
        for eighth in sorted(random.choice(8, size=3, replace=False)):
            note = random.choice(chord) + 12 + random.choice([0, 0, 12])
            offset = eighth // 2 * beat + (swung_half if eighth % 2 else 0)
            _add(melody, bar_start + offset, pluck(note), 0.09)

    mix = low_pass(harmony + melody, 2600) + low_pass(drums, 5000)
    noise = random.uniform(-1, 1, mix.size)
    mix += low_pass(noise, 3000) * 0.012
    crackle_positions = random.integers(0, mix.size, size=int(mix.size / SAMPLE_RATE * 6))
    mix[crackle_positions] += random.uniform(-0.25, 0.25, crackle_positions.size)
    if spec.rain:
        mix += low_pass(noise, 1400) * 0.06

    delay = int(0.013 * SAMPLE_RATE)
    left = 0.85 * mix + 0.15 * np.roll(mix, delay)
    right = 0.85 * mix + 0.15 * np.roll(mix, -delay)
    stereo = np.column_stack([left, right])
    stereo *= 0.9 / max(1e-6, float(np.abs(stereo).max()))
    return (stereo * 32767).astype(np.int16)


# Bài đã tổng hợp dùng chung cho cả chương trình (chỉ tổng hợp một lần).
COMPOSED: dict[int, np.ndarray] = {}


def track_for_world(world_number: int) -> int:
    """Bài 0 dành cho menu; các World luân phiên các bài còn lại."""
    return 1 + (world_number - 1) % (len(TRACKS) - 1)


class MusicPlayer:
    """Phát nhạc nền trên một kênh riêng, chuyển bài nhẹ nhàng (fade)."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.wanted = 0
        self.playing: int | None = None
        self._sounds: dict[int, pygame.mixer.Sound] = {}
        self._channel: pygame.mixer.Channel | None = None
        try:
            if pygame.mixer.get_init():
                pygame.mixer.set_reserved(1)
                self._channel = pygame.mixer.Channel(0)
        except pygame.error:
            self._channel = None
        self._worker: threading.Thread | None = None

    @property
    def track_name(self) -> str:
        return TRACKS[self.wanted].name

    def select(self, index: int) -> None:
        self.wanted = index % len(TRACKS)
        self._start_worker()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if not enabled and self._channel is not None:
            self._channel.fadeout(600)
            self.playing = None
        self._start_worker()

    def _start_worker(self) -> None:
        if self._channel is None or not self.enabled:
            return
        if self._worker is not None and self._worker.is_alive():
            return
        order = [self.wanted] + [index for index in range(len(TRACKS)) if index != self.wanted]
        missing = [index for index in order if index not in COMPOSED]
        if not missing:
            return
        self._worker = threading.Thread(target=self._compose_all, args=(missing,), daemon=True)
        self._worker.start()

    def _compose_all(self, indexes: list[int]) -> None:
        for index in indexes:
            if index not in COMPOSED:
                COMPOSED[index] = compose(TRACKS[index])

    def update(self) -> None:
        if self._channel is None or not self.enabled or self.playing == self.wanted:
            return
        array = COMPOSED.get(self.wanted)
        if array is None:
            self._start_worker()
            return
        sound = self._sounds.get(self.wanted)
        if sound is None:
            try:
                sound = pygame.sndarray.make_sound(np.ascontiguousarray(array))
            except (pygame.error, ValueError):
                self._channel = None
                return
            sound.set_volume(MUSIC_VOLUME)
            self._sounds[self.wanted] = sound
        if self.playing is not None:
            self._channel.fadeout(400)
        self._channel.play(sound, loops=-1, fade_ms=FADE_MILLISECONDS)
        self.playing = self.wanted
