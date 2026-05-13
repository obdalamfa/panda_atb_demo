from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BattleUnit:
    unit_id: str
    name: str
    is_player: bool
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    speed: float
    atb: float = 0.0
    skill_ids: list[str] = field(default_factory=list)
    defending: bool = False
    effects: dict[str, int] = field(default_factory=dict)
    exp_reward: int = 0
    gold_reward: int = 0
    loot_reward: list[str] = field(default_factory=list)
    attack_bonus: int = 0

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def has_mp(self, cost: int) -> bool:
        return self.mp >= cost

    def drain_mp(self, cost: int) -> None:
        self.mp = max(0, self.mp - cost)

    def heal(self, amount: int) -> int:
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    def damage(self, amount: int) -> int:
        before = self.hp
        self.hp = max(0, self.hp - amount)
        return before - self.hp

    def set_effect(self, effect_id: str, turns: int) -> None:
        if turns <= 0:
            return
        self.effects[effect_id] = max(self.effects.get(effect_id, 0), turns)

    def has_effect(self, effect_id: str) -> bool:
        return self.effects.get(effect_id, 0) > 0

    def tick_effects(self) -> None:
        expired: list[str] = []
        for k in list(self.effects.keys()):
            self.effects[k] -= 1
            if self.effects[k] <= 0:
                expired.append(k)
        for k in expired:
            del self.effects[k]
