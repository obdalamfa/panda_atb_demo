from __future__ import annotations

from direct.interval.IntervalGlobal import Func, Sequence, Wait
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, CardMaker, DirectionalLight, Point3, Vec3

from battle.engine import BattleEngine
from battle.entities import BattleUnit
from render.particle_fx import spawn_fire_bolt, spawn_heal_mist, spawn_thunder_sparks, stop_pe
from skills.base import SkillResult


def _cross_cards(parent, rgba: tuple[float, float, float, float]) -> None:
    cm = CardMaker("card")
    cm.setFrame(-0.55, 0.55, -1.15, 1.15)
    a = parent.attachNewNode(cm.generate())
    a.setColor(*rgba)
    b = parent.attachNewNode(cm.generate())
    b.setColor(*rgba)
    b.setH(90)


class ArenaScene:
    """Arena, unit silhouettes, lightweight motion, and Panda3D ParticleEffect bursts."""

    def __init__(self, base: ShowBase, engine: BattleEngine) -> None:
        self.base = base
        self.engine = engine
        self.root = base.render.attachNewNode("arena_root")
        self._fx_seq = None
        self._active_particles = []

        base.setBackgroundColor(0.09, 0.1, 0.14, 1)
        base.disableMouse()

        self._build_floor()

        self.hero_np = self.root.attachNewNode("hero_vis")
        _cross_cards(self.hero_np, (0.35, 0.65, 1.0, 1.0))

        self.enemy_nodes: dict[str, object] = {}
        enemies = engine.enemies
        n = max(1, len(enemies))
        spread = min(11.5, 2.9 + max(0, (n - 1)) * 2.85)

        self.hero_home = Point3(-5.4, 14.0, 1.35)
        self.hero_np.setPos(self.hero_home)

        for i, u in enumerate(enemies):
            g = float(i) / max(1.0, float(n - 1))
            x_center = spread * g - spread * 0.5 + 6.8
            z = Point3(x_center + 1.05, 14.0, 1.35)
            node = self.root.attachNewNode(f"enemy_vis_{u.unit_id}")
            _cross_cards(
                node,
                (0.35 + g * 0.35, 0.92 - g * 0.08, 0.38 + g * 0.12, 1.0),
            )
            node.setPos(z)
            self.enemy_nodes[u.unit_id] = node
            setattr(node, "_home_pos", Point3(z))

        self.enemy_home = Point3(5.9, 14.0, 1.35)

        self._lights()

        base.cam.setPos(0, -28.5, 12.8)
        base.cam.lookAt(Point3(0.5, 14.2, 1.2))
        self.cam_home = Point3(base.cam.getPos())

        self._bolt = self._make_orb((1.0, 0.35, 0.1, 1.0))
        self._bolt.reparentTo(self.root)
        self._bolt.hide()

        self._spark = self._make_orb((1.0, 1.0, 0.35, 1.0))
        self._spark.reparentTo(self.root)
        self._spark.hide()

    def _lights(self) -> None:
        ambient = AmbientLight("arena_ambient")
        ambient.setColor((0.32, 0.34, 0.38, 1))
        an = self.base.render.attachNewNode(ambient)
        self.base.render.setLight(an)

        sun = DirectionalLight("arena_sun")
        sun.setDirection((0.25, -1, -0.55))
        sun.setColor((0.92, 0.9, 0.82, 1))
        sn = self.base.render.attachNewNode(sun)
        self.base.render.setLight(sn)

    def _build_floor(self) -> None:
        cm = CardMaker("floor")
        cm.setFrame(-16.5, 16.5, -10, 11)
        floor = self.root.attachNewNode(cm.generate())
        floor.setP(-90)
        floor.setZ(0)
        floor.setColor(0.18, 0.2, 0.22, 1)

    def _make_orb(self, rgba: tuple[float, float, float, float]):
        cm = CardMaker("orb")
        cm.setFrame(-0.35, 0.35, -0.35, 0.35)
        n = self.root.attachNewNode(cm.generate())
        n.setBillboardPointEye()
        n.setColor(*rgba)
        n.setScale(1.2)
        return n

    def _clear_timeline(self) -> None:
        if self._fx_seq is not None:
            self._fx_seq.pause()
            self._fx_seq = None

    def set_target_highlight(self, unit_id: str | None) -> None:
        for uid, node in self.enemy_nodes.items():
            if uid == unit_id:
                node.setColorScale(1.2, 1.2, 0.95, 1)
            else:
                node.clearColorScale()

    def _np_for_unit_id(self, unit_id: str | None) -> tuple[object | None, Point3 | None]:
        if unit_id is None:
            return None, None
        if unit_id == self.engine.hero.unit_id:
            return self.hero_np, self.hero_home
        node = self.enemy_nodes.get(unit_id)
        if node is None:
            return None, None
        home = getattr(node, "_home_pos")
        return node, home

    def play_result(self, actor: BattleUnit, result: SkillResult, on_done) -> None:
        self._clear_timeline()
        self.set_target_highlight(None)

        tgt_id = result.fx_target_unit_id
        if tgt_id is None and actor.is_player and result.fx in ("slash", "fire_bolt", "thunder"):
            foes = self.engine.alive_enemies()
            if len(foes) == 1:
                tgt_id = foes[0].unit_id
        defender_np, _home = self._np_for_unit_id(tgt_id)

        hero = self.hero_np
        seq = Sequence()

        if result.fx == "slash":
            if defender_np is None:
                defender_np = hero if not actor.is_player else next(iter(self.enemy_nodes.values()), hero)
            atk_np = hero if actor.is_player else self.enemy_nodes.get(actor.unit_id)
            if atk_np is None:
                atk_np = hero
            tgt_np = defender_np

            atk_home_pt = self.hero_home if actor.is_player else getattr(atk_np, "_home_pos", self.hero_home)

            rush = atk_np.posInterval(
                0.1,
                Point3(defender_np.getX() + (-0.9 if actor.is_player else 0.9), defender_np.getY(), defender_np.getZ()),
            )
            seq.append(rush)

            def hit_flash():
                tgt_np.setColorScale(1.2, 0.55, 0.55, 1)

            seq.append(Func(hit_flash))
            seq.append(Wait(0.05))
            seq.append(Func(lambda: tgt_np.clearColorScale()))
            seq.append(self.base.camera.posInterval(0.05, self.cam_home + Vec3(0.12, 0, 0)))
            seq.append(self.base.camera.posInterval(0.05, self.cam_home))
            seq.append(atk_np.posInterval(0.12, atk_home_pt))

        elif result.fx == "fire_bolt":
            start_np = hero if actor.is_player else self.enemy_nodes.get(actor.unit_id, hero)
            if defender_np == hero:
                end_np = hero
            elif defender_np is not None:
                end_np = defender_np
            else:
                end_np = hero

            carrier = self.root.attachNewNode("fire_carrier")

            pe_holder: list | None = [None]

            def start_fire_pe():
                carrier.setPos(start_np.getPos() + Vec3(0, 0, 0.8))
                pe = spawn_fire_bolt(self.base, carrier, Vec3(0, 0, 0))
                pe_holder[0] = pe
                self._active_particles.append(pe)

            seq.append(Func(start_fire_pe))
            seq.append(Func(lambda: carrier.reparentTo(self.root)))
            seq.append(carrier.posInterval(0.24, end_np.getPos() + Vec3(0, 0, 0.8)))

            def end_fire_flash():
                if pe_holder[0] is not None:
                    stop_pe(pe_holder[0])
                end_np.setColorScale(1.35, 0.55, 0.28, 1)

            seq.append(Func(end_fire_flash))
            seq.append(Wait(0.07))
            seq.append(Func(lambda: end_np.clearColorScale()))
            seq.append(self.base.camera.posInterval(0.04, self.cam_home + Vec3(-0.1, 0, 0)))
            seq.append(self.base.camera.posInterval(0.04, self.cam_home))

        elif result.fx == "thunder":
            tgt = defender_np if defender_np is not None else hero
            anchor = tgt.getPos() + Vec3(0, 0, 3.8)
            attach = self.root.attachNewNode("thunder_spawn")
            attach.setPos(anchor)
            seq.append(Func(lambda attach=attach: attach.reparentTo(self.root)))

            pe_holder: list | None = [None]

            def start_th_pe():
                pe = spawn_thunder_sparks(self.base, attach, Vec3(0, 0, 0))
                pe_holder[0] = pe
                self._active_particles.append(pe)
                tgt.setColorScale(1.15, 1.05, 0.45, 1)

            seq.append(Func(start_th_pe))
            seq.append(Wait(0.13))

            def end_th_pe():
                if pe_holder[0] is not None:
                    stop_pe(pe_holder[0])
                tgt.clearColorScale()

            seq.append(Func(end_th_pe))
            seq.append(self.base.camera.posInterval(0.04, self.cam_home + Vec3(0, 0, 0.12)))
            seq.append(self.base.camera.posInterval(0.04, self.cam_home))

        elif result.fx == "heal":
            attach = hero.attachNewNode("heal_spawn")
            attach.setPos(Vec3(0, 0, 0.6))
            seq.append(Func(lambda attach=attach: attach.reparentTo(hero)))

            pe_holder: list | None = [None]

            def start_he_pe():
                pe = spawn_heal_mist(self.base, attach, Vec3(0, 0, 0))
                pe_holder[0] = pe
                self._active_particles.append(pe)
                hero.setColorScale(0.62, 1.08, 0.84, 1)

            seq.append(Func(start_he_pe))
            seq.append(Wait(0.16))

            def end_he_pe():
                if pe_holder[0] is not None:
                    stop_pe(pe_holder[0])
                hero.clearColorScale()

            seq.append(Func(end_he_pe))

        elif result.fx == "guard":
            seq.append(Func(lambda: hero.setColorScale(0.75, 0.85, 1.15, 1)))
            seq.append(Wait(0.12))
            seq.append(Func(lambda: hero.clearColorScale()))
        elif result.fx == "wait":
            seq.append(hero.posInterval(0.08, self.hero_home + Vec3(0, 0, 0.25)))
            seq.append(hero.posInterval(0.08, self.hero_home))
        else:
            seq.append(Wait(0.05))

        seq.append(Func(on_done))
        self._fx_seq = seq
        seq.start()
