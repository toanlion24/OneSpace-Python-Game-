"""CodeQuest - học Python Basic qua trò chơi (bản gộp một file).

Cách chạy:   pip install pygame-ce   rồi   python codequest_full.py
Cần thư mục gamekit/ (hình ảnh) nằm cùng chỗ với file này.
File được tạo tự động từ package codequest/ bằng merge_single_file.py.
"""

from __future__ import annotations

import ast
import ctypes
import json
import keyword
import os
import re
import sys
import time
import traceback
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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


class World:
    """Rules and state of one level."""

    def __init__(self, level: Level) -> None:
        self.level = level
        self.rows = level.rows
        self.height = len(level.rows)
        self.width = max(len(row) for row in level.rows)
        self.terrain: dict[tuple[int, int], str] = {}
        self.gems: dict[tuple[int, int], int] = {}
        self.enemies: dict[tuple[int, int], Enemy] = {}
        self.doors: dict[tuple[int, int], str] = {}
        self.jam_left: dict[tuple[int, int], int] = {}
        self.exit_position: tuple[int, int] = (0, 0)
        self.hero_start: tuple[int, int] = (0, 0)
        self._parse()

        self.hero_x, self.hero_y = self.hero_start
        self.facing = "right"
        self.hp = level.start_hp
        self.gems_collected = 0
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
        if pos in self.gems:
            return "gem"
        return self.terrain.get(pos, "wall")

    def is_walkable(self, pos: tuple[int, int]) -> bool:
        if pos in self.enemies or pos in self.doors:
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
        if name in ("wall", "door"):
            reason = "Đụng tường!" if name == "wall" else "Cửa đang đóng!"
            self.emit("bump", pos=origin, direction=direction)
            self.emit("info", text=reason)
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

    def use(self, item: Any) -> None:
        power = getattr(item, "power", None)
        if isinstance(power, bool) or not isinstance(power, int):
            raise TypeError("Vật phẩm cần có thuộc tính power là số nguyên (ví dụ self.power = 2).")
        self.count_action()
        healed = max(0, min(MAX_HERO_HP, self.hp + power) - self.hp)
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


def _safe_import(
    name: str,
    globals_: Any = None,
    locals_: Any = None,
    fromlist: Any = (),
    level: int = 0,
) -> Any:
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


OPERATOR_TOKENS: dict[str, type] = {"&": ast.BitAnd, "|": ast.BitOr, "-": ast.Sub, "@": ast.MatMult}


def _check_one(requirement: str, nodes: list[ast.AST], call_names: set[str], imported: set[str]) -> bool:
    if requirement.startswith("call:"):
        return requirement[5:] in call_names
    if requirement.startswith("import:"):
        return requirement[7:] in imported
    if requirement.startswith("dunder:"):
        name = requirement[7:]
        return any(isinstance(n, ast.FunctionDef) and n.name == name for n in nodes)
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


def run_code(level: Level, source: str) -> RunResult:
    """Run the player's code against a fresh world and judge the outcome."""
    world = World(level)

    try:
        tree = ast.parse(source, CODE_FILENAME)
        code = compile(tree, CODE_FILENAME, "exec")
    except SyntaxError as exc:
        return RunResult([], False, explain_syntax_error(exc), exc.lineno)

    namespace: dict[str, Any] = {
        "__builtins__": _safe_builtins(world),
        "__name__": "__main__",
        "hero": HeroAPI(world),
        "DoorJammed": DoorJammed,
    }
    namespace.update(level.extra_globals)

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
        return RunResult(world.events, False, error_message, error_line)

    problem = _judge(world, tree, level)
    if problem:
        return RunResult(world.events, False, problem)
    return RunResult(world.events, True, "Hoàn thành màn chơi!")


def _judge(world: World, tree: ast.AST, level: Level) -> str | None:
    if (world.hero_x, world.hero_y) != world.exit_position:
        return "Hero chưa tới cổng (cúp vàng). Hãy kiểm tra lại các bước đi."
    if world.gems:
        return f"Còn {len(world.gems)} viên ngọc chưa nhặt."
    if level.need_full_hp and world.hp < MAX_HERO_HP:
        return f"Hero mới có {world.hp}/{MAX_HERO_HP} máu - cần hồi đầy máu trước khi tới cúp."
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
CODE_COLOR_CURSOR = (255, 255, 255)
CODE_COLOR_BORDER_FOCUS = (98, 114, 164)

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


