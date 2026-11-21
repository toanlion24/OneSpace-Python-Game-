"""Pygame front-end: level select, code editor and animated playback."""

from __future__ import annotations

import ctypes
import json
import sys
from collections.abc import Callable
from typing import Any

import pygame

from .assets import APP_TITLE, TILE, Assets, load_logo, load_logo_icon, user_data_dir
from .display import VIEWPORT, mouse_pos, to_logical_event
from .editor import CodeEditor
from .engine import MAX_HERO_HP, Level, RunResult, World, requirement_label, run_code
from .levels import STAGES, WORLDS, all_levels, world_of
from .theory import THEORY
from .theory_view import TheoryView

SCREEN_SIZE = (1280, 720)
FPS = 60
PROGRESS_FILE = user_data_dir() / "progress.json"

VIEW_RECT = pygame.Rect(16, 64, 736, 440)
CONSOLE_RECT = pygame.Rect(16, 516, 736, 188)
THEORY_RECT = pygame.Rect(16, 64, 736, 640)
MENU_LEFT = 64
MENU_TAB_Y = 132
MENU_TAB_WIDTH = 224
MENU_WORLDS_Y = 340
MENU_ROWS_PER_COLUMN = 5
INFO_RECT = pygame.Rect(768, 64, 496, 196)
EDITOR_RECT = pygame.Rect(768, 270, 496, 372)
BUTTON_Y = 652

COLOR_PANEL = (22, 24, 34)
COLOR_PANEL_BORDER = (60, 66, 92)
COLOR_TEXT = (230, 232, 240)
COLOR_MUTED = (150, 156, 180)
COLOR_ACCENT = (255, 196, 64)
COLOR_GOOD = (90, 220, 120)
COLOR_BAD = (255, 98, 98)
COLOR_INFO = (130, 200, 255)

EVENT_DURATIONS: dict[str, float] = {
    "move": 0.22,
    "bump": 0.25,
    "attack": 0.35,
    "say": 0.7,
    "print": 0.15,
    "info": 0.2,
    "hurt": 0.4,
    "heal": 0.5,
    "gem": 0.05,
    "door_open": 0.3,
    "jam": 0.35,
    "die": 0.8,
    "fail": 0.1,
}


def wrap_text(text: str, font: pygame.font.Font, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split(" "):
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        lines.append(current)
    return lines


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, alpha: int = 225) -> None:
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*COLOR_PANEL, alpha), panel.get_rect(), border_radius=10)
    surface.blit(panel, rect.topleft)
    pygame.draw.rect(surface, COLOR_PANEL_BORDER, rect, width=2, border_radius=10)


class Button:
    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        on_click: Callable[[], None],
        color: tuple[int, int, int] = (70, 80, 120),
    ) -> None:
        self.rect = rect
        self.label = label
        self.on_click = on_click
        self.color = color

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.on_click()
            return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        hovered = self.rect.collidepoint(mouse_pos())
        color = tuple(min(255, channel + 30) for channel in self.color) if hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255, 40), self.rect, width=1, border_radius=8)
        label = font.render(self.label, True, COLOR_TEXT)
        surface.blit(label, label.get_rect(center=self.rect.center))


