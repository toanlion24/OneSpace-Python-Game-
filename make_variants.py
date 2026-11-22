"""Tạo codequest/variants.py: bản đồ kiểm tra ẩn cho từng màn.

Mỗi màn có thể có tới 2 bản đồ ẩn:
  - Bản đồ giãn: chèn thêm một cột (hoặc hàng) trống, chỉ cho các màn dạy "quan sát"
    (while, look, find_gems, scan, exit_position...).
  - Dữ liệu khác: đổi các con số trong biến có sẵn (scroll, prices...) và tính lại mật mã.

Một bản đồ ẩn chỉ được giữ khi:
  1. Lời giải mẫu vẫn thắng trên bản đồ ẩn (code tổng quát không bị làm khó).
  2. Bản "gõ cứng" của lời giải (đúng các lệnh đã chạy, với số cụ thể) thua trên bản đồ ẩn.

Lời giải mẫu chỉ có trên máy giáo viên. File sinh ra chỉ chứa bản đồ và dữ liệu, không chứa lời giải.

Chạy:  python make_variants.py
"""

from __future__ import annotations

import ast
import pprint
import re
from dataclasses import replace
from pathlib import Path
from typing import Any, Self

from codequest import engine
from codequest.engine import HeroAPI, Level, World, run_code
from codequest.levels import all_levels
from codequest.selftest import load_solutions

OUTPUT = Path(__file__).resolve().parent / "codequest" / "variants.py"
ACTION_METHODS = (
    "move_up", "move_down", "move_left", "move_right", "move_to", "attack", "attack_target", "say",
    "enter_code", "try_code", "open_door", "unlock", "open_chest", "use", "move_by", "follow",
)
SENSING_WORDS = ("look(", "find_gems", "find_enemies", "find_objects", "scan(", "exit_position", ".position")
STRETCHABLE = {"#", ".", " "}
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


