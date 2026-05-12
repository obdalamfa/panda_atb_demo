from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from battle.entities import BattleUnit
from skills.base import SkillContext, SkillResult


@dataclass(frozen=True)
class Skill:
    skill_id: str
    name: str
    mp_cost: int
    apply: Callable[[BattleUnit, BattleUnit, SkillContext], SkillResult]


def _physical(actor: BattleUnit, target: BattleUnit, ctx: SkillContext, label: str) -> SkillResult:
    power = int(ctx.raw.get("power", 10))
    mult = 0.5 if target.defending or target.has_effect("guard") else 1.0
    dmg = max(1, int(power * mult))
    dealt = target.damage(dmg)
    bleed_turns = int(ctx.raw.get("bleed_turns", 0))
    lines = [f"{actor.name} — {label} for {dealt}."]
    if bleed_turns > 0 and target.alive:
        target.set_effect("bleed", bleed_turns)
        lines.append(f"{target.name} bleeds for {bleed_turns} turns.")
    return SkillResult(
        lines=lines,
        actor_anim="attack",
        target_anim="hit",
        fx="slash",
        fx_target_unit_id=target.unit_id,
    )


def _fire(actor: BattleUnit, target: BattleUnit, ctx: SkillContext) -> SkillResult:
    power = int(ctx.raw.get("power", 24))
    mult = 0.5 if target.defending or target.has_effect("guard") else 1.0
    dmg = max(1, int(power * mult))
    dealt = target.damage(dmg)
    return SkillResult(
        lines=[f"{actor.name} — Fire Bolt for {dealt}."],
        actor_anim="cast",
        target_anim="hit",
        fx="fire_bolt",
        fx_target_unit_id=target.unit_id,
    )


def _thunder(actor: BattleUnit, target: BattleUnit, ctx: SkillContext) -> SkillResult:
    power = int(ctx.raw.get("power", 22))
    mult = 0.5 if target.defending or target.has_effect("guard") else 1.0
    dmg = max(1, int(power * mult))
    dealt = target.damage(dmg)
    lines = [f"{actor.name} — Thunder for {dealt}."]
    poison_turns = int(ctx.raw.get("poison_turns", 0))
    if poison_turns > 0 and target.alive:
        target.set_effect("poison", poison_turns)
        lines.append(f"{target.name} is poisoned ({poison_turns} turns).")
    slow_turns = int(ctx.raw.get("slow_turns", 0))
    if slow_turns > 0 and target.alive:
        target.set_effect("slow", slow_turns)
        lines.append(f"{target.name} is slowed ({slow_turns} turns).")
    return SkillResult(
        lines=lines,
        actor_anim="cast",
        target_anim="hit",
        fx="thunder",
        fx_target_unit_id=target.unit_id,
    )


def _heal(actor: BattleUnit, target: BattleUnit, ctx: SkillContext) -> SkillResult:
    power = int(ctx.raw.get("power", 30))
    gained = actor.heal(power)
    lines = [f"{actor.name} — Heal restores {gained} HP."]

    default_regen = int(ctx.raw.get("_status_regen_duration_turns", 0))
    if "regen_turns" in ctx.raw:
        regen_turns = int(ctx.raw["regen_turns"])
    else:
        regen_turns = default_regen

    if regen_turns > 0:
        actor.set_effect("regen", regen_turns)
        tick = int(ctx.raw.get("_status_regen_tick_heal", 0))
        lines.append(f"Regeneration: {regen_turns} turn(s), +{tick} HP each turn start (see status.regen_* in battle.json).")

    return SkillResult(lines=lines, actor_anim="cast", target_anim="idle", fx="heal")


def _wait(actor: BattleUnit, target: BattleUnit, ctx: SkillContext) -> SkillResult:
    regen = int(ctx.raw.get("mp_regen_on_wait", 5))
    actor.mp = min(actor.max_mp, actor.mp + regen)
    return SkillResult(lines=[f"{actor.name} waits (+{regen} MP)."], actor_anim="idle", target_anim="idle", fx="wait")


def _defend(actor: BattleUnit, target: BattleUnit, ctx: SkillContext) -> SkillResult:
    actor.defending = True
    actor.set_effect("guard", 1)
    return SkillResult(
        lines=[f"{actor.name} defends — damage halved until next action."],
        actor_anim="defend",
        target_anim="idle",
        fx="guard",
    )


def _dispatch(sid: str, ctx: SkillContext) -> Callable[[BattleUnit, BattleUnit, SkillContext], SkillResult]:
    kind = ctx.raw.get("kind", "physical")

    def run(actor: BattleUnit, target: BattleUnit, c: SkillContext) -> SkillResult:
        if kind == "physical":
            label = "Attack" if sid == "attack" else "Slash" if sid == "slash" else "Strike"
            return _physical(actor, target, c, label)
        if kind == "fire":
            return _fire(actor, target, c)
        if kind == "bolt":
            return _thunder(actor, target, c)
        if kind == "heal":
            return _heal(actor, target, c)
        if kind == "wait":
            return _wait(actor, target, c)
        if kind == "defend":
            return _defend(actor, target, c)
        return _physical(actor, target, c, "Attack")

    return run


def build_skills(definitions: dict[str, dict]) -> dict[str, Skill]:
    out: dict[str, Skill] = {}
    for sid, raw in definitions.items():
        ctx = SkillContext(raw=dict(raw))
        mp_cost = int(raw.get("mp_cost", 0))
        display = sid.replace("_", " ").title()
        apply_fn = _dispatch(sid, ctx)
        out[sid] = Skill(skill_id=sid, name=display, mp_cost=mp_cost, apply=apply_fn)
    return out


def skill_targets_enemy(skill_id: str, definitions: dict[str, dict]) -> bool:
    info = definitions.get(skill_id)
    if not info:
        return False
    return info.get("kind") in ("physical", "fire", "bolt")
