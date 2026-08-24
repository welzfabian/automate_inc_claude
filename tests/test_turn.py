"""Turn resolution: worker effects, settlement, lifecycles and endings."""

import pytest

from automate_inc.core import economy
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


def test_a_new_company_is_in_the_buildup_phase():
    assert Game(seed=1).phase is Phase.BUILDUP


def test_turns_alone_never_change_the_phase():
    """The phase describes what you did, not how long you took."""
    game = Game(seed=1)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    for _ in range(15):
        game.resolve_turn()
    assert game.phase is Phase.BUILDUP


def test_researching_agent_level_two_starts_the_scaling_phase():
    game = Game(seed=1)
    game.state.research = 500
    assert game.research("ai_intelligence_2").ok
    assert game.phase is Phase.SCALING


def test_enough_agents_scale_the_company_without_any_research():
    """Three agents is scaling - as long as there are still people around them."""
    game = Game(seed=1)
    for _ in range(3):
        game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
        game.hire_worker(Role.DEVELOPER, WorkerType.AGENT)
    assert game.phase is Phase.SCALING


def test_agents_outnumbering_humans_means_autonomy():
    game = Game(seed=1)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    for _ in range(6):
        game.hire_worker(Role.DEVELOPER, WorkerType.AGENT)
    assert game.phase is Phase.AUTONOMY


def test_a_single_agent_in_an_empty_company_is_not_autonomy():
    """Outnumbering only counts once there is a fleet to outnumber with."""
    game = Game(seed=1)
    game.hire_worker(Role.DEVELOPER, WorkerType.AGENT)
    assert game.phase is Phase.BUILDUP


def test_a_small_agent_team_beside_a_founder_is_only_scaling():
    """Three agents and one human is a lean company, not an autonomous one."""
    game = Game(seed=1)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    for _ in range(3):
        game.hire_worker(Role.DEVELOPER, WorkerType.AGENT)
    assert game.phase is Phase.SCALING


def test_falling_alignment_alone_means_autonomy():
    game = Game(seed=1)
    game.state.alignment = 40.0
    assert game.phase is Phase.AUTONOMY


def scaled_company(seed=1) -> Game:
    """Three agents and three humans: scaling, but not yet outnumbered."""
    game = Game(seed=seed)
    for _ in range(3):
        game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
        game.hire_worker(Role.DEVELOPER, WorkerType.AGENT)
    return game


def test_the_phase_falls_back_when_the_agents_are_fired():
    """Deliberate: the phase is recomputed, never remembered."""
    game = scaled_company()
    assert game.phase is Phase.SCALING
    for worker in [w for w in game.state.workers if not w.is_human]:
        game.fire_worker(worker.id)
    assert game.phase is Phase.BUILDUP


def test_phase_change_is_reported():
    game = scaled_company()
    report = game.resolve_turn()
    assert any("Skalierung" in event for event in report.events)


def test_falling_back_a_phase_reads_differently_from_advancing():
    game = scaled_company()
    game.resolve_turn()
    for worker in [w for w in game.state.workers if not w.is_human]:
        game.fire_worker(worker.id)
    report = game.resolve_turn()
    assert any("Zurück in Phase" in event for event in report.events)


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


# -- agent side effects (M2) -------------------------------------------------


# A project that actually asks for the role under test - assigning a worker to a
# project that does not want it is refused, and then nothing would be measured.
BLUEPRINT_FOR = {
    Role.DEVELOPER: "static_website",
    Role.DESIGNER: "ecommerce_shop",
    Role.SALES: "mobile_app",
    Role.RESEARCHER: "static_website",
}


def agent_game(role=Role.DEVELOPER, level=2, seed=6, lifetime=100) -> Game:
    """One agent of the given level on one long-running project.

    A throwaway human starts the project and is fired immediately: a company of
    nothing but level 1 agents cannot start one (BALANCING.md 1), and the test
    needs exactly one worker left so that there is exactly one RNG draw per turn.
    """
    game = Game(seed=seed)
    game.state.research = 500
    game.research("ai_intelligence_2")
    if level >= 3:
        game.research("ai_intelligence_3")
    game.state.research = 0

    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    starter = game.state.workers[0]
    assert game.start_project(BLUEPRINT_FOR[role]).ok
    assert game.fire_worker(starter.id).ok

    game.hire_worker(role, WorkerType.AGENT, level)
    project = game.state.active_projects[0]
    project.lifetime = lifetime
    game.assign_worker(game.state.workers[0].id, project.id)
    return game


def run_solvent(game: Game, turns: int) -> list[str]:
    """Resolve turns while keeping the books topped up.

    These tests are about side effects, not about the economy; bankruptcy would
    end the game and cut the sample short.
    """
    events: list[str] = []
    for _ in range(turns):
        game.state.money = 100_000.0
        game.state.tokens = 10_000.0
        events.extend(game.resolve_turn().events)
    return events


def test_level_one_agents_still_have_no_side_effects():
    game = agent_game(level=1, seed=6)
    project = game.state.active_projects[0]
    run_solvent(game, 40)
    assert project.bugs == 0.0