class Progress:
    def __init__(self) -> None:
        self.completed: set[str] = set()
        self.code: dict[str, str] = {}
        if PROGRESS_FILE.exists():
            try:
                data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
                self.completed = set(data.get("completed", []))
                self.code = dict(data.get("code", {}))
            except (OSError, ValueError):
                pass

    def save(self) -> None:
        data = {"completed": sorted(self.completed), "code": self.code}
        PROGRESS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class Playback:
    """Replays recorded engine events as an animation."""

    def __init__(self, level: Level) -> None:
        self.level = level
        self.terrain_world = World(level)
        self.events: list[dict[str, Any]] = []
        self.result: RunResult | None = None
        self.reset()

    def reset(self) -> None:
        world = self.terrain_world
        self.hero_position = pygame.Vector2(world.hero_start)
        self.facing = "right"
        self.hp = self.level.start_hp
        self.gems = dict(world.gems)
        self.enemies = {pos: enemy.kind for pos, enemy in world.enemies.items()}
        self.doors = dict(world.doors)
        self.dying_enemies: dict[tuple[int, int], tuple[str, float]] = {}
        self.enemy_flash: dict[tuple[int, int], float] = {}
        self.door_shake: dict[tuple[int, int], float] = {}
        self.bubble: tuple[str, float] | None = None
        self.floaters: list[list[Any]] = []
        self.hero_state = "idle"
        self.hero_state_time = 0.0
        self.dead = False
        self.events = []
        self.index = 0
        self.event_time = 0.0
        self.event_started = False
        self.finished = True
        self.result = None

    def start(self, result: RunResult) -> None:
        self.reset()
        self.result = result
        self.events = result.events
        self.finished = False

    def update(self, delta_seconds: float, speed: float, log: Callable[[str, tuple[int, int, int]], None]) -> bool:
        """Advance the animation. Returns True on the frame the playback ends."""
        self.hero_state_time += delta_seconds
        self._update_effects(delta_seconds)
        if self.finished:
            return False

        scaled = delta_seconds * speed
        while scaled > 0 and self.index < len(self.events):
            event = self.events[self.index]
            if not self.event_started:
                self._begin(event, log)
                self.event_started = True
            duration = EVENT_DURATIONS.get(event["type"], 0.1)
            used = min(scaled, duration - self.event_time)
            self.event_time += used
            scaled -= used
            self._progress(event, self.event_time / duration)
            if self.event_time >= duration:
                self._end(event)
                self.index += 1
                self.event_time = 0.0
                self.event_started = False
            else:
                break

        if self.index >= len(self.events):
            self.finished = True
            if self.hero_state == "run":
                self._set_hero_state("idle")
            return True
        return False

    def _set_hero_state(self, state: str) -> None:
        if self.hero_state != state:
            self.hero_state = state
            self.hero_state_time = 0.0

    def _float(self, text: str, color: tuple[int, int, int], position: pygame.Vector2) -> None:
        self.floaters.append([text, color, pygame.Vector2(position), 1.0])

    def _begin(self, event: dict[str, Any], log: Callable[[str, tuple[int, int, int]], None]) -> None:
        kind = event["type"]
        if kind == "move":
            self.facing = event["direction"]
            self._set_hero_state("run")
        elif kind == "bump":
            self.facing = event["direction"]
            self._set_hero_state("hit")
        elif kind == "attack":
            self.facing = event["direction"]
            self._set_hero_state("jump")
            target = tuple(event["target"])
            if event["hit"]:
                self.enemy_flash[target] = 0.3
        elif kind == "say":
            self.bubble = (event["text"], 2.2)
            log(f"Hero: {event['text']}", COLOR_ACCENT)
        elif kind == "print":
            log(event["text"], COLOR_TEXT)
        elif kind == "info":
            log(event["text"], COLOR_INFO)
        elif kind == "hurt":
            self.hp = event["hp"]
            self._set_hero_state("hit")
            self._float("-1 ♥", COLOR_BAD, self.hero_position)
            log(event["text"], COLOR_BAD)
        elif kind == "heal":
            self.hp = event["hp"]
            self._float(f"+{event['amount']} ♥", COLOR_GOOD, self.hero_position)
            log(f"Hồi {event['amount']} máu.", COLOR_GOOD)
        elif kind == "gem":
            position = tuple(event["pos"])
            self.gems.pop(position, None)
            self._float("+1", COLOR_ACCENT, pygame.Vector2(position))
        elif kind == "door_open":
            self.doors.pop(tuple(event["pos"]), None)
            log("Cửa đã mở!", COLOR_GOOD)
        elif kind == "jam":
            self.door_shake[tuple(event["pos"])] = 0.35
            log("DoorJammed: cửa bị kẹt!", COLOR_BAD)
        elif kind == "die":
            self._set_hero_state("hit")
            self.dead = True

    def _progress(self, event: dict[str, Any], fraction: float) -> None:
        if event["type"] == "move":
            source = pygame.Vector2(event["src"])
            destination = pygame.Vector2(event["dst"])
            self.hero_position = source.lerp(destination, min(1.0, fraction))

    def _end(self, event: dict[str, Any]) -> None:
        kind = event["type"]
        if kind == "move":
            self.hero_position = pygame.Vector2(event["dst"])
            next_event = self.events[self.index + 1] if self.index + 1 < len(self.events) else None
            if next_event is None or next_event["type"] not in ("move", "gem"):
                self._set_hero_state("idle")
        elif kind in ("bump", "attack", "hurt") and not self.dead:
            self._set_hero_state("idle")
        if kind == "attack" and event.get("killed"):
            target = tuple(event["target"])
            enemy_kind = self.enemies.pop(target, None)
            if enemy_kind:
                self.dying_enemies[target] = (enemy_kind, 0.5)

    def _update_effects(self, delta_seconds: float) -> None:
        if self.bubble:
            text, remaining = self.bubble
            remaining -= delta_seconds
            self.bubble = (text, remaining) if remaining > 0 else None
        for table in (self.enemy_flash, self.door_shake):
            for key in list(table):
                table[key] -= delta_seconds
                if table[key] <= 0:
                    del table[key]
        for key in list(self.dying_enemies):
            kind, remaining = self.dying_enemies[key]
            remaining -= delta_seconds
            if remaining <= 0:
                del self.dying_enemies[key]
            else:
                self.dying_enemies[key] = (kind, remaining)
        for floater in self.floaters:
            floater[3] -= delta_seconds
        self.floaters = [floater for floater in self.floaters if floater[3] > 0]


