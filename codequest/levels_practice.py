"""Bài luyện tập thêm: mỗi World có đủ 5 bài.

Các bài ở đây được nối vào cuối World tương ứng (xem levels.py). Mã bài cũ không đổi.
Lời giải mẫu nằm riêng trong solutions/practice_solutions.py (chỉ trên máy giáo viên).
"""

from __future__ import annotations

from .engine import Level


def corridor(inner: str) -> list[str]:
    """One-row corridor map surrounded by walls."""
    wall = "#" * (len(inner) + 2)
    return [wall, f"#{inner}#", wall]


DOOR_RIGHT = corridor("@.GD.GE")
DOOR_DOWN = [
    "#######",
    "#@..###",
    "###.###",
    "###D###",
    "###G###",
    "###E###",
    "#######",
]
STAIRS = [
    "#######",
    "#@G####",
    "##.G###",
    "###.G##",
    "####.G#",
    "#####E#",
    "#######",
]
WEAPON_ROOM = [
    "###########",
    "#@..r..b..#",
    "#.........#",
    "#....c...E#",
    "###########",
]

PRACTICE: dict[int, list[Level]] = {}

# ================================================================ GIAI ĐOẠN 1
PRACTICE[1] = [
    Level(
        id="1-4",
        title="Đường zigzag",
        story="Đường đi như bậc thang: sang phải 1 ô, xuống 1 ô, cứ thế lặp lại.",
        goal="Đi theo đường zigzag, nhặt 2 viên ngọc và tới cúp.",
        rows=[
            "#######",
            "#@.####",
            "##.G###",
            "###.G##",
            "####.E#",
            "#######",
        ],
        starter="hero.move_right()\nhero.move_down()\n# viết tiếp\n",
        hints=["Không ghi số trong ngoặc thì hero đi 1 bước.", "Đếm xem cần mấy lần sang phải, mấy lần đi xuống."],
    ),
    Level(
        id="1-5",
        title="Đường vòng chữ U",
        story="Bức tường chắn ngay trước mặt. Hero phải đi vòng xuống dưới rồi mới lên được cúp.",
        goal="Đi vòng qua tường, nhặt ngọc, tới cúp rồi nói \"Đến rồi!\".",
        rows=[
            "#########",
            "#@#####E#",
            "#.#####.#",
            "#...G...#",
            "#########",
        ],
        starter="hero.move_down(2)\n",
        hints=["Đường đi gồm 3 đoạn: xuống, sang phải, lên.", "Lệnh say đặt ở cuối, sau khi tới cúp."],
        requires=["call:say"],
        say_contains="Đến rồi",
    ),
]

PRACTICE[2] = [
    Level(
        id="2-3",
        title="Biến thay đổi",
        story="Giá trị trong biến có thể thay đổi: steps = steps - 1 nghĩa là lấy giá trị cũ trừ 1 rồi cất lại.",
        goal="Dùng MỘT biến steps cho cả hai đoạn đường: đi phải 3, rồi giảm steps đi 1 và đi xuống.",
        rows=[
            "######",
            "#@.G.#",
            "####.#",
            "####E#",
            "######",
        ],
        starter="steps = 3\nhero.move_right(steps)\n# đổi steps rồi đi xuống\n",
        hints=["Gán lại steps bằng giá trị cũ trừ đi 1.", "Đoạn đi xuống dài 2 ô."],
        requires=["assign"],
    ),
    Level(
        id="2-4",
        title="Thẻ học sinh",
        story="Biến có sẵn: name = \"Mai\" (chuỗi) và age = 12 (số). Muốn ghép số vào chuỗi phải đổi số sang chuỗi bằng str().",
        goal="Nói \"Mai 12 tuổi\" bằng cách ghép name và age, rồi tới cúp.",
        rows=corridor("@..G..E"),
        starter='# name = "Mai", age = 12\nhero.say(name)\nhero.move_right(6)\n',
        hints=["Dùng dấu + để nối các chuỗi, nhớ có dấu cách giữa các phần.", "age là số, cần str(age)."],
        requires=["call:str"],
        extra_globals={"name": "Mai", "age": 12},
        say_contains="Mai 12 tuổi",
    ),
    Level(
        id="2-5",
        title="Chia kẹo",
        story=(
            "Có gems = 17 viên kẹo chia đều cho friends = 5 bạn. "
            "Phép // cho phần nguyên (mỗi bạn được mấy viên), phép % cho phần dư."
        ),
        goal="Nói \"3 dư 2\" (mỗi bạn được bao nhiêu, còn dư bao nhiêu) rồi tới cúp.",
        rows=corridor("@.G..E"),
        starter="# gems = 17, friends = 5\neach = gems / friends\nhero.say(each)\nhero.move_right(5)\n",
        hints=["Phép / cho kết quả số thực 3.4 - cần phép chia lấy phần nguyên.", "Phần dư dùng phép %."],
        requires=["assign"],
        extra_globals={"gems": 17, "friends": 5},
        say_contains="3 dư 2",
    ),
]

PRACTICE[3] = [
    Level(
        id="3-3",
        title="Mua vé",
        story="Vé vào cổng giá 5 xu, hero có coins = 7 xu. So sánh >= nghĩa là \"lớn hơn hoặc bằng\".",
        goal="Nếu đủ tiền mua vé thì nói \"Đủ tiền\", không thì nói \"Thiếu tiền\". Rồi tới cúp.",
        rows=corridor("@..G.E"),
        starter=(
            "# coins = 7, vé vào cổng giá 5\n"
            "if coins >= 10:\n"
            '    hero.say("Đủ tiền")\n'
            "else:\n"
            '    hero.say("Thiếu tiền")\n'
            "hero.move_right(5)\n"
        ),
        hints=["Điều kiện đang so sánh với sai giá vé.", "Vé giá 5 xu."],
        requires=["if"],
        extra_globals={"coins": 7},
        say_contains="Đủ tiền",
    ),
    Level(
        id="3-4",
        title="Ngã ba thứ hai",
        story="Lần này gai có thể ở trên hoặc ở dưới. elif cho phép kiểm tra thêm một điều kiện khác.",
        goal="Ở ngã ba, đi về phía KHÔNG có gai, nhặt ngọc rồi tới cúp.",
        rows=[
            "#######",
            "###GE##",
            "#@..###",
            "###^###",
            "#######",
        ],
        starter=(
            "hero.move_right(2)\n"
            'if hero.look("up") == "spike":\n'
            "    hero.move_down()\n"
        ),
        hints=["Hãy kiểm tra cả phía dưới: nếu dưới có gai thì đi lên.", "Sau khi rẽ, đi phải 1 ô là tới cúp."],
        requires=["if"],
    ),
    Level(
        id="3-5",
        title="Hai điều kiện",
        story="and: cả hai điều kiện đều đúng. or: chỉ cần một điều kiện đúng. hero.hp là số máu hiện tại.",
        goal="Chỉ tấn công khi bên phải là quái VÀ hero còn nhiều hơn 1 máu. Rồi tới cúp.",
        rows=corridor("@..r..E"),
        starter="hero.move_right(2)\nif hero.hp > 1:\n    pass\n",
        hints=["Ghép hai điều kiện bằng and trong cùng một câu if.", "Hạ quái xong, đi phải 4 ô."],
        requires=["if", "boolop"],
    ),
]

PRACTICE[4] = [
    Level(
        id="4-4",
        title="Bậc thang lớn dần",
        story="Biến i trong vòng for thay đổi mỗi vòng. range(1, 4) cho i = 1, 2, 3.",
        goal="Bậc thứ nhất dài 1 ô, bậc thứ hai dài 2 ô, bậc thứ ba dài 3 ô. Dùng i để đi đúng độ dài.",
        rows=[
            "#########",
            "#@.######",
            "##.G.####",
            "####..G.#",
            "#######E#",
            "#########",
        ],
        starter="for i in range(3):\n    print(i)\n",
        hints=["range(1, 4) bắt đầu từ 1 thay vì 0.", "Mỗi vòng: sang phải i ô rồi xuống 1 ô."],
        requires=["for"],
    ),
    Level(
        id="4-5",
        title="Vòng lặp lồng nhau",
        story=(
            "Vòng lặp có thể nằm trong vòng lặp. Vòng ngoài đếm bậc thang, vòng trong đi từng bước. "
            "Lần này bậc thang dài 1, 2, 3, 4 ô."
        ),
        goal="Dùng hai vòng for lồng nhau để xuống hết 4 bậc thang.",
        rows=[
            "#############",
            "#@.##########",
            "##.G.########",
            "####..G.#####",
            "#######..G..#",
            "###########E#",
            "#############",
        ],
        starter="for i in range(1, 5):\n    hero.move_right(i)\n",
        hints=["Vòng trong lặp i lần, mỗi lần đi 1 bước sang phải.", "Lệnh đi xuống thuộc vòng ngoài (thụt lề ít hơn)."],
        requires=["nested_for"],
    ),
]

