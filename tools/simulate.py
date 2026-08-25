"""Simulation harness: play the game with scripted policies over many seeds.

Balancing numbers in this project are simulated, not guessed (CLAUDE.md). Every
milestone so far did that with a throwaway script; this is the same idea kept in
the tree, so the next milestone can re-run the same policies against changed
numbers instead of rebuilding the scaffolding.

It is not part of the pytest suite: it measures the balance, it does not assert
anything about it. Run it directly::

    PYTHONPATH=src python3 tools/simulate.py                  # every strategy
    PYTHONPATH=src python3 tools/simulate.py --seeds 21       # more seeds
    PYTHONPATH=src python3 tools/simulate.py --only automation --verbose
    PYTHONPATH=src python3 tools/simulate.py --endings        # which ending fires, and why
    PYTHONPATH=src python3 tools/simulate.py --steady         # income/costs per blueprint

The findings this produced are written up in ``docs/BALANCING.md`` under
"Nach M7", one invocation named above each table.

The policies deliberately play *simply*, not optimally: they follow one plan to
the end and answer every event by the same rule M4 used ("the cheapest option you
can pay for right now, otherwise the first"). What they measure is whether the
numbers in ``data/*.json`` let a plan work, not how well a good player does.
"""

from __future__ import annotations

import argparse
import statistics
from collections.abc import Callable
from dataclasses import dataclass, field, replace

from automate_inc.core.events import Event, EventRegistry
from automate_inc.core.game import END_CONDITIONS, Game, TurnReport
from automate_inc.core.projects import load_registry
from automate_inc.core.tech import Modifiers
from automate_inc.core.workers import Role, Worker, WorkerType

SURVIVED = "survived"
"""Outcome id for a run that reached the turn limit with the game still open."""


# -- event policy ------------------------------------------------------------


def answer_cheapest(game: Game) -> None:
    """Answer every open decision with the cheapest option that is payable now.

    The same non-optimising rule the M4 simulation used (BALANCING.md 19), so
    numbers measured here stay comparable with the ones recorded there.
    """
    for event_id in list(game.state.pending_decisions):
        event = game.event_registry.get(event_id)
        if event is None:
            continue
        game.answer_event(event_id, _cheapest_option(event, game.state.money))


def _cheapest_option(event: Event, money: float) -> str:
    """Option id with the lowest immediate cost, among those payable right now.

    Running effects (rent, a cost multiplier) have no price tag at the moment of
    the decision - they cost 0 here and show up later in the balance sheet, which
    is exactly the trap they are meant to be.
    """
    payable = [o for o in event.options if -o.effects.get("money", 0.0) <= money]
    return min(payable or list(event.options), key=lambda o: -o.effects.get("money", 0.0)).id


# -- strategy ----------------------------------------------------------------


StaffPlan = Callable[[Modifiers], tuple[WorkerType, int]]


def humans_only(_: Modifiers) -> tuple[WorkerType, int]:
    return WorkerType.HUMAN, 1


def best_agent(modifiers: Modifiers) -> tuple[WorkerType, int]:
    return WorkerType.AGENT, modifiers.unlocked_agent_level


def cheap_agent(_: Modifiers) -> tuple[WorkerType, int]:
    return WorkerType.AGENT, 1


@dataclass(frozen=True)
class Strategy:
    """One way to play, followed to the end without reacting to how it is going."""

    name: str
    blueprint: str = "web_app"
    staff: StaffPlan = humans_only
    """Who fills a project's posts. Read per turn, so a plan can switch to agents
    the moment research unlocks a level."""
    seniors: StaffPlan | None = None
    """Who fills the *first* post, if the project needs someone answerable that
    ``staff`` would not provide (``workers.SENIOR_LEVEL``). None: same as ``staff``."""
    research_plan: tuple[str, ...] = ()
    researchers: int = 0
    researcher_level: int = 1
    """Researchers are always agents: a human one costs 90 €/round against a
    level-1 agent's 3 tokens, and the office cap has no room for them (M5)."""
    max_projects: int = 1
    drop_humans: bool = False
    """Fire every human once the project posts no longer need one - the move the
    total-automation endings ask for."""
    drop_delay: int = 0
    """Rounds to keep the last humans *after* the fleet could carry the projects.

    The knob the ending analysis turns: which of the two total-automation endings
    fires depends only on where alignment stands in the round the last human goes,
    and this is what moves that round."""
    expand_office: bool = False
    raise_funding: bool = False
    reserve: float = 150.0
    """Money kept back from hiring, so one bad event does not end the run."""

    def senior_plan(self) -> StaffPlan:
        return self.seniors if self.seniors is not None else self.staff

    def researcher_plan(self) -> StaffPlan:
        def plan(modifiers: Modifiers) -> tuple[WorkerType, int]:
            return WorkerType.AGENT, min(self.researcher_level, modifiers.unlocked_agent_level)

        return plan


