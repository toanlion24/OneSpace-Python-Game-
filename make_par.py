"""Tạo codequest/par.py: số dòng code tối đa để đạt sao "code gọn" ở mỗi màn.

Số dòng lấy từ lời giải mẫu (chỉ có trên máy giáo viên). File sinh ra chỉ chứa CON SỐ,
không chứa code lời giải, nên an toàn để đưa vào game và GitHub.

Chạy:  python make_par.py
"""

from __future__ import annotations

from pathlib import Path

from codequest.engine import count_code_lines
from codequest.levels import all_levels
from codequest.selftest import load_solutions

OUTPUT = Path(__file__).resolve().parent / "codequest" / "par.py"


def main() -> None:
    solutions = load_solutions()
    if solutions is None:
        raise SystemExit("Không tìm thấy thư mục solutions/ - chỉ chạy được trên máy giáo viên.")
    lines = [
        '"""Số dòng code tối đa để đạt sao "code gọn" (sinh tự động bởi make_par.py)."""',
        "",
        "PAR: dict[str, int] = {",
    ]
    for level in all_levels():
        lines.append(f'    "{level.id}": {count_code_lines(solutions[level.id])},')
    lines += ["}", ""]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Đã tạo {OUTPUT.name} cho {len(all_levels())} màn")


if __name__ == "__main__":
    main()
