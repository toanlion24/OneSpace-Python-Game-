"""Lý thuyết cho từng màn: khái niệm, giải thích code ban đầu, ví dụ minh hoạ, lỗi hay gặp.

Ví dụ minh hoạ cố ý KHÁC lời giải của màn, để người chơi tự áp dụng.
"""

from __future__ import annotations

from dataclasses import dataclass, field


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
