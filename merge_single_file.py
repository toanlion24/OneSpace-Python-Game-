"""Gộp toàn bộ package codequest/ thành một file duy nhất: codequest_full.py

Chạy:  python merge_single_file.py
File gộp vẫn cần thư mục gamekit/ nằm cạnh nó để có hình ảnh.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "codequest"
OUTPUT = ROOT / "codequest_full.py"

# Thứ tự theo phụ thuộc: module đứng trước được dùng bởi module đứng sau.
MODULE_ORDER = [
    "telex",
    "engine",
    "par",
    "levels_practice",
    "levels",
    "theory",
    "theory_practice",
    "heroes",
    "themes",
    "rewards",
    "display",
    "completion",
    "editor",
    "theory_view",
    "assets",
    "hud",
    "sound",
    "progress",
    "store_view",
    "hero_view",
    "game",
]

# Các tên trùng nhau giữa các module được đổi tên để không ghi đè lẫn nhau.
RENAMES: dict[str, dict[str, str]] = {
    "levels": {"World": "WorldInfo"},
    "editor": {r"COLOR_(\w+)": r"CODE_COLOR_\1"},
    "theory_view": {r"COLOR_(\w+)": r"THEORY_COLOR_\1"},
    "store_view": {r"COLOR_(\w+)": r"STORE_COLOR_\1"},
    "hero_view": {r"COLOR_(\w+)": r"HERO_COLOR_\1", "PANEL": "HERO_PANEL"},
}

SOURCE_REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "assets": [
        ("PROJECT_ROOT = Path(__file__).resolve().parent.parent", "PROJECT_ROOT = Path(__file__).resolve().parent"),
    ],
}


def apply_renames(module: str, source: str) -> str:
    for pattern, replacement in RENAMES.get(module, {}).items():
        source = re.sub(rf"\b{pattern}\b", replacement, source)
    return source


def split_module(module: str) -> tuple[list[str], str]:
    """Return (import lines, body without module docstring / imports)."""
    source = (PACKAGE / f"{module}.py").read_text(encoding="utf-8")
    for old, new in SOURCE_REPLACEMENTS.get(module, []):
        if old not in source:
            raise ValueError(f"{module}: không tìm thấy '{old}'")
        source = source.replace(old, new)

    tree = ast.parse(source)
    lines = source.split("\n")
    skip_lines: set[int] = set()
    imports: list[str] = []
    for node in tree.body:
        is_docstring = (
            node is tree.body[0]
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )
        if is_docstring or isinstance(node, (ast.Import, ast.ImportFrom)):
            for line_number in range(node.lineno, node.end_lineno + 1):
                skip_lines.add(line_number)
            if isinstance(node, ast.ImportFrom) and (node.level > 0 or node.module == "__future__"):
                continue
            if not is_docstring:
                imports.append(ast.get_source_segment(source, node))

    body = "\n".join(line for index, line in enumerate(lines, start=1) if index not in skip_lines)
    return imports, apply_renames(module, body).strip("\n")


def _import_order(name: str) -> tuple[int, str]:
    """isort-style order: CONSTANTS, then Classes, then functions."""
    if name.isupper():
        return (0, name)
    return (1 if name[0].isupper() else 2, name)


def merge_imports(all_imports: list[str]) -> list[str]:
    plain: set[str] = set()
    from_imports: dict[str, set[str]] = {}
    for statement in all_imports:
        node = ast.parse(statement).body[0]
        if isinstance(node, ast.Import):
            plain.update(f"{alias.name} as {alias.asname}" if alias.asname else alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            from_imports.setdefault(node.module, set()).update(alias.name for alias in node.names)

    third_party = {"pygame", "numpy as np"}
    stdlib = sorted(name for name in plain if name not in third_party)
    lines = [f"import {name}" for name in stdlib]
    lines += [f"from {module} import {', '.join(sorted(names, key=_import_order))}" for module, names in sorted(from_imports.items())]
    lines += ["", *[f"import {name}" for name in sorted(plain & third_party)]]
    return lines


def main() -> None:
    all_imports: list[str] = []
    bodies: list[str] = []
    for module in MODULE_ORDER:
        imports, body = split_module(module)
        all_imports += imports
        banner = f"# {'=' * 70}\n# {module}.py\n# {'=' * 70}"
        bodies.append(f"{banner}\n\n{body}")

    header = [
        '"""CodeQuest - học Python Basic qua trò chơi (bản gộp một file).',
        "",
        "Cách chạy:   pip install pygame-ce   rồi   python codequest_full.py",
        "Cần thư mục gamekit/ (hình ảnh) nằm cùng chỗ với file này.",
        "File được tạo tự động từ package codequest/ bằng merge_single_file.py.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
    ]
    footer = ["", "", 'if __name__ == "__main__":', "    main()", ""]
    text = "\n".join(header + merge_imports(all_imports)) + "\n\n" +"\n\n\n".join(bodies) + "\n".join(footer)
    OUTPUT.write_text(text, encoding="utf-8")
    line_count = text.count("\n")
    print(f"Đã tạo {OUTPUT.name} ({line_count} dòng)")


if __name__ == "__main__":
    main()
