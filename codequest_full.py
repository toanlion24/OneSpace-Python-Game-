"""CodeQuest - học Python Basic qua trò chơi (bản gộp một file).

Cách chạy:   pip install pygame-ce   rồi   python codequest_full.py
Cần thư mục gamekit/ (hình ảnh) nằm cùng chỗ với file này.
File được tạo tự động từ package codequest/ bằng merge_single_file.py.
"""

from __future__ import annotations

import ast
import colorsys
import copy
import ctypes
import json
import keyword
import math
import os
import random
import re
import sys
import threading
import time
import traceback
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import pygame

# ======================================================================
# telex.py
# ======================================================================

TONE_KEYS = "sfrxj"
TONED_VOWELS: dict[str, str] = {
    "a": "aáàảãạ",
    "ă": "ăắằẳẵặ",
    "â": "âấầẩẫậ",
    "e": "eéèẻẽẹ",
    "ê": "êếềểễệ",
    "i": "iíìỉĩị",
    "o": "oóòỏõọ",
    "ô": "ôốồổỗộ",
    "ơ": "ơớờởỡợ",
    "u": "uúùủũụ",
    "ư": "ưứừửữự",
    "y": "yýỳỷỹỵ",
}
MARKED_BASES = set("ăâêôơư")

CHAR_TO_BASE_TONE: dict[str, tuple[str, int]] = {}
for _base, _forms in TONED_VOWELS.items():
    for _tone, _char in enumerate(_forms):
        CHAR_TO_BASE_TONE[_char] = (_base, _tone)
        CHAR_TO_BASE_TONE[_char.upper()] = (_base.upper(), _tone)


def is_vowel(char: str) -> bool:
    return char in CHAR_TO_BASE_TONE


def split_char(char: str) -> tuple[str, int]:
    return CHAR_TO_BASE_TONE.get(char, (char, 0))


def compose(base: str, tone: int) -> str:
    lower = base.lower()
    if lower not in TONED_VOWELS:
        return base
    char = TONED_VOWELS[lower][tone]
    return char.upper() if base.isupper() else char


def _vowel_span(word: str) -> tuple[int, int] | None:
    """Return [start, end) of the last vowel cluster, treating qu/gi as consonants."""
    end = None
    for index in range(len(word) - 1, -1, -1):
        if is_vowel(word[index]):
            end = index + 1
            break
    if end is None:
        return None
    start = end - 1
    while start > 0 and is_vowel(word[start - 1]):
        start -= 1
    head = word[: start + 1].lower()
    if end - start > 1 and head.endswith(("qu", "gi")):
        base_start = split_char(word[start])[0].lower()
        if base_start in ("u", "i"):
            start += 1
    return start, end


def _tone_position(word: str) -> int | None:
    span = _vowel_span(word)
    if span is None:
        return None
    start, end = span
    bases = [split_char(char)[0].lower() for char in word[start:end]]
    marked = [index for index, base in enumerate(bases) if base in MARKED_BASES]
    if marked:
        return start + marked[-1]
    length = end - start
    if length == 1:
        return start
    if end < len(word):
        return end - 1
    if length == 3:
        return start + 1
    if "".join(bases) in ("oa", "oe", "uy"):
        return start + 1
    return start


def current_tone(word: str) -> int:
    for char in word:
        tone = split_char(char)[1]
        if tone:
            return tone
    return 0


def strip_tones(word: str) -> str:
    return "".join(compose(*_strip(char)) for char in word)


def _strip(char: str) -> tuple[str, int]:
    base, _tone = split_char(char)
    return base, 0


def apply_tone(word: str, tone: int) -> str:
    plain = strip_tones(word)
    if tone == 0:
        return plain
    position = _tone_position(plain)
    if position is None:
        return plain
    base, _ = split_char(plain[position])
    return plain[:position] + compose(base, tone) + plain[position + 1 :]


def _replace_base(word: str, index: int, new_base: str) -> str:
    base, tone = split_char(word[index])
    if base.isupper():
        new_base = new_base.upper()
    return word[:index] + compose(new_base, tone) + word[index + 1 :]


def _modify_vowels(word: str, key: str) -> str | None:
    span = _vowel_span(word)
    lower_key = key.lower()
    if lower_key == "w":
        if span is None:
            return None
        start, end = span
        bases = [split_char(char)[0].lower() for char in word[start:end]]
        joined = "".join(bases)
        if "uo" in joined:
            offset = joined.index("uo")
            word = _replace_base(word, start + offset, "ư")
            return _replace_base(word, start + offset + 1, "ơ")
        for index in range(end - 1, start - 1, -1):
            base = split_char(word[index])[0].lower()
            mapping = {"a": "ă", "o": "ơ", "u": "ư"}
            if base in mapping:
                return _replace_base(word, index, mapping[base])
        return None

    if span is None:
        return None
    start, end = span
    for index in range(end - 1, start - 1, -1):
        base = split_char(word[index])[0].lower()
        if base == lower_key:
            return _replace_base(word, index, {"a": "â", "e": "ê", "o": "ô"}[lower_key])
    return None


def telex_key(word: str, key: str) -> str:
    """Return the new word after typing `key` at the end of `word`."""
    lower_key = key.lower()
    tone = current_tone(word)

    if lower_key in TONE_KEYS and _vowel_span(word) is not None:
        new_tone = TONE_KEYS.index(lower_key) + 1
        if tone == new_tone:
            return apply_tone(word, 0) + key
        return apply_tone(word, new_tone)

    if lower_key == "z" and tone:
        return apply_tone(word, 0)

    if lower_key == "d" and word and word[-1] in "dD" and len(word) == 1:
        return "Đ" if word[-1] == "D" else "đ"
    if lower_key == "d" and word[:1] in ("d", "D") and "đ" not in word.lower():
        return ("Đ" if word[0] == "D" else "đ") + word[1:]

    if lower_key in "aeow":
        modified = _modify_vowels(word, key)
        if modified is not None and modified != word:
            return apply_tone(modified, tone) if tone else modified
        if lower_key == "w":
            return word + ("Ư" if key.isupper() else "ư")

    appended = word + key
    return apply_tone(appended, tone) if tone else appended


def is_word_char(char: str) -> bool:
    return char.isalpha()


# ======================================================================
# variants.py
# ======================================================================

VARIANTS: dict[str, list[dict[str, Any]]] = {'4-3': [{'rows': ['################', '#@.G.G..G.G...E#', '################']}],
 '5-1': [{'extra_globals': {'secret': '75'}, 'door_code': 75}],
 '5-2': [{'extra_globals': {'a': '45', 'b': '63'}, 'door_code': 108}],
 '5-4': [{'extra_globals': {'room': 10}, 'door_code': 'Phòng 10'}],
 '6-3': [{'extra_globals': {'base': 24}, 'door_code': 48}],
 '7-1': [{'extra_globals': {'scroll': 'abc75xyz'}, 'door_code': 75}],
 '7-6': [{'extra_globals': {'note': 'Mật mã ở cuối thư: 75'}, 'door_code': 75}],
 '8-1': [{'rows': ['############', '#@.G##...G.#', '#.##..#.##.#', '#..G..G...E#', '############']}],
 '8-2': [{'rows': ['#############', '#@..r.......#', '#.r......r..#', '#..........E#', '#############']}],
 '8-6': [{'rows': ['##########', '#@..Q....#', '#........#', '#..Q...O.#', '#.......E#', '##########']}],
 '9-1': [{'rows': ['############', '#@..r...b..#', '#..........#', '#....c....E#', '############']}],
 '9-3': [{'extra_globals': {'prices': {'táo': 8, 'cam': 10, 'lê': 7}}, 'door_code': 23}],
 '10-3': [{'extra_globals': {'numbers': [4, 5, 6, 7]}, 'door_code': 126}],
 '10-4': [{'extra_globals': {'table': [[4, 5], [6, 7], [8, 9]]}, 'door_code': 39}],
 '10-5': [{'rows': ['##########', '#@..##..G#', '#.#....#.#', '#G..##..E#', '##########']}],
 '10-6': [{'rows': ['##########', '#.C..C.C.#', '#@.......#', '#.......E#', '##########']}],
 '11-6': [{'rows': ['###########', '#@.O..QO.E#', '###########']}],
 '12-1': [{'extra_globals': {'a': 9, 'b': 11}, 'door_code': 14}],
 '12-2': [{'extra_globals': {'candies': 87, 'cakes': 39}, 'door_code': 3}],
 '12-4': [{'extra_globals': {'r': 8}, 'door_code': 201}],
 '13-5': [{'extra_globals': {'coins': [4, 5, 8, 13]}, 'door_code': 6}],
 '14-5': [{'extra_globals': {'scores': [8, 11, 5, 12, 7]}, 'door_code': 24}],
 '16-3': [{'extra_globals': {'candidates': ['0x', '??', '75', 'abc']}, 'door_code': 75}],
 '16-4': [{'extra_globals': {'pairs': [(13, 5), (8, 3), (12, 6)]}, 'door_code': 6}],
 '17-4': [{'extra_globals': {'coins': [8, 13, 5]}, 'door_code': 26}],
 '18-3': [{'extra_globals': {'scroll': 'x0y6z2'}, 'door_code': 8}],
 '18-5': [{'extra_globals': {'candidates': ['7', 'x', '7', '0', '??', '5']}, 'door_code': 12}],
 '18-6': [{'rows': ['##############', '#@.O.k..r.L.E#', '###########C##']}],
 '19-1': [{'extra_globals': {'raw': ['6', 'x', '8', '?', '0']}, 'door_code': 14}],
 '19-2': [{'rows': ['############', '#@.r..b.c..#', '#..........#', '#.........E#', '############']}],
 '19-6': [{'rows': ['##########', '#C...C..C#', '#........#', '#@......E#', '##########']}],
 '20-1': [{'extra_globals': {'letter': 'Kho báu ở phòng 45. Mật mã là 7530, đừng nhầm với 22!'},
           'door_code': 7530}],
 '20-3': [{'extra_globals': {'letter': 'Ngọc: 6 đỏ, 8 xanh, 5 vàng'}, 'door_code': 19}],
 '20-6': [{'extra_globals': {'letter': 'Rương ở hướng up, cửa mã 0647.'}, 'door_code': 647}],
 '22-1': [{'extra_globals': {'scores': [[4, 5, 6], [7, 8, 9]]}, 'door_code': 39}],
 '22-2': [{'extra_globals': {'matrix_a': [[4, 5], [6, 7]], 'matrix_b': [[5, 3], [4, 5]]}, 'door_code': 188}],
 '22-3': [{'extra_globals': {'temps': [23, 25, 27, 29, 31]}, 'door_code': 27}],
 '22-4': [{'extra_globals': {'scores': [6, 10, 11, 5, 12, 9]}, 'door_code': 5}],
 '22-6': [{'extra_globals': {'weights': [[6, 11], [9, 5]]}, 'door_code': 11}],
 '23-2': [{'rows': ['############', '#@..r...b..#', '#..........#', '#....c....E#', '############']}]}


# ======================================================================
# engine.py
# ======================================================================

DIRECTIONS: dict[str, tuple[int, int]] = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}

ENEMY_CHARS: dict[str, str] = {
    "r": "robot",
    "b": "barrel",
    "c": "cannon",
    "x": "spikebox",
    "B": "duck",
}

ENEMY_WEAKNESS: dict[str, str] = {
    "robot": "hammer",
    "barrel": "axe",
    "cannon": "bow",
    "spikebox": "staff",
    "duck": "sword",
}

ENEMY_HP: dict[str, int] = {"duck": 3}

TYPE_NAMES: dict[type, str] = {
    int: "số nguyên (int)",
    str: "chuỗi (str)",
    float: "số thực (float)",
    tuple: "tuple",
    list: "list",
    bool: "bool",
}

BLOCKING_REASONS: dict[str, str] = {
    "wall": "Đụng tường!",
    "door": "Cửa đang đóng!",
    "box": "Thùng gỗ chắn đường - đập vỡ bằng hero.attack(...).",
    "lock": "Cửa khoá - dùng hero.unlock(...) khi đã có chìa.",
    "chest": "Rương báu chắn đường - mở bằng hero.open_chest(...).",
}

MAX_HERO_HP = 3
MAX_ACTIONS = 1500
MAX_TRACED_LINES = 30_000
MAX_RUN_SECONDS = 4.0
CODE_FILENAME = "<code>"


class DoorJammed(Exception):
    """Cửa bị kẹt - hãy thử lại."""


class HeroDefeated(BaseException):
    """Hero thất bại (không thể bị bắt bằng `except Exception`)."""


class StepLimitExceeded(BaseException):
    """Chương trình chạy quá lâu (có thể bị lặp vô hạn)."""


@dataclass
class Level:
    id: str
    title: str
    story: str
    goal: str
    rows: list[str]
    starter: str
    hints: list[str]
    requires: list[str] = field(default_factory=list)
    extra_globals: dict[str, Any] = field(default_factory=dict)
    door_code: Any = None
    jams: int = 0
    weapons: bool = False
    kill_all: bool = False
    say_contains: str | None = None
    start_hp: int = MAX_HERO_HP
    need_full_hp: bool = False
    need_chests: int = 0


@dataclass
class Enemy:
    kind: str
    hp: int


@dataclass
class RunResult:
    events: list[dict[str, Any]]
    won: bool
    message: str
    error_line: int | None = None
    damage_taken: int = 0
    code_lines: int = 0
    chests_opened: int = 0
    # Bản đồ kiểm tra ẩn: số bản đồ đã vượt, hoặc bản đồ đầu tiên bị sai.
    hidden_passed: int = 0
    hidden_failure: HiddenFailure | None = None


@dataclass
class HiddenFailure:
    """Code thắng ở bản đồ chính nhưng thua ở một bản đồ kiểm tra ẩn."""

    index: int
    level: Level
    events: list[dict[str, Any]]
    reason: str
    error_line: int | None
    changed_data: dict[str, Any]


def hidden_levels(level: Level) -> list[tuple[Level, dict[str, Any]]]:
    """Các bản đồ kiểm tra ẩn của màn: (màn biến thể, dữ liệu đã đổi)."""
    variants = []
    for variant in VARIANTS.get(level.id, []):
        changes: dict[str, Any] = {}
        if "rows" in variant:
            changes["rows"] = list(variant["rows"])
        changed_data: dict[str, Any] = {}
        if "extra_globals" in variant:
            changes["extra_globals"] = {**level.extra_globals, **variant["extra_globals"]}
            changed_data = dict(variant["extra_globals"])
        if "door_code" in variant:
            changes["door_code"] = variant["door_code"]
        variants.append((replace(level, **changes), changed_data))
    return variants


def describe_hidden_failure(failure: HiddenFailure) -> str:
    message = f"Code đúng ở bản đồ này nhưng SAI ở bản đồ kiểm tra ẩn {failure.index}: {failure.reason}"
    if failure.changed_data:
        shown = ", ".join(f"{name} = {value!r}" for name, value in failure.changed_data.items())
        return f"{message} Ở bản đồ ẩn, dữ liệu khác đi: {shown}. Đừng gõ thẳng đáp án - hãy tính từ biến."
    return (
        f"{message} Bản đồ ẩn dài / rộng hơn một chút: đừng đếm số ô cố định, "
        "hãy dùng vòng lặp với hero.look(...), find_gems(), exit_position..."
    )


def upgrades_apply(level: Level) -> bool:
    """Shop upgrades (extra hearts, shield) are off in levels that are about healing."""
    return not level.need_full_hp and level.start_hp == MAX_HERO_HP


def hero_hp_limits(level: Level, bonus_hp: int = 0) -> tuple[int, int]:
    """(starting hp, maximum hp) for a level, including shop upgrades when they apply."""
    if not upgrades_apply(level):
        return level.start_hp, MAX_HERO_HP
    return MAX_HERO_HP + bonus_hp, MAX_HERO_HP + bonus_hp


def count_code_lines(source: str) -> int:
    """Lines that contain code (blank lines and comment-only lines do not count)."""
    return sum(1 for line in source.split("\n") if line.strip() and not line.strip().startswith("#"))


class World:
    """Rules and state of one level."""

    def __init__(self, level: Level, bonus_hp: int = 0, shield: bool = False) -> None:
        self.level = level
        self.rows = level.rows
        self.height = len(level.rows)
        self.width = max(len(row) for row in level.rows)
        self.terrain: dict[tuple[int, int], str] = {}
        self.gems: dict[tuple[int, int], int] = {}
        self.enemies: dict[tuple[int, int], Enemy] = {}
        self.doors: dict[tuple[int, int], str] = {}
        self.jam_left: dict[tuple[int, int], int] = {}
        # Vật thể mới: thùng gỗ (True = có ngọc bên trong), chìa khoá, cửa khoá, rương báu.
        self.crates: dict[tuple[int, int], bool] = {}
        self.keys_on_map: set[tuple[int, int]] = set()
        self.locks: set[tuple[int, int]] = set()
        self.chests: dict[tuple[int, int], bool] = {}
        self.exit_position: tuple[int, int] = (0, 0)
        self.hero_start: tuple[int, int] = (0, 0)
        self._parse()

        self.hero_x, self.hero_y = self.hero_start
        self.facing = "right"
        self.hp, self.max_hp = hero_hp_limits(level, bonus_hp)
        self.shield = shield and upgrades_apply(level)
        self.damage_taken = 0
        self.gems_collected = 0
        self.keys = 0
        self.chests_opened = 0
        self.events: list[dict[str, Any]] = []
        self.messages: list[str] = []
        self.actions = 0

    def _parse(self) -> None:
        for y, row in enumerate(self.rows):
            for x in range(self.width):
                char = row[x] if x < len(row) else " "
                pos = (x, y)
                self.terrain[pos] = "wall" if char in "# " else "floor"
                if char == "@":
                    self.hero_start = pos
                elif char == "E":
                    self.exit_position = pos
                    self.terrain[pos] = "exit"
                elif char == "^":
                    self.terrain[pos] = "spike"
                elif char == "G":
                    self.gems[pos] = 1
                elif char in "123456":
                    self.gems[pos] = int(char)
                elif char == "D":
                    self.doors[pos] = "locked"
                elif char == "J":
                    self.doors[pos] = "jammed"
                    self.jam_left[pos] = self.level.jams
                elif char in ENEMY_CHARS:
                    kind = ENEMY_CHARS[char]
                    self.enemies[pos] = Enemy(kind, ENEMY_HP.get(kind, 1))
                elif char == "O":
                    self.crates[pos] = False
                elif char == "Q":
                    self.crates[pos] = True
                elif char == "k":
                    self.keys_on_map.add(pos)
                elif char == "L":
                    self.locks.add(pos)
                elif char == "C":
                    self.chests[pos] = False

    # ----------------------------------------------------------- helpers
    def emit(self, event_type: str, **data: Any) -> None:
        self.events.append({"type": event_type, **data})

    def count_action(self) -> None:
        self.actions += 1
        if self.actions > MAX_ACTIONS:
            raise StepLimitExceeded("Hero đã thực hiện quá nhiều lệnh.")

    def tile_name(self, pos: tuple[int, int]) -> str:
        if pos in self.enemies:
            return "enemy"
        if pos in self.doors:
            return "door"
        if pos in self.crates:
            return "box"
        if pos in self.locks:
            return "lock"
        if pos in self.chests:
            return "chest"
        if pos in self.gems:
            return "gem"
        if pos in self.keys_on_map:
            return "key"
        return self.terrain.get(pos, "wall")

    def is_blocking_object(self, pos: tuple[int, int]) -> bool:
        return pos in self.enemies or pos in self.doors or pos in self.crates or pos in self.locks or pos in self.chests

    def is_walkable(self, pos: tuple[int, int]) -> bool:
        if self.is_blocking_object(pos):
            return False
        return self.terrain.get(pos, "wall") in ("floor", "exit")

    def neighbor(self, direction: str) -> tuple[int, int]:
        dx, dy = DIRECTIONS[direction]
        return (self.hero_x + dx, self.hero_y + dy)

    def check_direction(self, direction: Any) -> str:
        if direction not in DIRECTIONS:
            raise ValueError(
                f"Hướng '{direction}' không hợp lệ. Dùng 'up', 'down', 'left' hoặc 'right'."
            )
        return direction

    def hurt(self, reason: str) -> None:
        if self.shield:
            self.shield = False
            self.emit("shield", text=f"Khiên đỡ đòn! ({reason})")
            return
        self.damage_taken += 1
        self.hp -= 1
        self.emit("hurt", hp=self.hp, text=reason)
        if self.hp <= 0:
            raise HeroDefeated("Hero hết máu!")

    # ----------------------------------------------------------- actions
    def step(self, direction: str) -> bool:
        self.check_direction(direction)
        self.count_action()
        self.facing = direction
        target = self.neighbor(direction)
        name = self.tile_name(target)
        origin = (self.hero_x, self.hero_y)

        if name == "enemy":
            self.emit("bump", pos=origin, direction=direction)
            self.hurt("Quái chặn đường! Hãy dùng hero.attack().")
            return False
        if name in BLOCKING_REASONS:
            self.emit("bump", pos=origin, direction=direction)
            self.emit("info", text=BLOCKING_REASONS[name])
            return False

        self.hero_x, self.hero_y = target
        self.emit("move", src=origin, dst=target, direction=direction)
        if name == "spike":
            self.emit("die", text="Hero dẫm phải gai!")
            raise HeroDefeated("Hero dẫm phải gai!")
        if target in self.gems:
            color = self.gems.pop(target)
            self.gems_collected += 1
            self.emit("gem", pos=target, color=color)
        if target in self.keys_on_map:
            self.keys_on_map.discard(target)
            self.keys += 1
            self.emit("key", pos=target, keys=self.keys)
        return True

    def move(self, direction: str, steps: Any) -> None:
        if isinstance(steps, bool) or not isinstance(steps, int):
            raise TypeError(
                f"Số bước phải là số nguyên (int), nhưng bạn đưa kiểu '{type(steps).__name__}'."
            )
        for _ in range(steps):
            if not self.step(direction):
                return

    def attack(self, direction: str | None, weapon: str | None) -> None:
        if direction is not None:
            self.check_direction(direction)
            self.facing = direction
        direction = self.facing
        self.count_action()
        target = self.neighbor(direction)
        enemy = self.enemies.get(target)
        if enemy is None and target in self.crates:
            has_gem = self.crates.pop(target)
            self.emit("attack", direction=direction, target=target, hit=False)
            self.emit("box_break", pos=target)
            if has_gem:
                self.gems[target] = 2
                self.emit("gem_reveal", pos=target, color=2)
            return
        if enemy is None:
            self.emit("attack", direction=direction, target=target, hit=False)
            self.emit("info", text="Đòn đánh trượt - không có quái ở đó.")
            return

        if self.level.weapons and weapon != ENEMY_WEAKNESS[enemy.kind]:
            self.emit("attack", direction=direction, target=target, hit=False)
            self.hurt(f"Sai vũ khí! {enemy.kind} không sợ '{weapon}'.")
            return

        enemy.hp -= 1
        killed = enemy.hp <= 0
        if killed:
            del self.enemies[target]
        self.emit("attack", direction=direction, target=target, hit=True, killed=killed)

    def _check_code_type(self, value: Any) -> Any:
        expected = self.level.door_code
        if isinstance(expected, tuple) and isinstance(value, list):
            value = tuple(value)
        if isinstance(expected, int) and hasattr(value, "item") and not isinstance(value, bool):
            # Số của NumPy (numpy.int64...) được chấp nhận như int.
            value = value.item()
        same_type = type(value) is type(expected) or (
            isinstance(expected, int) and isinstance(value, int) and not isinstance(value, bool)
        )
        if not same_type:
            raise TypeError(
                f"Mật mã phải là kiểu {TYPE_NAMES.get(type(expected), type(expected).__name__)}, "
                f"nhưng bạn đưa kiểu {TYPE_NAMES.get(type(value), type(value).__name__)}."
            )
        return value

    def _adjacent_locked_door(self) -> tuple[int, int] | None:
        for direction in DIRECTIONS:
            pos = self.neighbor(direction)
            if self.doors.get(pos) == "locked":
                return pos
        return None

    def enter_code(self, value: Any) -> None:
        value = self._check_code_type(value)
        self.count_action()
        pos = self._adjacent_locked_door()
        if pos is None:
            self.emit("info", text="Không có cửa khóa ở gần hero.")
            return
        if value == self.level.door_code:
            del self.doors[pos]
            self.emit("door_open", pos=pos)
        else:
            self.emit("info", text=f"Mật mã {value!r} sai!")
            self.hurt("Sai mật mã!")

    def try_code(self, value: Any) -> bool:
        """Thử mật mã mà không mất máu - dùng cho khoá rune nhiều lần thử."""
        value = self._check_code_type(value)
        self.count_action()
        pos = self._adjacent_locked_door()
        if pos is None:
            self.emit("info", text="Không có cửa khóa ở gần hero.")
            return False
        if value == self.level.door_code:
            del self.doors[pos]
            self.emit("door_open", pos=pos)
            return True
        self.emit("info", text=f"Thử {value!r}: chưa đúng.")
        return False

    def unlock(self, direction: str) -> None:
        self.check_direction(direction)
        self.facing = direction
        self.count_action()
        pos = self.neighbor(direction)
        if pos not in self.locks:
            self.emit("info", text="Không có cửa khoá ở hướng đó.")
            return
        if self.keys <= 0:
            raise ValueError("Chưa có chìa khoá! Hãy nhặt chìa (k) trước khi mở cửa khoá.")
        self.keys -= 1
        self.locks.discard(pos)
        self.emit("unlock", pos=pos, keys=self.keys)

    def open_chest(self, direction: str) -> None:
        self.check_direction(direction)
        self.facing = direction
        self.count_action()
        pos = self.neighbor(direction)
        if pos not in self.chests:
            self.emit("info", text="Không có rương ở hướng đó.")
            return
        if self.chests[pos]:
            self.emit("info", text="Rương này đã mở rồi.")
            return
        self.chests[pos] = True
        self.chests_opened += 1
        self.emit("chest_open", pos=pos)

    def find_objects(self, name: Any) -> list[dict[str, Any]]:
        tables: dict[str, Any] = {
            "gem": self.gems,
            "enemy": self.enemies,
            "box": self.crates,
            "key": self.keys_on_map,
            "lock": self.locks,
            "chest": {pos for pos, opened in self.chests.items() if not opened},
            "door": self.doors,
        }
        if name not in tables:
            raise ValueError(f"Không biết vật thể '{name}'. Dùng: {', '.join(tables)}.")
        positions = sorted(tables[name], key=lambda pos: (pos[1], pos[0]))
        return [{"x": x, "y": y} for x, y in positions]

    def use(self, item: Any) -> None:
        power = getattr(item, "power", None)
        if isinstance(power, bool) or not isinstance(power, int):
            raise TypeError("Vật phẩm cần có thuộc tính power là số nguyên (ví dụ self.power = 2).")
        self.count_action()
        healed = max(0, min(self.max_hp, self.hp + power) - self.hp)
        self.hp += healed
        self.emit("heal", hp=self.hp, amount=healed)

    def move_by(self, vector: Any) -> None:
        if not hasattr(vector, "x") or not hasattr(vector, "y"):
            raise TypeError("move_by cần một đối tượng có thuộc tính x và y.")
        dx, dy = vector.x, vector.y
        self.move("right" if dx >= 0 else "left", abs(dx))
        self.move("down" if dy >= 0 else "up", abs(dy))

    def follow(self, path: Any) -> None:
        try:
            iterator = iter(path)
        except TypeError:
            raise TypeError("follow cần một thứ duyệt được (list, hoặc class có __iter__).") from None
        for direction in iterator:
            if not self.step(self.check_direction(direction)):
                return

    def scan(self) -> list[list[str]]:
        grid = [[self.tile_name((x, y)) for x in range(self.width)] for y in range(self.height)]
        grid[self.hero_y][self.hero_x] = "hero"
        return grid

    def open_door(self, direction: str) -> None:
        self.check_direction(direction)
        self.facing = direction
        self.count_action()
        pos = self.neighbor(direction)
        if self.doors.get(pos) != "jammed":
            self.emit("info", text="Không có cửa kẹt ở hướng đó.")
            return
        if self.jam_left[pos] > 0:
            self.jam_left[pos] -= 1
            self.emit("jam", pos=pos)
            raise DoorJammed("Cửa bị kẹt!")
        del self.doors[pos]
        self.emit("door_open", pos=pos)

    def look(self, direction: str) -> str:
        self.check_direction(direction)
        return self.tile_name(self.neighbor(direction))

    # ----------------------------------------------------------- pathing
    def find_path(
        self, goals: set[tuple[int, int]], avoid_spikes: bool = True
    ) -> list[tuple[int, int]] | None:
        start = (self.hero_x, self.hero_y)
        if start in goals:
            return []
        previous: dict[tuple[int, int], tuple[int, int]] = {}
        queue = deque([start])
        seen = {start}
        while queue:
            current = queue.popleft()
            for dx, dy in DIRECTIONS.values():
                nxt = (current[0] + dx, current[1] + dy)
                if nxt in seen or not self.is_walkable(nxt):
                    continue
                if avoid_spikes and self.terrain.get(nxt) == "spike" and nxt not in goals:
                    continue
                seen.add(nxt)
                previous[nxt] = current
                if nxt in goals:
                    path = [nxt]
                    while path[-1] != start:
                        path.append(previous[path[-1]])
                    path.pop()
                    return path[::-1]
                queue.append(nxt)
        return None

    def walk_path(self, path: list[tuple[int, int]]) -> None:
        for pos in path:
            dx, dy = pos[0] - self.hero_x, pos[1] - self.hero_y
            direction = next(name for name, delta in DIRECTIONS.items() if delta == (dx, dy))
            if not self.step(direction):
                return

    def move_to(self, x: Any, y: Any) -> None:
        if not isinstance(x, int) or not isinstance(y, int):
            raise TypeError("Toạ độ x, y phải là số nguyên (int).")
        goal = (x, y)
        if not self.is_walkable(goal):
            raise ValueError(f"Không thể đi tới ({x}, {y}): ô này bị chặn.")
        path = self.find_path({goal})
        if path is None:
            raise ValueError(f"Không có đường tới ({x}, {y}).")
        self.walk_path(path)

    def attack_target(self, x: Any, y: Any, weapon: str | None) -> None:
        if (x, y) not in self.enemies:
            raise ValueError(f"Không có quái ở ({x}, {y}).")
        goals = {
            (x + dx, y + dy)
            for dx, dy in DIRECTIONS.values()
            if self.is_walkable((x + dx, y + dy))
        }
        path = self.find_path(goals)
        if path is None:
            raise ValueError(f"Không có đường tới quái ở ({x}, {y}).")
        self.walk_path(path)
        for direction, (dx, dy) in DIRECTIONS.items():
            if (self.hero_x + dx, self.hero_y + dy) == (x, y):
                self.attack(direction, weapon)
                return

    # ----------------------------------------------------------- scanning
    def find_gems(self) -> list[dict[str, Any]]:
        ordered = sorted(self.gems.items(), key=lambda item: (item[0][1], item[0][0]))
        return [{"x": pos[0], "y": pos[1], "color": color} for pos, color in ordered]

    def find_enemies(self) -> list[dict[str, Any]]:
        ordered = sorted(self.enemies.items(), key=lambda item: (item[0][0], item[0][1]))
        return [{"x": pos[0], "y": pos[1], "type": enemy.kind} for pos, enemy in ordered]

    def say(self, text: Any) -> None:
        self.count_action()
        self.emit("say", text=str(text))


class HeroAPI:
    """The object the player controls through the `hero` variable."""

    def __init__(self, world: World) -> None:
        self._world = world

    # movement
    def move_up(self, steps: int = 1) -> None:
        self._world.move("up", steps)

    def move_down(self, steps: int = 1) -> None:
        self._world.move("down", steps)

    def move_left(self, steps: int = 1) -> None:
        self._world.move("left", steps)

    def move_right(self, steps: int = 1) -> None:
        self._world.move("right", steps)

    def move_to(self, x: int, y: int) -> None:
        self._world.move_to(x, y)

    # actions
    def attack(self, direction: str | None = None, weapon: str | None = None) -> None:
        self._world.attack(direction, weapon)

    def attack_target(self, x: int, y: int, weapon: str | None = None) -> None:
        self._world.attack_target(x, y, weapon)

    def say(self, text: Any) -> None:
        self._world.say(text)

    def enter_code(self, code: Any) -> None:
        self._world.enter_code(code)

    def try_code(self, code: Any) -> bool:
        return self._world.try_code(code)

    def open_door(self, direction: str) -> None:
        self._world.open_door(direction)

    def use(self, item: Any) -> None:
        self._world.use(item)

    def move_by(self, vector: Any) -> None:
        self._world.move_by(vector)

    def follow(self, path: Any) -> None:
        self._world.follow(path)

    def scan(self) -> list[list[str]]:
        return self._world.scan()

    def unlock(self, direction: str) -> None:
        self._world.unlock(direction)

    def open_chest(self, direction: str) -> None:
        self._world.open_chest(direction)

    def find_objects(self, name: str) -> list[dict[str, Any]]:
        return self._world.find_objects(name)

    @property
    def keys(self) -> int:
        return self._world.keys

    # senses
    def look(self, direction: str) -> str:
        return self._world.look(direction)

    def find_gems(self) -> list[dict[str, Any]]:
        return self._world.find_gems()

    def find_enemies(self) -> list[dict[str, Any]]:
        return self._world.find_enemies()

    @property
    def x(self) -> int:
        return self._world.hero_x

    @property
    def y(self) -> int:
        return self._world.hero_y

    @property
    def position(self) -> tuple[int, int]:
        return (self._world.hero_x, self._world.hero_y)

    @property
    def exit_position(self) -> tuple[int, int]:
        return self._world.exit_position

    @property
    def hp(self) -> int:
        return self._world.hp

    @property
    def gems_collected(self) -> int:
        return self._world.gems_collected


# ---------------------------------------------------------------- sandbox
SAFE_BUILTIN_NAMES = (
    "abs", "all", "any", "bool", "dict", "enumerate", "float", "int", "len", "list",
    "max", "min", "range", "reversed", "round", "set", "frozenset", "sorted", "str",
    "sum", "tuple", "zip", "isinstance", "map", "filter", "iter", "next", "repr",
    "chr", "ord", "divmod", "pow", "callable", "format", "hasattr", "getattr",
    "setattr", "object", "super", "property", "staticmethod", "classmethod", "type",
    "__build_class__",
    "Exception", "ValueError", "TypeError", "KeyError", "IndexError",
    "ZeroDivisionError", "ArithmeticError", "LookupError", "AttributeError",
    "RuntimeError", "NotImplementedError", "StopIteration",
    "True", "False", "None",
)

# Thư viện chuẩn (và NumPy) được phép import trong game.
ALLOWED_MODULES = {
    "math", "itertools", "collections", "datetime", "re", "functools", "operator",
    "statistics", "string", "xml", "xml.etree", "xml.etree.ElementTree", "numpy",
}


def _time_without_sleep() -> Any:
    import types

    module = types.ModuleType("time")
    for attribute in dir(time):
        if attribute != "sleep" and not attribute.startswith("__"):
            setattr(module, attribute, getattr(time, attribute))
    return module


_TIME_WITHOUT_SLEEP = _time_without_sleep()


def _safe_import(
    name: str,
    globals_: Any = None,
    locals_: Any = None,
    fromlist: Any = (),
    level: int = 0,
) -> Any:
    if level == 0 and name == "time":
        # datetime.strftime tự import "time" bên trong. Trả về bản không có sleep để
        # code học sinh không thể làm treo game.
        return _TIME_WITHOUT_SLEEP
    if level > 0:
        # Thư viện được phép (ví dụ NumPy) đôi khi tự import tương đối bên trong nó.
        package = (globals_ or {}).get("__package__") or ""
        allowed_here = package.split(".")[0] in ALLOWED_MODULES
    else:
        # Cho phép cả module con của thư viện được phép (numpy._core..., xml.etree...).
        allowed_here = name.split(".")[0] in ALLOWED_MODULES
    if not allowed_here:
        allowed = ", ".join(sorted(module for module in ALLOWED_MODULES if "." not in module))
        raise ImportError(f"Không được import '{name}'. Chỉ dùng được: {allowed}.")
    return __import__(name, globals_, locals_, fromlist, level)


def _safe_builtins(world: World) -> dict[str, Any]:
    import builtins

    safe = {name: getattr(builtins, name) for name in SAFE_BUILTIN_NAMES}

    def game_print(*values: Any, sep: str = " ", end: str = "\n") -> None:
        world.emit("print", text=sep.join(str(value) for value in values))

    safe["print"] = game_print
    safe["__import__"] = _safe_import
    return safe


def _is_closure(node: ast.AST) -> bool:
    """A function that defines an inner function and returns it."""
    if not isinstance(node, ast.FunctionDef):
        return False
    inner_names = {child.name for child in node.body if isinstance(child, ast.FunctionDef)}
    return any(
        isinstance(child, ast.Return) and isinstance(child.value, ast.Name) and child.value.id in inner_names
        for child in ast.walk(node)
    )


OPERATOR_TOKENS: dict[str, type] = {
    "&": ast.BitAnd, "|": ast.BitOr, "-": ast.Sub, "@": ast.MatMult, "^": ast.BitXor,
}


def _has_nested_for(nodes: list[ast.AST]) -> bool:
    return any(
        isinstance(n, ast.For) and any(isinstance(inner, ast.For) for inner in ast.walk(n) if inner is not n)
        for n in nodes
    )


def _has_method(nodes: list[ast.AST]) -> bool:
    return any(
        isinstance(n, ast.ClassDef)
        and any(isinstance(item, ast.FunctionDef) and not item.name.startswith("__") for item in n.body)
        for n in nodes
    )


def _check_one(requirement: str, nodes: list[ast.AST], call_names: set[str], imported: set[str]) -> bool:
    if requirement.startswith("call:"):
        return requirement[5:] in call_names
    if requirement.startswith("import:"):
        return requirement[7:] in imported
    if requirement.startswith("dunder:"):
        name = requirement[7:]
        return any(isinstance(n, ast.FunctionDef) and n.name == name for n in nodes)
    if requirement.startswith("except:"):
        name = requirement[7:]
        return any(
            isinstance(n, ast.ExceptHandler) and isinstance(n.type, ast.Name) and n.type.id == name for n in nodes
        )
    if requirement.startswith("op:"):
        operator_type = OPERATOR_TOKENS[requirement[3:]]
        return any(isinstance(n, ast.BinOp) and isinstance(n.op, operator_type) for n in nodes)
    return REQUIREMENT_CHECKS[requirement](nodes, call_names)


REQUIREMENT_CHECKS: dict[str, Any] = {
    "for": lambda nodes, calls: any(isinstance(n, ast.For) for n in nodes),
    "while": lambda nodes, calls: any(isinstance(n, ast.While) for n in nodes),
    "if": lambda nodes, calls: any(isinstance(n, ast.If) for n in nodes),
    "def": lambda nodes, calls: any(isinstance(n, ast.FunctionDef) for n in nodes),
    "return": lambda nodes, calls: any(isinstance(n, ast.Return) for n in nodes),
    "try": lambda nodes, calls: any(isinstance(n, ast.Try) for n in nodes),
    "dict": lambda nodes, calls: any(isinstance(n, ast.Dict) for n in nodes) or "dict" in calls,
    "list": lambda nodes, calls: any(isinstance(n, ast.List) for n in nodes) or "list" in calls,
    "set": lambda nodes, calls: any(isinstance(n, ast.Set) for n in nodes) or "set" in calls,
    "assign": lambda nodes, calls: any(isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)) for n in nodes),
    "listcomp": lambda nodes, calls: any(
        isinstance(n, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)) for n in nodes
    ),
    "slice": lambda nodes, calls: any(isinstance(n, ast.Slice) for n in nodes),
    "fstring": lambda nodes, calls: any(isinstance(n, ast.JoinedStr) for n in nodes),
    "lambda": lambda nodes, calls: any(isinstance(n, ast.Lambda) for n in nodes),
    "class": lambda nodes, calls: any(isinstance(n, ast.ClassDef) for n in nodes),
    "decorator": lambda nodes, calls: any(
        isinstance(n, ast.FunctionDef) and n.decorator_list for n in nodes
    ),
    "closure": lambda nodes, calls: any(_is_closure(n) for n in nodes),
    "boolop": lambda nodes, calls: any(isinstance(n, ast.BoolOp) for n in nodes),
    "nested_for": lambda nodes, calls: _has_nested_for(nodes),
    "subscript": lambda nodes, calls: any(
        isinstance(n, ast.Subscript) and not isinstance(n.slice, ast.Slice) for n in nodes
    ),
    "membership": lambda nodes, calls: any(
        isinstance(n, ast.Compare) and any(isinstance(op, (ast.In, ast.NotIn)) for op in n.ops) for n in nodes
    ),
    "subset": lambda nodes, calls: "issubset" in calls or any(
        isinstance(n, ast.Compare) and any(isinstance(op, (ast.LtE, ast.GtE)) for op in n.ops) for n in nodes
    ),
    "method": lambda nodes, calls: _has_method(nodes),
    "raise": lambda nodes, calls: any(isinstance(n, ast.Raise) for n in nodes),
    "except_value_error": lambda nodes, calls: any(
        isinstance(n, ast.ExceptHandler) and isinstance(n.type, ast.Name) and n.type.id == "ValueError"
        for n in nodes
    ),
}

REQUIREMENT_LABELS: dict[str, str] = {
    "for": "vòng lặp for",
    "while": "vòng lặp while",
    "if": "câu lệnh if",
    "def": "định nghĩa hàm (def)",
    "return": "lệnh return",
    "try": "khối try/except",
    "dict": "từ điển (dict)",
    "list": "danh sách (list)",
    "set": "tập hợp (set)",
    "assign": "biến (phép gán =)",
    "listcomp": "list comprehension [... for ... in ...]",
    "slice": "cắt chuỗi/list [a:b]",
    "fstring": "f-string f\"...{...}\"",
    "lambda": "hàm lambda",
    "class": "định nghĩa class",
    "decorator": "decorator @...",
    "closure": "closure (hàm trả về hàm bên trong)",
    "boolop": "and / or",
    "nested_for": "vòng lặp for lồng nhau",
    "subscript": "lấy phần tử theo vị trí [i]",
    "membership": "toán tử in",
    "subset": "kiểm tra tập con (issubset hoặc <=)",
    "method": "phương thức tự viết trong class",
    "raise": "lệnh raise",
    "except_value_error": "except ValueError",
}


def requirement_label(requirement: str) -> str:
    """Human-readable Vietnamese label for a requirement token (alternatives separated by ' or ')."""
    parts = []
    for option in requirement.split(" or "):
        if option.startswith("call:"):
            parts.append(f"{option[5:]}(...)")
        elif option.startswith("import:"):
            parts.append(f"import {option[7:]}")
        elif option.startswith("dunder:"):
            parts.append(f"phương thức {option[7:]}")
        elif option.startswith("op:"):
            parts.append(f"toán tử {option[3:]}")
        elif option.startswith("except:"):
            parts.append(f"except {option[7:]}")
        else:
            parts.append(REQUIREMENT_LABELS[option])
    return " hoặc ".join(parts)


def _check_requirements(tree: ast.AST, requires: list[str]) -> list[str]:
    nodes = list(ast.walk(tree))
    call_names: set[str] = set()
    imported: set[str] = set()
    for node in nodes:
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                call_names.add(func.id)
            elif isinstance(func, ast.Attribute):
                call_names.add(func.attr)
        elif isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    return [
        requirement_label(requirement)
        for requirement in requires
        if not any(_check_one(option, nodes, call_names, imported) for option in requirement.split(" or "))
    ]


def _error_line(exc: BaseException) -> int | None:
    line = None
    for frame in traceback.extract_tb(exc.__traceback__):
        if frame.filename == CODE_FILENAME:
            line = frame.lineno
    return line


def explain_error(exc: BaseException, line: int | None) -> str:
    where = f"Dòng {line}: " if line else ""
    if isinstance(exc, NameError):
        return f"{where}Python không biết tên '{getattr(exc, 'name', '?')}'. Kiểm tra chính tả hoặc khai báo biến trước khi dùng."
    if isinstance(exc, AttributeError):
        return f"{where}Không có lệnh / thuộc tính '{getattr(exc, 'name', '?')}'. Kiểm tra chính tả tên lệnh."
    if isinstance(exc, ZeroDivisionError):
        return f"{where}Không thể chia cho 0."
    if isinstance(exc, DoorJammed):
        return f"{where}Cửa bị kẹt! Hãy bọc lệnh trong try/except DoorJammed."
    if isinstance(exc, TypeError):
        return f"{where}Sai kiểu dữ liệu - {exc}"
    if isinstance(exc, KeyError):
        return f"{where}Không tìm thấy khoá {exc} trong từ điển."
    if isinstance(exc, IndexError):
        return f"{where}Chỉ số nằm ngoài danh sách."
    if isinstance(exc, ValueError):
        return f"{where}{exc}"
    if isinstance(exc, ImportError):
        return f"{where}{exc}"
    return f"{where}{type(exc).__name__}: {exc}"


def explain_syntax_error(exc: SyntaxError) -> str:
    line = exc.lineno or "?"
    if isinstance(exc, IndentationError):
        return f"Dòng {line}: Lỗi thụt lề - kiểm tra số khoảng trắng đầu dòng."
    return f"Dòng {line}: Sai cú pháp ({exc.msg}). Kiểm tra dấu ngoặc, dấu hai chấm, dấu nháy."


def run_code(
    level: Level, source: str, bonus_hp: int = 0, shield: bool = False, check_hidden: bool = True
) -> RunResult:
    """Run the player's code against the level, then against its hidden test maps."""
    lines = count_code_lines(source)
    try:
        tree = ast.parse(source, CODE_FILENAME)
        code = compile(tree, CODE_FILENAME, "exec")
    except SyntaxError as exc:
        return RunResult([], False, explain_syntax_error(exc), exc.lineno, 0, lines)

    result = _run_compiled(level, code, tree, lines, bonus_hp, shield)
    if not result.won or not check_hidden:
        return result
    for index, (hidden_level, changed_data) in enumerate(hidden_levels(level), start=1):
        hidden = _run_compiled(hidden_level, code, tree, lines, bonus_hp, shield)
        if not hidden.won:
            failure = HiddenFailure(index, hidden_level, hidden.events, hidden.message, hidden.error_line, changed_data)
            result.won = False
            result.message = describe_hidden_failure(failure)
            result.hidden_failure = failure
            return result
        result.hidden_passed = index
    return result


def _run_compiled(
    level: Level, code: Any, tree: ast.AST, lines: int, bonus_hp: int, shield: bool
) -> RunResult:
    world = World(level, bonus_hp, shield)
    namespace: dict[str, Any] = {
        "__builtins__": _safe_builtins(world),
        "__name__": "__main__",
        "hero": HeroAPI(world),
        "DoorJammed": DoorJammed,
    }
    # Bản sao riêng để code của lần chạy trước không làm đổi dữ liệu của màn.
    namespace.update(copy.deepcopy(level.extra_globals))

    traced_lines = 0
    deadline = time.monotonic() + MAX_RUN_SECONDS

    def tracer(frame: Any, event: str, arg: Any) -> Any:
        nonlocal traced_lines
        if frame.f_code.co_filename != CODE_FILENAME:
            return None
        if event == "line":
            traced_lines += 1
            if traced_lines > MAX_TRACED_LINES or time.monotonic() > deadline:
                raise StepLimitExceeded("Chương trình chạy quá lâu.")
        return tracer

    error_message: str | None = None
    error_line: int | None = None
    old_trace = sys.gettrace()
    sys.settrace(tracer)
    try:
        exec(code, namespace)  # noqa: S102 - sandboxed learner code
    except HeroDefeated as exc:
        error_message = str(exc)
        error_line = _error_line(exc)
        world.emit("fail", text=error_message)
    except StepLimitExceeded:
        error_message = "Chương trình chạy quá lâu - có thể bạn bị lặp vô hạn (while True?)."
        error_line = None
    except Exception as exc:  # noqa: BLE001 - report any player error
        error_line = _error_line(exc)
        error_message = explain_error(exc, error_line)
    finally:
        sys.settrace(old_trace)

    if error_message is not None:
        return RunResult(world.events, False, error_message, error_line, world.damage_taken, lines, world.chests_opened)

    problem = _judge(world, tree, level)
    if problem:
        return RunResult(world.events, False, problem, None, world.damage_taken, lines, world.chests_opened)
    return RunResult(world.events, True, "Hoàn thành màn chơi!", None, world.damage_taken, lines, world.chests_opened)


def _judge(world: World, tree: ast.AST, level: Level) -> str | None:
    if (world.hero_x, world.hero_y) != world.exit_position:
        return "Hero chưa tới cổng (cúp vàng). Hãy kiểm tra lại các bước đi."
    if world.gems:
        return f"Còn {len(world.gems)} viên ngọc chưa nhặt."
    if level.need_full_hp and world.hp < world.max_hp:
        return f"Hero mới có {world.hp}/{world.max_hp} máu - cần hồi đầy máu trước khi tới cúp."
    if world.chests_opened < level.need_chests:
        return f"Cần mở {level.need_chests} rương báu - mới mở {world.chests_opened}."
    if level.kill_all and world.enemies:
        return f"Còn {len(world.enemies)} quái chưa bị hạ."
    if level.say_contains is not None:
        spoken = " ".join(
            event["text"] for event in world.events if event["type"] in ("say", "print")
        )
        if level.say_contains not in spoken:
            return f"Hero cần nói ra thông tin đúng (có chứa '{level.say_contains}')."
    missing = _check_requirements(tree, level.requires)
    if missing:
        return "Màn này yêu cầu dùng: " + ", ".join(missing) + "."
    return None


# ======================================================================
# par.py
# ======================================================================

PAR: dict[str, int] = {
    "1-1": 1,
    "1-2": 3,
    "1-3": 2,
    "1-4": 7,
    "1-5": 4,
    "1-6": 3,
    "2-1": 2,
    "2-2": 5,
    "2-3": 4,
    "2-4": 2,
    "2-5": 4,
    "2-6": 4,
    "3-1": 4,
    "3-2": 6,
    "3-3": 5,
    "3-4": 6,
    "3-5": 4,
    "3-6": 6,
    "4-1": 2,
    "4-2": 3,
    "4-3": 3,
    "4-4": 3,
    "4-5": 4,
    "4-6": 4,
    "5-1": 3,
    "5-2": 4,
    "5-3": 1,
    "5-4": 3,
    "5-5": 4,
    "5-6": 5,
    "6-1": 10,
    "6-2": 4,
    "6-3": 5,
    "6-4": 5,
    "6-5": 5,
    "6-6": 8,
    "7-1": 4,
    "7-2": 3,
    "7-3": 3,
    "7-4": 4,
    "7-5": 4,
    "7-6": 4,
    "8-1": 4,
    "8-2": 4,
    "8-3": 3,
    "8-4": 5,
    "8-5": 2,
    "8-6": 7,
    "9-1": 6,
    "9-2": 5,
    "9-3": 6,
    "9-4": 7,
    "9-5": 3,
    "9-6": 6,
    "10-1": 4,
    "10-2": 5,
    "10-3": 4,
    "10-4": 5,
    "10-5": 6,
    "10-6": 7,
    "11-1": 6,
    "11-2": 4,
    "11-3": 8,
    "11-4": 4,
    "11-5": 5,
    "11-6": 6,
    "12-1": 6,
    "12-2": 5,
    "12-3": 5,
    "12-4": 6,
    "12-5": 4,
    "12-6": 6,
    "13-1": 6,
    "13-2": 9,
    "13-3": 6,
    "13-4": 5,
    "13-5": 9,
    "13-6": 9,
    "14-1": 7,
    "14-2": 7,
    "14-3": 7,
    "14-4": 6,
    "14-5": 5,
    "14-6": 6,
    "15-1": 6,
    "15-2": 4,
    "15-3": 6,
    "15-4": 5,
    "15-5": 6,
    "15-6": 5,
    "16-1": 9,
    "16-2": 12,
    "16-3": 10,
    "16-4": 9,
    "16-5": 9,
    "16-6": 7,
    "17-1": 5,
    "17-2": 11,
    "17-3": 6,
    "17-4": 11,
    "17-5": 10,
    "17-6": 11,
    "18-1": 18,
    "18-2": 11,
    "18-3": 5,
    "18-4": 9,
    "18-5": 10,
    "18-6": 11,
    "19-1": 6,
    "19-2": 4,
    "19-3": 4,
    "19-4": 9,
    "19-5": 5,
    "19-6": 6,
    "20-1": 5,
    "20-2": 6,
    "20-3": 5,
    "20-4": 6,
    "20-5": 6,
    "20-6": 7,
    "21-1": 9,
    "21-2": 11,
    "21-3": 8,
    "21-4": 16,
    "21-5": 12,
    "21-6": 8,
    "22-1": 5,
    "22-2": 8,
    "22-3": 5,
    "22-4": 7,
    "22-5": 6,
    "22-6": 5,
    "23-1": 3,
    "23-2": 6,
    "23-3": 4,
    "23-4": 3,
    "23-5": 4,
    "23-6": 6,
}


# ======================================================================
# levels_practice.py
# ======================================================================

def corridor(inner: str) -> list[str]:
    """One-row corridor map surrounded by walls."""
    wall = "#" * (len(inner) + 2)
    return [wall, f"#{inner}#", wall]


DOOR_RIGHT = corridor("@.GD.GE")
DOOR_DOWN = [
    "#######",
    "#@..###",
    "###.###",
    "###D###",
    "###G###",
    "###E###",
    "#######",
]
STAIRS = [
    "#######",
    "#@G####",
    "##.G###",
    "###.G##",
    "####.G#",
    "#####E#",
    "#######",
]
WEAPON_ROOM = [
    "###########",
    "#@..r..b..#",
    "#.........#",
    "#....c...E#",
    "###########",
]

PRACTICE: dict[int, list[Level]] = {}

# ================================================================ GIAI ĐOẠN 1
PRACTICE[1] = [
    Level(
        id="1-4",
        title="Đường zigzag",
        story="Đường đi như bậc thang: sang phải 1 ô, xuống 1 ô, cứ thế lặp lại.",
        goal="Đi theo đường zigzag, nhặt 2 viên ngọc và tới cúp.",
        rows=[
            "#######",
            "#@.####",
            "##.G###",
            "###.G##",
            "####.E#",
            "#######",
        ],
        starter="hero.move_right()\nhero.move_down()\n# viết tiếp\n",
        hints=["Không ghi số trong ngoặc thì hero đi 1 bước.", "Đếm xem cần mấy lần sang phải, mấy lần đi xuống."],
    ),
    Level(
        id="1-5",
        title="Đường vòng chữ U",
        story="Bức tường chắn ngay trước mặt. Hero phải đi vòng xuống dưới rồi mới lên được cúp.",
        goal="Đi vòng qua tường, nhặt ngọc, tới cúp rồi nói \"Đến rồi!\".",
        rows=[
            "#########",
            "#@#####E#",
            "#.#####.#",
            "#...G...#",
            "#########",
        ],
        starter="hero.move_down(2)\n",
        hints=["Đường đi gồm 3 đoạn: xuống, sang phải, lên.", "Lệnh say đặt ở cuối, sau khi tới cúp."],
        requires=["call:say"],
        say_contains="Đến rồi",
    ),
]

PRACTICE[2] = [
    Level(
        id="2-3",
        title="Biến thay đổi",
        story="Giá trị trong biến có thể thay đổi: steps = steps - 1 nghĩa là lấy giá trị cũ trừ 1 rồi cất lại.",
        goal="Dùng MỘT biến steps cho cả hai đoạn đường: đi phải 3, rồi giảm steps đi 1 và đi xuống.",
        rows=[
            "######",
            "#@.G.#",
            "####.#",
            "####E#",
            "######",
        ],
        starter="steps = 3\nhero.move_right(steps)\n# đổi steps rồi đi xuống\n",
        hints=["Gán lại steps bằng giá trị cũ trừ đi 1.", "Đoạn đi xuống dài 2 ô."],
        requires=["assign"],
    ),
    Level(
        id="2-4",
        title="Thẻ học sinh",
        story="Biến có sẵn: name = \"Mai\" (chuỗi) và age = 12 (số). Muốn ghép số vào chuỗi phải đổi số sang chuỗi bằng str().",
        goal="Nói \"Mai 12 tuổi\" bằng cách ghép name và age, rồi tới cúp.",
        rows=corridor("@..G..E"),
        starter='# name = "Mai", age = 12\nhero.say(name)\nhero.move_right(6)\n',
        hints=["Dùng dấu + để nối các chuỗi, nhớ có dấu cách giữa các phần.", "age là số, cần str(age)."],
        requires=["call:str"],
        extra_globals={"name": "Mai", "age": 12},
        say_contains="Mai 12 tuổi",
    ),
    Level(
        id="2-5",
        title="Chia kẹo",
        story=(
            "Có gems = 17 viên kẹo chia đều cho friends = 5 bạn. "
            "Phép // cho phần nguyên (mỗi bạn được mấy viên), phép % cho phần dư."
        ),
        goal="Nói \"3 dư 2\" (mỗi bạn được bao nhiêu, còn dư bao nhiêu) rồi tới cúp.",
        rows=corridor("@.G..E"),
        starter="# gems = 17, friends = 5\neach = gems / friends\nhero.say(each)\nhero.move_right(5)\n",
        hints=["Phép / cho kết quả số thực 3.4 - cần phép chia lấy phần nguyên.", "Phần dư dùng phép %."],
        requires=["assign"],
        extra_globals={"gems": 17, "friends": 5},
        say_contains="3 dư 2",
    ),
]

PRACTICE[3] = [
    Level(
        id="3-3",
        title="Mua vé",
        story="Vé vào cổng giá 5 xu, hero có coins = 7 xu. So sánh >= nghĩa là \"lớn hơn hoặc bằng\".",
        goal="Nếu đủ tiền mua vé thì nói \"Đủ tiền\", không thì nói \"Thiếu tiền\". Rồi tới cúp.",
        rows=corridor("@..G.E"),
        starter=(
            "# coins = 7, vé vào cổng giá 5\n"
            "if coins >= 10:\n"
            '    hero.say("Đủ tiền")\n'
            "else:\n"
            '    hero.say("Thiếu tiền")\n'
            "hero.move_right(5)\n"
        ),
        hints=["Điều kiện đang so sánh với sai giá vé.", "Vé giá 5 xu."],
        requires=["if"],
        extra_globals={"coins": 7},
        say_contains="Đủ tiền",
    ),
    Level(
        id="3-4",
        title="Ngã ba thứ hai",
        story="Lần này gai có thể ở trên hoặc ở dưới. elif cho phép kiểm tra thêm một điều kiện khác.",
        goal="Ở ngã ba, đi về phía KHÔNG có gai, nhặt ngọc rồi tới cúp.",
        rows=[
            "#######",
            "###GE##",
            "#@..###",
            "###^###",
            "#######",
        ],
        starter=(
            "hero.move_right(2)\n"
            'if hero.look("up") == "spike":\n'
            "    hero.move_down()\n"
        ),
        hints=["Hãy kiểm tra cả phía dưới: nếu dưới có gai thì đi lên.", "Sau khi rẽ, đi phải 1 ô là tới cúp."],
        requires=["if"],
    ),
    Level(
        id="3-5",
        title="Hai điều kiện",
        story="and: cả hai điều kiện đều đúng. or: chỉ cần một điều kiện đúng. hero.hp là số máu hiện tại.",
        goal="Chỉ tấn công khi bên phải là quái VÀ hero còn nhiều hơn 1 máu. Rồi tới cúp.",
        rows=corridor("@..r..E"),
        starter="hero.move_right(2)\nif hero.hp > 1:\n    pass\n",
        hints=["Ghép hai điều kiện bằng and trong cùng một câu if.", "Hạ quái xong, đi phải 4 ô."],
        requires=["if", "boolop"],
    ),
]

PRACTICE[4] = [
    Level(
        id="4-4",
        title="Bậc thang lớn dần",
        story="Biến i trong vòng for thay đổi mỗi vòng. range(1, 4) cho i = 1, 2, 3.",
        goal="Bậc thứ nhất dài 1 ô, bậc thứ hai dài 2 ô, bậc thứ ba dài 3 ô. Dùng i để đi đúng độ dài.",
        rows=[
            "#########",
            "#@.######",
            "##.G.####",
            "####..G.#",
            "#######E#",
            "#########",
        ],
        starter="for i in range(3):\n    print(i)\n",
        hints=["range(1, 4) bắt đầu từ 1 thay vì 0.", "Mỗi vòng: sang phải i ô rồi xuống 1 ô."],
        requires=["for"],
    ),
    Level(
        id="4-5",
        title="Vòng lặp lồng nhau",
        story=(
            "Vòng lặp có thể nằm trong vòng lặp. Vòng ngoài đếm bậc thang, vòng trong đi từng bước. "
            "Lần này bậc thang dài 1, 2, 3, 4 ô."
        ),
        goal="Dùng hai vòng for lồng nhau để xuống hết 4 bậc thang.",
        rows=[
            "#############",
            "#@.##########",
            "##.G.########",
            "####..G.#####",
            "#######..G..#",
            "###########E#",
            "#############",
        ],
        starter="for i in range(1, 5):\n    hero.move_right(i)\n",
        hints=["Vòng trong lặp i lần, mỗi lần đi 1 bước sang phải.", "Lệnh đi xuống thuộc vòng ngoài (thụt lề ít hơn)."],
        requires=["nested_for"],
    ),
]

PRACTICE[5] = [
    Level(
        id="5-3",
        title="Số có dấu chấm",
        story="distance = \"7.0\" là chuỗi có dấu chấm. int(\"7.0\") báo lỗi, phải đổi qua float trước.",
        goal="Đổi distance thành số nguyên đúng cách rồi đi đúng số bước tới cúp.",
        rows=corridor("@..G...E"),
        starter='# distance = "7.0"\nhero.move_right(int(distance))\n',
        hints=["float(\"7.0\") cho ra 7.0.", "Rồi mới đổi số thực sang số nguyên."],
        requires=["call:float"],
        extra_globals={"distance": "7.0"},
    ),
    Level(
        id="5-4",
        title="Số phòng",
        story="Cửa này cần mật mã là CHUỖI \"Phòng 7\". Biến room = 7 là số.",
        goal="Ghép chữ \"Phòng \" với room để tạo mật mã, mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter='# room = 7\nhero.move_right(2)\nhero.enter_code("Phòng" + room)\n',
        hints=["Chuỗi + số sẽ lỗi - đổi số sang chuỗi.", "Đừng quên dấu cách sau chữ Phòng."],
        requires=["call:str"],
        extra_globals={"room": 7},
        door_code="Phòng 7",
    ),
    Level(
        id="5-5",
        title="Công tắc bật tắt",
        story=(
            "switch = \"0\". Cửa cần giá trị True/False (bool). Bẫy: bool(\"0\") là True vì chuỗi không rỗng! "
            "Số 0 thì bool(0) mới là False."
        ),
        goal="Đổi switch sang số rồi sang bool để có đúng trạng thái công tắc, mở cửa, tới cúp.",
        rows=DOOR_DOWN,
        starter=(
            '# switch = "0"\n'
            "print(bool(switch))  # thử xem\n"
            "hero.move_right(2)\n"
            "hero.move_down(1)\n"
        ),
        hints=["Đổi sang int trước, rồi mới bool(...).", "Mở cửa xong, đi xuống 3 ô."],
        requires=["call:bool", "call:int"],
        extra_globals={"switch": "0"},
        door_code=False,
    ),
]

PRACTICE[6] = [
    Level(
        id="6-4",
        title="Hàm có tham số",
        story="Tham số giúp một hàm làm việc với nhiều giá trị khác nhau: step(2) và step(3) đi xa khác nhau.",
        goal="Viết hàm step(n): đi phải n ô rồi xuống n ô. Gọi step(2) rồi step(3) để tới cúp.",
        rows=[
            "########",
            "#@.G####",
            "###.####",
            "###.G..#",
            "######.#",
            "######.#",
            "######E#",
            "########",
        ],
        starter="def step(n):\n    hero.move_right(n)\n\nstep(2)\n",
        hints=["Thêm lệnh đi xuống n ô vào trong hàm.", "Gọi hàm thêm lần nữa với số khác."],
        requires=["def", "call:step"],
    ),
    Level(
        id="6-5",
        title="Khoảng cách điểm",
        story="scores = [7, 9, 4, 10, 6]. max() cho số lớn nhất, min() cho số nhỏ nhất.",
        goal="Mật mã = điểm cao nhất trừ điểm thấp nhất. Mở cửa và tới cúp.",
        rows=DOOR_DOWN,
        starter=(
            "# scores = [7, 9, 4, 10, 6]\n"
            "print(sum(scores))\n"
            "hero.move_right(2)\n"
            "hero.move_down(1)\n"
        ),
        hints=["Dùng cả max và min.", "Mở cửa xong đi xuống 3 ô."],
        requires=["call:max", "call:min"],
        extra_globals={"scores": [7, 9, 4, 10, 6]},
        door_code=6,
    ),
]

PRACTICE[7] = [
    Level(
        id="7-3",
        title="Gương soi",
        story="Mật mã bị viết ngược trong gương: scroll = \"olleh\". Cắt chuỗi với bước -1 sẽ đảo ngược chuỗi.",
        goal="Đảo ngược scroll để có mật mã, mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter='# scroll = "olleh"\nprint(scroll[0])\nhero.move_right(2)\n',
        hints=["Cú pháp [đầu:cuối:bước] - để trống đầu và cuối.", "Bước -1 đi từ cuối về đầu."],
        requires=["slice"],
        extra_globals={"scroll": "olleh"},
        door_code="hello",
    ),
    Level(
        id="7-4",
        title="Chỉ đường",
        story=(
            "route = \"2,3,1\" là chỉ đường: phải 2, xuống 3, phải 1. "
            ".split(\",\") cắt chuỗi tại dấu phẩy thành list các chuỗi nhỏ."
        ),
        goal="Tách route, đổi từng phần sang số rồi đi đúng chỉ đường tới cúp.",
        rows=[
            "######",
            "#@.G##",
            "###.##",
            "###.##",
            "###.E#",
            "######",
        ],
        starter='# route = "2,3,1"\nparts = route\nprint(parts)\n',
        hints=["Sau khi split, parts[0] là phần đầu tiên.", "Mỗi phần vẫn là chuỗi - cần int(...)."],
        requires=["call:split"],
        extra_globals={"route": "2,3,1"},
    ),
    Level(
        id="7-5",
        title="Đếm chữ a",
        story="message = \"banana bandana\". Chuỗi có hàm .count(\"x\") đếm số lần \"x\" xuất hiện.",
        goal="Mật mã = số chữ \"a\" trong message. Mở cửa và tới cúp.",
        rows=DOOR_DOWN,
        starter=(
            '# message = "banana bandana"\n'
            "print(len(message))\n"
            "hero.move_right(2)\n"
            "hero.move_down(1)\n"
        ),
        hints=["len đếm TẤT CẢ ký tự, kể cả dấu cách.", "Gọi .count trên chính message."],
        requires=["call:count"],
        extra_globals={"message": "banana bandana"},
        door_code=6,
    ),
]

PRACTICE[8] = [
    Level(
        id="8-3",
        title="Danh sách bước đi",
        story="steps = [3, 2, 4]: phải 3, xuống 2, phải 4. steps[0] là phần tử đầu tiên (vị trí 0).",
        goal="Dùng từng phần tử của steps để đi tới cúp.",
        rows=[
            "##########",
            "#@..G#####",
            "####.#####",
            "####...GE#",
            "##########",
        ],
        starter="# steps = [3, 2, 4]\nprint(steps[0])\nprint(len(steps))\n",
        hints=["Phần tử thứ hai là steps[1].", "Thứ tự: phải, xuống, phải."],
        requires=["subscript"],
        extra_globals={"steps": [3, 2, 4]},
    ),
    Level(
        id="8-4",
        title="Ghi chép vị trí",
        story="list.append(x) thêm x vào cuối list. Ghi lại cột x của từng viên ngọc trước khi nhặt.",
        goal="Tạo list các toạ độ x của ngọc, nói list đó ra (ví dụ [2, 4, 6]) rồi tới cúp.",
        rows=corridor("@G.G.G.E"),
        starter="xs = []\nfor gem in hero.find_gems():\n    pass\nhero.say(xs)\n",
        hints=["Trong vòng lặp, thêm gem[\"x\"] vào xs.", "Nói xong thì đi phải 7 ô."],
        requires=["call:append"],
        say_contains="[2, 4, 6]",
    ),
    Level(
        id="8-5",
        title="Các điểm dừng",
        story="stops là list các tuple (x, y). Duyệt list và mở gói mỗi tuple ngay trong vòng for: for x, y in stops.",
        goal="Đi lần lượt tới mọi điểm dừng trong stops (điểm cuối là cổng).",
        rows=[
            "########",
            "#@.G####",
            "###.####",
            "###G.GE#",
            "########",
        ],
        starter=(
            "# stops = [(3, 1), (3, 3), (5, 3), (6, 3)]\n"
            "first = stops[0]\n"
            "print(first[0], first[1])\n"
        ),
        hints=["Vòng for có thể tách mỗi tuple thành 2 biến ngay khi duyệt.", "Mỗi vòng, đi tới toạ độ vừa lấy ra bằng move_to."],
        requires=["for", "call:move_to"],
        extra_globals={"stops": [(3, 1), (3, 3), (5, 3), (6, 3)]},
    ),
]

PRACTICE[9] = [
    Level(
        id="9-3",
        title="Đi chợ",
        story="prices = {\"táo\": 5, \"cam\": 7, \"lê\": 4} là bảng giá. basket = [\"táo\", \"lê\", \"táo\"] là giỏ hàng.",
        goal="Tính tổng tiền giỏ hàng bằng cách tra bảng giá, nhập làm mật mã, tới cúp.",
        rows=DOOR_RIGHT,
        starter='# prices, basket có sẵn\nprint(prices["táo"])\nhero.move_right(2)\n',
        hints=["Duyệt từng món trong giỏ, tra giá trong dict.", "Cộng dồn vào một biến tổng bắt đầu từ 0."],
        requires=["for"],
        extra_globals={"prices": {"táo": 5, "cam": 7, "lê": 4}, "basket": ["táo", "lê", "táo"]},
        door_code=14,
    ),
    Level(
        id="9-4",
        title="Sổ đếm",
        story=(
            "words = [\"mèo\", \"chó\", \"mèo\", \"cá\", \"mèo\"]. Dùng dict làm sổ đếm: "
            "counts.get(w, 0) trả về số đếm hiện tại, hoặc 0 nếu chưa có."
        ),
        goal="Đếm mỗi con vật xuất hiện mấy lần. Mật mã = số lần \"mèo\" xuất hiện.",
        rows=DOOR_DOWN,
        starter="counts = {}\nprint(counts)\nhero.move_right(2)\nhero.move_down(1)\n",
        hints=["Mỗi vòng: counts[w] = số cũ + 1.", "Tra counts[\"mèo\"] để lấy mật mã."],
        requires=["dict", "for"],
        extra_globals={"words": ["mèo", "chó", "mèo", "cá", "mèo"]},
        door_code=3,
    ),
    Level(
        id="9-5",
        title="Khách tham quan",
        story="visitors ghi tên khách mỗi lần vào cửa, có người vào nhiều lần. set chỉ giữ tên không trùng.",
        goal="Mật mã = số NGƯỜI khác nhau đã tới. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="# visitors có sẵn\nprint(len(visitors))\nhero.move_right(2)\n",
        hints=["len(visitors) đếm cả tên trùng.", "Đổi sang set trước khi đếm."],
        requires=["set"],
        extra_globals={"visitors": ["An", "Bình", "An", "Chi", "Bình", "An"]},
        door_code=3,
    ),
]

PRACTICE[10] = [
    Level(
        id="10-3",
        title="Tổng bình phương",
        story="numbers = [1, 2, 3, 4]. List comprehension tạo list mới từ list cũ trong 1 dòng.",
        goal="Tạo list bình phương các số bằng comprehension, mật mã = tổng của list đó.",
        rows=DOOR_RIGHT,
        starter="squares = []\nprint(numbers)\nhero.move_right(2)\n",
        hints=["[biểu_thức for n in numbers]", "Bình phương của n là n * n."],
        requires=["listcomp"],
        extra_globals={"numbers": [1, 2, 3, 4]},
        door_code=30,
    ),
    Level(
        id="10-4",
        title="Bảng số",
        story="table = [[1, 2], [3, 4], [5, 6]] là list lồng nhau. Comprehension có thể có 2 vòng for.",
        goal="Cộng mọi số trong table, nhập tổng làm mật mã, tới cúp.",
        rows=DOOR_DOWN,
        starter="print(table[0])\nprint(table[2][1])\nhero.move_right(2)\nhero.move_down(1)\n",
        hints=["Vòng for ngoài duyệt hàng, vòng trong duyệt số trong hàng.", "Tính sum của list vừa trải phẳng."],
        requires=["listcomp"],
        extra_globals={"table": [[1, 2], [3, 4], [5, 6]]},
        door_code=21,
    ),
    Level(
        id="10-5",
        title="Dò bản đồ",
        story=(
            "hero.scan() trả về bản đồ grid[y][x]. enumerate(list) cho cả vị trí lẫn phần tử. "
            "Lần này không dùng find_gems - hãy tự tìm toạ độ ngọc từ bản đồ."
        ),
        goal="Tìm toạ độ mọi ô \"gem\" bằng comprehension trên bản đồ, đi nhặt hết rồi tới cổng.",
        rows=[
            "#########",
            "#@..#..G#",
            "#.#...#.#",
            "#G..#..E#",
            "#########",
        ],
        starter="grid = hero.scan()\nprint(grid[1][7])\n",
        hints=[
            "Duyệt for y, row in enumerate(grid) rồi for x, tile in enumerate(row).",
            "Giữ lại (x, y) khi tile == \"gem\", sau đó move_to từng điểm.",
        ],
        requires=["listcomp", "call:scan"],
    ),
]

# ================================================================ GIAI ĐOẠN 2
PRACTICE[11] = [
    Level(
        id="11-2",
        title="Ai vắng mặt",
        story=(
            "invited là danh sách bạn được mời, came là những bạn đã tới. "
            "Hiệu tập hợp a - b gồm phần tử có trong a nhưng KHÔNG có trong b."
        ),
        goal="Mật mã = số bạn được mời mà chưa tới. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="# invited, came có sẵn\nprint(set(invited))\nhero.move_right(2)\n",
        hints=["Đổi cả hai list sang set.", "Lấy tập được mời trừ tập đã tới, rồi đếm."],
        requires=["op:- or call:difference"],
        extra_globals={"invited": ["An", "Bình", "Chi", "Dũng", "Hà"], "came": ["Bình", "Hà", "An"]},
        door_code=2,
    ),
    Level(
        id="11-3",
        title="Soát vé",
        story=(
            "tickets là các vé khách đưa ra, valid là tập các mã vé hợp lệ. "
            "Toán tử in kiểm tra một giá trị có nằm trong tập hay không - với set rất nhanh."
        ),
        goal="Đếm số vé hợp lệ (tính cả vé trùng), nhập làm mật mã, tới cúp.",
        rows=DOOR_DOWN,
        starter='# tickets (list), valid (set) có sẵn\nprint("A12" == "A12")\nhero.move_right(2)\nhero.move_down(1)\n',
        hints=["Duyệt từng vé, dùng if ... in valid.", "Cộng dồn số vé hợp lệ vào một biến đếm."],
        requires=["membership"],
        extra_globals={"tickets": ["A12", "B07", "A12", "C33", "B07"], "valid": {"A12", "C33"}},
        door_code=3,
    ),
    Level(
        id="11-4",
        title="Sticker độc nhất",
        story=(
            "An và Bình sưu tầm sticker. Hiệu đối xứng a ^ b gồm phần tử chỉ có ở MỘT trong hai người "
            "(bỏ những cái cả hai cùng có)."
        ),
        goal="Mật mã = số sticker chỉ một trong hai bạn có. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="a = set(stickers_an)\nb = set(stickers_binh)\nprint(a & b)\nhero.move_right(2)\n",
        hints=["a & b là phần CẢ HAI có - không phải thứ cần tìm.", "Dùng toán tử ^ rồi đếm."],
        requires=["op:^ or call:symmetric_difference"],
        extra_globals={"stickers_an": [1, 2, 3, 4], "stickers_binh": [3, 4, 5]},
        door_code=3,
    ),
    Level(
        id="11-5",
        title="Kiểm tra ba lô",
        story=(
            "Đi thám hiểm cần đủ các món trong required = {\"key\", \"map\"}. "
            "a <= b (hoặc a.issubset(b)) cho biết a có nằm trọn trong b không."
        ),
        goal="Nếu ba lô có đủ đồ cần thiết thì nói \"Đủ đồ\", không thì \"Thiếu đồ\". Rồi tới cúp.",
        rows=corridor("@..G..E"),
        starter=(
            "# required (set), backpack (list) có sẵn\n"
            "if len(backpack) > 5:\n"
            '    hero.say("Đủ đồ")\n'
            "else:\n"
            '    hero.say("Thiếu đồ")\n'
            "hero.move_right(6)\n"
        ),
        hints=[
            "Số món nhiều hay ít không quan trọng - quan trọng là có đủ món cần thiết không.",
            "Đổi backpack sang set rồi kiểm tra tập con.",
        ],
        requires=["if", "subset"],
        extra_globals={"required": {"key", "map"}, "backpack": ["map", "rope", "key", "torch"]},
        say_contains="Đủ đồ",
    ),
]

PRACTICE[12] = [
    Level(
        id="12-3",
        title="Thuê xe buýt",
        story="Có students = 45 học sinh, mỗi xe chở seats = 16 bạn. Thiếu chỗ là không được - phải làm tròn LÊN.",
        goal="Tính số xe cần thuê bằng math.ceil, nhập làm mật mã, tới cúp.",
        rows=DOOR_RIGHT,
        starter="import math\n# students = 45, seats = 16\nprint(students / seats)\nhero.move_right(2)\n",
        hints=["45 / 16 = 2.8125 - không thể thuê 2.8 xe.", "math.ceil làm tròn lên."],
        requires=["call:ceil"],
        extra_globals={"students": 45, "seats": 16},
        door_code=3,
    ),
    Level(
        id="12-4",
        title="Sân tròn",
        story="Sân chơi hình tròn bán kính r = 5 m. Diện tích = π × r². round() làm tròn tới số nguyên gần nhất.",
        goal="Tính diện tích sân, làm tròn thành số nguyên, nhập làm mật mã, tới cúp.",
        rows=DOOR_DOWN,
        starter="import math\n# r = 5\nprint(r ** 2)\nhero.move_right(2)\nhero.move_down(1)\n",
        hints=["Dùng math.pi cho số π.", "round(...) để ra số nguyên."],
        requires=["import:math"],
        extra_globals={"r": 5},
        door_code=79,
    ),
    Level(
        id="12-5",
        title="Chọn đội trực nhật",
        story=(
            "Tổ có 6 bạn, cần chọn 2 bạn trực nhật (không quan tâm thứ tự). "
            "math.comb(n, k) đếm số cách chọn k người trong n người."
        ),
        goal="Mật mã = số cách chọn 2 bạn trong 6 bạn. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="import math\nprint(math.factorial(3))\nhero.move_right(2)\n",
        hints=["comb = combination = tổ hợp.", "Truyền vào số bạn và số cần chọn."],
        requires=["call:comb or call:factorial"],
        door_code=15,
    ),
]

PRACTICE[13] = [
    Level(
        id="13-3",
        title="Bao nhiêu cách xếp",
        story="letters = \"ABCD\". permutations cũng dùng được với chuỗi. list(...) gom tất cả, len(...) để đếm.",
        goal="Mật mã = số cách sắp xếp 4 chữ cái A, B, C, D. Mở cửa và tới cúp.",
        rows=DOOR_DOWN,
        starter='from itertools import permutations\nprint(list(permutations("AB")))\nhero.move_right(2)\nhero.move_down(1)\n',
        hints=["Đếm số phần tử permutations sinh ra.", "4 vật có 4 × 3 × 2 × 1 cách xếp - hãy kiểm tra lại bằng code."],
        requires=["call:permutations"],
        extra_globals={"letters": "ABCD"},
        door_code=24,
    ),
    Level(
        id="13-4",
        title="Phối đồ",
        story=(
            "shirts = [\"đỏ\", \"xanh\"], pants = [\"đen\", \"trắng\", \"nâu\"]. "
            "product(a, b) ghép MỌI phần tử của a với MỌI phần tử của b."
        ),
        goal="Mật mã = số bộ quần áo phối được. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter='from itertools import product\nfor combo in product([1, 2], ["x"]):\n    print(combo)\n',
        hints=["Ghép shirts với pants bằng product.", "Gom vào list rồi đếm."],
        requires=["call:product"],
        extra_globals={"shirts": ["đỏ", "xanh"], "pants": ["đen", "trắng", "nâu"]},
        door_code=6,
    ),
    Level(
        id="13-5",
        title="Cặp xu",
        story="coins = [1, 2, 5, 10]. Chọn 2 đồng xu khác nhau. Có bao nhiêu cặp có tổng từ 7 trở lên?",
        goal="Đếm các cặp xu có tổng >= 7, nhập làm mật mã, tới cúp.",
        rows=DOOR_DOWN,
        starter="from itertools import combinations\nprint(list(combinations([1, 2, 5], 2)))\n",
        hints=["Duyệt combinations(coins, 2) và kiểm tra tổng.", "Đếm số cặp thoả điều kiện."],
        requires=["call:combinations"],
        extra_globals={"coins": [1, 2, 5, 10]},
        door_code=4,
    ),
]

PRACTICE[14] = [
    Level(
        id="14-3",
        title="Phân loại thực phẩm",
        story=(
            "foods là list các cặp (loại, tên). defaultdict(list) tự tạo list rỗng cho loại mới, "
            "nên có thể append ngay mà không lỗi."
        ),
        goal="Gom món ăn theo loại. Mật mã = số món thuộc loại \"quả\". Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter='from collections import defaultdict\ngroups = defaultdict(list)\nprint(groups["rau"])\n',
        hints=["Duyệt từng cặp (loại, tên) và thêm tên vào đúng nhóm.", "Đếm số phần tử trong nhóm \"quả\"."],
        requires=["call:defaultdict"],
        extra_globals={
            "foods": [("rau", "cải"), ("quả", "táo"), ("rau", "muống"), ("quả", "cam"), ("quả", "lê")],
        },
        door_code=3,
    ),
    Level(
        id="14-4",
        title="Bầu lớp trưởng",
        story="votes là các phiếu bầu. Mật mã là TÊN người được nhiều phiếu nhất.",
        goal="Dùng Counter tìm người thắng cử, nhập tên làm mật mã, tới cúp.",
        rows=DOOR_DOWN,
        starter="from collections import Counter\nprint(len(votes))\nhero.move_right(2)\nhero.move_down(1)\n",
        hints=["most_common(1) cho list có một tuple (tên, số phiếu).", "Mật mã là phần tên trong tuple."],
        requires=["call:Counter"],
        extra_globals={"votes": ["Lan", "Minh", "Lan", "Hoa", "Minh", "Lan"]},
        door_code="Lan",
    ),
    Level(
        id="14-5",
        title="Ba lần gần nhất",
        story=(
            "scores = [5, 8, 2, 9, 4] là điểm các lần chơi. deque(maxlen=3) chỉ giữ 3 phần tử MỚI NHẤT - "
            "thêm phần tử thứ 4 thì phần tử cũ nhất tự bị bỏ."
        ),
        goal="Mật mã = tổng điểm 3 lần chơi gần nhất. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="from collections import deque\nrecent = deque(maxlen=3)\nprint(recent)\n",
        hints=["Có thể tạo deque thẳng từ scores với maxlen=3.", "Cộng các phần tử còn lại trong deque."],
        requires=["call:deque"],
        extra_globals={"scores": [5, 8, 2, 9, 4]},
        door_code=15,
    ),
]

PRACTICE[15] = [
    Level(
        id="15-2",
        title="Thứ mấy",
        story=(
            "day = \"2026-09-05\" là ngày khai giảng. ngay.weekday() cho thứ trong tuần: "
            "0 = thứ Hai, 1 = thứ Ba, ..., 6 = Chủ nhật."
        ),
        goal="Mật mã = kết quả weekday() của ngày khai giảng. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="from datetime import date\nprint(date.fromisoformat(day))\nhero.move_right(2)\n",
        hints=["Đổi day thành date trước.", "Gọi .weekday() trên ngày đó."],
        requires=["call:weekday"],
        extra_globals={"day": "2026-09-05"},
        door_code=5,
    ),
    Level(
        id="15-3",
        title="Hạn nộp bài",
        story=(
            "Dự án bắt đầu start = \"2026-01-01\" và phải nộp sau 45 ngày. "
            "Ngày + timedelta(days=45) cho ra ngày mới. str(ngay) cho dạng \"năm-tháng-ngày\"."
        ),
        goal="Mật mã = ngày nộp bài dạng chuỗi \"năm-tháng-ngày\". Mở cửa và tới cúp.",
        rows=DOOR_DOWN,
        starter="from datetime import date, timedelta\nprint(timedelta(days=1))\nhero.move_right(2)\nhero.move_down(1)\n",
        hints=["Cộng một timedelta vào ngày bắt đầu.", "Mật mã là chuỗi - đổi ngày sang str."],
        requires=["call:timedelta"],
        extra_globals={"start": "2026-01-01"},
        door_code="2026-02-15",
    ),
    Level(
        id="15-4",
        title="Mấy tuần ôn thi",
        story="Ôn thi từ start = \"2026-03-02\" tới end = \"2026-05-25\". Một tuần có 7 ngày.",
        goal="Mật mã = số tuần ôn thi (số ngày chia lấy phần nguyên cho 7). Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="from datetime import date\nhero.move_right(2)\n",
        hints=["Trừ hai ngày rồi lấy .days.", "Dùng phép chia lấy phần nguyên cho 7."],
        requires=["import:datetime"],
        extra_globals={"start": "2026-03-02", "end": "2026-05-25"},
        door_code=12,
    ),
    Level(
        id="15-5",
        title="Viết ngày kiểu Việt Nam",
        story=(
            "day = \"2026-11-20\". Người Việt viết ngày/tháng/năm. ngay.strftime(\"%d/%m/%Y\") định dạng lại: "
            "%d là ngày, %m là tháng, %Y là năm."
        ),
        goal="Mật mã = ngày Nhà giáo Việt Nam viết dạng \"ngày/tháng/năm\". Mở cửa và tới cúp.",
        rows=DOOR_DOWN,
        starter="from datetime import date\nprint(date.fromisoformat(day))\nhero.move_right(2)\nhero.move_down(1)\n",
        hints=["Đổi day thành date rồi gọi strftime.", "Mẫu định dạng dùng dấu / giữa các phần."],
        requires=["call:strftime"],
        extra_globals={"day": "2026-11-20"},
        door_code="20/11/2026",
    ),
]

# ================================================================ GIAI ĐOẠN 3
GROWING_STAIRS = [
    "#########",
    "#@.######",
    "##.G.####",
    "####..G.#",
    "#######E#",
    "#########",
]
SPIKE_HOPS = [
    "#############",
    "#...G..G..G.#",
    "#@..^..^..^E#",
    "#############",
]

PRACTICE[16] = [
    Level(
        id="16-4",
        title="Phép chia nguy hiểm",
        story=(
            "pairs = [(10, 2), (5, 0), (9, 3)]. Chia cho 0 gây lỗi ZeroDivisionError. "
            "Hãy bỏ qua cặp chia cho 0 và cộng kết quả các cặp còn lại (dùng phép //)."
        ),
        goal="Mật mã = tổng a // b của các cặp chia được. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="total = 0\nfor a, b in pairs:\n    total += a // b\nprint(total)\n",
        hints=["Bọc phép chia trong try.", "Bắt đúng loại lỗi chia cho 0."],
        requires=["try", "except:ZeroDivisionError"],
        extra_globals={"pairs": [(10, 2), (5, 0), (9, 3)]},
        door_code=8,
    ),
    Level(
        id="16-5",
        title="Tự báo lỗi",
        story=(
            "moves = [3, -1, 4] là số bước cần đi, nhưng số bước âm là dữ liệu hỏng. "
            "Lệnh raise ValueError(\"...\") tự tạo ra lỗi - nơi gọi hàm sẽ bắt lỗi đó bằng try/except."
        ),
        goal="Viết hàm check(n) báo lỗi ValueError khi n âm. Đi theo các bước hợp lệ và bỏ qua bước hỏng.",
        rows=corridor("@..G...E"),
        starter="def check(n):\n    return n\n\nfor n in moves:\n    hero.move_right(check(n))\n",
        hints=["Trong check: nếu n nhỏ hơn 0 thì raise, ngược lại trả về n.", "Bọc lời gọi check trong try/except ValueError."],
        requires=["raise", "try"],
        extra_globals={"moves": [3, -1, 4]},
    ),
]

PRACTICE[17] = [
    Level(
        id="17-4",
        title="Chiếc ví",
        story=(
            "Phương thức là hàm viết BÊN TRONG class, luôn có self là tham số đầu tiên. "
            "coins = [5, 10, 2] là các đồng xu nhặt được."
        ),
        goal="Thêm phương thức add(amount) cho class Wallet, bỏ hết xu vào ví. Mật mã = tổng tiền trong ví.",
        rows=DOOR_RIGHT,
        starter="class Wallet:\n    def __init__(self):\n        self.total = 0\n\nw = Wallet()\nprint(w.total)\n",
        hints=["add(self, amount) cộng amount vào self.total.", "Duyệt coins và gọi w.add(...) cho từng đồng."],
        requires=["class", "method"],
        extra_globals={"coins": [5, 10, 2]},
        door_code=17,
    ),
    Level(
        id="17-5",
        title="Đội của tôi",
        story=(
            "Magic method __len__ quy định kết quả của len(doi_tuong). "
            "members = [\"An\", \"Bình\", \"Chi\", \"Dũng\"]."
        ),
        goal="Viết __len__ cho class Team trả về số thành viên, rồi nhập len(team) làm mật mã.",
        rows=DOOR_DOWN,
        starter=(
            "class Team:\n"
            "    def __init__(self, members):\n"
            "        self.members = members\n"
            "\n"
            "team = Team(members)\n"
            "print(team.members)\n"
        ),
        hints=["__len__(self) phải return một số nguyên.", "Số thành viên chính là độ dài list self.members."],
        requires=["dunder:__len__"],
        extra_globals={"members": ["An", "Bình", "Chi", "Dũng"]},
        door_code=4,
    ),
]

PRACTICE[18] = [
    Level(
        id="18-2",
        title="Kho vũ khí",
        story=(
            "Ôn tập: dict vũ khí, vòng lặp và cửa kẹt. Quái: robot → hammer, barrel → axe, cannon → bow. "
            "Cửa kẹt ở ngay trên cúp."
        ),
        goal="Hạ hết quái bằng đúng vũ khí, tới đứng trên cửa kẹt, mở cửa rồi xuống cúp.",
        rows=[
            "############",
            "#@..b...r..#",
            "#..c.......#",
            "##########J#",
            "##########E#",
            "############",
        ],
        starter=(
            'weakness = {"robot": "hammer", "barrel": "axe", "cannon": "bow"}\n'
            "for enemy in hero.find_enemies():\n"
            '    print(enemy["type"], enemy["x"], enemy["y"])\n'
        ),
        hints=[
            "Ô ngay trên cửa kẹt là (10, 2) - dùng move_to để tới đó sau khi hạ quái.",
            "Cửa kẹt nằm phía dưới hero: thử mở nhiều lần bằng try/except.",
        ],
        requires=["dict", "for", "try"],
        jams=2,
        weapons=True,
        kill_all=True,
    ),
    Level(
        id="18-3",
        title="Lọc chữ số",
        story="scroll = \"x7y3z9\". Mật mã = tổng các chữ số trong cuộn giấy. Hãy viết một hàm trả về list các chữ số.",
        goal="Viết hàm digits(text) dùng comprehension, mật mã = tổng các chữ số. Mở cửa, tới cúp.",
        rows=DOOR_RIGHT,
        starter="def digits(text):\n    return []\n\nprint(digits(scroll))\nhero.move_right(2)\n",
        hints=["Duyệt từng ký tự, giữ ký tự .isdigit() và đổi sang int.", "Cộng list trả về bằng sum."],
        requires=["def", "listcomp"],
        extra_globals={"scroll": "x7y3z9"},
        door_code=19,
    ),
    Level(
        id="18-4",
        title="Lộ trình bậc thang",
        story=(
            "Ôn tập class và __iter__. Route(size) là lộ trình bậc thang lớn dần: "
            "bậc i gồm i lần \"right\" rồi một \"down\", với i từ 1 tới size."
        ),
        goal="Viết __iter__ cho Route, rồi cho hero follow Route(3) để tới cúp.",
        rows=GROWING_STAIRS,
        starter=(
            "class Route:\n"
            "    def __init__(self, size):\n"
            "        self.size = size\n"
            "\n"
            'hero.follow(["right", "down"])\n'
        ),
        hints=["Tạo list các hướng trong __iter__ bằng vòng lặp, rồi trả về iter(list).", "List nhân số: [\"right\"] * i."],
        requires=["class", "dunder:__iter__"],
    ),
    Level(
        id="18-5",
        title="Phòng bẫy số",
        story=(
            "candidates = [\"4\", \"x\", \"4\", \"7\", \"??\", \"2\"]. Một số chuỗi không phải số, và có số bị lặp. "
            "Mật mã = tổng các số KHÁC NHAU đọc được."
        ),
        goal="Đổi các chuỗi đọc được sang số (bỏ qua chuỗi hỏng), loại số trùng, mật mã = tổng.",
        rows=DOOR_DOWN,
        starter="values = []\nfor text in candidates:\n    values.append(int(text))\n",
        hints=["Bắt lỗi ValueError khi đổi kiểu.", "Dùng set để không cộng trùng."],
        requires=["try", "set"],
        extra_globals={"candidates": ["4", "x", "4", "7", "??", "2"]},
        door_code=13,
    ),
]

# ================================================================ GIAI ĐOẠN 4
PRACTICE[19] = [
    Level(
        id="19-3",
        title="Người giỏi nhất",
        story=(
            "players = [(\"An\", 7), (\"Bình\", 9), (\"Chi\", 5)]. max(ds, key=...) và sorted(ds, key=...) "
            "nhận một hàm cho biết so sánh theo cái gì - rất hợp với lambda."
        ),
        goal="Tìm người có điểm cao nhất bằng lambda, nhập TÊN người đó làm mật mã, tới cúp.",
        rows=DOOR_RIGHT,
        starter="print(sorted(players))\nhero.move_right(2)\n",
        hints=["sorted(players) đang xếp theo tên - cần xếp theo điểm.", "key=lambda p: ... lấy phần tử thứ hai của tuple."],
        requires=["lambda", "call:sorted or call:max"],
        extra_globals={"players": [("An", 7), ("Bình", 9), ("Chi", 5)]},
        door_code="Bình",
    ),
    Level(
        id="19-4",
        title="Lần rẽ đầu tiên",
        story=(
            "route = [\"right\", \"right\", \"down\", \"down\", \"right\"]. "
            "enumerate(ds) cho từng cặp (vị trí, phần tử), vị trí đếm từ 0."
        ),
        goal="Mật mã = vị trí của \"down\" ĐẦU TIÊN trong route. Mở cửa và tới cúp.",
        rows=DOOR_DOWN,
        starter="for step in route:\n    print(step)\n",
        hints=["Duyệt for i, step in enumerate(route).", "Gặp \"down\" đầu tiên thì ghi nhớ vị trí và dừng vòng lặp."],
        requires=["call:enumerate"],
        extra_globals={"route": ["right", "right", "down", "down", "right"]},
        door_code=2,
    ),
    Level(
        id="19-5",
        title="Dự báo thời tiết",
        story=(
            "temps = [22, 25, 31, 28] là nhiệt độ các ngày. any(...) đúng nếu CÓ ÍT NHẤT MỘT phần tử đúng, "
            "all(...) đúng nếu TẤT CẢ đều đúng."
        ),
        goal="Nếu có ngày nào trên 30 độ thì nói \"Nóng\", không thì \"Mát\". Rồi tới cúp.",
        rows=corridor("@..G.E"),
        starter='if temps[0] > 30:\n    hero.say("Nóng")\nelse:\n    hero.say("Mát")\nhero.move_right(5)\n',
        hints=["Đang chỉ xét ngày đầu tiên.", "Đưa một biểu thức t > 30 cho mọi t vào any(...)."],
        requires=["call:any or call:all"],
        extra_globals={"temps": [22, 25, 31, 28]},
        say_contains="Nóng",
    ),
]

PRACTICE[20] = [
    Level(
        id="20-3",
        title="Đếm ngọc trong thư",
        story="letter = \"Ngọc: 3 đỏ, 5 xanh, 2 vàng\". re.findall trả về list MỌI chỗ khớp mẫu.",
        goal="Lấy mọi con số trong thư, mật mã = tổng của chúng. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter='import re\nprint(re.search(r"\\d+", letter).group())\nhero.move_right(2)\n',
        hints=["re.search chỉ tìm chỗ đầu tiên.", "Kết quả findall là list chuỗi - đổi sang int trước khi cộng."],
        requires=["call:findall"],
        extra_globals={"letter": "Ngọc: 3 đỏ, 5 xanh, 2 vàng"},
        door_code=10,
    ),
    Level(
        id="20-4",
        title="Mã hợp lệ",
        story=(
            "codes = [\"AB-123\", \"X-1\", \"CD-456\", \"EF-78\"]. Mã hợp lệ gồm 2 chữ in hoa, dấu -, rồi đúng 3 chữ số. "
            "Mẫu: [A-Z]{2} là 2 chữ in hoa, \\d{3} là 3 chữ số. re.fullmatch khớp TOÀN BỘ chuỗi."
        ),
        goal="Đếm số mã hợp lệ, nhập làm mật mã, tới cúp.",
        rows=DOOR_DOWN,
        starter="import re\nprint(len(codes))\nhero.move_right(2)\nhero.move_down(1)\n",
        hints=["Ghép mẫu: [A-Z]{2}, dấu -, \\d{3}.", "fullmatch trả về None nếu không khớp - dùng được trong if."],
        requires=["call:fullmatch or call:match"],
        extra_globals={"codes": ["AB-123", "X-1", "CD-456", "EF-78"]},
        door_code=2,
    ),
    Level(
        id="20-5",
        title="Lệnh tác chiến XML",
        story=(
            "room_xml ghi vị trí từng quái và vũ khí cần dùng: <enemy x=\"..\" y=\"..\" weapon=\"..\"/>, "
            "cùng vị trí cổng <exit .../>. Lần này hãy đọc mọi thứ từ XML."
        ),
        goal="Đọc XML, hạ từng quái bằng vũ khí ghi trong thẻ, rồi tới cổng.",
        rows=WEAPON_ROOM,
        starter='import xml.etree.ElementTree as ET\nroot = ET.fromstring(room_xml)\nprint(len(root.findall("enemy")))\n',
        hints=["Mỗi thẻ enemy có get(\"x\"), get(\"y\"), get(\"weapon\").", "Toạ độ là chuỗi - đổi sang int."],
        requires=["import:xml"],
        extra_globals={
            "room_xml": (
                '<room><enemy x="4" y="1" weapon="hammer"/><enemy x="7" y="1" weapon="axe"/>'
                '<enemy x="5" y="3" weapon="bow"/><exit x="9" y="3"/></room>'
            ),
        },
        weapons=True,
        kill_all=True,
    ),
]

PRACTICE[21] = [
    Level(
        id="21-3",
        title="Máy nhân",
        story="make_multiplier(k) tạo ra một hàm nhân với k. Mật mã = 14 nhân 3, tính bằng hàm triple tạo từ make_multiplier(3).",
        goal="Viết closure make_multiplier, tạo hàm triple, dùng nó tính mật mã. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="def make_multiplier(k):\n    pass\n\nhero.move_right(2)\n",
        hints=["Bên trong tạo hàm nhận n và trả về n nhân k.", "Hàm ngoài trả hàm trong ra (không có ngoặc)."],
        requires=["closure"],
        door_code=42,
    ),
    Level(
        id="21-4",
        title="Bùa báo hiệu",
        story=(
            "Viết decorator announce: trước khi chạy hàm, hero nói \"Bắt đầu: \" + tên hàm. "
            "Tên của hàm f lấy bằng f.__name__."
        ),
        goal="Gắn @announce vào hàm hop, dùng hop để vượt cả 3 cái gai và tới cúp.",
        rows=SPIKE_HOPS,
        starter=(
            "def announce(func):\n"
            "    return func\n"
            "\n"
            "@announce\n"
            "def hop():\n"
            "    hero.move_up()\n"
            "    hero.move_right(2)\n"
            "    hero.move_down()\n"
            "\n"
            "hero.move_right(2)\n"
            "hop()\n"
        ),
        hints=["Bên trong announce, tạo hàm bọc: nói trước, rồi gọi func().", "Giữa các lần hop() đi phải 1 ô."],
        requires=["decorator"],
        say_contains="Bắt đầu: hop",
    ),
    Level(
        id="21-5",
        title="Bùa lặp lại",
        story=(
            "Decorator có tham số: @repeat(4) làm hàm chạy 4 lần. repeat(times) trả về một decorator - "
            "tức là 3 tầng hàm lồng nhau."
        ),
        goal="Viết repeat(times), gắn @repeat(4) vào hàm stair, gọi stair() MỘT lần để xuống hết cầu thang.",
        rows=STAIRS,
        starter=(
            "def repeat(times):\n"
            "    pass\n"
            "\n"
            "def stair():\n"
            "    hero.move_right()\n"
            "    hero.move_down()\n"
            "\n"
            "stair()\n"
        ),
        hints=[
            "Tầng ngoài nhận times, tầng giữa nhận func, tầng trong chạy func times lần.",
            "Mỗi tầng trả về hàm ở tầng ngay bên trong nó.",
        ],
        requires=["decorator", "closure"],
    ),
]

# ================================================================ GIAI ĐOẠN 5
PRACTICE[22] = [
    Level(
        id="22-3",
        title="Nhiệt độ trung bình",
        story="temps = [20, 22, 24, 26, 28]. Mảng NumPy có .mean() tính trung bình cộng.",
        goal="Mật mã = nhiệt độ trung bình (số nguyên). Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="import numpy as np\ndata = np.array(temps)\nprint(data.max())\n",
        hints=["Gọi .mean() trên mảng.", "Đổi kết quả sang int."],
        requires=["import:numpy"],
        extra_globals={"temps": [20, 22, 24, 26, 28]},
        door_code=24,
    ),
    Level(
        id="22-4",
        title="Lọc điểm cao",
        story=(
            "scores = [3, 7, 8, 2, 9, 6]. Với NumPy, arr > 5 tạo mảng True/False; "
            "arr[arr > 5] chỉ giữ các phần tử lớn hơn 5."
        ),
        goal="Mật mã = số điểm lớn hơn 5. Mở cửa và tới cúp.",
        rows=DOOR_DOWN,
        starter="import numpy as np\narr = np.array(scores)\nprint(arr > 5)\n",
        hints=["Dùng mảng True/False làm chỉ số để lọc.", "Đếm số phần tử còn lại."],
        requires=["import:numpy"],
        extra_globals={"scores": [3, 7, 8, 2, 9, 6]},
        door_code=4,
    ),
    Level(
        id="22-5",
        title="Ngày bán chạy",
        story=(
            "sales là bảng số hàng bán: mỗi hàng là một cửa hàng, mỗi cột là một ngày. "
            ".sum(axis=0) cộng theo cột; .argmax() cho VỊ TRÍ của số lớn nhất."
        ),
        goal="Mật mã = vị trí (đếm từ 0) của ngày bán được nhiều nhất. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="import numpy as np\ntable = np.array(sales)\nprint(table.sum())\n",
        hints=["Cộng theo cột để có tổng mỗi ngày.", "argmax trả về vị trí - đổi sang int."],
        requires=["import:numpy", "call:argmax"],
        extra_globals={"sales": [[3, 5, 2], [4, 1, 6], [2, 7, 3]]},
        door_code=1,
    ),
]

PRACTICE[23] = [
    Level(
        id="23-3",
        title="Bọ tên biến",
        story="Code này báo NameError. Đọc thông báo lỗi: nó cho biết Python không biết tên nào.",
        goal="Sửa lỗi để hero tới cúp và nói \"Tới rồi\".",
        rows=corridor("@..G..E"),
        starter='steps = 6\nmessage = "Tới rồi"\nhero.move_right(step)\nhero.say(mesage)\n',
        hints=["So từng chữ của tên biến khi tạo và khi dùng.", "Có hai chỗ gõ sai tên."],
        requires=["assign"],
        say_contains="Tới rồi",
    ),
    Level(
        id="23-4",
        title="Bọ kiểu dữ liệu",
        story="Code này báo TypeError: dùng sai kiểu dữ liệu. Có 2 chỗ sai kiểu.",
        goal="Sửa lỗi để hero nói \"Có 1 ngọc\" và tới cúp.",
        rows=corridor("@.G.E"),
        starter='gems = len(hero.find_gems())\nhero.say("Có " + gems + " ngọc")\nhero.move_right("4")\n',
        hints=["Nối chuỗi với số phải đổi số sang chuỗi.", "Số bước phải là số, không phải chuỗi."],
        requires=["call:str"],
        say_contains="Có 1 ngọc",
    ),
    Level(
        id="23-5",
        title="Bọ lặp vô hạn",
        story="Chương trình này không bao giờ dừng: điều kiện của while luôn đúng. Hãy tìm vì sao.",
        goal="Sửa vòng lặp để hero đi đúng 5 bước, nhặt hết ngọc và tới cúp.",
        rows=corridor("@GGGGE"),
        starter="count = 0\nwhile count < 5:\n    hero.move_right()\n",
        hints=["Giá trị của count có bao giờ thay đổi không?", "Mỗi vòng lặp cần tăng count lên."],
        requires=["while"],
    ),
]

# ================================================================ BÀI 6: THỬ THÁCH VẬT THỂ MỚI
# Ký hiệu thêm: O thùng gỗ, Q thùng có ngọc, k chìa khoá, L cửa khoá, C rương báu.
CHEST_AND_DOOR = [
    "#######",
    "#C#####",
    "#@.D.E#",
    "#######",
]
CHALLENGES: dict[int, Level] = {
    1: Level(
        id="1-6",
        title="Thử thách: Thùng gỗ",
        story="Thùng gỗ chắn ngang đường! hero.attack(\"right\") đập vỡ thùng ở bên phải.",
        goal="Đập vỡ thùng gỗ, nhặt ngọc và tới cúp.",
        rows=corridor("@.O..GE"),
        starter="hero.move_right(1)\n# thùng gỗ chắn đường!\n",
        hints=["Đứng sát thùng rồi tấn công về phía thùng.", "Thùng vỡ thì đường thông - đi tiếp tới cúp."],
        requires=["call:attack"],
    ),
    2: Level(
        id="2-6",
        title="Thử thách: Chìa khoá",
        story=(
            "Đi qua chìa khoá (k) là nhặt được. Cửa khoá (L) mở bằng hero.unlock(\"right\") khi đã có chìa. "
            "Hãy dùng một biến steps cho cả hai đoạn đường."
        ),
        goal="Nhặt chìa, mở cửa khoá, tới cúp - dùng biến steps.",
        rows=corridor("@.k.L.GE"),
        starter="steps = 1\nhero.move_right(steps)\n",
        hints=["Đoạn đầu dài 3 ô (đi qua chìa).", "Đoạn sau dài hơn đoạn đầu 1 ô: steps + 1."],
        requires=["assign", "call:unlock"],
    ),
    3: Level(
        id="3-6",
        title="Thử thách: Rương bí mật",
        story="hero.look(...) còn nhận ra \"box\" (thùng) và \"chest\" (rương). hero.open_chest(\"up\") mở rương phía trên.",
        goal="Ở ngã ba: nếu trên có rương thì mở; nếu phải có thùng thì đập. Rồi tới cúp.",
        rows=[
            "########",
            "###C####",
            "#@..O.E#",
            "########",
        ],
        starter='hero.move_right(2)\nif hero.look("up") == "chest":\n    pass\n',
        hints=["Thay pass bằng lệnh mở rương phía trên.", "Viết thêm một if cho thùng gỗ bên phải."],
        requires=["if"],
        need_chests=1,
    ),
    4: Level(
        id="4-6",
        title="Thử thách: Hàng thùng",
        story="Năm cái thùng xếp thành hàng. Thùng có dấu X (Q) chứa ngọc - đập vỡ là ngọc rơi ra, đi qua để nhặt.",
        goal="Dùng vòng lặp: đập thùng rồi bước lên, lặp lại cho hết hàng. Tới cúp.",
        rows=corridor("@OQOQOE"),
        starter='hero.attack("right")\nhero.move_right()\n',
        hints=["Hai lệnh trong code ban đầu là một vòng - lặp nó lại.", "Đếm số thùng; sau vòng lặp còn thiếu một bước."],
        requires=["for"],
    ),
    5: Level(
        id="5-6",
        title="Thử thách: Cửa đôi",
        story="Có doors = \"2\" cặp chìa - cửa nối tiếp nhau. Mỗi lượt: nhặt chìa, mở cửa, bước qua.",
        goal="Lặp đúng số lượt (đổi doors sang số), mở hết cửa khoá, tới cúp.",
        rows=corridor("@kLkLE"),
        starter='# doors = "2"\nfor i in range(doors):\n    hero.move_right()\n',
        hints=["range cần số nguyên - đổi doors bằng int().", "Mỗi lượt: bước lên nhặt chìa, mở cửa bên phải, bước qua cửa."],
        requires=["call:int"],
        extra_globals={"doors": "2"},
    ),
    6: Level(
        id="6-6",
        title="Thử thách: Chiêu phá thùng",
        story="Ba cái thùng cách đều nhau. Viết một hàm làm trọn một lượt phá thùng để gọi lại nhiều lần.",
        goal="Viết hàm (ví dụ smash) gồm: bước lên, đập thùng, bước vào chỗ thùng vừa vỡ. Dùng nó 3 lần rồi tới cúp.",
        rows=corridor("@.O.O.O.E"),
        starter="def smash():\n    hero.move_right()\n\nsmash()\n",
        hints=["Thêm lệnh đập thùng và một bước nữa vào hàm.", "Sau 3 lần gọi hàm, còn 2 ô nữa tới cúp."],
        requires=["def"],
    ),
    7: Level(
        id="7-6",
        title="Thử thách: Thư trong rương",
        story="note = \"Mật mã ở cuối thư: 42\". Mở rương phía trên, rồi cắt lấy 2 ký tự cuối của note làm mật mã.",
        goal="Mở rương, cắt chuỗi lấy mật mã, mở cửa và tới cúp.",
        rows=CHEST_AND_DOOR,
        starter='# note = "Mật mã ở cuối thư: 42"\nprint(note[0])\n',
        hints=["Chỉ số âm đếm từ cuối: [-2:] lấy 2 ký tự cuối.", "Đứng cạnh cửa rồi mới nhập mật mã."],
        requires=["slice"],
        extra_globals={"note": "Mật mã ở cuối thư: 42"},
        door_code=42,
        need_chests=1,
    ),
    8: Level(
        id="8-6",
        title="Thử thách: Danh sách thùng",
        story=(
            "hero.find_objects(\"box\") trả về list toạ độ các thùng. Đứng bên TRÁI mỗi thùng rồi đập. "
            "Ngọc rơi ra phải đi nhặt hết."
        ),
        goal="Duyệt list thùng để đập hết, nhặt hết ngọc rơi ra, rồi tới cổng.",
        rows=[
            "#########",
            "#@..Q...#",
            "#.......#",
            "#..Q..O.#",
            "#......E#",
            "#########",
        ],
        starter='boxes = hero.find_objects("box")\nprint(boxes)\n',
        hints=["Ô bên trái thùng có toạ độ x nhỏ hơn 1.", "Đập xong hết thùng mới tìm lại danh sách ngọc."],
        requires=["for", "call:find_objects"],
    ),
    9: Level(
        id="9-6",
        title="Thử thách: Sổ kế hoạch",
        story="plan là dict: hướng → vật ở hướng đó (\"chest\" hoặc \"box\"). Duyệt plan.items() để xử lý từng hướng.",
        goal="Mở hết rương, đập thùng theo plan, rồi tới cúp.",
        rows=[
            "#######",
            "##C####",
            "#.@O.E#",
            "##C####",
            "#######",
        ],
        starter="for direction in plan:\n    print(direction)\n",
        hints=["for direction, thing in plan.items() cho cả hướng lẫn vật.", "Rương thì mở, thùng thì đập."],
        requires=["for", "call:items"],
        extra_globals={"plan": {"up": "chest", "down": "chest", "right": "box"}},
        need_chests=2,
    ),
    10: Level(
        id="10-6",
        title="Thử thách: Ba rương báu",
        story="Dùng hero.scan() và comprehension để tìm toạ độ mọi ô \"chest\". Mở rương từ ô ngay bên dưới nó.",
        goal="Tìm ba rương bằng comprehension, mở hết, rồi tới cổng.",
        rows=[
            "#########",
            "#.C.C.C.#",
            "#@......#",
            "#......E#",
            "#########",
        ],
        starter="grid = hero.scan()\nprint(grid[1])\n",
        hints=["Giữ lại (x, y) khi ô là \"chest\".", "Đi tới (x, y + 1) rồi mở rương hướng \"up\"."],
        requires=["listcomp", "call:scan"],
        need_chests=3,
    ),
    11: Level(
        id="11-6",
        title="Thử thách: Chỉ đập thùng",
        story="breakable = {\"box\"} là tập những thứ được phép đập. Đi dọc hành lang: gặp thứ trong tập thì đập, không thì bước.",
        goal="Dùng toán tử in với tập breakable để dọn đường tới cúp.",
        rows=corridor("@.O.QO.E"),
        starter='while hero.look("right") != "exit":\n    hero.move_right()\n',
        hints=["Trong vòng lặp, kiểm tra hero.look(\"right\") có nằm trong breakable không.", "Sau vòng lặp, bước thêm 1 ô vào cổng."],
        requires=["membership", "while"],
        extra_globals={"breakable": {"box"}},
    ),
    12: Level(
        id="12-6",
        title="Thử thách: Chìa và căn bậc hai",
        story="Nhặt chìa để qua cửa khoá. Cửa mật mã cần phần nguyên căn bậc hai của area = 50.",
        goal="Nhặt chìa, mở cửa khoá, nhập mật mã int(math.sqrt(area)), tới cúp.",
        rows=corridor("@k.L.D.GE"),
        starter="import math\nprint(math.sqrt(4))\n",
        hints=["Chìa ở ngay ô thứ nhất bên phải - đi 2 ô là tới sát cửa khoá.", "math.sqrt(50) ≈ 7.07 - chỉ lấy phần nguyên."],
        requires=["import:math", "call:unlock"],
        extra_globals={"area": 50},
        door_code=7,
    ),
    13: Level(
        id="13-6",
        title="Thử thách: Khoá ba màu",
        story=(
            "Đập thùng, rồi mở khoá màu: colors = [\"đỏ\", \"xanh\", \"vàng\"] phải xếp đúng thứ tự (dùng permutations và try_code). "
            "Qua cửa xong mở rương phía trên rồi tới cúp."
        ),
        goal="Đập thùng, thử hoán vị tới khi cửa mở, mở rương, tới cúp.",
        rows=[
            "########",
            "#####C##",
            "#@O.D.E#",
            "########",
        ],
        starter="from itertools import permutations\nhero.attack(\"right\")\n",
        hints=["Sau khi đập thùng, bước 2 ô là tới sát cửa.", "Mở được cửa thì dừng vòng lặp; rương nằm trên ô ngay sau cửa."],
        requires=["call:permutations"],
        extra_globals={"colors": ["đỏ", "xanh", "vàng"]},
        door_code=("vàng", "đỏ", "xanh"),
        need_chests=1,
    ),
    14: Level(
        id="14-6",
        title="Thử thách: Kiểm kê thùng",
        story="Mật mã = số thùng gỗ trong phòng. Dùng hero.scan() rồi Counter đếm mọi ô của bản đồ.",
        goal="Đếm số ô \"box\" bằng Counter, nhập làm mật mã, tới cúp.",
        rows=[
            "#########",
            "#O.O..O.#",
            "#@..D.GE#",
            "#.O.....#",
            "#########",
        ],
        starter="from collections import Counter\ngrid = hero.scan()\nprint(grid[1])\n",
        hints=["Trải phẳng bản đồ rồi đưa vào Counter.", "Tra kết quả Counter với khoá \"box\"."],
        requires=["call:Counter", "call:scan"],
        door_code=4,
    ),
    15: Level(
        id="15-6",
        title="Thử thách: Rương Giáng sinh",
        story="Mở rương phía trên. Mật mã cửa = thứ trong tuần (weekday) của day = \"2026-12-25\".",
        goal="Mở rương, tính weekday() của ngày Giáng sinh, mở cửa, tới cúp.",
        rows=CHEST_AND_DOOR,
        starter="from datetime import date\nprint(day)\n",
        hints=["Đổi day sang date bằng fromisoformat.", "Mở rương trước, rồi đi 1 ô tới sát cửa."],
        requires=["import:datetime"],
        extra_globals={"day": "2026-12-25"},
        door_code=4,
        need_chests=1,
    ),
    16: Level(
        id="16-6",
        title="Thử thách: Quên chìa",
        story=(
            "hero.unlock khi chưa có chìa sẽ báo lỗi ValueError. Chìa nằm ngay SAU LƯNG hero. "
            "Hãy thử mở cửa, nếu lỗi thì quay lại lấy chìa rồi mở lại."
        ),
        goal="Bắt lỗi ValueError khi mở cửa không có chìa, lấy chìa, mở cửa, tới cúp.",
        rows=corridor("k@L.GE"),
        starter='hero.unlock("right")\nhero.move_right(4)\n',
        hints=["Bọc lệnh unlock đầu tiên trong try.", "Trong except: lùi 1 ô lấy chìa, quay lại, mở cửa."],
        requires=["try", "except:ValueError"],
    ),
    17: Level(
        id="17-6",
        title="Thử thách: Nhà thám hiểm",
        story="Viết class Explorer có phương thức open(direction): mở rương ở hướng đó và đếm số rương đã mở.",
        goal="Dùng Explorer mở 2 rương (trên và trái), nói \"Mở 2 rương\", rồi tới cúp.",
        rows=[
            "#######",
            "###C###",
            "##C@.E#",
            "#######",
        ],
        starter="class Explorer:\n    def __init__(self):\n        self.opened = 0\n",
        hints=["Phương thức open(self, direction) gọi hero.open_chest rồi tăng self.opened.", "Nói số rương bằng f-string với e.opened."],
        requires=["class", "method"],
        need_chests=2,
        say_contains="Mở 2 rương",
    ),
    18: Level(
        id="18-6",
        title="Thử thách: Đường kho báu",
        story=(
            "Hành lang có thùng, chìa, quái, cửa khoá; một rương nằm phía dưới đường đi. "
            "Viết một vòng lặp tự xử lý mọi thứ: nhìn sang phải để quyết định làm gì, và mở rương nếu thấy ở dưới."
        ),
        goal="Dùng vòng lặp while + if để vượt hết chướng ngại, mở rương, tới cúp.",
        rows=[
            "#############",
            "#@.O.k.r.L.E#",
            "##########C##",
        ],
        starter='while hero.look("right") != "exit":\n    hero.move_right()\n',
        hints=[
            "Thùng hoặc quái thì tấn công, cửa khoá thì unlock, còn lại thì bước.",
            "Sau mỗi bước, kiểm tra phía dưới có rương không.",
        ],
        requires=["while", "if"],
        need_chests=1,
    ),
    19: Level(
        id="19-6",
        title="Thử thách: Mở rương có thứ tự",
        story="hero.find_objects(\"chest\") cho list rương. Dùng sorted với key=lambda để xếp rương theo cột x từ trái sang phải.",
        goal="Xếp rương bằng sorted + lambda, mở từng rương từ ô ngay dưới nó, rồi tới cổng.",
        rows=[
            "#########",
            "#C..C..C#",
            "#.......#",
            "#@.....E#",
            "#########",
        ],
        starter='chests = hero.find_objects("chest")\nprint(chests)\n',
        hints=["key=lambda c: c[\"x\"]", "Đi tới (x, y + 1) rồi mở rương hướng \"up\"."],
        requires=["lambda", "call:sorted"],
        need_chests=3,
    ),
    20: Level(
        id="20-6",
        title="Thử thách: Mật thư chỉ đường",
        story=(
            "letter = \"Rương ở hướng up, cửa mã 7314.\" Dùng regex lấy hướng (chữ sau \"hướng \") và mật mã (số sau \"mã \")."
        ),
        goal="Đọc mật thư bằng regex, mở rương đúng hướng, mở cửa, tới cúp.",
        rows=CHEST_AND_DOOR,
        starter="import re\nprint(letter)\n",
        hints=["\\w+ khớp một từ, \\d+ khớp một số.", "Đặt phần cần lấy trong ( ) rồi dùng .group(1)."],
        requires=["import:re"],
        extra_globals={"letter": "Rương ở hướng up, cửa mã 7314."},
        door_code=7314,
        need_chests=1,
    ),
    21: Level(
        id="21-6",
        title="Thử thách: Bùa mở rương",
        story="Viết closure make_opener(direction) trả về một hàm mở rương ở hướng đó. Tạo bùa cho hướng up và left.",
        goal="Dùng các hàm tạo từ make_opener mở 2 rương, đập thùng, tới cúp.",
        rows=[
            "#######",
            "##C####",
            "#C@O.E#",
            "#######",
        ],
        starter="def make_opener(direction):\n    pass\n",
        hints=["Hàm bên trong không cần tham số - nó nhớ direction.", "Mở xong 2 rương thì đập thùng bên phải rồi đi 3 ô."],
        requires=["closure"],
        need_chests=2,
    ),
    22: Level(
        id="22-6",
        title="Thử thách: Rương nặng nhất",
        story="Mở rương phía trên. weights là bảng cân nặng các thỏi vàng; mật mã = số lớn nhất trong bảng (dùng NumPy).",
        goal="Mở rương, tìm max của mảng NumPy, mở cửa, tới cúp.",
        rows=CHEST_AND_DOOR,
        starter="import numpy as np\nprint(np.array(weights).shape)\n",
        hints=["Mảng NumPy có .max().", "Đổi kết quả sang int trước khi nhập."],
        requires=["import:numpy"],
        extra_globals={"weights": [[3, 8], [6, 2]]},
        door_code=8,
        need_chests=1,
    ),
    23: Level(
        id="23-6",
        title="Thử thách: Bọ vật thể",
        story="Code này có nhiều lỗi: sai thứ tự (mở cửa khi chưa có chìa), gõ sai tên lệnh, đánh sai hướng. Sửa hết!",
        goal="Nhặt chìa, mở rương bên dưới, mở cửa khoá, đập thùng và tới cúp.",
        rows=[
            "##########",
            "#@k.L.O.E#",
            "###C######",
        ],
        starter=(
            'hero.unlock("right")\n'
            "hero.move_right(2)\n"
            'hero.open_chests("down")\n'
            'hero.attack("left")\n'
            "hero.move_right(3)\n"
        ),
        hints=["Phải nhặt chìa trước khi unlock - để ý thứ tự các dòng.", "Tên lệnh đúng là open_chest; thùng nằm bên phải."],
        need_chests=1,
    ),
}
for _world_number, _challenge in CHALLENGES.items():
    PRACTICE[_world_number].append(_challenge)


# ======================================================================
# levels.py
# ======================================================================

@dataclass
class Stage:
    number: int
    title: str
    skills: str
    content: str
    focus: str
    milestone: str


@dataclass
class WorldInfo:
    number: int
    stage: int
    title: str
    concept: str
    skill: str
    background: int
    levels: list[Level]


STAGES: list[Stage] = [
    Stage(
        1,
        "Cú pháp & kiểu dữ liệu nền tảng",
        "Nhập môn · Kiểu dữ liệu · Chuỗi",
        "Nhập/xuất, if-else, vòng lặp, hàm cơ bản, xử lý chuỗi (cắt, định dạng), list, tuple, dictionary.",
        "List Comprehension và list lồng nhau - viết code ngắn gọn thay cho nhiều vòng lặp lồng nhau.",
        "Nền móng cho mọi giai đoạn sau.",
    ),
    Stage(
        2,
        "Sức mạnh thư viện chuẩn",
        "Tập hợp · Toán học · Hoán vị - tổ hợp · Cấu trúc dữ liệu · Ngày giờ",
        "Phép toán tập hợp (giao, hợp), hoán vị - tổ hợp với itertools, Counter / deque trong collections, ngày giờ.",
        "Dùng đúng set hoặc Counter để tra cứu nhanh thay vì duyệt list nhiều lần.",
        "Giải các bài toán đếm, tìm kiếm, sắp xếp nhanh và gọn hơn hẳn.",
    ),
    Stage(
        3,
        "Lập trình hướng đối tượng & ngoại lệ",
        "Xử lý lỗi · Lập trình hướng đối tượng",
        "Bắt lỗi an toàn với try-except, thiết kế class, thuộc tính, magic methods (__str__, __add__, __iter__).",
        "Tự tạo kiểu dữ liệu của riêng mình và giữ chương trình không bị dừng khi gặp lỗi.",
        "Xong 3 giai đoạn đầu: vững toàn bộ kiến thức Python cơ bản.",
    ),
    Stage(
        4,
        "Lập trình hàm & kỹ thuật nâng cao",
        "Hàm có sẵn · Lập trình hàm · Biểu thức chính quy · XML · Closure và decorator",
        "map, filter, zip, lambda, biểu thức chính quy (regex), đọc XML, closure và decorator.",
        "Viết hàm nhận hàm, trả về hàm - mở rộng logic mà không sửa code cũ.",
        "Bước lên trình độ Python trung cấp.",
    ),
    Stage(
        5,
        "NumPy & gỡ lỗi thực chiến",
        "Tính toán với NumPy · Gỡ lỗi",
        "Mảng nhiều chiều với NumPy, phép tính ma trận cơ bản, đọc hiểu và sửa lỗi trong code có sẵn.",
        "Rèn kỹ năng đọc thông báo lỗi và tìm lỗi logic.",
        "Sẵn sàng học tiếp khoa học dữ liệu, AI và giải thuật nâng cao.",
    ),
]

# Bản đồ dùng lại nhiều lần.
MAP_DOOR = [
    "#########",
    "#@.GD.GE#",
    "#########",
]
MAP_DOOR_DOWN = [
    "#######",
    "#@..###",
    "###.###",
    "###D###",
    "###G###",
    "###E###",
    "#######",
]
MAP_STAIRS = [
    "#######",
    "#@G####",
    "##.G###",
    "###.G##",
    "####.G#",
    "#####E#",
    "#######",
]
MAP_WEAPON_ROOM = [
    "###########",
    "#@..r..b..#",
    "#.........#",
    "#....c...E#",
    "###########",
]

WORLDS: list[WorldInfo] = [
    # ================================================================ GIAI ĐOẠN 1
    WorldInfo(1, 1, "Khởi hành", "Cú pháp cơ bản", "Nhập môn", 1, [
        Level(
            id="1-1",
            title="Bước chân đầu tiên",
            story="Chào mừng tới CodeQuest! Hero chỉ làm theo lệnh Python bạn viết.",
            goal="Đi tới cúp vàng và nhặt viên ngọc trên đường.",
            rows=[
                "#########",
                "#@..G..E#",
                "#########",
            ],
            starter=(
                "# Dòng bắt đầu bằng # là ghi chú, Python bỏ qua.\n"
                "# Số trong ngoặc là số bước đi.\n"
                "hero.move_right(2)\n"
            ),
            hints=[
                "Số trong ngoặc là số bước hero đi.",
                "Đếm số ô từ hero tới cúp vàng, rồi sửa con số trong ngoặc.",
            ],
        ),
        Level(
            id="1-2",
            title="Rẽ góc",
            story="Mỗi lệnh nằm trên một dòng. Python chạy từ trên xuống dưới.",
            goal="Đi qua khúc quanh, nhặt ngọc, tới cúp.",
            rows=[
                "#######",
                "#@..###",
                "###G###",
                "###.###",
                "###..E#",
                "#######",
            ],
            starter="hero.move_right(2)\n# Thêm lệnh move_down và move_right\n",
            hints=[
                "Có 4 lệnh: move_up, move_down, move_left, move_right.",
                "Chia đường đi thành 3 đoạn thẳng, mỗi đoạn một lệnh.",
            ],
        ),
        Level(
            id="1-3",
            title="Lời chào",
            story="hero.say(...) cho hero nói. Chữ phải nằm trong dấu nháy: \"Xin chào\".",
            goal="Nói \"Xin chào\" rồi đi tới cúp.",
            rows=[
                "##########",
                "#@......E#",
                "##########",
            ],
            starter='hero.say("...")\nhero.move_right(1)\n',
            hints=[
                "Chuỗi phải nằm trong dấu nháy kép \" \". Gõ chaof sẽ ra chào.",
                "Câu cần nói phải đúng chữ \"Xin chào\". Sau đó đếm lại số bước tới cúp.",
            ],
            requires=["call:say"],
            say_contains="Xin chào",
        ),
    ]),
    WorldInfo(2, 1, "Kho đồ", "Biến và kiểu dữ liệu", "Kiểu dữ liệu", 2, [
        Level(
            id="2-1",
            title="Hộp chứa số bước",
            story="Biến là chiếc hộp có tên, cất một giá trị: steps = 3",
            goal="Gán đúng số bước vào biến steps rồi dùng biến đó để đi.",
            rows=[
                "##########",
                "#@..G...E#",
                "##########",
            ],
            starter="steps = 1  # đổi số này\nhero.move_right(steps)\n",
            hints=[
                "Đếm số ô từ hero tới cúp.",
                "Chỉ cần sửa giá trị gán cho steps, dòng thứ hai giữ nguyên.",
            ],
            requires=["assign"],
        ),
        Level(
            id="2-2",
            title="Đếm vàng",
            story=(
                "Kiểu dữ liệu: số nguyên (int), số thực (float), chuỗi (str), đúng/sai (bool). "
                "Mỗi viên ngọc giá 10 vàng."
            ),
            goal="Nhặt 3 ngọc, tính total từ gems và value, nói tổng số vàng rồi tới cúp.",
            rows=[
                "###########",
                "#@GGG....E#",
                "###########",
            ],
            starter=(
                "gems = 3\n"
                "value = 10\n"
                "total = 0  # tính lại total\n"
                "hero.move_right(8)\n"
            ),
            hints=[
                "Phép nhân dùng dấu *.",
                "Nối chuỗi với số thì phải đổi số sang chuỗi bằng str(...).",
            ],
            requires=["assign"],
            say_contains="30",
        ),
    ]),
    WorldInfo(3, 1, "Ngã rẽ", "Câu lệnh điều kiện", "Nhập môn", 3, [
        Level(
            id="3-1",
            title="Quái chặn đường",
            story="hero.look(\"right\") cho biết ô bên phải là gì: \"enemy\", \"wall\", \"spike\", \"gem\", \"floor\"...",
            goal="Nếu bên phải có quái thì tấn công, sau đó đi tới cúp.",
            rows=[
                "##########",
                "#@..r...E#",
                "##########",
            ],
            starter=(
                "hero.move_right(2)\n"
                'if hero.look("right") == "enemy":\n'
                "    # thụt vào 4 khoảng trắng\n"
                "    pass\n"
            ),
            hints=[
                "Lệnh bên trong if phải thụt vào 4 khoảng trắng.",
                "Thay pass bằng lệnh tấn công về phía quái; lệnh đi tiếp đặt NGOÀI if (không thụt lề).",
            ],
            requires=["if"],
        ),
        Level(
            id="3-2",
            title="Chọn lối",
            story="if / else: nếu điều kiện đúng làm việc này, ngược lại làm việc kia.",
            goal="Ở ngã ba, tránh lối có gai và tới cúp.",
            rows=[
                "#######",
                "###^###",
                "#@..###",
                "###.###",
                "###.E##",
                "#######",
            ],
            starter=(
                "hero.move_right(2)\n"
                'if hero.look("up") == "spike":\n'
                "    pass  # đi lối khác\n"
                "else:\n"
                "    hero.move_up()\n"
            ),
            hints=[
                "Lối nào không có gai thì đi lối đó.",
                "Sau khối if/else, hero vẫn cần đi thêm để tới cúp.",
            ],
            requires=["if"],
        ),
    ]),
    WorldInfo(4, 1, "Vòng lặp", "for và while", "Nhập môn", 4, [
        Level(
            id="4-1",
            title="Hàng ngọc",
            story="for i in range(n): lặp lại khối lệnh n lần.",
            goal="Dùng vòng lặp for để nhặt 8 viên ngọc và tới cúp.",
            rows=[
                "############",
                "#@GGGGGGGGE#",
                "############",
            ],
            starter="for i in range(1):\n    hero.move_right()\n",
            hints=[
                "range(n) lặp n lần.",
                "Đếm tổng số bước từ hero tới cúp - đó chính là số lần lặp.",
            ],
            requires=["for"],
        ),
        Level(
            id="4-2",
            title="Cầu thang",
            story="Khối lệnh trong vòng lặp có thể có nhiều dòng.",
            goal="Đi xuống cầu thang, nhặt hết ngọc, tới cúp.",
            rows=MAP_STAIRS,
            starter="for i in range(4):\n    hero.move_right()\n",
            hints=[
                "Mỗi bậc thang gồm 2 bước.",
                "Bước thứ hai phải thụt lề cùng mức với bước thứ nhất để nằm trong vòng lặp.",
            ],
            requires=["for"],
        ),
        Level(
            id="4-3",
            title="Hành lang dài",
            story="while điều_kiện: lặp lại chừng nào điều kiện còn đúng.",
            goal="Đi tới khi bên phải là cổng, rồi bước vào cổng.",
            rows=[
                "###############",
                "#@.G.G.G.G...E#",
                "###############",
            ],
            starter='while hero.look("right") != "exit":\n    pass\n',
            hints=[
                "Thay pass bằng lệnh cho hero tiến lên.",
                "Vòng lặp dừng khi cổng ở ngay bên phải - còn thiếu một bước nữa.",
            ],
            requires=["while"],
        ),
    ]),
    WorldInfo(5, 1, "Biến hình", "Ép kiểu dữ liệu", "Kiểu dữ liệu", 5, [
        Level(
            id="5-1",
            title="Mật mã chuỗi",
            story=(
                "Biến secret chứa mật mã nhưng ở dạng chuỗi: secret = \"42\". "
                "Cửa chỉ nhận số nguyên (int)."
            ),
            goal="Đứng cạnh cửa, nhập mật mã bằng hero.enter_code(...), rồi tới cúp.",
            rows=MAP_DOOR,
            starter=(
                "# secret đã có sẵn: secret = \"42\"\n"
                "hero.move_right(2)\n"
                "hero.enter_code(secret)\n"
            ),
            hints=[
                "int(...) đổi chuỗi thành số nguyên.",
                "Mở cửa xong, đếm số bước còn lại tới cúp.",
            ],
            requires=["call:int"],
            extra_globals={"secret": "42"},
            door_code=42,
        ),
        Level(
            id="5-2",
            title="Cộng hai mảnh",
            story="Mật mã bị chia làm 2 mảnh chuỗi: a = \"12\", b = \"30\". Mật mã là tổng của chúng.",
            goal="Đổi a, b sang số, cộng lại, mở cửa và tới cúp.",
            rows=MAP_DOOR_DOWN,
            starter=(
                "# a = \"12\", b = \"30\"\n"
                "print(a + b)  # thử xem: chuỗi cộng chuỗi ra gì?\n"
                "hero.move_right(2)\n"
                "hero.move_down(1)\n"
            ),
            hints=[
                "\"12\" + \"30\" là nối chuỗi, không phải cộng số.",
                "Đổi từng biến sang số trước, rồi mới cộng.",
            ],
            requires=["call:int"],
            extra_globals={"a": "12", "b": "30"},
            door_code=42,
        ),
    ]),
    WorldInfo(6, 1, "Phép thuật", "Hàm và hàm có sẵn", "Nhập môn", 1, [
        Level(
            id="6-1",
            title="Chiêu nhảy gai",
            story="def ten_ham(): tạo chiêu thức riêng để gọi lại nhiều lần.",
            goal="Viết hàm hop() vòng qua một cái gai và dùng nó để qua cả 3 gai.",
            rows=[
                "#############",
                "#...G..G..G.#",
                "#@..^..^..^E#",
                "#############",
            ],
            starter=(
                "def hop():\n"
                "    hero.move_up()\n"
                "    # thêm 2 lệnh nữa\n"
                "\n"
                "hero.move_right(2)\n"
                "hop()\n"
            ),
            hints=[
                "Chiêu hop gồm 3 bước: lên, sang phải, xuống.",
                "Giữa các lần gọi hop(), hero cần đi thêm tới sát gai tiếp theo.",
            ],
            requires=["def", "call:hop"],
        ),
        Level(
            id="6-2",
            title="Kiểm kê",
            story="Hàm có sẵn của Python: len(), sum(), min(), max()... hero.find_gems() trả về danh sách ngọc.",
            goal="Nói số ngọc trên bản đồ bằng len(), rồi nhặt hết và tới cúp.",
            rows=[
                "##############",
                "#@G.G.G.G.G.E#",
                "##############",
            ],
            starter="gems = hero.find_gems()\nhero.say(gems)\n",
            hints=[
                "len(...) cho biết danh sách có bao nhiêu phần tử.",
                "Nói số lượng, rồi dùng vòng lặp để đi tới cúp.",
            ],
            requires=["call:len"],
            say_contains="5",
        ),
        Level(
            id="6-3",
            title="Hàm trả kết quả",
            story="return trả giá trị về cho nơi gọi hàm. Mật mã = gấp đôi base (base = 21).",
            goal="Viết hàm double(n) trả về gấp đôi n, dùng nó để mở cửa.",
            rows=[
                "###########",
                "#@..GD..GE#",
                "###########",
            ],
            starter="def double(n):\n    pass\n\nhero.move_right(3)\n",
            hints=[
                "Hàm cần trả kết quả bằng return.",
                "Truyền biến base vào hàm, rồi đưa kết quả vào hero.enter_code(...).",
            ],
            requires=["def", "return"],
            extra_globals={"base": 21},
            door_code=42,
        ),
    ]),
    WorldInfo(7, 1, "Cuộn giấy", "Xử lý chuỗi", "Chuỗi", 2, [
        Level(
            id="7-1",
            title="Cắt chữ",
            story=(
                "Cuộn giấy ghi scroll = \"abc42xyz\". Mật mã là 2 chữ số nằm ở vị trí 3 và 4 "
                "(vị trí đếm từ 0). Cắt chuỗi: scroll[đầu:cuối]."
            ),
            goal="Cắt lấy mật mã từ scroll, đổi sang số, mở cửa và tới cúp.",
            rows=MAP_DOOR,
            starter=(
                "# scroll = \"abc42xyz\"\n"
                "print(scroll[0])  # chữ đầu tiên\n"
                "hero.move_right(2)\n"
            ),
            hints=[
                "Vị trí cuối trong [đầu:cuối] KHÔNG được lấy - lấy tới trước nó.",
                "Cắt ra được chuỗi \"42\" rồi thì vẫn phải đổi sang int.",
            ],
            requires=["slice", "call:int"],
            extra_globals={"scroll": "abc42xyz"},
            door_code=42,
        ),
        Level(
            id="7-2",
            title="Bảng tên",
            story=(
                "Bạn đồng hành tên name = \"mèo\". f-string ghép biến vào câu: f\"Xin chào {name}\". "
                "Chuỗi có sẵn các hàm như .upper() (viết hoa), .lower(), .title()."
            ),
            goal="Nói đúng câu \"MÈO có 3 ngọc\" (tên viết HOA, số ngọc đếm bằng code) rồi tới cúp.",
            rows=[
                "###########",
                "#@.G.G.G.E#",
                "###########",
            ],
            starter=(
                "# name = \"mèo\"\n"
                "count = len(hero.find_gems())\n"
                'hero.say("name có count ngọc")  # chưa đúng!\n'
                "hero.move_right(8)\n"
            ),
            hints=[
                "Thêm chữ f trước dấu nháy và đặt tên biến trong { }.",
                "Trong { } có thể gọi hàm của chuỗi, ví dụ viết hoa tên.",
            ],
            requires=["fstring", "call:upper"],
            extra_globals={"name": "mèo"},
            say_contains="MÈO có 3 ngọc",
        ),
    ]),
    WorldInfo(8, 1, "Ba lô", "List và tuple", "Kiểu dữ liệu", 2, [
        Level(
            id="8-1",
            title="Bản đồ kho báu",
            story=(
                "hero.find_gems() trả về list, mỗi phần tử là dict {\"x\":..., \"y\":...}. "
                "hero.move_to(x, y) tự tìm đường. hero.exit_position là tuple (x, y)."
            ),
            goal="Duyệt danh sách ngọc, nhặt hết rồi tới cổng.",
            rows=[
                "###########",
                "#@.G#...G.#",
                "#.##.#.##.#",
                "#..G.G...E#",
                "###########",
            ],
            starter=(
                "gems = hero.find_gems()\n"
                "print(gems)\n"
                "exit_x, exit_y = hero.exit_position  # mở gói tuple\n"
            ),
            hints=[
                "Mỗi viên ngọc là dict có khoá \"x\" và \"y\".",
                "Duyệt list ngọc bằng for, mỗi vòng đi tới toạ độ của viên đó; cuối cùng đi tới cổng.",
            ],
            requires=["for", "call:move_to"],
        ),
        Level(
            id="8-2",
            title="Dọn phòng",
            story="hero.find_enemies() trả về list quái. hero.attack_target(x, y) tự đi tới và đánh.",
            goal="Hạ hết quái trong phòng rồi tới cổng.",
            rows=[
                "############",
                "#@..r......#",
                "#.r.....r..#",
                "#.........E#",
                "############",
            ],
            starter="enemies = hero.find_enemies()\nprint(len(enemies), \"quái\")\n",
            hints=[
                "Duyệt list quái bằng for.",
                "Lấy toạ độ của từng quái trong dict rồi dùng attack_target.",
            ],
            requires=["for", "call:attack_target"],
            kill_all=True,
        ),
    ]),
    WorldInfo(9, 1, "Sổ tay", "Dictionary và set", "Kiểu dữ liệu", 3, [
        Level(
            id="9-1",
            title="Điểm yếu",
            story=(
                "Mỗi loại quái chỉ sợ một vũ khí: robot → \"hammer\", barrel → \"axe\", cannon → \"bow\". "
                "Dùng dict để tra cứu: weakness[\"robot\"]."
            ),
            goal="Tạo dict weakness, hạ hết quái bằng đúng vũ khí, tới cổng.",
            rows=MAP_WEAPON_ROOM,
            starter=(
                'weakness = {"robot": "hammer"}\n'
                "for enemy in hero.find_enemies():\n"
                '    print(enemy["type"])\n'
            ),
            hints=[
                "Dict cần đủ 3 cặp loại quái → vũ khí.",
                "Tra vũ khí bằng loại quái làm khoá, rồi truyền vũ khí vào attack_target.",
            ],
            requires=["dict", "for"],
            weapons=True,
            kill_all=True,
        ),
        Level(
            id="9-2",
            title="Bộ sưu tập màu",
            story="set chỉ giữ các giá trị KHÔNG trùng nhau. Mỗi viên ngọc có gem[\"color\"].",
            goal="Đếm số MÀU ngọc khác nhau bằng set, nói ra, rồi nhặt hết và tới cúp.",
            rows=[
                "###########",
                "#@121321.E#",
                "###########",
            ],
            starter="colors = set()\nfor gem in hero.find_gems():\n    pass\n",
            hints=[
                "set.add(...) thêm phần tử, giá trị trùng tự bị bỏ qua.",
                "len(set) cho số màu khác nhau. Nói ra rồi đi tới cúp.",
            ],
            requires=["set", "for"],
            say_contains="3",
        ),
    ]),
    WorldInfo(10, 1, "Đội hình", "List comprehension & list lồng nhau", "Kiểu dữ liệu", 4, [
        Level(
            id="10-1",
            title="Lọc ngọc xanh",
            story=(
                "List comprehension tạo list mới chỉ trong 1 dòng: [x for x in danh_sach if điều_kiện]. "
                "Mật mã cửa = số ngọc màu 3. Ngọc nhặt rồi sẽ biến mất, nên hãy đếm TRƯỚC khi đi."
            ),
            goal="Dùng list comprehension lọc ngọc màu 3, nhập số lượng làm mật mã, tới cúp.",
            rows=[
                "###########",
                "#@1323.D.E#",
                "###########",
            ],
            starter=(
                "gems = hero.find_gems()\n"
                "blue = []  # chỉ lấy ngọc màu 3\n"
                "hero.move_right(5)\n"
            ),
            hints=[
                "Cấu trúc: [biến for biến in list if điều_kiện].",
                "Điều kiện so sánh khoá \"color\" của mỗi viên ngọc với số 3.",
            ],
            requires=["listcomp"],
            door_code=2,
        ),
        Level(
            id="10-2",
            title="Bản đồ ô vuông",
            story=(
                "hero.scan() trả về bản đồ dạng list lồng nhau: mỗi hàng là một list các ô "
                "(\"wall\", \"floor\", \"spike\"...). grid[y][x] là ô ở hàng y, cột x. "
                "Mật mã = tổng số gai trên bản đồ."
            ),
            goal="Đếm số gai trong list lồng nhau, nhập mật mã, tới cúp.",
            rows=[
                "#########",
                "#^.^.^..#",
                "#@...D.E#",
                "#^..^...#",
                "#########",
            ],
            starter=(
                "grid = hero.scan()\n"
                "print(grid[1])  # hàng số 1\n"
                "print(grid[2][1])  # ô ở hàng 2, cột 1\n"
                "hero.move_right(3)\n"
            ),
            hints=[
                "Mỗi hàng là một list - list có hàm .count(giá_trị).",
                "Đếm từng hàng rồi cộng tất cả lại (sum + comprehension).",
            ],
            requires=["listcomp", "call:scan"],
            door_code=5,
        ),
    ]),
    # ================================================================ GIAI ĐOẠN 2
    WorldInfo(11, 2, "Tập hợp", "Giao, hợp tập hợp", "Tập hợp", 5, [
        Level(
            id="11-1",
            title="Hai trinh sát",
            story=(
                "Hai trinh sát báo về loại quái họ thấy: scout_a và scout_b. "
                "set(a) & set(b) là loại CẢ HAI cùng thấy (giao). set(a) | set(b) là TẤT CẢ loại (hợp)."
            ),
            goal="Nói số loại quái khác nhau (hợp). Mật mã = số loại cả hai cùng thấy (giao).",
            rows=MAP_DOOR,
            starter=(
                "# scout_a, scout_b: 2 danh sách loại quái\n"
                "a = set(scout_a)\n"
                "print(a)\n"
                "hero.move_right(2)\n"
            ),
            hints=[
                "Đổi cả hai list sang set trước.",
                "Toán tử & cho phần giao, | cho phần hợp; len() để đếm.",
            ],
            requires=["op:& or call:intersection", "op:| or call:union"],
            extra_globals={
                "scout_a": ["robot", "barrel", "cannon", "robot"],
                "scout_b": ["cannon", "duck", "robot", "cannon"],
            },
            door_code=2,
            say_contains="4",
        ),
    ]),
    WorldInfo(12, 2, "Toán học", "Thư viện math", "Toán học", 6, [
        Level(
            id="12-1",
            title="Chiếc thang",
            story=(
                "Thang dựa vào tường: chân thang cách tường a = 6 m, đỉnh thang cao b = 8 m. "
                "Theo định lý Pytago, thang dài √(a² + b²). Dùng math.sqrt."
            ),
            goal="import math, tính chiều dài thang, nhập làm mật mã (số nguyên), tới cúp.",
            rows=MAP_DOOR_DOWN,
            starter=(
                "import math\n"
                "print(math.pi)\n"
                "hero.move_right(2)\n"
                "hero.move_down(1)\n"
            ),
            hints=[
                "a ** 2 là a bình phương.",
                "math.sqrt trả về số thực (10.0) - đổi sang int trước khi nhập.",
            ],
            requires=["import:math"],
            extra_globals={"a": 6, "b": 8},
            door_code=10,
        ),
        Level(
            id="12-2",
            title="Chia túi quà",
            story=(
                "Có 84 cái kẹo và 36 cái bánh. Chia vào các túi giống hệt nhau, không thừa. "
                "Nhiều túi nhất là ước chung lớn nhất: math.gcd(84, 36)."
            ),
            goal="Tính số túi bằng math.gcd, mở cửa, tới cúp.",
            rows=MAP_DOOR,
            starter="import math\nhero.move_right(2)\n",
            hints=["Biến có sẵn: candies = 84, cakes = 36.", "gcd = greatest common divisor = ước chung lớn nhất."],
            requires=["call:gcd"],
            extra_globals={"candies": 84, "cakes": 36},
            door_code=12,
        ),
    ]),
    WorldInfo(13, 2, "Hoán vị", "itertools", "Hoán vị - tổ hợp", 1, [
        Level(
            id="13-1",
            title="Khoá ba rune",
            story=(
                "Khoá cửa có 3 rune: runes = [\"sun\", \"moon\", \"star\"], phải xếp đúng thứ tự. "
                "permutations(runes) sinh MỌI cách sắp xếp. hero.try_code(...) thử mà không mất máu, "
                "trả về True nếu cửa mở."
            ),
            goal="Thử lần lượt các hoán vị tới khi cửa mở, rồi tới cúp.",
            rows=MAP_DOOR,
            starter=(
                "from itertools import permutations\n"
                "print(list(permutations([1, 2])))\n"
                "hero.move_right(2)\n"
            ),
            hints=[
                "Duyệt for qua permutations(runes); mỗi phần tử là một tuple.",
                "Mở được rồi thì dừng vòng lặp bằng break.",
            ],
            requires=["call:permutations"],
            extra_globals={"runes": ["sun", "moon", "star"]},
            door_code=("star", "sun", "moon"),
        ),
        Level(
            id="13-2",
            title="Cặp ngọc may mắn",
            story=(
                "Trong values = [3, 8, 5, 12, 7] có đúng 1 cặp số cộng lại bằng 20. "
                "combinations(values, 2) sinh mọi cặp 2 số. Mật mã = TÍCH của cặp đó."
            ),
            goal="Tìm cặp có tổng 20, nhập tích của chúng, tới cúp.",
            rows=MAP_DOOR_DOWN,
            starter=(
                "from itertools import combinations\n"
                "for pair in combinations([1, 2, 3], 2):\n"
                "    print(pair)\n"
            ),
            hints=[
                "Mở gói mỗi cặp thành 2 biến ngay trong vòng for.",
                "Kiểm tra tổng bằng if, lưu tích lại để dùng sau vòng lặp.",
            ],
            requires=["call:combinations"],
            extra_globals={"values": [3, 8, 5, 12, 7]},
            door_code=96,
        ),
    ]),
    WorldInfo(14, 2, "Kho quân", "collections", "Cấu trúc dữ liệu", 2, [
        Level(
            id="14-1",
            title="Điểm danh quân địch",
            story=(
                "Counter đếm số lần xuất hiện của từng giá trị. "
                "Counter([...]).most_common(1) cho giá trị xuất hiện nhiều nhất và số lần."
            ),
            goal="Nói loại quái đông nhất. Mật mã = số con của loại đó. Rồi tới cúp.",
            rows=[
                "############",
                "#r.b.r.c.r.#",
                "#@......D.E#",
                "############",
            ],
            starter=(
                "from collections import Counter\n"
                'print(Counter(["a", "b", "a"]))\n'
                "hero.move_right(6)\n"
            ),
            hints=[
                "Đưa vào Counter danh sách các loại quái (khoá \"type\").",
                "most_common(1) trả về list có 1 tuple (loại, số lượng).",
            ],
            requires=["call:Counter"],
            door_code=3,
            say_contains="robot",
        ),
        Level(
            id="14-2",
            title="Hàng lính gác",
            story=(
                "guards = [\"An\", \"Bình\", \"Chi\", \"Dũng\"] xếp hàng. Mỗi lượt, người đứng đầu "
                "ra đứng cuối hàng. Sau 3 lượt, tên người đứng đầu là mật mã. "
                "deque là hàng đợi: popleft() lấy người đầu, append() thêm vào cuối."
            ),
            goal="Dùng deque mô phỏng 3 lượt, nhập tên người đứng đầu, tới cúp.",
            rows=MAP_DOOR,
            starter=(
                "from collections import deque\n"
                "line = deque(guards)\n"
                "print(line)\n"
            ),
            hints=[
                "Mỗi lượt: lấy người đầu ra rồi đưa vào cuối.",
                "Mật mã là chuỗi (tên), không phải số.",
            ],
            requires=["call:deque"],
            extra_globals={"guards": ["An", "Bình", "Chi", "Dũng"]},
            door_code="Dũng",
        ),
    ]),
    WorldInfo(15, 2, "Lịch", "Ngày và giờ", "Ngày giờ", 3, [
        Level(
            id="15-1",
            title="Đếm ngày tới hội trại",
            story=(
                "Học kỳ 2 bắt đầu start = \"2026-01-01\", hội trại vào end = \"2026-03-15\". "
                "date.fromisoformat(...) đổi chuỗi thành ngày; lấy ngày trừ ngày ra khoảng cách, .days là số ngày."
            ),
            goal="Tính số ngày từ start tới end, nhập làm mật mã, tới cúp.",
            rows=MAP_DOOR_DOWN,
            starter=(
                "from datetime import date\n"
                "print(date.fromisoformat(start))\n"
                "hero.move_right(2)\n"
                "hero.move_down(1)\n"
            ),
            hints=["Đổi cả hai chuỗi sang date rồi trừ.", "Kết quả phép trừ có thuộc tính .days."],
            requires=["import:datetime"],
            extra_globals={"start": "2026-01-01", "end": "2026-03-15"},
            door_code=73,
        ),
    ]),
    # ================================================================ GIAI ĐOẠN 3
    WorldInfo(16, 3, "Bẫy", "Xử lý ngoại lệ", "Xử lý lỗi", 6, [
        Level(
            id="16-1",
            title="Cửa kẹt",
            story=(
                "hero.open_door(\"right\") có thể gây lỗi DoorJammed. "
                "Dùng try/except để bắt lỗi và thử lại thay vì để chương trình dừng."
            ),
            goal="Mở được cửa kẹt và tới cúp.",
            rows=[
                "#########",
                "#@.GJ.GE#",
                "#########",
            ],
            starter=(
                "hero.move_right(2)\n"
                'hero.open_door("right")\n'
                "hero.move_right(4)\n"
            ),
            hints=[
                "Đặt lệnh mở cửa trong khối try, rồi bắt lỗi DoorJammed bằng khối except.",
                "Cửa có thể kẹt nhiều lần - hãy lặp tới khi mở được.",
            ],
            requires=["try"],
            jams=2,
        ),
        Level(
            id="16-2",
            title="Hai cánh cửa",
            story="Gom phần try/except vào một hàm để dùng lại cho nhiều cửa.",
            goal="Viết hàm force_open(direction) rồi mở cả hai cửa.",
            rows=[
                "##########",
                "#@.J..J.E#",
                "##########",
            ],
            starter=(
                "def force_open(direction):\n"
                "    pass  # thử mở tới khi được\n"
                "\n"
                "hero.move_right(1)\n"
            ),
            hints=[
                "Trong hàm, dùng while True và return khi mở được cửa.",
                "Sau khi viết hàm, gọi nó mỗi khi đứng trước một cửa kẹt.",
            ],
            requires=["try", "def"],
            jams=2,
        ),
        Level(
            id="16-3",
            title="Lọc mật mã giả",
            story=(
                "candidates = [\"7x\", \"??\", \"42\", \"abc\"] - chỉ một chuỗi là số thật. "
                "int(\"7x\") gây lỗi ValueError. Bắt lỗi đó để bỏ qua chuỗi giả."
            ),
            goal="Tìm chuỗi đổi được sang số, dùng nó làm mật mã, tới cúp.",
            rows=MAP_DOOR,
            starter=(
                "for text in candidates:\n"
                "    print(int(text))\n"
            ),
            hints=[
                "Bọc phép đổi int(...) trong try, bắt đúng loại lỗi ValueError.",
                "Đổi được thì giữ lại và thoát vòng lặp.",
            ],
            requires=["try", "except_value_error"],
            extra_globals={"candidates": ["7x", "??", "42", "abc"]},
            door_code=42,
        ),
    ]),
    WorldInfo(17, 3, "Xưởng class", "Class & magic methods", "Lập trình hướng đối tượng", 5, [
        Level(
            id="17-1",
            title="Bình thuốc hồi máu",
            story=(
                "Hero chỉ còn 1 máu! class là khuôn để tạo đồ vật. Tạo class Potion có thuộc tính power. "
                "hero.use(vật) hồi số máu bằng vật.power."
            ),
            goal="Tạo bình thuốc hồi 2 máu, dùng nó cho đầy 3 máu rồi tới cúp.",
            rows=[
                "#########",
                "#@..G..E#",
                "#########",
            ],
            starter=(
                "class Potion:\n"
                "    pass\n"
                "\n"
                "hero.move_right(6)\n"
            ),
            hints=[
                "__init__ chạy khi tạo đồ vật; lưu dữ liệu vào self.",
                "Tạo đồ vật bằng cách gọi tên class như gọi hàm, truyền sức mạnh vào.",
            ],
            requires=["class", "dunder:__init__"],
            start_hp=1,
            need_full_hp=True,
        ),
        Level(
            id="17-2",
            title="Cộng véc-tơ",
            story=(
                "Ba mảnh bản đồ ghi 3 bước dịch chuyển (x, y): (1, 0), (3, 0), (0, 3). "
                "Magic method __add__ cho phép dùng dấu + với đồ vật của bạn, __str__ quy định cách in ra. "
                "hero.move_by(v) đi v.x ô ngang rồi v.y ô dọc."
            ),
            goal="Viết __add__ và __str__, cộng 3 véc-tơ, nói kết quả \"(4, 3)\", rồi move_by tới cúp.",
            rows=[
                "#######",
                "#@...G#",
                "#####.#",
                "#####.#",
                "#####E#",
                "#######",
            ],
            starter=(
                "class Vector:\n"
                "    def __init__(self, x, y):\n"
                "        self.x = x\n"
                "        self.y = y\n"
                "\n"
                "a = Vector(1, 0)\n"
                "print(a.x, a.y)\n"
            ),
            hints=[
                "__add__(self, other) phải return một Vector MỚI.",
                "__str__ phải return một chuỗi dạng \"(x, y)\".",
            ],
            requires=["dunder:__add__", "dunder:__str__"],
            say_contains="(4, 3)",
        ),
        Level(
            id="17-3",
            title="Lộ trình tuần tra",
            story=(
                "hero.follow(lộ_trình) đi theo từng hướng trong lộ trình. "
                "Viết class Patrol có __iter__ để vòng for (và follow) duyệt được nó. "
                "Mỗi vòng tuần tra là: \"right\" rồi \"down\"."
            ),
            goal="Tạo Patrol(4) gồm 4 vòng tuần tra, cho hero follow để xuống hết cầu thang.",
            rows=MAP_STAIRS,
            starter=(
                "class Patrol:\n"
                "    def __init__(self, rounds):\n"
                "        self.rounds = rounds\n"
                "\n"
                'hero.follow(["right", "down"])  # follow nhận thứ duyệt được\n'
            ),
            hints=[
                "__iter__ cần return một iterator - iter(một_list) là đủ.",
                "Nhân list với số để lặp lại nó nhiều lần.",
            ],
            requires=["dunder:__iter__", "call:follow"],
        ),
    ]),
    WorldInfo(18, 3, "Trùm giữa", "Tổng hợp giai đoạn 1-3", "Ôn tập Python cơ bản", 4, [
        Level(
            id="18-1",
            title="Đại chiến Vịt Vương",
            story=(
                "Dùng mọi thứ đã học! Quái: robot → hammer, barrel → axe. "
                "Mật mã = int(secret) * 2 với secret = \"21\". Cửa thứ hai bị kẹt. "
                "Vịt Vương có 3 máu và chỉ sợ \"sword\"."
            ),
            goal="Hạ quái, mở 2 cửa, đánh bại Vịt Vương, nhặt ngọc và tới cúp.",
            rows=[
                "###############",
                "#@.rGb.D.JGB.E#",
                "###############",
            ],
            starter=(
                'weakness = {"robot": "hammer", "barrel": "axe", "duck": "sword"}\n'
                "\n"
                "# Giai đoạn 1: hạ 2 quái đầu tiên\n"
                "for enemy in hero.find_enemies()[:2]:\n"
                "    pass\n"
            ),
            hints=[
                "Giai đoạn 1: hạ 2 quái bằng vũ khí tra trong dict.",
                "Giai đoạn 2-3: đứng cạnh từng cửa; cửa mật mã cần ép kiểu, cửa kẹt cần try/except.",
                "Giai đoạn 4: boss có 3 máu - dùng vòng lặp để đánh.",
            ],
            requires=["dict", "for", "try", "call:int"],
            extra_globals={"secret": "21"},
            door_code=42,
            jams=2,
            weapons=True,
            kill_all=True,
        ),
    ]),
    # ================================================================ GIAI ĐOẠN 4
    WorldInfo(19, 4, "Băng chuyền", "map, filter, zip, lambda", "Lập trình hàm", 1, [
        Level(
            id="19-1",
            title="Máy lọc số",
            story=(
                "raw = [\"3\", \"x\", \"5\", \"?\", \"7\"] lẫn cả chữ. filter giữ lại phần tử thoả điều kiện, "
                "map áp một hàm lên mọi phần tử. lambda viết hàm ngắn trong 1 dòng."
            ),
            goal="Lọc chuỗi là số, đổi sang int bằng map, mật mã = tổng. Tới cúp.",
            rows=MAP_DOOR_DOWN,
            starter=(
                "double = lambda n: n * 2\n"
                "print(double(5))\n"
                "print(list(map(double, [1, 2, 3])))\n"
            ),
            hints=[
                "Chuỗi có hàm .isdigit() trả về True nếu toàn chữ số.",
                "filter trước, map sau, cuối cùng cộng lại.",
            ],
            requires=["call:map", "call:filter", "lambda"],
            extra_globals={"raw": ["3", "x", "5", "?", "7"]},
            door_code=15,
        ),
        Level(
            id="19-2",
            title="Phát vũ khí",
            story=(
                "weapons = [\"hammer\", \"axe\", \"bow\"] đã xếp đúng thứ tự quái từ trái sang phải. "
                "zip(a, b) ghép từng cặp: phần tử 1 của a với phần tử 1 của b..."
            ),
            goal="Dùng zip ghép quái với vũ khí, hạ hết quái, tới cổng.",
            rows=[
                "###########",
                "#@.r.b.c..#",
                "#.........#",
                "#........E#",
                "###########",
            ],
            starter=(
                'for number, letter in zip([1, 2, 3], ["a", "b", "c"]):\n'
                "    print(number, letter)\n"
            ),
            hints=[
                "find_enemies() đã xếp quái từ trái sang phải.",
                "Mỗi vòng zip cho một cặp (quái, vũ khí).",
            ],
            requires=["call:zip"],
            extra_globals={"weapons": ["hammer", "axe", "bow"]},
            weapons=True,
            kill_all=True,
        ),
    ]),
    WorldInfo(20, 4, "Mật thư", "Regex & XML", "Đọc và phân tích văn bản", 2, [
        Level(
            id="20-1",
            title="Bức thư bí ẩn",
            story=(
                "letter = \"Kho báu ở phòng 12. Mật mã là 4207, đừng nhầm với 99!\" "
                "Biểu thức chính quy (regex) tìm mẫu trong chữ: \\d+ là \"một hay nhiều chữ số\"."
            ),
            goal="Dùng re.search tìm số đứng sau \"Mật mã là\", mở cửa, tới cúp.",
            rows=MAP_DOOR,
            starter=(
                "import re\n"
                'print(re.findall(r"\\d+", letter))\n'
                "hero.move_right(2)\n"
            ),
            hints=[
                "Đặt phần cần lấy trong ngoặc tròn ( ) để tạo nhóm.",
                ".group(1) lấy nội dung nhóm thứ nhất - nhớ đổi sang int.",
            ],
            requires=["import:re"],
            extra_globals={"letter": "Kho báu ở phòng 12. Mật mã là 4207, đừng nhầm với 99!"},
            door_code=4207,
        ),
        Level(
            id="20-2",
            title="Bản đồ XML",
            story=(
                "Bản đồ kho báu viết bằng XML trong biến map_xml. Mỗi thẻ <gem x=\"..\" y=\"..\"/> là một viên ngọc, "
                "thẻ <exit .../> là cổng. Dùng xml.etree.ElementTree để đọc."
            ),
            goal="Đọc XML, đi nhặt từng viên ngọc theo toạ độ trong thẻ, rồi tới cổng.",
            rows=[
                "###########",
                "#@...#..G.#",
                "#.##...#..#",
                "#..G.....E#",
                "###########",
            ],
            starter=(
                "import xml.etree.ElementTree as ET\n"
                "root = ET.fromstring(map_xml)\n"
                "print(root.tag)\n"
            ),
            hints=[
                "root.findall(\"gem\") trả về list các thẻ gem.",
                "thẻ.get(\"x\") trả về CHUỖI - nhớ đổi sang int.",
            ],
            requires=["import:xml", "call:fromstring"],
            extra_globals={
                "map_xml": '<map><gem x="3" y="3"/><gem x="8" y="1"/><exit x="9" y="3"/></map>',
            },
        ),
    ]),
    WorldInfo(21, 4, "Bùa chú", "Closure & decorator", "Closure và decorator", 3, [
        Level(
            id="21-1",
            title="Xưởng làm bùa",
            story=(
                "Closure: hàm bên ngoài tạo và trả về một hàm bên trong; hàm bên trong NHỚ biến của hàm ngoài. "
                "Viết make_mover(direction) trả về một hàm mover(steps) đi theo hướng đó."
            ),
            goal="Tạo go_right và go_down bằng make_mover, dùng chúng đi tới cúp.",
            rows=[
                "#########",
                "#@..G####",
                "####.####",
                "####..GE#",
                "#########",
            ],
            starter=(
                "def make_mover(direction):\n"
                "    pass\n"
                "\n"
                'hero.follow(["right"] * 3)  # đi phải 3 ô\n'
            ),
            hints=[
                "Định nghĩa hàm mover BÊN TRONG make_mover, rồi return mover (không có ngoặc).",
                "Đường đi: phải 3, xuống 2, phải 3.",
            ],
            requires=["closure"],
        ),
        Level(
            id="21-2",
            title="Bùa nhân đôi",
            story=(
                "Decorator là hàm \"bọc\" một hàm khác để thêm sức mạnh. Viết @twice ở trên một hàm "
                "thì mỗi lần gọi, hàm đó chạy 2 lần."
            ),
            goal="Viết decorator twice, gắn vào hàm stair (1 bậc thang), xuống hết 4 bậc chỉ với 2 lần gọi.",
            rows=MAP_STAIRS,
            starter=(
                "def twice(action):\n"
                "    pass\n"
                "\n"
                "def stair():\n"
                "    hero.move_right()\n"
                "    hero.move_down()\n"
                "\n"
                "stair()\n"
            ),
            hints=[
                "twice nhận vào một hàm, tạo bên trong một hàm mới gọi hàm đó 2 lần, rồi trả hàm mới ra ngoài.",
                "Viết @twice ngay dòng phía trên def stair().",
            ],
            requires=["decorator"],
        ),
    ]),
    # ================================================================ GIAI ĐOẠN 5
    WorldInfo(22, 5, "Ma trận", "NumPy cơ bản", "Tính toán với NumPy", 4, [
        Level(
            id="22-1",
            title="Bảng điểm",
            story=(
                "NumPy làm việc với bảng số rất nhanh. scores là bảng điểm 2 hàng × 3 cột. "
                "np.array(scores) tạo mảng; .sum() cộng mọi phần tử, .shape cho biết số hàng, số cột."
            ),
            goal="Tính tổng mọi điểm trong bảng bằng NumPy, nhập làm mật mã, tới cúp.",
            rows=MAP_DOOR,
            starter=(
                "import numpy as np\n"
                "board = np.array(scores)\n"
                "print(board.shape)\n"
            ),
            hints=["Mảng NumPy có sẵn hàm .sum().", "Đổi kết quả sang int trước khi nhập mật mã."],
            requires=["import:numpy"],
            extra_globals={"scores": [[1, 2, 3], [4, 5, 6]]},
            door_code=21,
        ),
        Level(
            id="22-2",
            title="Nhân ma trận",
            story=(
                "Phép nhân ma trận A @ B: phần tử hàng i, cột j = tổng (hàng i của A) × (cột j của B). "
                "A = [[1, 2], [3, 4]], B = [[2, 0], [1, 2]]. Mật mã = tổng mọi phần tử của A @ B."
            ),
            goal="Nhân hai ma trận bằng NumPy, cộng tất cả phần tử, mở cửa, tới cúp.",
            rows=MAP_DOOR_DOWN,
            starter=(
                "import numpy as np\n"
                "A = np.array(matrix_a)\n"
                "print(A * 2)  # nhân mỗi phần tử với 2\n"
            ),
            hints=[
                "A * B là nhân TỪNG phần tử - khác với nhân ma trận.",
                "Nhân ma trận dùng toán tử @ (hoặc np.dot).",
            ],
            requires=["op:@ or call:dot or call:matmul"],
            extra_globals={"matrix_a": [[1, 2], [3, 4]], "matrix_b": [[2, 0], [1, 2]]},
            door_code=26,
        ),
    ]),
    WorldInfo(23, 5, "Thợ sửa lỗi", "Debugging", "Gỡ lỗi", 5, [
        Level(
            id="23-1",
            title="Ba con bọ cú pháp",
            story=(
                "Code bên phải có 4 lỗi! Đọc kỹ thông báo lỗi ở Bảng tin: nó cho biết DÒNG nào sai. "
                "Sửa từng lỗi, chạy lại, cho tới khi hero nhặt hết ngọc."
            ),
            goal="Sửa hết lỗi để hero nhặt 8 ngọc, tới cúp và nói \"Xong!\".",
            rows=[
                "############",
                "#@GGGGGGGGE#",
                "############",
            ],
            starter=(
                "for i in range(8)\n"
                "hero.move_right()\n"
                'hero.say("Xong!)\n'
            ),
            hints=[
                "Lỗi cú pháp: dòng for thiếu gì ở cuối? Chuỗi có đóng nháy chưa?",
                "Hết lỗi cú pháp rồi mà vẫn thiếu ngọc? Đếm lại số bước.",
            ],
            requires=["for"],
            say_contains="Xong!",
        ),
        Level(
            id="23-2",
            title="Bọ logic",
            story=(
                "Code này chạy không báo lỗi cú pháp nhưng sai logic. Có 3 con bọ: một khoá dict viết sai, "
                "một dòng thụt lề sai chỗ, một chỗ đảo ngược toạ độ. Dùng print() để kiểm tra giá trị."
            ),
            goal="Sửa code để hạ hết quái bằng đúng vũ khí rồi tới cổng.",
            rows=MAP_WEAPON_ROOM,
            starter=(
                'weakness = {"Robot": "hammer", "barrel": "axe", "cannon": "bow"}\n'
                "for enemy in hero.find_enemies():\n"
                '    weapon = weakness[enemy["type"]]\n'
                'hero.attack_target(enemy["x"], enemy["y"], weapon)\n'
                "exit_x, exit_y = hero.exit_position\n"
                "hero.move_to(exit_y, exit_x)\n"
            ),
            hints=[
                "KeyError nghĩa là khoá không có trong dict - Python phân biệt chữ hoa, chữ thường.",
                "Lệnh tấn công phải nằm TRONG vòng lặp; move_to nhận (x, y) theo đúng thứ tự.",
            ],
            requires=["dict", "for"],
            weapons=True,
            kill_all=True,
        ),
    ]),
]

# Bài luyện tập thêm (levels_practice.py) được nối vào cuối mỗi WorldInfo;
# mã bài cũ giữ nguyên nên tiến độ cũ của học sinh không bị ảnh hưởng.
for _world in WORLDS:
    _world.levels.extend(PRACTICE.get(_world.number, []))


def all_levels() -> list[Level]:
    return [level for world in WORLDS for level in world.levels]


def world_of(level_id: str) -> WorldInfo:
    return next(world for world in WORLDS if any(lv.id == level_id for lv in world.levels))


def stage_of(level_id: str) -> Stage:
    return STAGES[world_of(level_id).stage - 1]


# ======================================================================
# theory.py
# ======================================================================

@dataclass
class Theory:
    concept: list[str]
    starter_notes: list[tuple[str, str]]
    example: list[tuple[str, str]]
    mistakes: list[str] = field(default_factory=list)


THEORY: dict[str, Theory] = {
    "1-1": Theory(
        concept=[
            "Chương trình là danh sách lệnh. Python đọc và chạy từng lệnh, từ trên xuống dưới.",
            "Trong game, `hero` là nhân vật của bạn. Dấu chấm `.` nghĩa là \"của\": `hero.move_right` là lệnh move_right CỦA hero.",
            "Cặp ngoặc `( )` là GỌI lệnh. Số trong ngoặc là THAM SỐ - thông tin thêm cho lệnh, ở đây là số bước đi.",
            "Dòng bắt đầu bằng `#` là GHI CHÚ: Python bỏ qua, dùng để người đọc hiểu code.",
        ],
        starter_notes=[
            ("# Dòng bắt đầu bằng # là ghi chú, Python bỏ qua.", "Ghi chú - không chạy."),
            ("# Số trong ngoặc là số bước đi.", "Ghi chú - không chạy."),
            ("hero.move_right(2)", "Gọi lệnh move_right của hero với tham số 2: đi sang phải 2 ô."),
        ],
        example=[
            ("hero.move_right(3)", "Đi sang phải 3 ô."),
            ("hero.move_left(1)", "Quay lại trái 1 ô."),
            ("hero.move_right()", "Không ghi số thì mặc định đi 1 ô."),
        ],
        mistakes=[
            "Viết sai chính tả: `hero.move_rigth` → Python báo không có lệnh này.",
            "Quên ngoặc: `hero.move_right` (không có `()`) thì lệnh KHÔNG chạy.",
            "Viết hoa sai: Python phân biệt hoa thường, `Hero` khác `hero`.",
        ],
    ),
    "1-2": Theory(
        concept=[
            "Mỗi dòng một lệnh. Python chạy dòng 1, xong mới tới dòng 2, rồi dòng 3...",
            "Hero có 4 lệnh đi: `move_up` (lên), `move_down` (xuống), `move_left` (trái), `move_right` (phải).",
            "Trục toạ độ: x tăng khi sang phải, y tăng khi đi XUỐNG.",
            "Nếu hero đụng tường, hero đứng yên và các bước còn lại của lệnh đó bị bỏ qua.",
        ],
        starter_notes=[
            ("hero.move_right(2)", "Đi phải 2 ô - tới chỗ rẽ."),
            ("# Thêm lệnh move_down và move_right", "Ghi chú nhắc bạn viết tiếp các lệnh bên dưới."),
        ],
        example=[
            ("hero.move_down(2)", "Xuống 2 ô."),
            ("hero.move_left(1)", "Sang trái 1 ô."),
            ("hero.move_up(2)", "Lên 2 ô. Ba lệnh chạy lần lượt theo thứ tự."),
        ],
        mistakes=[
            "Thụt đầu dòng khi không cần: lệnh thường phải sát lề trái, nếu không sẽ lỗi thụt lề.",
            "Nhầm hướng: y tăng là đi xuống, không phải đi lên.",
        ],
    ),
    "1-3": Theory(
        concept=[
            "Chuỗi (string, `str`) là đoạn chữ, luôn nằm trong dấu nháy: `\"Xin chào\"` hoặc `'Xin chào'`.",
            "`hero.say(...)` cho hero nói một câu. `print(...)` in thông tin ra Bảng tin.",
            "Bộ gõ tiếng Việt Telex có sẵn trong game: chỉ hoạt động bên trong dấu nháy và ghi chú. Ví dụ gõ `chaof` → `chào`.",
        ],
        starter_notes=[
            ('hero.say("...")', "Hero nói chuỗi \"...\". Bạn thay bằng câu cần nói."),
            ("hero.move_right(1)", "Đi phải 1 ô - cần đổi số bước cho tới cúp."),
        ],
        example=[
            ('hero.say("Tạm biệt")', "Hero nói \"Tạm biệt\" - có dấu nháy hai đầu."),
            ('print("Đang đi...")', "In ra Bảng tin, hero không nói."),
            ("hero.say(123)", "say cũng nhận số."),
        ],
        mistakes=[
            "Quên dấu nháy: `hero.say(Xin chào)` → Python tưởng `Xin` là tên biến.",
            "Mở nháy kép đóng nháy đơn: `\"abc'` → lỗi cú pháp.",
        ],
    ),
    "2-1": Theory(
        concept=[
            "BIẾN là cái hộp có tên để cất giá trị. Phép gán dùng dấu `=`: `ten_bien = gia_tri`.",
            "Dấu `=` trong Python nghĩa là \"cất vào\", KHÔNG phải \"bằng nhau\" như trong toán.",
            "Sau khi gán, ở đâu dùng tên biến thì Python thay bằng giá trị trong hộp.",
            "Tên biến: chữ, số, dấu gạch dưới; không bắt đầu bằng số; không có dấu cách.",
        ],
        starter_notes=[
            ("steps = 1  # đổi số này", "Tạo biến steps, cất số 1. Phần sau # là ghi chú."),
            ("hero.move_right(steps)", "Python thay steps bằng giá trị trong hộp, rồi đi số bước đó."),
        ],
        example=[
            ("distance = 4", "Tạo biến distance chứa 4."),
            ("hero.move_down(distance)", "Đi xuống 4 ô."),
            ("distance = 2", "Gán lại: hộp giờ chứa 2 (giá trị cũ mất)."),
            ("hero.move_up(distance)", "Đi lên 2 ô."),
        ],
        mistakes=[
            "Dùng biến trước khi gán → NameError.",
            "Tên biến có dấu cách: `so buoc = 3` → lỗi cú pháp. Dùng `so_buoc`.",
        ],
    ),
    "2-2": Theory(
        concept=[
            "Các kiểu dữ liệu cơ bản: `int` (số nguyên: 3, -7), `float` (số thực: 2.5), `str` (chuỗi: \"abc\"), `bool` (True / False).",
            "Phép toán: `+` cộng, `-` trừ, `*` nhân, `/` chia (ra float), `//` chia lấy nguyên, `%` chia lấy dư.",
            "Có thể dùng biến để tính ra biến mới: `c = a + b`.",
            "Muốn nối chuỗi với số phải đổi số sang chuỗi: `\"Có \" + str(5)`. Hoặc dùng f-string: `f\"Có {so}\"`.",
        ],
        starter_notes=[
            ("gems = 3", "Biến gems (int) = 3 viên ngọc."),
            ("value = 10", "Biến value (int) = giá mỗi viên."),
            ("total = 0  # tính lại total", "total đang là 0 - bạn cần tính bằng gems và value."),
            ("hero.move_right(8)", "Đi phải 8 ô để nhặt ngọc và tới cúp."),
        ],
        example=[
            ("apples = 4", "Có 4 quả táo."),
            ("price = 5", "Mỗi quả 5 xu."),
            ("cost = apples * price", "cost = 4 * 5 = 20."),
            ('hero.say("Hết " + str(cost) + " xu")', "str(cost) đổi 20 thành \"20\" để nối chuỗi."),
            ('hero.say(f"Hết {cost} xu")', "Cách khác: f-string, viết biến trong { }."),
        ],
        mistakes=[
            "`\"Tổng: \" + total` khi total là int → TypeError. Cần `str(total)`.",
            "Viết `x` thay cho dấu nhân: Python dùng `*`.",
        ],
    ),
    "3-1": Theory(
        concept=[
            "Câu lệnh `if` cho chương trình RA QUYẾT ĐỊNH: chỉ chạy một khối lệnh khi điều kiện đúng.",
            "Cấu trúc: `if điều_kiện:` - có dấu hai chấm ở cuối, các lệnh bên trong THỤT VÀO 4 khoảng trắng.",
            "So sánh: `==` bằng, `!=` khác, `<` `>` `<=` `>=`. Chú ý `==` (so sánh) khác `=` (gán).",
            "`hero.look(\"right\")` trả về chuỗi mô tả ô bên phải: \"enemy\", \"wall\", \"spike\", \"gem\", \"door\", \"exit\", \"floor\".",
            "`hero.attack(\"right\")` đánh ô bên phải.",
        ],
        starter_notes=[
            ("hero.move_right(2)", "Đi tới gần quái."),
            ('if hero.look("right") == "enemy":', "Nếu ô bên phải là quái thì chạy khối thụt lề bên dưới."),
            ("    # thụt vào 4 khoảng trắng", "Ghi chú: lệnh trong if phải thụt vào."),
            ("    pass", "pass = \"không làm gì\". Hãy thay bằng lệnh tấn công."),
        ],
        example=[
            ('if hero.look("down") == "gem":', "Nếu bên dưới có ngọc..."),
            ("    hero.move_down()", "...thì đi xuống nhặt (thụt 4 khoảng)."),
            ('hero.say("Xong")', "Không thụt lề: chạy dù điều kiện đúng hay sai."),
        ],
        mistakes=[
            "Quên dấu `:` cuối dòng if → lỗi cú pháp.",
            "Dùng `=` thay vì `==` trong điều kiện → lỗi cú pháp.",
            "Quên thụt lề khối bên trong → IndentationError.",
        ],
    ),
    "3-2": Theory(
        concept=[
            "`else:` là nhánh \"ngược lại\" - chạy khi điều kiện của if SAI.",
            "Có thể nối nhiều điều kiện bằng `elif` (else if): chỉ nhánh đầu tiên đúng được chạy.",
            "Ghép điều kiện: `and` (cả hai đúng), `or` (một trong hai đúng), `not` (phủ định).",
        ],
        starter_notes=[
            ("hero.move_right(2)", "Đi tới ngã ba."),
            ('if hero.look("up") == "spike":', "Nếu phía trên có gai..."),
            ("    pass  # đi lối khác", "...thì đi lối khác (bạn viết lệnh ở đây)."),
            ("else:", "Ngược lại (phía trên không có gai)..."),
            ("    hero.move_up()", "...thì đi lên."),
        ],
        example=[
            ('tile = hero.look("left")', "Lưu kết quả look vào biến."),
            ('if tile == "wall":', "Nếu bên trái là tường"),
            ('    hero.say("Bị chặn")', "→ nói bị chặn."),
            ('elif tile == "gem":', "Nếu không, mà là ngọc"),
            ("    hero.move_left()", "→ đi nhặt."),
            ("else:", "Mọi trường hợp còn lại"),
            ('    hero.say("Không có gì")', "→ nói không có gì."),
        ],
        mistakes=[
            "`else` cũng cần dấu `:` và phải thẳng hàng với `if`.",
            "Viết `else if` → Python dùng `elif`.",
        ],
    ),
    "4-1": Theory(
        concept=[
            "Vòng lặp `for` lặp lại một khối lệnh nhiều lần mà không phải viết đi viết lại.",
            "`range(n)` sinh dãy số 0, 1, 2, ..., n-1 (tổng cộng n số). Vậy `for i in range(5):` lặp 5 lần.",
            "Biến `i` nhận lần lượt từng số trong dãy - có thể dùng hoặc bỏ qua.",
            "Khối lệnh lặp phải thụt vào 4 khoảng trắng, giống if.",
        ],
        starter_notes=[
            ("for i in range(1):", "Lặp 1 lần (i = 0). Hãy đổi số lần lặp."),
            ("    hero.move_right()", "Mỗi lần lặp: đi phải 1 ô."),
        ],
        example=[
            ("for i in range(3):", "Lặp 3 lần, i = 0, 1, 2."),
            ("    print(i)", "In ra 0, 1, 2."),
            ("    hero.move_down()", "Mỗi lần đi xuống 1 ô → tổng 3 ô."),
        ],
        mistakes=[
            "Quên `:` cuối dòng for.",
            "`range(3)` không gồm số 3: dãy là 0, 1, 2.",
        ],
    ),
    "4-2": Theory(
        concept=[
            "Khối lệnh trong vòng lặp có thể gồm nhiều dòng - tất cả thụt lề cùng mức.",
            "Mỗi lần lặp, Python chạy HẾT khối lệnh từ trên xuống rồi mới bắt đầu lần lặp tiếp theo.",
            "Tìm \"mẫu lặp lại\" trong bài toán, viết mẫu đó một lần trong vòng lặp.",
        ],
        starter_notes=[
            ("for i in range(4):", "Lặp 4 lần - mỗi lần là một bậc thang."),
            ("    hero.move_right()", "Đi phải 1 ô. Mỗi bậc còn thiếu một bước nữa."),
        ],
        example=[
            ("for i in range(2):", "Lặp 2 lần mẫu \"lên rồi trái\"."),
            ("    hero.move_up()", "Bước 1 của mẫu."),
            ("    hero.move_left()", "Bước 2 của mẫu (cùng mức thụt lề → vẫn trong vòng lặp)."),
            ('hero.say("Hết thang")', "Không thụt lề → chạy 1 lần sau khi lặp xong."),
        ],
        mistakes=["Lệnh thụt lề khác nhau trong cùng khối → IndentationError."],
    ),
    "4-3": Theory(
        concept=[
            "Vòng lặp `while điều_kiện:` lặp CHỪNG NÀO điều kiện còn đúng - dùng khi chưa biết trước số lần lặp.",
            "Mỗi vòng, Python kiểm tra điều kiện trước; nếu sai thì thoát vòng lặp.",
            "Cẩn thận lặp vô hạn: phải có gì đó thay đổi để điều kiện có lúc sai. Game sẽ dừng chương trình chạy quá lâu.",
            "`break` thoát vòng lặp ngay lập tức.",
        ],
        starter_notes=[
            ('while hero.look("right") != "exit":', "Chừng nào bên phải CHƯA phải cổng thì còn lặp."),
            ("    pass", "Chưa làm gì → hero đứng yên mãi → lặp vô hạn! Hãy cho hero đi."),
        ],
        example=[
            ('while hero.look("down") != "wall":', "Chừng nào bên dưới chưa phải tường..."),
            ("    hero.move_down()", "...cứ đi xuống."),
            ('hero.say("Chạm đáy")', "Thoát vòng lặp khi gặp tường."),
        ],
        mistakes=[
            "Điều kiện không bao giờ sai → lặp vô hạn.",
            "Quên bước cuối sau vòng lặp (vòng lặp dừng TRƯỚC khi vào cổng).",
        ],
    ),
    "5-1": Theory(
        concept=[
            "Ép kiểu (type casting) là đổi giá trị từ kiểu này sang kiểu khác.",
            "`int(\"42\")` → 42 (chuỗi thành số nguyên). `str(42)` → \"42\". `float(\"2.5\")` → 2.5. `bool(0)` → False.",
            "\"42\" (chuỗi) và 42 (số) là KHÁC nhau: chuỗi không tính toán được như số.",
            "`hero.enter_code(...)` nhập mật mã cho cửa bên cạnh, chỉ nhận số nguyên (int).",
        ],
        starter_notes=[
            ('# secret đã có sẵn: secret = "42"', "Màn này có sẵn biến secret là chuỗi \"42\"."),
            ("hero.move_right(2)", "Đi tới đứng cạnh cửa."),
            ("hero.enter_code(secret)", "Đưa chuỗi vào → báo lỗi sai kiểu. Cần đổi sang int."),
        ],
        example=[
            ('text = "7"', "text là chuỗi \"7\"."),
            ("number = int(text)", "number là số 7."),
            ("print(number + 1)", "In 8 - tính toán được vì là số."),
            ('print(text + "1")', "\"71\" - chuỗi thì chỉ nối được, không cộng như số."),
        ],
        mistakes=[
            "`int(\"abc\")` → ValueError vì \"abc\" không phải số.",
            "`int(\"4.5\")` → ValueError; phải `int(float(\"4.5\"))`.",
        ],
    ),
    "5-2": Theory(
        concept=[
            "Dấu `+` làm việc KHÁC NHAU tuỳ kiểu: với số là cộng (12 + 30 = 42), với chuỗi là nối (\"12\" + \"30\" = \"1230\").",
            "Vì vậy phải ép kiểu TRƯỚC khi tính: `int(a) + int(b)`.",
            "`print()` giúp kiểm tra giá trị đang có - thói quen tốt khi gỡ lỗi.",
        ],
        starter_notes=[
            ('# a = "12", b = "30"', "Hai biến có sẵn, đều là chuỗi."),
            ("print(a + b)  # thử xem: chuỗi cộng chuỗi ra gì?", "In ra \"1230\" - nối chuỗi chứ không cộng số."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1 - đứng ngay trên cửa."),
        ],
        example=[
            ('x = "5"', "Chuỗi \"5\"."),
            ('y = "3"', "Chuỗi \"3\"."),
            ("print(x + y)", "\"53\" - nối chuỗi."),
            ("print(int(x) + int(y))", "8 - cộng số."),
            ("print(int(x) * int(y))", "15 - nhân số."),
        ],
        mistakes=["`int(a + b)` = int(\"1230\") = 1230, không phải tổng!"],
    ),
    "16-1": Theory(
        concept=[
            "Ngoại lệ (exception) là lỗi xảy ra khi chương trình đang chạy. Nếu không xử lý, chương trình DỪNG.",
            "`try:` bọc đoạn code có thể lỗi. `except TenLoi:` chạy khi lỗi đó xảy ra, rồi chương trình chạy tiếp.",
            "Trong game, `hero.open_door(...)` có thể ném lỗi `DoorJammed` (cửa kẹt). Thử lại vài lần sẽ mở được.",
            "Kết hợp với vòng lặp để thử lại cho tới khi thành công.",
        ],
        starter_notes=[
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
            ('hero.open_door("right")', "Mở cửa bên phải - lần đầu sẽ ném DoorJammed và chương trình dừng!"),
            ("hero.move_right(4)", "Dòng này không bao giờ chạy tới nếu lỗi chưa được xử lý."),
        ],
        example=[
            ("try:", "Thử chạy khối bên dưới."),
            ('    number = int("abc")', "Lỗi ValueError xảy ra ở đây."),
            ("except ValueError:", "Bắt đúng loại lỗi đó."),
            ('    print("Không phải số!")', "In thông báo thay vì dừng chương trình."),
            ('print("Vẫn chạy tiếp")', "Chương trình tiếp tục bình thường."),
        ],
        mistakes=[
            "`except` phải thẳng hàng với `try`.",
            "Bắt sai tên lỗi → lỗi vẫn làm chương trình dừng.",
        ],
    ),
    "16-2": Theory(
        concept=[
            "Khi một đoạn code dùng nhiều lần, hãy gói vào HÀM bằng `def` (đã học ở World 6).",
            "`return` trong hàm kết thúc hàm ngay lập tức - dùng để thoát khỏi `while True` khi đã thành công.",
            "`while True:` là vòng lặp \"mãi mãi\" - chỉ dừng khi gặp `break` hoặc `return`.",
        ],
        starter_notes=[
            ("def force_open(direction):", "Định nghĩa hàm force_open, nhận tham số direction (hướng)."),
            ("    pass  # thử mở tới khi được", "Thân hàm - bạn viết vòng lặp try/except ở đây."),
            ("hero.move_right(1)", "Đi tới cửa thứ nhất."),
        ],
        example=[
            ("def safe_number(text):", "Hàm đổi chuỗi sang số, an toàn."),
            ("    try:", "Thử..."),
            ("        return int(text)", "...đổi được thì trả về số và thoát hàm."),
            ("    except ValueError:", "Nếu lỗi..."),
            ("        return 0", "...trả về 0."),
            ('print(safe_number("9"), safe_number("x"))', "In: 9 0"),
        ],
        mistakes=["Quên gọi hàm: định nghĩa `def` xong phải gọi `force_open(\"right\")` thì mới chạy."],
    ),
    "6-1": Theory(
        concept=[
            "HÀM là một nhóm lệnh có tên. Định nghĩa: `def ten_ham():` rồi các lệnh thụt vào bên dưới.",
            "Định nghĩa hàm KHÔNG chạy gì cả. Hàm chỉ chạy khi được GỌI: `ten_ham()`.",
            "Lợi ích: viết một lần, dùng nhiều lần; code ngắn và dễ đọc hơn.",
        ],
        starter_notes=[
            ("def hop():", "Định nghĩa hàm hop - chiêu nhảy vòng qua gai."),
            ("    hero.move_up()", "Bước 1 của chiêu: đi lên."),
            ("    # thêm 2 lệnh nữa", "Bạn viết tiếp các bước của chiêu."),
            ("hero.move_right(2)", "Không thụt lề → ngoài hàm: đi tới trước gai đầu tiên."),
            ("hop()", "GỌI hàm hop: chạy toàn bộ các lệnh trong hàm."),
        ],
        example=[
            ("def dance():", "Hàm dance."),
            ("    hero.move_left()", "Trái..."),
            ("    hero.move_right()", "...rồi phải."),
            ("dance()", "Gọi lần 1."),
            ("dance()", "Gọi lần 2 - không phải viết lại."),
        ],
        mistakes=[
            "Gọi hàm trước khi định nghĩa → NameError.",
            "Quên `()` khi gọi: `hop` (không ngoặc) không chạy hàm.",
        ],
    ),
    "6-2": Theory(
        concept=[
            "Python có sẵn nhiều HÀM DỰNG SẴN (builtin): `len()` đếm phần tử, `sum()` tính tổng, `min()` / `max()` nhỏ / lớn nhất, `sorted()` sắp xếp, `abs()` trị tuyệt đối, `round()` làm tròn.",
            "Hàm có thể TRẢ VỀ giá trị: `n = len([5, 6, 7])` → n = 3.",
            "`hero.find_gems()` trả về một danh sách (list) các viên ngọc còn trên bản đồ.",
        ],
        starter_notes=[
            ("gems = hero.find_gems()", "Lấy danh sách ngọc, cất vào biến gems."),
            ("hero.say(gems)", "Hero đọc cả danh sách - dài quá! Bạn chỉ cần nói SỐ LƯỢNG."),
        ],
        example=[
            ("scores = [7, 3, 9]", "Một danh sách điểm."),
            ("print(len(scores))", "3 - có 3 phần tử."),
            ("print(sum(scores))", "19 - tổng."),
            ("print(max(scores), min(scores))", "9 3 - lớn nhất, nhỏ nhất."),
        ],
        mistakes=["`len` chỉ dùng cho tập hợp nhiều phần tử (list, str, dict...), `len(5)` → TypeError."],
    ),
    "6-3": Theory(
        concept=[
            "Hàm có THAM SỐ nhận dữ liệu vào: `def tang(n):` - n là tham số.",
            "`return giá_trị` gửi kết quả về nơi gọi hàm và kết thúc hàm.",
            "Kết quả hàm dùng được như một giá trị: `x = tang(5)` hoặc `print(tang(5))`.",
            "Hàm không có return sẽ trả về `None`.",
        ],
        starter_notes=[
            ("def double(n):", "Hàm double nhận tham số n."),
            ("    pass", "Chưa trả về gì → double(...) cho ra None. Bạn cần return kết quả."),
            ("hero.move_right(3)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("def square(n):", "Hàm bình phương."),
            ("    return n * n", "Trả về n nhân n."),
            ("result = square(4)", "result = 16."),
            ("print(result + square(2))", "16 + 4 = 20."),
        ],
        mistakes=[
            "Dùng `print` thay cho `return`: print chỉ hiện ra, KHÔNG trả giá trị về.",
            "Code sau `return` trong cùng khối không bao giờ chạy.",
        ],
    ),
    "8-1": Theory(
        concept=[
            "LIST (danh sách) chứa nhiều giá trị theo thứ tự: `items = [3, 5, 8]`. Lấy phần tử bằng chỉ số bắt đầu từ 0: `items[0]` = 3.",
            "Duyệt list: `for item in items:` - mỗi vòng, item là một phần tử.",
            "TUPLE giống list nhưng KHÔNG sửa được, viết bằng ngoặc tròn: `pos = (2, 5)`. Mở gói: `x, y = pos`.",
            "DICT (từ điển) lưu theo khoá: `gem[\"x\"]`. Mỗi viên ngọc từ find_gems() là một dict có \"x\", \"y\", \"color\".",
            "`hero.move_to(x, y)` tự tìm đường tới ô (x, y). `hero.exit_position` là tuple (x, y) của cổng.",
        ],
        starter_notes=[
            ("gems = hero.find_gems()", "gems là list các dict ngọc."),
            ("print(gems)", "In ra để xem cấu trúc dữ liệu - hãy chạy thử!"),
            ("exit_x, exit_y = hero.exit_position  # mở gói tuple", "Tách tuple (x, y) thành hai biến."),
        ],
        example=[
            ('points = [(1, 1), (3, 2)]', "List gồm 2 tuple toạ độ."),
            ("for point in points:", "Duyệt từng toạ độ."),
            ("    px, py = point", "Mở gói tuple."),
            ("    hero.move_to(px, py)", "Đi tới toạ độ đó."),
            ("print(points[0])", "(1, 1) - phần tử đầu tiên, chỉ số 0."),
        ],
        mistakes=[
            "Chỉ số bắt đầu từ 0, phần tử cuối là `len(list) - 1`.",
            "Sửa tuple: `pos[0] = 3` → TypeError.",
        ],
    ),
    "8-2": Theory(
        concept=[
            "Các thao tác list hay dùng: `append(x)` thêm vào cuối, `pop()` lấy ra phần tử cuối, `len()` đếm, cắt lát `items[1:3]`.",
            "`hero.find_enemies()` trả về list quái, mỗi quái là dict {\"x\", \"y\", \"type\"}.",
            "`hero.attack_target(x, y)` tự đi tới cạnh quái ở (x, y) và đánh.",
        ],
        starter_notes=[
            ("enemies = hero.find_enemies()", "Lấy list quái."),
            ('print(len(enemies), "quái")', "In số lượng quái trong phòng."),
        ],
        example=[
            ("bag = []", "List rỗng."),
            ('bag.append("kiếm")', "bag = [\"kiếm\"]."),
            ('bag.append("khiên")', "bag = [\"kiếm\", \"khiên\"]."),
            ("for item in bag:", "Duyệt từng món."),
            ("    hero.say(item)", "Hero nói tên món đồ."),
            ("print(bag[-1])", "\"khiên\" - chỉ số -1 là phần tử cuối."),
        ],
        mistakes=["Lấy phần tử ngoài phạm vi: `bag[5]` khi chỉ có 2 phần tử → IndexError."],
    ),
    "9-1": Theory(
        concept=[
            "DICT (từ điển) lưu cặp KHOÁ: GIÁ TRỊ trong ngoặc nhọn: `ages = {\"An\": 10, \"Bình\": 11}`.",
            "Tra giá trị theo khoá: `ages[\"An\"]` → 10. Thêm / sửa: `ages[\"Chi\"] = 9`.",
            "Kiểm tra có khoá: `\"An\" in ages` → True. Duyệt: `for name in ages:`.",
            "Màn này: mỗi loại quái sợ một vũ khí - dict là công cụ tra cứu hoàn hảo. `hero.attack_target(x, y, weapon)` nhận thêm vũ khí.",
        ],
        starter_notes=[
            ('weakness = {"robot": "hammer"}', "Dict mới có 1 cặp: robot sợ hammer. Còn thiếu barrel và cannon."),
            ("for enemy in hero.find_enemies():", "Duyệt từng quái."),
            ('    print(enemy["type"])', "In loại quái để biết cần tra khoá nào."),
        ],
        example=[
            ('colors = {"apple": "red", "leaf": "green"}', "Dict 2 cặp."),
            ('colors["sky"] = "blue"', "Thêm cặp mới."),
            ('print(colors["leaf"])', "green."),
            ("for thing in colors:", "Duyệt các khoá."),
            ("    print(thing, colors[thing])", "In khoá và giá trị."),
        ],
        mistakes=[
            "Tra khoá không có → KeyError. Kiểm tra chính tả khoá (\"robot\" khác \"Robot\").",
            "Các cặp phải cách nhau bằng dấu phẩy.",
        ],
    ),
    "9-2": Theory(
        concept=[
            "SET (tập hợp) chứa các giá trị KHÔNG TRÙNG NHAU, không có thứ tự: `s = {1, 2, 2, 3}` → {1, 2, 3}.",
            "Tạo set rỗng: `set()` (chú ý `{}` là dict rỗng!). Thêm: `s.add(x)` - nếu đã có thì bỏ qua.",
            "Dùng set để đếm số giá trị khác nhau: `len(set(danh_sach))`.",
        ],
        starter_notes=[
            ("colors = set()", "Tạo tập hợp rỗng để chứa các màu."),
            ("for gem in hero.find_gems():", "Duyệt từng viên ngọc."),
            ("    pass", "Bạn thêm màu của viên ngọc vào set ở đây."),
        ],
        example=[
            ("animals = set()", "Set rỗng."),
            ('animals.add("mèo")', "{\"mèo\"}."),
            ('animals.add("chó")', "{\"mèo\", \"chó\"}."),
            ('animals.add("mèo")', "Đã có → set không đổi."),
            ("print(len(animals))", "2."),
            ("print(len(set([1, 1, 2])))", "2 - đổi list sang set để loại trùng."),
        ],
        mistakes=["`{}` tạo dict rỗng, không phải set rỗng."],
    ),
    "18-1": Theory(
        concept=[
            "Màn tổng hợp: chia bài toán lớn thành từng GIAI ĐOẠN nhỏ, giải từng phần.",
            "Giai đoạn gợi ý: (1) hạ quái bằng dict vũ khí, (2) mở cửa mật mã bằng ép kiểu, (3) mở cửa kẹt bằng try/except, (4) đánh boss nhiều lần bằng vòng lặp, (5) tới cúp.",
            "`hero.attack(\"right\", weapon)` đánh ô bên phải bằng vũ khí. Boss có 3 máu.",
            "Cắt lát list: `items[:2]` lấy 2 phần tử đầu.",
            "Chạy thử sau mỗi giai đoạn và xem Bảng tin để biết chương trình đang ở đâu.",
        ],
        starter_notes=[
            ('weakness = {"robot": "hammer", "barrel": "axe", "duck": "sword"}', "Dict vũ khí cho 3 loại quái (duck là Vịt Vương)."),
            ("# Giai đoạn 1: hạ 2 quái đầu tiên", "Ghi chú chia giai đoạn."),
            ("for enemy in hero.find_enemies()[:2]:", "Chỉ duyệt 2 quái đầu (cắt lát [:2]) - boss nằm sau cửa."),
            ("    pass", "Viết lệnh hạ quái bằng đúng vũ khí."),
        ],
        example=[
            ("tasks = [\"a\", \"b\", \"c\", \"d\"]", "List 4 phần tử."),
            ("print(tasks[:2])", "[\"a\", \"b\"] - 2 phần tử đầu."),
            ("print(tasks[2:])", "[\"c\", \"d\"] - từ chỉ số 2 tới hết."),
            ("for i in range(3):", "Lặp 3 lần..."),
            ('    hero.say("Đánh!")', "...dùng cho các hành động lặp lại."),
        ],
        mistakes=[
            "Đi tới quái phía sau cửa khi cửa còn đóng → \"Không có đường\".",
            "Sai vũ khí → hero mất máu.",
        ],
    ),
}


# ---------------------------------------------------------------- màn mới (giai đoạn 1-5)
THEORY.update({
    "7-1": Theory(
        concept=[
            "Chuỗi là dãy ký tự, mỗi ký tự có một VỊ TRÍ (index) đếm từ 0: trong `\"meo\"`, `m` ở vị trí 0, `e` ở 1, `o` ở 2.",
            "Lấy 1 ký tự: `chuoi[2]`. Lấy ký tự cuối: `chuoi[-1]`.",
            "CẮT chuỗi (slicing): `chuoi[dau:cuoi]` lấy từ vị trí `dau` tới TRƯỚC vị trí `cuoi`.",
            "Bỏ trống đầu hoặc cuối: `chuoi[:3]` lấy 3 ký tự đầu, `chuoi[3:]` lấy từ vị trí 3 tới hết. `chuoi[::-1]` đảo ngược chuỗi.",
        ],
        starter_notes=[
            ('# scroll = "abc42xyz"', "Biến scroll có sẵn trong màn."),
            ("print(scroll[0])  # chữ đầu tiên", "In ký tự ở vị trí 0, tức chữ a."),
            ("hero.move_right(2)", "Đi tới đứng cạnh cửa mật mã."),
        ],
        example=[
            ('word = "python"', "Chuỗi 6 ký tự: vị trí 0 tới 5."),
            ("print(word[0], word[-1])", "p n - ký tự đầu và cuối."),
            ("print(word[1:4])", "yth - vị trí 1, 2, 3 (không lấy 4)."),
            ("print(word[:2])", "py - 2 ký tự đầu."),
            ("print(word[::-1])", "nohtyp - đảo ngược."),
        ],
        mistakes=[
            "Quên rằng vị trí bắt đầu từ 0, không phải 1.",
            "`[1:4]` không lấy ký tự ở vị trí 4.",
            "Cắt ra vẫn là CHUỖI: `\"42\"` cần `int(...)` để thành số.",
        ],
    ),
    "7-2": Theory(
        concept=[
            "f-string ghép biến vào câu rất gọn: thêm chữ `f` trước dấu nháy và đặt biến trong `{ }`: `f\"Tôi {tuoi} tuổi\"`.",
            "Trong `{ }` có thể viết cả phép tính hoặc gọi hàm: `f\"{a + b}\"`, `f\"{ten.upper()}\"`.",
            "Hàm có sẵn của chuỗi: `.upper()` viết HOA, `.lower()` viết thường, `.title()` Viết Hoa Đầu Từ, `.strip()` bỏ khoảng trắng hai đầu, `.replace(a, b)` thay a bằng b.",
            "Làm tròn số thực trong f-string: `f\"{3.14159:.2f}\"` → `3.14`.",
        ],
        starter_notes=[
            ('# name = "mèo"', "Biến name có sẵn."),
            ("count = len(hero.find_gems())", "Đếm số ngọc còn trên bản đồ (trước khi đi nhặt)."),
            ('hero.say("name có count ngọc")  # chưa đúng!', "Đây là chuỗi thường: Python in nguyên chữ \"name\" và \"count\", không thay bằng giá trị."),
            ("hero.move_right(8)", "Đi tới cúp."),
        ],
        example=[
            ('pet = "chó"', "Một biến chuỗi."),
            ("legs = 4", "Một biến số."),
            ('print(f"Con {pet} có {legs} chân")', "Con chó có 4 chân."),
            ('print(f"{pet.title()} - {legs * 2}")', "Chó - 8 (gọi hàm và tính toán trong { })."),
            ('print(f"{10 / 3:.1f}")', "3.3 - làm tròn 1 chữ số thập phân."),
        ],
        mistakes=[
            "Quên chữ `f` → Python in nguyên văn `{name}`.",
            "Dùng `( )` thay vì `{ }` trong f-string.",
        ],
    ),
    "10-1": Theory(
        concept=[
            "List comprehension tạo list mới trong MỘT dòng: `[bieu_thuc for x in danh_sach]`.",
            "Thêm điều kiện để lọc: `[x for x in danh_sach if dieu_kien]` - chỉ giữ phần tử thoả điều kiện.",
            "So sánh với cách viết dài: tạo list rỗng, chạy for, dùng if, rồi append - comprehension làm gọn cả 4 bước đó.",
            "Đây là kỹ năng rất hay gặp trong các bài thi và bài tập lập trình.",
        ],
        starter_notes=[
            ("gems = hero.find_gems()", "Lấy danh sách ngọc (mỗi viên là dict có \"color\")."),
            ("blue = []  # chỉ lấy ngọc màu 3", "List rỗng - bạn thay bằng list comprehension có điều kiện."),
            ("hero.move_right(5)", "Đi tới cạnh cửa (ngọc trên đường sẽ được nhặt và biến mất)."),
        ],
        example=[
            ("numbers = [1, 2, 3, 4, 5, 6]", "List ban đầu."),
            ("squares = [n * n for n in numbers]", "[1, 4, 9, 16, 25, 36] - bình phương mọi số."),
            ("evens = [n for n in numbers if n % 2 == 0]", "[2, 4, 6] - chỉ giữ số chẵn."),
            ('names = ["an", "bình"]', "List tên."),
            ("print([name.upper() for name in names])", "['AN', 'BÌNH']."),
        ],
        mistakes=[
            "Đặt `if` trước `for`: `[x if ... for x in ...]` là cú pháp KHÁC (cần cả else).",
            "Lấy danh sách ngọc SAU khi đã nhặt → list rỗng.",
        ],
    ),
    "10-2": Theory(
        concept=[
            "List lồng nhau (nested list) là list chứa các list: giống bảng có hàng và cột.",
            "`grid[y]` là cả hàng y; `grid[y][x]` là ô ở hàng y, cột x.",
            "Duyệt cả bảng: hai vòng for lồng nhau, hoặc một comprehension có 2 vòng for: `[o for hang in grid for o in hang]`.",
            "list có hàm `.count(gia_tri)` đếm số lần giá trị xuất hiện. `sum(...)` cộng các số lại.",
        ],
        starter_notes=[
            ("grid = hero.scan()", "Lấy bản đồ: list các hàng, mỗi hàng là list tên ô."),
            ("print(grid[1])  # hàng số 1", "In cả hàng số 1."),
            ("print(grid[2][1])  # ô ở hàng 2, cột 1", "In một ô - chính là vị trí hero (\"hero\")."),
            ("hero.move_right(3)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("table = [[1, 2, 3], [4, 5, 6]]", "Bảng 2 hàng, 3 cột."),
            ("print(table[1][2])", "6 - hàng 1, cột 2."),
            ("flat = [n for row in table for n in row]", "[1, 2, 3, 4, 5, 6] - trải phẳng bảng."),
            ("print(sum(row.count(2) for row in table))", "1 - số 2 xuất hiện 1 lần trong cả bảng."),
        ],
        mistakes=[
            "Đảo thứ tự chỉ số: `grid[x][y]` thay vì `grid[y][x]`.",
            "Dùng `.count` trên cả bảng: `grid.count(\"spike\")` đếm HÀNG bằng \"spike\" (luôn 0).",
        ],
    ),
    "11-1": Theory(
        concept=[
            "set (tập hợp) giống tập hợp trong Toán: không có phần tử trùng, không có thứ tự.",
            "Giao `a & b`: phần tử có ở CẢ HAI. Hợp `a | b`: phần tử có ở ÍT NHẤT MỘT. Hiệu `a - b`: có ở a nhưng không ở b.",
            "Viết bằng hàm cũng được: `a.intersection(b)`, `a.union(b)`, `a.difference(b)`.",
            "Kiểm tra `x in tap_hop` cực nhanh - nhanh hơn nhiều so với tìm trong list dài. Đây là mẹo tăng tốc bài thuật toán.",
        ],
        starter_notes=[
            ("# scout_a, scout_b: 2 danh sách loại quái", "Hai list có sẵn, có thể chứa phần tử trùng."),
            ("a = set(scout_a)", "Đổi list sang set - phần tử trùng tự biến mất."),
            ("print(a)", "In ra để xem."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ('lop_a = {"bóng đá", "cờ vua", "bơi"}', "Các CLB lớp A thích."),
            ('lop_b = {"cờ vua", "vẽ", "bơi"}', "Các CLB lớp B thích."),
            ("print(lop_a & lop_b)", "{'cờ vua', 'bơi'} - cả hai lớp đều thích."),
            ("print(lop_a | lop_b)", "Cả 4 CLB."),
            ("print(lop_a - lop_b)", "{'bóng đá'} - chỉ lớp A thích."),
        ],
        mistakes=[
            "Dùng `&` trực tiếp trên list → TypeError. Phải đổi sang set trước.",
            "`{}` là dict rỗng; set rỗng phải viết `set()`.",
        ],
    ),
    "12-1": Theory(
        concept=[
            "`import math` mở hộp công cụ Toán học có sẵn của Python.",
            "Hay dùng: `math.sqrt(x)` căn bậc hai, `math.pi` số π, `math.ceil(x)` làm tròn lên, `math.floor(x)` làm tròn xuống, `math.hypot(a, b)` cạnh huyền.",
            "Luỹ thừa trong Python dùng `**`: `3 ** 2` = 9.",
            "Định lý Pytago: tam giác vuông có hai cạnh a, b thì cạnh huyền c = √(a² + b²).",
        ],
        starter_notes=[
            ("import math", "Nạp thư viện math."),
            ("print(math.pi)", "In số π = 3.14159..."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1 - đứng ngay trên cửa."),
        ],
        example=[
            ("import math", "Nạp thư viện."),
            ("print(math.sqrt(49))", "7.0 - kết quả là số thực."),
            ("print(math.ceil(4.1), math.floor(4.9))", "5 4."),
            ("area = math.pi * 3 ** 2", "Diện tích hình tròn bán kính 3."),
            ("print(round(area, 2))", "28.27."),
        ],
        mistakes=[
            "Quên `import math` → NameError: Python không biết `math`.",
            "Dùng `^` để luỹ thừa: trong Python `^` là phép khác, phải dùng `**`.",
        ],
    ),
    "12-2": Theory(
        concept=[
            "Ước chung lớn nhất (ƯCLN) của hai số là số lớn nhất chia hết cả hai. Python có sẵn `math.gcd(a, b)`.",
            "Bội chung nhỏ nhất: `math.lcm(a, b)`.",
            "Ứng dụng: chia đồ vật vào các nhóm bằng nhau, rút gọn phân số.",
        ],
        starter_notes=[
            ("import math", "Nạp thư viện math."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("import math", "Nạp thư viện."),
            ("print(math.gcd(12, 18))", "6."),
            ("print(math.lcm(4, 6))", "12."),
            ("tu, mau = 6, 8", "Phân số 6/8."),
            ("g = math.gcd(tu, mau)", "g = 2."),
            ("print(tu // g, mau // g)", "3 4 - phân số rút gọn 3/4."),
        ],
        mistakes=["Dùng `/` khi rút gọn sẽ ra số thực (3.0); dùng `//` để ra số nguyên."],
    ),
    "13-1": Theory(
        concept=[
            "HOÁN VỊ là các cách sắp xếp thứ tự. 3 vật có 3 × 2 × 1 = 6 cách xếp.",
            "`from itertools import permutations` - `permutations(ds)` sinh lần lượt từng cách xếp, mỗi cách là một tuple.",
            "`permutations(ds, k)` chỉ xếp k phần tử.",
            "`break` thoát vòng lặp ngay khi đã tìm được kết quả - không cần thử tiếp.",
        ],
        starter_notes=[
            ("from itertools import permutations", "Lấy hàm permutations từ thư viện itertools."),
            ("print(list(permutations([1, 2])))", "[(1, 2), (2, 1)] - 2 cách xếp."),
            ("hero.move_right(2)", "Đi tới cạnh cửa rune."),
        ],
        example=[
            ("from itertools import permutations", "Nạp hàm."),
            ('for order in permutations(["A", "B", "C"]):', "Duyệt 6 cách xếp."),
            ("    print(order)", "('A', 'B', 'C'), ('A', 'C', 'B'), ..."),
            ("print(len(list(permutations(range(4)))))", "24 cách xếp 4 vật."),
        ],
        mistakes=["Thử xong mà quên `break` → vẫn chạy tiếp các lần thử thừa."],
    ),
    "13-2": Theory(
        concept=[
            "TỔ HỢP là cách CHỌN ra k phần tử, không quan tâm thứ tự: chọn (8, 12) giống chọn (12, 8).",
            "`combinations(ds, 2)` sinh mọi cặp 2 phần tử khác nhau.",
            "Mở gói tuple ngay trong for: `for a, b in combinations(ds, 2):`.",
            "Tổ hợp chập k của n: `math.comb(n, k)` cho biết có bao nhiêu cách chọn.",
        ],
        starter_notes=[
            ("from itertools import combinations", "Lấy hàm combinations."),
            ("for pair in combinations([1, 2, 3], 2):", "Duyệt mọi cặp từ [1, 2, 3]."),
            ("    print(pair)", "(1, 2) (1, 3) (2, 3) - chỉ 3 cặp vì không tính thứ tự."),
        ],
        example=[
            ("from itertools import combinations", "Nạp hàm."),
            ('team = ["An", "Bình", "Chi", "Dũng"]', "4 bạn."),
            ("for a, b in combinations(team, 2):", "Mọi cặp đánh đôi."),
            ('    print(a, "-", b)', "6 cặp."),
        ],
        mistakes=["Nhầm permutations với combinations: permutations đếm cả (8, 12) và (12, 8)."],
    ),
    "14-1": Theory(
        concept=[
            "`Counter` (trong `collections`) đếm số lần xuất hiện của mỗi giá trị chỉ trong 1 dòng.",
            "Kết quả giống dict: `dem[\"a\"]` là số lần \"a\" xuất hiện.",
            "`.most_common(n)` trả về n giá trị xuất hiện nhiều nhất, dạng list các tuple (giá_trị, số_lần).",
            "Cùng nhóm: `defaultdict(list)` - dict tự tạo giá trị mặc định khi gặp khoá mới, rất tiện để gom nhóm.",
        ],
        starter_notes=[
            ("from collections import Counter", "Lấy Counter."),
            ('print(Counter(["a", "b", "a"]))', "Counter({'a': 2, 'b': 1})."),
            ("hero.move_right(6)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("from collections import Counter", "Nạp Counter."),
            ('votes = ["mèo", "chó", "mèo", "cá", "mèo"]', "Kết quả bình chọn."),
            ("tally = Counter(votes)", "Đếm phiếu."),
            ('print(tally["mèo"])', "3."),
            ("print(tally.most_common(1))", "[('mèo', 3)]."),
            ("winner, total = tally.most_common(1)[0]", "Mở gói: winner = 'mèo', total = 3."),
        ],
        mistakes=["`most_common(1)` là LIST chứa 1 tuple - cần `[0]` để lấy tuple ra."],
    ),
    "14-2": Theory(
        concept=[
            "`deque` (đọc là \"đéc\") là hàng đợi hai đầu: thêm / lấy ở cả đầu và cuối đều rất nhanh.",
            "`append(x)` thêm vào cuối, `appendleft(x)` thêm vào đầu, `popleft()` lấy người đầu ra, `pop()` lấy người cuối ra.",
            "`rotate(n)` xoay hàng: n âm là đưa người đầu xuống cuối.",
            "Với list thường, lấy phần tử đầu (`pop(0)`) phải dịch cả list - chậm khi list dài.",
        ],
        starter_notes=[
            ("from collections import deque", "Lấy deque."),
            ("line = deque(guards)", "Tạo hàng đợi từ list tên lính gác."),
            ("print(line)", "In hàng hiện tại."),
        ],
        example=[
            ("from collections import deque", "Nạp deque."),
            ('queue = deque(["A", "B", "C"])', "Hàng đợi."),
            ('queue.append("D")', "Thêm D vào cuối."),
            ("first = queue.popleft()", "first = 'A'; hàng còn B, C, D."),
            ("queue.rotate(-1)", "B xuống cuối: C, D, B."),
            ("print(first, list(queue))", "A ['C', 'D', 'B']."),
        ],
        mistakes=["Gọi `popleft()` trên list thường → AttributeError (list không có popleft)."],
    ),
    "15-1": Theory(
        concept=[
            "Thư viện `datetime` xử lý ngày giờ. `date(2026, 3, 15)` là ngày 15/3/2026.",
            "`date.fromisoformat(\"2026-03-15\")` đổi chuỗi dạng năm-tháng-ngày thành ngày.",
            "Trừ hai ngày ra khoảng thời gian (timedelta); `.days` là số ngày.",
            "`ngay.weekday()` cho thứ trong tuần (0 = thứ Hai ... 6 = Chủ nhật). `date.today()` là hôm nay.",
        ],
        starter_notes=[
            ("from datetime import date", "Lấy kiểu date."),
            ("print(date.fromisoformat(start))", "In ngày bắt đầu."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1, đứng trên cửa."),
        ],
        example=[
            ("from datetime import date, timedelta", "Nạp thư viện."),
            ("birthday = date(2026, 6, 1)", "Ngày 1/6/2026."),
            ("print(birthday.weekday())", "0 - thứ Hai."),
            ("later = birthday + timedelta(days=10)", "10 ngày sau."),
            ("print(later)", "2026-06-11."),
            ("print((later - birthday).days)", "10."),
        ],
        mistakes=["Quên `.days` → in ra dạng `73 days, 0:00:00` chứ không phải số 73."],
    ),
    "16-3": Theory(
        concept=[
            "Mỗi loại lỗi có tên riêng: `ValueError` (giá trị sai, ví dụ `int(\"abc\")`), `ZeroDivisionError` (chia cho 0), `KeyError` (khoá không có trong dict), `IndexError` (vị trí ngoài list).",
            "Nên bắt ĐÚNG loại lỗi: `except ValueError:` - để các lỗi khác vẫn hiện ra cho bạn sửa.",
            "`else:` chạy khi KHÔNG có lỗi, `finally:` luôn chạy dù có lỗi hay không.",
            "Tự ném lỗi: `raise ValueError(\"thông báo\")`.",
        ],
        starter_notes=[
            ("for text in candidates:", "Duyệt từng chuỗi ứng viên."),
            ("    print(int(text))", "\"7x\" không đổi được → ValueError → chương trình dừng ngay."),
        ],
        example=[
            ('for text in ["5", "năm", "7"]:', "Ba chuỗi cần đổi."),
            ("    try:", "Thử..."),
            ("        number = int(text)", "...đổi sang số."),
            ("    except ValueError:", "Nếu không đổi được"),
            ('        print("Bỏ qua", text)', "→ báo và bỏ qua."),
            ("    else:", "Nếu đổi được"),
            ("        print(number * 2)", "→ in gấp đôi: 10 và 14."),
        ],
        mistakes=["Viết `except:` trơn bắt MỌI lỗi, kể cả lỗi gõ sai tên biến - khó tìm bug."],
    ),
    "17-1": Theory(
        concept=[
            "class là KHUÔN để tạo đồ vật (object). Ví dụ class Potion là khuôn, mỗi bình thuốc là một đồ vật.",
            "`__init__(self, ...)` chạy tự động khi tạo đồ vật; dùng để cất dữ liệu vào `self.ten_thuoc_tinh`.",
            "`self` là chính đồ vật đang được tạo / đang được dùng.",
            "Tạo đồ vật: gọi tên class như gọi hàm: `p = Potion(2)`; đọc thuộc tính: `p.power`.",
        ],
        starter_notes=[
            ("class Potion:", "Định nghĩa class Potion."),
            ("    pass", "Class rỗng - chưa có thuộc tính power."),
            ("hero.move_right(6)", "Đi tới cúp (nhưng mới 1 máu thì chưa thắng)."),
        ],
        example=[
            ("class Pet:", "Khuôn thú cưng."),
            ("    def __init__(self, name, age):", "Chạy khi tạo thú cưng."),
            ("        self.name = name", "Cất tên."),
            ("        self.age = age", "Cất tuổi."),
            ('cat = Pet("Mướp", 2)', "Tạo một con mèo."),
            ("print(cat.name, cat.age)", "Mướp 2."),
        ],
        mistakes=[
            "Quên `self` trong `def __init__(self, ...)`.",
            "Viết `__init__` thiếu dấu gạch dưới: phải là HAI gạch mỗi bên.",
        ],
    ),
    "17-2": Theory(
        concept=[
            "Magic method (dunder) là các hàm tên `__ten__` mà Python tự gọi trong tình huống đặc biệt.",
            "`__str__(self)` trả về chuỗi dùng khi `print(vat)` hoặc `str(vat)`.",
            "`__add__(self, other)` chạy khi viết `vat1 + vat2`; nên trả về một đồ vật MỚI.",
            "Còn nhiều magic method khác: `__repr__`, `__eq__` (==), `__len__` (len), `__lt__` (<).",
        ],
        starter_notes=[
            ("class Vector:", "Class véc-tơ."),
            ("    def __init__(self, x, y):", "Nhận toạ độ x, y khi tạo."),
            ("        self.x = x", "Cất x."),
            ("        self.y = y", "Cất y."),
            ("a = Vector(1, 0)", "Tạo véc-tơ (1, 0)."),
            ("print(a.x, a.y)", "In 1 0."),
        ],
        example=[
            ("class Money:", "Class tiền."),
            ("    def __init__(self, amount):", "Nhận số tiền khi tạo."),
            ("        self.amount = amount", "Cất số tiền."),
            ("    def __add__(self, other):", "Khi viết tien1 + tien2..."),
            ("        return Money(self.amount + other.amount)", "...trả về tờ tiền mới có tổng."),
            ("    def __str__(self):", "Khi print..."),
            ('        return f"{self.amount} đồng"', "...hiện ra như vậy."),
            ("print(Money(5000) + Money(2000))", "7000 đồng."),
        ],
        mistakes=[
            "`__str__` dùng print thay vì return → lỗi TypeError.",
            "`__add__` sửa self rồi không trả về gì → kết quả là None.",
        ],
    ),
    "17-3": Theory(
        concept=[
            "Vòng for duyệt được list, chuỗi, range... vì chúng là đồ vật DUYỆT ĐƯỢC (iterable).",
            "Muốn đồ vật của bạn duyệt được, viết magic method `__iter__(self)` trả về một iterator.",
            "Cách dễ nhất: `return iter(mot_list)`. Nâng cao hơn: dùng `yield` để sinh từng phần tử.",
            "List nhân số sẽ lặp lại: `[\"a\", \"b\"] * 2` = `[\"a\", \"b\", \"a\", \"b\"]`.",
        ],
        starter_notes=[
            ("class Patrol:", "Class lộ trình tuần tra."),
            ("    def __init__(self, rounds):", "Nhận số vòng tuần tra."),
            ("        self.rounds = rounds", "Cất số vòng."),
            ('hero.follow(["right", "down"])  # follow nhận thứ duyệt được', "Đi theo một list - chỉ 1 bậc. Bạn cần đưa Patrol vào."),
        ],
        example=[
            ("class Countdown:", "Đếm ngược."),
            ("    def __init__(self, start):", "Nhận số bắt đầu."),
            ("        self.start = start", "Cất số bắt đầu."),
            ("    def __iter__(self):", "Giúp for duyệt được."),
            ("        return iter(range(self.start, 0, -1))", "Trả iterator đếm ngược."),
            ("for n in Countdown(3):", "Duyệt như list."),
            ("    print(n)", "3, 2, 1."),
        ],
        mistakes=["`__iter__` trả về list thay vì iterator → TypeError. Bọc bằng `iter(...)`."],
    ),
    "19-1": Theory(
        concept=[
            "`lambda` tạo hàm ngắn không cần tên: `lambda x: x * 2` giống `def f(x): return x * 2`.",
            "`map(ham, ds)` áp hàm lên TỪNG phần tử. `filter(ham, ds)` chỉ giữ phần tử mà hàm trả về True.",
            "map / filter trả về kết quả \"lười\" - bọc `list(...)` để xem, hoặc đưa thẳng vào `sum`, `for`.",
            "Chuỗi có `.isdigit()`: True nếu toàn chữ số.",
        ],
        starter_notes=[
            ("double = lambda n: n * 2", "Hàm lambda nhân đôi."),
            ("print(double(5))", "10."),
            ("print(list(map(double, [1, 2, 3])))", "[2, 4, 6] - nhân đôi từng phần tử."),
        ],
        example=[
            ("ages = [10, 15, 8, 17]", "Tuổi các bạn."),
            ("teens = list(filter(lambda a: a >= 13, ages))", "[15, 17] - chỉ giữ từ 13 tuổi."),
            ('words = ["1", "2", "3"]', "Chuỗi số."),
            ("print(sum(map(int, words)))", "6 - đổi từng chuỗi sang int rồi cộng."),
        ],
        mistakes=["Quên `list(...)` khi print → hiện `<map object ...>` thay vì danh sách."],
    ),
    "19-2": Theory(
        concept=[
            "`zip(a, b)` ghép từng cặp: phần tử thứ nhất của a với thứ nhất của b, thứ hai với thứ hai...",
            "Dừng khi list ngắn hơn hết phần tử.",
            "`enumerate(ds)` ghép số thứ tự với phần tử: `for i, x in enumerate(ds):`.",
            "`sorted(ds, key=lambda x: ...)` sắp xếp theo tiêu chí tuỳ chọn.",
        ],
        starter_notes=[
            ('for number, letter in zip([1, 2, 3], ["a", "b", "c"]):', "Ghép 1-a, 2-b, 3-c."),
            ("    print(number, letter)", "In từng cặp."),
        ],
        example=[
            ('names = ["An", "Bình"]', "Tên."),
            ("scores = [9, 7]", "Điểm."),
            ("for name, score in zip(names, scores):", "Ghép tên với điểm."),
            ('    print(f"{name}: {score}")', "An: 9, Bình: 7."),
            ("for rank, name in enumerate(names, start=1):", "Đánh số từ 1."),
            ("    print(rank, name)", "1 An, 2 Bình."),
        ],
        mistakes=["Hai list khác độ dài: zip bỏ qua phần thừa mà không báo lỗi."],
    ),
    "20-1": Theory(
        concept=[
            "Biểu thức chính quy (regex) là \"mẫu\" để tìm chữ trong văn bản. Dùng thư viện `re`.",
            "Ký hiệu hay dùng: `\\d` một chữ số, `\\w` một chữ cái/số, `+` một hay nhiều lần, `.` một ký tự bất kỳ.",
            "`re.findall(mau, chuoi)` trả về list mọi chỗ khớp. `re.search(mau, chuoi)` tìm chỗ khớp ĐẦU TIÊN.",
            "Ngoặc tròn `( )` tạo NHÓM để lấy riêng một phần: `ket_qua.group(1)`.",
            "Viết mẫu với chữ `r` phía trước (`r\"\\d+\"`) để Python không hiểu nhầm dấu `\\`.",
        ],
        starter_notes=[
            ("import re", "Nạp thư viện regex."),
            ('print(re.findall(r"\\d+", letter))', "In mọi dãy chữ số trong thư: ['12', '4207', '99']."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("import re", "Nạp thư viện."),
            ('text = "Lớp 7A có 32 bạn, lớp 7B có 30 bạn"', "Văn bản."),
            ('print(re.findall(r"\\d+", text))', "['7', '32', '7', '30']."),
            ('m = re.search(r"7B có (\\d+)", text)', "Tìm số sau \"7B có\"."),
            ("print(m.group(1))", "'30' - vẫn là chuỗi."),
        ],
        mistakes=[
            "Không tìm thấy thì `re.search` trả về None → gọi `.group` sẽ lỗi AttributeError.",
            "Kết quả regex luôn là chuỗi - cần `int(...)`.",
        ],
    ),
    "20-2": Theory(
        concept=[
            "XML là cách viết dữ liệu bằng THẺ, giống HTML: `<gem x=\"3\" y=\"1\"/>`.",
            "Thẻ có tên (`tag`) và thuộc tính (`x`, `y`). Thẻ có thể chứa thẻ con.",
            "`import xml.etree.ElementTree as ET` rồi `ET.fromstring(chuoi_xml)` để đọc.",
            "`goc.findall(\"ten\")` lấy mọi thẻ con có tên đó, `goc.find(\"ten\")` lấy thẻ đầu tiên, `the.get(\"x\")` đọc thuộc tính.",
        ],
        starter_notes=[
            ("import xml.etree.ElementTree as ET", "Nạp bộ đọc XML, đặt tên ngắn là ET."),
            ("root = ET.fromstring(map_xml)", "Đọc chuỗi XML, root là thẻ ngoài cùng <map>."),
            ("print(root.tag)", "In \"map\"."),
        ],
        example=[
            ("import xml.etree.ElementTree as ET", "Nạp thư viện."),
            ("data = '<class><student name=\"An\" score=\"9\"/><student name=\"Bình\" score=\"8\"/></class>'", "XML danh sách lớp."),
            ("root = ET.fromstring(data)", "Đọc XML."),
            ('for s in root.findall("student"):', "Duyệt từng học sinh."),
            ('    print(s.get("name"), int(s.get("score")))', "An 9, Bình 8."),
        ],
        mistakes=["`the.get(\"x\")` trả về CHUỖI \"3\", phải `int(...)` trước khi dùng làm toạ độ."],
    ),
    "21-1": Theory(
        concept=[
            "Trong Python, hàm cũng là một giá trị: có thể cất vào biến, truyền vào hàm khác, trả về từ hàm.",
            "CLOSURE: hàm bên trong được tạo trong hàm bên ngoài và NHỚ các biến của hàm ngoài, kể cả sau khi hàm ngoài chạy xong.",
            "Dùng closure để tạo \"nhà máy hàm\": một hàm sinh ra nhiều hàm tương tự nhau.",
            "Trả về hàm: `return ten_ham` (KHÔNG có ngoặc). Có ngoặc là gọi hàm.",
        ],
        starter_notes=[
            ("def make_mover(direction):", "Nhà máy tạo hàm di chuyển theo hướng direction."),
            ("    pass", "Chưa làm gì - bạn tạo hàm con và trả nó ra."),
            ('hero.follow(["right"] * 3)  # đi phải 3 ô', "Cách đi trực tiếp, để tham khảo."),
        ],
        example=[
            ("def make_greeter(greeting):", "Nhà máy tạo hàm chào."),
            ("    def greet(name):", "Hàm con nhớ biến greeting."),
            ('        print(f"{greeting}, {name}!")', "In lời chào."),
            ("    return greet", "Trả hàm con ra (không ngoặc)."),
            ('hello = make_greeter("Xin chào")', "hello là một hàm."),
            ('hello("An")', "Xin chào, An!"),
        ],
        mistakes=["`return greet()` (có ngoặc) là gọi hàm con ngay, trả về None."],
    ),
    "21-2": Theory(
        concept=[
            "DECORATOR là hàm nhận một hàm, trả về hàm mới \"bọc\" bên ngoài để thêm tính năng.",
            "Viết `@ten_decorator` ngay trên `def` - Python tự bọc hàm đó.",
            "`@twice` phía trên `def f():` tương đương với `f = twice(f)`.",
            "Ứng dụng thật: ghi log, đo thời gian, kiểm tra quyền truy cập... mà không sửa code bên trong hàm.",
        ],
        starter_notes=[
            ("def twice(action):", "Decorator nhận vào hàm action."),
            ("    pass", "Chưa bọc gì - bạn tạo hàm bọc gọi action 2 lần và trả nó ra."),
            ("def stair():", "Hàm đi 1 bậc thang."),
            ("    hero.move_right()", "Sang phải."),
            ("    hero.move_down()", "Xuống."),
            ("stair()", "Gọi 1 lần - mới xuống 1 bậc."),
        ],
        example=[
            ("def shout(func):", "Decorator thêm tiếng hô."),
            ("    def wrapper():", "Hàm bọc."),
            ('        print("Bắt đầu!")', "Làm thêm trước."),
            ("        func()", "Gọi hàm gốc."),
            ("    return wrapper", "Trả hàm bọc."),
            ("@shout", "Bọc hàm bên dưới."),
            ("def run():", "Hàm gốc."),
            ('    print("Chạy!")', "In Chạy!"),
            ("run()", "Bắt đầu! rồi Chạy!"),
        ],
        mistakes=["Quên trả hàm bọc ra → hàm sau khi bọc trở thành None, gọi sẽ lỗi."],
    ),
    "22-1": Theory(
        concept=[
            "NumPy là thư viện tính toán với BẢNG SỐ (mảng) rất nhanh - nền tảng của khoa học dữ liệu và AI.",
            "`import numpy as np` rồi `np.array(list)` để tạo mảng. List lồng nhau → mảng 2 chiều (bảng).",
            "`.shape` cho (số hàng, số cột). `.sum()`, `.max()`, `.min()`, `.mean()` tính trên cả mảng.",
            "Tính theo hàng / cột: `.sum(axis=0)` cộng theo cột, `.sum(axis=1)` cộng theo hàng.",
        ],
        starter_notes=[
            ("import numpy as np", "Nạp NumPy, đặt tên ngắn np."),
            ("board = np.array(scores)", "Đổi bảng điểm (list lồng nhau) thành mảng NumPy."),
            ("print(board.shape)", "(2, 3) - 2 hàng, 3 cột."),
        ],
        example=[
            ("import numpy as np", "Nạp NumPy."),
            ("marks = np.array([[8, 9], [6, 10]])", "Điểm 2 bạn, 2 môn."),
            ("print(marks.max())", "10."),
            ("print(marks.sum(axis=1))", "[17 16] - tổng điểm mỗi bạn."),
            ("print(marks.mean())", "8.25 - điểm trung bình."),
        ],
        mistakes=["Quên `import numpy as np` → NameError: không biết `np`."],
    ),
    "22-2": Theory(
        concept=[
            "Với mảng NumPy, `A * B` nhân TỪNG cặp phần tử cùng vị trí.",
            "NHÂN MA TRẬN viết `A @ B` (hoặc `np.dot(A, B)`): phần tử ở hàng i, cột j = hàng i của A nhân lần lượt với cột j của B rồi cộng lại.",
            "Ví dụ hàng [1, 2] nhân cột [2, 1]: 1×2 + 2×1 = 4.",
            "Phép nhân ma trận dùng nhiều trong đồ hoạ máy tính, game 3D và trí tuệ nhân tạo.",
        ],
        starter_notes=[
            ("import numpy as np", "Nạp NumPy."),
            ("A = np.array(matrix_a)", "Ma trận A."),
            ("print(A * 2)  # nhân mỗi phần tử với 2", "[[2 4] [6 8]]."),
        ],
        example=[
            ("import numpy as np", "Nạp NumPy."),
            ("P = np.array([[1, 0], [0, 1]])", "Ma trận đơn vị."),
            ("Q = np.array([[5, 6], [7, 8]])", "Ma trận Q."),
            ("print(P @ Q)", "Bằng chính Q - nhân với ma trận đơn vị."),
            ("print(P * Q)", "[[5 0] [0 8]] - nhân từng phần tử, khác hẳn!"),
        ],
        mistakes=["Dùng `*` khi cần nhân ma trận → ra kết quả sai mà không báo lỗi."],
    ),
    "23-1": Theory(
        concept=[
            "GỠ LỖI (debugging) là kỹ năng quan trọng nhất của lập trình viên.",
            "Bước 1: đọc thông báo lỗi - nó cho biết LOẠI lỗi và DÒNG lỗi (dòng tô đỏ trong khung code).",
            "Lỗi cú pháp (SyntaxError) hay gặp: thiếu `:`, thiếu dấu nháy đóng, thiếu ngoặc, thụt lề sai.",
            "Sửa từng lỗi một rồi chạy lại - đôi khi sửa xong lỗi đầu mới thấy lỗi tiếp theo.",
            "Hết lỗi cú pháp vẫn có thể còn lỗi LOGIC: chương trình chạy nhưng làm sai việc.",
        ],
        starter_notes=[
            ("for i in range(8)", "Dòng for này có đủ dấu cần thiết chưa? Và 8 bước có đủ tới cúp không?"),
            ("hero.move_right()", "Lệnh này có thuộc vòng lặp không? Nhìn thụt lề."),
            ('hero.say("Xong!)', "Đếm dấu nháy."),
        ],
        example=[
            ("total = 0", "Ví dụ code ĐÚNG để so sánh."),
            ("for n in range(1, 4):", "Có dấu : ở cuối."),
            ("    total = total + n", "Thụt 4 khoảng."),
            ('print("Tổng:", total)', "Nháy mở và đóng đầy đủ. In 6."),
        ],
        mistakes=["Sửa nhiều chỗ cùng lúc mà không chạy lại → khó biết chỗ nào đã đúng."],
    ),
    "23-2": Theory(
        concept=[
            "Lỗi LOGIC: code chạy được nhưng kết quả sai. Python không chỉ ra được - bạn phải tự tìm.",
            "Mẹo 1: dùng `print(...)` để xem giá trị biến tại từng bước.",
            "Mẹo 2: đọc lại từng dòng, tự hỏi \"dòng này thật sự làm gì?\" - nhất là thụt lề (thuộc vòng lặp hay không?).",
            "Mẹo 3: chú ý chữ hoa / chữ thường và thứ tự tham số (x trước, y sau).",
            "KeyError cho biết khoá bạn tra không có trong dict - in ra các khoá bằng `print(ten_dict.keys())`.",
        ],
        starter_notes=[
            ('weakness = {"Robot": "hammer", "barrel": "axe", "cannon": "bow"}', "So khoá trong dict với tên loại quái thật (in ra để xem)."),
            ("for enemy in hero.find_enemies():", "Duyệt từng quái."),
            ('    weapon = weakness[enemy["type"]]', "Tra vũ khí."),
            ('hero.attack_target(enemy["x"], enemy["y"], weapon)', "Dòng này chạy mấy lần? Nhìn thụt lề."),
            ("exit_x, exit_y = hero.exit_position", "Lấy toạ độ cổng."),
            ("hero.move_to(exit_y, exit_x)", "move_to nhận (x, y) theo thứ tự nào?"),
        ],
        example=[
            ('prices = {"táo": 5, "cam": 7}', "Code có in kiểm tra."),
            ("print(prices.keys())", "Xem có những khoá nào."),
            ("total = 0", "Bắt đầu từ 0."),
            ('for fruit in ["táo", "cam"]:', "Duyệt từng loại quả."),
            ("    total = total + prices[fruit]", "Trong vòng lặp - cộng mỗi loại."),
            ("    print(fruit, total)", "In từng bước để kiểm tra."),
            ("print(total)", "12."),
        ],
        mistakes=["Đoán mò rồi sửa lung tung - hãy in giá trị ra để biết chắc."],
    ),
})

# Lý thuyết của các bài luyện tập thêm (tự đăng ký vào THEORY khi được import).


# ======================================================================
# theory_practice.py
# ======================================================================

PRACTICE_THEORY: dict[str, Theory] = {}

# ================================================================ GIAI ĐOẠN 1
PRACTICE_THEORY.update({
    "1-4": Theory(
        concept=[
            "Chương trình là một DÃY lệnh chạy lần lượt. Đổi thứ tự lệnh là đổi đường đi.",
            "`hero.move_right()` không ghi số thì đi đúng 1 bước.",
            "Mẹo: nhìn bản đồ, đọc đường đi thành từng bước nhỏ rồi viết từng lệnh tương ứng.",
        ],
        starter_notes=[
            ("hero.move_right()", "Bước 1: sang phải 1 ô."),
            ("hero.move_down()", "Bước 2: xuống 1 ô."),
            ("# viết tiếp", "Ghi chú: bạn viết tiếp các bước còn lại."),
        ],
        example=[
            ("hero.move_down()", "Xuống 1."),
            ("hero.move_left()", "Trái 1."),
            ("hero.move_down()", "Xuống 1."),
            ("hero.move_left()", "Trái 1 - đường zigzag theo hướng ngược lại."),
        ],
        mistakes=["Viết thiếu hoặc thừa một lệnh làm hero đụng tường và dừng ở giữa đường."],
    ),
    "1-5": Theory(
        concept=[
            "Không phải lúc nào cũng đi thẳng tới đích được - đôi khi phải đi vòng.",
            "Có 4 hướng: lên (up), xuống (down), trái (left), phải (right).",
            "Lệnh `hero.say(...)` có thể đặt ở bất kỳ đâu - ở đây là sau khi tới cúp.",
        ],
        starter_notes=[("hero.move_down(2)", "Đoạn 1: đi xuống 2 ô.")],
        example=[
            ("hero.move_right(3)", "Sang phải 3."),
            ("hero.move_down(2)", "Xuống 2."),
            ("hero.move_left(3)", "Quay về trái 3 - một đường vòng chữ U úp."),
            ('hero.say("Xong")', "Nói khi đã tới nơi."),
        ],
        mistakes=["Nhầm move_up và move_down: trên bản đồ, đi lên là y giảm."],
    ),
    "2-3": Theory(
        concept=[
            "Giá trị trong biến có thể THAY ĐỔI. `steps = steps - 1`: lấy giá trị cũ trừ 1 rồi cất lại vào chính steps.",
            "Viết tắt: `steps -= 1` giống `steps = steps - 1`; `steps += 2` giống `steps = steps + 2`.",
            "Dùng lại một biến giúp code dễ sửa: đổi một chỗ là mọi nơi dùng biến đều đổi theo.",
        ],
        starter_notes=[
            ("steps = 3", "Biến steps bắt đầu bằng 3."),
            ("hero.move_right(steps)", "Đi phải 3 ô."),
            ("# đổi steps rồi đi xuống", "Bạn thay đổi steps rồi dùng nó để đi xuống."),
        ],
        example=[
            ("lives = 3", "Bắt đầu 3 mạng."),
            ("lives = lives - 1", "Mất 1 mạng: còn 2."),
            ("lives += 5", "Nhặt thêm 5: còn 7."),
            ("print(lives)", "7."),
        ],
        mistakes=["Viết `steps - 1` một mình (không gán) thì steps KHÔNG thay đổi."],
    ),
    "2-4": Theory(
        concept=[
            "Mỗi giá trị có KIỂU: `\"Mai\"` là chuỗi (str), `12` là số nguyên (int).",
            "Dấu `+` nối được chuỗi với chuỗi, cộng được số với số, nhưng KHÔNG trộn chuỗi với số.",
            "`str(12)` đổi số 12 thành chuỗi `\"12\"` để nối được.",
        ],
        starter_notes=[
            ('# name = "Mai", age = 12', "Hai biến có sẵn: một chuỗi, một số."),
            ("hero.say(name)", "Mới nói tên, còn thiếu tuổi."),
            ("hero.move_right(6)", "Đi tới cúp."),
        ],
        example=[
            ('pet = "Mướp"', "Chuỗi."),
            ("weight = 4", "Số."),
            ('print(pet + " nặng " + str(weight) + " kg")', "Mướp nặng 4 kg."),
        ],
        mistakes=["Quên dấu cách: `name + str(age)` cho ra \"Mai12\"."],
    ),
    "2-5": Theory(
        concept=[
            "Phép chia `/` luôn cho số thực: `17 / 5 = 3.4`.",
            "Phép chia lấy phần nguyên `//`: `17 // 5 = 3`. Phép chia lấy dư `%`: `17 % 5 = 2`.",
            "Ứng dụng: chia đồ vật, kiểm tra chẵn lẻ (`n % 2 == 0` là số chẵn).",
        ],
        starter_notes=[
            ("# gems = 17, friends = 5", "Biến có sẵn."),
            ("each = gems / friends", "Phép / cho 3.4 - không phải số kẹo nguyên."),
            ("hero.say(each)", "Hero nói 3.4."),
            ("hero.move_right(5)", "Đi tới cúp."),
        ],
        example=[
            ("minutes = 135", "135 phút."),
            ("hours = minutes // 60", "2 giờ."),
            ("rest = minutes % 60", "15 phút."),
            ('print(str(hours) + " giờ " + str(rest) + " phút")', "2 giờ 15 phút."),
        ],
        mistakes=["Nhầm `%` (chia lấy dư) với phần trăm."],
    ),
    "3-3": Theory(
        concept=[
            "Phép so sánh: `>` lớn hơn, `<` nhỏ hơn, `>=` lớn hơn hoặc bằng, `<=` nhỏ hơn hoặc bằng, `==` bằng, `!=` khác.",
            "Kết quả so sánh là `True` hoặc `False` - quyết định nhánh nào của if/else được chạy.",
        ],
        starter_notes=[
            ("# coins = 7, vé vào cổng giá 5", "Dữ kiện: có 7 xu, vé 5 xu."),
            ("if coins >= 10:", "Đang so với 10 - sai giá vé."),
            ('    hero.say("Đủ tiền")', "Nhánh đủ tiền."),
            ("else:", "Ngược lại..."),
            ('    hero.say("Thiếu tiền")', "...nhánh thiếu tiền."),
            ("hero.move_right(5)", "Đi tới cúp."),
        ],
        example=[
            ("age = 12", "12 tuổi."),
            ("if age >= 13:", "Từ 13 tuổi trở lên?"),
            ('    print("Vé người lớn")', ""),
            ("else:", ""),
            ('    print("Vé trẻ em")', "In: Vé trẻ em."),
        ],
        mistakes=["`>` và `>=` khác nhau khi hai số bằng nhau."],
    ),
    "3-4": Theory(
        concept=[
            "`elif` (else if) kiểm tra thêm điều kiện khi điều kiện trước sai.",
            "Python xét lần lượt từ trên xuống, chạy nhánh ĐẦU TIÊN đúng rồi bỏ qua các nhánh còn lại.",
        ],
        starter_notes=[
            ("hero.move_right(2)", "Đi tới ngã ba."),
            ('if hero.look("up") == "spike":', "Chỉ kiểm tra phía trên - lần này gai lại ở dưới."),
            ("    hero.move_down()", "Đi xuống nếu trên có gai."),
        ],
        example=[
            ("score = 7", "Điểm 7."),
            ("if score >= 9:", ""),
            ('    print("Giỏi")', ""),
            ("elif score >= 6.5:", "Không giỏi thì xét tiếp."),
            ('    print("Khá")', "In: Khá."),
            ("else:", ""),
            ('    print("Cố lên")', ""),
        ],
        mistakes=["Viết hai câu `if` riêng thay vì `if/elif` - cả hai có thể cùng chạy."],
    ),
    "3-5": Theory(
        concept=[
            "`and`: đúng khi CẢ HAI điều kiện đúng. `or`: đúng khi ÍT NHẤT MỘT điều kiện đúng. `not`: đảo ngược.",
            "`hero.hp` cho biết số máu hiện tại của hero (tối đa 3).",
        ],
        starter_notes=[
            ("hero.move_right(2)", "Đi tới gần quái."),
            ("if hero.hp > 1:", "Mới kiểm tra máu, chưa kiểm tra có quái hay không."),
            ("    pass", "Chưa làm gì."),
        ],
        example=[
            ("rain = False", "Không mưa."),
            ("homework_done = True", "Đã làm bài."),
            ("if homework_done and not rain:", "Cả hai cùng đúng."),
            ('    print("Đi đá bóng!")', "In ra."),
        ],
        mistakes=["Viết `if hero.look(\"right\") == \"enemy\" and > 1` - mỗi vế phải là một so sánh đầy đủ."],
    ),
    "4-4": Theory(
        concept=[
            "`range(a, b)` sinh các số từ a tới b-1: `range(1, 4)` cho 1, 2, 3.",
            "Biến vòng lặp (i) có thể dùng trong thân vòng lặp, mỗi vòng một giá trị khác.",
        ],
        starter_notes=[
            ("for i in range(3):", "Lặp 3 lần với i = 0, 1, 2."),
            ("    print(i)", "In giá trị i để xem."),
        ],
        example=[
            ("for n in range(2, 5):", "n = 2, 3, 4."),
            ('    print("*" * n)', "In 2, 3, 4 dấu sao - tam giác lớn dần."),
        ],
        mistakes=["range(1, 3) chỉ có 1 và 2 - không có 3."],
    ),
    "4-5": Theory(
        concept=[
            "Vòng lặp LỒNG NHAU: vòng trong chạy trọn vẹn cho MỖI lần lặp của vòng ngoài.",
            "Thụt lề quyết định lệnh thuộc vòng nào: thụt sâu hơn là thuộc vòng trong.",
            "Vòng trong có thể phụ thuộc biến của vòng ngoài: `for j in range(i):`.",
        ],
        starter_notes=[
            ("for i in range(1, 5):", "i = 1, 2, 3, 4 - độ dài mỗi bậc."),
            ("    hero.move_right(i)", "Đi i bước, nhưng chưa có bước đi xuống."),
        ],
        example=[
            ("for row in range(1, 4):", "3 hàng."),
            ("    line = \"\"", "Bắt đầu một hàng."),
            ("    for col in range(row):", "Hàng thứ row có row ô."),
            ('        line = line + "#"', ""),
            ("    print(line)", "In #, ##, ###."),
        ],
        mistakes=["Đặt lệnh của vòng ngoài vào vòng trong (thụt lề sai) làm nó chạy quá nhiều lần."],
    ),
    "5-3": Theory(
        concept=[
            "`int(\"7\")` được, nhưng `int(\"7.0\")` báo ValueError vì có dấu chấm.",
            "Cách làm: `float(\"7.0\")` → 7.0, rồi `int(7.0)` → 7. Có thể viết gọn `int(float(...))`.",
            "`int()` của số thực sẽ BỎ phần lẻ: `int(3.9)` là 3.",
        ],
        starter_notes=[
            ('# distance = "7.0"', "Chuỗi có dấu chấm thập phân."),
            ("hero.move_right(int(distance))", "int(\"7.0\") sẽ lỗi."),
        ],
        example=[
            ('height = "1.55"', "Chiều cao dạng chuỗi."),
            ("print(float(height) * 100)", "155.0."),
            ("print(int(float(height) * 100))", "155."),
        ],
        mistakes=["Dùng round thay int có thể làm tròn lên khác ý muốn."],
    ),
    "5-4": Theory(
        concept=[
            "Mật mã có thể là chuỗi chứ không chỉ là số.",
            "Ghép chữ và số: đổi số sang chuỗi bằng `str()` rồi nối bằng `+`.",
        ],
        starter_notes=[
            ("# room = 7", "Số phòng là số."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
            ('hero.enter_code("Phòng" + room)', "Chuỗi + số → TypeError; cũng thiếu dấu cách."),
        ],
        example=[
            ("level = 3", "Màn số 3."),
            ('label = "Màn " + str(level)', "\"Màn 3\"."),
            ("print(label)", "Màn 3."),
        ],
        mistakes=["`str(\"Phòng \" + room)` vẫn lỗi vì phép + chạy trước khi đổi kiểu."],
    ),
    "5-5": Theory(
        concept=[
            "`bool(x)` đổi sang True/False. Số 0, chuỗi rỗng `\"\"`, list rỗng `[]` là False; còn lại là True.",
            "Bẫy: `bool(\"0\")` là True vì chuỗi \"0\" KHÔNG rỗng. Phải đổi sang số trước: `bool(int(\"0\"))` là False.",
        ],
        starter_notes=[
            ('# switch = "0"', "Công tắc ghi bằng chuỗi."),
            ("print(bool(switch))  # thử xem", "In ra True - bất ngờ chưa?"),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1, đứng trên cửa."),
        ],
        example=[
            ("print(bool(5), bool(0))", "True False."),
            ('print(bool("hi"), bool(""))', "True False."),
            ("print(bool([]))", "False - list rỗng."),
        ],
        mistakes=["Tưởng `bool(\"False\")` là False - thực ra là True."],
    ),
    "6-4": Theory(
        concept=[
            "THAM SỐ là biến của hàm, nhận giá trị khi gọi: `step(2)` thì n = 2, `step(3)` thì n = 3.",
            "Một hàm có tham số dùng được cho nhiều trường hợp khác nhau.",
        ],
        starter_notes=[
            ("def step(n):", "Hàm step nhận tham số n."),
            ("    hero.move_right(n)", "Đi phải n ô - còn thiếu phần đi xuống."),
            ("step(2)", "Gọi hàm với n = 2."),
        ],
        example=[
            ("def greet(name, times):", "Hai tham số."),
            ("    for i in range(times):", ""),
            ('        print("Chào", name)', ""),
            ('greet("An", 2)', "In 2 lần: Chào An."),
        ],
        mistakes=["Định nghĩa hàm có tham số nhưng gọi mà không truyền giá trị → TypeError."],
    ),
    "6-5": Theory(
        concept=[
            "`max(list)` cho phần tử lớn nhất, `min(list)` cho phần tử nhỏ nhất.",
            "Có thể dùng thẳng kết quả trong phép tính: `max(a) - min(a)`.",
        ],
        starter_notes=[
            ("# scores = [7, 9, 4, 10, 6]", "List điểm có sẵn."),
            ("print(sum(scores))", "In tổng điểm."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ("temps = [28, 31, 25, 30]", "Nhiệt độ các ngày."),
            ("print(max(temps), min(temps))", "31 25."),
            ("print(sum(temps) / len(temps))", "28.5 - trung bình."),
        ],
        mistakes=["`max` của list rỗng sẽ báo lỗi."],
    ),
    "7-3": Theory(
        concept=[
            "Cắt chuỗi có 3 phần: `chuoi[dau:cuoi:buoc]`.",
            "Bước 2 lấy cách một ký tự; bước -1 đi ngược từ cuối về đầu, tức là ĐẢO NGƯỢC chuỗi.",
        ],
        starter_notes=[
            ('# scroll = "olleh"', "Mật mã bị viết ngược."),
            ("print(scroll[0])", "In chữ o."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ('word = "abcdef"', ""),
            ("print(word[::2])", "ace - lấy cách một."),
            ("print(word[::-1])", "fedcba - đảo ngược."),
            ('print("level"[::-1] == "level")', "True - từ đối xứng."),
        ],
        mistakes=["Viết `[:-1]` (bỏ ký tự cuối) thay vì `[::-1]` (đảo ngược)."],
    ),
    "7-4": Theory(
        concept=[
            "`.split(dau_tach)` cắt chuỗi thành list: `\"a,b\".split(\",\")` → `[\"a\", \"b\"]`.",
            "Các phần sau khi cắt vẫn là CHUỖI - muốn tính toán phải `int(...)`.",
            "Ngược lại, `\",\".join(list)` nối list chuỗi thành một chuỗi.",
        ],
        starter_notes=[
            ('# route = "2,3,1"', "Chỉ đường dạng chuỗi."),
            ("parts = route", "Chưa cắt chuỗi."),
            ("print(parts)", "In nguyên chuỗi."),
        ],
        example=[
            ('date = "21/11/2026"', ""),
            ('day, month, year = date.split("/")', "Cắt và mở gói 3 phần."),
            ("print(int(year) - 2000)", "26."),
            ('print("-".join(["a", "b", "c"]))', "a-b-c."),
        ],
        mistakes=["Quên `int()` → move_right(\"2\") báo lỗi kiểu."],
    ),
    "7-5": Theory(
        concept=[
            "`.count(x)` đếm số lần x xuất hiện trong chuỗi (dùng được cả với list).",
            "`len(chuoi)` đếm tất cả ký tự, kể cả dấu cách.",
            "Chuỗi còn có `.find(x)` (vị trí đầu tiên của x) và `.replace(a, b)`.",
        ],
        starter_notes=[
            ('# message = "banana bandana"', "Chuỗi có sẵn."),
            ("print(len(message))", "In 14 - tổng số ký tự."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ('text = "hello world"', ""),
            ('print(text.count("o"))', "2."),
            ('print(text.find("world"))', "6."),
            ('print(text.replace("world", "OneSpace"))', "hello OneSpace."),
        ],
        mistakes=["`count` phân biệt hoa thường: \"A\" khác \"a\"."],
    ),
    "8-3": Theory(
        concept=[
            "Lấy phần tử list theo VỊ TRÍ: `ds[0]` là phần tử đầu, `ds[1]` là phần tử thứ hai...",
            "`ds[-1]` là phần tử cuối. `len(ds)` cho số phần tử.",
        ],
        starter_notes=[
            ("# steps = [3, 2, 4]", "List có sẵn."),
            ("print(steps[0])", "In 3 - phần tử đầu tiên."),
            ("print(len(steps))", "In 3 - list có 3 phần tử."),
        ],
        example=[
            ('colors = ["đỏ", "xanh", "vàng"]', ""),
            ("print(colors[1])", "xanh."),
            ("print(colors[-1])", "vàng."),
            ('colors[0] = "tím"', "Sửa phần tử đầu."),
        ],
        mistakes=["`steps[3]` ngoài phạm vi khi list chỉ có 3 phần tử (vị trí 0, 1, 2)."],
    ),
    "8-4": Theory(
        concept=[
            "Bắt đầu với list rỗng `[]`, mỗi vòng lặp dùng `.append(x)` thêm một phần tử vào CUỐI list.",
            "Đây là cách thu thập kết quả hay dùng nhất.",
        ],
        starter_notes=[
            ("xs = []", "List rỗng để ghi chép."),
            ("for gem in hero.find_gems():", "Duyệt từng viên ngọc."),
            ("    pass", "Chưa ghi gì vào xs."),
            ("hero.say(xs)", "Nói ra list - hiện đang rỗng."),
        ],
        example=[
            ("evens = []", ""),
            ("for n in range(1, 7):", ""),
            ("    if n % 2 == 0:", "Số chẵn?"),
            ("        evens.append(n)", "Thêm vào cuối."),
            ("print(evens)", "[2, 4, 6]."),
        ],
        mistakes=["`xs = xs.append(x)` làm xs thành None - append sửa list tại chỗ, không trả về gì."],
    ),
    "8-5": Theory(
        concept=[
            "List có thể chứa tuple: `[(3, 1), (3, 3)]` - mỗi phần tử là một toạ độ.",
            "Mở gói tuple ngay trong vòng for: `for x, y in stops:`.",
        ],
        starter_notes=[
            ("# stops = [(3, 1), (3, 3), (5, 3), (6, 3)]", "List các điểm dừng."),
            ("first = stops[0]", "Lấy tuple đầu tiên (3, 1)."),
            ("print(first[0], first[1])", "In 3 1."),
        ],
        example=[
            ('friends = [("An", 12), ("Bình", 13)]', "List các tuple (tên, tuổi)."),
            ("for name, age in friends:", "Mở gói ngay."),
            ('    print(name, "năm sau", age + 1, "tuổi")', ""),
        ],
        mistakes=["`for x, y in stops[0]:` - duyệt trong một tuple, không phải cả list."],
    ),
    "9-3": Theory(
        concept=[
            "Dict dùng như BẢNG TRA: khoá là tên món, giá trị là giá.",
            "Tra nhiều lần trong vòng lặp và cộng dồn kết quả vào một biến.",
        ],
        starter_notes=[
            ("# prices, basket có sẵn", "Bảng giá (dict) và giỏ hàng (list)."),
            ('print(prices["táo"])', "In 5 - giá một quả táo."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ('points = {"vàng": 3, "bạc": 2, "đồng": 1}', "Điểm huy chương."),
            ('medals = ["vàng", "đồng", "vàng"]', ""),
            ("score = 0", ""),
            ("for m in medals:", ""),
            ("    score += points[m]", "Tra rồi cộng."),
            ("print(score)", "7."),
        ],
        mistakes=["Tra khoá không có (ví dụ \"nho\") → KeyError."],
    ),
    "9-4": Theory(
        concept=[
            "Dict làm SỔ ĐẾM: khoá là thứ cần đếm, giá trị là số lần.",
            "`d.get(k, 0)` trả về `d[k]` nếu có, nếu chưa có thì trả về 0 - không lỗi.",
            "Mẫu hay dùng: `d[k] = d.get(k, 0) + 1`.",
        ],
        starter_notes=[
            ("counts = {}", "Sổ đếm rỗng."),
            ("print(counts)", "In {}."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ('letters = "hello"', ""),
            ("tally = {}", ""),
            ("for ch in letters:", ""),
            ("    tally[ch] = tally.get(ch, 0) + 1", ""),
            ("print(tally)", "{'h': 1, 'e': 1, 'l': 2, 'o': 1}."),
        ],
        mistakes=["`counts[w] += 1` khi w chưa có trong dict → KeyError."],
    ),
    "9-5": Theory(
        concept=[
            "Đổi list sang set để LOẠI phần tử trùng: `set([1, 1, 2])` → `{1, 2}`.",
            "`len(set(ds))` = số giá trị khác nhau trong ds.",
        ],
        starter_notes=[
            ("# visitors có sẵn", "List tên khách, có tên trùng."),
            ("print(len(visitors))", "In 6 - đếm cả lượt trùng."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("rolls = [3, 6, 3, 1, 6, 6]", "Kết quả gieo xúc xắc."),
            ("print(set(rolls))", "{1, 3, 6}."),
            ("print(len(set(rolls)))", "3 mặt khác nhau."),
        ],
        mistakes=["set không giữ thứ tự - không dùng `set(...)[0]` được."],
    ),
    "10-3": Theory(
        concept=[
            "List comprehension: `[bieu_thuc for x in ds]` tạo list mới, mỗi phần tử là bieu_thuc tính từ x.",
            "Gọn hơn hẳn cách viết dài với list rỗng + for + append.",
        ],
        starter_notes=[
            ("squares = []", "List rỗng - bạn thay bằng comprehension."),
            ("print(numbers)", "In [1, 2, 3, 4]."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("prices = [10, 20, 30]", ""),
            ("sale = [p * 0.9 for p in prices]", "Giảm 10%."),
            ("print(sale)", "[9.0, 18.0, 27.0]."),
            ('print([w.upper() for w in ["a", "b"]])', "['A', 'B']."),
        ],
        mistakes=["Viết `for` trước biểu thức: `[for n in ds n*n]` là sai cú pháp."],
    ),
    "10-4": Theory(
        concept=[
            "Comprehension có thể có 2 vòng for, viết theo thứ tự giống for lồng nhau: `[n for row in t for n in row]`.",
            "Kết quả là list \"trải phẳng\" - mọi số nằm trên một hàng.",
        ],
        starter_notes=[
            ("print(table[0])", "In [1, 2] - hàng đầu."),
            ("print(table[2][1])", "In 6 - hàng 2, cột 1."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ('words = [["a", "b"], ["c"]]', ""),
            ("flat = [w for group in words for w in group]", "Trải phẳng."),
            ("print(flat)", "['a', 'b', 'c']."),
        ],
        mistakes=["Đảo thứ tự hai vòng for: `[n for n in row for row in t]` báo lỗi vì row chưa có."],
    ),
    "10-5": Theory(
        concept=[
            "`enumerate(ds)` cho từng cặp (vị trí, phần tử): rất hợp để biết TOẠ ĐỘ trong bản đồ.",
            "Comprehension 2 vòng có thêm `if` để chỉ giữ các ô cần tìm.",
            "Kết quả là list các tuple (x, y) - dùng `move_to` để đi tới.",
        ],
        starter_notes=[
            ("grid = hero.scan()", "Bản đồ: grid[y][x]."),
            ("print(grid[1][7])", "In ô ở hàng 1, cột 7 - là \"gem\"."),
        ],
        example=[
            ('seats = [["", "An"], ["Bình", ""]]', "Sơ đồ chỗ ngồi."),
            ('empty = [(r, c) for r, row in enumerate(seats) for c, name in enumerate(row) if name == ""]', ""),
            ("print(empty)", "[(0, 0), (1, 1)] - các ghế trống."),
        ],
        mistakes=["Nhầm thứ tự (x, y) và (y, x): grid[y][x] nhưng move_to(x, y)."],
    ),
})


# ================================================================ GIAI ĐOẠN 2
PRACTICE_THEORY.update({
    "11-2": Theory(
        concept=[
            "Hiệu tập hợp `a - b`: phần tử có trong a nhưng không có trong b. Viết bằng hàm: `a.difference(b)`.",
            "Thứ tự quan trọng: `a - b` khác `b - a`.",
        ],
        starter_notes=[
            ("# invited, came có sẵn", "Hai list tên."),
            ("print(set(invited))", "In tập các bạn được mời."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ('all_books = {"Toán", "Văn", "Anh", "Sử"}', "Sách cần mang."),
            ('packed = {"Toán", "Anh"}', "Đã cho vào cặp."),
            ("print(all_books - packed)", "{'Văn', 'Sử'} - còn thiếu."),
        ],
        mistakes=["Viết `came - invited` sẽ ra tập rỗng - đảo ngược thứ tự."],
    ),
    "11-3": Theory(
        concept=[
            "`x in tap_hop` trả về True nếu x có trong tập. Dùng được với list, chuỗi, dict, set.",
            "Với set, `in` kiểm tra gần như tức thì dù tập rất lớn - nhanh hơn list nhiều.",
            "`not in` là ngược lại.",
        ],
        starter_notes=[
            ("# tickets (list), valid (set) có sẵn", "Vé khách đưa và tập mã hợp lệ."),
            ('print("A12" == "A12")', "So sánh bằng: True."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ('vowels = {"a", "e", "i", "o", "u"}', ""),
            ("count = 0", ""),
            ('for ch in "education":', ""),
            ("    if ch in vowels:", "Là nguyên âm?"),
            ("        count += 1", ""),
            ("print(count)", "5."),
        ],
        mistakes=["`if ticket == valid` so sánh với cả tập - luôn sai."],
    ),
    "11-4": Theory(
        concept=[
            "Hiệu đối xứng `a ^ b`: phần tử chỉ thuộc MỘT trong hai tập. Hàm tương ứng: `a.symmetric_difference(b)`.",
            "Bằng `(a | b) - (a & b)`: hợp trừ đi phần chung.",
        ],
        starter_notes=[
            ("a = set(stickers_an)", "Sticker của An."),
            ("b = set(stickers_binh)", "Sticker của Bình."),
            ("print(a & b)", "In phần cả hai cùng có: {3, 4}."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ('lop_a = {"bơi", "cờ"}', ""),
            ('lop_b = {"cờ", "vẽ"}', ""),
            ("print(lop_a ^ lop_b)", "{'bơi', 'vẽ'}."),
        ],
        mistakes=["Nhầm `^` là luỹ thừa: trong Python luỹ thừa là `**`."],
    ),
    "11-5": Theory(
        concept=[
            "Tập con: `a <= b` (hay `a.issubset(b)`) đúng khi MỌI phần tử của a đều có trong b.",
            "Tập cha: `a >= b` đúng khi a chứa mọi phần tử của b.",
        ],
        starter_notes=[
            ("# required (set), backpack (list) có sẵn", "Đồ cần thiết và đồ trong ba lô."),
            ("if len(backpack) > 5:", "So số lượng - không đúng ý."),
            ('    hero.say("Đủ đồ")', ""),
            ("else:", ""),
            ('    hero.say("Thiếu đồ")', ""),
            ("hero.move_right(6)", "Đi tới cúp."),
        ],
        example=[
            ('needed = {"bút", "thước"}', ""),
            ('pencil_case = {"bút", "tẩy", "thước"}', ""),
            ("print(needed <= pencil_case)", "True - đủ đồ."),
            ('print({"compa"} <= pencil_case)', "False."),
        ],
        mistakes=["So sánh list với set bằng `<=` sẽ lỗi - đổi cả hai sang set."],
    ),
    "12-3": Theory(
        concept=[
            "`math.ceil(x)` làm tròn LÊN số nguyên gần nhất: `math.ceil(2.1)` = 3.",
            "`math.floor(x)` làm tròn XUỐNG; `round(x)` làm tròn tới số gần nhất.",
            "Bài toán \"cần bao nhiêu xe / hộp / túi\" thường phải làm tròn lên.",
        ],
        starter_notes=[
            ("import math", "Nạp thư viện."),
            ("# students = 45, seats = 16", "Biến có sẵn."),
            ("print(students / seats)", "In 2.8125."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("import math", ""),
            ("pages = 50", "50 trang."),
            ("per_day = 12", "Đọc 12 trang mỗi ngày."),
            ("print(math.ceil(pages / per_day))", "5 ngày mới đọc xong."),
        ],
        mistakes=["Dùng `//` (làm tròn xuống) sẽ thiếu một xe."],
    ),
    "12-4": Theory(
        concept=[
            "`math.pi` ≈ 3.14159. Diện tích hình tròn = π × r², chu vi = 2 × π × r.",
            "`round(x)` làm tròn về số nguyên gần nhất; `round(x, 2)` giữ 2 chữ số thập phân.",
        ],
        starter_notes=[
            ("import math", "Nạp thư viện."),
            ("# r = 5", "Bán kính có sẵn."),
            ("print(r ** 2)", "In 25."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ("import math", ""),
            ("radius = 3", ""),
            ("perimeter = 2 * math.pi * radius", "Chu vi."),
            ("print(round(perimeter, 1))", "18.8."),
        ],
        mistakes=["Viết `math.pi * r * 2` là chu vi chứ không phải diện tích."],
    ),
    "12-5": Theory(
        concept=[
            "Số cách CHỌN k người trong n người (không tính thứ tự) là tổ hợp: `math.comb(n, k)`.",
            "Giai thừa `math.factorial(n)` = 1 × 2 × ... × n - số cách xếp n người thành hàng.",
        ],
        starter_notes=[
            ("import math", "Nạp thư viện."),
            ("print(math.factorial(3))", "In 6 = 1 × 2 × 3."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("import math", ""),
            ("print(math.comb(5, 3))", "10 cách chọn 3 trong 5."),
            ("print(math.factorial(4))", "24 cách xếp 4 bạn."),
        ],
        mistakes=["Đảo tham số `math.comb(2, 6)` ra 0."],
    ),
    "13-3": Theory(
        concept=[
            "`permutations` sinh kết quả \"lười\" - phải bọc `list(...)` mới đếm được bằng `len`.",
            "Với chuỗi, mỗi ký tự là một phần tử: `permutations(\"AB\")` → ('A','B'), ('B','A').",
        ],
        starter_notes=[
            ("from itertools import permutations", "Nạp hàm."),
            ('print(list(permutations("AB")))', "In 2 cách xếp."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ("from itertools import permutations", ""),
            ('podium = list(permutations(["An", "Bình", "Chi"], 2))', "Chọn nhất và nhì."),
            ("print(len(podium))", "6."),
        ],
        mistakes=["`len(permutations(...))` báo lỗi - cần list(...) trước."],
    ),
    "13-4": Theory(
        concept=[
            "`product(a, b)` ghép mọi phần tử của a với mọi phần tử của b - như bảng phối đồ.",
            "Số kết quả = len(a) × len(b). Có thể ghép nhiều list: `product(a, b, c)`.",
        ],
        starter_notes=[
            ("from itertools import product", "Nạp hàm."),
            ('for combo in product([1, 2], ["x"]):', "Ghép 1-x, 2-x."),
            ("    print(combo)", "In từng cặp."),
        ],
        example=[
            ("from itertools import product", ""),
            ('drinks = ["trà", "sữa"]', ""),
            ('sizes = ["S", "M", "L"]', ""),
            ("print(len(list(product(drinks, sizes))))", "6 lựa chọn."),
        ],
        mistakes=["Nhầm với zip: zip ghép theo cặp vị trí, product ghép mọi khả năng."],
    ),
    "13-5": Theory(
        concept=[
            "Duyệt `combinations(ds, 2)` rồi dùng `if` để chỉ đếm các cặp thoả điều kiện.",
            "Cách này gọi là \"vét cạn\": thử hết khả năng - phù hợp khi dữ liệu nhỏ.",
        ],
        starter_notes=[
            ("from itertools import combinations", "Nạp hàm."),
            ("print(list(combinations([1, 2, 5], 2)))", "In 3 cặp."),
        ],
        example=[
            ("from itertools import combinations", ""),
            ("weights = [3, 4, 6]", "Cân nặng 3 kiện hàng."),
            ("light = [p for p in combinations(weights, 2) if sum(p) <= 8]", "Cặp nhẹ."),
            ("print(light)", "[(3, 4)]."),
        ],
        mistakes=["Quên rằng combinations không lấy một phần tử hai lần (không có cặp (5, 5))."],
    ),
    "14-3": Theory(
        concept=[
            "`defaultdict(list)`: dict tự tạo list rỗng khi gặp khoá mới, nên `groups[k].append(x)` không bao giờ KeyError.",
            "`defaultdict(int)` tự tạo số 0 - tiện để đếm.",
        ],
        starter_notes=[
            ("from collections import defaultdict", "Nạp defaultdict."),
            ("groups = defaultdict(list)", "Dict gom nhóm."),
            ('print(groups["rau"])', "In [] - khoá mới tự có list rỗng."),
        ],
        example=[
            ("from collections import defaultdict", ""),
            ('pets = [("mèo", "Mướp"), ("chó", "Vàng"), ("mèo", "Mun")]', ""),
            ("by_kind = defaultdict(list)", ""),
            ("for kind, name in pets:", ""),
            ("    by_kind[kind].append(name)", ""),
            ('print(by_kind["mèo"])', "['Mướp', 'Mun']."),
        ],
        mistakes=["Với dict thường, `d[k].append(x)` khi k chưa có sẽ KeyError."],
    ),
    "14-4": Theory(
        concept=[
            "`Counter(ds).most_common(1)` → `[(giá_trị, số_lần)]`.",
            "Lấy tên: `[0]` lấy tuple, `[0][0]` lấy phần tử đầu của tuple.",
        ],
        starter_notes=[
            ("from collections import Counter", "Nạp Counter."),
            ("print(len(votes))", "In tổng số phiếu: 6."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ("from collections import Counter", ""),
            ('fruits = ["táo", "cam", "táo"]', ""),
            ("top = Counter(fruits).most_common(1)", "[('táo', 2)]."),
            ("print(top[0][0], top[0][1])", "táo 2."),
        ],
        mistakes=["Nhập cả tuple `('Lan', 3)` thay vì chỉ tên → sai kiểu mật mã."],
    ),
    "14-5": Theory(
        concept=[
            "`deque(ds, maxlen=n)` chỉ giữ tối đa n phần tử; thêm vào thì phần tử cũ nhất bị đẩy ra.",
            "Rất hợp để lưu \"n lần gần nhất\" (lịch sử, điểm số, tin nhắn).",
        ],
        starter_notes=[
            ("from collections import deque", "Nạp deque."),
            ("recent = deque(maxlen=3)", "Hàng chỉ giữ 3 phần tử."),
            ("print(recent)", "In deque([], maxlen=3)."),
        ],
        example=[
            ("from collections import deque", ""),
            ("last_two = deque(maxlen=2)", ""),
            ("for page in [1, 2, 3, 4]:", "Lật trang."),
            ("    last_two.append(page)", ""),
            ("print(list(last_two))", "[3, 4]."),
        ],
        mistakes=["Quên `maxlen=` → deque giữ hết mọi phần tử."],
    ),
    "15-2": Theory(
        concept=[
            "`ngay.weekday()` cho thứ trong tuần dạng số: 0 = thứ Hai ... 6 = Chủ nhật.",
            "`ngay.isoweekday()` thì 1 = thứ Hai ... 7 = Chủ nhật.",
        ],
        starter_notes=[
            ("from datetime import date", "Nạp kiểu date."),
            ("print(date.fromisoformat(day))", "In 2026-09-05."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("from datetime import date", ""),
            ('names = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]', ""),
            ("print(names[date(2026, 1, 1).weekday()])", "T5 - thứ Năm."),
        ],
        mistakes=["Tưởng 0 là Chủ nhật như vài nước khác - trong Python 0 là thứ Hai."],
    ),
    "15-3": Theory(
        concept=[
            "`timedelta(days=n)` là khoảng thời gian n ngày. Ngày + timedelta → ngày mới (tự xử lý hết tháng, năm nhuận).",
            "`str(ngay)` hoặc `ngay.isoformat()` cho chuỗi dạng \"2026-02-15\".",
        ],
        starter_notes=[
            ("from datetime import date, timedelta", "Nạp hai kiểu."),
            ("print(timedelta(days=1))", "In 1 day, 0:00:00."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ("from datetime import date, timedelta", ""),
            ("today = date(2026, 12, 25)", ""),
            ("print(today + timedelta(days=10))", "2027-01-04 - tự sang năm mới."),
        ],
        mistakes=["Cộng số thẳng vào ngày (`date + 45`) báo lỗi - phải dùng timedelta."],
    ),
    "15-4": Theory(
        concept=[
            "Trừ hai ngày → khoảng cách; `.days` là số ngày.",
            "Đổi đơn vị: số tuần = số ngày // 7, ngày lẻ = số ngày % 7.",
        ],
        starter_notes=[
            ("from datetime import date", "Nạp kiểu date."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("from datetime import date", ""),
            ("gap = date(2026, 6, 1) - date(2026, 5, 1)", ""),
            ("print(gap.days, gap.days // 7, gap.days % 7)", "31 4 3."),
        ],
        mistakes=["Trừ ngược (sớm - muộn) ra số âm."],
    ),
    "15-5": Theory(
        concept=[
            "`ngay.strftime(mau)` đổi ngày thành chuỗi theo mẫu tuỳ ý.",
            "Mã hay dùng: `%d` ngày (2 chữ số), `%m` tháng, `%Y` năm 4 chữ số, `%H:%M` giờ:phút.",
        ],
        starter_notes=[
            ("from datetime import date", "Nạp kiểu date."),
            ("print(date.fromisoformat(day))", "In 2026-11-20."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ("from datetime import date", ""),
            ("d = date(2026, 3, 8)", ""),
            ('print(d.strftime("%d-%m"))', "08-03."),
            ('print(d.strftime("Năm %Y"))', "Năm 2026."),
        ],
        mistakes=["`%y` (chữ thường) chỉ có 2 chữ số năm: 26 thay vì 2026."],
    ),
})


# ================================================================ GIAI ĐOẠN 3 - 5
PRACTICE_THEORY.update({
    "16-4": Theory(
        concept=[
            "Chia cho 0 gây `ZeroDivisionError` - chương trình dừng nếu không bắt lỗi.",
            "Đặt try/except BÊN TRONG vòng lặp để một phần tử hỏng không làm hỏng cả vòng lặp.",
        ],
        starter_notes=[
            ("total = 0", "Biến tổng."),
            ("for a, b in pairs:", "Duyệt từng cặp."),
            ("    total += a // b", "Cặp (5, 0) sẽ gây lỗi chia cho 0."),
            ("print(total)", "Không bao giờ chạy tới."),
        ],
        example=[
            ("ages = [12, 0, 15]", "Một tuổi bị nhập sai là 0."),
            ("for age in ages:", ""),
            ("    try:", ""),
            ("        print(100 // age)", ""),
            ("    except ZeroDivisionError:", ""),
            ('        print("Bỏ qua tuổi 0")', "Vòng lặp vẫn chạy tiếp."),
        ],
        mistakes=["Đặt try bên ngoài vòng for: gặp lỗi là thoát luôn cả vòng lặp."],
    ),
    "16-5": Theory(
        concept=[
            "`raise LoaiLoi(\"thông báo\")` tự tạo ra lỗi - dùng khi dữ liệu sai mà hàm không xử lý được.",
            "Hàm chỉ báo lỗi; nơi GỌI hàm quyết định xử lý thế nào bằng try/except.",
        ],
        starter_notes=[
            ("def check(n):", "Hàm kiểm tra số bước."),
            ("    return n", "Chưa kiểm tra gì - số âm cũng cho qua."),
            ("for n in moves:", "Duyệt từng số bước."),
            ("    hero.move_right(check(n))", "Đi theo số bước đã kiểm tra."),
        ],
        example=[
            ("def set_age(age):", ""),
            ("    if age < 0:", "Tuổi âm là vô lý."),
            ('        raise ValueError("Tuổi không được âm")', "Báo lỗi."),
            ("    return age", ""),
            ("try:", ""),
            ("    set_age(-5)", ""),
            ("except ValueError as error:", "Bắt lỗi và đọc thông báo."),
            ("    print(error)", "Tuổi không được âm."),
        ],
        mistakes=["Viết `return ValueError(...)` - trả về lỗi chứ không ném lỗi."],
    ),
    "17-4": Theory(
        concept=[
            "PHƯƠNG THỨC là hàm viết trong class, tham số đầu luôn là `self` - chính đồ vật đó.",
            "Gọi phương thức: `doi_tuong.ten(...)` - Python tự truyền doi_tuong vào self.",
            "Phương thức có thể đọc và sửa thuộc tính: `self.total += amount`.",
        ],
        starter_notes=[
            ("class Wallet:", "Class chiếc ví."),
            ("    def __init__(self):", "Chạy khi tạo ví."),
            ("        self.total = 0", "Ví mới có 0 đồng."),
            ("w = Wallet()", "Tạo một chiếc ví."),
            ("print(w.total)", "In 0."),
        ],
        example=[
            ("class Plant:", ""),
            ("    def __init__(self):", ""),
            ("        self.height = 1", ""),
            ("    def water(self):", "Phương thức tưới cây."),
            ("        self.height += 2", ""),
            ("tree = Plant()", ""),
            ("tree.water()", ""),
            ("print(tree.height)", "3."),
        ],
        mistakes=["Quên `self` ở tham số đầu: gọi phương thức sẽ báo TypeError."],
    ),
    "17-5": Theory(
        concept=[
            "`__len__(self)` quyết định `len(doi_tuong)` trả về bao nhiêu - phải return số nguyên.",
            "Các magic method khác: `__str__` (print), `__add__` (+), `__eq__` (==), `__lt__` (<).",
        ],
        starter_notes=[
            ("class Team:", "Class đội."),
            ("    def __init__(self, members):", "Nhận danh sách thành viên."),
            ("        self.members = members", "Cất danh sách."),
            ("team = Team(members)", "Tạo đội."),
            ("print(team.members)", "In danh sách."),
        ],
        example=[
            ("class Playlist:", ""),
            ("    def __init__(self, songs):", ""),
            ("        self.songs = songs", ""),
            ("    def __len__(self):", ""),
            ("        return len(self.songs)", ""),
            ('print(len(Playlist(["A", "B", "C"])))', "3."),
        ],
        mistakes=["Gọi `len(team)` khi chưa có `__len__` → TypeError."],
    ),
    "18-2": Theory(
        concept=[
            "Bài ôn tập: kết hợp dict tra vũ khí, vòng lặp hạ quái, move_to và try/except mở cửa kẹt.",
            "Chia việc thành từng bước nhỏ, chạy thử sau mỗi bước.",
        ],
        starter_notes=[
            ('weakness = {"robot": "hammer", "barrel": "axe", "cannon": "bow"}', "Bảng vũ khí."),
            ("for enemy in hero.find_enemies():", "Duyệt từng quái."),
            ('    print(enemy["type"], enemy["x"], enemy["y"])', "In thông tin để xem."),
        ],
        example=[
            ('sounds = {"mèo": "meo", "chó": "gâu"}', ""),
            ('for pet in ["chó", "mèo"]:', ""),
            ("    print(sounds[pet])", "gâu, meo."),
            ("while True:", "Thử tới khi được."),
            ("    try:", ""),
            ('        value = int("5")', ""),
            ("        break", ""),
            ("    except ValueError:", ""),
            ("        pass", ""),
        ],
        mistakes=["Đi tới cửa trước khi hạ hết quái - quái chặn đường."],
    ),
    "18-3": Theory(
        concept=[
            "Hàm có thể trả về cả một list - kết hợp tốt với list comprehension.",
            "`ch.isdigit()` kiểm tra ký tự có phải chữ số.",
        ],
        starter_notes=[
            ("def digits(text):", "Hàm lấy các chữ số."),
            ("    return []", "Đang trả về list rỗng."),
            ("print(digits(scroll))", "In [] - chưa có gì."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("def vowels(word):", ""),
            ('    return [ch for ch in word if ch in "aeiou"]', ""),
            ('print(vowels("python"))', "['o']."),
            ('print(len(vowels("banana")))', "3."),
        ],
        mistakes=["Quên `int(ch)` → sum không cộng được các chuỗi."],
    ),
    "18-4": Theory(
        concept=[
            "Bài ôn tập class + `__iter__`: tự tạo một lộ trình mà `for` / `hero.follow` duyệt được.",
            "Trong `__iter__` có thể dùng vòng lặp để tạo list, rồi `return iter(list)`.",
        ],
        starter_notes=[
            ("class Route:", "Class lộ trình."),
            ("    def __init__(self, size):", "Nhận số bậc."),
            ("        self.size = size", "Cất số bậc."),
            ('hero.follow(["right", "down"])', "Đi theo một list cố định - chỉ 1 bậc."),
        ],
        example=[
            ("class Countdown:", ""),
            ("    def __init__(self, start):", ""),
            ("        self.start = start", ""),
            ("    def __iter__(self):", ""),
            ("        numbers = []", ""),
            ("        for n in range(self.start, 0, -1):", ""),
            ("            numbers.append(n)", ""),
            ("        return iter(numbers)", ""),
            ("print(list(Countdown(3)))", "[3, 2, 1]."),
        ],
        mistakes=["Trả về list thay vì iter(list) → TypeError."],
    ),
    "18-5": Theory(
        concept=[
            "Bài ôn tập: try/except để bỏ qua dữ liệu hỏng, set để bỏ dữ liệu trùng.",
            "`except ValueError: pass` - bắt lỗi rồi bỏ qua, không làm gì.",
        ],
        starter_notes=[
            ("values = []", "List các số."),
            ("for text in candidates:", "Duyệt từng chuỗi."),
            ("    values.append(int(text))", "Chuỗi \"x\" sẽ gây ValueError."),
        ],
        example=[
            ('inputs = ["3", "ba", "3"]', ""),
            ("seen = set()", ""),
            ("for text in inputs:", ""),
            ("    try:", ""),
            ("        seen.add(int(text))", ""),
            ("    except ValueError:", ""),
            ("        pass", ""),
            ("print(seen)", "{3}."),
        ],
        mistakes=["Dùng list thay set: số 4 bị cộng hai lần."],
    ),
    "19-3": Theory(
        concept=[
            "`max(ds, key=ham)` tìm phần tử có ham(phần tử) lớn nhất. `sorted(ds, key=ham)` sắp xếp theo ham.",
            "`lambda p: p[1]` là hàm lấy phần tử thứ hai của tuple - viết ngay tại chỗ.",
        ],
        starter_notes=[
            ("print(sorted(players))", "Sắp xếp theo tên (phần tử đầu tuple)."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ('words = ["kiwi", "táo", "dưa hấu"]', ""),
            ("print(max(words, key=lambda w: len(w)))", "dưa hấu - từ dài nhất."),
            ("print(sorted(words, key=lambda w: len(w)))", "Ngắn tới dài."),
        ],
        mistakes=["Nhập cả tuple (\"Bình\", 9) thay vì chỉ tên."],
    ),
    "19-4": Theory(
        concept=[
            "`enumerate(ds)` cho cặp (vị trí, phần tử) - không cần tự đếm vị trí.",
            "`break` dừng vòng lặp ngay khi tìm thấy.",
            "Với list có sẵn còn có `ds.index(x)` tìm vị trí đầu tiên của x.",
        ],
        starter_notes=[
            ("for step in route:", "Duyệt từng bước nhưng không biết vị trí."),
            ("    print(step)", "In từng bước."),
        ],
        example=[
            ('queue = ["An", "Bình", "Chi"]', ""),
            ("for i, name in enumerate(queue, start=1):", "Đánh số từ 1."),
            ('    print(i, name)', "1 An, 2 Bình, 3 Chi."),
        ],
        mistakes=["Quên break: vị trí cuối cùng gặp \"down\" sẽ ghi đè vị trí đầu."],
    ),
    "19-5": Theory(
        concept=[
            "`any(dieu_kien for x in ds)` → True nếu ÍT NHẤT MỘT phần tử thoả.",
            "`all(dieu_kien for x in ds)` → True nếu MỌI phần tử thoả.",
        ],
        starter_notes=[
            ("if temps[0] > 30:", "Chỉ xét ngày đầu tiên."),
            ('    hero.say("Nóng")', ""),
            ("else:", ""),
            ('    hero.say("Mát")', ""),
            ("hero.move_right(5)", "Đi tới cúp."),
        ],
        example=[
            ("scores = [8, 9, 7]", ""),
            ("print(all(s >= 5 for s in scores))", "True - đều trên trung bình."),
            ("print(any(s == 10 for s in scores))", "False - không có điểm 10."),
        ],
        mistakes=["`any(temps) > 30` sai: any trả về True/False, không phải số."],
    ),
    "20-3": Theory(
        concept=[
            "`re.findall(mau, text)` trả về list MỌI chỗ khớp; `re.search` chỉ tìm chỗ đầu tiên.",
            "Mẫu `\\d+`: một hoặc nhiều chữ số liền nhau.",
        ],
        starter_notes=[
            ("import re", "Nạp regex."),
            ('print(re.search(r"\\d+", letter).group())', "In 3 - chỉ số đầu tiên."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("import re", ""),
            ('order = "2 bánh, 10 kẹo, 1 sữa"', ""),
            ('numbers = re.findall(r"\\d+", order)', "['2', '10', '1']."),
            ("print(sum(int(n) for n in numbers))", "13."),
        ],
        mistakes=["Cộng thẳng list chuỗi → TypeError; phải int từng phần tử."],
    ),
    "20-4": Theory(
        concept=[
            "Lượng từ trong regex: `{3}` đúng 3 lần, `+` một hoặc nhiều, `*` không hoặc nhiều, `?` có hoặc không.",
            "`[A-Z]` một chữ in hoa, `[0-9]` hay `\\d` một chữ số.",
            "`re.fullmatch` khớp TOÀN BỘ chuỗi; `re.search` chỉ cần khớp một phần.",
        ],
        starter_notes=[
            ("import re", "Nạp regex."),
            ("print(len(codes))", "In 4 - tổng số mã."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ("import re", ""),
            ('phones = ["0912345678", "123", "0987654321"]', ""),
            ('ok = [p for p in phones if re.fullmatch(r"0\\d{9}", p)]', "Số 10 chữ số bắt đầu bằng 0."),
            ("print(ok)", "Hai số hợp lệ."),
        ],
        mistakes=["Dùng re.search thì \"EF-7890\" cũng có thể khớp một phần - nên dùng fullmatch."],
    ),
    "20-5": Theory(
        concept=[
            "Thẻ XML có thể chứa nhiều thuộc tính: `the.get(\"weapon\")` đọc từng thuộc tính.",
            "Dữ liệu điều khiển game (bản đồ, lệnh) thường được lưu bằng XML hoặc JSON.",
        ],
        starter_notes=[
            ("import xml.etree.ElementTree as ET", "Nạp bộ đọc XML."),
            ("root = ET.fromstring(room_xml)", "Đọc chuỗi XML."),
            ('print(len(root.findall("enemy")))', "In 3 - số thẻ enemy."),
        ],
        example=[
            ("import xml.etree.ElementTree as ET", ""),
            ("data = '<menu><dish name=\"phở\" price=\"40\"/><dish name=\"bún\" price=\"35\"/></menu>'", ""),
            ("root = ET.fromstring(data)", ""),
            ('for dish in root.findall("dish"):', ""),
            ('    print(dish.get("name"), int(dish.get("price")))', ""),
        ],
        mistakes=["Quên đổi toạ độ sang int → attack_target báo lỗi."],
    ),
    "21-3": Theory(
        concept=[
            "Closure nhớ biến của hàm ngoài: hàm `multiply` tạo trong `make_multiplier(3)` luôn nhớ k = 3.",
            "Mỗi lần gọi hàm ngoài tạo ra một hàm mới với giá trị riêng: `double = make_multiplier(2)`.",
        ],
        starter_notes=[
            ("def make_multiplier(k):", "Nhà máy tạo hàm nhân với k."),
            ("    pass", "Chưa tạo gì."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("def make_adder(bonus):", ""),
            ("    def add(score):", ""),
            ("        return score + bonus", "Nhớ bonus."),
            ("    return add", ""),
            ("plus_five = make_adder(5)", ""),
            ("print(plus_five(10))", "15."),
        ],
        mistakes=["Quên `return` trong hàm con → kết quả là None."],
    ),
    "21-4": Theory(
        concept=[
            "Decorator có thể làm thêm việc TRƯỚC (hoặc SAU) khi gọi hàm gốc - ví dụ ghi log.",
            "`func.__name__` là tên của hàm dạng chuỗi.",
        ],
        starter_notes=[
            ("def announce(func):", "Decorator báo hiệu."),
            ("    return func", "Đang trả hàm gốc - chưa thêm gì."),
            ("@announce", "Gắn decorator vào hop."),
            ("def hop():", "Chiêu nhảy gai."),
            ("    hero.move_up()", ""),
            ("    hero.move_right(2)", ""),
            ("    hero.move_down()", ""),
            ("hero.move_right(2)", "Tới trước gai đầu."),
            ("hop()", "Nhảy 1 lần."),
        ],
        example=[
            ("def log(func):", ""),
            ("    def wrapper():", ""),
            ('        print("Gọi", func.__name__)', "Làm thêm trước."),
            ("        func()", ""),
            ("    return wrapper", ""),
            ("@log", ""),
            ("def jump():", ""),
            ('    print("Nhảy!")', ""),
            ("jump()", "Gọi jump rồi Nhảy!"),
        ],
        mistakes=["Gọi `func` (không ngoặc) trong wrapper - hàm gốc không chạy."],
    ),
    "21-5": Theory(
        concept=[
            "Decorator có tham số cần 3 tầng: hàm nhận tham số → trả về decorator → decorator trả về wrapper.",
            "`@repeat(4)` = gọi `repeat(4)` trước để lấy decorator, rồi dùng decorator đó bọc hàm.",
        ],
        starter_notes=[
            ("def repeat(times):", "Nhận số lần lặp."),
            ("    pass", "Chưa làm gì."),
            ("def stair():", "Một bậc thang."),
            ("    hero.move_right()", ""),
            ("    hero.move_down()", ""),
            ("stair()", "Chỉ xuống 1 bậc."),
        ],
        example=[
            ("def shout(times):", ""),
            ("    def decorator(func):", ""),
            ("        def wrapper():", ""),
            ("            for i in range(times):", ""),
            ("                func()", ""),
            ("        return wrapper", ""),
            ("    return decorator", ""),
            ("@shout(2)", ""),
            ("def cheer():", ""),
            ('    print("Cố lên!")', ""),
            ("cheer()", "In 2 lần."),
        ],
        mistakes=["Viết `@repeat` không có (4) → times trở thành chính hàm stair."],
    ),
    "22-3": Theory(
        concept=[
            "Mảng NumPy có sẵn các phép thống kê: `.mean()` trung bình, `.max()`, `.min()`, `.std()` độ lệch chuẩn.",
            "Kết quả là số của NumPy - đổi sang int / float khi cần.",
        ],
        starter_notes=[
            ("import numpy as np", "Nạp NumPy."),
            ("data = np.array(temps)", "Tạo mảng nhiệt độ."),
            ("print(data.max())", "In 28."),
        ],
        example=[
            ("import numpy as np", ""),
            ("heights = np.array([150, 160, 155])", ""),
            ("print(heights.mean())", "155.0."),
            ("print(heights - 100)", "[50 60 55] - trừ mọi phần tử cùng lúc."),
        ],
        mistakes=["`data.mean` (không ngoặc) là chính hàm, chưa phải kết quả."],
    ),
    "22-4": Theory(
        concept=[
            "So sánh với mảng cho mảng True/False: `arr > 5` → `[False, True, ...]`.",
            "Lọc bằng mảng True/False: `arr[arr > 5]` chỉ giữ phần tử ứng với True.",
            "Đếm nhanh: `(arr > 5).sum()` vì True được tính là 1.",
        ],
        starter_notes=[
            ("import numpy as np", "Nạp NumPy."),
            ("arr = np.array(scores)", "Mảng điểm."),
            ("print(arr > 5)", "In mảng True/False."),
        ],
        example=[
            ("import numpy as np", ""),
            ("ages = np.array([10, 15, 12, 17])", ""),
            ("print(ages[ages >= 13])", "[15 17]."),
            ("print((ages < 13).sum())", "2."),
        ],
        mistakes=["Dùng `and`/`or` với mảng → lỗi; NumPy dùng `&` và `|` kèm ngoặc."],
    ),
    "22-5": Theory(
        concept=[
            "`axis=0` tính theo cột (gộp các hàng), `axis=1` tính theo hàng (gộp các cột).",
            "`.argmax()` trả về VỊ TRÍ của phần tử lớn nhất, `.argmin()` vị trí nhỏ nhất.",
        ],
        starter_notes=[
            ("import numpy as np", "Nạp NumPy."),
            ("table = np.array(sales)", "Bảng 3 × 3."),
            ("print(table.sum())", "In tổng cả bảng."),
        ],
        example=[
            ("import numpy as np", ""),
            ("grades = np.array([[8, 6], [9, 7]])", "2 bạn, 2 môn."),
            ("print(grades.sum(axis=1))", "[14 16] - tổng mỗi bạn."),
            ("print(grades.sum(axis=1).argmax())", "1 - bạn thứ hai cao hơn."),
        ],
        mistakes=["Nhầm axis=0 và axis=1 - in thử ra để kiểm tra."],
    ),
    "23-3": Theory(
        concept=[
            "`NameError: name 'x' is not defined` - Python không biết tên x: gõ sai tên hoặc dùng trước khi tạo.",
            "Cách sửa: so sánh tên ở chỗ tạo biến và chỗ dùng biến, từng chữ cái một.",
        ],
        starter_notes=[
            ("steps = 6", "Tạo biến steps."),
            ('message = "Tới rồi"', "Tạo biến message."),
            ("hero.move_right(step)", "Tên dùng ở đây có khớp tên đã tạo không?"),
            ("hero.say(mesage)", "Đếm số chữ s."),
        ],
        example=[
            ('color = "xanh"', "Tạo đúng tên."),
            ("print(color)", "Dùng đúng tên - chạy tốt."),
            ("count = 3", ""),
            ("print(count + 1)", "4."),
        ],
        mistakes=["Sửa tên ở chỗ dùng nhưng quên chỗ khác cũng gõ sai."],
    ),
    "23-4": Theory(
        concept=[
            "`TypeError` - dùng sai kiểu: nối chuỗi với số, đưa chuỗi vào nơi cần số...",
            "Thông báo lỗi thường nói rõ hai kiểu bị trộn (str và int).",
        ],
        starter_notes=[
            ("gems = len(hero.find_gems())", "gems là số."),
            ('hero.say("Có " + gems + " ngọc")', "Nối chuỗi với số - lỗi."),
            ('hero.move_right("4")', "Số bước đang là chuỗi."),
        ],
        example=[
            ("pages = 12", ""),
            ('print("Đọc " + str(pages) + " trang")', "Đổi số sang chuỗi."),
            ('print(int("8") + 2)', "10 - đổi chuỗi sang số."),
        ],
        mistakes=["Sửa xong một lỗi rồi dừng - chạy lại để tìm lỗi tiếp theo."],
    ),
    "23-5": Theory(
        concept=[
            "Vòng `while` dừng khi điều kiện SAI. Nếu biến trong điều kiện không bao giờ đổi, vòng lặp chạy mãi.",
            "Game sẽ dừng chương trình chạy quá lâu và báo lỗi - dấu hiệu của vòng lặp vô hạn.",
        ],
        starter_notes=[
            ("count = 0", "Biến đếm bắt đầu từ 0."),
            ("while count < 5:", "Lặp khi count nhỏ hơn 5."),
            ("    hero.move_right()", "count không bao giờ đổi..."),
        ],
        example=[
            ("water = 0", ""),
            ("while water < 3:", ""),
            ('    print("Rót thêm")', ""),
            ("    water += 1", "Thay đổi biến điều kiện."),
            ('print("Đầy cốc")', "Chạy sau 3 vòng."),
        ],
        mistakes=["Tăng biến đếm nhưng đặt NGOÀI vòng lặp (thụt lề sai)."],
    ),
})


# ================================================================ BÀI 6: THỬ THÁCH VẬT THỂ MỚI
OBJECTS_NOTE = (
    "Vật thể mới: thùng gỗ (\"box\") đập bằng `hero.attack(huong)`; chìa khoá (\"key\") đi qua là nhặt, "
    "`hero.keys` đếm số chìa; cửa khoá (\"lock\") mở bằng `hero.unlock(huong)`; rương báu (\"chest\") mở bằng "
    "`hero.open_chest(huong)` - mỗi rương thưởng thêm xu."
)

PRACTICE_THEORY.update({
    "1-6": Theory(
        concept=[
            "`hero.attack(\"right\")` không chỉ đánh quái - nó còn ĐẬP VỠ thùng gỗ ở ô bên phải.",
            "Thùng vỡ rồi thì ô đó thành đường đi bình thường.",
            OBJECTS_NOTE,
        ],
        starter_notes=[
            ("hero.move_right(1)", "Đi tới đứng sát thùng."),
            ("# thùng gỗ chắn đường!", "Ghi chú: cần phá thùng trước khi đi tiếp."),
        ],
        example=[
            ("hero.move_down()", "Đi xuống sát thùng phía dưới."),
            ('hero.attack("down")', "Đập thùng phía dưới."),
            ("hero.move_down(2)", "Đi qua chỗ thùng vừa vỡ."),
        ],
        mistakes=["Đi thẳng vào thùng: hero đụng thùng và đứng lại."],
    ),
    "2-6": Theory(
        concept=[
            "Đi qua ô chìa khoá là tự nhặt. `hero.keys` cho biết đang có mấy chìa.",
            "`hero.unlock(\"right\")` dùng 1 chìa để mở cửa khoá bên phải.",
            "Biến có thể dùng trong phép tính: `steps + 1`.",
        ],
        starter_notes=[
            ("steps = 1", "Biến số bước - cần đổi."),
            ("hero.move_right(steps)", "Đi theo số bước trong biến."),
        ],
        example=[
            ("hero.move_up(2)", "Đi lên, nhặt chìa trên đường."),
            ("print(hero.keys)", "In 1."),
            ('hero.unlock("up")', "Mở cửa khoá phía trên."),
        ],
        mistakes=["Gọi unlock khi chưa có chìa → lỗi ValueError."],
    ),
    "3-6": Theory(
        concept=[
            "`hero.look(huong)` trả về cả \"box\" (thùng), \"chest\" (rương), \"lock\" (cửa khoá), \"key\" (chìa).",
            "Có thể viết nhiều câu `if` liên tiếp để kiểm tra nhiều hướng.",
        ],
        starter_notes=[
            ("hero.move_right(2)", "Đi tới ngã ba."),
            ('if hero.look("up") == "chest":', "Nếu phía trên là rương..."),
            ("    pass", "...chưa làm gì - hãy mở rương."),
        ],
        example=[
            ('if hero.look("left") == "box":', "Bên trái có thùng?"),
            ('    hero.attack("left")', "Đập thùng."),
            ('if hero.look("down") == "chest":', "Bên dưới có rương?"),
            ('    hero.open_chest("down")', "Mở rương."),
        ],
        mistakes=["Mở rương bằng attack: rương không vỡ, phải dùng open_chest."],
    ),
    "4-6": Theory(
        concept=[
            "Khi một cặp lệnh lặp lại nhiều lần (đập thùng, bước lên), hãy đưa chúng vào vòng `for`.",
            "Thùng có dấu X (Q) chứa ngọc: đập vỡ thì ngọc rơi ra ngay tại ô đó.",
        ],
        starter_notes=[
            ('hero.attack("right")', "Đập thùng bên phải."),
            ("hero.move_right()", "Bước lên chỗ thùng vừa vỡ."),
        ],
        example=[
            ("for i in range(3):", "Lặp 3 lần."),
            ('    hero.attack("down")', "Đập thùng phía dưới."),
            ("    hero.move_down()", "Bước xuống."),
        ],
        mistakes=["Đặt hero.move_right() ngoài vòng lặp - chỉ bước được 1 lần."],
    ),
    "5-6": Theory(
        concept=[
            "`range()` chỉ nhận số nguyên: `range(\"2\")` báo TypeError, phải `range(int(\"2\"))`.",
            "Mỗi lượt lặp làm trọn một việc: nhặt chìa, mở cửa, bước qua.",
        ],
        starter_notes=[
            ('# doors = "2"', "Số cửa ghi bằng chuỗi."),
            ("for i in range(doors):", "range với chuỗi sẽ lỗi."),
            ("    hero.move_right()", "Mới chỉ bước, chưa mở cửa."),
        ],
        example=[
            ('times = "3"', ""),
            ("for i in range(int(times)):", "Đổi chuỗi sang số trước."),
            ('    print("Lượt", i + 1)', "Lượt 1, 2, 3."),
        ],
        mistakes=["Lặp quá số cửa → unlock khi không còn cửa / không còn chìa."],
    ),
    "6-6": Theory(
        concept=[
            "Gói một chuỗi thao tác lặp lại (bước, đập thùng, bước) thành hàm để gọi nhiều lần.",
            "Hàm giúp code ngắn - dễ đạt sao \"code gọn\".",
        ],
        starter_notes=[
            ("def smash():", "Hàm phá thùng."),
            ("    hero.move_right()", "Mới có bước đi - thiếu phần đập thùng."),
            ("smash()", "Gọi hàm một lần."),
        ],
        example=[
            ("def climb():", "Hàm leo một bậc."),
            ('    hero.attack("up")', "Đập thùng phía trên."),
            ("    hero.move_up()", "Leo lên."),
            ("climb()", ""),
            ("climb()", "Leo 2 bậc."),
        ],
        mistakes=["Định nghĩa hàm nhưng quên gọi."],
    ),
    "7-6": Theory(
        concept=[
            "Chỉ số âm đếm từ cuối chuỗi: `s[-1]` là ký tự cuối, `s[-2:]` là 2 ký tự cuối.",
            "Rương báu mở bằng `hero.open_chest(huong)` - mỗi rương mở được thưởng thêm xu khi qua màn.",
        ],
        starter_notes=[
            ('# note = "Mật mã ở cuối thư: 42"', "Biến note có sẵn."),
            ("print(note[0])", "In chữ M - ký tự đầu."),
        ],
        example=[
            ('code = "ABC-2026"', ""),
            ("print(code[-4:])", "2026."),
            ("print(int(code[-4:]) + 1)", "2027."),
        ],
        mistakes=["`note[-2]` chỉ lấy MỘT ký tự (số 4), không phải 42."],
    ),
    "8-6": Theory(
        concept=[
            "`hero.find_objects(\"box\")` trả về list dict {\"x\", \"y\"} của các thùng (dùng được với \"chest\", \"key\", \"lock\"...).",
            "Ô bên trái của (x, y) là (x - 1, y): đứng đó rồi `attack(\"right\")`.",
        ],
        starter_notes=[
            ('boxes = hero.find_objects("box")', "List toạ độ các thùng."),
            ("print(boxes)", "In ra để xem."),
        ],
        example=[
            ('for chest in hero.find_objects("chest"):', "Duyệt các rương."),
            ('    hero.move_to(chest["x"] + 1, chest["y"])', "Đứng bên PHẢI rương."),
            ('    hero.open_chest("left")', "Mở rương bên trái."),
        ],
        mistakes=["Lấy danh sách ngọc TRƯỚC khi đập thùng - thiếu các viên rơi ra sau."],
    ),
    "9-6": Theory(
        concept=[
            "`d.items()` cho từng cặp (khoá, giá trị) của dict: `for k, v in d.items():`.",
            "Dict làm \"kế hoạch\": khoá là hướng, giá trị là việc cần làm.",
        ],
        starter_notes=[
            ("for direction in plan:", "Duyệt dict chỉ cho khoá (hướng)."),
            ("    print(direction)", "In up, down, right."),
        ],
        example=[
            ('menu = {"phở": 40, "bún": 35}', ""),
            ("for dish, price in menu.items():", "Cả tên lẫn giá."),
            ('    print(dish, price, "nghìn")', ""),
        ],
        mistakes=["Duyệt `for direction in plan` rồi quên tra `plan[direction]`."],
    ),
    "10-6": Theory(
        concept=[
            "Comprehension trên bản đồ: `[(x, y) for y, row in enumerate(grid) for x, t in enumerate(row) if t == \"chest\"]`.",
            "Ô ngay DƯỚI rương (x, y) là (x, y + 1) - đứng đó và mở hướng \"up\".",
        ],
        starter_notes=[
            ("grid = hero.scan()", "Bản đồ grid[y][x]."),
            ("print(grid[1])", "Hàng 1 - nơi có các rương."),
        ],
        example=[
            ('board = [["box", "floor"], ["floor", "box"]]', ""),
            ('boxes = [(x, y) for y, row in enumerate(board) for x, t in enumerate(row) if t == "box"]', ""),
            ("print(boxes)", "[(0, 0), (1, 1)]."),
        ],
        mistakes=["Đi tới đúng ô rương bằng move_to → báo lỗi vì rương chắn đường."],
    ),
    "11-6": Theory(
        concept=[
            "`thu in tap_hop` kiểm tra rất nhanh - hợp để hỏi \"thứ này có nằm trong nhóm được phép không?\".",
            "Vòng while + if: mỗi vòng chỉ làm MỘT việc (đập hoặc bước), rồi nhìn lại.",
        ],
        starter_notes=[
            ('while hero.look("right") != "exit":', "Lặp tới khi cổng ở ngay bên phải."),
            ("    hero.move_right()", "Chỉ bước - sẽ đụng thùng."),
        ],
        example=[
            ('edible = {"táo", "cam"}', ""),
            ('for food in ["táo", "đá", "cam"]:', ""),
            ("    if food in edible:", ""),
            ('        print("Ăn", food)', "Ăn táo, Ăn cam."),
        ],
        mistakes=["Đập cả ngọc rơi ra: ngọc không thuộc breakable, cứ bước lên là nhặt."],
    ),
    "12-6": Theory(
        concept=[
            "Kết hợp nhiều vật thể: chìa → cửa khoá → cửa mật mã.",
            "`int(math.sqrt(50))` lấy phần nguyên của căn bậc hai: 7.",
        ],
        starter_notes=[
            ("import math", "Nạp thư viện."),
            ("print(math.sqrt(4))", "In 2.0."),
        ],
        example=[
            ("import math", ""),
            ("side = math.sqrt(30)", "≈ 5.477."),
            ("print(int(side), math.ceil(side))", "5 6."),
        ],
        mistakes=["Quên mở cửa khoá trước khi đi tới cửa mật mã."],
    ),
    "13-6": Theory(
        concept=[
            "`hero.try_code` trả về True khi đúng - dùng `break` để dừng thử.",
            "Thứ tự công việc quan trọng: thùng → cửa màu → rương → cúp.",
        ],
        starter_notes=[
            ("from itertools import permutations", "Nạp hàm hoán vị."),
            ('hero.attack("right")', "Đập thùng đầu tiên."),
        ],
        example=[
            ("from itertools import permutations", ""),
            ('for order in permutations(["A", "B"]):', ""),
            ("    print(order)", "('A', 'B'), ('B', 'A')."),
        ],
        mistakes=["Dùng enter_code để thử: sai là mất máu - try_code thì không."],
    ),
    "14-6": Theory(
        concept=[
            "`Counter(...)` đếm được mọi loại ô của bản đồ cùng lúc.",
            "Trải phẳng list lồng nhau bằng generator: `(t for row in grid for t in row)`.",
        ],
        starter_notes=[
            ("from collections import Counter", "Nạp Counter."),
            ("grid = hero.scan()", "Bản đồ."),
            ("print(grid[1])", "In hàng 1."),
        ],
        example=[
            ("from collections import Counter", ""),
            ('rows = [["a", "b"], ["a", "a"]]', ""),
            ("print(Counter(x for row in rows for x in row))", "Counter({'a': 3, 'b': 1})."),
        ],
        mistakes=["Đưa thẳng grid vào Counter → lỗi vì list không làm khoá được."],
    ),
    "15-6": Theory(
        concept=[
            "Ôn lại `date.fromisoformat(...)` và `.weekday()` (0 = thứ Hai).",
            "Mở rương bằng `hero.open_chest(huong)`.",
        ],
        starter_notes=[
            ("from datetime import date", "Nạp kiểu date."),
            ("print(day)", "In chuỗi ngày."),
        ],
        example=[
            ("from datetime import date", ""),
            ("print(date(2026, 1, 1).weekday())", "3 - thứ Năm."),
        ],
        mistakes=["Gọi .weekday() trên chuỗi → AttributeError; phải đổi sang date trước."],
    ),
    "16-6": Theory(
        concept=[
            "`hero.unlock` khi chưa có chìa ném `ValueError` - bắt lỗi để xử lý thay vì để chương trình dừng.",
            "Trong `except`: sửa tình huống (đi lấy chìa) rồi thử lại.",
        ],
        starter_notes=[
            ('hero.unlock("right")', "Chưa có chìa → ValueError, chương trình dừng."),
            ("hero.move_right(4)", "Không chạy tới được."),
        ],
        example=[
            ("try:", ""),
            ('    value = int("abc")', ""),
            ("except ValueError:", "Không đổi được..."),
            ("    value = 0", "...dùng giá trị mặc định."),
            ("print(value)", "0."),
        ],
        mistakes=["Bắt nhầm loại lỗi (ví dụ except TypeError) - lỗi vẫn làm dừng chương trình."],
    ),
    "17-6": Theory(
        concept=[
            "Class gom dữ liệu (số rương đã mở) và hành động (open) vào một chỗ.",
            "Phương thức có thể gọi lệnh của hero và cập nhật thuộc tính của self.",
        ],
        starter_notes=[
            ("class Explorer:", "Class nhà thám hiểm."),
            ("    def __init__(self):", "Chạy khi tạo."),
            ("        self.opened = 0", "Chưa mở rương nào."),
        ],
        example=[
            ("class Counter2:", ""),
            ("    def __init__(self):", ""),
            ("        self.value = 0", ""),
            ("    def click(self):", ""),
            ("        self.value += 1", ""),
            ("c = Counter2()", ""),
            ("c.click()", ""),
            ("print(c.value)", "1."),
        ],
        mistakes=["Quên tăng self.opened → nói sai số rương."],
    ),
    "18-6": Theory(
        concept=[
            "Một vòng lặp \"thông minh\": mỗi bước nhìn ô bên phải rồi chọn hành động phù hợp (if / elif / else).",
            "Có thể kiểm tra thêm hướng khác (phía dưới) trong cùng vòng lặp.",
        ],
        starter_notes=[
            ('while hero.look("right") != "exit":', "Lặp tới khi cổng bên phải."),
            ("    hero.move_right()", "Chỉ bước - sẽ kẹt ở thùng."),
        ],
        example=[
            ("for thing in [\"box\", \"floor\", \"lock\"]:", ""),
            ('    if thing == "box":', ""),
            ('        print("đập")', ""),
            ('    elif thing == "lock":', ""),
            ('        print("mở khoá")', ""),
            ("    else:", ""),
            ('        print("bước")', ""),
        ],
        mistakes=["Viết các if riêng lẻ: một vòng có thể vừa đập vừa bước, làm lệch vị trí."],
    ),
    "19-6": Theory(
        concept=[
            "`sorted(ds, key=lambda c: c[\"x\"])` xếp list dict theo khoá \"x\".",
            "`reverse=True` để xếp ngược (từ phải sang trái).",
        ],
        starter_notes=[
            ('chests = hero.find_objects("chest")', "List rương."),
            ("print(chests)", "In ra để xem."),
        ],
        example=[
            ('pets = [{"name": "Mèo", "age": 3}, {"name": "Chó", "age": 1}]', ""),
            ('youngest = sorted(pets, key=lambda p: p["age"])[0]', ""),
            ('print(youngest["name"])', "Chó."),
        ],
        mistakes=["key=c[\"x\"] (thiếu lambda) → lỗi NameError."],
    ),
    "20-6": Theory(
        concept=[
            "Một regex có thể lấy chữ (`\\w+`) hoặc số (`\\d+`); dùng nhiều lần cho nhiều thông tin.",
            "Kết quả `.group(1)` luôn là chuỗi - số cần `int()`, hướng dùng thẳng được.",
        ],
        starter_notes=[
            ("import re", "Nạp regex."),
            ("print(letter)", "In mật thư."),
        ],
        example=[
            ("import re", ""),
            ('msg = "Gặp ở phòng B lúc 15 giờ"', ""),
            ('room = re.search(r"phòng (\\w+)", msg).group(1)', "'B'."),
            ('hour = int(re.search(r"lúc (\\d+)", msg).group(1))', "15."),
        ],
        mistakes=["Quên dấu cách trong mẫu (\"hướng(\\w+)\") → không khớp."],
    ),
    "21-6": Theory(
        concept=[
            "Closure tạo ra các \"bùa\" giống nhau nhưng nhớ hướng khác nhau.",
            "Hàm cũng có thể nằm trong list: `[f, g]` rồi gọi lần lượt.",
        ],
        starter_notes=[
            ("def make_opener(direction):", "Nhà máy tạo bùa mở rương."),
            ("    pass", "Chưa tạo gì."),
        ],
        example=[
            ("def make_greeter(name):", ""),
            ("    def greet():", ""),
            ('        print("Chào", name)', ""),
            ("    return greet", ""),
            ('for g in [make_greeter("An"), make_greeter("Bình")]:', ""),
            ("    g()", "Chào An, Chào Bình."),
        ],
        mistakes=["Gọi make_opener(\"up\") mà không gọi hàm nó trả về → rương chưa mở."],
    ),
    "22-6": Theory(
        concept=[
            "`np.array(bang).max()` tìm số lớn nhất trong cả bảng 2 chiều.",
            "Kết quả là số của NumPy - `int(...)` để dùng làm mật mã.",
        ],
        starter_notes=[
            ("import numpy as np", "Nạp NumPy."),
            ("print(np.array(weights).shape)", "In (2, 2)."),
        ],
        example=[
            ("import numpy as np", ""),
            ("scores = np.array([[5, 9], [7, 6]])", ""),
            ("print(scores.max(), scores.min())", "9 5."),
        ],
        mistakes=["max(weights) với list lồng nhau so sánh cả hàng - không ra số lớn nhất."],
    ),
    "23-6": Theory(
        concept=[
            "Gỡ lỗi chương trình có vật thể: kiểm tra THỨ TỰ (nhặt chìa trước khi mở), TÊN lệnh, và HƯỚNG.",
            "Đọc thông báo lỗi ở Bảng tin để biết dòng nào sai, sửa từng lỗi rồi chạy lại.",
        ],
        starter_notes=[
            ('hero.unlock("right")', "Chưa có chìa mà đã mở cửa."),
            ("hero.move_right(2)", "Đi qua chìa."),
            ('hero.open_chests("down")', "Tên lệnh có đúng không?"),
            ('hero.attack("left")', "Thùng nằm ở hướng nào?"),
            ("hero.move_right(3)", "Đi tới cúp."),
        ],
        example=[
            ("hero.move_right()", "Ví dụ code ĐÚNG thứ tự: nhặt chìa..."),
            ('hero.unlock("right")', "...rồi mới mở cửa."),
        ],
        mistakes=["Sửa xong một lỗi là dừng - hãy chạy lại để tìm lỗi tiếp theo."],
    ),
})

THEORY.update(PRACTICE_THEORY)


# ======================================================================
# heroes.py
# ======================================================================

Color = tuple[int, int, int]

# Các màu được phép đổi của từng nhân vật gốc; da, mắt, viền giữ nguyên.
RECOLOR_PALETTES: dict[int, tuple[Color, ...]] = {
    # Bạn Nhỏ: tóc, cà vạt, áo vest.
    1: ((161, 71, 68), (132, 51, 70), (204, 48, 72), (156, 27, 77), (72, 71, 91)),
    # Rô-bốt: vỏ máy.
    2: ((225, 202, 51), (206, 139, 22), (247, 236, 138), (186, 87, 11)),
    # Cáo: bộ lông.
    3: ((210, 97, 47), (178, 46, 32), (230, 141, 65)),
}


@dataclass(frozen=True)
class HeroStyle:
    number: int
    name: str
    description: str
    base: int
    hue_shift: float = 0.0
    saturation: float = 1.0
    brightness: float = 1.0
    price: int = 0

    @property
    def item_id(self) -> str:
        return f"skin{self.number}"

    @property
    def is_recolored(self) -> bool:
        return (self.hue_shift, self.saturation, self.brightness) != (0.0, 1.0, 1.0)


HEROES: list[HeroStyle] = [
    HeroStyle(1, "Bạn Nhỏ", "Cậu học trò thích phiêu lưu.", 1),
    HeroStyle(2, "Rô-bốt Vàng", "Rô-bốt tinh nghịch.", 2),
    HeroStyle(3, "Cáo Lửa", "Cáo nhanh nhẹn.", 3),
    HeroStyle(4, "Bạn Tóc Xanh", "Tóc xanh biển, áo xanh.", 1, hue_shift=205),
    HeroStyle(5, "Bạn Tóc Tím", "Thích màu tím mộng mơ.", 1, hue_shift=270),
    HeroStyle(6, "Bạn Tóc Vàng", "Tóc vàng như nắng.", 1, hue_shift=45, brightness=1.35),
    HeroStyle(7, "Rô-bốt Lá", "Rô-bốt chạy bằng năng lượng xanh.", 2, hue_shift=55),
    HeroStyle(8, "Rô-bốt Biển", "Rô-bốt lặn biển.", 2, hue_shift=150),
    HeroStyle(9, "Rô-bốt Hồng", "Rô-bốt kẹo bông.", 2, hue_shift=270, saturation=0.8),
    HeroStyle(10, "Rô-bốt Bạc", "Vỏ thép sáng bóng.", 2, saturation=0.08, brightness=1.05),
    HeroStyle(11, "Cáo Tuyết", "Cáo trắng xứ lạnh.", 3, saturation=0.12, brightness=1.3),
    HeroStyle(12, "Cáo Đêm", "Cáo xanh tím ban đêm.", 3, hue_shift=225),
    HeroStyle(13, "Rô-bốt Bóng Đêm", "Nhân vật hiếm: vỏ đen huyền bí.", 2, saturation=0.25, brightness=0.45, price=150),
    HeroStyle(14, "Cáo Ngọc", "Nhân vật hiếm: lông xanh ngọc.", 3, hue_shift=150, price=200),
    HeroStyle(15, "Bạn Nhỏ Hoàng Kim", "Nhân vật hiếm: vest vàng óng.", 1, hue_shift=48, saturation=1.4,
              brightness=1.6, price=260),
]
HEROES_BY_NUMBER: dict[int, HeroStyle] = {hero.number: hero for hero in HEROES}
FREE_HEROES: list[HeroStyle] = [hero for hero in HEROES if hero.price == 0]
RARE_HEROES: list[HeroStyle] = [hero for hero in HEROES if hero.price > 0]


def recolor(color: Color, style: HeroStyle) -> Color:
    """Đổi một màu theo kiểu của nhân vật (xoay màu, chỉnh độ đậm và độ sáng)."""
    red, green, blue = (channel / 255 for channel in color)
    hue, saturation, value = colorsys.rgb_to_hsv(red, green, blue)
    hue = (hue + style.hue_shift / 360) % 1.0
    saturation = min(1.0, saturation * style.saturation)
    value = min(1.0, value * style.brightness)
    new_red, new_green, new_blue = colorsys.hsv_to_rgb(hue, saturation, value)
    return round(new_red * 255), round(new_green * 255), round(new_blue * 255)


def color_map(style: HeroStyle) -> dict[Color, Color]:
    """Bảng đổi màu cho sprite của nhân vật gốc."""
    if not style.is_recolored:
        return {}
    return {color: recolor(color, style) for color in RECOLOR_PALETTES[style.base]}


# ======================================================================
# themes.py
# ======================================================================

Color = tuple[int, int, int]
NO_TINT: Color = (255, 255, 255)
NO_ADD: Color = (0, 0, 0)


@dataclass(frozen=True)
class MapTheme:
    name: str
    floor: tuple[int, int]
    wall: tuple[int, int]
    floor_multiply: Color = NO_TINT
    wall_multiply: Color = NO_TINT
    add: Color = NO_ADD
    # Màu nền khung bản đồ (phía sau ô gạch).
    backdrop: Color = (24, 28, 40)
    # Hiệu ứng không khí: "snow", "dust", "fireflies", "sparkle", "leaves" hoặc "" (không có).
    ambient: str = ""


THEMES: list[MapTheme] = [
    MapTheme("Sân gạch", floor=(1, 1), wall=(1, 4), ambient="leaves"),
    MapTheme("Đồi đất đỏ", floor=(7, 1), wall=(7, 8), backdrop=(40, 26, 22), ambient="dust"),
    MapTheme("Rừng rêu", floor=(1, 1), wall=(1, 5), floor_multiply=(170, 220, 150), wall_multiply=(150, 205, 140),
             backdrop=(20, 36, 26), ambient="fireflies"),
    MapTheme("Phòng thép", floor=(12, 1), wall=(1, 5), backdrop=(30, 34, 44)),
    MapTheme("Sa mạc", floor=(7, 1), wall=(7, 8), floor_multiply=(255, 225, 150), wall_multiply=(255, 220, 160),
             add=(50, 40, 10), backdrop=(52, 42, 24), ambient="dust"),
    MapTheme("Băng tuyết", floor=(12, 1), wall=(1, 4), floor_multiply=(210, 235, 255), wall_multiply=(170, 210, 255),
             add=(20, 26, 36), backdrop=(26, 36, 52), ambient="snow"),
    MapTheme("Lâu đài tím", floor=(12, 1), wall=(1, 4), floor_multiply=(225, 205, 255), wall_multiply=(190, 150, 255),
             backdrop=(30, 20, 44), ambient="sparkle"),
    MapTheme("Hang đêm", floor=(1, 1), wall=(1, 4), floor_multiply=(120, 120, 190), wall_multiply=(110, 110, 160),
             backdrop=(12, 12, 24), ambient="fireflies"),
]

# World -> kiểu bản đồ: mỗi giai đoạn đổi cảnh, các World liền nhau không trùng kiểu.
WORLD_THEMES: dict[int, int] = {
    1: 0, 2: 2, 3: 1, 4: 0, 5: 2, 6: 3, 7: 4, 8: 1,
    9: 5, 10: 3, 11: 6, 12: 4, 13: 7, 14: 5, 15: 2, 16: 6,
    17: 3, 18: 7, 19: 1, 20: 5, 21: 6, 22: 4, 23: 7,
}


def theme_for_world(world_number: int) -> MapTheme:
    return THEMES[WORLD_THEMES.get(world_number, 0)]


# ======================================================================
# rewards.py
# ======================================================================

STAR_COINS = 10
WORLD_CHEST_COINS = 50
# Xu trong mỗi rương báu mở được TRONG màn (chỉ tính lần đầu).
LOOT_COINS = 5
DEFAULT_SKIN = "skin1"

RANKS: list[tuple[int, str]] = [
    (0, "Tân binh"),
    (15, "Học việc"),
    (45, "Hiệp sĩ code"),
    (90, "Chiến binh thuật toán"),
    (160, "Pháp sư Python"),
    (260, "Huyền thoại OneSpace"),
]


@dataclass(frozen=True)
class ShopItem:
    id: str
    name: str
    description: str
    price: int
    kind: str  # "skin", "heart", "shield"
    skin_number: int = 1
    requires: str | None = None


SKIN_ITEMS: list[ShopItem] = [
    ShopItem(hero.item_id, hero.name, hero.description, hero.price, "skin", skin_number=hero.number)
    for hero in HEROES
]
UPGRADE_ITEMS: list[ShopItem] = [
    ShopItem("heart1", "Tim thêm I", "+1 máu tối đa ở các màn thường.", 150, "heart"),
    ShopItem("heart2", "Tim thêm II", "+1 máu tối đa nữa (cần Tim thêm I).", 300, "heart", requires="heart1"),
    ShopItem("shield", "Khiên gỗ", "Đỡ giúp đòn đầu tiên trong mỗi màn thường.", 250, "shield"),
]
# Cửa hàng chỉ bán nhân vật hiếm và vật phẩm; nhân vật miễn phí chọn ở màn Chọn nhân vật.
SHOP_ITEMS: list[ShopItem] = [item for item in SKIN_ITEMS if item.price] + UPGRADE_ITEMS
ITEMS_BY_ID: dict[str, ShopItem] = {item.id: item for item in [*SKIN_ITEMS, *UPGRADE_ITEMS]}


@dataclass
class RewardSummary:
    stars: tuple[bool, bool, bool]
    new_stars: int
    coins: int
    chest_world: int | None = None
    loot_coins: int = 0
    old_rank: str = ""
    new_rank: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def rank_up(self) -> bool:
        return self.old_rank != self.new_rank


def par_for(level_id: str) -> int:
    return PAR.get(level_id, 99)


def star_flags(result: RunResult, level_id: str) -> tuple[bool, bool, bool]:
    won = result.won
    return (won, won and result.damage_taken == 0, won and result.code_lines <= par_for(level_id))


def star_goals(level_id: str) -> list[str]:
    return ["Qua màn", "Không mất máu", f"Code gọn: tối đa {par_for(level_id)} dòng"]


def rank_for(total_stars: int) -> tuple[str, int | None]:
    """(rank name, stars needed for the next rank or None at the top)."""
    name = RANKS[0][1]
    next_threshold: int | None = None
    for threshold, rank_name in RANKS:
        if total_stars >= threshold:
            name = rank_name
        elif next_threshold is None:
            next_threshold = threshold
    return name, next_threshold


def total_stars(progress: object) -> int:
    return sum(getattr(progress, "stars", {}).values())


def apply_win(progress: object, level: Level, world_levels: list[Level], world_number: int,
              flags: tuple[bool, bool, bool], chests_opened: int = 0) -> RewardSummary:
    """Record a win: keep the best stars, pay coins for NEW stars and open the world chest once."""
    stars: dict[str, int] = progress.stars  # type: ignore[attr-defined]
    earned = sum(flags)
    previous = stars.get(level.id, 0)
    old_rank = rank_for(total_stars(progress))[0]
    new_stars = max(0, earned - previous)
    stars[level.id] = max(previous, earned)
    progress.completed.add(level.id)  # type: ignore[attr-defined]
    coins = new_stars * STAR_COINS
    loot: dict[str, int] = progress.loot  # type: ignore[attr-defined]
    new_loot = max(0, chests_opened - loot.get(level.id, 0))
    loot[level.id] = max(loot.get(level.id, 0), chests_opened)
    loot_coins = new_loot * LOOT_COINS
    coins += loot_coins

    chest_world = None
    completed = progress.completed  # type: ignore[attr-defined]
    chests: set[int] = progress.chests  # type: ignore[attr-defined]
    if world_number not in chests and all(lv.id in completed for lv in world_levels):
        chests.add(world_number)
        coins += WORLD_CHEST_COINS
        chest_world = world_number

    progress.coins += coins  # type: ignore[attr-defined]
    new_rank = rank_for(total_stars(progress))[0]
    return RewardSummary(flags, new_stars, coins, chest_world, loot_coins, old_rank, new_rank)


# ---------------------------------------------------------------- shop
def bonus_hp(progress: object) -> int:
    owned: set[str] = progress.owned  # type: ignore[attr-defined]
    return sum(1 for item_id in owned if item_id in ITEMS_BY_ID and ITEMS_BY_ID[item_id].kind == "heart")


def has_shield(progress: object) -> bool:
    return "shield" in progress.owned  # type: ignore[attr-defined]


def can_buy(progress: object, item: ShopItem) -> tuple[bool, str]:
    owned: set[str] = progress.owned  # type: ignore[attr-defined]
    if item.id in owned or item.price == 0:
        return False, "Đã có"
    if item.requires and item.requires not in owned:
        return False, f"Cần {ITEMS_BY_ID[item.requires].name}"
    if progress.coins < item.price:  # type: ignore[attr-defined]
        return False, f"Thiếu {item.price - progress.coins} xu"  # type: ignore[attr-defined]
    return True, ""


def buy(progress: object, item: ShopItem) -> bool:
    ok, _ = can_buy(progress, item)
    if not ok:
        return False
    progress.coins -= item.price  # type: ignore[attr-defined]
    progress.owned.add(item.id)  # type: ignore[attr-defined]
    if item.kind == "skin":
        progress.skin = item.id  # type: ignore[attr-defined]
    return True


def equip_skin(progress: object, item_id: str) -> bool:
    item = ITEMS_BY_ID.get(item_id)
    if item is None or item.kind != "skin":
        return False
    if item.price and item_id not in progress.owned:  # type: ignore[attr-defined]
        return False
    progress.skin = item_id  # type: ignore[attr-defined]
    return True


def skin_number(progress: object) -> int:
    item = ITEMS_BY_ID.get(getattr(progress, "skin", DEFAULT_SKIN), SKIN_ITEMS[0])
    return item.skin_number


# ======================================================================
# display.py
# ======================================================================

class Viewport:
    def __init__(self) -> None:
        self.scale = 1.0
        self.offset = (0, 0)

    def fit(self, canvas_size: tuple[int, int], window_size: tuple[int, int]) -> tuple[int, int]:
        self.scale = min(window_size[0] / canvas_size[0], window_size[1] / canvas_size[1])
        scaled_size = (max(1, int(canvas_size[0] * self.scale)), max(1, int(canvas_size[1] * self.scale)))
        self.offset = ((window_size[0] - scaled_size[0]) // 2, (window_size[1] - scaled_size[1]) // 2)
        return scaled_size

    def to_logical(self, position: tuple[int, int]) -> tuple[int, int]:
        return (
            int((position[0] - self.offset[0]) / self.scale),
            int((position[1] - self.offset[1]) / self.scale),
        )


VIEWPORT = Viewport()


def mouse_pos() -> tuple[int, int]:
    """Mouse position in canvas coordinates."""
    return VIEWPORT.to_logical(pygame.mouse.get_pos())


def to_logical_event(event: pygame.event.Event) -> pygame.event.Event:
    if hasattr(event, "pos") and event.type in (
        pygame.MOUSEBUTTONDOWN,
        pygame.MOUSEBUTTONUP,
        pygame.MOUSEMOTION,
    ):
        data = dict(event.dict)
        data["pos"] = VIEWPORT.to_logical(event.pos)
        return pygame.event.Event(event.type, data)
    return event


# ======================================================================
# completion.py
# ======================================================================

@dataclass(frozen=True)
class Suggestion:
    label: str
    insert: str
    hint: str
    cursor_back: int = 0


def _call(name: str, params: str, hint: str) -> Suggestion:
    """A function/method: inserts `name()` and puts the cursor inside the brackets when it takes arguments."""
    return Suggestion(f"{name}({params})", f"{name}()", hint, 1 if params else 0)


def _plain(name: str, hint: str) -> Suggestion:
    return Suggestion(name, name, hint)


HERO_MEMBERS: list[Suggestion] = [
    _call("move_right", "steps", "Đi sang phải (mặc định 1 bước)"),
    _call("move_left", "steps", "Đi sang trái"),
    _call("move_up", "steps", "Đi lên"),
    _call("move_down", "steps", "Đi xuống"),
    _call("move_to", "x, y", "Tự tìm đường tới ô (x, y)"),
    _call("say", "text", "Hero nói một câu"),
    _call("look", "direction", "Xem ô bên cạnh: \"right\", \"left\", \"up\", \"down\""),
    _call("attack", "direction, weapon", "Đánh ô bên cạnh"),
    _call("attack_target", "x, y, weapon", "Đi tới cạnh quái rồi đánh"),
    _call("enter_code", "code", "Nhập mật mã cho cửa bên cạnh"),
    _call("try_code", "code", "Thử mật mã, không mất máu"),
    _call("open_door", "direction", "Mở cửa kẹt (có thể lỗi DoorJammed)"),
    _call("find_gems", "", "Danh sách ngọc còn trên bản đồ"),
    _call("find_enemies", "", "Danh sách quái"),
    _call("scan", "", "Bản đồ dạng list lồng nhau grid[y][x]"),
    _call("use", "item", "Dùng vật có thuộc tính power để hồi máu"),
    _call("move_by", "vector", "Đi theo đối tượng có x, y"),
    _call("follow", "path", "Đi theo từng hướng trong lộ trình"),
    _call("unlock", "direction", "Dùng 1 chìa mở cửa khoá bên cạnh"),
    _call("open_chest", "direction", "Mở rương báu bên cạnh (+xu)"),
    _call("find_objects", "name", "Toạ độ vật thể: \"box\", \"chest\", \"key\", \"lock\"..."),
    _plain("position", "Toạ độ hiện tại (x, y)"),
    _plain("exit_position", "Toạ độ cổng (x, y)"),
    _plain("hp", "Số máu hiện tại"),
    _plain("x", "Cột hiện tại"),
    _plain("y", "Hàng hiện tại"),
    _plain("gems_collected", "Số ngọc đã nhặt"),
    _plain("keys", "Số chìa khoá đang có"),
]

BUILTIN_FUNCTIONS: list[Suggestion] = [
    _call("print", "...", "In ra Bảng tin"),
    _call("len", "x", "Đếm số phần tử"),
    _call("range", "n", "Dãy số 0 .. n-1"),
    _call("int", "x", "Đổi sang số nguyên"),
    _call("str", "x", "Đổi sang chuỗi"),
    _call("float", "x", "Đổi sang số thực"),
    _call("bool", "x", "Đổi sang True/False"),
    _call("list", "x", "Tạo / đổi sang list"),
    _call("tuple", "x", "Tạo / đổi sang tuple"),
    _call("dict", "", "Tạo dict"),
    _call("set", "x", "Tạo tập hợp (bỏ phần tử trùng)"),
    _call("sum", "numbers", "Tổng các số"),
    _call("min", "values", "Giá trị nhỏ nhất"),
    _call("max", "values", "Giá trị lớn nhất"),
    _call("sorted", "values", "Sắp xếp, trả về list mới"),
    _call("abs", "x", "Giá trị tuyệt đối"),
    _call("round", "x, digits", "Làm tròn"),
    _call("enumerate", "values", "Ghép số thứ tự với phần tử"),
    _call("zip", "a, b", "Ghép từng cặp phần tử"),
    _call("map", "function, values", "Áp hàm lên mọi phần tử"),
    _call("filter", "function, values", "Giữ phần tử thoả điều kiện"),
    _call("isinstance", "value, type", "Kiểm tra kiểu dữ liệu"),
    _call("iter", "values", "Tạo iterator"),
    _call("next", "iterator", "Lấy phần tử tiếp theo"),
    _plain("DoorJammed", "Lỗi cửa kẹt (dùng với except)"),
    _plain("ValueError", "Lỗi giá trị sai, ví dụ int(\"abc\")"),
    _plain("KeyError", "Lỗi khoá không có trong dict"),
    _plain("IndexError", "Lỗi vị trí ngoài list"),
    _plain("TypeError", "Lỗi sai kiểu dữ liệu"),
    _plain("Exception", "Mọi loại lỗi"),
]

KEYWORD_INSERTS: dict[str, tuple[str, str]] = {
    "for": ("for ", "Vòng lặp: for x in ...:"),
    "while": ("while ", "Lặp khi điều kiện còn đúng"),
    "if": ("if ", "Nếu điều kiện đúng thì..."),
    "elif": ("elif ", "Nếu không thì xét điều kiện khác"),
    "else": ("else:", "Trường hợp còn lại"),
    "def": ("def ", "Định nghĩa hàm"),
    "return": ("return ", "Trả kết quả về từ hàm"),
    "class": ("class ", "Định nghĩa class"),
    "import": ("import ", "Nạp thư viện"),
    "from": ("from ", "from thư_viện import tên"),
    "try": ("try:", "Thử chạy, bắt lỗi bằng except"),
    "except": ("except ", "Xử lý khi có lỗi"),
    "finally": ("finally:", "Luôn chạy dù có lỗi hay không"),
    "lambda": ("lambda ", "Hàm ngắn: lambda x: ..."),
    "break": ("break", "Thoát vòng lặp"),
    "continue": ("continue", "Sang vòng lặp tiếp theo"),
    "pass": ("pass", "Không làm gì"),
    "in": ("in ", "Thuộc / duyệt trong"),
    "and": ("and ", "Và"),
    "or": ("or ", "Hoặc"),
    "not": ("not ", "Phủ định"),
    "True": ("True", "Đúng"),
    "False": ("False", "Sai"),
    "None": ("None", "Không có giá trị"),
    "with": ("with ", "Khối with"),
    "raise": ("raise ", "Tự ném lỗi"),
}
KEYWORDS: list[Suggestion] = [
    Suggestion(name, insert, hint) for name, (insert, hint) in KEYWORD_INSERTS.items()
]

MODULE_MEMBERS: dict[str, list[Suggestion]] = {
    "math": [
        _call("sqrt", "x", "Căn bậc hai"),
        _plain("pi", "Số π"),
        _call("gcd", "a, b", "Ước chung lớn nhất"),
        _call("lcm", "a, b", "Bội chung nhỏ nhất"),
        _call("hypot", "a, b", "Cạnh huyền √(a² + b²)"),
        _call("ceil", "x", "Làm tròn lên"),
        _call("floor", "x", "Làm tròn xuống"),
        _call("factorial", "n", "Giai thừa n!"),
        _call("comb", "n, k", "Số tổ hợp chập k của n"),
        _call("pow", "x, y", "Luỹ thừa"),
    ],
    "re": [
        _call("search", "pattern, text", "Tìm chỗ khớp đầu tiên"),
        _call("findall", "pattern, text", "Tìm mọi chỗ khớp"),
        _call("match", "pattern, text", "Khớp từ đầu chuỗi"),
        _call("sub", "pattern, new, text", "Thay thế"),
        _call("split", "pattern, text", "Tách chuỗi"),
    ],
    "numpy": [
        _call("array", "values", "Tạo mảng NumPy"),
        _call("sum", "array", "Tổng mọi phần tử"),
        _call("dot", "a, b", "Nhân ma trận / tích vô hướng"),
        _call("matmul", "a, b", "Nhân ma trận"),
        _call("zeros", "shape", "Mảng toàn số 0"),
        _call("ones", "shape", "Mảng toàn số 1"),
        _call("arange", "n", "Dãy số dạng mảng"),
        _call("mean", "array", "Trung bình"),
        _call("max", "array", "Lớn nhất"),
        _call("min", "array", "Nhỏ nhất"),
        _call("trace", "array", "Tổng đường chéo"),
        _call("transpose", "array", "Đổi hàng thành cột"),
    ],
    "itertools": [
        _call("permutations", "values, k", "Mọi cách sắp xếp (hoán vị)"),
        _call("combinations", "values, k", "Mọi cách chọn k phần tử (tổ hợp)"),
        _call("product", "a, b", "Mọi cặp ghép"),
        _call("chain", "a, b", "Nối nhiều dãy"),
    ],
    "collections": [
        _call("Counter", "values", "Đếm số lần xuất hiện"),
        _call("deque", "values", "Hàng đợi hai đầu"),
        _call("defaultdict", "list", "Dict có giá trị mặc định"),
    ],
    "datetime": [
        _call("date", "year, month, day", "Một ngày"),
        _call("timedelta", "days=...", "Khoảng thời gian"),
        _call("datetime", "...", "Ngày và giờ"),
    ],
    "date": [
        _call("fromisoformat", "\"2026-01-01\"", "Đổi chuỗi năm-tháng-ngày thành ngày"),
        _call("today", "", "Hôm nay"),
    ],
    "xml.etree.ElementTree": [
        _call("fromstring", "text", "Đọc XML từ chuỗi"),
    ],
}

COMMON_METHODS: list[Suggestion] = [
    _call("append", "x", "list: thêm vào cuối"),
    _call("pop", "", "list: lấy ra phần tử cuối"),
    _call("insert", "index, x", "list: chèn vào vị trí"),
    _call("remove", "x", "list: xoá phần tử"),
    _call("sort", "", "list: sắp xếp tại chỗ"),
    _call("reverse", "", "list: đảo ngược"),
    _call("index", "x", "Vị trí của phần tử"),
    _call("count", "x", "Đếm số lần xuất hiện"),
    _call("keys", "", "dict: các khoá"),
    _call("values", "", "dict: các giá trị"),
    _call("items", "", "dict: các cặp (khoá, giá trị)"),
    _call("get", "key", "dict: lấy giá trị theo khoá / XML: đọc thuộc tính"),
    _call("add", "x", "set: thêm phần tử"),
    _call("union", "other", "set: hợp"),
    _call("intersection", "other", "set: giao"),
    _call("difference", "other", "set: hiệu"),
    _call("upper", "", "chuỗi: viết HOA"),
    _call("lower", "", "chuỗi: viết thường"),
    _call("title", "", "chuỗi: Viết Hoa Đầu Từ"),
    _call("strip", "", "chuỗi: bỏ khoảng trắng hai đầu"),
    _call("split", "sep", "chuỗi: tách thành list"),
    _call("join", "values", "chuỗi: nối list thành chuỗi"),
    _call("replace", "old, new", "chuỗi: thay thế"),
    _call("startswith", "text", "chuỗi: bắt đầu bằng"),
    _call("isdigit", "", "chuỗi: toàn chữ số?"),
    _call("format", "...", "chuỗi: định dạng"),
    _call("popleft", "", "deque: lấy người đầu hàng"),
    _call("appendleft", "x", "deque: thêm vào đầu"),
    _call("rotate", "n", "deque: xoay hàng"),
    _call("most_common", "n", "Counter: phổ biến nhất"),
    _call("group", "n", "regex: lấy nhóm đã khớp"),
    _call("findall", "tag", "XML: mọi thẻ con"),
    _call("find", "tag", "XML: thẻ con đầu tiên"),
    _call("sum", "", "NumPy: tổng"),
    _plain("shape", "NumPy: (số hàng, số cột)"),
    _call("mean", "", "NumPy: trung bình"),
    _plain("days", "timedelta: số ngày"),
    _call("weekday", "", "date: thứ trong tuần (0 = thứ Hai)"),
    _plain("tag", "XML: tên thẻ"),
]

IMPORTABLE = ["math", "itertools", "collections", "datetime", "re", "numpy", "xml.etree.ElementTree", "functools", "statistics"]

IDENTIFIER_BEFORE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*$")
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
IMPORT_AS = re.compile(r"^\s*import\s+([\w.]+)(?:\s+as\s+(\w+))?")
FROM_IMPORT = re.compile(r"^\s*from\s+([\w.]+)\s+import\s+(.+)")
MAX_SUGGESTIONS = 7


def _in_text(line: str, column: int) -> bool:
    quote: str | None = None
    for char in line[:column]:
        if quote:
            if char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char == "#":
            return True
    return quote is not None


def _module_aliases(lines: list[str]) -> dict[str, str]:
    """Map names used in code (np, math, date, ET...) to the module they come from."""
    aliases: dict[str, str] = {}
    for line in lines:
        match = IMPORT_AS.match(line)
        if match:
            module, alias = match.group(1), match.group(2)
            aliases[alias or module.split(".")[0]] = module
            continue
        match = FROM_IMPORT.match(line)
        if match:
            for name in match.group(2).split(","):
                name = name.strip().split(" as ")[-1].strip()
                if name:
                    aliases[name] = name if name in MODULE_MEMBERS else match.group(1)
    return aliases


def _names_in_code(lines: list[str], skip_row: int) -> set[str]:
    names: set[str] = set()
    for index, line in enumerate(lines):
        code = line.split("#", 1)[0]
        code = re.sub(r"\"[^\"]*\"|'[^']*'", "", code)
        for name in IDENTIFIER.findall(code):
            if index == skip_row:
                continue
            if len(name) >= 2 and not keyword.iskeyword(name):
                names.add(name)
    return names


def suggest(
    lines: list[str],
    row: int,
    column: int,
    extra_names: list[str] | None = None,
) -> tuple[int, list[Suggestion]]:
    """Return (column where the typed word starts, suggestions)."""
    line = lines[row]
    before = line[:column]
    if _in_text(line, column):
        return column, []
    match = IDENTIFIER_BEFORE.search(before)
    prefix = match.group(0) if match else ""
    start = column - len(prefix)
    if prefix and prefix[0].isdigit():
        return column, []

    if start > 0 and before[start - 1] == ".":
        owner_match = IDENTIFIER_BEFORE.search(before[: start - 1])
        owner = owner_match.group(0) if owner_match else ""
        if owner == "hero":
            pool = HERO_MEMBERS
        else:
            module = _module_aliases(lines).get(owner, owner)
            pool = MODULE_MEMBERS.get(module, COMMON_METHODS)
        return start, _filter(pool, prefix, allow_empty=True)

    if not prefix:
        return column, []

    stripped = before.lstrip()
    if stripped.startswith(("import ", "from ")) and " import " not in stripped:
        pool = [Suggestion(name, name, "Thư viện được phép dùng") for name in IMPORTABLE]
        return start, _filter(pool, prefix)
    if re.search(r"\b(def|class)\s+\w*$", before):
        return column, []

    user_names = (_names_in_code(lines, row) | set(extra_names or [])) - set(KEYWORD_INSERTS)
    known = {item.label.split("(")[0] for item in BUILTIN_FUNCTIONS} | {"hero"}
    pool = [Suggestion("hero", "hero", "Nhân vật của bạn - gõ dấu . để xem lệnh")]
    pool += [Suggestion(name, name, "Tên trong code / dữ liệu có sẵn") for name in sorted(user_names - known)]
    pool += KEYWORDS + BUILTIN_FUNCTIONS
    return start, _filter(pool, prefix)


def _filter(pool: list[Suggestion], prefix: str, allow_empty: bool = False) -> list[Suggestion]:
    if not prefix and not allow_empty:
        return []
    lowered = prefix.lower()
    result = [
        item
        for item in pool
        if item.insert.lower().startswith(lowered) and item.insert.rstrip("():").strip() != prefix
    ]
    return result[:MAX_SUGGESTIONS] if prefix else result[:MAX_SUGGESTIONS + 3]


# ======================================================================
# editor.py
# ======================================================================

INDENT = "    "

CODE_COLOR_TEXT = (220, 224, 235)
CODE_COLOR_KEYWORD = (255, 121, 198)
CODE_COLOR_STRING = (241, 250, 140)
CODE_COLOR_COMMENT = (110, 120, 150)
CODE_COLOR_NUMBER = (189, 147, 249)
CODE_COLOR_HERO = (80, 250, 123)
CODE_COLOR_BUILTIN = (139, 233, 253)
CODE_COLOR_BACKGROUND = (30, 32, 44)
CODE_COLOR_GUTTER = (24, 26, 36)
CODE_COLOR_LINE_NUMBER = (90, 96, 120)
CODE_COLOR_CURRENT_LINE = (40, 43, 58)
CODE_COLOR_ERROR_LINE = (110, 40, 52)
CODE_COLOR_SELECTION = (62, 82, 140)
CODE_COLOR_CURSOR = (255, 255, 255)
CODE_COLOR_BORDER_FOCUS = (98, 114, 164)
CODE_COLOR_POPUP = (44, 48, 66)
CODE_COLOR_POPUP_BORDER = (110, 130, 190)
CODE_COLOR_POPUP_ACTIVE = (70, 96, 170)
CODE_COLOR_POPUP_HINT = (165, 172, 200)

BUILTINS = {
    "print", "len", "range", "int", "str", "float", "bool", "list", "dict", "set",
    "tuple", "sum", "min", "max", "sorted", "abs", "round", "enumerate", "zip",
    "DoorJammed", "True", "False", "None",
}

TOKEN_PATTERN = re.compile(
    r"(?P<comment>#.*)"
    r"|(?P<string>\"[^\"]*\"?|'[^']*'?)"
    r"|(?P<number>\b\d+(\.\d+)?\b)"
    r"|(?P<word>[A-Za-z_À-ỹ][\wÀ-ỹ]*)"
    r"|(?P<other>.)"
)

Position = tuple[int, int]


def in_text_context(line: str, column: int) -> bool:
    """True when `column` is inside a string literal or a comment."""
    quote: str | None = None
    for char in line[:column]:
        if quote:
            if char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char == "#":
            return True
    return quote is not None


def highlight(line: str) -> list[tuple[str, tuple[int, int, int]]]:
    tokens: list[tuple[str, tuple[int, int, int]]] = []
    for match in TOKEN_PATTERN.finditer(line):
        text = match.group(0)
        kind = match.lastgroup
        if kind == "comment":
            color = CODE_COLOR_COMMENT
        elif kind == "string":
            color = CODE_COLOR_STRING
        elif kind == "number":
            color = CODE_COLOR_NUMBER
        elif kind == "word" and text == "hero":
            color = CODE_COLOR_HERO
        elif kind == "word" and text in BUILTINS:
            color = CODE_COLOR_BUILTIN
        elif kind == "word" and keyword.iskeyword(text):
            color = CODE_COLOR_KEYWORD
        else:
            color = CODE_COLOR_TEXT
        tokens.append((text, color))
    return tokens


def _get_clipboard() -> str:
    try:
        text = pygame.scrap.get_text()
    except (pygame.error, AttributeError):
        return ""
    return (text or "").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


def _set_clipboard(text: str) -> None:
    try:
        pygame.scrap.put_text(text)
    except (pygame.error, AttributeError):
        return


class CodeEditor:
    def __init__(self, font: pygame.font.Font, hint_font: pygame.font.Font | None = None) -> None:
        self.font = font
        self.hint_font = hint_font or font
        self.char_width = font.size("M")[0]
        self.line_height = font.get_linesize() + 2
        self.lines: list[str] = [""]
        self.row = 0
        self.column = 0
        self.anchor: Position | None = None
        self.dragging = False
        self.scroll = 0
        self.focused = True
        self.error_line: int | None = None
        self.undo_stack: list[tuple[list[str], int, int]] = []
        self.blink_timer = 0.0
        self.rect = pygame.Rect(0, 0, 100, 100)
        self.gutter_width = self.char_width * 4
        self.vietnamese = True
        self.extra_names: list[str] = []
        self.suggestions: list[Suggestion] = []
        self.suggest_index = 0
        self.suggest_start = 0
        self.popup_rows: list[pygame.Rect] = []

    # ------------------------------------------------------------ content
    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    def set_text(self, text: str) -> None:
        self.lines = text.replace("\t", INDENT).replace("\r\n", "\n").rstrip("\n").split("\n") or [""]
        self.row = len(self.lines) - 1
        self.column = len(self.lines[self.row])
        self.anchor = None
        self.scroll = 0
        self.error_line = None
        self.undo_stack.clear()
        self.close_suggestions()

    def _save_undo(self) -> None:
        self.undo_stack.append((list(self.lines), self.row, self.column))
        if len(self.undo_stack) > 200:
            self.undo_stack.pop(0)

    def undo(self) -> None:
        if not self.undo_stack:
            return
        self.lines, self.row, self.column = self.undo_stack.pop()
        self.anchor = None
        self.close_suggestions()

    # ------------------------------------------------------------ selection
    def selection(self) -> tuple[Position, Position] | None:
        if self.anchor is None or self.anchor == (self.row, self.column):
            return None
        cursor = (self.row, self.column)
        return (min(self.anchor, cursor), max(self.anchor, cursor))

    def selected_text(self) -> str:
        span = self.selection()
        if span is None:
            return ""
        (start_row, start_col), (end_row, end_col) = span
        if start_row == end_row:
            return self.lines[start_row][start_col:end_col]
        parts = [self.lines[start_row][start_col:]]
        parts += self.lines[start_row + 1 : end_row]
        parts.append(self.lines[end_row][:end_col])
        return "\n".join(parts)

    def _delete_selection(self) -> bool:
        """Remove the selected text (caller saves undo). Returns True if something was removed."""
        span = self.selection()
        self.anchor = None
        if span is None:
            return False
        (start_row, start_col), (end_row, end_col) = span
        self.lines[start_row] = self.lines[start_row][:start_col] + self.lines[end_row][end_col:]
        del self.lines[start_row + 1 : end_row + 1]
        self.row, self.column = start_row, start_col
        return True

    def select_all(self) -> None:
        self.anchor = (0, 0)
        self.row = len(self.lines) - 1
        self.column = len(self.lines[self.row])

    # ------------------------------------------------------------ editing
    def insert(self, text: str) -> None:
        self._save_undo()
        self.error_line = None
        self._delete_selection()
        for index, part in enumerate(text.replace("\r", "").replace("\t", INDENT).split("\n")):
            if index > 0:
                self._split_line(auto_indent=False)
            line = self.lines[self.row]
            self.lines[self.row] = line[: self.column] + part + line[self.column :]
            self.column += len(part)

    def _split_line(self, auto_indent: bool) -> None:
        line = self.lines[self.row]
        before, after = line[: self.column], line[self.column :]
        indent = ""
        if auto_indent:
            indent = before[: len(before) - len(before.lstrip(" "))]
            if before.rstrip().endswith(":"):
                indent += INDENT
        self.lines[self.row] = before
        self.lines.insert(self.row + 1, indent + after.lstrip(" ") if auto_indent else after)
        self.row += 1
        self.column = len(indent)

    def newline(self) -> None:
        self._save_undo()
        self.error_line = None
        self._delete_selection()
        self._split_line(auto_indent=True)

    def backspace(self) -> None:
        self._save_undo()
        self.error_line = None
        if self._delete_selection():
            return
        line = self.lines[self.row]
        if self.column > 0:
            before = line[: self.column]
            remove = 1
            if before.strip() == "":
                remove = len(before) % len(INDENT) or len(INDENT)
            self.lines[self.row] = line[: self.column - remove] + line[self.column :]
            self.column -= remove
        elif self.row > 0:
            previous = self.lines[self.row - 1]
            self.lines[self.row - 1] = previous + line
            del self.lines[self.row]
            self.row -= 1
            self.column = len(previous)

    def delete(self) -> None:
        self._save_undo()
        self.error_line = None
        if self._delete_selection():
            return
        line = self.lines[self.row]
        if self.column < len(line):
            self.lines[self.row] = line[: self.column] + line[self.column + 1 :]
        elif self.row < len(self.lines) - 1:
            self.lines[self.row] = line + self.lines[self.row + 1]
            del self.lines[self.row + 1]

    def _selected_rows(self) -> range:
        span = self.selection()
        if span is None:
            return range(self.row, self.row + 1)
        (start_row, _), (end_row, end_col) = span
        if end_col == 0 and end_row > start_row:
            end_row -= 1
        return range(start_row, end_row + 1)

    def indent_lines(self) -> None:
        self._save_undo()
        for row in self._selected_rows():
            self.lines[row] = INDENT + self.lines[row]
        if self.anchor is not None:
            self.anchor = (self.anchor[0], self.anchor[1] + len(INDENT))
        self.column += len(INDENT)

    def dedent(self) -> None:
        self._save_undo()
        for row in self._selected_rows():
            if self.lines[row].startswith(INDENT):
                self.lines[row] = self.lines[row][len(INDENT) :]
                if row == self.row:
                    self.column = max(0, self.column - len(INDENT))
                if self.anchor is not None and row == self.anchor[0]:
                    self.anchor = (self.anchor[0], max(0, self.anchor[1] - len(INDENT)))

    # ------------------------------------------------------------ clipboard
    def copy(self) -> None:
        """Copy the selection; with no selection copy the whole current line."""
        text = self.selected_text() or self.lines[self.row] + "\n"
        _set_clipboard(text)

    def cut(self) -> None:
        if self.selection() is None:
            _set_clipboard(self.lines[self.row] + "\n")
            self._save_undo()
            if len(self.lines) > 1:
                del self.lines[self.row]
                self.row = min(self.row, len(self.lines) - 1)
            else:
                self.lines = [""]
            self.column = min(self.column, len(self.lines[self.row]))
            return
        _set_clipboard(self.selected_text())
        self._save_undo()
        self._delete_selection()

    def paste(self) -> None:
        text = _get_clipboard()
        if text:
            self.insert(text)

    def shortcut(self, name: str) -> None:
        """Run a Ctrl shortcut: "a" select all, "c" copy, "x" cut, "v" paste, "z" undo."""
        actions = {"z": self.undo, "a": self.select_all, "c": self.copy, "x": self.cut, "v": self.paste}
        if name not in actions:
            return
        actions[name]()
        self.blink_timer = 0.0
        if name != "c":
            self.close_suggestions()

    # ------------------------------------------------------------ suggestions
    def close_suggestions(self) -> None:
        self.suggestions = []
        self.suggest_index = 0

    def refresh_suggestions(self) -> None:
        if self.selection() is not None:
            self.close_suggestions()
            return
        start, items = suggest(self.lines, self.row, self.column, self.extra_names)
        self.suggest_start = start
        self.suggestions = items
        self.suggest_index = 0

    def accept_suggestion(self, index: int | None = None) -> None:
        if not self.suggestions:
            return
        item = self.suggestions[self.suggest_index if index is None else index]
        self._save_undo()
        line = self.lines[self.row]
        self.lines[self.row] = line[: self.suggest_start] + item.insert + line[self.column :]
        self.column = self.suggest_start + len(item.insert) - item.cursor_back
        self.close_suggestions()

    # ------------------------------------------------------------ events
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.popup_rows):
                if self.suggestions and rect.collidepoint(event.pos):
                    self.accept_suggestion(index)
                    return True
            self.focused = self.rect.collidepoint(event.pos)
            if self.focused:
                self.close_suggestions()
                shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
                if not shift or self.anchor is None:
                    self.anchor = None
                previous = (self.row, self.column)
                self._click(event.pos)
                if shift:
                    self.anchor = self.anchor or previous
                else:
                    self.anchor = (self.row, self.column)
                self.dragging = True
            return self.focused
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self._click(event.pos)
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            if self.anchor == (self.row, self.column):
                self.anchor = None
            return True
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(mouse_pos()):
            self.scroll = max(0, min(len(self.lines) - 1, self.scroll - event.y * 3))
            return True
        if not self.focused:
            return False
        if event.type == pygame.TEXTINPUT:
            if not self._try_telex(event.text):
                self.insert(event.text)
                self.refresh_suggestions()
            return True
        if event.type == pygame.KEYDOWN:
            return self._key(event)
        return False

    def handle_escape(self) -> bool:
        """Close the suggestion popup / selection first. Returns True if Escape was used."""
        if self.suggestions:
            self.close_suggestions()
            return True
        if self.selection() is not None:
            self.anchor = None
            return True
        return False

    def _try_telex(self, text: str) -> bool:
        """Apply Telex inside strings and comments only, so Python code stays untouched."""
        if not self.vietnamese or len(text) != 1 or not text.isascii() or not text.isalpha():
            return False
        if self.selection() is not None:
            return False
        line = self.lines[self.row]
        if not in_text_context(line, self.column):
            return False
        word_start = self.column
        while word_start > 0 and line[word_start - 1].isalpha():
            word_start -= 1
        word = line[word_start : self.column]
        new_word = telex_key(word, text)
        self._save_undo()
        self.error_line = None
        self.lines[self.row] = line[:word_start] + new_word + line[self.column :]
        self.column = word_start + len(new_word)
        self.close_suggestions()
        return True

    def _click(self, position: tuple[int, int]) -> None:
        relative_y = position[1] - self.rect.y - 6
        self.row = max(0, min(len(self.lines) - 1, self.scroll + relative_y // self.line_height))
        relative_x = position[0] - self.rect.x - self.gutter_width - 8
        self.column = max(0, min(len(self.lines[self.row]), round(relative_x / self.char_width)))
        self.blink_timer = 0.0

    def _key(self, event: pygame.event.Event) -> bool:
        control = event.mod & pygame.KMOD_CTRL
        shift = event.mod & pygame.KMOD_SHIFT
        key = event.key
        self.blink_timer = 0.0

        if self.suggestions and not control:
            if key == pygame.K_DOWN:
                self.suggest_index = (self.suggest_index + 1) % len(self.suggestions)
                return True
            if key == pygame.K_UP:
                self.suggest_index = (self.suggest_index - 1) % len(self.suggestions)
                return True
            if key in (pygame.K_TAB, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.accept_suggestion()
                return True

        if control:
            letters = {pygame.K_z: "z", pygame.K_a: "a", pygame.K_c: "c", pygame.K_x: "x", pygame.K_v: "v"}
            if key in letters:
                self.shortcut(letters[key])
                return True
            if key == pygame.K_SPACE:
                self.refresh_suggestions()
                return True
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return False

        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.newline()
            self.close_suggestions()
        elif key == pygame.K_BACKSPACE:
            self.backspace()
            if self.suggestions:
                self.refresh_suggestions()
        elif key == pygame.K_DELETE:
            self.delete()
            self.close_suggestions()
        elif key == pygame.K_TAB:
            if shift:
                self.dedent()
            elif self.selection() is not None:
                self.indent_lines()
            else:
                self.insert(INDENT)
        elif key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_HOME, pygame.K_END):
            self._navigate(key, shift)
            self.close_suggestions()
        else:
            return False
        return True

    def _navigate(self, key: int, extend: bool) -> None:
        if extend and self.anchor is None:
            self.anchor = (self.row, self.column)
        elif not extend:
            span = self.selection()
            self.anchor = None
            if span is not None and key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.row, self.column = span[0] if key == pygame.K_LEFT else span[1]
                return
        if key == pygame.K_LEFT:
            self._move_horizontal(-1)
        elif key == pygame.K_RIGHT:
            self._move_horizontal(1)
        elif key == pygame.K_UP:
            self._move_vertical(-1)
        elif key == pygame.K_DOWN:
            self._move_vertical(1)
        elif key == pygame.K_HOME:
            line = self.lines[self.row]
            first_char = len(line) - len(line.lstrip(" "))
            self.column = 0 if self.column == first_char else first_char
        elif key == pygame.K_END:
            self.column = len(self.lines[self.row])

    def _move_horizontal(self, delta: int) -> None:
        self.column += delta
        if self.column < 0 and self.row > 0:
            self.row -= 1
            self.column = len(self.lines[self.row])
        elif self.column > len(self.lines[self.row]) and self.row < len(self.lines) - 1:
            self.row += 1
            self.column = 0
        self.column = max(0, min(self.column, len(self.lines[self.row])))

    def _move_vertical(self, delta: int) -> None:
        self.row = max(0, min(len(self.lines) - 1, self.row + delta))
        self.column = min(self.column, len(self.lines[self.row]))

    # ------------------------------------------------------------ drawing
    def update(self, delta_seconds: float) -> None:
        self.blink_timer += delta_seconds

    def draw(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        self.rect = rect
        pygame.draw.rect(surface, CODE_COLOR_BACKGROUND, rect, border_radius=8)
        gutter = pygame.Rect(rect.x, rect.y, self.gutter_width + 4, rect.height)
        pygame.draw.rect(surface, CODE_COLOR_GUTTER, gutter, border_top_left_radius=8, border_bottom_left_radius=8)

        visible_rows = max(1, (rect.height - 12) // self.line_height)
        if self.row < self.scroll:
            self.scroll = self.row
        elif self.row >= self.scroll + visible_rows:
            self.scroll = self.row - visible_rows + 1

        span = self.selection()
        previous_clip = surface.get_clip()
        surface.set_clip(rect)
        text_x = rect.x + self.gutter_width + 8
        for screen_index in range(visible_rows):
            line_index = self.scroll + screen_index
            if line_index >= len(self.lines):
                break
            y = rect.y + 6 + screen_index * self.line_height
            line_rect = pygame.Rect(rect.x + gutter.width, y - 1, rect.width - gutter.width, self.line_height)
            if self.error_line == line_index + 1:
                pygame.draw.rect(surface, CODE_COLOR_ERROR_LINE, line_rect)
            elif line_index == self.row and self.focused and span is None:
                pygame.draw.rect(surface, CODE_COLOR_CURRENT_LINE, line_rect)
            if span is not None:
                self._draw_selection_row(surface, span, line_index, text_x, y)

            number = self.font.render(str(line_index + 1).rjust(3), True, CODE_COLOR_LINE_NUMBER)
            surface.blit(number, (rect.x + 4, y))

            x = text_x
            for text, color in highlight(self.lines[line_index]):
                rendered = self.font.render(text, True, color)
                surface.blit(rendered, (x, y))
                x += self.char_width * len(text)

        cursor_x = text_x + self.column * self.char_width
        cursor_y = rect.y + 6 + (self.row - self.scroll) * self.line_height
        if self.focused and (self.blink_timer % 1.0) < 0.6:
            pygame.draw.line(surface, CODE_COLOR_CURSOR, (cursor_x, cursor_y), (cursor_x, cursor_y + self.line_height - 3), 2)

        surface.set_clip(previous_clip)
        if self.focused:
            pygame.draw.rect(surface, CODE_COLOR_BORDER_FOCUS, rect, width=2, border_radius=8)
        self._draw_popup(surface, text_x + self.suggest_start * self.char_width, cursor_y)

    def _draw_selection_row(
        self,
        surface: pygame.Surface,
        span: tuple[Position, Position],
        line_index: int,
        text_x: int,
        y: int,
    ) -> None:
        (start_row, start_col), (end_row, end_col) = span
        if not start_row <= line_index <= end_row:
            return
        line_length = len(self.lines[line_index])
        first = start_col if line_index == start_row else 0
        last = end_col if line_index == end_row else line_length + 1
        if last <= first:
            return
        box = pygame.Rect(text_x + first * self.char_width, y - 1, (last - first) * self.char_width, self.line_height)
        pygame.draw.rect(surface, CODE_COLOR_SELECTION, box)

    def _draw_popup(self, surface: pygame.Surface, x: int, cursor_y: int) -> None:
        self.popup_rows = []
        if not self.suggestions or not self.focused:
            return
        row_height = self.line_height + 4
        labels = [self.font.render(item.label, True, CODE_COLOR_TEXT) for item in self.suggestions]
        hints = [self.hint_font.render(item.hint, True, CODE_COLOR_POPUP_HINT) for item in self.suggestions]
        label_width = max(label.get_width() for label in labels)
        width = min(self.rect.width - 8, label_width + 24 + max(hint.get_width() for hint in hints) + 16)
        height = row_height * len(self.suggestions) + 26
        box = pygame.Rect(x, cursor_y + self.line_height + 2, width, height)
        if box.bottom > surface.get_height() - 4:
            box.bottom = cursor_y - 2
        box.right = min(box.right, self.rect.right - 4)
        box.left = max(box.left, self.rect.left + 4)

        pygame.draw.rect(surface, CODE_COLOR_POPUP, box, border_radius=6)
        pygame.draw.rect(surface, CODE_COLOR_POPUP_BORDER, box, width=1, border_radius=6)
        previous_clip = surface.get_clip()
        surface.set_clip(box)
        for index, (label, hint) in enumerate(zip(labels, hints, strict=True)):
            row_rect = pygame.Rect(box.x + 2, box.y + 3 + index * row_height, box.width - 4, row_height)
            if index == self.suggest_index:
                pygame.draw.rect(surface, CODE_COLOR_POPUP_ACTIVE, row_rect, border_radius=4)
            surface.blit(label, (row_rect.x + 8, row_rect.y + 2))
            surface.blit(hint, (row_rect.x + 16 + label_width, row_rect.y + 3))
            self.popup_rows.append(row_rect)
        footer = self.hint_font.render("Tab / Enter: chọn  ·  ↑↓: đổi  ·  Esc: đóng", True, CODE_COLOR_POPUP_HINT)
        surface.blit(footer, (box.x + 10, box.bottom - 22))
        surface.set_clip(previous_clip)


# ======================================================================
# theory_view.py
# ======================================================================

THEORY_COLOR_TEXT = (230, 232, 240)
THEORY_COLOR_MUTED = (160, 166, 190)
THEORY_COLOR_HEADING = (255, 196, 64)
THEORY_COLOR_TAG = (90, 210, 230)
THEORY_COLOR_INLINE_CODE = (120, 230, 160)
THEORY_COLOR_CODE_BACKGROUND = (30, 32, 44)
THEORY_COLOR_PANEL = (18, 20, 30)
THEORY_COLOR_BORDER = (98, 114, 164)
PADDING = 22


def rich_words(text: str) -> list[tuple[str, bool]]:
    """Split text into words, marking those inside `backticks` as code."""
    words: list[tuple[str, bool]] = []
    for index, chunk in enumerate(text.split("`")):
        is_code = index % 2 == 1
        for word in chunk.split(" "):
            if word:
                words.append((word, is_code))
    return words


class TheoryView:
    def __init__(
        self,
        font: pygame.font.Font,
        font_bold: pygame.font.Font,
        font_title: pygame.font.Font,
        font_code: pygame.font.Font,
    ) -> None:
        self.font = font
        self.font_bold = font_bold
        self.font_title = font_title
        self.font_code = font_code
        self.operations: list[tuple[int, Callable[[pygame.Surface, int, int], None]]] = []
        self.content_height = 0
        self.scroll = 0
        self.rect = pygame.Rect(0, 0, 100, 100)
        self.close_rect = pygame.Rect(0, 0, 0, 0)

    # ------------------------------------------------------------ layout
    def build(
        self,
        title: str,
        tag: str,
        theory: Theory,
        rect: pygame.Rect,
        inputs: dict[str, Any],
        goal: str,
    ) -> None:
        self.rect = rect
        self.scroll = 0
        self.operations = []
        width = rect.width - PADDING * 2 - 12
        y = 0

        y = self._add_text(title, self.font_title, THEORY_COLOR_HEADING, y, width - 110)
        y = self._add_text(tag, self.font, THEORY_COLOR_TAG, y + 2, width - 110)
        y += 8
        y = self._add_heading("Khái niệm", y)
        for paragraph in theory.concept:
            y = self._add_rich("•  " + paragraph, y, width) + 6

        y = self._add_heading("Đề bài", y + 6)
        y = self._add_rich("Kết quả cần đạt: " + goal, y, width) + 4
        if inputs:
            y = self._add_rich("Dữ liệu vào (biến có sẵn, dùng ngay được trong code):", y, width) + 4
            input_lines = [(f"{name} = {value!r}", "") for name, value in inputs.items()]
            y = self._add_code_pairs(input_lines, y, width)

        if theory.starter_notes:
            y = self._add_heading("Giải thích code ban đầu của màn", y + 6)
            y = self._add_code_pairs(theory.starter_notes, y, width)

        y = self._add_heading("Ví dụ minh hoạ (khác lời giải - hãy tự áp dụng)", y + 6)
        y = self._add_code_pairs(theory.example, y, width)

        if theory.mistakes:
            y = self._add_heading("Lỗi hay gặp", y + 6)
            for mistake in theory.mistakes:
                y = self._add_rich("•  " + mistake, y, width) + 4
        self.content_height = y + PADDING

    def _add(self, y: int, draw: Callable[[pygame.Surface, int, int], None]) -> None:
        self.operations.append((y, draw))

    def _add_text(self, text: str, font: pygame.font.Font, color: tuple[int, int, int], y: int, width: int) -> int:
        for line in self._wrap_plain(text, font, width):
            rendered = font.render(line, True, color)
            self._add(y, lambda surface, x, top, image=rendered: surface.blit(image, (x, top)))
            y += font.get_linesize()
        return y

    def _add_heading(self, text: str, y: int) -> int:
        rendered = self.font_bold.render(text, True, THEORY_COLOR_HEADING)
        self._add(y + 4, lambda surface, x, top, image=rendered: surface.blit(image, (x, top)))
        return y + self.font_bold.get_linesize() + 10

    def _add_rich(self, text: str, y: int, width: int, indent: int = 0) -> int:
        space = self.font.size(" ")[0]
        line_height = self.font.get_linesize() + 2
        cursor_x = indent
        line_items: list[tuple[int, pygame.Surface, Any]] = []

        def flush(top: int) -> None:
            items = list(line_items)

            def draw(surface: pygame.Surface, x: int, current_top: int) -> None:
                for offset, image, is_code in items:
                    if is_code:
                        background = image.get_rect(topleft=(x + offset, current_top)).inflate(6, 2)
                        pygame.draw.rect(surface, THEORY_COLOR_CODE_BACKGROUND, background, border_radius=4)
                    surface.blit(image, (x + offset, current_top))

            self._add(top, draw)
            line_items.clear()

        for word, is_code in rich_words(text):
            font = self.font_code if is_code else self.font
            color = THEORY_COLOR_INLINE_CODE if is_code else THEORY_COLOR_TEXT
            image = font.render(word, True, color)
            if cursor_x + image.get_width() > width and line_items:
                flush(y)
                y += line_height
                cursor_x = indent + space * 4
            line_items.append((cursor_x, image, is_code))
            cursor_x += image.get_width() + space + (4 if is_code else 0)
        if line_items:
            flush(y)
            y += line_height
        return y

    def _add_code_pairs(self, pairs: list[tuple[str, str]], y: int, width: int) -> int:
        char_width = self.font_code.size("M")[0]
        code_height = self.font_code.get_linesize() + 4
        for code, note in pairs:
            tokens = highlight(code)

            def draw_code(surface: pygame.Surface, x: int, top: int, parts: list[Any] = tokens) -> None:
                box = pygame.Rect(x, top - 2, width, code_height)
                pygame.draw.rect(surface, THEORY_COLOR_CODE_BACKGROUND, box, border_radius=6)
                cursor = x + 10
                for text, color in parts:
                    surface.blit(self.font_code.render(text, True, color), (cursor, top))
                    cursor += char_width * len(text)

            self._add(y, draw_code)
            y += code_height + 2
            if note:
                y = self._add_note("→ " + note, y, width)
            y += 8
        return y

    def _add_note(self, text: str, y: int, width: int) -> int:
        for line in self._wrap_plain(text, self.font, width - 24):
            rendered = self.font.render(line, True, THEORY_COLOR_MUTED)
            self._add(y, lambda surface, x, top, image=rendered: surface.blit(image, (x + 18, top)))
            y += self.font.get_linesize()
        return y

    @staticmethod
    def _wrap_plain(text: str, font: pygame.font.Font, width: int) -> list[str]:
        lines: list[str] = []
        current = ""
        for word in text.split(" "):
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    # ------------------------------------------------------------ events
    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Returns "close" when the panel should close, "used" when the event was consumed."""
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(mouse_pos()):
            self._scroll_by(-event.y * 48)
            return "used"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_rect.collidepoint(event.pos):
                return "close"
            if self.rect.collidepoint(event.pos):
                return "used"
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_PAGEDOWN, pygame.K_PAGEUP):
            self._scroll_by(300 if event.key == pygame.K_PAGEDOWN else -300)
            return "used"
        return None

    def _scroll_by(self, amount: int) -> None:
        maximum = max(0, self.content_height - self.rect.height + PADDING)
        self.scroll = max(0, min(maximum, self.scroll + amount))

    # ------------------------------------------------------------ drawing
    def draw(self, surface: pygame.Surface) -> None:
        self._scroll_by(0)
        pygame.draw.rect(surface, THEORY_COLOR_PANEL, self.rect, border_radius=12)
        pygame.draw.rect(surface, THEORY_COLOR_BORDER, self.rect, width=2, border_radius=12)

        previous_clip = surface.get_clip()
        surface.set_clip(self.rect.inflate(-4, -4))
        left = self.rect.x + PADDING
        top = self.rect.y + PADDING - self.scroll
        for offset, draw in self.operations:
            screen_y = top + offset
            if self.rect.y - 80 < screen_y < self.rect.bottom + 10:
                draw(surface, left, screen_y)
        surface.set_clip(previous_clip)

        self._draw_scrollbar(surface)
        self.close_rect = pygame.Rect(self.rect.right - 110, self.rect.y + 14, 92, 36)
        hovered = self.close_rect.collidepoint(mouse_pos())
        pygame.draw.rect(surface, (150, 70, 80) if hovered else (120, 60, 70), self.close_rect, border_radius=8)
        label = self.font_bold.render("Đóng", True, THEORY_COLOR_TEXT)
        surface.blit(label, label.get_rect(center=self.close_rect.center))

    def _draw_scrollbar(self, surface: pygame.Surface) -> None:
        visible = self.rect.height
        if self.content_height <= visible:
            return
        track = pygame.Rect(self.rect.right - 10, self.rect.y + 60, 5, visible - 80)
        pygame.draw.rect(surface, (50, 54, 72), track, border_radius=3)
        thumb_height = max(30, track.height * visible // self.content_height)
        maximum = max(1, self.content_height - visible + PADDING)
        thumb_y = track.y + (track.height - thumb_height) * self.scroll // maximum
        pygame.draw.rect(surface, THEORY_COLOR_BORDER, (track.x, thumb_y, 5, thumb_height), border_radius=3)


# ======================================================================
# assets.py
# ======================================================================

IS_PACKAGED = getattr(sys, "frozen", False)
PROJECT_ROOT = Path(__file__).resolve().parent
# Khi đóng gói bằng PyInstaller, dữ liệu nằm trong thư mục giải nén tạm (sys._MEIPASS).
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
KIT = BUNDLE_ROOT / "gamekit"
LOGO_PATH = BUNDLE_ROOT / "assets" / "onespace_logo.png"
# Vùng hình tròn (tên lửa) trong logo OneSpace, dùng làm icon.
LOGO_ICON_BOX = (224, 120, 700, 596)
APP_TITLE = "OneSpace CodeQuest - Học Python qua trò chơi"


def user_data_dir() -> Path:
    """Nơi lưu tiến độ: %APPDATA%/CodeQuest khi chạy bản .exe, thư mục dự án khi phát triển."""
    if not IS_PACKAGED:
        return PROJECT_ROOT
    base = Path(os.environ.get("APPDATA", Path.home()))
    folder = base / "OneSpaceCodeQuest"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def documents_dir() -> Path:
    """The user's Documents folder (follows OneDrive redirection on Windows)."""
    if sys.platform == "win32":
        try:
            import ctypes

            buffer = ctypes.create_unicode_buffer(260)
            # CSIDL_PERSONAL = 5 (Documents)
            if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buffer) == 0 and buffer.value:
                return Path(buffer.value)
        except (AttributeError, OSError):
            pass
    return Path.home() / "Documents"


def backup_dir() -> Path | None:
    """Folder for the easy-to-find progress backup (only for the installed .exe)."""
    if not IS_PACKAGED:
        return None
    return documents_dir() / "OneSpace CodeQuest"


TILE = 48

ENEMY_FOLDERS: dict[str, tuple[str, int]] = {
    "robot": ("1", 48),
    "barrel": ("3", 48),
    "cannon": ("4", 48),
    "spikebox": ("5", 48),
    "duck": ("6 (48x72)", 72),
}


def load_logo(height: int) -> pygame.Surface | None:
    """Full OneSpace logo scaled to `height` pixels, or None if the file is missing."""
    try:
        logo = pygame.image.load(str(LOGO_PATH)).convert_alpha()
    except (pygame.error, FileNotFoundError):
        return None
    width = round(logo.get_width() * height / logo.get_height())
    return pygame.transform.smoothscale(logo, (width, height))


def load_logo_icon(size: int) -> pygame.Surface | None:
    """Round rocket emblem from the logo; works before the display is created."""
    try:
        logo = pygame.image.load(str(LOGO_PATH))
    except (pygame.error, FileNotFoundError):
        return None
    left, top, right, bottom = LOGO_ICON_BOX
    emblem = logo.subsurface((left, top, right - left, bottom - top))
    return pygame.transform.smoothscale(emblem, (size, size))


def load_image(relative_path: str) -> pygame.Surface:
    return pygame.image.load(str(KIT / relative_path)).convert_alpha()


def slice_strip(sheet: pygame.Surface, frame_width: int, scale: float) -> list[pygame.Surface]:
    frame_height = sheet.get_height()
    frame_count = max(1, sheet.get_width() // frame_width)
    size = (round(frame_width * scale), round(frame_height * scale))
    frames = []
    for index in range(frame_count):
        frame = sheet.subsurface((index * frame_width, 0, frame_width, frame_height))
        frames.append(pygame.transform.scale(frame, size))
    return frames


def recolored(sheet: pygame.Surface, replacements: dict[tuple[int, int, int], tuple[int, int, int]]) -> pygame.Surface:
    if not replacements:
        return sheet
    result = sheet.copy()
    pixels = pygame.PixelArray(result)
    for old_color, new_color in replacements.items():
        pixels.replace(old_color, new_color)
    pixels.close()
    return result


def tinted(tile: pygame.Surface, multiply: tuple[int, int, int], add: tuple[int, int, int]) -> pygame.Surface:
    result = tile.copy()
    if multiply != (255, 255, 255):
        result.fill(multiply, special_flags=pygame.BLEND_RGB_MULT)
    if add != (0, 0, 0):
        result.fill(add, special_flags=pygame.BLEND_RGB_ADD)
    return result


def strip(relative_path: str, frame_width: int, scale: float) -> list[pygame.Surface]:
    return slice_strip(load_image(relative_path), frame_width, scale)


class Assets:
    def __init__(self, hero_skin: int = 1) -> None:
        tileset = load_image("2 Locations/Tiles/Tileset.png")
        self._tileset = tileset
        self._theme_tiles: dict[str, tuple[pygame.Surface, pygame.Surface]] = {}
        self.floor = self._tile(tileset, 1, 1)
        self.wall = self._tile(tileset, 1, 4)
        self.door_locked = self._tile(tileset, 13, 5)
        self.door_jammed = self._tile(tileset, 6, 8)

        hero_scale = TILE / 32 * 1.25
        self._hero_skins: dict[int, dict[str, list[pygame.Surface]]] = {}
        self.hero = self.hero_skin(hero_skin)
        self.appearing = strip("1 Main Characters/Appearing.png", 96, hero_scale)

        self.enemies: dict[str, dict[str, list[pygame.Surface]]] = {}
        for kind, (folder, frame_width) in ENEMY_FOLDERS.items():
            scale = 1.8 if kind == "duck" else 1.6
            self.enemies[kind] = {
                "idle": strip(f"4 Enemies/{folder}/Idle.png", frame_width, scale),
                "hit": strip(f"4 Enemies/{folder}/Hit.png", frame_width, scale),
            }

        self.gems = {color: strip(f"3 Objects/Gems/{color}.png", 16, 2.5) for color in range(1, 7)}
        # Thùng gỗ: 1 = thùng thường (O), 2 = thùng có ngọc (Q).
        self.crates = {
            number: {
                "idle": strip(f"3 Objects/Boxes/{number}_Idle.png", 32, 1.5),
                "break": strip(f"3 Objects/Boxes/{number}_Break.png", 32, 1.5),
            }
            for number in (1, 2)
        }
        self.trophy = strip("3 Objects/Checkpoints/End_Idle.png", 64, 0.95)
        self.spike = strip("6 Traps/4.png", 48, 1.0)[4]
        self.backgrounds = {
            index: pygame.transform.scale(load_image(f"2 Locations/Backgrounds/{index}.png"), (128, 128))
            for index in range(1, 7)
        }

    def hero_skin(self, number: int) -> dict[str, list[pygame.Surface]]:
        """Animation frames for a hero of the roster (loaded once, then cached)."""
        if number not in self._hero_skins:
            style = HEROES_BY_NUMBER.get(number, HEROES[0])
            replacements = color_map(style)
            hero_dir = f"1 Main Characters/{style.base}"
            scale = TILE / 32 * 1.25
            self._hero_skins[number] = {
                state: slice_strip(recolored(load_image(f"{hero_dir}/{file_name}.png"), replacements), 32, scale)
                for state, file_name in (("idle", "Idle"), ("run", "Run"), ("hit", "Hit"), ("jump", "Jump"))
            }
        return self._hero_skins[number]

    def theme_tiles(self, theme: MapTheme) -> tuple[pygame.Surface, pygame.Surface]:
        """(floor, wall) tiles of a map theme, tinted and cached."""
        if theme.name not in self._theme_tiles:
            floor = tinted(self._tile(self._tileset, *theme.floor), theme.floor_multiply, theme.add)
            wall = tinted(self._tile(self._tileset, *theme.wall), theme.wall_multiply, theme.add)
            self._theme_tiles[theme.name] = (floor, wall)
        return self._theme_tiles[theme.name]

    @staticmethod
    def _tile(tileset: pygame.Surface, column: int, row: int) -> pygame.Surface:
        tile = tileset.subsurface((column * 16, row * 16, 16, 16))
        return pygame.transform.scale(tile, (TILE, TILE))


# ======================================================================
# hud.py
# ======================================================================

GOLD = (255, 205, 60)
GOLD_DARK = (150, 110, 20)
EMPTY_STAR = (70, 74, 96)
STAGE_COLORS: dict[int, tuple[int, int, int]] = {
    1: (80, 200, 120),
    2: (90, 160, 240),
    3: (240, 150, 70),
    4: (200, 110, 230),
    5: (240, 90, 110),
}


def star_points(center: tuple[float, float], radius: float) -> list[tuple[float, float]]:
    points = []
    for index in range(10):
        angle = math.pi / 2 + index * math.pi / 5
        distance = radius if index % 2 == 0 else radius * 0.45
        points.append((center[0] + distance * math.cos(angle), center[1] - distance * math.sin(angle)))
    return points


def draw_star(surface: pygame.Surface, center: tuple[float, float], radius: float, filled: bool) -> None:
    points = star_points(center, radius)
    pygame.draw.polygon(surface, GOLD if filled else EMPTY_STAR, points)
    pygame.draw.polygon(surface, GOLD_DARK if filled else (50, 54, 72), points, width=max(1, int(radius // 6)))


def draw_star_row(surface: pygame.Surface, center: tuple[float, float], radius: float, count: int, total: int = 3) -> None:
    spacing = radius * 2.3
    start_x = center[0] - spacing * (total - 1) / 2
    for index in range(total):
        draw_star(surface, (start_x + index * spacing, center[1]), radius, index < count)


def draw_coin(surface: pygame.Surface, center: tuple[int, int], radius: int) -> None:
    pygame.draw.circle(surface, GOLD_DARK, center, radius)
    pygame.draw.circle(surface, GOLD, center, radius - max(1, radius // 5))
    pygame.draw.circle(surface, (255, 235, 140), (center[0] - radius // 3, center[1] - radius // 3), max(1, radius // 4))


def draw_shield(surface: pygame.Surface, center: tuple[int, int], size: int, active: bool = True) -> None:
    x, y = center
    points = [
        (x - size, y - size), (x + size, y - size), (x + size, y),
        (x, y + int(size * 1.3)), (x - size, y),
    ]
    pygame.draw.polygon(surface, (120, 180, 240) if active else (70, 74, 96), points)
    pygame.draw.polygon(surface, (40, 70, 120), points, width=2)


def draw_heart(surface: pygame.Surface, center: tuple[int, int], size: int, color: tuple[int, int, int]) -> None:
    x, y = center
    radius = size // 2
    pygame.draw.circle(surface, color, (x - radius, y - radius // 2), radius)
    pygame.draw.circle(surface, color, (x + radius, y - radius // 2), radius)
    pygame.draw.polygon(surface, color, [(x - size, y - radius // 3), (x + size, y - radius // 3), (x, y + size)])


def draw_medal(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    label: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    earned: bool,
) -> None:
    x, y = center
    ribbon = (200, 60, 70) if earned else (60, 62, 80)
    pygame.draw.polygon(surface, ribbon, [(x - radius // 2, y - radius - 14), (x, y - radius + 4), (x - radius, y - radius - 2)])
    pygame.draw.polygon(surface, ribbon, [(x + radius // 2, y - radius - 14), (x, y - radius + 4), (x + radius, y - radius - 2)])
    pygame.draw.circle(surface, GOLD_DARK if earned else (50, 52, 68), center, radius)
    pygame.draw.circle(surface, color if earned else (64, 68, 88), center, radius - 4)
    text = font.render(label, True, (255, 255, 255) if earned else (120, 124, 146))
    surface.blit(text, text.get_rect(center=center))


class Confetti:
    """Short burst of falling paper for wins."""

    COLORS = ((255, 205, 60), (90, 220, 120), (120, 180, 255), (255, 110, 150), (200, 140, 255))

    def __init__(self) -> None:
        self.pieces: list[list[float]] = []

    def burst(self, area: pygame.Rect, count: int = 90) -> None:
        for _ in range(count):
            self.pieces.append([
                random.uniform(area.left, area.right),
                random.uniform(area.top - 40, area.top + 20),
                random.uniform(-60, 60),
                random.uniform(80, 220),
                random.uniform(0, 360),
                random.uniform(-400, 400),
                random.randrange(len(self.COLORS)),
                random.uniform(2.0, 3.2),
            ])

    def update(self, delta_seconds: float) -> None:
        for piece in self.pieces:
            piece[0] += piece[2] * delta_seconds
            piece[1] += piece[3] * delta_seconds
            piece[4] += piece[5] * delta_seconds
            piece[7] -= delta_seconds
        self.pieces = [piece for piece in self.pieces if piece[7] > 0]

    def draw(self, surface: pygame.Surface, clip: pygame.Rect) -> None:
        previous = surface.get_clip()
        surface.set_clip(clip)
        for x, y, _, _, angle, _, color_index, _ in self.pieces:
            width = 6 * abs(math.cos(math.radians(angle))) + 1
            pygame.draw.rect(surface, self.COLORS[int(color_index)], (x, y, width, 9))
        surface.set_clip(previous)


def draw_key(surface: pygame.Surface, center: tuple[int, int], size: int) -> None:
    """Small golden key, about 2 * size pixels wide."""
    x, y = center
    ring = max(3, size // 2)
    pygame.draw.circle(surface, GOLD_DARK, (x - size // 2, y), ring + 2)
    pygame.draw.circle(surface, GOLD, (x - size // 2, y), ring)
    pygame.draw.circle(surface, GOLD_DARK, (x - size // 2, y), max(1, ring // 2))
    shaft = pygame.Rect(x - size // 2 + ring, y - 2, size + ring, 5)
    pygame.draw.rect(surface, GOLD, shaft)
    pygame.draw.rect(surface, GOLD, (shaft.right - 5, y + 2, 4, 6))
    pygame.draw.rect(surface, GOLD, (shaft.right - 12, y + 2, 4, 5))


def draw_lock_door(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Wooden door with a golden padlock (opened with hero.unlock)."""
    pygame.draw.rect(surface, (110, 70, 40), rect)
    for offset in (rect.width // 3, 2 * rect.width // 3):
        pygame.draw.line(surface, (80, 48, 26), (rect.x + offset, rect.y + 2), (rect.x + offset, rect.bottom - 2), 2)
    pygame.draw.rect(surface, (70, 42, 22), rect, width=3)
    body = pygame.Rect(0, 0, rect.width // 2, rect.height // 3)
    body.center = (rect.centerx, rect.centery + rect.height // 10)
    pygame.draw.arc(surface, (200, 200, 210), body.inflate(-6, 10).move(0, -body.height // 2), 0, 3.2, 3)
    pygame.draw.rect(surface, GOLD, body, border_radius=3)
    pygame.draw.circle(surface, (60, 40, 20), (body.centerx, body.centery - 1), 3)
    pygame.draw.rect(surface, (60, 40, 20), (body.centerx - 1, body.centery, 3, 6))


def draw_chest(surface: pygame.Surface, rect: pygame.Rect, opened: bool, time_value: float = 0.0) -> None:
    """Treasure chest; when opened the lid is up and gold sparkles."""
    base = pygame.Rect(rect.x + 4, rect.y + rect.height // 2, rect.width - 8, rect.height // 2 - 4)
    pygame.draw.rect(surface, (140, 82, 40), base, border_radius=4)
    pygame.draw.rect(surface, (90, 50, 24), base, width=2, border_radius=4)
    if opened:
        pygame.draw.ellipse(surface, GOLD, (base.x + 4, base.y - 6, base.width - 8, 12))
        lid = pygame.Rect(base.x, base.y - rect.height // 3 - 6, base.width, rect.height // 4)
        pygame.draw.rect(surface, (120, 70, 34), lid, border_radius=4)
        pygame.draw.rect(surface, (90, 50, 24), lid, width=2, border_radius=4)
        for index in range(3):
            angle = time_value * 3 + index * 2.1
            sparkle = (int(base.centerx + math.cos(angle) * 12), int(base.y - 10 + math.sin(angle * 1.3) * 6))
            pygame.draw.circle(surface, (255, 245, 180), sparkle, 2)
    else:
        lid = pygame.Rect(base.x, base.y - rect.height // 4, base.width, rect.height // 4 + 2)
        pygame.draw.rect(surface, (160, 96, 46), lid, border_top_left_radius=8, border_top_right_radius=8)
        pygame.draw.rect(surface, (90, 50, 24), lid, width=2, border_top_left_radius=8, border_top_right_radius=8)
    band = pygame.Rect(base.centerx - 4, base.y - (0 if opened else rect.height // 4), 8, base.height + (0 if opened else rect.height // 4))
    pygame.draw.rect(surface, GOLD, band)
    if not opened:
        pygame.draw.rect(surface, GOLD_DARK, (base.centerx - 5, base.y - 3, 10, 8), border_radius=2)


# ---------------------------------------------------------------- map atmosphere
AMBIENT_SEEDS = [
    (random.Random(index).random(), random.Random(index * 7 + 3).random(), random.Random(index * 13 + 5).random())
    for index in range(48)
]


def draw_ambient(surface: pygame.Surface, area: pygame.Rect, kind: str, time_value: float) -> None:
    """Hạt không khí theo kiểu bản đồ (tuyết, bụi, đom đóm...), tính thẳng từ thời gian - không cần lưu trạng thái."""
    if not kind:
        return
    previous_clip = surface.get_clip()
    surface.set_clip(area)
    for seed_x, seed_y, seed_speed in AMBIENT_SEEDS:
        if kind == "snow":
            speed = 18 + 30 * seed_speed
            x = area.x + (seed_x * area.width + 14 * math.sin(time_value * 1.3 + seed_y * 9)) % area.width
            y = area.y + (seed_y * area.height + time_value * speed) % area.height
            pygame.draw.circle(surface, (235, 245, 255), (int(x), int(y)), 2 if seed_speed > 0.5 else 1)
        elif kind == "dust":
            speed = 12 + 22 * seed_speed
            x = area.x + (seed_x * area.width + time_value * speed) % area.width
            y = area.y + (seed_y * area.height + 6 * math.sin(time_value + seed_x * 7)) % area.height
            dot = pygame.Surface((3, 3), pygame.SRCALPHA)
            dot.fill((240, 210, 150, 110))
            surface.blit(dot, (int(x), int(y)))
        elif kind == "leaves":
            if seed_speed < 0.6:
                continue
            speed = 16 + 18 * seed_speed
            x = area.x + (seed_x * area.width + time_value * speed * 0.6) % area.width
            y = area.y + (seed_y * area.height + time_value * speed) % area.height
            sway = math.sin(time_value * 2 + seed_x * 11)
            pygame.draw.ellipse(surface, (110, 190, 90), (int(x + 6 * sway), int(y), 6, 3))
        elif kind == "fireflies":
            if seed_speed < 0.45:
                continue
            x = area.x + seed_x * area.width + 22 * math.sin(time_value * 0.7 + seed_y * 13)
            y = area.y + seed_y * area.height + 16 * math.cos(time_value * 0.9 + seed_x * 17)
            glow = 0.5 + 0.5 * math.sin(time_value * 3 + seed_speed * 20)
            halo = pygame.Surface((14, 14), pygame.SRCALPHA)
            pygame.draw.circle(halo, (200, 255, 120, int(70 * glow)), (7, 7), 7)
            surface.blit(halo, (int(x) - 7, int(y) - 7))
            pygame.draw.circle(surface, (230, 255, 160), (int(x), int(y)), 1 + int(glow + 0.5))
        elif kind == "sparkle":
            twinkle = math.sin(time_value * 2.5 + seed_speed * 30)
            if twinkle < 0.3:
                continue
            x = area.x + seed_x * area.width
            y = area.y + seed_y * area.height
            size = int(2 + 3 * twinkle)
            color = (230, 200, 255)
            pygame.draw.line(surface, color, (x - size, y), (x + size, y))
            pygame.draw.line(surface, color, (x, y - size), (x, y + size))
    surface.set_clip(previous_clip)


def make_vignette(size: tuple[int, int], strength: int = 120) -> pygame.Surface:
    """Viền tối mềm quanh khung bản đồ để mắt tập trung vào giữa."""
    small = pygame.Surface((40, 24), pygame.SRCALPHA)
    for x in range(40):
        for y in range(24):
            distance = math.hypot((x - 19.5) / 19.5, (y - 11.5) / 11.5) / math.sqrt(2)
            alpha = int(strength * max(0.0, distance - 0.35) / 0.65) if distance > 0.35 else 0
            small.set_at((x, y), (0, 0, 0, min(255, alpha)))
    return pygame.transform.smoothscale(small, size)


def make_soft_ellipse(size: tuple[int, int], color: tuple[int, int, int], alpha: int) -> pygame.Surface:
    """Hình elip mờ dần ra mép (bóng đổ, quầng sáng)."""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    steps = 6
    for step in range(steps):
        fraction = 1 - step / steps
        rect = pygame.Rect(0, 0, int(size[0] * fraction), int(size[1] * fraction))
        rect.center = (size[0] // 2, size[1] // 2)
        pygame.draw.ellipse(surface, (*color, alpha // steps), rect)
    return surface


def make_edge_shadow(width: int, height: int, alpha: int, vertical: bool) -> pygame.Surface:
    """Dải bóng mờ dần: tường đổ bóng xuống sàn."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    length = height if vertical else width
    for index in range(length):
        value = int(alpha * (1 - index / length) ** 2)
        if vertical:
            pygame.draw.line(surface, (0, 0, 0, value), (0, index), (width - 1, index))
        else:
            pygame.draw.line(surface, (0, 0, 0, value), (index, 0), (index, height - 1))
    return surface


# ======================================================================
# sound.py
# ======================================================================

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


# ======================================================================
# music.py
# ======================================================================

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


# ======================================================================
# progress.py
# ======================================================================

FORMAT_VERSION = 3
# Giá nhân vật ở bản 1.3 - 1.4 (nay miễn phí, xu được trả lại khi mở tiến độ cũ).
OLD_SKIN_PRICES: dict[str, int] = {"skin2": 120, "skin3": 220}
# Xu thưởng cho mỗi sao (giữ giống rewards.STAR_COINS).
STAR_COINS = 10
BACKUP_NAME = "tien-do.json"


def _read(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def _skin_refund(data: dict[str, Any]) -> int:
    """Nhân vật từng phải mua (trước bản 1.5) nay miễn phí: trả lại số xu đã tiêu."""
    if int(data.get("format", 1) or 1) >= 3:
        return 0
    owned = {str(item) for item in data.get("owned", [])}
    return sum(price for item_id, price in OLD_SKIN_PRICES.items() if item_id in owned)


class Progress:
    def __init__(self, main_file: Path, backup_dir: Path | None = None) -> None:
        self.main_file = main_file
        self.backup_dir = backup_dir
        self.completed: set[str] = set()
        self.code: dict[str, str] = {}
        self.stars: dict[str, int] = {}
        self.coins = 0
        self.owned: set[str] = set()
        self.skin = "skin1"
        self.chests: set[int] = set()
        self.loot: dict[str, int] = {}
        self.muted = False
        self.music_on = True
        self.hero_picked = False
        self.restored_from_backup = False
        self._load()

    # ------------------------------------------------------------ loading
    @property
    def backup_file(self) -> Path | None:
        return self.backup_dir / BACKUP_NAME if self.backup_dir else None

    def _load(self) -> None:
        data = _read(self.main_file)
        if data is None:
            data = _read(self.main_file.with_name(self.main_file.name + ".bak"))
        if data is None and self.backup_file is not None:
            data = _read(self.backup_file)
            self.restored_from_backup = data is not None and bool(data.get("completed") or data.get("code"))
        if data is not None:
            self._merge(data)

    def _merge(self, data: dict[str, Any]) -> int:
        """Merge saved data into this progress. Returns how many new completed levels were added."""
        before = len(self.completed)
        self.completed |= {str(level_id) for level_id in data.get("completed", [])}
        for level_id, text in dict(data.get("code", {})).items():
            if isinstance(text, str) and level_id not in self.code:
                self.code[str(level_id)] = text
        for level_id, count in dict(data.get("stars", {})).items():
            if isinstance(count, int):
                self.stars[str(level_id)] = max(self.stars.get(str(level_id), 0), min(3, count))
        if isinstance(data.get("coins"), int):
            self.coins = max(self.coins, data["coins"] + _skin_refund(data))
        self.owned |= {str(item) for item in data.get("owned", [])}
        self.chests |= {int(world) for world in data.get("chests", []) if str(world).isdigit()}
        if self.skin == "skin1" and isinstance(data.get("skin"), str):
            self.skin = data["skin"]
        for level_id, count in dict(data.get("loot", {})).items():
            if isinstance(count, int):
                self.loot[str(level_id)] = max(self.loot.get(str(level_id), 0), count)
        if isinstance(data.get("muted"), bool):
            self.muted = data["muted"]
        if isinstance(data.get("music_on"), bool):
            self.music_on = data["music_on"]
        if data.get("hero_picked") is True:
            self.hero_picked = True
        self._migrate_old_wins()
        return len(self.completed) - before

    def _migrate_old_wins(self) -> None:
        """Levels finished in versions before stars existed count as 1 star (and its coins)."""
        for level_id in self.completed:
            if level_id not in self.stars:
                self.stars[level_id] = 1
                self.coins += STAR_COINS

    # ------------------------------------------------------------ saving
    def to_json(self) -> str:
        data = {
            "app": "OneSpace CodeQuest",
            "format": FORMAT_VERSION,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "completed": sorted(self.completed),
            "code": self.code,
            "stars": self.stars,
            "coins": self.coins,
            "owned": sorted(self.owned),
            "skin": self.skin,
            "chests": sorted(self.chests),
            "loot": self.loot,
            "muted": self.muted,
            "music_on": self.music_on,
            "hero_picked": self.hero_picked,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def save(self) -> None:
        text = self.to_json()
        if self.main_file.exists():
            try:
                os.replace(self.main_file, self.main_file.with_name(self.main_file.name + ".bak"))
            except OSError:
                pass
        _write_atomic(self.main_file, text)
        if self.backup_file is not None:
            try:
                _write_atomic(self.backup_file, text)
            except OSError:
                pass

    def export_backup(self) -> Path | None:
        """Write the backup copy now. Returns its path, or None if there is no backup folder."""
        if self.backup_file is None:
            return None
        _write_atomic(self.backup_file, self.to_json())
        return self.backup_file

    def restore_backup(self) -> int | None:
        """Merge the backup copy into current progress. Returns new completed levels, or None if no backup."""
        if self.backup_file is None:
            return None
        data = _read(self.backup_file)
        if data is None:
            return None
        added = self._merge(data)
        self.save()
        return added


# ======================================================================
# store_view.py
# ======================================================================

if TYPE_CHECKING:
    from .game import App

STORE_COLOR_TEXT = (230, 232, 240)
STORE_COLOR_MUTED = (150, 156, 180)
STORE_COLOR_ACCENT = (255, 196, 64)
STORE_COLOR_GOOD = (90, 220, 120)
PANEL = pygame.Rect(40, 20, 1200, 690)
SHOP_X = 700
ITEM_HEIGHT = 92


class StoreView:
    def __init__(self, app: App) -> None:
        self.app = app
        self.buttons: list[Any] = []

    # ------------------------------------------------------------ actions
    def build(self) -> None:
        make_button = self.app.make_button
        progress = self.app.progress
        self.buttons = [make_button(pygame.Rect(64, 36, 110, 38), "← Menu", self.app.go_menu)]
        for index, item in enumerate(SHOP_ITEMS):
            rect = pygame.Rect(PANEL.right - 150, 130 + index * ITEM_HEIGHT + 24, 120, 40)
            label, color, action = self._button_for(item, progress)
            self.buttons.append(make_button(rect, label, action, color))

    def _button_for(self, item: ShopItem, progress: Any) -> tuple[str, tuple[int, int, int], Any]:
        owned = item.price == 0 or item.id in progress.owned
        if item.kind == "skin" and owned:
            if progress.skin == item.id:
                return "Đang dùng", (46, 120, 90), lambda: None
            return "Dùng", (70, 80, 120), lambda item_id=item.id: self._equip(item_id)
        if owned:
            return "Đã có", (46, 120, 90), lambda: None
        ok, _ = can_buy(progress, item)
        color = (150, 110, 40) if ok else (64, 66, 86)
        return f"Mua {item.price}", color, lambda chosen=item: self._buy(chosen)

    def _buy(self, item: ShopItem) -> None:
        ok, reason = can_buy(self.app.progress, item)
        if not ok:
            self.app.show_toast(f"Chưa mua được {item.name}: {reason}.")
            self.app.sound.play("fail")
            return
        buy(self.app.progress, item)
        self.app.progress.save()
        self.app.sound.play("coin")
        self.app.show_toast(f"Đã mua {item.name}!")
        self.build()

    def _equip(self, item_id: str) -> None:
        equip_skin(self.app.progress, item_id)
        self.app.progress.save()
        self.app.sound.play("click")
        self.build()

    def handle_event(self, event: pygame.event.Event) -> None:
        for button in self.buttons:
            if button.handle_event(event):
                return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.go_menu()

    # ------------------------------------------------------------ drawing
    def draw(self, surface: pygame.Surface) -> None:
        app = self.app
        progress = app.progress
        app.draw_background(5)
        pygame.draw.rect(surface, (22, 24, 34), PANEL, border_radius=10)
        pygame.draw.rect(surface, (60, 66, 92), PANEL, width=2, border_radius=10)

        title = app.font_title.render("Bộ sưu tập & Cửa hàng", True, STORE_COLOR_ACCENT)
        surface.blit(title, (196, 36))

        stars = total_stars(progress)
        max_stars = 3 * len(all_levels())
        rank, next_threshold = rank_for(stars)
        box = pygame.Rect(64, 96, SHOP_X - 90, 150)
        pygame.draw.rect(surface, (30, 34, 50), box, border_radius=10)
        surface.blit(app.font_bold.render(f"Cấp bậc: {rank}", True, STORE_COLOR_ACCENT), (box.x + 18, box.y + 14))
        draw_star(surface, (box.x + 30, box.y + 66), 13, True)
        surface.blit(app.font.render(f"{stars} / {max_stars} sao", True, STORE_COLOR_TEXT), (box.x + 52, box.y + 54))
        draw_coin(surface, (box.x + 250, box.y + 66), 12)
        surface.blit(app.font.render(f"{progress.coins} xu", True, STORE_COLOR_TEXT), (box.x + 270, box.y + 54))
        bar = pygame.Rect(box.x + 18, box.y + 100, box.width - 36, 16)
        pygame.draw.rect(surface, (50, 54, 72), bar, border_radius=8)
        if next_threshold is None:
            fill, caption = 1.0, "Cấp bậc cao nhất!"
        else:
            previous = max(threshold for threshold, _ in RANKS if threshold <= stars)
            fill = (stars - previous) / max(1, next_threshold - previous)
            caption = f"Còn {next_threshold - stars} sao để lên cấp tiếp theo"
        pygame.draw.rect(surface, STORE_COLOR_GOOD, (bar.x, bar.y, int(bar.width * fill), bar.height), border_radius=8)
        surface.blit(app.font_small.render(caption, True, STORE_COLOR_MUTED), (bar.x, bar.bottom + 4))

        surface.blit(app.font_bold.render("Huy hiệu World", True, STORE_COLOR_ACCENT), (64, 262))
        hint = app.font_small.render("Qua đủ 5 màn một World để mở rương và nhận huy hiệu.", True, STORE_COLOR_MUTED)
        surface.blit(hint, (64, 288))
        for index, world in enumerate(WORLDS):
            column, row = index % 8, index // 8
            center = (100 + column * 72, 360 + row * 104)
            earned = world.number in progress.chests
            draw_medal(surface, center, 26, str(world.number), app.font_bold, STAGE_COLORS[world.stage], earned)
            name = app._fit_text(world.title, 68)
            caption = app.font_small.render(name, True, STORE_COLOR_TEXT if earned else STORE_COLOR_MUTED)
            surface.blit(caption, caption.get_rect(midtop=(center[0], center[1] + 32)))

        surface.blit(app.font_bold.render("Cửa hàng", True, STORE_COLOR_ACCENT), (SHOP_X, 96))
        for index, item in enumerate(SHOP_ITEMS):
            row = pygame.Rect(SHOP_X, 130 + index * ITEM_HEIGHT, PANEL.right - SHOP_X - 20, ITEM_HEIGHT - 10)
            pygame.draw.rect(surface, (30, 34, 50), row, border_radius=10)
            icon_center = (row.x + 44, row.centery)
            if item.kind == "skin":
                frames = app.assets.hero_skin(item.skin_number)["idle"]
                image = frames[int(app.time * 10) % len(frames)]
                surface.blit(image, image.get_rect(center=icon_center))
            elif item.kind == "heart":
                draw_heart(surface, icon_center, 16, (255, 98, 98))
            else:
                draw_shield(surface, icon_center, 16)
            surface.blit(app.font_bold.render(item.name, True, STORE_COLOR_TEXT), (row.x + 90, row.y + 14))
            surface.blit(app.font_small.render(item.description, True, STORE_COLOR_MUTED), (row.x + 90, row.y + 44))

        for button in self.buttons:
            button.draw(surface, app.font_small if len(button.label) > 8 else app.font)
        app.draw_toast()


# ======================================================================
# hero_view.py
# ======================================================================

if TYPE_CHECKING:
    from .game import App

HERO_COLOR_TEXT = (230, 232, 240)
HERO_COLOR_MUTED = (150, 156, 180)
HERO_COLOR_ACCENT = (255, 196, 64)
HERO_COLOR_GOOD = (90, 220, 120)
HERO_PANEL = pygame.Rect(40, 20, 1200, 690)
GRID_LEFT = 64
GRID_TOP = 120
COLUMNS = 5
CARD_SIZE = (168, 176)
CARD_GAP = 12
PREVIEW = pygame.Rect(GRID_LEFT + COLUMNS * (CARD_SIZE[0] + CARD_GAP) + 8, GRID_TOP, 0, 552)
PREVIEW.width = HERO_PANEL.right - 24 - PREVIEW.x


def card_rect(index: int) -> pygame.Rect:
    row, column = divmod(index, COLUMNS)
    return pygame.Rect(
        GRID_LEFT + column * (CARD_SIZE[0] + CARD_GAP), GRID_TOP + row * (CARD_SIZE[1] + CARD_GAP), *CARD_SIZE
    )


def wrap_words(text: str, font: pygame.font.Font, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class HeroView:
    def __init__(self, app: App) -> None:
        self.app = app
        self.buttons: list[Any] = []
        self.first_time = False

    def build(self, first_time: bool = False) -> None:
        self.first_time = first_time
        make_button = self.app.make_button
        start_label = "Bắt đầu chơi →" if first_time else "Xong →"
        self.buttons = [
            make_button(pygame.Rect(PREVIEW.x + 20, PREVIEW.bottom - 64, PREVIEW.width - 40, 48), start_label,
                        self.finish, (46, 140, 86)),
        ]
        if not first_time:
            self.buttons.append(make_button(pygame.Rect(64, 36, 110, 38), "← Menu", self.finish))

    # ------------------------------------------------------------ actions
    def finish(self) -> None:
        self.app.progress.hero_picked = True
        self.app.progress.save()
        self.app.sound.play("click")
        self.app.go_menu()

    def _is_owned(self, hero: HeroStyle) -> bool:
        return hero.price == 0 or hero.item_id in self.app.progress.owned

    def choose(self, hero: HeroStyle) -> None:
        progress = self.app.progress
        if self._is_owned(hero):
            equip_skin(progress, hero.item_id)
            progress.save()
            self.app.sound.play("click")
            return
        item = ITEMS_BY_ID[hero.item_id]
        ok, reason = can_buy(progress, item)
        if not ok:
            self.app.show_toast(f"{hero.name} là nhân vật hiếm: {reason}. Qua màn để nhận thêm xu!")
            self.app.sound.play("fail")
            return
        buy(progress, item)
        progress.save()
        self.app.sound.play("coin")
        self.app.show_toast(f"Đã mở khoá {hero.name}!")

    def handle_event(self, event: pygame.event.Event) -> None:
        for button in self.buttons:
            if button.handle_event(event):
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, hero in enumerate(HEROES):
                if card_rect(index).collidepoint(event.pos):
                    self.choose(hero)
                    return
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.finish()

    # ------------------------------------------------------------ drawing
    def _hero_frame(self, number: int, state: str, scale: float) -> pygame.Surface:
        frames = self.app.assets.hero_skin(number)[state]
        frame = frames[int(self.app.time * 10) % len(frames)]
        if scale == 1:
            return frame
        size = (round(frame.get_width() * scale), round(frame.get_height() * scale))
        return pygame.transform.scale(frame, size)

    def draw(self, surface: pygame.Surface) -> None:
        app = self.app
        progress = app.progress
        app.draw_background(2)
        pygame.draw.rect(surface, (22, 24, 34), HERO_PANEL, border_radius=10)
        pygame.draw.rect(surface, (60, 66, 92), HERO_PANEL, width=2, border_radius=10)

        title_x = 64 if self.first_time else 196
        surface.blit(app.font_title.render("Chọn nhân vật của em", True, HERO_COLOR_ACCENT), (title_x, 34))
        subtitle = "Bấm vào một nhân vật để chọn. Nhân vật hiếm mở khoá bằng xu kiếm được khi qua màn."
        surface.blit(app.font_small.render(subtitle, True, HERO_COLOR_MUTED), (title_x, 76))
        draw_coin(surface, (HERO_PANEL.right - 120, 52), 11)
        surface.blit(app.font_bold.render(f"{progress.coins} xu", True, HERO_COLOR_TEXT), (HERO_PANEL.right - 102, 40))

        current = skin_number(progress)
        hovered_point = mouse_pos()
        for index, hero in enumerate(HEROES):
            rect = card_rect(index)
            selected = hero.number == current
            owned = self._is_owned(hero)
            base_color = (34, 40, 58) if owned else (28, 30, 42)
            if rect.collidepoint(hovered_point):
                base_color = tuple(channel + 16 for channel in base_color)
            pygame.draw.rect(surface, base_color, rect, border_radius=12)
            border = HERO_COLOR_GOOD if selected else (HERO_COLOR_ACCENT if hero.price else (60, 66, 92))
            pygame.draw.rect(surface, border, rect, width=3 if selected else 1, border_radius=12)

            image = self._hero_frame(hero.number, "idle" if selected else "jump", 1.4)
            if not owned:
                image = image.copy()
                image.fill((90, 90, 110), special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(image, image.get_rect(midbottom=(rect.centerx, rect.y + 120)))

            name = app._fit_text(hero.name, rect.width - 12)
            label = app.font_bold.render(name, True, HERO_COLOR_TEXT)
            surface.blit(label, label.get_rect(midtop=(rect.centerx, rect.y + 124)))
            if selected:
                status, status_color = "Đang dùng", HERO_COLOR_GOOD
            elif owned:
                status, status_color = "Miễn phí" if hero.price == 0 else "Đã mở khoá", HERO_COLOR_MUTED
            else:
                status, status_color = f"Hiếm · {hero.price} xu", HERO_COLOR_ACCENT
            status_text = app.font_small.render(status, True, status_color)
            surface.blit(status_text, status_text.get_rect(midtop=(rect.centerx, rect.y + 150)))

        self._draw_preview(surface, current)
        for button in self.buttons:
            button.draw(surface, app.font_bold)
        app.draw_toast()

    def _draw_preview(self, surface: pygame.Surface, current: int) -> None:
        app = self.app
        hero = next((style for style in HEROES if style.number == current), HEROES[0])
        pygame.draw.rect(surface, (30, 34, 50), PREVIEW, border_radius=12)
        # Nền xem trước đổi lần lượt qua các kiểu bản đồ.
        theme = THEMES[int(app.time / 3) % len(THEMES)]
        floor, wall = app.assets.theme_tiles(theme)
        caption = app.font_small.render(f"Bản đồ: {theme.name}", True, HERO_COLOR_MUTED)
        surface.blit(caption, caption.get_rect(midtop=(PREVIEW.centerx, PREVIEW.y + 14)))
        stage_top = PREVIEW.y + 250
        for x in range(PREVIEW.x + 12, PREVIEW.right - 12 - floor.get_width() + 1, floor.get_width()):
            surface.blit(wall, (x, stage_top + floor.get_height()))
            surface.blit(floor, (x, stage_top))
        state = "run" if int(app.time) % 4 < 2 else "idle"
        image = self._hero_frame(hero.number, state, 2.4)
        surface.blit(image, image.get_rect(midbottom=(PREVIEW.centerx, stage_top + floor.get_height() - 4)))
        name = app.font_title.render(hero.name, True, HERO_COLOR_ACCENT)
        surface.blit(name, name.get_rect(midtop=(PREVIEW.centerx, stage_top + 2 * floor.get_height() + 20)))
        lines = wrap_words(hero.description, app.font, PREVIEW.width - 40)
        for line_index, line in enumerate(lines):
            text = app.font.render(line, True, HERO_COLOR_TEXT)
            surface.blit(text, text.get_rect(midtop=(PREVIEW.centerx, stage_top + 2 * floor.get_height() + 64
                                                     + line_index * 24)))


# ======================================================================
# game.py
# ======================================================================

SCREEN_SIZE = (1280, 720)
FPS = 60
PROGRESS_FILE = user_data_dir() / "progress.json"

VIEW_RECT = pygame.Rect(16, 64, 736, 440)
# Vùng vẽ bản đồ trong khung (chừa chỗ cho tim / sao ở trên và tên bản đồ ở dưới).
MAP_AREA = pygame.Rect(VIEW_RECT.x + 16, VIEW_RECT.y + 40, VIEW_RECT.width - 32, VIEW_RECT.height - 70)
MAP_MAX_SCALE = 2.0
# Chừa một hàng phía trên cho nhân vật / cúp cao hơn một ô.
MAP_TOP_PAD = 48
CONSOLE_RECT = pygame.Rect(16, 516, 736, 188)
THEORY_RECT = pygame.Rect(16, 64, 736, 640)
MENU_LEFT = 64
MENU_TAB_Y = 132
MENU_TAB_WIDTH = 224
MENU_WORLDS_Y = 340
MENU_ROWS_PER_COLUMN = 5
MENU_LEVELS_OFFSET = 232
MENU_LEVEL_WIDTH = 52
INFO_RECT = pygame.Rect(768, 64, 496, 196)
EDITOR_RECT = pygame.Rect(768, 270, 496, 372)
BUTTON_Y = 652

COLOR_PANEL = (22, 24, 34)
COLOR_PANEL_BORDER = (60, 66, 92)
COLOR_TEXT = (230, 232, 240)
COLOR_MUTED = (150, 156, 180)
COLOR_ACCENT = (255, 196, 64)
COLOR_GOOD = (90, 220, 120)
COLOR_BAD = (255, 98, 98)
COLOR_INFO = (130, 200, 255)

EVENT_DURATIONS: dict[str, float] = {
    "move": 0.22,
    "bump": 0.25,
    "attack": 0.35,
    "say": 0.7,
    "print": 0.15,
    "info": 0.2,
    "hurt": 0.4,
    "heal": 0.5,
    "shield": 0.4,
    "box_break": 0.3,
    "gem_reveal": 0.15,
    "key": 0.15,
    "unlock": 0.35,
    "chest_open": 0.5,
    "gem": 0.05,
    "door_open": 0.3,
    "jam": 0.35,
    "die": 0.8,
    "fail": 0.1,
}


def wrap_text(text: str, font: pygame.font.Font, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split(" "):
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        lines.append(current)
    return lines


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, alpha: int = 225) -> None:
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*COLOR_PANEL, alpha), panel.get_rect(), border_radius=10)
    surface.blit(panel, rect.topleft)
    pygame.draw.rect(surface, COLOR_PANEL_BORDER, rect, width=2, border_radius=10)


class Button:
    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        on_click: Callable[[], None],
        color: tuple[int, int, int] = (70, 80, 120),
    ) -> None:
        self.rect = rect
        self.label = label
        self.on_click = on_click
        self.color = color

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.on_click()
            return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        hovered = self.rect.collidepoint(mouse_pos())
        color = tuple(min(255, channel + 30) for channel in self.color) if hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255, 40), self.rect, width=1, border_radius=8)
        label = font.render(self.label, True, COLOR_TEXT)
        surface.blit(label, label.get_rect(center=self.rect.center))


class LevelButton(Button):
    """Menu button for one level, showing the best stars earned."""

    def __init__(self, rect: pygame.Rect, label: str, on_click: Callable[[], None],
                 color: tuple[int, int, int], stars: int) -> None:
        super().__init__(rect, label, on_click, color)
        self.stars = stars

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        hovered = self.rect.collidepoint(mouse_pos())
        color = tuple(min(255, channel + 30) for channel in self.color) if hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255, 40), self.rect, width=1, border_radius=8)
        label = font.render(self.label, True, COLOR_TEXT)
        surface.blit(label, label.get_rect(center=(self.rect.centerx, self.rect.centery - 6)))
        draw_star_row(surface, (self.rect.centerx, self.rect.bottom - 9), 5, self.stars)


class Playback:
    """Replays recorded engine events as an animation."""

    def __init__(
        self,
        level: Level,
        bonus_hp: int = 0,
        shield: bool = False,
        sound: Callable[[str], None] | None = None,
    ) -> None:
        self.level = level
        self.bonus_hp = bonus_hp
        self.has_shield = shield and upgrades_apply(level)
        self.sound = sound or (lambda name: None)
        self.terrain_world = World(level)
        self.events: list[dict[str, Any]] = []
        self.result: RunResult | None = None
        self.reset()

    def reset(self) -> None:
        world = self.terrain_world
        self.hero_position = pygame.Vector2(world.hero_start)
        self.facing = "right"
        self.hp, self.max_hp = hero_hp_limits(self.level, self.bonus_hp)
        self.shield = self.has_shield
        self.gems = dict(world.gems)
        self.enemies = {pos: enemy.kind for pos, enemy in world.enemies.items()}
        self.doors = dict(world.doors)
        self.crates = dict(world.crates)
        self.keys_on_map = set(world.keys_on_map)
        self.locks = set(world.locks)
        self.chests = dict(world.chests)
        self.hero_keys = 0
        self.breaking: dict[tuple[int, int], tuple[bool, float]] = {}
        self.dying_enemies: dict[tuple[int, int], tuple[str, float]] = {}
        self.enemy_flash: dict[tuple[int, int], float] = {}
        self.door_shake: dict[tuple[int, int], float] = {}
        self.bubble: tuple[str, float] | None = None
        self.floaters: list[list[Any]] = []
        self.hero_state = "idle"
        self.hero_state_time = 0.0
        self.dead = False
        self.events = []
        self.index = 0
        self.event_time = 0.0
        self.event_started = False
        self.finished = True
        self.result = None

    def start(self, result: RunResult) -> None:
        self.reset()
        self.result = result
        self.events = result.events
        self.finished = False

    def update(self, delta_seconds: float, speed: float, log: Callable[[str, tuple[int, int, int]], None]) -> bool:
        """Advance the animation. Returns True on the frame the playback ends."""
        self.hero_state_time += delta_seconds
        self._update_effects(delta_seconds)
        if self.finished:
            return False

        scaled = delta_seconds * speed
        while scaled > 0 and self.index < len(self.events):
            event = self.events[self.index]
            if not self.event_started:
                self._begin(event, log)
                self.event_started = True
            duration = EVENT_DURATIONS.get(event["type"], 0.1)
            used = min(scaled, duration - self.event_time)
            self.event_time += used
            scaled -= used
            self._progress(event, self.event_time / duration)
            if self.event_time >= duration:
                self._end(event)
                self.index += 1
                self.event_time = 0.0
                self.event_started = False
            else:
                break

        if self.index >= len(self.events):
            self.finished = True
            if self.hero_state == "run":
                self._set_hero_state("idle")
            return True
        return False

    def _set_hero_state(self, state: str) -> None:
        if self.hero_state != state:
            self.hero_state = state
            self.hero_state_time = 0.0

    def _float(self, text: str, color: tuple[int, int, int], position: pygame.Vector2) -> None:
        self.floaters.append([text, color, pygame.Vector2(position), 1.0])

    def _begin(self, event: dict[str, Any], log: Callable[[str, tuple[int, int, int]], None]) -> None:
        kind = event["type"]
        if kind == "move":
            self.facing = event["direction"]
            self._set_hero_state("run")
            self.sound("step")
        elif kind == "shield":
            self.shield = False
            self._float("Khiên!", COLOR_INFO, self.hero_position)
            log(event["text"], COLOR_INFO)
            self.sound("shield")
        elif kind == "bump":
            self.facing = event["direction"]
            self._set_hero_state("hit")
        elif kind == "attack":
            self.facing = event["direction"]
            self._set_hero_state("jump")
            target = tuple(event["target"])
            if event["hit"]:
                self.enemy_flash[target] = 0.3
                self.sound("hit")
        elif kind == "say":
            self.bubble = (event["text"], 2.2)
            log(f"Hero: {event['text']}", COLOR_ACCENT)
        elif kind == "print":
            log(event["text"], COLOR_TEXT)
        elif kind == "info":
            log(event["text"], COLOR_INFO)
        elif kind == "hurt":
            self.hp = event["hp"]
            self._set_hero_state("hit")
            self._float("-1 ♥", COLOR_BAD, self.hero_position)
            log(event["text"], COLOR_BAD)
            self.sound("hurt")
        elif kind == "heal":
            self.hp = event["hp"]
            self._float(f"+{event['amount']} ♥", COLOR_GOOD, self.hero_position)
            log(f"Hồi {event['amount']} máu.", COLOR_GOOD)
        elif kind == "gem":
            position = tuple(event["pos"])
            self.gems.pop(position, None)
            self._float("+1", COLOR_ACCENT, pygame.Vector2(position))
            self.sound("gem")
        elif kind == "door_open":
            self.doors.pop(tuple(event["pos"]), None)
            log("Cửa đã mở!", COLOR_GOOD)
            self.sound("door")
        elif kind == "jam":
            self.door_shake[tuple(event["pos"])] = 0.35
            log("DoorJammed: cửa bị kẹt!", COLOR_BAD)
        elif kind == "die":
            self._set_hero_state("hit")
            self.dead = True
        elif kind == "box_break":
            position = tuple(event["pos"])
            has_gem = self.crates.pop(position, False)
            self.breaking[position] = (has_gem, 0.4)
            self.sound("hit")
        elif kind == "gem_reveal":
            self.gems[tuple(event["pos"])] = event["color"]
            log("Thùng vỡ, lộ ra một viên ngọc!", COLOR_ACCENT)
        elif kind == "key":
            self.keys_on_map.discard(tuple(event["pos"]))
            self.hero_keys = event["keys"]
            self._float("+1 chìa", COLOR_ACCENT, pygame.Vector2(event["pos"]))
            log(f"Nhặt được chìa khoá (đang có {self.hero_keys}).", COLOR_ACCENT)
            self.sound("coin")
        elif kind == "unlock":
            self.locks.discard(tuple(event["pos"]))
            self.hero_keys = event["keys"]
            log("Đã mở cửa khoá!", COLOR_GOOD)
            self.sound("door")
        elif kind == "chest_open":
            position = tuple(event["pos"])
            self.chests[position] = True
            self._float(f"+{LOOT_COINS} xu", COLOR_ACCENT, pygame.Vector2(position))
            log(f"Mở rương báu: +{LOOT_COINS} xu (nhận khi qua màn).", COLOR_ACCENT)
            self.sound("chest")

    def _progress(self, event: dict[str, Any], fraction: float) -> None:
        if event["type"] == "move":
            source = pygame.Vector2(event["src"])
            destination = pygame.Vector2(event["dst"])
            self.hero_position = source.lerp(destination, min(1.0, fraction))

    def _end(self, event: dict[str, Any]) -> None:
        kind = event["type"]
        if kind == "move":
            self.hero_position = pygame.Vector2(event["dst"])
            next_event = self.events[self.index + 1] if self.index + 1 < len(self.events) else None
            if next_event is None or next_event["type"] not in ("move", "gem"):
                self._set_hero_state("idle")
        elif kind in ("bump", "attack", "hurt") and not self.dead:
            self._set_hero_state("idle")
        if kind == "attack" and event.get("killed"):
            target = tuple(event["target"])
            enemy_kind = self.enemies.pop(target, None)
            if enemy_kind:
                self.dying_enemies[target] = (enemy_kind, 0.5)

    def _update_effects(self, delta_seconds: float) -> None:
        if self.bubble:
            text, remaining = self.bubble
            remaining -= delta_seconds
            self.bubble = (text, remaining) if remaining > 0 else None
        for table in (self.enemy_flash, self.door_shake):
            for key in list(table):
                table[key] -= delta_seconds
                if table[key] <= 0:
                    del table[key]
        for key in list(self.breaking):
            has_gem, remaining = self.breaking[key]
            remaining -= delta_seconds
            if remaining <= 0:
                del self.breaking[key]
            else:
                self.breaking[key] = (has_gem, remaining)
        for key in list(self.dying_enemies):
            kind, remaining = self.dying_enemies[key]
            remaining -= delta_seconds
            if remaining <= 0:
                del self.dying_enemies[key]
            else:
                self.dying_enemies[key] = (kind, remaining)
        for floater in self.floaters:
            floater[3] -= delta_seconds
        self.floaters = [floater for floater in self.floaters if floater[3] > 0]


def initial_window_size() -> tuple[int, int]:
    """Largest 16:9 window that fits the screen, leaving room for the taskbar and title bar."""
    try:
        desktop_width, desktop_height = pygame.display.get_desktop_sizes()[0]
    except (pygame.error, IndexError):
        return SCREEN_SIZE
    scale = min((desktop_width - 40) / SCREEN_SIZE[0], (desktop_height - 110) / SCREEN_SIZE[1])
    return (int(SCREEN_SIZE[0] * scale), int(SCREEN_SIZE[1] * scale))


def open_window() -> pygame.Surface:
    """Open a resizable window; the game draws on a fixed 1280x720 canvas that is scaled to fit."""
    if sys.platform == "win32":
        try:
            # Ngăn Windows tự phóng to cửa sổ (125%, 150%...) làm tràn khỏi màn hình.
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass
    pygame.init()
    pygame.display.set_caption(APP_TITLE)
    icon = load_logo_icon(64)
    if icon is not None:
        pygame.display.set_icon(icon)
    return pygame.display.set_mode(initial_window_size(), pygame.RESIZABLE)


def present(canvas: pygame.Surface, window: pygame.Surface) -> None:
    scaled_size = VIEWPORT.fit(canvas.get_size(), window.get_size())
    window.fill((0, 0, 0))
    if scaled_size == canvas.get_size():
        window.blit(canvas, VIEWPORT.offset)
    else:
        window.blit(pygame.transform.smoothscale(canvas, scaled_size), VIEWPORT.offset)
    pygame.display.flip()


class App:
    def __init__(self) -> None:
        self.window = open_window()
        self.screen = pygame.Surface(SCREEN_SIZE)
        self.clock = pygame.time.Clock()
        pygame.key.start_text_input()

        self.font = pygame.font.SysFont("segoeui", 17)
        self.font_small = pygame.font.SysFont("segoeui", 15)
        self.font_bold = pygame.font.SysFont("segoeui", 19, bold=True)
        self.font_title = pygame.font.SysFont("segoeui", 30, bold=True)
        self.font_bubble = pygame.font.SysFont("segoeui", 15, bold=True)
        self.font_code = pygame.font.SysFont("consolas", 17)

        self.assets = Assets()
        self.logo = load_logo(96)
        self.progress = Progress(PROGRESS_FILE, backup_dir())
        self.sound = SoundBoard(self.progress.muted)
        self.music = MusicPlayer(self.progress.music_on)
        self.music.select(0)
        self.confetti = Confetti()
        self.win_summary: RewardSummary | None = None
        self.win_time = 0.0
        self.store = StoreView(self)
        self.hero_view = HeroView(self)
        self.editor = CodeEditor(self.font_code, self.font_small)
        self.levels = all_levels()
        self.scene = "menu"
        self.level: Level = self.levels[0]
        self.playback = self._new_playback(self.level)
        # Số thứ tự bản đồ kiểm tra ẩn đang được diễn lại (0 = bản đồ chính).
        self.hidden_shown = 0
        self._effects: dict[str, pygame.Surface] | None = None
        self._map_layer: pygame.Surface | None = None
        self.console: list[tuple[str, tuple[int, int, int]]] = []
        self.hint_index = 0
        self.speed_options = [1.0, 2.0, 4.0]
        self.speed_index = 0
        self.show_win = False
        self.show_theory = False
        self.theory_view = TheoryView(self.font, self.font_bold, self.font_title, self.font_code)
        self.time = 0.0
        self.menu_buttons: list[Button] = []
        self.play_buttons: list[Button] = []
        self.win_buttons: list[Button] = []
        self.menu_stage = self._first_unfinished_stage()
        self.menu_tool_buttons: list[Button] = []
        self._build_tool_buttons()
        self.toast: tuple[str, float] | None = None
        if self.progress.restored_from_backup:
            self.show_toast("Đã tự khôi phục tiến độ từ bản sao lưu trong Documents.")
        self._build_menu()
        if not self.progress.hero_picked:
            self.open_heroes(first_time=True)

    # ------------------------------------------------------------ scenes
    def _first_unfinished_stage(self) -> int:
        for level in self.levels:
            if level.id not in self.progress.completed:
                return world_of(level.id).stage
        return 1

    @staticmethod
    def _stage_worlds(stage_number: int) -> list[Any]:
        return [world for world in WORLDS if world.stage == stage_number]

    @staticmethod
    def make_button(
        rect: pygame.Rect, label: str, on_click: Callable[[], None], color: tuple[int, int, int] = (70, 80, 120)
    ) -> Button:
        return Button(rect, label, on_click, color)

    def _upgrades(self) -> tuple[int, bool]:
        return bonus_hp(self.progress), has_shield(self.progress)

    def _new_playback(self, level: Level) -> Playback:
        bonus_hp, shield = self._upgrades()
        return Playback(level, bonus_hp, shield, self.sound.play)

    def _build_tool_buttons(self) -> None:
        sound_label = "Âm: Tắt" if self.sound.muted else "Âm: Bật"
        self.menu_tool_buttons = [
            Button(pygame.Rect(812, 30, 196, 36), "Cửa hàng & Huy hiệu", self.open_store, (170, 120, 40)),
            Button(pygame.Rect(1016, 30, 98, 36), "Sao lưu", self.backup_progress, (46, 120, 90)),
            Button(pygame.Rect(1118, 30, 98, 36), "Khôi phục", self.restore_progress, (90, 80, 140)),
            Button(pygame.Rect(812, 72, 96, 36), sound_label, self.toggle_sound, (70, 80, 120)),
            Button(pygame.Rect(912, 72, 96, 36), self._music_label(), self.toggle_music, (110, 70, 150)),
            Button(pygame.Rect(1016, 72, 200, 36), "Nhân vật", self.open_heroes, (40, 130, 160)),
        ]

    def _music_label(self) -> str:
        return "Nhạc: Bật" if self.music.enabled else "Nhạc: Tắt"

    def toggle_music(self) -> None:
        self.music.set_enabled(not self.music.enabled)
        self.progress.music_on = self.music.enabled
        self.progress.save()
        self._build_tool_buttons()
        self._build_play_buttons()
        self.sound.play("click")
        if self.music.enabled:
            self.show_toast(f"Nhạc nền: {self.music.track_name}")

    def toggle_sound(self) -> None:
        self.sound.muted = not self.sound.muted
        self.progress.muted = self.sound.muted
        self.progress.save()
        self._build_tool_buttons()
        self._build_play_buttons()
        self.sound.play("click")

    def open_heroes(self, first_time: bool = False) -> None:
        self.save_code()
        self.scene = "heroes"
        self.hero_view.build(first_time)

    def open_store(self) -> None:
        self.save_code()
        self.scene = "store"
        self.store.build()
        self.sound.play("click")

    def select_stage(self, stage_number: int) -> None:
        self.menu_stage = stage_number
        self._build_menu()

    def show_toast(self, text: str, seconds: float = 5.0) -> None:
        self.toast = (text, seconds)

    def backup_progress(self) -> None:
        self.save_code()
        try:
            path = self.progress.export_backup()
        except OSError as error:
            self.show_toast(f"Không sao lưu được: {error}")
            return
        if path is None:
            self.show_toast("Bản chạy thử từ mã nguồn: tiến độ nằm ở progress.json trong thư mục dự án.")
            return
        self.show_toast(f"Đã sao lưu vào {path}. Có thể chép file này sang USB / máy khác.", 7.0)
        try:
            os.startfile(path.parent)  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass

    def restore_progress(self) -> None:
        added = self.progress.restore_backup()
        if added is None:
            folder = self.progress.backup_dir or "Documents/OneSpace CodeQuest"
            self.show_toast(f"Chưa có bản sao lưu. Hãy chép file tien-do.json vào {folder} rồi thử lại.", 7.0)
            return
        self._build_menu()
        self.show_toast(f"Đã khôi phục tiến độ: thêm {added} màn hoàn thành.")

    def _build_menu(self) -> None:
        self.menu_buttons = []
        for index, stage in enumerate(STAGES):
            stage_levels = [lv for world in self._stage_worlds(stage.number) for lv in world.levels]
            done = sum(lv.id in self.progress.completed for lv in stage_levels)
            rect = pygame.Rect(MENU_LEFT + index * (MENU_TAB_WIDTH + 8), MENU_TAB_Y, MENU_TAB_WIDTH, 48)
            selected = stage.number == self.menu_stage
            color = (40, 150, 180) if selected else (60, 70, 105)
            label = f"Giai đoạn {stage.number}  ·  {done}/{len(stage_levels)}"
            self.menu_buttons.append(Button(rect, label, lambda n=stage.number: self.select_stage(n), color))

        for world_index, world in enumerate(self._stage_worlds(self.menu_stage)):
            cell_x, cell_y = self._world_cell(world_index)
            for level_index, level in enumerate(world.levels):
                rect = pygame.Rect(
                    cell_x + MENU_LEVELS_OFFSET + level_index * (MENU_LEVEL_WIDTH + 6), cell_y + 2, MENU_LEVEL_WIDTH, 50
                )
                done = level.id in self.progress.completed
                color = (46, 140, 86) if done else (70, 80, 120)
                stars = self.progress.stars.get(level.id, 0)
                self.menu_buttons.append(LevelButton(rect, level.id, lambda lv=level: self.open_level(lv), color, stars))

    @staticmethod
    def _world_cell(world_index: int) -> tuple[int, int]:
        column, row = divmod(world_index, MENU_ROWS_PER_COLUMN)
        return MENU_LEFT + column * 588, MENU_WORLDS_Y + row * 72

    def _build_play_buttons(self) -> None:
        width = 76
        gap = 8
        x = EDITOR_RECT.x
        typing_label = "Gõ: VI" if self.editor.vietnamese else "Gõ: EN"
        labels = [
            ("Chạy", self.run, (46, 140, 86)),
            ("Làm lại", self.reset_code, (70, 80, 120)),
            ("Gợi ý", self.show_hint, (150, 110, 40)),
            ("Lý thuyết", self.toggle_theory, (60, 110, 160)),
            (f"x{int(self.speed_options[self.speed_index])}", self.toggle_speed, (70, 80, 120)),
            (typing_label, self.toggle_typing, (100, 70, 140)),
        ]
        self.play_buttons = []
        for index, (label, callback, color) in enumerate(labels):
            rect = pygame.Rect(x + index * (width + gap), BUTTON_Y, width, 48)
            self.play_buttons.append(Button(rect, label, callback, color))
        self.play_buttons.append(Button(pygame.Rect(16, 14, 100, 36), "← Menu", self.go_menu))
        sound_label = "Âm: Tắt" if self.sound.muted else "Âm: Bật"
        self.play_buttons.append(Button(pygame.Rect(1160, 14, 104, 36), sound_label, self.toggle_sound))
        self.play_buttons.append(Button(pygame.Rect(1050, 14, 104, 36), self._music_label(), self.toggle_music))

    def open_level(self, level: Level) -> None:
        self.save_code()
        self.level = level
        self.scene = "play"
        self.playback = self._new_playback(level)
        self.win_summary = None
        self.editor.set_text(self.progress.code.get(level.id, level.starter))
        self.editor.extra_names = list(level.extra_globals)
        self.editor.focused = True
        self.console = []
        self.hint_index = 0
        self.show_win = False
        self.hidden_shown = 0
        self.music.select(track_for_world(world_of(level.id).number))
        self.log(f"Màn {level.id}: {level.title}", COLOR_ACCENT)
        self.log("Viết code bên phải rồi bấm Chạy (hoặc Ctrl+Enter).", COLOR_MUTED)
        self.log("Bộ gõ Telex có sẵn trong dấu nháy và ghi chú (F2 để bật/tắt).", COLOR_MUTED)
        world = world_of(level.id)
        self.theory_view.build(
            title=f"Lý thuyết · {world.concept}",
            tag=f"Kỹ năng: {world.skill}  |  Giai đoạn {world.stage}",
            theory=THEORY[level.id],
            rect=THEORY_RECT,
            inputs=level.extra_globals,
            goal=level.goal,
        )
        self.show_theory = level.id not in self.progress.completed
        self._build_play_buttons()

    def go_menu(self) -> None:
        self.save_code()
        self.scene = "menu"
        self.music.select(0)
        self._build_menu()

    def next_level(self) -> None:
        index = self.levels.index(self.level)
        if index + 1 < len(self.levels):
            self.open_level(self.levels[index + 1])
        else:
            self.go_menu()

    # ------------------------------------------------------------ actions
    def log(self, text: str, color: tuple[int, int, int] = COLOR_TEXT) -> None:
        for line in wrap_text(text, self.font_small, CONSOLE_RECT.width - 24):
            self.console.append((line, color))
        self.console = self.console[-200:]

    def save_code(self) -> None:
        if self.scene == "play":
            self.progress.code[self.level.id] = self.editor.text
            self.progress.save()

    def run(self) -> None:
        self.save_code()
        self.show_theory = False
        self.show_win = False
        self.console = []
        self.log("Đang chạy...", COLOR_MUTED)
        bonus_hp, shield = self._upgrades()
        result = run_code(self.level, self.editor.text, bonus_hp, shield)
        self.editor.error_line = result.error_line
        self._show_main_map()
        self.playback.start(result)

    def _show_main_map(self) -> None:
        if self.hidden_shown:
            self.playback = self._new_playback(self.level)
            self.hidden_shown = 0

    def reset_code(self) -> None:
        self.editor.set_text(self.level.starter)
        self._show_main_map()
        self.playback.reset()
        self.console = []
        self.log("Đã khôi phục code ban đầu.", COLOR_MUTED)

    def show_hint(self) -> None:
        hints = self.level.hints
        if not hints:
            return
        hint = hints[min(self.hint_index, len(hints) - 1)]
        self.log(f"Gợi ý {min(self.hint_index, len(hints) - 1) + 1}/{len(hints)}: {hint}", COLOR_ACCENT)
        self.hint_index += 1

    def toggle_theory(self) -> None:
        self.show_theory = not self.show_theory

    def toggle_typing(self) -> None:
        self.editor.vietnamese = not self.editor.vietnamese
        state = "BẬT (chỉ trong dấu nháy và ghi chú)" if self.editor.vietnamese else "TẮT"
        self.log(f"Bộ gõ tiếng Việt Telex: {state}.", COLOR_INFO)
        self._build_play_buttons()

    def toggle_speed(self) -> None:
        self.speed_index = (self.speed_index + 1) % len(self.speed_options)
        self._build_play_buttons()

    def on_playback_finished(self) -> None:
        result = self.playback.result
        if result is None:
            return
        failure = result.hidden_failure
        if failure is not None and not self.hidden_shown:
            self.log("Bản đồ chính: đi đúng!", COLOR_GOOD)
            self.log(f"Thử tiếp code trên bản đồ kiểm tra ẩn {failure.index}...", COLOR_INFO)
            self.hidden_shown = failure.index
            self.playback = self._new_playback(failure.level)
            self.playback.start(RunResult(failure.events, False, result.message, failure.error_line))
            self.editor.error_line = failure.error_line
            return
        if result.won:
            self.log("[OK] " + result.message, COLOR_GOOD)
            if result.hidden_passed:
                self.log(f"Code còn đúng trên cả {result.hidden_passed} bản đồ kiểm tra ẩn!", COLOR_GOOD)
            world = world_of(self.level.id)
            flags = star_flags(result, self.level.id)
            summary = apply_win(self.progress, self.level, world.levels, world.number, flags, result.chests_opened)
            self.progress.save()
            self.win_summary = summary
            self.win_time = 0.0
            if not flags[1]:
                self.log(f"Sao 2: hãy thử qua màn mà không mất máu (vừa mất {result.damage_taken}).", COLOR_INFO)
            if not flags[2]:
                limit = par_for(self.level.id)
                self.log(f"Sao 3: code đang có {result.code_lines} dòng - thử rút gọn còn tối đa {limit} dòng.", COLOR_INFO)
            if summary.coins:
                self.log(f"Nhận {summary.coins} xu!", COLOR_ACCENT)
            self.sound.play("chest" if summary.chest_world else "win")
            self.confetti.burst(VIEW_RECT, 140 if summary.chest_world else 90)
            self.show_win = True
            stay = pygame.Rect(0, 0, 160, 44)
            stay.center = (VIEW_RECT.centerx - 90, VIEW_RECT.centery + 124)
            next_rect = stay.copy()
            next_rect.centerx = VIEW_RECT.centerx + 90
            self.win_buttons = [
                Button(stay, "Ở lại", self.close_win),
                Button(next_rect, "Màn tiếp →", self.next_level, (46, 140, 86)),
            ]
        else:
            self.log("[Lỗi] " + result.message, COLOR_BAD)
            self.sound.play("fail")

    def close_win(self) -> None:
        self.show_win = False

    # ------------------------------------------------------------ loop
    def run_forever(self) -> None:
        running = True
        while running:
            delta_seconds = min(self.clock.tick(FPS) / 1000, 0.05)
            self.time += delta_seconds
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(to_logical_event(event))
            self.update(delta_seconds)
            self.draw()
            present(self.screen, pygame.display.get_surface())
        self.save_code()
        pygame.quit()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.scene == "store":
            self.store.handle_event(event)
            return
        if self.scene == "heroes":
            self.hero_view.handle_event(event)
            return
        if self.scene == "menu":
            for button in [*self.menu_buttons, *self.menu_tool_buttons]:
                if button.handle_event(event):
                    return
            return

        if self.show_theory:
            outcome = self.theory_view.handle_event(event)
            if outcome == "close":
                self.show_theory = False
                return
            if outcome == "used":
                return
        elif self.show_win:
            for button in self.win_buttons:
                if button.handle_event(event):
                    return
        for button in self.play_buttons:
            if button.handle_event(event):
                return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
            self.toggle_typing()
            return
        is_enter = event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
        if is_enter and event.mod & pygame.KMOD_CTRL:
            self.run()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.editor.handle_escape():
                return
            if self.show_theory:
                self.show_theory = False
            else:
                self.go_menu()
            return
        self.editor.handle_event(event)

    def update(self, delta_seconds: float) -> None:
        self.music.update()
        self.confetti.update(delta_seconds)
        self.win_time += delta_seconds
        if self.toast is not None:
            text, remaining = self.toast
            self.toast = (text, remaining - delta_seconds) if remaining > delta_seconds else None
        if self.scene != "play":
            return
        self.editor.update(delta_seconds)
        speed = self.speed_options[self.speed_index]
        if self.playback.update(delta_seconds, speed, self.log):
            self.on_playback_finished()

    # ------------------------------------------------------------ drawing
    def draw_background(self, background_index: int) -> None:
        tile = self.assets.backgrounds[background_index]
        offset = int(self.time * 12) % tile.get_width()
        for x in range(-tile.get_width(), SCREEN_SIZE[0], tile.get_width()):
            for y in range(-tile.get_height(), SCREEN_SIZE[1], tile.get_height()):
                self.screen.blit(tile, (x + offset, y + offset))
        shade = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
        shade.fill((10, 10, 20, 120))
        self.screen.blit(shade, (0, 0))

    def draw(self) -> None:
        if self.scene == "store":
            self.store.draw(self.screen)
        elif self.scene == "heroes":
            self.hero_view.draw(self.screen)
        elif self.scene == "menu":
            self.draw_menu()
        else:
            self.draw_play()

    def draw_menu(self) -> None:
        self.draw_background(4)
        draw_panel(self.screen, pygame.Rect(40, 20, 1200, 690))
        text_left = MENU_LEFT
        if self.logo is not None:
            self.screen.blit(self.logo, (MENU_LEFT - 8, 26))
            text_left = MENU_LEFT + self.logo.get_width() + 6
        title = self.font_title.render("OneSpace CodeQuest · Python", True, COLOR_ACCENT)
        self.screen.blit(title, (text_left, 34))
        stars = total_stars(self.progress)
        rank = rank_for(stars)[0]
        draw_star(self.screen, (text_left + 12, 92), 11, True)
        stats = self.font.render(f"{stars}/{3 * len(self.levels)} sao", True, COLOR_TEXT)
        self.screen.blit(stats, (text_left + 30, 80))
        coin_x = text_left + 50 + stats.get_width()
        draw_coin(self.screen, (coin_x, 92), 10)
        coins = self.font.render(f"{self.progress.coins} xu", True, COLOR_TEXT)
        self.screen.blit(coins, (coin_x + 16, 80))
        rank_text = self.font.render(f"Cấp bậc: {rank}", True, COLOR_ACCENT)
        self.screen.blit(rank_text, (coin_x + 40 + coins.get_width(), 80))
        for button in self.menu_tool_buttons:
            button.draw(self.screen, self.font_small)

        for button in self.menu_buttons[: len(STAGES)]:
            button.draw(self.screen, self.font)

        stage = STAGES[self.menu_stage - 1]
        box = pygame.Rect(MENU_LEFT, 192, 1152, 136)
        pygame.draw.rect(self.screen, (30, 34, 50), box, border_radius=10)
        y = box.y + 10
        heading = self.font_bold.render(f"Giai đoạn {stage.number}: {stage.title}", True, COLOR_ACCENT)
        self.screen.blit(heading, (box.x + 16, y))
        domains = self.font_small.render(f"Kỹ năng: {stage.skills}", True, COLOR_INFO)
        self.screen.blit(domains, (box.x + 16 + heading.get_width() + 18, y + 4))
        y += 32
        for label, text in (("Nội dung", stage.content), ("Trọng tâm", stage.focus), ("Mốc", stage.milestone)):
            for line in wrap_text(f"{label}: {text}", self.font_small, box.width - 32):
                self.screen.blit(self.font_small.render(line, True, COLOR_TEXT), (box.x + 16, y))
                y += 21

        for world_index, world in enumerate(self._stage_worlds(self.menu_stage)):
            cell_x, cell_y = self._world_cell(world_index)
            done = sum(level.id in self.progress.completed for level in world.levels)
            label = self.font_bold.render(f"World {world.number} · {world.title}", True, COLOR_TEXT)
            concept_text = self._fit_text(f"{world.concept}  ·  {done}/{len(world.levels)} xong", MENU_LEVELS_OFFSET - 12)
            concept = self.font_small.render(concept_text, True, COLOR_MUTED)
            self.screen.blit(label, (cell_x, cell_y))
            self.screen.blit(concept, (cell_x, cell_y + 26))

        for button in self.menu_buttons[len(STAGES):]:
            button.draw(self.screen, self.font)
        self.draw_toast()

    def draw_toast(self) -> None:
        if self.toast is None:
            return
        lines = wrap_text(self.toast[0], self.font, 900)
        box = pygame.Rect(0, 0, 940, 20 + 24 * len(lines))
        box.midbottom = (SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] - 24)
        pygame.draw.rect(self.screen, (20, 70, 60), box, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_GOOD, box, width=2, border_radius=10)
        for index, line in enumerate(lines):
            rendered = self.font.render(line, True, COLOR_TEXT)
            self.screen.blit(rendered, (box.x + 20, box.y + 10 + index * 24))

    def _fit_text(self, text: str, width: int) -> str:
        """Shorten text with "…" so it fits in `width` pixels."""
        if self.font_small.size(text)[0] <= width:
            return text
        while text and self.font_small.size(text + "…")[0] > width:
            text = text[:-1]
        return text + "…"

    def draw_play(self) -> None:
        world_info = world_of(self.level.id)
        self.draw_background(world_info.background)

        header = self.font_bold.render(
            f"Giai đoạn {world_info.stage} · World {world_info.number}: {world_info.title}   —   Màn {self.level.id}: {self.level.title}",
            True,
            COLOR_TEXT,
        )
        self.screen.blit(header, (132, 20))

        draw_panel(self.screen, VIEW_RECT, alpha=150)
        theme = theme_for_world(world_info.number)
        backdrop = pygame.Surface(VIEW_RECT.inflate(-4, -4).size, pygame.SRCALPHA)
        pygame.draw.rect(backdrop, (*theme.backdrop, 150), backdrop.get_rect(), border_radius=9)
        self.screen.blit(backdrop, VIEW_RECT.inflate(-4, -4).topleft)
        theme_label = self.font_small.render(f"Bản đồ: {theme.name}", True, COLOR_MUTED)
        self.screen.blit(theme_label, theme_label.get_rect(bottomright=(VIEW_RECT.right - 14, VIEW_RECT.bottom - 8)))
        self.draw_map()
        if self.hidden_shown:
            self._draw_hidden_banner()
        self.draw_hearts()
        self.draw_star_goals()
        if self.show_win:
            self.draw_win()
        self.confetti.draw(self.screen, VIEW_RECT)

        draw_panel(self.screen, CONSOLE_RECT)
        self.draw_console()

        draw_panel(self.screen, INFO_RECT)
        self.draw_info()

        if self.show_theory:
            self.theory_view.draw(self.screen)

        self.editor.draw(self.screen, EDITOR_RECT)
        for button in self.play_buttons:
            button.draw(self.screen, self.font_small if len(button.label) > 7 else self.font)

    def _map_origin(self) -> tuple[int, int]:
        """Gốc toạ độ khi vẽ lên lớp bản đồ (lớp này sau đó được phóng to vào khung)."""
        return 0, MAP_TOP_PAD

    def _map_layout(self) -> tuple[float, pygame.Rect]:
        """Tỉ lệ phóng và vị trí của lớp bản đồ trên màn hình - bản đồ nhỏ được phóng to cho dễ nhìn."""
        world = self.playback.terrain_world
        width, height = world.width * TILE, world.height * TILE + MAP_TOP_PAD
        scale = min(MAP_AREA.width / width, MAP_AREA.height / height, MAP_MAX_SCALE)
        rect = pygame.Rect(0, 0, round(width * scale), round(height * scale))
        rect.center = MAP_AREA.center
        return scale, rect

    def _layer_to_screen(self, point: tuple[float, float]) -> tuple[int, int]:
        scale, rect = self._map_layout()
        return round(rect.x + point[0] * scale), round(rect.y + point[1] * scale)

    def _map_effects(self) -> dict[str, pygame.Surface]:
        if self._effects is None:
            self._effects = {
                "shadow": make_soft_ellipse((TILE * 2 // 3, TILE // 5), (0, 0, 0), 150),
                "glow": make_soft_ellipse((TILE, TILE), (255, 240, 170), 90),
                "wall_top": make_edge_shadow(TILE, TILE // 3, 120, vertical=True),
                "wall_left": make_edge_shadow(TILE // 5, TILE, 80, vertical=False),
                "vignette": make_vignette(VIEW_RECT.inflate(-4, -4).size),
            }
        return self._effects

    def _draw_shadow(self, tile_x: float, tile_y: float) -> None:
        shadow = self._map_effects()["shadow"]
        origin_x, origin_y = self._map_origin()
        center = (origin_x + tile_x * TILE + TILE // 2, origin_y + (tile_y + 1) * TILE - 5)
        self.screen.blit(shadow, shadow.get_rect(center=(round(center[0]), round(center[1]))))

    def _frame(self, frames: list[pygame.Surface], fps: float = 12, time_value: float | None = None) -> pygame.Surface:
        moment = self.time if time_value is None else time_value
        return frames[int(moment * fps) % len(frames)]

    def _blit_on_tile(self, image: pygame.Surface, tile_x: float, tile_y: float, flip: bool = False) -> pygame.Rect:
        origin_x, origin_y = self._map_origin()
        if flip:
            image = pygame.transform.flip(image, True, False)
        rect = image.get_rect()
        rect.midbottom = (origin_x + tile_x * TILE + TILE // 2, origin_y + (tile_y + 1) * TILE)
        self.screen.blit(image, rect)
        return rect

    def draw_map(self) -> None:
        world = self.playback.terrain_world
        layer_size = (world.width * TILE, world.height * TILE + MAP_TOP_PAD)
        if self._map_layer is None or self._map_layer.get_size() != layer_size:
            self._map_layer = pygame.Surface(layer_size, pygame.SRCALPHA)
        self._map_layer.fill((0, 0, 0, 0))
        screen = self.screen
        self.screen = self._map_layer
        try:
            hero_rect = self._draw_map_layer()
        finally:
            self.screen = screen

        _, rect = self._map_layout()
        self.screen.blit(pygame.transform.scale(self._map_layer, rect.size), rect)
        theme = theme_for_world(world_of(self.level.id).number)
        draw_ambient(self.screen, VIEW_RECT.inflate(-4, -4), theme.ambient, self.time)
        self.screen.blit(self._map_effects()["vignette"], VIEW_RECT.inflate(-4, -4).topleft)

        playback = self.playback
        if playback.bubble:
            self.draw_bubble(playback.bubble[0], self._layer_to_screen(hero_rect.midtop))
        origin_x, origin_y = self._map_origin()
        for text, color, position, remaining in playback.floaters:
            rendered = self.font_bold.render(text, True, color)
            rendered.set_alpha(int(255 * min(1.0, remaining * 1.5)))
            rise = (1.0 - remaining) * 30
            anchor = self._layer_to_screen((origin_x + position.x * TILE + TILE // 2, origin_y + position.y * TILE))
            self.screen.blit(rendered, rendered.get_rect(center=(anchor[0], anchor[1] - rise)))

    def _draw_map_layer(self) -> pygame.Rect:
        """Vẽ ô gạch, vật thể và nhân vật lên lớp bản đồ; trả về khung của nhân vật."""
        world = self.playback.terrain_world
        playback = self.playback
        effects = self._map_effects()
        origin_x, origin_y = self._map_origin()
        floor_tile, wall_tile = self.assets.theme_tiles(theme_for_world(world_of(self.level.id).number))

        for (x, y), terrain in world.terrain.items():
            screen_position = (origin_x + x * TILE, origin_y + y * TILE)
            char = world.rows[y][x] if x < len(world.rows[y]) else " "
            if char == " ":
                continue
            if terrain == "wall":
                self.screen.blit(wall_tile, screen_position)
                continue
            self.screen.blit(floor_tile, screen_position)
            # Tường đổ bóng xuống sàn bên dưới và sang sàn bên phải: bản đồ có chiều sâu.
            if world.terrain.get((x, y - 1)) == "wall":
                self.screen.blit(effects["wall_top"], screen_position)
            if world.terrain.get((x - 1, y)) == "wall":
                self.screen.blit(effects["wall_left"], screen_position)

        for (x, y), terrain in world.terrain.items():
            if terrain == "spike":
                self._blit_on_tile(self.assets.spike, x, y)
            elif terrain == "exit":
                pulse = 1.2 + 0.2 * math.sin(self.time * 3)
                glow = effects["glow"]
                halo = pygame.transform.smoothscale(glow, (round(glow.get_width() * pulse), round(glow.get_height() * pulse)))
                center = (origin_x + x * TILE + TILE // 2, origin_y + y * TILE + TILE // 3)
                self.screen.blit(halo, halo.get_rect(center=center))
                self._draw_shadow(x, y)
                self._blit_on_tile(self._frame(self.assets.trophy, 8), x, y)

        for (x, y), kind in playback.doors.items():
            shake = 4 if (x, y) in playback.door_shake and int(self.time * 30) % 2 else 0
            image = self.assets.door_locked if kind == "locked" else self.assets.door_jammed
            self.screen.blit(image, (origin_x + x * TILE + shake, origin_y + y * TILE))

        for (x, y), has_gem in playback.crates.items():
            self._draw_shadow(x, y)
            self._blit_on_tile(self.assets.crates[2 if has_gem else 1]["idle"][0], x, y)
        for (x, y), (has_gem, remaining) in playback.breaking.items():
            image = self.assets.crates[2 if has_gem else 1]["break"][0].copy()
            image.set_alpha(int(255 * remaining / 0.4))
            self._blit_on_tile(image, x, y)
        for x, y in playback.locks:
            draw_lock_door(self.screen, pygame.Rect(origin_x + x * TILE, origin_y + y * TILE, TILE, TILE))
        for (x, y), opened in playback.chests.items():
            draw_chest(self.screen, pygame.Rect(origin_x + x * TILE, origin_y + y * TILE, TILE, TILE), opened, self.time)
        for x, y in playback.keys_on_map:
            bob = int(3 * pygame.math.Vector2(0, 1).rotate(self.time * 200 + x * 30).y)
            draw_key(self.screen, (origin_x + x * TILE + TILE // 2, origin_y + y * TILE + TILE // 2 + bob), 12)

        for (x, y), color in playback.gems.items():
            glow = effects["glow"]
            gem_center = (origin_x + x * TILE + TILE // 2, origin_y + y * TILE + TILE // 2)
            self.screen.blit(glow, glow.get_rect(center=gem_center))
            self._draw_shadow(x, y)
            bob = 3 * pygame.math.Vector2(0, 1).rotate(self.time * 180 + x * 40).y
            rect = self._blit_on_tile(self._frame(self.assets.gems[color], 10), x, y - 0.15)
            rect.y += int(bob)

        for (x, y), kind in playback.enemies.items():
            self._draw_shadow(x, y)
            frames = self.assets.enemies[kind]["hit" if (x, y) in playback.enemy_flash else "idle"]
            self._blit_on_tile(self._frame(frames, 10), x, y, flip=kind != "duck")

        for (x, y), (kind, remaining) in playback.dying_enemies.items():
            image = self._frame(self.assets.enemies[kind]["hit"], 14).copy()
            image.set_alpha(int(255 * remaining / 0.5))
            self._blit_on_tile(image, x, y, flip=kind != "duck")

        hero_frames = self.assets.hero_skin(skin_number(self.progress))[playback.hero_state]
        hero_image = self._frame(hero_frames, 16, playback.hero_state_time)
        if playback.dead:
            hero_image = hero_image.copy()
            hero_image.set_alpha(140)
        self._draw_shadow(playback.hero_position.x, playback.hero_position.y)
        return self._blit_on_tile(
            hero_image, playback.hero_position.x, playback.hero_position.y, flip=playback.facing == "left"
        )

    def draw_bubble(self, text: str, anchor: tuple[int, int]) -> None:
        lines = wrap_text(text, self.font_bubble, 220)
        width = max(self.font_bubble.size(line)[0] for line in lines) + 20
        height = len(lines) * 20 + 12
        rect = pygame.Rect(0, 0, width, height)
        rect.midbottom = (anchor[0], anchor[1] - 8)
        rect.clamp_ip(VIEW_RECT)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, border_radius=10)
        pygame.draw.polygon(
            self.screen, (255, 255, 255),
            [(anchor[0] - 6, rect.bottom - 1), (anchor[0] + 6, rect.bottom - 1), (anchor[0], rect.bottom + 8)],
        )
        for index, line in enumerate(lines):
            rendered = self.font_bubble.render(line, True, (30, 30, 40))
            self.screen.blit(rendered, (rect.x + 10, rect.y + 6 + index * 20))

    def _draw_hidden_banner(self) -> None:
        text = self.font_bold.render(f"BẢN ĐỒ KIỂM TRA ẨN {self.hidden_shown}", True, (20, 20, 30))
        banner = text.get_rect(midtop=(VIEW_RECT.centerx, VIEW_RECT.y + 44)).inflate(28, 10)
        pygame.draw.rect(self.screen, COLOR_ACCENT, banner, border_radius=8)
        self.screen.blit(text, text.get_rect(center=banner.center))

    def draw_hearts(self) -> None:
        for index in range(self.playback.max_hp):
            color = COLOR_BAD if index < self.playback.hp else (70, 70, 90)
            heart = self.font_bold.render("♥", True, color)
            self.screen.blit(heart, (VIEW_RECT.x + 12 + index * 24, VIEW_RECT.y + 8))
        next_x = VIEW_RECT.x + 24 + self.playback.max_hp * 24
        if self.playback.shield:
            draw_shield(self.screen, (next_x, VIEW_RECT.y + 20), 8)
            next_x += 26
        world = self.playback.terrain_world
        if world.keys_on_map or world.locks:
            draw_key(self.screen, (next_x + 6, VIEW_RECT.y + 20), 10)
            count = self.font_bold.render(f"x{self.playback.hero_keys}", True, COLOR_ACCENT)
            self.screen.blit(count, (next_x + 26, VIEW_RECT.y + 8))
        collected = len(self.playback.terrain_world.gems) - len(self.playback.gems)
        total = len(self.playback.terrain_world.gems)
        if total:
            gem_text = self.font_bold.render(f"Ngọc: {collected}/{total}", True, COLOR_ACCENT)
            self.screen.blit(gem_text, (VIEW_RECT.right - gem_text.get_width() - 14, VIEW_RECT.y + 8))

    def draw_star_goals(self) -> None:
        best = self.progress.stars.get(self.level.id, 0)
        goals = star_goals(self.level.id)
        pieces = [(self.font_small.render(text, True, COLOR_TEXT if index < best else COLOR_MUTED), index < best)
                  for index, text in enumerate(goals)]
        total_width = sum(image.get_width() + 26 for image, _ in pieces) + 12 * (len(pieces) - 1)
        x = VIEW_RECT.centerx - total_width // 2
        for image, achieved in pieces:
            draw_star(self.screen, (x + 9, VIEW_RECT.y + 20), 8, achieved)
            self.screen.blit(image, (x + 22, VIEW_RECT.y + 11))
            x += image.get_width() + 38

    def draw_win(self) -> None:
        summary = self.win_summary
        overlay = pygame.Surface(VIEW_RECT.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, VIEW_RECT.topleft)
        panel = pygame.Rect(0, 0, 470, 330)
        panel.center = VIEW_RECT.center
        draw_panel(self.screen, panel, alpha=245)
        title = self.font_title.render("Hoàn thành!", True, COLOR_GOOD)
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 32)))
        if summary is None:
            for button in self.win_buttons:
                button.draw(self.screen, self.font)
            return

        for index, achieved in enumerate(summary.stars):
            appear = min(1.0, max(0.0, (self.win_time - 0.25 * index) * 4))
            radius = 24 * (appear * (1.25 - 0.25 * appear)) if achieved else 22
            if achieved and appear <= 0:
                radius = 0
            center = (panel.centerx + (index - 1) * 62, panel.y + 84)
            if radius > 0:
                draw_star(self.screen, center, radius, achieved)

        y = panel.y + 122
        for achieved, text in zip(summary.stars, star_goals(self.level.id), strict=True):
            draw_star(self.screen, (panel.x + 46, y + 10), 8, achieved)
            color = COLOR_TEXT if achieved else COLOR_MUTED
            self.screen.blit(self.font_small.render(text, True, color), (panel.x + 62, y))
            y += 24

        draw_coin(self.screen, (panel.x + 48, y + 16), 11)
        coin_text = f"+{summary.coins} xu" if summary.coins else "Không có xu mới (đã nhận ở lần trước)"
        if summary.loot_coins:
            coin_text += f"  (rương: +{summary.loot_coins})"
        self.screen.blit(self.font_bold.render(coin_text, True, COLOR_ACCENT), (panel.x + 66, y + 4))
        y += 34
        if summary.chest_world is not None:
            world = WORLDS[summary.chest_world - 1]
            text = f"Mở rương World {world.number} · {world.title}: huy hiệu + {WORLD_CHEST_COINS} xu!"
            self.screen.blit(self.font_small.render(text, True, COLOR_GOOD), (panel.x + 30, y))
            y += 22
        if summary.rank_up:
            text = f"Lên cấp bậc mới: {summary.new_rank}!"
            self.screen.blit(self.font_small.render(text, True, COLOR_INFO), (panel.x + 30, y))
        for button in self.win_buttons:
            button.draw(self.screen, self.font)

    def draw_console(self) -> None:
        title = self.font_small.render("Bảng tin (print, lỗi, gợi ý)", True, COLOR_MUTED)
        self.screen.blit(title, (CONSOLE_RECT.x + 12, CONSOLE_RECT.y + 6))
        line_height = 19
        visible = (CONSOLE_RECT.height - 34) // line_height
        for index, (text, color) in enumerate(self.console[-visible:]):
            rendered = self.font_small.render(text, True, color)
            self.screen.blit(rendered, (CONSOLE_RECT.x + 12, CONSOLE_RECT.y + 30 + index * line_height))

    def draw_info(self) -> None:
        x = INFO_RECT.x + 14
        y = INFO_RECT.y + 10
        width = INFO_RECT.width - 28
        for line in wrap_text(self.level.story, self.font_small, width):
            self.screen.blit(self.font_small.render(line, True, COLOR_TEXT), (x, y))
            y += 20
        y += 6
        goal_title = self.font_bold.render("Nhiệm vụ", True, COLOR_ACCENT)
        self.screen.blit(goal_title, (x, y))
        y += 26
        for line in wrap_text(self.level.goal, self.font_small, width):
            self.screen.blit(self.font_small.render(line, True, COLOR_TEXT), (x, y))
            y += 20
        if self.level.requires:
            requirement = "Bắt buộc dùng: " + ", ".join(requirement_label(item) for item in self.level.requires)
            self.screen.blit(self.font_small.render(requirement, True, COLOR_MUTED), (x, INFO_RECT.bottom - 26))
        hidden_count = len(hidden_levels(self.level))
        if hidden_count:
            note = f"+ {hidden_count} bản đồ kiểm tra ẩn: code phải đúng cả khi bản đồ / dữ liệu thay đổi"
            self.screen.blit(self.font_small.render(note, True, COLOR_INFO), (x, INFO_RECT.bottom - 48))


def main() -> None:
    App().run_forever()

if __name__ == "__main__":
    main()
