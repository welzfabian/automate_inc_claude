"""External pressure: unlocking, triggering, deciding and ageing events."""

from __future__ import annotations

import json

import pytest

from _helpers import commission
from automate_inc.core.events import (
    ActiveEffect,
    Event,
    EventCategory,
    EventContext,
    EventOption,
    EventRegistry,
    Pressure,
    aggregate_pressure,
    load_event_registry,
)
from automate_inc.core.game import Game
from automate_inc.core.workers import Role, WorkerType

REGISTRY = load_event_registry()

NOTHING_UNLOCKED = EventContext(
    turn=0,
    money=1000.0,
    alignment=100.0,
    unlocked_agent_level=1,
    agents=0,
    humans=0,
    projects=0,
    last_net=None,
    triggered=frozenset(),
)
"""A context that satisfies none of the shipped catalog's conditions."""


# -- is_available: requires only, deterministic from the state ---------------


@pytest.mark.parametrize("event", REGISTRY.all(), ids=lambda e: e.id)
def test_an_event_with_unmet_conditions_never_triggers(event):
    assert not REGISTRY.is_available(event, NOTHING_UNLOCKED)


def test_min_turn_gates_on_the_turn_number():
    event = Event(
        id="x", category=EventCategory.MARKET, name="X", description="",
        requires={"min_turn": 5}, chance=1.0, once=False, options=(),
    )
    assert not REGISTRY.is_available(event, NOTHING_UNLOCKED)
    late = EventContext(**{**vars(NOTHING_UNLOCKED), "turn": 5})
    assert REGISTRY.is_available(event, late)


def test_after_event_reads_the_history():
    event = Event(
        id="x", category=EventCategory.INVESTOR, name="X", description="",
        requires={"after_event": "quarterly_report"}, chance=1.0, once=False, options=(),
    )
    assert not REGISTRY.is_available(event, NOTHING_UNLOCKED)
    followed = EventContext(
        **{**vars(NOTHING_UNLOCKED), "triggered": frozenset({"quarterly_report"})}
    )
    assert REGISTRY.is_available(event, followed)


def test_not_after_event_is_the_inverse():
    event = Event(
        id="x", category=EventCategory.MARKET, name="X", description="",
        requires={"not_after_event": "recession"}, chance=1.0, once=False, options=(),
    )
    assert REGISTRY.is_available(event, NOTHING_UNLOCKED)
    followed = EventContext(**{**vars(NOTHING_UNLOCKED), "triggered": frozenset({"recession"})})
    assert not REGISTRY.is_available(event, followed)


def test_max_last_net_needs_a_worse_last_round():
    event = Event(
        id="x", category=EventCategory.INVESTOR, name="X", description="",
        requires={"max_last_net": 0.0}, chance=1.0, once=False, options=(),
    )
    never_played = NOTHING_UNLOCKED
    assert not REGISTRY.is_available(event, never_played)
    profitable = EventContext(**{**vars(NOTHING_UNLOCKED), "last_net": 50.0})
    assert not REGISTRY.is_available(event, profitable)
    lossy = EventContext(**{**vars(NOTHING_UNLOCKED), "last_net": -50.0})
    assert REGISTRY.is_available(event, lossy)


def test_min_alignment_needs_at_least_the_threshold():
    event = Event(
        id="x", category=EventCategory.AI, name="X", description="",
        requires={"min_alignment": 50}, chance=1.0, once=False, options=(),
    )
    low = EventContext(**{**vars(NOTHING_UNLOCKED), "alignment": 49.0})
    assert not REGISTRY.is_available(event, low)
    assert REGISTRY.is_available(event, NOTHING_UNLOCKED)  # alignment defaults to 100.0


def test_max_money_needs_at_or_below_the_threshold():
    event = Event(
        id="x", category=EventCategory.MARKET, name="X", description="",
        requires={"max_money": 500}, chance=1.0, once=False, options=(),
    )
    assert not REGISTRY.is_available(event, NOTHING_UNLOCKED)  # money defaults to 1000.0
    poor = EventContext(**{**vars(NOTHING_UNLOCKED), "money": 500.0})
    assert REGISTRY.is_available(event, poor)


def test_min_investor_equity_needs_at_least_the_threshold():
    event = Event(
        id="x", category=EventCategory.INVESTOR, name="X", description="",
        requires={"min_investor_equity": 5.0}, chance=1.0, once=False, options=(),
    )
    assert not REGISTRY.is_available(event, NOTHING_UNLOCKED)  # investor_equity defaults to 0.0
    diluted = EventContext(**{**vars(NOTHING_UNLOCKED), "investor_equity": 5.0})
    assert REGISTRY.is_available(event, diluted)


