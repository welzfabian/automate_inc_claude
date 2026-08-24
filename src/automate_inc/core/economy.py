"""Income, costs and the token market. Pure functions - no game state, no I/O."""

from __future__ import annotations

import random
from collections.abc import Iterable

from automate_inc.core.projects import Project
from automate_inc.core.workers import Cost, Role, Worker

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
    """Sales workers make a project visible. Everything else does not."""
    assigned = [w for w in workers if w.assigned_to == project.id and w.role is Role.SALES]
    return sum(SALES_VISIBILITY_BONUS * w.efficiency for w in assigned)


def project_income(project: Project, workers: Iterable[Worker]) -> float:
    workers = list(workers)
    return calculate_income(
        base_income=project.base_income,
        quality=project.quality,
        aesthetics=project.aesthetics,
        bugs=project.bugs,
        visibility_bonus=visibility_bonus_for(project, workers),
        aesthetics_applies=project.requires(Role.DESIGNER),
    )


def project_costs(project: Project, workers: Iterable[Worker]) -> Cost:
    """Fixed costs plus everyone assigned to this project."""
    total = Cost(money=float(project.basis_fixed_costs))
    for worker in workers:
        if worker.assigned_to == project.id:
            total = total + worker.cost_per_round()
    return total


def idle_worker_costs(workers: Iterable[Worker]) -> Cost:
    """Workers without an assignment still get paid. Payroll does not pause."""
    total = Cost()
    for worker in workers:
        if worker.assigned_to is None:
            total = total + worker.cost_per_round()
    return total


def next_token_price(price: float, rng: random.Random) -> float:
    swing = rng.uniform(1.0 - TOKEN_PRICE_SWING, 1.0 + TOKEN_PRICE_SWING)
    return round(price * swing * TOKEN_PRICE_INFLATION, 2)