def initial_window_size() -> tuple[int, int]:
    """Largest 16:9 window that fits the screen, leaving room for the taskbar and title bar."""
    try:
        desktop_width, desktop_height = pygame.display.get_desktop_sizes()[0]
    except (pygame.error, IndexError):
        return SCREEN_SIZE
    scale = min((desktop_width - 40) / SCREEN_SIZE[0], (desktop_height - 110) / SCREEN_SIZE[1])
    return (int(SCREEN_SIZE[0] * scale), int(SCREEN_SIZE[1] * scale))


def open_window() -> pygame.Surface:
    """Open a resizable window; the game draws on a fixed 1280x720 canvas that is scaled to fit."""
    if sys.platform == "win32":
        try:
            # Ngăn Windows tự phóng to cửa sổ (125%, 150%...) làm tràn khỏi màn hình.
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass
    pygame.init()
    pygame.display.set_caption(APP_TITLE)
    icon = load_logo_icon(64)
    if icon is not None:
        pygame.display.set_icon(icon)
    return pygame.display.set_mode(initial_window_size(), pygame.RESIZABLE)


def present(canvas: pygame.Surface, window: pygame.Surface) -> None:
    scaled_size = VIEWPORT.fit(canvas.get_size(), window.get_size())
    window.fill((0, 0, 0))
    if scaled_size == canvas.get_size():
        window.blit(canvas, VIEWPORT.offset)
    else:
        window.blit(pygame.transform.smoothscale(canvas, scaled_size), VIEWPORT.offset)
    pygame.display.flip()


