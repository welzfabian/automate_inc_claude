"""Income and cost formulas, checked against PROJECTS_AND_PRODUCTS_SPEC.md."""

import random

import pytest

from automate_inc.core import economy
from automate_inc.core.projects import Project, ProjectType, load_tuning
from automate_inc.core.workers import Role, Worker, WorkerType, load_roles


def test_spec_example_web_app_income():
    """SPEC 6.1: 200 * 0.90 * 0.80 * 0.90 * 1.50 = 194.40, on a finished project."""
    income = economy.calculate_income(
        base_income=200, progress=100, quality=90, aesthetics=80, bugs=10, visibility_bonus=50
    )
    assert income == pytest.approx(194.40)


def test_spec_example_saas_income():
    """SPEC 6.1: 200 * 0.95 * 1.00 * 1.00 * 1.30 = 247.00, on a finished project."""
    income = economy.calculate_income(
        base_income=200, progress=100, quality=95, aesthetics=100, bugs=0, visibility_bonus=30
    )
    assert income == pytest.approx(247.00)


def test_an_unbuilt_project_earns_nothing():
    """The reason an unstaffed project is no longer free money."""
    assert economy.calculate_income(
        base_income=200, progress=0, quality=100, aesthetics=100, bugs=0, visibility_bonus=0
    ) == 0.0


def test_income_scales_linearly_with_progress():
    half = economy.calculate_income(
        base_income=200, progress=50, quality=100, aesthetics=100, bugs=0, visibility_bonus=0
    )
    full = economy.calculate_income(
        base_income=200, progress=100, quality=100, aesthetics=100, bugs=0, visibility_bonus=0
    )
    assert half == pytest.approx(full / 2)


def test_project_without_designer_is_not_punished_for_aesthetics():
    """A project that never asked for a designer must not be zeroed by aesthetics.

    This is the deliberate deviation from the written formula; without it a
    static website earns nothing forever.
    """
    with_aesthetics = economy.calculate_income(
        base_income=100, progress=100, quality=100, aesthetics=0, bugs=0, visibility_bonus=0
    )
    neutral = economy.calculate_income(
        base_income=100,
        progress=100,
        quality=100,
        aesthetics=0,
        bugs=0,
        visibility_bonus=0,
        aesthetics_applies=False,
    )
    assert with_aesthetics == 0.0
    assert neutral == pytest.approx(100.0)


def test_bugs_reduce_income():
    clean = economy.calculate_income(100, 100, 100, 100, bugs=0, visibility_bonus=0)
    buggy = economy.calculate_income(100, 100, 100, 100, bugs=40, visibility_bonus=0)
    assert buggy == pytest.approx(clean * 0.6)


def _project(**overrides) -> Project:
    defaults = dict(
        id="p1",
        blueprint_id="web_app",
        name="Web-App",
        project_type=ProjectType.WEB_APP,
        required_roles={Role.DEVELOPER: 2, Role.DESIGNER: 1},
        base_income=270,
        basis_fixed_costs=20,
        lifetime=12,
    )
    return Project(**{**defaults, **overrides})


def test_project_costs_split_money_and_tokens():
    """SPEC 6.2: fixed costs + sum of worker costs, in the right currency."""
    project = _project()
    workers = [
        Worker(id="a1", role=Role.DEVELOPER, worker_type=WorkerType.AGENT, assigned_to="p1"),
        Worker(id="a2", role=Role.DEVELOPER, worker_type=WorkerType.AGENT, assigned_to="p1"),
        Worker(id="a3", role=Role.DESIGNER, worker_type=WorkerType.AGENT, assigned_to="p1"),
    ]
    cost = economy.project_costs(project, workers)
    assert cost.money == 20.0  # only the fixed costs; agents never cost euros directly
    assert cost.tokens == 3 + 3 + 2


def test_human_workers_cost_money_not_tokens():
    project = _project(basis_fixed_costs=0)
    human = Worker(id="h1", role=Role.DEVELOPER, worker_type=WorkerType.HUMAN, assigned_to="p1")
    cost = economy.project_costs(project, [human])
    assert cost.money == 80.0
    assert cost.tokens == 0.0


def test_unassigned_workers_still_cost():
    """Payroll does not pause because someone has nothing to do."""
    idle = Worker(id="h1", role=Role.DEVELOPER, worker_type=WorkerType.HUMAN)
    assert economy.idle_worker_costs([idle]).money == 80.0


def test_sales_worker_adds_visibility():
    project = _project(required_roles={Role.SALES: 1})
    sales = Worker(id="s1", role=Role.SALES, worker_type=WorkerType.HUMAN, assigned_to="p1")
    assert economy.visibility_bonus_for(project, [sales]) == pytest.approx(
        load_tuning().sales_visibility_bonus
    )


def test_the_sales_post_pays_for_itself():
    """It did not at 10 %: the salary cost more than the bonus was worth."""
    project = _project(required_roles={Role.SALES: 1}, base_income=246, basis_fixed_costs=10)
    sales = Worker(id="s1", role=Role.SALES, worker_type=WorkerType.HUMAN, assigned_to="p1")
    bonus_value = project.base_income * load_tuning().sales_visibility_bonus / 100
    assert bonus_value > load_roles().spec(Role.SALES).human_salary


def test_token_price_stays_within_swing_and_drifts_up():
    rng = random.Random(1)
    prices = []
    price = 10.0
    for _ in range(200):
        new_price = economy.next_token_price(price, rng)
        assert 0.89 * price <= new_price <= 1.12 * price
        price = new_price
        prices.append(price)
    # Inflation means the long-run trend is upward.
    assert sum(prices[-20:]) > sum(prices[:20])
