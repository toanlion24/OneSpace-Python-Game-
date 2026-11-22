"""Pygame front-end: level select, code editor and animated playback."""

from __future__ import annotations

import ctypes
import math
import os
import sys
from collections.abc import Callable
from typing import Any

import pygame

from .assets import (
    APP_TITLE,
    TILE,
    Assets,
    backup_dir,
    load_logo,
    load_logo_icon,
    user_data_dir,
)
from .display import VIEWPORT, mouse_pos, to_logical_event
from .editor import CodeEditor
from .engine import (
    Level,
    RunResult,
    World,
    hero_hp_limits,
    hidden_levels,
    requirement_label,
    run_code,
    upgrades_apply,
)
from .hero_view import HeroView
from .hud import (
    Confetti,
    draw_ambient,
    draw_chest,
    draw_coin,
    draw_key,
    draw_lock_door,
    draw_shield,
    draw_star,
    draw_star_row,
    make_edge_shadow,
    make_soft_ellipse,
    make_vignette,
)
from .lessons import lesson_for_world
from .levels import STAGES, WORLDS, all_levels, world_of
from .music import MusicPlayer, track_for_world
from .music_view import AUTO_TRACK, MusicPanel
from .progress import Progress
from .rewards import (
    LOOT_COINS,
    WORLD_CHEST_COINS,
    RewardSummary,
    apply_win,
    bonus_hp,
    has_shield,
    par_for,
    rank_for,
    skin_number,
    star_flags,
    star_goals,
    total_stars,
)
from .sound import SoundBoard
from .store_view import StoreView
from .themes import theme_for_world
from .theory import THEORY
from .theory_view import TheoryView

SCREEN_SIZE = (1280, 720)
FPS = 60
PROGRESS_FILE = user_data_dir() / "progress.json"

VIEW_RECT = pygame.Rect(16, 64, 736, 440)
# Vùng vẽ bản đồ trong khung (chừa chỗ cho tim / sao ở trên và tên bản đồ ở dưới).
MAP_AREA = pygame.Rect(VIEW_RECT.x + 16, VIEW_RECT.y + 40, VIEW_RECT.width - 32, VIEW_RECT.height - 70)
MAP_MAX_SCALE = 2.0
# Chừa một hàng phía trên cho nhân vật / cúp cao hơn một ô.
MAP_TOP_PAD = 48
CONSOLE_RECT = pygame.Rect(16, 516, 736, 188)
THEORY_RECT = pygame.Rect(16, 64, 736, 640)
MENU_LEFT = 64
MENU_TAB_Y = 132
MENU_TAB_WIDTH = 224
MENU_WORLDS_Y = 340
MENU_ROWS_PER_COLUMN = 5
MENU_LEVELS_OFFSET = 232
MENU_LEVEL_WIDTH = 52
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
    "shield": 0.4,
    "box_break": 0.3,
    "gem_reveal": 0.15,
    "key": 0.15,
    "unlock": 0.35,
    "chest_open": 0.5,
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


class LevelButton(Button):
    """Menu button for one level, showing the best stars earned."""

    def __init__(self, rect: pygame.Rect, label: str, on_click: Callable[[], None],
                 color: tuple[int, int, int], stars: int) -> None:
        super().__init__(rect, label, on_click, color)
        self.stars = stars

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        hovered = self.rect.collidepoint(mouse_pos())
        color = tuple(min(255, channel + 30) for channel in self.color) if hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255, 40), self.rect, width=1, border_radius=8)
        label = font.render(self.label, True, COLOR_TEXT)
        surface.blit(label, label.get_rect(center=(self.rect.centerx, self.rect.centery - 6)))
        draw_star_row(surface, (self.rect.centerx, self.rect.bottom - 9), 5, self.stars)


