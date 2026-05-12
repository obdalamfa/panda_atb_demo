from core.progression import PlayerProfile


def test_level_up_progression():
    p = PlayerProfile()
    lines = p.gain_exp(200)
    assert p.level >= 2
    assert any("Level Up" in ln for ln in lines)


def test_inventory_consume():
    p = PlayerProfile()
    p.add_item("potion", 1)
    assert p.consume_item("potion", 1) is True
