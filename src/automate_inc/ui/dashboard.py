"""Rich rendering of the game state. Reads the state, never changes it."""

from __future__ import annotations

from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from automate_inc import strings as S
from automate_inc.core import economy
from automate_inc.core.game import Game, TurnReport
from automate_inc.core.state import GameState, Phase
from automate_inc.core.workers import Role, Worker, load_roles

PHASE_STYLES = {
    Phase.BUILDUP: "cyan",
    Phase.SCALING: "yellow",
    Phase.AUTONOMY: "bold red",
}

AGENT_SYMBOL = "🤖"
HUMAN_SYMBOL = "🧑"


def money_style(amount: float) -> str:
    return "green" if amount >= 0 else "bold red"


def alignment_style(value: float) -> str:
    if value >= 80:
        return "green"
    if value >= 40:
        return "yellow"
    if value >= 20:
        return "red"
    return "bold red blink"


def header(state: GameState) -> RenderableType:
    phase_style = PHASE_STYLES[state.phase]
    title = Text.assemble(
        (S.TITLE, "bold"),
        ("  ──  ", "dim"),
        (f"Runde {state.turn}", ""),
        ("  ──  ", "dim"),
        (S.PHASE_NAMES[state.phase.value], phase_style),
    )
    resources = Text.assemble(
        ("€ ", "dim"),
        (f"{state.money:,.2f}", money_style(state.money)),
        ("     ♦ ", "dim"),
        (f"{state.tokens:,.0f}", "yellow"),
        (f" ({state.token_price:.2f} €)", "dim yellow"),
        ("     🔬 ", "dim"),
        (f"{state.research}", "cyan"),
        ("     ⚖ ", "dim"),
        (f"{state.alignment:.0f}", alignment_style(state.alignment)),
    )
    return Panel(Group(Align.center(title), Align.center(resources)), border_style=phase_style)


def projects_table(game: Game) -> RenderableType:
    state = game.state
    if not state.active_projects:
        return Panel(Text(S.EMPTY_PROJECTS, style="dim"), title=S.HEADER_PROJECTS)

    table = Table(expand=True, header_style="dim", box=None, pad_edge=False)
    table.add_column("#", width=3)
    table.add_column("Projekt")
    table.add_column(S.COL_QUALITY, justify="right", width=9)
    table.add_column(S.COL_AESTHETICS, justify="right", width=9)
    table.add_column(S.COL_BUGS, justify="right", width=6)
    table.add_column("Team", justify="right", width=6)
    table.add_column(S.COL_ROUNDS_LEFT, justify="right", width=12)
    table.add_column(S.COL_NET, justify="right", width=12)

    for index, project in enumerate(state.active_projects, start=1):
        income = economy.project_income(project, state.workers)
        costs = economy.project_costs(project, state.workers)
        net = income - costs.money - costs.tokens * state.token_price
        needed = sum(project.required_roles.values())
        staffed = len(state.workers_on(project.id))
        table.add_row(
            str(index),
            project.name,
            f"{project.quality:.0f}",
            f"{project.aesthetics:.0f}" if project.requires(Role.DESIGNER) else "—",
            f"{project.bugs:.0f}",
            Text(f"{staffed}/{needed}", style="green" if staffed >= needed else "yellow"),
            f"{project.rounds_left}",
            Text(f"{net:+,.2f} €", style=money_style(net)),
        )
    return Panel(table, title=S.HEADER_PROJECTS, border_style="dim")


def team_table(game: Game) -> RenderableType:
    state = game.state
    if not state.workers:
        return Panel(Text(S.EMPTY_TEAM, style="dim"), title=S.HEADER_TEAM)

    catalog = load_roles()
    table = Table(expand=True, header_style="dim", box=None, pad_edge=False)
    table.add_column("#", width=3)
    table.add_column("Worker")
    table.add_column(S.COL_ROLE, width=12)
    table.add_column(S.COL_TYPE, width=10)
    table.add_column(S.COL_COST, justify="right", width=14)
    table.add_column(S.COL_ASSIGNMENT)

    for index, worker in enumerate(state.workers, start=1):
        spec = catalog.spec(worker.role)
        cost = worker.cost_per_round()
        cost_text = (
            Text(f"{cost.money:.0f} €", style="green")
            if worker.is_human
            else Text(f"{cost.tokens:.0f} ♦", style="yellow")
        )
        project = state.project(worker.assigned_to) if worker.assigned_to else None
        table.add_row(
            str(index),
            worker_label(worker),
            spec.name,
            S.WORKER_TYPE_NAMES[worker.worker_type.value],
            cost_text,
            project.name if project else Text(S.UNASSIGNED, style="dim"),
        )
    return Panel(table, title=S.HEADER_TEAM, border_style="dim")


def worker_label(worker: Worker) -> str:
    spec = load_roles().spec(worker.role)
    if worker.is_human:
        return f"{HUMAN_SYMBOL} {worker.name}"
    return f"{AGENT_SYMBOL} {spec.name}-Agent Lv{worker.level}"


def log_panel(state: GameState) -> RenderableType:
    if not state.log:
        return Panel(Text("—", style="dim"), title=S.HEADER_LOG, border_style="dim")
    body = Text()
    for entry in state.log:
        body.append(f"📩 {entry}\n")
    return Panel(body, title=S.HEADER_LOG, border_style="dim")


def menu_panel() -> RenderableType:
    table = Table.grid(padding=(0, 3))
    table.add_column()
    table.add_column()
    items = S.MENU_ITEMS
    half = (len(items) + 1) // 2
    for left, right in zip(items[:half], items[half:] + [("", "")], strict=False):
        table.add_row(
            Text.assemble((f"[{left[0]}] ", "bold cyan"), (left[1], "")),
            Text.assemble((f"[{right[0]}] ", "bold cyan"), (right[1], "")) if right[0] else "",
        )
    return Panel(table, title=S.MENU_TITLE, border_style="dim")


def render(console: Console, game: Game) -> None:
    console.clear()
    console.print(header(game.state))
    console.print(projects_table(game))
    console.print(team_table(game))
    console.print(log_panel(game.state))
    console.print(menu_panel())


def turn_summary(report: TurnReport) -> RenderableType:
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="right")
    table.add_column()
    table.add_row("Einnahmen", Text(f"{report.income:+,.2f} €", style="green"))
    table.add_row("Kosten", Text(f"{-report.costs_money:,.2f} €", style="red"))
    table.add_row("Tokens verbraucht", Text(f"{report.costs_tokens:,.0f} ♦", style="yellow"))
    table.add_row("Bilanz", Text(f"{report.net:+,.2f} €", style=money_style(report.net)))
    return Panel(table, title=S.TURN_HEADER.format(turn=report.turn), border_style="dim")


def game_over_panel(reason: str) -> RenderableType:
    return Panel(Align.center(Text(reason, style="bold red")), border_style="red")
