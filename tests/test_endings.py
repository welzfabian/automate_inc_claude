"""M7: total automation ends the game - which ending you get depends only on
the alignment tier at that moment, per ``core.game._total_automation``."""

from _helpers import advance
from automate_inc.core.game import Game
from automate_inc.core.state import AUTONOMY_AGENT_COUNT
from automate_inc.core.workers import Role, WorkerType


def automated_game(*, agents=AUTONOMY_AGENT_COUNT, humans=0, alignment, seed=1) -> Game:
    """Level 1 agents have zero alignment decay (BALANCING.md), so ``alignment``
    lands exactly as set once the turn resolves - the boundary tests below rely
    on that. Money is set high so agent upkeep this turn can never race the new
    endings against bankruptcy."""
    game = Game(seed=seed)
    for _ in range(humans):
        game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    for _ in range(agents):
        game.hire_worker(Role.DEVELOPER, WorkerType.AGENT, 1)
    game.state.money = 1_000_000.0
    game.state.alignment = alignment
    return game


def test_total_automation_with_high_alignment_is_the_secret_ending():
    game = automated_game(alignment=80.0)
    report = advance(game)
    assert game.state.is_over
    assert "FALSCHE HOFFNUNG" in (game.state.game_over_reason or "")
    assert game.state.game_over_reason in report.events


def test_total_automation_below_eighty_is_the_dystopia_ending():
    game = automated_game(alignment=79.9)
    report = advance(game)
    assert game.state.is_over
    assert "VOLLAUTOMATISIERUNG" in (game.state.game_over_reason or "")
    assert game.state.game_over_reason in report.events


def test_total_automation_below_the_misalignment_threshold_ends_as_misalignment_instead():
    """Ordering: ``misalignment`` (< 20) is checked before the new endings, so
    it wins the moment automation and a collapsed alignment coincide."""
    game = automated_game(alignment=19.9)
    advance(game)
    assert game.state.is_over
    assert "KONTROLLVERLUST" in (game.state.game_over_reason or "")


def test_one_remaining_human_prevents_both_new_endings():
    game = automated_game(humans=1, alignment=90.0)
    advance(game)
    assert not game.state.is_over


def test_a_fleet_below_the_autonomy_threshold_does_not_trigger_it():
    game = automated_game(agents=AUTONOMY_AGENT_COUNT - 1, alignment=90.0)
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
