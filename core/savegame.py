from __future__ import annotations

import json
from pathlib import Path

from core.progression import PlayerProfile


def load_profile(path: Path) -> PlayerProfile:
    if not path.exists():
        return PlayerProfile()
    raw = json.loads(path.read_text(encoding="utf-8"))
    return PlayerProfile.from_dict(raw)


def save_profile(path: Path, profile: PlayerProfile) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile.to_dict(), indent=2), encoding="utf-8")
