"""
Tekken-style combo catalog.
4 base inputs: LP (J), RP (K), LK (U), RK (I).
Combos are matched against the tail of the input chain — longest wins.
"""
from __future__ import annotations

from dataclasses import dataclass

LP = "LP"   # Left  Punch  — J / F
RP = "RP"   # Right Punch  — K
LK = "LK"   # Left  Kick   — U
RK = "RK"   # Right Kick   — I

# Base attack properties per button
BASE_CD: dict[str, float] = {LP: 0.32, RP: 0.44, LK: 0.40, RK: 0.58}
BASE_DMG: dict[str, float] = {LP: 1.0,  RP: 1.3,  LK: 1.1,  RK: 1.8}
BASE_RANGE: dict[str, float] = {LP: 1.4, RP: 1.5,  LK: 1.6,  RK: 2.0}


@dataclass(frozen=True)
class ComboMove:
    name:       str
    inputs:     tuple[str, ...]
    dmg:        float        # multiplier on player base atk
    fx:         str = "slash"    # vfx type sent to arena
    knockdown:  bool = False     # big horizontal knockback
    launch:     bool = False     # sends enemy airborne
    range_mult: float = 1.0      # multiplies the last-button range

    @property
    def tier(self) -> int:
        return len(self.inputs)

    @property
    def cd(self) -> float:
        """Total recovery time based on chain length."""
        return sum(BASE_CD[btn] for btn in self.inputs) * 0.75


# ── Combo table (longest first for greedy matching) ───────────────────────────

COMBOS: list[ComboMove] = [
    # ═══════ 4-hit ══════════════════════════════════════════════════════════
    ComboMove("HELL SWEEP",      (LP, LP, RP, RK), dmg=5.0, fx="heavy",     knockdown=True),
    ComboMove("LIGHTNING RUSH",  (LP, RP, LK, RK), dmg=5.5, fx="jump_slam", launch=True),
    ComboMove("TWIN FANGS",      (RP, LP, RP, LK), dmg=4.8, fx="heavy",     launch=True),
    ComboMove("ROLLING THUNDER", (LK, LK, RK, RP), dmg=5.2, fx="jump_slam", knockdown=True),
    ComboMove("JAB STORM",       (LP, LP, LP, LP), dmg=4.2, fx="slash"),
    ComboMove("KICK FRENZY",     (LK, RK, LK, RK), dmg=4.6, fx="heavy"),
    ComboMove("CROSS BREAKER",   (RP, RP, LP, RK), dmg=4.9, fx="jump_slam", knockdown=True),
    ComboMove("SPIRAL ASSAULT",  (LP, LK, RP, RK), dmg=5.1, fx="heavy",     launch=True),

    # ═══════ 3-hit ══════════════════════════════════════════════════════════
    ComboMove("1-2 CROSS",       (LP, LP, RP),      dmg=2.8, fx="slash"),
    ComboMove("JAB ROUNDHOUSE",  (LP, LP, RK),      dmg=3.2, fx="heavy"),
    ComboMove("LOW SWEEP",       (LP, LP, LK),      dmg=2.6, fx="slash",     knockdown=True),
    ComboMove("ASSAULT",         (LP, RP, RK),      dmg=3.5, fx="heavy"),
    ComboMove("JAB LOW HIGH",    (LP, LK, RK),      dmg=3.2, fx="heavy"),
    ComboMove("POWER SURGE",     (RP, RP, RK),      dmg=3.8, fx="heavy",     knockdown=True),
    ComboMove("DOUBLE CROSS",    (RP, LP, RP),      dmg=2.9, fx="slash"),
    ComboMove("TRIPLE KICK",     (LK, LK, RK),      dmg=3.0, fx="slash"),
    ComboMove("HURRICANE",       (RK, LK, RP),      dmg=3.6, fx="jump_slam"),
    ComboMove("GATLING COMBO",   (RP, LK, RK),      dmg=3.4, fx="heavy"),

    # ═══════ 2-hit ══════════════════════════════════════════════════════════
    ComboMove("1-2",             (LP, LP),           dmg=1.6, fx="slash"),
    ComboMove("JAB CROSS",       (LP, RP),           dmg=1.9, fx="slash"),
    ComboMove("JAB ROUND",       (LP, RK),           dmg=2.3, fx="heavy"),
    ComboMove("JAB KICK",        (LP, LK),           dmg=1.8, fx="slash"),
    ComboMove("DOUBLE CROSS",    (RP, RP),           dmg=2.0, fx="slash"),
    ComboMove("CROSS KICK",      (RP, LK),           dmg=2.0, fx="slash"),
    ComboMove("CROSS ROUND",     (RP, RK),           dmg=2.5, fx="heavy"),
    ComboMove("LOW HIGH",        (LK, RK),           dmg=2.2, fx="slash"),
    ComboMove("DOUBLE LOW",      (LK, LK),           dmg=1.7, fx="slash"),
    ComboMove("ROUND JAB",       (RK, LP),           dmg=2.1, fx="slash"),
    ComboMove("ROUND KICK",      (RK, LK),           dmg=2.4, fx="heavy"),

    # ═══════ 1-hit (base) ═══════════════════════════════════════════════════
    ComboMove("JAB",             (LP,),              dmg=1.0, fx="light"),
    ComboMove("CROSS",           (RP,),              dmg=1.3, fx="light"),
    ComboMove("LOW KICK",        (LK,),              dmg=1.1, fx="light"),
    ComboMove("ROUNDHOUSE",      (RK,),              dmg=1.8, fx="heavy",  range_mult=1.25),
]

# Pre-sorted longest-first for greedy matching
SORTED_COMBOS: tuple[ComboMove, ...] = tuple(
    sorted(COMBOS, key=lambda c: (-len(c.inputs), c.inputs))
)

# Quick lookup: all valid combo-input prefixes (for "still possible" check)
_ALL_PREFIXES: frozenset[tuple[str, ...]] = frozenset(
    combo.inputs[:i]
    for combo in COMBOS
    for i in range(1, len(combo.inputs) + 1)
)


def is_valid_prefix(chain: list[str]) -> bool:
    """Return True if `chain` is a prefix of any known combo."""
    return tuple(chain) in _ALL_PREFIXES


def best_match(chain: list[str]) -> ComboMove | None:
    """Return longest combo matching the tail of `chain`, or None."""
    t = tuple(chain)
    for combo in SORTED_COMBOS:
        clen = len(combo.inputs)
        if len(t) >= clen and t[-clen:] == combo.inputs:
            return combo
    return None
