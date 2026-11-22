"""Cửa hàng & Bộ sưu tập: badges, rank, coins and the item shop."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

from .hud import STAGE_COLORS, draw_coin, draw_heart, draw_medal, draw_shield, draw_star
from .levels import WORLDS, all_levels
from .rewards import (
    RANKS,
    SHOP_ITEMS,
    ShopItem,
    buy,
    can_buy,
    equip_skin,
    rank_for,
    total_stars,
)

if TYPE_CHECKING:
    from .game import App

COLOR_TEXT = (230, 232, 240)
COLOR_MUTED = (150, 156, 180)
COLOR_ACCENT = (255, 196, 64)
COLOR_GOOD = (90, 220, 120)
PANEL = pygame.Rect(40, 20, 1200, 690)
SHOP_X = 700
ITEM_HEIGHT = 92


class StoreView:
    def __init__(self, app: App) -> None:
        self.app = app
        self.buttons: list[Any] = []

    # ------------------------------------------------------------ actions
    def build(self) -> None:
        make_button = self.app.make_button
        progress = self.app.progress
        self.buttons = [make_button(pygame.Rect(64, 36, 110, 38), "← Menu", self.app.go_menu)]
        for index, item in enumerate(SHOP_ITEMS):
            rect = pygame.Rect(PANEL.right - 150, 130 + index * ITEM_HEIGHT + 24, 120, 40)
            label, color, action = self._button_for(item, progress)
            self.buttons.append(make_button(rect, label, action, color))

    def _button_for(self, item: ShopItem, progress: Any) -> tuple[str, tuple[int, int, int], Any]:
        owned = item.price == 0 or item.id in progress.owned
        if item.kind == "skin" and owned:
            if progress.skin == item.id:
                return "Đang dùng", (46, 120, 90), lambda: None
            return "Dùng", (70, 80, 120), lambda item_id=item.id: self._equip(item_id)
        if owned:
            return "Đã có", (46, 120, 90), lambda: None
        ok, _ = can_buy(progress, item)
        color = (150, 110, 40) if ok else (64, 66, 86)
        return f"Mua {item.price}", color, lambda chosen=item: self._buy(chosen)

    def _buy(self, item: ShopItem) -> None:
        ok, reason = can_buy(self.app.progress, item)
        if not ok:
            self.app.show_toast(f"Chưa mua được {item.name}: {reason}.")
            self.app.sound.play("fail")
            return
        buy(self.app.progress, item)
        self.app.progress.save()
        self.app.sound.play("coin")
        self.app.show_toast(f"Đã mua {item.name}!")
        self.build()

    def _equip(self, item_id: str) -> None:
        equip_skin(self.app.progress, item_id)
        self.app.progress.save()
        self.app.sound.play("click")
        self.build()

    def handle_event(self, event: pygame.event.Event) -> None:
        for button in self.buttons:
            if button.handle_event(event):
                return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.go_menu()

    # ------------------------------------------------------------ drawing
    def draw(self, surface: pygame.Surface) -> None:
        app = self.app
        progress = app.progress
        app.draw_background(5)
        pygame.draw.rect(surface, (22, 24, 34), PANEL, border_radius=10)
        pygame.draw.rect(surface, (60, 66, 92), PANEL, width=2, border_radius=10)

        title = app.font_title.render("Bộ sưu tập & Cửa hàng", True, COLOR_ACCENT)
        surface.blit(title, (196, 36))

        stars = total_stars(progress)
        max_stars = 3 * len(all_levels())
        rank, next_threshold = rank_for(stars)
        box = pygame.Rect(64, 96, SHOP_X - 90, 150)
        pygame.draw.rect(surface, (30, 34, 50), box, border_radius=10)
        surface.blit(app.font_bold.render(f"Cấp bậc: {rank}", True, COLOR_ACCENT), (box.x + 18, box.y + 14))
        draw_star(surface, (box.x + 30, box.y + 66), 13, True)
        surface.blit(app.font.render(f"{stars} / {max_stars} sao", True, COLOR_TEXT), (box.x + 52, box.y + 54))
        draw_coin(surface, (box.x + 250, box.y + 66), 12)
        surface.blit(app.font.render(f"{progress.coins} xu", True, COLOR_TEXT), (box.x + 270, box.y + 54))
        bar = pygame.Rect(box.x + 18, box.y + 100, box.width - 36, 16)
        pygame.draw.rect(surface, (50, 54, 72), bar, border_radius=8)
        if next_threshold is None:
            fill, caption = 1.0, "Cấp bậc cao nhất!"
        else:
            previous = max(threshold for threshold, _ in RANKS if threshold <= stars)
            fill = (stars - previous) / max(1, next_threshold - previous)
            caption = f"Còn {next_threshold - stars} sao để lên cấp tiếp theo"
        pygame.draw.rect(surface, COLOR_GOOD, (bar.x, bar.y, int(bar.width * fill), bar.height), border_radius=8)
        surface.blit(app.font_small.render(caption, True, COLOR_MUTED), (bar.x, bar.bottom + 4))

        surface.blit(app.font_bold.render("Huy hiệu World", True, COLOR_ACCENT), (64, 262))
        hint = app.font_small.render("Qua đủ 5 màn một World để mở rương và nhận huy hiệu.", True, COLOR_MUTED)
        surface.blit(hint, (64, 288))
        for index, world in enumerate(WORLDS):
            column, row = index % 8, index // 8
            center = (100 + column * 72, 360 + row * 104)
            earned = world.number in progress.chests
            draw_medal(surface, center, 26, str(world.number), app.font_bold, STAGE_COLORS[world.stage], earned)
            name = app._fit_text(world.title, 68)
            caption = app.font_small.render(name, True, COLOR_TEXT if earned else COLOR_MUTED)
            surface.blit(caption, caption.get_rect(midtop=(center[0], center[1] + 32)))

        surface.blit(app.font_bold.render("Cửa hàng", True, COLOR_ACCENT), (SHOP_X, 96))
        for index, item in enumerate(SHOP_ITEMS):
            row = pygame.Rect(SHOP_X, 130 + index * ITEM_HEIGHT, PANEL.right - SHOP_X - 20, ITEM_HEIGHT - 10)
            pygame.draw.rect(surface, (30, 34, 50), row, border_radius=10)
            icon_center = (row.x + 44, row.centery)
            if item.kind == "skin":
                frames = app.assets.hero_skin(item.skin_number)["idle"]
                image = frames[int(app.time * 10) % len(frames)]
                surface.blit(image, image.get_rect(center=icon_center))
            elif item.kind == "heart":
                draw_heart(surface, icon_center, 16, (255, 98, 98))
            else:
                draw_shield(surface, icon_center, 16)
            surface.blit(app.font_bold.render(item.name, True, COLOR_TEXT), (row.x + 90, row.y + 14))
            surface.blit(app.font_small.render(item.description, True, COLOR_MUTED), (row.x + 90, row.y + 44))

        for button in self.buttons:
            button.draw(surface, app.font_small if len(button.label) > 8 else app.font)
        app.draw_toast()