PRACTICE[5] = [
    Level(
        id="5-3",
        title="Số có dấu chấm",
        story="distance = \"7.0\" là chuỗi có dấu chấm. int(\"7.0\") báo lỗi, phải đổi qua float trước.",
        goal="Đổi distance thành số nguyên đúng cách rồi đi đúng số bước tới cúp.",
        rows=corridor("@..G...E"),
        starter='# distance = "7.0"\nhero.move_right(int(distance))\n',
        hints=["float(\"7.0\") cho ra 7.0.", "Rồi mới đổi số thực sang số nguyên."],
        requires=["call:float"],
        extra_globals={"distance": "7.0"},
    ),
    Level(
        id="5-4",
        title="Số phòng",
        story="Cửa này cần mật mã là CHUỖI \"Phòng 7\". Biến room = 7 là số.",
        goal="Ghép chữ \"Phòng \" với room để tạo mật mã, mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter='# room = 7\nhero.move_right(2)\nhero.enter_code("Phòng" + room)\n',
        hints=["Chuỗi + số sẽ lỗi - đổi số sang chuỗi.", "Đừng quên dấu cách sau chữ Phòng."],
        requires=["call:str"],
        extra_globals={"room": 7},
        door_code="Phòng 7",
    ),
    Level(
        id="5-5",
        title="Công tắc bật tắt",
        story=(
            "switch = \"0\". Cửa cần giá trị True/False (bool). Bẫy: bool(\"0\") là True vì chuỗi không rỗng! "
            "Số 0 thì bool(0) mới là False."
        ),
        goal="Đổi switch sang số rồi sang bool để có đúng trạng thái công tắc, mở cửa, tới cúp.",
        rows=DOOR_DOWN,
        starter=(
            '# switch = "0"\n'
            "print(bool(switch))  # thử xem\n"
            "hero.move_right(2)\n"
            "hero.move_down(1)\n"
        ),
        hints=["Đổi sang int trước, rồi mới bool(...).", "Mở cửa xong, đi xuống 3 ô."],
        requires=["call:bool", "call:int"],
        extra_globals={"switch": "0"},
        door_code=False,
    ),
]

PRACTICE[6] = [
    Level(
        id="6-4",
        title="Hàm có tham số",
        story="Tham số giúp một hàm làm việc với nhiều giá trị khác nhau: step(2) và step(3) đi xa khác nhau.",
        goal="Viết hàm step(n): đi phải n ô rồi xuống n ô. Gọi step(2) rồi step(3) để tới cúp.",
        rows=[
            "########",
            "#@.G####",
            "###.####",
            "###.G..#",
            "######.#",
            "######.#",
            "######E#",
            "########",
        ],
        starter="def step(n):\n    hero.move_right(n)\n\nstep(2)\n",
        hints=["Thêm lệnh đi xuống n ô vào trong hàm.", "Gọi hàm thêm lần nữa với số khác."],
        requires=["def", "call:step"],
    ),
    Level(
        id="6-5",
        title="Khoảng cách điểm",
        story="scores = [7, 9, 4, 10, 6]. max() cho số lớn nhất, min() cho số nhỏ nhất.",
        goal="Mật mã = điểm cao nhất trừ điểm thấp nhất. Mở cửa và tới cúp.",
        rows=DOOR_DOWN,
        starter=(
            "# scores = [7, 9, 4, 10, 6]\n"
            "print(sum(scores))\n"
            "hero.move_right(2)\n"
            "hero.move_down(1)\n"
        ),
        hints=["Dùng cả max và min.", "Mở cửa xong đi xuống 3 ô."],
        requires=["call:max", "call:min"],
        extra_globals={"scores": [7, 9, 4, 10, 6]},
        door_code=6,
    ),
]

PRACTICE[7] = [
    Level(
        id="7-3",
        title="Gương soi",
        story="Mật mã bị viết ngược trong gương: scroll = \"olleh\". Cắt chuỗi với bước -1 sẽ đảo ngược chuỗi.",
        goal="Đảo ngược scroll để có mật mã, mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter='# scroll = "olleh"\nprint(scroll[0])\nhero.move_right(2)\n',
        hints=["Cú pháp [đầu:cuối:bước] - để trống đầu và cuối.", "Bước -1 đi từ cuối về đầu."],
        requires=["slice"],
        extra_globals={"scroll": "olleh"},
        door_code="hello",
    ),
    Level(
        id="7-4",
        title="Chỉ đường",
        story=(
            "route = \"2,3,1\" là chỉ đường: phải 2, xuống 3, phải 1. "
            ".split(\",\") cắt chuỗi tại dấu phẩy thành list các chuỗi nhỏ."
        ),
        goal="Tách route, đổi từng phần sang số rồi đi đúng chỉ đường tới cúp.",
        rows=[
            "######",
            "#@.G##",
            "###.##",
            "###.##",
            "###.E#",
            "######",
        ],
        starter='# route = "2,3,1"\nparts = route\nprint(parts)\n',
        hints=["Sau khi split, parts[0] là phần đầu tiên.", "Mỗi phần vẫn là chuỗi - cần int(...)."],
        requires=["call:split"],
        extra_globals={"route": "2,3,1"},
    ),
    Level(
        id="7-5",
        title="Đếm chữ a",
        story="message = \"banana bandana\". Chuỗi có hàm .count(\"x\") đếm số lần \"x\" xuất hiện.",
        goal="Mật mã = số chữ \"a\" trong message. Mở cửa và tới cúp.",
        rows=DOOR_DOWN,
        starter=(
            '# message = "banana bandana"\n'
            "print(len(message))\n"
            "hero.move_right(2)\n"
            "hero.move_down(1)\n"
        ),
        hints=["len đếm TẤT CẢ ký tự, kể cả dấu cách.", "Gọi .count trên chính message."],
        requires=["call:count"],
        extra_globals={"message": "banana bandana"},
        door_code=6,
    ),
]

PRACTICE[8] = [
    Level(
        id="8-3",
        title="Danh sách bước đi",
        story="steps = [3, 2, 4]: phải 3, xuống 2, phải 4. steps[0] là phần tử đầu tiên (vị trí 0).",
        goal="Dùng từng phần tử của steps để đi tới cúp.",
        rows=[
            "##########",
            "#@..G#####",
            "####.#####",
            "####...GE#",
            "##########",
        ],
        starter="# steps = [3, 2, 4]\nprint(steps[0])\nprint(len(steps))\n",
        hints=["Phần tử thứ hai là steps[1].", "Thứ tự: phải, xuống, phải."],
        requires=["subscript"],
        extra_globals={"steps": [3, 2, 4]},
    ),
    Level(
        id="8-4",
        title="Ghi chép vị trí",
        story="list.append(x) thêm x vào cuối list. Ghi lại cột x của từng viên ngọc trước khi nhặt.",
        goal="Tạo list các toạ độ x của ngọc, nói list đó ra (ví dụ [2, 4, 6]) rồi tới cúp.",
        rows=corridor("@G.G.G.E"),
        starter="xs = []\nfor gem in hero.find_gems():\n    pass\nhero.say(xs)\n",
        hints=["Trong vòng lặp, thêm gem[\"x\"] vào xs.", "Nói xong thì đi phải 7 ô."],
        requires=["call:append"],
        say_contains="[2, 4, 6]",
    ),
    Level(
        id="8-5",
        title="Các điểm dừng",
        story="stops là list các tuple (x, y). Duyệt list và mở gói mỗi tuple ngay trong vòng for: for x, y in stops.",
        goal="Đi lần lượt tới mọi điểm dừng trong stops (điểm cuối là cổng).",
        rows=[
            "########",
            "#@.G####",
            "###.####",
            "###G.GE#",
            "########",
        ],
        starter=(
            "# stops = [(3, 1), (3, 3), (5, 3), (6, 3)]\n"
            "first = stops[0]\n"
            "print(first[0], first[1])\n"
        ),
        hints=["Vòng for có thể tách mỗi tuple thành 2 biến ngay khi duyệt.", "Mỗi vòng, đi tới toạ độ vừa lấy ra bằng move_to."],
        requires=["for", "call:move_to"],
        extra_globals={"stops": [(3, 1), (3, 3), (5, 3), (6, 3)]},
    ),
]

