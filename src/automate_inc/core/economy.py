"""Income, costs and the token market. Pure functions - no game state, no I/O."""

from __future__ import annotations

import random
from collections.abc import Iterable

from automate_inc.core.events import Pressure
from automate_inc.core.projects import Project, load_tuning
from automate_inc.core.tech import Modifiers
from automate_inc.core.workers import Cost, Role, Worker, load_roles

NO_MODIFIERS = Modifiers()
"""Neutral modifiers, so every function here stays callable without a tech tree."""

NO_PRESSURE = Pressure()
"""Neutral pressure, so every function here stays callable without any events."""

ROLE_ATTRIBUTES = {Role.DEVELOPER: "quality", Role.DESIGNER: "aesthetics"}
"""Which role holds which project attribute - and therefore caps it. Sales holds
none: leaving that post empty costs the visibility bonus, which is punishment enough."""

TOKEN_PRICE_SWING = 0.10
"""Random price movement per round, +/- 10% (VISION.md, "Dynamische Token-Wirtschaft")."""

TOKEN_PRICE_INFLATION = 1.01
"""Long-term upward drift. Tokens get more expensive the longer you rely on them."""

def calculate_income(
    base_income: float,
    service_level: float,
    quality: float,
    aesthetics: float,
    bugs: float,
    visibility_bonus: float,
    *,
    quality_applies: bool = True,
    aesthetics_applies: bool = True,
) -> float:
    """Income per round (PROJECTS_AND_PRODUCTS_SPEC.md 6.1).

    Two deviations from the written formula. ``quality_applies`` /
    ``aesthetics_applies``: a project that never asked for the role holding an
    attribute is not punished for not having it (BALANCING.md 2) - a static
    website has no designer, a landing page has no developer. And
    ``service_level``: you are paid for what the client is actually getting right
    now - that is what stops an unstaffed project from being free money.
    """
    quality_factor = (quality / 100.0) if quality_applies else 1.0
    aesthetics_factor = (aesthetics / 100.0) if aesthetics_applies else 1.0
    return (
        base_income
        * (service_level / 100.0)
        * quality_factor
        * aesthetics_factor
        * ((100.0 - bugs) / 100.0)
        * ((100.0 + visibility_bonus) / 100.0)
    )


def attribute_applies(project: Project, attribute: str) -> bool:
    """Whether this project asked for the role that holds ``attribute``.

    Read off ``ROLE_ATTRIBUTES`` rather than hard-coding the two role names, so
    that a project without a developer and a project without a designer are the
    same case - the neutral-attribute rule from BALANCING.md 2 held for aesthetics
    only until the project ladder added a design-only job.
    """
    return any(
        project.requires(role) for role, held in ROLE_ATTRIBUTES.items() if held == attribute
    )


def service_level_delta(project: Project, workers: Iterable[Worker]) -> float:
    """How much the service this project delivers moves this round.

    Staffed projects climb in proportion to how many of their posts are filled,
    weighted by efficiency. Only a project nobody is answerable for slides back:
    partial staffing is punished through the attribute caps instead. Taking the
    service level away too would let a one-third staffed project stall below 100
    forever - a trap the player cannot read in advance.

    "Nobody answerable" covers both the abandoned project and the one left to
    level-1 agents. ``Game.start_project`` has always demanded a senior worker;
    without the same test here, the founder could start a project, hand it to
    agents who own nothing and collect full income forever (BALANCING.md 24).
    """
    tuning = load_tuning()
    assigned = [w for w in workers if w.assigned_to == project.id]
    if not any(w.is_senior for w in assigned):
        return -tuning.service_level_neglect_rate
    slots = sum(project.required_roles.values())
    return tuning.service_level_build_rate * sum(w.efficiency for w in assigned) / slots


def attribute_cap(project: Project, workers: Iterable[Worker], role: Role) -> float:
    """The ceiling this project's staffing puts on the role's attribute."""
    required = project.required_roles[role]
    filled = sum(1 for w in workers if w.assigned_to == project.id and w.role is role)
    return load_tuning().cap(min(filled, required), required)


def attribute_delta(
    project: Project,
    workers: Iterable[Worker],
    role: Role,
    effect_amount: float,
    modifiers: Modifiers = NO_MODIFIERS,
) -> float:
    """How far a role's attribute moves this round: up toward its cap, or down to it.

    Above the cap it decays, once per unfilled post - so a project that loses half
    its team slides to what half a team can hold, and no further.
    """
    tuning = load_tuning()
    required = project.required_roles[role]
    assigned = [w for w in workers if w.assigned_to == project.id and w.role is role]
    cap = attribute_cap(project, workers, role)
    current = getattr(project, ROLE_ATTRIBUTES[role])
    if current > cap:
        return max(cap - current, -tuning.attribute_entropy * (required - len(assigned)))
    gain = sum(effect_amount * w.efficiency for w in assigned)
    if role is Role.DEVELOPER:
        gain *= modifiers.quality_multiplier
    return min(cap - current, gain)


