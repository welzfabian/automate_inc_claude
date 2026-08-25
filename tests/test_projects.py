"""Project catalog, instantiation and the rules for starting one."""

import pytest

from _helpers import NO_EVENTS, advance, commission, unlock
from automate_inc.core.game import Game
from automate_inc.core.projects import ProjectRegistry, load_registry
from automate_inc.core.workers import Role, WorkerType


def test_registry_loads_bundled_catalog():
    registry = load_registry()
    ids = {bp.id for bp in registry.all()}
    assert {"static_website", "ecommerce_shop", "web_app"} <= ids


def test_registry_is_pure_configuration():
    """Adding a project must not require code changes (SPEC 11.1)."""
    registry = ProjectRegistry.from_json(
        """
        {"projects": [{
            "id": "ai_chatbot", "name": "KI-Chatbot", "description": "Ein Chatbot",
            "project_type": "KI_INTEGRATION",
            "required_roles": {"DEVELOPER": 1, "RESEARCHER": 1},
            "base_income": 400, "basis_fixed_costs": 80, "lifetime": 10
        }]}
        """
    )
    project = registry.instantiate("ai_chatbot", "p1")
    assert project.required_roles == {Role.DEVELOPER: 1, Role.RESEARCHER: 1}
    assert project.rounds_left == 10


def test_instances_are_independent_of_the_blueprint():
    registry = load_registry()
    first = registry.instantiate("static_website", "p1")
    second = registry.instantiate("static_website", "p2")
    first.adjust("quality", 25)
    assert second.quality != first.quality


def test_cannot_start_project_without_a_senior_worker():
    """Level 1 agents alone cannot carry a project."""
    game = Game(seed=1)
    game.hire_worker(Role.DEVELOPER, WorkerType.AGENT)
    result = commission(game, "static_website")
    assert not result.ok
    assert game.state.active_projects == []


def test_a_human_satisfies_the_senior_requirement():
    game = Game(seed=1)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    assert commission(game, "static_website").ok
    assert len(game.state.active_projects) == 1


def test_unknown_blueprint_is_refused():
    game = Game(seed=1)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    assert not commission(game, "does_not_exist").ok


def test_worker_can_only_be_assigned_to_a_role_the_project_needs():
    game = Game(seed=1)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    game.hire_worker(Role.DESIGNER, WorkerType.HUMAN)
    commission(game, "static_website")  # needs a developer only
    project_id = game.state.active_projects[0].id
    designer = next(w for w in game.state.workers if w.role is Role.DESIGNER)
    result = game.assign_worker(designer.id, project_id)
    assert not result.ok
    assert designer.assigned_to is None


def test_role_slots_are_limited():
    game = Game(seed=1)
    for _ in range(2):
        game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    commission(game, "static_website")  # exactly 1 developer slot
    project_id = game.state.active_projects[0].id
    first, second = game.state.workers
    assert game.assign_worker(first.id, project_id).ok
    assert not game.assign_worker(second.id, project_id).ok
    assert second.assigned_to is None


@pytest.mark.parametrize("blueprint_id", ["static_website", "ecommerce_shop", "web_app"])
def test_every_catalog_project_is_profitable_with_humans(blueprint_id):
    """VISION.md: a purely human team should make a small profit, not a loss."""
    game = Game(seed=3, event_registry=NO_EVENTS)
    blueprint = game.registry.get(blueprint_id)
    for role, count in blueprint.required_roles.items():
        for _ in range(count):
            game.hire_worker(role, WorkerType.HUMAN)
    commission(game, blueprint_id)
    project_id = game.state.active_projects[0].id
    for worker in game.state.workers:
        game.assign_worker(worker.id, project_id)
    for _ in range(6):  # let quality and aesthetics ramp up to their ceiling
        report = advance(game)
    assert report.income > report.costs_money


# -- M8: every job exists once ----------------------------------------------


def test_a_blueprint_can_only_be_commissioned_once():
    """The ladder replaces the old plateau: you cannot rebuild the same web app
    forever, so growing means taking on a bigger job (M8)."""
    game = Game(seed=1)
    assert game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN).ok
    assert commission(game, "web_app").ok
    result = commission(game, "web_app")
    assert not result.ok
    assert "schon gebaut" in result.message
    assert len(game.state.active_projects) == 1


def test_a_commissioned_blueprint_stays_gone_after_it_expires():
    """``started_projects`` is kept separately from ``active_projects`` precisely
    because the latter is emptied at the end of a project's lifetime."""
    game = Game(seed=1, event_registry=NO_EVENTS)
    assert game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN).ok
    assert commission(game, "static_website").ok
    for _ in range(game.state.active_projects[0].lifetime):
        game.state.money = 100_000.0
        advance(game)
    assert not game.state.active_projects
    assert not commission(game, "static_website").ok


def test_taking_a_job_removes_it_and_offers_the_next_rung():
    """The catalogue does not simply shrink - working through it is what opens
    the bigger jobs, which is the whole point of the ladder."""
    game = Game(seed=1)
    assert game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN).ok
    unlock(game, "ecommerce_shop")
    assert game.start_project("ecommerce_shop").ok
    offered = {bp.id for bp in game.available_blueprints()}
    assert "ecommerce_shop" not in offered
    assert {"mobile_app", "web_app"} <= offered


def test_a_job_needs_a_smaller_one_on_the_record_first():
    """The ladder's rungs: a client hands over the big job to whoever can show
    the small one. Held in ``data/projects.json``, like a technology's requires."""
    game = Game(seed=1)
    assert game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN).ok
    result = game.start_project("web_app")
    assert not result.ok
    assert "Referenz" in result.message
    assert game.state.active_projects == []
    assert all(bp.id != "web_app" for bp in game.available_blueprints())


def test_the_catalogue_is_offered_smallest_first():
    """What the player can take on turn 0 has to be at the top of the menu."""
    sizes = [
        sum(bp.required_roles.values()) for bp in Game(seed=1).available_blueprints()
    ]
    assert sizes == sorted(sizes)


def test_the_last_job_needs_the_whole_ladder_walked():
    """Both branches, so no single line of jobs reaches the biggest one."""
    game = Game(seed=1)
    assert game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN).ok
    biggest = max(load_registry().all(), key=lambda bp: sum(bp.required_roles.values()))
    unlock(game, biggest.id)
    assert len(game.state.started_projects) == len(load_registry().all()) - 2
    assert game.start_project(biggest.id).ok


def test_a_failed_commission_leaves_the_catalogue_untouched():
    """Actions validate before they mutate - a rejected start must not consume
    the job it refused to begin."""
    game = Game(seed=1)
    assert not game.start_project("static_website").ok      # no senior worker yet
    assert game.state.started_projects == []
    assert any(bp.id == "static_website" for bp in game.available_blueprints())


def test_the_ladder_grows_by_headcount():
    """Every size from one post up to the biggest job exists, with no gaps -
    otherwise the ladder would have a rung the player cannot step on."""
    sizes = sorted(sum(bp.required_roles.values()) for bp in load_registry().all())
    assert sizes[0] == 1
    assert set(sizes) == set(range(1, max(sizes) + 1))