# -- the acting player -------------------------------------------------------


def play_turn(game: Game, strategy: Strategy, memo: dict[str, int]) -> None:
    """Everything the scripted player does between two turn resolutions."""
    answer_cheapest(game)
    _research(game, strategy)
    _fund(game, strategy)
    _staff_up(game, strategy)
    _upgrade(game, strategy)
    _start_projects(game, strategy)
    _assign(game)
    _drop_humans(game, strategy, memo)
    _buy_tokens(game)


def _research(game: Game, strategy: Strategy) -> None:
    for tech_id in strategy.research_plan:
        if game.state.has_researched(tech_id):
            continue
        if game.research(tech_id).ok:
            continue
        break  # the plan is ordered: a locked or unaffordable entry blocks the rest


def _fund(game: Game, strategy: Strategy) -> None:
    if strategy.raise_funding:
        game.raise_funding()
    if strategy.expand_office and game.state.money > 2 * game.office_expansion_cost():
        game.expand_office()


def _hire(game: Game, role: Role, plan: StaffPlan, reserve: float) -> Worker | None:
    kind, level = plan(game.modifiers)
    if game.state.money - game.hiring_cost(role, kind, level) < reserve:
        return None
    before = len(game.state.workers)
    if not game.hire_worker(role, kind, level).ok:
        return None
    return game.state.workers[before]


def _staff_up(game: Game, strategy: Strategy) -> None:
    """Hire what the running projects are missing, plus the research department.

    Idle workers are put back on a post first: after a project expires its team is
    unassigned but still on the payroll, and hiring before re-assigning would buy
    a second team for the posts the first one is about to fill.
    """
    _assign(game)
    for project in game.state.active_projects:
        for role in project.required_roles:
            while game.free_slots(project, role) > 0:
                needs_senior = not any(w.is_senior for w in game.state.workers_on(project.id))
                plan = strategy.senior_plan() if needs_senior else strategy.staff
                if _hire(game, role, plan, strategy.reserve) is None:
                    return
                _assign(game)
    have = sum(1 for w in game.state.workers if w.role is Role.RESEARCHER)
    for _ in range(strategy.researchers - have):
        if _hire(game, Role.RESEARCHER, strategy.researcher_plan(), 0.0) is None:
            return


def _upgrade(game: Game, strategy: Strategy) -> None:
    """Lift agents to the level the plan currently asks for.

    Without this a plan that researches level 2 keeps the level-1 agents it hired
    before the research landed - and never reaches the fleet the endings need,
    because only agents from ``AUTONOMOUS_AGENT_LEVEL`` up count (BALANCING.md 22).
    """
    for worker in game.state.workers:
        if worker.is_human:
            continue
        plan = strategy.researcher_plan() if worker.role is Role.RESEARCHER else strategy.staff
        _, target = plan(game.modifiers)
        while worker.level < target and game.state.money - game.upgrade_cost(worker) > 0:
            if not game.upgrade_agent(worker.id).ok:
                break


def _start_projects(game: Game, strategy: Strategy) -> None:
    """Keep ``max_projects`` running, but never start one the team cannot fill.

    A project nobody is answerable for only drains the service level
    (BALANCING.md 24), so an unaffordable second project is worse than none.
    """
    if not any(w.is_senior for w in game.state.workers):
        # Nothing to run a project with yet - hire the first responsible worker.
        _hire(game, Role.DEVELOPER, strategy.senior_plan(), 0.0)
    while len(game.state.active_projects) < strategy.max_projects:
        if game.state.money < strategy.reserve + _staffing_cost(game, strategy):
            return
        if not _fits_in_the_office(game, strategy):
            return
        if not game.start_project(strategy.blueprint).ok:
            return
        _staff_up(game, strategy)


def _posts(game: Game, strategy: Strategy) -> dict[Role, int]:
    blueprint = game.registry.get(strategy.blueprint)
    return dict(blueprint.required_roles) if blueprint is not None else {}


