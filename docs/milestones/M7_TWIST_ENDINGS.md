# M7 — Der Twist: zwei neue Enden

**Status:** ✅ Abgeschlossen
**Geplant:** 25. August 2026
**Abgeschlossen:** 25. August 2026

## Warum

Fünf Meilensteine haben ausschließlich die Wirtschaftsseite ausgebaut. Der eigentliche
Twist, den [VISION.md](../VISION.md) seit dem ersten Entwurf beschreibt — die KI übernimmt,
sobald der Spieler sich vollständig wegautomatisiert hat — existiert bisher nirgends im
Code: `END_CONDITIONS` in `core/game.py` kennt nur `bankrupt` und `misalignment`. M5s
"Nicht Teil von M5" hält das ausdrücklich als offenen Punkt fest.

Drei Zuschnitte standen zur Wahl: nur die Enden; Enden plus ein heimlich feuernder
HR-Agent (in `GAME_DESIGN.md` spezifiziert, nie gebaut); Enden plus HR-Agent plus
täuschende `ActionResult`-Nachrichten. Der letzte Punkt würde absichtlich eine
bestehende Invariante brechen — Ereignisse sind ehrliche, vollständig offengelegte
Angebote, deren Effekt dem Spieler im selben Zug zurückgemeldet wird — und ist damit,
wie CLAUDE.md es für alle Zwillings-Meilensteine verlangt, eine eigene Architektur-
Entscheidung und kein natürlicher Ausbau. M7 nimmt bewusst nur den ersten, kleinsten
Zuschnitt: zwei neue Enden, rein aus vorhandenem State abgeleitet, plus ein ehrliches
Vorwarnungs-Ereignis. HR-Agent und täuschende Nachrichten bleiben Kandidaten für einen
späteren, eigenen Meilenstein.

## Die Mechanik

**Ein Auslöser, zwei Ausgänge.** `core.game._total_automation(state)` ist wahr, sobald
kein Mensch mehr im Team ist und mindestens `AUTONOMY_AGENT_COUNT` (6) Agenten **ab
Stufe `AUTONOMOUS_AGENT_LEVEL` (2)** im Team sind. Die Flottengröße stammt aus
`GameState.phase()`, die Stufenbedingung nicht — sie ist die Korrektur aus
[BALANCING.md](../BALANCING.md) Nr. 22 und der eigentliche Kern dieses Meilensteins
(siehe „Was die Simulation korrigiert hat" unten).

Welches der beiden Enden dabei herauskommt, entscheidet einzig der Alignment-Wert in
diesem Moment, unter Wiederverwendung der bestehenden `ALIGNMENT_TIERS[0]`-Schwelle
(80.0):

- **Alignment ≥ 80 → „Geheimes Ende" (`GAME_OVER_SECRET`, „FALSCHE HOFFNUNG").** Bei
  Tier 0 hat der Spieler nie eine Alignment-Warnung gesehen (`ALIGNMENT_WARNINGS`
  beginnt erst bei Tier 1) — die psychologische Täuschung, die VISION.md für dieses Ende
  beschreibt, entsteht damit strukturell aus einer bereits bestehenden Schwelle, nicht
  aus neuem Code.
- **20 ≤ Alignment < 80 → „Dystopie" (`GAME_OVER_DYSTOPIA`, „VOLLAUTOMATISIERUNG").**
  Sichtbarer Kontrollverlust. Unter 20 greift ohnehin zuerst die bestehende
  `misalignment`-Bedingung — `END_CONDITIONS` wird der Reihe nach geprüft, erster
  Treffer gewinnt, und `secret_ending` steht bewusst vor `dystopia` in der Liste, weil
  dessen Bedingung eine Teilmenge von dessen Prädikat ist. Die drei Enden sind damit
  eine vollständige, überschneidungsfreie Partition des Alignment-Werts im
  Vollautomatisierungs-Fall.

Kein neues persistentes State-Feld, kein `SAVE_FORMAT_VERSION`-Bump: beide Bedingungen
sind reine Funktionen von `state.workers` und `state.alignment`, genau wie die beiden
bestehenden `EndCondition`s — CLAUDE.md: „die Twist-Enden sind zum Anhängen gedacht,
nicht zur Sonderbehandlung."

## Was die Simulation korrigiert hat

Die erste Fassung zählte Agenten **jeder** Stufe und wurde mit dem Argument dokumentiert,
sie kombiniere nur bereits kalibrierte Konstanten und brauche daher keine eigene
Simulation. Das war der Fehler dieses Meilensteins, und die nachgeholte Simulation hat ihn
in zwei Punkten widerlegt (Details und Zahlen in [BALANCING.md](../BALANCING.md) Nr. 22):

- **Das geheime Ende war auf Runde 0 erreichbar** — sechs Level-1-Agenten kosten rund 255 €
  und keine Forschung.
- **Das Dystopie-Ende feuerte in keinem simulierten Lauf**, weil Level-1-Agenten per Design
  kein Alignment kosten und die Flotte damit dauerhaft bei 100 stand.

