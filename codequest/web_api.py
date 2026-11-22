"""Cầu nối giữa giao diện web (webui/) và phần lõi Python của game.

Giao diện web chỉ lo hiển thị. Mọi việc chấm code, tính sao / xu, cửa hàng, nhân vật,
tổng hợp nhạc và lưu tiến độ vẫn do các module Python sẵn có làm - giống hệt bản pygame.
Các hàm trả về dict / list thuần để gửi sang JavaScript dạng JSON.
"""

from __future__ import annotations

import io
import os
import threading
import wave
from pathlib import Path
from typing import Any

from .completion import (
    BUILTIN_FUNCTIONS,
    COMMON_METHODS,
    HERO_MEMBERS,
    IMPORTABLE,
    KEYWORDS,
    MAX_SUGGESTIONS,
    MODULE_MEMBERS,
    Suggestion,
)
from .engine import Level, RunResult, hero_hp_limits, run_code
from .glossary import GLOSSARY, find_terms, theory_text
from .heroes import HEROES, HEROES_BY_NUMBER, color_map
from .lessons import lesson_for_world
from .levels import STAGES, WORLDS, all_levels, world_of
from .music import COMPOSED, SAMPLE_RATE, TRACKS, compose, track_for_world
from .progress import Progress
from .rewards import (
    ITEMS_BY_ID,
    RANKS,
    SHOP_ITEMS,
    WORLD_CHEST_COINS,
    apply_win,
    bonus_hp,
    buy,
    can_buy,
    equip_skin,
    has_shield,
    par_for,
    rank_for,
    skin_number,
    star_flags,
    star_goals,
    total_stars,
)
from .themes import THEMES, MapTheme, theme_for_world
from .theory import THEORY

LEVELS_BY_ID: dict[str, Level] = {level.id: level for level in all_levels()}
AUTO_TRACK = -1


def _theme_data(theme: MapTheme) -> dict[str, Any]:
    return {
        "name": theme.name,
        "floor": list(theme.floor),
        "wall": list(theme.wall),
        "floorMultiply": list(theme.floor_multiply),
        "wallMultiply": list(theme.wall_multiply),
        "add": list(theme.add),
        "backdrop": list(theme.backdrop),
        "ambient": theme.ambient,
    }


def _hero_data(number: int) -> dict[str, Any]:
    style = HEROES_BY_NUMBER[number]
    return {
        "number": style.number,
        "name": style.name,
        "description": style.description,
        "price": style.price,
        "base": style.base,
        "recolor": [[list(old), list(new)] for old, new in color_map(style).items()],
    }


def _theory_data(level: Level) -> dict[str, Any]:
    theory = THEORY[level.id]
    world = world_of(level.id)
    lesson = lesson_for_world(world.number)
    data: dict[str, Any] = {
        "concept": theory.concept,
        "terms": [
            {"term": glossary_term.term, "meaning": glossary_term.meaning}
            for glossary_term in find_terms(theory_text(theory))
        ],
        "starterNotes": [list(pair) for pair in theory.starter_notes],
        "example": [list(pair) for pair in theory.example],
        "mistakes": theory.mistakes,
        "lesson": None,
    }
    if lesson is not None:
        data["lesson"] = {
            "analogy": lesson.analogy,
            "syntax": [list(pair) for pair in lesson.syntax],
            "walkthrough": [list(pair) for pair in lesson.walkthrough],
            "tips": lesson.tips,
        }
    return data


def _run_data(result: RunResult) -> dict[str, Any]:
    data: dict[str, Any] = {
        "events": result.events,
        "won": result.won,
        "message": result.message,
        "errorLine": result.error_line,
        "damageTaken": result.damage_taken,
        "codeLines": result.code_lines,
        "hiddenPassed": result.hidden_passed,
        "hidden": None,
    }
    failure = result.hidden_failure
    if failure is not None:
        data["hidden"] = {
            "index": failure.index,
            "rows": failure.level.rows,
            "events": failure.events,
            "errorLine": failure.error_line,
        }
    return data


def _suggestion_data(suggestions: list[Suggestion]) -> list[dict[str, Any]]:
    return [
        {"label": item.label, "insert": item.insert, "hint": item.hint, "cursorBack": item.cursor_back}
        for item in suggestions
    ]


