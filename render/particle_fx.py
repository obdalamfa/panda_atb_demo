"""
Interval-based particle burst effects — no Panda3D ParticleEffect dependency.
Each spawn function returns an _FXHandle that can be stopped via stop_pe().
"""
from __future__ import annotations

import math
import random

from direct.interval.IntervalGlobal import (
    Func,
    LerpColorScaleInterval,
    LerpPosInterval,
    Parallel,
    Sequence,
)
from direct.showbase.ShowBase import ShowBase
from panda3d.core import CardMaker, LColor, Vec3


class _FXHandle:
    def __init__(self, seqs: list, nodes: list) -> None:
        self._seqs = seqs
        self._nodes = nodes

    def disable(self) -> None:
        for s in self._seqs:
            try:
                s.pause()
            except Exception:
                pass

    def cleanup(self) -> None:
        self.disable()
        for n in list(self._nodes):
            try:
                if not n.isEmpty():
                    n.removeNode()
            except Exception:
                pass
        self._nodes.clear()


def _spawn_orbs(
    base: ShowBase,
    origin: Vec3,
    *,
    count: int,
    color: tuple,
    spread: float,
    duration: float,
    size: float = 0.20,
    z_bias: float = 0.5,
) -> _FXHandle:
    nodes: list = []
    seqs: list = []
    lc = LColor(*color)
    lc_fade = LColor(color[0] * 0.1, color[1] * 0.1, color[2] * 0.1, 0.0)

    for _ in range(count):
        cm = CardMaker("fx_orb")
        cm.setFrame(-size, size, -size, size)
        orb = base.render.attachNewNode(cm.generate())
        orb.setColor(lc)
        orb.setBillboardPointEye()
        orb.setPos(origin)

        angle = random.uniform(0, 2 * math.pi)
        v = random.uniform(0.3, 1.0)
        dx = math.cos(angle) * spread * v
        dz = (abs(math.sin(angle)) * spread * v * 0.8) + z_bias * random.uniform(0.4, 1.0)
        end = Vec3(origin) + Vec3(dx, 0.0, dz)

        move = LerpPosInterval(orb, duration, end)
        fade = LerpColorScaleInterval(orb, duration * 0.9, lc_fade)
        s = Sequence(Parallel(move, fade), Func(orb.removeNode))
        s.start()
        seqs.append(s)
        nodes.append(orb)

    return _FXHandle(seqs, nodes)


def spawn_fire_bolt(base: ShowBase, world_pos: Vec3) -> _FXHandle:
    return _spawn_orbs(
        base, Vec3(world_pos),
        count=20, color=(1.0, 0.50, 0.12, 1.0),
        spread=1.5, duration=0.45, size=0.24, z_bias=0.4,
    )


def spawn_thunder_sparks(base: ShowBase, world_pos: Vec3) -> _FXHandle:
    return _spawn_orbs(
        base, Vec3(world_pos),
        count=26, color=(1.0, 0.95, 0.28, 1.0),
        spread=2.2, duration=0.38, size=0.17, z_bias=-0.3,
    )


def spawn_heal_mist(base: ShowBase, world_pos: Vec3) -> _FXHandle:
    return _spawn_orbs(
        base, Vec3(world_pos),
        count=16, color=(0.38, 1.0, 0.58, 0.90),
        spread=0.9, duration=0.65, size=0.21, z_bias=1.2,
    )


def stop_pe(pe: _FXHandle | None) -> None:
    if pe is not None:
        pe.cleanup()