# ------------------------------------------------------------------ hard-coded copy of a solution
class CallRecorder:
    """Ghi lại các lệnh hero mà lời giải đã gọi (chỉ lệnh ngoài cùng)."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.buildable = True
        self._depth = 0
        self._originals: dict[str, Any] = {}

    def __enter__(self) -> Self:
        for name in ACTION_METHODS:
            original = getattr(HeroAPI, name)
            self._originals[name] = original
            setattr(HeroAPI, name, self._wrap(name, original))
        return self

    def __exit__(self, *_: object) -> None:
        for name, original in self._originals.items():
            setattr(HeroAPI, name, original)

    def _wrap(self, name: str, original: Any) -> Any:
        recorder = self

        def wrapper(api: HeroAPI, *args: Any) -> Any:
            recorder._depth += 1
            try:
                result = original(api, *args)
            finally:
                recorder._depth -= 1
            if recorder._depth == 0:
                recorder._record(name, args, result)
            return result

        return wrapper

    def _record(self, name: str, args: tuple[Any, ...], result: Any) -> None:
        if name == "try_code":
            if result is True:
                self.calls.append(("enter_code", args))
            return
        if not all(_is_literal(value) for value in args):
            self.buildable = False
        self.calls.append((name, args))


def _is_literal(value: Any) -> bool:
    try:
        return ast.literal_eval(repr(value)) == value
    except (ValueError, SyntaxError):
        return False


def hard_coded_copy(level: Level, solution: str) -> str | None:
    with CallRecorder() as recorder:
        run_code(level, solution, check_hidden=False)
    if not recorder.buildable or not recorder.calls:
        return None
    lines = [f"hero.{name}({', '.join(repr(value) for value in args)})" for name, args in recorder.calls]
    return "\n".join(lines) + "\n"


def wins(level: Level, source: str) -> bool:
    return run_code(level, source, check_hidden=False).won


def cheat_wins(level: Level, cheat: str) -> bool:
    """Bản gõ cứng không dùng được cấu trúc bắt buộc (for, if...) - chỉ xét có tới đích hay không."""
    return wins(replace(level, requires=[]), cheat)


# ------------------------------------------------------------------ stretched maps
def is_sensing_level(level: Level, solution: str) -> bool:
    text = " ".join([level.starter, *level.hints, level.goal])
    return "while" in level.requires or any(word in text for word in SENSING_WORDS) and any(
        word in solution for word in SENSING_WORDS
    )


def stretch_columns(rows: list[str]) -> list[list[str]]:
    width = max(len(row) for row in rows)
    padded = [row.ljust(width) for row in rows]
    candidates = []
    order = sorted(range(1, width - 1), key=lambda column: abs(column - width // 2))
    for column in order:
        cells = {row[column] for row in padded}
        if cells <= STRETCHABLE and "." in cells:
            candidates.append([(row[:column + 1] + row[column:]).rstrip() for row in padded])
    return candidates


def stretch_rows(rows: list[str]) -> list[list[str]]:
    width = max(len(row) for row in rows)
    candidates = []
    order = sorted(range(1, len(rows) - 1), key=lambda index: abs(index - len(rows) // 2))
    for index in order:
        cells = set(rows[index].ljust(width))
        if cells <= STRETCHABLE and "." in cells:
            candidates.append(rows[:index + 1] + rows[index:])
    return candidates


def map_variant(level: Level, solution: str, cheat: str) -> dict[str, Any] | None:
    for rows in [*stretch_columns(level.rows), *stretch_rows(level.rows)]:
        variant = replace(level, rows=rows)
        if wins(variant, solution) and not cheat_wins(variant, cheat):
            return {"rows": rows}
    return None


# ------------------------------------------------------------------ changed data
def shift_digits(value: Any, amount: int) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value + amount
    if isinstance(value, float):
        return round(value + amount / 2, 2)
    if isinstance(value, str):
        # Ngày tháng đổi từng chữ số sẽ thành ngày vô lý (năm 3137...) - giữ nguyên.
        if DATE_PATTERN.search(value):
            return value
        return "".join(str((int(char) + amount) % 10) if char.isdigit() else char for char in value)
    if isinstance(value, list):
        return [shift_digits(item, amount) for item in value]
    if isinstance(value, tuple):
        return tuple(shift_digits(item, amount) for item in value)
    if isinstance(value, dict):
        return {key: shift_digits(item, amount) for key, item in value.items()}
    return value


class CodeRecorder:
    """Mật mã giả: chấp nhận mọi giá trị và ghi lại giá trị lời giải đã nhập."""

    def __init__(self) -> None:
        self.values: list[Any] = []

    def __eq__(self, other: object) -> bool:
        self.values.append(other)
        return True

    __hash__ = None  # type: ignore[assignment]


def record_door_code(level: Level, solution: str, original_code: Any) -> Any:
    recorder = CodeRecorder()
    original_check = World._check_code_type

    def accept_any(world: World, value: Any) -> Any:
        if isinstance(original_code, tuple) and isinstance(value, list):
            value = tuple(value)
        if hasattr(value, "item") and not isinstance(value, (bool, str)):
            value = value.item()
        return value

    World._check_code_type = accept_any  # type: ignore[method-assign]
    try:
        run_code(replace(level, door_code=recorder), solution, check_hidden=False)
    finally:
        World._check_code_type = original_check  # type: ignore[method-assign]
    values = recorder.values
    if not values or any(value != values[0] for value in values):
        return None
    if type(values[0]) is not type(original_code):
        return None
    return values[0]


def data_variant(level: Level, solution: str, cheat: str) -> dict[str, Any] | None:
    literal_globals = {name: value for name, value in level.extra_globals.items() if _is_literal(value)}
    if not literal_globals or level.say_contains is not None or "try_code" in solution:
        return None
    # Mật mã True/False: đổi số sẽ ra giá trị ngoài miền (công tắc "3"...).
    if isinstance(level.door_code, bool):
        return None
    for amount in (3, 1, 5):
        changed = {name: shift_digits(value, amount) for name, value in literal_globals.items()}
        changed = {name: value for name, value in changed.items() if value != level.extra_globals[name]}
        if not changed:
            continue
        variant = replace(level, extra_globals={**level.extra_globals, **changed})
        entry: dict[str, Any] = {"extra_globals": changed}
        if level.door_code is not None:
            code = record_door_code(variant, solution, level.door_code)
            # Đáp án 0 / rỗng thường là "không tìm thấy" - học sinh có cách giải đúng vẫn có thể lỗi.
            if code is None or code == level.door_code or not code:
                continue
            variant = replace(variant, door_code=code)
            entry["door_code"] = code
        if wins(variant, solution) and not cheat_wins(variant, cheat):
            return entry
    return None


# ------------------------------------------------------------------ main
def build_variants(solutions: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    variants: dict[str, list[dict[str, Any]]] = {}
    for level in all_levels():
        solution = solutions[level.id]
        cheat = hard_coded_copy(level, solution)
        if cheat is None or not cheat_wins(level, cheat):
            continue
        found = []
        if is_sensing_level(level, solution):
            stretched = map_variant(level, solution, cheat)
            if stretched:
                found.append(stretched)
        changed = data_variant(level, solution, cheat)
        if changed:
            found.append(changed)
        if found:
            variants[level.id] = found
    return variants


def main() -> None:
    solutions = load_solutions()
    if solutions is None:
        raise SystemExit("Không tìm thấy thư mục solutions/ - chỉ chạy được trên máy giáo viên.")
    # Không dùng bản đồ ẩn cũ khi sinh bản mới.
    engine.VARIANTS.clear()
    variants = build_variants(solutions)
    body = pprint.pformat(variants, width=110, sort_dicts=False)
    text = (
        '"""Bản đồ kiểm tra ẩn (tự sinh bằng make_variants.py - đừng sửa tay)."""\n\n'
        "from typing import Any\n\n"
        f"VARIANTS: dict[str, list[dict[str, Any]]] = {body}\n"
    )
    OUTPUT.write_text(text, encoding="utf-8")
    maps = sum(1 for entries in variants.values() for entry in entries if "rows" in entry)
    data = sum(1 for entries in variants.values() for entry in entries if "extra_globals" in entry)
    print(f"Đã tạo {OUTPUT.name}: {len(variants)}/{len(all_levels())} màn có bản đồ ẩn ({maps} giãn, {data} đổi dữ liệu)")


if __name__ == "__main__":
    main()
