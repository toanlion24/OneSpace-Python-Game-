"""Nhạc nền tự tổng hợp (không cần file nhạc, không lo bản quyền).

Có 7 thể loại: Lo-fi, 8-bit, Ambient, Jazz, Synthwave, Acoustic, Piano. Mỗi bài là một vòng lặp
liền mạch, tạo từ các "nhạc cụ" tổng hợp bằng numpy (piano điện, đàn guitar gảy, pad, chuông, trống...).
Giai điệu ngẫu nhiên theo hạt giống cố định nên mỗi lần mở game bài nhạc vẫn y như cũ.

Bài được tổng hợp trong luồng nền khi cần lần đầu (khoảng 1-3 giây); máy không có loa thì mọi lệnh bỏ qua.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pygame

SAMPLE_RATE = 22050
# Âm lượng 100% của nhạc nền (để chừa chỗ cho tiếng hiệu ứng).
MUSIC_FULL_VOLUME = 0.8
DEFAULT_MUSIC_PERCENT = 40
FADE_MILLISECONDS = 1200
TARGET_LOUDNESS = 0.12

Chord = tuple[int, ...]

GENRE_NAMES: dict[str, str] = {
    "lofi": "Lo-fi",
    "chiptune": "8-bit",
    "ambient": "Ambient",
    "jazz": "Jazz",
    "synthwave": "Synthwave",
    "acoustic": "Acoustic",
    "piano": "Piano",
}


@dataclass(frozen=True)
class TrackSpec:
    name: str
    style: str
    bpm: float
    # Mỗi hợp âm là danh sách số nốt MIDI (60 = Đô giữa); mỗi hợp âm kéo dài một ô nhịp.
    chords: tuple[Chord, ...]
    seed: int
    rain: bool = False
    swing: float = 0.18
    repeats: int = 4

    @property
    def genre(self) -> str:
        return GENRE_NAMES[self.style]


TRACKS: list[TrackSpec] = [
    TrackSpec("Cà phê code", "lofi", 80,
              ((53, 57, 60, 64), (52, 55, 59, 62), (50, 53, 57, 60), (48, 52, 55, 59)), seed=11),
    TrackSpec("Mưa đêm", "lofi", 72,
              ((57, 60, 64, 67), (53, 57, 60, 64), (48, 52, 55, 59), (55, 59, 62, 64)), seed=23, rain=True, swing=0.12),
    TrackSpec("Tập trung", "lofi", 84,
              ((50, 53, 57, 60, 64), (55, 59, 62, 65, 69), (48, 52, 55, 59, 62), (57, 61, 64, 67)), seed=37),
    TrackSpec("Trạm vũ trụ", "lofi", 76,
              ((52, 55, 59, 62), (48, 52, 55, 59), (45, 48, 52, 55), (47, 50, 54, 57)), seed=41, swing=0.1),
    TrackSpec("Pixel phiêu lưu", "chiptune", 128,
              ((48, 52, 55), (43, 47, 50), (45, 48, 52), (41, 45, 48)), seed=5, swing=0.0, repeats=6),
    TrackSpec("Trùm 8-bit", "chiptune", 140,
              ((45, 48, 52), (41, 45, 48), (43, 47, 50), (40, 44, 47)), seed=8, swing=0.0, repeats=6),
    TrackSpec("Không gian sâu", "ambient", 56,
              ((48, 55, 59, 64), (45, 52, 55, 60), (41, 48, 52, 57), (43, 50, 55, 59)), seed=13, repeats=3),
    TrackSpec("Jazz quán đêm", "jazz", 112,
              ((50, 53, 57, 60), (43, 47, 50, 53), (48, 52, 55, 59), (45, 49, 52, 55)), seed=17, swing=0.33, repeats=5),
    TrackSpec("Thành phố neon", "synthwave", 100,
              ((45, 48, 52), (41, 45, 48), (48, 52, 55), (43, 47, 50)), seed=29, swing=0.0, repeats=4),
    TrackSpec("Guitar buổi sáng", "acoustic", 92,
              ((43, 47, 50, 55), (50, 54, 57, 62), (52, 55, 59, 64), (48, 52, 55, 60)), seed=31, swing=0.08, repeats=4),
    TrackSpec("Piano yên tĩnh", "piano", 66,
              ((48, 52, 55, 59), (45, 48, 52, 55), (41, 45, 48, 52), (43, 47, 50, 55)), seed=43, swing=0.0, repeats=3),
    TrackSpec("Mưa trên phố", "jazz", 96,
              ((53, 57, 60, 64), (50, 53, 57, 60), (55, 59, 62, 65), (48, 52, 55, 59)), seed=47, swing=0.3,
              rain=True, repeats=5),
]


def midi_to_hz(note: float) -> float:
    return 440.0 * 2 ** ((note - 69) / 12)


def _time_axis(seconds: float) -> np.ndarray:
    return np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE


def _envelope(seconds: float, attack: float, decay: float) -> np.ndarray:
    time_axis = _time_axis(seconds)
    return np.minimum(1.0, time_axis / attack) * np.exp(-time_axis / decay)


def _fade_out(time_axis: np.ndarray, seconds: float) -> np.ndarray:
    return np.minimum(1.0, (time_axis[-1] - time_axis) / seconds + 1e-9)


def _harmonics(frequency: float, time_axis: np.ndarray, weights: list[float]) -> np.ndarray:
    """Cộng các hoạ âm (bỏ hoạ âm vượt quá tần số Nyquist để tiếng không bị rè)."""
    tone = np.zeros_like(time_axis)
    for index, weight in enumerate(weights, start=1):
        if frequency * index < SAMPLE_RATE / 2 - 500:
            tone += weight * np.sin(2 * np.pi * frequency * index * time_axis)
    return tone


# ---------------------------------------------------------------- instruments
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


def piano(note: float, seconds: float = 3.0) -> np.ndarray:
    """Tiếng piano: hoạ âm cao tắt nhanh hơn hoạ âm gốc."""
    frequency = midi_to_hz(note)
    time_axis = _time_axis(seconds)
    tone = np.zeros_like(time_axis)
    for index, weight in enumerate([1.0, 0.45, 0.25, 0.12, 0.06], start=1):
        if frequency * index < SAMPLE_RATE / 2 - 500:
            decay = 1.6 / index
            tone += weight * np.sin(2 * np.pi * frequency * index * 1.0008 * time_axis) * np.exp(-time_axis / decay)
    return tone * np.minimum(1.0, time_axis / 0.004) * _fade_out(time_axis, 0.05)


def bass_note(note: float, seconds: float = 1.2) -> np.ndarray:
    frequency = midi_to_hz(note)
    time_axis = _time_axis(seconds)
    tone = np.sin(2 * np.pi * frequency * time_axis) + 0.2 * np.sin(2 * np.pi * 2 * frequency * time_axis)
    return tone * _envelope(seconds, 0.012, 0.5) * _fade_out(time_axis, 0.02)


def pluck(note: float, seconds: float = 1.0) -> np.ndarray:
    frequency = midi_to_hz(note)
    time_axis = _time_axis(seconds)
    tone = np.sin(2 * np.pi * frequency * time_axis) + 0.35 * np.sin(2 * np.pi * 2 * frequency * time_axis)
    return tone * _envelope(seconds, 0.004, 0.32) * _fade_out(time_axis, 0.02)


def square(note: float, seconds: float, duty: float = 0.5, decay: float = 0.4) -> np.ndarray:
    """Sóng vuông kiểu máy chơi game 8-bit (tổng hoạ âm nên không chói)."""
    frequency = midi_to_hz(note)
    time_axis = _time_axis(seconds)
    weights = [2 * np.sin(np.pi * index * duty) / (np.pi * index) for index in range(1, 14)]
    tone = _harmonics(frequency, time_axis, weights)
    return tone * _envelope(seconds, 0.003, decay) * _fade_out(time_axis, 0.01)


def triangle(note: float, seconds: float) -> np.ndarray:
    frequency = midi_to_hz(note)
    time_axis = _time_axis(seconds)
    weights = [(1 / index**2) * (1 if index % 4 == 1 else -1) if index % 2 else 0.0 for index in range(1, 10)]
    tone = _harmonics(frequency, time_axis, weights)
    return tone * np.minimum(1.0, time_axis / 0.005) * _fade_out(time_axis, 0.03)


def saw_pad(note: float, seconds: float, attack: float = 0.6) -> np.ndarray:
    """Pad dày: ba sóng răng cưa lệch nhẹ cao độ, lên tiếng từ từ."""
    time_axis = _time_axis(seconds)
    tone = np.zeros_like(time_axis)
    for detune in (-0.07, 0.0, 0.07):
        frequency = midi_to_hz(note + detune)
        tone += _harmonics(frequency, time_axis, [1 / index for index in range(1, 8)])
    rise = np.minimum(1.0, time_axis / attack)
    return tone / 3 * rise * _fade_out(time_axis, attack * 0.8)


def bell(note: float, seconds: float = 3.0) -> np.ndarray:
    frequency = midi_to_hz(note)
    time_axis = _time_axis(seconds)
    overtone = 0.4 * np.sin(2 * np.pi * frequency * 2.76 * time_axis) * np.exp(-time_axis / 0.4)
    tone = np.sin(2 * np.pi * frequency * time_axis) + overtone
    return tone * _envelope(seconds, 0.003, 1.3) * _fade_out(time_axis, 0.05)


def guitar(note: float, random: np.random.Generator, seconds: float = 2.0) -> np.ndarray:
    """Dây đàn gảy (thuật toán Karplus-Strong): mỗi chu kỳ là trung bình hai mẫu của chu kỳ trước."""
    period = max(2, round(SAMPLE_RATE / midi_to_hz(note)))
    total = int(SAMPLE_RATE * seconds)
    buffer = np.zeros(total + period + 1)
    burst = random.uniform(-1, 1, period)
    buffer[1:period + 1] = (burst + np.roll(burst, 1)) / 2
    position = period + 1
    while position < buffer.size:
        end = min(position + period, buffer.size)
        count = end - position
        start = position - period
        buffer[position:end] = 0.996 * 0.5 * (buffer[start:start + count] + buffer[start - 1:start - 1 + count])
        position = end
    return buffer[1:total + 1] * _fade_out(_time_axis(seconds), 0.05)


def kick(length: float = 0.32) -> np.ndarray:
    time_axis = _time_axis(length)
    frequency = 45 + 75 * np.exp(-time_axis / 0.04)
    phase = 2 * np.pi * np.cumsum(frequency) / SAMPLE_RATE
    return np.sin(phase) * np.exp(-time_axis / (length * 0.4))


def snare(random: np.random.Generator, tail: float = 0.055) -> np.ndarray:
    time_axis = _time_axis(max(0.2, tail * 4))
    noise = random.uniform(-1, 1, time_axis.size)
    body = np.sin(2 * np.pi * 185 * time_axis) * np.exp(-time_axis / 0.04)
    return (0.6 * noise + 0.4 * body) * np.exp(-time_axis / tail)


def hi_hat(random: np.random.Generator, tail: float = 0.012) -> np.ndarray:
    time_axis = _time_axis(max(0.05, tail * 5))
    noise = np.diff(random.uniform(-1, 1, time_axis.size + 1))
    return noise * np.exp(-time_axis / tail)


def ride(random: np.random.Generator) -> np.ndarray:
    time_axis = _time_axis(0.6)
    noise = np.diff(random.uniform(-1, 1, time_axis.size + 1)) * 0.5
    metal = sum(np.sin(2 * np.pi * frequency * time_axis) for frequency in (3150, 4370, 5210)) / 3
    return (noise + 0.6 * metal) * np.exp(-time_axis / 0.22)


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


class Song:
    """Bản nhạc đang soạn: lớp nhạc cụ, lớp trống và bộ nhớ đệm các nốt đã tổng hợp."""

    def __init__(self, spec: TrackSpec) -> None:
        self.spec = spec
        self.random = np.random.default_rng(spec.seed)
        self.beat = 60.0 / spec.bpm
        self.bars = len(spec.chords) * spec.repeats
        length = int(SAMPLE_RATE * self.bars * 4 * self.beat)
        self.tonal = np.zeros(length)
        self.drums = np.zeros(length)
        self._cache: dict[tuple[object, ...], np.ndarray] = {}

    def note(self, maker: Callable[..., np.ndarray], note: float, *args: float) -> np.ndarray:
        key = (maker.__name__, note, *args)
        if key not in self._cache:
            self._cache[key] = maker(note, *args)
        return self._cache[key]

    def time_of(self, bar: int, beat_position: float) -> float:
        """Thời điểm (giây) của một phách trong ô nhịp; nửa phách lẻ được "swing" lùi lại một chút."""
        whole = int(beat_position)
        fraction = beat_position - whole
        if abs(fraction - 0.5) < 1e-6:
            fraction = 0.5 + self.spec.swing
        return (bar * 4 + whole + fraction) * self.beat

    def chord(self, bar: int) -> Chord:
        return self.spec.chords[bar % len(self.spec.chords)]


# ---------------------------------------------------------------- arrangements
def arrange_lofi(song: Song) -> None:
    random = song.random
    kick_sound = kick()
    for bar in range(song.bars):
        chord = song.chord(bar)
        for note in chord:
            _add(song.tonal, song.time_of(bar, 0), song.note(electric_piano, note), 0.13)
            _add(song.tonal, song.time_of(bar, 2.5), song.note(electric_piano, note, 1.4), 0.07)
        root = min(chord) - 12
        _add(song.tonal, song.time_of(bar, 0), song.note(bass_note, root), 0.42)
        _add(song.tonal, song.time_of(bar, 2), song.note(bass_note, root + (7 if bar % 2 else 0)), 0.32)
        _add(song.drums, song.time_of(bar, 0), kick_sound, 0.55)
        _add(song.drums, song.time_of(bar, 2.5), kick_sound, 0.35)
        for beat in (1, 3):
            _add(song.drums, song.time_of(bar, beat), snare(random), 0.16)
        for eighth in range(8):
            _add(song.drums, song.time_of(bar, eighth / 2), hi_hat(random), 0.07 if eighth % 2 else 0.1)
        if bar % 4 == 3:
            continue
        for eighth in sorted(random.choice(8, size=3, replace=False)):
            note = int(random.choice(chord)) + 12 + int(random.choice([0, 0, 12]))
            _add(song.tonal, song.time_of(bar, eighth / 2), song.note(pluck, note), 0.09)


def arrange_chiptune(song: Song) -> None:
    random = song.random
    scale_steps = [0, 2, 4, 7, 9, 12, 14, 16]
    sixteenth = song.beat / 4
    for bar in range(song.bars):
        chord = song.chord(bar)
        root = chord[0]
        for step in range(16):
            note = chord[step % len(chord)] + 12 + (12 if step % 8 >= 4 else 0)
            _add(song.tonal, bar * 4 * song.beat + step * sixteenth, song.note(square, note, 0.12, 0.25, 0.06), 0.05)
        for eighth in range(8):
            bass = root - 12 + (7 if eighth % 2 else 0)
            _add(song.tonal, song.time_of(bar, eighth / 2), song.note(triangle, bass, song.beat / 2 * 0.9), 0.35)
        # Giai điệu chính lặp lại theo chu kỳ 4 ô nhịp để dễ nhớ.
        motif = np.random.default_rng(song.spec.seed * 100 + bar % 4)
        for beat in range(4):
            if motif.random() < 0.2:
                continue
            note = root + 24 + scale_steps[int(motif.integers(len(scale_steps)))]
            length = song.beat * (0.9 if motif.random() < 0.7 else 0.45)
            _add(song.tonal, song.time_of(bar, beat), song.note(square, note, length, 0.5, 0.3), 0.11)
        _add(song.drums, song.time_of(bar, 0), kick(0.18), 0.5)
        _add(song.drums, song.time_of(bar, 2), kick(0.18), 0.5)
        for beat in (1, 3):
            _add(song.drums, song.time_of(bar, beat), snare(random, 0.04), 0.18)
        for eighth in range(8):
            _add(song.drums, song.time_of(bar, eighth / 2), hi_hat(random, 0.008), 0.06)


def arrange_ambient(song: Song) -> None:
    random = song.random
    bar_seconds = 4 * song.beat
    for bar in range(song.bars):
        chord = song.chord(bar)
        for note in chord:
            _add(song.tonal, song.time_of(bar, 0), song.note(saw_pad, note, bar_seconds * 1.35, 1.4), 0.07)
        _add(song.tonal, song.time_of(bar, 0), song.note(bass_note, chord[0] - 12, bar_seconds), 0.2)
        for _ in range(int(random.integers(1, 3))):
            note = int(random.choice(chord)) + 24
            _add(song.tonal, song.time_of(bar, float(random.integers(0, 8)) / 2), song.note(bell, note), 0.08)


def arrange_jazz(song: Song) -> None:
    random = song.random
    for bar in range(song.bars):
        chord = song.chord(bar)
        next_root = song.chord(bar + 1)[0]
        # Bass đi bộ: nốt gốc, hai nốt trong hợp âm, rồi nốt "dẫn" sát nốt gốc của ô nhịp sau.
        walk = [chord[0], chord[int(random.integers(1, len(chord)))], chord[2], next_root + int(random.choice([-1, 1]))]
        for beat, note in enumerate(walk):
            _add(song.tonal, song.time_of(bar, beat), song.note(bass_note, note - 12, song.beat * 1.1), 0.4)
        for position in (1.5, 3.5) if bar % 2 else (0.5, 2.5):
            for note in chord[1:]:
                _add(song.tonal, song.time_of(bar, position), song.note(electric_piano, note + 12, 0.7), 0.06)
        for position in (0, 1, 1.5, 2, 3, 3.5):
            _add(song.drums, song.time_of(bar, position), ride(random), 0.06 if position % 1 else 0.09)
        for beat in (1, 3):
            _add(song.drums, song.time_of(bar, beat), hi_hat(random, 0.02), 0.05)
        if bar % 4 == 3:
            continue
        for eighth in sorted(random.choice(8, size=int(random.integers(2, 5)), replace=False)):
            note = int(random.choice(chord)) + 24
            _add(song.tonal, song.time_of(bar, eighth / 2), song.note(bell, note, 1.2), 0.06)


def arrange_synthwave(song: Song) -> None:
    random = song.random
    bar_seconds = 4 * song.beat
    sixteenth = song.beat / 4
    pattern = [0, 1, 2, 1, 0, 2, 1, 2]
    for bar in range(song.bars):
        chord = song.chord(bar)
        for note in chord:
            _add(song.tonal, song.time_of(bar, 0), song.note(saw_pad, note + 12, bar_seconds * 1.05, 0.15), 0.05)
        for eighth in range(8):
            _add(song.tonal, song.time_of(bar, eighth / 2), song.note(bass_note, chord[0] - 12, song.beat / 2), 0.35)
        for step in range(16):
            note = chord[pattern[step % 8] % len(chord)] + 24
            _add(song.tonal, bar * bar_seconds + step * sixteenth, song.note(pluck, note, 0.25), 0.07)
        for beat in (0, 2):
            _add(song.drums, song.time_of(bar, beat), kick(0.4), 0.6)
        for beat in (1, 3):
            _add(song.drums, song.time_of(bar, beat), snare(random, 0.14), 0.18)
        for eighth in range(8):
            _add(song.drums, song.time_of(bar, eighth / 2), hi_hat(random, 0.01), 0.05)


def _guitar_note(note: float, seconds: float) -> np.ndarray:
    return guitar(note, np.random.default_rng(int(note * 10)), seconds)


def arrange_acoustic(song: Song) -> None:
    random = song.random
    # Kiểu quạt chả: Xuống - Xuống - Lên - Lên - Xuống - Lên.
    strums = [(0, 1.0, True), (1, 0.7, True), (1.5, 0.5, False), (2.5, 0.5, False), (3, 0.7, True), (3.5, 0.5, False)]
    for bar in range(song.bars):
        chord = song.chord(bar)
        for position, strength, downward in strums:
            notes = chord if downward else tuple(reversed(chord))
            for index, note in enumerate(notes):
                start = song.time_of(bar, position) + index * 0.012
                _add(song.tonal, start, song.note(_guitar_note, note, 1.6), 0.12 * strength)
        _add(song.tonal, song.time_of(bar, 0), song.note(bass_note, chord[0] - 12, 1.2), 0.25)
        for eighth in range(8):
            _add(song.drums, song.time_of(bar, eighth / 2), hi_hat(random, 0.03), 0.04 if eighth % 2 else 0.06)
        if bar % 2:
            note = int(random.choice(chord)) + 12
            _add(song.tonal, song.time_of(bar, float(random.integers(0, 4))), song.note(_guitar_note, note, 1.6), 0.12)


def arrange_piano(song: Song) -> None:
    random = song.random
    for bar in range(song.bars):
        chord = song.chord(bar)
        broken = [chord[0] - 12, chord[0], *chord[1:], chord[0] + 12, *chord[1:]][:8]
        for eighth, note in enumerate(broken):
            _add(song.tonal, song.time_of(bar, eighth / 2), song.note(piano, note), 0.11)
        if bar % 4 == 3:
            continue
        for beat in sorted(random.choice(4, size=int(random.integers(1, 3)), replace=False)):
            note = int(random.choice(chord)) + 12
            _add(song.tonal, song.time_of(bar, float(beat)), song.note(piano, note, 3.5), 0.16)


ARRANGERS: dict[str, Callable[[Song], None]] = {
    "lofi": arrange_lofi,
    "chiptune": arrange_chiptune,
    "ambient": arrange_ambient,
    "jazz": arrange_jazz,
    "synthwave": arrange_synthwave,
    "acoustic": arrange_acoustic,
    "piano": arrange_piano,
}
TONE_CUTOFF: dict[str, float] = {
    "lofi": 2600,
    "chiptune": 5000,
    "ambient": 3000,
    "jazz": 4200,
    "synthwave": 4500,
    "acoustic": 5000,
    "piano": 4500,
}


def compose(spec: TrackSpec) -> np.ndarray:
    """Tổng hợp một bài thành mảng stereo int16 (số mẫu x 2); các bài to đều nhau."""
    song = Song(spec)
    ARRANGERS[spec.style](song)
    mix = low_pass(song.tonal, TONE_CUTOFF[spec.style]) + low_pass(song.drums, 6000)
    random = song.random
    noise = random.uniform(-1, 1, mix.size)
    if spec.style == "lofi":
        mix += low_pass(noise, 3000) * 0.012
        crackle_positions = random.integers(0, mix.size, size=int(mix.size / SAMPLE_RATE * 6))
        mix[crackle_positions] += random.uniform(-0.25, 0.25, crackle_positions.size)
    if spec.rain:
        mix += low_pass(noise, 1400) * 0.06

    delay = int(0.013 * SAMPLE_RATE)
    left = 0.85 * mix + 0.15 * np.roll(mix, delay)
    right = 0.85 * mix + 0.15 * np.roll(mix, -delay)
    stereo = np.column_stack([left, right])
    loudness = float(np.sqrt((stereo**2).mean()))
    stereo *= TARGET_LOUDNESS / max(1e-6, loudness)
    # Nén mềm các đỉnh thay vì cắt cụt để không bị rè.
    stereo = np.tanh(stereo * 1.2) / 1.2
    return (stereo * 32767).astype(np.int16)


# Bài đã tổng hợp dùng chung cho cả chương trình (chỉ tổng hợp một lần).
COMPOSED: dict[int, np.ndarray] = {}


def track_for_world(world_number: int) -> int:
    """Bài 0 dành cho menu; các World luân phiên các bài còn lại."""
    return 1 + (world_number - 1) % (len(TRACKS) - 1)


class MusicPlayer:
    """Phát nhạc nền trên một kênh riêng, chuyển bài nhẹ nhàng (fade), âm lượng theo phần trăm."""

    def __init__(self, volume_percent: int = DEFAULT_MUSIC_PERCENT) -> None:
        self.volume_percent = max(0, min(100, volume_percent))
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
    def enabled(self) -> bool:
        return self.volume_percent > 0

    @property
    def track_name(self) -> str:
        return TRACKS[self.wanted].name

    @property
    def is_loading(self) -> bool:
        return self.enabled and self._channel is not None and self.wanted not in COMPOSED

    def select(self, index: int) -> None:
        self.wanted = index % len(TRACKS)
        self._start_worker()

    def set_volume(self, percent: int) -> None:
        self.volume_percent = max(0, min(100, percent))
        if self._channel is None:
            return
        if not self.enabled:
            self._channel.fadeout(400)
            self.playing = None
            return
        self._channel.set_volume(self.volume_percent / 100 * MUSIC_FULL_VOLUME)
        self._start_worker()

    def _start_worker(self) -> None:
        if self._channel is None or not self.enabled or self.wanted in COMPOSED:
            return
        if self._worker is not None and self._worker.is_alive():
            return
        self._worker = threading.Thread(target=self._compose, args=(self.wanted,), daemon=True)
        self._worker.start()

    @staticmethod
    def _compose(index: int) -> None:
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
            self._sounds[self.wanted] = sound
        if self.playing is not None:
            self._channel.fadeout(300)
        self._channel.play(sound, loops=-1, fade_ms=FADE_MILLISECONDS)
        self._channel.set_volume(self.volume_percent / 100 * MUSIC_FULL_VOLUME)
        self.playing = self.wanted