class App:
    def __init__(self) -> None:
        self.window = open_window()
        self.screen = pygame.Surface(SCREEN_SIZE)
        self.clock = pygame.time.Clock()
        pygame.key.start_text_input()

        self.font = pygame.font.SysFont("segoeui", 17)
        self.font_small = pygame.font.SysFont("segoeui", 15)
        self.font_bold = pygame.font.SysFont("segoeui", 19, bold=True)
        self.font_title = pygame.font.SysFont("segoeui", 30, bold=True)
        self.font_bubble = pygame.font.SysFont("segoeui", 15, bold=True)
        self.font_code = pygame.font.SysFont("consolas", 17)

        self.assets = Assets()
        self.logo = load_logo(96)
        self.progress = Progress()
        self.editor = CodeEditor(self.font_code)
        self.levels = all_levels()
        self.scene = "menu"
        self.level: Level = self.levels[0]
        self.playback = Playback(self.level)
        self.console: list[tuple[str, tuple[int, int, int]]] = []
        self.hint_index = 0
        self.speed_options = [1.0, 2.0, 4.0]
        self.speed_index = 0
        self.show_win = False
        self.show_theory = False
        self.theory_view = TheoryView(self.font, self.font_bold, self.font_title, self.font_code)
        self.time = 0.0
        self.menu_buttons: list[Button] = []
        self.play_buttons: list[Button] = []
        self.win_buttons: list[Button] = []
        self.menu_stage = self._first_unfinished_stage()
        self._build_menu()

    # ------------------------------------------------------------ scenes
    def _first_unfinished_stage(self) -> int:
        for level in self.levels:
            if level.id not in self.progress.completed:
                return world_of(level.id).stage
        return 1

    @staticmethod
    def _stage_worlds(stage_number: int) -> list[Any]:
        return [world for world in WORLDS if world.stage == stage_number]

    def select_stage(self, stage_number: int) -> None:
        self.menu_stage = stage_number
        self._build_menu()

    def _build_menu(self) -> None:
        self.menu_buttons = []
        for index, stage in enumerate(STAGES):
            stage_levels = [lv for world in self._stage_worlds(stage.number) for lv in world.levels]
            done = sum(lv.id in self.progress.completed for lv in stage_levels)
            rect = pygame.Rect(MENU_LEFT + index * (MENU_TAB_WIDTH + 8), MENU_TAB_Y, MENU_TAB_WIDTH, 48)
            selected = stage.number == self.menu_stage
            color = (40, 150, 180) if selected else (60, 70, 105)
            label = f"Giai đoạn {stage.number}  ·  {done}/{len(stage_levels)}"
            self.menu_buttons.append(Button(rect, label, lambda n=stage.number: self.select_stage(n), color))

        for world_index, world in enumerate(self._stage_worlds(self.menu_stage)):
            cell_x, cell_y = self._world_cell(world_index)
            for level_index, level in enumerate(world.levels):
                rect = pygame.Rect(cell_x + 300 + level_index * 86, cell_y + 4, 80, 42)
                done = level.id in self.progress.completed
                color = (46, 140, 86) if done else (70, 80, 120)
                self.menu_buttons.append(Button(rect, level.id, lambda lv=level: self.open_level(lv), color))

    @staticmethod
    def _world_cell(world_index: int) -> tuple[int, int]:
        column, row = divmod(world_index, MENU_ROWS_PER_COLUMN)
        return MENU_LEFT + column * 588, MENU_WORLDS_Y + row * 72

    def _build_play_buttons(self) -> None:
        width = 76
        gap = 8
        x = EDITOR_RECT.x
        typing_label = "Gõ: VI" if self.editor.vietnamese else "Gõ: EN"
        labels = [
            ("Chạy", self.run, (46, 140, 86)),
            ("Làm lại", self.reset_code, (70, 80, 120)),
            ("Gợi ý", self.show_hint, (150, 110, 40)),
            ("Lý thuyết", self.toggle_theory, (60, 110, 160)),
            (f"x{int(self.speed_options[self.speed_index])}", self.toggle_speed, (70, 80, 120)),
            (typing_label, self.toggle_typing, (100, 70, 140)),
        ]
        self.play_buttons = []
        for index, (label, callback, color) in enumerate(labels):
            rect = pygame.Rect(x + index * (width + gap), BUTTON_Y, width, 48)
            self.play_buttons.append(Button(rect, label, callback, color))
        self.play_buttons.append(Button(pygame.Rect(16, 14, 100, 36), "← Menu", self.go_menu))

    def open_level(self, level: Level) -> None:
        self.save_code()
        self.level = level
        self.scene = "play"
        self.playback = Playback(level)
        self.editor.set_text(self.progress.code.get(level.id, level.starter))
        self.editor.focused = True
        self.console = []
        self.hint_index = 0
        self.show_win = False
        self.log(f"Màn {level.id}: {level.title}", COLOR_ACCENT)
        self.log("Viết code bên phải rồi bấm Chạy (hoặc Ctrl+Enter).", COLOR_MUTED)
        self.log("Bộ gõ Telex có sẵn trong dấu nháy và ghi chú (F2 để bật/tắt).", COLOR_MUTED)
        world = world_of(level.id)
        self.theory_view.build(
            title=f"Lý thuyết · {world.concept}",
            tag=f"Kỹ năng: {world.skill}  |  Giai đoạn {world.stage}",
            theory=THEORY[level.id],
            rect=THEORY_RECT,
            inputs=level.extra_globals,
            goal=level.goal,
        )
        self.show_theory = level.id not in self.progress.completed
        self._build_play_buttons()

    def go_menu(self) -> None:
        self.save_code()
        self.scene = "menu"
        self._build_menu()

    def next_level(self) -> None:
        index = self.levels.index(self.level)
        if index + 1 < len(self.levels):
            self.open_level(self.levels[index + 1])
        else:
            self.go_menu()

    # ------------------------------------------------------------ actions
    def log(self, text: str, color: tuple[int, int, int] = COLOR_TEXT) -> None:
        for line in wrap_text(text, self.font_small, CONSOLE_RECT.width - 24):
            self.console.append((line, color))
        self.console = self.console[-200:]

    def save_code(self) -> None:
        if self.scene == "play":
            self.progress.code[self.level.id] = self.editor.text
            self.progress.save()

    def run(self) -> None:
        self.save_code()
        self.show_theory = False
        self.show_win = False
        self.console = []
        self.log("Đang chạy...", COLOR_MUTED)
        result = run_code(self.level, self.editor.text)
        self.editor.error_line = result.error_line
        self.playback.start(result)

    def reset_code(self) -> None:
        self.editor.set_text(self.level.starter)
        self.playback.reset()
        self.console = []
        self.log("Đã khôi phục code ban đầu.", COLOR_MUTED)

    def show_hint(self) -> None:
        hints = self.level.hints
        if not hints:
            return
        hint = hints[min(self.hint_index, len(hints) - 1)]
        self.log(f"Gợi ý {min(self.hint_index, len(hints) - 1) + 1}/{len(hints)}: {hint}", COLOR_ACCENT)
        self.hint_index += 1

    def toggle_theory(self) -> None:
        self.show_theory = not self.show_theory

    def toggle_typing(self) -> None:
        self.editor.vietnamese = not self.editor.vietnamese
        state = "BẬT (chỉ trong dấu nháy và ghi chú)" if self.editor.vietnamese else "TẮT"
        self.log(f"Bộ gõ tiếng Việt Telex: {state}.", COLOR_INFO)
        self._build_play_buttons()

    def toggle_speed(self) -> None:
        self.speed_index = (self.speed_index + 1) % len(self.speed_options)
        self._build_play_buttons()

    def on_playback_finished(self) -> None:
        result = self.playback.result
        if result is None:
            return
        if result.won:
            self.log("[OK] " + result.message, COLOR_GOOD)
            self.progress.completed.add(self.level.id)
            self.progress.save()
            self.show_win = True
            center = pygame.Rect(0, 0, 160, 46)
            center.center = (VIEW_RECT.centerx - 90, VIEW_RECT.centery + 50)
            next_rect = center.copy()
            next_rect.centerx = VIEW_RECT.centerx + 90
            self.win_buttons = [
                Button(center, "Ở lại", self.close_win),
                Button(next_rect, "Màn tiếp →", self.next_level, (46, 140, 86)),
            ]
        else:
            self.log("[Lỗi] " + result.message, COLOR_BAD)

    def close_win(self) -> None:
        self.show_win = False

    # ------------------------------------------------------------ loop
    def run_forever(self) -> None:
        running = True
        while running:
            delta_seconds = min(self.clock.tick(FPS) / 1000, 0.05)
            self.time += delta_seconds
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(to_logical_event(event))
            self.update(delta_seconds)
            self.draw()
            present(self.screen, pygame.display.get_surface())
        self.save_code()
        pygame.quit()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.scene == "menu":
            for button in self.menu_buttons:
                if button.handle_event(event):
                    return
            return

        if self.show_theory:
            outcome = self.theory_view.handle_event(event)
            if outcome == "close":
                self.show_theory = False
                return
            if outcome == "used":
                return
        elif self.show_win:
            for button in self.win_buttons:
                if button.handle_event(event):
                    return
        for button in self.play_buttons:
            if button.handle_event(event):
                return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
            self.toggle_typing()
            return
        is_enter = event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
        if is_enter and event.mod & pygame.KMOD_CTRL:
            self.run()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.show_theory:
                self.show_theory = False
            else:
                self.go_menu()
            return
        self.editor.handle_event(event)

    def update(self, delta_seconds: float) -> None:
        if self.scene != "play":
            return
        self.editor.update(delta_seconds)
        speed = self.speed_options[self.speed_index]
        if self.playback.update(delta_seconds, speed, self.log):
            self.on_playback_finished()

    # ------------------------------------------------------------ drawing
    def draw_background(self, background_index: int) -> None:
        tile = self.assets.backgrounds[background_index]
        offset = int(self.time * 12) % tile.get_width()
        for x in range(-tile.get_width(), SCREEN_SIZE[0], tile.get_width()):
            for y in range(-tile.get_height(), SCREEN_SIZE[1], tile.get_height()):
                self.screen.blit(tile, (x + offset, y + offset))
        shade = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
        shade.fill((10, 10, 20, 120))
        self.screen.blit(shade, (0, 0))

    def draw(self) -> None:
        if self.scene == "menu":
            self.draw_menu()
        else:
            self.draw_play()

    def draw_menu(self) -> None:
        self.draw_background(4)
        draw_panel(self.screen, pygame.Rect(40, 20, 1200, 690))
        text_left = MENU_LEFT
        if self.logo is not None:
            self.screen.blit(self.logo, (MENU_LEFT - 8, 26))
            text_left = MENU_LEFT + self.logo.get_width() + 6
        title = self.font_title.render("OneSpace CodeQuest · Python", True, COLOR_ACCENT)
        self.screen.blit(title, (text_left, 34))
        subtitle = self.font.render(
            "Viết code Python để đưa nhân vật vượt màn - 5 giai đoạn từ nền tảng tới nâng cao. Cho học sinh THCS - THPT.",
            True,
            COLOR_MUTED,
        )
        self.screen.blit(subtitle, (text_left + 2, 80))

        for button in self.menu_buttons[: len(STAGES)]:
            button.draw(self.screen, self.font)

        stage = STAGES[self.menu_stage - 1]
        box = pygame.Rect(MENU_LEFT, 192, 1152, 136)
        pygame.draw.rect(self.screen, (30, 34, 50), box, border_radius=10)
        y = box.y + 10
        heading = self.font_bold.render(f"Giai đoạn {stage.number}: {stage.title}", True, COLOR_ACCENT)
        self.screen.blit(heading, (box.x + 16, y))
        domains = self.font_small.render(f"Kỹ năng: {stage.skills}", True, COLOR_INFO)
        self.screen.blit(domains, (box.x + 16 + heading.get_width() + 18, y + 4))
        y += 32
        for label, text in (("Nội dung", stage.content), ("Trọng tâm", stage.focus), ("Mốc", stage.milestone)):
            for line in wrap_text(f"{label}: {text}", self.font_small, box.width - 32):
                self.screen.blit(self.font_small.render(line, True, COLOR_TEXT), (box.x + 16, y))
                y += 21

        for world_index, world in enumerate(self._stage_worlds(self.menu_stage)):
            cell_x, cell_y = self._world_cell(world_index)
            done = sum(level.id in self.progress.completed for level in world.levels)
            label = self.font_bold.render(f"World {world.number} · {world.title}", True, COLOR_TEXT)
            concept = self.font_small.render(f"{world.concept}  ·  {done}/{len(world.levels)} xong", True, COLOR_MUTED)
            self.screen.blit(label, (cell_x, cell_y))
            self.screen.blit(concept, (cell_x, cell_y + 26))

        for button in self.menu_buttons[len(STAGES):]:
            button.draw(self.screen, self.font)

    def draw_play(self) -> None:
        world_info = world_of(self.level.id)
        self.draw_background(world_info.background)

        header = self.font_bold.render(
            f"Giai đoạn {world_info.stage} · World {world_info.number}: {world_info.title}   —   Màn {self.level.id}: {self.level.title}",
            True,
            COLOR_TEXT,
        )
        self.screen.blit(header, (132, 20))

        draw_panel(self.screen, VIEW_RECT, alpha=150)
        self.draw_map()
        self.draw_hearts()
        if self.show_win:
            self.draw_win()

        draw_panel(self.screen, CONSOLE_RECT)
        self.draw_console()

        draw_panel(self.screen, INFO_RECT)
        self.draw_info()

        if self.show_theory:
            self.theory_view.draw(self.screen)

        self.editor.draw(self.screen, EDITOR_RECT)
        for button in self.play_buttons:
            button.draw(self.screen, self.font_small if len(button.label) > 7 else self.font)

    def _map_origin(self) -> tuple[int, int]:
        world = self.playback.terrain_world
        origin_x = VIEW_RECT.x + (VIEW_RECT.width - world.width * TILE) // 2
        origin_y = VIEW_RECT.y + (VIEW_RECT.height - world.height * TILE) // 2
        return origin_x, origin_y

    def _frame(self, frames: list[pygame.Surface], fps: float = 12, time_value: float | None = None) -> pygame.Surface:
        moment = self.time if time_value is None else time_value
        return frames[int(moment * fps) % len(frames)]

    def _blit_on_tile(self, image: pygame.Surface, tile_x: float, tile_y: float, flip: bool = False) -> pygame.Rect:
        origin_x, origin_y = self._map_origin()
        if flip:
            image = pygame.transform.flip(image, True, False)
        rect = image.get_rect()
        rect.midbottom = (origin_x + tile_x * TILE + TILE // 2, origin_y + (tile_y + 1) * TILE)
        self.screen.blit(image, rect)
        return rect

    def draw_map(self) -> None:
        world = self.playback.terrain_world
        playback = self.playback
        origin_x, origin_y = self._map_origin()

        for (x, y), terrain in world.terrain.items():
            screen_position = (origin_x + x * TILE, origin_y + y * TILE)
            char = world.rows[y][x] if x < len(world.rows[y]) else " "
            if char == " ":
                continue
            if terrain == "wall":
                self.screen.blit(self.assets.wall, screen_position)
            else:
                self.screen.blit(self.assets.floor, screen_position)

        for (x, y), terrain in world.terrain.items():
            if terrain == "spike":
                self._blit_on_tile(self.assets.spike, x, y)
            elif terrain == "exit":
                self._blit_on_tile(self._frame(self.assets.trophy, 8), x, y)

        for (x, y), kind in playback.doors.items():
            shake = 4 if (x, y) in playback.door_shake and int(self.time * 30) % 2 else 0
            image = self.assets.door_locked if kind == "locked" else self.assets.door_jammed
            self.screen.blit(image, (origin_x + x * TILE + shake, origin_y + y * TILE))

        for (x, y), color in playback.gems.items():
            bob = 3 * pygame.math.Vector2(0, 1).rotate(self.time * 180 + x * 40).y
            rect = self._blit_on_tile(self._frame(self.assets.gems[color], 10), x, y - 0.15)
            rect.y += int(bob)

        for (x, y), kind in playback.enemies.items():
            frames = self.assets.enemies[kind]["hit" if (x, y) in playback.enemy_flash else "idle"]
            self._blit_on_tile(self._frame(frames, 10), x, y, flip=kind != "duck")

        for (x, y), (kind, remaining) in playback.dying_enemies.items():
            image = self._frame(self.assets.enemies[kind]["hit"], 14).copy()
            image.set_alpha(int(255 * remaining / 0.5))
            self._blit_on_tile(image, x, y, flip=kind != "duck")

        hero_frames = self.assets.hero[playback.hero_state]
        hero_image = self._frame(hero_frames, 16, playback.hero_state_time)
        if playback.dead:
            hero_image = hero_image.copy()
            hero_image.set_alpha(140)
        hero_rect = self._blit_on_tile(
            hero_image, playback.hero_position.x, playback.hero_position.y, flip=playback.facing == "left"
        )

        if playback.bubble:
            self.draw_bubble(playback.bubble[0], hero_rect.midtop)

        for text, color, position, remaining in playback.floaters:
            rendered = self.font_bold.render(text, True, color)
            rendered.set_alpha(int(255 * min(1.0, remaining * 1.5)))
            rise = (1.0 - remaining) * 30
            self.screen.blit(
                rendered,
                rendered.get_rect(center=(origin_x + position.x * TILE + TILE // 2, origin_y + position.y * TILE - rise)),
            )

    def draw_bubble(self, text: str, anchor: tuple[int, int]) -> None:
        lines = wrap_text(text, self.font_bubble, 220)
        width = max(self.font_bubble.size(line)[0] for line in lines) + 20
        height = len(lines) * 20 + 12
        rect = pygame.Rect(0, 0, width, height)
        rect.midbottom = (anchor[0], anchor[1] - 8)
        rect.clamp_ip(VIEW_RECT)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, border_radius=10)
        pygame.draw.polygon(
            self.screen, (255, 255, 255),
            [(anchor[0] - 6, rect.bottom - 1), (anchor[0] + 6, rect.bottom - 1), (anchor[0], rect.bottom + 8)],
        )
        for index, line in enumerate(lines):
            rendered = self.font_bubble.render(line, True, (30, 30, 40))
            self.screen.blit(rendered, (rect.x + 10, rect.y + 6 + index * 20))

    def draw_hearts(self) -> None:
        for index in range(MAX_HERO_HP):
            color = COLOR_BAD if index < self.playback.hp else (70, 70, 90)
            heart = self.font_bold.render("♥", True, color)
            self.screen.blit(heart, (VIEW_RECT.x + 12 + index * 24, VIEW_RECT.y + 8))
        collected = len(self.playback.terrain_world.gems) - len(self.playback.gems)
        total = len(self.playback.terrain_world.gems)
        if total:
            gem_text = self.font_bold.render(f"Ngọc: {collected}/{total}", True, COLOR_ACCENT)
            self.screen.blit(gem_text, (VIEW_RECT.right - gem_text.get_width() - 14, VIEW_RECT.y + 8))

    def draw_win(self) -> None:
        overlay = pygame.Surface(VIEW_RECT.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, VIEW_RECT.topleft)
        panel = pygame.Rect(0, 0, 420, 190)
        panel.center = VIEW_RECT.center
        draw_panel(self.screen, panel, alpha=245)
        title = self.font_title.render("Hoàn thành!", True, COLOR_GOOD)
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 40)))
        sub = self.font.render(f"Bạn đã vượt qua màn {self.level.id}.", True, COLOR_TEXT)
        self.screen.blit(sub, sub.get_rect(center=(panel.centerx, panel.y + 80)))
        for button in self.win_buttons:
            button.draw(self.screen, self.font)

    def draw_console(self) -> None:
        title = self.font_small.render("Bảng tin (print, lỗi, gợi ý)", True, COLOR_MUTED)
        self.screen.blit(title, (CONSOLE_RECT.x + 12, CONSOLE_RECT.y + 6))
        line_height = 19
        visible = (CONSOLE_RECT.height - 34) // line_height
        for index, (text, color) in enumerate(self.console[-visible:]):
            rendered = self.font_small.render(text, True, color)
            self.screen.blit(rendered, (CONSOLE_RECT.x + 12, CONSOLE_RECT.y + 30 + index * line_height))

    def draw_info(self) -> None:
        x = INFO_RECT.x + 14
        y = INFO_RECT.y + 10
        width = INFO_RECT.width - 28
        for line in wrap_text(self.level.story, self.font_small, width):
            self.screen.blit(self.font_small.render(line, True, COLOR_TEXT), (x, y))
            y += 20
        y += 6
        goal_title = self.font_bold.render("Nhiệm vụ", True, COLOR_ACCENT)
        self.screen.blit(goal_title, (x, y))
        y += 26
        for line in wrap_text(self.level.goal, self.font_small, width):
            self.screen.blit(self.font_small.render(line, True, COLOR_TEXT), (x, y))
            y += 20
        if self.level.requires:
            requirement = "Bắt buộc dùng: " + ", ".join(requirement_label(item) for item in self.level.requires)
            self.screen.blit(self.font_small.render(requirement, True, COLOR_MUTED), (x, INFO_RECT.bottom - 26))


def main() -> None:
    App().run_forever()
