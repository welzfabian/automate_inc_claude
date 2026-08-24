"""Saving and loading. Saves are plain JSON so they stay readable and diffable."""

import json

import pytest

from automate_inc.core.game import Game
from automate_inc.core.state import SAVE_FORMAT_VERSION, GameState
from automate_inc.core.workers import Role, WorkerType


def played_game(seed=11) -> Game:
    game = Game(seed=seed)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    game.hire_worker(Role.DESIGNER, WorkerType.AGENT)
    game.start_project("ecommerce_shop")
    project_id = game.state.active_projects[0].id
    for worker in game.state.workers:
        game.assign_worker(worker.id, project_id)
    for _ in range(3):
        game.resolve_turn()
    return game


def test_round_trip_preserves_the_whole_state():
    original = played_game().state
    restored = GameState.from_dict(json.loads(json.dumps(original.to_dict())))
    assert restored.to_dict() == original.to_dict()


def test_save_file_is_human_readable_json(tmp_path):
    game = played_game()
    path = tmp_path / "save.json"
    assert game.save(path).ok
    data = json.loads(path.read_text("utf-8"))
    assert data["format_version"] == SAVE_FORMAT_VERSION
    assert data["turn"] == 3
    assert isinstance(data["workers"], list)


def test_loaded_game_resolves_the_next_turn_identically(tmp_path):
    """The RNG is derived from seed and turn, so loading cannot change the future."""
    original = played_game()
    path = tmp_path / "save.json"
    original.save(path)

    loaded = Game.load(path)
    original.resolve_turn()
    loaded.resolve_turn()
    assert loaded.state.to_dict() == original.state.to_dict()


def test_worker_assignments_survive_a_save(tmp_path):
    game = played_game()
    path = tmp_path / "save.json"
    game.save(path)
    loaded = Game.load(path)
    project = loaded.state.active_projects[0]
    assert len(loaded.state.workers_on(project.id)) == 2
    assert sorted(project.assigned_workers) == sorted(w.id for w in loaded.state.workers)


def test_new_ids_do_not_collide_after_loading(tmp_path):
    game = played_game()
    path = tmp_path / "save.json"
    game.save(path)
    loaded = Game.load(path)
    existing = {w.id for w in loaded.state.workers} | {p.id for p in loaded.state.active_projects}
    loaded.hire_worker(Role.SALES, WorkerType.AGENT)
    assert loaded.state.workers[-1].id not in existing


def test_unknown_save_format_is_rejected():
    with pytest.raises(ValueError):
        GameState.from_dict({"format_version": 999})


# -- research and agent levels (M2, save format 2) ---------------------------


def researched_game(seed=12) -> Game:
    game = Game(seed=seed)
    game.state.research = 500
    game.research("ai_intelligence_2")
    game.research("token_optimization")
    game.hire_worker(Role.DEVELOPER, WorkerType.AGENT, level=2)
    game.start_project("static_website")
    project_id = game.state.active_projects[0].id
    game.assign_worker(game.state.workers[0].id, project_id)
    game.resolve_turn()
    return game


def test_researched_technologies_survive_the_round_trip():
    original = researched_game().state
    restored = GameState.from_dict(json.loads(json.dumps(original.to_dict())))
    assert restored.researched == original.researched
    assert restored.to_dict() == original.to_dict()


def test_a_loaded_game_keeps_its_modifiers(tmp_path):
    game = researched_game()
    path = tmp_path / "save.json"
    game.save(path)
    assert Game.load(path).modifiers == game.modifiers


def test_agent_level_and_staleness_counter_survive_the_round_trip():
    original = researched_game().state
    restored = GameState.from_dict(json.loads(json.dumps(original.to_dict())))
    assert restored.workers[0].level == 2
    assert restored.workers[0].rounds_in_assignment == original.workers[0].rounds_in_assignment


def test_saves_from_before_the_tech_tree_are_rejected():
    """Format 1 knew no research; there is deliberately no migration path."""
    data = researched_game().state.to_dict()
    data["format_version"] = 1
    with pytest.raises(ValueError, match="Unsupported save format version"):
        GameState.from_dict(data)


def test_the_current_save_format_is_version_two():
    assert SAVE_FORMAT_VERSION == 2
