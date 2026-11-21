"""Self-test for teachers / developers: run every level's reference solution.

Lời giải mẫu nằm trong solutions/level_solutions.py, chỉ có trên máy giáo viên
(không có trong repo công khai và không được đóng gói vào bản .exe).

Usage:  python main.py --self-test   → ghi selftest.txt vào thư mục tiến độ.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from .assets import PROJECT_ROOT, user_data_dir
from .engine import run_code
from .levels import all_levels

SOLUTIONS_FILE = PROJECT_ROOT / "solutions" / "level_solutions.py"
PRACTICE_SOLUTIONS_FILE = PROJECT_ROOT / "solutions" / "practice_solutions.py"


def _load_dict(path: Path, name: str) -> dict[str, str] | None:
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(getattr(module, name))


def load_solutions(path: Path = SOLUTIONS_FILE) -> dict[str, str] | None:
    """Return {level_id: solution code}, or None when the private files are not present."""
    solutions = _load_dict(path, "SOLUTIONS")
    if solutions is None:
        return None
    solutions.update(_load_dict(PRACTICE_SOLUTIONS_FILE, "SOLUTIONS_PRACTICE") or {})
    return solutions


def run_self_test() -> int:
    """Return 0 when every solution wins and every starter does not."""
    report_path = user_data_dir() / "selftest.txt"
    solutions = load_solutions()
    if solutions is None:
        report_path.write_text(
            "Không tìm thấy lời giải mẫu (solutions/level_solutions.py).\n"
            "Chế độ tự kiểm tra chỉ dùng trên máy giáo viên / người phát triển.\n",
            encoding="utf-8",
        )
        return 2

    lines: list[str] = []
    failures = 0
    for level in all_levels():
        solution = run_code(level, solutions[level.id])
        starter = run_code(level, level.starter)
        ok = solution.won and not starter.won
        failures += 0 if ok else 1
        status = "OK " if ok else "LỖI"
        lines.append(f"{status} {level.id:>5}  {level.title}  |  lời giải: {solution.message}")
    summary = f"{len(lines) - failures}/{len(lines)} màn chạy đúng."
    report_path.write_text("\n".join([summary, "", *lines, ""]), encoding="utf-8")
    return 0 if failures == 0 else 1
