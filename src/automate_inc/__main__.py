"""Entry point: python -m automate_inc"""

from __future__ import annotations

import random

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from automate_inc import strings as S
from automate_inc.core.game import Game
from automate_inc.ui.menu import Menu


def splash(console: Console) -> None:
    console.clear()
    console.print(
        Panel(
            Align.center(
                Text.assemble(
                    (S.TITLE + "\n", "bold"),
                    (S.TAGLINE, "dim italic"),
                )
            ),
            border_style="cyan",
        )
    )
    console.print(
        "\n[dim]Du hast 1.000 €, 50 Tokens und keine Kunden. "
        "Stell jemanden ein und fang an.[/dim]\n"
    )
    try:
        console.input(f"[dim]{S.PRESS_ENTER}[/dim] ")
    except EOFError:
        pass


def main() -> None:
    console = Console()
    game = Game(seed=random.randrange(2**31))
    splash(console)
    try:
        Menu(game, console).run()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Beendet.[/dim]")


if __name__ == "__main__":
    main()
