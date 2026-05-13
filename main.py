"""
Panda3D 2.5D Beat-em-up — Roguelike edition.

Run:
  pip install -r requirements.txt
  python main.py

Controls (battle):
  WASD / Arrow Keys — Move (W/S = depth axis)
  Space             — Jump
  J                 — Attack
  R                 — Restart run
  M                 — Menu
"""
from __future__ import annotations

import json
import random
import sys
from enum import Enum, auto
from pathlib import Path

from direct.showbase.ShowBase import ShowBase
from direct.task import Task

from battle.action_engine import ActionEngine
from core import PlayerProfile, RunState, load_profile, save_profile
from render.arena import ArenaScene
from ui.hud import ActionHud


ROOT   = Path(__file__).resolve().parent
CONFIG = ROOT / "config"  / "battle.json"
POOL   = ROOT / "content" / "enemy_pool.json"
UPGDB  = ROOT / "content" / "upgrades.json"
BREWDB = ROOT / "content" / "brew_recipes.json"
SAVE   = ROOT / "save"    / "profile.json"


class AppScene(Enum):
    MENU      = auto()
    BATTLE    = auto()
    REWARD    = auto()
    BREW      = auto()
    GAME_OVER = auto()


def _load_unit_stats(config_path: Path) -> dict:
    """Return a flat dict keyed by unit id from battle.json party + enemies."""
    cfg    = json.loads(config_path.read_text(encoding="utf-8"))
    result = {}
    for u in cfg.get("party", []):
        result[u["id"]] = u
    for u in cfg.get("enemies", []):
        # Flatten rewards into the dict for easy access
        r = u.get("rewards", {})
        result[u["id"]] = {**u, "exp_reward": r.get("exp", 0),
                           "gold_reward": r.get("gold", 0),
                           "loot_reward": r.get("loot", [])}
    return result


