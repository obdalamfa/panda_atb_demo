from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class PlayerProfile:
    name: str = "Hero"
    level: int = 1
    exp: int = 0
    gold: int = 0
    chapter: int = 1
    encounter_index: int = 0
    max_hp_bonus: int = 0
    max_mp_bonus: int = 0
    speed_bonus: float = 0.0
    attack_bonus: int = 0
    inventory: dict[str, int] = field(default_factory=lambda: {"potion": 2})

    def exp_to_next(self) -> int:
        return 70 + (self.level - 1) * 30

    def gain_exp(self, amount: int) -> list[str]:
        self.exp += max(0, amount)
        lines: list[str] = []
        while self.exp >= self.exp_to_next():
            self.exp -= self.exp_to_next()
            self.level += 1
            self.max_hp_bonus += 8
            self.max_mp_bonus += 3
            self.speed_bonus += 0.02
            self.attack_bonus += 1
            lines.append(f"Level Up! Lv {self.level}")
        return lines

    def gain_gold(self, amount: int) -> None:
        self.gold += max(0, amount)

    def can_pay(self, amount: int) -> bool:
        return self.gold >= amount

    def pay(self, amount: int) -> bool:
        if not self.can_pay(amount):
            return False
        self.gold -= amount
        return True

    def add_item(self, item_id: str, amount: int = 1) -> None:
        self.inventory[item_id] = self.inventory.get(item_id, 0) + max(0, amount)

    def consume_item(self, item_id: str, amount: int = 1) -> bool:
        if self.inventory.get(item_id, 0) < amount:
            return False
        self.inventory[item_id] -= amount
        if self.inventory[item_id] <= 0:
            del self.inventory[item_id]
        return True

    def hero_override(self) -> dict:
        return {
            "name": self.name,
            "hp": 140 + self.max_hp_bonus,
            "mp": 65 + self.max_mp_bonus,
            "speed": 1.2 + self.speed_bonus,
        }

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(raw: dict) -> PlayerProfile:
        p = PlayerProfile()
        for k in p.to_dict().keys():
            if k in raw:
                setattr(p, k, raw[k])
        return p