Übernommen worden war die *Zahl* `AUTONOMY_AGENT_COUNT`, nicht ihre *Aussage*: Sie
beschreibt eine Phase („du hast skaliert"), die absichtlich früh und billig erreichbar ist.
`AUTONOMOUS_AGENT_LEVEL = 2` schließt die Lücke genau dort, wo VISION.md die Harmlosigkeit
enden lässt. Die Lehre steht als eigener Absatz in BALANCING.md 22: Eine bereits
kalibrierte Konstante wiederzuverwenden ersetzt keine Simulation, sobald sie eine andere
Frage beantworten soll.

**Derselbe Fehler eine Ebene tiefer** ([BALANCING.md](../BALANCING.md) Nr. 24): Die Regel
„ohne erfahrenen Worker läuft kein Projekt" wurde seit M1 nur in `start_project` geprüft,
obwohl ihre eigene Fehlermeldung sie als Dauerzustand formuliert. Genau darüber lief der
Exploit — Projekt mit dem Startmenschen anlegen, Menschen feuern, Level-1-Flotte kassiert
weiter. `economy.service_level_delta` fragt jetzt nach einem *Verantwortlichen*
(`Worker.is_senior`) statt nach irgendeiner Zuweisung, womit die reine Level-1-Besetzung in
denselben Verfall läuft wie ein verlassenes Projekt. Nr. 22 nimmt dieser Flotte das
Spielende, Nr. 24 nimmt ihr die Einnahmen.

**Ein Vorbote, der nicht lügt.** Neues Ereignis `full_automation_warning` (Kategorie
`AI`, `data/events.json`) feuert einen Schritt vor der Vollautomatisierung — 6 Agenten,
höchstens noch ein Mensch — und lässt den Spieler wählen: 200 € zahlen und die letzte
Stelle rechtfertigen (+3 Alignment) oder Kurs halten (−3 Alignment). Beide Optionen
werden wie jede andere über `Game._apply_event_option` verbucht und zurückgemeldet —
das Ereignis warnt, blockiert aber mechanisch nichts. Dafür war ein neuer Eintrag
`max_humans` in `events.CONDITION_CHECKS` nötig (Spiegelbild von `min_humans`,
`EventContext.humans` existierte bereits).

## Was das kostet

- Zwei neue `EndCondition`-Einträge in `core/game.py`, eine private Hilfsfunktion
  `_total_automation` plus die Konstante `AUTONOMOUS_AGENT_LEVEL`, zwei neue
  `GAME_OVER_*`-Konstanten in `strings.py`.
- `ALIGNMENT_TIERS` musste von unten im Modul nach oben wandern (neben
  `MISALIGNMENT_THRESHOLD`), weil `END_CONDITIONS` es beim Modul-Import schon braucht.
- Ein neuer Eintrag `max_humans` in `events.CONDITION_CHECKS`, ein neues Ereignis in
  `data/events.json`. Keine Schema-Änderung an `EventContext` oder `GameState`.
- `workers.SENIOR_LEVEL` und `Worker.is_senior` lösen die bis dahin an zwei Stellen
  verstreute wörtliche `2` ab; `_advance_service_level` nimmt jetzt den `TurnReport`
  entgegen, um den Verfall zu benennen (`PROJECT_NEGLECTED`/`PROJECT_UNSUPERVISED`).

## Nicht Teil von M7

Ein heimlich feuernder HR-Agent (GAME_DESIGN.md §3.6) — die Rolle `HR` existiert im
`Role`-Enum bis heute nicht. Täuschende `ActionResult`-Nachrichten oder blockierte
Aktionen mit falscher Begründung — beides bricht absichtlich die „Ereignisse lügen nie"-
Invariante und braucht einen eigenen Entwurf. Ein Hostile-Takeover-Ende über
`investor_equity` — laut `INVESTOR_EQUITY_CAP`s Kommentar in `core/game.py` bewusst der
Alignment-Achse vorbehalten, bleibt aber unimplementiert und ist ein anderes Thema als
die hier gebauten, automatisierungsgetriebenen Enden.

## Ergebnis

Umgesetzt, aber **nicht wie geplant**: Die Stufenbedingung `AUTONOMOUS_AGENT_LEVEL` kam
erst nach der nachgeholten Simulation dazu und ist die eigentliche Substanz des
Meilensteins (siehe oben). Kein Save-Format-Bump (weiterhin Version 6) — beide neuen
Enden sind reine Ableitungen aus bestehendem State.

## Testlage

`tests/test_endings.py` (neu). Da die Enden am Ende von `resolve_turn()` geprüft werden,
also **nach** dem Alignment-Verfall der Runde, zielen alle Fixtures eine Runde Verfall
über dem getesteten Tier:

- Vollautomatisierung, die exakt auf 80,0 landet, endet mit dem geheimen Ende; knapp
  darunter mit der Dystopie — beide Nachrichten erscheinen in `game_over_reason` und
  `report.events`.
- Vollautomatisierung unterhalb von 20 endet stattdessen als Kontrollverlust
  (Reihenfolge-Test).
- **Regression zu BALANCING.md 22:** Eine Flotte aus zehn Level-1-Agenten ohne einen
  einzigen Menschen beendet das Spiel *nicht*; ebenso wenig eine Flotte, die die Zahl nur
  mit Level-1-Agenten auffüllt.
- Ein einzelner verbliebener Mensch oder eine Flotte unterhalb der Autonomie-Schwelle
  verhindert beide neuen Enden.
- Aktionen werden nach jedem der beiden neuen Enden verweigert.

`tests/test_service_level.py` — Ergänzungen zu [BALANCING.md](../BALANCING.md) Nr. 24:
- Ein fertiges Projekt, das an Level-1-Agenten übergeben wird, rutscht zurück.
- Dieselbe Flotte auf Stufe 2 hält den Servicegrad bei 100 — die Regel fragt nach
  Verantwortung, nicht nach Agenten als solchen.
- Der Verfall bekommt seine eigene Zeile im Rundenbericht.

`tests/test_events.py` — Ergänzungen: `max_humans` als eigenständige Bedingung, sowie ein
Test, dass `full_automation_warning` exakt ab 6 Agenten und höchstens einem Menschen
verfügbar wird, nicht früher.

`pytest` (292 Tests) und `ruff check .` bleiben grün.
