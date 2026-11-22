import ast

import pygame
import pytest

from codequest.glossary import GLOSSARY, find_terms, theory_text
from codequest.lessons import WORLD_LESSONS, lesson_for_world
from codequest.levels import WORLDS, all_levels
from codequest.theory import THEORY
from codequest.theory_view import TheoryView

from .conftest import SOLUTIONS

LEVELS = all_levels()


@pytest.fixture(scope="module")
def view():
    pygame.font.init()
    font = pygame.font.Font(None, 22)
    return TheoryView(font, font, font, font)


def build(view, level_id="2-1", lesson_world=2):
    level = next(level for level in LEVELS if level.id == level_id)
    view.clock = lambda: 0
    view.build(
        title="Lý thuyết",
        tag="Kỹ năng",
        theory=THEORY[level_id],
        rect=pygame.Rect(16, 64, 736, 640),
        inputs=level.extra_globals,
        goal=level.goal,
        lesson=lesson_for_world(lesson_world),
    )


def test_every_world_has_a_lesson():
    assert {world.number for world in WORLDS} == set(WORLD_LESSONS)


@pytest.mark.parametrize("number", sorted(WORLD_LESSONS))
def test_lesson_walkthrough_is_valid_python_and_not_a_solution(number):
    lesson = WORLD_LESSONS[number]
    assert lesson.analogy and lesson.syntax and lesson.tips
    walkthrough = "\n".join(code for code, _note in lesson.walkthrough)
    ast.parse(walkthrough)
    if SOLUTIONS is not None:
        assert all(walkthrough.strip() != solution.strip() for solution in SOLUTIONS.values())


def test_glossary_terms_are_unique_and_explained():
    names = [glossary_term.term for glossary_term in GLOSSARY]
    assert len(names) == len(set(names))
    assert all(len(glossary_term.meaning) > 20 for glossary_term in GLOSSARY)


def test_find_terms_follows_text_order():
    terms = [glossary_term.term for glossary_term in find_terms("Truyền THAM SỐ, rồi gặp NameError.")]
    assert terms == ["Tham số", "NameError"]


def test_key_term_ignores_game_keys_and_doors():
    assert find_terms("Nhặt chìa khoá rồi mở cửa khoá.") == []
    assert [term.term for term in find_terms("Tra giá trị theo khoá của dict.")] == ["Khoá (key)", "Dict (từ điển)"]


@pytest.mark.parametrize("level", LEVELS, ids=[level.id for level in LEVELS])
def test_every_level_explains_some_terms(level):
    assert find_terms(theory_text(THEORY[level.id]))


def test_view_shows_lesson_and_glossary(view):
    build(view)
    text = view.copy_text()
    assert "Hiểu kỹ hơn" in text
    assert "\n\nTừ khó trong bài" in text
    assert "Biến: Một chiếc hộp" in text
    assert "coins = coins - price" in text


def test_copy_all_without_selection(view):
    build(view)
    assert view.copy() == "copied"
    assert view.copied_character_count == len(view.copy_text().strip())


def line_index_of(view, text):
    return next(index for index, line in enumerate(view.lines) if line.text == text)


def screen_point(view, line_index, char_index):
    line = view.lines[line_index]
    view.scroll = max(0, line.top - 100)
    area = view.content_area
    return area.x + line.char_x[char_index], area.y - view.scroll + line.top + 4


def mouse(event_type, position):
    if event_type == pygame.MOUSEMOTION:
        return pygame.event.Event(event_type, pos=position, rel=(0, 0), buttons=(1, 0, 0))
    return pygame.event.Event(event_type, button=1, pos=position)


def test_drag_selects_characters_and_copies_on_release(view):
    build(view)
    view.clock = lambda: 0
    first = line_index_of(view, "coins = 10")
    start = screen_point(view, first, 0)
    end = (view.content_area.x + view.lines[first].char_x[5], start[1])
    assert view.handle_event(mouse(pygame.MOUSEBUTTONDOWN, start)) == "used"
    view.handle_event(mouse(pygame.MOUSEMOTION, end))
    assert view.handle_event(mouse(pygame.MOUSEBUTTONUP, end)) == "copied"
    assert view.copy_text() == "coins"


def test_drag_across_lines(view):
    build(view)
    view.clock = lambda: 0
    first = line_index_of(view, "coins = 10")
    start = screen_point(view, first, 0)
    price_line = view.lines[line_index_of(view, "price = 3")]
    end = (view.content_area.x + price_line.char_x[5], view.content_area.y - view.scroll + price_line.top + 4)
    view.handle_event(mouse(pygame.MOUSEBUTTONDOWN, start))
    view.handle_event(mouse(pygame.MOUSEMOTION, end))
    view.handle_event(mouse(pygame.MOUSEBUTTONUP, end))
    assert view.copy_text() == "coins = 10\n→ Tạo hộp coins, cất số 10.\nprice"


def test_double_click_selects_word_and_triple_click_copies_block(view):
    build(view)
    view.clock = lambda: 1000
    point = screen_point(view, line_index_of(view, "coins = coins - price"), 9)
    view.handle_event(mouse(pygame.MOUSEBUTTONDOWN, point))
    view.handle_event(mouse(pygame.MOUSEBUTTONUP, point))
    view.handle_event(mouse(pygame.MOUSEBUTTONDOWN, point))
    assert view.copy_text() == "coins"
    assert view.handle_event(mouse(pygame.MOUSEBUTTONDOWN, point)) == "copied"
    assert view.copy_text() == "coins = coins - price"


def test_triple_click_copies_whole_wrapped_paragraph(view):
    build(view)
    view.clock = lambda: 1000
    wrapped = next(index for index, line in enumerate(view.lines) if line.joins_previous)
    point = screen_point(view, wrapped, 2)
    for _click in range(3):
        result = view.handle_event(mouse(pygame.MOUSEBUTTONDOWN, point))
    assert result == "copied"
    copied = view.copy_text()
    assert view.lines[wrapped].text in copied
    assert "\n" not in copied


def test_slow_clicks_do_not_count_as_triple(view):
    build(view)
    times = iter([0, 1000, 2000])
    view.clock = lambda: next(times)
    point = screen_point(view, line_index_of(view, "coins = 10"), 2)
    results = [view.handle_event(mouse(pygame.MOUSEBUTTONDOWN, point)) for _click in range(3)]
    assert results == ["used", "used", "used"]


def test_ctrl_c_needs_selection(view):
    build(view)
    ctrl_c = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c, mod=pygame.KMOD_CTRL, unicode="c")
    assert view.handle_event(ctrl_c) is None
    view.select_all()
    assert view.handle_event(ctrl_c) == "copied"


def test_click_outside_clears_selection(view):
    build(view)
    view.select_all()
    assert view.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(1000, 300))) is None
    assert not view.has_selection
