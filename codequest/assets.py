"""Loads sprites from the Craftpix platformer kit in ./gamekit."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pygame

from .heroes import HEROES, HEROES_BY_NUMBER, color_map
from .themes import MapTheme

IS_PACKAGED = getattr(sys, "frozen", False)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Khi đóng gói bằng PyInstaller, dữ liệu nằm trong thư mục giải nén tạm (sys._MEIPASS).
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
KIT = BUNDLE_ROOT / "gamekit"
LOGO_PATH = BUNDLE_ROOT / "assets" / "onespace_logo.png"
# Vùng hình tròn (tên lửa) trong logo OneSpace, dùng làm icon.
LOGO_ICON_BOX = (224, 120, 700, 596)
APP_TITLE = "OneSpace CodeQuest - Học Python qua trò chơi"


def user_data_dir() -> Path:
    """Nơi lưu tiến độ: %APPDATA%/CodeQuest khi chạy bản .exe, thư mục dự án khi phát triển."""
    if not IS_PACKAGED:
        return PROJECT_ROOT
    base = Path(os.environ.get("APPDATA", Path.home()))
    folder = base / "OneSpaceCodeQuest"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def documents_dir() -> Path:
    """The user's Documents folder (follows OneDrive redirection on Windows)."""
    if sys.platform == "win32":
        try:
            import ctypes

            buffer = ctypes.create_unicode_buffer(260)
            # CSIDL_PERSONAL = 5 (Documents)
            if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buffer) == 0 and buffer.value:
                return Path(buffer.value)
        except (AttributeError, OSError):
            pass
    return Path.home() / "Documents"


def backup_dir() -> Path | None:
    """Folder for the easy-to-find progress backup (only for the installed .exe)."""
    if not IS_PACKAGED:
        return None
    return documents_dir() / "OneSpace CodeQuest"


TILE = 48

ENEMY_FOLDERS: dict[str, tuple[str, int]] = {
    "robot": ("1", 48),
    "barrel": ("3", 48),
    "cannon": ("4", 48),
    "spikebox": ("5", 48),
    "duck": ("6 (48x72)", 72),
}


def load_logo(height: int) -> pygame.Surface | None:
    """Full OneSpace logo scaled to `height` pixels, or None if the file is missing."""
    try:
        logo = pygame.image.load(str(LOGO_PATH)).convert_alpha()
    except (pygame.error, FileNotFoundError):
        return None
    width = round(logo.get_width() * height / logo.get_height())
    return pygame.transform.smoothscale(logo, (width, height))


def load_logo_icon(size: int) -> pygame.Surface | None:
    """Round rocket emblem from the logo; works before the display is created."""
    try:
        logo = pygame.image.load(str(LOGO_PATH))
    except (pygame.error, FileNotFoundError):
        return None
    left, top, right, bottom = LOGO_ICON_BOX
    emblem = logo.subsurface((left, top, right - left, bottom - top))
    return pygame.transform.smoothscale(emblem, (size, size))


def load_image(relative_path: str) -> pygame.Surface:
    return pygame.image.load(str(KIT / relative_path)).convert_alpha()


