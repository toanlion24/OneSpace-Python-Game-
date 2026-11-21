# Khung chương trình Python Basic

Nguồn: roadmap.sh/python, nhánh **Learn the Basics** (trích từ PDF roadmap chính thức).
Dùng làm xương sống cho các màn chơi (kiểu CodeCombat: người chơi viết Python để điều khiển nhân vật).

## Các chủ đề gốc của roadmap

1. Basic Syntax
2. Variables and Data Types
3. Conditionals
4. Loops
5. Type Casting
6. Exceptions
7. Functions, Builtin Functions
8. Data Structures: Lists, Tuples, Sets, Dictionaries

## Đề xuất chia thành World / màn chơi

| World | Chủ đề roadmap | Khái niệm cần dạy | Ý tưởng màn chơi |
|---|---|---|---|
| 1. Khởi hành | Basic Syntax | Lệnh, thụt lề, comment, `print()`, gọi hàm có tham số | Gọi `hero.move_right()`, `hero.say("...")` để đi tới cổng |
| 2. Kho đồ | Variables and Data Types | Biến, `int`, `float`, `str`, `bool`, phép toán, nối chuỗi | Đếm vàng, lưu tên/máu/tốc độ của nhân vật |
| 3. Ngã rẽ | Conditionals | `if / elif / else`, so sánh, `and / or / not` | Gặp kẻ địch: đánh hay né; cửa chỉ mở khi đủ điều kiện |
| 4. Vòng lặp | Loops | `for`, `while`, `range()`, `break`, `continue` | Thu hết đồng xu trên đường, canh gác đến khi hết quái |
| 5. Biến hình | Type Casting | `int()`, `str()`, `float()`, `bool()` | Mật mã nhập vào là chuỗi, phải đổi sang số để mở khoá |
| 6. Bẫy | Exceptions | `try / except / finally`, `raise`, lỗi thường gặp | Qua bẫy: bắt lỗi để nhân vật không bị hạ gục |
| 7. Phép thuật | Functions, Builtin Functions | `def`, tham số, `return`, `len`, `sum`, `min`, `max`, `sorted`... | Tự viết "chiêu thức" tái sử dụng |
| 8. Ba lô | Lists, Tuples | Chỉ số, cắt lát, `append`, duyệt danh sách | Quản lý danh sách kẻ địch / vật phẩm |
| 9. Sổ tay | Sets, Dictionaries | Tập hợp, khoá-giá trị, duyệt dict | Tra cứu điểm yếu từng loại quái |
| 10. Boss | Tổng hợp | Kết hợp mọi thứ trên | Trận boss cần dùng vòng lặp + điều kiện + hàm + dict |

## Nguyên tắc thiết kế màn

- Mỗi màn dạy **một** khái niệm mới, lặp lại các khái niệm cũ ở màn sau.
- Chuỗi mỗi World: giới thiệu → luyện tập → thử thách → boss nhỏ.
- Có gợi ý theo bậc và lời giải mẫu; báo lỗi bằng tiếng Việt dễ hiểu.
- Kiểm tra đúng/sai bằng kết quả trong game (đã thu đủ vàng, đã qua cổng...) và giới hạn số dòng/số bước khi cần.

## Chủ đề nâng cao (ngoài phạm vi Basic, để dành sau)

OOP (Classes, Inheritance), Modules, List Comprehensions, Lambdas, Decorators, Iterators, Regular Expressions, Typing, Concurrency, Testing, Package Managers.
