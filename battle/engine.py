from __future__ import annotations

import json
from enum import Enum, auto
from pathlib import Path
from typing import Callable

from battle.entities import BattleUnit
from skills.base import SkillContext, SkillResult
from skills.catalog import Skill, build_skills, skill_targets_enemy


class BattleState(Enum):
    TICKING = auto()
    PLAYER_COMMAND = auto()
    PLAYER_PICK_TARGET = auto()
    BUSY = auto()
    VICTORY = auto()
    DEFEAT = auto()


class RewardSummary(dict):
    pass


class BattleEngine:
    def __init__(
        self,
        config_path: Path | str,
        wave_index: int = 1,
        enemy_ids: list[str] | None = None,
        hero_override: dict | None = None,
    ) -> None:
        path = Path(config_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        self._raw = data
        self.wave_index = max(1, wave_index)
        atb = data["atb"]
        self.atb_max = float(atb["max"])
        self.fill_multiplier = float(atb["fill_multiplier"])
        self.tie_player_first = bool(data.get("tie_break_player_first", True))

        self.status_block = dict(data.get("status", {}))
        self.poison_tick_damage = int(self.status_block.get("poison_tick_damage", 8))
        self.bleed_tick_damage = int(self.status_block.get("bleed_tick_damage", 6))
        self.regen_tick_heal = int(self.status_block.get("regen_tick_heal", 4))
        self.slow_speed_multiplier = float(self.status_block.get("slow_speed_multiplier", 0.8))
        self.waves_block = dict(data.get("waves", {}))

        defs = data["skill_definitions"]
        self.skills: dict[str, Skill] = build_skills(defs)

        hero_entry = dict(data["party"][0])
        if hero_override:
            hero_entry.update(hero_override)
        self.hero = self._unit_from_entry(hero_entry, is_player=True)
        enemy_defs = {str(e["id"]): e for e in data["enemies"]}
        if enemy_ids:
            id_counts: dict[str, int] = {}
            for eid in enemy_ids:
                id_counts[eid] = id_counts.get(eid, 0) + 1
            seen: dict[str, int] = {}
            self.enemies = []
            for eid in enemy_ids:
                entry = enemy_defs.get(eid)
                if entry is None:
                    continue
                seen[eid] = seen.get(eid, 0) + 1
                overridden = dict(entry)
                if id_counts[eid] > 1:
                    overridden["id"] = f"{eid}_{seen[eid]}"
                    overridden["name"] = f"{entry['name']} {seen[eid]}"
                self.enemies.append(self._unit_from_entry(overridden, is_player=False, index=len(self.enemies)))
        else:
            self.enemies = [self._unit_from_entry(e, is_player=False, index=i) for i, e in enumerate(data["enemies"])]
        self._apply_wave_scaling()

        self.state = BattleState.TICKING
        self.pending_actor: BattleUnit | None = None
        self.pending_skill_id: str | None = None
        self.selected_target_idx = 0
        self.last_reward: RewardSummary | None = None

        self.on_log: Callable[[str], None] = lambda _line: None
        self.on_result: Callable[[BattleUnit, SkillResult], None] | None = None

    def _unit_from_entry(self, entry: dict, *, is_player: bool, index: int = 0) -> BattleUnit:
        skills = list(entry.get("skills", []))
        uid = str(entry["id"]) if "id" in entry else f"unit_{index}"
        unit = BattleUnit(
            unit_id=uid,
            name=str(entry["name"]),
            is_player=is_player,
            hp=int(entry["hp"]),
            max_hp=int(entry["hp"]),
            mp=int(entry["mp"]),
            max_mp=int(entry["mp"]),
            speed=float(entry["speed"]),
            skill_ids=skills,
        )
        rewards = entry.get("rewards", {})
        unit.exp_reward = int(rewards.get("exp", 0))
        unit.gold_reward = int(rewards.get("gold", 0))
        unit.loot_reward = list(rewards.get("loot", []))
        unit.attack_bonus = int(entry.get("attack_bonus", 0))
        return unit

    def _apply_wave_scaling(self) -> None:
        hp_scale = float(self.waves_block.get("hp_scale_per_wave", 0.15))
        reward_scale = float(self.waves_block.get("reward_scale_per_wave", 0.25))
        wave_mult_hp = 1.0 + hp_scale * (self.wave_index - 1)
        wave_mult_reward = 1.0 + reward_scale * (self.wave_index - 1)
        for e in self.enemies:
            e.max_hp = int(e.max_hp * wave_mult_hp)
            e.hp = e.max_hp
            e.exp_reward = int(e.exp_reward * wave_mult_reward)
            e.gold_reward = int(e.gold_reward * wave_mult_reward)

    def alive_enemies(self) -> list[BattleUnit]:
        return [u for u in self.enemies if u.alive]

    def alive_units(self) -> list[BattleUnit]:
        alive = []
        if self.hero.alive:
            alive.append(self.hero)
        alive.extend(self.alive_enemies())
        return alive

    def enemy_by_unit_id(self, unit_id: str) -> BattleUnit | None:
        for e in self.alive_enemies():
            if e.unit_id == unit_id:
                return e
        return None

    def _sort_ready(self, ready: list[BattleUnit]) -> list[BattleUnit]:
        def key(u: BattleUnit) -> tuple:
            sp = -u.speed
            tie = -int(u.is_player) if self.tie_player_first else int(u.is_player)
            prio = tuple(str(u.unit_id))
            return (sp, tie, prio)

        return sorted(ready, key=key)

    def _log_lines(self, lines: list[str]) -> None:
        for ln in lines:
            self.on_log(ln)

    def _check_end(self) -> bool:
        if len(self.alive_enemies()) == 0:
            if self.state != BattleState.VICTORY:
                self.state = BattleState.VICTORY
                self.last_reward = self._reward_summary()
                self.on_log("Victory!")
            return True
        if not self.hero.alive:
            if self.state != BattleState.DEFEAT:
                self.state = BattleState.DEFEAT
                self.on_log("Defeat...")
            return True
        return False

    def _turn_start(self, actor: BattleUnit) -> None:
        lines: list[str] = []
        if actor.has_effect("poison"):
            dmg = self.poison_tick_damage
            actor.damage(dmg)
            lines.append(f"{actor.name} suffers poison ({dmg}).")
        if actor.has_effect("bleed"):
            dmg = self.bleed_tick_damage
            actor.damage(dmg)
            lines.append(f"{actor.name} bleeds ({dmg}).")
        if actor.alive and actor.has_effect("regen"):
            h = actor.heal(self.regen_tick_heal)
            lines.append(f"{actor.name} regenerates (+{h}).")
        actor.tick_effects()
        if lines:
            self._log_lines(lines)
        self._check_end()

    def _tick_waiting_enemies(self, dt: float) -> None:
        for u in self.alive_enemies():
            self._tick_atb_single(u, dt)

    def update(self, dt: float) -> None:
        if self.state in (BattleState.VICTORY, BattleState.DEFEAT):
            return

        if self.state == BattleState.BUSY:
            return

        if self.state in (BattleState.PLAYER_COMMAND, BattleState.PLAYER_PICK_TARGET):
            self._tick_waiting_enemies(dt)
            return

        if self.state == BattleState.TICKING:
            for u in self.alive_units():
                self._tick_atb_single(u, dt)

        ready = [u for u in self.alive_units() if u.atb >= self.atb_max - 1e-6]
        if not ready:
            return

        ordered = self._sort_ready(ready)
        actor = ordered[0]

        self._turn_start(actor)
        if self.state in (BattleState.VICTORY, BattleState.DEFEAT):
            return

        actor.atb = self.atb_max
        self.pending_actor = actor

        if actor.is_player:
            self.pending_skill_id = None
            self.state = BattleState.PLAYER_COMMAND
            self.on_log("Hero ready — choose a command.")
            return

        self.state = BattleState.BUSY
        skill = self._pick_enemy_skill(actor)
        self.resolve_skill(actor, skill.skill_id, target=self.hero)

    def _tick_atb_single(self, unit: BattleUnit, dt: float) -> None:
        if not unit.alive:
            return
        if unit.atb >= self.atb_max:
            return
        speed_mult = self.slow_speed_multiplier if unit.has_effect("slow") else 1.0
        unit.atb = min(self.atb_max, unit.atb + unit.speed * speed_mult * self.fill_multiplier * dt)

    def _pick_enemy_skill(self, enemy: BattleUnit) -> Skill:
        best: Skill | None = None
        best_score = -999999
        defs = self._raw["skill_definitions"]
        for sid in enemy.skill_ids:
            sk = self.skills[sid]
            if not enemy.has_mp(sk.mp_cost):
                continue
            power = int(defs[sid].get("power", 0))
            kind = defs[sid].get("kind", "")
            score = power
            if self.hero.hp <= int(self.hero.max_hp * 0.35):
                score += 8
            if enemy.hp <= int(enemy.max_hp * 0.35) and sid == "defend":
                score += 30
            if enemy.mp <= 6 and sid == "wait":
                score += 22
            if kind == "bolt" and not self.hero.has_effect("slow"):
                score += 6
            if kind == "physical" and self.hero.has_effect("guard"):
                score -= 6
            if score > best_score:
                best_score = score
                best = sk
        if best is None:
            if "attack" in self.skills:
                return self.skills["attack"]
            return self.skills[next(iter(self.skills))]
        return best

    def _skill_context(self, skill_id: str) -> SkillContext:
        raw_skill = dict(self._raw["skill_definitions"][skill_id])
        raw_skill["_status_regen_duration_turns"] = int(self.status_block.get("regen_duration_turns", 0))
        raw_skill["_status_regen_tick_heal"] = int(self.status_block.get("regen_tick_heal", 0))
        return SkillContext(raw=raw_skill)

    def resolve_skill(self, actor: BattleUnit, skill_id: str, target: BattleUnit | None = None) -> None:
        if self.pending_actor is not actor:
            return

        defs = self._raw["skill_definitions"]
        sk = self.skills.get(skill_id)
        needs_enemy_target = actor.is_player and skill_targets_enemy(skill_id, defs)

        if sk is None:
            self.on_log(f"Unknown skill: {skill_id}")
            self._recover_from_failed_resolve(actor)
            return

        if not actor.has_mp(sk.mp_cost):
            self.on_log("Not enough MP.")
            self._recover_from_failed_resolve(actor)
            return

        tgt: BattleUnit
        if not actor.is_player:
            tgt = self.hero
        elif needs_enemy_target:
            if target is None or target.is_player or target not in self.enemies or not target.alive:
                self.on_log("Invalid enemy target.")
                self._recover_from_failed_resolve(actor)
                return
            tgt = target
        else:
            tgt = target if target is not None else self.hero

        if skill_id != "defend":
            actor.defending = False

        actor.drain_mp(sk.mp_cost)
        ctx = self._skill_context(skill_id)
        result = sk.apply(actor, tgt, ctx)

        self._log_lines(result.lines)
        if self.on_result:
            self.on_result(actor, result)

        actor.atb = 0.0
        self.pending_actor = None

        self.pending_skill_id = None

        if self._check_end():
            return

        self.state = BattleState.TICKING

    def _recover_from_failed_resolve(self, actor: BattleUnit) -> None:
        if actor.is_player:
            self.pending_skill_id = None
            self.state = BattleState.PLAYER_COMMAND
            self.pending_actor = actor
            actor.atb = self.atb_max
            return

        self.pending_actor = None
        self.state = BattleState.TICKING

    def player_try_skill(self, skill_id: str) -> None:
        if self.state != BattleState.PLAYER_COMMAND:
            return
        if self.pending_actor is not self.hero:
            return
        sk = self.skills.get(skill_id)
        if sk is None or skill_id not in self.hero.skill_ids:
            self.on_log("That command is unavailable.")
            return
        if not self.hero.has_mp(sk.mp_cost):
            self.on_log("Not enough MP.")
            return

        defs = self._raw["skill_definitions"]
        if skill_targets_enemy(skill_id, defs):
            foes = self.alive_enemies()
            if len(foes) == 0:
                return
            if len(foes) > 1:
                self.state = BattleState.PLAYER_PICK_TARGET
                self.pending_skill_id = skill_id
                self.selected_target_idx = 0
                self.on_log("Choose a target.")
                return

            self.state = BattleState.BUSY
            self.resolve_skill(self.hero, skill_id, target=foes[0])
            return

        self.state = BattleState.BUSY
        self.resolve_skill(self.hero, skill_id, target=self.hero)

    def player_confirm_target(self, enemy_unit_id: str) -> None:
        if self.state != BattleState.PLAYER_PICK_TARGET:
            return
        if self.pending_actor is not self.hero or self.pending_skill_id is None:
            return
        tgt = self.enemy_by_unit_id(enemy_unit_id)
        if tgt is None:
            self.on_log("Target unavailable.")
            return
        sid = self.pending_skill_id
        self.state = BattleState.BUSY
        self.resolve_skill(self.hero, sid, target=tgt)

    def cycle_target(self, delta: int) -> None:
        if self.state != BattleState.PLAYER_PICK_TARGET:
            return
        foes = self.alive_enemies()
        if not foes:
            return
        self.selected_target_idx = (self.selected_target_idx + delta) % len(foes)

    def selected_target(self) -> BattleUnit | None:
        foes = self.alive_enemies()
        if not foes:
            return None
        self.selected_target_idx = min(self.selected_target_idx, len(foes) - 1)
        return foes[self.selected_target_idx]

    def confirm_selected_target(self) -> None:
        tgt = self.selected_target()
        if tgt is None:
            return
        self.player_confirm_target(tgt.unit_id)

    def _reward_summary(self) -> RewardSummary:
        exp = sum(e.exp_reward for e in self.enemies)
        gold = sum(e.gold_reward for e in self.enemies)
        loot: list[str] = []
        for e in self.enemies:
            loot.extend(e.loot_reward)
        return RewardSummary(exp=exp, gold=gold, loot=loot, wave=self.wave_index)

    def player_cancel_target(self) -> None:
        if self.state != BattleState.PLAYER_PICK_TARGET:
            return
        self.pending_skill_id = None
        self.state = BattleState.PLAYER_COMMAND

    def skill_available(self, actor: BattleUnit, skill_id: str) -> bool:
        sk = self.skills.get(skill_id)
        if sk is None:
            return False
        return skill_id in actor.skill_ids and actor.has_mp(sk.mp_cost)
