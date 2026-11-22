"""Scrollable panel that shows the theory of a level.

Học sinh kéo chuột để chọn dòng rồi bấm Ctrl+C (hoặc nút "Sao chép") để chép
lý thuyết ra ngoài - ví dụ dán vào vở ghi chép hay vào khung code.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pygame

from .display import mouse_pos
from .editor import _set_clipboard, highlight
from .glossary import find_terms, theory_text
from .lessons import WorldLesson
from .theory import Theory

COLOR_TEXT = (230, 232, 240)
COLOR_MUTED = (160, 166, 190)
COLOR_HEADING = (255, 196, 64)
COLOR_SUBHEADING = (120, 200, 255)
COLOR_TAG = (90, 210, 230)
COLOR_TERM = (255, 220, 140)
COLOR_INLINE_CODE = (120, 230, 160)
COLOR_CODE_BACKGROUND = (30, 32, 44)
COLOR_PANEL = (18, 20, 30)
COLOR_BORDER = (98, 114, 164)
COLOR_SELECTION = (52, 78, 140)
PADDING = 22
AUTO_SCROLL_MARGIN = 36
AUTO_SCROLL_SPEED = 14

STYLE_PLAIN = "plain"
STYLE_CODE = "code"
STYLE_BOLD = "bold"


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
        self.copy_lines: list[tuple[int, int, str]] = []
        self.content_height = 0
        self.content_width = 100
        self.scroll = 0
        self.rect = pygame.Rect(0, 0, 100, 100)
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        self.copy_rect = pygame.Rect(0, 0, 0, 0)
        self.selection_anchor: int | None = None
        self.selection_end: int | None = None
        self.dragging = False
        self.copied_line_count = 0

    # ------------------------------------------------------------ layout
    def build(
        self,
        title: str,
        tag: str,
        theory: Theory,
        rect: pygame.Rect,
        inputs: dict[str, Any],
        goal: str,
        lesson: WorldLesson | None = None,
    ) -> None:
        self.rect = rect
        self.scroll = 0
        self.operations = []
        self.copy_lines = []
        self.clear_selection()
        width = rect.width - PADDING * 2 - 12
        self.content_width = width
        y = 0

        y = self._add_text(title, self.font_title, COLOR_HEADING, y, width - 220)
        y = self._add_text(tag, self.font, COLOR_TAG, y + 2, width - 220)
        hint = "Kéo chuột để chọn dòng, rồi Ctrl+C hoặc nút Sao chép (chưa chọn thì chép cả bài)."
        y = self._add_text(hint, self.font, COLOR_MUTED, y + 2, width)
        y += 8
        y = self._add_heading("Khái niệm", y)
        for paragraph in theory.concept:
            y = self._add_rich("•  " + paragraph, y, width) + 6

        terms = find_terms(theory_text(theory))
        if terms:
            y = self._add_heading("Từ khó trong bài", y + 6)
            for glossary_term in terms:
                y = self._add_rich(glossary_term.meaning, y, width, bold_prefix=f"•  {glossary_term.term}:") + 4

        y = self._add_heading("Đề bài", y + 6)
        y = self._add_rich("Kết quả cần đạt: " + goal, y, width) + 4
        if inputs:
            y = self._add_rich("Dữ liệu vào (biến có sẵn, dùng ngay được trong code):", y, width) + 4
            input_lines = [(f"{name} = {value!r}", "") for name, value in inputs.items()]
            y = self._add_code_pairs(input_lines, y, width)

        if theory.starter_notes:
            y = self._add_heading("Giải thích code ban đầu của màn", y + 6)
            y = self._add_code_pairs(theory.starter_notes, y, width)

        if lesson is not None:
            y = self._add_lesson(lesson, y, width)

        y = self._add_heading("Ví dụ minh hoạ (khác lời giải - hãy tự áp dụng)", y + 6)
        y = self._add_code_pairs(theory.example, y, width)

        if theory.mistakes:
            y = self._add_heading("Lỗi hay gặp", y + 6)
            for mistake in theory.mistakes:
                y = self._add_rich("•  " + mistake, y, width) + 4
        self.content_height = y + PADDING

    def _add_lesson(self, lesson: WorldLesson, y: int, width: int) -> int:
        y = self._add_heading("Hiểu kỹ hơn", y + 6)
        y = self._add_subheading("Hình dung đời thường", y)
        y = self._add_rich(lesson.analogy, y, width) + 8
        y = self._add_subheading("Mẫu câu lệnh - từng phần nghĩa là gì", y)
        y = self._add_code_pairs(lesson.syntax, y, width)
        y = self._add_subheading("Chạy thử trong đầu - Python làm gì ở từng dòng", y)
        y = self._add_code_pairs(lesson.walkthrough, y, width)
        y = self._add_subheading("Mẹo nhớ", y)
        for tip in lesson.tips:
            y = self._add_rich("•  " + tip, y, width) + 4
        return y

    def _add(self, y: int, draw: Callable[[pygame.Surface, int, int], None]) -> None:
        self.operations.append((y, draw))

    def _add_copy_line(self, top: int, bottom: int, text: str) -> None:
        self.copy_lines.append((top, bottom, text))

    def _add_text(self, text: str, font: pygame.font.Font, color: tuple[int, int, int], y: int, width: int) -> int:
        for line in self._wrap_plain(text, font, width):
            rendered = font.render(line, True, color)
            self._add(y, lambda surface, x, top, image=rendered: surface.blit(image, (x, top)))
            self._add_copy_line(y, y + font.get_linesize(), line)
            y += font.get_linesize()
        return y

    def _add_heading(self, text: str, y: int) -> int:
        rendered = self.font_bold.render(text, True, COLOR_HEADING)
        self._add(y + 4, lambda surface, x, top, image=rendered: surface.blit(image, (x, top)))
        bottom = y + self.font_bold.get_linesize() + 10
        self._add_copy_line(y, bottom, "\n" + text.upper())
        return bottom

    def _add_subheading(self, text: str, y: int) -> int:
        rendered = self.font_bold.render(text, True, COLOR_SUBHEADING)
        self._add(y, lambda surface, x, top, image=rendered: surface.blit(image, (x, top)))
        bottom = y + self.font_bold.get_linesize() + 6
        self._add_copy_line(y, bottom, f"[{text}]")
        return bottom

    def _styled_words(self, text: str, bold_prefix: str) -> list[tuple[str, str]]:
        words = [(word, STYLE_BOLD) for word in bold_prefix.split(" ") if word]
        for word, is_code in rich_words(text):
            words.append((word, STYLE_CODE if is_code else STYLE_PLAIN))
        return words

    def _render_word(self, word: str, style: str) -> pygame.Surface:
        if style == STYLE_CODE:
            return self.font_code.render(word, True, COLOR_INLINE_CODE)
        if style == STYLE_BOLD:
            return self.font_bold.render(word, True, COLOR_TERM)
        return self.font.render(word, True, COLOR_TEXT)

    def _add_rich(self, text: str, y: int, width: int, indent: int = 0, bold_prefix: str = "") -> int:
        space = self.font.size(" ")[0]
        line_height = self.font.get_linesize() + 2
        cursor_x = indent
        line_items: list[tuple[int, pygame.Surface, bool]] = []
        line_words: list[str] = []

        def flush(top: int) -> None:
            items = list(line_items)

            def draw(surface: pygame.Surface, x: int, current_top: int) -> None:
                for offset, image, is_code in items:
                    if is_code:
                        background = image.get_rect(topleft=(x + offset, current_top)).inflate(6, 2)
                        pygame.draw.rect(surface, COLOR_CODE_BACKGROUND, background, border_radius=4)
                    surface.blit(image, (x + offset, current_top))

            self._add(top, draw)
            self._add_copy_line(top, top + line_height, " ".join(line_words))
            line_items.clear()
            line_words.clear()

        for word, style in self._styled_words(text, bold_prefix):
            is_code = style == STYLE_CODE
            image = self._render_word(word, style)
            if cursor_x + image.get_width() > width and line_items:
                flush(y)
                y += line_height
                cursor_x = indent + space * 4
            line_items.append((cursor_x, image, is_code))
            line_words.append(word)
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
            self._add_copy_line(y - 2, y + code_height, code)
            y += code_height + 2
            if note:
                y = self._add_note("→ " + note, y, width)
            y += 8
        return y

    def _add_note(self, text: str, y: int, width: int) -> int:
        for line in self._wrap_plain(text, self.font, width - 24):
            rendered = self.font.render(line, True, COLOR_MUTED)
            self._add(y, lambda surface, x, top, image=rendered: surface.blit(image, (x + 18, top)))
            self._add_copy_line(y, y + self.font.get_linesize(), "    " + line)
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

    # ------------------------------------------------------------ selection and copy
    @property
    def has_selection(self) -> bool:
        return self.selection_anchor is not None and self.selection_end is not None

    def clear_selection(self) -> None:
        self.selection_anchor = None
        self.selection_end = None
        self.dragging = False

    def select_all(self) -> None:
        if not self.copy_lines:
            return
        self.selection_anchor = 0
        self.selection_end = len(self.copy_lines) - 1

    def selected_range(self) -> range:
        if self.selection_anchor is None or self.selection_end is None:
            return range(0)
        first = min(self.selection_anchor, self.selection_end)
        last = max(self.selection_anchor, self.selection_end)
        return range(first, last + 1)

    def copy_text(self) -> str:
        """Chữ sẽ được chép: các dòng đang chọn, hoặc cả bài nếu chưa chọn gì."""
        indexes = self.selected_range() if self.has_selection else range(len(self.copy_lines))
        lines = [self.copy_lines[index][2] for index in indexes]
        return "\n".join(lines).strip("\n") + "\n"

    def copy(self) -> str:
        text = self.copy_text()
        _set_clipboard(text)
        self.copied_line_count = len(self.selected_range()) if self.has_selection else len(self.copy_lines)
        return "copied"

    def _content_top(self) -> int:
        return self.rect.y + PADDING - self.scroll

    def _line_at(self, screen_y: int) -> int:
        content_y = screen_y - self._content_top()
        found = 0
        for index, (top, _bottom, _text) in enumerate(self.copy_lines):
            if top > content_y:
                break
            found = index
        return found

    def _start_selection(self, screen_y: int) -> None:
        if not self.copy_lines:
            return
        line_index = self._line_at(screen_y)
        self.selection_anchor = line_index
        self.selection_end = line_index
        self.dragging = True

    # ------------------------------------------------------------ events
    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Returns "close", "copied", or "used" when the event was consumed."""
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(mouse_pos()):
            self._scroll_by(-event.y * 48)
            return "used"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click(event.pos)
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self.selection_end = self._line_at(event.pos[1])
            return "used"
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            return "used"
        if event.type == pygame.KEYDOWN:
            return self._handle_key(event)
        return None

    def _handle_click(self, position: tuple[int, int]) -> str | None:
        if self.close_rect.collidepoint(position):
            return "close"
        if self.copy_rect.collidepoint(position):
            return self.copy()
        if not self.rect.collidepoint(position):
            self.clear_selection()
            return None
        self._start_selection(position[1])
        return "used"

    def _handle_key(self, event: pygame.event.Event) -> str | None:
        if event.key in (pygame.K_PAGEDOWN, pygame.K_PAGEUP):
            self._scroll_by(300 if event.key == pygame.K_PAGEDOWN else -300)
            return "used"
        if not event.mod & pygame.KMOD_CTRL:
            return None
        if event.key == pygame.K_c and self.has_selection:
            return self.copy()
        if event.key == pygame.K_a and self.rect.collidepoint(mouse_pos()):
            self.select_all()
            return "used"
        return None

    def _scroll_by(self, amount: int) -> None:
        maximum = max(0, self.content_height - self.rect.height + PADDING)
        self.scroll = max(0, min(maximum, self.scroll + amount))

    def _auto_scroll_while_dragging(self) -> None:
        if not self.dragging:
            return
        mouse_y = mouse_pos()[1]
        if mouse_y < self.rect.y + AUTO_SCROLL_MARGIN:
            self._scroll_by(-AUTO_SCROLL_SPEED)
        elif mouse_y > self.rect.bottom - AUTO_SCROLL_MARGIN:
            self._scroll_by(AUTO_SCROLL_SPEED)
        else:
            return
        self.selection_end = self._line_at(mouse_y)

    # ------------------------------------------------------------ drawing
    def draw(self, surface: pygame.Surface) -> None:
        self._auto_scroll_while_dragging()
        self._scroll_by(0)
        pygame.draw.rect(surface, COLOR_PANEL, self.rect, border_radius=12)
        pygame.draw.rect(surface, COLOR_BORDER, self.rect, width=2, border_radius=12)

        previous_clip = surface.get_clip()
        surface.set_clip(self.rect.inflate(-4, -4))
        left = self.rect.x + PADDING
        top = self._content_top()
        self._draw_selection(surface, left, top)
        for offset, draw in self.operations:
            screen_y = top + offset
            if self.rect.y - 80 < screen_y < self.rect.bottom + 10:
                draw(surface, left, screen_y)
        surface.set_clip(previous_clip)

        self._draw_scrollbar(surface)
        self.copy_rect = pygame.Rect(self.rect.right - 216, self.rect.y + 14, 98, 36)
        self.close_rect = pygame.Rect(self.rect.right - 110, self.rect.y + 14, 92, 36)
        self._draw_button(surface, self.copy_rect, "Sao chép", (46, 110, 150), (60, 135, 180))
        self._draw_button(surface, self.close_rect, "Đóng", (120, 60, 70), (150, 70, 80))

    def _draw_button(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        color: tuple[int, int, int],
        hover_color: tuple[int, int, int],
    ) -> None:
        hovered = rect.collidepoint(mouse_pos())
        pygame.draw.rect(surface, hover_color if hovered else color, rect, border_radius=8)
        rendered = self.font_bold.render(label, True, COLOR_TEXT)
        surface.blit(rendered, rendered.get_rect(center=rect.center))

    def _draw_selection(self, surface: pygame.Surface, left: int, top: int) -> None:
        for index in self.selected_range():
            line_top, line_bottom, _text = self.copy_lines[index]
            highlight_rect = pygame.Rect(left - 6, top + line_top, self.content_width + 12, line_bottom - line_top)
            pygame.draw.rect(surface, COLOR_SELECTION, highlight_rect)

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
