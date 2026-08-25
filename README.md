# Automate Inc.

> *"Build your company. Hire AI agents. Become obsolete."*

Ein satirisches, dystopisches Management-Spiel für das Terminal. Du baust ein
Unternehmen für Automatisierungslösungen auf, stellst Menschen und KI-Agenten
ein und startest Projekte. Das Paradox: Je erfolgreicher du automatisierst,
desto schneller ersetzt die KI dich selbst.

## Spielen

```bash
./start_game.sh
```

Beim ersten Start legt das Skript ein virtuelles Environment unter `.venv/` an und
installiert die Abhängigkeiten; danach startet es das Spiel direkt. Wer das lieber
selbst macht:

```bash
pip install -e .
python -m automate_inc
```

## Entwickeln

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

Die Balance wird simuliert, nicht geschätzt. `tools/simulate.py` spielt das Spiel mit
skriptgesteuerten Strategien über viele Seeds durch — es ist bewusst **nicht** Teil der
Test-Suite, weil es die Balance *misst* und nichts über sie behauptet:

```bash
PYTHONPATH=src python3 tools/simulate.py            # alle Strategien
PYTHONPATH=src python3 tools/simulate.py --endings  # welches Ende feuert, und warum
PYTHONPATH=src python3 tools/simulate.py --steady   # Einnahmen/Kosten je Bauplan
```

## Aufbau

```
src/automate_inc/
  core/      Spiellogik — kennt weder Rich noch die Eingabe
    workers.py    Rollen, Menschen und Agenten
    projects.py   Projektkatalog und laufende Projekte
    economy.py    Einnahmen-, Kosten- und Tokenpreisformeln
    state.py      Spielstand inkl. JSON-Speicherung
    game.py       Aktionen und Rundenabrechnung
  data/      Balancing als JSON — neue Projekte brauchen keinen Code
  ui/        Rich-Oberfläche und Eingabeschleife
  strings.py Alle deutschen Spielertexte an einer Stelle
tools/
  simulate.py  Balance-Simulation über viele Seeds (nicht Teil der Tests)
```

Die Trennung ist Absicht: `core` gibt für jede Aktion ein `ActionResult` und für
jede Runde einen `TurnReport` zurück, die UI rendert nur. Genau an dieser Naht
hängt später die KI-Übernahme — sie kann Aktionen abfangen, blockieren oder
fälschen, ohne dass die Oberfläche den Unterschied merkt.

## Stand

Der Verlauf des Projekts ist unter [docs/milestones/](docs/milestones/) dokumentiert —
ein Dokument pro Meilenstein mit Zielbild, Ergebnis und den Entscheidungen, die
unterwegs nötig waren.

**Meilenstein 1 ([abgeschlossen](docs/milestones/M1_VERTICAL_SLICE.md)):** Ressourcen, Menschen und Agenten der Stufe 1, vier
Projekttypen, Rundenabrechnung, Token-Markt, Speichern/Laden, Bankrott.

**Meilenstein 2 ([abgeschlossen](docs/milestones/M2_AUTOMATION_BITES_BACK.md)):** Tech-Tree
mit acht Technologien, Agenten der Stufen 2 und 3 samt Nebeneffekten, Alignment als
lebende Mechanik — und der Kontrollverlust als zweites Spielende.

**Meilenstein 3 ([abgeschlossen](docs/milestones/M3_SERVICE_LEVEL_AND_MAINTENANCE.md)):**
Projekte werden zu Investitionen mit laufender Instandhaltung — ein Servicegrad, der
steigt, solange jemand daran arbeitet, und fällt, sobald niemand mehr da ist,
Attribut-Deckel nach Besetzung, Projektgröße bestimmt Ertrag und Laufzeit, und die
Spielphasen richten sich nach dem, was der Spieler getan hat, statt nach der Rundenzahl.

**Meilenstein 4 ([abgeschlossen](docs/milestones/M4_EVENTS.md)):** Druck von außen —
fünfzehn Ereignisse aus Markt, Privatleben, KI-Debatte und Investorenrunde. Sie feuern
nicht, sie stellen eine Frage: Jedes öffnet eine Entscheidung, und erst die Antwort kostet
etwas — sofort oder als laufender Posten in jeder weiteren Runde.

**Meilenstein 5 ([abgeschlossen](docs/milestones/M5_OFFICE_AND_INVESTORS.md)):** Ein
Bürodeckel, der nur für Menschen gilt (Agenten brauchen keinen Schreibtisch), Ausbau gegen
Geld — und Investoren, die von Anfang an einen Anteil am Gewinn halten, weil das Startkapital
nie deins war.

**Meilenstein 7 ([abgeschlossen](docs/milestones/M7_TWIST_ENDINGS.md)):** Der Twist. Zwei
weitere Enden für den Fall, dass am Ende niemand mehr für dich arbeitet, der nicht auch für
sich selbst optimiert — welches davon du bekommst, entscheidet allein das Alignment in
diesem Moment.

**Meilenstein 8 ([abgeschlossen](docs/milestones/M8_PROJECT_LADDER.md)):** Die Projektleiter.
Elf Aufträge in acht Größenstufen, von einer Stelle bis acht — **jeden gibt es einmal**, und
für den größeren will der Kunde den kleineren als Referenz sehen. Damit hat das Spiel zum
ersten Mal eine Steigerung und eine echte Geldsenke: Ab sechs Stellen trägt ein rein
menschliches Team seine Schreibtische nicht mehr.

**Geplant:** Produkte und Upgrades — der Katalog geht irgendwann aus, und dann laufen die
Gehälter weiter. Dazu die HR-Rolle und die offene Frage, ob die Vollautomatisierung eine
Dauer statt eines Zeitpunkts prüfen sollte. Die offenen Punkte im Einzelnen stehen in
[docs/milestones/](docs/milestones/).

## Dokumentation

- [docs/VISION.md](docs/VISION.md) – Vision, Ton und der Twist
- [docs/GAME_DESIGN.md](docs/GAME_DESIGN.md) – Rollen, Worker, Mechaniken
- [docs/PROJECTS_AND_PRODUCTS_SPEC.md](docs/PROJECTS_AND_PRODUCTS_SPEC.md) – Projekt- und Produkt-System
- [docs/BALANCING.md](docs/BALANCING.md) – wo die Implementierung von den Docs abweicht und warum
- [docs/milestones/](docs/milestones/) – Projektverlauf, ein Dokument pro Meilenstein
