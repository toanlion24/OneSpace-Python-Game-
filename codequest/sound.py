"""Small synthesized sound effects (no audio files needed).

If the computer has no audio device, every call silently does nothing.
"""

from __future__ import annotations

import numpy as np
import pygame

SAMPLE_RATE = 22050


def _tone(frequencies: list[tuple[float, float]], volume: float = 0.35, wave: str = "square") -> np.ndarray:
    """Concatenate (frequency Hz, seconds) notes into one sound with a short fade on each note."""
    parts = []
    for frequency, seconds in frequencies:
        count = int(SAMPLE_RATE * seconds)
        time_axis = np.arange(count) / SAMPLE_RATE
        if frequency <= 0:
            samples = np.random.uniform(-1, 1, count)
        elif wave == "square":
            samples = np.sign(np.sin(2 * np.pi * frequency * time_axis))
        else:
            samples = np.sin(2 * np.pi * frequency * time_axis)
        envelope = np.minimum(1.0, np.linspace(1.0, 0.0, count) * 4)
        parts.append(samples * envelope)
    return (np.concatenate(parts) * volume * 32767).astype(np.int16)


SOUND_RECIPES: dict[str, np.ndarray] = {}


def _recipes() -> dict[str, np.ndarray]:
    if not SOUND_RECIPES:
        SOUND_RECIPES.update({
            "step": _tone([(220, 0.03)], volume=0.08),
            "gem": _tone([(988, 0.06), (1319, 0.12)], volume=0.25),
            "hit": _tone([(0, 0.08)], volume=0.25),
            "hurt": _tone([(196, 0.08), (147, 0.14)], volume=0.3),
            "door": _tone([(330, 0.06), (440, 0.06), (554, 0.1)], volume=0.25),
            "shield": _tone([(660, 0.05), (880, 0.1)], volume=0.25, wave="sine"),
            "win": _tone([(523, 0.1), (659, 0.1), (784, 0.1), (1047, 0.25)], volume=0.3),
            "fail": _tone([(392, 0.12), (330, 0.12), (262, 0.25)], volume=0.25),
            "coin": _tone([(1319, 0.05), (1760, 0.1)], volume=0.2),
            "chest": _tone([(523, 0.08), (659, 0.08), (784, 0.08), (1047, 0.08), (1319, 0.3)], volume=0.3),
            "click": _tone([(660, 0.02)], volume=0.1),
        })
    return SOUND_RECIPES


class SoundBoard:
    def __init__(self, muted: bool = False) -> None:
        self.muted = muted
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)
            _, _, channels = pygame.mixer.get_init()
            for name, mono in _recipes().items():
                data = np.column_stack([mono] * channels) if channels > 1 else mono
                self.sounds[name] = pygame.sndarray.make_sound(np.ascontiguousarray(data))
        except (pygame.error, TypeError, ValueError):
            self.sounds = {}

    def play(self, name: str) -> None:
        if self.muted:
            return
        sound = self.sounds.get(name)
        if sound is not None:
            sound.play()
