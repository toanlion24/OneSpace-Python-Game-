"""Bảng "Nhạc nền": âm lượng nhạc / hiệu ứng theo phần trăm và chọn bài theo thể loại."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import pygame

from .music import TRACKS

if TYPE_CHECKING:
    from .game import App

COLOR_TEXT = (230, 232, 240)
COLOR_MUTED = (150, 156, 180)
COLOR_ACCENT = (255, 196, 64)
COLOR_TRACK = (60, 70, 105)
COLOR_SELECTED = (40, 150, 180)
PANEL = pygame.Rect(0, 0, 720, 640)
PANEL.center = (640, 360)
VOLUME_STEP = 10
AUTO_TRACK = -1


class Slider:
    """Thanh kéo 0-100%: bấm hoặc kéo chuột để chỉnh."""

    def __init__(self, rect: pygame.Rect, read: Callable[[], int], write: Callable[[int], None]) -> None:
        self.rect = rect
        self.read = read
        self.write = write
        self.dragging = False

    def _set_from_x(self, x: int) -> None:
        fraction = (x - self.rect.x) / self.rect.width
        self.write(round(max(0.0, min(1.0, fraction)) * 100))

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.inflate(16, 24).collidepoint(event.pos):
            self.dragging = True
            self._set_from_x(event.pos[0])
            return True
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_x(event.pos[0])
            return True
        if event.type == pygame.MOUSEBUTTONUP and self.dragging:
            self.dragging = False
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        value = self.read()
        pygame.draw.rect(surface, (50, 54, 72), self.rect, border_radius=self.rect.height // 2)
        filled = self.rect.copy()
        filled.width = round(self.rect.width * value / 100)
        if filled.width:
            pygame.draw.rect(surface, COLOR_SELECTED, filled, border_radius=self.rect.height // 2)
        knob_center = (self.rect.x + filled.width, self.rect.centery)
        pygame.draw.circle(surface, (255, 255, 255), knob_center, self.rect.height)
        pygame.draw.circle(surface, COLOR_SELECTED, knob_center, self.rect.height, width=3)


class MusicPanel:
    def __init__(self, app: App) -> None:
        self.app = app
        self.visible = False
        self.buttons: list[Any] = []
        left = PANEL.x + 220
        self.music_slider = Slider(
            pygame.Rect(left, PANEL.y + 112, 300, 12), lambda: self.app.progress.music_volume, app.set_music_volume
        )
        self.sfx_slider = Slider(
            pygame.Rect(left, PANEL.y + 162, 300, 12), lambda: self.app.progress.sfx_volume, app.set_sfx_volume
        )

    # ------------------------------------------------------------ actions
    def open(self) -> None:
        self.visible = True
        self.build()
        self.app.sound.play("click")

    def close(self) -> None:
        self.visible = False
        self.app.progress.save()
        self.app.build_music_buttons()

    def build(self) -> None:
        make_button = self.app.make_button
        progress = self.app.progress
        right = self.music_slider.rect.right
        self.buttons = [
            make_button(pygame.Rect(right + 24, PANEL.y + 98, 40, 40), "−",
                        lambda: self.app.set_music_volume(progress.music_volume - VOLUME_STEP)),
            make_button(pygame.Rect(right + 70, PANEL.y + 98, 40, 40), "+",
                        lambda: self.app.set_music_volume(progress.music_volume + VOLUME_STEP)),
            make_button(pygame.Rect(right + 24, PANEL.y + 148, 40, 40), "−",
                        lambda: self.app.set_sfx_volume(progress.sfx_volume - VOLUME_STEP)),
            make_button(pygame.Rect(right + 70, PANEL.y + 148, 40, 40), "+",
                        lambda: self.app.set_sfx_volume(progress.sfx_volume + VOLUME_STEP)),
            make_button(pygame.Rect(PANEL.right - 150, PANEL.bottom - 62, 126, 44), "Xong", self.close, (46, 140, 86)),
        ]
        selected = progress.music_track
        auto_color = COLOR_SELECTED if selected == AUTO_TRACK else COLOR_TRACK
        self.buttons.append(make_button(
            pygame.Rect(PANEL.x + 24, PANEL.y + 238, PANEL.width - 48, 38),
            "Tự động: menu một bài, mỗi World một bài khác", lambda: self._choose(AUTO_TRACK), auto_color,
        ))
        column_width = (PANEL.width - 48 - 12) // 2
        for index, track in enumerate(TRACKS):
            column, row = index % 2, index // 2
            rect = pygame.Rect(PANEL.x + 24 + column * (column_width + 12), PANEL.y + 288 + row * 44, column_width, 38)
            color = COLOR_SELECTED if selected == index else COLOR_TRACK
            label = f"{track.genre}  ·  {track.name}"
            self.buttons.append(make_button(rect, label, lambda chosen=index: self._choose(chosen), color))

    def _choose(self, index: int) -> None:
        self.app.choose_music_track(index)
        self.build()

    def handle_event(self, event: pygame.event.Event) -> None:
        for slider in (self.music_slider, self.sfx_slider):
            if slider.handle_event(event):
                return
        if event.type == pygame.MOUSEBUTTONDOWN:
            for button in self.buttons:
                if button.handle_event(event):
                    return
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.close()

    # ------------------------------------------------------------ drawing
    def draw(self, surface: pygame.Surface) -> None:
        app = self.app
        progress = app.progress
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 150))
        surface.blit(shade, (0, 0))
        pygame.draw.rect(surface, (24, 26, 38), PANEL, border_radius=14)
        pygame.draw.rect(surface, (80, 88, 120), PANEL, width=2, border_radius=14)

        surface.blit(app.font_title.render("Nhạc nền", True, COLOR_ACCENT), (PANEL.x + 24, PANEL.y + 18))
        track = TRACKS[app.music.wanted]
        if not app.music.enabled:
            status = "Nhạc đang tắt (âm lượng 0%)"
        elif app.music.is_loading:
            status = f"Đang chuẩn bị: {track.name} ({track.genre})..."
        else:
            status = f"Đang phát: {track.name} ({track.genre})"
        surface.blit(app.font.render(status, True, COLOR_MUTED), (PANEL.x + 24, PANEL.y + 62))

        rows = (
            ("Âm lượng nhạc", self.music_slider, progress.music_volume),
            ("Âm lượng hiệu ứng", self.sfx_slider, progress.sfx_volume),
        )
        for label, slider, value in rows:
            text = app.font_bold.render(label, True, COLOR_TEXT)
            surface.blit(text, text.get_rect(midleft=(PANEL.x + 24, slider.rect.centery)))
            slider.draw(surface)
            percent = app.font_bold.render(f"{value}%", True, COLOR_ACCENT)
            surface.blit(percent, percent.get_rect(midright=(PANEL.right - 20, slider.rect.centery)))

        surface.blit(app.font_bold.render("Chọn bài", True, COLOR_ACCENT), (PANEL.x + 24, PANEL.y + 206))
        for button in self.buttons:
            button.draw(surface, app.font_small if len(button.label) > 12 else app.font_bold)
