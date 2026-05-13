from __future__ import annotations

from direct.interval.IntervalGlobal import (
    Func,
    LerpColorScaleInterval,
    LerpPosInterval,
    Parallel,
    Sequence,
    Wait,
)
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight,
    CardMaker,
    DirectionalLight,
    LColor,
    Point3,
    TextNode,
    Vec3,
)

from battle.engine import BattleEngine
from battle.entities import BattleUnit
from render.particle_fx import spawn_fire_bolt, spawn_heal_mist, spawn_thunder_sparks
from render.scenery import build_scenery
from render.sprites import make_char_sprite
from skills.base import SkillResult


def _make_hp_bar(parent, width: float = 1.1, z_pos: float = 2.55) -> object:
    cm_bg = CardMaker("hp_bg")
    cm_bg.setFrame(-(width / 2 + 0.05), width / 2 + 0.05, -0.11, 0.11)
    bg = parent.attachNewNode(cm_bg.generate())
    bg.setColor(LColor(0.08, 0.08, 0.08, 0.88))
    bg.setPos(0, 0, z_pos)
    bg.setBillboardPointEye()
    cm_fill = CardMaker("hp_fill")
    cm_fill.setFrame(0.0, width, -0.085, 0.085)
    fill = parent.attachNewNode(cm_fill.generate())
    fill.setColor(LColor(0.20, 0.85, 0.35, 1.0))
    fill.setPos(-width / 2, -0.01, z_pos)
    fill.setBillboardPointEye()
    return fill


def _make_name_label(parent, text: str, z: float = 2.82) -> None:
    tn = TextNode("name_lbl")
    tn.setText(text)
    tn.setAlign(TextNode.ACenter)
    np = parent.attachNewNode(tn)
    np.setScale(0.26)
    np.setColor(LColor(0.92, 0.92, 0.95, 1.0))
    np.setPos(0, -0.02, z)
    np.setBillboardPointEye()


