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
| M? | Weitere Geldsenken *(noch nicht geplant)* | ⬜ offen | — |

## Offene Punkte ohne eigenen Meilenstein

Befunde, die feststehen, aber noch keinem Meilenstein zugeordnet sind. Sie stehen
hier, damit sie beim Planen des nächsten Meilensteins auf dem Tisch liegen.

- **Geldsenke fehlt — von [M4](./M4_EVENTS.md) teilweise beantwortet.** Nach M3 endete
  der Spieler in jeder Simulation mit über 30.000 € und keiner einzigen knappen Runde.
  M4 bringt mit den Ereignissen (Miete, Krankenversicherung, Steuererhöhung,
  KI-Regulierung als laufende Fixkosten, dazu einmalige Kosten wie Rezession oder Auto
  kaputt) eine echte Geldsenke — ein Ein-Projekt-Team mit dünner Marge geht jetzt in
  knapp der Hälfte simulierter Läufe bankrott, wo es vorher nie geschah
  ([BALANCING.md](../BALANCING.md) Nr. 19). **Ausdrücklich nicht abschließend**: Produkte,
  Upgrades, Büro-Ausbau und Investoren-Auszahlungen jenseits der Ereignis-Fixkosten
  bleiben Kandidaten für einen späteren Meilenstein.
- **Kunden-App und Web-App sind wirtschaftlich fast identisch** — beide fordern drei
  Stellen, und die Zielgröße hängt nur an der Stellenzahl. Eine der beiden braucht eine
  vierte Stelle oder eine andere Laufzeit.
- **Ein Projekt, das bei Ablauf nie fertig wurde, hat keine Folgen.** Naheliegender
  Anknüpfungspunkt für die Ereignisse — in [M4](./M4_EVENTS.md) als offene Frage geführt,
  weil es streng genommen eine Projektregel ist und kein externer Druck.

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