class Playback:
    """Replays recorded engine events as an animation."""

    def __init__(
        self,
        level: Level,
        bonus_hp: int = 0,
        shield: bool = False,
        sound: Callable[[str], None] | None = None,
    ) -> None:
        self.level = level
        self.bonus_hp = bonus_hp
        self.has_shield = shield and upgrades_apply(level)
        self.sound = sound or (lambda name: None)
        self.terrain_world = World(level)
        self.events: list[dict[str, Any]] = []
        self.result: RunResult | None = None
        self.reset()

    def reset(self) -> None:
        world = self.terrain_world
        self.hero_position = pygame.Vector2(world.hero_start)
        self.facing = "right"
        self.hp, self.max_hp = hero_hp_limits(self.level, self.bonus_hp)
        self.shield = self.has_shield
        self.gems = dict(world.gems)
        self.enemies = {pos: enemy.kind for pos, enemy in world.enemies.items()}
        self.doors = dict(world.doors)
        self.crates = dict(world.crates)
        self.keys_on_map = set(world.keys_on_map)
        self.locks = set(world.locks)
        self.chests = dict(world.chests)
        self.hero_keys = 0
        self.breaking: dict[tuple[int, int], tuple[bool, float]] = {}
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
            self.sound("step")
        elif kind == "shield":
            self.shield = False
            self._float("Khiên!", COLOR_INFO, self.hero_position)
            log(event["text"], COLOR_INFO)
            self.sound("shield")
        elif kind == "bump":
            self.facing = event["direction"]
            self._set_hero_state("hit")
        elif kind == "attack":
            self.facing = event["direction"]
            self._set_hero_state("jump")
            target = tuple(event["target"])
            if event["hit"]:
                self.enemy_flash[target] = 0.3
                self.sound("hit")
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
            self.sound("hurt")
        elif kind == "heal":
            self.hp = event["hp"]
            self._float(f"+{event['amount']} ♥", COLOR_GOOD, self.hero_position)
            log(f"Hồi {event['amount']} máu.", COLOR_GOOD)
        elif kind == "gem":
            position = tuple(event["pos"])
            self.gems.pop(position, None)
            self._float("+1", COLOR_ACCENT, pygame.Vector2(position))
            self.sound("gem")
        elif kind == "door_open":
            self.doors.pop(tuple(event["pos"]), None)
            log("Cửa đã mở!", COLOR_GOOD)
            self.sound("door")
        elif kind == "jam":
            self.door_shake[tuple(event["pos"])] = 0.35
            log("DoorJammed: cửa bị kẹt!", COLOR_BAD)
        elif kind == "die":
            self._set_hero_state("hit")
            self.dead = True
        elif kind == "box_break":
            position = tuple(event["pos"])
            has_gem = self.crates.pop(position, False)
            self.breaking[position] = (has_gem, 0.4)
            self.sound("hit")
        elif kind == "gem_reveal":
            self.gems[tuple(event["pos"])] = event["color"]
            log("Thùng vỡ, lộ ra một viên ngọc!", COLOR_ACCENT)
        elif kind == "key":
            self.keys_on_map.discard(tuple(event["pos"]))
            self.hero_keys = event["keys"]
            self._float("+1 chìa", COLOR_ACCENT, pygame.Vector2(event["pos"]))
            log(f"Nhặt được chìa khoá (đang có {self.hero_keys}).", COLOR_ACCENT)
            self.sound("coin")
        elif kind == "unlock":
            self.locks.discard(tuple(event["pos"]))
            self.hero_keys = event["keys"]
            log("Đã mở cửa khoá!", COLOR_GOOD)
            self.sound("door")
        elif kind == "chest_open":
            position = tuple(event["pos"])
            self.chests[position] = True
            self._float(f"+{LOOT_COINS} xu", COLOR_ACCENT, pygame.Vector2(position))
            log(f"Mở rương báu: +{LOOT_COINS} xu (nhận khi qua màn).", COLOR_ACCENT)
            self.sound("chest")

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
        for key in list(self.breaking):
            has_gem, remaining = self.breaking[key]
            remaining -= delta_seconds
            if remaining <= 0:
                del self.breaking[key]
            else:
                self.breaking[key] = (has_gem, remaining)
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
        self.progress = Progress(PROGRESS_FILE, backup_dir())
        self.sound = SoundBoard(self.progress.muted)
        self.sound.set_volume(self.progress.sfx_volume)
        self.music = MusicPlayer(self.progress.music_volume)
        self.music.select(self._music_track_for(None))
        self.music_panel = MusicPanel(self)
        self.confetti = Confetti()
        self.win_summary: RewardSummary | None = None
        self.win_time = 0.0
        self.store = StoreView(self)
        self.hero_view = HeroView(self)
        self.editor = CodeEditor(self.font_code, self.font_small)
        self.levels = all_levels()
        self.scene = "menu"
        self.level: Level = self.levels[0]
        self.playback = self._new_playback(self.level)
        # Số thứ tự bản đồ kiểm tra ẩn đang được diễn lại (0 = bản đồ chính).
        self.hidden_shown = 0
        self._effects: dict[str, pygame.Surface] | None = None
        self._map_layer: pygame.Surface | None = None
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
        self.menu_tool_buttons: list[Button] = []
        self._build_tool_buttons()
        self.toast: tuple[str, float] | None = None
        if self.progress.restored_from_backup:
            self.show_toast("Đã tự khôi phục tiến độ từ bản sao lưu trong Documents.")
        self._build_menu()
        if not self.progress.hero_picked:
            self.open_heroes(first_time=True)

    # ------------------------------------------------------------ scenes
    def _first_unfinished_stage(self) -> int:
        for level in self.levels:
            if level.id not in self.progress.completed:
                return world_of(level.id).stage
        return 1

    @staticmethod
    def _stage_worlds(stage_number: int) -> list[Any]:
        return [world for world in WORLDS if world.stage == stage_number]

    @staticmethod
    def make_button(
        rect: pygame.Rect, label: str, on_click: Callable[[], None], color: tuple[int, int, int] = (70, 80, 120)
    ) -> Button:
        return Button(rect, label, on_click, color)

    def _upgrades(self) -> tuple[int, bool]:
        return bonus_hp(self.progress), has_shield(self.progress)

    def _new_playback(self, level: Level) -> Playback:
        bonus_hp, shield = self._upgrades()
        return Playback(level, bonus_hp, shield, self.sound.play)

    def _build_tool_buttons(self) -> None:
        sound_label = "Âm: Tắt" if self.sound.muted else "Âm: Bật"
        self.menu_tool_buttons = [
            Button(pygame.Rect(812, 30, 196, 36), "Cửa hàng & Huy hiệu", self.open_store, (170, 120, 40)),
            Button(pygame.Rect(1016, 30, 98, 36), "Sao lưu", self.backup_progress, (46, 120, 90)),
            Button(pygame.Rect(1118, 30, 98, 36), "Khôi phục", self.restore_progress, (90, 80, 140)),
            Button(pygame.Rect(812, 72, 96, 36), sound_label, self.toggle_sound, (70, 80, 120)),
            Button(pygame.Rect(912, 72, 96, 36), self._music_label(), self.music_panel.open, (110, 70, 150)),
            Button(pygame.Rect(1016, 72, 200, 36), "Nhân vật", self.open_heroes, (40, 130, 160)),
        ]

    def _music_label(self) -> str:
        if not self.music.enabled:
            return "Nhạc: Tắt"
        return f"Nhạc: {self.music.volume_percent}%"

    def build_music_buttons(self) -> None:
        self._build_tool_buttons()
        self._build_play_buttons()

    def _music_track_for(self, level: Level | None) -> int:
        """Bài cần phát: bài em đã chọn, hoặc tự động (menu bài 0, mỗi World một bài)."""
        if self.progress.music_track != AUTO_TRACK:
            return self.progress.music_track
        if level is None:
            return 0
        return track_for_world(world_of(level.id).number)

    def choose_music_track(self, index: int) -> None:
        self.progress.music_track = index
        level = self.level if self.scene == "play" else None
        self.music.select(self._music_track_for(level))
        if not self.music.enabled:
            self.set_music_volume(40)

    def set_music_volume(self, percent: int) -> None:
        self.progress.music_volume = max(0, min(100, percent))
        self.music.set_volume(self.progress.music_volume)

    def set_sfx_volume(self, percent: int) -> None:
        self.progress.sfx_volume = max(0, min(100, percent))
        self.sound.set_volume(self.progress.sfx_volume)
        self.sound.play("coin")

    def toggle_sound(self) -> None:
        self.sound.muted = not self.sound.muted
        self.progress.muted = self.sound.muted
        self.progress.save()
        self._build_tool_buttons()
        self._build_play_buttons()
        self.sound.play("click")

    def open_heroes(self, first_time: bool = False) -> None:
        self.save_code()
        self.scene = "heroes"
        self.hero_view.build(first_time)

    def open_store(self) -> None:
        self.save_code()
        self.scene = "store"
        self.store.build()
        self.sound.play("click")

    def select_stage(self, stage_number: int) -> None:
        self.menu_stage = stage_number
        self._build_menu()

    def show_toast(self, text: str, seconds: float = 5.0) -> None:
        self.toast = (text, seconds)

    def backup_progress(self) -> None:
        self.save_code()
        try:
            path = self.progress.export_backup()
        except OSError as error:
            self.show_toast(f"Không sao lưu được: {error}")
            return
        if path is None:
            self.show_toast("Bản chạy thử từ mã nguồn: tiến độ nằm ở progress.json trong thư mục dự án.")
            return
        self.show_toast(f"Đã sao lưu vào {path}. Có thể chép file này sang USB / máy khác.", 7.0)
        try:
            os.startfile(path.parent)  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass

    def restore_progress(self) -> None:
        added = self.progress.restore_backup()
        if added is None:
            folder = self.progress.backup_dir or "Documents/OneSpace CodeQuest"
            self.show_toast(f"Chưa có bản sao lưu. Hãy chép file tien-do.json vào {folder} rồi thử lại.", 7.0)
            return
        self._build_menu()
        self.show_toast(f"Đã khôi phục tiến độ: thêm {added} màn hoàn thành.")

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
                rect = pygame.Rect(
                    cell_x + MENU_LEVELS_OFFSET + level_index * (MENU_LEVEL_WIDTH + 6), cell_y + 2, MENU_LEVEL_WIDTH, 50
                )
                done = level.id in self.progress.completed
                color = (46, 140, 86) if done else (70, 80, 120)
                stars = self.progress.stars.get(level.id, 0)
                self.menu_buttons.append(LevelButton(rect, level.id, lambda lv=level: self.open_level(lv), color, stars))

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
        sound_label = "Âm: Tắt" if self.sound.muted else "Âm: Bật"
        self.play_buttons.append(Button(pygame.Rect(1160, 14, 104, 36), sound_label, self.toggle_sound))
        self.play_buttons.append(Button(pygame.Rect(1050, 14, 104, 36), self._music_label(), self.music_panel.open))

    def open_level(self, level: Level) -> None:
        self.save_code()
        self.level = level
        self.scene = "play"
        self.playback = self._new_playback(level)
        self.win_summary = None
        self.editor.set_text(self.progress.code.get(level.id, level.starter))
        self.editor.extra_names = list(level.extra_globals)
        self.editor.focused = True
        self.console = []
        self.hint_index = 0
        self.show_win = False
        self.hidden_shown = 0
        self.music.select(self._music_track_for(level))
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
            lesson=lesson_for_world(world.number),
        )
        self.show_theory = level.id not in self.progress.completed
        self._build_play_buttons()

    def go_menu(self) -> None:
        self.save_code()
        self.scene = "menu"
        self.music.select(self._music_track_for(None))
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
        bonus_hp, shield = self._upgrades()
        result = run_code(self.level, self.editor.text, bonus_hp, shield)
        self.editor.error_line = result.error_line
        self._show_main_map()
        self.playback.start(result)

    def _show_main_map(self) -> None:
        if self.hidden_shown:
            self.playback = self._new_playback(self.level)
            self.hidden_shown = 0

    def reset_code(self) -> None:
        self.editor.set_text(self.level.starter)
        self._show_main_map()
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
        failure = result.hidden_failure
        if failure is not None and not self.hidden_shown:
            self.log("Bản đồ chính: đi đúng!", COLOR_GOOD)
            self.log(f"Thử tiếp code trên bản đồ kiểm tra ẩn {failure.index}...", COLOR_INFO)
            self.hidden_shown = failure.index
            self.playback = self._new_playback(failure.level)
            self.playback.start(RunResult(failure.events, False, result.message, failure.error_line))
            self.editor.error_line = failure.error_line
            return
        if result.won:
            self.log("[OK] " + result.message, COLOR_GOOD)
            if result.hidden_passed:
                self.log(f"Code còn đúng trên cả {result.hidden_passed} bản đồ kiểm tra ẩn!", COLOR_GOOD)
            world = world_of(self.level.id)
            flags = star_flags(result, self.level.id)
            summary = apply_win(self.progress, self.level, world.levels, world.number, flags, result.chests_opened)
            self.progress.save()
            self.win_summary = summary
            self.win_time = 0.0
            if not flags[1]:
                self.log(f"Sao 2: hãy thử qua màn mà không mất máu (vừa mất {result.damage_taken}).", COLOR_INFO)
            if not flags[2]:
                limit = par_for(self.level.id)
                self.log(f"Sao 3: code đang có {result.code_lines} dòng - thử rút gọn còn tối đa {limit} dòng.", COLOR_INFO)
            if summary.coins:
                self.log(f"Nhận {summary.coins} xu!", COLOR_ACCENT)
            self.sound.play("chest" if summary.chest_world else "win")
            self.confetti.burst(VIEW_RECT, 140 if summary.chest_world else 90)
            self.show_win = True
            stay = pygame.Rect(0, 0, 160, 44)
            stay.center = (VIEW_RECT.centerx - 90, VIEW_RECT.centery + 124)
            next_rect = stay.copy()
            next_rect.centerx = VIEW_RECT.centerx + 90
            self.win_buttons = [
                Button(stay, "Ở lại", self.close_win),
                Button(next_rect, "Màn tiếp →", self.next_level, (46, 140, 86)),
            ]
        else:
            self.log("[Lỗi] " + result.message, COLOR_BAD)
            self.sound.play("fail")

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
        if self.music_panel.visible:
            self.music_panel.handle_event(event)
            return
        if self.scene == "store":
            self.store.handle_event(event)
            return
        if self.scene == "heroes":
            self.hero_view.handle_event(event)
            return
        if self.scene == "menu":
            for button in [*self.menu_buttons, *self.menu_tool_buttons]:
                if button.handle_event(event):
                    return
            return

        if self.show_theory:
            outcome = self.theory_view.handle_event(event)
            if outcome == "close":
                self.show_theory = False
                return
            if outcome == "copied":
                character_count = self.theory_view.copied_character_count
                self.show_toast(f"Đã chép {character_count} ký tự - dán bằng Ctrl+V.", 3.0)
                self.sound.play("click")
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
            if self.editor.handle_escape():
                return
            if self.show_theory:
                self.show_theory = False
            else:
                self.go_menu()
            return
        self.editor.handle_event(event)

    def update(self, delta_seconds: float) -> None:
        self.music.update()
        self.confetti.update(delta_seconds)
        self.win_time += delta_seconds
        if self.toast is not None:
            text, remaining = self.toast
            self.toast = (text, remaining - delta_seconds) if remaining > delta_seconds else None
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
        if self.scene == "store":
            self.store.draw(self.screen)
        elif self.scene == "heroes":
            self.hero_view.draw(self.screen)
        elif self.scene == "menu":
            self.draw_menu()
        else:
            self.draw_play()
        if self.music_panel.visible:
            self.music_panel.draw(self.screen)

    def draw_menu(self) -> None:
        self.draw_background(4)
        draw_panel(self.screen, pygame.Rect(40, 20, 1200, 690))
        text_left = MENU_LEFT
        if self.logo is not None:
            self.screen.blit(self.logo, (MENU_LEFT - 8, 26))
            text_left = MENU_LEFT + self.logo.get_width() + 6
        title = self.font_title.render("OneSpace CodeQuest · Python", True, COLOR_ACCENT)
        self.screen.blit(title, (text_left, 34))
        stars = total_stars(self.progress)
        rank = rank_for(stars)[0]
        draw_star(self.screen, (text_left + 12, 92), 11, True)
        stats = self.font.render(f"{stars}/{3 * len(self.levels)} sao", True, COLOR_TEXT)
        self.screen.blit(stats, (text_left + 30, 80))
        coin_x = text_left + 50 + stats.get_width()
        draw_coin(self.screen, (coin_x, 92), 10)
        coins = self.font.render(f"{self.progress.coins} xu", True, COLOR_TEXT)
        self.screen.blit(coins, (coin_x + 16, 80))
        rank_text = self.font.render(f"Cấp bậc: {rank}", True, COLOR_ACCENT)
        self.screen.blit(rank_text, (coin_x + 40 + coins.get_width(), 80))
        for button in self.menu_tool_buttons:
            button.draw(self.screen, self.font_small)

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
            concept_text = self._fit_text(f"{world.concept}  ·  {done}/{len(world.levels)} xong", MENU_LEVELS_OFFSET - 12)
            concept = self.font_small.render(concept_text, True, COLOR_MUTED)
            self.screen.blit(label, (cell_x, cell_y))
            self.screen.blit(concept, (cell_x, cell_y + 26))

        for button in self.menu_buttons[len(STAGES):]:
            button.draw(self.screen, self.font)
        self.draw_toast()

    def draw_toast(self) -> None:
        if self.toast is None:
            return
        lines = wrap_text(self.toast[0], self.font, 900)
        box = pygame.Rect(0, 0, 940, 20 + 24 * len(lines))
        box.midbottom = (SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] - 24)
        pygame.draw.rect(self.screen, (20, 70, 60), box, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_GOOD, box, width=2, border_radius=10)
        for index, line in enumerate(lines):
            rendered = self.font.render(line, True, COLOR_TEXT)
            self.screen.blit(rendered, (box.x + 20, box.y + 10 + index * 24))

    def _fit_text(self, text: str, width: int) -> str:
        """Shorten text with "…" so it fits in `width` pixels."""
        if self.font_small.size(text)[0] <= width:
            return text
        while text and self.font_small.size(text + "…")[0] > width:
            text = text[:-1]
        return text + "…"

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
        theme = theme_for_world(world_info.number)
        backdrop = pygame.Surface(VIEW_RECT.inflate(-4, -4).size, pygame.SRCALPHA)
        pygame.draw.rect(backdrop, (*theme.backdrop, 150), backdrop.get_rect(), border_radius=9)
        self.screen.blit(backdrop, VIEW_RECT.inflate(-4, -4).topleft)
        theme_label = self.font_small.render(f"Bản đồ: {theme.name}", True, COLOR_MUTED)
        self.screen.blit(theme_label, theme_label.get_rect(bottomright=(VIEW_RECT.right - 14, VIEW_RECT.bottom - 8)))
        self.draw_map()
        if self.hidden_shown:
            self._draw_hidden_banner()
        self.draw_hearts()
        self.draw_star_goals()
        if self.show_win:
            self.draw_win()
        self.confetti.draw(self.screen, VIEW_RECT)

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
        """Gốc toạ độ khi vẽ lên lớp bản đồ (lớp này sau đó được phóng to vào khung)."""
        return 0, MAP_TOP_PAD

    def _map_layout(self) -> tuple[float, pygame.Rect]:
        """Tỉ lệ phóng và vị trí của lớp bản đồ trên màn hình - bản đồ nhỏ được phóng to cho dễ nhìn."""
        world = self.playback.terrain_world
        width, height = world.width * TILE, world.height * TILE + MAP_TOP_PAD
        scale = min(MAP_AREA.width / width, MAP_AREA.height / height, MAP_MAX_SCALE)
        rect = pygame.Rect(0, 0, round(width * scale), round(height * scale))
        rect.center = MAP_AREA.center
        return scale, rect

    def _layer_to_screen(self, point: tuple[float, float]) -> tuple[int, int]:
        scale, rect = self._map_layout()
        return round(rect.x + point[0] * scale), round(rect.y + point[1] * scale)

    def _map_effects(self) -> dict[str, pygame.Surface]:
        if self._effects is None:
            self._effects = {
                "shadow": make_soft_ellipse((TILE * 2 // 3, TILE // 5), (0, 0, 0), 150),
                "glow": make_soft_ellipse((TILE, TILE), (255, 240, 170), 90),
                "wall_top": make_edge_shadow(TILE, TILE // 3, 120, vertical=True),
                "wall_left": make_edge_shadow(TILE // 5, TILE, 80, vertical=False),
                "vignette": make_vignette(VIEW_RECT.inflate(-4, -4).size),
            }
        return self._effects

    def _draw_shadow(self, tile_x: float, tile_y: float) -> None:
        shadow = self._map_effects()["shadow"]
        origin_x, origin_y = self._map_origin()
        center = (origin_x + tile_x * TILE + TILE // 2, origin_y + (tile_y + 1) * TILE - 5)
        self.screen.blit(shadow, shadow.get_rect(center=(round(center[0]), round(center[1]))))

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
        layer_size = (world.width * TILE, world.height * TILE + MAP_TOP_PAD)
        if self._map_layer is None or self._map_layer.get_size() != layer_size:
            self._map_layer = pygame.Surface(layer_size, pygame.SRCALPHA)
        self._map_layer.fill((0, 0, 0, 0))
        screen = self.screen
        self.screen = self._map_layer
        try:
            hero_rect = self._draw_map_layer()
        finally:
            self.screen = screen

        _, rect = self._map_layout()
        self.screen.blit(pygame.transform.scale(self._map_layer, rect.size), rect)
        theme = theme_for_world(world_of(self.level.id).number)
        draw_ambient(self.screen, VIEW_RECT.inflate(-4, -4), theme.ambient, self.time)
        self.screen.blit(self._map_effects()["vignette"], VIEW_RECT.inflate(-4, -4).topleft)

        playback = self.playback
        if playback.bubble:
            self.draw_bubble(playback.bubble[0], self._layer_to_screen(hero_rect.midtop))
        origin_x, origin_y = self._map_origin()
        for text, color, position, remaining in playback.floaters:
            rendered = self.font_bold.render(text, True, color)
            rendered.set_alpha(int(255 * min(1.0, remaining * 1.5)))
            rise = (1.0 - remaining) * 30
            anchor = self._layer_to_screen((origin_x + position.x * TILE + TILE // 2, origin_y + position.y * TILE))
            self.screen.blit(rendered, rendered.get_rect(center=(anchor[0], anchor[1] - rise)))

    def _draw_map_layer(self) -> pygame.Rect:
        """Vẽ ô gạch, vật thể và nhân vật lên lớp bản đồ; trả về khung của nhân vật."""
        world = self.playback.terrain_world
        playback = self.playback
        effects = self._map_effects()
        origin_x, origin_y = self._map_origin()
        floor_tile, wall_tile = self.assets.theme_tiles(theme_for_world(world_of(self.level.id).number))

        for (x, y), terrain in world.terrain.items():
            screen_position = (origin_x + x * TILE, origin_y + y * TILE)
            char = world.rows[y][x] if x < len(world.rows[y]) else " "
            if char == " ":
                continue
            if terrain == "wall":
                self.screen.blit(wall_tile, screen_position)
                continue
            self.screen.blit(floor_tile, screen_position)
            # Tường đổ bóng xuống sàn bên dưới và sang sàn bên phải: bản đồ có chiều sâu.
            if world.terrain.get((x, y - 1)) == "wall":
                self.screen.blit(effects["wall_top"], screen_position)
            if world.terrain.get((x - 1, y)) == "wall":
                self.screen.blit(effects["wall_left"], screen_position)

        for (x, y), terrain in world.terrain.items():
            if terrain == "spike":
                self._blit_on_tile(self.assets.spike, x, y)
            elif terrain == "exit":
                pulse = 1.2 + 0.2 * math.sin(self.time * 3)
                glow = effects["glow"]
                halo = pygame.transform.smoothscale(glow, (round(glow.get_width() * pulse), round(glow.get_height() * pulse)))
                center = (origin_x + x * TILE + TILE // 2, origin_y + y * TILE + TILE // 3)
                self.screen.blit(halo, halo.get_rect(center=center))
                self._draw_shadow(x, y)
                self._blit_on_tile(self._frame(self.assets.trophy, 8), x, y)

        for (x, y), kind in playback.doors.items():
            shake = 4 if (x, y) in playback.door_shake and int(self.time * 30) % 2 else 0
            image = self.assets.door_locked if kind == "locked" else self.assets.door_jammed
            self.screen.blit(image, (origin_x + x * TILE + shake, origin_y + y * TILE))

        for (x, y), has_gem in playback.crates.items():
            self._draw_shadow(x, y)
            self._blit_on_tile(self.assets.crates[2 if has_gem else 1]["idle"][0], x, y)
        for (x, y), (has_gem, remaining) in playback.breaking.items():
            image = self.assets.crates[2 if has_gem else 1]["break"][0].copy()
            image.set_alpha(int(255 * remaining / 0.4))
            self._blit_on_tile(image, x, y)
        for x, y in playback.locks:
            draw_lock_door(self.screen, pygame.Rect(origin_x + x * TILE, origin_y + y * TILE, TILE, TILE))
        for (x, y), opened in playback.chests.items():
            draw_chest(self.screen, pygame.Rect(origin_x + x * TILE, origin_y + y * TILE, TILE, TILE), opened, self.time)
        for x, y in playback.keys_on_map:
            bob = int(3 * pygame.math.Vector2(0, 1).rotate(self.time * 200 + x * 30).y)
            draw_key(self.screen, (origin_x + x * TILE + TILE // 2, origin_y + y * TILE + TILE // 2 + bob), 12)

        for (x, y), color in playback.gems.items():
            glow = effects["glow"]
            gem_center = (origin_x + x * TILE + TILE // 2, origin_y + y * TILE + TILE // 2)
            self.screen.blit(glow, glow.get_rect(center=gem_center))
            self._draw_shadow(x, y)
            bob = 3 * pygame.math.Vector2(0, 1).rotate(self.time * 180 + x * 40).y
            rect = self._blit_on_tile(self._frame(self.assets.gems[color], 10), x, y - 0.15)
            rect.y += int(bob)

        for (x, y), kind in playback.enemies.items():
            self._draw_shadow(x, y)
            frames = self.assets.enemies[kind]["hit" if (x, y) in playback.enemy_flash else "idle"]
            self._blit_on_tile(self._frame(frames, 10), x, y, flip=kind != "duck")

        for (x, y), (kind, remaining) in playback.dying_enemies.items():
            image = self._frame(self.assets.enemies[kind]["hit"], 14).copy()
            image.set_alpha(int(255 * remaining / 0.5))
            self._blit_on_tile(image, x, y, flip=kind != "duck")

        hero_frames = self.assets.hero_skin(skin_number(self.progress))[playback.hero_state]
        hero_image = self._frame(hero_frames, 16, playback.hero_state_time)
        if playback.dead:
            hero_image = hero_image.copy()
            hero_image.set_alpha(140)
        self._draw_shadow(playback.hero_position.x, playback.hero_position.y)
        return self._blit_on_tile(
            hero_image, playback.hero_position.x, playback.hero_position.y, flip=playback.facing == "left"
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

    def _draw_hidden_banner(self) -> None:
        text = self.font_bold.render(f"BẢN ĐỒ KIỂM TRA ẨN {self.hidden_shown}", True, (20, 20, 30))
        banner = text.get_rect(midtop=(VIEW_RECT.centerx, VIEW_RECT.y + 44)).inflate(28, 10)
        pygame.draw.rect(self.screen, COLOR_ACCENT, banner, border_radius=8)
        self.screen.blit(text, text.get_rect(center=banner.center))

    def draw_hearts(self) -> None:
        for index in range(self.playback.max_hp):
            color = COLOR_BAD if index < self.playback.hp else (70, 70, 90)
            heart = self.font_bold.render("♥", True, color)
            self.screen.blit(heart, (VIEW_RECT.x + 12 + index * 24, VIEW_RECT.y + 8))
        next_x = VIEW_RECT.x + 24 + self.playback.max_hp * 24
        if self.playback.shield:
            draw_shield(self.screen, (next_x, VIEW_RECT.y + 20), 8)
            next_x += 26
        world = self.playback.terrain_world
        if world.keys_on_map or world.locks:
            draw_key(self.screen, (next_x + 6, VIEW_RECT.y + 20), 10)
            count = self.font_bold.render(f"x{self.playback.hero_keys}", True, COLOR_ACCENT)
            self.screen.blit(count, (next_x + 26, VIEW_RECT.y + 8))
        collected = len(self.playback.terrain_world.gems) - len(self.playback.gems)
        total = len(self.playback.terrain_world.gems)
        if total:
            gem_text = self.font_bold.render(f"Ngọc: {collected}/{total}", True, COLOR_ACCENT)
            self.screen.blit(gem_text, (VIEW_RECT.right - gem_text.get_width() - 14, VIEW_RECT.y + 8))

    def draw_star_goals(self) -> None:
        best = self.progress.stars.get(self.level.id, 0)
        goals = star_goals(self.level.id)
        pieces = [(self.font_small.render(text, True, COLOR_TEXT if index < best else COLOR_MUTED), index < best)
                  for index, text in enumerate(goals)]
        total_width = sum(image.get_width() + 26 for image, _ in pieces) + 12 * (len(pieces) - 1)
        x = VIEW_RECT.centerx - total_width // 2
        for image, achieved in pieces:
            draw_star(self.screen, (x + 9, VIEW_RECT.y + 20), 8, achieved)
            self.screen.blit(image, (x + 22, VIEW_RECT.y + 11))
            x += image.get_width() + 38

    def draw_win(self) -> None:
        summary = self.win_summary
        overlay = pygame.Surface(VIEW_RECT.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, VIEW_RECT.topleft)
        panel = pygame.Rect(0, 0, 470, 330)
        panel.center = VIEW_RECT.center
        draw_panel(self.screen, panel, alpha=245)
        title = self.font_title.render("Hoàn thành!", True, COLOR_GOOD)
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 32)))
        if summary is None:
            for button in self.win_buttons:
                button.draw(self.screen, self.font)
            return

        for index, achieved in enumerate(summary.stars):
            appear = min(1.0, max(0.0, (self.win_time - 0.25 * index) * 4))
            radius = 24 * (appear * (1.25 - 0.25 * appear)) if achieved else 22
            if achieved and appear <= 0:
                radius = 0
            center = (panel.centerx + (index - 1) * 62, panel.y + 84)
            if radius > 0:
                draw_star(self.screen, center, radius, achieved)

        y = panel.y + 122
        for achieved, text in zip(summary.stars, star_goals(self.level.id), strict=True):
            draw_star(self.screen, (panel.x + 46, y + 10), 8, achieved)
            color = COLOR_TEXT if achieved else COLOR_MUTED
            self.screen.blit(self.font_small.render(text, True, color), (panel.x + 62, y))
            y += 24

        draw_coin(self.screen, (panel.x + 48, y + 16), 11)
        coin_text = f"+{summary.coins} xu" if summary.coins else "Không có xu mới (đã nhận ở lần trước)"
        if summary.loot_coins:
            coin_text += f"  (rương: +{summary.loot_coins})"
        self.screen.blit(self.font_bold.render(coin_text, True, COLOR_ACCENT), (panel.x + 66, y + 4))
        y += 34
        if summary.chest_world is not None:
            world = WORLDS[summary.chest_world - 1]
            text = f"Mở rương World {world.number} · {world.title}: huy hiệu + {WORLD_CHEST_COINS} xu!"
            self.screen.blit(self.font_small.render(text, True, COLOR_GOOD), (panel.x + 30, y))
            y += 22
        if summary.rank_up:
            text = f"Lên cấp bậc mới: {summary.new_rank}!"
            self.screen.blit(self.font_small.render(text, True, COLOR_INFO), (panel.x + 30, y))
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
        hidden_count = len(hidden_levels(self.level))
        if hidden_count:
            note = f"+ {hidden_count} bản đồ kiểm tra ẩn: code phải đúng cả khi bản đồ / dữ liệu thay đổi"
            self.screen.blit(self.font_small.render(note, True, COLOR_INFO), (x, INFO_RECT.bottom - 48))


def main() -> None:
    App().run_forever()