def test_agents_outnumber_humans_compares_headcounts():
    event = Event(
        id="x", category=EventCategory.AI, name="X", description="",
        requires={"agents_outnumber_humans": True}, chance=1.0, once=False, options=(),
    )
    assert not REGISTRY.is_available(event, NOTHING_UNLOCKED)  # 0 agents, 0 humans
    outnumbered = EventContext(**{**vars(NOTHING_UNLOCKED), "agents": 3, "humans": 1})
    assert REGISTRY.is_available(event, outnumbered)


def test_max_humans_needs_at_or_below_the_threshold():
    event = Event(
        id="x", category=EventCategory.AI, name="X", description="",
        requires={"max_humans": 1}, chance=1.0, once=False, options=(),
    )
    assert REGISTRY.is_available(event, NOTHING_UNLOCKED)  # humans defaults to 0
    staffed = EventContext(**{**vars(NOTHING_UNLOCKED), "humans": 2})
    assert not REGISTRY.is_available(event, staffed)


def test_full_automation_warning_needs_a_full_fleet_and_at_most_one_human():
    """M7: fires exactly one human away from the total-automation endings."""
    event = REGISTRY.get("full_automation_warning")
    assert event is not None
    almost = EventContext(**{**vars(NOTHING_UNLOCKED), "agents": 5, "humans": 1})
    assert not REGISTRY.is_available(event, almost)  # not enough agents yet
    staffed = EventContext(**{**vars(NOTHING_UNLOCKED), "agents": 6, "humans": 2})
    assert not REGISTRY.is_available(event, staffed)  # too many humans left
    edge = EventContext(**{**vars(NOTHING_UNLOCKED), "agents": 6, "humans": 1})
    assert REGISTRY.is_available(event, edge)
    empty = EventContext(**{**vars(NOTHING_UNLOCKED), "agents": 6, "humans": 0})
    assert REGISTRY.is_available(event, empty)


def test_agents_outnumber_humans_false_does_not_require_the_opposite():
    """``{"agents_outnumber_humans": false}`` is not "humans must not be
    outnumbered" - the check is skipped outright, same as omitting it."""
    event = Event(
        id="x", category=EventCategory.AI, name="X", description="",
        requires={"agents_outnumber_humans": False}, chance=1.0, once=False, options=(),
    )
    lopsided = EventContext(**{**vars(NOTHING_UNLOCKED), "agents": 5, "humans": 0})
    assert REGISTRY.is_available(event, lopsided)


# -- catalog validation --------------------------------------------------------


def test_bundled_catalog_loads_without_error():
    assert len(REGISTRY.all()) > 0


def test_unknown_instant_effect_is_rejected_at_load():
    with pytest.raises(ValueError, match="instant-incompatible"):
        EventRegistry.from_json(
            json.dumps(
                {
                    "events": [
                        {
                            "id": "x", "category": "MARKET", "name": "X", "description": "",
                            "requires": {}, "chance": 1.0,
                            "options": [
                                {"id": "o", "label": "O", "effects": {"income_multiplier": 1.1}}
                            ],
                        }
                    ]
                }
            )
        )


def test_unknown_running_effect_is_rejected_at_load():
    with pytest.raises(ValueError, match="running-incompatible"):
        EventRegistry.from_json(
            json.dumps(
                {
                    "events": [
                        {
                            "id": "x", "category": "MARKET", "name": "X", "description": "",
                            "requires": {}, "chance": 1.0,
                            "options": [
                                {"id": "o", "label": "O", "effects": {"money": -5}, "duration": 3}
                            ],
                        }
                    ]
                }
            )
        )


def test_unknown_condition_is_rejected_at_load():
    with pytest.raises(ValueError, match="unknown conditions"):
        EventRegistry.from_json(
            json.dumps(
                {
                    "events": [
                        {
                            "id": "x", "category": "MARKET", "name": "X", "description": "",
                            "requires": {"min_unicorns": 1}, "chance": 1.0,
                            "options": [{"id": "o", "label": "O", "effects": {}}],
                        }
                    ]
                }
            )
        )


