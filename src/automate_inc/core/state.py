"""The complete game state, serialisable to plain JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from automate_inc.core.projects import Project
from automate_inc.core.workers import Worker

SAVE_FORMAT_VERSION = 2

START_MONEY = 1000.0
START_TOKENS = 50.0
START_TOKEN_PRICE = 10.0
START_RESEARCH = 0
START_ALIGNMENT = 100.0

MAX_LOG_ENTRIES = 200


class Phase(str, Enum):
    BUILDUP = "BUILDUP"
    SCALING = "SCALING"
    AUTONOMY = "AUTONOMY"

    @classmethod
    def for_turn(cls, turn: int) -> Phase:
        if turn < 5:
            return cls.BUILDUP
        if turn < 10:
            return cls.SCALING
        return cls.AUTONOMY


@dataclass
class GameState:
    money: float = START_MONEY
    tokens: float = START_TOKENS
    token_price: float = START_TOKEN_PRICE
    research: int = START_RESEARCH
    alignment: float = START_ALIGNMENT
    turn: int = 0
    researched: list[str] = field(default_factory=list)
    workers: list[Worker] = field(default_factory=list)
    active_projects: list[Project] = field(default_factory=list)
    rng_seed: int = 0
    log: list[str] = field(default_factory=list)
    game_over_reason: str | None = None

    @property
    def phase(self) -> Phase:
        return Phase.for_turn(self.turn)

    @property
    def is_over(self) -> bool:
        return self.game_over_reason is not None

    def worker(self, worker_id: str) -> Worker | None:
        return next((w for w in self.workers if w.id == worker_id), None)

    def project(self, project_id: str) -> Project | None:
        return next((p for p in self.active_projects if p.id == project_id), None)

    def workers_on(self, project_id: str) -> list[Worker]:
        return [w for w in self.workers if w.assigned_to == project_id]

    def has_researched(self, tech_id: str) -> bool:
        return tech_id in self.researched

    def add_log(self, message: str) -> None:
        self.log.append(message)
        del self.log[:-MAX_LOG_ENTRIES]

    def to_dict(self) -> dict:
        return {
            "format_version": SAVE_FORMAT_VERSION,
            "money": self.money,
            "tokens": self.tokens,
            "token_price": self.token_price,
            "research": self.research,
            "alignment": self.alignment,
            "turn": self.turn,
            "researched": list(self.researched),
            "workers": [w.to_dict() for w in self.workers],
            "active_projects": [p.to_dict() for p in self.active_projects],
            "rng_seed": self.rng_seed,
            "log": list(self.log),
            "game_over_reason": self.game_over_reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GameState:
        version = data.get("format_version")
        if version != SAVE_FORMAT_VERSION:
            raise ValueError(f"Unsupported save format version: {version!r}")
        return cls(
            money=data["money"],
            tokens=data["tokens"],
            token_price=data["token_price"],
            research=data["research"],
            alignment=data["alignment"],
            turn=data["turn"],
            researched=list(data["researched"]),
            workers=[Worker.from_dict(w) for w in data["workers"]],
            active_projects=[Project.from_dict(p) for p in data["active_projects"]],
            rng_seed=data["rng_seed"],
            log=list(data["log"]),
            game_over_reason=data["game_over_reason"],
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), "utf-8")

    @classmethod
    def load(cls, path: Path) -> GameState:
        return cls.from_dict(json.loads(path.read_text("utf-8")))
