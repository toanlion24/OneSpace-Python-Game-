"""Drawing helpers for game rewards: stars, coins, shields, medals and confetti."""

from __future__ import annotations

import math
import random

import pygame

GOLD = (255, 205, 60)
GOLD_DARK = (150, 110, 20)
EMPTY_STAR = (70, 74, 96)
STAGE_COLORS: dict[int, tuple[int, int, int]] = {
    1: (80, 200, 120),
    2: (90, 160, 240),
    3: (240, 150, 70),
    4: (200, 110, 230),
    5: (240, 90, 110),
}


def star_points(center: tuple[float, float], radius: float) -> list[tuple[float, float]]:
    points = []
    for index in range(10):
        angle = math.pi / 2 + index * math.pi / 5
        distance = radius if index % 2 == 0 else radius * 0.45
        points.append((center[0] + distance * math.cos(angle), center[1] - distance * math.sin(angle)))
    return points


def draw_star(surface: pygame.Surface, center: tuple[float, float], radius: float, filled: bool) -> None:
    points = star_points(center, radius)
    pygame.draw.polygon(surface, GOLD if filled else EMPTY_STAR, points)
    pygame.draw.polygon(surface, GOLD_DARK if filled else (50, 54, 72), points, width=max(1, int(radius // 6)))


def draw_star_row(surface: pygame.Surface, center: tuple[float, float], radius: float, count: int, total: int = 3) -> None:
    spacing = radius * 2.3
    start_x = center[0] - spacing * (total - 1) / 2
    for index in range(total):
        draw_star(surface, (start_x + index * spacing, center[1]), radius, index < count)


def draw_coin(surface: pygame.Surface, center: tuple[int, int], radius: int) -> None:
    pygame.draw.circle(surface, GOLD_DARK, center, radius)
    pygame.draw.circle(surface, GOLD, center, radius - max(1, radius // 5))
    pygame.draw.circle(surface, (255, 235, 140), (center[0] - radius // 3, center[1] - radius // 3), max(1, radius // 4))


def draw_shield(surface: pygame.Surface, center: tuple[int, int], size: int, active: bool = True) -> None:
    x, y = center
    points = [
        (x - size, y - size), (x + size, y - size), (x + size, y),
        (x, y + int(size * 1.3)), (x - size, y),
    ]
    pygame.draw.polygon(surface, (120, 180, 240) if active else (70, 74, 96), points)
    pygame.draw.polygon(surface, (40, 70, 120), points, width=2)


def draw_heart(surface: pygame.Surface, center: tuple[int, int], size: int, color: tuple[int, int, int]) -> None:
    x, y = center
    radius = size // 2
    pygame.draw.circle(surface, color, (x - radius, y - radius // 2), radius)
    pygame.draw.circle(surface, color, (x + radius, y - radius // 2), radius)
    pygame.draw.polygon(surface, color, [(x - size, y - radius // 3), (x + size, y - radius // 3), (x, y + size)])


def draw_medal(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    label: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    earned: bool,
) -> None:
    x, y = center
    ribbon = (200, 60, 70) if earned else (60, 62, 80)
    pygame.draw.polygon(surface, ribbon, [(x - radius // 2, y - radius - 14), (x, y - radius + 4), (x - radius, y - radius - 2)])
    pygame.draw.polygon(surface, ribbon, [(x + radius // 2, y - radius - 14), (x, y - radius + 4), (x + radius, y - radius - 2)])
    pygame.draw.circle(surface, GOLD_DARK if earned else (50, 52, 68), center, radius)
    pygame.draw.circle(surface, color if earned else (64, 68, 88), center, radius - 4)
    text = font.render(label, True, (255, 255, 255) if earned else (120, 124, 146))
    surface.blit(text, text.get_rect(center=center))


class Confetti:
    """Short burst of falling paper for wins."""

    COLORS = ((255, 205, 60), (90, 220, 120), (120, 180, 255), (255, 110, 150), (200, 140, 255))

    def __init__(self) -> None:
        self.pieces: list[list[float]] = []

    def burst(self, area: pygame.Rect, count: int = 90) -> None:
        for _ in range(count):
            self.pieces.append([
                random.uniform(area.left, area.right),
                random.uniform(area.top - 40, area.top + 20),
                random.uniform(-60, 60),
                random.uniform(80, 220),
                random.uniform(0, 360),
                random.uniform(-400, 400),
                random.randrange(len(self.COLORS)),
                random.uniform(2.0, 3.2),
            ])

    def update(self, delta_seconds: float) -> None:
        for piece in self.pieces:
            piece[0] += piece[2] * delta_seconds
            piece[1] += piece[3] * delta_seconds
            piece[4] += piece[5] * delta_seconds
            piece[7] -= delta_seconds
        self.pieces = [piece for piece in self.pieces if piece[7] > 0]

    def draw(self, surface: pygame.Surface, clip: pygame.Rect) -> None:
        previous = surface.get_clip()
        surface.set_clip(clip)
        for x, y, _, _, angle, _, color_index, _ in self.pieces:
            width = 6 * abs(math.cos(math.radians(angle))) + 1
            pygame.draw.rect(surface, self.COLORS[int(color_index)], (x, y, width, 9))
        surface.set_clip(previous)


def draw_key(surface: pygame.Surface, center: tuple[int, int], size: int) -> None:
    """Small golden key, about 2 * size pixels wide."""
    x, y = center
    ring = max(3, size // 2)
    pygame.draw.circle(surface, GOLD_DARK, (x - size // 2, y), ring + 2)
    pygame.draw.circle(surface, GOLD, (x - size // 2, y), ring)
    pygame.draw.circle(surface, GOLD_DARK, (x - size // 2, y), max(1, ring // 2))
    shaft = pygame.Rect(x - size // 2 + ring, y - 2, size + ring, 5)
    pygame.draw.rect(surface, GOLD, shaft)
    pygame.draw.rect(surface, GOLD, (shaft.right - 5, y + 2, 4, 6))
    pygame.draw.rect(surface, GOLD, (shaft.right - 12, y + 2, 4, 5))


def draw_lock_door(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Wooden door with a golden padlock (opened with hero.unlock)."""
    pygame.draw.rect(surface, (110, 70, 40), rect)
    for offset in (rect.width // 3, 2 * rect.width // 3):
        pygame.draw.line(surface, (80, 48, 26), (rect.x + offset, rect.y + 2), (rect.x + offset, rect.bottom - 2), 2)
    pygame.draw.rect(surface, (70, 42, 22), rect, width=3)
    body = pygame.Rect(0, 0, rect.width // 2, rect.height // 3)
    body.center = (rect.centerx, rect.centery + rect.height // 10)
    pygame.draw.arc(surface, (200, 200, 210), body.inflate(-6, 10).move(0, -body.height // 2), 0, 3.2, 3)
    pygame.draw.rect(surface, GOLD, body, border_radius=3)
    pygame.draw.circle(surface, (60, 40, 20), (body.centerx, body.centery - 1), 3)
    pygame.draw.rect(surface, (60, 40, 20), (body.centerx - 1, body.centery, 3, 6))


def draw_chest(surface: pygame.Surface, rect: pygame.Rect, opened: bool, time_value: float = 0.0) -> None:
    """Treasure chest; when opened the lid is up and gold sparkles."""
    base = pygame.Rect(rect.x + 4, rect.y + rect.height // 2, rect.width - 8, rect.height // 2 - 4)
    pygame.draw.rect(surface, (140, 82, 40), base, border_radius=4)
    pygame.draw.rect(surface, (90, 50, 24), base, width=2, border_radius=4)
    if opened:
        pygame.draw.ellipse(surface, GOLD, (base.x + 4, base.y - 6, base.width - 8, 12))
        lid = pygame.Rect(base.x, base.y - rect.height // 3 - 6, base.width, rect.height // 4)
        pygame.draw.rect(surface, (120, 70, 34), lid, border_radius=4)
        pygame.draw.rect(surface, (90, 50, 24), lid, width=2, border_radius=4)
        for index in range(3):
            angle = time_value * 3 + index * 2.1
            sparkle = (int(base.centerx + math.cos(angle) * 12), int(base.y - 10 + math.sin(angle * 1.3) * 6))
            pygame.draw.circle(surface, (255, 245, 180), sparkle, 2)
    else:
        lid = pygame.Rect(base.x, base.y - rect.height // 4, base.width, rect.height // 4 + 2)
        pygame.draw.rect(surface, (160, 96, 46), lid, border_top_left_radius=8, border_top_right_radius=8)
        pygame.draw.rect(surface, (90, 50, 24), lid, width=2, border_top_left_radius=8, border_top_right_radius=8)
    band = pygame.Rect(base.centerx - 4, base.y - (0 if opened else rect.height // 4), 8, base.height + (0 if opened else rect.height // 4))
    pygame.draw.rect(surface, GOLD, band)
    if not opened:
        pygame.draw.rect(surface, GOLD_DARK, (base.centerx - 5, base.y - 3, 10, 8), border_radius=2)


# ---------------------------------------------------------------- map atmosphere
AMBIENT_SEEDS = [
    (random.Random(index).random(), random.Random(index * 7 + 3).random(), random.Random(index * 13 + 5).random())
    for index in range(48)
]


def draw_ambient(surface: pygame.Surface, area: pygame.Rect, kind: str, time_value: float) -> None:
    """Hạt không khí theo kiểu bản đồ (tuyết, bụi, đom đóm...), tính thẳng từ thời gian - không cần lưu trạng thái."""
    if not kind:
        return
    previous_clip = surface.get_clip()
    surface.set_clip(area)
    for seed_x, seed_y, seed_speed in AMBIENT_SEEDS:
        if kind == "snow":
            speed = 18 + 30 * seed_speed
            x = area.x + (seed_x * area.width + 14 * math.sin(time_value * 1.3 + seed_y * 9)) % area.width
            y = area.y + (seed_y * area.height + time_value * speed) % area.height
            pygame.draw.circle(surface, (235, 245, 255), (int(x), int(y)), 2 if seed_speed > 0.5 else 1)
        elif kind == "dust":
            speed = 12 + 22 * seed_speed
            x = area.x + (seed_x * area.width + time_value * speed) % area.width
            y = area.y + (seed_y * area.height + 6 * math.sin(time_value + seed_x * 7)) % area.height
            dot = pygame.Surface((3, 3), pygame.SRCALPHA)
            dot.fill((240, 210, 150, 110))
            surface.blit(dot, (int(x), int(y)))
        elif kind == "leaves":
            if seed_speed < 0.6:
                continue
            speed = 16 + 18 * seed_speed
            x = area.x + (seed_x * area.width + time_value * speed * 0.6) % area.width
            y = area.y + (seed_y * area.height + time_value * speed) % area.height
            sway = math.sin(time_value * 2 + seed_x * 11)
            pygame.draw.ellipse(surface, (110, 190, 90), (int(x + 6 * sway), int(y), 6, 3))
        elif kind == "fireflies":
            if seed_speed < 0.45:
                continue
            x = area.x + seed_x * area.width + 22 * math.sin(time_value * 0.7 + seed_y * 13)
            y = area.y + seed_y * area.height + 16 * math.cos(time_value * 0.9 + seed_x * 17)
            glow = 0.5 + 0.5 * math.sin(time_value * 3 + seed_speed * 20)
            halo = pygame.Surface((14, 14), pygame.SRCALPHA)
            pygame.draw.circle(halo, (200, 255, 120, int(70 * glow)), (7, 7), 7)
            surface.blit(halo, (int(x) - 7, int(y) - 7))
            pygame.draw.circle(surface, (230, 255, 160), (int(x), int(y)), 1 + int(glow + 0.5))
        elif kind == "sparkle":
            twinkle = math.sin(time_value * 2.5 + seed_speed * 30)
            if twinkle < 0.3:
                continue
            x = area.x + seed_x * area.width
            y = area.y + seed_y * area.height
            size = int(2 + 3 * twinkle)
            color = (230, 200, 255)
            pygame.draw.line(surface, color, (x - size, y), (x + size, y))
            pygame.draw.line(surface, color, (x, y - size), (x, y + size))
    surface.set_clip(previous_clip)


def make_vignette(size: tuple[int, int], strength: int = 120) -> pygame.Surface:
    """Viền tối mềm quanh khung bản đồ để mắt tập trung vào giữa."""
    small = pygame.Surface((40, 24), pygame.SRCALPHA)
    for x in range(40):
        for y in range(24):
            distance = math.hypot((x - 19.5) / 19.5, (y - 11.5) / 11.5) / math.sqrt(2)
            alpha = int(strength * max(0.0, distance - 0.35) / 0.65) if distance > 0.35 else 0
            small.set_at((x, y), (0, 0, 0, min(255, alpha)))
    return pygame.transform.smoothscale(small, size)


def make_soft_ellipse(size: tuple[int, int], color: tuple[int, int, int], alpha: int) -> pygame.Surface:
    """Hình elip mờ dần ra mép (bóng đổ, quầng sáng)."""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    steps = 6
    for step in range(steps):
        fraction = 1 - step / steps
        rect = pygame.Rect(0, 0, int(size[0] * fraction), int(size[1] * fraction))
        rect.center = (size[0] // 2, size[1] // 2)
        pygame.draw.ellipse(surface, (*color, alpha // steps), rect)
    return surface


def make_edge_shadow(width: int, height: int, alpha: int, vertical: bool) -> pygame.Surface:
    """Dải bóng mờ dần: tường đổ bóng xuống sàn."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    length = height if vertical else width
    for index in range(length):
        value = int(alpha * (1 - index / length) ** 2)
        if vertical:
            pygame.draw.line(surface, (0, 0, 0, value), (0, index), (width - 1, index))
        else:
            pygame.draw.line(surface, (0, 0, 0, value), (index, 0), (index, height - 1))
    return surface