def completion_data() -> dict[str, Any]:
    """Dữ liệu gợi ý lệnh (lấy từ completion.py) để khung code trên web tự lọc khi gõ."""
    return {
        "hero": _suggestion_data(HERO_MEMBERS),
        "builtins": _suggestion_data(BUILTIN_FUNCTIONS),
        "keywords": _suggestion_data(KEYWORDS),
        "modules": {name: _suggestion_data(members) for name, members in MODULE_MEMBERS.items()},
        "methods": _suggestion_data(COMMON_METHODS),
        "importable": IMPORTABLE,
        "maxSuggestions": MAX_SUGGESTIONS,
    }


def _handbook_world(world: Any) -> dict[str, Any]:
    lesson = lesson_for_world(world.number)
    lesson_data = None
    if lesson is not None:
        lesson_data = {
            "analogy": lesson.analogy,
            "syntax": [list(pair) for pair in lesson.syntax],
            "walkthrough": [list(pair) for pair in lesson.walkthrough],
            "tips": lesson.tips,
        }
    levels = []
    for level in world.levels:
        theory = THEORY[level.id]
        levels.append({
            "id": level.id,
            "title": level.title,
            "concept": theory.concept,
            "example": [list(pair) for pair in theory.example],
            "mistakes": theory.mistakes,
        })
    return {
        "number": world.number,
        "stage": world.stage,
        "title": world.title,
        "concept": world.concept,
        "skill": world.skill,
        "lesson": lesson_data,
        "levels": levels,
    }


def handbook_data() -> dict[str, Any]:
    """Nội dung sổ tay. Chỉ gồm lý thuyết và ví dụ (vốn khác lời giải) - không có đề bài hay code ban đầu."""
    return {
        "stages": [{"number": stage.number, "title": stage.title, "skills": stage.skills} for stage in STAGES],
        "worlds": [_handbook_world(world) for world in WORLDS],
        "glossary": sorted(
            ({"term": glossary_term.term, "meaning": glossary_term.meaning} for glossary_term in GLOSSARY),
            key=lambda entry: entry["term"].casefold(),
        ),
        "commands": completion_data(),
    }


