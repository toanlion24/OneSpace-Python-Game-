# OneSpace CodeQuest – Học Python qua trò chơi

<p align="center"><img src="assets/onespace_logo.png" width="220" alt="OneSpace"></p>

Trò chơi học lập trình Python của OneSpace, dành cho học sinh **THCS – THPT**.

Mỗi màn là một thử thách nhỏ: học sinh viết code Python thật để đưa nhân vật vượt bản đồ –
đi đường, nhặt ngọc, hạ quái, giải mật mã mở cửa. Code chạy xong, nhân vật diễn lại từng bước
để các em thấy ngay chương trình của mình đúng hay sai ở đâu.

- **48 màn, 5 giai đoạn**: đi từ câu lệnh đầu tiên tới thư viện chuẩn, class, lập trình hàm, NumPy và gỡ lỗi.
- **Lý thuyết đi kèm từng màn**: khái niệm, đề bài, dữ liệu có sẵn, giải thích từng dòng code ban đầu,
  ví dụ minh hoạ (khác lời giải) và các lỗi hay gặp.
- **Tự suy nghĩ**: game không hiện lời giải; nút Gợi ý chỉ gợi hướng.
- **Thân thiện với học sinh Việt Nam**: lời giải thích bằng tiếng Việt, bộ gõ Telex có sẵn
  (chỉ hoạt động trong dấu nháy và ghi chú nên không làm hỏng code).

## Tải game (Windows)

Vào mục **[Releases](../../releases)**, tải file `OneSpace-CodeQuest-v…-Windows.zip`,
giải nén rồi bấm đúp `OneSpace-CodeQuest.exe`. Không cần cài Python.

Nếu Windows hiện "Windows protected your PC": bấm **More info → Run anyway**.

## Lộ trình 5 giai đoạn

| Giai đoạn | Các em học gì | World | Số màn |
|---|---|---|---|
| 1. Cú pháp & kiểu dữ liệu nền tảng | Câu lệnh, biến, `if`, vòng lặp, ép kiểu, hàm, xử lý chuỗi, list/tuple, dict/set, list comprehension, list lồng nhau | 1–10 | 23 |
| 2. Thư viện chuẩn | Giao/hợp tập hợp, `math`, hoán vị – tổ hợp (`itertools`), `Counter`, `deque`, ngày giờ | 11–15 | 8 |
| 3. Hướng đối tượng & xử lý lỗi | `try/except`, class, `__init__`, `__add__`, `__str__`, `__iter__`, màn trùm tổng hợp | 16–18 | 7 |
| 4. Lập trình hàm & nâng cao | `map`, `filter`, `zip`, `lambda`, biểu thức chính quy, đọc XML, closure, decorator | 19–21 | 6 |
| 5. NumPy & gỡ lỗi | Mảng và ma trận với NumPy, đọc thông báo lỗi, sửa lỗi cú pháp và lỗi logic | 22–23 | 4 |

Xong 3 giai đoạn đầu, học sinh nắm chắc Python cơ bản; giai đoạn 4–5 đưa các em lên trình độ trung cấp
và sẵn sàng học tiếp khoa học dữ liệu, AI hoặc giải thuật.

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
codequest/theory_view.py  Khung lý thuyết cuộn được
codequest/display.py      Co giãn khung hình theo cửa sổ
codequest/assets.py       Nạp đồ hoạ và logo
codequest/selftest.py     Tự kiểm tra mọi màn (cần lời giải riêng của giáo viên)
tests/                    Bộ test
```

Thêm màn mới: thêm `Level(...)` vào `WORLDS` trong `codequest/levels.py`, một mục trong
`codequest/theory.py` và lời giải trong `solutions/level_solutions.py`, rồi chạy `python -m pytest`.

---

Sản phẩm của **OneSpace – Technology Education for the Future Generation**.
