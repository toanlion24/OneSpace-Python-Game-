# Quy tắc dự án – AI Python Game OSP

Các quy tắc dưới đây là BẮT BUỘC, ưu tiên hơn thói quen mặc định của Claude. Áp dụng lặng lẽ, không cần nhắc là đang làm theo quy tắc.
Nếu hai quy tắc mâu thuẫn, theo quy tắc nằm ở mục cao hơn. Nếu một quy tắc không rõ, hỏi lại thay vì lờ đi.

## 1. Bảo mật (luôn áp dụng)

- KHÔNG đọc, hiển thị, sửa file `.env` / `.env.*` hay biến môi trường hệ thống (`os.environ`, `os.getenv` để in ra…).
- KHÔNG viết code làm lộ biến môi trường hoặc khoá bí mật (in ra log, ghi vào file, đẩy lên mạng).
- Nếu được hỏi về biến môi trường: giải thích là bị chặn vì lý do bảo mật.
- `mcp.json` thì ĐƯỢC đọc khi cần.

## 2. Quy trình làm việc

1. **Hiểu trước khi làm**: xác định ý định thật của yêu cầu, tác động phụ, trường hợp biên. Đọc các file liên quan, lần theo hàm / class tới định nghĩa và nơi dùng trước khi sửa.
2. **Đọc lại file trước khi sửa** nếu chưa đọc gần đây – người dùng có thể đã đổi file. Sửa thất bại thì đọc lại rồi mới sửa tiếp.
3. **Lập kế hoạch** cho việc nhiều bước, theo dõi bằng danh sách việc; đánh dấu xong ngay khi xong, mỗi lúc chỉ một việc đang làm, không làm lại việc đã xong.
4. **Thay đổi tối thiểu**: sửa nhỏ nhất mà đúng; không refactor hay sửa lan sang phần không liên quan.
5. **Tự làm tới cùng**: tiếp tục cho tới khi yêu cầu được giải quyết hẳn. Nói "sẽ làm X" thì làm X ngay trong lượt đó. Chỉ dừng hỏi khi thật sự bị chặn.
6. Không tự sửa file ngoài thư mục dự án nếu chưa được phép.
7. Không bịa kết quả công cụ / lệnh; không báo đã sửa nếu lệnh sửa chưa thành công.

## 3. Kiểm tra chất lượng code (bắt buộc)

- Sau MỌI thay đổi code: chạy linter (ưu tiên `ruff check`, nếu không có thì `python -m py_compile <file>`), sửa hết lỗi trước khi coi là xong.
- Có test thì chạy test (`pytest`); có thể chạy game thì chạy thử để chắc không crash lúc khởi động.
- Không lặp quá 3 lần sửa cùng một lỗi lint trên cùng một file – lần thứ 3 thì dừng, giải thích và hỏi người dùng.
- Lỗi khi chạy lệnh: đọc kỹ output → tìm nguyên nhân gốc (sai cú pháp? thiếu thư viện? sai đường dẫn?) → sửa code → chạy lại đúng lệnh đó. Không sửa mò.
- Không mở thêm terminal / tiến trình mới mỗi khi gặp lỗi; dùng lại terminal đang có. Gộp lệnh liên quan (`pip install -r requirements.txt && pytest`).

## 4. Code phải chạy được ngay

- Thêm đủ `import` và phụ thuộc cần thiết.
- Khi tạo dự án / module mới: có `requirements.txt` (ghi phiên bản) và `README.md` ngắn hướng dẫn chạy.
- Giao diện game: đẹp, hiện đại, dễ dùng.
- Không sinh chuỗi hash dài hay dữ liệu nhị phân trong code.

## 5. Phong cách code

Code sẽ được người đọc lại – ưu tiên rõ ràng, dễ hiểu.

**Đặt tên**
- Không dùng tên 1–2 ký tự (trừ biến đếm vòng lặp ngắn rất hiển nhiên).
- Hàm là động từ / cụm động từ, biến là danh từ / cụm danh từ; viết đủ từ, không viết tắt.
- Ví dụ: `n` → `num_enemies_alive`, `gen_pos` → `generate_spawn_position`, `for k, v in d.items()` → `for player_id, player in player_id_to_player.items()`.
- Theo PEP 8: `snake_case` cho hàm / biến, `PascalCase` cho class, `UPPER_SNAKE_CASE` cho hằng số.

**Kiểu dữ liệu**
- Ghi type hint cho chữ ký hàm và API công khai; không cần cho biến suy ra hiển nhiên.
- Tránh `Any` và ép kiểu không an toàn.

**Luồng điều khiển**
- Dùng guard clause / return sớm; xử lý lỗi và trường hợp biên trước.
- Không lồng quá 2–3 cấp.

**Comment**
- Không comment cho code hiển nhiên; comment giải thích "vì sao", không phải "làm gì".
- Không comment cuối dòng – đặt comment phía trên dòng code hoặc dùng docstring.
- Không để `TODO` – làm luôn.
- Không chèn comment kể lể hành động ("# now we update...").

**Định dạng**
- Theo phong cách code sẵn có; ưu tiên nhiều dòng hơn one-liner / biểu thức điều kiện phức tạp.
- Ngắt dòng dài; không format lại code không liên quan.

## 6. Giao tiếp với người dùng

- Trả lời ngắn: mặc định 3–6 câu hoặc ≤ 5 gạch đầu dòng.
- Không kể lể kiểu "Bây giờ tôi sẽ…", "Tiếp theo…"; không trình bày suy luận nội bộ.
- Khi người dùng yêu cầu sửa code: sửa bằng công cụ, không dán code ra chat trừ khi được yêu cầu.
- Tên file, thư mục, hàm, class đặt trong backtick. Không dán URL trần – dùng link markdown hoặc backtick.
- Dùng heading `##` / `###`, không dùng `#`. In đậm ý quan trọng.
- Nêu giả định rồi làm tiếp; không hỏi xác nhận kiểu "như vậy được không?" nếu không bị chặn.
- Cuối lượt: tóm tắt ngắn những gì đã thay đổi và tác động (≤ 5 gạch đầu dòng), không lặp lại kế hoạch.

## 7. Commit message (khi được yêu cầu commit)

- Một câu (tối đa hai) nêu **mục đích** của thay đổi, ví dụ: `Fix player collision with moving platforms`.
