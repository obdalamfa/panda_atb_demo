"""
Real-time 2.5D beat-em-up engine.
Player has 3 attack types; each enemy has a distinct attack style.
VFX events are queued for the arena to consume each frame.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

GRAVITY = -24.0
GROUND  =   0.0
PLAY_W  =   9.0   # x: -PLAY_W .. PLAY_W
PLAY_D  =   4.5   # depth: 0 .. PLAY_D

# ── Player attack types ───────────────────────────────────────────────────────
AT_LIGHT = "light"      # J  — fast, 1× dmg, normal reach
AT_HEAVY = "heavy"      # K  — slow, 2.2× dmg, wide reach, shockwave
AT_JUMP  = "jump_slam"  # J in air — AoE on landing, 1.8× dmg

# ── Enemy attack styles ───────────────────────────────────────────────────────
ES_BASIC  = "basic"    # standard melee
ES_SLAM   = "slam"     # telegraphed wide slam, high damage
ES_COMBO  = "combo"    # two quick hits back-to-back
ES_RANGED = "ranged"   # fires a bolt (instant dmg + vfx)
ES_DIVE   = "dive"     # jumps up then crashes down on player


@dataclass
class ActionUnit:
    unit_id: str
    name:    str
    is_player: bool
    hp: int
    max_hp: int
    atk: int

    speed:        float = 4.0
    x:            float = 0.0
    depth:        float = 2.0
    y:            float = 0.0   # vertical (0 = ground)
    vy:           float = 0.0
    facing:       int   = 1     # 1=right, -1=left
    state:        str   = "idle"

    hurt_timer:   float = 0.0
    attack_timer: float = 0.0
    attack_cd:    float = 0.55
    attack_range: float = 1.5
    attack_depth: float = 0.9   # depth tolerance

    attack_style: str   = ES_BASIC   # enemy only
    combo_left:   int   = 0          # remaining combo hits

    # Visual offsets applied by arena (not used in logic)
    lunge_dx: float = 0.0
    lunge_dd: float = 0.0

    # Knockback
    kbv_x: float = 0.0   # knockback velocity x
    kbv_d: float = 0.0   # knockback velocity depth

    anim_t: float = 0.0  # per-unit animation clock

    exp_reward:  int      = 0
    gold_reward: int      = 0
    loot_reward: list[str] = field(default_factory=list)

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int, kbx: float = 0.0, kbd: float = 0.0) -> int:
        if self.hurt_timer > 0 or self.state == "dead":
            return 0
        actual = max(1, amount)
        self.hp = max(0, self.hp - actual)
        if self.hp <= 0:
            self.state = "dead"
        else:
            self.state      = "hurt"
            self.hurt_timer = 0.50
            self.kbv_x = kbx
            self.kbv_d = kbd
        return actual


class ActionEngine:
    def __init__(self, player_data: dict, enemies_data: list[dict], wave: int = 1) -> None:
        self.wave  = wave
        scale      = 1.0 + (wave - 1) * 0.07

        p = player_data
        self.player = ActionUnit(
            unit_id="hero", name=p.get("name", "Hero"),
            is_player=True,
            hp=p.get("hp", 100), max_hp=p.get("hp", 100),
            atk=p.get("atk", 22), speed=p.get("speed", 4.8),
            x=-5.5, depth=2.2, facing=1,
        )

        self.enemies: list[ActionUnit] = []
        for i, ed in enumerate(enemies_data):
            col, row = i % 3, i // 3
            hp_s = int(ed.get("hp", 40) * scale)
            self.enemies.append(ActionUnit(
                unit_id=ed.get("unit_id", f"enemy_{i}"),
                name=ed.get("name", "Enemy"),
                is_player=False,
                hp=hp_s, max_hp=hp_s,
                atk=int(ed.get("atk", 10) * scale),
                speed=ed.get("speed", 2.0),
                x=4.5 + col * 2.5, depth=1.2 + row * 1.5,
                facing=-1,
                attack_cd=ed.get("attack_cd", 1.5),
                attack_range=ed.get("attack_range", 1.3),
                attack_style=ed.get("attack_style", ES_BASIC),
                exp_reward=ed.get("exp", 20),
                gold_reward=ed.get("gold", 10),
                loot_reward=ed.get("loot", []),
            ))

        self.cleared   = False
        self.game_over = False

        self._queued_atk: str | None = None   # AT_LIGHT / AT_HEAVY / AT_JUMP
        self.combo_count = 0
        self.combo_timer = 0.0
        self.screen_shake = 0.0  # consumed by arena for camera shake

        self.damage_log: list[tuple[str, int, bool, str]] = []
        # (target_id, amount, is_heal, fx_type)

        self.vfx_queue: list[dict] = []
        # [{type, src_id, tgt_id, x, depth}]

    # ── Public ────────────────────────────────────────────────────────────────

    def queue_light_attack(self) -> None:
        if self._queued_atk is None:
            self._queued_atk = AT_LIGHT

    def queue_heavy_attack(self) -> None:
        if self._queued_atk is None:
            self._queued_atk = AT_HEAVY

    def queue_jump_attack(self) -> None:
        if self._queued_atk is None:
            self._queued_atk = AT_JUMP

    def alive_enemies(self) -> list[ActionUnit]:
        return [e for e in self.enemies if e.alive]

    def update(self, dt: float, keys: dict) -> None:
        if self.cleared or self.game_over:
            return
        self._tick_anim(dt)
        self._move_player(dt, keys)
        self._player_attack(dt)
        for enemy in self.enemies:
            if enemy.alive:
                self._enemy_update(enemy, dt)
        if not self.alive_enemies():
            self.cleared = True
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo_count = 0
        if self.screen_shake > 0:
            self.screen_shake = max(0.0, self.screen_shake - dt * 3.0)

    # ── Animation clock ───────────────────────────────────────────────────────

    def _tick_anim(self, dt: float) -> None:
        self.player.anim_t += dt
        for e in self.enemies:
            e.anim_t += dt

    # ── Knockback decay ───────────────────────────────────────────────────────

    def _apply_knockback(self, u: ActionUnit, dt: float) -> None:
        if u.kbv_x != 0 or u.kbv_d != 0:
            u.x     = max(-PLAY_W, min(PLAY_W, u.x     + u.kbv_x * dt))
            u.depth = max(0.0,     min(PLAY_D, u.depth  + u.kbv_d * dt))
            decay = max(0.0, 1.0 - dt * 6.0)
            u.kbv_x *= decay
            u.kbv_d *= decay

    # ── Lunge decay ───────────────────────────────────────────────────────────

    def _decay_lunge(self, u: ActionUnit, dt: float) -> None:
        decay = max(0.0, 1.0 - dt * 9.0)
        u.lunge_dx *= decay
        u.lunge_dd *= decay

    # ── Player movement ───────────────────────────────────────────────────────

    def _move_player(self, dt: float, keys: dict) -> None:
        p = self.player
        p.vy += GRAVITY * dt
        p.y   = max(GROUND, p.y + p.vy * dt)
        if p.y <= GROUND:
            p.y  = GROUND
            p.vy = 0.0

        self._apply_knockback(p, dt)
        self._decay_lunge(p, dt)

        if p.state == "hurt":
            p.hurt_timer -= dt
            if p.hurt_timer <= 0:
                p.state = "idle"
            return
        if p.state == "dead":
            return

        dx     = (1.0 if keys.get("d") or keys.get("arrow_right") else 0.0) \
                - (1.0 if keys.get("a") or keys.get("arrow_left")  else 0.0)
        ddepth = (1.0 if keys.get("w") or keys.get("arrow_up")    else 0.0) \
                - (1.0 if keys.get("s") or keys.get("arrow_down")  else 0.0)

        if dx != 0:
            p.facing = int(dx)
        if dx != 0 and ddepth != 0:
            dx     *= 0.707
            ddepth *= 0.707

        p.x     = max(-PLAY_W, min(PLAY_W, p.x     + dx     * p.speed * dt))
        p.depth = max(0.0,     min(PLAY_D, p.depth  + ddepth * p.speed * 0.55 * dt))

        if p.y <= GROUND and keys.get("space_pressed"):
            p.vy = 10.5
            keys["space_pressed"] = False

        if p.state == "attack":
            p.attack_timer -= dt
            if p.attack_timer <= 0:
                p.state = "idle"
        elif dx != 0 or ddepth != 0:
            p.state = "walk"
        else:
            p.state = "idle"

    # ── Player attack ─────────────────────────────────────────────────────────

    def _player_attack(self, dt: float) -> None:
        p = self.player
        if p.attack_timer > 0:
            p.attack_timer -= dt

        if self._queued_atk is None or p.attack_timer > 0:
            return
        if p.state in ("hurt", "dead"):
            self._queued_atk = None
            return

        atk_type = self._queued_atk
        self._queued_atk = None

        # Auto-upgrade to jump slam if airborne
        if p.y > 0.5 and atk_type == AT_LIGHT:
            atk_type = AT_JUMP

        if atk_type == AT_LIGHT:
            self._do_player_light(p)
        elif atk_type == AT_HEAVY:
            self._do_player_heavy(p)
        elif atk_type == AT_JUMP:
            self._do_player_jump_slam(p)

    def _do_player_light(self, p: ActionUnit) -> None:
        p.state        = "attack"
        p.attack_timer = 0.42
        p.lunge_dx     = p.facing * 0.9

        self.vfx_queue.append({"type": "slash_arc", "src_id": p.unit_id,
                                "x": p.x + p.facing * 0.8, "depth": p.depth})

        for enemy in self.alive_enemies():
            if abs(enemy.x - p.x) < 1.6 and abs(enemy.depth - p.depth) < 0.95:
                dmg    = p.atk + random.randint(-2, 5)
                kbx    = p.facing * 2.5
                actual = enemy.take_damage(dmg, kbx=kbx)
                if actual > 0:
                    self.damage_log.append((enemy.unit_id, actual, False, "light"))
                    self.combo_count += 1
                    self.combo_timer  = 2.5

    def _do_player_heavy(self, p: ActionUnit) -> None:
        p.state        = "attack"
        p.attack_timer = 0.75
        p.lunge_dx     = p.facing * 1.5

        self.vfx_queue.append({"type": "heavy_slam", "src_id": p.unit_id,
                                "x": p.x + p.facing * 1.2, "depth": p.depth})
        self.screen_shake = max(self.screen_shake, 0.25)

        for enemy in self.alive_enemies():
            if abs(enemy.x - p.x) < 2.5 and abs(enemy.depth - p.depth) < 1.2:
                dmg    = int(p.atk * 2.2) + random.randint(0, 8)
                kbx    = p.facing * 4.5
                actual = enemy.take_damage(dmg, kbx=kbx)
                if actual > 0:
                    self.damage_log.append((enemy.unit_id, actual, False, "heavy"))
                    self.combo_count += 1
                    self.combo_timer  = 2.5

    def _do_player_jump_slam(self, p: ActionUnit) -> None:
        p.state        = "attack"
        p.attack_timer = 0.55
        p.vy           = -6.0   # force down fast

        self.vfx_queue.append({"type": "jump_slam", "src_id": p.unit_id,
                                "x": p.x, "depth": p.depth})
        self.screen_shake = max(self.screen_shake, 0.20)

        for enemy in self.alive_enemies():
            if abs(enemy.x - p.x) < 2.0 and abs(enemy.depth - p.depth) < 1.3:
                dmg    = int(p.atk * 1.8) + random.randint(-2, 6)
                kbx    = (enemy.x - p.x) * 2.0   # radial knockback
                kbd    = (enemy.depth - p.depth) * 1.5
                actual = enemy.take_damage(dmg, kbx=kbx, kbd=kbd)
                if actual > 0:
                    self.damage_log.append((enemy.unit_id, actual, False, "jump_slam"))
                    self.combo_count += 1
                    self.combo_timer  = 2.5

    # ── Enemy update dispatcher ───────────────────────────────────────────────

    def _enemy_update(self, e: ActionUnit, dt: float) -> None:
        self._decay_lunge(e, dt)
        self._apply_knockback(e, dt)

        if e.hurt_timer > 0:
            e.hurt_timer -= dt
            if e.hurt_timer <= 0 and e.state == "hurt":
                e.state = "idle"
            return

        if e.attack_timer > 0:
            e.attack_timer -= dt

        if e.attack_style == ES_SLAM:
            self._enemy_slam(e, dt)
        elif e.attack_style == ES_COMBO:
            self._enemy_combo(e, dt)
        elif e.attack_style == ES_RANGED:
            self._enemy_ranged(e, dt)
        elif e.attack_style == ES_DIVE:
            self._enemy_dive(e, dt)
        else:
            self._enemy_basic(e, dt)

    # ── Enemy movement helper ─────────────────────────────────────────────────

    def _chase(self, e: ActionUnit, dt: float, stop_dist: float = 0.15) -> None:
        p  = self.player
        dx = p.x     - e.x
        dd = p.depth - e.depth
        dist = (dx * dx + dd * dd) ** 0.5
        if dist > stop_dist:
            e.state = "walk"
            e.x     += (dx / dist) * e.speed * dt
            e.depth += (dd / dist) * e.speed * 0.55 * dt
            e.facing = 1 if dx > 0 else -1
        else:
            e.state = "idle"

    def _in_melee(self, e: ActionUnit, rx: float | None = None, rd: float | None = None) -> bool:
        p   = self.player
        rx  = rx or e.attack_range
        rd  = rd or e.attack_depth
        return abs(e.x - p.x) < rx and abs(e.depth - p.depth) < rd

    def _deal_to_player(self, e: ActionUnit, mult: float = 1.0,
                        kbx: float = 0.0, kbd: float = 0.0) -> None:
        if self.player.state == "dead":
            return
        dmg    = int(e.atk * mult) + random.randint(-1, 3)
        actual = self.player.take_damage(dmg, kbx=kbx, kbd=kbd)
        if actual > 0:
            self.damage_log.append((self.player.unit_id, actual, False, e.attack_style))
        if self.player.hp <= 0:
            self.game_over = True

    # ── Attack styles ─────────────────────────────────────────────────────────

    def _enemy_basic(self, e: ActionUnit, dt: float) -> None:
        if self._in_melee(e) and e.attack_timer <= 0:
            e.state        = "attack"
            e.attack_timer = e.attack_cd
            e.lunge_dx     = (self.player.x - e.x) * 0.4
            self.vfx_queue.append({"type": "enemy_slash", "src_id": e.unit_id,
                                   "x": e.x, "depth": e.depth})
            self._deal_to_player(e, kbx=-e.facing * 2.0)
        else:
            self._chase(e, dt)

    def _enemy_slam(self, e: ActionUnit, dt: float) -> None:
        """Slow, telegraphed wide slam: wide range, high damage, screen shake."""
        if self._in_melee(e, rx=e.attack_range * 1.5, rd=e.attack_depth * 1.3) \
                and e.attack_timer <= 0:
            e.state        = "attack"
            e.attack_timer = e.attack_cd
            e.lunge_dx     = (self.player.x - e.x) * 0.6
            self.vfx_queue.append({"type": "slam_wave", "src_id": e.unit_id,
                                   "x": e.x, "depth": e.depth})
            self.screen_shake = max(self.screen_shake, 0.18)
            self._deal_to_player(e, mult=1.6, kbx=-e.facing * 5.0, kbd=random.choice([-1.5, 1.5]))
        else:
            self._chase(e, dt)

    def _enemy_combo(self, e: ActionUnit, dt: float) -> None:
        """Two quick hits; second is queued via combo_left."""
        if e.combo_left > 0 and e.attack_timer <= 0:
            e.combo_left  -= 1
            e.attack_timer = 0.25
            e.lunge_dx     = (self.player.x - e.x) * 0.35
            self.vfx_queue.append({"type": "enemy_slash", "src_id": e.unit_id,
                                   "x": e.x, "depth": e.depth})
            if self._in_melee(e):
                self._deal_to_player(e, mult=0.75, kbx=-e.facing * 1.5)
            return

        if self._in_melee(e) and e.attack_timer <= 0:
            e.state        = "attack"
            e.attack_timer = e.attack_cd
            e.combo_left   = 1      # triggers second hit
            e.lunge_dx     = (self.player.x - e.x) * 0.35
            self.vfx_queue.append({"type": "enemy_slash", "src_id": e.unit_id,
                                   "x": e.x, "depth": e.depth})
            if self._in_melee(e):
                self._deal_to_player(e, mult=0.75, kbx=-e.facing * 1.5)
        else:
            self._chase(e, dt)

    def _enemy_ranged(self, e: ActionUnit, dt: float) -> None:
        """Fires a bolt from range; no need to be in melee."""
        p      = self.player
        dist_x = abs(e.x - p.x)
        dist_d = abs(e.depth - p.depth)
        in_sight = dist_x < 7.0 and dist_d < 1.5

        # Keep preferred distance — retreat if too close
        if dist_x < 2.0:
            e.state = "walk"
            e.x     += -e.facing * e.speed * dt
        elif in_sight and e.attack_timer <= 0:
            e.state        = "attack"
            e.attack_timer = e.attack_cd
            e.facing       = 1 if (p.x - e.x) > 0 else -1
            self.vfx_queue.append({"type": "ranged_bolt",
                                   "src_id": e.unit_id, "tgt_id": p.unit_id,
                                   "sx": e.x, "sd": e.depth,
                                   "tx": p.x, "td": p.depth})
            self._deal_to_player(e, mult=1.1)
        else:
            self._chase(e, dt, stop_dist=2.0)

    def _enemy_dive(self, e: ActionUnit, dt: float) -> None:
        """Bat-style: flies up then dives down on player."""
        p = self.player

        if e.state == "dive_rise":
            e.y  += 4.5 * dt
            e.vy  = 0.0
            if e.y >= 2.5:
                # align x with player before diving
                e.x    = p.x
                e.depth = p.depth
                e.state = "dive_fall"
            return

        if e.state == "dive_fall":
            e.y -= 9.0 * dt
            if e.y <= GROUND:
                e.y            = GROUND
                e.state        = "attack"
                e.attack_timer = e.attack_cd
                self.vfx_queue.append({"type": "slam_wave", "src_id": e.unit_id,
                                       "x": e.x, "depth": e.depth})
                self.screen_shake = max(self.screen_shake, 0.10)
                self._deal_to_player(e, mult=1.4, kbx=-e.facing * 3.0)
            return

        # Ground phase — same as basic but initiates dive
        if self._in_melee(e) and e.attack_timer <= 0:
            e.state = "dive_rise"
            e.attack_timer = e.attack_cd + 0.8   # full CD for next dive
        else:
            self._chase(e, dt)
