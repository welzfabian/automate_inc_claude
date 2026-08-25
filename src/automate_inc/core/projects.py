"""Projects: time-limited client work that earns money while it lasts."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from importlib import resources

from automate_inc.core.workers import Role

ATTRIBUTE_MIN = 0.0
ATTRIBUTE_MAX = 100.0

INITIAL_BUGS = 0.0


@dataclass(frozen=True)
class Tuning:
    """Balancing knobs for the project mechanics. Data, never code."""

    service_level_start: float
    service_level_build_rate: float
    service_level_neglect_rate: float
    attribute_start: float
    attribute_cap_base: float
    attribute_entropy: float
    sales_visibility_bonus: float

    def cap(self, filled: int, required: int) -> float:
        """How high an attribute can climb at this staffing level.

        The base is what an unstaffed role decays to. It cannot usefully exceed
        ``attribute_start``: an attribute only rises through workers of its own
        role, so with the role unfilled a higher cap would never be reached.
        """
        return self.attribute_cap_base + (
            ATTRIBUTE_MAX - self.attribute_cap_base
        ) * filled / required


class ProjectType(str, Enum):
    WEBSITE = "WEBSITE"
    ECOMMERCE = "ECOMMERCE"
    WEB_APP = "WEB_APP"
    MOBILE_APP = "MOBILE_APP"
    ENTERPRISE_SOFTWARE = "ENTERPRISE_SOFTWARE"
    KI_INTEGRATION = "KI_INTEGRATION"


@dataclass(frozen=True)
class ProjectBlueprint:
    """A project as defined in data/projects.json - not yet running."""

    id: str
    name: str
    description: str
    project_type: ProjectType
    required_roles: dict[Role, int]
    base_income: int
    basis_fixed_costs: int
    lifetime: int
    requires: tuple[str, ...] = ()
    """Blueprints that must already have been commissioned before this one is
    offered - the ladder's rungs, held in data exactly like ``Technology.requires``.
    A client hands over the big job to whoever can show the smaller one."""


@dataclass
class Project:
    """A running project. Its attributes drift with the workers assigned to it."""

    id: str
    blueprint_id: str
    name: str
    project_type: ProjectType
    required_roles: dict[Role, int]
    base_income: int
    basis_fixed_costs: int
    lifetime: int
    current_round: int = 0
    service_level: float = 0.0
    quality: float = 0.0
    aesthetics: float = 0.0
    bugs: float = INITIAL_BUGS
    assigned_workers: list[str] = field(default_factory=list)

    @property
    def at_full_service(self) -> bool:
        """Running at the full level it was sold at - not a finished state.

        It is a ceiling the team holds, and it slides back the moment nobody does.
        """
        return self.service_level >= ATTRIBUTE_MAX

    @property
    def is_expired(self) -> bool:
        return self.current_round >= self.lifetime

    @property
    def rounds_left(self) -> int:
        return max(0, self.lifetime - self.current_round)

    def requires(self, role: Role) -> bool:
        """Whether this project cares about a role at all.

        Attributes a project never asked for count as neutral in the income
        formula - a static website has no designer and must not be penalised
        for having no aesthetics.
        """
        return role in self.required_roles

    def adjust(self, attribute: str, amount: float) -> None:
        """Apply a delta to a project attribute, clamped to 0-100."""
        current = getattr(self, attribute)
        setattr(self, attribute, max(ATTRIBUTE_MIN, min(ATTRIBUTE_MAX, current + amount)))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "blueprint_id": self.blueprint_id,
            "name": self.name,
            "project_type": self.project_type.value,
            "required_roles": {role.value: count for role, count in self.required_roles.items()},
            "base_income": self.base_income,
            "basis_fixed_costs": self.basis_fixed_costs,
            "lifetime": self.lifetime,
            "current_round": self.current_round,
            "service_level": self.service_level,
            "quality": self.quality,
            "aesthetics": self.aesthetics,
            "bugs": self.bugs,
            "assigned_workers": list(self.assigned_workers),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Project:
        return cls(
            id=data["id"],
            blueprint_id=data["blueprint_id"],
            name=data["name"],
            project_type=ProjectType(data["project_type"]),
            required_roles={Role(r): c for r, c in data["required_roles"].items()},
            base_income=data["base_income"],
            basis_fixed_costs=data["basis_fixed_costs"],
            lifetime=data["lifetime"],
            current_round=data["current_round"],
            service_level=data["service_level"],
            quality=data["quality"],
            aesthetics=data["aesthetics"],
            bugs=data["bugs"],
            assigned_workers=list(data["assigned_workers"]),
        )


class ProjectRegistry:
    """Catalog of available projects. Adding a project is pure configuration."""

    def __init__(self, blueprints: dict[str, ProjectBlueprint]) -> None:
        self._blueprints = blueprints

    @classmethod
    def from_json(cls, text: str) -> ProjectRegistry:
        raw = json.loads(text)
        blueprints = {
            entry["id"]: ProjectBlueprint(
                id=entry["id"],
                name=entry["name"],
                description=entry["description"],
                project_type=ProjectType(entry["project_type"]),
                required_roles={Role(r): c for r, c in entry["required_roles"].items()},
                base_income=entry["base_income"],
                basis_fixed_costs=entry["basis_fixed_costs"],
                lifetime=entry["lifetime"],
                requires=tuple(entry.get("requires", [])),
            )
            for entry in raw["projects"]
        }
        for blueprint in blueprints.values():
            missing = [r for r in blueprint.requires if r not in blueprints]
            if missing:
                raise ValueError(f"Project {blueprint.id!r} requires unknown: {missing}")
        return cls(blueprints)

    def all(self) -> list[ProjectBlueprint]:
        return list(self._blueprints.values())

    def get(self, blueprint_id: str) -> ProjectBlueprint | None:
        return self._blueprints.get(blueprint_id)

    def missing_requirements(
        self, blueprint: ProjectBlueprint, started: Iterable[str]
    ) -> list[str]:
        done = set(started)
        return [r for r in blueprint.requires if r not in done]

    def is_available(self, blueprint: ProjectBlueprint, started: Iterable[str]) -> bool:
        """Whether this job is on offer: not taken yet, and its references done."""
        started = set(started)
        return blueprint.id not in started and not self.missing_requirements(blueprint, started)

    def instantiate(self, blueprint_id: str, instance_id: str) -> Project:
        blueprint = self._blueprints[blueprint_id]
        tuning = load_tuning()
        return Project(
            id=instance_id,
            blueprint_id=blueprint.id,
            name=blueprint.name,
            project_type=blueprint.project_type,
            required_roles=dict(blueprint.required_roles),
            base_income=blueprint.base_income,
            basis_fixed_costs=blueprint.basis_fixed_costs,
            lifetime=blueprint.lifetime,
            service_level=tuning.service_level_start,
            quality=tuning.attribute_start,
            aesthetics=tuning.attribute_start,
        )


def _project_data() -> str:
    return resources.files("automate_inc.data").joinpath("projects.json").read_text("utf-8")


@lru_cache(maxsize=1)
def load_registry() -> ProjectRegistry:
    return ProjectRegistry.from_json(_project_data())


@lru_cache(maxsize=1)
def load_tuning() -> Tuning:
    return Tuning(**json.loads(_project_data())["tuning"])