def test_a_level_two_developer_agent_introduces_bugs():
    game = agent_game(level=2, seed=6)
    project = game.state.active_projects[0]
    run_solvent(game, 40)
    assert project.bugs > 0.0


def test_bug_fixing_research_halves_the_rate():
    """Level 3 fails often enough (5 %) to make the halving visible in 40 turns."""
    plain = agent_game(level=3, seed=6)
    with_fix = agent_game(level=3, seed=6)
    with_fix.state.research = 35
    assert with_fix.research("bug_fixing").ok

    plain_events = [e for e in run_solvent(plain, 40) if "Edge Case" in e]
    fixed_events = [e for e in run_solvent(with_fix, 40) if "Edge Case" in e]
    assert len(plain_events) == 5
    assert len(fixed_events) == 2


def test_a_sales_agent_costs_money_when_it_oversells():
    game = agent_game(role=Role.SALES, level=3, seed=6)
    events = run_solvent(game, 40)
    assert any("Schadensbegrenzung" in event for event in events)


def test_a_researcher_agent_can_waste_research_points():
    game = agent_game(role=Role.RESEARCHER, level=3, seed=6)
    events = run_solvent(game, 40)
    assert any("Sackgasse" in event for event in events)


def test_research_points_never_go_negative():
    game = agent_game(role=Role.RESEARCHER, level=3, seed=6)
    run_solvent(game, 40)
    assert game.state.research >= 0


# -- designer staleness (M2) -------------------------------------------------


def visibility(game: Game) -> float:
    project = game.state.active_projects[0]
    return economy.visibility_bonus_for(project, game.state.workers)


def test_a_designer_agent_goes_generic_after_five_rounds():
    game = agent_game(role=Role.DESIGNER, level=2, seed=6)
    assert visibility(game) == 0.0
    run_solvent(game, 4)
    assert visibility(game) == 0.0
    run_solvent(game, 1)
    assert visibility(game) == -5.0


def test_the_staleness_penalty_scales_with_the_agent_level():
    game = agent_game(role=Role.DESIGNER, level=3, seed=6)
    run_solvent(game, 5)
    assert visibility(game) == -10.0


def test_human_designers_never_go_stale():
    game = Game(seed=6)
    game.hire_worker(Role.DESIGNER, WorkerType.HUMAN)
    assert game.start_project("ecommerce_shop").ok
    project = game.state.active_projects[0]
    project.lifetime = 100
    game.assign_worker(game.state.workers[0].id, project.id)
    run_solvent(game, 10)
    assert visibility(game) == 0.0


def test_reassignment_resets_the_staleness_counter():
    game = agent_game(role=Role.DESIGNER, level=2, seed=6)
    run_solvent(game, 6)
    assert visibility(game) == -5.0
    worker = game.state.workers[0]
    project = game.state.active_projects[0]
    assert game.unassign_worker(worker.id).ok
    assert worker.rounds_in_assignment == 0
    assert game.assign_worker(worker.id, project.id).ok
    assert visibility(game) == 0.0


# -- what the assignment menu may offer --------------------------------------


def test_free_slots_counts_down_as_the_posts_fill():
    game = Game(seed=2)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    game.start_project("web_app")                      # 2x Entwickler, 1x Designer
    project = game.state.active_projects[0]
    assert game.free_slots(project, Role.DEVELOPER) == 2
    game.assign_worker(game.state.workers[0].id, project.id)
    assert game.free_slots(project, Role.DEVELOPER) == 1


def test_a_role_the_project_never_asked_for_has_no_slots():
    game = Game(seed=2)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    game.start_project("static_website")               # only a developer
    assert game.free_slots(game.state.active_projects[0], Role.SALES) == 0


def test_projects_needing_a_role_skips_the_ones_that_do_not():
    game = Game(seed=2)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    game.start_project("static_website")               # no designer
    game.start_project("ecommerce_shop")               # wants one
    needing = game.projects_needing(Role.DESIGNER)
    assert [p.blueprint_id for p in needing] == ["ecommerce_shop"]


def test_a_project_drops_off_the_list_once_its_posts_are_filled():
    game = Game(seed=2)
    game.hire_worker(Role.DESIGNER, WorkerType.HUMAN)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    game.start_project("ecommerce_shop")
    project = game.state.active_projects[0]
    assert game.projects_needing(Role.DESIGNER) == [project]
    designer = next(w for w in game.state.workers if w.role is Role.DESIGNER)
    assert game.assign_worker(designer.id, project.id).ok
    assert game.projects_needing(Role.DESIGNER) == []


def test_everything_the_menu_offers_is_actually_accepted():
    """The point of putting the rule in the engine: the two cannot drift apart."""
    game = Game(seed=2)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    for blueprint_id in ("static_website", "ecommerce_shop", "mobile_app", "web_app"):
        game.start_project(blueprint_id)
    for role in Role:
        game.hire_worker(role, WorkerType.HUMAN)
        worker = game.state.workers[-1]
        for project in game.projects_needing(role):
            assert game.assign_worker(worker.id, project.id).ok
