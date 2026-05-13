"""
Panda3D JRPG-style ATB demo — Roguelike edition.

Run from this folder:
  pip install -r requirements.txt
  python main.py

Controls (battle): 1-7 skills | ←/→ cycle target | Enter confirm
Controls (reward): 1/2/3 pick upgrade | B brew | N next battle
Controls (brew):   1/2/3 brew recipe | N back
"""
from __future__ import annotations

import json
import random
import sys
from enum import Enum, auto
from pathlib import Path

from direct.showbase.ShowBase import ShowBase
from direct.task import Task

from battle.engine import BattleEngine, BattleState
from core import PlayerProfile, RunState, load_profile, save_profile
from render.arena import ArenaScene
from skills.base import SkillResult
from ui.hud import BattleHud


ROOT   = Path(__file__).resolve().parent
CONFIG = ROOT / "config"  / "battle.json"
POOL   = ROOT / "content" / "enemy_pool.json"
UPGDB  = ROOT / "content" / "upgrades.json"
BREWDB = ROOT / "content" / "brew_recipes.json"
SAVE   = ROOT / "save"    / "profile.json"


class AppScene(Enum):
    MENU    = auto()
    BATTLE  = auto()
    REWARD  = auto()
    BREW    = auto()
    GAME_OVER = auto()


