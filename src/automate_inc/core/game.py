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
from automate_inc.core.workers import Cost, Role, Worker, WorkerType, load_roles


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
]


class Game:
    def __init__(
        self,
        state: GameState | None = None,
        registry: ProjectRegistry | None = None,
        seed: int | None = None,
    ) -> None:
        self.state = state if state is not None else GameState()
        self.registry = registry if registry is not None else load_registry()
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

    def _worker_label(self, worker: Worker) -> str:
        spec = load_roles().spec(worker.role)
        if worker.is_human:
            return f"{worker.name} ({spec.name})"
        return f"{spec.name}-Agent Lv{worker.level}"

    def hiring_cost(self, role: Role, worker_type: WorkerType, level: int = 1) -> float:
        """One round of pay up front, in euros, so hiring is never free."""
        cost = Worker(id="_", role=role, worker_type=worker_type, level=level).cost_per_round()
        return cost.money + cost.tokens * self.state.token_price

    # -- actions -------------------------------------------------------------

    def hire_worker(self, role: Role, worker_type: WorkerType, level: int = 1) -> ActionResult:
        if (blocked := self._guard()) is not None:
            return blocked
        spec = load_roles().spec(role)
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
        taken = sum(
            1
            for w in self.state.workers_on(project.id)
            if w.role is worker.role and w.id != worker.id
        )
        if taken >= slots:
            return ActionResult.failure(
                S.ERR_ROLE_SLOTS_FULL.format(project=project.name, count=slots, role=spec.name)
            )
        self._detach(worker)
        worker.assigned_to = project.id
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

    # -- turn resolution -----------------------------------------------------

    def resolve_turn(self) -> TurnReport:
        report = TurnReport(turn=self.state.turn, money_before=self.state.money)
        rng = self._turn_rng()
        phase_before = self.state.phase

        self._apply_worker_effects()
        self._apply_side_effects(report, rng)
        report.income = self._calculate_income()
        money_costs, token_costs = self._calculate_costs()
        report.costs_money = money_costs
        report.costs_tokens = token_costs
        self._settle(report)
        self._update_token_price(report, rng)
        self._advance_projects(report)

        self.state.turn += 1
        if self.state.phase is not phase_before:
            report.events.append(
                S.PHASE_CHANGED.format(phase=S.PHASE_NAMES[self.state.phase.value])
            )
        self._check_game_over(report)

        report.money_after = self.state.money
        self.state.log = list(report.events)
        return report

    def _apply_worker_effects(self) -> None:
        for worker in self.state.workers:
            effect = load_roles().spec(worker.role).effect
            amount = effect.amount * worker.efficiency
            if effect.attribute == "research":
                # Researchers work for the company, not for a single project.
                self.state.research += int(round(amount))
                continue
            if worker.assigned_to is None:
                continue
            project = self.state.project(worker.assigned_to)
            if project is None:
                continue
            if effect.attribute in ("quality", "aesthetics", "bugs"):
                project.adjust(effect.attribute, amount)
            # income_bonus_pct (sales) is applied in the income formula via visibility.

    def _apply_side_effects(self, report: TurnReport, rng: random.Random) -> None:
        """M1 only models the rare human mistakes.

        Level 1 agents have no side effects by design (VISION.md) - which is
        exactly what makes them look like the obvious choice. Agent side effects
        arrive with levels 2 and 3.
        """
        for worker in self.state.workers:
            if not worker.is_human:
                continue
            error = load_roles().spec(worker.role).human_error
            if rng.random() >= error.chance:
                continue
            label = self._worker_label(worker)
            project = self.state.project(worker.assigned_to) if worker.assigned_to else None
            if error.attribute == "money":
                self.state.money += error.amount
                report.events.append(S.HUMAN_ERROR_MONEY.format(worker=label, amount=error.amount))
            elif error.attribute == "research":
                self.state.research = max(0, self.state.research + int(error.amount))
                report.events.append(S.HUMAN_ERROR_RESEARCH.format(worker=label))
            elif project is not None:
                project.adjust(error.attribute, error.amount)
                template = (
                    S.HUMAN_ERROR_QUALITY
                    if error.attribute == "quality"
                    else S.HUMAN_ERROR_AESTHETICS
                )
                report.events.append(template.format(worker=label, project=project.name))

    def _calculate_income(self) -> float:
        return sum(
            economy.project_income(project, self.state.workers)
            for project in self.state.active_projects
        )

    def _calculate_costs(self) -> tuple[float, float]:
        total: Cost = economy.idle_worker_costs(self.state.workers)
        for project in self.state.active_projects:
            total = total + economy.project_costs(project, self.state.workers)
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
            if project.is_expired:
                for worker in self.state.workers_on(project.id):
                    worker.assigned_to = None
                report.events.append(S.PROJECT_EXPIRED.format(name=project.name))
            else:
                surviving.append(project)
        self.state.active_projects = surviving

    def _check_game_over(self, report: TurnReport) -> None:
        for condition in END_CONDITIONS:
            if condition.triggered(self.state):
                self.state.game_over_reason = condition.message.format(turn=self.state.turn)
                report.events.append(self.state.game_over_reason)
                return


def phase_name(phase: Phase) -> str:
    return S.PHASE_NAMES[phase.value]
