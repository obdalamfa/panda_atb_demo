"""
Real-time 2.5D beat-em-up engine.
ActionUnit: position on XZ (left/right) and depth axis.
ActionEngine: physics, player input, enemy AI, hit detection.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

GRAVITY  = -24.0
GROUND   = 0.0
PLAY_W   = 9.0    # x range: -PLAY_W .. PLAY_W
PLAY_D   = 4.5    # depth range: 0 .. PLAY_D


@dataclass
class ActionUnit:
    unit_id: str
    name: str
    is_player: bool
    hp: int
    max_hp: int
    atk: int
    speed: float        = 4.0
    x: float            = 0.0
    depth: float        = 2.0
    y: float            = 0.0    # vertical height (0 = ground)
    vy: float           = 0.0
    facing: int         = 1      # 1=right, -1=left
    state: str          = "idle" # idle/walk/attack/hurt/dead
    hurt_timer: float   = 0.0
    attack_timer: float = 0.0
    attack_cd: float    = 0.55
    attack_range: float = 1.5
    attack_depth: float = 0.9    # depth tolerance for hit
    exp_reward: int     = 0
    gold_reward: int    = 0
    loot_reward: list[str] = field(default_factory=list)

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        if self.hurt_timer > 0 or self.state == "dead":
            return 0
        actual = max(1, amount)
        self.hp = max(0, self.hp - actual)
        self.state = "dead" if self.hp <= 0 else "hurt"
        if self.state == "hurt":
            self.hurt_timer = 0.50
        return actual


class ActionEngine:
    def __init__(
        self,
        player_data: dict,
        enemies_data: list[dict],
        wave: int = 1,
    ) -> None:
        self.wave = wave
        scale = 1.0 + (wave - 1) * 0.07

        p = player_data
        self.player = ActionUnit(
            unit_id="hero",
            name=p.get("name", "Hero"),
            is_player=True,
            hp=p.get("hp", 100),
            max_hp=p.get("hp", 100),
            atk=p.get("atk", 20),
            speed=p.get("speed", 4.8),
            x=-5.5,
            depth=2.2,
            facing=1,
        )

        self.enemies: list[ActionUnit] = []
        n = len(enemies_data)
        for i, ed in enumerate(enemies_data):
            col = i % 3
            row = i // 3
            ex = 4.5 + col * 2.5
            edepth = 1.2 + row * 1.5
            hp_s = int(ed.get("hp", 40) * scale)
            self.enemies.append(ActionUnit(
                unit_id=ed.get("unit_id", f"enemy_{i}"),
                name=ed.get("name", "Enemy"),
                is_player=False,
                hp=hp_s,
                max_hp=hp_s,
                atk=int(ed.get("atk", 10) * scale),
                speed=ed.get("speed", 2.0),
                x=ex,
                depth=edepth,
                facing=-1,
                attack_cd=ed.get("attack_cd", 1.5),
                attack_range=ed.get("attack_range", 1.3),
                exp_reward=ed.get("exp", 20),
                gold_reward=ed.get("gold", 10),
                loot_reward=ed.get("loot", []),
            ))

        self.cleared   = False
        self.game_over = False

        self._attack_queued = False
        self.combo_count    = 0
        self.combo_timer    = 0.0

        # (unit_id, amount, is_heal) — consumed each frame by arena
        self.damage_log: list[tuple[str, int, bool]] = []

    # ── Public interface ──────────────────────────────────────────────────────

    def queue_attack(self) -> None:
        self._attack_queued = True

    def alive_enemies(self) -> list[ActionUnit]:
        return [e for e in self.enemies if e.alive]

    def update(self, dt: float, keys: dict) -> None:
        if self.cleared or self.game_over:
            return
        self._move_player(dt, keys)
        self._player_attack(dt)
        for enemy in self.enemies:
            if enemy.alive:
                self._enemy_ai(enemy, dt)
        if not self.alive_enemies():
            self.cleared = True
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo_count = 0

    # ── Player movement ───────────────────────────────────────────────────────

    def _move_player(self, dt: float, keys: dict) -> None:
        p = self.player

        # gravity always applied
        p.vy += GRAVITY * dt
        p.y = max(GROUND, p.y + p.vy * dt)
        if p.y <= GROUND:
            p.y = GROUND
            p.vy = 0.0

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

        # jump (edge-triggered by caller setting keys["space_pressed"])
        if p.y <= GROUND and keys.get("space_pressed"):
            p.vy = 10.0
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

        if self._attack_queued and p.attack_timer <= 0 and p.state not in ("hurt", "dead"):
            self._attack_queued = False
            p.state = "attack"
            p.attack_timer = p.attack_cd
            hit_any = False
            for enemy in self.alive_enemies():
                if (
                    abs(enemy.x - p.x)         < p.attack_range
                    and abs(enemy.depth - p.depth) < p.attack_depth
                ):
                    dmg    = p.atk + random.randint(-2, 5)
                    actual = enemy.take_damage(dmg)
                    if actual > 0:
                        self.damage_log.append((enemy.unit_id, actual, False))
                        self.combo_count += 1
                        self.combo_timer  = 2.5
                        hit_any = True
        else:
            self._attack_queued = False

    # ── Enemy AI ──────────────────────────────────────────────────────────────

    def _enemy_ai(self, e: ActionUnit, dt: float) -> None:
        p = self.player

        if e.hurt_timer > 0:
            e.hurt_timer -= dt
            if e.hurt_timer <= 0 and e.state == "hurt":
                e.state = "idle"
            return

        if e.attack_timer > 0:
            e.attack_timer -= dt

        dx     = p.x     - e.x
        ddepth = p.depth  - e.depth
        dist_x = abs(dx)
        dist_d = abs(ddepth)

        in_range = dist_x < e.attack_range and dist_d < e.attack_depth

        if in_range and e.attack_timer <= 0 and p.state != "dead":
            e.state        = "attack"
            e.attack_timer = e.attack_cd
            dmg    = e.atk + random.randint(-1, 3)
            actual = p.take_damage(dmg)
            if actual > 0:
                self.damage_log.append((p.unit_id, actual, False))
            if p.hp <= 0:
                self.game_over = True
        else:
            dist = (dx * dx + ddepth * ddepth) ** 0.5
            if dist > 0.15:
                e.state  = "walk"
                nx       = dx     / dist
                nd       = ddepth / dist
                e.x     += nx * e.speed * dt
                e.depth += nd * e.speed * 0.55 * dt
                e.facing = 1 if dx > 0 else -1
            else:
                e.state = "idle"
