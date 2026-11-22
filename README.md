# OneSpace CodeQuest – Học Python qua trò chơi

<p align="center"><img src="assets/onespace_logo.png" width="220" alt="OneSpace"></p>

Trò chơi học lập trình Python của OneSpace, dành cho học sinh **THCS – THPT**.

Mỗi màn là một thử thách nhỏ: học sinh viết code Python thật để đưa nhân vật vượt bản đồ –
đi đường, nhặt ngọc, hạ quái, giải mật mã mở cửa. Code chạy xong, nhân vật diễn lại từng bước
để các em thấy ngay chương trình của mình đúng hay sai ở đâu.

- **138 màn, 5 giai đoạn, mỗi World 6 bài** (5 bài + 1 Thử thách): đi từ câu lệnh đầu tiên tới thư viện chuẩn, class, lập trình hàm, NumPy và gỡ lỗi.
- **Lý thuyết đi kèm từng màn**: khái niệm, **Từ khó trong bài** (giải thích thuật ngữ bằng lời đời thường),
  đề bài, dữ liệu có sẵn, giải thích từng dòng code ban đầu, mục **Hiểu kỹ hơn** của từng World (hình dung
  đời thường, mẫu câu lệnh, chạy thử từng dòng, mẹo nhớ), ví dụ minh hoạ (khác lời giải) và các lỗi hay gặp.
- **Chép được lý thuyết**: kéo chuột bôi đen là tự chép, nhấn đúp chọn một từ, nhấn 3 lần chép cả đoạn;
  Ctrl+C / Ctrl+A, hoặc nút Sao chép (chưa chọn thì chép cả bài).
- **Sổ tay lý thuyết**: tra cứu toàn bộ kiến thức 23 World, từ điển thuật ngữ và bảng tra lệnh ở một chỗ;
  tìm kiếm gõ không dấu được, in hoặc lưu PDF thành cuốn sổ giấy.
- **Tự suy nghĩ**: game không hiện lời giải; nút Gợi ý chỉ gợi hướng.
- **Bản đồ kiểm tra ẩn**: nhiều màn chạy thêm code trên bản đồ dài hơn hoặc dữ liệu khác;
  code "gõ cứng" (đếm ô, gõ thẳng đáp án) sẽ bị phát hiện, và game diễn lại bản đồ ẩn để em thấy sai ở đâu.
- **Thân thiện với học sinh Việt Nam**: lời giải thích bằng tiếng Việt; gõ tiếng Việt bằng Unikey / EVKey
  như bình thường (giao diện cũ có bộ gõ Telex riêng).
- **Khung code dễ dùng**: gõ vài chữ đầu là hiện **gợi ý lệnh** kèm giải thích (Tab / Enter để chọn,
  Ctrl+Space để mở lại); bôi đen bằng chuột hoặc Shift + mũi tên; Ctrl+A / C / X / V / Z;
  Tab thụt lề cả đoạn đã chọn.
- **Không mất bài**: code và các màn đã qua được lưu tự động, cài lại game vẫn còn.
- **Chơi như game thật**:
  - Mỗi màn có **3 sao**: qua màn · không mất máu · code gọn (không vượt quá số dòng cho phép).
  - Sao mới đạt được đổi ra **xu**; tổng sao quyết định **cấp bậc** (Tân binh → Huyền thoại OneSpace).
  - **Vật thể trong màn**: thùng gỗ phải đập vỡ (có thùng giấu ngọc), chìa khoá mở cửa khoá,
    rương báu mở ra được thêm xu.
  - Qua hết các màn một World thì **mở rương báu**: nhận **huy hiệu chiến thắng** + xu thưởng.
  - **15 nhân vật**: mở game lần đầu là chọn nhân vật – 12 nhân vật miễn phí, 3 nhân vật hiếm mở khoá bằng xu.
    Đổi nhân vật bất cứ lúc nào bằng nút **Nhân vật** ở menu.
  - **8 kiểu bản đồ**: Sân gạch, Đồi đất đỏ, Rừng rêu, Phòng thép, Sa mạc, Băng tuyết, Lâu đài tím, Hang đêm –
    mỗi World một cảnh riêng.
  - **Cửa hàng**: dùng xu mua nhân vật hiếm, Tim thêm (+1 máu), Khiên gỗ (đỡ đòn đầu tiên).
  - Hiệu ứng pháo giấy, âm thanh (bật/tắt được).
  - **Nhạc nền**: 12 bài tự tổng hợp thuộc 7 thể loại – Lo-fi, 8-bit, Ambient, Jazz, Synthwave, Acoustic, Piano.
    Nút **Nhạc** mở bảng chỉnh **âm lượng nhạc và hiệu ứng theo %** và chọn bài (hoặc Tự động: mỗi World một bài).

