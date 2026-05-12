"""
Panda3D JRPG-style ATB demo (modular battle layer + 3D arena).

Unity reference (clone locally to compare tuning): https://github.com/obdalimfa/Unity3D-Turn_Based_RPG.git

Run from this folder:
  pip install -r requirements.txt
  python main.py
"""
from __future__ import annotations

import json
import sys
from enum import Enum, auto
from pathlib import Path

from direct.showbase.ShowBase import ShowBase
from direct.task import Task

from battle.engine import BattleEngine, BattleState
from core import PlayerProfile, load_profile, save_profile
from render.arena import ArenaScene
from skills.base import SkillResult
from ui.hud import BattleHud


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "battle.json"
AREAS = ROOT / "content" / "areas.json"
SHOP = ROOT / "content" / "shop.json"
SAVE = ROOT / "save" / "profile.json"


class AppScene(Enum):
    MENU = auto()
    EXPLORE = auto()
    BATTLE = auto()
    REWARD = auto()
    SHOP = auto()
    GAME_OVER = auto()
    CLEAR = auto()


class JrpgAtbApp(ShowBase):
    def __init__(self) -> None:
        ShowBase.__init__(self)
        self.setFrameRateMeter(True)
        self.enableParticles()

        self.profile: PlayerProfile = load_profile(SAVE)
        self.scene = AppScene.MENU
        self.wave_index = 1
        self.total_loot: list[str] = []
        self._flow_locked = False
        self.pending_reward: dict | None = None
        self.areas = json.loads(AREAS.read_text(encoding="utf-8"))["chapters"]
        self.shop_items = json.loads(SHOP.read_text(encoding="utf-8"))["items"]
        self.max_wave = int(json.loads(CONFIG.read_text(encoding="utf-8")).get("waves", {}).get("max_wave", 5))

        self.engine = BattleEngine(CONFIG, wave_index=self.wave_index, hero_override=self.profile.hero_override())
        self._fx_busy = False

        self.hud = BattleHud(self, self.engine)
        self.arena = ArenaScene(self, self.engine)

        self._wire_engine_callbacks()
        self._bind_hotkeys()

        self.hud.add_log("Campaign flow ready. Start from menu.")
        self._show_menu()

        self.taskMgr.add(self._battle_loop, "battle_loop")
        self.accept("escape", sys.exit)

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
        for key, sid in skill_keys:
            self.accept(key, self._press_skill, [sid])
        self.accept("arrow_left", self._cycle_target, [-1])
        self.accept("arrow_right", self._cycle_target, [1])
        self.accept("enter", self._confirm_target)
        self.accept("n", self._next_wave)
        self.accept("r", self._restart_run)
        self.accept("m", self._show_menu)
        self.accept("s", self._enter_shop)
        self.accept("b", self._start_encounter)
        self.accept("p", self._use_potion)
        self.accept("o", self._buy_first_shop_item)

    def _press_skill(self, skill_id: str) -> None:
        self.engine.player_try_skill(skill_id)

    def _cycle_target(self, delta: int) -> None:
        self.engine.cycle_target(delta)

    def _confirm_target(self) -> None:
        self.engine.confirm_selected_target()

    def _on_skill_result(self, actor, result: SkillResult) -> None:
        self._fx_busy = True

        def done() -> None:
            self._fx_busy = False

        self.arena.play_result(actor, result, done)

    def _refresh_result_flow(self) -> None:
        if self.scene != AppScene.BATTLE:
            return
        st = self.engine.state
        if st == BattleState.VICTORY and self.engine.last_reward and not self._flow_locked:
            rw = self.engine.last_reward
            self.profile.gain_gold(int(rw["gold"]))
            self.total_loot.extend(list(rw["loot"]))
            lvl_lines = self.profile.gain_exp(int(rw["exp"]))
            self._flow_locked = True
            self.pending_reward = dict(rw)
            for ln in lvl_lines:
                self.hud.add_log(ln)
            save_profile(SAVE, self.profile)
            self.scene = AppScene.REWARD
            self.hud.show_result(
                f"VICTORY\n"
                f"+EXP {rw['exp']}  +Gold {rw['gold']}\n"
                f"Loot: {', '.join(rw['loot']) if rw['loot'] else '-'}\n"
                f"Lv {self.profile.level}  Exp {self.profile.exp}/{self.profile.exp_to_next()}  Gold {self.profile.gold}\n"
                "Press N = continue explore, S = shop, R = restart run"
            )
        elif st == BattleState.DEFEAT:
            self.scene = AppScene.GAME_OVER
            self.hud.show_result(
                f"DEFEAT\n"
                f"Reached Chapter {self.profile.chapter} Encounter {self.profile.encounter_index + 1}\n"
                "Press R to restart run."
            )

    def _show_menu(self) -> None:
        self.scene = AppScene.MENU
        self.hud.show_result(
            "JRPG ATB DEMO\n"
            "Press B = Start/Resume Explore\n"
            "Press S = Shop\n"
            "Press P = Use Potion in camp\n"
            "Press R = New Run"
        )

    def _current_chapter(self) -> dict:
        idx = max(0, min(self.profile.chapter - 1, len(self.areas) - 1))
        return self.areas[idx]

    def _encounter_for_progress(self) -> dict:
        chapter = self._current_chapter()
        encounters = chapter["encounters"]
        idx = self.profile.encounter_index
        if idx >= len(encounters):
            return chapter["boss"]
        return encounters[idx]

    def _start_encounter(self) -> None:
        if self.scene in (AppScene.BATTLE,):
            return
        self.scene = AppScene.BATTLE
        enc = self._encounter_for_progress()
        self.wave_index = max(1, self.profile.chapter + self.profile.encounter_index)
        self._boot_wave(enemy_ids=list(enc["enemy_ids"]))
        self.hud.add_log(f"Encounter: {enc['label']}")

    def _advance_progress_after_win(self) -> None:
        chapter = self._current_chapter()
        encounters = chapter["encounters"]
        if self.profile.encounter_index < len(encounters):
            self.profile.encounter_index += 1
        else:
            self.profile.chapter = min(self.profile.chapter + 1, len(self.areas))
            self.profile.encounter_index = 0
        save_profile(SAVE, self.profile)

    def _enter_shop(self) -> None:
        if self.scene not in (AppScene.MENU, AppScene.EXPLORE, AppScene.REWARD):
            return
        self.scene = AppScene.SHOP
        lines = ["SHOP"]
        for i, item in enumerate(self.shop_items, start=1):
            lines.append(f"{i}. {item['name']} ({item['price']}g)")
        lines.append(f"Gold: {self.profile.gold}")
        lines.append("Quick Buy: press O to buy item #1 (Potion)")
        lines.append("Press B to go explore")
        self.hud.show_result("\n".join(lines))

    def _buy_first_shop_item(self) -> None:
        if self.scene != AppScene.SHOP:
            return
        item = self.shop_items[0]
        if not self.profile.pay(int(item["price"])):
            self.hud.add_log("Not enough gold.")
            return
        self.profile.add_item(item["id"], 1)
        save_profile(SAVE, self.profile)
        self.hud.add_log(f"Bought {item['name']}.")
        self._enter_shop()

    def _use_potion(self) -> None:
        if self.scene not in (AppScene.MENU, AppScene.EXPLORE, AppScene.SHOP):
            return
        if not self.profile.consume_item("potion", 1):
            self.hud.add_log("No potion left.")
            return
        # Camp-side sustain as macro progression
        self.profile.max_hp_bonus += 1
        save_profile(SAVE, self.profile)
        self.hud.add_log("Used potion in camp: +1 max HP bonus.")

    def _next_wave(self) -> None:
        if self.scene != AppScene.REWARD:
            return
        self._advance_progress_after_win()
        if self.profile.chapter >= len(self.areas) and self.profile.encounter_index == 0:
            self.scene = AppScene.CLEAR
            self.hud.show_result(
                f"CHAPTER CLEAR!\nLv {self.profile.level} | Gold {self.profile.gold}\n"
                f"Loot: {', '.join(self.total_loot) if self.total_loot else '-'}\n"
                "Press R for new run, B to replay explore."
            )
            return
        self.scene = AppScene.EXPLORE
        self.hud.show_result(
            f"EXPLORE - Chapter {self.profile.chapter}\n"
            "Press B for next encounter.\n"
            "Press S for shop.\n"
            "Press M for menu."
        )

    def _restart_run(self) -> None:
        self.profile = PlayerProfile()
        self.total_loot = []
        self.wave_index = 1
        self.scene = AppScene.MENU
        save_profile(SAVE, self.profile)
        self._boot_wave(enemy_ids=None)
        self._show_menu()

    def _boot_wave(self, enemy_ids: list[str] | None) -> None:
        self.hud.hide_result()
        self._flow_locked = False
        self.engine = BattleEngine(
            CONFIG,
            wave_index=self.wave_index,
            enemy_ids=enemy_ids,
            hero_override=self.profile.hero_override(),
        )
        self._wire_engine_callbacks()
        self.hud.engine = self.engine
        self.arena.engine = self.engine
        self.hud.add_log(f"Wave {self.wave_index} begins.")

    def _battle_loop(self, task: Task) -> int:
        if self.scene == AppScene.BATTLE and not self._fx_busy and self.engine.state not in (BattleState.VICTORY, BattleState.DEFEAT):
            self.engine.update(globalClock.getDt())
        if self.scene == AppScene.BATTLE and self.engine.state == BattleState.PLAYER_PICK_TARGET:
            tgt = self.engine.selected_target()
            self.arena.set_target_highlight(tgt.unit_id if tgt else None)
        else:
            self.arena.set_target_highlight(None)
        self._refresh_result_flow()
        self.hud.refresh()
        return task.cont


if __name__ == "__main__":
    JrpgAtbApp().run()