def visibility_bonus_for(project: Project, workers: Iterable[Worker]) -> float:
    """Sales workers make a project visible. Stale designers make it forgettable.

    The staleness malus lives here rather than in the turn loop because it is not
    an event: it is a standing property of who is on the project right now.
    """
    catalog = load_roles()
    bonus = 0.0
    for worker in workers:
        if worker.assigned_to != project.id:
            continue
        if worker.role is Role.SALES:
            bonus += load_tuning().sales_visibility_bonus * worker.efficiency
            continue
        staleness = catalog.spec(worker.role).agent_staleness
        if staleness is not None and not worker.is_human:
            bonus += staleness.penalty_for(worker.level, worker.rounds_in_assignment)
    return bonus


def project_income(
    project: Project,
    workers: Iterable[Worker],
    modifiers: Modifiers = NO_MODIFIERS,
    pressure: Pressure = NO_PRESSURE,
) -> float:
    workers = list(workers)
    return (
        calculate_income(
            base_income=project.base_income,
            service_level=project.service_level,
            quality=project.quality,
            aesthetics=project.aesthetics,
            bugs=project.bugs,
            visibility_bonus=visibility_bonus_for(project, workers),
            quality_applies=attribute_applies(project, "quality"),
            aesthetics_applies=attribute_applies(project, "aesthetics"),
        )
        * modifiers.income_multiplier
        * pressure.income_multiplier
    )


def project_costs(
    project: Project,
    workers: Iterable[Worker],
    modifiers: Modifiers = NO_MODIFIERS,
) -> Cost:
    """Fixed costs plus everyone assigned to this project. Pressure's own cost
    fields are company-wide, not per project, and are added in ``pressure_costs``."""
    total = Cost(money=float(project.basis_fixed_costs))
    for worker in workers:
        if worker.assigned_to == project.id:
            total = total + worker.cost_per_round(modifiers)
    return total


def idle_worker_costs(workers: Iterable[Worker], modifiers: Modifiers = NO_MODIFIERS) -> Cost:
    """Workers without an assignment still get paid. Payroll does not pause."""
    total = Cost()
    for worker in workers:
        if worker.assigned_to is None:
            total = total + worker.cost_per_round(modifiers)
    return total


def pressure_costs(workers: Iterable[Worker], pressure: Pressure = NO_PRESSURE) -> Cost:
    """Rent, taxes, regulation: costs pressure adds on top, company-wide.

    ``fixed_cost`` applies once regardless of headcount (rent does not care how
    many agents you run); ``cost_per_agent`` scales with the fleet on purpose -
    it is how the AI-specific events (a per-agent tax) become a real cost.
    """
    agents = sum(1 for w in workers if not w.is_human)
    return Cost(money=pressure.fixed_cost + pressure.cost_per_agent * agents)


AGENT_ALIGNMENT_DECAY = {1: 0.0, 2: -1.0, 3: -3.0}
"""Alignment lost per agent and round, by level. BALANCING.md 7: the decay hangs
on the level, never on the role."""

HUMAN_ALIGNMENT_GAIN = 1.0
"""BALANCING.md 9: humans slow the decay, they do not stop it."""


def alignment_delta(
    workers: Iterable[Worker],
    modifiers: Modifiers = NO_MODIFIERS,
    pressure: Pressure = NO_PRESSURE,
) -> float:
    """The alignment balance for one round - deterministic and readable.

    BALANCING.md 8: there is no random base decay. The player must be able to
    connect what they did to what happened.

    The decay from agents is dampened by alignment research, the gains are not.
    A dampener scales with the size of the fleet where a flat bonus would not -
    which is what makes "research alignment" a real answer to "hire humans", and
    what makes it deepen the dependency instead of ending it. Event pressure adds
    on top, undampened - it is not a consequence of fleet size.
    """
    decay = sum(
        AGENT_ALIGNMENT_DECAY.get(w.level, 0.0) for w in workers if not w.is_human
    )
    gain = sum(HUMAN_ALIGNMENT_GAIN for w in workers if w.is_human)
    return (
        decay * modifiers.alignment_decay_multiplier
        + gain
        + modifiers.alignment_per_round
        + pressure.alignment_per_round
    )


def next_token_price(price: float, rng: random.Random) -> float:
    swing = rng.uniform(1.0 - TOKEN_PRICE_SWING, 1.0 + TOKEN_PRICE_SWING)
    return round(price * swing * TOKEN_PRICE_INFLATION, 2)
