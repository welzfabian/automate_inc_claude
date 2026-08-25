"""Cross-cutting rules that hold for every guarded player action alike.

Individual action mechanics (which role can be hired, what a project needs,
what research unlocks) live in their own test files. This one checks the two
invariants CLAUDE.md calls out as load-bearing for the whole action layer:
a failed action must leave the state byte-identical, and no action works
once the game is over - across the full set of guarded actions, not just one
representative case.
"""

import pytest

from automate_inc import strings as S
from automate_inc.core.game import INVESTOR_EQUITY_CAP, MAX_AGENT_LEVEL, Game
from automate_inc.core.workers import Role, Worker, WorkerType

# -- refused once the game is over --------------------------------------------
#
# The guard is checked before an action looks at its arguments, so any
# plausible-looking call demonstrates it - the placeholder ids below are
# never resolved.

GUARDED_CALLS = [
    pytest.param(lambda g: g.hire_worker(Role.DEVELOPER, WorkerType.HUMAN), id="hire_worker"),
    pytest.param(lambda g: g.fire_worker("w_1"), id="fire_worker"),
    pytest.param(lambda g: g.start_project("static_website"), id="start_project"),
    pytest.param(lambda g: g.assign_worker("w_1", "p_1"), id="assign_worker"),
    pytest.param(lambda g: g.unassign_worker("w_1"), id="unassign_worker"),
    pytest.param(lambda g: g.research("efficient_development"), id="research"),
    pytest.param(lambda g: g.upgrade_agent("w_1"), id="upgrade_agent"),
    pytest.param(lambda g: g.buy_tokens(5), id="buy_tokens"),
    pytest.param(lambda g: g.answer_event("e_1", "opt_1"), id="answer_event"),
    pytest.param(lambda g: g.expand_office(), id="expand_office"),
    pytest.param(lambda g: g.raise_funding(), id="raise_funding"),
]


@pytest.mark.parametrize("call", GUARDED_CALLS)
def test_actions_are_refused_once_the_game_is_over(call):
    game = Game(seed=1)
    game.state.game_over_reason = "vorbei"
    result = call(game)
    assert not result.ok
    assert result.message == S.ERR_GAME_OVER


# -- failed actions leave the state untouched ---------------------------------
#
# One realistic validation failure per action, chosen to be distinct from the
# "unknown id" case already covered elsewhere so the matrix exercises a
# variety of guard clauses, not the same one nine times.


def _fresh_game() -> Game:
    return Game(seed=1)


def _broke_game() -> Game:
    game = Game(seed=1)
    game.state.money = 0.0
    return game


def _staffed_game() -> Game:
    game = Game(seed=1)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    return game


def _game_with_an_assigned_worker() -> Game:
    game = Game(seed=1)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    game.start_project("static_website")
    project_id = game.state.active_projects[0].id
    game.assign_worker(game.state.workers[0].id, project_id)
    return game


def _game_with_a_maxed_agent() -> Game:
    game = Game(seed=1)
    game.state.workers.append(
        Worker(id="w_max", role=Role.DEVELOPER, worker_type=WorkerType.AGENT, level=MAX_AGENT_LEVEL)
    )
    return game


def _game_at_the_equity_cap() -> Game:
    game = Game(seed=1)
    game.state.investor_equity = INVESTOR_EQUITY_CAP
    return game


def _broke_game_with_an_upgradeable_agent() -> Game:
    """A level-1 agent with level 2 already researched, so the only thing
    stopping the upgrade is money - not the research-lock check upgrade_agent
    runs first."""
    game = Game(seed=1)
    game.state.research = 500
    game.research("ai_intelligence_2")
    game.state.workers.append(
        Worker(id="w_agent", role=Role.DEVELOPER, worker_type=WorkerType.AGENT, level=1)
    )
    game.state.money = 0.0
    return game


FAILURE_CASES = [
    pytest.param(
        _broke_game,
        lambda g: g.hire_worker(Role.DEVELOPER, WorkerType.HUMAN),
        id="hire_worker_insufficient_money",
    ),
    pytest.param(_fresh_game, lambda g: g.fire_worker("nope"), id="fire_worker_unknown_worker"),
    pytest.param(
        _staffed_game,
        lambda g: g.start_project("does_not_exist"),
        id="start_project_unknown_blueprint",
    ),
    pytest.param(
        _game_with_an_assigned_worker,
        lambda g: g.assign_worker(g.state.workers[0].id, g.state.active_projects[0].id),
        id="assign_worker_already_assigned",
    ),
    pytest.param(
        _staffed_game,
        lambda g: g.unassign_worker(g.state.workers[0].id),
        id="unassign_worker_not_assigned",
    ),
    pytest.param(
        _fresh_game,
        lambda g: g.research("efficient_development"),
        id="research_insufficient_points",
    ),
    pytest.param(
        _game_with_a_maxed_agent,
        lambda g: g.upgrade_agent("w_max"),
        id="upgrade_agent_at_max_level",
    ),
    pytest.param(
        _broke_game_with_an_upgradeable_agent,
        lambda g: g.upgrade_agent("w_agent"),
        id="upgrade_agent_insufficient_money",
    ),
    pytest.param(_fresh_game, lambda g: g.buy_tokens(0), id="buy_tokens_invalid_amount"),
    pytest.param(
        _fresh_game, lambda g: g.answer_event("nope", "nope"), id="answer_event_unknown_decision"
    ),
    pytest.param(_broke_game, lambda g: g.expand_office(), id="expand_office_insufficient_money"),
    pytest.param(
        _game_at_the_equity_cap, lambda g: g.raise_funding(), id="raise_funding_at_cap"
    ),
]


@pytest.mark.parametrize("build, call", FAILURE_CASES)
def test_failed_action_leaves_state_untouched(build, call):
    game = build()
    before = game.state.to_dict()
    result = call(game)
    assert not result.ok
    assert game.state.to_dict() == before