PRACTICE[9] = [
    Level(
        id="9-3",
        title="Đi chợ",
        story="prices = {\"táo\": 5, \"cam\": 7, \"lê\": 4} là bảng giá. basket = [\"táo\", \"lê\", \"táo\"] là giỏ hàng.",
        goal="Tính tổng tiền giỏ hàng bằng cách tra bảng giá, nhập làm mật mã, tới cúp.",
        rows=DOOR_RIGHT,
        starter='# prices, basket có sẵn\nprint(prices["táo"])\nhero.move_right(2)\n',
        hints=["Duyệt từng món trong giỏ, tra giá trong dict.", "Cộng dồn vào một biến tổng bắt đầu từ 0."],
        requires=["for"],
        extra_globals={"prices": {"táo": 5, "cam": 7, "lê": 4}, "basket": ["táo", "lê", "táo"]},
        door_code=14,
    ),
    Level(
        id="9-4",
        title="Sổ đếm",
        story=(
            "words = [\"mèo\", \"chó\", \"mèo\", \"cá\", \"mèo\"]. Dùng dict làm sổ đếm: "
            "counts.get(w, 0) trả về số đếm hiện tại, hoặc 0 nếu chưa có."
        ),
        goal="Đếm mỗi con vật xuất hiện mấy lần. Mật mã = số lần \"mèo\" xuất hiện.",
        rows=DOOR_DOWN,
        starter="counts = {}\nprint(counts)\nhero.move_right(2)\nhero.move_down(1)\n",
        hints=["Mỗi vòng: counts[w] = số cũ + 1.", "Tra counts[\"mèo\"] để lấy mật mã."],
        requires=["dict", "for"],
        extra_globals={"words": ["mèo", "chó", "mèo", "cá", "mèo"]},
        door_code=3,
    ),
    Level(
        id="9-5",
        title="Khách tham quan",
        story="visitors ghi tên khách mỗi lần vào cửa, có người vào nhiều lần. set chỉ giữ tên không trùng.",
        goal="Mật mã = số NGƯỜI khác nhau đã tới. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="# visitors có sẵn\nprint(len(visitors))\nhero.move_right(2)\n",
        hints=["len(visitors) đếm cả tên trùng.", "Đổi sang set trước khi đếm."],
        requires=["set"],
        extra_globals={"visitors": ["An", "Bình", "An", "Chi", "Bình", "An"]},
        door_code=3,
    ),
]

PRACTICE[10] = [
    Level(
        id="10-3",
        title="Tổng bình phương",
        story="numbers = [1, 2, 3, 4]. List comprehension tạo list mới từ list cũ trong 1 dòng.",
        goal="Tạo list bình phương các số bằng comprehension, mật mã = tổng của list đó.",
        rows=DOOR_RIGHT,
        starter="squares = []\nprint(numbers)\nhero.move_right(2)\n",
        hints=["[biểu_thức for n in numbers]", "Bình phương của n là n * n."],
        requires=["listcomp"],
        extra_globals={"numbers": [1, 2, 3, 4]},
        door_code=30,
    ),
    Level(
        id="10-4",
        title="Bảng số",
        story="table = [[1, 2], [3, 4], [5, 6]] là list lồng nhau. Comprehension có thể có 2 vòng for.",
        goal="Cộng mọi số trong table, nhập tổng làm mật mã, tới cúp.",
        rows=DOOR_DOWN,
        starter="print(table[0])\nprint(table[2][1])\nhero.move_right(2)\nhero.move_down(1)\n",
        hints=["Vòng for ngoài duyệt hàng, vòng trong duyệt số trong hàng.", "Tính sum của list vừa trải phẳng."],
        requires=["listcomp"],
        extra_globals={"table": [[1, 2], [3, 4], [5, 6]]},
        door_code=21,
    ),
    Level(
        id="10-5",
        title="Dò bản đồ",
        story=(
            "hero.scan() trả về bản đồ grid[y][x]. enumerate(list) cho cả vị trí lẫn phần tử. "
            "Lần này không dùng find_gems - hãy tự tìm toạ độ ngọc từ bản đồ."
        ),
        goal="Tìm toạ độ mọi ô \"gem\" bằng comprehension trên bản đồ, đi nhặt hết rồi tới cổng.",
        rows=[
            "#########",
            "#@..#..G#",
            "#.#...#.#",
            "#G..#..E#",
            "#########",
        ],
        starter="grid = hero.scan()\nprint(grid[1][7])\n",
        hints=[
            "Duyệt for y, row in enumerate(grid) rồi for x, tile in enumerate(row).",
            "Giữ lại (x, y) khi tile == \"gem\", sau đó move_to từng điểm.",
        ],
        requires=["listcomp", "call:scan"],
    ),
]

# ================================================================ GIAI ĐOẠN 2
PRACTICE[11] = [
    Level(
        id="11-2",
        title="Ai vắng mặt",
        story=(
            "invited là danh sách bạn được mời, came là những bạn đã tới. "
            "Hiệu tập hợp a - b gồm phần tử có trong a nhưng KHÔNG có trong b."
        ),
        goal="Mật mã = số bạn được mời mà chưa tới. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="# invited, came có sẵn\nprint(set(invited))\nhero.move_right(2)\n",
        hints=["Đổi cả hai list sang set.", "Lấy tập được mời trừ tập đã tới, rồi đếm."],
        requires=["op:- or call:difference"],
        extra_globals={"invited": ["An", "Bình", "Chi", "Dũng", "Hà"], "came": ["Bình", "Hà", "An"]},
        door_code=2,
    ),
    Level(
        id="11-3",
        title="Soát vé",
        story=(
            "tickets là các vé khách đưa ra, valid là tập các mã vé hợp lệ. "
            "Toán tử in kiểm tra một giá trị có nằm trong tập hay không - với set rất nhanh."
        ),
        goal="Đếm số vé hợp lệ (tính cả vé trùng), nhập làm mật mã, tới cúp.",
        rows=DOOR_DOWN,
        starter='# tickets (list), valid (set) có sẵn\nprint("A12" == "A12")\nhero.move_right(2)\nhero.move_down(1)\n',
        hints=["Duyệt từng vé, dùng if ... in valid.", "Cộng dồn số vé hợp lệ vào một biến đếm."],
        requires=["membership"],
        extra_globals={"tickets": ["A12", "B07", "A12", "C33", "B07"], "valid": {"A12", "C33"}},
        door_code=3,
    ),
    Level(
        id="11-4",
        title="Sticker độc nhất",
        story=(
            "An và Bình sưu tầm sticker. Hiệu đối xứng a ^ b gồm phần tử chỉ có ở MỘT trong hai người "
            "(bỏ những cái cả hai cùng có)."
        ),
        goal="Mật mã = số sticker chỉ một trong hai bạn có. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="a = set(stickers_an)\nb = set(stickers_binh)\nprint(a & b)\nhero.move_right(2)\n",
        hints=["a & b là phần CẢ HAI có - không phải thứ cần tìm.", "Dùng toán tử ^ rồi đếm."],
        requires=["op:^ or call:symmetric_difference"],
        extra_globals={"stickers_an": [1, 2, 3, 4], "stickers_binh": [3, 4, 5]},
        door_code=3,
    ),
    Level(
        id="11-5",
        title="Kiểm tra ba lô",
        story=(
            "Đi thám hiểm cần đủ các món trong required = {\"key\", \"map\"}. "
            "a <= b (hoặc a.issubset(b)) cho biết a có nằm trọn trong b không."
        ),
        goal="Nếu ba lô có đủ đồ cần thiết thì nói \"Đủ đồ\", không thì \"Thiếu đồ\". Rồi tới cúp.",
        rows=corridor("@..G..E"),
        starter=(
            "# required (set), backpack (list) có sẵn\n"
            "if len(backpack) > 5:\n"
            '    hero.say("Đủ đồ")\n'
            "else:\n"
            '    hero.say("Thiếu đồ")\n'
            "hero.move_right(6)\n"
        ),
        hints=[
            "Số món nhiều hay ít không quan trọng - quan trọng là có đủ món cần thiết không.",
            "Đổi backpack sang set rồi kiểm tra tập con.",
        ],
        requires=["if", "subset"],
        extra_globals={"required": {"key", "map"}, "backpack": ["map", "rope", "key", "torch"]},
        say_contains="Đủ đồ",
    ),
]

PRACTICE[12] = [
    Level(
        id="12-3",
        title="Thuê xe buýt",
        story="Có students = 45 học sinh, mỗi xe chở seats = 16 bạn. Thiếu chỗ là không được - phải làm tròn LÊN.",
        goal="Tính số xe cần thuê bằng math.ceil, nhập làm mật mã, tới cúp.",
        rows=DOOR_RIGHT,
        starter="import math\n# students = 45, seats = 16\nprint(students / seats)\nhero.move_right(2)\n",
        hints=["45 / 16 = 2.8125 - không thể thuê 2.8 xe.", "math.ceil làm tròn lên."],
        requires=["call:ceil"],
        extra_globals={"students": 45, "seats": 16},
        door_code=3,
    ),
    Level(
        id="12-4",
        title="Sân tròn",
        story="Sân chơi hình tròn bán kính r = 5 m. Diện tích = π × r². round() làm tròn tới số nguyên gần nhất.",
        goal="Tính diện tích sân, làm tròn thành số nguyên, nhập làm mật mã, tới cúp.",
        rows=DOOR_DOWN,
        starter="import math\n# r = 5\nprint(r ** 2)\nhero.move_right(2)\nhero.move_down(1)\n",
        hints=["Dùng math.pi cho số π.", "round(...) để ra số nguyên."],
        requires=["import:math"],
        extra_globals={"r": 5},
        door_code=79,
    ),
    Level(
        id="12-5",
        title="Chọn đội trực nhật",
        story=(
            "Tổ có 6 bạn, cần chọn 2 bạn trực nhật (không quan tâm thứ tự). "
            "math.comb(n, k) đếm số cách chọn k người trong n người."
        ),
        goal="Mật mã = số cách chọn 2 bạn trong 6 bạn. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="import math\nprint(math.factorial(3))\nhero.move_right(2)\n",
        hints=["comb = combination = tổ hợp.", "Truyền vào số bạn và số cần chọn."],
        requires=["call:comb or call:factorial"],
        door_code=15,
    ),
]

