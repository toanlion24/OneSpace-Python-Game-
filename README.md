# OneSpace CodeQuest – Học Python qua trò chơi

<p align="center"><img src="assets/onespace_logo.png" width="220" alt="OneSpace"></p>

Game học lập trình Python cho học sinh **THCS – THPT**:

- **Chơi như CodeCombat**: viết code Python để điều khiển hero đi, nhặt ngọc, đánh quái, mở cửa.
- **Học như HackerRank**: 48 màn chia thành 5 giai đoạn theo lộ trình HackerRank Python.
  Mỗi màn có phần **Lý thuyết**: khái niệm, đề bài, dữ liệu vào, giải thích code ban đầu,
  ví dụ minh hoạ (khác lời giải) và lỗi hay gặp.
- Không hiện lời giải; **Gợi ý** chỉ gợi hướng suy nghĩ.
- Có sẵn **bộ gõ tiếng Việt Telex** (chỉ hoạt động trong dấu nháy và ghi chú).

## Tải game (Windows)

Vào mục **[Releases](../../releases)**, tải file `OneSpace-CodeQuest-v…-Windows.zip`,
giải nén rồi bấm đúp `OneSpace-CodeQuest.exe`. Không cần cài Python.

Nếu Windows hiện "Windows protected your PC": bấm **More info → Run anyway**.

## Lộ trình 5 giai đoạn

| Giai đoạn | Chủ đề (HackerRank) | World | Số màn |
|---|---|---|---|
| 1. Cú pháp & kiểu dữ liệu nền tảng | Introduction, Basic Data Types, Strings | 1–10: cú pháp, biến, if, vòng lặp, ép kiểu, hàm, chuỗi, list/tuple, dict/set, list comprehension | 23 |
| 2. Thư viện chuẩn | Sets, Math, Itertools, Collections, Date and Time | 11–15 | 8 |
| 3. OOP & ngoại lệ | Errors and Exceptions, Classes | 16–18 (try/except, class, `__init__`, `__add__`, `__str__`, `__iter__`, trùm giữa) | 7 |
| 4. Lập trình hàm & nâng cao | Built-Ins, Functionals, Regex, XML, Closures, Decorators | 19–21 | 6 |
| 5. NumPy & gỡ lỗi | NumPy, Debugging | 22–23 | 4 |

Xong 3 giai đoạn đầu ≈ kiến thức chứng chỉ HackerRank Python (Basic);
giai đoạn 4 là trọng tâm Python (Intermediate).

## Chạy từ mã nguồn

```bash
pip install -r requirements.txt
python main.py
```

> **Đồ hoạ**: game dùng bộ [Free Simple Platformer Game Kit](https://craftpix.net/freebies/free-simple-platformer-game-kit-pixel-art/)
> của CraftPix.net. Giấy phép của CraftPix không cho phát tán lại file gốc, nên repo này không chứa thư mục `gamekit/`.
> Hãy tải bộ kit và giải nén vào `gamekit/` (cấu trúc: `gamekit/1 Main Characters`, `gamekit/2 Locations`, …).
> Bản `.exe` trong Releases đã có sẵn đồ hoạ.

Python 3.14 dùng `pygame-ce` (bản `pygame` gốc chưa có wheel cho 3.14).

### Lệnh của hero

| Lệnh | Ý nghĩa |
|---|---|
| `hero.move_up/down/left/right(steps=1)` | Đi theo hướng |
| `hero.move_to(x, y)` | Tự tìm đường tới ô (x, y) |
| `hero.say(text)` / `print(...)` | Nói / in ra bảng tin |
| `hero.look(direction)` | `"wall"`, `"floor"`, `"gem"`, `"enemy"`, `"spike"`, `"door"`, `"exit"` |
| `hero.scan()` | Bản đồ dạng list lồng nhau `grid[y][x]` |
| `hero.attack(direction=None, weapon=None)` | Đánh ô bên cạnh |
| `hero.attack_target(x, y, weapon=None)` | Đi tới cạnh quái rồi đánh |
| `hero.enter_code(value)` | Nhập mật mã cho cửa bên cạnh (sai thì mất máu) |
| `hero.try_code(value)` | Thử mật mã không mất máu, trả về True/False |
| `hero.open_door(direction)` | Mở cửa kẹt, có thể ném `DoorJammed` |
| `hero.use(item)` | Dùng vật có thuộc tính `power` để hồi máu |
| `hero.move_by(vector)` | Đi theo đối tượng có `x`, `y` |
| `hero.follow(path)` | Đi theo từng hướng trong một thứ duyệt được |
| `hero.find_gems()` / `hero.find_enemies()` | List dict `{"x", "y", "color"/"type"}` |
| `hero.position`, `hero.exit_position`, `hero.hp` | Thông tin |

Được `import`: `math`, `itertools`, `collections`, `datetime`, `re`, `functools`, `operator`,
`statistics`, `string`, `xml`, `numpy`.

## Phát triển

```bash
python -m pytest          # kiểm tra bản đồ, code ban đầu, lý thuyết (+ lời giải nếu có solutions/)
python build_exe.py       # đóng gói release/OneSpace-CodeQuest-v…-Windows.zip
python merge_single_file.py   # gộp toàn bộ code thành codequest_full.py
```

**Lời giải mẫu không có trong repo công khai và không có trong bản `.exe`.**
Giáo viên / người phát triển giữ lời giải ở `solutions/level_solutions.py` (đã `.gitignore`).
Khi có file này: `python -m pytest` kiểm tra mọi lời giải thắng, và
`python main.py --self-test` ghi báo cáo `selftest.txt`. Không có file này, các test cần lời giải tự bỏ qua.

```
main.py                   Điểm khởi chạy
codequest/engine.py       Luật chơi + chạy code người chơi an toàn (không phụ thuộc pygame)
codequest/levels.py       5 giai đoạn, 23 world, 48 màn (bản đồ ASCII, code ban đầu, gợi ý)
codequest/theory.py       Lý thuyết từng màn
codequest/game.py         Giao diện: menu theo giai đoạn, bản đồ, phát lại hoạt ảnh, bảng tin
codequest/editor.py       Trình soạn code (tô màu, tự thụt lề, undo, Telex)
codequest/telex.py        Bộ gõ tiếng Việt Telex
codequest/theory_view.py  Khung lý thuyết kiểu HackerRank
codequest/display.py      Co giãn khung hình theo cửa sổ
codequest/assets.py       Nạp đồ hoạ và logo
codequest/selftest.py     Tự kiểm tra mọi màn (cần lời giải riêng của giáo viên)
tests/                    Bộ test
```

Thêm màn mới: thêm `Level(...)` vào `WORLDS` trong `codequest/levels.py`, một mục trong
`codequest/theory.py` và lời giải trong `solutions/level_solutions.py`, rồi chạy `python -m pytest`.

---

Sản phẩm của **OneSpace – Technology Education for the Future Generation**.
