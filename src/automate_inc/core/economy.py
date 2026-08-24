"""Income, costs and the token market. Pure functions - no game state, no I/O."""

from __future__ import annotations

import random
from collections.abc import Iterable

from automate_inc.core.projects import Project
from automate_inc.core.tech import Modifiers
from automate_inc.core.workers import Cost, Role, Worker, load_roles

NO_MODIFIERS = Modifiers()
"""Neutral modifiers, so every function here stays callable without a tech tree."""

TOKEN_PRICE_SWING = 0.10
"""Random price movement per round, +/- 10% (VISION.md, "Dynamische Token-Wirtschaft")."""

TOKEN_PRICE_INFLATION = 1.01
"""Long-term upward drift. Tokens get more expensive the longer you rely on them."""

SALES_VISIBILITY_BONUS = 10.0
"""Percentage points of visibility each assigned sales worker adds to a project."""


def calculate_income(
    base_income: float,
    quality: float,
    aesthetics: float,
    bugs: float,
    visibility_bonus: float,
    *,
    aesthetics_applies: bool = True,
) -> float:
    """Income per round (PROJECTS_AND_PRODUCTS_SPEC.md 6.1).

    ``aesthetics_applies`` is the one deviation from the written formula: a project
    that never asked for a designer is not punished for having no aesthetics.
    """
    aesthetics_factor = (aesthetics / 100.0) if aesthetics_applies else 1.0
    return (
        base_income
        * (quality / 100.0)
        * aesthetics_factor
        * ((100.0 - bugs) / 100.0)
        * ((100.0 + visibility_bonus) / 100.0)
    )


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
            bonus += SALES_VISIBILITY_BONUS * worker.efficiency
            continue
        staleness = catalog.spec(worker.role).agent_staleness
        if staleness is not None and not worker.is_human:
            bonus += staleness.penalty_for(worker.level, worker.rounds_in_assignment)
    return bonus


def project_income(
    project: Project,
    workers: Iterable[Worker],
    modifiers: Modifiers = NO_MODIFIERS,
) -> float:
    workers = list(workers)
    return calculate_income(
        base_income=project.base_income,
        quality=project.quality,
        aesthetics=project.aesthetics,
        bugs=project.bugs,
        visibility_bonus=visibility_bonus_for(project, workers),
        aesthetics_applies=project.requires(Role.DESIGNER),
    ) * modifiers.income_multiplier


def project_costs(
    project: Project,
    workers: Iterable[Worker],
    modifiers: Modifiers = NO_MODIFIERS,
) -> Cost:
    """Fixed costs plus everyone assigned to this project."""
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


AGENT_ALIGNMENT_DECAY = {1: 0.0, 2: -1.0, 3: -3.0}
"""Alignment lost per agent and round, by level. BALANCING.md 7: the decay hangs
on the level, never on the role."""

HUMAN_ALIGNMENT_GAIN = 1.0
"""BALANCING.md 9: humans slow the decay, they do not stop it."""


def alignment_delta(workers: Iterable[Worker], modifiers: Modifiers = NO_MODIFIERS) -> float:
    """The alignment balance for one round - deterministic and readable.

    BALANCING.md 8: there is no random base decay. The player must be able to
    connect what they did to what happened.

    The decay from agents is dampened by alignment research, the gains are not.
    A dampener scales with the size of the fleet where a flat bonus would not -
    which is what makes "research alignment" a real answer to "hire humans", and
    what makes it deepen the dependency instead of ending it.
    """
    decay = sum(
        AGENT_ALIGNMENT_DECAY.get(w.level, 0.0) for w in workers if not w.is_human
    )
    gain = sum(HUMAN_ALIGNMENT_GAIN for w in workers if w.is_human)
    return decay * modifiers.alignment_decay_multiplier + gain + modifiers.alignment_per_round


def next_token_price(price: float, rng: random.Random) -> float:
    swing = rng.uniform(1.0 - TOKEN_PRICE_SWING, 1.0 + TOKEN_PRICE_SWING)
    return round(price * swing * TOKEN_PRICE_INFLATION, 2)
