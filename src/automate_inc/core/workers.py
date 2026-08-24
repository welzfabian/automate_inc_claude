"""Roles and workers - the people (and things) that do the work."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from importlib import resources


class Role(str, Enum):
    DEVELOPER = "DEVELOPER"
    DESIGNER = "DESIGNER"
    SALES = "SALES"
    RESEARCHER = "RESEARCHER"


class WorkerType(str, Enum):
    HUMAN = "HUMAN"
    AGENT = "AGENT"


@dataclass(frozen=True)
class Effect:
    """What a worker contributes to its assignment each round."""

    attribute: str
    amount: float


@dataclass(frozen=True)
class ErrorChance:
    """A rare mistake. Humans always have one; agents only from level 2 up."""

    chance: float
    attribute: str
    amount: float


@dataclass(frozen=True)
class Staleness:
    """A penalty that grows out of routine rather than out of a dice roll.

    Only the designer has one: an agent that works the same project for too long
    starts producing generic designs (GAME_DESIGN.md 1).
    """

    after_rounds: int
    penalty: dict[int, float]

    def penalty_for(self, level: int, rounds_in_assignment: int) -> float:
        if rounds_in_assignment < self.after_rounds:
            return 0.0
        return self.penalty.get(level, 0.0)


@dataclass(frozen=True)
class RoleSpec:
    id: Role
    name: str
    symbol: str
    human_salary: int
    agent_tokens: int
    effect: Effect
    human_error: ErrorChance
    agent_side_effect: dict[int, ErrorChance]
    agent_staleness: Staleness | None = None

    def side_effect_for(self, level: int) -> ErrorChance | None:
        """Level 1 agents have no side effects by design - that is the bait."""
        return self.agent_side_effect.get(level)


@dataclass(frozen=True)
class RoleCatalog:
    """All role definitions plus the shared efficiency/cost tables."""

    roles: dict[Role, RoleSpec]
    efficiency: dict[str, float]
    agent_token_multiplier: dict[int, float]

    def spec(self, role: Role) -> RoleSpec:
        return self.roles[role]


def _staleness(raw: dict | None) -> Staleness | None:
    if not raw:
        return None
    return Staleness(
        after_rounds=raw["after_rounds"],
        penalty={int(level): float(value) for level, value in raw["penalty"].items()},
    )


@lru_cache(maxsize=1)
def load_roles() -> RoleCatalog:
    """Load the role catalog from the bundled JSON. Cached: the data never changes."""
    raw = json.loads(resources.files("automate_inc.data").joinpath("roles.json").read_text("utf-8"))
    roles = {
        Role(entry["id"]): RoleSpec(
            id=Role(entry["id"]),
            name=entry["name"],
            symbol=entry["symbol"],
            human_salary=entry["human_salary"],
            agent_tokens=entry["agent_tokens"],
            effect=Effect(**entry["effect"]),
            human_error=ErrorChance(**entry["human_error"]),
            agent_side_effect={
                int(level): ErrorChance(**data)
                for level, data in entry.get("agent_side_effect", {}).items()
            },
            agent_staleness=_staleness(entry.get("agent_staleness")),
        )
        for entry in raw["roles"]
    }
    return RoleCatalog(
        roles=roles,
        efficiency=dict(raw["efficiency"]),
        agent_token_multiplier={int(k): v for k, v in raw["agent_token_cost_multiplier"].items()},
    )


@dataclass(frozen=True)
class Cost:
    """Money and tokens are separate currencies and are settled separately."""

    money: float = 0.0
    tokens: float = 0.0

    def __add__(self, other: Cost) -> Cost:
        return Cost(self.money + other.money, self.tokens + other.tokens)


@dataclass
class Worker:
    id: str
    role: Role
    worker_type: WorkerType
    name: str = ""
    level: int = 1
    assigned_to: str | None = None
    rounds_in_assignment: int = 0
    """Rounds spent on the current assignment; reset whenever it changes."""

    @property
    def is_human(self) -> bool:
        return self.worker_type is WorkerType.HUMAN

    @property
    def effective_level(self) -> int:
        """Humans always satisfy the level-2 requirement for starting a project.

        GAME_DESIGN.md 3.2 allows "an agent OR an experienced human"; without this,
        no project could ever be started on turn 0 (level 2 agents need research,
        research needs income, income needs a project).
        """
        return 2 if self.is_human else self.level

    @property
    def efficiency(self) -> float:
        catalog = load_roles()
        key = "HUMAN" if self.is_human else f"AGENT_{self.level}"
        return catalog.efficiency[key]

    def cost_per_round(self, modifiers: object | None = None) -> Cost:
        """Humans cost money, agents cost tokens. Unassigned workers still cost.

        ``modifiers`` is a ``tech.Modifiers``; typed loosely to keep this module
        free of a tech import it would otherwise only need for an annotation.
        """
        spec = load_roles().spec(self.role)
        if self.is_human:
            return Cost(money=float(spec.human_salary))
        multiplier = load_roles().agent_token_multiplier[self.level]
        discount = getattr(modifiers, "token_cost_multiplier", 1.0)
        return Cost(tokens=spec.agent_tokens * multiplier * discount)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role.value,
            "worker_type": self.worker_type.value,
            "name": self.name,
            "level": self.level,
            "assigned_to": self.assigned_to,
            "rounds_in_assignment": self.rounds_in_assignment,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Worker:
        return cls(
            id=data["id"],
            role=Role(data["role"]),
            worker_type=WorkerType(data["worker_type"]),
            name=data.get("name", ""),
            level=data.get("level", 1),
            assigned_to=data.get("assigned_to"),
            rounds_in_assignment=data.get("rounds_in_assignment", 0),
        )