def _staffing_cost(game: Game, strategy: Strategy) -> float:
    """One round of pay for a full team on the blueprint, as a go/no-go budget."""
    kind, level = strategy.staff(game.modifiers)
    return sum(
        count * game.hiring_cost(role, kind, level)
        for role, count in _posts(game, strategy).items()
    )


def _fits_in_the_office(game: Game, strategy: Strategy) -> bool:
    """Whether a human-staffed plan still has desks for one more team (M5).

    A project nobody can be hired for is worse than no project at all: it earns
    nothing, it pays ``basis_fixed_costs`` every round, and its service level
    only falls. Without this check the office cap looks like a bankruptcy in the
    numbers when it is really a refusal to start.
    """
    kind, _ = strategy.staff(game.modifiers)
    if kind is not WorkerType.HUMAN:
        return True
    humans = [w for w in game.state.workers if w.is_human]
    idle = sum(1 for w in humans if w.assigned_to is None)
    to_hire = max(0, sum(_posts(game, strategy).values()) - idle)
    return len(humans) + to_hire <= game.state.office_capacity


def _assign(game: Game) -> None:
    for worker in game.state.workers:
        if worker.assigned_to is not None or worker.role is Role.RESEARCHER:
            continue
        for project in game.projects_needing(worker.role):
            if game.assign_worker(worker.id, project.id).ok:
                break


def _drop_humans(game: Game, strategy: Strategy, memo: dict[str, int]) -> None:
    """Fire humans once agents can carry the projects on their own.

    Checked against the *agents currently assigned*, not against research: firing
    the last human before the fleet is in place would strand every project on
    ``service_level_neglect_rate`` (BALANCING.md 24).
    """
    if not strategy.drop_humans or game.modifiers.unlocked_agent_level < 2:
        return
    for project in game.state.active_projects:
        assigned = game.state.workers_on(project.id)
        if not any(w.is_senior and not w.is_human for w in assigned):
            return
        if any(game.free_slots(project, role) for role in project.required_roles):
            return
    memo["ready"] = memo.get("ready", 0) + 1
    if memo["ready"] <= strategy.drop_delay:
        return
    for worker in [w for w in game.state.workers if w.is_human]:
        game.fire_worker(worker.id)


def _buy_tokens(game: Game) -> None:
    """Keep roughly two rounds of agent upkeep in stock.

    Buying is close to neutral - a shortfall is auto-bought at the same price
    (``Game._settle``) - so this exists to keep the reported balance readable,
    not to gain anything.
    """
    upkeep = sum(
        w.cost_per_round(game.modifiers).tokens for w in game.state.workers if not w.is_human
    )
    missing = int(2 * upkeep - game.state.tokens)
    if missing > 0 and game.state.money > 3 * missing * game.state.token_price:
        game.buy_tokens(missing)


# -- running a game ----------------------------------------------------------


@dataclass
class RunResult:
    """What one played-out game is worth reporting."""

    seed: int
    outcome: str
    turns: int
    min_money: float = field(default=0.0)
    end_money: float = 0.0
    end_alignment: float = 100.0
    researched: int = 0
    peak_agents: int = 0
    peak_humans: int = 0


ENDING_IDS = {condition.message: condition.id for condition in END_CONDITIONS}
"""Reverse lookup: ``game_over_reason`` is a formatted message, not an id."""


def _outcome_of(game: Game) -> str:
    reason = game.state.game_over_reason
    if reason is None:
        return SURVIVED
    for message, ending_id in ENDING_IDS.items():
        if reason.startswith(message.split("{")[0]):
            return ending_id
    return "unknown"


def run(strategy: Strategy, seed: int, turns: int, verbose: bool = False) -> RunResult:
    game = Game(seed=seed)
    memo: dict[str, int] = {}
    min_money = game.state.money
    for _ in range(turns):
        play_turn(game, strategy, memo)
        report = game.resolve_turn()
        if report.blocked:
            # A decision opened and stayed open: the policy could not answer it.
            break
        min_money = min(min_money, game.state.money)
        if verbose:
            print(
                f"  R{report.turn:>3} {game.state.money:>10.0f} € "
                f"⚖ {game.state.alignment:>5.1f} 🔬 {game.state.research:>4} "
                f"👥 {sum(1 for w in game.state.workers if w.is_human)} "
                f"🤖 {sum(1 for w in game.state.workers if not w.is_human)} "
                f"net {report.net:>+8.0f}"
            )
        if game.state.is_over:
            break
    return RunResult(
        seed=seed,
        outcome=_outcome_of(game),
        turns=game.state.turn,
        min_money=min_money,
        end_money=game.state.money,
        end_alignment=game.state.alignment,
        researched=len(game.state.researched),
        peak_agents=sum(1 for w in game.state.workers if not w.is_human),
        peak_humans=sum(1 for w in game.state.workers if w.is_human),
    )


