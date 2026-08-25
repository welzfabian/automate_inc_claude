"""Rich rendering of the game state. Reads the state, never changes it."""

from __future__ import annotations

from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from automate_inc import strings as S
from automate_inc.core import economy
from automate_inc.core.events import PERMANENT
from automate_inc.core.game import Game, TurnReport, alignment_tier
from automate_inc.core.state import GameState, Phase
from automate_inc.core.tech import TechCategory
from automate_inc.core.workers import Role, Worker, load_roles

CATEGORY_NAMES = {
    TechCategory.FOUNDATION: "Grundlagen",
    TechCategory.ECONOMY: "Wirtschaft",
    TechCategory.AI: "KI",
    TechCategory.DANGEROUS: "Gefährlich",
}

CATEGORY_STYLES = {
    TechCategory.FOUNDATION: "cyan",
    TechCategory.ECONOMY: "green",
    TechCategory.AI: "yellow",
    TechCategory.DANGEROUS: "bold red",
}

PHASE_STYLES = {
    Phase.BUILDUP: "cyan",
    Phase.SCALING: "yellow",
    Phase.AUTONOMY: "bold red",
}

AGENT_SYMBOL = "🤖"
HUMAN_SYMBOL = "🧑"

SERVICE_BAR_WIDTH = 8


def service_bar(project) -> Text:
    """A bar plus the number - the bar for the glance, the number for the decision."""
    filled = int(round(project.service_level / 100 * SERVICE_BAR_WIDTH))
    style = "green" if project.at_full_service else "yellow"
    return Text.assemble(
        ("▓" * filled + "░" * (SERVICE_BAR_WIDTH - filled), style),
        (f" {project.service_level:3.0f}%", "dim"),
    )


def capped_attribute(project, workers, role: Role) -> Text:
    """Show the value, and the ceiling its staffing imposes when one is binding."""
    value = getattr(project, economy.ROLE_ATTRIBUTES[role])
    cap = economy.attribute_cap(project, workers, role)
    if cap >= 100:
        return Text(f"{value:.0f}")
    return Text.assemble((f"{value:.0f}", ""), (f"/{cap:.0f}", "dim red"))


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


def header(game: Game) -> RenderableType:
    state = game.state
    phase = game.phase
    phase_style = PHASE_STYLES[phase]
    delta = economy.alignment_delta(state.workers, game.modifiers)
    title = Text.assemble(
        (S.TITLE, "bold"),
        ("  ──  ", "dim"),
        (f"Runde {state.turn}", ""),
        ("  ──  ", "dim"),
        (S.PHASE_NAMES[phase.value], phase_style),
    )
    parts: list[tuple[str, str]] = [
        ("€ ", "dim"),
        (f"{state.money:,.2f}", money_style(state.money)),
        ("     ♦ ", "dim"),
        (f"{state.tokens:,.0f}", "yellow"),
        (f" ({state.token_price:.2f} €)", "dim yellow"),
        ("     🔬 ", "dim"),
        (f"{state.research}", "cyan"),
        ("     ⚖ ", "dim"),
        (f"{state.alignment:.0f}", alignment_style(state.alignment)),
        (f" ({delta:+.0f}/Runde)", "dim" if delta >= 0 else "dim red"),
    ]
    if state.investor_equity:
        parts.append(("     💼 ", "dim"))
        parts.append((f"{state.investor_equity:.0f} % Investoren", "dim red"))
    resources = Text.assemble(*parts)
    return Panel(Group(Align.center(title), Align.center(resources)), border_style=phase_style)


