"""Scrollable panel that shows the theory of a level."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pygame

from .display import mouse_pos
from .editor import highlight
from .theory import Theory

COLOR_TEXT = (230, 232, 240)
COLOR_MUTED = (160, 166, 190)
COLOR_HEADING = (255, 196, 64)
COLOR_TAG = (90, 210, 230)
COLOR_INLINE_CODE = (120, 230, 160)
COLOR_CODE_BACKGROUND = (30, 32, 44)
COLOR_PANEL = (18, 20, 30)
COLOR_BORDER = (98, 114, 164)
PADDING = 22


def rich_words(text: str) -> list[tuple[str, bool]]:
    """Split text into words, marking those inside `backticks` as code."""
    words: list[tuple[str, bool]] = []
    for index, chunk in enumerate(text.split("`")):
        is_code = index % 2 == 1
        for word in chunk.split(" "):
            if word:
                words.append((word, is_code))
    return words


class TheoryView:
    def __init__(
        self,
        font: pygame.font.Font,
        font_bold: pygame.font.Font,
        font_title: pygame.font.Font,
        font_code: pygame.font.Font,
    ) -> None:
        self.font = font
        self.font_bold = font_bold
        self.font_title = font_title
        self.font_code = font_code
        self.operations: list[tuple[int, Callable[[pygame.Surface, int, int], None]]] = []
        self.content_height = 0
        self.scroll = 0
        self.rect = pygame.Rect(0, 0, 100, 100)
        self.close_rect = pygame.Rect(0, 0, 0, 0)

    # ------------------------------------------------------------ layout
    def build(
        self,
        title: str,
        tag: str,
        theory: Theory,
        rect: pygame.Rect,
        inputs: dict[str, Any],
        goal: str,
    ) -> None:
        self.rect = rect
        self.scroll = 0
        self.operations = []
        width = rect.width - PADDING * 2 - 12
        y = 0

        y = self._add_text(title, self.font_title, COLOR_HEADING, y, width - 110)
        y = self._add_text(tag, self.font, COLOR_TAG, y + 2, width - 110)
        y += 8
        y = self._add_heading("Khái niệm", y)
        for paragraph in theory.concept:
            y = self._add_rich("•  " + paragraph, y, width) + 6

        y = self._add_heading("Đề bài", y + 6)
        y = self._add_rich("Kết quả cần đạt: " + goal, y, width) + 4
        if inputs:
            y = self._add_rich("Dữ liệu vào (biến có sẵn, dùng ngay được trong code):", y, width) + 4
            input_lines = [(f"{name} = {value!r}", "") for name, value in inputs.items()]
            y = self._add_code_pairs(input_lines, y, width)

        if theory.starter_notes:
            y = self._add_heading("Giải thích code ban đầu của màn", y + 6)
            y = self._add_code_pairs(theory.starter_notes, y, width)

        y = self._add_heading("Ví dụ minh hoạ (khác lời giải - hãy tự áp dụng)", y + 6)
        y = self._add_code_pairs(theory.example, y, width)

        if theory.mistakes:
            y = self._add_heading("Lỗi hay gặp", y + 6)
            for mistake in theory.mistakes:
                y = self._add_rich("•  " + mistake, y, width) + 4
        self.content_height = y + PADDING

    def _add(self, y: int, draw: Callable[[pygame.Surface, int, int], None]) -> None:
        self.operations.append((y, draw))

    def _add_text(self, text: str, font: pygame.font.Font, color: tuple[int, int, int], y: int, width: int) -> int:
        for line in self._wrap_plain(text, font, width):
            rendered = font.render(line, True, color)
            self._add(y, lambda surface, x, top, image=rendered: surface.blit(image, (x, top)))
            y += font.get_linesize()
        return y

    def _add_heading(self, text: str, y: int) -> int:
        rendered = self.font_bold.render(text, True, COLOR_HEADING)
        self._add(y + 4, lambda surface, x, top, image=rendered: surface.blit(image, (x, top)))
        return y + self.font_bold.get_linesize() + 10

    def _add_rich(self, text: str, y: int, width: int, indent: int = 0) -> int:
        space = self.font.size(" ")[0]
        line_height = self.font.get_linesize() + 2
        cursor_x = indent
        line_items: list[tuple[int, pygame.Surface, Any]] = []

        def flush(top: int) -> None:
            items = list(line_items)

            def draw(surface: pygame.Surface, x: int, current_top: int) -> None:
                for offset, image, is_code in items:
                    if is_code:
                        background = image.get_rect(topleft=(x + offset, current_top)).inflate(6, 2)
                        pygame.draw.rect(surface, COLOR_CODE_BACKGROUND, background, border_radius=4)
                    surface.blit(image, (x + offset, current_top))

            self._add(top, draw)
            line_items.clear()

        for word, is_code in rich_words(text):
            font = self.font_code if is_code else self.font
            color = COLOR_INLINE_CODE if is_code else COLOR_TEXT
            image = font.render(word, True, color)
            if cursor_x + image.get_width() > width and line_items:
                flush(y)
                y += line_height
                cursor_x = indent + space * 4
            line_items.append((cursor_x, image, is_code))
            cursor_x += image.get_width() + space + (4 if is_code else 0)
        if line_items:
            flush(y)
            y += line_height
        return y

    def _add_code_pairs(self, pairs: list[tuple[str, str]], y: int, width: int) -> int:
        char_width = self.font_code.size("M")[0]
        code_height = self.font_code.get_linesize() + 4
        for code, note in pairs:
            tokens = highlight(code)

            def draw_code(surface: pygame.Surface, x: int, top: int, parts: list[Any] = tokens) -> None:
                box = pygame.Rect(x, top - 2, width, code_height)
                pygame.draw.rect(surface, COLOR_CODE_BACKGROUND, box, border_radius=6)
                cursor = x + 10
                for text, color in parts:
                    surface.blit(self.font_code.render(text, True, color), (cursor, top))
                    cursor += char_width * len(text)

            self._add(y, draw_code)
            y += code_height + 2
            if note:
                y = self._add_note("→ " + note, y, width)
            y += 8
        return y

    def _add_note(self, text: str, y: int, width: int) -> int:
        for line in self._wrap_plain(text, self.font, width - 24):
            rendered = self.font.render(line, True, COLOR_MUTED)
            self._add(y, lambda surface, x, top, image=rendered: surface.blit(image, (x + 18, top)))
            y += self.font.get_linesize()
        return y

    @staticmethod
    def _wrap_plain(text: str, font: pygame.font.Font, width: int) -> list[str]:
        lines: list[str] = []
        current = ""
        for word in text.split(" "):
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    # ------------------------------------------------------------ events
    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Returns "close" when the panel should close, "used" when the event was consumed."""
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(mouse_pos()):
            self._scroll_by(-event.y * 48)
            return "used"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_rect.collidepoint(event.pos):
                return "close"
            if self.rect.collidepoint(event.pos):
                return "used"
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_PAGEDOWN, pygame.K_PAGEUP):
            self._scroll_by(300 if event.key == pygame.K_PAGEDOWN else -300)
            return "used"
        return None

    def _scroll_by(self, amount: int) -> None:
        maximum = max(0, self.content_height - self.rect.height + PADDING)
        self.scroll = max(0, min(maximum, self.scroll + amount))

    # ------------------------------------------------------------ drawing
    def draw(self, surface: pygame.Surface) -> None:
        self._scroll_by(0)
        pygame.draw.rect(surface, COLOR_PANEL, self.rect, border_radius=12)
        pygame.draw.rect(surface, COLOR_BORDER, self.rect, width=2, border_radius=12)

        previous_clip = surface.get_clip()
        surface.set_clip(self.rect.inflate(-4, -4))
        left = self.rect.x + PADDING
        top = self.rect.y + PADDING - self.scroll
        for offset, draw in self.operations:
            screen_y = top + offset
            if self.rect.y - 80 < screen_y < self.rect.bottom + 10:
                draw(surface, left, screen_y)
        surface.set_clip(previous_clip)

        self._draw_scrollbar(surface)
        self.close_rect = pygame.Rect(self.rect.right - 110, self.rect.y + 14, 92, 36)
        hovered = self.close_rect.collidepoint(mouse_pos())
        pygame.draw.rect(surface, (150, 70, 80) if hovered else (120, 60, 70), self.close_rect, border_radius=8)
        label = self.font_bold.render("Đóng", True, COLOR_TEXT)
        surface.blit(label, label.get_rect(center=self.close_rect.center))

    def _draw_scrollbar(self, surface: pygame.Surface) -> None:
        visible = self.rect.height
        if self.content_height <= visible:
            return
        track = pygame.Rect(self.rect.right - 10, self.rect.y + 60, 5, visible - 80)
        pygame.draw.rect(surface, (50, 54, 72), track, border_radius=3)
        thumb_height = max(30, track.height * visible // self.content_height)
        maximum = max(1, self.content_height - visible + PADDING)
        thumb_y = track.y + (track.height - thumb_height) * self.scroll // maximum
        pygame.draw.rect(surface, COLOR_BORDER, (track.x, thumb_y, 5, thumb_height), border_radius=3)