PRACTICE[13] = [
    Level(
        id="13-3",
        title="Bao nhiêu cách xếp",
        story="letters = \"ABCD\". permutations cũng dùng được với chuỗi. list(...) gom tất cả, len(...) để đếm.",
        goal="Mật mã = số cách sắp xếp 4 chữ cái A, B, C, D. Mở cửa và tới cúp.",
        rows=DOOR_DOWN,
        starter='from itertools import permutations\nprint(list(permutations("AB")))\nhero.move_right(2)\nhero.move_down(1)\n',
        hints=["Đếm số phần tử permutations sinh ra.", "4 vật có 4 × 3 × 2 × 1 cách xếp - hãy kiểm tra lại bằng code."],
        requires=["call:permutations"],
        extra_globals={"letters": "ABCD"},
        door_code=24,
    ),
    Level(
        id="13-4",
        title="Phối đồ",
        story=(
            "shirts = [\"đỏ\", \"xanh\"], pants = [\"đen\", \"trắng\", \"nâu\"]. "
            "product(a, b) ghép MỌI phần tử của a với MỌI phần tử của b."
        ),
        goal="Mật mã = số bộ quần áo phối được. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter='from itertools import product\nfor combo in product([1, 2], ["x"]):\n    print(combo)\n',
        hints=["Ghép shirts với pants bằng product.", "Gom vào list rồi đếm."],
        requires=["call:product"],
        extra_globals={"shirts": ["đỏ", "xanh"], "pants": ["đen", "trắng", "nâu"]},
        door_code=6,
    ),
    Level(
        id="13-5",
        title="Cặp xu",
        story="coins = [1, 2, 5, 10]. Chọn 2 đồng xu khác nhau. Có bao nhiêu cặp có tổng từ 7 trở lên?",
        goal="Đếm các cặp xu có tổng >= 7, nhập làm mật mã, tới cúp.",
        rows=DOOR_DOWN,
        starter="from itertools import combinations\nprint(list(combinations([1, 2, 5], 2)))\n",
        hints=["Duyệt combinations(coins, 2) và kiểm tra tổng.", "Đếm số cặp thoả điều kiện."],
        requires=["call:combinations"],
        extra_globals={"coins": [1, 2, 5, 10]},
        door_code=4,
    ),
]

PRACTICE[14] = [
    Level(
        id="14-3",
        title="Phân loại thực phẩm",
        story=(
            "foods là list các cặp (loại, tên). defaultdict(list) tự tạo list rỗng cho loại mới, "
            "nên có thể append ngay mà không lỗi."
        ),
        goal="Gom món ăn theo loại. Mật mã = số món thuộc loại \"quả\". Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter='from collections import defaultdict\ngroups = defaultdict(list)\nprint(groups["rau"])\n',
        hints=["Duyệt từng cặp (loại, tên) và thêm tên vào đúng nhóm.", "Đếm số phần tử trong nhóm \"quả\"."],
        requires=["call:defaultdict"],
        extra_globals={
            "foods": [("rau", "cải"), ("quả", "táo"), ("rau", "muống"), ("quả", "cam"), ("quả", "lê")],
        },
        door_code=3,
    ),
    Level(
        id="14-4",
        title="Bầu lớp trưởng",
        story="votes là các phiếu bầu. Mật mã là TÊN người được nhiều phiếu nhất.",
        goal="Dùng Counter tìm người thắng cử, nhập tên làm mật mã, tới cúp.",
        rows=DOOR_DOWN,
        starter="from collections import Counter\nprint(len(votes))\nhero.move_right(2)\nhero.move_down(1)\n",
        hints=["most_common(1) cho list có một tuple (tên, số phiếu).", "Mật mã là phần tên trong tuple."],
        requires=["call:Counter"],
        extra_globals={"votes": ["Lan", "Minh", "Lan", "Hoa", "Minh", "Lan"]},
        door_code="Lan",
    ),
    Level(
        id="14-5",
        title="Ba lần gần nhất",
        story=(
            "scores = [5, 8, 2, 9, 4] là điểm các lần chơi. deque(maxlen=3) chỉ giữ 3 phần tử MỚI NHẤT - "
            "thêm phần tử thứ 4 thì phần tử cũ nhất tự bị bỏ."
        ),
        goal="Mật mã = tổng điểm 3 lần chơi gần nhất. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="from collections import deque\nrecent = deque(maxlen=3)\nprint(recent)\n",
        hints=["Có thể tạo deque thẳng từ scores với maxlen=3.", "Cộng các phần tử còn lại trong deque."],
        requires=["call:deque"],
        extra_globals={"scores": [5, 8, 2, 9, 4]},
        door_code=15,
    ),
]

PRACTICE[15] = [
    Level(
        id="15-2",
        title="Thứ mấy",
        story=(
            "day = \"2026-09-05\" là ngày khai giảng. ngay.weekday() cho thứ trong tuần: "
            "0 = thứ Hai, 1 = thứ Ba, ..., 6 = Chủ nhật."
        ),
        goal="Mật mã = kết quả weekday() của ngày khai giảng. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="from datetime import date\nprint(date.fromisoformat(day))\nhero.move_right(2)\n",
        hints=["Đổi day thành date trước.", "Gọi .weekday() trên ngày đó."],
        requires=["call:weekday"],
        extra_globals={"day": "2026-09-05"},
        door_code=5,
    ),
    Level(
        id="15-3",
        title="Hạn nộp bài",
        story=(
            "Dự án bắt đầu start = \"2026-01-01\" và phải nộp sau 45 ngày. "
            "Ngày + timedelta(days=45) cho ra ngày mới. str(ngay) cho dạng \"năm-tháng-ngày\"."
        ),
        goal="Mật mã = ngày nộp bài dạng chuỗi \"năm-tháng-ngày\". Mở cửa và tới cúp.",
        rows=DOOR_DOWN,
        starter="from datetime import date, timedelta\nprint(timedelta(days=1))\nhero.move_right(2)\nhero.move_down(1)\n",
        hints=["Cộng một timedelta vào ngày bắt đầu.", "Mật mã là chuỗi - đổi ngày sang str."],
        requires=["call:timedelta"],
        extra_globals={"start": "2026-01-01"},
        door_code="2026-02-15",
    ),
    Level(
        id="15-4",
        title="Mấy tuần ôn thi",
        story="Ôn thi từ start = \"2026-03-02\" tới end = \"2026-05-25\". Một tuần có 7 ngày.",
        goal="Mật mã = số tuần ôn thi (số ngày chia lấy phần nguyên cho 7). Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="from datetime import date\nhero.move_right(2)\n",
        hints=["Trừ hai ngày rồi lấy .days.", "Dùng phép chia lấy phần nguyên cho 7."],
        requires=["import:datetime"],
        extra_globals={"start": "2026-03-02", "end": "2026-05-25"},
        door_code=12,
    ),
    Level(
        id="15-5",
        title="Viết ngày kiểu Việt Nam",
        story=(
            "day = \"2026-11-20\". Người Việt viết ngày/tháng/năm. ngay.strftime(\"%d/%m/%Y\") định dạng lại: "
            "%d là ngày, %m là tháng, %Y là năm."
        ),
        goal="Mật mã = ngày Nhà giáo Việt Nam viết dạng \"ngày/tháng/năm\". Mở cửa và tới cúp.",
        rows=DOOR_DOWN,
        starter="from datetime import date\nprint(date.fromisoformat(day))\nhero.move_right(2)\nhero.move_down(1)\n",
        hints=["Đổi day thành date rồi gọi strftime.", "Mẫu định dạng dùng dấu / giữa các phần."],
        requires=["call:strftime"],
        extra_globals={"day": "2026-11-20"},
        door_code="20/11/2026",
    ),
]

# ================================================================ GIAI ĐOẠN 3
GROWING_STAIRS = [
    "#########",
    "#@.######",
    "##.G.####",
    "####..G.#",
    "#######E#",
    "#########",
]
SPIKE_HOPS = [
    "#############",
    "#...G..G..G.#",
    "#@..^..^..^E#",
    "#############",
]

PRACTICE[16] = [
    Level(
        id="16-4",
        title="Phép chia nguy hiểm",
        story=(
            "pairs = [(10, 2), (5, 0), (9, 3)]. Chia cho 0 gây lỗi ZeroDivisionError. "
            "Hãy bỏ qua cặp chia cho 0 và cộng kết quả các cặp còn lại (dùng phép //)."
        ),
        goal="Mật mã = tổng a // b của các cặp chia được. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="total = 0\nfor a, b in pairs:\n    total += a // b\nprint(total)\n",
        hints=["Bọc phép chia trong try.", "Bắt đúng loại lỗi chia cho 0."],
        requires=["try", "except:ZeroDivisionError"],
        extra_globals={"pairs": [(10, 2), (5, 0), (9, 3)]},
        door_code=8,
    ),
    Level(
        id="16-5",
        title="Tự báo lỗi",
        story=(
            "moves = [3, -1, 4] là số bước cần đi, nhưng số bước âm là dữ liệu hỏng. "
            "Lệnh raise ValueError(\"...\") tự tạo ra lỗi - nơi gọi hàm sẽ bắt lỗi đó bằng try/except."
        ),
        goal="Viết hàm check(n) báo lỗi ValueError khi n âm. Đi theo các bước hợp lệ và bỏ qua bước hỏng.",
        rows=corridor("@..G...E"),
        starter="def check(n):\n    return n\n\nfor n in moves:\n    hero.move_right(check(n))\n",
        hints=["Trong check: nếu n nhỏ hơn 0 thì raise, ngược lại trả về n.", "Bọc lời gọi check trong try/except ValueError."],
        requires=["raise", "try"],
        extra_globals={"moves": [3, -1, 4]},
    ),
]

