"""Lý thuyết cho các bài luyện tập thêm (levels_practice.py).

Mỗi mục được đăng ký vào THEORY chung. Ví dụ minh hoạ luôn khác lời giải.
"""

from __future__ import annotations

from .theory import THEORY, Theory

PRACTICE_THEORY: dict[str, Theory] = {}

# ================================================================ GIAI ĐOẠN 1
PRACTICE_THEORY.update({
    "1-4": Theory(
        concept=[
            "Chương trình là một DÃY lệnh chạy lần lượt. Đổi thứ tự lệnh là đổi đường đi.",
            "`hero.move_right()` không ghi số thì đi đúng 1 bước.",
            "Mẹo: nhìn bản đồ, đọc đường đi thành từng bước nhỏ rồi viết từng lệnh tương ứng.",
        ],
        starter_notes=[
            ("hero.move_right()", "Bước 1: sang phải 1 ô."),
            ("hero.move_down()", "Bước 2: xuống 1 ô."),
            ("# viết tiếp", "Ghi chú: bạn viết tiếp các bước còn lại."),
        ],
        example=[
            ("hero.move_down()", "Xuống 1."),
            ("hero.move_left()", "Trái 1."),
            ("hero.move_down()", "Xuống 1."),
            ("hero.move_left()", "Trái 1 - đường zigzag theo hướng ngược lại."),
        ],
        mistakes=["Viết thiếu hoặc thừa một lệnh làm hero đụng tường và dừng ở giữa đường."],
    ),
    "1-5": Theory(
        concept=[
            "Không phải lúc nào cũng đi thẳng tới đích được - đôi khi phải đi vòng.",
            "Có 4 hướng: lên (up), xuống (down), trái (left), phải (right).",
            "Lệnh `hero.say(...)` có thể đặt ở bất kỳ đâu - ở đây là sau khi tới cúp.",
        ],
        starter_notes=[("hero.move_down(2)", "Đoạn 1: đi xuống 2 ô.")],
        example=[
            ("hero.move_right(3)", "Sang phải 3."),
            ("hero.move_down(2)", "Xuống 2."),
            ("hero.move_left(3)", "Quay về trái 3 - một đường vòng chữ U úp."),
            ('hero.say("Xong")', "Nói khi đã tới nơi."),
        ],
        mistakes=["Nhầm move_up và move_down: trên bản đồ, đi lên là y giảm."],
    ),
    "2-3": Theory(
        concept=[
            "Giá trị trong biến có thể THAY ĐỔI. `steps = steps - 1`: lấy giá trị cũ trừ 1 rồi cất lại vào chính steps.",
            "Viết tắt: `steps -= 1` giống `steps = steps - 1`; `steps += 2` giống `steps = steps + 2`.",
            "Dùng lại một biến giúp code dễ sửa: đổi một chỗ là mọi nơi dùng biến đều đổi theo.",
        ],
        starter_notes=[
            ("steps = 3", "Biến steps bắt đầu bằng 3."),
            ("hero.move_right(steps)", "Đi phải 3 ô."),
            ("# đổi steps rồi đi xuống", "Bạn thay đổi steps rồi dùng nó để đi xuống."),
        ],
        example=[
            ("lives = 3", "Bắt đầu 3 mạng."),
            ("lives = lives - 1", "Mất 1 mạng: còn 2."),
            ("lives += 5", "Nhặt thêm 5: còn 7."),
            ("print(lives)", "7."),
        ],
        mistakes=["Viết `steps - 1` một mình (không gán) thì steps KHÔNG thay đổi."],
    ),
    "2-4": Theory(
        concept=[
            "Mỗi giá trị có KIỂU: `\"Mai\"` là chuỗi (str), `12` là số nguyên (int).",
            "Dấu `+` nối được chuỗi với chuỗi, cộng được số với số, nhưng KHÔNG trộn chuỗi với số.",
            "`str(12)` đổi số 12 thành chuỗi `\"12\"` để nối được.",
        ],
        starter_notes=[
            ('# name = "Mai", age = 12', "Hai biến có sẵn: một chuỗi, một số."),
            ("hero.say(name)", "Mới nói tên, còn thiếu tuổi."),
            ("hero.move_right(6)", "Đi tới cúp."),
        ],
        example=[
            ('pet = "Mướp"', "Chuỗi."),
            ("weight = 4", "Số."),
            ('print(pet + " nặng " + str(weight) + " kg")', "Mướp nặng 4 kg."),
        ],
        mistakes=["Quên dấu cách: `name + str(age)` cho ra \"Mai12\"."],
    ),
    "2-5": Theory(
        concept=[
            "Phép chia `/` luôn cho số thực: `17 / 5 = 3.4`.",
            "Phép chia lấy phần nguyên `//`: `17 // 5 = 3`. Phép chia lấy dư `%`: `17 % 5 = 2`.",
            "Ứng dụng: chia đồ vật, kiểm tra chẵn lẻ (`n % 2 == 0` là số chẵn).",
        ],
        starter_notes=[
            ("# gems = 17, friends = 5", "Biến có sẵn."),
            ("each = gems / friends", "Phép / cho 3.4 - không phải số kẹo nguyên."),
            ("hero.say(each)", "Hero nói 3.4."),
            ("hero.move_right(5)", "Đi tới cúp."),
        ],
        example=[
            ("minutes = 135", "135 phút."),
            ("hours = minutes // 60", "2 giờ."),
            ("rest = minutes % 60", "15 phút."),
            ('print(str(hours) + " giờ " + str(rest) + " phút")', "2 giờ 15 phút."),
        ],
        mistakes=["Nhầm `%` (chia lấy dư) với phần trăm."],
    ),
    "3-3": Theory(
        concept=[
            "Phép so sánh: `>` lớn hơn, `<` nhỏ hơn, `>=` lớn hơn hoặc bằng, `<=` nhỏ hơn hoặc bằng, `==` bằng, `!=` khác.",
            "Kết quả so sánh là `True` hoặc `False` - quyết định nhánh nào của if/else được chạy.",
        ],
        starter_notes=[
            ("# coins = 7, vé vào cổng giá 5", "Dữ kiện: có 7 xu, vé 5 xu."),
            ("if coins >= 10:", "Đang so với 10 - sai giá vé."),
            ('    hero.say("Đủ tiền")', "Nhánh đủ tiền."),
            ("else:", "Ngược lại..."),
            ('    hero.say("Thiếu tiền")', "...nhánh thiếu tiền."),
            ("hero.move_right(5)", "Đi tới cúp."),
        ],
        example=[
            ("age = 12", "12 tuổi."),
            ("if age >= 13:", "Từ 13 tuổi trở lên?"),
            ('    print("Vé người lớn")', ""),
            ("else:", ""),
            ('    print("Vé trẻ em")', "In: Vé trẻ em."),
        ],
        mistakes=["`>` và `>=` khác nhau khi hai số bằng nhau."],
    ),
    "3-4": Theory(
        concept=[
            "`elif` (else if) kiểm tra thêm điều kiện khi điều kiện trước sai.",
            "Python xét lần lượt từ trên xuống, chạy nhánh ĐẦU TIÊN đúng rồi bỏ qua các nhánh còn lại.",
        ],
        starter_notes=[
            ("hero.move_right(2)", "Đi tới ngã ba."),
            ('if hero.look("up") == "spike":', "Chỉ kiểm tra phía trên - lần này gai lại ở dưới."),
            ("    hero.move_down()", "Đi xuống nếu trên có gai."),
        ],
        example=[
            ("score = 7", "Điểm 7."),
            ("if score >= 9:", ""),
            ('    print("Giỏi")', ""),
            ("elif score >= 6.5:", "Không giỏi thì xét tiếp."),
            ('    print("Khá")', "In: Khá."),
            ("else:", ""),
            ('    print("Cố lên")', ""),
        ],
        mistakes=["Viết hai câu `if` riêng thay vì `if/elif` - cả hai có thể cùng chạy."],
    ),
    "3-5": Theory(
        concept=[
            "`and`: đúng khi CẢ HAI điều kiện đúng. `or`: đúng khi ÍT NHẤT MỘT điều kiện đúng. `not`: đảo ngược.",
            "`hero.hp` cho biết số máu hiện tại của hero (tối đa 3).",
        ],
        starter_notes=[
            ("hero.move_right(2)", "Đi tới gần quái."),
            ("if hero.hp > 1:", "Mới kiểm tra máu, chưa kiểm tra có quái hay không."),
            ("    pass", "Chưa làm gì."),
        ],
        example=[
            ("rain = False", "Không mưa."),
            ("homework_done = True", "Đã làm bài."),
            ("if homework_done and not rain:", "Cả hai cùng đúng."),
            ('    print("Đi đá bóng!")', "In ra."),
        ],
        mistakes=["Viết `if hero.look(\"right\") == \"enemy\" and > 1` - mỗi vế phải là một so sánh đầy đủ."],
    ),
    "4-4": Theory(
        concept=[
            "`range(a, b)` sinh các số từ a tới b-1: `range(1, 4)` cho 1, 2, 3.",
            "Biến vòng lặp (i) có thể dùng trong thân vòng lặp, mỗi vòng một giá trị khác.",
        ],
        starter_notes=[
            ("for i in range(3):", "Lặp 3 lần với i = 0, 1, 2."),
            ("    print(i)", "In giá trị i để xem."),
        ],
        example=[
            ("for n in range(2, 5):", "n = 2, 3, 4."),
            ('    print("*" * n)', "In 2, 3, 4 dấu sao - tam giác lớn dần."),
        ],
        mistakes=["range(1, 3) chỉ có 1 và 2 - không có 3."],
    ),
    "4-5": Theory(
        concept=[
            "Vòng lặp LỒNG NHAU: vòng trong chạy trọn vẹn cho MỖI lần lặp của vòng ngoài.",
            "Thụt lề quyết định lệnh thuộc vòng nào: thụt sâu hơn là thuộc vòng trong.",
            "Vòng trong có thể phụ thuộc biến của vòng ngoài: `for j in range(i):`.",
        ],
        starter_notes=[
            ("for i in range(1, 5):", "i = 1, 2, 3, 4 - độ dài mỗi bậc."),
            ("    hero.move_right(i)", "Đi i bước, nhưng chưa có bước đi xuống."),
        ],
        example=[
            ("for row in range(1, 4):", "3 hàng."),
            ("    line = \"\"", "Bắt đầu một hàng."),
            ("    for col in range(row):", "Hàng thứ row có row ô."),
            ('        line = line + "#"', ""),
            ("    print(line)", "In #, ##, ###."),
        ],
        mistakes=["Đặt lệnh của vòng ngoài vào vòng trong (thụt lề sai) làm nó chạy quá nhiều lần."],
    ),
    "5-3": Theory(
        concept=[
            "`int(\"7\")` được, nhưng `int(\"7.0\")` báo ValueError vì có dấu chấm.",
            "Cách làm: `float(\"7.0\")` → 7.0, rồi `int(7.0)` → 7. Có thể viết gọn `int(float(...))`.",
            "`int()` của số thực sẽ BỎ phần lẻ: `int(3.9)` là 3.",
        ],
        starter_notes=[
            ('# distance = "7.0"', "Chuỗi có dấu chấm thập phân."),
            ("hero.move_right(int(distance))", "int(\"7.0\") sẽ lỗi."),
        ],
        example=[
            ('height = "1.55"', "Chiều cao dạng chuỗi."),
            ("print(float(height) * 100)", "155.0."),
            ("print(int(float(height) * 100))", "155."),
        ],
        mistakes=["Dùng round thay int có thể làm tròn lên khác ý muốn."],
    ),
    "5-4": Theory(
        concept=[
            "Mật mã có thể là chuỗi chứ không chỉ là số.",
            "Ghép chữ và số: đổi số sang chuỗi bằng `str()` rồi nối bằng `+`.",
        ],
        starter_notes=[
            ("# room = 7", "Số phòng là số."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
            ('hero.enter_code("Phòng" + room)', "Chuỗi + số → TypeError; cũng thiếu dấu cách."),
        ],
        example=[
            ("level = 3", "Màn số 3."),
            ('label = "Màn " + str(level)', "\"Màn 3\"."),
            ("print(label)", "Màn 3."),
        ],
        mistakes=["`str(\"Phòng \" + room)` vẫn lỗi vì phép + chạy trước khi đổi kiểu."],
    ),
    "5-5": Theory(
        concept=[
            "`bool(x)` đổi sang True/False. Số 0, chuỗi rỗng `\"\"`, list rỗng `[]` là False; còn lại là True.",
            "Bẫy: `bool(\"0\")` là True vì chuỗi \"0\" KHÔNG rỗng. Phải đổi sang số trước: `bool(int(\"0\"))` là False.",
        ],
        starter_notes=[
            ('# switch = "0"', "Công tắc ghi bằng chuỗi."),
            ("print(bool(switch))  # thử xem", "In ra True - bất ngờ chưa?"),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1, đứng trên cửa."),
        ],
        example=[
            ("print(bool(5), bool(0))", "True False."),
            ('print(bool("hi"), bool(""))', "True False."),
            ("print(bool([]))", "False - list rỗng."),
        ],
        mistakes=["Tưởng `bool(\"False\")` là False - thực ra là True."],
    ),
    "6-4": Theory(
        concept=[
            "THAM SỐ là biến của hàm, nhận giá trị khi gọi: `step(2)` thì n = 2, `step(3)` thì n = 3.",
            "Một hàm có tham số dùng được cho nhiều trường hợp khác nhau.",
        ],
        starter_notes=[
            ("def step(n):", "Hàm step nhận tham số n."),
            ("    hero.move_right(n)", "Đi phải n ô - còn thiếu phần đi xuống."),
            ("step(2)", "Gọi hàm với n = 2."),
        ],
        example=[
            ("def greet(name, times):", "Hai tham số."),
            ("    for i in range(times):", ""),
            ('        print("Chào", name)', ""),
            ('greet("An", 2)', "In 2 lần: Chào An."),
        ],
        mistakes=["Định nghĩa hàm có tham số nhưng gọi mà không truyền giá trị → TypeError."],
    ),
    "6-5": Theory(
        concept=[
            "`max(list)` cho phần tử lớn nhất, `min(list)` cho phần tử nhỏ nhất.",
            "Có thể dùng thẳng kết quả trong phép tính: `max(a) - min(a)`.",
        ],
        starter_notes=[
            ("# scores = [7, 9, 4, 10, 6]", "List điểm có sẵn."),
            ("print(sum(scores))", "In tổng điểm."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ("temps = [28, 31, 25, 30]", "Nhiệt độ các ngày."),
            ("print(max(temps), min(temps))", "31 25."),
            ("print(sum(temps) / len(temps))", "28.5 - trung bình."),
        ],
        mistakes=["`max` của list rỗng sẽ báo lỗi."],
    ),
    "7-3": Theory(
        concept=[
            "Cắt chuỗi có 3 phần: `chuoi[dau:cuoi:buoc]`.",
            "Bước 2 lấy cách một ký tự; bước -1 đi ngược từ cuối về đầu, tức là ĐẢO NGƯỢC chuỗi.",
        ],
        starter_notes=[
            ('# scroll = "olleh"', "Mật mã bị viết ngược."),
            ("print(scroll[0])", "In chữ o."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ('word = "abcdef"', ""),
            ("print(word[::2])", "ace - lấy cách một."),
            ("print(word[::-1])", "fedcba - đảo ngược."),
            ('print("level"[::-1] == "level")', "True - từ đối xứng."),
        ],
        mistakes=["Viết `[:-1]` (bỏ ký tự cuối) thay vì `[::-1]` (đảo ngược)."],
    ),
    "7-4": Theory(
        concept=[
            "`.split(dau_tach)` cắt chuỗi thành list: `\"a,b\".split(\",\")` → `[\"a\", \"b\"]`.",
            "Các phần sau khi cắt vẫn là CHUỖI - muốn tính toán phải `int(...)`.",
            "Ngược lại, `\",\".join(list)` nối list chuỗi thành một chuỗi.",
        ],
        starter_notes=[
            ('# route = "2,3,1"', "Chỉ đường dạng chuỗi."),
            ("parts = route", "Chưa cắt chuỗi."),
            ("print(parts)", "In nguyên chuỗi."),
        ],
        example=[
            ('date = "21/11/2026"', ""),
            ('day, month, year = date.split("/")', "Cắt và mở gói 3 phần."),
            ("print(int(year) - 2000)", "26."),
            ('print("-".join(["a", "b", "c"]))', "a-b-c."),
        ],
        mistakes=["Quên `int()` → move_right(\"2\") báo lỗi kiểu."],
    ),
    "7-5": Theory(
        concept=[
            "`.count(x)` đếm số lần x xuất hiện trong chuỗi (dùng được cả với list).",
            "`len(chuoi)` đếm tất cả ký tự, kể cả dấu cách.",
            "Chuỗi còn có `.find(x)` (vị trí đầu tiên của x) và `.replace(a, b)`.",
        ],
        starter_notes=[
            ('# message = "banana bandana"', "Chuỗi có sẵn."),
            ("print(len(message))", "In 14 - tổng số ký tự."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ('text = "hello world"', ""),
            ('print(text.count("o"))', "2."),
            ('print(text.find("world"))', "6."),
            ('print(text.replace("world", "OneSpace"))', "hello OneSpace."),
        ],
        mistakes=["`count` phân biệt hoa thường: \"A\" khác \"a\"."],
    ),
    "8-3": Theory(
        concept=[
            "Lấy phần tử list theo VỊ TRÍ: `ds[0]` là phần tử đầu, `ds[1]` là phần tử thứ hai...",
            "`ds[-1]` là phần tử cuối. `len(ds)` cho số phần tử.",
        ],
        starter_notes=[
            ("# steps = [3, 2, 4]", "List có sẵn."),
            ("print(steps[0])", "In 3 - phần tử đầu tiên."),
            ("print(len(steps))", "In 3 - list có 3 phần tử."),
        ],
        example=[
            ('colors = ["đỏ", "xanh", "vàng"]', ""),
            ("print(colors[1])", "xanh."),
            ("print(colors[-1])", "vàng."),
            ('colors[0] = "tím"', "Sửa phần tử đầu."),
        ],
        mistakes=["`steps[3]` ngoài phạm vi khi list chỉ có 3 phần tử (vị trí 0, 1, 2)."],
    ),
    "8-4": Theory(
        concept=[
            "Bắt đầu với list rỗng `[]`, mỗi vòng lặp dùng `.append(x)` thêm một phần tử vào CUỐI list.",
            "Đây là cách thu thập kết quả hay dùng nhất.",
        ],
        starter_notes=[
            ("xs = []", "List rỗng để ghi chép."),
            ("for gem in hero.find_gems():", "Duyệt từng viên ngọc."),
            ("    pass", "Chưa ghi gì vào xs."),
            ("hero.say(xs)", "Nói ra list - hiện đang rỗng."),
        ],
        example=[
            ("evens = []", ""),
            ("for n in range(1, 7):", ""),
            ("    if n % 2 == 0:", "Số chẵn?"),
            ("        evens.append(n)", "Thêm vào cuối."),
            ("print(evens)", "[2, 4, 6]."),
        ],
        mistakes=["`xs = xs.append(x)` làm xs thành None - append sửa list tại chỗ, không trả về gì."],
    ),
    "8-5": Theory(
        concept=[
            "List có thể chứa tuple: `[(3, 1), (3, 3)]` - mỗi phần tử là một toạ độ.",
            "Mở gói tuple ngay trong vòng for: `for x, y in stops:`.",
        ],
        starter_notes=[
            ("# stops = [(3, 1), (3, 3), (5, 3), (6, 3)]", "List các điểm dừng."),
            ("first = stops[0]", "Lấy tuple đầu tiên (3, 1)."),
            ("print(first[0], first[1])", "In 3 1."),
        ],
        example=[
            ('friends = [("An", 12), ("Bình", 13)]', "List các tuple (tên, tuổi)."),
            ("for name, age in friends:", "Mở gói ngay."),
            ('    print(name, "năm sau", age + 1, "tuổi")', ""),
        ],
        mistakes=["`for x, y in stops[0]:` - duyệt trong một tuple, không phải cả list."],
    ),
    "9-3": Theory(
        concept=[
            "Dict dùng như BẢNG TRA: khoá là tên món, giá trị là giá.",
            "Tra nhiều lần trong vòng lặp và cộng dồn kết quả vào một biến.",
        ],
        starter_notes=[
            ("# prices, basket có sẵn", "Bảng giá (dict) và giỏ hàng (list)."),
            ('print(prices["táo"])', "In 5 - giá một quả táo."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ('points = {"vàng": 3, "bạc": 2, "đồng": 1}', "Điểm huy chương."),
            ('medals = ["vàng", "đồng", "vàng"]', ""),
            ("score = 0", ""),
            ("for m in medals:", ""),
            ("    score += points[m]", "Tra rồi cộng."),
            ("print(score)", "7."),
        ],
        mistakes=["Tra khoá không có (ví dụ \"nho\") → KeyError."],
    ),
    "9-4": Theory(
        concept=[
            "Dict làm SỔ ĐẾM: khoá là thứ cần đếm, giá trị là số lần.",
            "`d.get(k, 0)` trả về `d[k]` nếu có, nếu chưa có thì trả về 0 - không lỗi.",
            "Mẫu hay dùng: `d[k] = d.get(k, 0) + 1`.",
        ],
        starter_notes=[
            ("counts = {}", "Sổ đếm rỗng."),
            ("print(counts)", "In {}."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ('letters = "hello"', ""),
            ("tally = {}", ""),
            ("for ch in letters:", ""),
            ("    tally[ch] = tally.get(ch, 0) + 1", ""),
            ("print(tally)", "{'h': 1, 'e': 1, 'l': 2, 'o': 1}."),
        ],
        mistakes=["`counts[w] += 1` khi w chưa có trong dict → KeyError."],
    ),
    "9-5": Theory(
        concept=[
            "Đổi list sang set để LOẠI phần tử trùng: `set([1, 1, 2])` → `{1, 2}`.",
            "`len(set(ds))` = số giá trị khác nhau trong ds.",
        ],
        starter_notes=[
            ("# visitors có sẵn", "List tên khách, có tên trùng."),
            ("print(len(visitors))", "In 6 - đếm cả lượt trùng."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("rolls = [3, 6, 3, 1, 6, 6]", "Kết quả gieo xúc xắc."),
            ("print(set(rolls))", "{1, 3, 6}."),
            ("print(len(set(rolls)))", "3 mặt khác nhau."),
        ],
        mistakes=["set không giữ thứ tự - không dùng `set(...)[0]` được."],
    ),
    "10-3": Theory(
        concept=[
            "List comprehension: `[bieu_thuc for x in ds]` tạo list mới, mỗi phần tử là bieu_thuc tính từ x.",
            "Gọn hơn hẳn cách viết dài với list rỗng + for + append.",
        ],
        starter_notes=[
            ("squares = []", "List rỗng - bạn thay bằng comprehension."),
            ("print(numbers)", "In [1, 2, 3, 4]."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("prices = [10, 20, 30]", ""),
            ("sale = [p * 0.9 for p in prices]", "Giảm 10%."),
            ("print(sale)", "[9.0, 18.0, 27.0]."),
            ('print([w.upper() for w in ["a", "b"]])', "['A', 'B']."),
        ],
        mistakes=["Viết `for` trước biểu thức: `[for n in ds n*n]` là sai cú pháp."],
    ),
    "10-4": Theory(
        concept=[
            "Comprehension có thể có 2 vòng for, viết theo thứ tự giống for lồng nhau: `[n for row in t for n in row]`.",
            "Kết quả là list \"trải phẳng\" - mọi số nằm trên một hàng.",
        ],
        starter_notes=[
            ("print(table[0])", "In [1, 2] - hàng đầu."),
            ("print(table[2][1])", "In 6 - hàng 2, cột 1."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ('words = [["a", "b"], ["c"]]', ""),
            ("flat = [w for group in words for w in group]", "Trải phẳng."),
            ("print(flat)", "['a', 'b', 'c']."),
        ],
        mistakes=["Đảo thứ tự hai vòng for: `[n for n in row for row in t]` báo lỗi vì row chưa có."],
    ),
    "10-5": Theory(
        concept=[
            "`enumerate(ds)` cho từng cặp (vị trí, phần tử): rất hợp để biết TOẠ ĐỘ trong bản đồ.",
            "Comprehension 2 vòng có thêm `if` để chỉ giữ các ô cần tìm.",
            "Kết quả là list các tuple (x, y) - dùng `move_to` để đi tới.",
        ],
        starter_notes=[
            ("grid = hero.scan()", "Bản đồ: grid[y][x]."),
            ("print(grid[1][7])", "In ô ở hàng 1, cột 7 - là \"gem\"."),
        ],
        example=[
            ('seats = [["", "An"], ["Bình", ""]]', "Sơ đồ chỗ ngồi."),
            ('empty = [(r, c) for r, row in enumerate(seats) for c, name in enumerate(row) if name == ""]', ""),
            ("print(empty)", "[(0, 0), (1, 1)] - các ghế trống."),
        ],
        mistakes=["Nhầm thứ tự (x, y) và (y, x): grid[y][x] nhưng move_to(x, y)."],
    ),
})


# ================================================================ GIAI ĐOẠN 2
PRACTICE_THEORY.update({
    "11-2": Theory(
        concept=[
            "Hiệu tập hợp `a - b`: phần tử có trong a nhưng không có trong b. Viết bằng hàm: `a.difference(b)`.",
            "Thứ tự quan trọng: `a - b` khác `b - a`.",
        ],
        starter_notes=[
            ("# invited, came có sẵn", "Hai list tên."),
            ("print(set(invited))", "In tập các bạn được mời."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ('all_books = {"Toán", "Văn", "Anh", "Sử"}', "Sách cần mang."),
            ('packed = {"Toán", "Anh"}', "Đã cho vào cặp."),
            ("print(all_books - packed)", "{'Văn', 'Sử'} - còn thiếu."),
        ],
        mistakes=["Viết `came - invited` sẽ ra tập rỗng - đảo ngược thứ tự."],
    ),
    "11-3": Theory(
        concept=[
            "`x in tap_hop` trả về True nếu x có trong tập. Dùng được với list, chuỗi, dict, set.",
            "Với set, `in` kiểm tra gần như tức thì dù tập rất lớn - nhanh hơn list nhiều.",
            "`not in` là ngược lại.",
        ],
        starter_notes=[
            ("# tickets (list), valid (set) có sẵn", "Vé khách đưa và tập mã hợp lệ."),
            ('print("A12" == "A12")', "So sánh bằng: True."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ('vowels = {"a", "e", "i", "o", "u"}', ""),
            ("count = 0", ""),
            ('for ch in "education":', ""),
            ("    if ch in vowels:", "Là nguyên âm?"),
            ("        count += 1", ""),
            ("print(count)", "5."),
        ],
        mistakes=["`if ticket == valid` so sánh với cả tập - luôn sai."],
    ),
    "11-4": Theory(
        concept=[
            "Hiệu đối xứng `a ^ b`: phần tử chỉ thuộc MỘT trong hai tập. Hàm tương ứng: `a.symmetric_difference(b)`.",
            "Bằng `(a | b) - (a & b)`: hợp trừ đi phần chung.",
        ],
        starter_notes=[
            ("a = set(stickers_an)", "Sticker của An."),
            ("b = set(stickers_binh)", "Sticker của Bình."),
            ("print(a & b)", "In phần cả hai cùng có: {3, 4}."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ('lop_a = {"bơi", "cờ"}', ""),
            ('lop_b = {"cờ", "vẽ"}', ""),
            ("print(lop_a ^ lop_b)", "{'bơi', 'vẽ'}."),
        ],
        mistakes=["Nhầm `^` là luỹ thừa: trong Python luỹ thừa là `**`."],
    ),
    "11-5": Theory(
        concept=[
            "Tập con: `a <= b` (hay `a.issubset(b)`) đúng khi MỌI phần tử của a đều có trong b.",
            "Tập cha: `a >= b` đúng khi a chứa mọi phần tử của b.",
        ],
        starter_notes=[
            ("# required (set), backpack (list) có sẵn", "Đồ cần thiết và đồ trong ba lô."),
            ("if len(backpack) > 5:", "So số lượng - không đúng ý."),
            ('    hero.say("Đủ đồ")', ""),
            ("else:", ""),
            ('    hero.say("Thiếu đồ")', ""),
            ("hero.move_right(6)", "Đi tới cúp."),
        ],
        example=[
            ('needed = {"bút", "thước"}', ""),
            ('pencil_case = {"bút", "tẩy", "thước"}', ""),
            ("print(needed <= pencil_case)", "True - đủ đồ."),
            ('print({"compa"} <= pencil_case)', "False."),
        ],
        mistakes=["So sánh list với set bằng `<=` sẽ lỗi - đổi cả hai sang set."],
    ),
    "12-3": Theory(
        concept=[
            "`math.ceil(x)` làm tròn LÊN số nguyên gần nhất: `math.ceil(2.1)` = 3.",
            "`math.floor(x)` làm tròn XUỐNG; `round(x)` làm tròn tới số gần nhất.",
            "Bài toán \"cần bao nhiêu xe / hộp / túi\" thường phải làm tròn lên.",
        ],
        starter_notes=[
            ("import math", "Nạp thư viện."),
            ("# students = 45, seats = 16", "Biến có sẵn."),
            ("print(students / seats)", "In 2.8125."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("import math", ""),
            ("pages = 50", "50 trang."),
            ("per_day = 12", "Đọc 12 trang mỗi ngày."),
            ("print(math.ceil(pages / per_day))", "5 ngày mới đọc xong."),
        ],
        mistakes=["Dùng `//` (làm tròn xuống) sẽ thiếu một xe."],
    ),
    "12-4": Theory(
        concept=[
            "`math.pi` ≈ 3.14159. Diện tích hình tròn = π × r², chu vi = 2 × π × r.",
            "`round(x)` làm tròn về số nguyên gần nhất; `round(x, 2)` giữ 2 chữ số thập phân.",
        ],
        starter_notes=[
            ("import math", "Nạp thư viện."),
            ("# r = 5", "Bán kính có sẵn."),
            ("print(r ** 2)", "In 25."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ("import math", ""),
            ("radius = 3", ""),
            ("perimeter = 2 * math.pi * radius", "Chu vi."),
            ("print(round(perimeter, 1))", "18.8."),
        ],
        mistakes=["Viết `math.pi * r * 2` là chu vi chứ không phải diện tích."],
    ),
    "12-5": Theory(
        concept=[
            "Số cách CHỌN k người trong n người (không tính thứ tự) là tổ hợp: `math.comb(n, k)`.",
            "Giai thừa `math.factorial(n)` = 1 × 2 × ... × n - số cách xếp n người thành hàng.",
        ],
        starter_notes=[
            ("import math", "Nạp thư viện."),
            ("print(math.factorial(3))", "In 6 = 1 × 2 × 3."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("import math", ""),
            ("print(math.comb(5, 3))", "10 cách chọn 3 trong 5."),
            ("print(math.factorial(4))", "24 cách xếp 4 bạn."),
        ],
        mistakes=["Đảo tham số `math.comb(2, 6)` ra 0."],
    ),
    "13-3": Theory(
        concept=[
            "`permutations` sinh kết quả \"lười\" - phải bọc `list(...)` mới đếm được bằng `len`.",
            "Với chuỗi, mỗi ký tự là một phần tử: `permutations(\"AB\")` → ('A','B'), ('B','A').",
        ],
        starter_notes=[
            ("from itertools import permutations", "Nạp hàm."),
            ('print(list(permutations("AB")))', "In 2 cách xếp."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ("from itertools import permutations", ""),
            ('podium = list(permutations(["An", "Bình", "Chi"], 2))', "Chọn nhất và nhì."),
            ("print(len(podium))", "6."),
        ],
        mistakes=["`len(permutations(...))` báo lỗi - cần list(...) trước."],
    ),
    "13-4": Theory(
        concept=[
            "`product(a, b)` ghép mọi phần tử của a với mọi phần tử của b - như bảng phối đồ.",
            "Số kết quả = len(a) × len(b). Có thể ghép nhiều list: `product(a, b, c)`.",
        ],
        starter_notes=[
            ("from itertools import product", "Nạp hàm."),
            ('for combo in product([1, 2], ["x"]):', "Ghép 1-x, 2-x."),
            ("    print(combo)", "In từng cặp."),
        ],
        example=[
            ("from itertools import product", ""),
            ('drinks = ["trà", "sữa"]', ""),
            ('sizes = ["S", "M", "L"]', ""),
            ("print(len(list(product(drinks, sizes))))", "6 lựa chọn."),
        ],
        mistakes=["Nhầm với zip: zip ghép theo cặp vị trí, product ghép mọi khả năng."],
    ),
    "13-5": Theory(
        concept=[
            "Duyệt `combinations(ds, 2)` rồi dùng `if` để chỉ đếm các cặp thoả điều kiện.",
            "Cách này gọi là \"vét cạn\": thử hết khả năng - phù hợp khi dữ liệu nhỏ.",
        ],
        starter_notes=[
            ("from itertools import combinations", "Nạp hàm."),
            ("print(list(combinations([1, 2, 5], 2)))", "In 3 cặp."),
        ],
        example=[
            ("from itertools import combinations", ""),
            ("weights = [3, 4, 6]", "Cân nặng 3 kiện hàng."),
            ("light = [p for p in combinations(weights, 2) if sum(p) <= 8]", "Cặp nhẹ."),
            ("print(light)", "[(3, 4)]."),
        ],
        mistakes=["Quên rằng combinations không lấy một phần tử hai lần (không có cặp (5, 5))."],
    ),
    "14-3": Theory(
        concept=[
            "`defaultdict(list)`: dict tự tạo list rỗng khi gặp khoá mới, nên `groups[k].append(x)` không bao giờ KeyError.",
            "`defaultdict(int)` tự tạo số 0 - tiện để đếm.",
        ],
        starter_notes=[
            ("from collections import defaultdict", "Nạp defaultdict."),
            ("groups = defaultdict(list)", "Dict gom nhóm."),
            ('print(groups["rau"])', "In [] - khoá mới tự có list rỗng."),
        ],
        example=[
            ("from collections import defaultdict", ""),
            ('pets = [("mèo", "Mướp"), ("chó", "Vàng"), ("mèo", "Mun")]', ""),
            ("by_kind = defaultdict(list)", ""),
            ("for kind, name in pets:", ""),
            ("    by_kind[kind].append(name)", ""),
            ('print(by_kind["mèo"])', "['Mướp', 'Mun']."),
        ],
        mistakes=["Với dict thường, `d[k].append(x)` khi k chưa có sẽ KeyError."],
    ),
    "14-4": Theory(
        concept=[
            "`Counter(ds).most_common(1)` → `[(giá_trị, số_lần)]`.",
            "Lấy tên: `[0]` lấy tuple, `[0][0]` lấy phần tử đầu của tuple.",
        ],
        starter_notes=[
            ("from collections import Counter", "Nạp Counter."),
            ("print(len(votes))", "In tổng số phiếu: 6."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ("from collections import Counter", ""),
            ('fruits = ["táo", "cam", "táo"]', ""),
            ("top = Counter(fruits).most_common(1)", "[('táo', 2)]."),
            ("print(top[0][0], top[0][1])", "táo 2."),
        ],
        mistakes=["Nhập cả tuple `('Lan', 3)` thay vì chỉ tên → sai kiểu mật mã."],
    ),
    "14-5": Theory(
        concept=[
            "`deque(ds, maxlen=n)` chỉ giữ tối đa n phần tử; thêm vào thì phần tử cũ nhất bị đẩy ra.",
            "Rất hợp để lưu \"n lần gần nhất\" (lịch sử, điểm số, tin nhắn).",
        ],
        starter_notes=[
            ("from collections import deque", "Nạp deque."),
            ("recent = deque(maxlen=3)", "Hàng chỉ giữ 3 phần tử."),
            ("print(recent)", "In deque([], maxlen=3)."),
        ],
        example=[
            ("from collections import deque", ""),
            ("last_two = deque(maxlen=2)", ""),
            ("for page in [1, 2, 3, 4]:", "Lật trang."),
            ("    last_two.append(page)", ""),
            ("print(list(last_two))", "[3, 4]."),
        ],
        mistakes=["Quên `maxlen=` → deque giữ hết mọi phần tử."],
    ),
    "15-2": Theory(
        concept=[
            "`ngay.weekday()` cho thứ trong tuần dạng số: 0 = thứ Hai ... 6 = Chủ nhật.",
            "`ngay.isoweekday()` thì 1 = thứ Hai ... 7 = Chủ nhật.",
        ],
        starter_notes=[
            ("from datetime import date", "Nạp kiểu date."),
            ("print(date.fromisoformat(day))", "In 2026-09-05."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("from datetime import date", ""),
            ('names = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]', ""),
            ("print(names[date(2026, 1, 1).weekday()])", "T5 - thứ Năm."),
        ],
        mistakes=["Tưởng 0 là Chủ nhật như vài nước khác - trong Python 0 là thứ Hai."],
    ),
    "15-3": Theory(
        concept=[
            "`timedelta(days=n)` là khoảng thời gian n ngày. Ngày + timedelta → ngày mới (tự xử lý hết tháng, năm nhuận).",
            "`str(ngay)` hoặc `ngay.isoformat()` cho chuỗi dạng \"2026-02-15\".",
        ],
        starter_notes=[
            ("from datetime import date, timedelta", "Nạp hai kiểu."),
            ("print(timedelta(days=1))", "In 1 day, 0:00:00."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ("from datetime import date, timedelta", ""),
            ("today = date(2026, 12, 25)", ""),
            ("print(today + timedelta(days=10))", "2027-01-04 - tự sang năm mới."),
        ],
        mistakes=["Cộng số thẳng vào ngày (`date + 45`) báo lỗi - phải dùng timedelta."],
    ),
    "15-4": Theory(
        concept=[
            "Trừ hai ngày → khoảng cách; `.days` là số ngày.",
            "Đổi đơn vị: số tuần = số ngày // 7, ngày lẻ = số ngày % 7.",
        ],
        starter_notes=[
            ("from datetime import date", "Nạp kiểu date."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("from datetime import date", ""),
            ("gap = date(2026, 6, 1) - date(2026, 5, 1)", ""),
            ("print(gap.days, gap.days // 7, gap.days % 7)", "31 4 3."),
        ],
        mistakes=["Trừ ngược (sớm - muộn) ra số âm."],
    ),
    "15-5": Theory(
        concept=[
            "`ngay.strftime(mau)` đổi ngày thành chuỗi theo mẫu tuỳ ý.",
            "Mã hay dùng: `%d` ngày (2 chữ số), `%m` tháng, `%Y` năm 4 chữ số, `%H:%M` giờ:phút.",
        ],
        starter_notes=[
            ("from datetime import date", "Nạp kiểu date."),
            ("print(date.fromisoformat(day))", "In 2026-11-20."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ("from datetime import date", ""),
            ("d = date(2026, 3, 8)", ""),
            ('print(d.strftime("%d-%m"))', "08-03."),
            ('print(d.strftime("Năm %Y"))', "Năm 2026."),
        ],
        mistakes=["`%y` (chữ thường) chỉ có 2 chữ số năm: 26 thay vì 2026."],
    ),
})


# ================================================================ GIAI ĐOẠN 3 - 5
PRACTICE_THEORY.update({
    "16-4": Theory(
        concept=[
            "Chia cho 0 gây `ZeroDivisionError` - chương trình dừng nếu không bắt lỗi.",
            "Đặt try/except BÊN TRONG vòng lặp để một phần tử hỏng không làm hỏng cả vòng lặp.",
        ],
        starter_notes=[
            ("total = 0", "Biến tổng."),
            ("for a, b in pairs:", "Duyệt từng cặp."),
            ("    total += a // b", "Cặp (5, 0) sẽ gây lỗi chia cho 0."),
            ("print(total)", "Không bao giờ chạy tới."),
        ],
        example=[
            ("ages = [12, 0, 15]", "Một tuổi bị nhập sai là 0."),
            ("for age in ages:", ""),
            ("    try:", ""),
            ("        print(100 // age)", ""),
            ("    except ZeroDivisionError:", ""),
            ('        print("Bỏ qua tuổi 0")', "Vòng lặp vẫn chạy tiếp."),
        ],
        mistakes=["Đặt try bên ngoài vòng for: gặp lỗi là thoát luôn cả vòng lặp."],
    ),
    "16-5": Theory(
        concept=[
            "`raise LoaiLoi(\"thông báo\")` tự tạo ra lỗi - dùng khi dữ liệu sai mà hàm không xử lý được.",
            "Hàm chỉ báo lỗi; nơi GỌI hàm quyết định xử lý thế nào bằng try/except.",
        ],
        starter_notes=[
            ("def check(n):", "Hàm kiểm tra số bước."),
            ("    return n", "Chưa kiểm tra gì - số âm cũng cho qua."),
            ("for n in moves:", "Duyệt từng số bước."),
            ("    hero.move_right(check(n))", "Đi theo số bước đã kiểm tra."),
        ],
        example=[
            ("def set_age(age):", ""),
            ("    if age < 0:", "Tuổi âm là vô lý."),
            ('        raise ValueError("Tuổi không được âm")', "Báo lỗi."),
            ("    return age", ""),
            ("try:", ""),
            ("    set_age(-5)", ""),
            ("except ValueError as error:", "Bắt lỗi và đọc thông báo."),
            ("    print(error)", "Tuổi không được âm."),
        ],
        mistakes=["Viết `return ValueError(...)` - trả về lỗi chứ không ném lỗi."],
    ),
    "17-4": Theory(
        concept=[
            "PHƯƠNG THỨC là hàm viết trong class, tham số đầu luôn là `self` - chính đồ vật đó.",
            "Gọi phương thức: `doi_tuong.ten(...)` - Python tự truyền doi_tuong vào self.",
            "Phương thức có thể đọc và sửa thuộc tính: `self.total += amount`.",
        ],
        starter_notes=[
            ("class Wallet:", "Class chiếc ví."),
            ("    def __init__(self):", "Chạy khi tạo ví."),
            ("        self.total = 0", "Ví mới có 0 đồng."),
            ("w = Wallet()", "Tạo một chiếc ví."),
            ("print(w.total)", "In 0."),
        ],
        example=[
            ("class Plant:", ""),
            ("    def __init__(self):", ""),
            ("        self.height = 1", ""),
            ("    def water(self):", "Phương thức tưới cây."),
            ("        self.height += 2", ""),
            ("tree = Plant()", ""),
            ("tree.water()", ""),
            ("print(tree.height)", "3."),
        ],
        mistakes=["Quên `self` ở tham số đầu: gọi phương thức sẽ báo TypeError."],
    ),
    "17-5": Theory(
        concept=[
            "`__len__(self)` quyết định `len(doi_tuong)` trả về bao nhiêu - phải return số nguyên.",
            "Các magic method khác: `__str__` (print), `__add__` (+), `__eq__` (==), `__lt__` (<).",
        ],
        starter_notes=[
            ("class Team:", "Class đội."),
            ("    def __init__(self, members):", "Nhận danh sách thành viên."),
            ("        self.members = members", "Cất danh sách."),
            ("team = Team(members)", "Tạo đội."),
            ("print(team.members)", "In danh sách."),
        ],
        example=[
            ("class Playlist:", ""),
            ("    def __init__(self, songs):", ""),
            ("        self.songs = songs", ""),
            ("    def __len__(self):", ""),
            ("        return len(self.songs)", ""),
            ('print(len(Playlist(["A", "B", "C"])))', "3."),
        ],
        mistakes=["Gọi `len(team)` khi chưa có `__len__` → TypeError."],
    ),
    "18-2": Theory(
        concept=[
            "Bài ôn tập: kết hợp dict tra vũ khí, vòng lặp hạ quái, move_to và try/except mở cửa kẹt.",
            "Chia việc thành từng bước nhỏ, chạy thử sau mỗi bước.",
        ],
        starter_notes=[
            ('weakness = {"robot": "hammer", "barrel": "axe", "cannon": "bow"}', "Bảng vũ khí."),
            ("for enemy in hero.find_enemies():", "Duyệt từng quái."),
            ('    print(enemy["type"], enemy["x"], enemy["y"])', "In thông tin để xem."),
        ],
        example=[
            ('sounds = {"mèo": "meo", "chó": "gâu"}', ""),
            ('for pet in ["chó", "mèo"]:', ""),
            ("    print(sounds[pet])", "gâu, meo."),
            ("while True:", "Thử tới khi được."),
            ("    try:", ""),
            ('        value = int("5")', ""),
            ("        break", ""),
            ("    except ValueError:", ""),
            ("        pass", ""),
        ],
        mistakes=["Đi tới cửa trước khi hạ hết quái - quái chặn đường."],
    ),
    "18-3": Theory(
        concept=[
            "Hàm có thể trả về cả một list - kết hợp tốt với list comprehension.",
            "`ch.isdigit()` kiểm tra ký tự có phải chữ số.",
        ],
        starter_notes=[
            ("def digits(text):", "Hàm lấy các chữ số."),
            ("    return []", "Đang trả về list rỗng."),
            ("print(digits(scroll))", "In [] - chưa có gì."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("def vowels(word):", ""),
            ('    return [ch for ch in word if ch in "aeiou"]', ""),
            ('print(vowels("python"))', "['o']."),
            ('print(len(vowels("banana")))', "3."),
        ],
        mistakes=["Quên `int(ch)` → sum không cộng được các chuỗi."],
    ),
    "18-4": Theory(
        concept=[
            "Bài ôn tập class + `__iter__`: tự tạo một lộ trình mà `for` / `hero.follow` duyệt được.",
            "Trong `__iter__` có thể dùng vòng lặp để tạo list, rồi `return iter(list)`.",
        ],
        starter_notes=[
            ("class Route:", "Class lộ trình."),
            ("    def __init__(self, size):", "Nhận số bậc."),
            ("        self.size = size", "Cất số bậc."),
            ('hero.follow(["right", "down"])', "Đi theo một list cố định - chỉ 1 bậc."),
        ],
        example=[
            ("class Countdown:", ""),
            ("    def __init__(self, start):", ""),
            ("        self.start = start", ""),
            ("    def __iter__(self):", ""),
            ("        numbers = []", ""),
            ("        for n in range(self.start, 0, -1):", ""),
            ("            numbers.append(n)", ""),
            ("        return iter(numbers)", ""),
            ("print(list(Countdown(3)))", "[3, 2, 1]."),
        ],
        mistakes=["Trả về list thay vì iter(list) → TypeError."],
    ),
    "18-5": Theory(
        concept=[
            "Bài ôn tập: try/except để bỏ qua dữ liệu hỏng, set để bỏ dữ liệu trùng.",
            "`except ValueError: pass` - bắt lỗi rồi bỏ qua, không làm gì.",
        ],
        starter_notes=[
            ("values = []", "List các số."),
            ("for text in candidates:", "Duyệt từng chuỗi."),
            ("    values.append(int(text))", "Chuỗi \"x\" sẽ gây ValueError."),
        ],
        example=[
            ('inputs = ["3", "ba", "3"]', ""),
            ("seen = set()", ""),
            ("for text in inputs:", ""),
            ("    try:", ""),
            ("        seen.add(int(text))", ""),
            ("    except ValueError:", ""),
            ("        pass", ""),
            ("print(seen)", "{3}."),
        ],
        mistakes=["Dùng list thay set: số 4 bị cộng hai lần."],
    ),
    "19-3": Theory(
        concept=[
            "`max(ds, key=ham)` tìm phần tử có ham(phần tử) lớn nhất. `sorted(ds, key=ham)` sắp xếp theo ham.",
            "`lambda p: p[1]` là hàm lấy phần tử thứ hai của tuple - viết ngay tại chỗ.",
        ],
        starter_notes=[
            ("print(sorted(players))", "Sắp xếp theo tên (phần tử đầu tuple)."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ('words = ["kiwi", "táo", "dưa hấu"]', ""),
            ("print(max(words, key=lambda w: len(w)))", "dưa hấu - từ dài nhất."),
            ("print(sorted(words, key=lambda w: len(w)))", "Ngắn tới dài."),
        ],
        mistakes=["Nhập cả tuple (\"Bình\", 9) thay vì chỉ tên."],
    ),
    "19-4": Theory(
        concept=[
            "`enumerate(ds)` cho cặp (vị trí, phần tử) - không cần tự đếm vị trí.",
            "`break` dừng vòng lặp ngay khi tìm thấy.",
            "Với list có sẵn còn có `ds.index(x)` tìm vị trí đầu tiên của x.",
        ],
        starter_notes=[
            ("for step in route:", "Duyệt từng bước nhưng không biết vị trí."),
            ("    print(step)", "In từng bước."),
        ],
        example=[
            ('queue = ["An", "Bình", "Chi"]', ""),
            ("for i, name in enumerate(queue, start=1):", "Đánh số từ 1."),
            ('    print(i, name)', "1 An, 2 Bình, 3 Chi."),
        ],
        mistakes=["Quên break: vị trí cuối cùng gặp \"down\" sẽ ghi đè vị trí đầu."],
    ),
    "19-5": Theory(
        concept=[
            "`any(dieu_kien for x in ds)` → True nếu ÍT NHẤT MỘT phần tử thoả.",
            "`all(dieu_kien for x in ds)` → True nếu MỌI phần tử thoả.",
        ],
        starter_notes=[
            ("if temps[0] > 30:", "Chỉ xét ngày đầu tiên."),
            ('    hero.say("Nóng")', ""),
            ("else:", ""),
            ('    hero.say("Mát")', ""),
            ("hero.move_right(5)", "Đi tới cúp."),
        ],
        example=[
            ("scores = [8, 9, 7]", ""),
            ("print(all(s >= 5 for s in scores))", "True - đều trên trung bình."),
            ("print(any(s == 10 for s in scores))", "False - không có điểm 10."),
        ],
        mistakes=["`any(temps) > 30` sai: any trả về True/False, không phải số."],
    ),
    "20-3": Theory(
        concept=[
            "`re.findall(mau, text)` trả về list MỌI chỗ khớp; `re.search` chỉ tìm chỗ đầu tiên.",
            "Mẫu `\\d+`: một hoặc nhiều chữ số liền nhau.",
        ],
        starter_notes=[
            ("import re", "Nạp regex."),
            ('print(re.search(r"\\d+", letter).group())', "In 3 - chỉ số đầu tiên."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("import re", ""),
            ('order = "2 bánh, 10 kẹo, 1 sữa"', ""),
            ('numbers = re.findall(r"\\d+", order)', "['2', '10', '1']."),
            ("print(sum(int(n) for n in numbers))", "13."),
        ],
        mistakes=["Cộng thẳng list chuỗi → TypeError; phải int từng phần tử."],
    ),
    "20-4": Theory(
        concept=[
            "Lượng từ trong regex: `{3}` đúng 3 lần, `+` một hoặc nhiều, `*` không hoặc nhiều, `?` có hoặc không.",
            "`[A-Z]` một chữ in hoa, `[0-9]` hay `\\d` một chữ số.",
            "`re.fullmatch` khớp TOÀN BỘ chuỗi; `re.search` chỉ cần khớp một phần.",
        ],
        starter_notes=[
            ("import re", "Nạp regex."),
            ("print(len(codes))", "In 4 - tổng số mã."),
            ("hero.move_right(2)", "Đi phải 2."),
            ("hero.move_down(1)", "Xuống 1."),
        ],
        example=[
            ("import re", ""),
            ('phones = ["0912345678", "123", "0987654321"]', ""),
            ('ok = [p for p in phones if re.fullmatch(r"0\\d{9}", p)]', "Số 10 chữ số bắt đầu bằng 0."),
            ("print(ok)", "Hai số hợp lệ."),
        ],
        mistakes=["Dùng re.search thì \"EF-7890\" cũng có thể khớp một phần - nên dùng fullmatch."],
    ),
    "20-5": Theory(
        concept=[
            "Thẻ XML có thể chứa nhiều thuộc tính: `the.get(\"weapon\")` đọc từng thuộc tính.",
            "Dữ liệu điều khiển game (bản đồ, lệnh) thường được lưu bằng XML hoặc JSON.",
        ],
        starter_notes=[
            ("import xml.etree.ElementTree as ET", "Nạp bộ đọc XML."),
            ("root = ET.fromstring(room_xml)", "Đọc chuỗi XML."),
            ('print(len(root.findall("enemy")))', "In 3 - số thẻ enemy."),
        ],
        example=[
            ("import xml.etree.ElementTree as ET", ""),
            ("data = '<menu><dish name=\"phở\" price=\"40\"/><dish name=\"bún\" price=\"35\"/></menu>'", ""),
            ("root = ET.fromstring(data)", ""),
            ('for dish in root.findall("dish"):', ""),
            ('    print(dish.get("name"), int(dish.get("price")))', ""),
        ],
        mistakes=["Quên đổi toạ độ sang int → attack_target báo lỗi."],
    ),
    "21-3": Theory(
        concept=[
            "Closure nhớ biến của hàm ngoài: hàm `multiply` tạo trong `make_multiplier(3)` luôn nhớ k = 3.",
            "Mỗi lần gọi hàm ngoài tạo ra một hàm mới với giá trị riêng: `double = make_multiplier(2)`.",
        ],
        starter_notes=[
            ("def make_multiplier(k):", "Nhà máy tạo hàm nhân với k."),
            ("    pass", "Chưa tạo gì."),
            ("hero.move_right(2)", "Đi tới cạnh cửa."),
        ],
        example=[
            ("def make_adder(bonus):", ""),
            ("    def add(score):", ""),
            ("        return score + bonus", "Nhớ bonus."),
            ("    return add", ""),
            ("plus_five = make_adder(5)", ""),
            ("print(plus_five(10))", "15."),
        ],
        mistakes=["Quên `return` trong hàm con → kết quả là None."],
    ),
    "21-4": Theory(
        concept=[
            "Decorator có thể làm thêm việc TRƯỚC (hoặc SAU) khi gọi hàm gốc - ví dụ ghi log.",
            "`func.__name__` là tên của hàm dạng chuỗi.",
        ],
        starter_notes=[
            ("def announce(func):", "Decorator báo hiệu."),
            ("    return func", "Đang trả hàm gốc - chưa thêm gì."),
            ("@announce", "Gắn decorator vào hop."),
            ("def hop():", "Chiêu nhảy gai."),
            ("    hero.move_up()", ""),
            ("    hero.move_right(2)", ""),
            ("    hero.move_down()", ""),
            ("hero.move_right(2)", "Tới trước gai đầu."),
            ("hop()", "Nhảy 1 lần."),
        ],
        example=[
            ("def log(func):", ""),
            ("    def wrapper():", ""),
            ('        print("Gọi", func.__name__)', "Làm thêm trước."),
            ("        func()", ""),
            ("    return wrapper", ""),
            ("@log", ""),
            ("def jump():", ""),
            ('    print("Nhảy!")', ""),
            ("jump()", "Gọi jump rồi Nhảy!"),
        ],
        mistakes=["Gọi `func` (không ngoặc) trong wrapper - hàm gốc không chạy."],
    ),
    "21-5": Theory(
        concept=[
            "Decorator có tham số cần 3 tầng: hàm nhận tham số → trả về decorator → decorator trả về wrapper.",
            "`@repeat(4)` = gọi `repeat(4)` trước để lấy decorator, rồi dùng decorator đó bọc hàm.",
        ],
        starter_notes=[
            ("def repeat(times):", "Nhận số lần lặp."),
            ("    pass", "Chưa làm gì."),
            ("def stair():", "Một bậc thang."),
            ("    hero.move_right()", ""),
            ("    hero.move_down()", ""),
            ("stair()", "Chỉ xuống 1 bậc."),
        ],
        example=[
            ("def shout(times):", ""),
            ("    def decorator(func):", ""),
            ("        def wrapper():", ""),
            ("            for i in range(times):", ""),
            ("                func()", ""),
            ("        return wrapper", ""),
            ("    return decorator", ""),
            ("@shout(2)", ""),
            ("def cheer():", ""),
            ('    print("Cố lên!")', ""),
            ("cheer()", "In 2 lần."),
        ],
        mistakes=["Viết `@repeat` không có (4) → times trở thành chính hàm stair."],
    ),
    "22-3": Theory(
        concept=[
            "Mảng NumPy có sẵn các phép thống kê: `.mean()` trung bình, `.max()`, `.min()`, `.std()` độ lệch chuẩn.",
            "Kết quả là số của NumPy - đổi sang int / float khi cần.",
        ],
        starter_notes=[
            ("import numpy as np", "Nạp NumPy."),
            ("data = np.array(temps)", "Tạo mảng nhiệt độ."),
            ("print(data.max())", "In 28."),
        ],
        example=[
            ("import numpy as np", ""),
            ("heights = np.array([150, 160, 155])", ""),
            ("print(heights.mean())", "155.0."),
            ("print(heights - 100)", "[50 60 55] - trừ mọi phần tử cùng lúc."),
        ],
        mistakes=["`data.mean` (không ngoặc) là chính hàm, chưa phải kết quả."],
    ),
    "22-4": Theory(
        concept=[
            "So sánh với mảng cho mảng True/False: `arr > 5` → `[False, True, ...]`.",
            "Lọc bằng mảng True/False: `arr[arr > 5]` chỉ giữ phần tử ứng với True.",
            "Đếm nhanh: `(arr > 5).sum()` vì True được tính là 1.",
        ],
        starter_notes=[
            ("import numpy as np", "Nạp NumPy."),
            ("arr = np.array(scores)", "Mảng điểm."),
            ("print(arr > 5)", "In mảng True/False."),
        ],
        example=[
            ("import numpy as np", ""),
            ("ages = np.array([10, 15, 12, 17])", ""),
            ("print(ages[ages >= 13])", "[15 17]."),
            ("print((ages < 13).sum())", "2."),
        ],
        mistakes=["Dùng `and`/`or` với mảng → lỗi; NumPy dùng `&` và `|` kèm ngoặc."],
    ),
    "22-5": Theory(
        concept=[
            "`axis=0` tính theo cột (gộp các hàng), `axis=1` tính theo hàng (gộp các cột).",
            "`.argmax()` trả về VỊ TRÍ của phần tử lớn nhất, `.argmin()` vị trí nhỏ nhất.",
        ],
        starter_notes=[
            ("import numpy as np", "Nạp NumPy."),
            ("table = np.array(sales)", "Bảng 3 × 3."),
            ("print(table.sum())", "In tổng cả bảng."),
        ],
        example=[
            ("import numpy as np", ""),
            ("grades = np.array([[8, 6], [9, 7]])", "2 bạn, 2 môn."),
            ("print(grades.sum(axis=1))", "[14 16] - tổng mỗi bạn."),
            ("print(grades.sum(axis=1).argmax())", "1 - bạn thứ hai cao hơn."),
        ],
        mistakes=["Nhầm axis=0 và axis=1 - in thử ra để kiểm tra."],
    ),
    "23-3": Theory(
        concept=[
            "`NameError: name 'x' is not defined` - Python không biết tên x: gõ sai tên hoặc dùng trước khi tạo.",
            "Cách sửa: so sánh tên ở chỗ tạo biến và chỗ dùng biến, từng chữ cái một.",
        ],
        starter_notes=[
            ("steps = 6", "Tạo biến steps."),
            ('message = "Tới rồi"', "Tạo biến message."),
            ("hero.move_right(step)", "Tên dùng ở đây có khớp tên đã tạo không?"),
            ("hero.say(mesage)", "Đếm số chữ s."),
        ],
        example=[
            ('color = "xanh"', "Tạo đúng tên."),
            ("print(color)", "Dùng đúng tên - chạy tốt."),
            ("count = 3", ""),
            ("print(count + 1)", "4."),
        ],
        mistakes=["Sửa tên ở chỗ dùng nhưng quên chỗ khác cũng gõ sai."],
    ),
    "23-4": Theory(
        concept=[
            "`TypeError` - dùng sai kiểu: nối chuỗi với số, đưa chuỗi vào nơi cần số...",
            "Thông báo lỗi thường nói rõ hai kiểu bị trộn (str và int).",
        ],
        starter_notes=[
            ("gems = len(hero.find_gems())", "gems là số."),
            ('hero.say("Có " + gems + " ngọc")', "Nối chuỗi với số - lỗi."),
            ('hero.move_right("4")', "Số bước đang là chuỗi."),
        ],
        example=[
            ("pages = 12", ""),
            ('print("Đọc " + str(pages) + " trang")', "Đổi số sang chuỗi."),
            ('print(int("8") + 2)', "10 - đổi chuỗi sang số."),
        ],
        mistakes=["Sửa xong một lỗi rồi dừng - chạy lại để tìm lỗi tiếp theo."],
    ),
    "23-5": Theory(
        concept=[
            "Vòng `while` dừng khi điều kiện SAI. Nếu biến trong điều kiện không bao giờ đổi, vòng lặp chạy mãi.",
            "Game sẽ dừng chương trình chạy quá lâu và báo lỗi - dấu hiệu của vòng lặp vô hạn.",
        ],
        starter_notes=[
            ("count = 0", "Biến đếm bắt đầu từ 0."),
            ("while count < 5:", "Lặp khi count nhỏ hơn 5."),
            ("    hero.move_right()", "count không bao giờ đổi..."),
        ],
        example=[
            ("water = 0", ""),
            ("while water < 3:", ""),
            ('    print("Rót thêm")', ""),
            ("    water += 1", "Thay đổi biến điều kiện."),
            ('print("Đầy cốc")', "Chạy sau 3 vòng."),
        ],
        mistakes=["Tăng biến đếm nhưng đặt NGOÀI vòng lặp (thụt lề sai)."],
    ),
})


# ================================================================ BÀI 6: THỬ THÁCH VẬT THỂ MỚI
OBJECTS_NOTE = (
    "Vật thể mới: thùng gỗ (\"box\") đập bằng `hero.attack(huong)`; chìa khoá (\"key\") đi qua là nhặt, "
    "`hero.keys` đếm số chìa; cửa khoá (\"lock\") mở bằng `hero.unlock(huong)`; rương báu (\"chest\") mở bằng "
    "`hero.open_chest(huong)` - mỗi rương thưởng thêm xu."
)

PRACTICE_THEORY.update({
    "1-6": Theory(
        concept=[
            "`hero.attack(\"right\")` không chỉ đánh quái - nó còn ĐẬP VỠ thùng gỗ ở ô bên phải.",
            "Thùng vỡ rồi thì ô đó thành đường đi bình thường.",
            OBJECTS_NOTE,
        ],
        starter_notes=[
            ("hero.move_right(1)", "Đi tới đứng sát thùng."),
            ("# thùng gỗ chắn đường!", "Ghi chú: cần phá thùng trước khi đi tiếp."),
        ],
        example=[
            ("hero.move_down()", "Đi xuống sát thùng phía dưới."),
            ('hero.attack("down")', "Đập thùng phía dưới."),
            ("hero.move_down(2)", "Đi qua chỗ thùng vừa vỡ."),
        ],
        mistakes=["Đi thẳng vào thùng: hero đụng thùng và đứng lại."],
    ),
    "2-6": Theory(
        concept=[
            "Đi qua ô chìa khoá là tự nhặt. `hero.keys` cho biết đang có mấy chìa.",
            "`hero.unlock(\"right\")` dùng 1 chìa để mở cửa khoá bên phải.",
            "Biến có thể dùng trong phép tính: `steps + 1`.",
        ],
        starter_notes=[
            ("steps = 1", "Biến số bước - cần đổi."),
            ("hero.move_right(steps)", "Đi theo số bước trong biến."),
        ],
        example=[
            ("hero.move_up(2)", "Đi lên, nhặt chìa trên đường."),
            ("print(hero.keys)", "In 1."),
            ('hero.unlock("up")', "Mở cửa khoá phía trên."),
        ],
        mistakes=["Gọi unlock khi chưa có chìa → lỗi ValueError."],
    ),
    "3-6": Theory(
        concept=[
            "`hero.look(huong)` trả về cả \"box\" (thùng), \"chest\" (rương), \"lock\" (cửa khoá), \"key\" (chìa).",
            "Có thể viết nhiều câu `if` liên tiếp để kiểm tra nhiều hướng.",
        ],
        starter_notes=[
            ("hero.move_right(2)", "Đi tới ngã ba."),
            ('if hero.look("up") == "chest":', "Nếu phía trên là rương..."),
            ("    pass", "...chưa làm gì - hãy mở rương."),
        ],
        example=[
            ('if hero.look("left") == "box":', "Bên trái có thùng?"),
            ('    hero.attack("left")', "Đập thùng."),
            ('if hero.look("down") == "chest":', "Bên dưới có rương?"),
            ('    hero.open_chest("down")', "Mở rương."),
        ],
        mistakes=["Mở rương bằng attack: rương không vỡ, phải dùng open_chest."],
    ),
    "4-6": Theory(
        concept=[
            "Khi một cặp lệnh lặp lại nhiều lần (đập thùng, bước lên), hãy đưa chúng vào vòng `for`.",
            "Thùng có dấu X (Q) chứa ngọc: đập vỡ thì ngọc rơi ra ngay tại ô đó.",
        ],
        starter_notes=[
            ('hero.attack("right")', "Đập thùng bên phải."),
            ("hero.move_right()", "Bước lên chỗ thùng vừa vỡ."),
        ],
        example=[
            ("for i in range(3):", "Lặp 3 lần."),
            ('    hero.attack("down")', "Đập thùng phía dưới."),
            ("    hero.move_down()", "Bước xuống."),
        ],
        mistakes=["Đặt hero.move_right() ngoài vòng lặp - chỉ bước được 1 lần."],
    ),
    "5-6": Theory(
        concept=[
            "`range()` chỉ nhận số nguyên: `range(\"2\")` báo TypeError, phải `range(int(\"2\"))`.",
            "Mỗi lượt lặp làm trọn một việc: nhặt chìa, mở cửa, bước qua.",
        ],
        starter_notes=[
            ('# doors = "2"', "Số cửa ghi bằng chuỗi."),
            ("for i in range(doors):", "range với chuỗi sẽ lỗi."),
            ("    hero.move_right()", "Mới chỉ bước, chưa mở cửa."),
        ],
        example=[
            ('times = "3"', ""),
            ("for i in range(int(times)):", "Đổi chuỗi sang số trước."),
            ('    print("Lượt", i + 1)', "Lượt 1, 2, 3."),
        ],
        mistakes=["Lặp quá số cửa → unlock khi không còn cửa / không còn chìa."],
    ),
    "6-6": Theory(
        concept=[
            "Gói một chuỗi thao tác lặp lại (bước, đập thùng, bước) thành hàm để gọi nhiều lần.",
            "Hàm giúp code ngắn - dễ đạt sao \"code gọn\".",
        ],
        starter_notes=[
            ("def smash():", "Hàm phá thùng."),
            ("    hero.move_right()", "Mới có bước đi - thiếu phần đập thùng."),
            ("smash()", "Gọi hàm một lần."),
        ],
        example=[
            ("def climb():", "Hàm leo một bậc."),
            ('    hero.attack("up")', "Đập thùng phía trên."),
            ("    hero.move_up()", "Leo lên."),
            ("climb()", ""),
            ("climb()", "Leo 2 bậc."),
        ],
        mistakes=["Định nghĩa hàm nhưng quên gọi."],
    ),
    "7-6": Theory(
        concept=[
            "Chỉ số âm đếm từ cuối chuỗi: `s[-1]` là ký tự cuối, `s[-2:]` là 2 ký tự cuối.",
            "Rương báu mở bằng `hero.open_chest(huong)` - mỗi rương mở được thưởng thêm xu khi qua màn.",
        ],
        starter_notes=[
            ('# note = "Mật mã ở cuối thư: 42"', "Biến note có sẵn."),
            ("print(note[0])", "In chữ M - ký tự đầu."),
        ],
        example=[
            ('code = "ABC-2026"', ""),
            ("print(code[-4:])", "2026."),
            ("print(int(code[-4:]) + 1)", "2027."),
        ],
        mistakes=["`note[-2]` chỉ lấy MỘT ký tự (số 4), không phải 42."],
    ),
    "8-6": Theory(
        concept=[
            "`hero.find_objects(\"box\")` trả về list dict {\"x\", \"y\"} của các thùng (dùng được với \"chest\", \"key\", \"lock\"...).",
            "Ô bên trái của (x, y) là (x - 1, y): đứng đó rồi `attack(\"right\")`.",
        ],
        starter_notes=[
            ('boxes = hero.find_objects("box")', "List toạ độ các thùng."),
            ("print(boxes)", "In ra để xem."),
        ],
        example=[
            ('for chest in hero.find_objects("chest"):', "Duyệt các rương."),
            ('    hero.move_to(chest["x"] + 1, chest["y"])', "Đứng bên PHẢI rương."),
            ('    hero.open_chest("left")', "Mở rương bên trái."),
        ],
        mistakes=["Lấy danh sách ngọc TRƯỚC khi đập thùng - thiếu các viên rơi ra sau."],
    ),
    "9-6": Theory(
        concept=[
            "`d.items()` cho từng cặp (khoá, giá trị) của dict: `for k, v in d.items():`.",
            "Dict làm \"kế hoạch\": khoá là hướng, giá trị là việc cần làm.",
        ],
        starter_notes=[
            ("for direction in plan:", "Duyệt dict chỉ cho khoá (hướng)."),
            ("    print(direction)", "In up, down, right."),
        ],
        example=[
            ('menu = {"phở": 40, "bún": 35}', ""),
            ("for dish, price in menu.items():", "Cả tên lẫn giá."),
            ('    print(dish, price, "nghìn")', ""),
        ],
        mistakes=["Duyệt `for direction in plan` rồi quên tra `plan[direction]`."],
    ),
    "10-6": Theory(
        concept=[
            "Comprehension trên bản đồ: `[(x, y) for y, row in enumerate(grid) for x, t in enumerate(row) if t == \"chest\"]`.",
            "Ô ngay DƯỚI rương (x, y) là (x, y + 1) - đứng đó và mở hướng \"up\".",
        ],
        starter_notes=[
            ("grid = hero.scan()", "Bản đồ grid[y][x]."),
            ("print(grid[1])", "Hàng 1 - nơi có các rương."),
        ],
        example=[
            ('board = [["box", "floor"], ["floor", "box"]]', ""),
            ('boxes = [(x, y) for y, row in enumerate(board) for x, t in enumerate(row) if t == "box"]', ""),
            ("print(boxes)", "[(0, 0), (1, 1)]."),
        ],
        mistakes=["Đi tới đúng ô rương bằng move_to → báo lỗi vì rương chắn đường."],
    ),
    "11-6": Theory(
        concept=[
            "`thu in tap_hop` kiểm tra rất nhanh - hợp để hỏi \"thứ này có nằm trong nhóm được phép không?\".",
            "Vòng while + if: mỗi vòng chỉ làm MỘT việc (đập hoặc bước), rồi nhìn lại.",
        ],
        starter_notes=[
            ('while hero.look("right") != "exit":', "Lặp tới khi cổng ở ngay bên phải."),
            ("    hero.move_right()", "Chỉ bước - sẽ đụng thùng."),
        ],
        example=[
            ('edible = {"táo", "cam"}', ""),
            ('for food in ["táo", "đá", "cam"]:', ""),
            ("    if food in edible:", ""),
            ('        print("Ăn", food)', "Ăn táo, Ăn cam."),
        ],
        mistakes=["Đập cả ngọc rơi ra: ngọc không thuộc breakable, cứ bước lên là nhặt."],
    ),
    "12-6": Theory(
        concept=[
            "Kết hợp nhiều vật thể: chìa → cửa khoá → cửa mật mã.",
            "`int(math.sqrt(50))` lấy phần nguyên của căn bậc hai: 7.",
        ],
        starter_notes=[
            ("import math", "Nạp thư viện."),
            ("print(math.sqrt(4))", "In 2.0."),
        ],
        example=[
            ("import math", ""),
            ("side = math.sqrt(30)", "≈ 5.477."),
            ("print(int(side), math.ceil(side))", "5 6."),
        ],
        mistakes=["Quên mở cửa khoá trước khi đi tới cửa mật mã."],
    ),
    "13-6": Theory(
        concept=[
            "`hero.try_code` trả về True khi đúng - dùng `break` để dừng thử.",
            "Thứ tự công việc quan trọng: thùng → cửa màu → rương → cúp.",
        ],
        starter_notes=[
            ("from itertools import permutations", "Nạp hàm hoán vị."),
            ('hero.attack("right")', "Đập thùng đầu tiên."),
        ],
        example=[
            ("from itertools import permutations", ""),
            ('for order in permutations(["A", "B"]):', ""),
            ("    print(order)", "('A', 'B'), ('B', 'A')."),
        ],
        mistakes=["Dùng enter_code để thử: sai là mất máu - try_code thì không."],
    ),
    "14-6": Theory(
        concept=[
            "`Counter(...)` đếm được mọi loại ô của bản đồ cùng lúc.",
            "Trải phẳng list lồng nhau bằng generator: `(t for row in grid for t in row)`.",
        ],
        starter_notes=[
            ("from collections import Counter", "Nạp Counter."),
            ("grid = hero.scan()", "Bản đồ."),
            ("print(grid[1])", "In hàng 1."),
        ],
        example=[
            ("from collections import Counter", ""),
            ('rows = [["a", "b"], ["a", "a"]]', ""),
            ("print(Counter(x for row in rows for x in row))", "Counter({'a': 3, 'b': 1})."),
        ],
        mistakes=["Đưa thẳng grid vào Counter → lỗi vì list không làm khoá được."],
    ),
    "15-6": Theory(
        concept=[
            "Ôn lại `date.fromisoformat(...)` và `.weekday()` (0 = thứ Hai).",
            "Mở rương bằng `hero.open_chest(huong)`.",
        ],
        starter_notes=[
            ("from datetime import date", "Nạp kiểu date."),
            ("print(day)", "In chuỗi ngày."),
        ],
        example=[
            ("from datetime import date", ""),
            ("print(date(2026, 1, 1).weekday())", "3 - thứ Năm."),
        ],
        mistakes=["Gọi .weekday() trên chuỗi → AttributeError; phải đổi sang date trước."],
    ),
    "16-6": Theory(
        concept=[
            "`hero.unlock` khi chưa có chìa ném `ValueError` - bắt lỗi để xử lý thay vì để chương trình dừng.",
            "Trong `except`: sửa tình huống (đi lấy chìa) rồi thử lại.",
        ],
        starter_notes=[
            ('hero.unlock("right")', "Chưa có chìa → ValueError, chương trình dừng."),
            ("hero.move_right(4)", "Không chạy tới được."),
        ],
        example=[
            ("try:", ""),
            ('    value = int("abc")', ""),
            ("except ValueError:", "Không đổi được..."),
            ("    value = 0", "...dùng giá trị mặc định."),
            ("print(value)", "0."),
        ],
        mistakes=["Bắt nhầm loại lỗi (ví dụ except TypeError) - lỗi vẫn làm dừng chương trình."],
    ),
    "17-6": Theory(
        concept=[
            "Class gom dữ liệu (số rương đã mở) và hành động (open) vào một chỗ.",
            "Phương thức có thể gọi lệnh của hero và cập nhật thuộc tính của self.",
        ],
        starter_notes=[
            ("class Explorer:", "Class nhà thám hiểm."),
            ("    def __init__(self):", "Chạy khi tạo."),
            ("        self.opened = 0", "Chưa mở rương nào."),
        ],
        example=[
            ("class Counter2:", ""),
            ("    def __init__(self):", ""),
            ("        self.value = 0", ""),
            ("    def click(self):", ""),
            ("        self.value += 1", ""),
            ("c = Counter2()", ""),
            ("c.click()", ""),
            ("print(c.value)", "1."),
        ],
        mistakes=["Quên tăng self.opened → nói sai số rương."],
    ),
    "18-6": Theory(
        concept=[
            "Một vòng lặp \"thông minh\": mỗi bước nhìn ô bên phải rồi chọn hành động phù hợp (if / elif / else).",
            "Có thể kiểm tra thêm hướng khác (phía dưới) trong cùng vòng lặp.",
        ],
        starter_notes=[
            ('while hero.look("right") != "exit":', "Lặp tới khi cổng bên phải."),
            ("    hero.move_right()", "Chỉ bước - sẽ kẹt ở thùng."),
        ],
        example=[
            ("for thing in [\"box\", \"floor\", \"lock\"]:", ""),
            ('    if thing == "box":', ""),
            ('        print("đập")', ""),
            ('    elif thing == "lock":', ""),
            ('        print("mở khoá")', ""),
            ("    else:", ""),
            ('        print("bước")', ""),
        ],
        mistakes=["Viết các if riêng lẻ: một vòng có thể vừa đập vừa bước, làm lệch vị trí."],
    ),
    "19-6": Theory(
        concept=[
            "`sorted(ds, key=lambda c: c[\"x\"])` xếp list dict theo khoá \"x\".",
            "`reverse=True` để xếp ngược (từ phải sang trái).",
        ],
        starter_notes=[
            ('chests = hero.find_objects("chest")', "List rương."),
            ("print(chests)", "In ra để xem."),
        ],
        example=[
            ('pets = [{"name": "Mèo", "age": 3}, {"name": "Chó", "age": 1}]', ""),
            ('youngest = sorted(pets, key=lambda p: p["age"])[0]', ""),
            ('print(youngest["name"])', "Chó."),
        ],
        mistakes=["key=c[\"x\"] (thiếu lambda) → lỗi NameError."],
    ),
    "20-6": Theory(
        concept=[
            "Một regex có thể lấy chữ (`\\w+`) hoặc số (`\\d+`); dùng nhiều lần cho nhiều thông tin.",
            "Kết quả `.group(1)` luôn là chuỗi - số cần `int()`, hướng dùng thẳng được.",
        ],
        starter_notes=[
            ("import re", "Nạp regex."),
            ("print(letter)", "In mật thư."),
        ],
        example=[
            ("import re", ""),
            ('msg = "Gặp ở phòng B lúc 15 giờ"', ""),
            ('room = re.search(r"phòng (\\w+)", msg).group(1)', "'B'."),
            ('hour = int(re.search(r"lúc (\\d+)", msg).group(1))', "15."),
        ],
        mistakes=["Quên dấu cách trong mẫu (\"hướng(\\w+)\") → không khớp."],
    ),
    "21-6": Theory(
        concept=[
            "Closure tạo ra các \"bùa\" giống nhau nhưng nhớ hướng khác nhau.",
            "Hàm cũng có thể nằm trong list: `[f, g]` rồi gọi lần lượt.",
        ],
        starter_notes=[
            ("def make_opener(direction):", "Nhà máy tạo bùa mở rương."),
            ("    pass", "Chưa tạo gì."),
        ],
        example=[
            ("def make_greeter(name):", ""),
            ("    def greet():", ""),
            ('        print("Chào", name)', ""),
            ("    return greet", ""),
            ('for g in [make_greeter("An"), make_greeter("Bình")]:', ""),
            ("    g()", "Chào An, Chào Bình."),
        ],
        mistakes=["Gọi make_opener(\"up\") mà không gọi hàm nó trả về → rương chưa mở."],
    ),
    "22-6": Theory(
        concept=[
            "`np.array(bang).max()` tìm số lớn nhất trong cả bảng 2 chiều.",
            "Kết quả là số của NumPy - `int(...)` để dùng làm mật mã.",
        ],
        starter_notes=[
            ("import numpy as np", "Nạp NumPy."),
            ("print(np.array(weights).shape)", "In (2, 2)."),
        ],
        example=[
            ("import numpy as np", ""),
            ("scores = np.array([[5, 9], [7, 6]])", ""),
            ("print(scores.max(), scores.min())", "9 5."),
        ],
        mistakes=["max(weights) với list lồng nhau so sánh cả hàng - không ra số lớn nhất."],
    ),
    "23-6": Theory(
        concept=[
            "Gỡ lỗi chương trình có vật thể: kiểm tra THỨ TỰ (nhặt chìa trước khi mở), TÊN lệnh, và HƯỚNG.",
            "Đọc thông báo lỗi ở Bảng tin để biết dòng nào sai, sửa từng lỗi rồi chạy lại.",
        ],
        starter_notes=[
            ('hero.unlock("right")', "Chưa có chìa mà đã mở cửa."),
            ("hero.move_right(2)", "Đi qua chìa."),
            ('hero.open_chests("down")', "Tên lệnh có đúng không?"),
            ('hero.attack("left")', "Thùng nằm ở hướng nào?"),
            ("hero.move_right(3)", "Đi tới cúp."),
        ],
        example=[
            ("hero.move_right()", "Ví dụ code ĐÚNG thứ tự: nhặt chìa..."),
            ('hero.unlock("right")', "...rồi mới mở cửa."),
        ],
        mistakes=["Sửa xong một lỗi là dừng - hãy chạy lại để tìm lỗi tiếp theo."],
    ),
})

THEORY.update(PRACTICE_THEORY)