class CodeEditor:
    def __init__(self, font: pygame.font.Font) -> None:
        self.font = font
        self.char_width = font.size("M")[0]
        self.line_height = font.get_linesize() + 2
        self.lines: list[str] = [""]
        self.row = 0
        self.column = 0
        self.scroll = 0
        self.focused = True
        self.error_line: int | None = None
        self.undo_stack: list[tuple[list[str], int, int]] = []
        self.blink_timer = 0.0
        self.rect = pygame.Rect(0, 0, 100, 100)
        self.gutter_width = self.char_width * 4
        self.vietnamese = True

    # ------------------------------------------------------------ content
    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    def set_text(self, text: str) -> None:
        self.lines = text.replace("\t", INDENT).rstrip("\n").split("\n") or [""]
        self.row = len(self.lines) - 1
        self.column = len(self.lines[self.row])
        self.scroll = 0
        self.error_line = None
        self.undo_stack.clear()

    def _save_undo(self) -> None:
        self.undo_stack.append((list(self.lines), self.row, self.column))
        if len(self.undo_stack) > 200:
            self.undo_stack.pop(0)

    def undo(self) -> None:
        if not self.undo_stack:
            return
        self.lines, self.row, self.column = self.undo_stack.pop()

    def insert(self, text: str) -> None:
        self._save_undo()
        self.error_line = None
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
        self._split_line(auto_indent=True)

    def backspace(self) -> None:
        self._save_undo()
        self.error_line = None
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
        line = self.lines[self.row]
        if self.column < len(line):
            self.lines[self.row] = line[: self.column] + line[self.column + 1 :]
        elif self.row < len(self.lines) - 1:
            self.lines[self.row] = line + self.lines[self.row + 1]
            del self.lines[self.row + 1]

    def dedent(self) -> None:
        line = self.lines[self.row]
        if line.startswith(INDENT):
            self._save_undo()
            self.lines[self.row] = line[len(INDENT) :]
            self.column = max(0, self.column - len(INDENT))

    # ------------------------------------------------------------ events
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused = self.rect.collidepoint(event.pos)
            if self.focused:
                self._click(event.pos)
            return self.focused
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(mouse_pos()):
            self.scroll = max(0, min(len(self.lines) - 1, self.scroll - event.y * 3))
            return True
        if not self.focused:
            return False
        if event.type == pygame.TEXTINPUT:
            if not self._try_telex(event.text):
                self.insert(event.text)
            return True
        if event.type == pygame.KEYDOWN:
            return self._key(event)
        return False

    def _try_telex(self, text: str) -> bool:
        """Apply Telex inside strings and comments only, so Python code stays untouched."""
        if not self.vietnamese or len(text) != 1 or not text.isascii() or not text.isalpha():
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

        if control and key == pygame.K_z:
            self.undo()
        elif control and key == pygame.K_v:
            self._paste()
        elif control and key == pygame.K_c:
            self._copy_all()
        elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            if control:
                return False
            self.newline()
        elif key == pygame.K_BACKSPACE:
            self.backspace()
        elif key == pygame.K_DELETE:
            self.delete()
        elif key == pygame.K_TAB:
            if shift:
                self.dedent()
            else:
                self.insert(INDENT)
        elif key == pygame.K_LEFT:
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
        else:
            return False
        return True

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

    def _paste(self) -> None:
        try:
            text = pygame.scrap.get_text()
        except (pygame.error, AttributeError):
            return
        if text:
            self.insert(text.replace("\x00", ""))

    def _copy_all(self) -> None:
        try:
            pygame.scrap.put_text(self.text)
        except (pygame.error, AttributeError):
            return

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
            elif line_index == self.row and self.focused:
                pygame.draw.rect(surface, CODE_COLOR_CURRENT_LINE, line_rect)

            number = self.font.render(str(line_index + 1).rjust(3), True, CODE_COLOR_LINE_NUMBER)
            surface.blit(number, (rect.x + 4, y))

            x = text_x
            for text, color in highlight(self.lines[line_index]):
                rendered = self.font.render(text, True, color)
                surface.blit(rendered, (x, y))
                x += self.char_width * len(text)

        if self.focused and (self.blink_timer % 1.0) < 0.6:
            cursor_x = text_x + self.column * self.char_width
            cursor_y = rect.y + 6 + (self.row - self.scroll) * self.line_height
            pygame.draw.line(surface, CODE_COLOR_CURSOR, (cursor_x, cursor_y), (cursor_x, cursor_y + self.line_height - 3), 2)

        surface.set_clip(previous_clip)
        if self.focused:
            pygame.draw.rect(surface, CODE_COLOR_BORDER_FOCUS, rect, width=2, border_radius=8)


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


