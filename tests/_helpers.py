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
