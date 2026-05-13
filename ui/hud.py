"""Action-game HUD — HP bar, wave info, Tekken-style combo banner, log."""
from __future__ import annotations

from direct.gui.DirectGui import DirectFrame
from direct.showbase.ShowBase import ShowBase
from panda3d.core import LColor, TextNode

# Combo name color by tier (1-hit → 4-hit)
_TIER_COLOR: dict[int, tuple] = {
    1: (0.85, 0.85, 0.85, 1.0),   # gray
    2: (1.00, 1.00, 0.50, 1.0),   # yellow
    3: (1.00, 0.60, 0.10, 1.0),   # orange
    4: (1.00, 0.20, 0.90, 1.0),   # magenta/pink (ultimate)
}


class ActionHud:
    def __init__(self, base: ShowBase, engine) -> None:
        self.base   = base
        self.engine = engine
        self.log_lines: list[str] = []

        self.root = base.aspect2d.attachNewNode("hud_root")

        # ── Player HP bar (bottom-left) ────────────────────────────────────
        self._hp_bg = DirectFrame(
            frameSize=(0.0, 1.65, 0.0, 0.082),
            frameColor=(0.05, 0.05, 0.10, 0.88),
            pos=(-1.38, 0, -0.90),
            parent=base.aspect2d,
        )
        self._hp_fill = DirectFrame(
            frameSize=(0.0, 1.65, 0.0, 0.065),
            frameColor=(0.18, 0.84, 0.38, 1.0),
            pos=(-1.38, 0, -0.893),
            parent=base.aspect2d,
        )
        self._hp_text = self._lbl("HP", (-1.34, 0, -0.855), 0.048, (0.96, 0.96, 0.96, 1))

        # ── Wave / enemy count (top-left) ──────────────────────────────────
        self._wave_lbl = self._lbl("", (-1.38, 0, 0.90), 0.052, (1.0, 0.88, 0.30, 1))

        # ── Combat log (upper-left) ────────────────────────────────────────
        self._log_lbl = self._lbl("", (-1.38, 0, 0.60), 0.034, (0.88, 0.88, 0.92, 1))

        # ── Combo hit counter (upper-center-left) ──────────────────────────
        self._combo_count_lbl = self._lbl("", (-0.30, 0, 0.74), 0.076, (1.0, 0.72, 0.12, 1))
        self._combo_count_lbl.hide()

        # ── Combo name banner (below counter) ─────────────────────────────
        self._combo_name_lbl = self._lbl("", (-0.30, 0, 0.58), 0.052, (1.0, 1.0, 1.0, 1))
        self._combo_name_lbl.hide()

        # ── Input display (shows last chain, bottom-center) ────────────────
        self._input_lbl = self._lbl("", (-0.30, 0, -0.96), 0.036, (0.72, 0.90, 1.0, 1))

        # ── Controls hint (bottom-right) ───────────────────────────────────
        self._ctrl_lbl = self._lbl(
            "WASD: Move   Space: Jump   J:LP  K:RP  U:LK  I:RK",
            (-0.50, 0, -1.02), 0.028, (0.55, 0.55, 0.60, 1),
        )

        # ── Result overlay (center) ────────────────────────────────────────
        self._result_lbl = self._lbl("", (-0.65, 0, 0.18), 0.060, (1.0, 1.0, 1.0, 1))
        self._result_lbl.hide()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _lbl(self, text: str, pos, scale: float, color=(0.95, 0.95, 0.95, 1)):
        tn = TextNode("hud_t")
        tn.setText(text)
        tn.setAlign(TextNode.ALeft)
        np = self.root.attachNewNode(tn)
        np.setPos(pos)
        np.setScale(scale)
        np.setColor(LColor(*color))
        return np

    # ── Public interface ──────────────────────────────────────────────────────

    def add_log(self, line: str) -> None:
        self.log_lines.append(line)
        self.log_lines = self.log_lines[-8:]
        self._log_lbl.node().setText("\n".join(self.log_lines))

    def refresh(self) -> None:
        e = self.engine
        p = e.player

        # HP bar
        pct = max(0.0, p.hp / p.max_hp) if p.max_hp > 0 else 0.0
        self._hp_fill.setScale(pct, 1, 1)
        if pct > 0.6:
            self._hp_fill["frameColor"] = (0.18, 0.84, 0.38, 1.0)
        elif pct > 0.3:
            self._hp_fill["frameColor"] = (0.94, 0.80, 0.10, 1.0)
        else:
            self._hp_fill["frameColor"] = (0.90, 0.18, 0.18, 1.0)
        self._hp_text.node().setText(f"HP   {p.hp} / {p.max_hp}")

        # Wave info
        alive = len(e.alive_enemies())
        self._wave_lbl.node().setText(f"Wave {e.wave}   Enemies: {alive}")

        # Combo hit counter
        if e.combo_count >= 2 and e.combo_timer > 0:
            self._combo_count_lbl.node().setText(f"{e.combo_count} HIT!")
            self._combo_count_lbl.show()
        else:
            self._combo_count_lbl.hide()

        # Combo name banner — fades after timer
        if e.combo_name_timer > 0 and e.last_combo_name:
            tier  = e.last_combo_tier
            color = _TIER_COLOR.get(tier, (1.0, 1.0, 1.0, 1.0))
            alpha = min(1.0, e.combo_name_timer / 0.5)   # fade last 0.5s
            self._combo_name_lbl.node().setText(e.last_combo_name)
            self._combo_name_lbl.setColor(LColor(color[0], color[1], color[2], alpha))
            self._combo_name_lbl.show()
        else:
            self._combo_name_lbl.hide()

        # Input chain display (bottom center)
        chain = getattr(e, "_chain", [])
        if chain:
            self._input_lbl.node().setText("  ".join(chain))
        else:
            self._input_lbl.node().setText("")

    def show_result(self, text: str) -> None:
        self._result_lbl.node().setText(text)
        self._result_lbl.show()

    def hide_result(self) -> None:
        self._result_lbl.hide()