def projects_table(game: Game) -> RenderableType:
    state = game.state
    if not state.active_projects:
        return Panel(Text(S.EMPTY_PROJECTS, style="dim"), title=S.HEADER_PROJECTS)

    table = Table(expand=True, header_style="dim", box=None, pad_edge=False)
    table.add_column("#", width=3)
    table.add_column("Projekt")
    table.add_column(S.COL_SERVICE_LEVEL, justify="left", width=14)
    table.add_column(S.COL_QUALITY, justify="right", width=9)
    table.add_column(S.COL_AESTHETICS, justify="right", width=9)
    table.add_column(S.COL_BUGS, justify="right", width=6)
    table.add_column("Team", justify="right", width=6)
    table.add_column(S.COL_ROUNDS_LEFT, justify="right", width=12)
    table.add_column(S.COL_NET, justify="right", width=12)

    for index, project in enumerate(state.active_projects, start=1):
        income = economy.project_income(project, state.workers, game.modifiers)
        costs = economy.project_costs(project, state.workers, game.modifiers)
        net = income - costs.money - costs.tokens * state.token_price
        needed = sum(project.required_roles.values())
        staffed = len(state.workers_on(project.id))
        table.add_row(
            str(index),
            project.name,
            service_bar(project),
            capped_attribute(project, state.workers, Role.DEVELOPER),
            capped_attribute(project, state.workers, Role.DESIGNER)
            if project.requires(Role.DESIGNER)
            else Text("—", style="dim"),
            f"{project.bugs:.0f}",
            Text(f"{staffed}/{needed}", style="green" if staffed >= needed else "yellow"),
            f"{project.rounds_left}",
            Text(f"{net:+,.2f} €", style=money_style(net)),
        )
    return Panel(table, title=S.HEADER_PROJECTS, border_style="dim")


def team_table(game: Game) -> RenderableType:
    state = game.state
    humans = sum(1 for w in state.workers if w.is_human)
    title = f"{S.HEADER_TEAM} — 🧑 {humans}/{state.office_capacity}"
    if not state.workers:
        return Panel(Text(S.EMPTY_TEAM, style="dim"), title=title)

    catalog = load_roles()
    table = Table(expand=True, header_style="dim", box=None, pad_edge=False)
    table.add_column("#", width=3)
    table.add_column("Worker")
    table.add_column(S.COL_ROLE, width=12)
    table.add_column(S.COL_TYPE, width=10)
    table.add_column(S.COL_COST, justify="right", width=18)
    table.add_column(S.COL_ASSIGNMENT)

    for index, worker in enumerate(state.workers, start=1):
        spec = catalog.spec(worker.role)
        project = state.project(worker.assigned_to) if worker.assigned_to else None
        table.add_row(
            str(index),
            worker_label(worker),
            spec.name,
            S.WORKER_TYPE_NAMES[worker.worker_type.value],
            worker_cost(worker, game),
            project.name if project else Text(S.UNASSIGNED, style="dim"),
        )
    return Panel(table, title=title, border_style="dim")


def worker_cost(worker: Worker, game: Game) -> Text:
    """What this worker costs per round, in a currency the player can compare.

    Agents are billed in tokens, so their euro price moves with the token market.
    Showing the conversion here is what makes "human or agent" a decision the player
    can read off the table instead of doing in their head - and it puts the token
    inflation in front of them while it happens.

    Neither is styled as alarming: a salary is normal. What is alarming is a project
    whose net has gone red, and that is already in the project table.
    """
    cost = worker.cost_per_round(game.modifiers)
    if worker.is_human:
        return Text(f"{cost.money:.0f} €")
    euro = cost.tokens * game.state.token_price
    return Text.assemble(
        (f"{cost.tokens:.0f} ♦", "yellow"),
        (f"  ≈ {euro:.0f} €", "dim"),
    )


def worker_label(worker: Worker) -> str:
    spec = load_roles().spec(worker.role)
    if worker.is_human:
        return f"{HUMAN_SYMBOL} {worker.name}"
    return f"{AGENT_SYMBOL} {spec.name}-Agent Lv{worker.level}"


