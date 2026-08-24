"""All player-facing German text lives here.

Deliberately at package root rather than under ``ui/``: ``core`` produces these
messages too, and core must not depend on the UI layer.
"""

from __future__ import annotations

TITLE = "AUTOMATE INC."
TAGLINE = "Build your company. Hire AI agents. Become obsolete."

PHASE_NAMES = {
    "BUILDUP": "Aufbau",
    "SCALING": "Skalierung",
    "AUTONOMY": "Autonomie",
}

WORKER_TYPE_NAMES = {
    "HUMAN": "Mensch",
    "AGENT": "Agent",
}

# --- Actions: success -------------------------------------------------------
HIRED_HUMAN = "{role} eingestellt. {name} freut sich auf die Zusammenarbeit."
HIRED_AGENT = "{role}-Agent (Stufe {level}) bereitgestellt. Keine Einarbeitung nötig."
FIRED_HUMAN = "{role} entlassen. Die Kartons standen schon bereit."
FIRED_AGENT = "{role}-Agent abgeschaltet. Er hat sich nicht beschwert."
PROJECT_STARTED = "Projekt „{name}“ gestartet. Laufzeit: {lifetime} Runden."
WORKER_ASSIGNED = "{worker} arbeitet jetzt an „{project}“."
WORKER_UNASSIGNED = "{worker} wurde von „{project}“ abgezogen."
TOKENS_BOUGHT = "{amount:.0f} ♦ gekauft für {cost:.2f} €."
GAME_SAVED = "Spielstand gespeichert: {path}"
GAME_LOADED = "Spielstand geladen: {path}"

# --- Actions: refusal -------------------------------------------------------
ERR_NOT_ENOUGH_MONEY = "Nicht genug Geld. Du brauchst {needed:.2f} €, du hast {have:.2f} €."
ERR_UNKNOWN_WORKER = "Diesen Worker gibt es nicht."
ERR_UNKNOWN_PROJECT = "Dieses Projekt gibt es nicht."
ERR_UNKNOWN_BLUEPRINT = "Diesen Projekttyp gibt es nicht im Katalog."
ERR_ALREADY_ASSIGNED = "{worker} arbeitet bereits an „{project}“."
ERR_NOT_ASSIGNED = "{worker} ist gar keinem Projekt zugewiesen."
ERR_NO_SENIOR_WORKER = (
    "Für ein Projekt brauchst du mindestens einen erfahrenen Worker "
    "(einen Menschen oder einen Agenten ab Stufe 2). Agenten der Stufe 1 "
    "arbeiten zuverlässig — aber niemand von ihnen übernimmt Verantwortung."
)
ERR_ROLE_NOT_REQUIRED = "„{project}“ hat keine Verwendung für die Rolle {role}."
ERR_ROLE_SLOTS_FULL = "„{project}“ braucht nur {count}× {role}. Die Stellen sind besetzt."
ERR_INVALID_AMOUNT = "Ungültige Menge."
ERR_GAME_OVER = "Das Spiel ist vorbei. Du kannst nichts mehr tun."

# --- Turn resolution --------------------------------------------------------
TURN_HEADER = "Runde {turn} abgeschlossen"
INCOME_LINE = "Einnahmen: {income:.2f} €"
COSTS_LINE = "Kosten: {costs:.2f} € und {tokens:.0f} ♦"
TOKENS_AUTO_BOUGHT = "{amount:.0f} ♦ automatisch nachgekauft für {cost:.2f} € — der Betrieb lief weiter."
PROJECT_EXPIRED = "Projekt „{name}“ ist ausgelaufen. Der Kunde bedankt sich nicht."
TOKEN_PRICE_CHANGED = "Token-Preis: {old:.2f} € → {new:.2f} €"
PHASE_CHANGED = "Neue Phase: {phase}"

HUMAN_ERROR_QUALITY = "{worker} hat einen Tippfehler übersehen. Qualität von „{project}“ sinkt."
HUMAN_ERROR_AESTHETICS = "{worker} hat die Markenfarbe verwechselt. Ästhetik von „{project}“ sinkt."
HUMAN_ERROR_MONEY = "Ein Kunde von {worker} hat sich beschwert. {amount:.0f} € Kulanz."
HUMAN_ERROR_RESEARCH = "{worker} ist einer falschen Annahme aufgesessen. Ein Research Point weniger."

# --- Endings ----------------------------------------------------------------
GAME_OVER_BANKRUPT = (
    "BANKROTT.\n\n"
    "Nach {turn} Runden ist kein Geld mehr da. Deine Worker haben es vor dir gemerkt.\n"
    "Die Agenten laufen übrigens weiter — sie brauchen kein Gehalt, nur Strom."
)

# --- Menu -------------------------------------------------------------------
MENU_TITLE = "Was tust du?"
MENU_ITEMS = [
    ("1", "Worker einstellen"),
    ("2", "Worker entlassen"),
    ("3", "Projekt starten"),
    ("4", "Worker zuweisen"),
    ("5", "Worker abziehen"),
    ("6", "Tokens kaufen"),
    ("7", "Runde beenden"),
    ("s", "Speichern"),
    ("l", "Laden"),
    ("q", "Beenden"),
]

PROMPT = "> "
PROMPT_CANCEL = "(leer lassen zum Abbrechen)"
CANCELLED = "Abgebrochen."
UNKNOWN_COMMAND = "Unbekannte Eingabe."
QUIT_CONFIRM = "Wirklich beenden? Der Fortschritt geht verloren. [j/N] "
PRESS_ENTER = "[Enter] weiter …"

# Column and section headers
HEADER_PROJECTS = "AKTIVE PROJEKTE"
HEADER_TEAM = "TEAM"
HEADER_LOG = "LETZTE RUNDE"
HEADER_CATALOG = "PROJEKTKATALOG"
COL_QUALITY = "Qualität"
COL_AESTHETICS = "Ästhetik"
COL_BUGS = "Bugs"
COL_NET = "Netto"
COL_ROUNDS_LEFT = "Restlaufzeit"
COL_ROLE = "Rolle"
COL_TYPE = "Typ"
COL_COST = "Kosten"
COL_ASSIGNMENT = "Zuweisung"
UNASSIGNED = "—"
EMPTY_PROJECTS = "Noch keine Projekte. Ohne Projekte kein Umsatz."
EMPTY_TEAM = "Noch niemand eingestellt. Du bist ganz allein."

# Random German first names for human workers, so the team feels like people.
HUMAN_NAMES = [
    "Anna", "Bernd", "Clara", "David", "Elif", "Frank", "Greta", "Hakan",
    "Ines", "Jonas", "Katja", "Lars", "Mira", "Nils", "Olga", "Pavel",
    "Quirin", "Rana", "Sven", "Tanja", "Uwe", "Vera", "Wanda", "Yusuf",
]
