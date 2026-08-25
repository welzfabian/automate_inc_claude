"""M7: total automation ends the game - which ending you get depends only on
the alignment tier at that moment, per ``core.game._total_automation``.

Only agents at ``AUTONOMOUS_AGENT_LEVEL`` or above count. A level-1 fleet is a
cheap workforce, not a takeover, and used to end the game on turn 0 at
alignment 100 (BALANCING.md 22) - ``test_a_level_one_fleet_is_not_a_takeover``
is that regression.
"""

from _helpers import advance
from automate_inc.core.game import AUTONOMOUS_AGENT_LEVEL, Game
from automate_inc.core.state import AUTONOMY_AGENT_COUNT
from automate_inc.core.workers import Role, WorkerType

DECAY_PER_TURN = 1.0 * AUTONOMY_AGENT_COUNT
"""A full fleet of level-2 agents costs this much alignment per round
(economy.AGENT_ALIGNMENT_DECAY). The endings are checked at the *end* of
``resolve_turn``, after the decay, so every fixture below aims one round of
decay above the tier it is testing."""


def automated_game(
    *, agents=AUTONOMY_AGENT_COUNT, level=AUTONOMOUS_AGENT_LEVEL, humans=0, alignment, seed=1
) -> Game:
    """Money is set high so agent upkeep can never race the new endings against
    bankruptcy; ``alignment`` is the value *before* the turn's decay."""
    game = Game(seed=seed)
    game.state.research = 500
    assert game.research("ai_intelligence_2").ok
    game.state.research = 0
    for _ in range(humans):
        game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    for _ in range(agents):
        assert game.hire_worker(Role.DEVELOPER, WorkerType.AGENT, level).ok
    game.state.money = 1_000_000.0
    game.state.alignment = alignment
    return game


def test_total_automation_with_high_alignment_is_the_secret_ending():
    """Lands on exactly 80.0 after the decay - the tier boundary itself."""
    game = automated_game(alignment=80.0 + DECAY_PER_TURN)
    report = advance(game)
    assert game.state.alignment == 80.0
    assert game.state.is_over
    assert "FALSCHE HOFFNUNG" in (game.state.game_over_reason or "")
    assert game.state.game_over_reason in report.events


def test_total_automation_below_eighty_is_the_dystopia_ending():
    game = automated_game(alignment=79.9 + DECAY_PER_TURN)
    report = advance(game)
    assert game.state.is_over
    assert "VOLLAUTOMATISIERUNG" in (game.state.game_over_reason or "")
    assert game.state.game_over_reason in report.events


def test_total_automation_below_the_misalignment_threshold_ends_as_misalignment_instead():
    """Ordering: ``misalignment`` (< 20) is checked before the new endings, so
    it wins the moment automation and a collapsed alignment coincide."""
    game = automated_game(alignment=19.9 + DECAY_PER_TURN)
    advance(game)
    assert game.state.is_over
    assert "KONTROLLVERLUST" in (game.state.game_over_reason or "")


def test_a_level_one_fleet_is_not_a_takeover():
    """The turn-0 exploit: level-1 agents are free of alignment cost, so this
    fleet sat at 100 forever and handed out the rare ending immediately."""
    game = automated_game(agents=AUTONOMY_AGENT_COUNT + 4, level=1, alignment=100.0)
    advance(game)
    assert not game.state.is_over


def test_a_part_upgraded_fleet_does_not_reach_the_threshold():
    """One agent short of a full autonomous fleet, padded with level-1 bodies."""
    game = automated_game(agents=AUTONOMY_AGENT_COUNT - 1, alignment=100.0)
    for _ in range(3):
        assert game.hire_worker(Role.DEVELOPER, WorkerType.AGENT, 1).ok
    advance(game)
    assert not game.state.is_over


def test_one_remaining_human_prevents_both_new_endings():
    game = automated_game(humans=1, alignment=100.0)
    advance(game)
    assert not game.state.is_over


def test_a_fleet_below_the_autonomy_threshold_does_not_trigger_it():
    game = automated_game(agents=AUTONOMY_AGENT_COUNT - 1, alignment=100.0)
    advance(game)
    assert not game.state.is_over


def test_actions_are_refused_after_the_dystopia_ending():
    game = automated_game(alignment=50.0)
    advance(game)
    assert game.state.is_over
    assert not game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN).ok


def test_actions_are_refused_after_the_secret_ending():
    game = automated_game(alignment=100.0)
    advance(game)
    assert game.state.is_over
    assert not game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN).ok
