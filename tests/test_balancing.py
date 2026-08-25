"""The balancing rules of BALANCING.md, as executable checks.

``tools/simulate.py`` measures the balance and asserts nothing about it - that
separation is deliberate (CLAUDE.md). This file is the other half: the rules
that must hold for *every* entry in ``data/*.json``, checked directly instead of
played out, so that adding a twelfth blueprint cannot quietly break one.

Two kinds of test live here and they are labelled as such:

- **Garantien** - properties the design promises. They must stay green.
- **Befunde** - known open points from BALANCING.md, pinned to what they
  currently do. They are *expected* to fail once the point is resolved; each
  one names the entry that decides it.
"""

import pytest

from _helpers import NO_EVENTS, commission
from automate_inc.core.game import Game
from automate_inc.core.projects import ProjectBlueprint, load_registry, load_tuning
from automate_inc.core.workers import Role, WorkerType

REGISTRY = load_registry()
TUNING = load_tuning()

BLUEPRINT_IDS = [bp.id for bp in REGISTRY.all()]

DEVELOPER_FLOOR = 160.0
DESIGNER_FLOOR = 140.0
SALES_FLOOR = 240.0
"""BALANCING.md 33. A post costs its salary and lifts the attribute cap by
``(100 - attribute_cap_base) / n``; the floors are what makes losing the post
cost more than the salary saves. Sales holds no attribute - its floor is the
point at which 25 % visibility outearns a 60 € salary."""

HUMAN_WALL_POSTS = 6
"""BALANCING.md 34: at six posts a human team still clears a margin, from seven
it pays to work. Set through ``basis_fixed_costs``, never through income - see
the floors above, which forbid the other lever."""

STEADY_ROUNDS = 8
"""Long enough for quality, aesthetics and the service level to reach their caps."""


def visibility(blueprint: ProjectBlueprint) -> float:
    sales = blueprint.required_roles.get(Role.SALES, 0)
    return 1.0 + sales * TUNING.sales_visibility_bonus / 100.0


def posts(blueprint: ProjectBlueprint) -> int:
    return sum(blueprint.required_roles.values())


def steady_state(blueprint_id: str, kind: WorkerType, level: int, price: float = 10.0):
    """Income and costs per round once the attributes have settled.

    The same measurement ``tools/simulate.py --steady`` prints, rebuilt here
    because the tools directory is not on the test path. Events off and the
    token price pinned, so the result is a property of ``data/*.json`` alone.

    A level-1 fleet has nobody answerable for the project (BALANCING.md 24), so
    the cheapest *real* level-1 team is one human on the first post plus agents
    on the rest - which is what ``kind``/``level`` below 2 produces.
    """
    game = Game(seed=1, event_registry=NO_EVENTS)
    game.state.research = 500
    assert game.research("ai_intelligence_2").ok
    assert game.research("ai_intelligence_3").ok
    game.state.research = 0
    game.state.money = 1e9
    game.state.tokens = 1e9
    game.state.investor_equity = 0.0
    game.state.office_capacity = 99

    blueprint = REGISTRY.get(blueprint_id)
    assert blueprint is not None
    # The senior has to hold a post this blueprint actually asks for - the
    # ladder has jobs with no developer on them.
    senior_role = next(iter(blueprint.required_roles))
    if kind is WorkerType.AGENT and level >= 2:
        assert game.hire_worker(senior_role, WorkerType.AGENT, level).ok
    else:
        assert game.hire_worker(senior_role, WorkerType.HUMAN).ok
    assert commission(game, blueprint_id).ok
    project = game.state.active_projects[0]
    assert game.assign_worker(game.state.workers[-1].id, project.id).ok
    for role in list(project.required_roles):
        for _ in range(game.free_slots(project, role)):
            assert game.hire_worker(role, kind, level).ok
            assert game.assign_worker(game.state.workers[-1].id, project.id).ok

    report = None
    for _ in range(STEADY_ROUNDS):
        game.state.token_price = price
        report = game.resolve_turn()
    assert report is not None
    return report.income, report.costs_money + report.costs_tokens * price


def steady_net(blueprint_id: str, kind: WorkerType, level: int) -> float:
    income, costs = steady_state(blueprint_id, kind, level)
    return income - costs


# -- Garantien: die Untergrenzen aus Nr. 33 ----------------------------------


