"""Service level and maintenance: a project earns what the client is getting."""

import pytest

from automate_inc.core import economy
from automate_inc.core.game import Game
from automate_inc.core.projects import load_tuning
from automate_inc.core.workers import Role, WorkerType

TUNING = load_tuning()


def project_game(blueprint_id="ecommerce_shop", staffing=None, seed=4) -> Game:
    """Start a project, then staff exactly the posts named in ``staffing``.

    A throwaway human starts the project and is fired again, so that an
    understaffed scenario really is understaffed.
    """
    game = Game(seed=seed)
    game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    starter = game.state.workers[0]
    assert game.start_project(blueprint_id).ok
    assert game.fire_worker(starter.id).ok
    project = game.state.active_projects[0]
    for role, count in (staffing or {}).items():
        for _ in range(count):
            assert game.hire_worker(role, WorkerType.HUMAN).ok
            assert game.assign_worker(game.state.workers[-1].id, project.id).ok
    return game


def play(game: Game, turns: int) -> float:
    """Resolve turns with the books topped up; returns the average net per turn."""
    total = 0.0
    for _ in range(turns):
        game.state.money = 100_000.0
        total += game.resolve_turn().net
    return total / turns


def full(game: Game) -> dict:
    return dict(game.state.active_projects[0].required_roles)


# -- the service level -------------------------------------------------------


def test_a_new_project_starts_part_way_in():
    """The briefing and the contract are already done."""
    project = project_game().state.active_projects[0]
    assert project.service_level == TUNING.service_level_start


def test_a_staffed_project_gets_finished():
    game = project_game(staffing={Role.DEVELOPER: 1, Role.DESIGNER: 1})
    play(game, 4)
    assert game.state.active_projects[0].at_full_service


def test_an_abandoned_project_falls_back_to_nothing():
    game = project_game()
    play(game, 3)
    assert game.state.active_projects[0].service_level == 0.0


def test_an_abandoned_project_earns_nothing():
    """The whole point: doing nothing used to be the most profitable strategy."""
    game = project_game()
    play(game, 3)
    project = game.state.active_projects[0]
    assert economy.project_income(project, game.state.workers) == 0.0


def test_abandoning_a_finished_project_undoes_it():
    game = project_game(staffing={Role.DEVELOPER: 1, Role.DESIGNER: 1})
    play(game, 4)
    project = game.state.active_projects[0]
    assert project.at_full_service
    for worker in list(game.state.workers):
        assert game.fire_worker(worker.id).ok
    play(game, 2)
    assert 0.0 < project.service_level < 100.0        # it slides, it does not snap
    play(game, 6)
    assert project.service_level == 0.0


def test_agents_build_faster_than_people():
    """Efficiency stops being only about quality once there is a build phase."""
    humans = project_game(staffing={Role.DEVELOPER: 1, Role.DESIGNER: 1})
    agents = Game(seed=4)
    agents.state.research = 500
    agents.research("ai_intelligence_2")
    agents.research("ai_intelligence_3")
    agents.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    starter = agents.state.workers[0]
    agents.start_project("ecommerce_shop")
    agents.fire_worker(starter.id)
    for role in (Role.DEVELOPER, Role.DESIGNER):
        agents.hire_worker(role, WorkerType.AGENT, 3)
        agents.assign_worker(agents.state.workers[-1].id, agents.state.active_projects[0].id)
    play(humans, 2)
    play(agents, 2)
    assert (
        agents.state.active_projects[0].service_level
        > humans.state.active_projects[0].service_level
    )


def test_half_a_team_builds_at_half_speed():
    fully = project_game(staffing={Role.DEVELOPER: 1, Role.DESIGNER: 1})
    partly = project_game(staffing={Role.DEVELOPER: 1})
    play(fully, 1)
    play(partly, 1)
    gained_full = fully.state.active_projects[0].service_level - TUNING.service_level_start
    gained_part = partly.state.active_projects[0].service_level - TUNING.service_level_start
    assert gained_part == pytest.approx(gained_full / 2)