class JrpgAtbApp(ShowBase):
    def __init__(self) -> None:
        ShowBase.__init__(self)
        self.setFrameRateMeter(True)
        self.enableParticles()

        self.profile: PlayerProfile = load_profile(SAVE)
        self.scene = AppScene.MENU

        self.run_state = RunState()
        self.run_state.load(POOL)

        self._upgrade_pool: list[dict] = json.loads(
            UPGDB.read_text(encoding="utf-8")
        )["upgrades"]
        self._brew_recipes: list[dict] = json.loads(
            BREWDB.read_text(encoding="utf-8")
        )["recipes"]

        self._flow_locked = False
        self._pending_upgrades: list[dict] = []
        self._pending_reward: dict | None = None
        self._brew_menu: list[dict] = []
        self._fx_busy = False

        self.engine = BattleEngine(
            CONFIG,
            wave_index=1,
            enemy_ids=["blob_small"],
            hero_override=self.profile.hero_override(),
        )

        self.hud = BattleHud(self, self.engine)
        self.arena = ArenaScene(self, self.engine, zone=1)

        self._wire_engine_callbacks()
        self._bind_hotkeys()

        self.hud.add_log("Roguelike run ready.")
        self._show_menu()

        self.taskMgr.add(self._battle_loop, "battle_loop")
        self.accept("escape", sys.exit)

    # ── Wiring ────────────────────────────────────────────────────────────────

    def _wire_engine_callbacks(self) -> None:
        self.engine.on_log = self.hud.add_log
        self.engine.on_result = self._on_skill_result

    def _bind_hotkeys(self) -> None:
        skill_keys = [
            ("1", "attack"),
            ("2", "slash"),
            ("3", "fire_bolt"),
            ("4", "thunder"),
            ("5", "heal"),
            ("6", "wait"),
            ("7", "defend"),
        ]
        self._skill_key_order = [sid for _, sid in skill_keys]
        for key, sid in skill_keys:
            self.accept(key, self._press_skill, [sid])
        self.accept("arrow_left",  self._cycle_target, [-1])
        self.accept("arrow_right", self._cycle_target, [1])
        self.accept("enter", self._confirm_target)
        self.accept("n", self._on_n_key)
        self.accept("r", self._restart_run)
        self.accept("m", self._show_menu)
        self.accept("b", self._on_b_key)
        self.accept("p", self._use_potion)

    # ── Hotkey handlers ───────────────────────────────────────────────────────

    def _press_skill(self, skill_id: str) -> None:
        if self.scene == AppScene.BATTLE:
            self.engine.player_try_skill(skill_id)
        elif self.scene == AppScene.REWARD:
            idx = self._skill_key_order.index(skill_id) if skill_id in self._skill_key_order else -1
            if 0 <= idx <= 2:
                self._pick_upgrade(idx)
        elif self.scene == AppScene.BREW:
            idx = self._skill_key_order.index(skill_id) if skill_id in self._skill_key_order else -1
            if 0 <= idx <= 2:
                self._do_brew(idx)

    def _cycle_target(self, delta: int) -> None:
        self.engine.cycle_target(delta)

    def _confirm_target(self) -> None:
        self.engine.confirm_selected_target()

    def _on_n_key(self) -> None:
        if self.scene in (AppScene.REWARD, AppScene.BREW):
            self._begin_battle()

    def _on_b_key(self) -> None:
        if self.scene == AppScene.MENU:
            self._begin_battle()
        elif self.scene in (AppScene.REWARD, AppScene.BREW):
            self._show_brew()

    def _use_potion(self) -> None:
        if self.scene == AppScene.MENU:
            if not self.profile.consume_item("potion", 1):
                self.hud.add_log("No potions.")
                return
            self.profile.max_hp_bonus += 5
            save_profile(SAVE, self.profile)
            self.hud.add_log("Used potion at camp: +5 max HP bonus.")
            self._show_menu()

    # ── Skill result VFX ──────────────────────────────────────────────────────

    def _on_skill_result(self, actor, result: SkillResult) -> None:
        self._fx_busy = True

        def done() -> None:
            self._fx_busy = False

        self.arena.play_result(actor, result, done)

    # ── Battle flow ───────────────────────────────────────────────────────────

    def _begin_battle(self) -> None:
        if self.scene == AppScene.BATTLE:
            return
        zone = self.run_state.get_zone()
        enemy_ids = self.run_state.get_enemy_ids()
        label = "BOSS BATTLE!" if self.run_state.is_boss() else f"Depth {self.run_state.depth}"

        self.scene = AppScene.BATTLE
        self._flow_locked = False
        self.engine = BattleEngine(
            CONFIG,
            wave_index=self.run_state.depth,
            enemy_ids=enemy_ids,
            hero_override=self.profile.hero_override(),
        )
        self._wire_engine_callbacks()
        self.hud.engine = self.engine
        self.arena.engine = self.engine
        self.arena.reset_for_battle(zone)
        self.hud.hide_result()
        self.hud.add_log(f"{label} — {', '.join(enemy_ids)}")

    def _refresh_result_flow(self) -> None:
        if self.scene != AppScene.BATTLE:
            return
        st = self.engine.state
        if st == BattleState.VICTORY and self.engine.last_reward and not self._flow_locked:
            self._flow_locked = True
            rw = self.engine.last_reward
            self._pending_reward = dict(rw)

            self.profile.gain_gold(int(rw["gold"]))
            for item in rw["loot"]:
                self.profile.add_item(item, 1)
            lvl_lines = self.profile.gain_exp(int(rw["exp"]))
            for ln in lvl_lines:
                self.hud.add_log(ln)

            kill_lines: list[str] = []
            for _ in self.engine.enemies:
                kill_lines.extend(self.profile.on_kill())
            for ln in kill_lines:
                self.hud.add_log(ln)

            save_profile(SAVE, self.profile)
            self.run_state.advance()
            self._show_reward(rw)

        elif st == BattleState.DEFEAT:
            self.scene = AppScene.GAME_OVER
            self.hud.show_result(
                f"DEFEAT — Depth {self.run_state.depth}\n"
                f"Lv {self.profile.level}  Gold {self.profile.gold}\n"
                "Press R to start a new run."
            )

    # ── Reward / upgrade screen ───────────────────────────────────────────────

    def _show_reward(self, rw: dict) -> None:
        self.scene = AppScene.REWARD
        pool = self._upgrade_pool
        count = min(3, len(pool))
        self._pending_upgrades = random.sample(pool, count)

        lines = [
            f"VICTORY!  Depth {self.run_state.depth - 1}  →  Depth {self.run_state.depth}",
            f"+EXP {rw['exp']}  +Gold {rw['gold']}",
        ]
        if rw["loot"]:
            lines.append(f"Loot: {', '.join(rw['loot'])}")
        lines.append("")
        lines.append("Choose an upgrade (1 / 2 / 3):")
        for i, upg in enumerate(self._pending_upgrades, 1):
            lines.append(f"  {i}. {upg['name']}")
        lines.append("")
        lines.append("B = Brew items  |  N = Skip, next battle  |  R = Restart")
        self.hud.show_result("\n".join(lines))

    def _pick_upgrade(self, idx: int) -> None:
        if self.scene != AppScene.REWARD:
            return
        if idx >= len(self._pending_upgrades):
            return
        upg = self._pending_upgrades[idx]
        lines = self.profile.apply_upgrade(upg)
        save_profile(SAVE, self.profile)
        for ln in lines:
            self.hud.add_log(ln)
        self.hud.add_log(f"Upgrade chosen: {upg['name']}")
        self._pending_upgrades = []
        self._refresh_reward_display()

    def _refresh_reward_display(self) -> None:
        lines = [
            f"Lv {self.profile.level}  Exp {self.profile.exp}/{self.profile.exp_to_next()}",
            f"Gold {self.profile.gold}  ATK {self.profile.attack_bonus}",
            f"HP +{self.profile.max_hp_bonus}  MP +{self.profile.max_mp_bonus}",
            "",
            "B = Brew items  |  N = Next battle  |  R = Restart",
        ]
        self.hud.show_result("\n".join(lines))

    # ── Brew screen ───────────────────────────────────────────────────────────

    def _show_brew(self) -> None:
        inv = self.profile.inventory
        available = [
            r for r in self._brew_recipes
            if all(inv.get(item, 0) >= count for item, count in r["ingredients"].items())
        ]
        self._brew_menu = available[:3]

        lines = ["BREW STATION"]
        lines.append(f"Inventory: {', '.join(f'{v}x {k}' for k, v in inv.items() if k != 'potion') or 'empty'}")
        lines.append("")
        if available:
            lines.append("Available recipes (1 / 2 / 3):")
            for i, r in enumerate(self._brew_menu, 1):
                lines.append(f"  {i}. {r['name']} — {r['desc']}")
        else:
            lines.append("No brewable recipes with current items.")
        lines.append("")
        lines.append("N = Back / Next battle  |  R = Restart")
        self.scene = AppScene.BREW
        self.hud.show_result("\n".join(lines))

    def _do_brew(self, idx: int) -> None:
        if self.scene != AppScene.BREW:
            return
        if idx >= len(self._brew_menu):
            self.hud.add_log("No recipe at that slot.")
            return
        recipe = self._brew_menu[idx]
        _, lines = self.profile.brew(recipe)
        save_profile(SAVE, self.profile)
        for ln in lines:
            self.hud.add_log(ln)
        self._show_brew()

    # ── Menu / misc ───────────────────────────────────────────────────────────

    def _show_menu(self) -> None:
        self.scene = AppScene.MENU
        inv_potions = self.profile.inventory.get("potion", 0)
        self.hud.show_result(
            f"ROGUELIKE ATB\n"
            f"Lv {self.profile.level}  Gold {self.profile.gold}  Kills {self.profile.kill_count}\n"
            f"ATK +{self.profile.attack_bonus}  HP +{self.profile.max_hp_bonus}\n"
            f"Potions: {inv_potions}\n\n"
            "B = Begin Run\n"
            "P = Use Potion at camp (+5 max HP)\n"
            "R = Reset profile & new run"
        )

    def _restart_run(self) -> None:
        self.profile = PlayerProfile()
        save_profile(SAVE, self.profile)
        self.run_state = RunState()
        self.run_state.load(POOL)
        self._pending_upgrades = []
        self._pending_reward = None
        self._brew_menu = []
        self.scene = AppScene.MENU
        self._show_menu()

    # ── Main loop ─────────────────────────────────────────────────────────────

    def _battle_loop(self, task: Task) -> int:
        if (
            self.scene == AppScene.BATTLE
            and not self._fx_busy
            and self.engine.state not in (BattleState.VICTORY, BattleState.DEFEAT)
        ):
            self.engine.update(globalClock.getDt())

        if self.scene == AppScene.BATTLE and self.engine.state == BattleState.PLAYER_PICK_TARGET:
            tgt = self.engine.selected_target()
            self.arena.set_target_highlight(tgt.unit_id if tgt else None)
        else:
            self.arena.set_target_highlight(None)

        self._refresh_result_flow()
        self.hud.refresh()
        if self.scene == AppScene.BATTLE:
            self.arena.update_hp_bars()
        return task.cont


if __name__ == "__main__":
    JrpgAtbApp().run()
