"""The complete game state, serialisable to plain JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from automate_inc.core.events import ActiveEffect
from automate_inc.core.projects import Project
from automate_inc.core.workers import Worker

SAVE_FORMAT_VERSION = 6

START_MONEY = 1000.0
START_TOKENS = 50.0
START_TOKEN_PRICE = 10.0
START_RESEARCH = 0
START_ALIGNMENT = 100.0
START_OFFICE_CAPACITY = 3
"""Exactly what the minimal single-project team needs (BALANCING.md 19) - the
baseline strategy never has to touch ``expand_office``."""
START_INVESTOR_EQUITY = 15.0
"""The seed money was never yours - the first slice is already gone on turn 0.
Payouts are a share of net profit, never of revenue (``Game._pay_investors``),
so this pauses on its own the moment a team is struggling instead of being
able to push a marginal run into bankruptcy. Calibrated in BALANCING.md 21."""

MAX_LOG_ENTRIES = 200


class Phase(str, Enum):
    BUILDUP = "BUILDUP"
    SCALING = "SCALING"
    AUTONOMY = "AUTONOMY"


SCALING_AGENT_COUNT = 3
"""Enough agents to count as scaling even without any research."""

AUTONOMY_AGENT_COUNT = 6
"""A fleet this size that outnumbers the humans runs the company, not you.

Deliberately twice the scaling count: three agents beside one founder is a small
company being efficient, not an autonomous one."""

AUTONOMY_ALIGNMENT = 50.0
"""Below this the company is in the autonomy phase whatever else is true."""


@dataclass
class GameState:
    money: float = START_MONEY
    tokens: float = START_TOKENS
    token_price: float = START_TOKEN_PRICE
    research: int = START_RESEARCH
    alignment: float = START_ALIGNMENT
    turn: int = 0
    researched: list[str] = field(default_factory=list)
    phase_announced: str = Phase.BUILDUP.value
    """The phase last reported to the player.

    The phase itself is always derived, never stored - but it now changes the
    moment you hire or research, not at end of turn. Remembering what was last
    announced is what still lets the turn report mention it."""
    workers: list[Worker] = field(default_factory=list)
    active_projects: list[Project] = field(default_factory=list)
    rng_seed: int = 0
    log: list[str] = field(default_factory=list)
    game_over_reason: str | None = None
    active_events: list[ActiveEffect] = field(default_factory=list)
    """Running event effects, read by ``events.Pressure`` - the ``Modifiers``
    equivalent for external pressure instead of research."""
    pending_decisions: list[str] = field(default_factory=list)
    """Event IDs waiting for ``Game.answer_event``. Non-empty blocks ``resolve_turn``."""
    event_history: list[str] = field(default_factory=list)
    """Every event ID that has ever triggered, in order - drives ``once`` and
    ``after_event``/``not_after_event`` chains."""
    event_last_turn: dict[str, int] = field(default_factory=dict)
    """Turn each event last triggered on, for its cooldown."""
    last_net: float | None = None
    """The previous round's net result, read by the ``max_last_net`` condition."""
    office_capacity: int = START_OFFICE_CAPACITY
    """How many human workers fit at once. Agents are exempt - see ``Game.expand_office``."""
    investor_equity: float = START_INVESTOR_EQUITY
    """Percentage of income permanently owed to investors, see ``Game.raise_funding``.
    Starts above zero: the seed round already sold a slice, on turn 0."""

    def phase(self, unlocked_agent_level: int = 1) -> Phase:
        """Which phase the company is in, derived from what the player has done.

        Not from the turn number: the game says "scaling" because you scaled.
        The research signal is read from ``Modifiers`` rather than from technology
        IDs, so the engine still knows nothing about individual technologies.

        Deliberately recomputed on every call and allowed to fall back - firing
        your agents really does take the company out of autonomy.
        """
        agents = [w for w in self.workers if not w.is_human]
        humans = [w for w in self.workers if w.is_human]
        outnumbered = len(agents) >= AUTONOMY_AGENT_COUNT and len(agents) > len(humans)
        if unlocked_agent_level >= 3 or outnumbered or self.alignment < AUTONOMY_ALIGNMENT:
            return Phase.AUTONOMY
        if unlocked_agent_level >= 2 or len(agents) >= SCALING_AGENT_COUNT:
            return Phase.SCALING
        return Phase.BUILDUP

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
            "phase_announced": self.phase_announced,
            "workers": [w.to_dict() for w in self.workers],
            "active_projects": [p.to_dict() for p in self.active_projects],
            "rng_seed": self.rng_seed,
            "log": list(self.log),
            "game_over_reason": self.game_over_reason,
            "active_events": [e.to_dict() for e in self.active_events],
            "pending_decisions": list(self.pending_decisions),
            "event_history": list(self.event_history),
            "event_last_turn": dict(self.event_last_turn),
            "last_net": self.last_net,
            "office_capacity": self.office_capacity,
            "investor_equity": self.investor_equity,
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
            phase_announced=data["phase_announced"],
            workers=[Worker.from_dict(w) for w in data["workers"]],
            active_projects=[Project.from_dict(p) for p in data["active_projects"]],
            rng_seed=data["rng_seed"],
            log=list(data["log"]),
            game_over_reason=data["game_over_reason"],
            active_events=[ActiveEffect.from_dict(e) for e in data["active_events"]],
            pending_decisions=list(data["pending_decisions"]),
            event_history=list(data["event_history"]),
            event_last_turn=dict(data["event_last_turn"]),
            last_net=data["last_net"],
            office_capacity=data["office_capacity"],
            investor_equity=data["investor_equity"],
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), "utf-8")

    @classmethod
    def load(cls, path: Path) -> GameState:
        return cls.from_dict(json.loads(path.read_text("utf-8")))