def slice_strip(sheet: pygame.Surface, frame_width: int, scale: float) -> list[pygame.Surface]:
    frame_height = sheet.get_height()
    frame_count = max(1, sheet.get_width() // frame_width)
    size = (round(frame_width * scale), round(frame_height * scale))
    frames = []
    for index in range(frame_count):
        frame = sheet.subsurface((index * frame_width, 0, frame_width, frame_height))
        frames.append(pygame.transform.scale(frame, size))
    return frames


def recolored(sheet: pygame.Surface, replacements: dict[tuple[int, int, int], tuple[int, int, int]]) -> pygame.Surface:
    if not replacements:
        return sheet
    result = sheet.copy()
    pixels = pygame.PixelArray(result)
    for old_color, new_color in replacements.items():
        pixels.replace(old_color, new_color)
    pixels.close()
    return result


def tinted(tile: pygame.Surface, multiply: tuple[int, int, int], add: tuple[int, int, int]) -> pygame.Surface:
    result = tile.copy()
    if multiply != (255, 255, 255):
        result.fill(multiply, special_flags=pygame.BLEND_RGB_MULT)
    if add != (0, 0, 0):
        result.fill(add, special_flags=pygame.BLEND_RGB_ADD)
    return result


def strip(relative_path: str, frame_width: int, scale: float) -> list[pygame.Surface]:
    return slice_strip(load_image(relative_path), frame_width, scale)


class Assets:
    def __init__(self, hero_skin: int = 1) -> None:
        tileset = load_image("2 Locations/Tiles/Tileset.png")
        self._tileset = tileset
        self._theme_tiles: dict[str, tuple[pygame.Surface, pygame.Surface]] = {}
        self.floor = self._tile(tileset, 1, 1)
        self.wall = self._tile(tileset, 1, 4)
        self.door_locked = self._tile(tileset, 13, 5)
        self.door_jammed = self._tile(tileset, 6, 8)

        hero_scale = TILE / 32 * 1.25
        self._hero_skins: dict[int, dict[str, list[pygame.Surface]]] = {}
        self.hero = self.hero_skin(hero_skin)
        self.appearing = strip("1 Main Characters/Appearing.png", 96, hero_scale)

        self.enemies: dict[str, dict[str, list[pygame.Surface]]] = {}
        for kind, (folder, frame_width) in ENEMY_FOLDERS.items():
            scale = 1.8 if kind == "duck" else 1.6
            self.enemies[kind] = {
                "idle": strip(f"4 Enemies/{folder}/Idle.png", frame_width, scale),
                "hit": strip(f"4 Enemies/{folder}/Hit.png", frame_width, scale),
            }

        self.gems = {color: strip(f"3 Objects/Gems/{color}.png", 16, 2.5) for color in range(1, 7)}
        # Thùng gỗ: 1 = thùng thường (O), 2 = thùng có ngọc (Q).
        self.crates = {
            number: {
                "idle": strip(f"3 Objects/Boxes/{number}_Idle.png", 32, 1.5),
                "break": strip(f"3 Objects/Boxes/{number}_Break.png", 32, 1.5),
            }
            for number in (1, 2)
        }
        self.trophy = strip("3 Objects/Checkpoints/End_Idle.png", 64, 0.95)
        self.spike = strip("6 Traps/4.png", 48, 1.0)[4]
        self.backgrounds = {
            index: pygame.transform.scale(load_image(f"2 Locations/Backgrounds/{index}.png"), (128, 128))
            for index in range(1, 7)
        }

    def hero_skin(self, number: int) -> dict[str, list[pygame.Surface]]:
        """Animation frames for a hero of the roster (loaded once, then cached)."""
        if number not in self._hero_skins:
            style = HEROES_BY_NUMBER.get(number, HEROES[0])
            replacements = color_map(style)
            hero_dir = f"1 Main Characters/{style.base}"
            scale = TILE / 32 * 1.25
            self._hero_skins[number] = {
                state: slice_strip(recolored(load_image(f"{hero_dir}/{file_name}.png"), replacements), 32, scale)
                for state, file_name in (("idle", "Idle"), ("run", "Run"), ("hit", "Hit"), ("jump", "Jump"))
            }
        return self._hero_skins[number]

    def theme_tiles(self, theme: MapTheme) -> tuple[pygame.Surface, pygame.Surface]:
        """(floor, wall) tiles of a map theme, tinted and cached."""
        if theme.name not in self._theme_tiles:
            floor = tinted(self._tile(self._tileset, *theme.floor), theme.floor_multiply, theme.add)
            wall = tinted(self._tile(self._tileset, *theme.wall), theme.wall_multiply, theme.add)
            self._theme_tiles[theme.name] = (floor, wall)
        return self._theme_tiles[theme.name]

    @staticmethod
    def _tile(tileset: pygame.Surface, column: int, row: int) -> pygame.Surface:
        tile = tileset.subsurface((column * 16, row * 16, 16, 16))
        return pygame.transform.scale(tile, (TILE, TILE))
