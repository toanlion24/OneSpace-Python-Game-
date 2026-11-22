"""Scrollable panel that shows the theory of a level.

Chọn chữ giống trình soạn thảo: kéo chuột để bôi đen (nhả chuột là tự chép),
nhấn đúp để chọn một từ, nhấn 3 lần để chép cả đoạn. Ctrl+C / Ctrl+A và nút
"Sao chép" (chưa chọn gì thì chép cả bài) cũng dùng được.
"""

from __future__ import annotations

import bisect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pygame

from .display import mouse_pos
from .editor import _set_clipboard, highlight
from .glossary import find_terms, theory_text
from .lessons import WorldLesson
from .theory import Theory

Color = tuple[int, int, int]

COLOR_TEXT = (226, 230, 240)
COLOR_MUTED = (150, 158, 184)
COLOR_TITLE = (255, 210, 110)
COLOR_TAG = (120, 214, 236)
COLOR_TERM = (255, 214, 150)
COLOR_INLINE_CODE = (130, 232, 170)
COLOR_CODE_BACKGROUND = (24, 27, 39)
COLOR_PANEL = (17, 19, 29)
COLOR_HEADER = (25, 28, 42)
COLOR_BORDER = (78, 92, 140)
COLOR_CARD = (26, 29, 43)
COLOR_SHADOW = (6, 7, 12)
COLOR_SELECTION = (80, 130, 255, 95)

COLOR_CONCEPT = (255, 196, 64)
COLOR_TERMS = (240, 140, 205)
COLOR_GOAL = (110, 220, 140)
COLOR_STARTER = (110, 170, 255)
COLOR_LESSON = (90, 210, 230)
COLOR_TIPS = (255, 180, 90)
COLOR_EXAMPLE = (175, 145, 255)
COLOR_MISTAKES = (255, 112, 112)

PADDING = 22
SCROLLBAR_SPACE = 14
MULTI_CLICK_MILLISECONDS = 450
MULTI_CLICK_DISTANCE = 6
COPIED_FLASH_MILLISECONDS = 1400
AUTO_SCROLL_MARGIN = 28
AUTO_SCROLL_SPEED = 14
HINT = "Kéo chuột: bôi đen và tự chép  ·  Nhấn 3 lần: chép cả đoạn  ·  Ctrl+A: chọn hết"

STYLE_PLAIN = "plain"
STYLE_CODE = "code"
STYLE_BOLD = "bold"

DrawOperation = Callable[[pygame.Surface, int, int], None]


def rich_words(text: str) -> list[tuple[str, bool]]:
    """Split text into words, marking those inside `backticks` as code."""
    words: list[tuple[str, bool]] = []
    for index, chunk in enumerate(text.split("`")):
        is_code = index % 2 == 1
        for word in chunk.split(" "):
            if word:
                words.append((word, is_code))
    return words


def _dim(color: Color, amount: float = 0.35) -> Color:
    red, green, blue = color
    panel_red, panel_green, panel_blue = COLOR_PANEL
    return (
        round(panel_red + (red - panel_red) * amount),
        round(panel_green + (green - panel_green) * amount),
        round(panel_blue + (blue - panel_blue) * amount),
    )


def _is_word_character(character: str) -> bool:
    return character.isalnum() or character == "_"


