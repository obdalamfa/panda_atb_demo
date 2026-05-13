from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SkillResult:
    lines: list[str]
    actor_anim: str = "idle"
    target_anim: str = "hit"
    fx: str = "none"
    fx_target_unit_id: str | None = None
    damage_dealt: int = 0
    heal_dealt: int = 0


@dataclass
class SkillContext:
    raw: dict[str, Any]