def test_dangling_after_event_reference_is_rejected_at_load():
    with pytest.raises(ValueError, match="unknown event"):
        EventRegistry.from_json(
            json.dumps(
                {
                    "events": [
                        {
                            "id": "x", "category": "MARKET", "name": "X", "description": "",
                            "requires": {"after_event": "does_not_exist"}, "chance": 1.0,
                            "options": [{"id": "o", "label": "O", "effects": {}}],
                        }
                    ]
                }
            )
        )


def test_a_non_positive_duration_is_rejected_at_load():
    with pytest.raises(ValueError, match="non-positive duration"):
        EventRegistry.from_json(
            json.dumps(
                {
                    "events": [
                        {
                            "id": "x", "category": "MARKET", "name": "X", "description": "",
                            "requires": {}, "chance": 1.0,
                            "options": [
                                {"id": "o", "label": "O", "effects": {}, "duration": 0}
                            ],
                        }
                    ]
                }
            )
        )


# -- Pressure: the Modifiers equivalent for running effects -------------------


def test_no_active_effects_is_neutral_pressure():
    assert aggregate_pressure([]) == Pressure()


def test_multiplicative_fields_multiply_and_additive_fields_add():
    a = EventOption(
        id="a", label="A", effects={"income_multiplier": 0.9, "fixed_cost": 10}, duration=3
    )
    b = EventOption(
        id="b", label="B", effects={"income_multiplier": 0.8, "fixed_cost": 5}, duration=-1
    )
    pressure = aggregate_pressure([a, b])
    assert pressure.income_multiplier == pytest.approx(0.72)
    assert pressure.fixed_cost == pytest.approx(15.0)


# -- resolve_active: save/load resilience -------------------------------------


def test_resolve_active_skips_an_effect_whose_event_a_newer_catalog_lost():
    """A save may name an event the current catalog no longer has - the same
    tolerance ``TechRegistry.resolve`` has for a dropped technology."""
    active = [ActiveEffect(event_id="does_not_exist", option_id="whatever", remaining=1)]
    assert REGISTRY.resolve_active(active) == []


def test_resolve_active_skips_an_effect_whose_option_a_newer_catalog_lost():
    """The event can still exist while the specific option it fired with was
    renamed or removed - that must not crash the resolve either."""
    active = [ActiveEffect(event_id="rent", option_id="does_not_exist", remaining=1)]
    assert REGISTRY.resolve_active(active) == []


# -- wired into Game: trigger -> pending decision -> answer -------------------


def force_pending(game: Game, event_id: str) -> None:
    """Skip the RNG roll and put an event straight into the decision queue -
    the tests below are about what happens once one is pending, not about
    whether the dice landed right."""
    game.state.pending_decisions.append(event_id)
    game.state.event_history.append(event_id)


def test_resolve_turn_blocks_while_a_decision_is_open():
    game = Game(seed=1)
    force_pending(game, "rent")
    before = game.state.to_dict()
    report = game.resolve_turn()
    assert report.blocked
    assert game.state.to_dict() == before


def test_answering_the_only_decision_unblocks_the_turn():
    game = Game(seed=1)
    force_pending(game, "rent")
    assert game.answer_event("rent", "sign_lease").ok
    report = game.resolve_turn()
    assert not report.blocked
    assert game.state.turn == 1


def test_answering_an_unknown_decision_is_refused():
    game = Game(seed=1)
    assert not game.answer_event("does_not_exist", "whatever").ok


def test_answering_an_unknown_option_is_refused():
    game = Game(seed=1)
    force_pending(game, "rent")
    assert not game.answer_event("rent", "does_not_exist").ok


def test_triggering_alone_books_no_effect():
    """An event that has fired but not been answered changes nothing yet."""
    game = Game(seed=1)
    before_money = game.state.money
    force_pending(game, "ai_regulation")
    assert game.state.money == before_money
    assert game.state.active_events == []


def test_an_instant_option_books_money_immediately():
    game = Game(seed=1)
    money_before = game.state.money
    force_pending(game, "car_trouble")
    assert game.answer_event("car_trouble", "repair").ok
    assert game.state.money == pytest.approx(money_before - 300.0)


def test_give_equity_permanently_raises_investor_equity():
    """M5: investor_threat's give_equity is no longer a free 3.000 € - it sells a
    permanent income share, the same effect raise_funding grants voluntarily."""
    game = Game(seed=1)
    before = game.state.investor_equity
    force_pending(game, "investor_threat")
    assert game.answer_event("investor_threat", "give_equity").ok
    assert game.state.investor_equity == pytest.approx(before + 8.0)


