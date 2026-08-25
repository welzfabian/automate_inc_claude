"""M5: office capacity for human workers, and the investor-equity income drag."""

from __future__ import annotations

import pytest

from _helpers import NO_EVENTS, advance
from automate_inc import strings as S
from automate_inc.core.game import (
    INVESTOR_EQUITY_CAP,
    INVESTOR_EQUITY_STEP,
    INVESTOR_FUNDING_AMOUNT,
    OFFICE_EXPANSION_BASE_COST,
    OFFICE_EXPANSION_GROWTH,
    OFFICE_EXPANSION_STEP,
    Game,
)
from automate_inc.core.state import START_INVESTOR_EQUITY, START_OFFICE_CAPACITY
from automate_inc.core.workers import Role, WorkerType

# -- office capacity -----------------------------------------------------


def _game_with_a_full_office() -> Game:
    game = Game(seed=1)
    for _ in range(START_OFFICE_CAPACITY):
        game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    return game


def test_hiring_a_human_beyond_capacity_is_refused():
    game = _game_with_a_full_office()
    result = game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    assert not result.ok
    assert result.message == S.ERR_OFFICE_FULL.format(capacity=START_OFFICE_CAPACITY)


def test_a_full_human_office_does_not_block_agents():
    game = _game_with_a_full_office()
    result = game.hire_worker(Role.DEVELOPER, WorkerType.AGENT)
    assert result.ok


def test_expanding_the_office_raises_capacity_by_the_fixed_step():
    game = Game(seed=1)
    before = game.state.office_capacity
    game.expand_office()
    assert game.state.office_capacity == before + OFFICE_EXPANSION_STEP


def test_expansion_unblocks_the_next_hire():
    game = _game_with_a_full_office()
    game.expand_office()
    assert game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN).ok


def test_each_expansion_costs_more_than_the_last():
    game = Game(seed=1)
    game.state.money = 1_000_000.0
    first_cost = game.office_expansion_cost()
    assert first_cost == pytest.approx(OFFICE_EXPANSION_BASE_COST)
    game.expand_office()
    second_cost = game.office_expansion_cost()
    assert second_cost == pytest.approx(OFFICE_EXPANSION_BASE_COST * OFFICE_EXPANSION_GROWTH)


def test_expand_office_deducts_its_cost():
    game = Game(seed=1)
    game.state.money = 1_000_000.0
    before = game.state.money
    cost = game.office_expansion_cost()
    game.expand_office()
    assert game.state.money == pytest.approx(before - cost)


# -- investor funding ------------------------------------------------------


def test_a_fresh_game_already_owes_investors_the_seed_equity():
    """The starting money was a seed round, not savings - M5 addendum."""
    game = Game(seed=1)
    assert game.state.investor_equity == pytest.approx(START_INVESTOR_EQUITY)


def test_raise_funding_grants_money_and_equity():
    game = Game(seed=1)
    before_money = game.state.money
    before_equity = game.state.investor_equity
    result = game.raise_funding()
    assert result.ok
    assert game.state.money == pytest.approx(before_money + INVESTOR_FUNDING_AMOUNT)
    assert game.state.investor_equity == pytest.approx(before_equity + INVESTOR_EQUITY_STEP)


def test_raise_funding_is_refused_at_the_cap():
    game = Game(seed=1)
    game.state.investor_equity = INVESTOR_EQUITY_CAP
    result = game.raise_funding()
    assert not result.ok
    assert result.message == S.ERR_EQUITY_CAP.format(cap=INVESTOR_EQUITY_CAP)


def test_equity_never_exceeds_the_cap_even_near_the_boundary():
    game = Game(seed=1)
    game.state.investor_equity = INVESTOR_EQUITY_CAP - 1.0
    game.raise_funding()
    assert game.state.investor_equity == INVESTOR_EQUITY_CAP


def test_investor_payout_is_a_share_of_net_profit_not_revenue():
    """Deliberately net, not gross - see ``Game._pay_investors``: a flat cut of
    revenue would tax full staffing harder than partial in absolute terms and
    could overturn the thin margins ``test_service_level.py`` depends on."""
    game = Game(seed=5, event_registry=NO_EVENTS)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    game.start_project("static_website")
    game.assign_worker(game.state.workers[0].id, game.state.active_projects[0].id)
    for _ in range(5):  # let service level ramp up so the round nets a profit
        advance(game)
    game.raise_funding()
    report = advance(game)
    net = report.income - report.costs_money
    assert net > 0
    equity = START_INVESTOR_EQUITY + INVESTOR_EQUITY_STEP
    assert report.investor_payout == pytest.approx(net * equity / 100)
    expected_after = report.money_before + net - report.investor_payout
    assert game.state.money == pytest.approx(expected_after)


def test_no_payout_on_a_loss_making_round():
    game = Game(seed=5, event_registry=NO_EVENTS)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)  # cost, no project: pure loss
    report = advance(game)
    assert report.investor_payout == 0.0


def test_investor_payout_is_a_named_report_line():
    game = Game(seed=5, event_registry=NO_EVENTS)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    game.start_project("static_website")
    game.assign_worker(game.state.workers[0].id, game.state.active_projects[0].id)
    for _ in range(5):
        advance(game)
    report = advance(game)
    assert any("Investoren-Anteil" in event for event in report.events)


def test_no_investor_payout_line_without_equity():
    game = Game(seed=5, event_registry=NO_EVENTS)
    game.state.investor_equity = 0.0
    report = advance(game)
    assert report.investor_payout == 0.0
    assert not any("Investoren-Anteil" in event for event in report.events)
