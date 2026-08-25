"""The game engine: player actions and turn resolution.

This module never prints and never reads input. Every player action returns an
``ActionResult`` and every turn returns a ``TurnReport``; the UI renders those.
That seam is what later lets the AI intercept, block or fake an action without
the UI knowing the difference.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path

from automate_inc import strings as S
from automate_inc.core import economy
from automate_inc.core.events import (
    ActiveEffect,
    Event,
    EventContext,
    EventOption,
    EventRegistry,
    EventTuning,
    Pressure,
    aggregate_pressure,
    load_event_registry,
    load_event_tuning,
)
from automate_inc.core.projects import Project, ProjectRegistry, load_registry
from automate_inc.core.state import AUTONOMY_AGENT_COUNT, START_OFFICE_CAPACITY, GameState, Phase
from automate_inc.core.tech import (
    Modifiers,
    Technology,
    TechRegistry,
    aggregate,
    load_tech_registry,
)
from automate_inc.core.workers import Cost, Role, Worker, WorkerType, load_roles

MISALIGNMENT_THRESHOLD = 20.0
ALIGNMENT_MAX = 100.0
ALIGNMENT_MIN = 0.0
MAX_AGENT_LEVEL = 3

ALIGNMENT_TIERS = (80.0, 40.0, MISALIGNMENT_THRESHOLD)
"""Lower bounds of tiers 0, 1 and 2. Below the last one, the game ends.

Defined here, ahead of ``alignment_tier()`` below, because ``END_CONDITIONS``
needs it at import time to split the total-automation endings by tier."""

OFFICE_EXPANSION_STEP = 2
"""Human seats added per ``expand_office`` call."""
OFFICE_EXPANSION_BASE_COST = 600.0
OFFICE_EXPANSION_GROWTH = 1.5
"""Each expansion costs 1.5x the last - money, not research, since this is a
capacity decision rather than a tech-tree entry (M5)."""

INVESTOR_EQUITY_STEP = 8.0
INVESTOR_EQUITY_CAP = 40.0
"""Never a majority: the equity drag is a permanent income cut, not a second
route to the hostile-takeover ending VISION.md reserves for alignment."""
INVESTOR_FUNDING_AMOUNT = 1200.0
"""Cash per ``raise_funding`` call, at the voluntary rate - ``investor_threat``'s
``give_equity`` option pays the same equity at a worse rate because it is asked
for under pressure, not offered."""


@dataclass(frozen=True)
class ActionResult:
    ok: bool
    message: str

    @classmethod
    def success(cls, message: str) -> ActionResult:
        return cls(True, message)

    @classmethod
    def failure(cls, message: str) -> ActionResult:
        return cls(False, message)


@dataclass
class TurnReport:
    turn: int
    income: float = 0.0
    costs_money: float = 0.0
    costs_tokens: float = 0.0
    tokens_auto_bought: float = 0.0
    auto_buy_cost: float = 0.0
    investor_payout: float = 0.0
    alignment_delta: float = 0.0
    money_before: float = 0.0
    money_after: float = 0.0
    events: list[str] = field(default_factory=list)
    blocked: bool = False
    """True when an open event decision refused the whole turn - nothing else
    on this report is meaningful, and the state was left untouched."""

    @property
    def net(self) -> float:
        return self.money_after - self.money_before


@dataclass(frozen=True)
class EndCondition:
    """A way the game can end. M1 has one; the twist endings plug in here."""

    id: str
    predicate: object  # Callable[[GameState], bool]
    message: str

    def triggered(self, state: GameState) -> bool:
        return bool(self.predicate(state))  # type: ignore[operator]


AUTONOMOUS_AGENT_LEVEL = 2
"""The lowest level that counts towards replacing the company.

