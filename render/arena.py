"""
Arena scene — 2.5D billboard characters.
Handles per-frame animations (idle bob, attack lunge, death sink),
VFX spawning (slash arc, shockwave, ranged bolt), screen shake.
"""
from __future__ import annotations

import math

from direct.interval.IntervalGlobal import (
    Func, LerpColorScaleInterval, LerpPosInterval, LerpScaleInterval,
    Parallel, Sequence, Wait,
)
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight, CardMaker, DirectionalLight,
    LColor, Point3, TextNode, Vec3,
)

from render.scenery import build_scenery
from render.sprites import make_char_sprite

_DEPTH_NEAR = 10.0
_DEPTH_FAR  = 19.0
_SCALE_NEAR = 1.00
_SCALE_FAR  = 0.78


def _dw(depth: float, play_d: float = 4.5) -> float:
    return _DEPTH_NEAR + (depth / play_d) * (_DEPTH_FAR - _DEPTH_NEAR)


def _dscale(depth: float, play_d: float = 4.5) -> float:
    return _SCALE_NEAR + (depth / play_d) * (_SCALE_FAR - _SCALE_NEAR)


def _make_hp_bar(parent, width=1.1, z_pos=2.55):
    cm = CardMaker("hp_bg")
    cm.setFrame(-(width / 2 + 0.05), width / 2 + 0.05, -0.11, 0.11)
    bg = parent.attachNewNode(cm.generate())
    bg.setColor(LColor(0.08, 0.08, 0.08, 0.88))
    bg.setPos(0, 0, z_pos)
    bg.setBillboardPointEye()

    cm2 = CardMaker("hp_fill")
    cm2.setFrame(0.0, width, -0.085, 0.085)
    fill = parent.attachNewNode(cm2.generate())
    fill.setColor(LColor(0.20, 0.85, 0.35, 1.0))
    fill.setPos(-width / 2, -0.01, z_pos)
    fill.setBillboardPointEye()
    return fill


def _make_name_label(parent, text, z=2.82):
    tn = TextNode("name_lbl")
    tn.setText(text)
    tn.setAlign(TextNode.ACenter)
    np = parent.attachNewNode(tn)
    np.setScale(0.26)
    np.setColor(LColor(0.92, 0.92, 0.95, 1.0))
    np.setPos(0, -0.02, z)
    np.setBillboardPointEye()


def _make_shadow(parent, radius=0.55):
    cm = CardMaker("shadow")
    cm.setFrame(-radius, radius, -radius * 0.35, radius * 0.35)
    sh = parent.attachNewNode(cm.generate())
    sh.setColor(LColor(0.0, 0.0, 0.0, 0.36))
    sh.setPos(0, 0.02, 0.02)
    sh.setHpr(0, -90, 0)
    return sh


