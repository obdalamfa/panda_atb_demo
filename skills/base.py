from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SkillResult:
    lines: list[str]
    actor_anim: str = "idle"
    target_anim: str = "hit"
    fx: str = "none"
    # If set, arena/VFX snap to this defender (offensive skills).
    fx_target_unit_id: str | None = None


@dataclass
class SkillContext:
    raw: dict
