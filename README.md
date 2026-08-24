# Automate Inc.

> *"Build your company. Hire AI agents. Become obsolete."*

Ein satirisches, dystopisches Management-Spiel für das Terminal. Du baust ein
Unternehmen für Automatisierungslösungen auf, stellst Menschen und KI-Agenten
ein und startest Projekte. Das Paradox: Je erfolgreicher du automatisierst,
desto schneller ersetzt die KI dich selbst.

## Spielen

```bash
pip install -e .
python -m automate_inc
```

Ohne Installation genügt `PYTHONPATH=src python -m automate_inc`, sofern `rich`
verfügbar ist.

## Entwickeln

```bash
pip install -e ".[dev]"
pytest
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
```

Die Trennung ist Absicht: `core` gibt für jede Aktion ein `ActionResult` und für
jede Runde einen `TurnReport` zurück, die UI rendert nur. Genau an dieser Naht
hängt später die KI-Übernahme — sie kann Aktionen abfangen, blockieren oder
fälschen, ohne dass die Oberfläche den Unterschied merkt.

## Stand

**Meilenstein 1 (spielbar):** Ressourcen, Menschen und Agenten der Stufe 1, vier
Projekttypen, Rundenabrechnung, Token-Markt, Speichern/Laden, Bankrott.

**Geplant:** Produkte und Upgrades, Tech-Tree, Agenten-Stufen 2 und 3, externe
Druckereignisse (Investoren, Privatleben, Markt), HR-Rolle — und der Twist.

## Dokumentation

- [docs/VISION.md](docs/VISION.md) – Vision, Ton und der Twist
- [docs/GAME_DESIGN.md](docs/GAME_DESIGN.md) – Rollen, Worker, Mechaniken
- [docs/PROJECTS_AND_PRODUCTS_SPEC.md](docs/PROJECTS_AND_PRODUCTS_SPEC.md) – Projekt- und Produkt-System
- [docs/BALANCING.md](docs/BALANCING.md) – wo die Implementierung von den Docs abweicht und warum
