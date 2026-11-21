"""A small multi-line Python code editor widget for pygame."""

from __future__ import annotations

import keyword
import re

import pygame

from .display import mouse_pos
from .telex import telex_key

INDENT = "    "

COLOR_TEXT = (220, 224, 235)
COLOR_KEYWORD = (255, 121, 198)
COLOR_STRING = (241, 250, 140)
COLOR_COMMENT = (110, 120, 150)
COLOR_NUMBER = (189, 147, 249)
COLOR_HERO = (80, 250, 123)
COLOR_BUILTIN = (139, 233, 253)
COLOR_BACKGROUND = (30, 32, 44)
COLOR_GUTTER = (24, 26, 36)
COLOR_LINE_NUMBER = (90, 96, 120)
COLOR_CURRENT_LINE = (40, 43, 58)
COLOR_ERROR_LINE = (110, 40, 52)
COLOR_CURSOR = (255, 255, 255)
COLOR_BORDER_FOCUS = (98, 114, 164)

BUILTINS = {
    "print", "len", "range", "int", "str", "float", "bool", "list", "dict", "set",
    "tuple", "sum", "min", "max", "sorted", "abs", "round", "enumerate", "zip",
    "DoorJammed", "True", "False", "None",
}

TOKEN_PATTERN = re.compile(
    r"(?P<comment>#.*)"
    r"|(?P<string>\"[^\"]*\"?|'[^']*'?)"
    r"|(?P<number>\b\d+(\.\d+)?\b)"
    r"|(?P<word>[A-Za-z_À-ỹ][\wÀ-ỹ]*)"
    r"|(?P<other>.)"
)


def in_text_context(line: str, column: int) -> bool:
    """True when `column` is inside a string literal or a comment."""
    quote: str | None = None
    for char in line[:column]:
        if quote:
            if char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char == "#":
            return True
    return quote is not None


def highlight(line: str) -> list[tuple[str, tuple[int, int, int]]]:
    tokens: list[tuple[str, tuple[int, int, int]]] = []
    for match in TOKEN_PATTERN.finditer(line):
        text = match.group(0)
        kind = match.lastgroup
        if kind == "comment":
            color = COLOR_COMMENT
        elif kind == "string":
            color = COLOR_STRING
        elif kind == "number":
            color = COLOR_NUMBER
        elif kind == "word" and text == "hero":
            color = COLOR_HERO
        elif kind == "word" and text in BUILTINS:
            color = COLOR_BUILTIN
        elif kind == "word" and keyword.iskeyword(text):
            color = COLOR_KEYWORD
        else:
            color = COLOR_TEXT
        tokens.append((text, color))
    return tokens


