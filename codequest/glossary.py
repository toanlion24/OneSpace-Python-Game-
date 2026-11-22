"""Từ điển thuật ngữ: giải thích từ khó bằng lời đời thường.

Mỗi màn tự tìm các thuật ngữ xuất hiện trong lý thuyết của màn đó và hiện
mục "Từ khó trong bài", để học sinh không bị kẹt vì một từ chưa hiểu.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .theory import Theory

MAX_TERMS_PER_LEVEL = 12
MIN_TERMS_BEFORE_BASIC = 3


@dataclass(frozen=True)
class GlossaryTerm:
    term: str
    patterns: tuple[str, ...]
    meaning: str
    basic: bool = False

    def first_position(self, text: str) -> int:
        """Vị trí đầu tiên thuật ngữ xuất hiện trong text, -1 nếu không có."""
        positions = []
        for pattern in self.patterns:
            match = re.search(rf"(?<!\w){pattern}(?!\w)", text, flags=re.IGNORECASE)
            if match:
                positions.append(match.start())
        if not positions:
            return -1
        return min(positions)


def _term(term: str, patterns: list[str], meaning: str, basic: bool = False) -> GlossaryTerm:
    return GlossaryTerm(term, tuple(patterns), meaning, basic)


GLOSSARY: list[GlossaryTerm] = [
    # ------------------------------------------------------------ từ rất cơ bản: chỉ hiện khi bài có ít từ khó
    _term("Chương trình", ["chương trình"],
          "Danh sách lệnh viết cho máy tính làm theo, chạy lần lượt từ dòng trên xuống dòng dưới.", basic=True),
    _term("Lệnh", ["lệnh"],
          "Một việc cụ thể bảo máy làm, thường viết trên một dòng, ví dụ hero.move_right(2).", basic=True),
    _term("Hướng", ["hướng", "huong"],
          "Một trong 4 chuỗi \"up\", \"down\", \"left\", \"right\" (lên, xuống, trái, phải), đặt trong dấu nháy.",
          basic=True),
    # ------------------------------------------------------------ nhập môn
    _term("Tham số", ["tham số", "đối số"],
          "Thông tin thêm bạn đưa cho lệnh, đặt trong ngoặc ( ). Như gọi món \"cho 2 cốc trà\" thì số 2 là tham số."),
    _term("Cú pháp / SyntaxError", ["cú pháp", "SyntaxError"],
          "Cú pháp là \"ngữ pháp\" của Python. Viết sai ngữ pháp (thiếu dấu :, thiếu ngoặc, thiếu dấu nháy) thì "
          "Python không hiểu và báo SyntaxError, chưa chạy dòng nào."),
    _term("Chuỗi (str)", ["chuỗi", "string", "str"],
          "Một đoạn chữ nằm trong dấu nháy, như \"Xin chào\". Python coi nó là CHỮ, kể cả \"123\" cũng là chữ "
          "chứ không phải số."),
    _term("Toạ độ (x, y)", ["toạ độ"],
          "Cặp số chỉ vị trí một ô: x đếm từ trái sang phải, y đếm từ trên xuống dưới, cả hai bắt đầu từ 0."),
    _term("print", ["print"],
          "Lệnh in thông tin ra Bảng tin. Dùng để XEM giá trị đang có - rất hữu ích khi tìm lỗi."),
    _term("Thụt lề", ["thụt lề", "thụt vào", "thụt đầu dòng", "IndentationError"],
          "Đẩy dòng code lùi vào 4 dấu cách. Python nhìn thụt lề để biết dòng nào nằm TRONG if, for, def. "
          "Thụt lề lộn xộn thì báo IndentationError."),
    _term("Khối lệnh", ["khối lệnh", "khối"],
          "Nhóm các dòng thụt vào cùng mức, nằm ngay dưới một dòng kết thúc bằng dấu :. Cả nhóm \"thuộc về\" dòng đó."),
    # ------------------------------------------------------------ biến và kiểu
    _term("Biến", ["biến"],
          "Một chiếc hộp có dán nhãn tên để cất giá trị. Gọi tên hộp là lấy được thứ bên trong."),
    _term("Gán", ["gán", "phép gán"],
          "Cất giá trị vào biến bằng dấu =. Đọc `a = 5` là \"cất 5 vào hộp a\", không phải \"a bằng 5\"."),
    _term("Kiểu dữ liệu", ["kiểu dữ liệu"],
          "Loại của giá trị: số nguyên (int), số thực (float), chữ (str), đúng/sai (bool)... Mỗi loại làm được "
          "những việc khác nhau."),
    _term("Số nguyên (int)", ["int", "số nguyên"],
          "Số không có phần lẻ: 3, 0, -7. Dùng để đếm số bước, số viên ngọc..."),
    _term("Số thực (float)", ["float", "số thực"],
          "Số có phần thập phân, viết bằng dấu CHẤM: 2.5, 3.0 (Python không dùng dấu phẩy cho phần lẻ)."),
    _term("bool / True / False", ["bool", "True", "False"],
          "Kiểu chỉ có hai giá trị: True (đúng) và False (sai) - giống câu trả lời Có / Không."),
    _term("Ép kiểu", ["ép kiểu", "type casting"],
          "Đổi giá trị sang kiểu khác. Ví dụ int(\"42\") biến chữ \"42\" thành số 42 để tính toán."),
    _term("f-string", ["f-string"],
          "Chuỗi có chữ f phía trước, cho phép chèn biến vào câu: f\"Có {so} viên\" → \"Có 3 viên\"."),
    _term("Chia lấy dư (%)", ["chia lấy dư"],
          "Phần còn thừa sau khi chia đều. 17 % 5 = 2 vì 17 chia 5 được 3, còn thừa 2."),
    _term("Biểu thức", ["biểu thức"],
          "Một đoạn tính ra được giá trị, như `a + b` hay `steps * 2`."),
    # ------------------------------------------------------------ điều kiện, vòng lặp
    _term("Điều kiện", ["điều kiện", "điều_kiện"],
          "Một câu hỏi có câu trả lời Đúng (True) hoặc Sai (False), ví dụ `hp > 1` (\"máu còn nhiều hơn 1 không?\")."),
    _term("if / elif / else", ["if", "elif", "else"],
          "if = \"nếu\", elif = \"nếu không thì nếu\", else = \"còn lại thì\". Python chọn ĐÚNG MỘT nhánh để chạy."),
    _term("and / or / not", ["and", "or", "not"],
          "Ghép điều kiện: and = \"và\" (cả hai đúng), or = \"hoặc\" (ít nhất một đúng), not = \"không\" (đảo ngược)."),
    _term("Vòng lặp", ["vòng lặp"],
          "Cách bảo máy làm đi làm lại một việc, thay vì chép cùng một lệnh nhiều lần."),
    _term("for", ["for"],
          "Vòng lặp đi qua LẦN LƯỢT từng phần tử của một dãy (range, list, chuỗi...). Mỗi vòng xử lý một phần tử."),
    _term("while", ["while"],
          "Vòng lặp chạy CHỪNG NÀO điều kiện còn đúng, như \"còn đói thì còn ăn\"."),
    _term("range", ["range"],
          "Tạo dãy số để đếm: range(4) là 0, 1, 2, 3 (bắt đầu từ 0, dừng TRƯỚC 4)."),
    _term("Lặp vô hạn", ["vô hạn"],
          "Vòng lặp không bao giờ dừng vì điều kiện luôn đúng. Game sẽ tự dừng chương trình chạy quá lâu."),
    _term("break", ["break"], "Lệnh thoát khỏi vòng lặp NGAY LẬP TỨC, dù vòng lặp chưa chạy hết."),
    _term("pass", ["pass"], "Lệnh \"không làm gì\". Dùng để giữ chỗ khi khối lệnh chưa viết."),
    _term("Duyệt", ["duyệt"],
          "Đi qua lần lượt từng phần tử, mỗi lần xử lý một phần tử - như điểm danh từng bạn trong lớp."),
    # ------------------------------------------------------------ hàm
    _term("Hàm", ["hàm"],
          "Một nhóm lệnh được đặt tên để dùng lại - như một \"chiêu\" đã luyện sẵn, chỉ cần gọi tên là làm cả chuỗi "
          "động tác."),
    _term("def", ["def"], "Từ khoá để TẠO (định nghĩa) hàm mới. Tạo xong chưa chạy, phải gọi tên hàm kèm () mới chạy."),
    _term("Trả về (return)", ["return", "trả về"],
          "Hàm gửi kết quả về cho nơi đã gọi nó. Như máy bán nước: bỏ tiền vào (tham số), máy trả lon nước ra "
          "(giá trị trả về)."),
    _term("None", ["None"], "Giá trị đặc biệt nghĩa là \"không có gì\". Hàm không có return sẽ trả về None."),
    _term("Hàm dựng sẵn", ["dựng sẵn", "builtin"],
          "Hàm Python làm sẵn cho bạn, gọi được ngay: len, sum, max, min, sorted, abs, round..."),
    _term("len", ["len"], "Đếm số phần tử của list, set, dict hoặc số ký tự của chuỗi."),
    _term("Phương thức (method)", ["phương thức", "method"],
          "Hàm \"gắn\" vào một giá trị, gọi bằng dấu chấm: `\"abc\".upper()`, `bag.append(3)`."),
    # ------------------------------------------------------------ chuỗi, list, dict, set
    _term("Chỉ số / vị trí (index)", ["chỉ số", "index"],
          "Số thứ tự của phần tử, ĐẾM TỪ 0: phần tử đầu tiên có chỉ số 0, phần tử thứ hai có chỉ số 1..."),
    _term("Cắt (slicing)", ["slicing", "cắt chuỗi", "cắt lát"],
          "Lấy một đoạn liền nhau: s[1:4] lấy vị trí 1, 2, 3 (dừng TRƯỚC 4)."),
    _term("List (danh sách)", ["list"],
          "Dãy nhiều giá trị có thứ tự, trong ngoặc vuông: [3, 5, 8]. Thêm, bớt, sửa được - như chiếc ba lô nhiều ngăn."),
    _term("Phần tử", ["phần tử"], "Một món bên trong list, tuple, set... [3, 5, 8] có 3 phần tử."),
    _term("append", ["append"], "Thêm một phần tử vào CUỐI list: bag.append(9)."),
    _term("Tuple", ["tuple"],
          "Giống list nhưng KHÔNG sửa được, viết bằng ngoặc tròn: (2, 5). Hay dùng cho toạ độ."),
    _term("Mở gói (unpacking)", ["mở gói"],
          "Tách các phần của tuple / list ra nhiều biến cùng lúc: `x, y = (2, 5)` cho x = 2, y = 5."),
    _term("Dict (từ điển)", ["dict", "từ điển"],
          "Bảng tra cứu theo cặp khoá → giá trị, như danh bạ: tra TÊN ra SỐ điện thoại. Viết {\"An\": 10}."),
    _term("Khoá (key)", [r"(?<!cửa )(?<!chìa )khoá(?! cửa)", "key(?==)"],
          "Trong dict, khoá là \"tên để tra\" (như tên trong danh bạ). Trong sorted/max, key= là hàm chọn tiêu chí "
          "để so sánh."),
    _term("Set (tập hợp)", ["set", "tập hợp"],
          "Túi chứa các giá trị KHÔNG TRÙNG, không có thứ tự: {1, 2, 3}. Bỏ thêm số đã có thì túi không đổi."),
    _term("Giao / hợp / hiệu", ["giao", "hiệu tập hợp", "hiệu đối xứng"],
          "Giao (&): có ở cả hai. Hợp (|): có ở ít nhất một. Hiệu (-): có ở bên này mà không có ở bên kia."),
    _term("List comprehension", ["comprehension"],
          "Cách viết gọn MỘT dòng để tạo list mới từ list cũ: [x * 2 for x in nums]."),
    _term("Lồng nhau", ["lồng nhau"],
          "Một thứ nằm bên trong thứ cùng loại: list trong list (như bảng có hàng và cột), vòng lặp trong vòng lặp."),
    _term("enumerate", ["enumerate"],
          "Vừa duyệt vừa đánh số thứ tự: mỗi vòng cho cặp (vị trí, phần tử)."),
    # ------------------------------------------------------------ thư viện
    _term("Thư viện / import", ["thư viện", "import", "module"],
          "Thư viện là hộp đồ nghề người khác viết sẵn. `import` là mở hộp đó ra để dùng."),
    _term("Luỹ thừa (**)", ["luỹ thừa"], "Nhân một số với chính nó nhiều lần: 3 ** 2 = 3 × 3 = 9."),
    _term("Giai thừa", ["giai thừa"], "Tích các số từ 1 tới n: 4! = 1 × 2 × 3 × 4 = 24."),
    _term("Hoán vị", ["hoán vị", "permutations"],
          "Các cách SẮP XẾP thứ tự. Đổi chỗ là tính khác: (A, B) khác (B, A)."),
    _term("Tổ hợp", ["tổ hợp", "combinations"],
          "Các cách CHỌN ra vài phần tử, không quan tâm thứ tự: chọn (A, B) giống chọn (B, A)."),
    _term("Vét cạn", ["vét cạn"], "Thử HẾT mọi khả năng để tìm đáp án - hợp khi dữ liệu nhỏ."),
    _term("Kết quả \"lười\" / iterator", ["lười", "iterator", "iterable", "generator", "yield"],
          "Thứ sinh ra từng phần tử khi được hỏi tới, chứ không làm sẵn cả list. Muốn xem hết thì bọc list(...)."),
    _term("Counter", ["Counter"], "Công cụ đếm: đọc một dãy và ghi số lần xuất hiện của từng giá trị."),
    _term("deque", ["deque"],
          "Hàng đợi hai đầu, như hàng người mua vé: thêm / lấy ở đầu hay cuối hàng đều nhanh."),
    _term("defaultdict", ["defaultdict"], "Dict tự tạo giá trị mặc định (0, list rỗng...) khi gặp khoá mới."),
    _term("datetime / timedelta", ["datetime", "timedelta"],
          "datetime xử lý ngày giờ như một cuốn lịch thông minh; timedelta là một KHOẢNG thời gian (ví dụ 10 ngày)."),
    # ------------------------------------------------------------ lỗi
    _term("Ngoại lệ (exception)", ["ngoại lệ", "exception", "ném"],
          "Lỗi xảy ra khi chương trình ĐANG chạy. Không ai xử lý thì chương trình dừng lại."),
    _term("try / except", ["try", "except", "finally"],
          "Lưới an toàn: thử chạy khối try, nếu lỗi thì khối except xử lý thay vì để chương trình dừng."),
    _term("raise", ["raise"], "Tự báo lỗi khi dữ liệu không hợp lệ: raise ValueError(\"...\")."),
    _term("NameError", ["NameError"],
          "Python gặp một cái tên nó chưa từng biết: gõ sai tên, hoặc dùng biến / hàm trước khi tạo."),
    _term("TypeError", ["TypeError"],
          "Dùng sai kiểu: cộng chữ với số, gọi hàm thiếu tham số, dùng len cho một con số..."),
    _term("ValueError", ["ValueError"], "Đúng kiểu nhưng giá trị không dùng được, ví dụ int(\"abc\")."),
    _term("IndexError", ["IndexError"], "Lấy vị trí không tồn tại, ví dụ phần tử số 5 của list chỉ có 3 phần tử."),
    _term("KeyError", ["KeyError"], "Tra một khoá không có trong dict (hay gặp khi gõ sai chính tả khoá)."),
    _term("ZeroDivisionError", ["ZeroDivisionError"], "Lỗi chia cho số 0 - phép chia này không có kết quả nên Python dừng lại."),
    _term("AttributeError", ["AttributeError"],
          "Gọi một thuộc tính / phương thức mà giá trị đó không có, ví dụ list không có popleft."),
    _term("Gỡ lỗi (debugging)", ["gỡ lỗi", "debugging", "bug"],
          "Tìm và sửa lỗi trong code: đọc thông báo lỗi, in giá trị ra xem, sửa từng chỗ rồi chạy lại."),
    _term("Lỗi logic", ["lỗi logic"],
          "Code chạy được, không báo lỗi, nhưng làm SAI việc. Python không chỉ ra được - bạn phải tự tìm."),
    # ------------------------------------------------------------ class
    _term("Class", ["class"],
          "Cái KHUÔN để tạo đồ vật. Một khuôn đúc ra được nhiều đồ vật cùng kiểu (như khuôn bánh)."),
    _term("Đối tượng (object)", ["object", "đối tượng", "đồ vật"],
          "Một đồ vật cụ thể được tạo từ class, có dữ liệu riêng của nó."),
    _term("Thuộc tính", ["thuộc tính"],
          "Thông tin gắn với một đồ vật, đọc bằng dấu chấm: p.power. Trong XML, thuộc tính là thông tin ghi trong "
          "thẻ, như x=\"3\"."),
    _term("self", ["self"], "\"Chính tôi\" - chính đồ vật đang chạy phương thức đó."),
    _term("__init__", ["__init__"], "Phương thức tự chạy khi tạo đồ vật mới, dùng để cất dữ liệu ban đầu."),
    _term("Magic method (dunder)", ["magic method", "dunder"],
          "Phương thức tên dạng __ten__ mà Python tự gọi: __str__ khi print, __len__ khi len, __add__ khi dùng +."),
    # ------------------------------------------------------------ nâng cao
    _term("lambda", ["lambda"], "Hàm ngắn không tên, viết tại chỗ: lambda x: x * 2 (nhận x, trả về x * 2)."),
    _term("map / filter", ["map", "filter"],
          "map áp một hàm lên TỪNG phần tử; filter chỉ GIỮ các phần tử mà hàm trả về True."),
    _term("zip", ["zip"], "Ghép cặp theo vị trí: phần tử thứ nhất với thứ nhất, thứ hai với thứ hai..."),
    _term("any / all", ["any", "all"], "any: có ÍT NHẤT MỘT cái đúng không? all: TẤT CẢ đều đúng không?"),
    _term("Regex (biểu thức chính quy)", ["regex", "biểu thức chính quy"],
          "Một \"khuôn\" mô tả hình dạng chữ cần tìm (ví dụ: một dãy chữ số), dùng để tìm trong văn bản."),
    _term("XML / thẻ", ["xml"],
          "Cách ghi dữ liệu bằng các THẺ lồng nhau như <gem x=\"3\"/>, giống HTML của trang web."),
    _term("Closure", ["closure"],
          "Hàm con NHỚ các biến của hàm cha đã tạo ra nó, kể cả khi hàm cha đã chạy xong."),
    _term("Decorator", ["decorator"],
          "Hàm \"bọc\" một hàm khác để thêm việc trước / sau mà không sửa hàm gốc. Viết @ten ngay trên def."),
    _term("NumPy / mảng", ["numpy", "mảng"],
          "Thư viện tính toán với BẢNG SỐ (mảng) rất nhanh - ra lệnh cho cả bảng cùng lúc thay vì từng ô."),
    _term("Ma trận", ["ma trận"], "Bảng số có hàng và cột, như bảng điểm của cả lớp."),
    _term("axis", ["axis"], "Hướng tính trong NumPy: axis=0 đi dọc theo cột, axis=1 đi ngang theo hàng."),
]


def theory_text(theory: Theory) -> str:
    """Toàn bộ chữ của một bài lý thuyết, dùng để tìm thuật ngữ."""
    parts = [*theory.concept, *theory.mistakes]
    for code, note in [*theory.starter_notes, *theory.example]:
        parts.append(code)
        parts.append(note)
    return "\n".join(parts)


def find_terms(text: str, limit: int = MAX_TERMS_PER_LEVEL) -> list[GlossaryTerm]:
    """Các thuật ngữ có trong text, theo thứ tự xuất hiện lần đầu.

    Từ rất cơ bản (chương trình, lệnh...) chỉ được thêm khi bài có ít từ khó,
    để bài nâng cao không bị lặp lại những từ học sinh đã biết.
    """
    found = []
    for glossary_term in GLOSSARY:
        position = glossary_term.first_position(text)
        if position >= 0:
            found.append((position, glossary_term))
    found.sort(key=lambda pair: pair[0])
    advanced = [glossary_term for _position, glossary_term in found if not glossary_term.basic]
    if len(advanced) >= MIN_TERMS_BEFORE_BASIC:
        return advanced[:limit]
    return [glossary_term for _position, glossary_term in found[:limit]]
