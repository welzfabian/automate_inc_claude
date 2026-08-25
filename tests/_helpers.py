"""Shared test helpers - not collected by pytest, the module name has no test_ prefix."""

from __future__ import annotations

from automate_inc.core.events import EventRegistry
from automate_inc.core.game import Game, TurnReport

NO_EVENTS = EventRegistry({})
"""An empty event catalog, for tests that measure the plain economy and would
otherwise have a random event's pressure show up as unexplained noise in a
same-seed comparison between two differently staffed games."""


def advance(game: Game) -> TurnReport:
    """Resolve one turn, auto-answering any pending event decisions first.

    Most tests exercise the economy or a specific mechanic and are not testing
    the event flow itself, so picking each decision's first option keeps a
    plain loop of ``resolve_turn()`` calls from stalling on M4's ``once``
    events (rent, the AI-hype wave, ...) the moment their conditions are met.
    """
    for event_id in list(game.state.pending_decisions):
        event = game.event_registry.get(event_id)
        assert event is not None
        game.answer_event(event_id, event.options[0].id)
    return game.resolve_turn()


def unlock(game: Game, blueprint_id: str) -> None:
    """Mark this job's whole reference chain as already commissioned (M8).

    Every job above the first rung wants a smaller one on the record before a
    client hands it over. Tests that measure something else - the economy, an
    event, a save round-trip - start their project directly, so they need the
    chain filled in rather than played through. Deliberately not a production
    helper: it writes ``started_projects`` behind ``start_project``'s back.
    """
    registry = game.registry
    pending = [blueprint_id]
    while pending:
        blueprint = registry.get(pending.pop())
        if blueprint is None:
            continue
        for required in blueprint.requires:
            if required not in game.state.started_projects:
                game.state.started_projects.append(required)
                pending.append(required)


def commission(game: Game, blueprint_id: str):
    """Unlock a job's chain and start it - what most fixtures actually mean."""
    unlock(game, blueprint_id)
    return game.start_project(blueprint_id)