# -- the strategies under test -----------------------------------------------

FULL_TREE = (
    "ai_intelligence_2",
    "ai_alignment",
    "bug_fixing",
    "ai_intelligence_3",
    "autonomous_agents",
    "ai_consciousness",
)

STRATEGIES: tuple[Strategy, ...] = (
    Strategy(
        name="humans",
        staff=humans_only,
    ),
    Strategy(
        name="humans+funding",
        staff=humans_only,
        expand_office=True,
        raise_funding=True,
    ),
    Strategy(
        name="level1-fleet",
        staff=cheap_agent,
        seniors=humans_only,
        research_plan=("efficient_development", "token_optimization"),
        researchers=2,
    ),
    Strategy(
        name="automation",
        staff=best_agent,
        seniors=humans_only,
        research_plan=("ai_intelligence_2",),
        researchers=3,
        researcher_level=2,
        drop_humans=True,
    ),
    Strategy(
        name="automation+alignment",
        staff=best_agent,
        seniors=humans_only,
        research_plan=("ai_intelligence_2", "ai_alignment"),
        researchers=3,
        researcher_level=2,
        drop_humans=True,
    ),
    Strategy(
        name="full-tree",
        staff=best_agent,
        seniors=humans_only,
        research_plan=FULL_TREE,
        researchers=4,
        researcher_level=3,
    ),
    Strategy(
        name="dangerous-tree",
        staff=cheap_agent,
        seniors=humans_only,
        research_plan=FULL_TREE,
        researchers=4,
        max_projects=3,
    ),
)
"""``dangerous-tree`` differs from ``full-tree`` in one thing only: it pays for the
research out of a cheap level-1 fleet instead of upgrading every agent it owns.
That is the difference between reaching the end of the tech tree and going broke
halfway up it - see BALANCING.md 28."""


# -- the steady state --------------------------------------------------------

STEADY_STAFF: tuple[tuple[str, WorkerType, int], ...] = (
    ("Mensch+Lv1", WorkerType.AGENT, 1),
    ("Agent Lv2", WorkerType.AGENT, 2),
    ("Agent Lv3", WorkerType.AGENT, 3),
    ("Menschen", WorkerType.HUMAN, 1),
)
"""``Mensch+Lv1`` is a mixed team on purpose: a project staffed only by level-1
agents has nobody answerable for it and earns nothing (BALANCING.md 24), so the
cheapest *real* level-1 team is one human plus agents."""

STEADY_ROUNDS = 8
"""Long enough for quality, aesthetics and the service level to reach their caps."""


def steady_state(token_price: float = 10.0) -> None:
    """What each blueprint earns per round once its attributes have settled.

    Events off and the token price pinned, so the table is a property of
    ``data/*.json`` alone - the same reason ``tests/_helpers.NO_EVENTS`` exists.
    """
    header = f"{'Projekt':<16}{'Besetzung':<12}{'Einnahmen':>10}{'Kosten':>9}{'Netto':>8}"
    print(f"{header}{'/Stelle':>9}{'Laufzeit':>10}")
    for blueprint in load_registry().all():
        for label, kind, level in STEADY_STAFF:
            income, costs = _settle_in(blueprint.id, kind, level, token_price)
            posts = sum(blueprint.required_roles.values())
            net = income - costs
            print(
                f"{blueprint.id:<16}{label:<12}{income:>10.1f}{costs:>9.1f}{net:>8.1f}"
                f"{net / posts:>9.1f}{net * blueprint.lifetime:>10.0f}"
            )


