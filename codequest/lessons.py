"""Bài giảng "Hiểu kỹ hơn" cho từng World.

Mỗi World có: một hình ảnh đời thường, mẫu câu lệnh giải thích từng phần,
một chương trình nhỏ chạy thử từng dòng, và mẹo nhớ. Chương trình chạy thử
là ví dụ chung, không phải lời giải của màn nào.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorldLesson:
    analogy: str
    syntax: list[tuple[str, str]]
    walkthrough: list[tuple[str, str]]
    tips: list[str]


WORLD_LESSONS: dict[int, WorldLesson] = {
    1: WorldLesson(
        analogy=(
            "Viết chương trình giống viết giấy nhắn việc cho một người bạn rất ngoan nhưng rất \"thẳng tính\": "
            "bạn ấy làm ĐÚNG từng chữ bạn viết, theo đúng thứ tự từ trên xuống, không tự đoán ý. "
            "Viết sai một chữ là bạn ấy không hiểu."
        ),
        syntax=[
            ("hero.move_right(3)", "hero = AI làm · dấu . = \"của\" · move_right = LÀM GÌ · (3) = LÀM BAO NHIÊU."),
            ('hero.say("Chào")', "Chữ phải nằm trong dấu nháy để Python biết đó là câu nói, không phải tên lệnh."),
            ("# ghi chú", "Sau dấu # là lời nhắn cho người đọc - Python bỏ qua."),
        ],
        walkthrough=[
            ("hero.move_down(1)", "Bước 1: Python đọc dòng đầu tiên, hero đi xuống 1 ô."),
            ("hero.move_right(2)", "Bước 2: dòng trên xong mới tới dòng này - hero sang phải 2 ô."),
            ('hero.say("Tới rồi")', "Bước 3: hero nói. Hết dòng thì chương trình kết thúc."),
        ],
        tips=[
            "Đọc to lệnh lên: \"hero, đi sang phải 3 ô\". Đọc thấy đúng ý thì code thường đúng.",
            "Python phân biệt chữ hoa, chữ thường và cần đúng chính tả từng chữ cái.",
            "Bấm Chạy thường xuyên: sai ở đâu sẽ thấy ngay ở đó.",
        ],
    ),
    2: WorldLesson(
        analogy=(
            "Biến giống một chiếc hộp có dán nhãn tên. `coins = 5` nghĩa là bỏ số 5 vào hộp tên coins. "
            "Muốn dùng thì gọi tên hộp. Bỏ thứ mới vào hộp thì thứ cũ bị lấy ra mất."
        ),
        syntax=[
            ("ten_bien = gia_tri", "TRÁI dấu = là tên hộp, PHẢI là thứ cất vào. Python tính vế phải trước rồi mới cất."),
            ("total = a + b", "Có thể cất kết quả của một phép tính."),
            ("count += 1", "Viết tắt của count = count + 1: lấy số cũ cộng 1 rồi cất lại."),
        ],
        walkthrough=[
            ("coins = 10", "Tạo hộp coins, cất số 10."),
            ("price = 3", "Tạo hộp price, cất số 3."),
            ("coins = coins - price", "Vế phải: 10 - 3 = 7. Cất 7 vào coins (số 10 cũ bị thay)."),
            ('print("Còn", coins, "xu")', "Bảng tin hiện: Còn 7 xu."),
        ],
        tips=[
            "Đặt tên biến nói rõ nó chứa gì: so_buoc dễ hiểu hơn x.",
            "Số không có dấu nháy (5), chữ thì có (\"5\"). Hai thứ này KHÁC nhau.",
            "Không chắc biến đang chứa gì? Dùng print(ten_bien) để xem.",
        ],
    ),
    3: WorldLesson(
        analogy=(
            "Câu lệnh if giống khi ra đường: NẾU trời mưa THÌ mang áo mưa, NGƯỢC LẠI thì đội mũ. "
            "Máy hỏi \"trời có mưa không?\" - đúng thì làm việc này, sai thì làm việc kia."
        ),
        syntax=[
            ("if dieu_kien:", "if = \"nếu\". Cuối dòng bắt buộc có dấu hai chấm."),
            ("    lenh_khi_dung", "Thụt vào 4 dấu cách = lệnh này nằm TRONG if, chỉ chạy khi điều kiện đúng."),
            ("elif dieu_kien_khac:", "\"Nếu không thì nếu...\": chỉ xét khi các điều kiện phía trên đều sai."),
            ("else:", "\"Còn lại\": chạy khi mọi điều kiện phía trên đều sai."),
        ],
        walkthrough=[
            ("hp = 2", "Hero còn 2 máu."),
            ("if hp >= 3:", "Hỏi: 2 >= 3? SAI → bỏ qua khối bên dưới."),
            ('    hero.say("Khoẻ re")', "Không chạy."),
            ("elif hp == 2:", "Hỏi tiếp: 2 == 2? ĐÚNG → chạy khối này."),
            ('    hero.say("Hơi mệt")', "Hero nói \"Hơi mệt\"."),
            ("else:", "Đã có nhánh đúng rồi nên bỏ qua else."),
            ('    hero.say("Nguy hiểm")', "Không chạy."),
        ],
        tips=[
            "Một dấu = là CẤT vào; hai dấu == là HỎI \"có bằng không?\".",
            "Trong chuỗi if / elif / else, Python chỉ chạy MỘT nhánh: nhánh đúng đầu tiên.",
            "Dòng không thụt vào thì không thuộc if - nó luôn chạy.",
        ],
    ),
    4: WorldLesson(
        analogy=(
            "Vòng lặp giống khi cô giáo bảo \"chép 5 lần\": thay vì viết 5 dòng giống nhau, bạn viết 1 dòng và "
            "nói \"làm 5 lần\". `for` dùng khi biết trước số lần; `while` dùng khi \"làm tới khi xong thì thôi\", "
            "như ăn cho tới khi no."
        ),
        syntax=[
            ("for i in range(4):", "Lặp 4 lần; i lần lượt là 0, 1, 2, 3."),
            ("for i in range(1, 4):", "i lần lượt là 1, 2, 3 (không có 4)."),
            ("while dieu_kien:", "Hỏi điều kiện: đúng thì chạy khối lệnh rồi quay lại hỏi tiếp; sai thì thoát."),
            ("break", "Thoát khỏi vòng lặp ngay lập tức."),
        ],
        walkthrough=[
            ("for i in range(3):", "Vòng 1: i = 0. Vòng 2: i = 1. Vòng 3: i = 2. Rồi hết."),
            ("    hero.move_down()", "Mỗi vòng hero đi xuống 1 ô → tổng cộng 3 ô."),
            ("    print(i)", "Bảng tin hiện 0, rồi 1, rồi 2."),
            ('hero.say("Xong")', "Không thụt lề nên chạy MỘT lần, sau khi vòng lặp kết thúc."),
        ],
        tips=[
            "Tìm phần \"lặp lại\" trong đường đi rồi viết nó MỘT lần trong thân vòng lặp.",
            "range(n) bắt đầu từ 0 và dừng TRƯỚC n.",
            "Với while, mỗi vòng phải có gì đó thay đổi, nếu không vòng lặp chạy mãi.",
        ],
    ),
    5: WorldLesson(
        analogy=(
            "Ép kiểu giống đổi tiền: tờ giấy ghi \"42\" (chuỗi) chỉ là chữ, chưa tính được. `int(...)` đổi nó "
            "thành con số 42 thật để cộng trừ. Ngược lại, `str(...)` biến con số thành chữ để ghép vào câu."
        ),
        syntax=[
            ('int("42")', "Chuỗi → số nguyên 42. Chuỗi chỉ được chứa chữ số."),
            ('float("2.5")', "Chuỗi → số thực 2.5."),
            ("str(42)", "Số → chuỗi \"42\", để nối với chữ khác."),
            ("bool(0)", "→ False. Số 0, chuỗi rỗng, list rỗng là False; còn lại là True."),
        ],
        walkthrough=[
            ('a = "12"', "a là CHUỖI \"12\" (có dấu nháy)."),
            ('b = "30"', "b là chuỗi \"30\"."),
            ("print(a + b)", "Chuỗi + chuỗi = NỐI lại: in ra 1230."),
            ("print(int(a) + int(b))", "Đổi sang số trước rồi cộng: in ra 42."),
            ('print("Tổng: " + str(42))', "Số đổi thành chuỗi để nối: in ra Tổng: 42."),
        ],
        tips=[
            "Thấy dấu nháy là chuỗi, dù bên trong toàn chữ số.",
            "int(\"7.5\") báo lỗi - đi đường vòng: int(float(\"7.5\")).",
            "Trước khi tính, in giá trị ra để chắc nó là số chứ không phải chữ.",
        ],
    ),
    6: WorldLesson(
        analogy=(
            "Hàm giống một \"chiêu thức\" bạn tự đặt tên: luyện chiêu một lần (def), sau đó chỉ cần gọi tên chiêu là "
            "hero làm cả chuỗi động tác. Hàm có tham số giống chiêu chỉnh được: \"nhảy 2 ô\", \"nhảy 3 ô\". "
            "Hàm có return giống máy bán nước: đưa vào thứ gì, máy trả ra kết quả."
        ),
        syntax=[
            ("def ten_ham(tham_so):", "def = \"định nghĩa\": tạo chiêu mới tên ten_ham, nhận vào tham_so. Có dấu :"),
            ("    return ket_qua", "Gửi kết quả về chỗ gọi và kết thúc hàm."),
            ("x = ten_ham(5)", "GỌI hàm với tham_so = 5, cất kết quả vào x."),
            ("len(ds), max(ds), sum(ds)", "Hàm có sẵn của Python - gọi ngay, không cần def."),
        ],
        walkthrough=[
            ("def double(n):", "Python ghi nhớ hàm double, CHƯA chạy gì cả."),
            ("    return n * 2", "(Chỉ chạy khi hàm được gọi.)"),
            ("x = double(4)", "Gọi hàm: n = 4 → tính 4 * 2 = 8 → trả về 8 → x = 8."),
            ("y = double(x) + 1", "Gọi tiếp với n = 8 → được 16, cộng 1 → y = 17."),
            ("print(x, y)", "Bảng tin hiện: 8 17."),
        ],
        tips=[
            "def chỉ là \"dạy chiêu\"; muốn chạy phải GỌI kèm dấu ngoặc ().",
            "print chỉ hiện ra màn hình; return mới gửi kết quả cho code dùng tiếp.",
            "Thấy một đoạn code lặp lại 2-3 lần? Gói nó vào một hàm.",
        ],
    ),
    7: WorldLesson(
        analogy=(
            "Chuỗi giống một hàng ghế có đánh số, mỗi ghế có một ký tự ngồi. Số ghế bắt đầu từ 0. "
            "Cắt chuỗi giống nói \"mời các bạn từ ghế 1 tới TRƯỚC ghế 4 đứng dậy\"."
        ),
        syntax=[
            ("s[0]", "Ký tự ở ghế số 0 (ký tự đầu tiên)."),
            ("s[-1]", "Ký tự cuối cùng (số âm là đếm ngược từ cuối)."),
            ("s[1:4]", "Từ vị trí 1 tới TRƯỚC vị trí 4: lấy vị trí 1, 2, 3."),
            ('f"Xin chào {ten}"', "f-string: chèn giá trị của biến vào trong câu."),
            ('s.upper(), s.split(","), s.replace("a", "b")', "Viết hoa; cắt thành list theo dấu phẩy; thay chữ a bằng b."),
        ],
        walkthrough=[
            ('word = "PYTHON"', "P ở vị trí 0, Y ở 1, T ở 2, H ở 3, O ở 4, N ở 5."),
            ("print(word[0])", "In P."),
            ("print(word[2:5])", "Vị trí 2, 3, 4 → in THO."),
            ("print(word[::-1])", "Bước -1 = đọc ngược → in NOHTYP."),
            ('print(f"Có {len(word)} chữ")', "len đếm được 6 ký tự → in Có 6 chữ."),
        ],
        tips=[
            "Luôn đếm từ 0. Viết số vị trí dưới từng chữ ra giấy nháp cho chắc.",
            "Cắt chuỗi ra vẫn là chuỗi - cần int(...) nếu muốn tính toán.",
            "Phương thức chuỗi không sửa chuỗi gốc mà tạo chuỗi mới: nhớ cất lại vào biến.",
        ],
    ),
    8: WorldLesson(
        analogy=(
            "List giống chiếc ba lô có nhiều ngăn đánh số 0, 1, 2...: thêm đồ, lấy đồ, đổi đồ đều được. "
            "Tuple giống hộp quà đã dán kín: xem được bên trong nhưng không thay được. Toạ độ (x, y) thường cất "
            "trong tuple."
        ),
        syntax=[
            ("bag = [3, 5, 8]", "List 3 phần tử: trong ngoặc vuông, cách nhau bằng dấu phẩy."),
            ("bag[0]", "Phần tử ở ngăn số 0 → 3."),
            ("bag.append(9)", "Thêm 9 vào CUỐI list."),
            ("for item in bag:", "Lấy lần lượt từng món trong ba lô."),
            ("x, y = (2, 5)", "Mở gói tuple: x = 2, y = 5."),
        ],
        walkthrough=[
            ("scores = [7, 9]", "List có 2 phần tử."),
            ("scores.append(10)", "Giờ list là [7, 9, 10]."),
            ("total = 0", "Hộp cộng dồn, bắt đầu từ 0."),
            ("for s in scores:", "s lần lượt là 7, rồi 9, rồi 10."),
            ("    total += s", "total đổi dần: 0 → 7 → 16 → 26."),
            ("print(total, len(scores))", "In 26 3."),
        ],
        tips=[
            "Phần tử cuối có chỉ số len(list) - 1, hoặc dùng [-1] cho nhanh.",
            "append sửa list tại chỗ - đừng viết a = a.append(x).",
            "Mỗi viên ngọc là một dict như {\"x\": 2, \"y\": 1}: đọc bằng gem[\"x\"].",
        ],
    ),
    9: WorldLesson(
        analogy=(
            "Dict giống cuốn danh bạ điện thoại: tra theo TÊN (khoá) để ra SỐ (giá trị), không cần nhớ nó nằm "
            "trang mấy. Set giống túi sticker không trùng: bỏ vào sticker đã có thì túi không thay đổi."
        ),
        syntax=[
            ('prices = {"táo": 5, "cam": 7}', "Mỗi cặp khoá: giá trị, cách nhau bằng dấu phẩy, trong ngoặc nhọn."),
            ('prices["táo"]', "Tra giá trị của khoá \"táo\" → 5."),
            ('prices["lê"] = 4', "Thêm cặp mới (hoặc sửa nếu khoá đã có)."),
            ('prices.get("nho", 0)', "Tra an toàn: không có khoá thì trả về 0 thay vì báo lỗi."),
            ("seen = set()", "Tạo set rỗng; dùng seen.add(x) để thêm."),
        ],
        walkthrough=[
            ('fruits = ["táo", "cam", "táo"]', "List có \"táo\" 2 lần."),
            ("count = {}", "Dict rỗng làm sổ đếm."),
            ("for fruit in fruits:", "Lần lượt: táo, cam, táo."),
            ("    count[fruit] = count.get(fruit, 0) + 1", "táo: 0 + 1 = 1 → cam: 0 + 1 = 1 → táo: 1 + 1 = 2."),
            ("print(count)", "In {'táo': 2, 'cam': 1}."),
            ("print(len(set(fruits)))", "set bỏ phần trùng còn táo, cam → in 2."),
        ],
        tips=[
            "Khoá phải gõ y hệt, kể cả chữ hoa, chữ thường và dấu.",
            "{} là dict rỗng; set rỗng phải viết set().",
            "Lấy cả khoá lẫn giá trị: for khoa, gia_tri in d.items():",
        ],
    ),
    10: WorldLesson(
        analogy=(
            "List comprehension giống ra lệnh cho cả hàng: \"mỗi bạn trong hàng, ai cao hơn 1m5 thì bước lên\" - "
            "một câu thay cho cả đoạn dài. List lồng nhau giống bảng ô vuông trong vở: grid[hàng][cột]."
        ),
        syntax=[
            ("[x * 2 for x in nums]", "Với MỖI x trong nums, lấy x * 2 → được list mới."),
            ("[x for x in nums if x > 0]", "Chỉ giữ những x thoả điều kiện x > 0."),
            ("grid[y][x]", "Vào hàng y trước, rồi tới cột x trong hàng đó."),
            ("for y, row in enumerate(grid):", "Vừa lấy số hàng y, vừa lấy cả hàng row."),
        ],
        walkthrough=[
            ("nums = [3, -1, 4]", "List gốc."),
            ("big = [n * 10 for n in nums if n > 0]", "3 giữ → 30; -1 bỏ; 4 giữ → 40. big = [30, 40]."),
            ("table = [[1, 2], [3, 4]]", "Bảng 2 hàng, 2 cột."),
            ("print(table[1][0])", "Hàng 1 là [3, 4], lấy cột 0 → in 3."),
            ("flat = [v for row in table for v in row]", "Đi từng hàng, rồi từng số trong hàng: [1, 2, 3, 4]."),
        ],
        tips=[
            "Đọc comprehension bắt đầu từ chữ for: \"với mỗi n trong nums, nếu..., thì lấy...\".",
            "Bản đồ: y là hàng (trên → dưới), x là cột (trái → phải): grid[y][x] nhưng move_to(x, y).",
            "Comprehension khó đọc quá? Viết bằng for thường trước, rút gọn sau.",
        ],
    ),
    11: WorldLesson(
        analogy=(
            "Hai nhóm bạn: nhóm thích bóng đá và nhóm thích cờ vua. GIAO là các bạn thích CẢ HAI; HỢP là tất cả "
            "các bạn của hai nhóm (không đếm trùng); HIỆU là các bạn chỉ thích bóng đá mà không thích cờ vua - "
            "đúng như tập hợp trong môn Toán."
        ),
        syntax=[
            ("a & b", "Giao: có ở cả a và b."),
            ("a | b", "Hợp: có ở ít nhất một trong hai."),
            ("a - b", "Hiệu: có ở a nhưng không có ở b."),
            ("a ^ b", "Chỉ có ở MỘT bên (bỏ phần chung)."),
            ("x in a", "Hỏi: x có trong a không? → True / False."),
        ],
        walkthrough=[
            ('football = {"An", "Bình", "Chi"}', "Nhóm bóng đá."),
            ('chess = {"Bình", "Dũng"}', "Nhóm cờ vua."),
            ("print(football & chess)", "Phần chung → {'Bình'}."),
            ("print(football - chess)", "Chỉ bóng đá → {'An', 'Chi'} (thứ tự có thể khác)."),
            ('print("Dũng" in football)', "Dũng không có trong nhóm bóng đá → False."),
        ],
        tips=[
            "Phép giao, hợp, hiệu chỉ dùng cho set: list phải đổi bằng set(...) trước.",
            "a - b khác b - a: hãy hỏi \"có ở đâu mà không có ở đâu?\".",
            "Set không có thứ tự nên không lấy phần tử theo chỉ số được.",
        ],
    ),
    12: WorldLesson(
        analogy=(
            "`import math` giống mở hộp dụng cụ học Toán: trong đó có sẵn căn bậc hai, số π, máy làm tròn... "
            "Bạn không cần tự chế tạo, chỉ cần lấy ra dùng bằng math.ten_dung_cu."
        ),
        syntax=[
            ("import math", "Mở hộp dụng cụ - đặt ở đầu chương trình."),
            ("math.sqrt(16)", "Căn bậc hai → 4.0."),
            ("math.ceil(2.1), math.floor(2.9)", "Làm tròn LÊN → 3; làm tròn XUỐNG → 2."),
            ("3 ** 2", "Luỹ thừa: 3 mũ 2 = 9 (không dùng dấu ^)."),
            ("math.gcd(12, 18)", "Ước chung lớn nhất → 6."),
        ],
        walkthrough=[
            ("import math", "Có hộp dụng cụ math."),
            ("students = 45", "45 học sinh."),
            ("seats = 20", "Mỗi xe 20 chỗ."),
            ("print(students / seats)", "In 2.25 - không thuê được 0.25 chiếc xe!"),
            ("print(math.ceil(students / seats))", "Làm tròn lên → cần 3 xe."),
            ("print(round(math.pi, 2))", "π giữ 2 chữ số sau dấu chấm → 3.14."),
        ],
        tips=[
            "Quên import math thì Python báo NameError ngay.",
            "Bài \"cần bao nhiêu xe / hộp\" → làm tròn LÊN (ceil).",
            "sqrt cho số thực; cần số nguyên thì bọc int(...).",
        ],
    ),
    13: WorldLesson(
        analogy=(
            "3 bạn xếp hàng chụp ảnh có bao nhiêu cách xếp? Đó là HOÁN VỊ (đổi chỗ là khác). Chọn 2 bạn trực "
            "nhật trong 3 bạn có bao nhiêu cách? Đó là TỔ HỢP (An-Bình cũng như Bình-An). itertools là \"máy liệt "
            "kê\" giúp bạn không bỏ sót cách nào."
        ),
        syntax=[
            ("from itertools import permutations, combinations, product", "Lấy 3 công cụ liệt kê ra dùng."),
            ("permutations(ds)", "Mọi cách SẮP XẾP thứ tự."),
            ("combinations(ds, 2)", "Mọi cách CHỌN 2 phần tử, không tính thứ tự."),
            ("product(a, b)", "Ghép MỌI phần tử của a với MỌI phần tử của b."),
        ],
        walkthrough=[
            ("from itertools import permutations, combinations", "Lấy công cụ."),
            ('kids = ["An", "Bình", "Chi"]', "3 bạn."),
            ("print(len(list(permutations(kids))))", "Số cách xếp hàng: 3 × 2 × 1 → in 6."),
            ("for first, second in combinations(kids, 2):", "Lần lượt: (An, Bình), (An, Chi), (Bình, Chi)."),
            ("    print(first, second)", "In 3 cặp - không có cặp đảo ngược."),
        ],
        tips=[
            "Hỏi \"đổi chỗ có tính là khác không?\" - có: permutations; không: combinations.",
            "Kết quả là \"lười\": bọc list(...) nếu muốn đếm bằng len hoặc in ra.",
            "Tìm được đáp án rồi thì break để khỏi thử tiếp.",
        ],
    ),
    14: WorldLesson(
        analogy=(
            "Counter giống lớp trưởng kiểm phiếu: đọc từng phiếu và ghi vạch đếm cho từng tên. deque giống hàng "
            "người mua vé: người mới vào cuối hàng, người đầu hàng được phục vụ trước. defaultdict giống tủ đồ tự "
            "mọc thêm ngăn mới khi có bạn mới tới."
        ),
        syntax=[
            ("from collections import Counter, deque, defaultdict", "Lấy 3 công cụ."),
            ("Counter(ds).most_common(2)", "2 giá trị xuất hiện nhiều nhất: [(giá trị, số lần), ...]."),
            ("queue.popleft()", "Với deque: lấy người ở ĐẦU hàng ra."),
            ("groups = defaultdict(list)", "Khoá mới tự có sẵn một list rỗng."),
        ],
        walkthrough=[
            ("from collections import Counter, deque", "Lấy công cụ."),
            ('votes = ["Lan", "Minh", "Lan"]', "3 phiếu bầu."),
            ("tally = Counter(votes)", "tally giống dict: {'Lan': 2, 'Minh': 1}."),
            ("print(tally.most_common(1)[0][0])", "most_common(1) là [('Lan', 2)] → [0] là ('Lan', 2) → [0] nữa là Lan."),
            ('line = deque(["A", "B"])', "Hàng có A rồi tới B."),
            ('line.append("C")', "C vào cuối hàng."),
            ("print(line.popleft())", "A ở đầu hàng ra trước → in A."),
        ],
        tips=[
            "most_common trả về LIST các cặp - nhớ [0] để lấy cặp đầu tiên.",
            "Cần lấy ra ở đầu hàng nhiều lần → dùng deque thay cho list.",
            "deque(ds, maxlen=3) chỉ giữ 3 phần tử mới nhất.",
        ],
    ),
    15: WorldLesson(
        analogy=(
            "datetime giống một cuốn lịch thông minh: biết tháng nào 30 hay 31 ngày, năm nào nhuận. Bạn chỉ cần "
            "hỏi \"còn bao nhiêu ngày tới sinh nhật?\" hay \"45 ngày nữa là ngày nào?\" - lịch tự tính hộ."
        ),
        syntax=[
            ("from datetime import date, timedelta", "Lấy công cụ ngày và khoảng thời gian."),
            ("date(2026, 9, 5)", "Ngày 5/9/2026 - thứ tự là năm, tháng, ngày."),
            ('date.fromisoformat("2026-09-05")', "Đổi chuỗi năm-tháng-ngày thành ngày."),
            ("(later - earlier).days", "Số ngày giữa hai ngày."),
            ('day.strftime("%d/%m/%Y")', "Viết ngày kiểu Việt Nam: 05/09/2026."),
        ],
        walkthrough=[
            ("from datetime import date, timedelta", "Lấy công cụ."),
            ("start = date(2026, 1, 25)", "Ngày 25/1/2026."),
            ("later = start + timedelta(days=10)", "10 ngày sau: lịch tự sang tháng 2 → 4/2/2026."),
            ("print((later - start).days)", "Khoảng cách → in 10."),
            ("print(start.weekday())", "25/1/2026 là Chủ nhật → in 6 (0 là thứ Hai, 6 là Chủ nhật)."),
        ],
        tips=[
            "date(năm, tháng, ngày) - năm đứng trước.",
            "Muốn cộng ngày phải dùng timedelta, không cộng số thẳng vào ngày.",
            "Quên .days thì in ra cả dòng dài như \"10 days, 0:00:00\".",
        ],
    ),
    16: WorldLesson(
        analogy=(
            "try / except giống tấm đệm khi tập nhảy cao: cứ thử nhảy (try), nếu ngã (lỗi) thì đệm đỡ (except) "
            "và bạn đứng dậy nhảy tiếp, thay vì nghỉ cả buổi. Không có đệm, gặp lỗi là chương trình dừng hẳn."
        ),
        syntax=[
            ("try:", "Thử chạy khối lệnh bên dưới."),
            ("except ValueError:", "Nếu xảy ra lỗi ValueError thì chạy khối này thay vì dừng chương trình."),
            ("else:", "Chạy khi KHÔNG có lỗi nào."),
            ("finally:", "Luôn chạy, dù có lỗi hay không."),
            ('raise ValueError("Sai rồi")', "Tự báo lỗi khi dữ liệu không hợp lệ."),
        ],
        walkthrough=[
            ('texts = ["5", "abc", "7"]', "Có một phần tử không phải số."),
            ("total = 0", "Cộng dồn từ 0."),
            ("for text in texts:", "Lần lượt \"5\", \"abc\", \"7\"."),
            ("    try:", "Thử đổi sang số..."),
            ("        total += int(text)", "\"5\" → 5: được. \"abc\" → lỗi ValueError!"),
            ("    except ValueError:", "Đệm đỡ: bắt đúng lỗi ValueError."),
            ('        print("Bỏ qua", text)', "In \"Bỏ qua abc\" rồi chạy tiếp vòng sau."),
            ("print(total)", "5 + 7 → in 12."),
        ],
        tips=[
            "Bắt đúng tên lỗi (ValueError, KeyError...) để các lỗi khác vẫn hiện ra cho bạn sửa.",
            "Đặt try bên TRONG vòng lặp nếu muốn một lần lỗi không làm hỏng cả vòng lặp.",
            "Tên lỗi ở Bảng tin cho biết nên viết except loại nào.",
        ],
    ),
    17: WorldLesson(
        analogy=(
            "Class giống KHUÔN làm bánh: khuôn hình con cá (class) đúc ra được nhiều chiếc bánh cá (đồ vật). "
            "Mỗi chiếc có nhân riêng (thuộc tính) nhưng cùng hình dạng và cùng cách dùng (phương thức). "
            "`self` nghĩa là \"chính chiếc bánh này\"."
        ),
        syntax=[
            ("class Pet:", "Tạo khuôn tên Pet (tên class viết hoa chữ cái đầu)."),
            ("    def __init__(self, name):", "Tự chạy khi đúc đồ vật mới; self là đồ vật đó."),
            ("        self.name = name", "Cất dữ liệu vào đồ vật: thuộc tính name."),
            ("    def greet(self):", "Phương thức: việc mà đồ vật làm được."),
            ('cat = Pet("Mướp")', "Đúc một đồ vật mới từ khuôn Pet."),
        ],
        walkthrough=[
            ("class Pet:", "Khuôn Pet."),
            ("    def __init__(self, name):", "Khi đúc, nhận vào name."),
            ("        self.name = name", "Ghi tên lên đồ vật."),
            ("        self.meals = 0", "Mỗi con bắt đầu với 0 bữa."),
            ("    def eat(self):", "Phương thức ăn."),
            ("        self.meals += 1", "Chỉ con đang ăn mới tăng số bữa."),
            ('cat = Pet("Mướp")', "Tạo cat: name = Mướp, meals = 0."),
            ("cat.eat()", "Python tự đưa cat vào self → cat.meals = 1."),
            ("print(cat.name, cat.meals)", "In: Mướp 1."),
        ],
        tips=[
            "Mọi phương thức đều có self ở tham số đầu tiên.",
            "__init__ có HAI dấu gạch dưới ở mỗi bên.",
            "Magic method như __str__, __len__, __add__ quyết định print(), len(), dấu + làm gì với đồ vật của bạn.",
        ],
    ),
    18: WorldLesson(
        analogy=(
            "Màn trùm giống bài kiểm tra cuối kỳ: không có kiến thức mới, nhưng phải ghép nhiều kỹ năng đã học. "
            "Như nấu một bữa cơm: nấu cơm, rán trứng, luộc rau - làm xong món nào nếm thử món đó, rồi mới dọn mâm."
        ),
        syntax=[
            ("# Phần 1: ...", "Chia code thành từng phần, ghi chú tên mỗi phần."),
            ("weapons = {...}", "Dict để tra cứu (World 9)."),
            ("for ... in ...:", "Vòng lặp cho việc lặp lại (World 4)."),
            ("try: ... except ...:", "Tấm đệm cho việc có thể lỗi (World 16)."),
        ],
        walkthrough=[
            ("# Phần 1: chuẩn bị dữ liệu", "Viết, bấm Chạy, xem Bảng tin."),
            ('plan = {"right": 2, "down": 1}', "Dữ liệu tra cứu."),
            ("# Phần 2: hành động", "Chỉ viết tiếp khi phần 1 đã đúng."),
            ("for direction, steps in plan.items():", "Lặp qua từng cặp (hướng, số bước)."),
            ("    print(direction, steps)", "In ra để chắc dữ liệu đúng trước khi cho hero đi."),
        ],
        tips=[
            "Đọc kỹ đề, liệt kê các việc theo thứ tự trước khi gõ code.",
            "Xong mỗi phần thì bấm Chạy để kiểm tra - đừng đợi viết hết.",
            "Kẹt ở phần nào thì mở lại lý thuyết của World đó.",
        ],
    ),
    19: WorldLesson(
        analogy=(
            "Tưởng tượng băng chuyền trong nhà máy: map là máy đóng dấu lên TỪNG hộp đi qua; filter là cổng chỉ "
            "cho hộp đạt chuẩn đi tiếp; zip ghép từng hộp của băng chuyền A với hộp cùng vị trí của băng chuyền B. "
            "lambda là cái máy nhỏ lắp nhanh tại chỗ, không cần đặt tên."
        ),
        syntax=[
            ("lambda x: x * 2", "Hàm không tên: nhận x, trả về x * 2."),
            ("list(map(f, ds))", "Áp f lên từng phần tử."),
            ("list(filter(f, ds))", "Giữ phần tử mà f trả về True."),
            ("zip(a, b)", "Ghép cặp theo vị trí."),
            ("sorted(ds, key=lambda p: p[1])", "Sắp xếp theo phần tử thứ hai của mỗi cặp."),
        ],
        walkthrough=[
            ("nums = [4, 7, 10]", "List gốc."),
            ("print(list(map(lambda n: n + 1, nums)))", "Mỗi số cộng 1 → [5, 8, 11]."),
            ("print(list(filter(lambda n: n % 2 == 0, nums)))", "Chỉ giữ số chẵn → [4, 10]."),
            ('names = ["An", "Bo"]', "Hai tên."),
            ("for name, number in zip(names, nums):", "Cặp (An, 4), (Bo, 7); số 10 không có cặp nên bị bỏ."),
            ("    print(name, number)", "In 2 dòng."),
        ],
        tips=[
            "map / filter cho kết quả \"lười\": bọc list(...) để xem.",
            "lambda chỉ viết được MỘT biểu thức và không cần chữ return.",
            "key=... nhận một HÀM (thường là lambda), không phải một giá trị.",
        ],
    ),
    20: WorldLesson(
        analogy=(
            "Regex giống tấm khuôn soi chữ: bạn mô tả hình dạng chữ cần tìm (ví dụ \"một dãy chữ số\"), rồi đặt "
            "khuôn lên văn bản để tìm mọi chỗ vừa khuôn. XML giống những hộp quà lồng nhau có dán nhãn: mỗi thẻ là "
            "một hộp, có tên và ghi thông tin bên ngoài (thuộc tính)."
        ),
        syntax=[
            ("import re", "Mở thư viện regex."),
            (r're.findall(r"\d+", text)', "Tìm MỌI dãy chữ số → list các chuỗi."),
            (r're.search(r"x(\d+)", text).group(1)', "Tìm chỗ khớp đầu tiên, lấy phần nằm trong ngoặc ( )."),
            ("ET.fromstring(xml_text)", "Đọc XML thành cây thẻ."),
            ('tag.get("x")', "Đọc thuộc tính x của thẻ (luôn là chuỗi)."),
        ],
        walkthrough=[
            ("import re", "Lấy thư viện regex."),
            ('text = "Kho 1 có 12 ngọc, kho 2 có 30 ngọc"', "Văn bản cần đọc."),
            (r'nums = re.findall(r"\d+", text)', r'\d+ là một hay nhiều chữ số liền nhau → ["1", "12", "2", "30"].'),
            ("print(sum(int(n) for n in nums))", "Đổi từng chuỗi sang số rồi cộng → in 45."),
            (r'match = re.search(r"có (\d+)", text)', "Chỗ khớp đầu tiên là \"có 12\"."),
            ("print(match.group(1))", "Phần trong ngoặc → in 12."),
        ],
        tips=[
            r'Viết mẫu với chữ r phía trước: r"\d+".',
            "Kết quả regex và thuộc tính XML đều là CHUỖI - cần int(...) trước khi tính.",
            "re.search không tìm thấy thì trả về None - kiểm tra trước khi gọi .group.",
        ],
    ),
    21: WorldLesson(
        analogy=(
            "Closure giống chiếc máy được cài sẵn công thức: máy \"cộng 5\" sau khi tạo ra sẽ nhớ mãi số 5, dù người "
            "cài đặt đã đi về. Decorator giống giấy gói quà: món quà (hàm gốc) giữ nguyên, nhưng lớp giấy làm "
            "thêm việc trước hoặc sau khi mở (in lời chào, làm lại 2 lần...)."
        ),
        syntax=[
            ("def make_adder(k):", "Hàm NGOÀI nhận k..."),
            ("    def add(x):", "...tạo hàm TRONG có dùng k..."),
            ("        return x + k", "...hàm trong nhớ k."),
            ("    return add", "Trả về chính hàm trong (KHÔNG có ngoặc)."),
            ("@decorator", "Đặt ngay trên def: nghĩa là f = decorator(f)."),
        ],
        walkthrough=[
            ("def make_adder(k):", "Nhà máy tạo hàm cộng."),
            ("    def add(x):", "Hàm con."),
            ("        return x + k", "Dùng k của hàm ngoài."),
            ("    return add", "Gửi hàm con ra ngoài."),
            ("plus5 = make_adder(5)", "plus5 là hàm add đã nhớ k = 5."),
            ("print(plus5(10))", "10 + 5 → in 15."),
            ("def loud(func):", "Decorator: nhận một hàm..."),
            ("    def wrapper():", "...tạo hàm bọc..."),
            ('        print("Bắt đầu")', "...làm thêm việc TRƯỚC..."),
            ("        func()", "...rồi gọi hàm gốc."),
            ("    return wrapper", "Trả hàm bọc ra."),
            ("@loud", "Bọc hàm hello ngay bên dưới."),
            ("def hello():", "Hàm gốc."),
            ('    print("Xin chào")', "Gọi hello() sẽ in \"Bắt đầu\" rồi \"Xin chào\"."),
        ],
        tips=[
            "return ten_ham (không ngoặc) = trả về hàm; return ten_ham() = gọi hàm rồi trả về kết quả.",
            "Decorator phải trả về hàm bọc, nếu không hàm sau khi bọc sẽ thành None.",
            "Decorator có tham số như @repeat(3) cần thêm một tầng hàm nữa.",
        ],
    ),
    22: WorldLesson(
        analogy=(
            "NumPy giống bảng tính Excel siêu tốc cho Python: thay vì cộng từng ô bằng vòng lặp, bạn ra lệnh cho "
            "CẢ BẢNG cùng lúc: \"cộng mọi ô thêm 1\", \"tìm số lớn nhất\", \"cộng theo từng cột\"."
        ),
        syntax=[
            ("import numpy as np", "Mở NumPy, gọi tắt là np."),
            ("table = np.array([[1, 2], [3, 4]])", "Mảng 2 hàng, 2 cột."),
            ("table.sum(), table.max(), table.mean()", "Tổng, số lớn nhất, trung bình của cả mảng."),
            ("table.sum(axis=0)", "Cộng dọc xuống theo CỘT → mỗi cột ra một số."),
            ("table[table > 2]", "Lọc: chỉ giữ các số lớn hơn 2."),
        ],
        walkthrough=[
            ("import numpy as np", "Lấy NumPy."),
            ("marks = np.array([[8, 6], [9, 7]])", "Mỗi hàng là một học sinh, mỗi cột là một môn."),
            ("print(marks.shape)", "In (2, 2): 2 hàng, 2 cột."),
            ("print(marks.sum(axis=1))", "Tổng theo hàng (mỗi học sinh) → [14 16]."),
            ("print(marks.mean(axis=0))", "Trung bình mỗi môn → [8.5 6.5]."),
            ("print((marks >= 8).sum())", "Đếm điểm từ 8 trở lên: 8 và 9 → in 2."),
        ],
        tips=[
            "axis=0 = đi dọc xuống (theo cột); axis=1 = đi ngang (theo hàng).",
            "A * B nhân từng ô với nhau; nhân ma trận phải dùng A @ B.",
            "Kết quả là số kiểu NumPy: bọc int(...) khi cần nhập mật mã.",
        ],
    ),
    23: WorldLesson(
        analogy=(
            "Gỡ lỗi giống làm thám tử: đọc dấu vết (thông báo lỗi), khoanh vùng hiện trường (dòng bị tô đỏ), hỏi "
            "nhân chứng (in giá trị biến ra), rồi mới kết luận thủ phạm. Thám tử giỏi không đoán mò."
        ),
        syntax=[
            ("SyntaxError", "Viết sai \"ngữ pháp\": thiếu dấu :, thiếu ngoặc, thiếu dấu nháy."),
            ("NameError", "Dùng một cái tên Python chưa biết: gõ sai hoặc chưa tạo."),
            ("TypeError", "Trộn sai kiểu: chuỗi + số, gọi hàm thiếu tham số."),
            ("print(bien)", "Vũ khí số 1: xem giá trị thật đang có."),
        ],
        walkthrough=[
            ("count = 0", "Biến đếm."),
            ("for i in range(3):", "Lặp 3 lần."),
            ("    count += 1", "Thụt vào nên thuộc vòng lặp → tăng 3 lần."),
            ('    print("vòng", i, "count =", count)', "In từng bước để xem count thay đổi thế nào."),
            ("print(count)", "Ra 3. Nếu ra 1 thì có thể dòng count += 1 bị thụt lề sai."),
        ],
        tips=[
            "Đọc tên lỗi và số dòng trước tiên.",
            "Sửa MỘT lỗi, chạy lại, rồi mới sửa lỗi tiếp theo.",
            "Code chạy mà kết quả sai là lỗi logic: in giá trị ra từng bước để tìm chỗ lệch.",
        ],
    ),
}


def lesson_for_world(world_number: int) -> WorldLesson | None:
    return WORLD_LESSONS.get(world_number)
