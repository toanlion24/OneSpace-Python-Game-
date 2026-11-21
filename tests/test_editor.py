import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from codequest import editor as editor_module
from codequest.completion import suggest
from codequest.editor import CodeEditor


@pytest.fixture
def clipboard(monkeypatch):
    store = {"text": ""}
    monkeypatch.setattr(editor_module, "_set_clipboard", lambda text: store.update(text=text))
    monkeypatch.setattr(editor_module, "_get_clipboard", lambda: store["text"])
    return store


@pytest.fixture
def editor():
    pygame.display.init()
    pygame.font.init()
    widget = CodeEditor(pygame.font.SysFont("consolas", 16))
    widget.vietnamese = False
    return widget


def press(widget, key, mod=0):
    widget.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod, unicode=""))


def type_text(widget, text):
    for char in text:
        widget.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=char))


def test_select_all_copy_and_paste(editor, clipboard):
    editor.set_text("hero.move_right(2)\nhero.say(\"hi\")")
    press(editor, pygame.K_a, pygame.KMOD_CTRL)
    press(editor, pygame.K_c, pygame.KMOD_CTRL)
    assert clipboard["text"] == "hero.move_right(2)\nhero.say(\"hi\")"
    press(editor, pygame.K_v, pygame.KMOD_CTRL)
    assert editor.text == "hero.move_right(2)\nhero.say(\"hi\")"


def test_shift_arrows_select_and_typing_replaces(editor):
    editor.set_text("steps = 1")
    for _ in range(1):
        press(editor, pygame.K_LEFT, pygame.KMOD_SHIFT)
    assert editor.selected_text() == "1"
    type_text(editor, "7")
    assert editor.text == "steps = 7"


def test_cut_selection_and_paste_elsewhere(editor, clipboard):
    editor.set_text("abc def")
    editor.anchor = (0, 4)
    editor.column = 7
    press(editor, pygame.K_x, pygame.KMOD_CTRL)
    assert editor.text == "abc "
    assert clipboard["text"] == "def"
    editor.column = 0
    press(editor, pygame.K_v, pygame.KMOD_CTRL)
    assert editor.text == "defabc "


def test_copy_without_selection_copies_current_line(editor, clipboard):
    editor.set_text("line one\nline two")
    editor.row, editor.column = 0, 2
    press(editor, pygame.K_c, pygame.KMOD_CTRL)
    assert clipboard["text"] == "line one\n"


def test_paste_multiline_from_windows(editor, clipboard):
    editor.set_text("")
    clipboard["text"] = "for i in range(2):\n    hero.move_right()"
    press(editor, pygame.K_v, pygame.KMOD_CTRL)
    assert editor.lines == ["for i in range(2):", "    hero.move_right()"]


def test_backspace_deletes_selection_and_undo_restores(editor):
    editor.set_text("hero.move_right(2)\nhero.move_down(3)")
    press(editor, pygame.K_a, pygame.KMOD_CTRL)
    press(editor, pygame.K_BACKSPACE)
    assert editor.text == ""
    press(editor, pygame.K_z, pygame.KMOD_CTRL)
    assert editor.text == "hero.move_right(2)\nhero.move_down(3)"


def test_tab_indents_selected_lines(editor):
    editor.set_text("a = 1\nb = 2")
    press(editor, pygame.K_a, pygame.KMOD_CTRL)
    press(editor, pygame.K_TAB)
    assert editor.lines == ["    a = 1", "    b = 2"]
    press(editor, pygame.K_TAB, pygame.KMOD_SHIFT)
    assert editor.lines == ["a = 1", "b = 2"]


def test_typing_shows_suggestions_and_tab_accepts(editor):
    editor.set_text("")
    type_text(editor, "hero.mo")
    labels = [item.label for item in editor.suggestions]
    assert "move_right(steps)" in labels
    assert all(label.startswith("mo") for label in labels)
    index = labels.index("move_right(steps)")
    editor.suggest_index = index
    press(editor, pygame.K_TAB)
    assert editor.text == "hero.move_right()"
    assert editor.column == len("hero.move_right(")
    type_text(editor, "3")
    assert editor.text == "hero.move_right(3)"


def test_enter_accepts_suggestion_instead_of_new_line(editor):
    editor.set_text("")
    type_text(editor, "pri")
    assert editor.suggestions[0].label.startswith("print")
    press(editor, pygame.K_RETURN)
    assert editor.lines == ["print()"]


def test_escape_closes_suggestions(editor):
    editor.set_text("")
    type_text(editor, "ra")
    assert editor.suggestions
    assert editor.handle_escape()
    assert not editor.suggestions


def test_no_suggestions_inside_strings_and_comments():
    assert suggest(['hero.say("pri'], 0, len('hero.say("pri'))[1] == []
    assert suggest(["# pri"], 0, 5)[1] == []


def test_suggestions_include_names_from_code_and_level_data():
    lines = ["total_gems = 3", "to"]
    _, items = suggest(lines, 1, 2, extra_names=["tokens_list"])
    labels = [item.label for item in items]
    assert "total_gems" in labels
    assert "tokens_list" in labels


def test_module_members_after_import_alias():
    lines = ["import numpy as np", "np.ar"]
    _, items = suggest(lines, 1, len("np.ar"))
    assert items[0].label.startswith("array")
    lines = ["import math", "math.sq"]
    assert suggest(lines, 1, len("math.sq"))[1][0].label.startswith("sqrt")


def test_import_suggests_allowed_modules():
    _, items = suggest(["import ite"], 0, len("import ite"))
    assert [item.label for item in items] == ["itertools"]


def test_mouse_drag_selects_text(editor):
    editor.set_text("hero.move_right(2)\nhero.say(\"hi\")")
    editor.rect = pygame.Rect(0, 0, 600, 300)
    text_left = editor.gutter_width + 8
    first_row_y = 6 + editor.line_height // 2

    def at(column, row):
        return (text_left + column * editor.char_width, first_row_y + row * editor.line_height)

    editor.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=at(0, 0)))
    editor.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=at(4, 0), buttons=(1, 0, 0)))
    editor.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=at(4, 0)))
    assert editor.selected_text() == "hero"


def test_click_on_suggestion_inserts_it(editor):
    editor.set_text("")
    editor.rect = pygame.Rect(0, 0, 600, 300)
    surface = pygame.Surface((800, 600))
    type_text(editor, "hero.sa")
    editor.draw(surface, editor.rect)
    assert editor.popup_rows
    editor.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=editor.popup_rows[0].center))
    assert editor.text == "hero.say()"
