"""Phần thưởng: sao, xu, cấp bậc, rương báu cuối World, cửa hàng vật phẩm.

Pure logic (no pygame) so it can be tested directly.

Mỗi màn có 3 sao:
  1. Qua màn.
  2. Không mất máu.
  3. Code gọn: số dòng code không vượt quá PAR của màn.
Mỗi sao MỚI đạt được thưởng xu; qua đủ 5 màn một World thì mở rương báu (huy hiệu + xu).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .engine import Level, RunResult
from .par import PAR

STAR_COINS = 10
WORLD_CHEST_COINS = 50
# Xu trong mỗi rương báu mở được TRONG màn (chỉ tính lần đầu).
LOOT_COINS = 5
DEFAULT_SKIN = "skin1"

RANKS: list[tuple[int, str]] = [
    (0, "Tân binh"),
    (15, "Học việc"),
    (45, "Hiệp sĩ code"),
    (90, "Chiến binh thuật toán"),
    (160, "Pháp sư Python"),
    (260, "Huyền thoại OneSpace"),
]


@dataclass(frozen=True)
class ShopItem:
    id: str
    name: str
    description: str
    price: int
    kind: str  # "skin", "heart", "shield"
    skin_number: int = 1
    requires: str | None = None


SHOP_ITEMS: list[ShopItem] = [
    ShopItem("skin1", "Bạn Nhỏ", "Nhân vật mặc định.", 0, "skin", skin_number=1),
    ShopItem("skin2", "Rô-bốt Vàng", "Nhân vật rô-bốt tinh nghịch.", 120, "skin", skin_number=2),
    ShopItem("skin3", "Cáo Lửa", "Nhân vật cáo nhanh nhẹn.", 220, "skin", skin_number=3),
    ShopItem("heart1", "Tim thêm I", "+1 máu tối đa ở các màn thường.", 150, "heart"),
    ShopItem("heart2", "Tim thêm II", "+1 máu tối đa nữa (cần Tim thêm I).", 300, "heart", requires="heart1"),
    ShopItem("shield", "Khiên gỗ", "Đỡ giúp đòn đầu tiên trong mỗi màn thường.", 250, "shield"),
]
ITEMS_BY_ID: dict[str, ShopItem] = {item.id: item for item in SHOP_ITEMS}


@dataclass
class RewardSummary:
    stars: tuple[bool, bool, bool]
    new_stars: int
    coins: int
    chest_world: int | None = None
    loot_coins: int = 0
    old_rank: str = ""
    new_rank: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def rank_up(self) -> bool:
        return self.old_rank != self.new_rank


def par_for(level_id: str) -> int:
    return PAR.get(level_id, 99)


def star_flags(result: RunResult, level_id: str) -> tuple[bool, bool, bool]:
    won = result.won
    return (won, won and result.damage_taken == 0, won and result.code_lines <= par_for(level_id))


def star_goals(level_id: str) -> list[str]:
    return ["Qua màn", "Không mất máu", f"Code gọn: tối đa {par_for(level_id)} dòng"]


def rank_for(total_stars: int) -> tuple[str, int | None]:
    """(rank name, stars needed for the next rank or None at the top)."""
    name = RANKS[0][1]
    next_threshold: int | None = None
    for threshold, rank_name in RANKS:
        if total_stars >= threshold:
            name = rank_name
        elif next_threshold is None:
            next_threshold = threshold
    return name, next_threshold


def total_stars(progress: object) -> int:
    return sum(getattr(progress, "stars", {}).values())


def apply_win(progress: object, level: Level, world_levels: list[Level], world_number: int,
              flags: tuple[bool, bool, bool], chests_opened: int = 0) -> RewardSummary:
    """Record a win: keep the best stars, pay coins for NEW stars and open the world chest once."""
    stars: dict[str, int] = progress.stars  # type: ignore[attr-defined]
    earned = sum(flags)
    previous = stars.get(level.id, 0)
    old_rank = rank_for(total_stars(progress))[0]
    new_stars = max(0, earned - previous)
    stars[level.id] = max(previous, earned)
    progress.completed.add(level.id)  # type: ignore[attr-defined]
    coins = new_stars * STAR_COINS
    loot: dict[str, int] = progress.loot  # type: ignore[attr-defined]
    new_loot = max(0, chests_opened - loot.get(level.id, 0))
    loot[level.id] = max(loot.get(level.id, 0), chests_opened)
    loot_coins = new_loot * LOOT_COINS
    coins += loot_coins

    chest_world = None
    completed = progress.completed  # type: ignore[attr-defined]
    chests: set[int] = progress.chests  # type: ignore[attr-defined]
    if world_number not in chests and all(lv.id in completed for lv in world_levels):
        chests.add(world_number)
        coins += WORLD_CHEST_COINS
        chest_world = world_number

    progress.coins += coins  # type: ignore[attr-defined]
    new_rank = rank_for(total_stars(progress))[0]
    return RewardSummary(flags, new_stars, coins, chest_world, loot_coins, old_rank, new_rank)


# ---------------------------------------------------------------- shop
def bonus_hp(progress: object) -> int:
    owned: set[str] = progress.owned  # type: ignore[attr-defined]
    return sum(1 for item_id in owned if ITEMS_BY_ID.get(item_id, SHOP_ITEMS[0]).kind == "heart")


def has_shield(progress: object) -> bool:
    return "shield" in progress.owned  # type: ignore[attr-defined]


def can_buy(progress: object, item: ShopItem) -> tuple[bool, str]:
    owned: set[str] = progress.owned  # type: ignore[attr-defined]
    if item.id in owned or item.price == 0:
        return False, "Đã có"
    if item.requires and item.requires not in owned:
        return False, f"Cần {ITEMS_BY_ID[item.requires].name}"
    if progress.coins < item.price:  # type: ignore[attr-defined]
        return False, f"Thiếu {item.price - progress.coins} xu"  # type: ignore[attr-defined]
    return True, ""


def buy(progress: object, item: ShopItem) -> bool:
    ok, _ = can_buy(progress, item)
    if not ok:
        return False
    progress.coins -= item.price  # type: ignore[attr-defined]
    progress.owned.add(item.id)  # type: ignore[attr-defined]
    if item.kind == "skin":
        progress.skin = item.id  # type: ignore[attr-defined]
    return True


def equip_skin(progress: object, item_id: str) -> bool:
    item = ITEMS_BY_ID.get(item_id)
    if item is None or item.kind != "skin":
        return False
    if item.price and item_id not in progress.owned:  # type: ignore[attr-defined]
        return False
    progress.skin = item_id  # type: ignore[attr-defined]
    return True


def skin_number(progress: object) -> int:
    item = ITEMS_BY_ID.get(getattr(progress, "skin", DEFAULT_SKIN), SHOP_ITEMS[0])
    return item.skin_number
