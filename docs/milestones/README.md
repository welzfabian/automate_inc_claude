# Meilensteine

Ein Dokument pro Meilenstein, damit der Projektstand ohne Git-Archäologie
nachvollziehbar bleibt: was war das Ziel, was ist tatsächlich entstanden, welche
Entscheidungen mussten unterwegs getroffen werden — und was ausdrücklich **nicht**
Teil davon war.

| Meilenstein | Titel | Status | Abgeschlossen |
|-------------|-------|--------|---------------|
| [M1](./M1_VERTICAL_SLICE.md) | Spielbarer Vertical Slice | ✅ Abgeschlossen | 24. August 2026 |
| [M2](./M2_AUTOMATION_BITES_BACK.md) | Automatisierung beißt zurück | ✅ Abgeschlossen | 24. August 2026 |
| M3 | Zufallsereignisse *(noch nicht geplant)* | ⬜ offen | — |

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
