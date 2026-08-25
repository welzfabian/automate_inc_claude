# M8 — Die Projektleiter

**Status:** ✅ Abgeschlossen · 25. August 2026

## Ziel

Jeden Auftrag gibt es **einmal**, und die Aufträge werden **größer** — mehr Stellen, mehr
Einnahmen, längere Laufzeit. Damit bekommt das Spiel eine Steigerung, die es nach
[BALANCING.md](../BALANCING.md) Nr. 31 nicht hatte: Ein Menschen-Team lieferte mit einem und
mit drei erlaubten Projekten dasselbe Ergebnis, weil „Web-App auf Dauerschleife" das Optimum
war.

Die Vorgabe kam aus drei Entscheidungen:

- **Viel mehr Aufträge, immer größer** — und irgendwann muss man auf Produkte umstellen.
  Produkte sind ausdrücklich **nicht** Teil von M8.
- **Acht Stufen, bis 6–8 Stellen.**
- **Ab einer Stufe unbezahlbar** für ein reines Menschen-Team.

## Was entstanden ist

**Elf Baupläne in acht Größenstufen**, von einer Stelle bis acht
([`data/projects.json`](../../src/automate_inc/data/projects.json)). Die vier bestehenden
bleiben unverändert — sie waren kalibriert, und M8 rührt sie nicht an. Neu sind Landingpage
(1), Konzern-Warenwirtschaft und KI-Integration (4), SaaS-Plattform (5), Plattform-Neubau
(6), Konzern-Suite (7) und Konzern-KI-Plattform (8). Die beiden Vierer stehen seit M1 als
`ProjectType` im Enum und fehlten nur im Katalog.

**Zwei Regeln, beide Konfiguration** (siehe [BALANCING.md](../BALANCING.md) Nr. 32):

- `GameState.started_projects` — jeder Bauplan wird beim Start vermerkt und ist danach weg.
- `ProjectBlueprint.requires` — dieselbe Form wie `Technology.requires`. Der letzte Auftrag
  verlangt beide Äste der Leiter; es gibt keine Abkürzung nach oben.

**Ein Fehler, den die Leiter aufgedeckt hat:** Nicht angeforderte *Qualität* war nie
neutral — nur Ästhetik war es. Die Landingpage (kein Entwickler) verdiente die Hälfte.
[BALANCING.md](../BALANCING.md) Nr. 35.

**Save-Format 6 → 7.**

## Entscheidungen unterwegs

| Frage | Entscheidung | Wo begründet |
|---|---|---|
| Wie hoch dürfen die Einnahmen der großen Aufträge sein? | Nicht frei wählbar — die Voll-Besetzungs-Invariante gibt zwei Untergrenzen vor | [Nr. 33](../BALANCING.md) |
| Wie wird der Menschen-Pfad unbezahlbar, wenn die Einnahmen nach unten gebunden sind? | Über `basis_fixed_costs`; die verschieben das Niveau, nie den Vergleich | [Nr. 34](../BALANCING.md) |
| Forscher-Stellen auf den beiden Vierer-Aufträgen, wie in der Spec? | Nein — eine Stelle ohne Attribut ist gratis leer zu lassen und bricht die Invariante | [Nr. 36](../BALANCING.md) |
| Was, wenn der Katalog leer ist? | Nichts. Die Einnahmen enden, der Bankrott kommt — das ist der Anlass für die Produkte | [Nr. 38](../BALANCING.md) |

## Was die Simulation zeigt

Vollständig in [BALANCING.md](../BALANCING.md) Nr. 34, 37 und 38. Die drei Kernpunkte:

- **Die Wand steht bei sechs Stellen.** Menschen: +87 (3 Stellen) → +20 (6) → −80 (8).
  Agenten bleiben über alle Stufen bei +180 bis +295. Sechs Stellen brauchen zwei
  Büroausbauten (900 €) und tragen über die Laufzeit 560 € ein.
- **Die Enden haben sich verschoben, ohne dass sie angefasst wurden.** Automatisieren endete
  vor M8 in 11 von 11 Seeds im geheimen Ende; jetzt in 11 von 11 in der Dystopie, weil der
  längere Anlauf das Alignment vor dem Übergang unter 80 drückt. Das geheime Ende bleibt
  erreichbar — für den, der die Leiter überspringt. [Nr. 37](../BALANCING.md)
- **Geld ist zum ersten Mal knapp.** Der offene Punkt „Geldsenke fehlt" aus M3 ist damit
  beantwortet; kein Lauf endet mehr mit 10.000 € Überschuss.

## Ausdrücklich nicht Teil von M8

- **Produkte.** Der Weg Projekt → Produkt aus
  [PROJECTS_AND_PRODUCTS_SPEC.md](../PROJECTS_AND_PRODUCTS_SPEC.md) §8 bleibt offen. M8
  erzeugt den Druck dafür (der Katalog geht aus), beantwortet ihn aber nicht.
- **Die Enden selbst.** Nr. 25 bleibt offen: Die Vollautomatisierung wird weiterhin an einem
  Zeitpunkt geprüft, wo die Spec eine Dauer verlangt. M8 verändert nur, mit welchem
  Alignment normales Spiel dort ankommt.
- **Ein Ende für „Katalog leer".** Wer alle elf Aufträge abgearbeitet hat, läuft in den
  Bankrott. Ob das ein eigenes Ende verdient, entscheidet der Produkt-Meilenstein.

## Testlage

315 Tests grün, `ruff check .` sauber.
`test_full_staffing_beats_every_partial_staffing` läuft seit M8 über die **Registry** statt
über eine handgepflegte Liste und deckt damit alle elf Baupläne ab — das ist der Test, der
die Untergrenzen aus Nr. 33 durchsetzt. Neu dazu: die Einmaligkeit, die Referenzkette, die
Reihenfolge des Katalogs und die Neutralität eines Attributs, das kein Projekt anfordert.