def strip(relative_path: str, frame_width: int, scale: float) -> list[pygame.Surface]:
    return slice_strip(load_image(relative_path), frame_width, scale)


class Assets:
    def __init__(self, hero_skin: int = 1) -> None:
        tileset = load_image("2 Locations/Tiles/Tileset.png")
        self.floor = self._tile(tileset, 1, 1)
        self.wall = self._tile(tileset, 1, 4)
        self.door_locked = self._tile(tileset, 13, 5)
        self.door_jammed = self._tile(tileset, 6, 8)

        hero_dir = f"1 Main Characters/{hero_skin}"
        hero_scale = TILE / 32 * 1.25
        self.hero = {
            "idle": strip(f"{hero_dir}/Idle.png", 32, hero_scale),
            "run": strip(f"{hero_dir}/Run.png", 32, hero_scale),
            "hit": strip(f"{hero_dir}/Hit.png", 32, hero_scale),
            "jump": strip(f"{hero_dir}/Jump.png", 32, hero_scale),
        }
        self.appearing = strip("1 Main Characters/Appearing.png", 96, hero_scale)

        self.enemies: dict[str, dict[str, list[pygame.Surface]]] = {}
        for kind, (folder, frame_width) in ENEMY_FOLDERS.items():
            scale = 1.8 if kind == "duck" else 1.6
            self.enemies[kind] = {
                "idle": strip(f"4 Enemies/{folder}/Idle.png", frame_width, scale),
                "hit": strip(f"4 Enemies/{folder}/Hit.png", frame_width, scale),
            }

        self.gems = {color: strip(f"3 Objects/Gems/{color}.png", 16, 2.5) for color in range(1, 7)}
        self.trophy = strip("3 Objects/Checkpoints/End_Idle.png", 64, 0.95)
        self.spike = strip("6 Traps/4.png", 48, 1.0)[4]
        self.backgrounds = {
            index: pygame.transform.scale(load_image(f"2 Locations/Backgrounds/{index}.png"), (128, 128))
            for index in range(1, 7)
        }

    @staticmethod
    def _tile(tileset: pygame.Surface, column: int, row: int) -> pygame.Surface:
        tile = tileset.subsurface((column * 16, row * 16, 16, 16))
        return pygame.transform.scale(tile, (TILE, TILE))


# ======================================================================
# game.py
# ======================================================================

SCREEN_SIZE = (1280, 720)
FPS = 60
PROGRESS_FILE = user_data_dir() / "progress.json"

VIEW_RECT = pygame.Rect(16, 64, 736, 440)
CONSOLE_RECT = pygame.Rect(16, 516, 736, 188)
THEORY_RECT = pygame.Rect(16, 64, 736, 640)
MENU_LEFT = 64
MENU_TAB_Y = 132
MENU_TAB_WIDTH = 224
MENU_WORLDS_Y = 340
MENU_ROWS_PER_COLUMN = 5
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


