"""A small multi-line Python code editor widget for pygame.

Features: syntax colours, auto-indent, undo, Vietnamese Telex input in strings/comments,
text selection (mouse drag, Shift + arrows, Ctrl+A), copy / cut / paste with the system
clipboard, and code suggestions while typing (Tab / Enter to accept).
"""

from __future__ import annotations

import keyword
import re

import pygame

from .completion import Suggestion, suggest
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
COLOR_SELECTION = (62, 82, 140)
COLOR_CURSOR = (255, 255, 255)
COLOR_BORDER_FOCUS = (98, 114, 164)
COLOR_POPUP = (44, 48, 66)
COLOR_POPUP_BORDER = (110, 130, 190)
COLOR_POPUP_ACTIVE = (70, 96, 170)
COLOR_POPUP_HINT = (165, 172, 200)

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

Position = tuple[int, int]


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


def _get_clipboard() -> str:
    try:
        text = pygame.scrap.get_text()
    except (pygame.error, AttributeError):
        return ""
    return (text or "").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


def _set_clipboard(text: str) -> None:
    try:
        pygame.scrap.put_text(text)
    except (pygame.error, AttributeError):
        return


class CodeEditor:
    def __init__(self, font: pygame.font.Font, hint_font: pygame.font.Font | None = None) -> None:
        self.font = font
        self.hint_font = hint_font or font
        self.char_width = font.size("M")[0]
        self.line_height = font.get_linesize() + 2
        self.lines: list[str] = [""]
        self.row = 0
        self.column = 0
        self.anchor: Position | None = None
        self.dragging = False
        self.scroll = 0
        self.focused = True
        self.error_line: int | None = None
        self.undo_stack: list[tuple[list[str], int, int]] = []
        self.blink_timer = 0.0
        self.rect = pygame.Rect(0, 0, 100, 100)
        self.gutter_width = self.char_width * 4
        self.vietnamese = True
        self.extra_names: list[str] = []
        self.suggestions: list[Suggestion] = []
        self.suggest_index = 0
        self.suggest_start = 0
        self.popup_rows: list[pygame.Rect] = []

    # ------------------------------------------------------------ content
    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    def set_text(self, text: str) -> None:
        self.lines = text.replace("\t", INDENT).replace("\r\n", "\n").rstrip("\n").split("\n") or [""]
        self.row = len(self.lines) - 1
        self.column = len(self.lines[self.row])
        self.anchor = None
        self.scroll = 0
        self.error_line = None
        self.undo_stack.clear()
        self.close_suggestions()

    def _save_undo(self) -> None:
        self.undo_stack.append((list(self.lines), self.row, self.column))
        if len(self.undo_stack) > 200:
            self.undo_stack.pop(0)

    def undo(self) -> None:
        if not self.undo_stack:
            return
        self.lines, self.row, self.column = self.undo_stack.pop()
        self.anchor = None
        self.close_suggestions()

    # ------------------------------------------------------------ selection
    def selection(self) -> tuple[Position, Position] | None:
        if self.anchor is None or self.anchor == (self.row, self.column):
            return None
        cursor = (self.row, self.column)
        return (min(self.anchor, cursor), max(self.anchor, cursor))

    def selected_text(self) -> str:
        span = self.selection()
        if span is None:
            return ""
        (start_row, start_col), (end_row, end_col) = span
        if start_row == end_row:
            return self.lines[start_row][start_col:end_col]
        parts = [self.lines[start_row][start_col:]]
        parts += self.lines[start_row + 1 : end_row]
        parts.append(self.lines[end_row][:end_col])
        return "\n".join(parts)

    def _delete_selection(self) -> bool:
        """Remove the selected text (caller saves undo). Returns True if something was removed."""
        span = self.selection()
        self.anchor = None
        if span is None:
            return False
        (start_row, start_col), (end_row, end_col) = span
        self.lines[start_row] = self.lines[start_row][:start_col] + self.lines[end_row][end_col:]
        del self.lines[start_row + 1 : end_row + 1]
        self.row, self.column = start_row, start_col
        return True

    def select_all(self) -> None:
        self.anchor = (0, 0)
        self.row = len(self.lines) - 1
        self.column = len(self.lines[self.row])

    # ------------------------------------------------------------ editing
    def insert(self, text: str) -> None:
        self._save_undo()
        self.error_line = None
        self._delete_selection()
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
        self._delete_selection()
        self._split_line(auto_indent=True)

    def backspace(self) -> None:
        self._save_undo()
        self.error_line = None
        if self._delete_selection():
            return
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
        self.error_line = None
        if self._delete_selection():
            return
        line = self.lines[self.row]
        if self.column < len(line):
            self.lines[self.row] = line[: self.column] + line[self.column + 1 :]
        elif self.row < len(self.lines) - 1:
            self.lines[self.row] = line + self.lines[self.row + 1]
            del self.lines[self.row + 1]

    def _selected_rows(self) -> range:
        span = self.selection()
        if span is None:
            return range(self.row, self.row + 1)
        (start_row, _), (end_row, end_col) = span
        if end_col == 0 and end_row > start_row:
            end_row -= 1
        return range(start_row, end_row + 1)

    def indent_lines(self) -> None:
        self._save_undo()
        for row in self._selected_rows():
            self.lines[row] = INDENT + self.lines[row]
        if self.anchor is not None:
            self.anchor = (self.anchor[0], self.anchor[1] + len(INDENT))
        self.column += len(INDENT)

    def dedent(self) -> None:
        self._save_undo()
        for row in self._selected_rows():
            if self.lines[row].startswith(INDENT):
                self.lines[row] = self.lines[row][len(INDENT) :]
                if row == self.row:
                    self.column = max(0, self.column - len(INDENT))
                if self.anchor is not None and row == self.anchor[0]:
                    self.anchor = (self.anchor[0], max(0, self.anchor[1] - len(INDENT)))

    # ------------------------------------------------------------ clipboard
    def copy(self) -> None:
        """Copy the selection; with no selection copy the whole current line."""
        text = self.selected_text() or self.lines[self.row] + "\n"
        _set_clipboard(text)

    def cut(self) -> None:
        if self.selection() is None:
            _set_clipboard(self.lines[self.row] + "\n")
            self._save_undo()
            if len(self.lines) > 1:
                del self.lines[self.row]
                self.row = min(self.row, len(self.lines) - 1)
            else:
                self.lines = [""]
            self.column = min(self.column, len(self.lines[self.row]))
            return
        _set_clipboard(self.selected_text())
        self._save_undo()
        self._delete_selection()

    def paste(self) -> None:
        text = _get_clipboard()
        if text:
            self.insert(text)

    def shortcut(self, name: str) -> None:
        """Run a Ctrl shortcut: "a" select all, "c" copy, "x" cut, "v" paste, "z" undo."""
        actions = {"z": self.undo, "a": self.select_all, "c": self.copy, "x": self.cut, "v": self.paste}
        if name not in actions:
            return
        actions[name]()
        self.blink_timer = 0.0
        if name != "c":
            self.close_suggestions()

    # ------------------------------------------------------------ suggestions
    def close_suggestions(self) -> None:
        self.suggestions = []
        self.suggest_index = 0

    def refresh_suggestions(self) -> None:
        if self.selection() is not None:
            self.close_suggestions()
            return
        start, items = suggest(self.lines, self.row, self.column, self.extra_names)
        self.suggest_start = start
        self.suggestions = items
        self.suggest_index = 0

    def accept_suggestion(self, index: int | None = None) -> None:
        if not self.suggestions:
            return
        item = self.suggestions[self.suggest_index if index is None else index]
        self._save_undo()
        line = self.lines[self.row]
        self.lines[self.row] = line[: self.suggest_start] + item.insert + line[self.column :]
        self.column = self.suggest_start + len(item.insert) - item.cursor_back
        self.close_suggestions()

    # ------------------------------------------------------------ events
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.popup_rows):
                if self.suggestions and rect.collidepoint(event.pos):
                    self.accept_suggestion(index)
                    return True
            self.focused = self.rect.collidepoint(event.pos)
            if self.focused:
                self.close_suggestions()
                shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
                if not shift or self.anchor is None:
                    self.anchor = None
                previous = (self.row, self.column)
                self._click(event.pos)
                if shift:
                    self.anchor = self.anchor or previous
                else:
                    self.anchor = (self.row, self.column)
                self.dragging = True
            return self.focused
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self._click(event.pos)
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            if self.anchor == (self.row, self.column):
                self.anchor = None
            return True
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(mouse_pos()):
            self.scroll = max(0, min(len(self.lines) - 1, self.scroll - event.y * 3))
            return True
        if not self.focused:
            return False
        if event.type == pygame.TEXTINPUT:
            if not self._try_telex(event.text):
                self.insert(event.text)
                self.refresh_suggestions()
            return True
        if event.type == pygame.KEYDOWN:
            return self._key(event)
        return False

    def handle_escape(self) -> bool:
        """Close the suggestion popup / selection first. Returns True if Escape was used."""
        if self.suggestions:
            self.close_suggestions()
            return True
        if self.selection() is not None:
            self.anchor = None
            return True
        return False

    def _try_telex(self, text: str) -> bool:
        """Apply Telex inside strings and comments only, so Python code stays untouched."""
        if not self.vietnamese or len(text) != 1 or not text.isascii() or not text.isalpha():
            return False
        if self.selection() is not None:
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
        self.close_suggestions()
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

        if self.suggestions and not control:
            if key == pygame.K_DOWN:
                self.suggest_index = (self.suggest_index + 1) % len(self.suggestions)
                return True
            if key == pygame.K_UP:
                self.suggest_index = (self.suggest_index - 1) % len(self.suggestions)
                return True
            if key in (pygame.K_TAB, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.accept_suggestion()
                return True

        if control:
            letters = {pygame.K_z: "z", pygame.K_a: "a", pygame.K_c: "c", pygame.K_x: "x", pygame.K_v: "v"}
            if key in letters:
                self.shortcut(letters[key])
                return True
            if key == pygame.K_SPACE:
                self.refresh_suggestions()
                return True
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return False

        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.newline()
            self.close_suggestions()
        elif key == pygame.K_BACKSPACE:
            self.backspace()
            if self.suggestions:
                self.refresh_suggestions()
        elif key == pygame.K_DELETE:
            self.delete()
            self.close_suggestions()
        elif key == pygame.K_TAB:
            if shift:
                self.dedent()
            elif self.selection() is not None:
                self.indent_lines()
            else:
                self.insert(INDENT)
        elif key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_HOME, pygame.K_END):
            self._navigate(key, shift)
            self.close_suggestions()
        else:
            return False
        return True

    def _navigate(self, key: int, extend: bool) -> None:
        if extend and self.anchor is None:
            self.anchor = (self.row, self.column)
        elif not extend:
            span = self.selection()
            self.anchor = None
            if span is not None and key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.row, self.column = span[0] if key == pygame.K_LEFT else span[1]
                return
        if key == pygame.K_LEFT:
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

        span = self.selection()
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
            elif line_index == self.row and self.focused and span is None:
                pygame.draw.rect(surface, COLOR_CURRENT_LINE, line_rect)
            if span is not None:
                self._draw_selection_row(surface, span, line_index, text_x, y)

            number = self.font.render(str(line_index + 1).rjust(3), True, COLOR_LINE_NUMBER)
            surface.blit(number, (rect.x + 4, y))

            x = text_x
            for text, color in highlight(self.lines[line_index]):
                rendered = self.font.render(text, True, color)
                surface.blit(rendered, (x, y))
                x += self.char_width * len(text)

        cursor_x = text_x + self.column * self.char_width
        cursor_y = rect.y + 6 + (self.row - self.scroll) * self.line_height
        if self.focused and (self.blink_timer % 1.0) < 0.6:
            pygame.draw.line(surface, COLOR_CURSOR, (cursor_x, cursor_y), (cursor_x, cursor_y + self.line_height - 3), 2)

        surface.set_clip(previous_clip)
        if self.focused:
            pygame.draw.rect(surface, COLOR_BORDER_FOCUS, rect, width=2, border_radius=8)
        self._draw_popup(surface, text_x + self.suggest_start * self.char_width, cursor_y)

    def _draw_selection_row(
        self,
        surface: pygame.Surface,
        span: tuple[Position, Position],
        line_index: int,
        text_x: int,
        y: int,
    ) -> None:
        (start_row, start_col), (end_row, end_col) = span
        if not start_row <= line_index <= end_row:
            return
        line_length = len(self.lines[line_index])
        first = start_col if line_index == start_row else 0
        last = end_col if line_index == end_row else line_length + 1
        if last <= first:
            return
        box = pygame.Rect(text_x + first * self.char_width, y - 1, (last - first) * self.char_width, self.line_height)
        pygame.draw.rect(surface, COLOR_SELECTION, box)

    def _draw_popup(self, surface: pygame.Surface, x: int, cursor_y: int) -> None:
        self.popup_rows = []
        if not self.suggestions or not self.focused:
            return
        row_height = self.line_height + 4
        labels = [self.font.render(item.label, True, COLOR_TEXT) for item in self.suggestions]
        hints = [self.hint_font.render(item.hint, True, COLOR_POPUP_HINT) for item in self.suggestions]
        label_width = max(label.get_width() for label in labels)
        width = min(self.rect.width - 8, label_width + 24 + max(hint.get_width() for hint in hints) + 16)
        height = row_height * len(self.suggestions) + 26
        box = pygame.Rect(x, cursor_y + self.line_height + 2, width, height)
        if box.bottom > surface.get_height() - 4:
            box.bottom = cursor_y - 2
        box.right = min(box.right, self.rect.right - 4)
        box.left = max(box.left, self.rect.left + 4)

        pygame.draw.rect(surface, COLOR_POPUP, box, border_radius=6)
        pygame.draw.rect(surface, COLOR_POPUP_BORDER, box, width=1, border_radius=6)
        previous_clip = surface.get_clip()
        surface.set_clip(box)
        for index, (label, hint) in enumerate(zip(labels, hints, strict=True)):
            row_rect = pygame.Rect(box.x + 2, box.y + 3 + index * row_height, box.width - 4, row_height)
            if index == self.suggest_index:
                pygame.draw.rect(surface, COLOR_POPUP_ACTIVE, row_rect, border_radius=4)
            surface.blit(label, (row_rect.x + 8, row_rect.y + 2))
            surface.blit(hint, (row_rect.x + 16 + label_width, row_rect.y + 3))
            self.popup_rows.append(row_rect)
        footer = self.hint_font.render("Tab / Enter: chọn  ·  ↑↓: đổi  ·  Esc: đóng", True, COLOR_POPUP_HINT)
        surface.blit(footer, (box.x + 10, box.bottom - 22))
        surface.set_clip(previous_clip)