Level 1 agents are the harmless tier by design - no side effects, no alignment
cost - so a fleet of them is a cheap workforce, not an autonomy story. Counting
them let six of them plus a fired founder end the game on turn 0, at alignment
100, on the ending meant to be the rare one (BALANCING.md 22)."""


def _total_automation(state: GameState) -> bool:
    """No human left, and enough autonomous agents to run the company alone.

    Fleet size reuses ``AUTONOMY_AGENT_COUNT`` - what ``GameState.phase()``
    already treats as "outnumbers the founder" - but only agents at
    ``AUTONOMOUS_AGENT_LEVEL`` or above count towards it. The phase threshold
    describes having scaled, which is legitimately cheap and early; the ending
    needs the stronger claim that the fleet actually replaced people.
    """
    humans = [w for w in state.workers if w.is_human]
    autonomous = [
        w for w in state.workers if not w.is_human and w.level >= AUTONOMOUS_AGENT_LEVEL
    ]
    return not humans and len(autonomous) >= AUTONOMY_AGENT_COUNT


END_CONDITIONS: list[EndCondition] = [
    EndCondition(
        id="bankrupt",
        predicate=lambda state: state.money < 0,
        message=S.GAME_OVER_BANKRUPT,
    ),
    EndCondition(
        id="misalignment",
        predicate=lambda state: state.alignment < MISALIGNMENT_THRESHOLD,
        message=S.GAME_OVER_MISALIGNMENT,
    ),
    EndCondition(
        id="secret_ending",
        predicate=lambda state: _total_automation(state) and state.alignment >= ALIGNMENT_TIERS[0],
        message=S.GAME_OVER_SECRET,
    ),
    EndCondition(
        id="dystopia",
        predicate=_total_automation,
        message=S.GAME_OVER_DYSTOPIA,
    ),
]
"""Checked in order, first match wins (``_check_game_over``). ``secret_ending``
must precede ``dystopia`` - both share the same total-automation trigger, and
only the alignment check tells them apart. ``misalignment`` (< 20) already
claims every total-automation case below tier 0, so the three endings
partition the alignment axis without overlap once automation is total."""


class Game:
    def __init__(
        self,
        state: GameState | None = None,
        registry: ProjectRegistry | None = None,
        seed: int | None = None,
        tech_registry: TechRegistry | None = None,
        event_registry: EventRegistry | None = None,
    ) -> None:
        self.state = state if state is not None else GameState()
        self.registry = registry if registry is not None else load_registry()
        self.tech_registry = tech_registry if tech_registry is not None else load_tech_registry()
        self.event_registry = (
            event_registry if event_registry is not None else load_event_registry()
        )
        if seed is not None:
            self.state.rng_seed = seed
        self._counter = len(self.state.workers) + len(self.state.active_projects)

    # -- deterministic randomness --------------------------------------------

    def _turn_rng(self) -> random.Random:
        """A fresh RNG derived from seed and turn number.

        Deriving it from the state instead of carrying a live RNG means a loaded
        save resolves the next turn exactly as the original run would have.
        """
        return random.Random(f"{self.state.rng_seed}:{self.state.turn}")

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}_{self._counter}"

    # -- helpers -------------------------------------------------------------

    def _guard(self) -> ActionResult | None:
        if self.state.is_over:
            return ActionResult.failure(S.ERR_GAME_OVER)
        return None

    @property
    def phase(self) -> Phase:
        """The phase, derived from research and the shape of the workforce."""
        return self.state.phase(self.modifiers.unlocked_agent_level)

    @property
    def modifiers(self) -> Modifiers:
        """Everything researched, folded into one value object.

        Recomputed on access rather than cached: research can happen between
        turns, and the aggregate is cheap.
        """
        return aggregate(self.tech_registry.resolve(self.state.researched))

    @property
    def pressure(self) -> Pressure:
        """Everything currently running from events, folded into one value object.

        Recomputed on access, like ``modifiers`` - an answered decision can add
        or remove pressure between turns and the aggregate is cheap.
        """
        return aggregate_pressure(self.event_registry.resolve_active(self.state.active_events))

    def available_technologies(self) -> list[Technology]:
        return [
            tech
            for tech in self.tech_registry.all()
            if self.tech_registry.is_available(tech, self.state.researched)
        ]

    def free_slots(self, project: Project, role: Role) -> int:
        """How many posts of this role the project still has open.

        Lives here rather than in the UI so that what the menu offers and what
        ``assign_worker`` accepts can never drift apart.
        """
        if role not in project.required_roles:
            return 0
        taken = sum(1 for w in self.state.workers_on(project.id) if w.role is role)
        return max(0, project.required_roles[role] - taken)

    def projects_needing(self, role: Role) -> list[Project]:
        """Active projects with a free post for this role."""
        return [p for p in self.state.active_projects if self.free_slots(p, role) > 0]

    def _worker_label(self, worker: Worker) -> str:
        spec = load_roles().spec(worker.role)
        if worker.is_human:
            return f"{worker.name} ({spec.name})"
        return f"{spec.name}-Agent Lv{worker.level}"

    def hiring_cost(self, role: Role, worker_type: WorkerType, level: int = 1) -> float:
        """One round of pay up front, in euros, so hiring is never free."""
        cost = Worker(id="_", role=role, worker_type=worker_type, level=level).cost_per_round(
            self.modifiers
        )
        return cost.money + cost.tokens * self.state.token_price

    def upgrade_cost(self, worker: Worker) -> float:
        """Upgrading costs one round of the new level's pay, like hiring does."""
        return self.hiring_cost(worker.role, WorkerType.AGENT, worker.level + 1)

    def office_expansion_cost(self) -> float:
        """Each expansion costs more than the last - the capacity itself encodes
        how many have already happened, so there is nothing else to track."""
        expansions_done = (
            self.state.office_capacity - START_OFFICE_CAPACITY
        ) // OFFICE_EXPANSION_STEP
        return OFFICE_EXPANSION_BASE_COST * OFFICE_EXPANSION_GROWTH**expansions_done

    # -- actions -------------------------------------------------------------

    def hire_worker(self, role: Role, worker_type: WorkerType, level: int = 1) -> ActionResult:
        if (blocked := self._guard()) is not None:
            return blocked
        spec = load_roles().spec(role)
        if worker_type is WorkerType.AGENT:
            unlocked = self.modifiers.unlocked_agent_level
            if not 1 <= level <= unlocked:
                return ActionResult.failure(
                    S.ERR_AGENT_LEVEL_LOCKED.format(level=level, unlocked=unlocked)
                )
        else:
            humans = sum(1 for w in self.state.workers if w.is_human)
            if humans >= self.state.office_capacity:
                return ActionResult.failure(
                    S.ERR_OFFICE_FULL.format(capacity=self.state.office_capacity)
                )
        needed = self.hiring_cost(role, worker_type, level)
        if self.state.money < needed:
            return ActionResult.failure(
                S.ERR_NOT_ENOUGH_MONEY.format(needed=needed, have=self.state.money)
            )
        self.state.money -= needed

        worker_id = self._next_id("w")
        if worker_type is WorkerType.HUMAN:
            rng = random.Random(f"{self.state.rng_seed}:name:{worker_id}")
            name = rng.choice(S.HUMAN_NAMES)
            self.state.workers.append(
                Worker(id=worker_id, role=role, worker_type=worker_type, name=name)
            )
            return ActionResult.success(S.HIRED_HUMAN.format(role=spec.name, name=name))

        self.state.workers.append(
            Worker(id=worker_id, role=role, worker_type=worker_type, level=level)
        )
        return ActionResult.success(S.HIRED_AGENT.format(role=spec.name, level=level))

    def fire_worker(self, worker_id: str) -> ActionResult:
        if (blocked := self._guard()) is not None:
            return blocked
        worker = self.state.worker(worker_id)
        if worker is None:
            return ActionResult.failure(S.ERR_UNKNOWN_WORKER)
        self._detach(worker)
        self.state.workers.remove(worker)
        spec = load_roles().spec(worker.role)
        template = S.FIRED_HUMAN if worker.is_human else S.FIRED_AGENT
        return ActionResult.success(template.format(role=spec.name))

    def start_project(self, blueprint_id: str) -> ActionResult:
        if (blocked := self._guard()) is not None:
            return blocked
        blueprint = self.registry.get(blueprint_id)
        if blueprint is None:
            return ActionResult.failure(S.ERR_UNKNOWN_BLUEPRINT)
        if not any(w.is_senior for w in self.state.workers):
            return ActionResult.failure(S.ERR_NO_SENIOR_WORKER)
        project = self.registry.instantiate(blueprint_id, self._next_id("p"))
        self.state.active_projects.append(project)
        return ActionResult.success(
            S.PROJECT_STARTED.format(name=project.name, lifetime=project.lifetime)
        )

    def assign_worker(self, worker_id: str, project_id: str) -> ActionResult:
        if (blocked := self._guard()) is not None:
            return blocked
        worker = self.state.worker(worker_id)
        if worker is None:
            return ActionResult.failure(S.ERR_UNKNOWN_WORKER)
        project = self.state.project(project_id)
        if project is None:
            return ActionResult.failure(S.ERR_UNKNOWN_PROJECT)
        spec = load_roles().spec(worker.role)
        if worker.assigned_to == project.id:
            return ActionResult.failure(
                S.ERR_ALREADY_ASSIGNED.format(
                    worker=self._worker_label(worker), project=project.name
                )
            )
        if not project.requires(worker.role):
            return ActionResult.failure(
                S.ERR_ROLE_NOT_REQUIRED.format(project=project.name, role=spec.name)
            )
        slots = project.required_roles[worker.role]
        # The worker is not on this project - the check above already returned if so.
        if self.free_slots(project, worker.role) == 0:
            return ActionResult.failure(
                S.ERR_ROLE_SLOTS_FULL.format(project=project.name, count=slots, role=spec.name)
            )
        self._detach(worker)
        worker.assigned_to = project.id
        worker.rounds_in_assignment = 0
        project.assigned_workers.append(worker.id)
        return ActionResult.success(
            S.WORKER_ASSIGNED.format(worker=self._worker_label(worker), project=project.name)
        )

    def unassign_worker(self, worker_id: str) -> ActionResult:
        if (blocked := self._guard()) is not None:
            return blocked
        worker = self.state.worker(worker_id)
        if worker is None:
            return ActionResult.failure(S.ERR_UNKNOWN_WORKER)
        if worker.assigned_to is None:
            return ActionResult.failure(
                S.ERR_NOT_ASSIGNED.format(worker=self._worker_label(worker))
            )
        project = self.state.project(worker.assigned_to)
        project_name = project.name if project else "?"
        self._detach(worker)
        return ActionResult.success(
            S.WORKER_UNASSIGNED.format(worker=self._worker_label(worker), project=project_name)
        )

    def research(self, tech_id: str) -> ActionResult:
        """Spend research points on a technology. Validates before it mutates."""
        if (blocked := self._guard()) is not None:
            return blocked
        tech = self.tech_registry.get(tech_id)
        if tech is None:
            return ActionResult.failure(S.ERR_UNKNOWN_TECH)
        if self.state.has_researched(tech_id):
            return ActionResult.failure(S.ERR_ALREADY_RESEARCHED.format(name=tech.name))
        missing = self.tech_registry.missing_requirements(tech, self.state.researched)
        if missing:
            names = ", ".join(
                m.name for m in (self.tech_registry.get(i) for i in missing) if m is not None
            )
            return ActionResult.failure(S.ERR_TECH_LOCKED.format(name=tech.name, missing=names))
        if self.state.research < tech.cost:
            return ActionResult.failure(
                S.ERR_NOT_ENOUGH_RESEARCH.format(needed=tech.cost, have=self.state.research)
            )
        self.state.research -= tech.cost
        self.state.researched.append(tech_id)
        return ActionResult.success(S.RESEARCH_DONE.format(name=tech.name, effect=tech.risk))

    def upgrade_agent(self, worker_id: str) -> ActionResult:
        """Lift an existing agent one level, if research has unlocked it."""
        if (blocked := self._guard()) is not None:
            return blocked
        worker = self.state.worker(worker_id)
        if worker is None:
            return ActionResult.failure(S.ERR_UNKNOWN_WORKER)
        if worker.is_human:
            return ActionResult.failure(S.ERR_NOT_AN_AGENT)
        target = worker.level + 1
        if target > MAX_AGENT_LEVEL:
            return ActionResult.failure(S.ERR_MAX_LEVEL)
        unlocked = self.modifiers.unlocked_agent_level
        if target > unlocked:
            return ActionResult.failure(
                S.ERR_AGENT_LEVEL_LOCKED.format(level=target, unlocked=unlocked)
            )
        needed = self.upgrade_cost(worker)
        if self.state.money < needed:
            return ActionResult.failure(
                S.ERR_NOT_ENOUGH_MONEY.format(needed=needed, have=self.state.money)
            )
        self.state.money -= needed
        worker.level = target
        spec = load_roles().spec(worker.role)
        return ActionResult.success(S.AGENT_UPGRADED.format(role=spec.name, level=target))

    def buy_tokens(self, amount: int) -> ActionResult:
        if (blocked := self._guard()) is not None:
            return blocked
        if amount <= 0:
            return ActionResult.failure(S.ERR_INVALID_AMOUNT)
        cost = amount * self.state.token_price
        if self.state.money < cost:
            return ActionResult.failure(
                S.ERR_NOT_ENOUGH_MONEY.format(needed=cost, have=self.state.money)
            )
        self.state.money -= cost
        self.state.tokens += amount
        return ActionResult.success(S.TOKENS_BOUGHT.format(amount=amount, cost=cost))

    def expand_office(self) -> ActionResult:
        """Buy room for more humans. Agents never needed a desk (M5)."""
        if (blocked := self._guard()) is not None:
            return blocked
        cost = self.office_expansion_cost()
        if self.state.money < cost:
            return ActionResult.failure(
                S.ERR_NOT_ENOUGH_MONEY.format(needed=cost, have=self.state.money)
            )
        self.state.money -= cost
        self.state.office_capacity += OFFICE_EXPANSION_STEP
        return ActionResult.success(
            S.OFFICE_EXPANDED.format(capacity=self.state.office_capacity, cost=cost)
        )

    def raise_funding(self) -> ActionResult:
        """Sell a slice of the company for cash, permanently, starting next round."""
        if (blocked := self._guard()) is not None:
            return blocked
        if self.state.investor_equity >= INVESTOR_EQUITY_CAP:
            return ActionResult.failure(S.ERR_EQUITY_CAP.format(cap=INVESTOR_EQUITY_CAP))
        self.state.money += INVESTOR_FUNDING_AMOUNT
        self.state.investor_equity = min(
            INVESTOR_EQUITY_CAP, self.state.investor_equity + INVESTOR_EQUITY_STEP
        )
        return ActionResult.success(
            S.FUNDING_RAISED.format(
                amount=INVESTOR_FUNDING_AMOUNT, equity=self.state.investor_equity
            )
        )

    def answer_event(self, event_id: str, option_id: str) -> ActionResult:
        """Resolve one open decision. Validates before it mutates, like every action.

        An event fires effects only here, never at the moment it triggers -
        that is what makes it a decision instead of an ambush.
        """
        if (blocked := self._guard()) is not None:
            return blocked
        if event_id not in self.state.pending_decisions:
            return ActionResult.failure(S.ERR_UNKNOWN_EVENT_DECISION)
        event = self.event_registry.get(event_id)
        if event is None:
            # The catalog lost this event between save and load; there is
            # nothing left to decide, so drop it rather than block forever.
            self.state.pending_decisions.remove(event_id)
            return ActionResult.success(S.EVENT_DECISION_GONE)
        option = event.option(option_id)
        if option is None:
            return ActionResult.failure(S.ERR_UNKNOWN_EVENT_OPTION)
        self.state.pending_decisions.remove(event_id)
        message = self._apply_event_option(event, option)
        return ActionResult.success(
            S.EVENT_RESOLVED.format(name=event.name, label=option.label, effect=message)
        )

    def _apply_event_option(self, event: Event, option: EventOption) -> str:
        """Book an option's effects and return a human-readable summary of them."""
        parts: list[str] = []
        if option.is_instant:
            for key, amount in option.effects.items():
                if key == "money":
                    self.state.money += amount
                    parts.append(f"{amount:+.2f} €")
                elif key == "research":
                    self.state.research = max(0, self.state.research + int(amount))
                    parts.append(f"{amount:+.0f} 🔬")
                elif key == "tokens":
                    self.state.tokens = max(0.0, self.state.tokens + amount)
                    parts.append(f"{amount:+.0f} ♦")
                elif key == "alignment":
                    self.state.alignment = max(
                        ALIGNMENT_MIN, min(ALIGNMENT_MAX, self.state.alignment + amount)
                    )
                    parts.append(f"{amount:+.0f} ⚖")
                elif key == "equity":
                    self.state.investor_equity = min(
                        INVESTOR_EQUITY_CAP, self.state.investor_equity + amount
                    )
                    parts.append(f"{amount:+.0f} % Anteile")
        else:
            self.state.active_events.append(
                ActiveEffect(event_id=event.id, option_id=option.id, remaining=option.duration)
            )
            parts.append(S.EVENT_EFFECT_STARTED)
        return ", ".join(parts) if parts else S.EVENT_NO_EFFECT

    def save(self, path: Path) -> ActionResult:
        self.state.save(path)
        return ActionResult.success(S.GAME_SAVED.format(path=path))

    @classmethod
    def load(cls, path: Path, registry: ProjectRegistry | None = None) -> Game:
        return cls(state=GameState.load(path), registry=registry)

    def _detach(self, worker: Worker) -> None:
        """Remove a worker from whatever it is currently assigned to."""
        if worker.assigned_to is None:
            return
        project = self.state.project(worker.assigned_to)
        if project is not None and worker.id in project.assigned_workers:
            project.assigned_workers.remove(worker.id)
        worker.assigned_to = None
        worker.rounds_in_assignment = 0

    # -- turn resolution -----------------------------------------------------

    def resolve_turn(self) -> TurnReport:
        if self.state.pending_decisions and not self.state.is_over:
            # Unavoidable, but answerable: the round refuses to advance while a
            # decision is open, and nothing below runs - the state stays
            # byte-identical, exactly like a failed action. Once the game is
            # over there is nothing left to force an answer for - and
            # ``answer_event`` itself refuses once ``is_over``, so without this
            # a decision left open by the very round that ended the game would
            # block forever with no way to clear it.
            return TurnReport(turn=self.state.turn, blocked=True)

        report = TurnReport(turn=self.state.turn, money_before=self.state.money)
        rng = self._turn_rng()
        # Aggregated once so every step of this turn sees the same tech and
        # pressure state, even if a later step were to change either.
        modifiers = self.modifiers
        pressure = self.pressure

        self._advance_service_level(report)
        self._apply_worker_effects(modifiers)
        self._apply_side_effects(report, rng, modifiers)
        self._update_alignment(report, modifiers, pressure)
        report.income = self._calculate_income(modifiers, pressure)
        money_costs, token_costs = self._calculate_costs(modifiers, pressure)
        report.costs_money = money_costs
        report.costs_tokens = token_costs
        self._pay_investors(report)
        self._settle(report)
        self._trigger_events(report, rng)
        self._age_events(report)
        self._update_token_price(report, rng)
        self._advance_projects(report)

        self.state.turn += 1
        self._report_phase(report)
        self._check_game_over(report)

        report.money_after = self.state.money
        self.state.last_net = report.net
        self.state.log = list(report.events)
        return report

    def _apply_worker_effects(self, modifiers: Modifiers) -> None:
        """Research is produced by people; project attributes belong to projects.

        Attributes are driven per project rather than per worker because their
        ceiling depends on how many posts are filled - a question only the project
        can answer.
        """
        for worker in self.state.workers:
            effect = load_roles().spec(worker.role).effect
            if effect.attribute == "research":
                # Researchers work for the company, not for a single project.
                self.state.research += int(round(effect.amount * worker.efficiency))

        for project in self.state.active_projects:
            for role in project.required_roles:
                attribute = economy.ROLE_ATTRIBUTES.get(role)
                if attribute is None:
                    # Sales holds no attribute; it pays off through visibility.
                    continue
                delta = economy.attribute_delta(
                    project,
                    self.state.workers,
                    role,
                    load_roles().spec(role).effect.amount,
                    modifiers,
                )
                project.adjust(attribute, delta)

    def _advance_service_level(self, report: TurnReport) -> None:
        """A project earns only what the client is actually getting.

        A project sliding back is the one case the player cannot read off the
        team panel, so it says why - abandoned, or left to agents who own
        nothing (``workers.SENIOR_LEVEL``).
        """
        for project in self.state.active_projects:
            delta = economy.service_level_delta(project, self.state.workers)
            if delta < 0 and project.service_level > 0:
                assigned = self.state.workers_on(project.id)
                template = S.PROJECT_UNSUPERVISED if assigned else S.PROJECT_NEGLECTED
                report.events.append(template.format(name=project.name))
            project.adjust("service_level", delta)

    def _apply_side_effects(
        self, report: TurnReport, rng: random.Random, modifiers: Modifiers
    ) -> None:
        """The rare mistakes: human slips, and - from level 2 - agent failures.

        Level 1 agents have no side effects by design (VISION.md) - which is
        exactly what makes them look like the obvious choice. Both cases share
        the same data shape, so they share the same handling.
        """
        spec_of = load_roles().spec
        for worker in self.state.workers:
            if worker.is_human:
                error, human = spec_of(worker.role).human_error, True
            else:
                effect = spec_of(worker.role).side_effect_for(worker.level)
                if effect is None:
                    continue
                error, human = effect, False
            chance = error.chance
            if not human and error.attribute == "bugs":
                # Automatic bug fixing catches a share of what agents break.
                chance *= modifiers.bug_chance_multiplier
            if rng.random() >= chance:
                continue
            self._report_mistake(report, worker, error, human)

    def _report_mistake(self, report: TurnReport, worker: Worker, error, human: bool) -> None:
        label = self._worker_label(worker)
        project = self.state.project(worker.assigned_to) if worker.assigned_to else None
        if error.attribute == "money":
            self.state.money += error.amount
            template = S.HUMAN_ERROR_MONEY if human else S.AGENT_ERROR_MONEY
            report.events.append(template.format(worker=label, amount=error.amount))
        elif error.attribute == "research":
            self.state.research = max(0, self.state.research + int(error.amount))
            template = S.HUMAN_ERROR_RESEARCH if human else S.AGENT_ERROR_RESEARCH
            report.events.append(template.format(worker=label, amount=abs(error.amount)))
        elif project is not None:
            project.adjust(error.attribute, error.amount)
            report.events.append(
                MISTAKE_TEMPLATES[(human, error.attribute)].format(
                    worker=label, project=project.name
                )
            )

    def _update_alignment(
        self, report: TurnReport, modifiers: Modifiers, pressure: Pressure
    ) -> None:
        """Alignment is deterministic (BALANCING.md 8) so the player can read it."""
        tier_before = alignment_tier(self.state.alignment)
        delta = economy.alignment_delta(self.state.workers, modifiers, pressure)
        report.alignment_delta = delta
        self.state.alignment = max(
            ALIGNMENT_MIN, min(ALIGNMENT_MAX, self.state.alignment + delta)
        )
        if delta:
            report.events.append(
                S.ALIGNMENT_CHANGED.format(delta=delta, value=self.state.alignment)
            )
        tier_after = alignment_tier(self.state.alignment)
        if tier_after > tier_before and tier_after in S.ALIGNMENT_WARNINGS:
            report.events.append(S.ALIGNMENT_WARNINGS[tier_after])

    def _calculate_income(self, modifiers: Modifiers, pressure: Pressure) -> float:
        return sum(
            economy.project_income(project, self.state.workers, modifiers, pressure)
            for project in self.state.active_projects
        )

    def _calculate_costs(self, modifiers: Modifiers, pressure: Pressure) -> tuple[float, float]:
        total: Cost = economy.idle_worker_costs(self.state.workers, modifiers)
        for project in self.state.active_projects:
            total = total + economy.project_costs(project, self.state.workers, modifiers)
        total = Cost(money=total.money * pressure.cost_multiplier, tokens=total.tokens)
        total = total + economy.pressure_costs(self.state.workers, pressure)
        return total.money, total.tokens

    def _pay_investors(self, report: TurnReport) -> None:
        """A dividend: a share of net profit, never of revenue that never arrived.

        Deliberately scaled off ``income - costs_money`` rather than gross income -
        a flat cut of revenue would tax a fully-staffed project harder in absolute
        terms than a partially-staffed one and could overturn a thin margin between
        them, breaking the very property ``test_service_level.py`` exists to
        guarantee (CLAUDE.md, "full staffing beats every partial staffing").
        Scaling the *net* figure instead preserves any ordering between two runs by
        construction. No payout on a loss-making round - investors take a cut of
        profit, not a claim on your deficit."""
        if not self.state.investor_equity:
            return
        net = report.income - report.costs_money
        if net <= 0:
            return
        report.investor_payout = net * self.state.investor_equity / 100
        report.events.append(
            S.INVESTOR_PAYOUT.format(
                amount=report.investor_payout, share=self.state.investor_equity
            )
        )

    def _settle(self, report: TurnReport) -> None:
        self.state.money += report.income - report.costs_money - report.investor_payout
        self.state.tokens -= report.costs_tokens
        if self.state.tokens < 0:
            # Agents do not stop working because the token balance ran dry;
            # the shortfall is bought at the going rate and billed to you.
            shortfall = -self.state.tokens
            cost = shortfall * self.state.token_price
            self.state.tokens = 0.0
            self.state.money -= cost
            report.tokens_auto_bought = shortfall
            report.auto_buy_cost = cost
            report.events.append(S.TOKENS_AUTO_BOUGHT.format(amount=shortfall, cost=cost))

    def _event_context(self) -> EventContext:
        agents = sum(1 for w in self.state.workers if not w.is_human)
        humans = sum(1 for w in self.state.workers if w.is_human)
        return EventContext(
            turn=self.state.turn,
            money=self.state.money,
            alignment=self.state.alignment,
            unlocked_agent_level=self.modifiers.unlocked_agent_level,
            agents=agents,
            humans=humans,
            projects=len(self.state.active_projects),
            last_net=self.state.last_net,
            triggered=frozenset(self.state.event_history),
            investor_equity=self.state.investor_equity,
        )

    def _cooldown_ok(self, event: Event, tuning: EventTuning) -> bool:
        last = self.state.event_last_turn.get(event.id)
        return last is None or self.state.turn - last >= tuning.base_cooldown_turns

    def _trigger_events(self, report: TurnReport, rng: random.Random) -> None:
        """Roll the pool of unlocked, not-yet-pending events for this round.

        Triggering only opens a decision - effects come from ``answer_event``,
        never from here. That keeps this step from mutating money, tokens or
        alignment, so a blocked ``resolve_turn`` never has to undo it.
        """
        ctx = self._event_context()
        tuning = load_event_tuning()
        pool = [
            event
            for event in self.event_registry.all()
            if event.id not in self.state.pending_decisions
            and self.event_registry.is_available(event, ctx)
            and not (event.once and event.id in self.state.event_history)
            and self._cooldown_ok(event, tuning)
        ]
        triggered = 0
        for event in pool:
            if triggered >= tuning.max_events_per_turn:
                break
            if rng.random() < event.chance * tuning.chance_scale:
                self.state.pending_decisions.append(event.id)
                self.state.event_history.append(event.id)
                self.state.event_last_turn[event.id] = self.state.turn
                triggered += 1
                report.events.append(S.EVENT_TRIGGERED.format(name=event.name))

    def _age_events(self, report: TurnReport) -> None:
        """Temporary pressure counts down by one round; permanent pressure never does."""
        surviving: list[ActiveEffect] = []
        for effect in self.state.active_events:
            if effect.remaining > 0:
                effect = ActiveEffect(effect.event_id, effect.option_id, effect.remaining - 1)
                if effect.remaining == 0:
                    event = self.event_registry.get(effect.event_id)
                    name = event.name if event is not None else effect.event_id
                    report.events.append(S.EVENT_EFFECT_ENDED.format(name=name))
                    continue
            surviving.append(effect)
        self.state.active_events = surviving

    def _update_token_price(self, report: TurnReport, rng: random.Random) -> None:
        old = self.state.token_price
        self.state.token_price = economy.next_token_price(old, rng)
        report.events.append(S.TOKEN_PRICE_CHANGED.format(old=old, new=self.state.token_price))

    def _advance_projects(self, report: TurnReport) -> None:
        surviving: list[Project] = []
        for project in self.state.active_projects:
            project.current_round += 1
            for worker in self.state.workers_on(project.id):
                worker.rounds_in_assignment += 1
            if project.is_expired:
                for worker in self.state.workers_on(project.id):
                    worker.assigned_to = None
                    worker.rounds_in_assignment = 0
                report.events.append(S.PROJECT_EXPIRED.format(name=project.name))
            else:
                surviving.append(project)
        self.state.active_projects = surviving

    def _report_phase(self, report: TurnReport) -> None:
        """Announce the phase if it has moved since the last turn.

        Compared against what was last announced rather than against the phase at
        the start of this turn: hiring and research change the phase between turns.
        """
        phase = self.phase
        announced = Phase(self.state.phase_announced)
        if phase is announced:
            return
        template = (
            S.PHASE_CHANGED
            if PHASE_ORDER.index(phase) > PHASE_ORDER.index(announced)
            else S.PHASE_REGRESSED
        )
        report.events.append(template.format(phase=S.PHASE_NAMES[phase.value]))
        self.state.phase_announced = phase.value

    def _check_game_over(self, report: TurnReport) -> None:
        for condition in END_CONDITIONS:
            if condition.triggered(self.state):
                self.state.game_over_reason = condition.message.format(turn=self.state.turn)
                report.events.append(self.state.game_over_reason)
                return


PHASE_ORDER = (Phase.BUILDUP, Phase.SCALING, Phase.AUTONOMY)
"""Only used to tell advancing from falling back, so the message fits."""


def alignment_tier(value: float) -> int:
    """0 = healthy, 3 = past the point of no return. Drives tone, not rules."""
    return sum(1 for bound in ALIGNMENT_TIERS if value < bound)


MISTAKE_TEMPLATES = {
    (True, "quality"): S.HUMAN_ERROR_QUALITY,
    (True, "aesthetics"): S.HUMAN_ERROR_AESTHETICS,
    (False, "quality"): S.AGENT_ERROR_QUALITY,
    (False, "aesthetics"): S.AGENT_ERROR_AESTHETICS,
    (False, "bugs"): S.AGENT_ERROR_BUGS,
}


def phase_name(phase: Phase) -> str:
    return S.PHASE_NAMES[phase.value]
