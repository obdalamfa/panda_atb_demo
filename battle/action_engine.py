"""
Real-time 2.5D beat-em-up engine with Tekken-style combo input system.

4 attack buttons: LP (J/F), RP (K), LK (U), RK (I).
Input chain accumulates timed button presses; best matching combo executes.
Longer combos always win. Chain resets on timeout, hurt, or dead.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from battle.combo_catalog import (
    LP, RP, LK, RK,
    BASE_CD, BASE_DMG, BASE_RANGE,
    ComboMove, best_match, is_valid_prefix,
)

GRAVITY      = -24.0
GROUND       =   0.0
PLAY_W       =   9.0
PLAY_D       =   4.5
CHAIN_WINDOW =  0.42   # seconds between inputs before chain resets
LINK_GRACE   =  0.10   # seconds before recovery end where next input is buffered

# ── Enemy attack styles ───────────────────────────────────────────────────────
ES_BASIC  = "basic"
ES_SLAM   = "slam"
ES_COMBO  = "combo"
ES_RANGED = "ranged"
ES_DIVE   = "dive"


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
    y:            float = 0.0
    vy:           float = 0.0
    facing:       int   = 1
    state:        str   = "idle"

    hurt_timer:   float = 0.0
    attack_timer: float = 0.0
    attack_cd:    float = 0.55
    attack_range: float = 1.5
    attack_depth: float = 0.9

    attack_style: str = ES_BASIC
    combo_left:   int = 0

    lunge_dx: float = 0.0
    lunge_dd: float = 0.0

    kbv_x: float = 0.0
    kbv_d: float = 0.0

    anim_t: float = 0.0

    exp_reward:  int       = 0
    gold_reward: int       = 0
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

        # ── Combo input system ────────────────────────────────────────────────
        self._chain:       list[str] = []   # buttons pressed in current chain
        self._chain_timer: float     = 0.0  # time until chain resets
        self._next_btn:    str | None = None  # buffered during recovery

        # ── Combo feedback ────────────────────────────────────────────────────
        self.combo_count     = 0
        self.combo_timer     = 0.0
        self.last_combo_name = ""
        self.last_combo_tier = 0   # 1-4, drives HUD color
        self.combo_name_timer = 0.0

        self.screen_shake = 0.0

        # (target_id, amount, is_heal, fx_type)
        self.damage_log: list[tuple[str, int, bool, str]] = []
        # VFX events for arena
        self.vfx_queue:  list[dict] = []

    # ── Public input interface ────────────────────────────────────────────────

    def queue_input(self, btn: str) -> None:
        """Called by main.py when J/K/U/I is pressed."""
        p = self.player
        if p.state in ("hurt", "dead") or self.cleared or self.game_over:
            return

        if p.state == "attack":
            # buffer exactly one next input during recovery
            self._next_btn = btn
        else:
            self._push_chain(btn)
            self._try_execute()

    def alive_enemies(self) -> list[ActionUnit]:
        return [e for e in self.enemies if e.alive]

    # ── Main update ───────────────────────────────────────────────────────────

    def update(self, dt: float, keys: dict) -> None:
        if self.cleared or self.game_over:
            return
        self._tick_anim(dt)
        self._move_player(dt, keys)
        self._tick_chain(dt)
        for enemy in self.enemies:
            if enemy.alive:
                self._enemy_update(enemy, dt)
        if not self.alive_enemies():
            self.cleared = True
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo_count = 0
        if self.combo_name_timer > 0:
            self.combo_name_timer -= dt
        if self.screen_shake > 0:
            self.screen_shake = max(0.0, self.screen_shake - dt * 3.0)

    # ── Combo chain management ────────────────────────────────────────────────

    def _push_chain(self, btn: str) -> None:
        """Add btn to chain, keep max last 4."""
        self._chain.append(btn)
        if len(self._chain) > 4:
            self._chain = self._chain[-4:]
        self._chain_timer = CHAIN_WINDOW

    def _tick_chain(self, dt: float) -> None:
        p = self.player

        # Window countdown — chain resets on timeout
        if self._chain_timer > 0:
            self._chain_timer -= dt
            if self._chain_timer <= 0:
                self._chain.clear()

        # When recovery ends, pick up buffered next input
        if p.state == "attack" and p.attack_timer > 0:
            p.attack_timer -= dt
            if p.attack_timer <= 0:
                p.state = "idle"
                if self._next_btn is not None:
                    btn = self._next_btn
                    self._next_btn = None
                    self._push_chain(btn)
                    self._try_execute()
        elif p.state == "attack":
            p.state = "idle"

    def _try_execute(self) -> None:
        """Find best combo for current chain and execute if possible."""
        p = self.player
        if p.state in ("attack", "hurt", "dead"):
            return
        combo = best_match(self._chain)
        if combo:
            self._do_combo(combo)
        # If no match (shouldn't happen since single buttons always match), do nothing

    # ── Combo execution ───────────────────────────────────────────────────────

    def _do_combo(self, combo: ComboMove) -> None:
        p = self.player
        p.state        = "attack"
        p.attack_timer = combo.cd

        # Lunge — bigger for longer combos
        lunge = 0.7 + combo.tier * 0.25
        p.lunge_dx = p.facing * lunge

        # Base damage from the last button in combo
        last_btn     = combo.inputs[-1]
        hit_range    = BASE_RANGE[last_btn] * combo.range_mult
        hit_depth    = 0.95

        # Update combo feedback
        self.last_combo_name  = combo.name
        self.last_combo_tier  = combo.tier
        self.combo_name_timer = 1.8

        # VFX
        self.vfx_queue.append({
            "type": combo.fx, "src_id": p.unit_id,
            "x": p.x + p.facing * hit_range * 0.6, "depth": p.depth,
            "tier": combo.tier,
        })

        if combo.tier >= 3 or combo.fx in ("heavy", "jump_slam"):
            self.screen_shake = max(self.screen_shake, 0.10 + combo.tier * 0.06)

        hit_any = False
        for enemy in self.alive_enemies():
            if abs(enemy.x - p.x) < hit_range and abs(enemy.depth - p.depth) < hit_depth:
                dmg    = int(p.atk * combo.dmg) + random.randint(0, max(1, combo.tier * 2))
                kbx    = p.facing * (2.5 + combo.tier * 1.2)
                kbd    = random.choice([-0.8, 0.8]) * combo.tier * 0.4
                actual = enemy.take_damage(dmg, kbx=kbx, kbd=kbd)
                if actual > 0:
                    self.damage_log.append((enemy.unit_id, actual, False, combo.fx))
                    self.combo_count += 1
                    self.combo_timer  = 2.5
                    hit_any = True

                    if combo.launch and enemy.alive:
                        enemy.vy    = 13.0
                        enemy.y    += 0.3
                        enemy.state = "hurt"
                        enemy.hurt_timer = 0.80
                        self.vfx_queue.append({
                            "type": "launch", "src_id": p.unit_id, "tgt_id": enemy.unit_id,
                            "x": enemy.x, "depth": enemy.depth,
                        })

                    if combo.knockdown and enemy.alive:
                        enemy.kbv_x = p.facing * 6.0
                        enemy.kbv_d = random.choice([-1.5, 1.5])

    # ── Animation clock ───────────────────────────────────────────────────────

    def _tick_anim(self, dt: float) -> None:
        self.player.anim_t += dt
        for e in self.enemies:
            e.anim_t += dt

    # ── Physics helpers ───────────────────────────────────────────────────────

    def _apply_knockback(self, u: ActionUnit, dt: float) -> None:
        if u.kbv_x or u.kbv_d:
            u.x     = max(-PLAY_W, min(PLAY_W, u.x     + u.kbv_x * dt))
            u.depth = max(0.0,     min(PLAY_D,  u.depth + u.kbv_d * dt))
            decay   = max(0.0, 1.0 - dt * 6.0)
            u.kbv_x *= decay
            u.kbv_d *= decay

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
            p.y = GROUND; p.vy = 0.0

        self._apply_knockback(p, dt)
        self._decay_lunge(p, dt)

        if p.state == "hurt":
            p.hurt_timer -= dt
            if p.hurt_timer <= 0:
                p.state = "idle"
            return
        if p.state in ("dead", "attack"):
            return

        dx     = (1.0 if keys.get("d") or keys.get("arrow_right") else 0.0) \
                - (1.0 if keys.get("a") or keys.get("arrow_left")  else 0.0)
        ddepth = (1.0 if keys.get("w") or keys.get("arrow_up")    else 0.0) \
                - (1.0 if keys.get("s") or keys.get("arrow_down")  else 0.0)

        if dx:
            p.facing = int(dx)
        if dx and ddepth:
            dx *= 0.707; ddepth *= 0.707

        p.x     = max(-PLAY_W, min(PLAY_W, p.x     + dx     * p.speed * dt))
        p.depth = max(0.0,     min(PLAY_D,  p.depth + ddepth * p.speed * 0.55 * dt))

        if p.y <= GROUND and keys.get("space_pressed"):
            p.vy = 10.5
            keys["space_pressed"] = False

        p.state = "walk" if (dx or ddepth) else "idle"

    # ── Enemy update dispatcher ───────────────────────────────────────────────

    def _enemy_update(self, e: ActionUnit, dt: float) -> None:
        self._decay_lunge(e, dt)
        self._apply_knockback(e, dt)

        # Apply gravity (enemies can be launched)
        if e.y > GROUND or e.vy != 0:
            e.vy += GRAVITY * dt
            e.y   = max(GROUND, e.y + e.vy * dt)
            if e.y <= GROUND:
                e.y = GROUND; e.vy = 0.0

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

    # ── Movement helpers ──────────────────────────────────────────────────────

    def _chase(self, e: ActionUnit, dt: float, stop: float = 0.15) -> None:
        p  = self.player
        dx = p.x - e.x; dd = p.depth - e.depth
        dist = (dx*dx + dd*dd)**0.5
        if dist > stop:
            e.state = "walk"
            e.x     += (dx/dist) * e.speed * dt
            e.depth += (dd/dist) * e.speed * 0.55 * dt
            e.facing = 1 if dx > 0 else -1
        else:
            e.state = "idle"

    def _in_melee(self, e: ActionUnit, rx: float | None = None, rd: float | None = None) -> bool:
        p = self.player
        return (abs(e.x - p.x) < (rx or e.attack_range)
                and abs(e.depth - p.depth) < (rd or e.attack_depth))

    def _deal(self, e: ActionUnit, mult: float = 1.0,
              kbx: float = 0.0, kbd: float = 0.0, fx: str = "enemy_slash") -> None:
        if self.player.state == "dead":
            return
        dmg    = int(e.atk * mult) + random.randint(-1, 3)
        actual = self.player.take_damage(dmg, kbx=kbx, kbd=kbd)
        if actual > 0:
            self.damage_log.append((self.player.unit_id, actual, False, fx))
        if self.player.hp <= 0:
            self.game_over = True

    # ── Enemy attack styles ───────────────────────────────────────────────────

    def _enemy_basic(self, e: ActionUnit, dt: float) -> None:
        if self._in_melee(e) and e.attack_timer <= 0:
            e.state = "attack"; e.attack_timer = e.attack_cd
            e.lunge_dx = (self.player.x - e.x) * 0.4
            self.vfx_queue.append({"type":"enemy_slash","src_id":e.unit_id,"x":e.x,"depth":e.depth})
            self._deal(e, kbx=-e.facing*2.0)
        else:
            self._chase(e, dt)

    def _enemy_slam(self, e: ActionUnit, dt: float) -> None:
        if self._in_melee(e, e.attack_range*1.5, e.attack_depth*1.3) and e.attack_timer <= 0:
            e.state = "attack"; e.attack_timer = e.attack_cd
            e.lunge_dx = (self.player.x - e.x) * 0.6
            self.vfx_queue.append({"type":"slam_wave","src_id":e.unit_id,"x":e.x,"depth":e.depth})
            self.screen_shake = max(self.screen_shake, 0.18)
            self._deal(e, 1.6, kbx=-e.facing*5.0, kbd=random.choice([-1.5,1.5]), fx="slam_wave")
        else:
            self._chase(e, dt)

    def _enemy_combo(self, e: ActionUnit, dt: float) -> None:
        if e.combo_left > 0 and e.attack_timer <= 0:
            e.combo_left -= 1; e.attack_timer = 0.25
            e.lunge_dx = (self.player.x - e.x) * 0.35
            self.vfx_queue.append({"type":"enemy_slash","src_id":e.unit_id,"x":e.x,"depth":e.depth})
            if self._in_melee(e):
                self._deal(e, 0.75, kbx=-e.facing*1.5)
            return
        if self._in_melee(e) and e.attack_timer <= 0:
            e.state = "attack"; e.attack_timer = e.attack_cd
            e.combo_left = 1
            e.lunge_dx = (self.player.x - e.x) * 0.35
            self.vfx_queue.append({"type":"enemy_slash","src_id":e.unit_id,"x":e.x,"depth":e.depth})
            if self._in_melee(e):
                self._deal(e, 0.75, kbx=-e.facing*1.5)
        else:
            self._chase(e, dt)

    def _enemy_ranged(self, e: ActionUnit, dt: float) -> None:
        p = self.player
        dist_x = abs(e.x - p.x)
        if dist_x < 2.0:
            e.state = "walk"; e.x += -e.facing * e.speed * dt
        elif abs(e.depth - p.depth) < 1.5 and e.attack_timer <= 0:
            e.state = "attack"; e.attack_timer = e.attack_cd
            e.facing = 1 if (p.x - e.x) > 0 else -1
            self.vfx_queue.append({"type":"ranged_bolt","src_id":e.unit_id,"tgt_id":p.unit_id,
                                   "sx":e.x,"sd":e.depth,"tx":p.x,"td":p.depth})
            self._deal(e, 1.1, fx="ranged_bolt")
        else:
            self._chase(e, dt, stop=2.0)

    def _enemy_dive(self, e: ActionUnit, dt: float) -> None:
        p = self.player
        if e.state == "dive_rise":
            e.y += 4.5*dt
            if e.y >= 2.5:
                e.x = p.x; e.depth = p.depth
                e.state = "dive_fall"
            return
        if e.state == "dive_fall":
            e.y -= 9.0*dt
            if e.y <= GROUND:
                e.y = GROUND; e.state = "attack"
                e.attack_timer = e.attack_cd
                self.vfx_queue.append({"type":"slam_wave","src_id":e.unit_id,"x":e.x,"depth":e.depth})
                self.screen_shake = max(self.screen_shake, 0.10)
                self._deal(e, 1.4, kbx=-e.facing*3.0, fx="slam_wave")
            return
        if self._in_melee(e) and e.attack_timer <= 0:
            e.state = "dive_rise"; e.attack_timer = e.attack_cd + 0.8
        else:
            self._chase(e, dt)