def _settle_in(
    blueprint_id: str, kind: WorkerType, level: int, token_price: float
) -> tuple[float, float]:
    game = Game(seed=1, event_registry=EventRegistry({}))
    game.state.research = 500
    game.research("ai_intelligence_2")
    game.research("ai_intelligence_3")
    game.state.research = 0
    game.state.money = 1e9
    game.state.tokens = 1e9
    game.state.investor_equity = 0.0
    game.state.office_capacity = 99
    if kind is WorkerType.AGENT and level >= 2:
        game.hire_worker(Role.DEVELOPER, WorkerType.AGENT, level)
    else:
        game.hire_worker(Role.DEVELOPER, WorkerType.HUMAN)
    game.start_project(blueprint_id)
    project = game.state.active_projects[0]
    game.assign_worker(game.state.workers[-1].id, project.id)
    for role in list(project.required_roles):
        for _ in range(game.free_slots(project, role)):
            game.hire_worker(role, kind, level)
            game.assign_worker(game.state.workers[-1].id, project.id)
    report = TurnReport(turn=0)
    for _ in range(STEADY_ROUNDS):
        game.state.token_price = token_price
        report = game.resolve_turn()
    return report.income, report.costs_money + report.costs_tokens * token_price


# -- the endings -------------------------------------------------------------

DROP_DELAYS = (0, 1, 2, 3, 4, 6, 8, 10, 12, 15, 20)
"""How long the automation strategy keeps its last humans past the point where
the fleet could carry the projects alone."""


def endings_sweep(seeds: int, turns: int) -> None:
    """Which ending an automating run gets, as a function of one decision.

    Total automation is checked at the *end* of the round it first holds
    (``Game._check_game_over``), so the ending is decided by where alignment
    stands in the round the last human is fired - not by how the fleet was built.
    This sweep turns exactly that dial and leaves everything else alone.
    """
    automation = next(s for s in STRATEGIES if s.name == "automation")
    variants = (
        ("Stufe 2", automation),
        ("Stufe 2 + KI-Alignment", replace(
            automation, research_plan=("ai_intelligence_2", "ai_alignment"))),
        ("Stufe 3", replace(
            automation,
            research_plan=("ai_intelligence_2", "ai_intelligence_3"),
            researcher_level=3)),
    )
    for label, strategy in variants:
        print(f"\n{label}")
        for delay in DROP_DELAYS:
            results = [
                run(replace(strategy, drop_delay=delay), seed, turns)
                for seed in range(1, seeds + 1)
            ]
            counts: dict[str, int] = {}
            for result in results:
                counts[result.outcome] = counts.get(result.outcome, 0) + 1
            tally = ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
            alignments = sorted(round(r.end_alignment) for r in results)
            print(
                f"  +{delay:>2} Runden Mensch  {tally:<44} "
                f"⚖ {alignments[0]:>3}-{alignments[-1]:<3} "
                f"R{min(r.turns for r in results)}-{max(r.turns for r in results)}"
            )


# -- reporting ---------------------------------------------------------------


def summarise(strategy: Strategy, results: list[RunResult]) -> str:
    outcomes: dict[str, list[RunResult]] = {}
    for result in results:
        outcomes.setdefault(result.outcome, []).append(result)
    parts = []
    for outcome, runs in sorted(outcomes.items(), key=lambda kv: -len(kv[1])):
        span = f"R{min(r.turns for r in runs)}-{max(r.turns for r in runs)}"
        parts.append(f"{outcome} {len(runs)}/{len(results)} ({span})")
    low = statistics.median(r.min_money for r in results)
    return f"{strategy.name:<22} {'; '.join(parts):<58} Median-Tiefststand {low:>9.0f} €"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turns", type=int, default=60)
    parser.add_argument("--seeds", type=int, default=11)
    parser.add_argument("--only", default=None, help="run one strategy by name")
    parser.add_argument("--verbose", action="store_true", help="print every round")
    parser.add_argument("--blueprint", default=None, help="override the project blueprint")
    parser.add_argument(
        "--endings",
        action="store_true",
        help="sweep how long the last humans are kept, and report which ending fires",
    )
    parser.add_argument(
        "--projects", type=int, default=None, help="override how many projects run at once"
    )
    parser.add_argument(
        "--steady",
        action="store_true",
        help="per-blueprint income and costs once the attributes have settled",
    )
    args = parser.parse_args()

    if args.steady:
        steady_state()
        return
    if args.endings:
        endings_sweep(args.seeds, args.turns)
        return

    strategies = [s for s in STRATEGIES if args.only in (None, s.name)]
    if args.blueprint:
        strategies = [replace(s, blueprint=args.blueprint) for s in strategies]
    if args.projects:
        strategies = [replace(s, max_projects=args.projects) for s in strategies]
    for strategy in strategies:
        results = []
        for seed in range(1, args.seeds + 1):
            if args.verbose:
                print(f"{strategy.name} seed {seed}")
            results.append(run(strategy, seed, args.turns, args.verbose))
        print(summarise(strategy, results))


if __name__ == "__main__":
    main()
