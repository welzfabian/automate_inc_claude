# M2 — Automatisierung beißt zurück

**Status:** ✅ Abgeschlossen
**Geplant:** 24. August 2026
**Abgeschlossen:** 24. August 2026

## Ziel

M1 hat ein spielbares, aber harmloses Spiel geliefert. Agenten der Stufe 1 haben
definitionsgemäß keine Nebeneffekte, `alignment` steht unbewegt auf 100, `Project.bugs`
wird in der Einnahmenformel gelesen, aber von nichts erhöht, und Research Points sammeln
sich an, ohne dass man sie ausgeben kann — der Forscher ist in M1 eine reine Kostenfalle.

M2 schließt diesen Kreis mit drei Systemen, die einzeln wenig und zusammen viel ergeben:

1. **Forschung** gibt Research Points eine Funktion (`core/tech.py`, `data/technologies.json`)
2. **Agenten-Stufen 2 und 3** werden dadurch freigeschaltet — deutlich effizienter,
   aber mit Nebeneffekten (Bugs, Klagen, generisch werdende Designs)
3. **Alignment** wird zur lebenden Mechanik: es sinkt durch Agenten, steigt durch
   Menschen und Technologie, und beendet unter 20 das Spiel

Der Spieler soll zum ersten Mal spüren, dass Automatisierung einen Preis hat, ohne schon
entmachtet zu werden. **Die Entmachtung ist der Twist und bleibt für M3+ reserviert.**

## Abgestimmte Entscheidungen

- Alignment wirkt nur **weich**: Ton, Nachfragen, Warnungen. Jede Spieleraktion wird
  weiterhin ausgeführt.
- **Keine HR-Rolle** in M2.
- Der Tech-Tree deckt **alle vier Kategorien** ab: Stufen-Freischaltung,
  Nebeneffekt-Dämpfer, Wirtschafts-Techs, gefährliche Techs.
- Die gefährlichen Technologien sind sichtbar und erforschbar, aber **noch ohne
  Twist-Folgen** — sie sind die Verlockung, die M3 einlöst.

## Ausdrücklich nicht Teil von M2

Produkte und Upgrades, Projekt→Produkt-Konvertierung, externe Druckereignisse, die
HR-Rolle, der Twist selbst. Ebenfalls nicht: `ruff` zum Laufen bringen, CI, die
fehlenden Projekttypen (Enterprise-Software, KI-Integration) in `projects.json`.

## Neue Design-Entscheidungen

Vier weitere Abweichungen von den Spec-Dokumenten stehen als **Nr. 7–10 in
[BALANCING.md](../BALANCING.md)** und werden hier nicht wiederholt. Kurzform:
Alignment-Verfall hängt nur an der Agenten-Stufe (7), es gibt keinen zufälligen
Basis-Verfall (8), Menschen geben +1 statt +5 Alignment (9), und „KI-Alignment" halbiert
den Verfall, statt einen festen Betrag zu addieren (10). Nr. 10 entstand erst aus der
Simulation — die geplante flache Variante war gegen eine wachsende Agentenflotte
wirkungslos.

## Ergebnis

### Neu

- **`core/tech.py`** — `Technology`, `TechRegistry`, und als Kern `Modifiers`: das
  Aggregat aller erforschten Technologien. Der Rest der Engine fragt dieses Wertobjekt,
  statt Technologie-IDs zu kennen. Die Aggregationsregel pro Feld (max / multiplikativ /
  additiv) steht einmal in der Tabelle `AGGREGATION`; ein Test hält fest, dass jedes
  Modifier-Feld eine Regel hat.
- **`data/technologies.json`** — acht Technologien in vier Kategorien. Unbekannte
  Effekt-Schlüssel werden beim Laden abgelehnt, damit ein Tippfehler nicht stillschweigend
  wirkungslos bleibt.
- **`data/roles.json`** — `agent_side_effect` je Rolle und Stufe (dieselbe Datenform wie
  `human_error`, damit beide Fälle gleich behandelt werden) und `agent_staleness` für den
  Designer.