PRACTICE[17] = [
    Level(
        id="17-4",
        title="Chiếc ví",
        story=(
            "Phương thức là hàm viết BÊN TRONG class, luôn có self là tham số đầu tiên. "
            "coins = [5, 10, 2] là các đồng xu nhặt được."
        ),
        goal="Thêm phương thức add(amount) cho class Wallet, bỏ hết xu vào ví. Mật mã = tổng tiền trong ví.",
        rows=DOOR_RIGHT,
        starter="class Wallet:\n    def __init__(self):\n        self.total = 0\n\nw = Wallet()\nprint(w.total)\n",
        hints=["add(self, amount) cộng amount vào self.total.", "Duyệt coins và gọi w.add(...) cho từng đồng."],
        requires=["class", "method"],
        extra_globals={"coins": [5, 10, 2]},
        door_code=17,
    ),
    Level(
        id="17-5",
        title="Đội của tôi",
        story=(
            "Magic method __len__ quy định kết quả của len(doi_tuong). "
            "members = [\"An\", \"Bình\", \"Chi\", \"Dũng\"]."
        ),
        goal="Viết __len__ cho class Team trả về số thành viên, rồi nhập len(team) làm mật mã.",
        rows=DOOR_DOWN,
        starter=(
            "class Team:\n"
            "    def __init__(self, members):\n"
            "        self.members = members\n"
            "\n"
            "team = Team(members)\n"
            "print(team.members)\n"
        ),
        hints=["__len__(self) phải return một số nguyên.", "Số thành viên chính là độ dài list self.members."],
        requires=["dunder:__len__"],
        extra_globals={"members": ["An", "Bình", "Chi", "Dũng"]},
        door_code=4,
    ),
]

PRACTICE[18] = [
    Level(
        id="18-2",
        title="Kho vũ khí",
        story=(
            "Ôn tập: dict vũ khí, vòng lặp và cửa kẹt. Quái: robot → hammer, barrel → axe, cannon → bow. "
            "Cửa kẹt ở ngay trên cúp."
        ),
        goal="Hạ hết quái bằng đúng vũ khí, tới đứng trên cửa kẹt, mở cửa rồi xuống cúp.",
        rows=[
            "############",
            "#@..b...r..#",
            "#..c.......#",
            "##########J#",
            "##########E#",
            "############",
        ],
        starter=(
            'weakness = {"robot": "hammer", "barrel": "axe", "cannon": "bow"}\n'
            "for enemy in hero.find_enemies():\n"
            '    print(enemy["type"], enemy["x"], enemy["y"])\n'
        ),
        hints=[
            "Ô ngay trên cửa kẹt là (10, 2) - dùng move_to để tới đó sau khi hạ quái.",
            "Cửa kẹt nằm phía dưới hero: thử mở nhiều lần bằng try/except.",
        ],
        requires=["dict", "for", "try"],
        jams=2,
        weapons=True,
        kill_all=True,
    ),
    Level(
        id="18-3",
        title="Lọc chữ số",
        story="scroll = \"x7y3z9\". Mật mã = tổng các chữ số trong cuộn giấy. Hãy viết một hàm trả về list các chữ số.",
        goal="Viết hàm digits(text) dùng comprehension, mật mã = tổng các chữ số. Mở cửa, tới cúp.",
        rows=DOOR_RIGHT,
        starter="def digits(text):\n    return []\n\nprint(digits(scroll))\nhero.move_right(2)\n",
        hints=["Duyệt từng ký tự, giữ ký tự .isdigit() và đổi sang int.", "Cộng list trả về bằng sum."],
        requires=["def", "listcomp"],
        extra_globals={"scroll": "x7y3z9"},
        door_code=19,
    ),
    Level(
        id="18-4",
        title="Lộ trình bậc thang",
        story=(
            "Ôn tập class và __iter__. Route(size) là lộ trình bậc thang lớn dần: "
            "bậc i gồm i lần \"right\" rồi một \"down\", với i từ 1 tới size."
        ),
        goal="Viết __iter__ cho Route, rồi cho hero follow Route(3) để tới cúp.",
        rows=GROWING_STAIRS,
        starter=(
            "class Route:\n"
            "    def __init__(self, size):\n"
            "        self.size = size\n"
            "\n"
            'hero.follow(["right", "down"])\n'
        ),
        hints=["Tạo list các hướng trong __iter__ bằng vòng lặp, rồi trả về iter(list).", "List nhân số: [\"right\"] * i."],
        requires=["class", "dunder:__iter__"],
    ),
    Level(
        id="18-5",
        title="Phòng bẫy số",
        story=(
            "candidates = [\"4\", \"x\", \"4\", \"7\", \"??\", \"2\"]. Một số chuỗi không phải số, và có số bị lặp. "
            "Mật mã = tổng các số KHÁC NHAU đọc được."
        ),
        goal="Đổi các chuỗi đọc được sang số (bỏ qua chuỗi hỏng), loại số trùng, mật mã = tổng.",
        rows=DOOR_DOWN,
        starter="values = []\nfor text in candidates:\n    values.append(int(text))\n",
        hints=["Bắt lỗi ValueError khi đổi kiểu.", "Dùng set để không cộng trùng."],
        requires=["try", "set"],
        extra_globals={"candidates": ["4", "x", "4", "7", "??", "2"]},
        door_code=13,
    ),
]

# ================================================================ GIAI ĐOẠN 4
PRACTICE[19] = [
    Level(
        id="19-3",
        title="Người giỏi nhất",
        story=(
            "players = [(\"An\", 7), (\"Bình\", 9), (\"Chi\", 5)]. max(ds, key=...) và sorted(ds, key=...) "
            "nhận một hàm cho biết so sánh theo cái gì - rất hợp với lambda."
        ),
        goal="Tìm người có điểm cao nhất bằng lambda, nhập TÊN người đó làm mật mã, tới cúp.",
        rows=DOOR_RIGHT,
        starter="print(sorted(players))\nhero.move_right(2)\n",
        hints=["sorted(players) đang xếp theo tên - cần xếp theo điểm.", "key=lambda p: ... lấy phần tử thứ hai của tuple."],
        requires=["lambda", "call:sorted or call:max"],
        extra_globals={"players": [("An", 7), ("Bình", 9), ("Chi", 5)]},
        door_code="Bình",
    ),
    Level(
        id="19-4",
        title="Lần rẽ đầu tiên",
        story=(
            "route = [\"right\", \"right\", \"down\", \"down\", \"right\"]. "
            "enumerate(ds) cho từng cặp (vị trí, phần tử), vị trí đếm từ 0."
        ),
        goal="Mật mã = vị trí của \"down\" ĐẦU TIÊN trong route. Mở cửa và tới cúp.",
        rows=DOOR_DOWN,
        starter="for step in route:\n    print(step)\n",
        hints=["Duyệt for i, step in enumerate(route).", "Gặp \"down\" đầu tiên thì ghi nhớ vị trí và dừng vòng lặp."],
        requires=["call:enumerate"],
        extra_globals={"route": ["right", "right", "down", "down", "right"]},
        door_code=2,
    ),
    Level(
        id="19-5",
        title="Dự báo thời tiết",
        story=(
            "temps = [22, 25, 31, 28] là nhiệt độ các ngày. any(...) đúng nếu CÓ ÍT NHẤT MỘT phần tử đúng, "
            "all(...) đúng nếu TẤT CẢ đều đúng."
        ),
        goal="Nếu có ngày nào trên 30 độ thì nói \"Nóng\", không thì \"Mát\". Rồi tới cúp.",
        rows=corridor("@..G.E"),
        starter='if temps[0] > 30:\n    hero.say("Nóng")\nelse:\n    hero.say("Mát")\nhero.move_right(5)\n',
        hints=["Đang chỉ xét ngày đầu tiên.", "Đưa một biểu thức t > 30 cho mọi t vào any(...)."],
        requires=["call:any or call:all"],
        extra_globals={"temps": [22, 25, 31, 28]},
        say_contains="Nóng",
    ),
]