class CodeEditor:
    def __init__(self, font: pygame.font.Font) -> None:
        self.font = font
        self.char_width = font.size("M")[0]
        self.line_height = font.get_linesize() + 2
        self.lines: list[str] = [""]
        self.row = 0
        self.column = 0
        self.scroll = 0
        self.focused = True
        self.error_line: int | None = None
        self.undo_stack: list[tuple[list[str], int, int]] = []
        self.blink_timer = 0.0
        self.rect = pygame.Rect(0, 0, 100, 100)
        self.gutter_width = self.char_width * 4
        self.vietnamese = True

    # ------------------------------------------------------------ content
    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    def set_text(self, text: str) -> None:
        self.lines = text.replace("\t", INDENT).rstrip("\n").split("\n") or [""]
        self.row = len(self.lines) - 1
        self.column = len(self.lines[self.row])
        self.scroll = 0
        self.error_line = None
        self.undo_stack.clear()

    def _save_undo(self) -> None:
        self.undo_stack.append((list(self.lines), self.row, self.column))
        if len(self.undo_stack) > 200:
            self.undo_stack.pop(0)

    def undo(self) -> None:
        if not self.undo_stack:
            return
        self.lines, self.row, self.column = self.undo_stack.pop()

    def insert(self, text: str) -> None:
        self._save_undo()
        self.error_line = None
        for index, part in enumerate(text.replace("\r", "").replace("\t", INDENT).split("\n")):
            if index > 0:
                self._split_line(auto_indent=False)
            line = self.lines[self.row]
            self.lines[self.row] = line[: self.column] + part + line[self.column :]
            self.column += len(part)

    def _split_line(self, auto_indent: bool) -> None:
        line = self.lines[self.row]
        before, after = line[: self.column], line[self.column :]
        indent = ""
        if auto_indent:
            indent = before[: len(before) - len(before.lstrip(" "))]
            if before.rstrip().endswith(":"):
                indent += INDENT
        self.lines[self.row] = before
        self.lines.insert(self.row + 1, indent + after.lstrip(" ") if auto_indent else after)
        self.row += 1
        self.column = len(indent)

    def newline(self) -> None:
        self._save_undo()
        self.error_line = None
        self._split_line(auto_indent=True)

    def backspace(self) -> None:
        self._save_undo()
        self.error_line = None
        line = self.lines[self.row]
        if self.column > 0:
            before = line[: self.column]
            remove = 1
            if before.strip() == "":
                remove = len(before) % len(INDENT) or len(INDENT)
            self.lines[self.row] = line[: self.column - remove] + line[self.column :]
            self.column -= remove
        elif self.row > 0:
            previous = self.lines[self.row - 1]
            self.lines[self.row - 1] = previous + line
            del self.lines[self.row]
            self.row -= 1
            self.column = len(previous)

    def delete(self) -> None:
        self._save_undo()
        line = self.lines[self.row]
        if self.column < len(line):
            self.lines[self.row] = line[: self.column] + line[self.column + 1 :]
        elif self.row < len(self.lines) - 1:
            self.lines[self.row] = line + self.lines[self.row + 1]
            del self.lines[self.row + 1]

    def dedent(self) -> None:
        line = self.lines[self.row]
        if line.startswith(INDENT):
            self._save_undo()
            self.lines[self.row] = line[len(INDENT) :]
            self.column = max(0, self.column - len(INDENT))

    # ------------------------------------------------------------ events
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused = self.rect.collidepoint(event.pos)
            if self.focused:
                self._click(event.pos)
            return self.focused
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(mouse_pos()):
            self.scroll = max(0, min(len(self.lines) - 1, self.scroll - event.y * 3))
            return True
        if not self.focused:
            return False
        if event.type == pygame.TEXTINPUT:
            if not self._try_telex(event.text):
                self.insert(event.text)
            return True
        if event.type == pygame.KEYDOWN:
            return self._key(event)
        return False

    def _try_telex(self, text: str) -> bool:
        """Apply Telex inside strings and comments only, so Python code stays untouched."""
        if not self.vietnamese or len(text) != 1 or not text.isascii() or not text.isalpha():
            return False
        line = self.lines[self.row]
        if not in_text_context(line, self.column):
            return False
        word_start = self.column
        while word_start > 0 and line[word_start - 1].isalpha():
            word_start -= 1
        word = line[word_start : self.column]
        new_word = telex_key(word, text)
        self._save_undo()
        self.error_line = None
        self.lines[self.row] = line[:word_start] + new_word + line[self.column :]
        self.column = word_start + len(new_word)
        return True

    def _click(self, position: tuple[int, int]) -> None:
        relative_y = position[1] - self.rect.y - 6
        self.row = max(0, min(len(self.lines) - 1, self.scroll + relative_y // self.line_height))
        relative_x = position[0] - self.rect.x - self.gutter_width - 8
        self.column = max(0, min(len(self.lines[self.row]), round(relative_x / self.char_width)))
        self.blink_timer = 0.0

    def _key(self, event: pygame.event.Event) -> bool:
        control = event.mod & pygame.KMOD_CTRL
        shift = event.mod & pygame.KMOD_SHIFT
        key = event.key
        self.blink_timer = 0.0

        if control and key == pygame.K_z:
            self.undo()
        elif control and key == pygame.K_v:
            self._paste()
        elif control and key == pygame.K_c:
            self._copy_all()
        elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            if control:
                return False
            self.newline()
        elif key == pygame.K_BACKSPACE:
            self.backspace()
        elif key == pygame.K_DELETE:
            self.delete()
        elif key == pygame.K_TAB:
            if shift:
                self.dedent()
            else:
                self.insert(INDENT)
        elif key == pygame.K_LEFT:
            self._move_horizontal(-1)
        elif key == pygame.K_RIGHT:
            self._move_horizontal(1)
        elif key == pygame.K_UP:
            self._move_vertical(-1)
        elif key == pygame.K_DOWN:
            self._move_vertical(1)
        elif key == pygame.K_HOME:
            line = self.lines[self.row]
            first_char = len(line) - len(line.lstrip(" "))
            self.column = 0 if self.column == first_char else first_char
        elif key == pygame.K_END:
            self.column = len(self.lines[self.row])
        else:
            return False
        return True

    def _move_horizontal(self, delta: int) -> None:
        self.column += delta
        if self.column < 0 and self.row > 0:
            self.row -= 1
            self.column = len(self.lines[self.row])
        elif self.column > len(self.lines[self.row]) and self.row < len(self.lines) - 1:
            self.row += 1
            self.column = 0
        self.column = max(0, min(self.column, len(self.lines[self.row])))

    def _move_vertical(self, delta: int) -> None:
        self.row = max(0, min(len(self.lines) - 1, self.row + delta))
        self.column = min(self.column, len(self.lines[self.row]))

    def _paste(self) -> None:
        try:
            text = pygame.scrap.get_text()
        except (pygame.error, AttributeError):
            return
        if text:
            self.insert(text.replace("\x00", ""))

    def _copy_all(self) -> None:
        try:
            pygame.scrap.put_text(self.text)
        except (pygame.error, AttributeError):
            return

    # ------------------------------------------------------------ drawing
    def update(self, delta_seconds: float) -> None:
        self.blink_timer += delta_seconds

    def draw(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        self.rect = rect
        pygame.draw.rect(surface, COLOR_BACKGROUND, rect, border_radius=8)
        gutter = pygame.Rect(rect.x, rect.y, self.gutter_width + 4, rect.height)
        pygame.draw.rect(surface, COLOR_GUTTER, gutter, border_top_left_radius=8, border_bottom_left_radius=8)

        visible_rows = max(1, (rect.height - 12) // self.line_height)
        if self.row < self.scroll:
            self.scroll = self.row
        elif self.row >= self.scroll + visible_rows:
            self.scroll = self.row - visible_rows + 1

        previous_clip = surface.get_clip()
        surface.set_clip(rect)
        text_x = rect.x + self.gutter_width + 8
        for screen_index in range(visible_rows):
            line_index = self.scroll + screen_index
            if line_index >= len(self.lines):
                break
            y = rect.y + 6 + screen_index * self.line_height
            line_rect = pygame.Rect(rect.x + gutter.width, y - 1, rect.width - gutter.width, self.line_height)
            if self.error_line == line_index + 1:
                pygame.draw.rect(surface, COLOR_ERROR_LINE, line_rect)
            elif line_index == self.row and self.focused:
                pygame.draw.rect(surface, COLOR_CURRENT_LINE, line_rect)

            number = self.font.render(str(line_index + 1).rjust(3), True, COLOR_LINE_NUMBER)
            surface.blit(number, (rect.x + 4, y))

            x = text_x
            for text, color in highlight(self.lines[line_index]):
                rendered = self.font.render(text, True, color)
                surface.blit(rendered, (x, y))
                x += self.char_width * len(text)

        if self.focused and (self.blink_timer % 1.0) < 0.6:
            cursor_x = text_x + self.column * self.char_width
            cursor_y = rect.y + 6 + (self.row - self.scroll) * self.line_height
            pygame.draw.line(surface, COLOR_CURSOR, (cursor_x, cursor_y), (cursor_x, cursor_y + self.line_height - 3), 2)

        surface.set_clip(previous_clip)
        if self.focused:
            pygame.draw.rect(surface, COLOR_BORDER_FOCUS, rect, width=2, border_radius=8)
