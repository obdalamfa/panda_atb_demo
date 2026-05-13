"""Action-game HUD — HP bar, wave info, combo counter, log, result overlay."""
from __future__ import annotations

from direct.gui.DirectGui import DirectFrame
from direct.showbase.ShowBase import ShowBase
from panda3d.core import LColor, TextNode


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

        # ── Combo counter (upper-center) ───────────────────────────────────
        self._combo_lbl = self._lbl("", (-0.22, 0, 0.62), 0.082, (1.0, 0.72, 0.12, 1))
        self._combo_lbl.hide()

        # ── Controls hint (bottom-right) ───────────────────────────────────
        self._ctrl_lbl = self._lbl(
            "WASD/Arrows: Move   Space: Jump   J: Attack",
            (-0.38, 0, -0.97), 0.030, (0.58, 0.58, 0.62, 1),
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

        # HP bar fill
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

        # Combo
        if e.combo_count >= 3 and e.combo_timer > 0:
            self._combo_lbl.node().setText(f"{e.combo_count} HIT COMBO!")
            self._combo_lbl.show()
        else:
            self._combo_lbl.hide()

    def show_result(self, text: str) -> None:
        self._result_lbl.node().setText(text)
        self._result_lbl.show()

    def hide_result(self) -> None:
        self._result_lbl.hide()
