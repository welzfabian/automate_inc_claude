"""Project catalog, instantiation and the rules for starting one."""

import pytest

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
    result = game.start_project("static_website")
    assert not result.ok
    assert game.state.active_projects == []


def test_a_human_satisfies_the_senior_requirement():
    game = Game(seed=1)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    assert game.start_project("static_website").ok
    assert len(game.state.active_projects) == 1


def test_unknown_blueprint_is_refused():
    game = Game(seed=1)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    assert not game.start_project("does_not_exist").ok


def test_worker_can_only_be_assigned_to_a_role_the_project_needs():
    game = Game(seed=1)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    game.hire_worker(Role.DESIGNER, WorkerType.HUMAN)
    game.start_project("static_website")  # needs a developer only
    project_id = game.state.active_projects[0].id
    designer = next(w for w in game.state.workers if w.role is Role.DESIGNER)
    result = game.assign_worker(designer.id, project_id)
    assert not result.ok
    assert designer.assigned_to is None


def test_role_slots_are_limited():
    game = Game(seed=1)
    for _ in range(2):
        game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    game.start_project("static_website")  # exactly 1 developer slot
    project_id = game.state.active_projects[0].id
    first, second = game.state.workers
    assert game.assign_worker(first.id, project_id).ok
    assert not game.assign_worker(second.id, project_id).ok
    assert second.assigned_to is None


def test_failed_action_leaves_state_untouched():
    """Every action validates before it mutates - nothing half-applies."""
    game = Game(seed=1)
    before = game.state.to_dict()
    assert not game.assign_worker("nope", "also_nope").ok
    assert game.state.to_dict() == before


@pytest.mark.parametrize("blueprint_id", ["static_website", "ecommerce_shop", "web_app"])
def test_every_catalog_project_is_profitable_with_humans(blueprint_id):
    """VISION.md: a purely human team should make a small profit, not a loss."""
    game = Game(seed=3)
    blueprint = game.registry.get(blueprint_id)
    for role, count in blueprint.required_roles.items():
        for _ in range(count):
            game.hire_worker(role, WorkerType.HUMAN)
    game.start_project(blueprint_id)
    project_id = game.state.active_projects[0].id
    for worker in game.state.workers:
        game.assign_worker(worker.id, project_id)
    for _ in range(6):  # let quality and aesthetics ramp up to their ceiling
        report = game.resolve_turn()
    assert report.income > report.costs_money
