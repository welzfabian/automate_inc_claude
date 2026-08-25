# Meilensteine

Ein Dokument pro Meilenstein, damit der Projektstand ohne Git-Archäologie
nachvollziehbar bleibt: was war das Ziel, was ist tatsächlich entstanden, welche
Entscheidungen mussten unterwegs getroffen werden — und was ausdrücklich **nicht**
Teil davon war.

| Meilenstein | Titel | Status | Abgeschlossen |
|-------------|-------|--------|---------------|
| [M1](./M1_VERTICAL_SLICE.md) | Spielbarer Vertical Slice | ✅ Abgeschlossen | 24. August 2026 |
| [M2](./M2_AUTOMATION_BITES_BACK.md) | Automatisierung beißt zurück | ✅ Abgeschlossen | 24. August 2026 |
| [M3](./M3_SERVICE_LEVEL_AND_MAINTENANCE.md) | Servicegrad und Instandhaltung | ✅ Abgeschlossen | 24. August 2026 |
| [M4](./M4_EVENTS.md) | Druck von außen: Ereignisse | ✅ Abgeschlossen | 24. August 2026 |
| [M5](./M5_OFFICE_AND_INVESTORS.md) | Büro-Ausbau und Investoren-Auszahlung | ✅ Abgeschlossen | 25. August 2026 |
| [M7](./M7_TWIST_ENDINGS.md) | Der Twist: zwei neue Enden | ✅ Abgeschlossen | 25. August 2026 |
| [M8](./M8_PROJECT_LADDER.md) | Die Projektleiter | ✅ Abgeschlossen | 25. August 2026 |

## Offene Punkte ohne eigenen Meilenstein

Befunde, die feststehen, aber noch keinem Meilenstein zugeordnet sind. Sie stehen
hier, damit sie beim Planen des nächsten Meilensteins auf dem Tisch liegen.

- **Geldsenke fehlt — von [M4](./M4_EVENTS.md) teilweise beantwortet.** Nach M3 endete
  der Spieler in jeder Simulation mit über 30.000 € und keiner einzigen knappen Runde.
  M4 bringt mit den Ereignissen (Miete, Krankenversicherung, Steuererhöhung,
  KI-Regulierung als laufende Fixkosten, dazu einmalige Kosten wie Rezession oder Auto
  kaputt) eine echte Geldsenke — ein Ein-Projekt-Team mit dünner Marge geht jetzt in
  knapp der Hälfte simulierter Läufe bankrott, wo es vorher nie geschah
  ([BALANCING.md](../BALANCING.md) Nr. 19). [M5](./M5_OFFICE_AND_INVESTORS.md) deckt davon
  Büro-Ausbau und Investoren-Auszahlungen ab. **Ausdrücklich nicht abschließend**:
  Produkte, Upgrades und Agenten-Wartung bleiben Kandidaten für einen späteren
  Meilenstein. **Verschärft nach M7** ([BALANCING.md](../BALANCING.md) Nr. 28–29): Die
  45-%-Bankrottquote aus Nr. 19 war eine Eigenschaft der damaligen Simulationspolitik
  (sie hat das abgelaufene Projekt nicht ersetzt), nicht der Zahlen — mit
  Anschlussprojekt überlebt dasselbe Team 11 von 11 Läufen. Die Ereignisse halbieren das
  Wachstum, drücken den Tiefpunkt aber nicht. Wer drei Projekte am Laufen hat, endet
  weiterhin bei 10.000–23.000 €. **Beantwortet von [M8](./M8_PROJECT_LADDER.md)**
  ([BALANCING.md](../BALANCING.md) Nr. 38): Einmalige, wachsende Aufträge verlangen für jede
  Sprosse Personal, Schreibtische und Fixkosten. Kein Lauf endet mehr mit einem Überschuss
  von 10.000 €; Geld ist erstmals der Engpass. **Neu offen:** Wenn der Katalog leer ist,
  enden die Einnahmen und die Gehälter laufen weiter — der Anlass für die Produkte.
- **Kunden-App und Web-App sind wirtschaftlich fast identisch** — beide fordern drei
  Stellen, und die Zielgröße hängt nur an der Stellenzahl. Eine der beiden braucht eine
  vierte Stelle oder eine andere Laufzeit. **Präzisiert nach M7**
  ([BALANCING.md](../BALANCING.md) Nr. 27): Für ein Menschen-Team stimmt das noch
  (87,5 gegen 87,0 €/Runde), für jedes Agenten-Team nicht mehr — die Kunden-App liegt
  über die Laufzeit 700 € vorn, weil ihre Sales-Stelle Sichtbarkeit bringt, wo die zweite
  Entwicklerstelle der Web-App vor allem Bugs beisteuert. **Erledigt von
  [M8](./M8_PROJECT_LADDER.md):** Beide sind jetzt einmalig und führen auf verschiedene
  Äste der Leiter (Kunden-App → KI-Integration, Web-App → Konzern-Warenwirtschaft), und der
  letzte Auftrag verlangt beide. Sie konkurrieren nicht mehr, sie sind eine Reihenfolge.
- **Ein Projekt, das bei Ablauf nie fertig wurde, hat keine Folgen.** Naheliegender
  Anknüpfungspunkt für die Ereignisse — in [M4](./M4_EVENTS.md) als offene Frage geführt,
  weil es streng genommen eine Projektregel ist und kein externer Druck. **Wiegt seit
  [M8](./M8_PROJECT_LADDER.md) schwerer:** Aufträge sind einmalig, also ist ein
  verpatzter Auftrag endgültig verpatzt — und blockiert womöglich eine Referenz für die
  nächste Sprosse. Genau deshalb sollte er etwas bedeuten.