class Progress:
    def __init__(self) -> None:
        self.completed: set[str] = set()
        self.code: dict[str, str] = {}
        if PROGRESS_FILE.exists():
            try:
                data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
                self.completed = set(data.get("completed", []))
                self.code = dict(data.get("code", {}))
            except (OSError, ValueError):
                pass

    def save(self) -> None:
        data = {"completed": sorted(self.completed), "code": self.code}
        PROGRESS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class Playback:
    """Replays recorded engine events as an animation."""

    def __init__(self, level: Level) -> None:
        self.level = level
        self.terrain_world = World(level)
        self.events: list[dict[str, Any]] = []
        self.result: RunResult | None = None
        self.reset()

    def reset(self) -> None:
        world = self.terrain_world
        self.hero_position = pygame.Vector2(world.hero_start)
        self.facing = "right"
        self.hp = self.level.start_hp
        self.gems = dict(world.gems)
        self.enemies = {pos: enemy.kind for pos, enemy in world.enemies.items()}
        self.doors = dict(world.doors)
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
        elif kind == "bump":
            self.facing = event["direction"]
            self._set_hero_state("hit")
        elif kind == "attack":
            self.facing = event["direction"]
            self._set_hero_state("jump")
            target = tuple(event["target"])
            if event["hit"]:
                self.enemy_flash[target] = 0.3
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
        elif kind == "heal":
            self.hp = event["hp"]
            self._float(f"+{event['amount']} ♥", COLOR_GOOD, self.hero_position)
            log(f"Hồi {event['amount']} máu.", COLOR_GOOD)
        elif kind == "gem":
            position = tuple(event["pos"])
            self.gems.pop(position, None)
            self._float("+1", COLOR_ACCENT, pygame.Vector2(position))
        elif kind == "door_open":
            self.doors.pop(tuple(event["pos"]), None)
            log("Cửa đã mở!", COLOR_GOOD)
        elif kind == "jam":
            self.door_shake[tuple(event["pos"])] = 0.35
            log("DoorJammed: cửa bị kẹt!", COLOR_BAD)
        elif kind == "die":
            self._set_hero_state("hit")
            self.dead = True

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
        self.progress = Progress()
        self.editor = CodeEditor(self.font_code)
        self.levels = all_levels()
        self.scene = "menu"
        self.level: Level = self.levels[0]
        self.playback = Playback(self.level)
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
        self._build_menu()

    # ------------------------------------------------------------ scenes
    def _first_unfinished_stage(self) -> int:
        for level in self.levels:
            if level.id not in self.progress.completed:
                return world_of(level.id).stage
        return 1

    @staticmethod
    def _stage_worlds(stage_number: int) -> list[Any]:
        return [world for world in WORLDS if world.stage == stage_number]

    def select_stage(self, stage_number: int) -> None:
        self.menu_stage = stage_number
        self._build_menu()

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
                rect = pygame.Rect(cell_x + 300 + level_index * 86, cell_y + 4, 80, 42)
                done = level.id in self.progress.completed
                color = (46, 140, 86) if done else (70, 80, 120)
                self.menu_buttons.append(Button(rect, level.id, lambda lv=level: self.open_level(lv), color))

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

    def open_level(self, level: Level) -> None:
        self.save_code()
        self.level = level
        self.scene = "play"
        self.playback = Playback(level)
        self.editor.set_text(self.progress.code.get(level.id, level.starter))
        self.editor.focused = True
        self.console = []
        self.hint_index = 0
        self.show_win = False
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
        result = run_code(self.level, self.editor.text)
        self.editor.error_line = result.error_line
        self.playback.start(result)

    def reset_code(self) -> None:
        self.editor.set_text(self.level.starter)
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
        if result.won:
            self.log("[OK] " + result.message, COLOR_GOOD)
            self.progress.completed.add(self.level.id)
            self.progress.save()
            self.show_win = True
            center = pygame.Rect(0, 0, 160, 46)
            center.center = (VIEW_RECT.centerx - 90, VIEW_RECT.centery + 50)
            next_rect = center.copy()
            next_rect.centerx = VIEW_RECT.centerx + 90
            self.win_buttons = [
                Button(center, "Ở lại", self.close_win),
                Button(next_rect, "Màn tiếp →", self.next_level, (46, 140, 86)),
            ]
        else:
            self.log("[Lỗi] " + result.message, COLOR_BAD)

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
        if self.scene == "menu":
            for button in self.menu_buttons:
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
            if self.show_theory:
                self.show_theory = False
            else:
                self.go_menu()
            return
        self.editor.handle_event(event)

    def update(self, delta_seconds: float) -> None:
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
        if self.scene == "menu":
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
        subtitle = self.font.render(
            "Viết code Python để đưa nhân vật vượt màn - 5 giai đoạn từ nền tảng tới nâng cao. Cho học sinh THCS - THPT.",
            True,
            COLOR_MUTED,
        )
        self.screen.blit(subtitle, (text_left + 2, 80))

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
            concept = self.font_small.render(f"{world.concept}  ·  {done}/{len(world.levels)} xong", True, COLOR_MUTED)
            self.screen.blit(label, (cell_x, cell_y))
            self.screen.blit(concept, (cell_x, cell_y + 26))

        for button in self.menu_buttons[len(STAGES):]:
            button.draw(self.screen, self.font)

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
        self.draw_map()
        self.draw_hearts()
        if self.show_win:
            self.draw_win()

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
        world = self.playback.terrain_world
        origin_x = VIEW_RECT.x + (VIEW_RECT.width - world.width * TILE) // 2
        origin_y = VIEW_RECT.y + (VIEW_RECT.height - world.height * TILE) // 2
        return origin_x, origin_y

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
        playback = self.playback
        origin_x, origin_y = self._map_origin()

        for (x, y), terrain in world.terrain.items():
            screen_position = (origin_x + x * TILE, origin_y + y * TILE)
            char = world.rows[y][x] if x < len(world.rows[y]) else " "
            if char == " ":
                continue
            if terrain == "wall":
                self.screen.blit(self.assets.wall, screen_position)
            else:
                self.screen.blit(self.assets.floor, screen_position)

        for (x, y), terrain in world.terrain.items():
            if terrain == "spike":
                self._blit_on_tile(self.assets.spike, x, y)
            elif terrain == "exit":
                self._blit_on_tile(self._frame(self.assets.trophy, 8), x, y)

        for (x, y), kind in playback.doors.items():
            shake = 4 if (x, y) in playback.door_shake and int(self.time * 30) % 2 else 0
            image = self.assets.door_locked if kind == "locked" else self.assets.door_jammed
            self.screen.blit(image, (origin_x + x * TILE + shake, origin_y + y * TILE))

        for (x, y), color in playback.gems.items():
            bob = 3 * pygame.math.Vector2(0, 1).rotate(self.time * 180 + x * 40).y
            rect = self._blit_on_tile(self._frame(self.assets.gems[color], 10), x, y - 0.15)
            rect.y += int(bob)

        for (x, y), kind in playback.enemies.items():
            frames = self.assets.enemies[kind]["hit" if (x, y) in playback.enemy_flash else "idle"]
            self._blit_on_tile(self._frame(frames, 10), x, y, flip=kind != "duck")

        for (x, y), (kind, remaining) in playback.dying_enemies.items():
            image = self._frame(self.assets.enemies[kind]["hit"], 14).copy()
            image.set_alpha(int(255 * remaining / 0.5))
            self._blit_on_tile(image, x, y, flip=kind != "duck")

        hero_frames = self.assets.hero[playback.hero_state]
        hero_image = self._frame(hero_frames, 16, playback.hero_state_time)
        if playback.dead:
            hero_image = hero_image.copy()
            hero_image.set_alpha(140)
        hero_rect = self._blit_on_tile(
            hero_image, playback.hero_position.x, playback.hero_position.y, flip=playback.facing == "left"
        )

        if playback.bubble:
            self.draw_bubble(playback.bubble[0], hero_rect.midtop)

        for text, color, position, remaining in playback.floaters:
            rendered = self.font_bold.render(text, True, color)
            rendered.set_alpha(int(255 * min(1.0, remaining * 1.5)))
            rise = (1.0 - remaining) * 30
            self.screen.blit(
                rendered,
                rendered.get_rect(center=(origin_x + position.x * TILE + TILE // 2, origin_y + position.y * TILE - rise)),
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

    def draw_hearts(self) -> None:
        for index in range(MAX_HERO_HP):
            color = COLOR_BAD if index < self.playback.hp else (70, 70, 90)
            heart = self.font_bold.render("♥", True, color)
            self.screen.blit(heart, (VIEW_RECT.x + 12 + index * 24, VIEW_RECT.y + 8))
        collected = len(self.playback.terrain_world.gems) - len(self.playback.gems)
        total = len(self.playback.terrain_world.gems)
        if total:
            gem_text = self.font_bold.render(f"Ngọc: {collected}/{total}", True, COLOR_ACCENT)
            self.screen.blit(gem_text, (VIEW_RECT.right - gem_text.get_width() - 14, VIEW_RECT.y + 8))

    def draw_win(self) -> None:
        overlay = pygame.Surface(VIEW_RECT.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, VIEW_RECT.topleft)
        panel = pygame.Rect(0, 0, 420, 190)
        panel.center = VIEW_RECT.center
        draw_panel(self.screen, panel, alpha=245)
        title = self.font_title.render("Hoàn thành!", True, COLOR_GOOD)
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 40)))
        sub = self.font.render(f"Bạn đã vượt qua màn {self.level.id}.", True, COLOR_TEXT)
        self.screen.blit(sub, sub.get_rect(center=(panel.centerx, panel.y + 80)))
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


def main() -> None:
    App().run_forever()

if __name__ == "__main__":
    main()
