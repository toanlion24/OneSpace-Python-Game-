"""Màn Chọn nhân vật: lưới nhân vật miễn phí + nhân vật hiếm mua bằng xu."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

from .display import mouse_pos
from .heroes import HEROES, HeroStyle
from .hud import draw_coin
from .rewards import ITEMS_BY_ID, buy, can_buy, equip_skin, skin_number
from .themes import THEMES

if TYPE_CHECKING:
    from .game import App

COLOR_TEXT = (230, 232, 240)
COLOR_MUTED = (150, 156, 180)
COLOR_ACCENT = (255, 196, 64)
COLOR_GOOD = (90, 220, 120)
PANEL = pygame.Rect(40, 20, 1200, 690)
GRID_LEFT = 64
GRID_TOP = 120
COLUMNS = 5
CARD_SIZE = (168, 176)
CARD_GAP = 12
PREVIEW = pygame.Rect(GRID_LEFT + COLUMNS * (CARD_SIZE[0] + CARD_GAP) + 8, GRID_TOP, 0, 552)
PREVIEW.width = PANEL.right - 24 - PREVIEW.x


def card_rect(index: int) -> pygame.Rect:
    row, column = divmod(index, COLUMNS)
    return pygame.Rect(
        GRID_LEFT + column * (CARD_SIZE[0] + CARD_GAP), GRID_TOP + row * (CARD_SIZE[1] + CARD_GAP), *CARD_SIZE
    )


def wrap_words(text: str, font: pygame.font.Font, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class HeroView:
    def __init__(self, app: App) -> None:
        self.app = app
        self.buttons: list[Any] = []
        self.first_time = False

    def build(self, first_time: bool = False) -> None:
        self.first_time = first_time
        make_button = self.app.make_button
        start_label = "Bắt đầu chơi →" if first_time else "Xong →"
        self.buttons = [
            make_button(pygame.Rect(PREVIEW.x + 20, PREVIEW.bottom - 64, PREVIEW.width - 40, 48), start_label,
                        self.finish, (46, 140, 86)),
        ]
        if not first_time:
            self.buttons.append(make_button(pygame.Rect(64, 36, 110, 38), "← Menu", self.finish))

    # ------------------------------------------------------------ actions
    def finish(self) -> None:
        self.app.progress.hero_picked = True
        self.app.progress.save()
        self.app.sound.play("click")
        self.app.go_menu()

    def _is_owned(self, hero: HeroStyle) -> bool:
        return hero.price == 0 or hero.item_id in self.app.progress.owned

    def choose(self, hero: HeroStyle) -> None:
        progress = self.app.progress
        if self._is_owned(hero):
            equip_skin(progress, hero.item_id)
            progress.save()
            self.app.sound.play("click")
            return
        item = ITEMS_BY_ID[hero.item_id]
        ok, reason = can_buy(progress, item)
        if not ok:
            self.app.show_toast(f"{hero.name} là nhân vật hiếm: {reason}. Qua màn để nhận thêm xu!")
            self.app.sound.play("fail")
            return
        buy(progress, item)
        progress.save()
        self.app.sound.play("coin")
        self.app.show_toast(f"Đã mở khoá {hero.name}!")

    def handle_event(self, event: pygame.event.Event) -> None:
        for button in self.buttons:
            if button.handle_event(event):
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, hero in enumerate(HEROES):
                if card_rect(index).collidepoint(event.pos):
                    self.choose(hero)
                    return
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.finish()

    # ------------------------------------------------------------ drawing
    def _hero_frame(self, number: int, state: str, scale: float) -> pygame.Surface:
        frames = self.app.assets.hero_skin(number)[state]
        frame = frames[int(self.app.time * 10) % len(frames)]
        if scale == 1:
            return frame
        size = (round(frame.get_width() * scale), round(frame.get_height() * scale))
        return pygame.transform.scale(frame, size)

    def draw(self, surface: pygame.Surface) -> None:
        app = self.app
        progress = app.progress
        app.draw_background(2)
        pygame.draw.rect(surface, (22, 24, 34), PANEL, border_radius=10)
        pygame.draw.rect(surface, (60, 66, 92), PANEL, width=2, border_radius=10)

        title_x = 64 if self.first_time else 196
        surface.blit(app.font_title.render("Chọn nhân vật của em", True, COLOR_ACCENT), (title_x, 34))
        subtitle = "Bấm vào một nhân vật để chọn. Nhân vật hiếm mở khoá bằng xu kiếm được khi qua màn."
        surface.blit(app.font_small.render(subtitle, True, COLOR_MUTED), (title_x, 76))
        draw_coin(surface, (PANEL.right - 120, 52), 11)
        surface.blit(app.font_bold.render(f"{progress.coins} xu", True, COLOR_TEXT), (PANEL.right - 102, 40))

        current = skin_number(progress)
        hovered_point = mouse_pos()
        for index, hero in enumerate(HEROES):
            rect = card_rect(index)
            selected = hero.number == current
            owned = self._is_owned(hero)
            base_color = (34, 40, 58) if owned else (28, 30, 42)
            if rect.collidepoint(hovered_point):
                base_color = tuple(channel + 16 for channel in base_color)
            pygame.draw.rect(surface, base_color, rect, border_radius=12)
            border = COLOR_GOOD if selected else (COLOR_ACCENT if hero.price else (60, 66, 92))
            pygame.draw.rect(surface, border, rect, width=3 if selected else 1, border_radius=12)

            image = self._hero_frame(hero.number, "idle" if selected else "jump", 1.4)
            if not owned:
                image = image.copy()
                image.fill((90, 90, 110), special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(image, image.get_rect(midbottom=(rect.centerx, rect.y + 120)))

            name = app._fit_text(hero.name, rect.width - 12)
            label = app.font_bold.render(name, True, COLOR_TEXT)
            surface.blit(label, label.get_rect(midtop=(rect.centerx, rect.y + 124)))
            if selected:
                status, status_color = "Đang dùng", COLOR_GOOD
            elif owned:
                status, status_color = "Miễn phí" if hero.price == 0 else "Đã mở khoá", COLOR_MUTED
            else:
                status, status_color = f"Hiếm · {hero.price} xu", COLOR_ACCENT
            status_text = app.font_small.render(status, True, status_color)
            surface.blit(status_text, status_text.get_rect(midtop=(rect.centerx, rect.y + 150)))

        self._draw_preview(surface, current)
        for button in self.buttons:
            button.draw(surface, app.font_bold)
        app.draw_toast()

    def _draw_preview(self, surface: pygame.Surface, current: int) -> None:
        app = self.app
        hero = next((style for style in HEROES if style.number == current), HEROES[0])
        pygame.draw.rect(surface, (30, 34, 50), PREVIEW, border_radius=12)
        # Nền xem trước đổi lần lượt qua các kiểu bản đồ.
        theme = THEMES[int(app.time / 3) % len(THEMES)]
        floor, wall = app.assets.theme_tiles(theme)
        caption = app.font_small.render(f"Bản đồ: {theme.name}", True, COLOR_MUTED)
        surface.blit(caption, caption.get_rect(midtop=(PREVIEW.centerx, PREVIEW.y + 14)))
        stage_top = PREVIEW.y + 250
        for x in range(PREVIEW.x + 12, PREVIEW.right - 12 - floor.get_width() + 1, floor.get_width()):
            surface.blit(wall, (x, stage_top + floor.get_height()))
            surface.blit(floor, (x, stage_top))
        state = "run" if int(app.time) % 4 < 2 else "idle"
        image = self._hero_frame(hero.number, state, 2.4)
        surface.blit(image, image.get_rect(midbottom=(PREVIEW.centerx, stage_top + floor.get_height() - 4)))
        name = app.font_title.render(hero.name, True, COLOR_ACCENT)
        surface.blit(name, name.get_rect(midtop=(PREVIEW.centerx, stage_top + 2 * floor.get_height() + 20)))
        lines = wrap_words(hero.description, app.font, PREVIEW.width - 40)
        for line_index, line in enumerate(lines):
            text = app.font.render(line, True, COLOR_TEXT)
            surface.blit(text, text.get_rect(midtop=(PREVIEW.centerx, stage_top + 2 * floor.get_height() + 64
                                                     + line_index * 24)))