## Tải game (Windows)

Vào mục **[Releases](../../releases)**, tải file `OneSpace-CodeQuest-v…-Windows.zip`,
giải nén rồi bấm đúp `OneSpace-CodeQuest.exe`. Không cần cài Python.

Nếu Windows hiện "Windows protected your PC": bấm **More info → Run anyway**.

### Tiến độ được lưu ở đâu

- Bản chính: `%APPDATA%\OneSpaceCodeQuest\progress.json` – giữ nguyên khi xoá / cài lại game
  hoặc cập nhật lên bản mới.
- Bản sao lưu: `Documents\OneSpace CodeQuest\tien-do.json` – tự cập nhật mỗi lần lưu. Nếu bản chính
  bị mất, game tự khôi phục từ bản này.
- Đổi máy: ở menu bấm **Sao lưu tiến độ** (mở sẵn thư mục chứa file), chép `tien-do.json` sang
  thư mục `Documents\OneSpace CodeQuest` của máy mới, rồi bấm **Khôi phục tiến độ**.

## Lộ trình 5 giai đoạn

| Giai đoạn | Các em học gì | World | Số màn |
|---|---|---|---|
| 1. Cú pháp & kiểu dữ liệu nền tảng | Câu lệnh, biến, `if`, vòng lặp, ép kiểu, hàm, xử lý chuỗi, list/tuple, dict/set, list comprehension, list lồng nhau | 1–10 | 50 |
| 2. Thư viện chuẩn | Giao/hợp tập hợp, `math`, hoán vị – tổ hợp (`itertools`), `Counter`, `deque`, ngày giờ | 11–15 | 25 |
| 3. Hướng đối tượng & xử lý lỗi | `try/except`, class, `__init__`, `__add__`, `__str__`, `__iter__`, màn trùm tổng hợp | 16–18 | 15 |
| 4. Lập trình hàm & nâng cao | `map`, `filter`, `zip`, `lambda`, biểu thức chính quy, đọc XML, closure, decorator | 19–21 | 15 |
| 5. NumPy & gỡ lỗi | Mảng và ma trận với NumPy, đọc thông báo lỗi, sửa lỗi cú pháp và lỗi logic | 22–23 | 10 |

Xong 3 giai đoạn đầu, học sinh nắm chắc Python cơ bản; giai đoạn 4–5 đưa các em lên trình độ trung cấp
và sẵn sàng học tiếp khoa học dữ liệu, AI hoặc giải thuật.

## Chạy từ mã nguồn

```bash
pip install -r requirements.txt
python main.py
```

Từ v2.0 game mở **giao diện web** trong cửa sổ dùng Microsoft Edge WebView2 (có sẵn trên Windows 10/11).
Giao diện viết bằng HTML/CSS/JS trong `webui/`; chấm code, sao, xu, cửa hàng, nhạc và tiến độ vẫn do Python
(`codequest/web_api.py`) làm. Máy thiếu WebView2 thì tự mở giao diện pygame cũ; `python main.py --classic` để chọn
giao diện cũ. `python -m codequest.web_app --browser` mở bằng trình duyệt thường để phát triển.

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
| `hero.look(direction)` | `"wall"`, `"floor"`, `"gem"`, `"enemy"`, `"spike"`, `"door"`, `"exit"`, `"box"`, `"key"`, `"lock"`, `"chest"` |
| `hero.scan()` | Bản đồ dạng list lồng nhau `grid[y][x]` |
| `hero.attack(direction=None, weapon=None)` | Đánh quái / đập thùng gỗ ở ô bên cạnh |
| `hero.attack_target(x, y, weapon=None)` | Đi tới cạnh quái rồi đánh |
| `hero.enter_code(value)` | Nhập mật mã cho cửa bên cạnh (sai thì mất máu) |
| `hero.try_code(value)` | Thử mật mã không mất máu, trả về True/False |
| `hero.open_door(direction)` | Mở cửa kẹt, có thể ném `DoorJammed` |
| `hero.use(item)` | Dùng vật có thuộc tính `power` để hồi máu |
| `hero.move_by(vector)` | Đi theo đối tượng có `x`, `y` |
| `hero.follow(path)` | Đi theo từng hướng trong một thứ duyệt được |
| `hero.find_gems()` / `hero.find_enemies()` | List dict `{"x", "y", "color"/"type"}` |
| `hero.unlock(direction)` | Dùng 1 chìa mở cửa khoá (chưa có chìa thì ném `ValueError`) |
| `hero.open_chest(direction)` | Mở rương báu bên cạnh (+xu khi qua màn) |
| `hero.find_objects(name)` | List dict `{"x", "y"}` của `"box"`, `"chest"`, `"key"`, `"lock"`, ... |
| `hero.keys` | Số chìa khoá đang có |
| `hero.position`, `hero.exit_position`, `hero.hp` | Thông tin |

