# M5 — Büro-Ausbau und Investoren-Auszahlung

**Status:** ✅ Abgeschlossen
**Geplant:** 25. August 2026
**Abgeschlossen:** 25. August 2026

## Warum

`docs/milestones/README.md` führt seit M4 zwei offene Geldsenken-Kandidaten, die die
Fixkosten-Ereignisse bewusst nicht abgedeckt haben: **Büro-Ausbau** und
**Investoren-Auszahlungen**. Beide haben denselben Charakter, den `BALANCING.md` 19 schon
für M4 beschrieben hat — eine Grenze, die mitwächst, statt einer Pauschale, die alles
gleich teuer macht:

- **Büro-Ausbau** begrenzt, wie viele Menschen das Team gleichzeitig hat — nicht wie viele
  Agenten. Das ist der Punkt: ein physisches Büro braucht Schreibtische, ein Agent nicht.
  Wer wächst, muss entweder zahlen oder automatisieren — und automatisieren ist genau die
  Entscheidung, die den Spieler laut `VISION.md` am Ende ersetzt.
- **Investoren-Auszahlung** war bisher nur der `give_equity`-Ausweg in `investor_threat`:
  einmalig 3.000 € für −10 Alignment, ohne Folgekosten — eine Option ohne echten
  Kompromiss. Jetzt kostet jede Finanzierungsrunde dauerhaft einen Anteil vom Einkommen,
  und der Spieler kann sie auch **freiwillig** ziehen, nicht nur unter Ereignis-Druck.

Beide Mechaniken sind bewusst kleiner geschnitten als M4: keine neue Katalog-Kategorie,
keine Entscheidungs-Blockade, sondern je eine neue Spieler-Aktion plus ein bestehender
Ereignis-Ausweg, der jetzt Konsequenzen hat.

## Büro-Ausbau

- `GameState.office_capacity` (Start: 3) deckelt **nur menschliche** `hire_worker`-Aufrufe.
  Drei Stellen ist genau die Größe, die die minimal besetzte Web-App-Strategie aus
  `BALANCING.md` 19 ohnehin braucht — die Basisstrategie wird durch den Deckel nicht
  berührt, erst der Wunsch nach einem zweiten Team.
- Neue Aktion `Game.expand_office()`: hebt die Kapazität um 2, Kosten steigen geometrisch
  mit jeder Erweiterung (600 € · 1,5ⁿ). Reines Geld, keine Forschung — das ist eine
  Kapazitätsentscheidung, kein Tech-Tree-Eintrag.
- Agenten sind vom Deckel ausgenommen. Wer die Grenze nicht bezahlen will, stellt Agenten
  ein — und das ist die Ironie, die dieser Meilenstein einbaut: das Büro wird eng, die
  Automatisierung nicht.

## Investoren-Auszahlung

- `GameState.investor_equity` (0–40 %, Schritt 8 pro Runde) senkt `_calculate_income`
  dauerhaft um genau diesen Anteil — mit einer eigenen benannten Zeile im Rundenbericht
  („Investoren-Anteil: −X €"), wie es die Regel „nichts Unerklärtes in der Bilanz" verlangt.
- Neue Aktion `Game.raise_funding()`: 1.200 € sofort gegen 8 Prozentpunkte, bis zum Deckel
  von 40 %. Freiwillig, jederzeit außer am Deckel.
- `investor_threat`s `give_equity`-Option bekommt denselben Effekt zum schlechteren Kurs
  (1.500 € für dieselben 8 Punkte plus −10 Alignment) — unter Druck verhandelt man
  schlechter als freiwillig.

## Was das kostet

- **Save-Format 6**: `office_capacity`, `investor_equity`.
- Neuer Instant-Effekt `equity` in `core/events.py` (`INSTANT_FIELDS`), verarbeitet in
  `Game._apply_event_option` wie `alignment`.
- `_calculate_income` bekommt eine eigene Zeile im `TurnReport` (`investor_payout`) statt
  den Abzug still in `income` zu verstecken.
- UI: Team-Panel zeigt die Bürokapazität, Dashboard-Kopf den Investorenanteil, Menü bekommt
  zwei neue Einträge.

## Nicht Teil von M5

Agenten-Wartung (eigener, noch kleinerer Meilenstein), das komplette
Produkt-/Upgrade-System aus `PROJECTS_AND_PRODUCTS_SPEC.md`, ein Hostile-Takeover-Ende bei
hohem Investorenanteil — der Anteil bleibt eine Zahl, die das Einkommen drückt, keine neue
Endbedingung.

## Ergebnis

Umgesetzt wie geplant. Save-Format 6 wie vorgesehen (`office_capacity`,
`investor_equity`). Eine Abweichung von oben: `give_equity` wurde nicht nur teurer,
sondern nutzt jetzt denselben `equity`-Instant-Effekt wie `raise_funding` — ein neuer
Eintrag in `events.INSTANT_FIELDS`, verarbeitet in `Game._apply_event_option` genau wie
`alignment`. Das war schon in Abschnitt „Investoren-Auszahlung" oben so vorgesehen, hier
nur konkretisiert.

Kalibrierung siehe [BALANCING.md](../BALANCING.md) Nr. 20 — gegen bestehende Tabellen
abgeglichen statt neu simuliert, weil beide Mechaniken optional sind und den kalibrierten
Grundlauf aus Nr. 19 nicht berühren, solange niemand sie zieht.

## Testlage

`tests/test_office_and_investors.py`, plus eine Ergänzung in `tests/test_events.py`:

- Ein vierter Mensch wird abgelehnt, solange die Bürokapazität nicht erweitert ist; ein
  Agent ist davon nie betroffen.
- `expand_office` hebt die Kapazität um den festen Schritt und wird mit jeder Erweiterung
  teurer (`OFFICE_EXPANSION_GROWTH`).
- `raise_funding` bucht Geld und Anteil sofort, ist am Deckel gesperrt und überschreitet
  ihn nie, auch nicht bei einem Aufruf knapp darunter.
- Der Investorenanteil zieht in `resolve_turn()` exakt `income * equity / 100` ab, erzeugt
  eine benannte Zeile im Bericht und bleibt bei 0 % stumm.
- `give_equity` in `investor_threat` erhöht `investor_equity` genauso wie `raise_funding`.
- Beide neuen Aktionen sind Teil der bestehenden Matrix-Tests: verweigert, sobald das
  Spiel vorbei ist; lässt den Zustand bei einer fehlgeschlagenen Ausführung unangetastet.
