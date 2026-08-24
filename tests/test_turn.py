"""Turn resolution: worker effects, settlement, lifecycles and endings."""

import pytest

from automate_inc.core.game import Game
from automate_inc.core.state import GameState, Phase
from automate_inc.core.workers import Role, WorkerType


def staffed_game(blueprint_id="static_website", worker_type=WorkerType.HUMAN, seed=5) -> Game:
    game = Game(seed=seed)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    game.start_project(blueprint_id)
    project_id = game.state.active_projects[0].id
    blueprint = game.registry.get(blueprint_id)
    if worker_type is WorkerType.AGENT:
        game.fire_worker(game.state.workers[0].id)
    have: dict[Role, int] = {}
    for worker in game.state.workers:
        have[worker.role] = have.get(worker.role, 0) + 1
    for role, count in blueprint.required_roles.items():
        for _ in range(count - have.get(role, 0)):
            game.hire_worker(role, worker_type)
    for worker in game.state.workers:
        game.assign_worker(worker.id, project_id)
    return game


def test_developer_raises_quality_and_it_is_capped_at_100():
    game = staffed_game()
    project = game.state.active_projects[0]
    for _ in range(10):
        game.resolve_turn()
    assert project.quality == 100.0


def test_researcher_produces_research_points_without_a_project():
    game = Game(seed=1)
    game.hire_worker(Role.RESEARCHER, WorkerType.HUMAN)
    game.resolve_turn()
    assert game.state.research == 2


def test_agents_are_more_efficient_than_humans():
    human = staffed_game(worker_type=WorkerType.HUMAN)
    agent = staffed_game(worker_type=WorkerType.AGENT)
    human.resolve_turn()
    agent.resolve_turn()
    assert agent.state.active_projects[0].quality > human.state.active_projects[0].quality


def test_project_expires_after_its_lifetime_and_frees_its_workers():
    game = staffed_game()
    lifetime = game.state.active_projects[0].lifetime
    for _ in range(lifetime):
        game.resolve_turn()
    assert game.state.active_projects == []
    assert all(w.assigned_to is None for w in game.state.workers)


def test_tokens_are_auto_bought_when_the_balance_runs_dry():
    game = staffed_game(worker_type=WorkerType.AGENT)
    game.state.tokens = 1.0
    report = game.resolve_turn()
    assert report.tokens_auto_bought > 0
    assert report.auto_buy_cost > 0
    assert game.state.tokens == 0.0


def test_bankruptcy_ends_the_game():
    game = Game(seed=1)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)  # 80 EUR/round, no income
    game.state.money = 10.0
    report = game.resolve_turn()
    assert game.state.is_over
    assert "BANKROTT" in (game.state.game_over_reason or "")
    assert any("BANKROTT" in event for event in report.events)


def test_actions_are_refused_once_the_game_is_over():
    game = Game(seed=1)
    game.state.game_over_reason = "vorbei"
    assert not game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN).ok
    assert not game.start_project("static_website").ok
    assert not game.buy_tokens(5).ok


def test_phases_follow_the_turn_counter():
    assert Phase.for_turn(0) is Phase.BUILDUP
    assert Phase.for_turn(4) is Phase.BUILDUP
    assert Phase.for_turn(5) is Phase.SCALING
    assert Phase.for_turn(9) is Phase.SCALING
    assert Phase.for_turn(10) is Phase.AUTONOMY


def test_phase_change_is_reported():
    game = Game(seed=1)
    game.state.turn = 4
    report = game.resolve_turn()
    assert any("Skalierung" in event for event in report.events)


def test_turn_resolution_is_deterministic_for_a_given_seed():
    first = staffed_game(seed=99)
    second = staffed_game(seed=99)
    for _ in range(8):
        first.resolve_turn()
        second.resolve_turn()
    assert first.state.to_dict() == second.state.to_dict()


def test_buying_tokens_costs_money_at_the_current_price():
    game = Game(seed=1)
    game.state.token_price = 12.5
    assert game.buy_tokens(4).ok
    assert game.state.tokens == pytest.approx(54.0)
    assert game.state.money == pytest.approx(950.0)


def test_buying_more_tokens_than_you_can_afford_is_refused():
    game = Game(seed=1)
    result = game.buy_tokens(10_000)
    assert not result.ok
    assert game.state.tokens == GameState().tokens
