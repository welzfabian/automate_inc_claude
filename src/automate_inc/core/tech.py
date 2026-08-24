"""The tech tree: what research points buy, and what that does to everything else.

Built like ``core/projects.py`` on purpose - blueprint dataclass, registry loaded
from bundled JSON, cached loader - so that adding a technology stays pure
configuration.

The important type here is ``Modifiers``: the aggregate of everything researched
so far. The rest of the engine asks it questions ("how expensive are tokens?")
instead of knowing technology IDs. A new technology that reuses an existing
modifier field therefore needs no code change at all.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, fields
from enum import Enum
from functools import lru_cache
from importlib import resources


class TechCategory(str, Enum):
    FOUNDATION = "FOUNDATION"
    ECONOMY = "ECONOMY"
    AI = "AI"
    DANGEROUS = "DANGEROUS"


@dataclass(frozen=True)
class Technology:
    """A node in the tech tree, as defined in data/technologies.json."""

    id: str
    name: str
    description: str
    category: TechCategory
    cost: int
    requires: tuple[str, ...]
    effects: dict[str, float]
    risk: str = ""


@dataclass(frozen=True)
class Modifiers:
    """Everything researched so far, folded into one value object.

    Defaults are the neutral element of each field's aggregation rule, so an
    empty research list yields "no effect at all".
    """

    unlocked_agent_level: int = 1
    quality_multiplier: float = 1.0
    bug_chance_multiplier: float = 1.0
    token_cost_multiplier: float = 1.0
    income_multiplier: float = 1.0
    alignment_per_round: float = 0.0
    alignment_decay_multiplier: float = 1.0


# How each modifier field combines when several technologies touch it. This is
# the single place that knows; ``aggregate`` and the JSON validation both read it.
AGGREGATION: dict[str, str] = {
    "unlocked_agent_level": "max",
    "quality_multiplier": "multiply",
    "bug_chance_multiplier": "multiply",
    "token_cost_multiplier": "multiply",
    "income_multiplier": "multiply",
    "alignment_per_round": "add",
    "alignment_decay_multiplier": "multiply",
}

MODIFIER_FIELDS = frozenset(f.name for f in fields(Modifiers))


def aggregate(technologies: Iterable[Technology]) -> Modifiers:
    """Fold a set of researched technologies into a single ``Modifiers``."""
    values: dict[str, float] = {f.name: f.default for f in fields(Modifiers)}
    for tech in technologies:
        for key, amount in tech.effects.items():
            rule = AGGREGATION[key]
            if rule == "max":
                values[key] = max(values[key], amount)
            elif rule == "multiply":
                values[key] *= amount
            else:
                values[key] += amount
    values["unlocked_agent_level"] = int(values["unlocked_agent_level"])
    return Modifiers(**values)


class TechRegistry:
    """Catalog of technologies. Adding one is pure configuration."""

    def __init__(self, technologies: dict[str, Technology]) -> None:
        self._technologies = technologies

    @classmethod
    def from_json(cls, text: str) -> TechRegistry:
        raw = json.loads(text)
        technologies: dict[str, Technology] = {}
        for entry in raw["technologies"]:
            effects = {str(k): float(v) for k, v in entry["effects"].items()}
            unknown = set(effects) - MODIFIER_FIELDS
            if unknown:
                raise ValueError(
                    f"Technology {entry['id']!r} has unknown effects: {sorted(unknown)}"
                )
            technologies[entry["id"]] = Technology(
                id=entry["id"],
                name=entry["name"],
                description=entry["description"],
                category=TechCategory(entry["category"]),
                cost=entry["cost"],
                requires=tuple(entry.get("requires", [])),
                effects=effects,
                risk=entry.get("risk", ""),
            )
        for tech in technologies.values():
            missing = [r for r in tech.requires if r not in technologies]
            if missing:
                raise ValueError(f"Technology {tech.id!r} requires unknown: {missing}")
        return cls(technologies)

    def all(self) -> list[Technology]:
        return list(self._technologies.values())

    def get(self, tech_id: str) -> Technology | None:
        return self._technologies.get(tech_id)

    def resolve(self, tech_ids: Iterable[str]) -> list[Technology]:
        """Technologies for these IDs, silently skipping IDs the catalog lost.

        A save may name a technology a later catalog no longer has; that must not
        crash the load.
        """
        return [t for t in (self._technologies.get(i) for i in tech_ids) if t is not None]

    def missing_requirements(self, tech: Technology, researched: Iterable[str]) -> list[str]:
        done = set(researched)
        return [r for r in tech.requires if r not in done]

    def is_available(self, tech: Technology, researched: Iterable[str]) -> bool:
        researched = set(researched)
        return tech.id not in researched and not self.missing_requirements(tech, researched)


@lru_cache(maxsize=1)
def load_tech_registry() -> TechRegistry:
    text = resources.files("automate_inc.data").joinpath("technologies.json").read_text("utf-8")
    return TechRegistry.from_json(text)


def modifiers_for(researched: Iterable[str], registry: TechRegistry | None = None) -> Modifiers:
    registry = registry if registry is not None else load_tech_registry()
    return aggregate(registry.resolve(researched))
