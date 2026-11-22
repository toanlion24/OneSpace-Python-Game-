"""Game logic for CodeQuest.

This module has no pygame dependency so it can be tested headless.
The player's code runs once, to completion, against a ``World``. Every action
is recorded as an event; the UI then replays the events as an animation.
"""

from __future__ import annotations

import ast
import copy
import sys
import time
import traceback
from collections import deque
from dataclasses import dataclass, field, replace
from typing import Any

from .variants import VARIANTS

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
