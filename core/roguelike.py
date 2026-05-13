from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path

_BOSS_DEPTHS: dict[int, str] = {
    5:  "slime_king",
    10: "goblin_chief",
    15: "dark_knight",
    20: "ancient_golem",
}


@dataclass
class RunState:
    depth: int = 1
    _pool: dict = field(default_factory=dict, repr=False)

    def load(self, pool_path: Path) -> None:
        self._pool = json.loads(pool_path.read_text(encoding="utf-8"))

    def is_boss(self) -> bool:
        return self.depth in _BOSS_DEPTHS

    def get_zone(self) -> int:
        if self.depth <= 4:
            return 1
        if self.depth <= 9:
            return 2
        if self.depth <= 14:
            return 3
        return 4

    def get_enemy_ids(self) -> list[str]:
        if self.is_boss():
            return [_BOSS_DEPTHS[self.depth]]

        tiers = self._pool.get("tiers", [])
        candidates: list[str] = []
        for tier in tiers:
            mn = tier.get("min_depth", 1)
            mx = tier.get("max_depth")
            in_range = self.depth >= mn and (mx is None or self.depth <= mx)
            if in_range:
                candidates.extend(tier["ids"])

        if not candidates:
            candidates = ["blob_small"]

        count = min(3, max(1, (self.depth + 1) // 2))
        return [random.choice(candidates) for _ in range(count)]

    def advance(self) -> None:
        self.depth += 1
