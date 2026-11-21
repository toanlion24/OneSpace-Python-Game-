"""Code suggestions shown while typing in the editor (autocomplete).

Pure logic, no pygame: given the code and the cursor, return what to suggest.
"""

from __future__ import annotations

import keyword
import re
from dataclasses import dataclass


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
    _plain("position", "Toạ độ hiện tại (x, y)"),
    _plain("exit_position", "Toạ độ cổng (x, y)"),
    _plain("hp", "Số máu hiện tại"),
    _plain("x", "Cột hiện tại"),
    _plain("y", "Hàng hiện tại"),
    _plain("gems_collected", "Số ngọc đã nhặt"),
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
