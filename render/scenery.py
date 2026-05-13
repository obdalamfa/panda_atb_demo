from __future__ import annotations

from panda3d.core import CardMaker, LColor, NodePath

_PALETTES: dict[int, dict[str, LColor]] = {
    1: {  # Forest
        "sky_far":  LColor(0.07, 0.16, 0.08, 1),
        "sky_mid":  LColor(0.11, 0.22, 0.11, 1),
        "horizon":  LColor(0.35, 0.70, 0.28, 0.55),
        "floor":    LColor(0.09, 0.14, 0.09, 1),
        "grid":     LColor(0.15, 0.22, 0.13, 1),
        "edge":     LColor(0.20, 0.58, 0.20, 0.60),
        "bg_color": (0.06, 0.10, 0.07, 1),
    },
    2: {  # Ruins
        "sky_far":  LColor(0.16, 0.12, 0.06, 1),
        "sky_mid":  LColor(0.24, 0.18, 0.08, 1),
        "horizon":  LColor(0.80, 0.52, 0.16, 0.55),
        "floor":    LColor(0.20, 0.15, 0.09, 1),
        "grid":     LColor(0.28, 0.22, 0.13, 1),
        "edge":     LColor(0.74, 0.46, 0.12, 0.60),
        "bg_color": (0.10, 0.08, 0.04, 1),
    },
    3: {  # Cave
        "sky_far":  LColor(0.05, 0.03, 0.02, 1),
        "sky_mid":  LColor(0.09, 0.05, 0.03, 1),
        "horizon":  LColor(0.60, 0.28, 0.06, 0.55),
        "floor":    LColor(0.10, 0.07, 0.05, 1),
        "grid":     LColor(0.16, 0.11, 0.07, 1),
        "edge":     LColor(0.58, 0.26, 0.06, 0.60),
        "bg_color": (0.04, 0.02, 0.01, 1),
    },
    4: {  # Dark Realm
        "sky_far":  LColor(0.05, 0.02, 0.12, 1),
        "sky_mid":  LColor(0.08, 0.03, 0.18, 1),
        "horizon":  LColor(0.55, 0.10, 0.80, 0.55),
        "floor":    LColor(0.07, 0.03, 0.13, 1),
        "grid":     LColor(0.13, 0.05, 0.22, 1),
        "edge":     LColor(0.55, 0.10, 0.80, 0.60),
        "bg_color": (0.03, 0.01, 0.08, 1),
    },
}


def build_scenery(root: NodePath, base, zone: int) -> None:
    pal = _PALETTES.get(zone, _PALETTES[1])
    bg = pal["bg_color"]
    base.setBackgroundColor(bg[0], bg[1], bg[2], bg[3])

    def _quad(name: str, l, r, b, t) -> NodePath:
        cm = CardMaker(name)
        cm.setFrame(l, r, b, t)
        return root.attachNewNode(cm.generate())

    sky = _quad("sky_far", -26, 26, -2, 22)
    sky.setColor(pal["sky_far"])
    sky.setPos(0, 25, 0)

    mid = _quad("sky_mid", -24, 24, -1, 10)
    mid.setColor(pal["sky_mid"])
    mid.setPos(0, 22, 0)

    hz = _quad("horizon", -22, 22, -0.15, 0.15)
    hz.setColor(pal["horizon"])
    hz.setPos(0, 21.8, 5.6)

    floor = _quad("floor_base", -18, 18, -12, 14)
    floor.setP(-90)
    floor.setZ(0)
    floor.setColor(pal["floor"])

    gc = pal["grid"]
    for step in range(7):
        hl = _quad(f"grid_h{step}", -18, 18, -0.04, 0.04)
        hl.setP(-90)
        hl.setZ(0.005)
        hl.setY(8.0 + step * 2.2)
        hl.setColor(gc)

    for step in range(9):
        vl = _quad(f"grid_v{step}", -0.04, 0.04, -12, 14)
        vl.setP(-90)
        vl.setZ(0.005)
        vl.setX(-16.0 + step * 4.0)
        vl.setColor(gc)

    edge = _quad("floor_edge", -18, 18, -0.18, 0.18)
    edge.setP(-90)
    edge.setZ(0.01)
    edge.setY(7.8)
    edge.setColor(pal["edge"])

    {1: _deco_forest, 2: _deco_ruins, 3: _deco_cave, 4: _deco_realm}.get(
        zone, _deco_forest
    )(root)


def _deco_forest(root: NodePath) -> None:
    trunk_c = LColor(0.32, 0.20, 0.08, 1)
    leaf_c  = LColor(0.12, 0.42, 0.10, 1)
    for x, y in [(-14, 20), (-9, 22), (-5, 21), (8, 22), (12, 20), (16, 21)]:
        _rect(root, "trunk", x, y, 0,   -0.22, 0.22, 0, 2.8, trunk_c)
        _rect(root, "leaf",  x, y - 0.1, 1.6, -1.3, 1.3, 0, 3.8, leaf_c)


def _deco_ruins(root: NodePath) -> None:
    stone = LColor(0.42, 0.36, 0.26, 1)
    crack = LColor(0.25, 0.20, 0.12, 1)
    for x, y, h in [(-15, 20, 3.8), (-8, 22, 2.6), (10, 21, 4.2), (15, 20, 2.2)]:
        _rect(root, "pillar", x, y, 0, -0.5, 0.5, 0, h, stone)
        _rect(root, "crack",  x + 0.15, y - 0.05, h * 0.15, -0.07, 0.07, 0, h * 0.65, crack)


def _deco_cave(root: NodePath) -> None:
    rock = LColor(0.20, 0.14, 0.08, 1)
    glow = LColor(0.55, 0.22, 0.06, 0.5)
    for x, y, z, w in [(-13, 21, 5.2, 1.4), (-5, 22, 6.0, 1.0), (7, 21, 4.8, 1.2), (14, 20, 5.6, 0.9)]:
        _rect(root, "stala", x, y, z, -w / 2, w / 2, -3.5, 0, rock)
    for x, y in [(-10, 21), (4, 22), (11, 20)]:
        _rect(root, "glow", x, y - 0.2, 0.02, -0.6, 0.6, 0, 0.4, glow)


def _deco_realm(root: NodePath) -> None:
    cry  = LColor(0.50, 0.10, 0.78, 0.85)
    glow = LColor(0.72, 0.20, 0.95, 0.45)
    for x, y in [(-14, 20), (-8, 22), (9, 21), (14, 20)]:
        _rect(root, "crystal", x, y, 0, -0.38, 0.38, 0, 3.2, cry)
        _rect(root, "cglow",   x, y - 0.08, 0.4, -0.75, 0.75, 0.6, 2.6, glow)


def _rect(root, name, x, y, z, l, r, b, t, color: LColor) -> None:
    cm = CardMaker(name)
    cm.setFrame(l, r, b, t)
    n = root.attachNewNode(cm.generate())
    n.setPos(x, y, z)
    n.setColor(color)
