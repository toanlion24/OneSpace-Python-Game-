"""Danh sách nhân vật: 3 nhân vật gốc của bộ đồ hoạ và các phiên bản đổi màu.

Pure data + colour maths (no pygame) so it can be tested directly.
Mỗi nhân vật có số `number` (lưu trong tiến độ dưới dạng "skin<number>").
Nhân vật có `price` = 0 được chọn ngay từ đầu; nhân vật hiếm mua bằng xu trong Cửa hàng.
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass

Color = tuple[int, int, int]

# Các màu được phép đổi của từng nhân vật gốc; da, mắt, viền giữ nguyên.
RECOLOR_PALETTES: dict[int, tuple[Color, ...]] = {
    # Bạn Nhỏ: tóc, cà vạt, áo vest.
    1: ((161, 71, 68), (132, 51, 70), (204, 48, 72), (156, 27, 77), (72, 71, 91)),
    # Rô-bốt: vỏ máy.
    2: ((225, 202, 51), (206, 139, 22), (247, 236, 138), (186, 87, 11)),
    # Cáo: bộ lông.
    3: ((210, 97, 47), (178, 46, 32), (230, 141, 65)),
}


@dataclass(frozen=True)
class HeroStyle:
    number: int
    name: str
    description: str
    base: int
    hue_shift: float = 0.0
    saturation: float = 1.0
    brightness: float = 1.0
    price: int = 0

    @property
    def item_id(self) -> str:
        return f"skin{self.number}"

    @property
    def is_recolored(self) -> bool:
        return (self.hue_shift, self.saturation, self.brightness) != (0.0, 1.0, 1.0)


HEROES: list[HeroStyle] = [
    HeroStyle(1, "Bạn Nhỏ", "Cậu học trò thích phiêu lưu.", 1),
    HeroStyle(2, "Rô-bốt Vàng", "Rô-bốt tinh nghịch.", 2),
    HeroStyle(3, "Cáo Lửa", "Cáo nhanh nhẹn.", 3),
    HeroStyle(4, "Bạn Tóc Xanh", "Tóc xanh biển, áo xanh.", 1, hue_shift=205),
    HeroStyle(5, "Bạn Tóc Tím", "Thích màu tím mộng mơ.", 1, hue_shift=270),
    HeroStyle(6, "Bạn Tóc Vàng", "Tóc vàng như nắng.", 1, hue_shift=45, brightness=1.35),
    HeroStyle(7, "Rô-bốt Lá", "Rô-bốt chạy bằng năng lượng xanh.", 2, hue_shift=55),
    HeroStyle(8, "Rô-bốt Biển", "Rô-bốt lặn biển.", 2, hue_shift=150),
    HeroStyle(9, "Rô-bốt Hồng", "Rô-bốt kẹo bông.", 2, hue_shift=270, saturation=0.8),
    HeroStyle(10, "Rô-bốt Bạc", "Vỏ thép sáng bóng.", 2, saturation=0.08, brightness=1.05),
    HeroStyle(11, "Cáo Tuyết", "Cáo trắng xứ lạnh.", 3, saturation=0.12, brightness=1.3),
    HeroStyle(12, "Cáo Đêm", "Cáo xanh tím ban đêm.", 3, hue_shift=225),
    HeroStyle(13, "Rô-bốt Bóng Đêm", "Nhân vật hiếm: vỏ đen huyền bí.", 2, saturation=0.25, brightness=0.45, price=150),
    HeroStyle(14, "Cáo Ngọc", "Nhân vật hiếm: lông xanh ngọc.", 3, hue_shift=150, price=200),
    HeroStyle(15, "Bạn Nhỏ Hoàng Kim", "Nhân vật hiếm: vest vàng óng.", 1, hue_shift=48, saturation=1.4,
              brightness=1.6, price=260),
]
HEROES_BY_NUMBER: dict[int, HeroStyle] = {hero.number: hero for hero in HEROES}
FREE_HEROES: list[HeroStyle] = [hero for hero in HEROES if hero.price == 0]
RARE_HEROES: list[HeroStyle] = [hero for hero in HEROES if hero.price > 0]


def recolor(color: Color, style: HeroStyle) -> Color:
    """Đổi một màu theo kiểu của nhân vật (xoay màu, chỉnh độ đậm và độ sáng)."""
    red, green, blue = (channel / 255 for channel in color)
    hue, saturation, value = colorsys.rgb_to_hsv(red, green, blue)
    hue = (hue + style.hue_shift / 360) % 1.0
    saturation = min(1.0, saturation * style.saturation)
    value = min(1.0, value * style.brightness)
    new_red, new_green, new_blue = colorsys.hsv_to_rgb(hue, saturation, value)
    return round(new_red * 255), round(new_green * 255), round(new_blue * 255)


def color_map(style: HeroStyle) -> dict[Color, Color]:
    """Bảng đổi màu cho sprite của nhân vật gốc."""
    if not style.is_recolored:
        return {}
    return {color: recolor(color, style) for color in RECOLOR_PALETTES[style.base]}