def test_dividend_call_stalling_costs_more_equity_and_alignment():
    game = Game(seed=1)
    force_pending(game, "dividend_call")
    before_equity = game.state.investor_equity
    before_alignment = game.state.alignment
    assert game.answer_event("dividend_call", "stall").ok
    assert game.state.investor_equity == pytest.approx(before_equity + 5.0)
    assert game.state.alignment == pytest.approx(before_alignment - 6.0)


def test_dividend_call_is_only_available_with_existing_equity():
    event = REGISTRY.get("dividend_call")
    assert event is not None
    diluted = EventContext(**{**vars(NOTHING_UNLOCKED), "turn": 8, "investor_equity": 5.0})
    assert REGISTRY.is_available(event, diluted)
    undiluted = EventContext(**{**vars(diluted), "investor_equity": 0.0})
    assert not REGISTRY.is_available(event, undiluted)


def test_a_running_option_becomes_active_pressure():
    game = Game(seed=1)
    force_pending(game, "ai_regulation")
    assert game.answer_event("ai_regulation", "comply").ok
    assert game.pressure.cost_per_agent == pytest.approx(10.0)


def test_a_permanent_effect_never_ages_out():
    game = Game(seed=1)
    force_pending(game, "ai_regulation")
    game.answer_event("ai_regulation", "comply")
    for _ in range(20):
        game.state.money = 100_000.0
        game.resolve_turn()
    assert game.pressure.cost_per_agent == pytest.approx(10.0)


def test_a_temporary_effect_ages_out_after_its_duration():
    game = Game(seed=1)
    force_pending(game, "recession")
    game.answer_event("recession", "endure")  # duration: 4
    assert game.pressure.income_multiplier == pytest.approx(0.7)
    for _ in range(4):
        game.state.money = 100_000.0
        game.resolve_turn()
    assert game.pressure.income_multiplier == pytest.approx(1.0)


def test_ageing_out_is_reported_by_name():
    game = Game(seed=1)
    force_pending(game, "recession")
    game.answer_event("recession", "endure")
    events = []
    for _ in range(4):
        game.state.money = 100_000.0
        events.extend(game.resolve_turn().events)
    assert any("Rezession" in e for e in events)


# -- every catalog option is a real, always-selectable decision --------------


CATALOG_OPTIONS = [(event, option) for event in REGISTRY.all() for option in event.options]


@pytest.mark.parametrize("event, option", CATALOG_OPTIONS, ids=lambda x: getattr(x, "id", ""))
def test_every_option_is_selectable_even_with_no_money(event, option):
    game = Game(seed=1)
    game.state.money = -5000.0
    force_pending(game, event.id)
    result = game.answer_event(event.id, option.id)
    assert result.ok


@pytest.mark.parametrize("event, option", CATALOG_OPTIONS, ids=lambda x: getattr(x, "id", ""))
def test_every_option_produces_a_named_report_line(event, option):
    game = Game(seed=1)
    force_pending(game, event.id)
    result = game.answer_event(event.id, option.id)
    assert event.name in result.message
    assert option.label in result.message


# -- determinism: same seed, same event sequence ------------------------------


def grown_company(seed: int) -> Game:
    game = Game(seed=seed)
    for _ in range(7):
        game.hire_worker(Role.DEVELOPER, WorkerType.AGENT)
    for _ in range(2):
        game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    commission(game, "web_app")
    project_id = game.state.active_projects[0].id
    for worker in game.state.workers[:3]:
        game.assign_worker(worker.id, project_id)
    return game


def play_answering_first_option(game: Game, turns: int) -> list[str]:
    triggered: list[str] = []
    for _ in range(turns):
        for event_id in list(game.state.pending_decisions):
            event = game.event_registry.get(event_id)
            game.answer_event(event_id, event.options[0].id)
        game.state.money = 1_000_000.0
        game.state.tokens = 100_000.0
        triggered.extend(game.state.event_history[len(triggered):])
        game.resolve_turn()
    return list(game.state.event_history)


def test_the_same_seed_yields_the_same_event_sequence():
    first = play_answering_first_option(grown_company(42), 20)
    second = play_answering_first_option(grown_company(42), 20)
    assert first == second
    assert first != []


def test_a_reloaded_save_continues_the_same_event_sequence(tmp_path):
    original = grown_company(42)
    play_answering_first_option(original, 10)
    path = tmp_path / "save.json"
    original.save(path)
    loaded = Game.load(path)

    play_answering_first_option(original, 10)
    play_answering_first_option(loaded, 10)
    assert original.state.to_dict() == loaded.state.to_dict()