class BeatEmUpApp(ShowBase):
    def __init__(self) -> None:
        ShowBase.__init__(self)
        self.setFrameRateMeter(True)
        self.enableParticles()

        self.profile   = load_profile(SAVE)
        self.scene     = AppScene.MENU
        self.run_state = RunState()
        self.run_state.load(POOL)

        self._unit_stats  = _load_unit_stats(CONFIG)
        self._upgrade_pool: list[dict] = json.loads(
            UPGDB.read_text(encoding="utf-8")
        )["upgrades"]
        self._brew_recipes: list[dict] = json.loads(
            BREWDB.read_text(encoding="utf-8")
        )["recipes"]

        self._pending_upgrades: list[dict] = []
        self._brew_menu:        list[dict] = []
        self._flow_locked = False

        # Key-held state (continuous) + edge events
        self._keys: dict[str, bool] = {}

        # Build a placeholder engine for the initial scene (menu)
        self.engine = self._make_engine()
        self.hud    = ActionHud(self, self.engine)
        self.arena  = ArenaScene(self, self.engine, zone=1)

        self._bind_keys()
        self._show_menu()

        self.taskMgr.add(self._main_loop, "main_loop")
        self.accept("escape", sys.exit)

    # ── Engine factory ────────────────────────────────────────────────────────

    @staticmethod
    def _action_atk(stats: dict) -> int:
        """Derive action-game atk from ATB stats (hp-proportional)."""
        return max(6, int(stats.get("hp", 40) * 0.18))

    @staticmethod
    def _action_cd(stats: dict) -> float:
        """Faster ATB speed → shorter attack cooldown."""
        return max(0.8, 1.8 / max(0.5, stats.get("speed", 1.0)))

    def _make_engine(self, enemy_ids: list[str] | None = None, wave: int = 1) -> ActionEngine:
        p          = self.profile
        hero_stats = self._unit_stats.get("hero", {})
        player_data = {
            "hp":    p.max_hp_bonus + hero_stats.get("hp", 220),
            "atk":   p.attack_bonus  + 22,
            "speed": 4.8,
        }
        enemies_data: list[dict] = []
        if enemy_ids:
            for eid in enemy_ids:
                stats = self._unit_stats.get(eid, {})
                enemies_data.append({
                    "unit_id":      eid,
                    "name":         stats.get("name", eid),
                    "hp":           stats.get("hp", 40),
                    "atk":          self._action_atk(stats),
                    "speed":        max(1.5, stats.get("speed", 1.0) * 1.8),
                    "attack_cd":    self._action_cd(stats),
                    "attack_range": 1.4,
                    "exp":          stats.get("exp_reward", 20),
                    "gold":         stats.get("gold_reward", 10),
                    "loot":         stats.get("loot_reward", []),
                })
        return ActionEngine(player_data, enemies_data, wave=wave)

    # ── Key binding ───────────────────────────────────────────────────────────

    def _bind_keys(self) -> None:
        move_keys = ["a", "d", "w", "s",
                     "arrow_left", "arrow_right", "arrow_up", "arrow_down"]
        for k in move_keys:
            self.accept(k,        self._key_down, [k])
            self.accept(k + "-up", self._key_up,  [k])

        # Jump — edge trigger
        self.accept("space",    self._on_jump)
        self.accept("space-up", self._noop)

        # Attack
        self.accept("j", self._on_attack)
        self.accept("f", self._on_attack)

        # Meta
        self.accept("n", self._on_n)
        self.accept("b", self._on_b)
        self.accept("r", self._restart_run)
        self.accept("m", self._show_menu)
        self.accept("p", self._use_potion)

        # Upgrade picks (1/2/3)
        for i, k in enumerate(("1", "2", "3")):
            self.accept(k, self._pick_or_brew, [i])

    def _key_down(self, k: str) -> None:
        self._keys[k] = True

    def _key_up(self, k: str) -> None:
        self._keys[k] = False

    def _noop(self) -> None:
        pass

    def _on_jump(self) -> None:
        if self.scene == AppScene.BATTLE:
            self._keys["space_pressed"] = True

    def _on_attack(self) -> None:
        if self.scene == AppScene.BATTLE:
            self.engine.queue_attack()

    def _on_n(self) -> None:
        if self.scene in (AppScene.REWARD, AppScene.BREW):
            self._begin_battle()

    def _on_b(self) -> None:
        if self.scene == AppScene.MENU:
            self._begin_battle()
        elif self.scene in (AppScene.REWARD, AppScene.BREW):
            self._show_brew()

    def _pick_or_brew(self, idx: int) -> None:
        if self.scene == AppScene.REWARD:
            self._pick_upgrade(idx)
        elif self.scene == AppScene.BREW:
            self._do_brew(idx)

    def _use_potion(self) -> None:
        if self.scene != AppScene.MENU:
            return
        if not self.profile.consume_item("potion", 1):
            self.hud.add_log("No potions.")
            return
        self.profile.max_hp_bonus += 5
        save_profile(SAVE, self.profile)
        self.hud.add_log("Used potion at camp: +5 max HP bonus.")
        self._show_menu()

    # ── Battle flow ───────────────────────────────────────────────────────────

    def _begin_battle(self) -> None:
        if self.scene == AppScene.BATTLE:
            return
        zone       = self.run_state.get_zone()
        enemy_ids  = self.run_state.get_enemy_ids()
        label      = "BOSS BATTLE!" if self.run_state.is_boss() else f"Depth {self.run_state.depth}"

        self.engine    = self._make_engine(enemy_ids, wave=self.run_state.depth)
        self.hud.engine = self.engine
        self.arena.engine = self.engine
        self.arena.reset_for_battle(zone)
        self.hud.hide_result()
        self.scene     = AppScene.BATTLE
        self._flow_locked = False
        self._keys     = {}

        self.hud.add_log(f"{label}  —  {', '.join(enemy_ids)}")

    def _check_battle_over(self) -> None:
        if self.scene != AppScene.BATTLE:
            return

        e = self.engine
        if e.cleared and not self._flow_locked:
            self._flow_locked = True
            # Collect rewards
            exp  = sum(u.exp_reward  for u in e.enemies)
            gold = sum(u.gold_reward for u in e.enemies)
            loot = [item for u in e.enemies for item in u.loot_reward]

            self.profile.gain_gold(gold)
            for item in loot:
                self.profile.add_item(item, 1)
            for ln in self.profile.gain_exp(exp):
                self.hud.add_log(ln)
            for _ in e.enemies:
                for ln in self.profile.on_kill():
                    self.hud.add_log(ln)

            save_profile(SAVE, self.profile)
            self.run_state.advance()
            self._show_reward({"exp": exp, "gold": gold, "loot": loot})

        elif e.game_over:
            self.scene = AppScene.GAME_OVER
            self.hud.show_result(
                f"DEFEAT — Depth {self.run_state.depth}\n"
                f"Lv {self.profile.level}  Gold {self.profile.gold}\n"
                "Press R to start a new run."
            )

    # ── Reward / upgrade screen ───────────────────────────────────────────────

    def _show_reward(self, rw: dict) -> None:
        self.scene = AppScene.REWARD
        pool  = self._upgrade_pool
        self._pending_upgrades = random.sample(pool, min(3, len(pool)))

        lines = [
            f"VICTORY!  Depth {self.run_state.depth - 1}  →  Depth {self.run_state.depth}",
            f"+EXP {rw['exp']}  +Gold {rw['gold']}",
        ]
        if rw["loot"]:
            lines.append(f"Loot: {', '.join(rw['loot'])}")
        lines += ["", "Choose an upgrade (1 / 2 / 3):"]
        for i, upg in enumerate(self._pending_upgrades, 1):
            lines.append(f"  {i}. {upg['name']}")
        lines += ["", "B = Brew  |  N = Skip, next fight  |  R = Restart"]
        self.hud.show_result("\n".join(lines))

    def _pick_upgrade(self, idx: int) -> None:
        if idx >= len(self._pending_upgrades):
            return
        upg = self._pending_upgrades[idx]
        for ln in self.profile.apply_upgrade(upg):
            self.hud.add_log(ln)
        self.hud.add_log(f"Upgrade: {upg['name']}")
        self._pending_upgrades = []
        save_profile(SAVE, self.profile)
        lines = [
            f"Lv {self.profile.level}  Exp {self.profile.exp}/{self.profile.exp_to_next()}",
            f"Gold {self.profile.gold}  ATK +{self.profile.attack_bonus}",
            f"HP +{self.profile.max_hp_bonus}",
            "", "B = Brew  |  N = Next fight  |  R = Restart",
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
        lines.append(
            f"Inventory: {', '.join(f'{v}x {k}' for k, v in inv.items() if k != 'potion') or 'empty'}"
        )
        lines.append("")
        if available:
            lines.append("Recipes (1/2/3):")
            for i, r in enumerate(self._brew_menu, 1):
                lines.append(f"  {i}. {r['name']} — {r['desc']}")
        else:
            lines.append("No brewable recipes.")
        lines += ["", "N = Back / Next fight  |  R = Restart"]
        self.scene = AppScene.BREW
        self.hud.show_result("\n".join(lines))

    def _do_brew(self, idx: int) -> None:
        if idx >= len(self._brew_menu):
            self.hud.add_log("No recipe there.")
            return
        _, lines = self.profile.brew(self._brew_menu[idx])
        save_profile(SAVE, self.profile)
        for ln in lines:
            self.hud.add_log(ln)
        self._show_brew()

    # ── Menu ──────────────────────────────────────────────────────────────────

    def _show_menu(self) -> None:
        self.scene = AppScene.MENU
        potions = self.profile.inventory.get("potion", 0)
        self.hud.show_result(
            f"ROGUELIKE BEAT-EM-UP\n"
            f"Lv {self.profile.level}  Gold {self.profile.gold}  Kills {self.profile.kill_count}\n"
            f"ATK +{self.profile.attack_bonus}  HP +{self.profile.max_hp_bonus}\n"
            f"Potions: {potions}\n\n"
            "B = Begin Run\n"
            "P = Use Potion (+5 max HP)\n"
            "R = Reset profile & new run"
        )

    def _restart_run(self) -> None:
        self.profile   = PlayerProfile()
        save_profile(SAVE, self.profile)
        self.run_state = RunState()
        self.run_state.load(POOL)
        self._pending_upgrades = []
        self._brew_menu        = []
        self.scene             = AppScene.MENU
        self._show_menu()

    # ── Main loop ─────────────────────────────────────────────────────────────

    def _main_loop(self, task: Task) -> int:
        dt = globalClock.getDt()

        if self.scene == AppScene.BATTLE:
            self.engine.update(dt, self._keys)
            self.arena.process_damage_log()
            self.arena.update_characters()
            self._check_battle_over()

        self.hud.refresh()
        return task.cont


if __name__ == "__main__":
    BeatEmUpApp().run()
