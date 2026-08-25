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

- `GameState.investor_equity` (0–40 %, Schritt 8 pro Runde) senkt den **Nettogewinn** der
  Runde dauerhaft um genau diesen Anteil — mit einer eigenen benannten Zeile im
  Rundenbericht („Investoren-Anteil: −X €"), wie es die Regel „nichts Unerklärtes in der
  Bilanz" verlangt. Bewusst Nettogewinn statt Umsatz — siehe Nachtrag unten, das war
  ursprünglich anders und ist der Grund für den Nachtrag.
- Neue Aktion `Game.raise_funding()`: 1.200 € sofort gegen 8 Prozentpunkte, bis zum Deckel
  von 40 %. Freiwillig, jederzeit außer am Deckel.
- `investor_threat`s `give_equity`-Option bekommt denselben Effekt zum schlechteren Kurs
  (1.500 € für dieselben 8 Punkte plus −10 Alignment) — unter Druck verhandelt man
  schlechter als freiwillig.

## Nachtrag: Startanteil und `dividend_call` (noch am 25. August, gleicher Tag)

Zwei Ergänzungen, direkt aus der Reaktion auf die erste Version: Das Startkapital ist
Investorengeld, kein Erspartes — der Spieler startet nicht bei 0 %, sondern bei **15 %**
Investorenanteil (`START_INVESTOR_EQUITY`). Und ein neues Ereignis `dividend_call`
(Kategorie INVESTOR, alle 4 Runden ab Runde 6, nur wenn `investor_equity > 0`) macht den
laufenden Abzug zu einer wiederkehrenden Entscheidung statt nur einer stillen Zeile:
zahlen (400 €) oder vertrösten (+5 Punkte, −6 Alignment).

Der Startanteil deckt genau den blinden Fleck der ersten Version auf: Bis hierhin waren
Büro-Ausbau und `raise_funding` **optional**, ein Startwert > 0 % gilt dagegen für **jede**
Partie. Das legte offen, dass `_pay_investors` den Anteil vom Bruttoeinkommen statt vom
Nettogewinn abgezogen hatte — was zwei der vier `test_full_staffing_beats_every_partial_staffing`-Fälle
brach, die CLAUDE.md als tragende Eigenschaft markiert. Details und die Kalibrierung des
15-%-Startwerts stehen in [BALANCING.md](../BALANCING.md) Nr. 21.

## Was das kostet

- **Save-Format 6**: `office_capacity`, `investor_equity` (jetzt mit Startwert > 0).
- Neuer Instant-Effekt `equity` in `core/events.py` (`INSTANT_FIELDS`), verarbeitet in
  `Game._apply_event_option` wie `alignment`.
- Neue Bedingung `min_investor_equity` in `CONDITION_CHECKS`, `EventContext` trägt jetzt
  `investor_equity` — nötig, damit `dividend_call` überhaupt lesen kann, ob es was zu
  fordern gibt.
- `_pay_investors` bekommt eine eigene Zeile im `TurnReport` (`investor_payout`) statt den
  Abzug still in `income` zu verstecken — und rechnet auf Nettogewinn, nicht auf Umsatz
  (siehe Nachtrag).
- UI: Team-Panel zeigt die Bürokapazität, Dashboard-Kopf den Investorenanteil ab Runde 0,
  Menü bekommt zwei neue Einträge.

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

Kalibrierung siehe [BALANCING.md](../BALANCING.md) Nr. 20 (Büro, `raise_funding`) und
Nr. 21 (Startanteil, Nettogewinn-Korrektur, `dividend_call`).

## Testlage

`tests/test_office_and_investors.py`, plus Ergänzungen in `tests/test_events.py`:

- Ein vierter Mensch wird abgelehnt, solange die Bürokapazität nicht erweitert ist; ein
  Agent ist davon nie betroffen.
- `expand_office` hebt die Kapazität um den festen Schritt und wird mit jeder Erweiterung
  teurer (`OFFICE_EXPANSION_GROWTH`).
- `raise_funding` bucht Geld und Anteil sofort, ist am Deckel gesperrt und überschreitet
  ihn nie, auch nicht bei einem Aufruf knapp darunter.
- Ein frischer Spielstand startet bereits bei `START_INVESTOR_EQUITY`, nicht bei 0.
- Der Investorenanteil zieht in `resolve_turn()` exakt `(income - costs_money) * equity /
  100` ab, erzeugt eine benannte Zeile im Bericht, bleibt bei 0 % stumm und zahlt nichts in
  einer Verlustrunde.
- `give_equity` in `investor_threat` erhöht `investor_equity` genauso wie `raise_funding`.
- `dividend_call` ist nur mit `investor_equity > 0` verfügbar; „Vertrösten" erhöht Anteil
  und senkt Alignment wie im Katalog angegeben.
- Beide neuen Aktionen sind Teil der bestehenden Matrix-Tests: verweigert, sobald das
  Spiel vorbei ist; lässt den Zustand bei einer fehlgeschlagenen Ausführung unangetastet.
- `tests/test_service_level.py::test_full_staffing_beats_every_partial_staffing` bleibt
  über alle vier Projekttypen grün — das war der Regressionstest, der die
  Umsatz-statt-Nettogewinn-Abweichung im Nachtrag überhaupt aufgedeckt hat.
