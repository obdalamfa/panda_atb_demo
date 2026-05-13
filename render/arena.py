"""
Arena scene — billboard sprite characters on a 2.5D stage.
Positions are driven every frame by ActionEngine unit data (x, depth, y).
"""
from __future__ import annotations

from direct.interval.IntervalGlobal import Func, LerpColorScaleInterval, Parallel, Sequence, Wait
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

from render.scenery import build_scenery
from render.sprites import make_char_sprite

# World-space mapping for depth axis
_DEPTH_NEAR = 10.0   # depth=0  → world Y
_DEPTH_FAR  = 19.0   # depth=PLAY_D → world Y
_DEPTH_SPAN = _DEPTH_FAR - _DEPTH_NEAR   # = 9.0 / PLAY_D(4.5) = 2.0 per unit

# Scale range for 2.5D parallax (front bigger, back smaller)
_SCALE_NEAR = 1.00
_SCALE_FAR  = 0.78


def _depth_to_world(depth: float, play_d: float = 4.5) -> float:
    return _DEPTH_NEAR + (depth / play_d) * (_DEPTH_FAR - _DEPTH_NEAR)


def _depth_scale(depth: float, play_d: float = 4.5) -> float:
    t = depth / play_d
    return _SCALE_NEAR + t * (_SCALE_FAR - _SCALE_NEAR)


def _make_hp_bar(parent, width: float = 1.1, z_pos: float = 2.55):
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


def _make_shadow(parent, radius: float = 0.55):
    cm = CardMaker("shadow")
    cm.setFrame(-radius, radius, -radius * 0.35, radius * 0.35)
    sh = parent.attachNewNode(cm.generate())
    sh.setColor(LColor(0.0, 0.0, 0.0, 0.38))
    sh.setPos(0, 0.02, 0.02)
    sh.setHpr(0, -90, 0)
    return sh


