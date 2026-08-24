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
from automate_inc.core.projects import Project, ProjectRegistry, load_registry
from automate_inc.core.state import GameState, Phase
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
    alignment_delta: float = 0.0
    money_before: float = 0.0
    money_after: float = 0.0
    events: list[str] = field(default_factory=list)

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
]


class Game:
    def __init__(
        self,
        state: GameState | None = None,
        registry: ProjectRegistry | None = None,
        seed: int | None = None,
        tech_registry: TechRegistry | None = None,
    ) -> None:
        self.state = state if state is not None else GameState()
        self.registry = registry if registry is not None else load_registry()
        self.tech_registry = tech_registry if tech_registry is not None else load_tech_registry()
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
        if not any(w.effective_level >= 2 for w in self.state.workers):
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
        report = TurnReport(turn=self.state.turn, money_before=self.state.money)
        rng = self._turn_rng()
        # Aggregated once so every step of this turn sees the same tech state,
        # even if a later step were to change what is researched.
        modifiers = self.modifiers

        self._advance_service_level()
        self._apply_worker_effects(modifiers)
        self._apply_side_effects(report, rng, modifiers)
        self._update_alignment(report, modifiers)
        report.income = self._calculate_income(modifiers)
        money_costs, token_costs = self._calculate_costs(modifiers)
        report.costs_money = money_costs
        report.costs_tokens = token_costs
        self._settle(report)
        self._update_token_price(report, rng)
        self._advance_projects(report)

        self.state.turn += 1
        self._report_phase(report)
        self._check_game_over(report)

        report.money_after = self.state.money
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

    def _advance_service_level(self) -> None:
        """A project earns only what the client is actually getting."""
        for project in self.state.active_projects:
            project.adjust(
                "service_level", economy.service_level_delta(project, self.state.workers)
            )

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

    def _update_alignment(self, report: TurnReport, modifiers: Modifiers) -> None:
        """Alignment is deterministic (BALANCING.md 8) so the player can read it."""
        tier_before = alignment_tier(self.state.alignment)
        delta = economy.alignment_delta(self.state.workers, modifiers)
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

    def _calculate_income(self, modifiers: Modifiers) -> float:
        return sum(
            economy.project_income(project, self.state.workers, modifiers)
            for project in self.state.active_projects
        )

    def _calculate_costs(self, modifiers: Modifiers) -> tuple[float, float]:
        total: Cost = economy.idle_worker_costs(self.state.workers, modifiers)
        for project in self.state.active_projects:
            total = total + economy.project_costs(project, self.state.workers, modifiers)
        return total.money, total.tokens

    def _settle(self, report: TurnReport) -> None:
        self.state.money += report.income - report.costs_money
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


ALIGNMENT_TIERS = (80.0, 40.0, MISALIGNMENT_THRESHOLD)
"""Lower bounds of tiers 0, 1 and 2. Below the last one, the game ends."""


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
