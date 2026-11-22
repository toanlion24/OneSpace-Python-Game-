import json

from codequest import rewards
from codequest.engine import RunResult, World, run_code
from codequest.levels import WORLDS, all_levels
from codequest.par import PAR
from codequest.progress import Progress

from .conftest import requires_solutions, solution_for

LEVELS = {level.id: level for level in all_levels()}


def fresh_progress(tmp_path):
    return Progress(tmp_path / "progress.json", None)


def result(won=True, damage=0, lines=1):
    return RunResult([], won, "", None, damage, lines)


def test_par_exists_for_every_level():
    assert set(PAR) == set(LEVELS)
    assert all(value >= 1 for value in PAR.values())


@requires_solutions
def test_reference_solutions_get_three_stars():
    for level_id, level in LEVELS.items():
        outcome = run_code(level, solution_for(level_id))
        assert rewards.star_flags(outcome, level_id) == (True, True, True), level_id


def test_star_flags():
    assert rewards.star_flags(result(won=False), "1-1") == (False, False, False)
    assert rewards.star_flags(result(damage=1, lines=1), "1-1") == (True, False, True)
    assert rewards.star_flags(result(lines=PAR["1-2"] + 1), "1-2") == (True, True, False)


def test_coins_only_for_new_stars(tmp_path):
    progress = fresh_progress(tmp_path)
    world = WORLDS[0]
    level = world.levels[0]
    first = rewards.apply_win(progress, level, world.levels, world.number, (True, False, False))
    assert first.new_stars == 1 and first.coins == rewards.STAR_COINS
    again = rewards.apply_win(progress, level, world.levels, world.number, (True, False, False))
    assert again.new_stars == 0 and again.coins == 0
    better = rewards.apply_win(progress, level, world.levels, world.number, (True, True, True))
    assert better.new_stars == 2 and progress.stars[level.id] == 3
    assert progress.coins == 3 * rewards.STAR_COINS


def test_world_chest_opens_once(tmp_path):
    progress = fresh_progress(tmp_path)
    world = WORLDS[1]
    summaries = [
        rewards.apply_win(progress, level, world.levels, world.number, (True, True, True)) for level in world.levels
    ]
    assert [summary.chest_world for summary in summaries] == [None] * (len(world.levels) - 1) + [world.number]
    replay = rewards.apply_win(progress, world.levels[0], world.levels, world.number, (True, True, True))
    assert replay.chest_world is None
    assert progress.coins == 3 * len(world.levels) * rewards.STAR_COINS + rewards.WORLD_CHEST_COINS


def test_rank_progression():
    assert rewards.rank_for(0) == ("Tân binh", 15)
    assert rewards.rank_for(15)[0] == "Học việc"
    assert rewards.rank_for(400) == ("Huyền thoại OneSpace", None)


def test_shop_rules(tmp_path):
    progress = fresh_progress(tmp_path)
    heart2 = rewards.ITEMS_BY_ID["heart2"]
    progress.coins = 1000
    ok, reason = rewards.can_buy(progress, heart2)
    assert not ok and "Tim thêm I" in reason
    assert rewards.buy(progress, rewards.ITEMS_BY_ID["heart1"])
    assert rewards.buy(progress, heart2)
    assert rewards.bonus_hp(progress) == 2
    assert progress.coins == 1000 - 150 - 300
    assert not rewards.buy(progress, heart2)
    progress.coins = 10
    assert not rewards.buy(progress, rewards.ITEMS_BY_ID["shield"])


def test_skins_buy_and_equip(tmp_path):
    progress = fresh_progress(tmp_path)
    assert rewards.skin_number(progress) == 1
    assert not rewards.equip_skin(progress, "skin2")
    progress.coins = 500
    assert rewards.buy(progress, rewards.ITEMS_BY_ID["skin2"])
    assert rewards.skin_number(progress) == 2
    assert rewards.equip_skin(progress, "skin1")
    assert rewards.skin_number(progress) == 1


def test_upgrades_give_extra_hearts_and_shield():
    level = LEVELS["3-1"]
    world = World(level, bonus_hp=2, shield=True)
    assert (world.hp, world.max_hp, world.shield) == (5, 5, True)
    world.hurt("thử")
    assert world.hp == 5 and world.damage_taken == 0 and not world.shield
    world.hurt("thử")
    assert world.hp == 4 and world.damage_taken == 1


def test_healing_level_ignores_upgrades():
    level = LEVELS["17-1"]
    world = World(level, bonus_hp=2, shield=True)
    assert (world.hp, world.max_hp, world.shield) == (1, 3, False)


def test_progress_saves_rewards_and_migrates_old_files(tmp_path):
    main = tmp_path / "progress.json"
    main.write_text(json.dumps({"completed": ["1-1", "1-2"], "code": {}}), encoding="utf-8")
    progress = Progress(main, None)
    assert progress.stars == {"1-1": 1, "1-2": 1}
    assert progress.coins == 2 * rewards.STAR_COINS
    progress.owned.add("shield")
    progress.skin = "skin2"
    progress.chests.add(1)
    progress.save()
    reopened = Progress(main, None)
    assert reopened.coins == progress.coins and reopened.owned == {"shield"}
    assert reopened.skin == "skin2" and reopened.chests == {1}
    assert reopened.stars == progress.stars