PRACTICE[20] = [
    Level(
        id="20-3",
        title="Đếm ngọc trong thư",
        story="letter = \"Ngọc: 3 đỏ, 5 xanh, 2 vàng\". re.findall trả về list MỌI chỗ khớp mẫu.",
        goal="Lấy mọi con số trong thư, mật mã = tổng của chúng. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter='import re\nprint(re.search(r"\\d+", letter).group())\nhero.move_right(2)\n',
        hints=["re.search chỉ tìm chỗ đầu tiên.", "Kết quả findall là list chuỗi - đổi sang int trước khi cộng."],
        requires=["call:findall"],
        extra_globals={"letter": "Ngọc: 3 đỏ, 5 xanh, 2 vàng"},
        door_code=10,
    ),
    Level(
        id="20-4",
        title="Mã hợp lệ",
        story=(
            "codes = [\"AB-123\", \"X-1\", \"CD-456\", \"EF-78\"]. Mã hợp lệ gồm 2 chữ in hoa, dấu -, rồi đúng 3 chữ số. "
            "Mẫu: [A-Z]{2} là 2 chữ in hoa, \\d{3} là 3 chữ số. re.fullmatch khớp TOÀN BỘ chuỗi."
        ),
        goal="Đếm số mã hợp lệ, nhập làm mật mã, tới cúp.",
        rows=DOOR_DOWN,
        starter="import re\nprint(len(codes))\nhero.move_right(2)\nhero.move_down(1)\n",
        hints=["Ghép mẫu: [A-Z]{2}, dấu -, \\d{3}.", "fullmatch trả về None nếu không khớp - dùng được trong if."],
        requires=["call:fullmatch or call:match"],
        extra_globals={"codes": ["AB-123", "X-1", "CD-456", "EF-78"]},
        door_code=2,
    ),
    Level(
        id="20-5",
        title="Lệnh tác chiến XML",
        story=(
            "room_xml ghi vị trí từng quái và vũ khí cần dùng: <enemy x=\"..\" y=\"..\" weapon=\"..\"/>, "
            "cùng vị trí cổng <exit .../>. Lần này hãy đọc mọi thứ từ XML."
        ),
        goal="Đọc XML, hạ từng quái bằng vũ khí ghi trong thẻ, rồi tới cổng.",
        rows=WEAPON_ROOM,
        starter='import xml.etree.ElementTree as ET\nroot = ET.fromstring(room_xml)\nprint(len(root.findall("enemy")))\n',
        hints=["Mỗi thẻ enemy có get(\"x\"), get(\"y\"), get(\"weapon\").", "Toạ độ là chuỗi - đổi sang int."],
        requires=["import:xml"],
        extra_globals={
            "room_xml": (
                '<room><enemy x="4" y="1" weapon="hammer"/><enemy x="7" y="1" weapon="axe"/>'
                '<enemy x="5" y="3" weapon="bow"/><exit x="9" y="3"/></room>'
            ),
        },
        weapons=True,
        kill_all=True,
    ),
]

PRACTICE[21] = [
    Level(
        id="21-3",
        title="Máy nhân",
        story="make_multiplier(k) tạo ra một hàm nhân với k. Mật mã = 14 nhân 3, tính bằng hàm triple tạo từ make_multiplier(3).",
        goal="Viết closure make_multiplier, tạo hàm triple, dùng nó tính mật mã. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="def make_multiplier(k):\n    pass\n\nhero.move_right(2)\n",
        hints=["Bên trong tạo hàm nhận n và trả về n nhân k.", "Hàm ngoài trả hàm trong ra (không có ngoặc)."],
        requires=["closure"],
        door_code=42,
    ),
    Level(
        id="21-4",
        title="Bùa báo hiệu",
        story=(
            "Viết decorator announce: trước khi chạy hàm, hero nói \"Bắt đầu: \" + tên hàm. "
            "Tên của hàm f lấy bằng f.__name__."
        ),
        goal="Gắn @announce vào hàm hop, dùng hop để vượt cả 3 cái gai và tới cúp.",
        rows=SPIKE_HOPS,
        starter=(
            "def announce(func):\n"
            "    return func\n"
            "\n"
            "@announce\n"
            "def hop():\n"
            "    hero.move_up()\n"
            "    hero.move_right(2)\n"
            "    hero.move_down()\n"
            "\n"
            "hero.move_right(2)\n"
            "hop()\n"
        ),
        hints=["Bên trong announce, tạo hàm bọc: nói trước, rồi gọi func().", "Giữa các lần hop() đi phải 1 ô."],
        requires=["decorator"],
        say_contains="Bắt đầu: hop",
    ),
    Level(
        id="21-5",
        title="Bùa lặp lại",
        story=(
            "Decorator có tham số: @repeat(4) làm hàm chạy 4 lần. repeat(times) trả về một decorator - "
            "tức là 3 tầng hàm lồng nhau."
        ),
        goal="Viết repeat(times), gắn @repeat(4) vào hàm stair, gọi stair() MỘT lần để xuống hết cầu thang.",
        rows=STAIRS,
        starter=(
            "def repeat(times):\n"
            "    pass\n"
            "\n"
            "def stair():\n"
            "    hero.move_right()\n"
            "    hero.move_down()\n"
            "\n"
            "stair()\n"
        ),
        hints=[
            "Tầng ngoài nhận times, tầng giữa nhận func, tầng trong chạy func times lần.",
            "Mỗi tầng trả về hàm ở tầng ngay bên trong nó.",
        ],
        requires=["decorator", "closure"],
    ),
]

# ================================================================ GIAI ĐOẠN 5
PRACTICE[22] = [
    Level(
        id="22-3",
        title="Nhiệt độ trung bình",
        story="temps = [20, 22, 24, 26, 28]. Mảng NumPy có .mean() tính trung bình cộng.",
        goal="Mật mã = nhiệt độ trung bình (số nguyên). Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="import numpy as np\ndata = np.array(temps)\nprint(data.max())\n",
        hints=["Gọi .mean() trên mảng.", "Đổi kết quả sang int."],
        requires=["import:numpy"],
        extra_globals={"temps": [20, 22, 24, 26, 28]},
        door_code=24,
    ),
    Level(
        id="22-4",
        title="Lọc điểm cao",
        story=(
            "scores = [3, 7, 8, 2, 9, 6]. Với NumPy, arr > 5 tạo mảng True/False; "
            "arr[arr > 5] chỉ giữ các phần tử lớn hơn 5."
        ),
        goal="Mật mã = số điểm lớn hơn 5. Mở cửa và tới cúp.",
        rows=DOOR_DOWN,
        starter="import numpy as np\narr = np.array(scores)\nprint(arr > 5)\n",
        hints=["Dùng mảng True/False làm chỉ số để lọc.", "Đếm số phần tử còn lại."],
        requires=["import:numpy"],
        extra_globals={"scores": [3, 7, 8, 2, 9, 6]},
        door_code=4,
    ),
    Level(
        id="22-5",
        title="Ngày bán chạy",
        story=(
            "sales là bảng số hàng bán: mỗi hàng là một cửa hàng, mỗi cột là một ngày. "
            ".sum(axis=0) cộng theo cột; .argmax() cho VỊ TRÍ của số lớn nhất."
        ),
        goal="Mật mã = vị trí (đếm từ 0) của ngày bán được nhiều nhất. Mở cửa và tới cúp.",
        rows=DOOR_RIGHT,
        starter="import numpy as np\ntable = np.array(sales)\nprint(table.sum())\n",
        hints=["Cộng theo cột để có tổng mỗi ngày.", "argmax trả về vị trí - đổi sang int."],
        requires=["import:numpy", "call:argmax"],
        extra_globals={"sales": [[3, 5, 2], [4, 1, 6], [2, 7, 3]]},
        door_code=1,
    ),
]

PRACTICE[23] = [
    Level(
        id="23-3",
        title="Bọ tên biến",
        story="Code này báo NameError. Đọc thông báo lỗi: nó cho biết Python không biết tên nào.",
        goal="Sửa lỗi để hero tới cúp và nói \"Tới rồi\".",
        rows=corridor("@..G..E"),
        starter='steps = 6\nmessage = "Tới rồi"\nhero.move_right(step)\nhero.say(mesage)\n',
        hints=["So từng chữ của tên biến khi tạo và khi dùng.", "Có hai chỗ gõ sai tên."],
        requires=["assign"],
        say_contains="Tới rồi",
    ),
    Level(
        id="23-4",
        title="Bọ kiểu dữ liệu",
        story="Code này báo TypeError: dùng sai kiểu dữ liệu. Có 2 chỗ sai kiểu.",
        goal="Sửa lỗi để hero nói \"Có 1 ngọc\" và tới cúp.",
        rows=corridor("@.G.E"),
        starter='gems = len(hero.find_gems())\nhero.say("Có " + gems + " ngọc")\nhero.move_right("4")\n',
        hints=["Nối chuỗi với số phải đổi số sang chuỗi.", "Số bước phải là số, không phải chuỗi."],
        requires=["call:str"],
        say_contains="Có 1 ngọc",
    ),
    Level(
        id="23-5",
        title="Bọ lặp vô hạn",
        story="Chương trình này không bao giờ dừng: điều kiện của while luôn đúng. Hãy tìm vì sao.",
        goal="Sửa vòng lặp để hero đi đúng 5 bước, nhặt hết ngọc và tới cúp.",
        rows=corridor("@GGGGE"),
        starter="count = 0\nwhile count < 5:\n    hero.move_right()\n",
        hints=["Giá trị của count có bao giờ thay đổi không?", "Mỗi vòng lặp cần tăng count lên."],
        requires=["while"],
    ),
]

