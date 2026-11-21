"""Level data, organised into the 5 stages of the HackerRank Python path.

Map legend:
    #  tường        .  sàn          @  hero        E  cổng đích (cúp)
    G  ngọc         1-6 ngọc màu    ^  gai         D  cửa mật mã
    J  cửa kẹt      r b c x  quái (robot, barrel, cannon, spikebox)
    B  boss (duck)

Gợi ý (hints) chỉ gợi hướng suy nghĩ, không đưa code đáp án.
Nội dung dành cho học sinh cấp 2 - cấp 3.
"""

from __future__ import annotations

from dataclasses import dataclass

from .engine import Level


@dataclass
class Stage:
    number: int
    title: str
    subdomains: str
    content: str
    focus: str
    milestone: str


@dataclass
class World:
    number: int
    stage: int
    title: str
    concept: str
    hackerrank: str
    background: int
    levels: list[Level]


STAGES: list[Stage] = [
    Stage(
        1,
        "Cú pháp & kiểu dữ liệu nền tảng",
        "Introduction · Basic Data Types · Strings",
        "Nhập/xuất, if-else, vòng lặp, hàm cơ bản, xử lý chuỗi (cắt, định dạng), list, tuple, dictionary.",
        "List Comprehension và list lồng nhau - viết code ngắn gọn thay cho nhiều vòng lặp lồng nhau.",
        "Nền móng cho mọi giai đoạn sau.",
    ),
    Stage(
        2,
        "Sức mạnh thư viện chuẩn",
        "Sets · Math · Itertools · Collections · Date and Time",
        "Phép toán tập hợp (giao, hợp), hoán vị - tổ hợp với itertools, Counter / deque trong collections, ngày giờ.",
        "Dùng đúng set hoặc Counter để tra cứu nhanh thay vì duyệt list nhiều lần.",
        "Giải bài thuật toán nhanh hơn hẳn.",
    ),
    Stage(
        3,
        "Lập trình hướng đối tượng & ngoại lệ",
        "Errors and Exceptions · Classes",
        "Bắt lỗi an toàn với try-except, thiết kế class, thuộc tính, magic methods (__str__, __add__, __iter__).",
        "Tự tạo kiểu dữ liệu của riêng mình và giữ chương trình không bị dừng khi gặp lỗi.",
        "Xong 3 giai đoạn đầu: đủ kiến thức thi chứng chỉ HackerRank Python (Basic).",
    ),
    Stage(
        4,
        "Lập trình hàm & kỹ thuật nâng cao",
        "Built-Ins · Python Functionals · Regex and Parsing · XML · Closures and Decorators",
        "map, filter, zip, lambda, biểu thức chính quy (regex), đọc XML, closure và decorator.",
        "Viết hàm nhận hàm, trả về hàm - mở rộng logic mà không sửa code cũ.",
        "Trọng tâm của chứng chỉ HackerRank Python (Intermediate).",
    ),
    Stage(
        5,
        "NumPy & gỡ lỗi thực chiến",
        "NumPy · Debugging",
        "Mảng nhiều chiều với NumPy, phép tính ma trận cơ bản, đọc hiểu và sửa lỗi trong code có sẵn.",
        "Rèn kỹ năng đọc thông báo lỗi và tìm lỗi logic.",
        "Hướng tới huy hiệu 5 sao Python, rồi sang nhánh Problem Solving.",
    ),
]

# Bản đồ dùng lại nhiều lần.
MAP_DOOR = [
    "#########",
    "#@.GD.GE#",
    "#########",
]
MAP_DOOR_DOWN = [
    "#######",
    "#@..###",
    "###.###",
    "###D###",
    "###G###",
    "###E###",
    "#######",
]
MAP_STAIRS = [
    "#######",
    "#@G####",
    "##.G###",
    "###.G##",
    "####.G#",
    "#####E#",
    "#######",
]
MAP_WEAPON_ROOM = [
    "###########",
    "#@..r..b..#",
    "#.........#",
    "#....c...E#",
    "###########",
]

