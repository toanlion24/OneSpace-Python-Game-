"""Kiểu bản đồ: mỗi World có nền đất, tường và hình nền riêng.

Pure data (no pygame). Ô gạch lấy từ `2 Locations/Tiles/Tileset.png` theo (cột, hàng),
mỗi ô 16x16; `multiply` / `add` nhuộm màu ô gạch để tạo thêm kiểu bản đồ.
"""

from __future__ import annotations

from dataclasses import dataclass

Color = tuple[int, int, int]
NO_TINT: Color = (255, 255, 255)
NO_ADD: Color = (0, 0, 0)


@dataclass(frozen=True)
class MapTheme:
    name: str
    floor: tuple[int, int]
    wall: tuple[int, int]
    floor_multiply: Color = NO_TINT
    wall_multiply: Color = NO_TINT
    add: Color = NO_ADD
    # Màu nền khung bản đồ (phía sau ô gạch).
    backdrop: Color = (24, 28, 40)


THEMES: list[MapTheme] = [
    MapTheme("Sân gạch", floor=(1, 1), wall=(1, 4)),
    MapTheme("Đồi đất đỏ", floor=(7, 1), wall=(7, 8), backdrop=(40, 26, 22)),
    MapTheme("Rừng rêu", floor=(1, 1), wall=(1, 5), floor_multiply=(170, 220, 150), wall_multiply=(150, 205, 140),
             backdrop=(20, 36, 26)),
    MapTheme("Phòng thép", floor=(12, 1), wall=(1, 5), backdrop=(30, 34, 44)),
    MapTheme("Sa mạc", floor=(7, 1), wall=(7, 8), floor_multiply=(255, 225, 150), wall_multiply=(255, 220, 160),
             add=(50, 40, 10), backdrop=(52, 42, 24)),
    MapTheme("Băng tuyết", floor=(12, 1), wall=(1, 4), floor_multiply=(210, 235, 255), wall_multiply=(170, 210, 255),
             add=(20, 26, 36), backdrop=(26, 36, 52)),
    MapTheme("Lâu đài tím", floor=(12, 1), wall=(1, 4), floor_multiply=(225, 205, 255), wall_multiply=(190, 150, 255),
             backdrop=(30, 20, 44)),
    MapTheme("Hang đêm", floor=(1, 1), wall=(1, 4), floor_multiply=(120, 120, 190), wall_multiply=(110, 110, 160),
             backdrop=(12, 12, 24)),
]

# World -> kiểu bản đồ: mỗi giai đoạn đổi cảnh, các World liền nhau không trùng kiểu.
WORLD_THEMES: dict[int, int] = {
    1: 0, 2: 2, 3: 1, 4: 0, 5: 2, 6: 3, 7: 4, 8: 1,
    9: 5, 10: 3, 11: 6, 12: 4, 13: 7, 14: 5, 15: 2, 16: 6,
    17: 3, 18: 7, 19: 1, 20: 5, 21: 6, 22: 4, 23: 7,
}


def theme_for_world(world_number: int) -> MapTheme:
    return THEMES[WORLD_THEMES.get(world_number, 0)]
