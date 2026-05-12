from pathlib import Path

from battle.engine import BattleEngine


def test_engine_construct_with_enemy_filter():
    root = Path(__file__).resolve().parents[1]
    engine = BattleEngine(
        root / "config" / "battle.json",
        wave_index=1,
        enemy_ids=["slime_a"],
    )
    assert len(engine.enemies) == 1
    assert engine.enemies[0].unit_id == "slime_a"