# ================================================================ BÀI 6: THỬ THÁCH VẬT THỂ MỚI
# Ký hiệu thêm: O thùng gỗ, Q thùng có ngọc, k chìa khoá, L cửa khoá, C rương báu.
CHEST_AND_DOOR = [
    "#######",
    "#C#####",
    "#@.D.E#",
    "#######",
]
CHALLENGES: dict[int, Level] = {
    1: Level(
        id="1-6",
        title="Thử thách: Thùng gỗ",
        story="Thùng gỗ chắn ngang đường! hero.attack(\"right\") đập vỡ thùng ở bên phải.",
        goal="Đập vỡ thùng gỗ, nhặt ngọc và tới cúp.",
        rows=corridor("@.O..GE"),
        starter="hero.move_right(1)\n# thùng gỗ chắn đường!\n",
        hints=["Đứng sát thùng rồi tấn công về phía thùng.", "Thùng vỡ thì đường thông - đi tiếp tới cúp."],
        requires=["call:attack"],
    ),
    2: Level(
        id="2-6",
        title="Thử thách: Chìa khoá",
        story=(
            "Đi qua chìa khoá (k) là nhặt được. Cửa khoá (L) mở bằng hero.unlock(\"right\") khi đã có chìa. "
            "Hãy dùng một biến steps cho cả hai đoạn đường."
        ),
        goal="Nhặt chìa, mở cửa khoá, tới cúp - dùng biến steps.",
        rows=corridor("@.k.L.GE"),
        starter="steps = 1\nhero.move_right(steps)\n",
        hints=["Đoạn đầu dài 3 ô (đi qua chìa).", "Đoạn sau dài hơn đoạn đầu 1 ô: steps + 1."],
        requires=["assign", "call:unlock"],
    ),
    3: Level(
        id="3-6",
        title="Thử thách: Rương bí mật",
        story="hero.look(...) còn nhận ra \"box\" (thùng) và \"chest\" (rương). hero.open_chest(\"up\") mở rương phía trên.",
        goal="Ở ngã ba: nếu trên có rương thì mở; nếu phải có thùng thì đập. Rồi tới cúp.",
        rows=[
            "########",
            "###C####",
            "#@..O.E#",
            "########",
        ],
        starter='hero.move_right(2)\nif hero.look("up") == "chest":\n    pass\n',
        hints=["Thay pass bằng lệnh mở rương phía trên.", "Viết thêm một if cho thùng gỗ bên phải."],
        requires=["if"],
        need_chests=1,
    ),
    4: Level(
        id="4-6",
        title="Thử thách: Hàng thùng",
        story="Năm cái thùng xếp thành hàng. Thùng có dấu X (Q) chứa ngọc - đập vỡ là ngọc rơi ra, đi qua để nhặt.",
        goal="Dùng vòng lặp: đập thùng rồi bước lên, lặp lại cho hết hàng. Tới cúp.",
        rows=corridor("@OQOQOE"),
        starter='hero.attack("right")\nhero.move_right()\n',
        hints=["Hai lệnh trong code ban đầu là một vòng - lặp nó lại.", "Đếm số thùng; sau vòng lặp còn thiếu một bước."],
        requires=["for"],
    ),
    5: Level(
        id="5-6",
        title="Thử thách: Cửa đôi",
        story="Có doors = \"2\" cặp chìa - cửa nối tiếp nhau. Mỗi lượt: nhặt chìa, mở cửa, bước qua.",
        goal="Lặp đúng số lượt (đổi doors sang số), mở hết cửa khoá, tới cúp.",
        rows=corridor("@kLkLE"),
        starter='# doors = "2"\nfor i in range(doors):\n    hero.move_right()\n',
        hints=["range cần số nguyên - đổi doors bằng int().", "Mỗi lượt: bước lên nhặt chìa, mở cửa bên phải, bước qua cửa."],
        requires=["call:int"],
        extra_globals={"doors": "2"},
    ),
    6: Level(
        id="6-6",
        title="Thử thách: Chiêu phá thùng",
        story="Ba cái thùng cách đều nhau. Viết một hàm làm trọn một lượt phá thùng để gọi lại nhiều lần.",
        goal="Viết hàm (ví dụ smash) gồm: bước lên, đập thùng, bước vào chỗ thùng vừa vỡ. Dùng nó 3 lần rồi tới cúp.",
        rows=corridor("@.O.O.O.E"),
        starter="def smash():\n    hero.move_right()\n\nsmash()\n",
        hints=["Thêm lệnh đập thùng và một bước nữa vào hàm.", "Sau 3 lần gọi hàm, còn 2 ô nữa tới cúp."],
        requires=["def"],
    ),
    7: Level(
        id="7-6",
        title="Thử thách: Thư trong rương",
        story="note = \"Mật mã ở cuối thư: 42\". Mở rương phía trên, rồi cắt lấy 2 ký tự cuối của note làm mật mã.",
        goal="Mở rương, cắt chuỗi lấy mật mã, mở cửa và tới cúp.",
        rows=CHEST_AND_DOOR,
        starter='# note = "Mật mã ở cuối thư: 42"\nprint(note[0])\n',
        hints=["Chỉ số âm đếm từ cuối: [-2:] lấy 2 ký tự cuối.", "Đứng cạnh cửa rồi mới nhập mật mã."],
        requires=["slice"],
        extra_globals={"note": "Mật mã ở cuối thư: 42"},
        door_code=42,
        need_chests=1,
    ),
    8: Level(
        id="8-6",
        title="Thử thách: Danh sách thùng",
        story=(
            "hero.find_objects(\"box\") trả về list toạ độ các thùng. Đứng bên TRÁI mỗi thùng rồi đập. "
            "Ngọc rơi ra phải đi nhặt hết."
        ),
        goal="Duyệt list thùng để đập hết, nhặt hết ngọc rơi ra, rồi tới cổng.",
        rows=[
            "#########",
            "#@..Q...#",
            "#.......#",
            "#..Q..O.#",
            "#......E#",
            "#########",
        ],
        starter='boxes = hero.find_objects("box")\nprint(boxes)\n',
        hints=["Ô bên trái thùng có toạ độ x nhỏ hơn 1.", "Đập xong hết thùng mới tìm lại danh sách ngọc."],
        requires=["for", "call:find_objects"],
    ),
    9: Level(
        id="9-6",
        title="Thử thách: Sổ kế hoạch",
        story="plan là dict: hướng → vật ở hướng đó (\"chest\" hoặc \"box\"). Duyệt plan.items() để xử lý từng hướng.",
        goal="Mở hết rương, đập thùng theo plan, rồi tới cúp.",
        rows=[
            "#######",
            "##C####",
            "#.@O.E#",
            "##C####",
            "#######",
        ],
        starter="for direction in plan:\n    print(direction)\n",
        hints=["for direction, thing in plan.items() cho cả hướng lẫn vật.", "Rương thì mở, thùng thì đập."],
        requires=["for", "call:items"],
        extra_globals={"plan": {"up": "chest", "down": "chest", "right": "box"}},
        need_chests=2,
    ),
    10: Level(
        id="10-6",
        title="Thử thách: Ba rương báu",
        story="Dùng hero.scan() và comprehension để tìm toạ độ mọi ô \"chest\". Mở rương từ ô ngay bên dưới nó.",
        goal="Tìm ba rương bằng comprehension, mở hết, rồi tới cổng.",
        rows=[
            "#########",
            "#.C.C.C.#",
            "#@......#",
            "#......E#",
            "#########",
        ],
        starter="grid = hero.scan()\nprint(grid[1])\n",
        hints=["Giữ lại (x, y) khi ô là \"chest\".", "Đi tới (x, y + 1) rồi mở rương hướng \"up\"."],
        requires=["listcomp", "call:scan"],
        need_chests=3,
    ),
    11: Level(
        id="11-6",
        title="Thử thách: Chỉ đập thùng",
        story="breakable = {\"box\"} là tập những thứ được phép đập. Đi dọc hành lang: gặp thứ trong tập thì đập, không thì bước.",
        goal="Dùng toán tử in với tập breakable để dọn đường tới cúp.",
        rows=corridor("@.O.QO.E"),
        starter='while hero.look("right") != "exit":\n    hero.move_right()\n',
        hints=["Trong vòng lặp, kiểm tra hero.look(\"right\") có nằm trong breakable không.", "Sau vòng lặp, bước thêm 1 ô vào cổng."],
        requires=["membership", "while"],
        extra_globals={"breakable": {"box"}},
    ),
    12: Level(
        id="12-6",
        title="Thử thách: Chìa và căn bậc hai",
        story="Nhặt chìa để qua cửa khoá. Cửa mật mã cần phần nguyên căn bậc hai của area = 50.",
        goal="Nhặt chìa, mở cửa khoá, nhập mật mã int(math.sqrt(area)), tới cúp.",
        rows=corridor("@k.L.D.GE"),
        starter="import math\nprint(math.sqrt(4))\n",
        hints=["Chìa ở ngay ô thứ nhất bên phải - đi 2 ô là tới sát cửa khoá.", "math.sqrt(50) ≈ 7.07 - chỉ lấy phần nguyên."],
        requires=["import:math", "call:unlock"],
        extra_globals={"area": 50},
        door_code=7,
    ),
    13: Level(
        id="13-6",
        title="Thử thách: Khoá ba màu",
        story=(
            "Đập thùng, rồi mở khoá màu: colors = [\"đỏ\", \"xanh\", \"vàng\"] phải xếp đúng thứ tự (dùng permutations và try_code). "
            "Qua cửa xong mở rương phía trên rồi tới cúp."
        ),
        goal="Đập thùng, thử hoán vị tới khi cửa mở, mở rương, tới cúp.",
        rows=[
            "########",
            "#####C##",
            "#@O.D.E#",
            "########",
        ],
        starter="from itertools import permutations\nhero.attack(\"right\")\n",
        hints=["Sau khi đập thùng, bước 2 ô là tới sát cửa.", "Mở được cửa thì dừng vòng lặp; rương nằm trên ô ngay sau cửa."],
        requires=["call:permutations"],
        extra_globals={"colors": ["đỏ", "xanh", "vàng"]},
        door_code=("vàng", "đỏ", "xanh"),
        need_chests=1,
    ),
    14: Level(
        id="14-6",
        title="Thử thách: Kiểm kê thùng",
        story="Mật mã = số thùng gỗ trong phòng. Dùng hero.scan() rồi Counter đếm mọi ô của bản đồ.",
        goal="Đếm số ô \"box\" bằng Counter, nhập làm mật mã, tới cúp.",
        rows=[
            "#########",
            "#O.O..O.#",
            "#@..D.GE#",
            "#.O.....#",
            "#########",
        ],
        starter="from collections import Counter\ngrid = hero.scan()\nprint(grid[1])\n",
        hints=["Trải phẳng bản đồ rồi đưa vào Counter.", "Tra kết quả Counter với khoá \"box\"."],
        requires=["call:Counter", "call:scan"],
        door_code=4,
    ),
    15: Level(
        id="15-6",
        title="Thử thách: Rương Giáng sinh",
        story="Mở rương phía trên. Mật mã cửa = thứ trong tuần (weekday) của day = \"2026-12-25\".",
        goal="Mở rương, tính weekday() của ngày Giáng sinh, mở cửa, tới cúp.",
        rows=CHEST_AND_DOOR,
        starter="from datetime import date\nprint(day)\n",
        hints=["Đổi day sang date bằng fromisoformat.", "Mở rương trước, rồi đi 1 ô tới sát cửa."],
        requires=["import:datetime"],
        extra_globals={"day": "2026-12-25"},
        door_code=4,
        need_chests=1,
    ),
    16: Level(
        id="16-6",
        title="Thử thách: Quên chìa",
        story=(
            "hero.unlock khi chưa có chìa sẽ báo lỗi ValueError. Chìa nằm ngay SAU LƯNG hero. "
            "Hãy thử mở cửa, nếu lỗi thì quay lại lấy chìa rồi mở lại."
        ),
        goal="Bắt lỗi ValueError khi mở cửa không có chìa, lấy chìa, mở cửa, tới cúp.",
        rows=corridor("k@L.GE"),
        starter='hero.unlock("right")\nhero.move_right(4)\n',
        hints=["Bọc lệnh unlock đầu tiên trong try.", "Trong except: lùi 1 ô lấy chìa, quay lại, mở cửa."],
        requires=["try", "except:ValueError"],
    ),
    17: Level(
        id="17-6",
        title="Thử thách: Nhà thám hiểm",
        story="Viết class Explorer có phương thức open(direction): mở rương ở hướng đó và đếm số rương đã mở.",
        goal="Dùng Explorer mở 2 rương (trên và trái), nói \"Mở 2 rương\", rồi tới cúp.",
        rows=[
            "#######",
            "###C###",
            "##C@.E#",
            "#######",
        ],
        starter="class Explorer:\n    def __init__(self):\n        self.opened = 0\n",
        hints=["Phương thức open(self, direction) gọi hero.open_chest rồi tăng self.opened.", "Nói số rương bằng f-string với e.opened."],
        requires=["class", "method"],
        need_chests=2,
        say_contains="Mở 2 rương",
    ),
    18: Level(
        id="18-6",
        title="Thử thách: Đường kho báu",
        story=(
            "Hành lang có thùng, chìa, quái, cửa khoá; một rương nằm phía dưới đường đi. "
            "Viết một vòng lặp tự xử lý mọi thứ: nhìn sang phải để quyết định làm gì, và mở rương nếu thấy ở dưới."
        ),
        goal="Dùng vòng lặp while + if để vượt hết chướng ngại, mở rương, tới cúp.",
        rows=[
            "#############",
            "#@.O.k.r.L.E#",
            "##########C##",
        ],
        starter='while hero.look("right") != "exit":\n    hero.move_right()\n',
        hints=[
            "Thùng hoặc quái thì tấn công, cửa khoá thì unlock, còn lại thì bước.",
            "Sau mỗi bước, kiểm tra phía dưới có rương không.",
        ],
        requires=["while", "if"],
        need_chests=1,
    ),
    19: Level(
        id="19-6",
        title="Thử thách: Mở rương có thứ tự",
        story="hero.find_objects(\"chest\") cho list rương. Dùng sorted với key=lambda để xếp rương theo cột x từ trái sang phải.",
        goal="Xếp rương bằng sorted + lambda, mở từng rương từ ô ngay dưới nó, rồi tới cổng.",
        rows=[
            "#########",
            "#C..C..C#",
            "#.......#",
            "#@.....E#",
            "#########",
        ],
        starter='chests = hero.find_objects("chest")\nprint(chests)\n',
        hints=["key=lambda c: c[\"x\"]", "Đi tới (x, y + 1) rồi mở rương hướng \"up\"."],
        requires=["lambda", "call:sorted"],
        need_chests=3,
    ),
    20: Level(
        id="20-6",
        title="Thử thách: Mật thư chỉ đường",
        story=(
            "letter = \"Rương ở hướng up, cửa mã 7314.\" Dùng regex lấy hướng (chữ sau \"hướng \") và mật mã (số sau \"mã \")."
        ),
        goal="Đọc mật thư bằng regex, mở rương đúng hướng, mở cửa, tới cúp.",
        rows=CHEST_AND_DOOR,
        starter="import re\nprint(letter)\n",
        hints=["\\w+ khớp một từ, \\d+ khớp một số.", "Đặt phần cần lấy trong ( ) rồi dùng .group(1)."],
        requires=["import:re"],
        extra_globals={"letter": "Rương ở hướng up, cửa mã 7314."},
        door_code=7314,
        need_chests=1,
    ),
    21: Level(
        id="21-6",
        title="Thử thách: Bùa mở rương",
        story="Viết closure make_opener(direction) trả về một hàm mở rương ở hướng đó. Tạo bùa cho hướng up và left.",
        goal="Dùng các hàm tạo từ make_opener mở 2 rương, đập thùng, tới cúp.",
        rows=[
            "#######",
            "##C####",
            "#C@O.E#",
            "#######",
        ],
        starter="def make_opener(direction):\n    pass\n",
        hints=["Hàm bên trong không cần tham số - nó nhớ direction.", "Mở xong 2 rương thì đập thùng bên phải rồi đi 3 ô."],
        requires=["closure"],
        need_chests=2,
    ),
    22: Level(
        id="22-6",
        title="Thử thách: Rương nặng nhất",
        story="Mở rương phía trên. weights là bảng cân nặng các thỏi vàng; mật mã = số lớn nhất trong bảng (dùng NumPy).",
        goal="Mở rương, tìm max của mảng NumPy, mở cửa, tới cúp.",
        rows=CHEST_AND_DOOR,
        starter="import numpy as np\nprint(np.array(weights).shape)\n",
        hints=["Mảng NumPy có .max().", "Đổi kết quả sang int trước khi nhập."],
        requires=["import:numpy"],
        extra_globals={"weights": [[3, 8], [6, 2]]},
        door_code=8,
        need_chests=1,
    ),
    23: Level(
        id="23-6",
        title="Thử thách: Bọ vật thể",
        story="Code này có nhiều lỗi: sai thứ tự (mở cửa khi chưa có chìa), gõ sai tên lệnh, đánh sai hướng. Sửa hết!",
        goal="Nhặt chìa, mở rương bên dưới, mở cửa khoá, đập thùng và tới cúp.",
        rows=[
            "##########",
            "#@k.L.O.E#",
            "###C######",
        ],
        starter=(
            'hero.unlock("right")\n'
            "hero.move_right(2)\n"
            'hero.open_chests("down")\n'
            'hero.attack("left")\n'
            "hero.move_right(3)\n"
        ),
        hints=["Phải nhặt chìa trước khi unlock - để ý thứ tự các dòng.", "Tên lệnh đúng là open_chest; thùng nằm bên phải."],
        need_chests=1,
    ),
}
for _world_number, _challenge in CHALLENGES.items():
    PRACTICE[_world_number].append(_challenge)