def test_partial_staffing_still_finishes_eventually():
    """Slower is a lane, not a trap - why an empty post costs no service level."""
    game = project_game(blueprint_id="mobile_app", staffing={Role.DEVELOPER: 1})
    play(game, 10)
    assert game.state.active_projects[0].at_full_service


# -- attribute caps ----------------------------------------------------------


def test_a_filled_team_lifts_the_ceiling_to_the_top():
    game = project_game(staffing={Role.DEVELOPER: 1, Role.DESIGNER: 1})
    play(game, 6)
    project = game.state.active_projects[0]
    assert project.quality == 100.0
    assert project.aesthetics == 100.0


def test_an_empty_post_caps_its_attribute_at_the_base():
    game = project_game(staffing={Role.DEVELOPER: 1})
    play(game, 6)
    project = game.state.active_projects[0]
    assert project.quality == 100.0
    assert project.aesthetics == TUNING.attribute_cap_base


def test_one_of_two_posts_caps_halfway():
    """The web app is the only project asking for two of the same role."""
    game = project_game("web_app", staffing={Role.DEVELOPER: 1, Role.DESIGNER: 1})
    play(game, 6)
    assert game.state.active_projects[0].quality == pytest.approx(75.0)


def test_losing_a_worker_lets_the_attribute_slide_to_the_new_ceiling():
    game = project_game("web_app", staffing={Role.DEVELOPER: 2, Role.DESIGNER: 1})
    play(game, 6)
    project = game.state.active_projects[0]
    assert project.quality == 100.0
    developer = next(w for w in game.state.workers if w.role is Role.DEVELOPER)
    assert game.fire_worker(developer.id).ok
    play(game, 10)
    assert project.quality == pytest.approx(75.0)


def test_the_slide_is_gradual_not_instant():
    game = project_game("web_app", staffing={Role.DEVELOPER: 2, Role.DESIGNER: 1})
    play(game, 6)
    project = game.state.active_projects[0]
    developer = next(w for w in game.state.workers if w.role is Role.DEVELOPER)
    game.fire_worker(developer.id)
    play(game, 1)
    assert project.quality == pytest.approx(100.0 - TUNING.attribute_entropy)


def test_sales_caps_nothing():
    """It has no attribute to hold; leaving the post empty costs the visibility bonus."""
    assert Role.SALES not in economy.ROLE_ATTRIBUTES


# -- the economics -----------------------------------------------------------


@pytest.mark.parametrize(
    "blueprint_id", ["static_website", "ecommerce_shop", "mobile_app", "web_app"]
)
def test_full_staffing_beats_every_partial_staffing(blueprint_id):
    """The property that makes the whole mechanic work."""
    reference = project_game(blueprint_id)
    required = full(reference)
    complete = project_game(blueprint_id, staffing=required)
    best_full = play(complete, complete.state.active_projects[0].lifetime)

    for role in required:
        reduced = dict(required)
        reduced[role] -= 1
        if reduced[role] == 0:
            del reduced[role]
        partial = project_game(blueprint_id, staffing=reduced)
        assert play(partial, partial.state.active_projects[0].lifetime) < best_full


def test_bigger_projects_earn_more_than_small_ones():
    """They did not before: every project paid the same +20 a round."""
    earnings = {}
    for blueprint_id in ("static_website", "ecommerce_shop", "web_app"):
        game = project_game(blueprint_id)
        game = project_game(blueprint_id, staffing=full(game))
        project = game.state.active_projects[0]
        earnings[blueprint_id] = play(game, project.lifetime) * project.lifetime
    assert earnings["static_website"] < earnings["ecommerce_shop"] < earnings["web_app"]


def test_bigger_projects_also_run_longer():
    """They used to run shorter - exactly inverted."""
    registry = Game(seed=1).registry
    by_size = sorted(registry.all(), key=lambda bp: sum(bp.required_roles.values()))
    lifetimes = [bp.lifetime for bp in by_size]
    assert lifetimes == sorted(lifetimes)
