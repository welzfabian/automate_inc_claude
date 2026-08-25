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
    PYTHONPATH=src python3 tools/simulate.py --dividend       # what the investors really take
    PYTHONPATH=src python3 tools/simulate.py --guards         # which go/no-go guards ever bind

The findings this produced are written up in ``docs/BALANCING.md`` under
"Nach M7" and "Nach M8", one invocation named above each table.

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
from automate_inc.core.projects import ProjectBlueprint, load_registry, load_tuning
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
    blueprint: str | None = None
    """Restrict the policy to a single job. ``None`` climbs the ladder instead:
    every blueprint exists once (M8), so repeating one is no longer a plan."""
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
    max_projects: int = 3
    """Jobs run at once. Three since M8: the ladder is climbed by taking on more
    work, not by repeating one job, and a policy limited to one project never
    gets past the third rung."""
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
    prudent: bool = True
    """Refuse a job whose fully staffed team would cost more than it earns.

    A player can read that off the catalogue before signing (posts, income and
    fixed costs are all on the menu line), so a policy that signs anyway is
    measuring its own recklessness rather than the balance.

    **It currently measures nothing.** Over every strategy below the guard
    changes not one decision: the rungs where a full team runs at a loss sit at
    seven and eight posts, and no policy that gets that far up the ladder is
    staffed in a way that loses money there (BALANCING.md 40). Kept because it
    is the right guard for a future catalogue, not because it is doing work -
    ``--guards`` prints how often it, and every other go/no-go check, binds."""

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
    _lay_off_surplus(game, strategy)
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
    (BALANCING.md 24), so an unaffordable job is worse than no job at all.
    """
    if not any(w.is_senior for w in game.state.workers):
        # Nothing to run a project with yet - hire the first responsible worker.
        _hire(game, Role.DEVELOPER, strategy.senior_plan(), 0.0)
    while len(game.state.active_projects) < strategy.max_projects:
        blueprint = _pick_blueprint(game, strategy)
        if blueprint is None or not game.start_project(blueprint.id).ok:
            return
        _staff_up(game, strategy)


def _pick_blueprint(game: Game, strategy: Strategy) -> ProjectBlueprint | None:
    """The biggest job still on offer that the company could actually take on.

    Biggest-first is the profit-maximising read of the ladder and the one that
    stresses the balance hardest: it walks the catalogue down from the top until
    something is both payable and staffable, instead of working politely upwards.
    """
    offered = game.available_blueprints()
    if strategy.blueprint is not None:
        # Restricting to one job means restricting to the way up to it as well -
        # every rung above the first wants a smaller job on the record (M8).
        wanted = reference_chain(strategy.blueprint)
        offered = [bp for bp in offered if bp.id in wanted]
    for blueprint in sorted(offered, key=lambda bp: -sum(bp.required_roles.values())):
        if game.state.money < strategy.reserve + _staffing_cost(game, strategy, blueprint):
            continue
        if strategy.prudent and _expected_net(game, strategy, blueprint) <= 0:
            continue
        if _fits_in_the_office(game, strategy, blueprint):
            return blueprint
    return None


def _expected_net(game: Game, strategy: Strategy, blueprint: ProjectBlueprint) -> float:
    """What a fully staffed team would clear per round on this job.

    Assumes the attributes have reached their caps, which a full team always does
    - so this is the steady state ``--steady`` prints, not the ramp. A level-1
    plan also needs one senior beside the fleet (BALANCING.md 24); that worker is
    not counted here, so the estimate is mildly optimistic for exactly that plan.
    """
    kind, level = strategy.staff(game.modifiers)
    wages = visibility = 0.0
    for role, count in blueprint.required_roles.items():
        worker = Worker(id="_", role=role, worker_type=kind, level=level)
        cost = worker.cost_per_round(game.modifiers)
        wages += count * (cost.money + cost.tokens * game.state.token_price)
        if role is Role.SALES:
            visibility += count * load_tuning().sales_visibility_bonus * worker.efficiency
    income = blueprint.base_income * (1.0 + visibility / 100.0)
    return income - wages - blueprint.basis_fixed_costs


def _staffing_cost(game: Game, strategy: Strategy, blueprint: ProjectBlueprint) -> float:
    """One round of pay for a full team on the blueprint, as a go/no-go budget."""
    kind, level = strategy.staff(game.modifiers)
    return sum(
        count * game.hiring_cost(role, kind, level)
        for role, count in blueprint.required_roles.items()
    )


def _fits_in_the_office(game: Game, strategy: Strategy, blueprint: ProjectBlueprint) -> bool:
    """Whether a human-staffed plan still has desks for one more team (M5).

    A project nobody can be hired for is worse than no project at all: it earns
    nothing, it pays ``basis_fixed_costs`` every round, and its service level
    only falls. Without this check the office cap looks like a bankruptcy in the
    numbers when it is really a refusal to start.
    """
    kind, _ = strategy.staff(game.modifiers)
    if kind is not WorkerType.HUMAN:
        return True
    # Surplus people are let go in the same turn (``_lay_off_surplus``), so the
    # head count this plan settles at is exactly the number of posts it owes -
    # counting who happens to sit there right now would let a sales worker left
    # over from the last job block a developer's desk on the next one.
    posts = sum(blueprint.required_roles.values()) + sum(
        sum(p.required_roles.values()) for p in game.state.active_projects
    )
    return posts <= game.state.office_capacity


def _assign(game: Game) -> None:
    for worker in game.state.workers:
        if worker.assigned_to is not None or worker.role is Role.RESEARCHER:
            continue
        for project in game.projects_needing(worker.role):
            if game.assign_worker(worker.id, project.id).ok:
                break


def _lay_off_surplus(game: Game, strategy: Strategy) -> None:
    """Let go of whoever no running job has a post for.

    The ladder makes this a real move: each rung wants a different mix, so the
    sales worker who carried the customer app is dead weight on the web app -
    a desk in the office and a salary against no income. Researchers are exempt
    (they never take a post), and the company always keeps someone answerable
    so its running projects do not slide (BALANCING.md 24).
    """
    for worker in list(game.state.workers):
        if worker.assigned_to is not None or worker.role is Role.RESEARCHER:
            continue
        if any(game.free_slots(p, worker.role) for p in game.state.active_projects):
            continue
        others = [w for w in game.state.workers if w is not worker]
        if worker.is_senior and not any(w.is_senior for w in others):
            continue
        game.fire_worker(worker.id)


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
    jobs_done: int = 0
    """Blueprints commissioned - how far up the ladder the run actually got."""
    biggest_job: int = 0
    """Posts on the largest job taken. The rung, in the only unit that matters."""
    catalogue_left: int = 0
    """Jobs still on offer at the end. Zero means the company ran out of work -
    the pressure M8 leaves for the products milestone to answer."""


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
        jobs_done=len(game.state.started_projects),
        biggest_job=max(
            (
                sum(bp.required_roles.values())
                for bp in (game.registry.get(i) for i in game.state.started_projects)
                if bp is not None
            ),
            default=0,
        ),
        catalogue_left=len(game.available_blueprints()),
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
        name="humans-greedy",
        staff=humans_only,
        prudent=False,
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


def reference_chain(blueprint_id: str) -> set[str]:
    """A job and every job that has to be on the record before it (M8)."""
    registry = load_registry()
    chain: set[str] = set()
    pending = [blueprint_id]
    while pending:
        blueprint = registry.get(pending.pop())
        if blueprint is None or blueprint.id in chain:
            continue
        chain.add(blueprint.id)
        pending.extend(blueprint.requires)
    return chain


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
    """Income and total costs per round, once the attributes have settled."""
    report = _settle_report(blueprint_id, kind, level, token_price)
    return report.income, report.costs_money + report.costs_tokens * token_price


def _settle_report(
    blueprint_id: str, kind: WorkerType, level: int, token_price: float
) -> TurnReport:
    game = Game(seed=1, event_registry=EventRegistry({}))
    game.state.research = 500
    game.research("ai_intelligence_2")
    game.research("ai_intelligence_3")
    game.state.research = 0
    game.state.money = 1e9
    game.state.tokens = 1e9
    game.state.investor_equity = 0.0
    game.state.office_capacity = 99
    # Measuring one job in isolation: put its references on the record rather
    # than playing them out, the same shortcut ``tests/_helpers.unlock`` takes.
    game.state.started_projects = sorted(reference_chain(blueprint_id) - {blueprint_id})
    # The senior has to hold a post this blueprint actually asks for - the ladder
    # has jobs without a developer on it.
    senior_role = next(iter(load_registry().get(blueprint_id).required_roles))
    if kind is WorkerType.AGENT and level >= 2:
        game.hire_worker(senior_role, WorkerType.AGENT, level)
    else:
        game.hire_worker(senior_role, WorkerType.HUMAN)
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
    return report


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


# -- the investor dividend ---------------------------------------------------

DIVIDEND_BLUEPRINTS = (
    "ecommerce_shop",
    "web_app",
    "ki_integration",
    "saas_platform",
    "corporate_suite",
    "group_ai_platform",
)

DIVIDEND_SHARES = (15.0, 40.0)
"""The starting equity (M5) and the cap - the two ends of what a run can owe."""


def dividend_sweep(token_price: float = 10.0) -> None:
    """What the investors take, measured against the round's *real* profit.

    ``Game._pay_investors`` scales the payout off ``income - costs_money``, and
    an agent pays in tokens rather than money. This prints both figures side by
    side so the gap between them is a number rather than an argument
    (BALANCING.md 39).
    """
    print(f"{'Auftrag':<20}{'Besetzung':<12}{'ech.Gewinn':>11}", end="")
    for share in DIVIDEND_SHARES:
        print(f"{f'Div@{share:.0f}%':>10}{'Anteil':>8}", end="")
    print()
    for blueprint_id in DIVIDEND_BLUEPRINTS:
        for label, kind, level in STEADY_STAFF:
            report = _settle_report(blueprint_id, kind, level, token_price)
            real = report.income - report.costs_money - report.costs_tokens * token_price
            if real <= 0:
                continue  # a loss-making staffing pays no dividend anyway
            # What ``_pay_investors`` actually scales the payout off: the token
            # bill is settled separately (``Game._settle``) and never reaches it.
            book = report.income - report.costs_money
            print(f"{blueprint_id:<20}{label:<12}{real:>11.1f}", end="")
            for share in DIVIDEND_SHARES:
                payout = book * share / 100.0
                print(f"{payout:>10.1f}{payout / real:>7.0%}", end="")
            print()
    _dividend_runs()


DIVIDEND_RUN_SHARES = (0.0, 15.0, 40.0)
DIVIDEND_RUN_STRATEGIES = ("humans", "level1-fleet", "dangerous-tree")


def _dividend_runs(seeds: int = 11, turns: int = 60) -> None:
    """The same gap over whole runs: only the starting equity is varied.

    ``raise_funding`` is switched off for all three so that the equity really is
    the only difference - otherwise a policy would sell more of itself mid-run
    and the comparison would measure that instead.
    """
    print(f"\n{seeds} Seeds, {turns} Runden - nur der Investoren-Anteil variiert\n")
    print(f"{'Strategie':<16}{'Anteil':>8}  Ausgang")
    for name in DIVIDEND_RUN_STRATEGIES:
        strategy = replace(
            next(s for s in STRATEGIES if s.name == name), raise_funding=False
        )
        for share in DIVIDEND_RUN_SHARES:
            results = [
                _run_with_equity(strategy, seed, turns, share) for seed in range(1, seeds + 1)
            ]
            counts: dict[str, int] = {}
            for result in results:
                counts[result.outcome] = counts.get(result.outcome, 0) + 1
            tally = ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
            end = statistics.median(r.end_money for r in results)
            print(f"{name:<16}{share:>7.0f}%  {tally:<38} Endgeld {end:>9.0f} €")


def _run_with_equity(
    strategy: Strategy, seed: int, turns: int, equity: float
) -> RunResult:
    """``run`` with the starting equity overridden before the first turn."""
    game = Game(seed=seed)
    game.state.investor_equity = equity
    memo: dict[str, int] = {}
    for _ in range(turns):
        play_turn(game, strategy, memo)
        if game.resolve_turn().blocked or game.state.is_over:
            break
    return RunResult(
        seed=seed,
        outcome=_outcome_of(game),
        turns=game.state.turn,
        end_money=game.state.money,
        end_alignment=game.state.alignment,
    )


# -- how often the go/no-go guards actually bind ------------------------------


def guard_sweep(seeds: int, turns: int) -> None:
    """How often each blueprint guard in ``_pick_blueprint`` changes a decision.

    A guard that never binds is not a safety net, it is decoration - and a
    strategy whose only difference is a guard that never binds measures nothing
    at all. That is the mistake BALANCING.md 22, 25 and 29 each record once;
    this is the check that would have caught it (BALANCING.md 40).
    """
    global _expected_net
    original = _expected_net
    tally: dict[str, dict[str, int]] = {}

    def counted(game: Game, strategy: Strategy, blueprint: ProjectBlueprint) -> float:
        value = original(game, strategy, blueprint)
        row = tally.setdefault(strategy.name, {"seen": 0, "refused": 0})
        row["seen"] += 1
        if value <= 0:
            row["refused"] += 1
        return value

    _expected_net = counted
    try:
        for strategy in STRATEGIES:
            for seed in range(1, seeds + 1):
                run(strategy, seed, turns)
    finally:
        _expected_net = original

    print(f"{'Strategie':<22}{'bewertet':>10}{'abgelehnt':>11}")
    for strategy in STRATEGIES:
        if not strategy.prudent:
            print(f"{strategy.name:<22}{'Sperre aus':>10}{'-':>11}")
            continue
        row = tally.get(strategy.name, {"seen": 0, "refused": 0})
        print(f"{strategy.name:<22}{row['seen']:>10}{row['refused']:>11}")

    # The counts alone would still leave "but does it matter?" open. A refusal
    # only matters if taking the job would have played out differently, and the
    # other two guards (reserve, office) reject the same jobs first - so the A/B
    # is the finding, not the tally.
    print("\nDieselbe Politik mit und ohne Sperre:")
    for strategy in STRATEGIES:
        if not strategy.prudent:
            continue
        both = [
            [run(replace(strategy, prudent=flag), seed, turns) for seed in range(1, seeds + 1)]
            for flag in (True, False)
        ]
        verdict = "identisch" if _outcomes(both[0]) == _outcomes(both[1]) else "UNTERSCHIED"
        print(f"  {strategy.name:<22}{verdict}")


def _outcomes(results: list[RunResult]) -> list[tuple[str, int, float]]:
    return [(r.outcome, r.turns, round(r.end_money, 2)) for r in results]


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
    jobs = statistics.median(r.jobs_done for r in results)
    rung = statistics.median(r.biggest_job for r in results)
    dry = sum(1 for r in results if r.catalogue_left == 0)
    return (
        f"{strategy.name:<22} {'; '.join(parts):<56} Tief {low:>7.0f} € "
        f"Aufträge {jobs:>4.1f} größte Stufe {rung:>3.1f} Katalog leer {dry}/{len(results)}"
    )


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
    parser.add_argument(
        "--dividend",
        action="store_true",
        help="what the investors take, against the round's real profit",
    )
    parser.add_argument(
        "--guards",
        action="store_true",
        help="how often each go/no-go guard actually changes a decision",
    )
    args = parser.parse_args()

    if args.steady:
        steady_state()
        return
    if args.dividend:
        dividend_sweep()
        return
    if args.guards:
        guard_sweep(args.seeds, args.turns)
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
