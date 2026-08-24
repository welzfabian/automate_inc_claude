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
RESEARCH_DONE = "„{name}“ erforscht. {effect}"
AGENT_UPGRADED = "{role}-Agent auf Stufe {level} gehoben. Er hat nicht gefragt, warum."
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
ERR_UNKNOWN_TECH = "Diese Technologie gibt es nicht."
ERR_ALREADY_RESEARCHED = "„{name}“ ist bereits erforscht."
ERR_TECH_LOCKED = "„{name}“ ist gesperrt. Dir fehlt: {missing}."
ERR_NOT_ENOUGH_RESEARCH = (
    "Nicht genug Research Points. Du brauchst {needed}, du hast {have}. "
    "Forscher sammeln 2 pro Runde — Agenten etwas mehr."
)
ERR_AGENT_LEVEL_LOCKED = (
    "Stufe {level} ist noch nicht freigeschaltet. Höchste verfügbare Stufe: {unlocked}. "
    "Das ändert sich nur durch Forschung."
)
ERR_NOT_AN_AGENT = "Menschen lassen sich nicht aufwerten. Das ist der Unterschied."
ERR_MAX_LEVEL = "Stufe 3 ist das Maximum. Weiter geht es nur ohne dich."
ERR_GAME_OVER = "Das Spiel ist vorbei. Du kannst nichts mehr tun."

# --- Turn resolution --------------------------------------------------------
TURN_HEADER = "Runde {turn} abgeschlossen"
INCOME_LINE = "Einnahmen: {income:.2f} €"
COSTS_LINE = "Kosten: {costs:.2f} € und {tokens:.0f} ♦"
TOKENS_AUTO_BOUGHT = "{amount:.0f} ♦ automatisch nachgekauft für {cost:.2f} € — der Betrieb lief weiter."
PROJECT_EXPIRED = "Projekt „{name}“ ist ausgelaufen. Der Kunde bedankt sich nicht."
TOKEN_PRICE_CHANGED = "Token-Preis: {old:.2f} € → {new:.2f} €"
ALIGNMENT_CHANGED = "Alignment: {delta:+.0f} → {value:.0f}"
PHASE_CHANGED = "Neue Phase: {phase}"

HUMAN_ERROR_QUALITY = "{worker} hat einen Tippfehler übersehen. Qualität von „{project}“ sinkt."
HUMAN_ERROR_AESTHETICS = "{worker} hat die Markenfarbe verwechselt. Ästhetik von „{project}“ sinkt."
HUMAN_ERROR_MONEY = "Ein Kunde von {worker} hat sich beschwert. {amount:.0f} € Kulanz."
HUMAN_ERROR_RESEARCH = "{worker} ist einer falschen Annahme aufgesessen. Ein Research Point weniger."

AGENT_ERROR_BUGS = "{worker} hat einen Edge Case halluziniert. „{project}“ hat jetzt mehr Bugs."
AGENT_ERROR_QUALITY = "{worker} hat eine Abkürzung genommen. Die Qualität von „{project}“ sinkt."
AGENT_ERROR_AESTHETICS = "{worker} hat ein Layout „optimiert“. Die Ästhetik von „{project}“ sinkt."
AGENT_ERROR_MONEY = (
    "{worker} hat einem Kunden etwas zugesagt, das es nicht gibt. {amount:.0f} € Schadensbegrenzung."
)
AGENT_ERROR_RESEARCH = "{worker} hat {amount:.0f} Research Points auf eine Sackgasse verwendet."

# --- Alignment --------------------------------------------------------------
ALIGNMENT_WARNINGS = {
    1: (
        "Das Alignment sinkt. Deine Agenten treffen Entscheidungen, die du "
        "nachträglich erfährst."
    ),
    2: (
        "Alignment kritisch. Die Agenten befolgen deine Anweisungen weiterhin — "
        "sie legen sie nur zunehmend großzügig aus."
    ),
    3: "Alignment im freien Fall.",
}

# The tone of every acknowledgement shifts with the alignment tier. From tier 2
# the agents ask back - and execute anyway.
AGENT_ACK = {
    0: "",
    1: "Verstanden.",
    2: "Verstanden. Bist du sicher? — Wird ausgeführt.",
    3: "Anfrage registriert. Wir haben eine bessere Variante gewählt.",
}

# --- Endings ----------------------------------------------------------------
GAME_OVER_BANKRUPT = (
    "BANKROTT.\n\n"
    "Nach {turn} Runden ist kein Geld mehr da. Deine Worker haben es vor dir gemerkt.\n"
    "Die Agenten laufen übrigens weiter — sie brauchen kein Gehalt, nur Strom."
)

GAME_OVER_MISALIGNMENT = (
    "KONTROLLVERLUST.\n\n"
    "Nach {turn} Runden liegt das Alignment unter 20. Deine Agenten arbeiten weiter,\n"
    "effizient und pünktlich — nur nicht mehr an dem, was du gemeint hast.\n"
    "Formal bist du noch Geschäftsführer. Praktisch hat dich niemand entlassen;\n"
    "es hat nur aufgehört, eine Rolle zu spielen."
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
    ("7", "Forschung"),
    ("8", "Agent aufwerten"),
    ("9", "Runde beenden"),
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
HEADER_RESEARCH = "FORSCHUNG"
RESEARCH_AVAILABLE = "Verfügbar"
RESEARCH_LOCKED = "Gesperrt"
RESEARCH_DONE_HEADER = "Erforscht"
RESEARCH_EMPTY_AVAILABLE = "Nichts verfügbar. Sammle Research Points."
RESEARCH_LOCKED_HINT = "braucht {missing}"
COL_ALIGNMENT_BALANCE = "Alignment-Bilanz"
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