Được `import`: `math`, `itertools`, `collections`, `datetime`, `re`, `functools`, `operator`,
`statistics`, `string`, `xml`, `numpy`.

## Phát triển

```bash
python -m pytest          # kiểm tra bản đồ, code ban đầu, lý thuyết (+ lời giải nếu có solutions/)
python build_exe.py       # đóng gói release/OneSpace-CodeQuest-v…-Windows.zip
python merge_single_file.py   # gộp toàn bộ code thành codequest_full.py
python make_par.py        # (máy giáo viên) tính số dòng cho sao "code gọn"
python make_variants.py   # (máy giáo viên) sinh bản đồ kiểm tra ẩn từ lời giải mẫu
```

**Lời giải mẫu không có trong repo công khai và không có trong bản `.exe`.**
Giáo viên / người phát triển giữ lời giải ở `solutions/level_solutions.py` và `solutions/practice_solutions.py` (đã `.gitignore`).
Khi có file này: `python -m pytest` kiểm tra mọi lời giải thắng, và
`python main.py --self-test` ghi báo cáo `selftest.txt`. Không có file này, các test cần lời giải tự bỏ qua.

```
main.py                   Điểm khởi chạy
codequest/engine.py       Luật chơi + chạy code người chơi an toàn (không phụ thuộc pygame)
codequest/levels.py       5 giai đoạn, 23 world, 2-3 bài chính mỗi world (bản đồ ASCII, code ban đầu, gợi ý)
codequest/levels_practice.py  Bài luyện tập thêm + màn Thử thách (mỗi world 6 bài)
codequest/theory_practice.py  Lý thuyết cho bài luyện tập
codequest/theory.py       Lý thuyết từng màn
codequest/lessons.py      Mục "Hiểu kỹ hơn" cho từng World
codequest/glossary.py     Từ điển thuật ngữ (tự hiện "Từ khó trong bài")
codequest/game.py         Giao diện: menu theo giai đoạn, bản đồ, phát lại hoạt ảnh, bảng tin
codequest/editor.py       Trình soạn code (tô màu, tự thụt lề, bôi đen, copy/paste, undo, Telex)
codequest/completion.py   Gợi ý code khi gõ
codequest/progress.py     Lưu / sao lưu / khôi phục tiến độ (cả sao, xu, đồ đã mua)
codequest/rewards.py      Sao, xu, cấp bậc, rương báu, cửa hàng
codequest/par.py          Số dòng code tối đa cho sao "code gọn" (sinh bởi make_par.py)
codequest/store_view.py   Màn Bộ sưu tập & Cửa hàng
codequest/hud.py          Vẽ sao, xu, huy hiệu, pháo giấy
codequest/sound.py        Âm thanh tạo bằng code
codequest/telex.py        Bộ gõ tiếng Việt Telex
codequest/theory_view.py  Khung lý thuyết cuộn được, chọn và chép được
codequest/web_api.py      Cầu nối Python cho giao diện web (chấm code, cửa hàng, nhạc, tiến độ)
codequest/web_app.py      Máy chủ nội bộ + cửa sổ WebView2
webui/                    Giao diện web: app.js (màn hình), map.js (bản đồ), editor.js (khung code), audio.js
codequest/display.py      Co giãn khung hình theo cửa sổ
codequest/assets.py       Nạp đồ hoạ và logo
codequest/selftest.py     Tự kiểm tra mọi màn (cần lời giải riêng của giáo viên)
tests/                    Bộ test
```

Thêm màn mới: thêm `Level(...)` vào `WORLDS` trong `codequest/levels.py`, một mục trong
`codequest/theory.py` và lời giải trong `solutions/level_solutions.py` (bài luyện tập: `levels_practice.py`,
`theory_practice.py`, `solutions/practice_solutions.py`), rồi chạy `python -m pytest`.

---

Sản phẩm của **OneSpace – Technology Education for the Future Generation**.