@pytest.mark.parametrize("blueprint_id", BLUEPRINT_IDS)
def test_every_blueprint_meets_the_income_floors(blueprint_id):
    """BALANCING.md 33, checked as arithmetic rather than played out.

    ``test_full_staffing_beats_every_partial_staffing`` already checks the
    *consequence* by simulating every staffing of every job, which is slow and
    tells you only that something broke. This checks the rule itself, so a new
    ``base_income`` fails on the line that names the number it has to clear.
    """
    blueprint = REGISTRY.get(blueprint_id)
    if posts(blueprint) == 1:
        pytest.skip("one-post jobs are the documented exception - see below")
    earned = blueprint.base_income * visibility(blueprint)
    developers = blueprint.required_roles.get(Role.DEVELOPER, 0)
    designers = blueprint.required_roles.get(Role.DESIGNER, 0)
    if developers:
        assert earned > DEVELOPER_FLOOR * developers
    if designers:
        assert earned > DESIGNER_FLOOR * designers
    if blueprint.required_roles.get(Role.SALES, 0):
        assert blueprint.base_income > SALES_FLOOR


@pytest.mark.parametrize(
    "blueprint_id", [bp.id for bp in REGISTRY.all() if sum(bp.required_roles.values()) == 1]
)
def test_a_one_post_job_only_has_to_beat_its_own_salary(blueprint_id):
    """Dropping the only post empties the project: the service level falls to 0
    and it earns nothing at all (BALANCING.md 11/24/33). The floors above are a
    comparison between two staffings and have nothing to compare here."""
    blueprint = REGISTRY.get(blueprint_id)
    role = next(iter(blueprint.required_roles))
    salary = Game(seed=1).hiring_cost(role, WorkerType.HUMAN)
    assert blueprint.base_income > salary


# -- Garantien: die Leiter ---------------------------------------------------


def test_the_ladder_is_acyclic_and_rooted():
    """Every job has to be reachable from turn 0, or it is not on the ladder."""
    reachable: set[str] = set()
    progressed = True
    while progressed:
        progressed = False
        for blueprint in REGISTRY.all():
            if blueprint.id in reachable:
                continue
            if all(required in reachable for required in blueprint.requires):
                reachable.add(blueprint.id)
                progressed = True
    assert reachable == set(BLUEPRINT_IDS)


def test_at_least_one_job_needs_nothing_at_all():
    """Otherwise the first rung is unreachable and the catalogue never opens."""
    assert any(not bp.requires for bp in REGISTRY.all())


@pytest.mark.parametrize("blueprint_id", BLUEPRINT_IDS)
def test_every_rung_is_profitable_for_at_least_one_staffing(blueprint_id):
    """A job nobody can run at a profit is a dead rung: taking it is strictly
    worse than idling, and on a ladder it also blocks everything above it."""
    nets = {
        "Mensch+Lv1": steady_net(blueprint_id, WorkerType.AGENT, 1),
        "Agent Lv2": steady_net(blueprint_id, WorkerType.AGENT, 2),
        "Agent Lv3": steady_net(blueprint_id, WorkerType.AGENT, 3),
        "Menschen": steady_net(blueprint_id, WorkerType.HUMAN, 1),
    }
    assert max(nets.values()) > 0, nets


# -- Garantien: die Menschen-Wand (Nr. 34) -----------------------------------


@pytest.mark.parametrize(
    "blueprint_id",
    [bp.id for bp in REGISTRY.all() if sum(bp.required_roles.values()) <= HUMAN_WALL_POSTS],
)
def test_a_human_team_still_clears_a_margin_up_to_the_wall(blueprint_id):
    assert steady_net(blueprint_id, WorkerType.HUMAN, 1) > 0


@pytest.mark.parametrize(
    "blueprint_id",
    [bp.id for bp in REGISTRY.all() if sum(bp.required_roles.values()) > HUMAN_WALL_POSTS],
)
def test_a_human_team_pays_to_work_past_the_wall(blueprint_id):
    """The point of M8: from seven posts up, automating is not the better
    calculation any more, it is the only one (BALANCING.md 34)."""
    assert steady_net(blueprint_id, WorkerType.HUMAN, 1) < 0


def test_the_wall_is_built_from_fixed_costs_not_from_income():
    """The floors in Nr. 33 forbid the obvious lever: a big job cannot be made
    unprofitable through ``base_income`` without breaking full-staffing-wins.
    So every job past the wall has to carry real fixed costs instead."""
    for blueprint in REGISTRY.all():
        if posts(blueprint) > HUMAN_WALL_POSTS:
            assert blueprint.basis_fixed_costs > 0


# -- Garantien: die Tuning-Konstanten ----------------------------------------


