"""Maps the fixed 1280x720 game canvas onto a window of any size (letterboxed)."""

from __future__ import annotations

import pygame


class Viewport:
    def __init__(self) -> None:
        self.scale = 1.0
        self.offset = (0, 0)

    def fit(self, canvas_size: tuple[int, int], window_size: tuple[int, int]) -> tuple[int, int]:
        self.scale = min(window_size[0] / canvas_size[0], window_size[1] / canvas_size[1])
        scaled_size = (max(1, int(canvas_size[0] * self.scale)), max(1, int(canvas_size[1] * self.scale)))
        self.offset = ((window_size[0] - scaled_size[0]) // 2, (window_size[1] - scaled_size[1]) // 2)
        return scaled_size

    def to_logical(self, position: tuple[int, int]) -> tuple[int, int]:
        return (
            int((position[0] - self.offset[0]) / self.scale),
            int((position[1] - self.offset[1]) / self.scale),
        )


VIEWPORT = Viewport()


def mouse_pos() -> tuple[int, int]:
    """Mouse position in canvas coordinates."""
    return VIEWPORT.to_logical(pygame.mouse.get_pos())


def to_logical_event(event: pygame.event.Event) -> pygame.event.Event:
    if hasattr(event, "pos") and event.type in (
        pygame.MOUSEBUTTONDOWN,
        pygame.MOUSEBUTTONUP,
        pygame.MOUSEMOTION,
    ):
        data = dict(event.dict)
        data["pos"] = VIEWPORT.to_logical(event.pos)
        return pygame.event.Event(event.type, data)
    return event
