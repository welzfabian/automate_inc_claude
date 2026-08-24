"""Alignment: deterministic by design, so the player can read cause and effect."""

import pytest

from automate_inc.core.economy import alignment_delta
from automate_inc.core.game import MISALIGNMENT_THRESHOLD, Game, alignment_tier
from automate_inc.core.state import START_ALIGNMENT
from automate_inc.core.workers import Role, WorkerType


def game_with(*, humans=0, level_1=0, level_2=0, level_3=0, seed=7) -> Game:
    game = Game(seed=seed)
    game.state.research = 500
    if level_2 or level_3:
        game.research("ai_intelligence_2")
    if level_3:
        game.research("ai_intelligence_3")
    for _ in range(humans):
        game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    for level, count in ((1, level_1), (2, level_2), (3, level_3)):
        for _ in range(count):
            game.hire_worker(Role.DEVELOPER, WorkerType.AGENT, level)
    game.state.research = 0
    return game


def delta_of(game: Game) -> float:
    return alignment_delta(game.state.workers, game.modifiers)


# -- the balance -------------------------------------------------------------


def test_an_empty_company_has_no_drift():
    assert delta_of(game_with()) == 0.0


def test_a_pure_human_team_never_loses_alignment():
    game = game_with(humans=3)
    for _ in range(10):
        game.resolve_turn()
    assert game.state.alignment == START_ALIGNMENT


def test_level_one_agents_are_harmless_by_design():
    assert delta_of(game_with(level_1=3)) == 0.0


def test_a_level_two_agent_costs_exactly_one_alignment_per_round():
    assert delta_of(game_with(level_2=1)) == pytest.approx(-1.0)


def test_a_level_three_agent_costs_exactly_three_alignment_per_round():
    assert delta_of(game_with(level_3=1)) == pytest.approx(-3.0)


def test_decay_scales_with_the_number_of_agents():
    assert delta_of(game_with(level_2=4)) == pytest.approx(-4.0)


def test_humans_slow_the_decay_but_do_not_stop_it():
    """BALANCING.md 9: +1 per human, not the +5 the docs suggest."""
    assert delta_of(game_with(humans=2, level_3=1)) == pytest.approx(-1.0)


def test_the_researcher_role_gets_no_extra_decay():
    """BALANCING.md 7: decay hangs on the level, never on the role."""
    developer = Game(seed=1)
    developer.state.research = 500
    developer.research("ai_intelligence_2")
    developer.hire_worker(Role.DEVELOPER, WorkerType.AGENT, 2)

    researcher = Game(seed=1)
    researcher.state.research = 500
    researcher.research("ai_intelligence_2")
    researcher.hire_worker(Role.RESEARCHER, WorkerType.AGENT, 2)

    assert delta_of(developer) == delta_of(researcher)


def test_ai_alignment_research_halves_the_decay():
    game = game_with(level_3=2)
    assert delta_of(game) == pytest.approx(-6.0)
    game.state.research = 50
    assert game.research("ai_alignment").ok
    assert delta_of(game) == pytest.approx(-3.0)


def test_the_dampener_scales_with_the_fleet_where_humans_do_not():
    """That is the point: it is the answer that lets you keep automating."""
    small = game_with(level_2=2)
    large = game_with(level_2=20)
    for game in (small, large):
        game.state.research = 50
        assert game.research("ai_alignment").ok
    assert delta_of(small) == pytest.approx(-1.0)
    assert delta_of(large) == pytest.approx(-10.0)


def test_the_dampener_does_not_soften_the_dangerous_technologies():
    """Their cost is structural, not a side effect of headcount."""
    game = Game(seed=4)
    game.state.research = 500
    for tech_id in ("ai_intelligence_2", "ai_intelligence_3", "autonomous_agents", "ai_alignment"):
        assert game.research(tech_id).ok
    assert delta_of(game) == pytest.approx(-3.0)


def test_dangerous_technologies_cost_alignment_even_without_agents():
    game = Game(seed=2)
    game.state.research = 500
    for tech_id in ("ai_intelligence_2", "ai_intelligence_3", "autonomous_agents"):
        assert game.research(tech_id).ok
    assert delta_of(game) == pytest.approx(-3.0)


# -- the turn loop -----------------------------------------------------------


def test_the_balance_is_applied_once_per_turn_and_reported():
    game = game_with(level_2=2)
    report = game.resolve_turn()
    assert report.alignment_delta == pytest.approx(-2.0)
    assert game.state.alignment == pytest.approx(START_ALIGNMENT - 2.0)


def test_alignment_is_capped_at_one_hundred():
    game = game_with(humans=5)
    game.resolve_turn()
    assert game.state.alignment == START_ALIGNMENT


# -- the ending --------------------------------------------------------------


def test_falling_below_the_threshold_ends_the_game():
    game = game_with(level_3=1)
    game.state.alignment = MISALIGNMENT_THRESHOLD + 1
    report = game.resolve_turn()
    assert game.state.is_over
    assert "KONTROLLVERLUST" in game.state.game_over_reason
    assert game.state.game_over_reason in report.events


def test_staying_at_the_threshold_does_not_end_the_game():
    game = game_with(humans=1)
    game.state.alignment = MISALIGNMENT_THRESHOLD
    game.resolve_turn()
    assert not game.state.is_over


def test_actions_are_refused_once_alignment_ended_the_game():
    game = game_with(level_3=1)
    game.state.alignment = MISALIGNMENT_THRESHOLD
    game.resolve_turn()
    assert game.state.is_over
    assert not game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN).ok


# -- tone --------------------------------------------------------------------


def test_the_tone_tier_tightens_as_alignment_falls():
    assert alignment_tier(100.0) == 0
    assert alignment_tier(79.0) == 1
    assert alignment_tier(39.0) == 2
    assert alignment_tier(19.0) == 3