class ArenaScene:
    """Billboard-sprite arena for the 2.5D beat-em-up."""

    def __init__(self, base: ShowBase, engine, zone: int = 1) -> None:
        self.base   = base
        self.engine = engine
        self.root   = base.render.attachNewNode("arena_root")

        self._hp_fill_nodes: dict[str, object] = {}
        self._char_nodes:    dict[str, object] = {}  # unit_id → NodePath
        self._flash_seqs:    dict[str, object] = {}

        base.disableMouse()
        self._scenery_np = self.root.attachNewNode("scenery")
        build_scenery(self._scenery_np, base, zone)
        self._build_characters()
        self._lights()

        base.cam.setPos(0, -28.5, 12.8)
        base.cam.lookAt(Point3(0.5, 14.2, 1.2))
        self.cam_home = Point3(base.cam.getPos())

    # ── Build / reset ─────────────────────────────────────────────────────────

    def _build_characters(self) -> None:
        self._hp_fill_nodes.clear()
        self._char_nodes.clear()
        self._flash_seqs.clear()
        e = self.engine

        # Hero
        hero_np = self.root.attachNewNode("hero_vis")
        _, hero_h = make_char_sprite(hero_np, e.player.unit_id)
        _make_name_label(hero_np, e.player.name, z=hero_h + 0.55)
        self._hp_fill_nodes[e.player.unit_id] = _make_hp_bar(hero_np, width=1.1, z_pos=hero_h + 0.32)
        _make_shadow(hero_np, radius=0.60)
        self._char_nodes[e.player.unit_id] = hero_np

        # Enemies
        for u in e.enemies:
            node = self.root.attachNewNode(f"enemy_vis_{u.unit_id}")
            _, eh = make_char_sprite(node, u.unit_id)
            _make_name_label(node, u.name, z=eh + 0.50)
            self._hp_fill_nodes[u.unit_id] = _make_hp_bar(node, width=1.0, z_pos=eh + 0.28)
            _make_shadow(node, radius=0.52)
            self._char_nodes[u.unit_id] = node

        # Set initial positions
        self._sync_positions()

    def reset_for_battle(self, zone: int) -> None:
        for node in self._char_nodes.values():
            if not node.isEmpty():
                node.removeNode()
        if not self._scenery_np.isEmpty():
            self._scenery_np.removeNode()
        self._scenery_np = self.root.attachNewNode("scenery")
        build_scenery(self._scenery_np, self.base, zone)
        self._build_characters()

    # ── Lights ────────────────────────────────────────────────────────────────

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

    # ── Per-frame updates ─────────────────────────────────────────────────────

    def _sync_positions(self) -> None:
        e = self.engine

        def _place(node, unit):
            wy = _depth_to_world(unit.depth)
            sc = _depth_scale(unit.depth)
            node.setPos(unit.x, wy, unit.y)
            node.setScale(sc, sc, sc)
            # face the camera (flip X for facing direction)
            node.setH(0)
            if unit.facing == -1:
                node.setH(180)

        p_node = self._char_nodes.get(e.player.unit_id)
        if p_node and not p_node.isEmpty():
            _place(p_node, e.player)

        for u in e.enemies:
            node = self._char_nodes.get(u.unit_id)
            if node and not node.isEmpty():
                if not u.alive and u.state == "dead":
                    node.setZ(-0.5)   # slump slightly
                else:
                    _place(node, u)

    def update_characters(self) -> None:
        self._sync_positions()
        self._update_hp_bars()

    def _update_hp_bars(self) -> None:
        e = self.engine

        def _bar(uid, hp, max_hp):
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

        _bar(e.player.unit_id, e.player.hp, e.player.max_hp)
        for foe in e.enemies:
            _bar(foe.unit_id, foe.hp, foe.max_hp)

    # ── Hit flash ─────────────────────────────────────────────────────────────

    def flash_hit(self, unit_id: str, is_player_hit: bool = False) -> None:
        node = self._char_nodes.get(unit_id)
        if node is None or node.isEmpty():
            return
        if unit_id in self._flash_seqs and self._flash_seqs[unit_id]:
            try:
                self._flash_seqs[unit_id].pause()
            except Exception:
                pass
        if is_player_hit:
            color = LColor(1.0, 0.40, 0.40, 1)
        else:
            color = LColor(1.30, 0.55, 0.30, 1)
        seq = Sequence(
            Func(lambda n=node, c=color: n.setColorScale(c)),
            Wait(0.08),
            Func(lambda n=node: n.clearColorScale()),
        )
        self._flash_seqs[unit_id] = seq
        seq.start()

    # ── Damage numbers ────────────────────────────────────────────────────────

    def spawn_damage_number(
        self,
        world_pos: Point3,
        text: str,
        color: tuple = (1.0, 0.25, 0.20, 1.0),
    ) -> None:
        from direct.interval.IntervalGlobal import LerpPosInterval
        tn = TextNode("dmg_num")
        tn.setText(text)
        tn.setAlign(TextNode.ACenter)
        np = self.root.attachNewNode(tn)
        np.setPos(world_pos + Vec3(0, 0, 1.0))
        np.setScale(0.68)
        np.setColor(LColor(*color))
        np.setBillboardPointEye()
        end_pos = world_pos + Vec3(0, 0, 3.6)
        seq = Sequence(
            Parallel(
                LerpPosInterval(np, 0.75, end_pos),
                LerpColorScaleInterval(np, 0.75, LColor(1, 1, 1, 0)),
            ),
            Func(np.removeNode),
        )
        seq.start()

    def process_damage_log(self) -> None:
        """Read engine.damage_log and spawn visuals for each entry."""
        e = self.engine
        for uid, amount, is_heal in e.damage_log:
            node = self._char_nodes.get(uid)
            if node and not node.isEmpty():
                pos = node.getPos()
                if is_heal:
                    self.spawn_damage_number(pos, f"+{amount}", (0.28, 1.0, 0.45, 1.0))
                else:
                    self.spawn_damage_number(pos, f"-{amount}", (1.0, 0.25, 0.20, 1.0))
                    self.flash_hit(uid, is_player_hit=(uid == e.player.unit_id))
        e.damage_log.clear()