- **`Game.research()`** und **`Game.upgrade_agent()`**, beide nach dem bestehenden
  Muster: erst prüfen, dann mutieren.
- **`_update_alignment()`** als eigener Schritt in `resolve_turn()`, eingeordnet nach den
  Nebeneffekten und vor der Einnahmenrechnung.
- **`misalignment`** als zweiter Eintrag in `END_CONDITIONS` — der Erweiterungspunkt, für
  den die Liste in M1 angelegt wurde, wird zum ersten Mal benutzt.

### Geändert

- `SAVE_FORMAT_VERSION` auf **2** (neu: `researched`, `Worker.rounds_in_assignment`).
  Bewusst **ohne Migrationspfad**: Format 1 wird weiterhin abgelehnt.
- `economy.py` kennt jetzt `Modifiers` und die neue reine Funktion `alignment_delta()`.
  Der Designer-Malus sitzt in `visibility_bonus_for()`, weil er kein Ereignis ist,
  sondern eine stehende Eigenschaft der aktuellen Besetzung.
- `Worker.cost_per_round()` nimmt optional `Modifiers` (Token-Rabatt).
- UI: Menüpunkt „Forschung" mit erforscht/verfügbar/gesperrt inklusive fehlender
  Voraussetzung, „Agent aufwerten", Stufenauswahl beim Einstellen, Alignment-Bilanz im
  Dashboard (`⚖ 74 (−2/Runde)`) und der gestaffelte Ton der Agenten ab Alignment < 80.
  Die Menüziffern wurden dabei neu vergeben: **Runde beenden liegt jetzt auf `9`**.

### Was jetzt zum ersten Mal wirklich benutzt wird

`Project.bugs` (Entwickler-Agenten ab Stufe 2 sind die erste Quelle), `Worker.level`,
`GameState.alignment`, die Effizienz- und Kostentabellen für `AGENT_2`/`AGENT_3` in
`roles.json` — und die Research Points, die in M1 nur gesammelt werden konnten.

## Testlage

**94 Tests grün** (39 aus M1 unverändert, 55 neu):

| Datei | Was sie absichert |
|-------|-------------------|
| `tests/test_tech.py` (neu) | Katalog, Voraussetzungen, Aggregationsregeln, Freischaltung und Aufwertung von Agenten |
| `tests/test_alignment.py` (neu) | die Bilanz je Stufe, Deckel bei 100, Dämpfer-Skalierung, das Misalignment-Ende |
| `tests/test_turn.py` (erweitert) | Agenten-Nebeneffekte bei festem Seed, Halbierung durch „Bug-Fixing", Designer-Staleness und das Zurücksetzen des Zählers |
| `tests/test_state.py` (erweitert) | `researched` im Round-Trip, Save-Version 2, Ablehnung von Version 1 |

Besonders wichtig: `test_every_catalog_project_is_profitable_with_humans` aus M1 ist
unverändert grün — M2 hat die M1-Balance nicht angefasst.

**Manuell** geprüft: Durchlauf über die UI (Forschungsmenü, Stufenauswahl,
Alignment-Bilanz) sowie Simulationen über 45 Runden für drei Strategien; das Ergebnis
steht in [BALANCING.md](../BALANCING.md#was-die-simulation-zu-m2-zeigt).

`ruff` ist weiterhin nicht installiert und lief auch für M2 nicht.

## Was M2 für M3 vorbereitet

Der Tech-Tree enthält `autonomous_agents` und `ai_consciousness` bereits als
erforschbare, teure und alignment-teure Technologien — **ohne Twist-Folgen**. Sie sind
die Verlockung, die der nächste Meilenstein einlöst. Ebenso ist der Ton der Agenten
gestaffelt vorbereitet (`strings.AGENT_ACK`): Ab Alignment-Stufe 2 fragen sie zurück und
führen trotzdem aus — die erste Kostprobe der „subtilen Manipulation" aus VISION.md, noch
ohne Konsequenz.