class ArenaScene:
    """Arena with JRPG-style billboard characters, HP bars, and VFX."""

    def __init__(self, base: ShowBase, engine: BattleEngine, zone: int = 1) -> None:
        self.base = base
        self.engine = engine
        self.root = base.render.attachNewNode("arena_root")
        self._fx_seq = None
        self._active_particles: list = []
        self._hp_fill_nodes: dict[str, object] = {}
        self.enemy_nodes: dict[str, object] = {}

        base.disableMouse()
        self._scenery_np = self.root.attachNewNode("scenery")
        build_scenery(self._scenery_np, base, zone)
        self._build_characters()
        self._lights()

        base.cam.setPos(0, -28.5, 12.8)
        base.cam.lookAt(Point3(0.5, 14.2, 1.2))
        self.cam_home = Point3(base.cam.getPos())

        self._bolt = self._make_orb(LColor(1.0, 0.35, 0.1, 1.0))
        self._bolt.reparentTo(self.root)
        self._bolt.hide()
        self._spark = self._make_orb(LColor(1.0, 1.0, 0.35, 1.0))
        self._spark.reparentTo(self.root)
        self._spark.hide()

    def _build_characters(self) -> None:
        self._hp_fill_nodes.clear()
        self.enemy_nodes.clear()

        self.hero_np = self.root.attachNewNode("hero_vis")
        _, hero_h = make_char_sprite(self.hero_np, self.engine.hero.unit_id)
        _make_name_label(self.hero_np, self.engine.hero.name, z=hero_h + 0.55)
        self._hp_fill_nodes[self.engine.hero.unit_id] = _make_hp_bar(
            self.hero_np, width=1.1, z_pos=hero_h + 0.32
        )
        self.hero_home = Point3(-5.4, 14.0, 0.0)
        self.hero_np.setPos(self.hero_home)

        enemies = self.engine.enemies
        n = max(1, len(enemies))
        spread = min(11.5, 2.9 + max(0, n - 1) * 2.85)
        for i, u in enumerate(enemies):
            g = float(i) / max(1.0, float(n - 1))
            x_center = spread * g - spread * 0.5 + 6.8
            node = self.root.attachNewNode(f"enemy_vis_{u.unit_id}")
            _, eh = make_char_sprite(node, u.unit_id)
            _make_name_label(node, u.name, z=eh + 0.50)
            self._hp_fill_nodes[u.unit_id] = _make_hp_bar(node, width=1.0, z_pos=eh + 0.28)
            pos = Point3(x_center + 1.05, 14.0, 0.0)
            node.setPos(pos)
            node.setPythonTag("_home_pos", Point3(pos))
            self.enemy_nodes[u.unit_id] = node

        self.enemy_home = Point3(5.9, 14.0, 0.0)

    def reset_for_battle(self, zone: int) -> None:
        if hasattr(self, "hero_np") and not self.hero_np.isEmpty():
            self.hero_np.removeNode()
        for node in self.enemy_nodes.values():
            if not node.isEmpty():
                node.removeNode()

        if not self._scenery_np.isEmpty():
            self._scenery_np.removeNode()
        self._scenery_np = self.root.attachNewNode("scenery")
        build_scenery(self._scenery_np, self.base, zone)

        self._build_characters()

    def _lights(self) -> None:
        ambient = AmbientLight("arena_ambient")
        ambient.setColor((0.40, 0.42, 0.48, 1))
        an = self.base.render.attachNewNode(ambient)
        self.base.render.setLight(an)

        sun = DirectionalLight("arena_sun")
        sun.setDirection((0.25, -1, -0.55))
        sun.setColor((0.88, 0.86, 0.78, 1))
        sn = self.base.render.attachNewNode(sun)
        self.base.render.setLight(sn)

    def _make_orb(self, color: LColor):
        cm = CardMaker("orb")
        cm.setFrame(-0.35, 0.35, -0.35, 0.35)
        n = self.root.attachNewNode(cm.generate())
        n.setBillboardPointEye()
        n.setColor(color)
        n.setScale(1.2)
        return n

    def _clear_timeline(self) -> None:
        if self._fx_seq is not None:
            self._fx_seq.pause()
            self._fx_seq = None

    def set_target_highlight(self, unit_id: str | None) -> None:
        for uid, node in self.enemy_nodes.items():
            if uid == unit_id:
                node.setColorScale(1.3, 1.3, 0.85, 1)
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
        return node, node.getPythonTag("_home_pos")

    def update_hp_bars(self) -> None:
        h = self.engine.hero
        self._update_bar(h.unit_id, h.hp, h.max_hp)
        for foe in self.engine.enemies:
            self._update_bar(foe.unit_id, foe.hp, foe.max_hp)

    def _update_bar(self, uid: str, hp: int, max_hp: int) -> None:
        fill = self._hp_fill_nodes.get(uid)
        if fill is None:
            return
        pct = max(0.0, hp / max_hp) if max_hp > 0 else 0.0
        fill.setScale(pct, 1.0, 1.0)
        if pct > 0.6:
            fill.setColor(LColor(0.20, 0.85, 0.35, 1.0))
        elif pct > 0.3:
            fill.setColor(LColor(0.95, 0.80, 0.10, 1.0))
        else:
            fill.setColor(LColor(0.90, 0.20, 0.18, 1.0))

    def spawn_damage_number(
        self,
        world_pos: Point3,
        text: str,
        color: tuple = (1.0, 0.25, 0.20, 1.0),
    ) -> None:
        tn = TextNode("dmg_num")
        tn.setText(text)
        tn.setAlign(TextNode.ACenter)
        np = self.root.attachNewNode(tn)
        np.setPos(world_pos + Vec3(0, 0, 1.2))
        np.setScale(0.72)
        np.setColor(LColor(*color))
        np.setBillboardPointEye()
        end_pos = world_pos + Vec3(0, 0, 3.8)
        seq = Sequence(
            Parallel(
                LerpPosInterval(np, 0.80, end_pos),
                LerpColorScaleInterval(np, 0.80, LColor(1, 1, 1, 0)),
            ),
            Func(np.removeNode),
        )
        seq.start()

    def play_result(self, actor: BattleUnit, result: SkillResult, on_done) -> None:
        self._clear_timeline()
        self.set_target_highlight(None)

        tgt_id = result.fx_target_unit_id
        if tgt_id is None and actor.is_player and result.fx in ("slash", "fire_bolt", "thunder"):
            foes = self.engine.alive_enemies()
            if len(foes) == 1:
                tgt_id = foes[0].unit_id
        defender_np, _home = self._np_for_unit_id(tgt_id)

        if result.damage_dealt > 0 and tgt_id is not None:
            tgt_np, _ = self._np_for_unit_id(tgt_id)
            if tgt_np is not None:
                self.spawn_damage_number(
                    tgt_np.getPos(), f"-{result.damage_dealt}", (1.0, 0.25, 0.20, 1.0)
                )
        if result.heal_dealt > 0:
            actor_np, _ = self._np_for_unit_id(actor.unit_id)
            if actor_np is None:
                actor_np = self.hero_np
            self.spawn_damage_number(
                actor_np.getPos(), f"+{result.heal_dealt}", (0.28, 1.0, 0.45, 1.0)
            )

        hero = self.hero_np
        seq = Sequence()

        if result.fx == "slash":
            if defender_np is None:
                defender_np = (
                    hero if not actor.is_player
                    else next(iter(self.enemy_nodes.values()), hero)
                )
            atk_np = hero if actor.is_player else self.enemy_nodes.get(actor.unit_id, hero)
            tgt_np2 = defender_np
            atk_home_pt = (
                self.hero_home if actor.is_player
                else (atk_np.getPythonTag("_home_pos") or self.hero_home)
            )
            rush = atk_np.posInterval(
                0.10,
                Point3(
                    defender_np.getX() + (-0.9 if actor.is_player else 0.9),
                    defender_np.getY(),
                    defender_np.getZ(),
                ),
            )
            seq.append(rush)
            seq.append(Func(lambda n=tgt_np2: n.setColorScale(1.25, 0.50, 0.50, 1)))
            seq.append(Wait(0.06))
            seq.append(Func(lambda n=tgt_np2: n.clearColorScale()))
            seq.append(self.base.camera.posInterval(0.05, self.cam_home + Vec3(0.14, 0, 0)))
            seq.append(self.base.camera.posInterval(0.05, self.cam_home))
            seq.append(atk_np.posInterval(0.12, atk_home_pt))

        elif result.fx == "fire_bolt":
            start_np = (
                hero if actor.is_player
                else self.enemy_nodes.get(actor.unit_id, hero)
            )
            end_np = defender_np if defender_np is not None else hero
            start_world = start_np.getPos() + Vec3(0, 0, 1.1)
            end_world = end_np.getPos() + Vec3(0, 0, 1.1)

            cm = CardMaker("bolt_orb")
            cm.setFrame(-0.32, 0.32, -0.32, 0.32)
            bolt = self.root.attachNewNode(cm.generate())
            bolt.setColor(LColor(1.0, 0.50, 0.10, 1.0))
            bolt.setBillboardPointEye()
            bolt.setPos(start_world)
            bolt.setScale(1.8)

            seq.append(bolt.posInterval(0.20, end_world))

            def end_fire(b=bolt, en=end_np, ew=end_world):
                if not b.isEmpty():
                    b.removeNode()
                spawn_fire_bolt(self.base, ew)
                en.setColorScale(1.4, 0.50, 0.25, 1)

            seq.append(Func(end_fire))
            seq.append(Wait(0.08))
            seq.append(Func(lambda n=end_np: n.clearColorScale()))
            seq.append(self.base.camera.posInterval(0.04, self.cam_home + Vec3(-0.12, 0, 0)))
            seq.append(self.base.camera.posInterval(0.04, self.cam_home))

        elif result.fx == "thunder":
            tgt_local = defender_np if defender_np is not None else hero
            tgt_world = tgt_local.getPos() + Vec3(0, 0, 2.2)

            def start_th(tl=tgt_local, tw=tgt_world):
                spawn_thunder_sparks(self.base, tw)
                tl.setColorScale(1.18, 1.08, 0.42, 1)

            seq.append(Func(start_th))
            seq.append(Wait(0.15))
            seq.append(Func(lambda tl=tgt_local: tl.clearColorScale()))
            seq.append(self.base.camera.posInterval(0.04, self.cam_home + Vec3(0, 0, 0.14)))
            seq.append(self.base.camera.posInterval(0.04, self.cam_home))

        elif result.fx == "heal":
            hero_world = hero.getPos() + Vec3(0, 0, 0.9)

            def start_he(hw=hero_world):
                spawn_heal_mist(self.base, hw)
                hero.setColorScale(0.60, 1.10, 0.82, 1)

            seq.append(Func(start_he))
            seq.append(Wait(0.18))
            seq.append(Func(lambda: hero.clearColorScale()))

        elif result.fx == "guard":
            seq.append(Func(lambda: hero.setColorScale(0.72, 0.84, 1.18, 1)))
            seq.append(Wait(0.14))
            seq.append(Func(lambda: hero.clearColorScale()))

        elif result.fx == "wait":
            seq.append(hero.posInterval(0.08, self.hero_home + Vec3(0, 0, 0.30)))
            seq.append(hero.posInterval(0.08, self.hero_home))

        else:
            seq.append(Wait(0.05))

        seq.append(Func(on_done))
        self._fx_seq = seq
        seq.start()
