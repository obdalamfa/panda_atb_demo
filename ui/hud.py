from __future__ import annotations

from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextNode

from battle.engine import BattleEngine, BattleState


class BattleHud:
    def __init__(self, base: ShowBase, engine: BattleEngine) -> None:
        self.base = base
        self.engine = engine
        self.log_lines: list[str] = []

        self.root = base.aspect2d.attachNewNode("hud_root")

        self.status_label = self._label("", (-1.28, 0, 0.92), 0.042)
        self.log_label = self._label("", (-1.28, 0, 0.58), 0.035)
        self.info_label = self._label("", (-1.28, 0, -0.44), 0.032)
        self.result_label = self._label("", (-0.55, 0, 0.22), 0.055)
        self.result_label.hide()

        self.panel = DirectFrame(
            frameSize=(-1.38, 1.38, -0.98, -0.48),
            frameColor=(0.02, 0.02, 0.05, 0.72),
            pos=(0, 0, -0.86),
            parent=base.aspect2d,
        )

        skill_specs = [
            ("attack", "Attack"),
            ("slash", "Slash"),
            ("fire_bolt", "Fire Bolt"),
            ("thunder", "Thunder"),
            ("heal", "Heal"),
            ("wait", "Wait"),
            ("defend", "Defend"),
        ]
        self._buttons: dict[str, DirectButton] = {}
        cols = 4
        for i, (sid, label) in enumerate(skill_specs):
            row, col = divmod(i, cols)
            x = -0.95 + col * 0.62
            y = -0.02 - row * 0.13
            btn = DirectButton(
                text=label,
                scale=0.062,
                pos=(x, 0, y),
                command=lambda s=sid: self.engine.player_try_skill(s),
                parent=self.panel,
                state="disabled",
            )
            self._buttons[sid] = btn

        self.btn_cancel = DirectButton(
            text="Cancel",
            scale=0.055,
            pos=(-1.2, 0, 0.18),
            command=self._cancel_target,
            parent=self.panel,
            state="disabled",
        )

        self._target_buttons: list[DirectButton] = []
        self._target_button_uids: list[str] = []

        self._last_picking_state = False
        self._last_selected_idx = -1

        self.set_commands_enabled(False)

    def _label(self, text: str, pos, scale: float):
        tn = TextNode("hud_text")
        tn.setText(text)
        tn.setAlign(TextNode.ALeft)
        np = self.root.attachNewNode(tn)
        np.setPos(pos)
        np.setScale(scale)
        np.setColor(0.95, 0.95, 0.95, 1)
        return np

    def _clear_target_buttons(self) -> None:
        for b in self._target_buttons:
            b.destroy()
        self._target_buttons.clear()

    def add_log(self, line: str) -> None:
        self.log_lines.append(line)
        self.log_lines = self.log_lines[-9:]
        self.log_label.node().setText("\n".join(self.log_lines))

    def set_commands_enabled(self, enabled: bool) -> None:
        for btn in self._buttons.values():
            btn["state"] = "normal" if enabled else "disabled"

    def refresh(self) -> None:
        e = self.engine
        lines: list[str] = []

        picking = e.state == BattleState.PLAYER_PICK_TARGET

        h = e.hero
        lines.append(
            f"{h.name}  HP {h.hp}/{h.max_hp}  MP {h.mp}/{h.max_mp}  ATB {h.atb:5.1f}/{e.atb_max}"
            f"{'  DEF' if h.defending else ''}"
            f"{'  Regen:' + str(h.effects.get('regen', 0)) if h.has_effect('regen') else ''}"
            f"{'  Psn:' + str(h.effects.get('poison', 0)) if h.has_effect('poison') else ''}"
            f"{'  Slow:' + str(h.effects.get('slow', 0)) if h.has_effect('slow') else ''}"
        )

        for foe in e.enemies:
            if foe.alive:
                lines.append(
                    f"{foe.name}  HP {foe.hp}/{foe.max_hp}  MP {foe.mp}/{foe.max_mp}  ATB {foe.atb:5.1f}/{e.atb_max}"
                    f"{'  DEF' if foe.defending else ''}"
                    f"{'  Psn:' + str(foe.effects.get('poison', 0)) if foe.has_effect('poison') else ''}"
                    f"{'  Slow:' + str(foe.effects.get('slow', 0)) if foe.has_effect('slow') else ''}"
                )
            else:
                lines.append(f"{foe.name}  (KO)")

        self.status_label.node().setText("\n".join(lines))
        self.info_label.node().setText(
            "Hotkeys: 1-7 skills | Target: Left/Right, Enter | B battle, S shop, M menu, N continue, R restart"
        )

        st = e.state
        over = st in (BattleState.VICTORY, BattleState.DEFEAT)
        if over:
            self.set_commands_enabled(False)
            self.btn_cancel["state"] = "disabled"
            if self._last_picking_state:
                self._clear_target_buttons()
                self._last_picking_state = False
            return

        if picking:
            self.set_commands_enabled(False)
            self.btn_cancel["state"] = "normal"
            foes = e.alive_enemies()
            
            if not self._last_picking_state or self._last_selected_idx != e.selected_target_idx:
                self._clear_target_buttons()
                for i, foe in enumerate(foes):
                    x = -0.95 + i * 0.42  # narrower if many foes
                    b = DirectButton(
                        text=f"> {foe.name} <" if i == e.selected_target_idx else foe.name,
                        scale=0.05,
                        pos=(x if len(foes) <= 4 else -1.05 + (i % 5) * 0.52, 0, 0.2 - 0.12 * (i // 5)),
                        command=lambda uid=foe.unit_id: self.engine.player_confirm_target(uid),
                        parent=self.panel,
                    )
                    self._target_buttons.append(b)
                    self._target_button_uids.append(foe.unit_id)
                self._last_selected_idx = e.selected_target_idx
                self._last_picking_state = True
            return

        if self._last_picking_state:
            self._clear_target_buttons()
            self._last_picking_state = False

        self.btn_cancel["state"] = "disabled"

        can_cmd = st == BattleState.PLAYER_COMMAND and e.pending_actor is h
        self.set_commands_enabled(can_cmd)
        if can_cmd:
            for sid, btn in self._buttons.items():
                ok = e.skill_available(h, sid)
                btn["state"] = "normal" if ok else "disabled"

    def show_result(self, text: str) -> None:
        self.result_label.node().setText(text)
        self.result_label.show()

    def hide_result(self) -> None:
        self.result_label.hide()

    def _cancel_target(self) -> None:
        self.engine.player_cancel_target()
