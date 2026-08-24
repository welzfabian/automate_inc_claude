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
        self.show(self.game.hire_worker(role, WorkerType(type_key)))

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
            (bp.id, f"{bp.name} — {bp.base_income} €/Runde, {bp.lifetime} Runden — {bp.description}")
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
        projects = [(p.id, p.name) for p in self.game.state.active_projects]
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

    def buy_tokens(self) -> None:
        price = self.game.state.token_price
        self.console.print()
        self.console.print(f"Token-Preis: [yellow]{price:.2f} €[/yellow]. Wie viele? {S.PROMPT_CANCEL}")
        raw = self.ask(S.PROMPT)
        if not raw:
            return self.note(S.CANCELLED, style="dim")
        if not raw.isdigit():
            return self.note(S.ERR_INVALID_AMOUNT, style="red")
        self.show(self.game.buy_tokens(int(raw)))

    def end_turn(self) -> None:
        report = self.game.resolve_turn()
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
            "7": self.end_turn,
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
                self.console.print(dashboard.game_over_panel(self.game.state.game_over_reason or ""))
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