def research_panel(game: Game) -> RenderableType:
    """Researched, available and locked - locked entries name what is missing."""
    state = game.state
    registry = game.tech_registry
    table = Table.grid(padding=(0, 2))
    table.add_column(width=11)
    table.add_column()
    table.add_column(justify="right", width=8)

    def section(title: str, style: str) -> None:
        table.add_row("", Text(title, style=f"bold {style}"), "")

    done = registry.resolve(state.researched)
    if done:
        section(S.RESEARCH_DONE_HEADER, "green")
        for tech in done:
            table.add_row(Text("✓", style="green"), Text(tech.name, style="dim"), "")

    available = game.available_technologies()
    section(S.RESEARCH_AVAILABLE, "cyan")
    if not available:
        table.add_row("", Text(S.RESEARCH_EMPTY_AVAILABLE, style="dim"), "")
    for tech in available:
        affordable = state.research >= tech.cost
        table.add_row(
            Text(CATEGORY_NAMES[tech.category], style=CATEGORY_STYLES[tech.category]),
            Text(tech.name, style="" if affordable else "dim"),
            Text(f"{tech.cost} 🔬", style="cyan" if affordable else "dim"),
        )

    locked = [
        tech
        for tech in registry.all()
        if tech.id not in state.researched and registry.missing_requirements(tech, state.researched)
    ]
    if locked:
        section(S.RESEARCH_LOCKED, "dim")
        for tech in locked:
            missing = ", ".join(
                m.name
                for m in (
                    registry.get(i) for i in registry.missing_requirements(tech, state.researched)
                )
                if m is not None
            )
            table.add_row(
                Text("🔒", style="dim"),
                Text(
                    f"{tech.name} — {S.RESEARCH_LOCKED_HINT.format(missing=missing)}",
                    style="dim",
                ),
                Text(f"{tech.cost} 🔬", style="dim"),
            )
    return Panel(table, title=S.HEADER_RESEARCH, border_style="dim")


def active_events_panel(game: Game) -> RenderableType | None:
    """Running pressure, named and with its remaining duration.

    Shown before the round so the player can weigh it before deciding, not
    just read it off the balance afterwards - what has not triggered yet stays
    hidden entirely, unlocking is not a promise.
    """
    if not game.state.active_events:
        return None
    table = Table.grid(padding=(0, 2))
    table.add_column()
    for effect in game.state.active_events:
        event = game.event_registry.get(effect.event_id)
        name = event.name if event is not None else effect.event_id
        option = event.option(effect.option_id) if event is not None else None
        label = option.label if option is not None else effect.option_id
        if effect.remaining == PERMANENT:
            line = S.ACTIVE_EVENT_LINE_PERMANENT.format(name=name, label=label)
        else:
            line = S.ACTIVE_EVENT_LINE_TEMPORARY.format(
                name=name, label=label, remaining=effect.remaining
            )
        table.add_row(Text(line, style="yellow"))
    return Panel(table, title=S.HEADER_ACTIVE_EVENTS, border_style="yellow")


def agent_tone(state: GameState) -> str:
    """The acknowledgement line agents append to your orders. Cosmetic - for now."""
    return S.AGENT_ACK[alignment_tier(state.alignment)]


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
    console.print(header(game))
    console.print(projects_table(game))
    console.print(team_table(game))
    events_panel = active_events_panel(game)
    if events_panel is not None:
        console.print(events_panel)
    console.print(log_panel(game.state))
    console.print(menu_panel())


def turn_summary(report: TurnReport) -> RenderableType:
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="right")
    table.add_column()
    table.add_row("Einnahmen", Text(f"{report.income:+,.2f} €", style="green"))
    table.add_row("Kosten", Text(f"{-report.costs_money:,.2f} €", style="red"))
    table.add_row("Tokens verbraucht", Text(f"{report.costs_tokens:,.0f} ♦", style="yellow"))
    if report.investor_payout:
        table.add_row("Investoren-Anteil", Text(f"{-report.investor_payout:,.2f} €", style="red"))
    table.add_row("Bilanz", Text(f"{report.net:+,.2f} €", style=money_style(report.net)))
    if report.alignment_delta:
        table.add_row(
            S.COL_ALIGNMENT_BALANCE,
            Text(
                f"{report.alignment_delta:+.0f} ⚖",
                style="green" if report.alignment_delta > 0 else "red",
            ),
        )
    return Panel(table, title=S.TURN_HEADER.format(turn=report.turn), border_style="dim")


def game_over_panel(reason: str) -> RenderableType:
    return Panel(Align.center(Text(reason, style="bold red")), border_style="red")