@dataclass
class TextLine:
    """Một dòng chữ trên màn hình, nhớ toạ độ x của từng ký tự để chọn chữ."""

    top: int
    bottom: int
    text: str
    char_x: list[int]
    block: int
    joins_previous: bool = False
    gap_before: bool = False

    def char_at(self, x: int) -> int:
        index = bisect.bisect_left(self.char_x, x)
        if index <= 0:
            return 0
        if index >= len(self.char_x):
            return len(self.text)
        before = self.char_x[index - 1]
        after = self.char_x[index]
        if x - before < after - x:
            return index - 1
        return index


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
        self.operations: list[tuple[int, DrawOperation]] = []
        self.header_images: list[tuple[pygame.Surface, tuple[int, int]]] = []
        self.lines: list[TextLine] = []
        self.block_count = 0
        self.content_height = 0
        self.content_width = 100
        self.header_height = 100
        self.scroll = 0
        self.rect = pygame.Rect(0, 0, 100, 100)
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        self.copy_rect = pygame.Rect(0, 0, 0, 0)
        self.anchor: tuple[int, int] | None = None
        self.focus: tuple[int, int] | None = None
        self.dragging = False
        self.click_count = 0
        self.last_click_time = -10_000
        self.last_click_position = (0, 0)
        self.copied_character_count = 0
        self.copied_flash_until = -10_000
        self.clock: Callable[[], int] = pygame.time.get_ticks

    # ------------------------------------------------------------ layout
    @property
    def content_area(self) -> pygame.Rect:
        return pygame.Rect(
            self.rect.x + PADDING,
            self.rect.y + self.header_height,
            self.content_width,
            self.rect.height - self.header_height - 10,
        )

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
        self.lines = []
        self.block_count = 0
        self.clear_selection()
        self.click_count = 0
        self.last_click_time = -10_000
        width = rect.width - PADDING * 2 - SCROLLBAR_SPACE
        self.content_width = width
        self._build_header(title, tag, width)

        y = self._add_heading("Khái niệm", COLOR_CONCEPT, 14)
        for paragraph in theory.concept:
            y = self._add_paragraph(paragraph, y, width, bullet=COLOR_CONCEPT) + 6

        terms = find_terms(theory_text(theory))
        if terms:
            y = self._add_heading("Từ khó trong bài", COLOR_TERMS, y + 10)
            card_index, card_top = len(self.operations), y
            y += 10
            for glossary_term in terms:
                y = self._add_paragraph(
                    glossary_term.meaning, y, width - 12, bullet=COLOR_TERMS,
                    bold_prefix=f"{glossary_term.term}:", indent=12,
                ) + 5
            y += 6
            self._add_card(card_index, card_top, y, COLOR_TERMS)

        y = self._add_heading("Đề bài", COLOR_GOAL, y + 14)
        y = self._add_paragraph(goal, y, width, bold_prefix="Kết quả cần đạt:") + 6
        if inputs:
            y = self._add_paragraph("Dữ liệu vào (biến có sẵn, dùng ngay được trong code):", y, width) + 6
            input_lines = [(f"{name} = {value!r}", "") for name, value in inputs.items()]
            y = self._add_code_pairs(input_lines, y, width, COLOR_GOAL)

        if theory.starter_notes:
            y = self._add_heading("Giải thích code ban đầu của màn", COLOR_STARTER, y + 10)
            y = self._add_code_pairs(theory.starter_notes, y, width, COLOR_STARTER)

        if lesson is not None:
            y = self._add_lesson(lesson, y + 10, width)

        y = self._add_heading("Ví dụ minh hoạ (khác lời giải - hãy tự áp dụng)", COLOR_EXAMPLE, y + 10)
        y = self._add_code_pairs(theory.example, y, width, COLOR_EXAMPLE)

        if theory.mistakes:
            y = self._add_heading("Lỗi hay gặp", COLOR_MISTAKES, y + 10)
            card_index, card_top = len(self.operations), y
            y += 10
            for mistake in theory.mistakes:
                y = self._add_paragraph(mistake, y, width - 12, bullet=COLOR_MISTAKES, indent=12) + 5
            y += 6
            self._add_card(card_index, card_top, y, COLOR_MISTAKES)
        self.content_height = y + 20

    def _add_lesson(self, lesson: WorldLesson, y: int, width: int) -> int:
        y = self._add_heading("Hiểu kỹ hơn", COLOR_LESSON, y)
        y = self._add_subheading("Hình dung đời thường", COLOR_LESSON, y)
        card_index, card_top = len(self.operations), y
        y = self._add_paragraph(lesson.analogy, y + 10, width - 24, indent=16) + 8
        self._add_card(card_index, card_top, y, COLOR_LESSON)
        y = self._add_subheading("Mẫu câu lệnh - từng phần nghĩa là gì", COLOR_LESSON, y + 12)
        y = self._add_code_pairs(lesson.syntax, y, width, COLOR_LESSON)
        y = self._add_subheading("Chạy thử trong đầu - Python làm gì ở từng dòng", COLOR_LESSON, y + 4)
        y = self._add_code_pairs(lesson.walkthrough, y, width, COLOR_LESSON)
        y = self._add_subheading("Mẹo nhớ", COLOR_TIPS, y + 4)
        card_index, card_top = len(self.operations), y
        y += 10
        for tip in lesson.tips:
            y = self._add_paragraph(tip, y, width - 12, bullet=COLOR_TIPS, indent=12) + 5
        y += 6
        self._add_card(card_index, card_top, y, COLOR_TIPS)
        return y

    def _build_header(self, title: str, tag: str, width: int) -> None:
        self.header_images = []
        y = 16
        title_image = self.font_title.render(self._fit_text(title, self.font_title, width - 230), True, COLOR_TITLE)
        self.header_images.append((title_image, (PADDING, y)))
        y += title_image.get_height() + 2
        tag_image = self.font.render(tag, True, COLOR_TAG)
        self.header_images.append((tag_image, (PADDING, y)))
        y += self.font.get_linesize() + 2
        for line in self._wrap_plain(HINT, self.font, width):
            self.header_images.append((self.font.render(line, True, COLOR_MUTED), (PADDING, y)))
            y += self.font.get_linesize()
        self.header_height = y + 12

    def _new_block(self) -> int:
        self.block_count += 1
        return self.block_count

    def _add(self, y: int, draw: DrawOperation) -> None:
        self.operations.append((y, draw))

    def _add_line(
        self, top: int, bottom: int, text: str, char_x: list[int], block: int,
        joins_previous: bool = False, gap_before: bool = False,
    ) -> None:
        self.lines.append(TextLine(top, bottom, text, char_x, block, joins_previous, gap_before))

    @staticmethod
    def _plain_char_x(text: str, font: pygame.font.Font, left: int) -> list[int]:
        return [left + font.size(text[:count])[0] for count in range(len(text) + 1)]

    def _add_card(self, operation_index: int, top: int, bottom: int, accent: Color) -> None:
        width = self.content_width

        def draw(surface: pygame.Surface, x: int, card_top: int) -> None:
            card = pygame.Rect(x - 4, card_top, width + 8, bottom - top)
            pygame.draw.rect(surface, COLOR_CARD, card, border_radius=10)
            pygame.draw.rect(surface, _dim(accent, 0.45), card, width=1, border_radius=10)
            pygame.draw.rect(surface, accent, (card.x, card.y + 8, 4, card.height - 16), border_radius=2)

        self.operations.insert(operation_index, (top, draw))

    def _add_heading(self, text: str, color: Color, y: int) -> int:
        image = self.font_bold.render(text, True, color)
        height = self.font_bold.get_linesize()
        width = self.content_width

        def draw(surface: pygame.Surface, x: int, top: int) -> None:
            pygame.draw.rect(surface, color, (x, top + 3, 5, height - 6), border_radius=3)
            surface.blit(image, (x + 14, top))
            line_start = x + 14 + image.get_width() + 12
            if line_start < x + width:
                line_y = top + height // 2
                pygame.draw.line(surface, _dim(color), (line_start, line_y), (x + width, line_y))

        self._add(y, draw)
        self._add_line(y, y + height, text, self._plain_char_x(text, self.font_bold, 14), self._new_block(),
                       gap_before=True)
        return y + height + 8

    def _add_subheading(self, text: str, color: Color, y: int) -> int:
        image = self.font_bold.render(text, True, color)
        height = self.font_bold.get_linesize()

        def draw(surface: pygame.Surface, x: int, top: int) -> None:
            pygame.draw.circle(surface, color, (x + 6, top + height // 2), 4)
            surface.blit(image, (x + 16, top))

        self._add(y, draw)
        self._add_line(y, y + height, text, self._plain_char_x(text, self.font_bold, 16), self._new_block(),
                       gap_before=True)
        return y + height + 6

    def _styled_words(self, text: str, bold_prefix: str) -> list[tuple[str, str]]:
        words = [(word, STYLE_BOLD) for word in bold_prefix.split(" ") if word]
        for word, is_code in rich_words(text):
            words.append((word, STYLE_CODE if is_code else STYLE_PLAIN))
        return words

    def _font_for(self, style: str) -> pygame.font.Font:
        if style == STYLE_CODE:
            return self.font_code
        if style == STYLE_BOLD:
            return self.font_bold
        return self.font

    def _render_word(self, word: str, style: str) -> pygame.Surface:
        if style == STYLE_CODE:
            return self.font_code.render(word, True, COLOR_INLINE_CODE)
        if style == STYLE_BOLD:
            return self.font_bold.render(word, True, COLOR_TERM)
        return self.font.render(word, True, COLOR_TEXT)

    def _add_paragraph(
        self, text: str, y: int, width: int, bullet: Color | None = None, bold_prefix: str = "", indent: int = 0,
    ) -> int:
        """Đoạn văn tự xuống dòng; dòng tiếp theo thẳng hàng với chữ (thụt treo sau dấu chấm đầu dòng)."""
        block = self._new_block()
        space = self.font.size(" ")[0]
        line_height = self.font.get_linesize() + 3
        text_left = indent + (18 if bullet else 0)
        right_edge = indent + width
        cursor_x = text_left
        line_items: list[tuple[int, int, pygame.Surface, bool]] = []
        line_words: list[str] = []
        char_x: list[int] = []
        is_first_line = True

        def flush(top: int, first: bool) -> None:
            items = list(line_items)
            dot_color = bullet if first else None

            def draw(surface: pygame.Surface, x: int, current_top: int) -> None:
                if dot_color is not None:
                    pygame.draw.circle(surface, dot_color, (x + indent + 6, current_top + line_height // 2), 3)
                for offset, baseline_shift, image, is_code in items:
                    word_top = current_top + baseline_shift
                    if is_code:
                        chip = image.get_rect(topleft=(x + offset, word_top)).inflate(6, 2)
                        pygame.draw.rect(surface, COLOR_CODE_BACKGROUND, chip, border_radius=4)
                    surface.blit(image, (x + offset, word_top))

            self._add(top, draw)
            self._add_line(top, top + line_height, " ".join(line_words), list(char_x), block,
                           joins_previous=not first)
            line_items.clear()
            line_words.clear()
            char_x.clear()

        for word, style in self._styled_words(text, bold_prefix):
            is_code = style == STYLE_CODE
            font = self._font_for(style)
            image = self._render_word(word, style)
            if cursor_x + image.get_width() > right_edge and line_items:
                flush(y, is_first_line)
                is_first_line = False
                y += line_height
                cursor_x = text_left
            word_x = cursor_x + (3 if is_code else 0)
            # Các font có độ cao chữ khác nhau: căn theo đường chân chữ của font thường.
            baseline_shift = self.font.get_ascent() - font.get_ascent()
            line_items.append((word_x, baseline_shift, image, is_code))
            line_words.append(word)
            char_x.extend(word_x + font.size(word[:count])[0] for count in range(len(word) + 1))
            cursor_x = word_x + image.get_width() + space + (3 if is_code else 0)
        if line_items:
            flush(y, is_first_line)
            y += line_height
        return y

    def _add_code_pairs(self, pairs: list[tuple[str, str]], y: int, width: int, accent: Color) -> int:
        char_width = self.font_code.size("M")[0]
        code_height = self.font_code.get_linesize() + 6
        for code, note in pairs:
            tokens = highlight(code)

            def draw_code(surface: pygame.Surface, x: int, top: int, parts: list[Any] = tokens) -> None:
                box = pygame.Rect(x, top - 3, width, code_height)
                pygame.draw.rect(surface, COLOR_CODE_BACKGROUND, box, border_radius=6)
                pygame.draw.rect(surface, accent, (box.x, box.y, 3, box.height), border_radius=2)
                cursor = x + 14
                for text, color in parts:
                    surface.blit(self.font_code.render(text, True, color), (cursor, top))
                    cursor += char_width * len(text)

            self._add(y, draw_code)
            code_char_x = [14 + count * char_width for count in range(len(code) + 1)]
            self._add_line(y - 3, y + code_height - 3, code, code_char_x, self._new_block())
            y += code_height + 1
            if note:
                y = self._add_note("→ " + note, y, width)
            y += 7
        return y

    def _add_note(self, text: str, y: int, width: int) -> int:
        block = self._new_block()
        for index, line in enumerate(self._wrap_plain(text, self.font, width - 30)):
            image = self.font.render(line, True, COLOR_MUTED)
            self._add(y, lambda surface, x, top, rendered=image: surface.blit(rendered, (x + 22, top)))
            self._add_line(y, y + self.font.get_linesize(), line, self._plain_char_x(line, self.font, 22), block,
                           joins_previous=index > 0)
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

    @staticmethod
    def _fit_text(text: str, font: pygame.font.Font, width: int) -> str:
        if font.size(text)[0] <= width:
            return text
        while text and font.size(text + "...")[0] > width:
            text = text[:-1]
        return text + "..."

    # ------------------------------------------------------------ selection and copy
    @property
    def has_selection(self) -> bool:
        return self.anchor is not None and self.focus is not None and self.anchor != self.focus

    def clear_selection(self) -> None:
        self.anchor = None
        self.focus = None
        self.dragging = False

    def select_all(self) -> None:
        if not self.lines:
            return
        self.anchor = (0, 0)
        self.focus = (len(self.lines) - 1, len(self.lines[-1].text))

    def _ordered_selection(self) -> tuple[tuple[int, int], tuple[int, int]] | None:
        if not self.has_selection or self.anchor is None or self.focus is None:
            return None
        return min(self.anchor, self.focus), max(self.anchor, self.focus)

    def _text_between(self, start: tuple[int, int], end: tuple[int, int]) -> str:
        pieces: list[str] = []
        for line_index in range(start[0], end[0] + 1):
            line = self.lines[line_index]
            first_char = start[1] if line_index == start[0] else 0
            last_char = end[1] if line_index == end[0] else len(line.text)
            if line_index > start[0]:
                if line.gap_before:
                    pieces.append("\n\n")
                elif line.joins_previous:
                    pieces.append(" ")
                else:
                    pieces.append("\n")
            pieces.append(line.text[first_char:last_char])
        return "".join(pieces)

    def copy_text(self) -> str:
        """Chữ sẽ được chép: phần đang bôi đen, hoặc cả bài nếu chưa chọn gì."""
        selection = self._ordered_selection()
        if selection is not None:
            return self._text_between(*selection)
        if not self.lines:
            return ""
        last_index = len(self.lines) - 1
        return self._text_between((0, 0), (last_index, len(self.lines[last_index].text))) + "\n"

    def copy(self) -> str:
        text = self.copy_text()
        _set_clipboard(text)
        self.copied_character_count = len(text.strip())
        self.copied_flash_until = self.clock() + COPIED_FLASH_MILLISECONDS
        return "copied"

    def _content_top(self) -> int:
        return self.content_area.y - self.scroll

    def _position_at(self, position: tuple[int, int]) -> tuple[int, int]:
        content_x = position[0] - self.content_area.x
        content_y = position[1] - self._content_top()
        line_index = 0
        for index, line in enumerate(self.lines):
            if line.top > content_y:
                break
            line_index = index
        return line_index, self.lines[line_index].char_at(content_x)

    def _select_word(self, position: tuple[int, int]) -> None:
        line_index, char_index = position
        text = self.lines[line_index].text
        start = char_index
        while start > 0 and _is_word_character(text[start - 1]):
            start -= 1
        end = char_index
        while end < len(text) and _is_word_character(text[end]):
            end += 1
        self.anchor = (line_index, start)
        self.focus = (line_index, end)

    def _select_block(self, line_index: int) -> None:
        block = self.lines[line_index].block
        indexes = [index for index, line in enumerate(self.lines) if line.block == block]
        self.anchor = (indexes[0], 0)
        self.focus = (indexes[-1], len(self.lines[indexes[-1]].text))

    def _count_click(self, position: tuple[int, int]) -> int:
        now = self.clock()
        distance = max(abs(position[0] - self.last_click_position[0]), abs(position[1] - self.last_click_position[1]))
        if now - self.last_click_time <= MULTI_CLICK_MILLISECONDS and distance <= MULTI_CLICK_DISTANCE:
            self.click_count = min(self.click_count + 1, 3)
        else:
            self.click_count = 1
        self.last_click_time = now
        self.last_click_position = position
        return self.click_count

    # ------------------------------------------------------------ events
    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Returns "close", "copied", or "used" when the event was consumed."""
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(mouse_pos()):
            self._scroll_by(-event.y * 48)
            return "used"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click(event.pos)
        if event.type == pygame.MOUSEMOTION and self.dragging and self.lines:
            self.focus = self._position_at(event.pos)
            return "used"
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            if self.has_selection:
                return self.copy()
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
        if not self.content_area.collidepoint(position) or not self.lines:
            return "used"
        clicks = self._count_click(position)
        text_position = self._position_at(position)
        if clicks == 1:
            self.anchor = text_position
            self.focus = text_position
            self.dragging = True
            return "used"
        self.dragging = False
        if clicks == 2:
            self._select_word(text_position)
            return "used"
        self._select_block(text_position[0])
        return self.copy()

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
        maximum = max(0, self.content_height - self.content_area.height)
        self.scroll = max(0, min(maximum, self.scroll + amount))

    def _auto_scroll_while_dragging(self) -> None:
        if not self.dragging or not self.lines:
            return
        position = mouse_pos()
        area = self.content_area
        if position[1] < area.y + AUTO_SCROLL_MARGIN:
            self._scroll_by(-AUTO_SCROLL_SPEED)
        elif position[1] > area.bottom - AUTO_SCROLL_MARGIN:
            self._scroll_by(AUTO_SCROLL_SPEED)
        else:
            return
        self.focus = self._position_at(position)

    # ------------------------------------------------------------ drawing
    def draw(self, surface: pygame.Surface) -> None:
        self._auto_scroll_while_dragging()
        self._scroll_by(0)
        pygame.draw.rect(surface, COLOR_SHADOW, self.rect.move(0, 5), border_radius=14)
        pygame.draw.rect(surface, COLOR_PANEL, self.rect, border_radius=14)

        area = self.content_area
        clip = pygame.Rect(self.rect.x + 2, area.y, self.rect.width - 4, area.height)
        previous_clip = surface.get_clip()
        surface.set_clip(clip)
        top = self._content_top()
        for offset, draw in self.operations:
            screen_y = top + offset
            if screen_y < area.bottom + 10:
                draw(surface, area.x, screen_y)
        self._draw_selection(surface, area.x, top)
        surface.set_clip(previous_clip)

        self._draw_header(surface)
        pygame.draw.rect(surface, COLOR_BORDER, self.rect, width=2, border_radius=14)
        self._draw_scrollbar(surface)

    def _draw_header(self, surface: pygame.Surface) -> None:
        header = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, self.header_height)
        pygame.draw.rect(surface, COLOR_HEADER, header, border_top_left_radius=14, border_top_right_radius=14)
        pygame.draw.line(surface, COLOR_BORDER, (header.x + 2, header.bottom - 1), (header.right - 3, header.bottom - 1))
        for shade_step in range(6):
            shade = pygame.Surface((header.width - 4, 1), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 70 - shade_step * 12))
            surface.blit(shade, (header.x + 2, header.bottom + shade_step))
        for image, (offset_x, offset_y) in self.header_images:
            surface.blit(image, (header.x + offset_x, header.y + offset_y))

        self.copy_rect = pygame.Rect(self.rect.right - 236, self.rect.y + 16, 118, 38)
        self.close_rect = pygame.Rect(self.rect.right - 108, self.rect.y + 16, 88, 38)
        copied_recently = self.clock() < self.copied_flash_until
        copy_label = "Đã chép!" if copied_recently else "Sao chép"
        copy_color = (40, 140, 90) if copied_recently else (46, 104, 160)
        self._draw_button(surface, self.copy_rect, copy_label, copy_color, self._draw_copy_icon)
        self._draw_button(surface, self.close_rect, "Đóng", (128, 58, 72), self._draw_close_icon)

    def _draw_button(
        self, surface: pygame.Surface, rect: pygame.Rect, label: str, color: Color,
        draw_icon: Callable[[pygame.Surface, int, int], None],
    ) -> None:
        hovered = rect.collidepoint(mouse_pos())
        fill = tuple(min(255, channel + 24) for channel in color) if hovered else color
        pygame.draw.rect(surface, COLOR_SHADOW, rect.move(0, 3), border_radius=10)
        pygame.draw.rect(surface, fill, rect, border_radius=10)
        pygame.draw.rect(surface, tuple(min(255, channel + 50) for channel in color), rect, width=1, border_radius=10)
        rendered = self.font_bold.render(label, True, COLOR_TEXT)
        total_width = 18 + rendered.get_width()
        left = rect.centerx - total_width // 2
        draw_icon(surface, left, rect.centery)
        surface.blit(rendered, rendered.get_rect(midleft=(left + 18, rect.centery)))

    @staticmethod
    def _draw_copy_icon(surface: pygame.Surface, left: int, center_y: int) -> None:
        pygame.draw.rect(surface, COLOR_TEXT, (left + 3, center_y - 7, 9, 11), width=2, border_radius=2)
        pygame.draw.rect(surface, COLOR_TEXT, (left, center_y - 4, 9, 11), border_radius=2)

    @staticmethod
    def _draw_close_icon(surface: pygame.Surface, left: int, center_y: int) -> None:
        pygame.draw.line(surface, COLOR_TEXT, (left + 1, center_y - 5), (left + 11, center_y + 5), 3)
        pygame.draw.line(surface, COLOR_TEXT, (left + 1, center_y + 5), (left + 11, center_y - 5), 3)

    def _draw_selection(self, surface: pygame.Surface, left: int, top: int) -> None:
        selection = self._ordered_selection()
        if selection is None:
            return
        start, end = selection
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for line_index in range(start[0], end[0] + 1):
            line = self.lines[line_index]
            first_char = start[1] if line_index == start[0] else 0
            last_char = end[1] if line_index == end[0] else len(line.text)
            x_start = line.char_x[first_char]
            x_end = line.char_x[last_char]
            if line_index < end[0]:
                x_end += 6
            if x_end <= x_start:
                continue
            highlight_rect = pygame.Rect(left + x_start, top + line.top, x_end - x_start, line.bottom - line.top)
            pygame.draw.rect(overlay, COLOR_SELECTION, highlight_rect, border_radius=3)
        surface.blit(overlay, (0, 0))

    def _draw_scrollbar(self, surface: pygame.Surface) -> None:
        area = self.content_area
        if self.content_height <= area.height:
            return
        track = pygame.Rect(self.rect.right - 12, area.y + 8, 6, area.height - 16)
        pygame.draw.rect(surface, (40, 44, 62), track, border_radius=3)
        thumb_height = max(36, track.height * area.height // self.content_height)
        maximum = max(1, self.content_height - area.height)
        thumb_y = track.y + (track.height - thumb_height) * self.scroll // maximum
        hovered = track.inflate(12, 0).collidepoint(mouse_pos())
        thumb_color = (130, 150, 210) if hovered else COLOR_BORDER
        pygame.draw.rect(surface, thumb_color, (track.x, thumb_y, 6, thumb_height), border_radius=3)