def test_the_attribute_cap_base_cannot_exceed_the_starting_value():
    """An attribute only rises through workers of its own role, so with the post
    unfilled a cap above ``attribute_start`` could never be reached - the knob
    would silently do nothing (``projects.Tuning.cap``)."""
    assert TUNING.attribute_cap_base <= TUNING.attribute_start


def test_a_full_team_reaches_the_cap_within_the_shortest_lifetime():
    """The service level has to be reachable, or the shortest jobs never pay
    what they were sold at."""
    shortest = min(bp.lifetime for bp in REGISTRY.all())
    rounds_needed = (100.0 - TUNING.service_level_start) / TUNING.service_level_build_rate
    assert rounds_needed < shortest


# -- Befunde: offene Punkte, festgenagelt ------------------------------------


@pytest.mark.parametrize("blueprint_id", BLUEPRINT_IDS)
def test_agent_level_three_is_never_the_better_buy(blueprint_id):
    """**Offener Punkt, BALANCING.md 27.** Level 3 costs 2.2x the tokens for
    1.33x the efficiency, and that efficiency buys nothing because the attribute
    caps are already reached at level 1. From level 2 up there are side effects
    on top, so income *falls* with the level.

    Pinned rather than fixed: the numbers behind it (Nr. 5, Nr. 7) are
    calibrated, and correcting it here would soften the level-1 recommendation
    of Nr. 22/24. When the open point is resolved, this test is the one that
    should go red.
    """
    assert steady_net(blueprint_id, WorkerType.AGENT, 3) < steady_net(
        blueprint_id, WorkerType.AGENT, 2
    )


def test_the_investor_dividend_is_a_true_share_of_profit_for_a_human_team():
    """The guarantee ``Game._pay_investors`` states, where it actually holds.

    A human team pays salaries, not tokens, so ``income - costs_money`` really
    is the round's profit and the reported payout really is a share of it. This
    is the case every investor test in ``test_office_and_investors.py`` uses -
    which is why the one below went unnoticed.
    """
    game = Game(seed=1, event_registry=NO_EVENTS)
    game.state.money = 1e9
    game.state.office_capacity = 99
    game.state.investor_equity = 15.0
    assert game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN).ok
    assert commission(game, "web_app").ok
    project = game.state.active_projects[0]
    assert game.assign_worker(game.state.workers[-1].id, project.id).ok
    for role in list(project.required_roles):
        for _ in range(game.free_slots(project, role)):
            assert game.hire_worker(role, WorkerType.HUMAN).ok
            assert game.assign_worker(game.state.workers[-1].id, project.id).ok
    report = None
    for _ in range(STEADY_ROUNDS):
        game.state.token_price = 10.0
        report = game.resolve_turn()

    assert report.costs_tokens == 0.0
    real_profit = report.income - report.costs_money - report.costs_tokens * 10.0
    assert report.investor_payout == pytest.approx(real_profit * 15.0 / 100)
    assert report.investor_payout < real_profit


def test_the_dividend_is_scaled_off_a_profit_that_ignores_the_token_bill():
    """**Offener Punkt, BALANCING.md 39.** ``_pay_investors`` scales the payout
    off ``income - costs_money``, and agents cost *tokens*, not money. For a
    fleet-run job the dividend is therefore a share of something close to gross
    revenue, and on the top rung it exceeds the round's real profit outright -
    which the docstring's promise ("investors take a cut of profit, not a claim
    on your deficit") says it never does.

    Pinned rather than fixed: including tokens changes what the equity mechanic
    costs on every automated path and is a balancing decision, not a typo.
    """
    income, costs = steady_state("group_ai_platform", WorkerType.AGENT, 2)
    real_profit = income - costs
    assert real_profit > 0

    game = Game(seed=1, event_registry=NO_EVENTS)
    game.state.research = 500
    assert game.research("ai_intelligence_2").ok
    game.state.money = 1e9
    game.state.tokens = 1e9
    game.state.office_capacity = 99
    assert game.hire_worker(Role.DEVELOPER, WorkerType.AGENT, 2).ok
    assert commission(game, "group_ai_platform").ok
    project = game.state.active_projects[0]
    assert game.assign_worker(game.state.workers[-1].id, project.id).ok
    for role in list(project.required_roles):
        for _ in range(game.free_slots(project, role)):
            assert game.hire_worker(role, WorkerType.AGENT, 2).ok
            assert game.assign_worker(game.state.workers[-1].id, project.id).ok
    report = None
    for _ in range(STEADY_ROUNDS):
        game.state.token_price = 10.0
        report = game.resolve_turn()

    assert report.costs_tokens > 0                       # the bill the dividend skips
    assert report.investor_payout > real_profit          # more than the round actually made