def wav_bytes(samples: Any) -> bytes:
    """Đóng gói mảng int16 stereo (số mẫu x 2) thành file WAV trong bộ nhớ."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(samples.shape[1] if samples.ndim > 1 else 1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(samples.tobytes())
    return buffer.getvalue()


class WebApi:
    def __init__(self, progress_file: Path, backup_dir: Path | None = None) -> None:
        self.progress = Progress(progress_file, backup_dir)
        # Mỗi yêu cầu chạy trên một luồng riêng: khoá để không ghi tiến độ chồng lên nhau.
        self._lock = threading.Lock()
        self._music_lock = threading.Lock()
        self._music_cache: dict[int, bytes] = {}

    # ------------------------------------------------------------ menu
    def bootstrap(self) -> dict[str, Any]:
        with self._lock:
            return {
                "player": self._player_data(),
                "settings": self._settings_data(),
                "stages": [
                    {"number": stage.number, "title": stage.title, "skills": stage.skills}
                    for stage in STAGES
                ],
                "worlds": [self._world_data(world) for world in WORLDS],
                "continueLevel": self._continue_level(),
                "tracks": [{"name": track.name, "genre": track.genre} for track in TRACKS],
                "themes": [_theme_data(theme) for theme in THEMES],
                "restoredFromBackup": self.progress.restored_from_backup,
            }

    def _player_data(self) -> dict[str, Any]:
        progress = self.progress
        stars_total = total_stars(progress)
        rank, next_rank = rank_for(stars_total)
        previous_rank = max(threshold for threshold, _name in RANKS if threshold <= stars_total)
        return {
            "coins": progress.coins,
            "stars": stars_total,
            "maxStars": 3 * len(LEVELS_BY_ID),
            "rank": rank,
            "rankStart": previous_rank,
            "nextRank": next_rank,
            "hero": _hero_data(skin_number(progress)),
            "completed": len(progress.completed),
            "heroPicked": progress.hero_picked,
            "badges": sorted(progress.chests),
        }

    def _settings_data(self) -> dict[str, Any]:
        return {
            "musicVolume": self.progress.music_volume,
            "sfxVolume": self.progress.sfx_volume,
            "musicTrack": self.progress.music_track,
        }

    def _world_data(self, world: Any) -> dict[str, Any]:
        stars = self.progress.stars
        return {
            "number": world.number,
            "stage": world.stage,
            "title": world.title,
            "concept": world.concept,
            "skill": world.skill,
            "theme": _theme_data(theme_for_world(world.number)),
            "chestOpened": world.number in self.progress.chests,
            "musicTrack": track_for_world(world.number),
            "levels": [
                {
                    "id": level.id,
                    "title": level.title,
                    "stars": stars.get(level.id, 0),
                    "done": level.id in self.progress.completed,
                    "challenge": index == len(world.levels) - 1,
                }
                for index, level in enumerate(world.levels)
            ],
        }

    def _continue_level(self) -> str:
        for level_id in LEVELS_BY_ID:
            if level_id not in self.progress.completed:
                return level_id
        return next(iter(LEVELS_BY_ID))

    # ------------------------------------------------------------ heroes and shop
    def collection(self) -> dict[str, Any]:
        with self._lock:
            progress = self.progress
            current = skin_number(progress)
            heroes = []
            for hero in HEROES:
                data = _hero_data(hero.number)
                data["owned"] = hero.price == 0 or hero.item_id in progress.owned
                data["selected"] = hero.number == current
                heroes.append(data)
            items = []
            for item in SHOP_ITEMS:
                ok, reason = can_buy(progress, item)
                items.append({
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "price": item.price,
                    "kind": item.kind,
                    "hero": _hero_data(item.skin_number) if item.kind == "skin" else None,
                    "owned": item.id in progress.owned,
                    "selected": item.kind == "skin" and progress.skin == item.id,
                    "canBuy": ok,
                    "reason": reason,
                })
            return {
                "player": self._player_data(),
                "heroes": heroes,
                "items": items,
                "ranks": [{"stars": threshold, "name": name} for threshold, name in RANKS],
                "badges": [
                    {"number": world.number, "stage": world.stage, "title": world.title,
                     "earned": world.number in progress.chests}
                    for world in WORLDS
                ],
                "chestCoins": WORLD_CHEST_COINS,
            }

    def choose_hero(self, number: int) -> dict[str, Any]:
        hero = HEROES_BY_NUMBER.get(int(number))
        if hero is None:
            return {"ok": False, "message": "Không có nhân vật này."}
        with self._lock:
            progress = self.progress
            if hero.price == 0 or hero.item_id in progress.owned:
                equip_skin(progress, hero.item_id)
                progress.save()
                return {"ok": True, "message": f"Đã chọn {hero.name}.", "sound": "click"}
            item = ITEMS_BY_ID[hero.item_id]
            ok, reason = can_buy(progress, item)
            if not ok:
                return {"ok": False, "message": f"{hero.name} là nhân vật hiếm: {reason}. Qua màn để nhận thêm xu!"}
            buy(progress, item)
            progress.save()
            return {"ok": True, "message": f"Đã mở khoá {hero.name}!", "sound": "coin"}

    def buy_item(self, item_id: str) -> dict[str, Any]:
        item = ITEMS_BY_ID.get(str(item_id))
        if item is None:
            return {"ok": False, "message": "Không có vật phẩm này."}
        with self._lock:
            ok, reason = can_buy(self.progress, item)
            if not ok:
                return {"ok": False, "message": f"Chưa mua được {item.name}: {reason}."}
            buy(self.progress, item)
            self.progress.save()
            return {"ok": True, "message": f"Đã mua {item.name}!", "sound": "coin"}

    def finish_hero_pick(self) -> bool:
        with self._lock:
            self.progress.hero_picked = True
            self.progress.save()
        return True

    # ------------------------------------------------------------ settings, backup
    def save_settings(self, music_volume: int, sfx_volume: int, music_track: int) -> dict[str, Any]:
        with self._lock:
            self.progress.music_volume = max(0, min(100, int(music_volume)))
            self.progress.sfx_volume = max(0, min(100, int(sfx_volume)))
            track = int(music_track)
            self.progress.music_track = track if track == AUTO_TRACK or 0 <= track < len(TRACKS) else AUTO_TRACK
            self.progress.save()
            return self._settings_data()

    def backup(self) -> dict[str, Any]:
        with self._lock:
            try:
                path = self.progress.export_backup()
            except OSError as error:
                return {"ok": False, "message": f"Không sao lưu được: {error}"}
        if path is None:
            return {"ok": False, "message": "Bản chạy thử từ mã nguồn: tiến độ nằm ở progress.json trong thư mục dự án."}
        try:
            os.startfile(path.parent)  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass
        return {"ok": True, "message": f"Đã sao lưu vào {path}. Có thể chép file này sang USB / máy khác."}

    def restore(self) -> dict[str, Any]:
        with self._lock:
            added = self.progress.restore_backup()
            folder = self.progress.backup_dir or "Documents/OneSpace CodeQuest"
        if added is None:
            return {"ok": False, "message": f"Chưa có bản sao lưu. Hãy chép file tien-do.json vào {folder} rồi thử lại."}
        return {"ok": True, "message": f"Đã khôi phục tiến độ: thêm {added} màn hoàn thành."}

    def completions(self) -> dict[str, Any]:
        return completion_data()

    def handbook(self) -> dict[str, Any]:
        """Sổ tay lý thuyết: toàn bộ bài học theo World, từ điển thuật ngữ và bảng tra lệnh."""
        return handbook_data()

    def music(self, index: int) -> bytes:
        """File WAV của một bài nhạc (tổng hợp lần đầu mất vài giây, sau đó dùng lại)."""
        index = int(index) % len(TRACKS)
        with self._music_lock:
            if index not in self._music_cache:
                if index not in COMPOSED:
                    COMPOSED[index] = compose(TRACKS[index])
                self._music_cache[index] = wav_bytes(COMPOSED[index])
            return self._music_cache[index]

    # ------------------------------------------------------------ level
    def level(self, level_id: str) -> dict[str, Any]:
        level = LEVELS_BY_ID[level_id]
        world = world_of(level_id)
        stage = STAGES[world.stage - 1]
        with self._lock:
            code = self.progress.code.get(level_id, level.starter)
            best_stars = self.progress.stars.get(level_id, 0)
            completed = level_id in self.progress.completed
            start_hp, max_hp = hero_hp_limits(level, bonus_hp(self.progress))
            shield = has_shield(self.progress)
        ids = list(LEVELS_BY_ID)
        position = ids.index(level_id)
        return {
            "id": level.id,
            "title": level.title,
            "story": level.story,
            "goal": level.goal,
            "rows": level.rows,
            "starter": level.starter,
            "code": code,
            "hints": level.hints,
            "inputs": {name: repr(value) for name, value in level.extra_globals.items()},
            "inputNames": list(level.extra_globals),
            "world": {"number": world.number, "title": world.title, "concept": world.concept, "skill": world.skill},
            "stage": {"number": stage.number, "title": stage.title},
            "theme": _theme_data(theme_for_world(world.number)),
            "musicTrack": track_for_world(world.number),
            "starGoals": star_goals(level_id),
            "par": par_for(level_id),
            "bestStars": best_stars,
            "hp": start_hp,
            "maxHp": max_hp,
            "shield": shield,
            "completed": completed,
            "theory": _theory_data(level),
            "nextLevel": ids[position + 1] if position + 1 < len(ids) else None,
            "previousLevel": ids[position - 1] if position > 0 else None,
        }

    def save_code(self, level_id: str, code: str) -> bool:
        if level_id not in LEVELS_BY_ID:
            return False
        with self._lock:
            self.progress.code[level_id] = code
            self.progress.save()
        return True

    def run(self, level_id: str, code: str) -> dict[str, Any]:
        level = LEVELS_BY_ID[level_id]
        with self._lock:
            self.progress.code[level_id] = code
            hearts = bonus_hp(self.progress)
            shield = has_shield(self.progress)
        result = run_code(level, code, hearts, shield)
        data = _run_data(result)
        data["reward"] = None
        if not result.won:
            with self._lock:
                self.progress.save()
            return data
        world = world_of(level_id)
        flags = star_flags(result, level_id)
        with self._lock:
            summary = apply_win(self.progress, level, world.levels, world.number, flags, result.chests_opened)
            self.progress.save()
            data["reward"] = {
                "stars": list(summary.stars),
                "newStars": summary.new_stars,
                "coins": summary.coins,
                "lootCoins": summary.loot_coins,
                "chestWorld": summary.chest_world,
                "chestCoins": WORLD_CHEST_COINS,
                "rankUp": summary.rank_up,
                "newRank": summary.new_rank,
                "totalCoins": self.progress.coins,
            }
        return data