WORLDS: list[World] = [
    # ================================================================ GIAI ĐOẠN 1
    World(1, 1, "Khởi hành", "Cú pháp cơ bản", "Introduction", 1, [
        Level(
            id="1-1",
            title="Bước chân đầu tiên",
            story="Chào mừng tới CodeQuest! Hero chỉ làm theo lệnh Python bạn viết.",
            goal="Đi tới cúp vàng và nhặt viên ngọc trên đường.",
            rows=[
                "#########",
                "#@..G..E#",
                "#########",
            ],
            starter=(
                "# Dòng bắt đầu bằng # là ghi chú, Python bỏ qua.\n"
                "# Số trong ngoặc là số bước đi.\n"
                "hero.move_right(2)\n"
            ),
            hints=[
                "Số trong ngoặc là số bước hero đi.",
                "Đếm số ô từ hero tới cúp vàng, rồi sửa con số trong ngoặc.",
            ],
        ),
        Level(
            id="1-2",
            title="Rẽ góc",
            story="Mỗi lệnh nằm trên một dòng. Python chạy từ trên xuống dưới.",
            goal="Đi qua khúc quanh, nhặt ngọc, tới cúp.",
            rows=[
                "#######",
                "#@..###",
                "###G###",
                "###.###",
                "###..E#",
                "#######",
            ],
            starter="hero.move_right(2)\n# Thêm lệnh move_down và move_right\n",
            hints=[
                "Có 4 lệnh: move_up, move_down, move_left, move_right.",
                "Chia đường đi thành 3 đoạn thẳng, mỗi đoạn một lệnh.",
            ],
        ),
        Level(
            id="1-3",
            title="Lời chào",
            story="hero.say(...) cho hero nói. Chữ phải nằm trong dấu nháy: \"Xin chào\".",
            goal="Nói \"Xin chào\" rồi đi tới cúp.",
            rows=[
                "##########",
                "#@......E#",
                "##########",
            ],
            starter='hero.say("...")\nhero.move_right(1)\n',
            hints=[
                "Chuỗi phải nằm trong dấu nháy kép \" \". Gõ chaof sẽ ra chào.",
                "Câu cần nói phải đúng chữ \"Xin chào\". Sau đó đếm lại số bước tới cúp.",
            ],
            requires=["call:say"],
            say_contains="Xin chào",
        ),
    ]),
    World(2, 1, "Kho đồ", "Biến và kiểu dữ liệu", "Basic Data Types", 2, [
        Level(
            id="2-1",
            title="Hộp chứa số bước",
            story="Biến là chiếc hộp có tên, cất một giá trị: steps = 3",
            goal="Gán đúng số bước vào biến steps rồi dùng biến đó để đi.",
            rows=[
                "##########",
                "#@..G...E#",
                "##########",
            ],
            starter="steps = 1  # đổi số này\nhero.move_right(steps)\n",
            hints=[
                "Đếm số ô từ hero tới cúp.",
                "Chỉ cần sửa giá trị gán cho steps, dòng thứ hai giữ nguyên.",
            ],
            requires=["assign"],
        ),
        Level(
            id="2-2",
            title="Đếm vàng",
            story=(
                "Kiểu dữ liệu: số nguyên (int), số thực (float), chuỗi (str), đúng/sai (bool). "
                "Mỗi viên ngọc giá 10 vàng."
            ),
            goal="Nhặt 3 ngọc, tính total từ gems và value, nói tổng số vàng rồi tới cúp.",
            rows=[
                "###########",
                "#@GGG....E#",
                "###########",
            ],
            starter=(
                "gems = 3\n"
                "value = 10\n"
                "total = 0  # tính lại total\n"
                "hero.move_right(8)\n"
            ),
            hints=[
                "Phép nhân dùng dấu *.",
                "Nối chuỗi với số thì phải đổi số sang chuỗi bằng str(...).",
            ],
            requires=["assign"],
            say_contains="30",
        ),
    ]),
    World(3, 1, "Ngã rẽ", "Câu lệnh điều kiện", "Introduction", 3, [
        Level(
            id="3-1",
            title="Quái chặn đường",
            story="hero.look(\"right\") cho biết ô bên phải là gì: \"enemy\", \"wall\", \"spike\", \"gem\", \"floor\"...",
            goal="Nếu bên phải có quái thì tấn công, sau đó đi tới cúp.",
            rows=[
                "##########",
                "#@..r...E#",
                "##########",
            ],
            starter=(
                "hero.move_right(2)\n"
                'if hero.look("right") == "enemy":\n'
                "    # thụt vào 4 khoảng trắng\n"
                "    pass\n"
            ),
            hints=[
                "Lệnh bên trong if phải thụt vào 4 khoảng trắng.",
                "Thay pass bằng lệnh tấn công về phía quái; lệnh đi tiếp đặt NGOÀI if (không thụt lề).",
            ],
            requires=["if"],
        ),
        Level(
            id="3-2",
            title="Chọn lối",
            story="if / else: nếu điều kiện đúng làm việc này, ngược lại làm việc kia.",
            goal="Ở ngã ba, tránh lối có gai và tới cúp.",
            rows=[
                "#######",
                "###^###",
                "#@..###",
                "###.###",
                "###.E##",
                "#######",
            ],
            starter=(
                "hero.move_right(2)\n"
                'if hero.look("up") == "spike":\n'
                "    pass  # đi lối khác\n"
                "else:\n"
                "    hero.move_up()\n"
            ),
            hints=[
                "Lối nào không có gai thì đi lối đó.",
                "Sau khối if/else, hero vẫn cần đi thêm để tới cúp.",
            ],
            requires=["if"],
        ),
    ]),
    World(4, 1, "Vòng lặp", "for và while", "Introduction", 4, [
        Level(
            id="4-1",
            title="Hàng ngọc",
            story="for i in range(n): lặp lại khối lệnh n lần.",
            goal="Dùng vòng lặp for để nhặt 8 viên ngọc và tới cúp.",
            rows=[
                "############",
                "#@GGGGGGGGE#",
                "############",
            ],
            starter="for i in range(1):\n    hero.move_right()\n",
            hints=[
                "range(n) lặp n lần.",
                "Đếm tổng số bước từ hero tới cúp - đó chính là số lần lặp.",
            ],
            requires=["for"],
        ),
        Level(
            id="4-2",
            title="Cầu thang",
            story="Khối lệnh trong vòng lặp có thể có nhiều dòng.",
            goal="Đi xuống cầu thang, nhặt hết ngọc, tới cúp.",
            rows=MAP_STAIRS,
            starter="for i in range(4):\n    hero.move_right()\n",
            hints=[
                "Mỗi bậc thang gồm 2 bước.",
                "Bước thứ hai phải thụt lề cùng mức với bước thứ nhất để nằm trong vòng lặp.",
            ],
            requires=["for"],
        ),
        Level(
            id="4-3",
            title="Hành lang dài",
            story="while điều_kiện: lặp lại chừng nào điều kiện còn đúng.",
            goal="Đi tới khi bên phải là cổng, rồi bước vào cổng.",
            rows=[
                "###############",
                "#@.G.G.G.G...E#",
                "###############",
            ],
            starter='while hero.look("right") != "exit":\n    pass\n',
            hints=[
                "Thay pass bằng lệnh cho hero tiến lên.",
                "Vòng lặp dừng khi cổng ở ngay bên phải - còn thiếu một bước nữa.",
            ],
            requires=["while"],
        ),
    ]),
    World(5, 1, "Biến hình", "Ép kiểu dữ liệu", "Basic Data Types", 5, [
        Level(
            id="5-1",
            title="Mật mã chuỗi",
            story=(
                "Biến secret chứa mật mã nhưng ở dạng chuỗi: secret = \"42\". "
                "Cửa chỉ nhận số nguyên (int)."
            ),
            goal="Đứng cạnh cửa, nhập mật mã bằng hero.enter_code(...), rồi tới cúp.",
            rows=MAP_DOOR,
            starter=(
                "# secret đã có sẵn: secret = \"42\"\n"
                "hero.move_right(2)\n"
                "hero.enter_code(secret)\n"
            ),
            hints=[
                "int(...) đổi chuỗi thành số nguyên.",
                "Mở cửa xong, đếm số bước còn lại tới cúp.",
            ],
            requires=["call:int"],
            extra_globals={"secret": "42"},
            door_code=42,
        ),
        Level(
            id="5-2",
            title="Cộng hai mảnh",
            story="Mật mã bị chia làm 2 mảnh chuỗi: a = \"12\", b = \"30\". Mật mã là tổng của chúng.",
            goal="Đổi a, b sang số, cộng lại, mở cửa và tới cúp.",
            rows=MAP_DOOR_DOWN,
            starter=(
                "# a = \"12\", b = \"30\"\n"
                "print(a + b)  # thử xem: chuỗi cộng chuỗi ra gì?\n"
                "hero.move_right(2)\n"
                "hero.move_down(1)\n"
            ),
            hints=[
                "\"12\" + \"30\" là nối chuỗi, không phải cộng số.",
                "Đổi từng biến sang số trước, rồi mới cộng.",
            ],
            requires=["call:int"],
            extra_globals={"a": "12", "b": "30"},
            door_code=42,
        ),
    ]),
    World(6, 1, "Phép thuật", "Hàm và hàm có sẵn", "Introduction", 1, [
        Level(
            id="6-1",
            title="Chiêu nhảy gai",
            story="def ten_ham(): tạo chiêu thức riêng để gọi lại nhiều lần.",
            goal="Viết hàm hop() vòng qua một cái gai và dùng nó để qua cả 3 gai.",
            rows=[
                "#############",
                "#...G..G..G.#",
                "#@..^..^..^E#",
                "#############",
            ],
            starter=(
                "def hop():\n"
                "    hero.move_up()\n"
                "    # thêm 2 lệnh nữa\n"
                "\n"
                "hero.move_right(2)\n"
                "hop()\n"
            ),
            hints=[
                "Chiêu hop gồm 3 bước: lên, sang phải, xuống.",
                "Giữa các lần gọi hop(), hero cần đi thêm tới sát gai tiếp theo.",
            ],
            requires=["def", "call:hop"],
        ),
        Level(
            id="6-2",
            title="Kiểm kê",
            story="Hàm có sẵn của Python: len(), sum(), min(), max()... hero.find_gems() trả về danh sách ngọc.",
            goal="Nói số ngọc trên bản đồ bằng len(), rồi nhặt hết và tới cúp.",
            rows=[
                "##############",
                "#@G.G.G.G.G.E#",
                "##############",
            ],
            starter="gems = hero.find_gems()\nhero.say(gems)\n",
            hints=[
                "len(...) cho biết danh sách có bao nhiêu phần tử.",
                "Nói số lượng, rồi dùng vòng lặp để đi tới cúp.",
            ],
            requires=["call:len"],
            say_contains="5",
        ),
        Level(
            id="6-3",
            title="Hàm trả kết quả",
            story="return trả giá trị về cho nơi gọi hàm. Mật mã = gấp đôi base (base = 21).",
            goal="Viết hàm double(n) trả về gấp đôi n, dùng nó để mở cửa.",
            rows=[
                "###########",
                "#@..GD..GE#",
                "###########",
            ],
            starter="def double(n):\n    pass\n\nhero.move_right(3)\n",
            hints=[
                "Hàm cần trả kết quả bằng return.",
                "Truyền biến base vào hàm, rồi đưa kết quả vào hero.enter_code(...).",
            ],
            requires=["def", "return"],
            extra_globals={"base": 21},
            door_code=42,
        ),
    ]),
    World(7, 1, "Cuộn giấy", "Xử lý chuỗi", "Strings", 2, [
        Level(
            id="7-1",
            title="Cắt chữ",
            story=(
                "Cuộn giấy ghi scroll = \"abc42xyz\". Mật mã là 2 chữ số nằm ở vị trí 3 và 4 "
                "(vị trí đếm từ 0). Cắt chuỗi: scroll[đầu:cuối]."
            ),
            goal="Cắt lấy mật mã từ scroll, đổi sang số, mở cửa và tới cúp.",
            rows=MAP_DOOR,
            starter=(
                "# scroll = \"abc42xyz\"\n"
                "print(scroll[0])  # chữ đầu tiên\n"
                "hero.move_right(2)\n"
            ),
            hints=[
                "Vị trí cuối trong [đầu:cuối] KHÔNG được lấy - lấy tới trước nó.",
                "Cắt ra được chuỗi \"42\" rồi thì vẫn phải đổi sang int.",
            ],
            requires=["slice", "call:int"],
            extra_globals={"scroll": "abc42xyz"},
            door_code=42,
        ),
        Level(
            id="7-2",
            title="Bảng tên",
            story=(
                "Bạn đồng hành tên name = \"mèo\". f-string ghép biến vào câu: f\"Xin chào {name}\". "
                "Chuỗi có sẵn các hàm như .upper() (viết hoa), .lower(), .title()."
            ),
            goal="Nói đúng câu \"MÈO có 3 ngọc\" (tên viết HOA, số ngọc đếm bằng code) rồi tới cúp.",
            rows=[
                "###########",
                "#@.G.G.G.E#",
                "###########",
            ],
            starter=(
                "# name = \"mèo\"\n"
                "count = len(hero.find_gems())\n"
                'hero.say("name có count ngọc")  # chưa đúng!\n'
                "hero.move_right(8)\n"
            ),
            hints=[
                "Thêm chữ f trước dấu nháy và đặt tên biến trong { }.",
                "Trong { } có thể gọi hàm của chuỗi, ví dụ viết hoa tên.",
            ],
            requires=["fstring", "call:upper"],
            extra_globals={"name": "mèo"},
            say_contains="MÈO có 3 ngọc",
        ),
    ]),
    World(8, 1, "Ba lô", "List và tuple", "Basic Data Types", 2, [
        Level(
            id="8-1",
            title="Bản đồ kho báu",
            story=(
                "hero.find_gems() trả về list, mỗi phần tử là dict {\"x\":..., \"y\":...}. "
                "hero.move_to(x, y) tự tìm đường. hero.exit_position là tuple (x, y)."
            ),
            goal="Duyệt danh sách ngọc, nhặt hết rồi tới cổng.",
            rows=[
                "###########",
                "#@.G#...G.#",
                "#.##.#.##.#",
                "#..G.G...E#",
                "###########",
            ],
            starter=(
                "gems = hero.find_gems()\n"
                "print(gems)\n"
                "exit_x, exit_y = hero.exit_position  # mở gói tuple\n"
            ),
            hints=[
                "Mỗi viên ngọc là dict có khoá \"x\" và \"y\".",
                "Duyệt list ngọc bằng for, mỗi vòng đi tới toạ độ của viên đó; cuối cùng đi tới cổng.",
            ],
            requires=["for", "call:move_to"],
        ),
        Level(
            id="8-2",
            title="Dọn phòng",
            story="hero.find_enemies() trả về list quái. hero.attack_target(x, y) tự đi tới và đánh.",
            goal="Hạ hết quái trong phòng rồi tới cổng.",
            rows=[
                "############",
                "#@..r......#",
                "#.r.....r..#",
                "#.........E#",
                "############",
            ],
            starter="enemies = hero.find_enemies()\nprint(len(enemies), \"quái\")\n",
            hints=[
                "Duyệt list quái bằng for.",
                "Lấy toạ độ của từng quái trong dict rồi dùng attack_target.",
            ],
            requires=["for", "call:attack_target"],
            kill_all=True,
        ),
    ]),
    World(9, 1, "Sổ tay", "Dictionary và set", "Basic Data Types", 3, [
        Level(
            id="9-1",
            title="Điểm yếu",
            story=(
                "Mỗi loại quái chỉ sợ một vũ khí: robot → \"hammer\", barrel → \"axe\", cannon → \"bow\". "
                "Dùng dict để tra cứu: weakness[\"robot\"]."
            ),
            goal="Tạo dict weakness, hạ hết quái bằng đúng vũ khí, tới cổng.",
            rows=MAP_WEAPON_ROOM,
            starter=(
                'weakness = {"robot": "hammer"}\n'
                "for enemy in hero.find_enemies():\n"
                '    print(enemy["type"])\n'
            ),
            hints=[
                "Dict cần đủ 3 cặp loại quái → vũ khí.",
                "Tra vũ khí bằng loại quái làm khoá, rồi truyền vũ khí vào attack_target.",
            ],
            requires=["dict", "for"],
            weapons=True,
            kill_all=True,
        ),
        Level(
            id="9-2",
            title="Bộ sưu tập màu",
            story="set chỉ giữ các giá trị KHÔNG trùng nhau. Mỗi viên ngọc có gem[\"color\"].",
            goal="Đếm số MÀU ngọc khác nhau bằng set, nói ra, rồi nhặt hết và tới cúp.",
            rows=[
                "###########",
                "#@121321.E#",
                "###########",
            ],
            starter="colors = set()\nfor gem in hero.find_gems():\n    pass\n",
            hints=[
                "set.add(...) thêm phần tử, giá trị trùng tự bị bỏ qua.",
                "len(set) cho số màu khác nhau. Nói ra rồi đi tới cúp.",
            ],
            requires=["set", "for"],
            say_contains="3",
        ),
    ]),
    World(10, 1, "Đội hình", "List comprehension & list lồng nhau", "Basic Data Types", 4, [
        Level(
            id="10-1",
            title="Lọc ngọc xanh",
            story=(
                "List comprehension tạo list mới chỉ trong 1 dòng: [x for x in danh_sach if điều_kiện]. "
                "Mật mã cửa = số ngọc màu 3. Ngọc nhặt rồi sẽ biến mất, nên hãy đếm TRƯỚC khi đi."
            ),
            goal="Dùng list comprehension lọc ngọc màu 3, nhập số lượng làm mật mã, tới cúp.",
            rows=[
                "###########",
                "#@1323.D.E#",
                "###########",
            ],
            starter=(
                "gems = hero.find_gems()\n"
                "blue = []  # chỉ lấy ngọc màu 3\n"
                "hero.move_right(5)\n"
            ),
            hints=[
                "Cấu trúc: [biến for biến in list if điều_kiện].",
                "Điều kiện so sánh khoá \"color\" của mỗi viên ngọc với số 3.",
            ],
            requires=["listcomp"],
            door_code=2,
        ),
        Level(
            id="10-2",
            title="Bản đồ ô vuông",
            story=(
                "hero.scan() trả về bản đồ dạng list lồng nhau: mỗi hàng là một list các ô "
                "(\"wall\", \"floor\", \"spike\"...). grid[y][x] là ô ở hàng y, cột x. "
                "Mật mã = tổng số gai trên bản đồ."
            ),
            goal="Đếm số gai trong list lồng nhau, nhập mật mã, tới cúp.",
            rows=[
                "#########",
                "#^.^.^..#",
                "#@...D.E#",
                "#^..^...#",
                "#########",
            ],
            starter=(
                "grid = hero.scan()\n"
                "print(grid[1])  # hàng số 1\n"
                "print(grid[2][1])  # ô ở hàng 2, cột 1\n"
                "hero.move_right(3)\n"
            ),
            hints=[
                "Mỗi hàng là một list - list có hàm .count(giá_trị).",
                "Đếm từng hàng rồi cộng tất cả lại (sum + comprehension).",
            ],
            requires=["listcomp", "call:scan"],
            door_code=5,
        ),
    ]),
    # ================================================================ GIAI ĐOẠN 2
    World(11, 2, "Tập hợp", "Giao, hợp tập hợp", "Sets", 5, [
        Level(
            id="11-1",
            title="Hai trinh sát",
            story=(
                "Hai trinh sát báo về loại quái họ thấy: scout_a và scout_b. "
                "set(a) & set(b) là loại CẢ HAI cùng thấy (giao). set(a) | set(b) là TẤT CẢ loại (hợp)."
            ),
            goal="Nói số loại quái khác nhau (hợp). Mật mã = số loại cả hai cùng thấy (giao).",
            rows=MAP_DOOR,
            starter=(
                "# scout_a, scout_b: 2 danh sách loại quái\n"
                "a = set(scout_a)\n"
                "print(a)\n"
                "hero.move_right(2)\n"
            ),
            hints=[
                "Đổi cả hai list sang set trước.",
                "Toán tử & cho phần giao, | cho phần hợp; len() để đếm.",
            ],
            requires=["op:& or call:intersection", "op:| or call:union"],
            extra_globals={
                "scout_a": ["robot", "barrel", "cannon", "robot"],
                "scout_b": ["cannon", "duck", "robot", "cannon"],
            },
            door_code=2,
            say_contains="4",
        ),
    ]),
    World(12, 2, "Toán học", "Thư viện math", "Math", 6, [
        Level(
            id="12-1",
            title="Chiếc thang",
            story=(
                "Thang dựa vào tường: chân thang cách tường a = 6 m, đỉnh thang cao b = 8 m. "
                "Theo định lý Pytago, thang dài √(a² + b²). Dùng math.sqrt."
            ),
            goal="import math, tính chiều dài thang, nhập làm mật mã (số nguyên), tới cúp.",
            rows=MAP_DOOR_DOWN,
            starter=(
                "import math\n"
                "print(math.pi)\n"
                "hero.move_right(2)\n"
                "hero.move_down(1)\n"
            ),
            hints=[
                "a ** 2 là a bình phương.",
                "math.sqrt trả về số thực (10.0) - đổi sang int trước khi nhập.",
            ],
            requires=["import:math"],
            extra_globals={"a": 6, "b": 8},
            door_code=10,
        ),
        Level(
            id="12-2",
            title="Chia túi quà",
            story=(
                "Có 84 cái kẹo và 36 cái bánh. Chia vào các túi giống hệt nhau, không thừa. "
                "Nhiều túi nhất là ước chung lớn nhất: math.gcd(84, 36)."
            ),
            goal="Tính số túi bằng math.gcd, mở cửa, tới cúp.",
            rows=MAP_DOOR,
            starter="import math\nhero.move_right(2)\n",
            hints=["Biến có sẵn: candies = 84, cakes = 36.", "gcd = greatest common divisor = ước chung lớn nhất."],
            requires=["call:gcd"],
            extra_globals={"candies": 84, "cakes": 36},
            door_code=12,
        ),
    ]),
    World(13, 2, "Hoán vị", "itertools", "Itertools", 1, [
        Level(
            id="13-1",
            title="Khoá ba rune",
            story=(
                "Khoá cửa có 3 rune: runes = [\"sun\", \"moon\", \"star\"], phải xếp đúng thứ tự. "
                "permutations(runes) sinh MỌI cách sắp xếp. hero.try_code(...) thử mà không mất máu, "
                "trả về True nếu cửa mở."
            ),
            goal="Thử lần lượt các hoán vị tới khi cửa mở, rồi tới cúp.",
            rows=MAP_DOOR,
            starter=(
                "from itertools import permutations\n"
                "print(list(permutations([1, 2])))\n"
                "hero.move_right(2)\n"
            ),
            hints=[
                "Duyệt for qua permutations(runes); mỗi phần tử là một tuple.",
                "Mở được rồi thì dừng vòng lặp bằng break.",
            ],
            requires=["call:permutations"],
            extra_globals={"runes": ["sun", "moon", "star"]},
            door_code=("star", "sun", "moon"),
        ),
        Level(
            id="13-2",
            title="Cặp ngọc may mắn",
            story=(
                "Trong values = [3, 8, 5, 12, 7] có đúng 1 cặp số cộng lại bằng 20. "
                "combinations(values, 2) sinh mọi cặp 2 số. Mật mã = TÍCH của cặp đó."
            ),
            goal="Tìm cặp có tổng 20, nhập tích của chúng, tới cúp.",
            rows=MAP_DOOR_DOWN,
            starter=(
                "from itertools import combinations\n"
                "for pair in combinations([1, 2, 3], 2):\n"
                "    print(pair)\n"
            ),
            hints=[
                "Mở gói mỗi cặp thành 2 biến ngay trong vòng for.",
                "Kiểm tra tổng bằng if, lưu tích lại để dùng sau vòng lặp.",
            ],
            requires=["call:combinations"],
            extra_globals={"values": [3, 8, 5, 12, 7]},
            door_code=96,
        ),
    ]),
    World(14, 2, "Kho quân", "collections", "Collections", 2, [
        Level(
            id="14-1",
            title="Điểm danh quân địch",
            story=(
                "Counter đếm số lần xuất hiện của từng giá trị. "
                "Counter([...]).most_common(1) cho giá trị xuất hiện nhiều nhất và số lần."
            ),
            goal="Nói loại quái đông nhất. Mật mã = số con của loại đó. Rồi tới cúp.",
            rows=[
                "############",
                "#r.b.r.c.r.#",
                "#@......D.E#",
                "############",
            ],
            starter=(
                "from collections import Counter\n"
                'print(Counter(["a", "b", "a"]))\n'
                "hero.move_right(6)\n"
            ),
            hints=[
                "Đưa vào Counter danh sách các loại quái (khoá \"type\").",
                "most_common(1) trả về list có 1 tuple (loại, số lượng).",
            ],
            requires=["call:Counter"],
            door_code=3,
            say_contains="robot",
        ),
        Level(
            id="14-2",
            title="Hàng lính gác",
            story=(
                "guards = [\"An\", \"Bình\", \"Chi\", \"Dũng\"] xếp hàng. Mỗi lượt, người đứng đầu "
                "ra đứng cuối hàng. Sau 3 lượt, tên người đứng đầu là mật mã. "
                "deque là hàng đợi: popleft() lấy người đầu, append() thêm vào cuối."
            ),
            goal="Dùng deque mô phỏng 3 lượt, nhập tên người đứng đầu, tới cúp.",
            rows=MAP_DOOR,
            starter=(
                "from collections import deque\n"
                "line = deque(guards)\n"
                "print(line)\n"
            ),
            hints=[
                "Mỗi lượt: lấy người đầu ra rồi đưa vào cuối.",
                "Mật mã là chuỗi (tên), không phải số.",
            ],
            requires=["call:deque"],
            extra_globals={"guards": ["An", "Bình", "Chi", "Dũng"]},
            door_code="Dũng",
        ),
    ]),
    World(15, 2, "Lịch", "Ngày và giờ", "Date and Time", 3, [
        Level(
            id="15-1",
            title="Đếm ngày tới hội trại",
            story=(
                "Học kỳ 2 bắt đầu start = \"2026-01-01\", hội trại vào end = \"2026-03-15\". "
                "date.fromisoformat(...) đổi chuỗi thành ngày; lấy ngày trừ ngày ra khoảng cách, .days là số ngày."
            ),
            goal="Tính số ngày từ start tới end, nhập làm mật mã, tới cúp.",
            rows=MAP_DOOR_DOWN,
            starter=(
                "from datetime import date\n"
                "print(date.fromisoformat(start))\n"
                "hero.move_right(2)\n"
                "hero.move_down(1)\n"
            ),
            hints=["Đổi cả hai chuỗi sang date rồi trừ.", "Kết quả phép trừ có thuộc tính .days."],
            requires=["import:datetime"],
            extra_globals={"start": "2026-01-01", "end": "2026-03-15"},
            door_code=73,
        ),
    ]),
    # ================================================================ GIAI ĐOẠN 3
    World(16, 3, "Bẫy", "Xử lý ngoại lệ", "Errors and Exceptions", 6, [
        Level(
            id="16-1",
            title="Cửa kẹt",
            story=(
                "hero.open_door(\"right\") có thể gây lỗi DoorJammed. "
                "Dùng try/except để bắt lỗi và thử lại thay vì để chương trình dừng."
            ),
            goal="Mở được cửa kẹt và tới cúp.",
            rows=[
                "#########",
                "#@.GJ.GE#",
                "#########",
            ],
            starter=(
                "hero.move_right(2)\n"
                'hero.open_door("right")\n'
                "hero.move_right(4)\n"
            ),
            hints=[
                "Đặt lệnh mở cửa trong khối try, rồi bắt lỗi DoorJammed bằng khối except.",
                "Cửa có thể kẹt nhiều lần - hãy lặp tới khi mở được.",
            ],
            requires=["try"],
            jams=2,
        ),
        Level(
            id="16-2",
            title="Hai cánh cửa",
            story="Gom phần try/except vào một hàm để dùng lại cho nhiều cửa.",
            goal="Viết hàm force_open(direction) rồi mở cả hai cửa.",
            rows=[
                "##########",
                "#@.J..J.E#",
                "##########",
            ],
            starter=(
                "def force_open(direction):\n"
                "    pass  # thử mở tới khi được\n"
                "\n"
                "hero.move_right(1)\n"
            ),
            hints=[
                "Trong hàm, dùng while True và return khi mở được cửa.",
                "Sau khi viết hàm, gọi nó mỗi khi đứng trước một cửa kẹt.",
            ],
            requires=["try", "def"],
            jams=2,
        ),
        Level(
            id="16-3",
            title="Lọc mật mã giả",
            story=(
                "candidates = [\"7x\", \"??\", \"42\", \"abc\"] - chỉ một chuỗi là số thật. "
                "int(\"7x\") gây lỗi ValueError. Bắt lỗi đó để bỏ qua chuỗi giả."
            ),
            goal="Tìm chuỗi đổi được sang số, dùng nó làm mật mã, tới cúp.",
            rows=MAP_DOOR,
            starter=(
                "for text in candidates:\n"
                "    print(int(text))\n"
            ),
            hints=[
                "Bọc phép đổi int(...) trong try, bắt đúng loại lỗi ValueError.",
                "Đổi được thì giữ lại và thoát vòng lặp.",
            ],
            requires=["try", "except_value_error"],
            extra_globals={"candidates": ["7x", "??", "42", "abc"]},
            door_code=42,
        ),
    ]),
    World(17, 3, "Xưởng class", "Class & magic methods", "Classes", 5, [
        Level(
            id="17-1",
            title="Bình thuốc hồi máu",
            story=(
                "Hero chỉ còn 1 máu! class là khuôn để tạo đồ vật. Tạo class Potion có thuộc tính power. "
                "hero.use(vật) hồi số máu bằng vật.power."
            ),
            goal="Tạo bình thuốc hồi 2 máu, dùng nó cho đầy 3 máu rồi tới cúp.",
            rows=[
                "#########",
                "#@..G..E#",
                "#########",
            ],
            starter=(
                "class Potion:\n"
                "    pass\n"
                "\n"
                "hero.move_right(6)\n"
            ),
            hints=[
                "__init__ chạy khi tạo đồ vật; lưu dữ liệu vào self.",
                "Tạo đồ vật bằng cách gọi tên class như gọi hàm, truyền sức mạnh vào.",
            ],
            requires=["class", "dunder:__init__"],
            start_hp=1,
            need_full_hp=True,
        ),
        Level(
            id="17-2",
            title="Cộng véc-tơ",
            story=(
                "Ba mảnh bản đồ ghi 3 bước dịch chuyển (x, y): (1, 0), (3, 0), (0, 3). "
                "Magic method __add__ cho phép dùng dấu + với đồ vật của bạn, __str__ quy định cách in ra. "
                "hero.move_by(v) đi v.x ô ngang rồi v.y ô dọc."
            ),
            goal="Viết __add__ và __str__, cộng 3 véc-tơ, nói kết quả \"(4, 3)\", rồi move_by tới cúp.",
            rows=[
                "#######",
                "#@...G#",
                "#####.#",
                "#####.#",
                "#####E#",
                "#######",
            ],
            starter=(
                "class Vector:\n"
                "    def __init__(self, x, y):\n"
                "        self.x = x\n"
                "        self.y = y\n"
                "\n"
                "a = Vector(1, 0)\n"
                "print(a.x, a.y)\n"
            ),
            hints=[
                "__add__(self, other) phải return một Vector MỚI.",
                "__str__ phải return một chuỗi dạng \"(x, y)\".",
            ],
            requires=["dunder:__add__", "dunder:__str__"],
            say_contains="(4, 3)",
        ),
        Level(
            id="17-3",
            title="Lộ trình tuần tra",
            story=(
                "hero.follow(lộ_trình) đi theo từng hướng trong lộ trình. "
                "Viết class Patrol có __iter__ để vòng for (và follow) duyệt được nó. "
                "Mỗi vòng tuần tra là: \"right\" rồi \"down\"."
            ),
            goal="Tạo Patrol(4) gồm 4 vòng tuần tra, cho hero follow để xuống hết cầu thang.",
            rows=MAP_STAIRS,
            starter=(
                "class Patrol:\n"
                "    def __init__(self, rounds):\n"
                "        self.rounds = rounds\n"
                "\n"
                'hero.follow(["right", "down"])  # follow nhận thứ duyệt được\n'
            ),
            hints=[
                "__iter__ cần return một iterator - iter(một_list) là đủ.",
                "Nhân list với số để lặp lại nó nhiều lần.",
            ],
            requires=["dunder:__iter__", "call:follow"],
        ),
    ]),
    World(18, 3, "Trùm giữa", "Tổng hợp giai đoạn 1-3", "Kiểm tra Python (Basic)", 4, [
        Level(
            id="18-1",
            title="Đại chiến Vịt Vương",
            story=(
                "Dùng mọi thứ đã học! Quái: robot → hammer, barrel → axe. "
                "Mật mã = int(secret) * 2 với secret = \"21\". Cửa thứ hai bị kẹt. "
                "Vịt Vương có 3 máu và chỉ sợ \"sword\"."
            ),
            goal="Hạ quái, mở 2 cửa, đánh bại Vịt Vương, nhặt ngọc và tới cúp.",
            rows=[
                "###############",
                "#@.rGb.D.JGB.E#",
                "###############",
            ],
            starter=(
                'weakness = {"robot": "hammer", "barrel": "axe", "duck": "sword"}\n'
                "\n"
                "# Giai đoạn 1: hạ 2 quái đầu tiên\n"
                "for enemy in hero.find_enemies()[:2]:\n"
                "    pass\n"
            ),
            hints=[
                "Giai đoạn 1: hạ 2 quái bằng vũ khí tra trong dict.",
                "Giai đoạn 2-3: đứng cạnh từng cửa; cửa mật mã cần ép kiểu, cửa kẹt cần try/except.",
                "Giai đoạn 4: boss có 3 máu - dùng vòng lặp để đánh.",
            ],
            requires=["dict", "for", "try", "call:int"],
            extra_globals={"secret": "21"},
            door_code=42,
            jams=2,
            weapons=True,
            kill_all=True,
        ),
    ]),
    # ================================================================ GIAI ĐOẠN 4
    World(19, 4, "Băng chuyền", "map, filter, zip, lambda", "Built-Ins · Python Functionals", 1, [
        Level(
            id="19-1",
            title="Máy lọc số",
            story=(
                "raw = [\"3\", \"x\", \"5\", \"?\", \"7\"] lẫn cả chữ. filter giữ lại phần tử thoả điều kiện, "
                "map áp một hàm lên mọi phần tử. lambda viết hàm ngắn trong 1 dòng."
            ),
            goal="Lọc chuỗi là số, đổi sang int bằng map, mật mã = tổng. Tới cúp.",
            rows=MAP_DOOR_DOWN,
            starter=(
                "double = lambda n: n * 2\n"
                "print(double(5))\n"
                "print(list(map(double, [1, 2, 3])))\n"
            ),
            hints=[
                "Chuỗi có hàm .isdigit() trả về True nếu toàn chữ số.",
                "filter trước, map sau, cuối cùng cộng lại.",
            ],
            requires=["call:map", "call:filter", "lambda"],
            extra_globals={"raw": ["3", "x", "5", "?", "7"]},
            door_code=15,
        ),
        Level(
            id="19-2",
            title="Phát vũ khí",
            story=(
                "weapons = [\"hammer\", \"axe\", \"bow\"] đã xếp đúng thứ tự quái từ trái sang phải. "
                "zip(a, b) ghép từng cặp: phần tử 1 của a với phần tử 1 của b..."
            ),
            goal="Dùng zip ghép quái với vũ khí, hạ hết quái, tới cổng.",
            rows=[
                "###########",
                "#@.r.b.c..#",
                "#.........#",
                "#........E#",
                "###########",
            ],
            starter=(
                'for number, letter in zip([1, 2, 3], ["a", "b", "c"]):\n'
                "    print(number, letter)\n"
            ),
            hints=[
                "find_enemies() đã xếp quái từ trái sang phải.",
                "Mỗi vòng zip cho một cặp (quái, vũ khí).",
            ],
            requires=["call:zip"],
            extra_globals={"weapons": ["hammer", "axe", "bow"]},
            weapons=True,
            kill_all=True,
        ),
    ]),
    World(20, 4, "Mật thư", "Regex & XML", "Regex and Parsing · XML", 2, [
        Level(
            id="20-1",
            title="Bức thư bí ẩn",
            story=(
                "letter = \"Kho báu ở phòng 12. Mật mã là 4207, đừng nhầm với 99!\" "
                "Biểu thức chính quy (regex) tìm mẫu trong chữ: \\d+ là \"một hay nhiều chữ số\"."
            ),
            goal="Dùng re.search tìm số đứng sau \"Mật mã là\", mở cửa, tới cúp.",
            rows=MAP_DOOR,
            starter=(
                "import re\n"
                'print(re.findall(r"\\d+", letter))\n'
                "hero.move_right(2)\n"
            ),
            hints=[
                "Đặt phần cần lấy trong ngoặc tròn ( ) để tạo nhóm.",
                ".group(1) lấy nội dung nhóm thứ nhất - nhớ đổi sang int.",
            ],
            requires=["import:re"],
            extra_globals={"letter": "Kho báu ở phòng 12. Mật mã là 4207, đừng nhầm với 99!"},
            door_code=4207,
        ),
        Level(
            id="20-2",
            title="Bản đồ XML",
            story=(
                "Bản đồ kho báu viết bằng XML trong biến map_xml. Mỗi thẻ <gem x=\"..\" y=\"..\"/> là một viên ngọc, "
                "thẻ <exit .../> là cổng. Dùng xml.etree.ElementTree để đọc."
            ),
            goal="Đọc XML, đi nhặt từng viên ngọc theo toạ độ trong thẻ, rồi tới cổng.",
            rows=[
                "###########",
                "#@...#..G.#",
                "#.##...#..#",
                "#..G.....E#",
                "###########",
            ],
            starter=(
                "import xml.etree.ElementTree as ET\n"
                "root = ET.fromstring(map_xml)\n"
                "print(root.tag)\n"
            ),
            hints=[
                "root.findall(\"gem\") trả về list các thẻ gem.",
                "thẻ.get(\"x\") trả về CHUỖI - nhớ đổi sang int.",
            ],
            requires=["import:xml", "call:fromstring"],
            extra_globals={
                "map_xml": '<map><gem x="3" y="3"/><gem x="8" y="1"/><exit x="9" y="3"/></map>',
            },
        ),
    ]),
    World(21, 4, "Bùa chú", "Closure & decorator", "Closures and Decorators", 3, [
        Level(
            id="21-1",
            title="Xưởng làm bùa",
            story=(
                "Closure: hàm bên ngoài tạo và trả về một hàm bên trong; hàm bên trong NHỚ biến của hàm ngoài. "
                "Viết make_mover(direction) trả về một hàm mover(steps) đi theo hướng đó."
            ),
            goal="Tạo go_right và go_down bằng make_mover, dùng chúng đi tới cúp.",
            rows=[
                "#########",
                "#@..G####",
                "####.####",
                "####..GE#",
                "#########",
            ],
            starter=(
                "def make_mover(direction):\n"
                "    pass\n"
                "\n"
                'hero.follow(["right"] * 3)  # đi phải 3 ô\n'
            ),
            hints=[
                "Định nghĩa hàm mover BÊN TRONG make_mover, rồi return mover (không có ngoặc).",
                "Đường đi: phải 3, xuống 2, phải 3.",
            ],
            requires=["closure"],
        ),
        Level(
            id="21-2",
            title="Bùa nhân đôi",
            story=(
                "Decorator là hàm \"bọc\" một hàm khác để thêm sức mạnh. Viết @twice ở trên một hàm "
                "thì mỗi lần gọi, hàm đó chạy 2 lần."
            ),
            goal="Viết decorator twice, gắn vào hàm stair (1 bậc thang), xuống hết 4 bậc chỉ với 2 lần gọi.",
            rows=MAP_STAIRS,
            starter=(
                "def twice(action):\n"
                "    pass\n"
                "\n"
                "def stair():\n"
                "    hero.move_right()\n"
                "    hero.move_down()\n"
                "\n"
                "stair()\n"
            ),
            hints=[
                "twice nhận vào một hàm, tạo bên trong một hàm mới gọi hàm đó 2 lần, rồi trả hàm mới ra ngoài.",
                "Viết @twice ngay dòng phía trên def stair().",
            ],
            requires=["decorator"],
        ),
    ]),
    # ================================================================ GIAI ĐOẠN 5
    World(22, 5, "Ma trận", "NumPy cơ bản", "NumPy", 4, [
        Level(
            id="22-1",
            title="Bảng điểm",
            story=(
                "NumPy làm việc với bảng số rất nhanh. scores là bảng điểm 2 hàng × 3 cột. "
                "np.array(scores) tạo mảng; .sum() cộng mọi phần tử, .shape cho biết số hàng, số cột."
            ),
            goal="Tính tổng mọi điểm trong bảng bằng NumPy, nhập làm mật mã, tới cúp.",
            rows=MAP_DOOR,
            starter=(
                "import numpy as np\n"
                "board = np.array(scores)\n"
                "print(board.shape)\n"
            ),
            hints=["Mảng NumPy có sẵn hàm .sum().", "Đổi kết quả sang int trước khi nhập mật mã."],
            requires=["import:numpy"],
            extra_globals={"scores": [[1, 2, 3], [4, 5, 6]]},
            door_code=21,
        ),
        Level(
            id="22-2",
            title="Nhân ma trận",
            story=(
                "Phép nhân ma trận A @ B: phần tử hàng i, cột j = tổng (hàng i của A) × (cột j của B). "
                "A = [[1, 2], [3, 4]], B = [[2, 0], [1, 2]]. Mật mã = tổng mọi phần tử của A @ B."
            ),
            goal="Nhân hai ma trận bằng NumPy, cộng tất cả phần tử, mở cửa, tới cúp.",
            rows=MAP_DOOR_DOWN,
            starter=(
                "import numpy as np\n"
                "A = np.array(matrix_a)\n"
                "print(A * 2)  # nhân mỗi phần tử với 2\n"
            ),
            hints=[
                "A * B là nhân TỪNG phần tử - khác với nhân ma trận.",
                "Nhân ma trận dùng toán tử @ (hoặc np.dot).",
            ],
            requires=["op:@ or call:dot or call:matmul"],
            extra_globals={"matrix_a": [[1, 2], [3, 4]], "matrix_b": [[2, 0], [1, 2]]},
            door_code=26,
        ),
    ]),
    World(23, 5, "Thợ sửa lỗi", "Debugging", "Debugging", 5, [
        Level(
            id="23-1",
            title="Ba con bọ cú pháp",
            story=(
                "Code bên phải có 4 lỗi! Đọc kỹ thông báo lỗi ở Bảng tin: nó cho biết DÒNG nào sai. "
                "Sửa từng lỗi, chạy lại, cho tới khi hero nhặt hết ngọc."
            ),
            goal="Sửa hết lỗi để hero nhặt 8 ngọc, tới cúp và nói \"Xong!\".",
            rows=[
                "############",
                "#@GGGGGGGGE#",
                "############",
            ],
            starter=(
                "for i in range(8)\n"
                "hero.move_right()\n"
                'hero.say("Xong!)\n'
            ),
            hints=[
                "Lỗi cú pháp: dòng for thiếu gì ở cuối? Chuỗi có đóng nháy chưa?",
                "Hết lỗi cú pháp rồi mà vẫn thiếu ngọc? Đếm lại số bước.",
            ],
            requires=["for"],
            say_contains="Xong!",
        ),
        Level(
            id="23-2",
            title="Bọ logic",
            story=(
                "Code này chạy không báo lỗi cú pháp nhưng sai logic. Có 3 con bọ: một khoá dict viết sai, "
                "một dòng thụt lề sai chỗ, một chỗ đảo ngược toạ độ. Dùng print() để kiểm tra giá trị."
            ),
            goal="Sửa code để hạ hết quái bằng đúng vũ khí rồi tới cổng.",
            rows=MAP_WEAPON_ROOM,
            starter=(
                'weakness = {"Robot": "hammer", "barrel": "axe", "cannon": "bow"}\n'
                "for enemy in hero.find_enemies():\n"
                '    weapon = weakness[enemy["type"]]\n'
                'hero.attack_target(enemy["x"], enemy["y"], weapon)\n'
                "exit_x, exit_y = hero.exit_position\n"
                "hero.move_to(exit_y, exit_x)\n"
            ),
            hints=[
                "KeyError nghĩa là khoá không có trong dict - Python phân biệt chữ hoa, chữ thường.",
                "Lệnh tấn công phải nằm TRONG vòng lặp; move_to nhận (x, y) theo đúng thứ tự.",
            ],
            requires=["dict", "for"],
            weapons=True,
            kill_all=True,
        ),
    ]),
]


def all_levels() -> list[Level]:
    return [level for world in WORLDS for level in world.levels]


def world_of(level_id: str) -> World:
    return next(world for world in WORLDS if any(lv.id == level_id for lv in world.levels))


def stage_of(level_id: str) -> Stage:
    return STAGES[world_of(level_id).stage - 1]
