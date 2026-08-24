"""The tech tree: catalog, prerequisites, and how modifiers combine."""

import pytest

from automate_inc.core.game import Game
from automate_inc.core.tech import (
    AGGREGATION,
    MODIFIER_FIELDS,
    Modifiers,
    TechCategory,
    TechRegistry,
    Technology,
    aggregate,
    load_tech_registry,
)
from automate_inc.core.workers import Role, WorkerType


def researching_game(points=500, seed=3) -> Game:
    game = Game(seed=seed)
    game.state.research = points
    return game


def tech(tech_id, **effects) -> Technology:
    return Technology(
        id=tech_id,
        name=tech_id,
        description="",
        category=TechCategory.ECONOMY,
        cost=1,
        requires=(),
        effects=effects,
    )


# -- catalog -----------------------------------------------------------------


def test_the_bundled_tree_loads_and_every_prerequisite_exists():
    registry = load_tech_registry()
    ids = {t.id for t in registry.all()}
    assert ids
    for entry in registry.all():
        assert set(entry.requires) <= ids


def test_every_effect_names_a_real_modifier_field():
    for entry in load_tech_registry().all():
        assert set(entry.effects) <= MODIFIER_FIELDS


def test_unknown_effect_keys_are_rejected_at_load_time():
    with pytest.raises(ValueError, match="unknown effects"):
        TechRegistry.from_json(
            '{"technologies": [{"id": "x", "name": "X", "description": "",'
            ' "category": "ECONOMY", "cost": 1, "effects": {"free_money": 5}}]}'
        )


def test_both_agent_levels_are_reachable_through_research():
    registry = load_tech_registry()
    unlocks = {
        int(t.effects["unlocked_agent_level"])
        for t in registry.all()
        if "unlocked_agent_level" in t.effects
    }
    assert unlocks == {2, 3}


# -- aggregation -------------------------------------------------------------


def test_nothing_researched_means_no_effect():
    assert aggregate([]) == Modifiers()


def test_every_modifier_field_has_an_aggregation_rule():
    assert set(AGGREGATION) == MODIFIER_FIELDS


def test_levels_aggregate_by_maximum_not_by_sum():
    combined = aggregate([tech("a", unlocked_agent_level=2), tech("b", unlocked_agent_level=3)])
    assert combined.unlocked_agent_level == 3


def test_multipliers_stack_multiplicatively():
    combined = aggregate([tech("a", income_multiplier=1.25), tech("b", income_multiplier=1.5)])
    assert combined.income_multiplier == pytest.approx(1.875)


def test_alignment_effects_stack_additively_and_can_cancel_out():
    combined = aggregate([tech("a", alignment_per_round=2.0), tech("b", alignment_per_round=-3.0)])
    assert combined.alignment_per_round == pytest.approx(-1.0)


def test_a_save_naming_an_unknown_technology_is_ignored_not_fatal():
    registry = load_tech_registry()
    assert registry.resolve(["ai_intelligence_2", "does_not_exist"]) == [
        registry.get("ai_intelligence_2")
    ]


# -- the research action -----------------------------------------------------


def test_researching_spends_the_points_and_records_the_technology():
    game = researching_game(points=30)
    assert game.research("ai_intelligence_2").ok
    assert game.state.researched == ["ai_intelligence_2"]
    assert game.state.research == 0
    assert game.modifiers.unlocked_agent_level == 2


def test_research_without_enough_points_changes_nothing():
    game = researching_game(points=29)
    before = game.state.to_dict()
    result = game.research("ai_intelligence_2")
    assert not result.ok
    assert game.state.to_dict() == before


def test_a_locked_technology_is_refused_and_names_what_is_missing():
    game = researching_game()
    result = game.research("ai_intelligence_3")
    assert not result.ok
    assert "KI-Intelligenz Stufe 2" in result.message
    assert game.state.researched == []


def test_prerequisites_make_a_technology_available():
    game = researching_game()
    assert game.research("ai_intelligence_2").ok
    assert game.research("ai_intelligence_3").ok


def test_researching_the_same_technology_twice_is_refused():
    game = researching_game()
    assert game.research("ai_intelligence_2").ok
    spent = game.state.research
    assert not game.research("ai_intelligence_2").ok
    assert game.state.research == spent
    assert game.state.researched == ["ai_intelligence_2"]


def test_unknown_technology_is_refused():
    assert not researching_game().research("time_travel").ok


# -- what research unlocks ---------------------------------------------------


def test_higher_level_agents_cannot_be_hired_before_they_are_researched():
    game = researching_game()
    result = game.hire_worker(Role.DEVELOPER, WorkerType.AGENT, level=2)
    assert not result.ok
    assert game.state.workers == []


def test_hiring_a_level_two_agent_works_once_researched():
    game = researching_game()
    game.research("ai_intelligence_2")
    assert game.hire_worker(Role.DEVELOPER, WorkerType.AGENT, level=2).ok
    assert game.state.workers[0].level == 2


def test_upgrading_lifts_an_agent_one_level_and_costs_money():
    game = researching_game()
    game.research("ai_intelligence_2")
    game.hire_worker(Role.DEVELOPER, WorkerType.AGENT, level=1)
    agent = game.state.workers[0]
    money_before = game.state.money
    assert game.upgrade_agent(agent.id).ok
    assert agent.level == 2
    assert game.state.money < money_before


def test_upgrading_beyond_what_is_researched_is_refused():
    game = researching_game()
    game.research("ai_intelligence_2")
    game.hire_worker(Role.DEVELOPER, WorkerType.AGENT, level=2)
    agent = game.state.workers[0]
    assert not game.upgrade_agent(agent.id).ok
    assert agent.level == 2


def test_humans_cannot_be_upgraded():
    game = researching_game()
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    result = game.upgrade_agent(game.state.workers[0].id)
    assert not result.ok


def test_token_optimization_makes_agents_cheaper():
    game = researching_game()
    game.hire_worker(Role.DEVELOPER, WorkerType.AGENT)
    full = game.state.workers[0].cost_per_round(game.modifiers).tokens
    game.research("token_optimization")
    discounted = game.state.workers[0].cost_per_round(game.modifiers).tokens
    assert discounted == pytest.approx(full * 0.8)