- **Produkte fehlen — und der Katalog geht aus.** Der Weg Projekt → Produkt aus
  [PROJECTS_AND_PRODUCTS_SPEC.md](../PROJECTS_AND_PRODUCTS_SPEC.md) §8 ist der nächste
  Meilenstein. [M8](./M8_PROJECT_LADDER.md) erzeugt den Druck (eine Level-1-Flotte arbeitet
  über 120 Runden alle elf Aufträge ab und geht danach in 6 von 11 Läufen bankrott),
  beantwortet ihn aber ausdrücklich nicht. Mit zu entscheiden: ob „Katalog leer" ein
  eigenes Ende verdient.
- **Eine Forscher-Stelle auf einem Projekt braucht erst ein Attribut, das sie hält**
  ([BALANCING.md](../BALANCING.md) Nr. 36). Solange es keines gibt, ist so eine Stelle
  gratis leer zu lassen und bricht die Voll-Besetzungs-Invariante — weshalb die beiden
  Vierer-Aufträge von der Spec abweichen und ohne Forscher auskommen.
- **Das geheime Ende ist der Regelfall, nicht die Ausnahme** — der wichtigste Befund der
  Simulation nach M7 ([BALANCING.md](../BALANCING.md) Nr. 25). `_check_game_over` prüft
  die Vollautomatisierung am Ende **der Runde, in der sie zum ersten Mal gilt**; bis
  dahin stand mindestens ein Mensch auf der Gehaltsliste und hat das Alignment oben
  gehalten. Ergebnis: „FALSCHE HOFFNUNG" in 11 von 11 Läufen, die Dystopie nur, wenn der
  Spieler überflüssige Menschen drei Runden zu lang bezahlt. [VISION.md](../VISION.md)
  verlangt „Alignment > 80 **bis Spielende**" — eine Dauer, implementiert als
  Momentaufnahme. Das ist derselbe Fehlertyp wie Nr. 22 und Nr. 24, eine Ebene höher.
  Bewusst nicht als Zahlenkorrektur behandelt: Jede Auflösung ändert, was die beiden
  Enden bedeuten, und braucht einen eigenen Meilenstein. `full_automation_warning` hängt
  mit dran (Nr. 26) — die Vorwarnung feuert in ≤ 20 % der Läufe, weil ihr Zeitfenster
  ein bis zwei Runden lang ist, nicht weil ihre Bedingung zu eng wäre.
  **Nach [M8](./M8_PROJECT_LADDER.md) verschoben, nicht behoben**
  ([BALANCING.md](../BALANCING.md) Nr. 37): Die Leiter verlängert den Anlauf, das Alignment
  steht beim Übergang bei 66–76 statt 89, und dieselbe Messung liefert jetzt Dystopie
  11/11 statt geheimes Ende 11/11. Der Zeitpunkt-statt-Dauer-Fehler steht unverändert —
  wer das Tempo wieder ändert, kippt die Verteilung zurück, ohne die Enden anzufassen.
- **Agentenstufe 3 ist als Kaufentscheidung nie richtig** ([BALANCING.md](../BALANCING.md)
  Nr. 27): teurer als Stufe 2 (Faktor 2,2 auf die Tokens gegen 1,33 auf die Effizienz),
  und die zusätzliche Effizienz verpufft am Attribut-Deckel, den schon Level-1-Agenten
  erreichen. Die Einnahmen *fallen* mit der Stufe, weil erst ab Stufe 2 Nebeneffekte
  existieren. Stufe 3 lohnt sich damit ausschließlich als Türöffnerin für den
  DANGEROUS-Ast. Offen, ob das die beabsichtigte Satire ist oder eine Zahl, die nachgezogen
  gehört.
- **Die Token-Inflation wirkt innerhalb einer Partie nicht** ([BALANCING.md](../BALANCING.md)
  Nr. 30): Die Drift liegt real bei ≈ 0,8 %/Runde und ist kleiner als die Streuung —
  nach 60 Runden liegt der Preis in manchen Läufen unter dem Startwert. Der Gleichstand
  zwischen Agenten- und Menschen-Team läge im Median bei Runde 70–135. Eine Korrektur
  setzt voraus, dass die Zielspiellänge irgendwo festgeschrieben wird; das ist sie nicht.

## Konvention

- **Dateiname:** `M<n>_<KURZTITEL>.md`
- **Angelegt wird die Datei beim Planen**, mit Status „In Arbeit" und dem Zielbild.
  Beim Abschluss kommen Ergebnis, Abweichungen und Testlage dazu.
- **Status:** ⬜ offen · 🔄 in Arbeit · ✅ abgeschlossen · ❌ verworfen
- **Keine Duplikate:** Dauerhaft gültige Regeln gehören in die Spec-Dokumente
  ([GAME_DESIGN.md](../GAME_DESIGN.md), [PROJECTS_AND_PRODUCTS_SPEC.md](../PROJECTS_AND_PRODUCTS_SPEC.md))
  bzw. nach [BALANCING.md](../BALANCING.md). Die Meilenstein-Datei ist eine **Chronik**
  und verlinkt dorthin, statt Regeln zu wiederholen. Wo beides auseinanderfällt, gilt
  das Spec-Dokument.
- **Zahlen im Spiel** stehen immer in `src/automate_inc/data/*.json` — auch dorthin wird
  verlinkt statt kopiert.
