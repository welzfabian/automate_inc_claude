"""The interactive loop: read a command, call the engine, render the result."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.text import Text

from automate_inc import strings as S
from automate_inc.core.game import ActionResult, Game
from automate_inc.core.workers import Role, WorkerType, load_roles
from automate_inc.ui import dashboard

DEFAULT_SAVE = Path("saves/savegame.json")

AGENT_LEVEL_HINTS = {
    1: " (zuverlässig, keine Nebeneffekte)",
    2: " (effizienter — macht Fehler, −1 ⚖/Runde)",
    3: " (doppelte Effizienz — macht mehr Fehler, −3 ⚖/Runde)",
}


class Abort(Exception):
    """Raised when stdin closes - the player is gone, stop asking them things."""


class Menu:
    def __init__(self, game: Game, console: Console | None = None) -> None:
        self.game = game
        self.console = console or Console()
        self.pending: list[str] = []

    # -- input helpers -------------------------------------------------------

    def ask(self, prompt: str) -> str:
        try:
            return self.console.input(prompt).strip()
        except EOFError as exc:
            raise Abort from exc

    def choose(self, title: str, options: list[tuple[str, str]]) -> str | None:
        """Show a numbered list and return the chosen key, or None if cancelled."""
        self.console.print()
        self.console.print(Text(title, style="bold"))
        for index, (_, label) in enumerate(options, start=1):
            self.console.print(f"  [cyan]{index}[/cyan]  {label}")
        self.console.print(f"[dim]{S.PROMPT_CANCEL}[/dim]")
        raw = self.ask(S.PROMPT)
        if not raw:
            return None
        if not raw.isdigit() or not 1 <= int(raw) <= len(options):
            self.note(S.UNKNOWN_COMMAND)
            return None
        return options[int(raw) - 1][0]

    def note(self, message: str, style: str = "") -> None:
        self.pending.append(message)
        self.console.print(Text(message, style=style))

    def show(self, result: ActionResult) -> None:
        self.note(result.message, style="green" if result.ok else "red")
        tone = dashboard.agent_tone(self.game.state)
        if result.ok and tone:
            self.note(f"🤖 {tone}", style="dim italic")

    # -- action handlers -----------------------------------------------------

    def hire(self) -> None:
        catalog = load_roles()
        roles = [(role.value, catalog.spec(role).name) for role in Role]
        role_key = self.choose("Welche Rolle?", roles)
        if role_key is None:
            return self.note(S.CANCELLED, style="dim")
        role = Role(role_key)
        options = []
        for worker_type in (WorkerType.HUMAN, WorkerType.AGENT):
            cost = self.game.hiring_cost(role, worker_type)
            label = S.WORKER_TYPE_NAMES[worker_type.value]
            options.append((worker_type.value, f"{label} — {cost:.2f} € pro Runde"))
        type_key = self.choose("Mensch oder Agent?", options)
        if type_key is None:
            return self.note(S.CANCELLED, style="dim")
        worker_type = WorkerType(type_key)
        level = 1
        unlocked = self.game.modifiers.unlocked_agent_level
        if worker_type is WorkerType.AGENT and unlocked > 1:
            levels = [
                (
                    str(lvl),
                    f"Stufe {lvl} — {self.game.hiring_cost(role, worker_type, lvl):.2f} € pro Runde"
                    f"{AGENT_LEVEL_HINTS[lvl]}",
                )
                for lvl in range(1, unlocked + 1)
            ]
            level_key = self.choose("Welche Stufe?", levels)
            if level_key is None:
                return self.note(S.CANCELLED, style="dim")
            level = int(level_key)
        self.show(self.game.hire_worker(role, worker_type, level))

    def fire(self) -> None:
        workers = self.game.state.workers
        if not workers:
            return self.note(S.EMPTY_TEAM, style="dim")
        options = [(w.id, dashboard.worker_label(w)) for w in workers]
        worker_id = self.choose("Wen entlassen?", options)
        if worker_id is None:
            return self.note(S.CANCELLED, style="dim")
        self.show(self.game.fire_worker(worker_id))

    def start_project(self) -> None:
        options = [
            (
                bp.id,
                f"{bp.name} — {bp.base_income} €/Runde, {bp.lifetime} Runden "
                f"— {bp.description}",
            )
            for bp in self.game.registry.all()
        ]
        blueprint_id = self.choose(S.HEADER_CATALOG, options)
        if blueprint_id is None:
            return self.note(S.CANCELLED, style="dim")
        self.show(self.game.start_project(blueprint_id))

    def assign(self) -> None:
        free = [w for w in self.game.state.workers if w.assigned_to is None]
        if not free:
            return self.note("Alle Worker sind bereits zugewiesen.", style="dim")
        if not self.game.state.active_projects:
            return self.note(S.EMPTY_PROJECTS, style="dim")
        worker_id = self.choose("Wen zuweisen?", [(w.id, dashboard.worker_label(w)) for w in free])
        if worker_id is None:
            return self.note(S.CANCELLED, style="dim")
        worker = self.game.state.worker(worker_id)
        role_name = load_roles().spec(worker.role).name
        # Only offer what the engine would actually accept.
        open_projects = self.game.projects_needing(worker.role)
        if not open_projects:
            return self.note(S.NO_PROJECT_NEEDS_ROLE.format(role=role_name), style="dim")
        projects = [
            (
                project.id,
                S.PROJECT_WITH_FREE_SLOTS.format(
                    project=project.name,
                    count=self.game.free_slots(project, worker.role),
                    role=role_name,
                ),
            )
            for project in open_projects
        ]
        project_id = self.choose("An welches Projekt?", projects)
        if project_id is None:
            return self.note(S.CANCELLED, style="dim")
        self.show(self.game.assign_worker(worker_id, project_id))

    def unassign(self) -> None:
        busy = [w for w in self.game.state.workers if w.assigned_to is not None]
        if not busy:
            return self.note("Niemand ist einem Projekt zugewiesen.", style="dim")
        worker_id = self.choose("Wen abziehen?", [(w.id, dashboard.worker_label(w)) for w in busy])
        if worker_id is None:
            return self.note(S.CANCELLED, style="dim")
        self.show(self.game.unassign_worker(worker_id))

    def research(self) -> None:
        self.console.print()
        self.console.print(dashboard.research_panel(self.game))
        available = self.game.available_technologies()
        if not available:
            return self.note(S.RESEARCH_EMPTY_AVAILABLE, style="dim")
        options = [
            (tech.id, f"{tech.name} — {tech.cost} 🔬 — {tech.description}")
            for tech in available
        ]
        tech_id = self.choose(S.HEADER_RESEARCH, options)
        if tech_id is None:
            return self.note(S.CANCELLED, style="dim")
        self.show(self.game.research(tech_id))

    def upgrade(self) -> None:
        agents = [
            w
            for w in self.game.state.workers
            if not w.is_human and w.level < self.game.modifiers.unlocked_agent_level
        ]
        if not agents:
            return self.note(S.ERR_MAX_LEVEL, style="dim")
        options = [
            (
                w.id,
                f"{dashboard.worker_label(w)} → Stufe {w.level + 1} "
                f"— {self.game.upgrade_cost(w):.2f} €",
            )
            for w in agents
        ]
        worker_id = self.choose("Welchen Agenten aufwerten?", options)
        if worker_id is None:
            return self.note(S.CANCELLED, style="dim")
        self.show(self.game.upgrade_agent(worker_id))

    def buy_tokens(self) -> None:
        price = self.game.state.token_price
        self.console.print()
        self.console.print(
            f"Token-Preis: [yellow]{price:.2f} €[/yellow]. Wie viele? {S.PROMPT_CANCEL}"
        )
        raw = self.ask(S.PROMPT)
        if not raw:
            return self.note(S.CANCELLED, style="dim")
        if not raw.isdigit():
            return self.note(S.ERR_INVALID_AMOUNT, style="red")
        self.show(self.game.buy_tokens(int(raw)))

    def _answer_pending_decisions(self) -> None:
        """Unavoidable: the round will not resolve while one of these is open."""
        while self.game.state.pending_decisions:
            event_id = self.game.state.pending_decisions[0]
            event = self.game.event_registry.get(event_id)
            if event is None:
                # The catalog lost this event since it triggered; answer_event
                # itself drops a decision it cannot find anything for.
                self.game.answer_event(event_id, "")
                continue
            self.console.print()
            self.console.print(Text(S.EVENT_DECISION_HEADER.format(name=event.name), style="bold"))
            self.console.print(Text(event.description, style="dim"))
            option_id = self.choose(
                event.name, [(o.id, o.label) for o in event.options]
            )
            if option_id is None:
                continue  # not answerable away - it blocks the turn either way
            self.show(self.game.answer_event(event_id, option_id))

    def end_turn(self) -> None:
        self._answer_pending_decisions()
        report = self.game.resolve_turn()
        if report.blocked:
            self.note(S.TURN_BLOCKED, style="red")
            return
        self.console.print()
        self.console.print(dashboard.turn_summary(report))
        for event in report.events:
            self.console.print(f"[dim]📩[/dim] {event}")
        self.ask(f"\n[dim]{S.PRESS_ENTER}[/dim] ")
        self.pending = []

    def save(self) -> None:
        self.show(self.game.save(DEFAULT_SAVE))

    def load(self) -> None:
        if not DEFAULT_SAVE.exists():
            return self.note("Kein Spielstand gefunden.", style="red")
        self.game = Game.load(DEFAULT_SAVE)
        self.note(S.GAME_LOADED.format(path=DEFAULT_SAVE), style="green")

    # -- main loop -----------------------------------------------------------

    def run(self) -> None:
        handlers = {
            "1": self.hire,
            "2": self.fire,
            "3": self.start_project,
            "4": self.assign,
            "5": self.unassign,
            "6": self.buy_tokens,
            "7": self.research,
            "8": self.upgrade,
            "9": self.end_turn,
            "s": self.save,
            "l": self.load,
        }
        try:
            self._loop(handlers)
        except Abort:
            self.console.print("\n[dim]Beendet.[/dim]")

    def _loop(self, handlers: dict) -> None:
        while True:
            dashboard.render(self.console, self.game)
            for message in self.pending:
                self.console.print(Text(message, style="dim"))
            if self.game.state.is_over:
                reason = self.game.state.game_over_reason or ""
                self.console.print(dashboard.game_over_panel(reason))
                self.ask(f"[dim]{S.PRESS_ENTER}[/dim] ")
                return
            command = self.ask(f"\n{S.PROMPT}").lower()
            self.pending = []
            if command == "q":
                if self.ask(S.QUIT_CONFIRM).lower().startswith("j"):
                    return
                continue
            handler = handlers.get(command)
            if handler is None:
                self.note(S.UNKNOWN_COMMAND, style="red")
                continue
            handler()
