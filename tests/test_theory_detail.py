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
    assert "HIỂU KỸ HƠN" in text
    assert "TỪ KHÓ TRONG BÀI" in text
    assert "Biến:" in text
    assert "coins = coins - price" in text


def test_copy_all_without_selection(view):
    build(view)
    assert view.copy() == "copied"
    assert view.copied_line_count == len(view.copy_lines)


def test_drag_selects_lines_and_copies_only_them(view):
    build(view)
    first_code = next(index for index, line in enumerate(view.copy_lines) if line[2] == "coins = 10")
    view.scroll = view.copy_lines[first_code][0] - 100
    top = view.rect.y + 22 - view.scroll
    start_y = top + view.copy_lines[first_code][0] + 2
    end_y = top + view.copy_lines[first_code + 2][0] + 2
    view.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, start_y)))
    view.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(100, end_y), rel=(0, 0), buttons=(1, 0, 0)))
    view.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(100, end_y)))
    copied = view.copy_text()
    assert copied.startswith("coins = 10")
    assert "KHÁI NIỆM" not in copied
    assert len(copied.strip().split("\n")) == 3


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