class ArenaScene:
    def __init__(self, base: ShowBase, engine, zone: int = 1) -> None:
        self.base   = base
        self.engine = engine
        self.root   = base.render.attachNewNode("arena_root")

        self._hp_fills:    dict[str, object]  = {}
        self._char_nodes:  dict[str, object]  = {}
        self._shadow_nodes:dict[str, object]  = {}
        self._flash_seqs:  dict[str, object]  = {}
        self._vfx_nodes:   list[object]       = []  # temporary VFX nodes

        # Screen shake
        self._shake_t    = 0.0
        self._shake_amp  = 0.0

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
        self._hp_fills.clear()
        self._char_nodes.clear()
        self._shadow_nodes.clear()
        self._flash_seqs.clear()
        e = self.engine

        def _add(unit, nname, bar_w, bar_z, name_z, shad_r):
            node = self.root.attachNewNode(nname)
            _, h = make_char_sprite(node, unit.unit_id)
            _make_name_label(node, unit.name, z=h + name_z)
            self._hp_fills[unit.unit_id]     = _make_hp_bar(node, bar_w, h + bar_z)
            self._shadow_nodes[unit.unit_id] = _make_shadow(node, shad_r)
            self._char_nodes[unit.unit_id]   = node

        _add(e.player, "hero_vis", 1.1, 0.32, 0.55, 0.60)
        for u in e.enemies:
            _add(u, f"enemy_vis_{u.unit_id}", 1.0, 0.28, 0.50, 0.52)

        self._sync_positions(force=True)

    def reset_for_battle(self, zone: int) -> None:
        for node in self._char_nodes.values():
            if not node.isEmpty():
                node.removeNode()
        for vn in self._vfx_nodes:
            try:
                if not vn.isEmpty():
                    vn.removeNode()
            except Exception:
                pass
        self._vfx_nodes.clear()

        if not self._scenery_np.isEmpty():
            self._scenery_np.removeNode()
        self._scenery_np = self.root.attachNewNode("scenery")
        build_scenery(self._scenery_np, self.base, zone)
        self._build_characters()

    # ── Lights ────────────────────────────────────────────────────────────────

    def _lights(self) -> None:
        al = AmbientLight("arena_a")
        al.setColor((0.40, 0.42, 0.48, 1))
        self.base.render.setLight(self.base.render.attachNewNode(al))

        dl = DirectionalLight("arena_d")
        dl.setDirection((0.25, -1, -0.55))
        dl.setColor((0.88, 0.86, 0.78, 1))
        self.base.render.setLight(self.base.render.attachNewNode(dl))

    # ── Per-frame main call ───────────────────────────────────────────────────

    def update_characters(self, dt: float = 0.0) -> None:
        self._sync_positions()
        self._update_hp_bars()
        self._update_screen_shake(dt)

    # ── Position sync with animation offsets ──────────────────────────────────

    def _sync_positions(self, force: bool = False) -> None:
        e = self.engine

        def _place(node, unit):
            # Bob amplitude depends on state
            bob = 0.0
            if unit.state in ("idle",):
                bob = math.sin(unit.anim_t * 2.8) * 0.06
            elif unit.state == "walk":
                bob = math.sin(unit.anim_t * 6.5) * 0.10
            elif unit.state == "attack":
                bob = math.sin(unit.anim_t * 18.0) * 0.04

            # Squash/stretch during attack
            sx = sy = sz = 1.0
            if unit.state == "attack":
                sq = 1.0 + math.sin(unit.anim_t * 20.0) * 0.08
                sx = sq
                sz = 2.0 - sq

            x_vis    = unit.x     + unit.lunge_dx
            depth_vis = unit.depth + unit.lunge_dd
            wy       = _dw(max(0.0, min(4.5, depth_vis)))
            sc       = _dscale(max(0.0, min(4.5, depth_vis)))

            node.setPos(x_vis, wy, unit.y + bob)
            node.setScale(sc * sx, sc, sc * sz)
            node.setH(180 if unit.facing == -1 else 0)

            # Shadow scales with height (shrinks when jumping)
            sh = self._shadow_nodes.get(unit.unit_id)
            if sh:
                shadow_scale = max(0.3, 1.0 - unit.y * 0.12)
                sh.setScale(shadow_scale, 1, shadow_scale)
                # alpha darkens shadow as character gets closer to ground
                sh.setColorScale(1, 1, 1, max(0.1, shadow_scale * 0.8))

            # Death: tilt and darken
            if unit.state == "dead":
                node.setR(min(85.0, (1.0 - unit.hurt_timer) * 100.0))
                node.setColorScale(LColor(0.55, 0.55, 0.55, 1.0))

        # Place hero
        pn = self._char_nodes.get(e.player.unit_id)
        if pn and not pn.isEmpty():
            _place(pn, e.player)

        # Place enemies
        for u in e.enemies:
            node = self._char_nodes.get(u.unit_id)
            if node and not node.isEmpty():
                _place(node, u)

    # ── HP bars ───────────────────────────────────────────────────────────────

    def _update_hp_bars(self) -> None:
        e = self.engine

        def _bar(uid, hp, max_hp):
            fill = self._hp_fills.get(uid)
            if not fill:
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

    # ── Screen shake ──────────────────────────────────────────────────────────

    def _update_screen_shake(self, dt: float) -> None:
        amp = self.engine.screen_shake
        if amp > 0:
            self._shake_t  += dt * 48.0
            ox = math.sin(self._shake_t)         * amp * 0.28
            oz = math.sin(self._shake_t * 1.37)  * amp * 0.18
            self.base.cam.setPos(
                self.cam_home.x + ox,
                self.cam_home.y,
                self.cam_home.z + oz,
            )
        else:
            self.base.cam.setPos(self.cam_home)

    # ── Hit flash ─────────────────────────────────────────────────────────────

    def flash_hit(self, unit_id: str, is_player: bool = False) -> None:
        node = self._char_nodes.get(unit_id)
        if not node or node.isEmpty():
            return
        try:
            prev = self._flash_seqs.get(unit_id)
            if prev:
                prev.pause()
        except Exception:
            pass
        col = LColor(1.0, 0.35, 0.35, 1) if is_player else LColor(1.5, 0.60, 0.30, 1)
        seq = Sequence(
            Func(lambda n=node, c=col: n.setColorScale(c)),
            Wait(0.06),
            Func(lambda n=node, c=col: n.setColorScale(c * 0.5)),
            Wait(0.06),
            Func(lambda n=node: n.clearColorScale()),
        )
        self._flash_seqs[unit_id] = seq
        seq.start()

    # ── Damage numbers ────────────────────────────────────────────────────────

    def spawn_damage_number(self, world_pos: Point3, text: str,
                            color=(1.0, 0.25, 0.20, 1.0)) -> None:
        tn = TextNode("dmg")
        tn.setText(text)
        tn.setAlign(TextNode.ACenter)
        np = self.root.attachNewNode(tn)
        np.setPos(world_pos + Vec3(0, 0, 1.0))
        np.setScale(0.70)
        np.setColor(LColor(*color))
        np.setBillboardPointEye()
        self._vfx_nodes.append(np)
        end_pos = world_pos + Vec3(0, 0, 3.6)
        seq = Sequence(
            Parallel(
                LerpPosInterval(np, 0.75, end_pos),
                LerpColorScaleInterval(np, 0.75, LColor(1, 1, 1, 0)),
            ),
            Func(lambda n=np: self._cleanup_vfx(n)),
        )
        seq.start()

    def _cleanup_vfx(self, node) -> None:
        try:
            if not node.isEmpty():
                node.removeNode()
        except Exception:
            pass
        if node in self._vfx_nodes:
            self._vfx_nodes.remove(node)

    # ── Damage log → visuals ──────────────────────────────────────────────────

    def process_damage_log(self) -> None:
        e = self.engine
        for uid, amount, is_heal, fx_type in e.damage_log:
            node = self._char_nodes.get(uid)
            if node and not node.isEmpty():
                pos = node.getPos()
                if is_heal:
                    self.spawn_damage_number(pos, f"+{amount}", (0.28, 1.0, 0.45, 1.0))
                else:
                    # Damage text bigger for heavy hits
                    scale_big = fx_type in ("heavy", "slam", "jump_slam")
                    color = (1.0, 0.82, 0.10, 1.0) if fx_type == "heavy" else (1.0, 0.22, 0.18, 1.0)
                    txt = f"-{amount}!" if scale_big else f"-{amount}"
                    self.spawn_damage_number(pos, txt, color)
                    self.flash_hit(uid, is_player=(uid == e.player.unit_id))
        e.damage_log.clear()

    # ── VFX queue → effects ───────────────────────────────────────────────────

    def process_vfx_queue(self) -> None:
        for ev in self.engine.vfx_queue:
            t = ev.get("type", "")
            if t == "slash_arc":
                self._vfx_slash_arc(ev)
            elif t == "heavy_slam":
                self._vfx_heavy_slam(ev)
            elif t == "jump_slam":
                self._vfx_jump_slam(ev)
            elif t == "enemy_slash":
                self._vfx_enemy_slash(ev)
            elif t == "slam_wave":
                self._vfx_slam_wave(ev)
            elif t == "ranged_bolt":
                self._vfx_ranged_bolt(ev)
        self.engine.vfx_queue.clear()

    def _world_pos(self, x: float, depth: float, z: float = 0.0) -> Point3:
        return Point3(x, _dw(max(0.0, min(4.5, depth))), z)

    def _make_orb(self, color: LColor, radius: float = 0.28) -> object:
        cm = CardMaker("vfx_orb")
        cm.setFrame(-radius, radius, -radius, radius)
        n = self.root.attachNewNode(cm.generate())
        n.setColor(color)
        n.setBillboardPointEye()
        self._vfx_nodes.append(n)
        return n

    def _make_ring(self, color: LColor, radius: float) -> object:
        cm = CardMaker("vfx_ring")
        cm.setFrame(-radius, radius, -radius * 0.35, radius * 0.35)
        n = self.root.attachNewNode(cm.generate())
        n.setColor(color)
        n.setHpr(0, -90, 0)
        self._vfx_nodes.append(n)
        return n

    # ── VFX helpers ───────────────────────────────────────────────────────────

    def _vfx_slash_arc(self, ev: dict) -> None:
        pos = self._world_pos(ev["x"], ev["depth"], 1.0)
        arc = self._make_orb(LColor(0.95, 0.95, 1.0, 0.9), radius=0.55)
        arc.setScale(1.6, 1.0, 0.38)
        arc.setPos(pos)
        Sequence(
            LerpScaleInterval(arc, 0.12, (2.4, 1.0, 0.22)),
            LerpColorScaleInterval(arc, 0.10, LColor(1, 1, 1, 0)),
            Func(lambda n=arc: self._cleanup_vfx(n)),
        ).start()

    def _vfx_heavy_slam(self, ev: dict) -> None:
        pos = self._world_pos(ev["x"], ev["depth"], 0.5)
        orb = self._make_orb(LColor(1.0, 0.65, 0.15, 1.0), radius=0.80)
        orb.setPos(pos)
        ring = self._make_ring(LColor(1.0, 0.50, 0.10, 0.75), 1.2)
        ring.setPos(pos + Vec3(0, 0, -0.5))
        Sequence(
            Parallel(
                LerpScaleInterval(orb, 0.18, (3.2, 3.2, 3.2)),
                LerpColorScaleInterval(orb, 0.18, LColor(1, 1, 1, 0)),
                LerpScaleInterval(ring, 0.18, (2.8, 2.8, 2.8)),
                LerpColorScaleInterval(ring, 0.18, LColor(1, 1, 1, 0)),
            ),
            Func(lambda a=orb, b=ring: [self._cleanup_vfx(a), self._cleanup_vfx(b)]),
        ).start()

    def _vfx_jump_slam(self, ev: dict) -> None:
        pos = self._world_pos(ev["x"], ev["depth"], 0.05)
        ring = self._make_ring(LColor(0.80, 0.60, 1.0, 0.85), 0.5)
        ring.setPos(pos)
        ring2 = self._make_ring(LColor(0.60, 0.40, 1.0, 0.60), 0.8)
        ring2.setPos(pos)
        Sequence(
            Parallel(
                LerpScaleInterval(ring,  0.22, (3.5, 3.5, 3.5)),
                LerpColorScaleInterval(ring,  0.22, LColor(1, 1, 1, 0)),
                LerpScaleInterval(ring2, 0.26, (5.0, 5.0, 5.0)),
                LerpColorScaleInterval(ring2, 0.26, LColor(1, 1, 1, 0)),
            ),
            Func(lambda a=ring, b=ring2: [self._cleanup_vfx(a), self._cleanup_vfx(b)]),
        ).start()

    def _vfx_enemy_slash(self, ev: dict) -> None:
        pos = self._world_pos(ev["x"], ev["depth"], 0.9)
        arc = self._make_orb(LColor(1.0, 0.28, 0.28, 0.80), radius=0.45)
        arc.setScale(1.4, 1.0, 0.30)
        arc.setPos(pos)
        Sequence(
            LerpScaleInterval(arc, 0.10, (2.0, 1.0, 0.18)),
            LerpColorScaleInterval(arc, 0.08, LColor(1, 1, 1, 0)),
            Func(lambda n=arc: self._cleanup_vfx(n)),
        ).start()

    def _vfx_slam_wave(self, ev: dict) -> None:
        pos = self._world_pos(ev["x"], ev["depth"], 0.05)
        ring = self._make_ring(LColor(0.95, 0.40, 0.10, 0.80), 0.6)
        ring.setPos(pos)
        Sequence(
            LerpScaleInterval(ring, 0.20, (4.5, 4.5, 4.5)),
            LerpColorScaleInterval(ring, 0.20, LColor(1, 1, 1, 0)),
            Func(lambda n=ring: self._cleanup_vfx(n)),
        ).start()

    def _vfx_ranged_bolt(self, ev: dict) -> None:
        src = self._world_pos(ev["sx"], ev["sd"], 1.1)
        dst = self._world_pos(ev["tx"], ev["td"], 1.1)
        bolt = self._make_orb(LColor(0.80, 0.25, 1.00, 1.0), radius=0.25)
        bolt.setPos(src)
        bolt.setScale(1.5)
        Sequence(
            LerpPosInterval(bolt, 0.22, dst),
            Func(lambda n=bolt: self._cleanup_vfx(n)),
            Func(lambda p=dst: self._ranged_impact(p)),
        ).start()

    def _ranged_impact(self, pos: Point3) -> None:
        imp = self._make_orb(LColor(0.80, 0.25, 1.00, 0.85), radius=0.45)
        imp.setPos(pos)
        Sequence(
            LerpScaleInterval(imp, 0.10, (2.2, 2.2, 2.2)),
            LerpColorScaleInterval(imp, 0.10, LColor(1, 1, 1, 0)),
            Func(lambda n=imp: self._cleanup_vfx(n)),
        ).start()
