# M4 — Druck von außen: Ereignisse

**Status:** ✅ Abgeschlossen
**Geplant:** 24. August 2026
**Abgeschlossen:** 24. August 2026

## Warum

Nach M3 ist das Spiel wirtschaftlich in sich schlüssig, aber **von außen passiert nichts**.
Die einzige Kraft, die den Spieler stört, ist er selbst: Er stellt zu teuer ein, er lässt
ein Projekt verwahrlosen, er erforscht die falsche Stufe. Drei Befunde aus M3 hängen alle
an derselben Lücke:

- **Es fehlt eine Geldsenke.** Der Spieler endet mit über 30.000 € und keiner einzigen
  knappen Runde ([BALANCING.md](../BALANCING.md), Simulation zu M3). Geld ist nie der
  Engpass, nur die Forscherzahl.
- **Ein Projekt, das bei Ablauf nie fertig wurde, hat keine Folgen.** Es verschwindet
  kommentarlos.
- **Der Twist hat keine Vorboten.** `docs/VISION.md` beschreibt eine Firma, die dem Spieler
  entgleitet — heute merkt er davon bis zum Kontrollverlust nichts außer einer sinkenden
  Zahl.

`GAME_DESIGN.md` und `VISION.md` beschreiben dafür seit dem ersten Entwurf **externe
Druckfaktoren** in vier Kategorien. Sie sind der letzte große Block der Spec, der noch
komplett fehlt — und der einzige, der alle drei Befunde mit einer Mechanik erreicht.

## Ziel

Ereignisse, die **erst freigeschaltet und dann zufällig ausgelöst** werden — der Wunsch,
mit dem dieser Meilenstein angestoßen wurde. Zwei Fragen, die bewusst getrennt bleiben:

1. **Ist das Ereignis überhaupt möglich?** Deterministisch aus dem Zustand ablesbar,
   genau wie `TechRegistry.is_available()`. Der Tech-Baum, die Zusammensetzung der
   Belegschaft und bisherige Entscheidungen schalten frei.
2. **Löst es diese Runde aus?** Ein Wurf über den freigeschalteten Pool mit dem
   abgeleiteten RNG aus `Game._turn_rng()`, damit Spielstände reproduzierbar bleiben.

Und sie sind **unausweichlich, aber beantwortbar**: Jedes Ereignis stellt den Spieler vor
eine Wahl, keins lässt sich ignorieren (`GAME_DESIGN.md`, „Externe Druckfaktoren").

## Die Mechanik

### 1. `core/events.py` — gebaut wie `core/tech.py`

Blueprint-Dataclass, Registry aus gebündeltem JSON, gecachter Loader. Und vor allem
dieselbe Kernregel:

> **Ereignisse tauchen nie im Engine-Code auf.**

`core/tech.py` faltet alles Erforschte zu einem `Modifiers`-Wertobjekt; `core/events.py`
faltet alles gerade Laufende zu einem `Pressure`-Wertobjekt. Der Rest der Engine fragt
dieses Objekt („wie hoch sind die Fixkosten gerade?"), statt Ereignis-IDs zu kennen. Ein
neues Ereignis, das ein bestehendes Feld benutzt, ist damit **reine Konfiguration**.

### 2. Freischaltung: deklarativer Bedingungs-Wortschatz

`requires` ist ein Objekt aus benannten Bedingungen, ausgewertet über eine Tabelle nach
dem Vorbild von `AGGREGATION` in `tech.py`. Eine neue Bedingungsart ist ein Tabelleneintrag,
ein neues Ereignis ist keiner.

| Schlüssel | Bedeutung |
|-----------|-----------|
| `min_turn`, `every_n_turns` | Zeitliche Taktung (Quartalsbericht, Miete) |
| `min_agents`, `min_humans`, `agents_outnumber_humans` | Form der Belegschaft |
| `min_agent_level` | Forschungsstand — gelesen aus **`Modifiers`, nie aus Technologie-IDs** |
| `min_projects` | Firmengröße |
| `min_alignment`, `max_alignment` | Zustand der KI |
| `min_money`, `max_money` | Liquidität |
| `max_last_net` | Die letzte Runde war schlechter als … (Investoren) |
| `after_event`, `not_after_event` | Ketten und Ausschlüsse (Drohung folgt auf Bericht) |

Alle Bedingungen eines Ereignisses müssen erfüllt sein (UND). Ein ODER wird als zwei
Ereignisse geschrieben — billiger als eine Ausdruckssprache in JSON.

### 3. Auslösung: ein Wurf, reproduzierbar

```
pool = [e für e in katalog wenn e.requires erfüllt und nicht (e.once und schon dagewesen)
        und cooldown abgelaufen]
für e in pool: wenn rng.random() < e.chance -> auslösen
```

Der RNG ist der Runden-RNG aus `Game._turn_rng()` — derselbe Spielstand ergibt dieselbe
Ereignisfolge, auch nach Speichern und Laden mittendrin. Ein `max_events_per_turn` in der
Tuning-Konfiguration deckelt, wie viel in einer Runde auf einmal einschlagen darf.

### 4. Entscheidungen: die Runde blockiert, bis geantwortet ist

Ein ausgelöstes Ereignis wirkt **nicht sofort**. Es legt eine `PendingDecision` in den
Zustand; erst die gewählte Option bringt Effekte mit.

- Neue Aktion `Game.answer_event(event_id, option_id) -> ActionResult`. Sie validiert,
  bevor sie mutiert, wie jede andere Aktion.
- `resolve_turn()` **scheitert**, solange eine Entscheidung offen ist, und lässt den
  Zustand unangetastet. Die Regel „unausweichlich" steht damit in `core`, nicht im Menü —
  die UI kann sie nicht umgehen und der spätere KI-Übernahme-Seam sieht sie.
- **Keine Option wird durch fehlendes Geld gesperrt.** Wer nicht zahlen kann, zahlt
  trotzdem und rutscht ins Minus — dort greift die bestehende Bankrott-Endbedingung. Eine
  gesperrte Option wäre eine Sackgasse ohne Ausweg.

Damit bekommt die Engine zum ersten Mal einen Zustand, der eine Spielerantwort *erwartet*.
Das ist der eigentliche Aufwand dieses Meilensteins — und zugleich die Vorarbeit für den
Twist: Genau an dieser Stelle wird die KI später Optionen vorauswählen, verstecken oder
eine Antwort behaupten, die der Spieler nie gegeben hat.

### 5. Wirkung: einmalig oder laufend

Dieselbe JSON-Form, `duration` entscheidet:

- **fehlt** → Sofort-Effekt (Auto kaputt: −300 €)
- **Zahl** → läuft n Runden (Rezession: Einnahmen −30 % für 3 Runden)
- **`null`** → dauerhaft (Miete, KI-Steuer)

| Effektfeld | Aggregation | wirkt auf |
|------------|-------------|-----------|
| `money`, `research`, `tokens`, `alignment` | einmalig | Sofortbuchung beim Auslösen |
| `income_multiplier` | multiplikativ | `_calculate_income` |
| `cost_multiplier` | multiplikativ | `_calculate_costs` |
| `fixed_cost` | additiv | `_calculate_costs` (Miete, Versicherung) |
| `cost_per_agent` | additiv | `_calculate_costs` (KI-Regulierung) |
| `alignment_per_round` | additiv | `_update_alignment` |

`Pressure` ist von `Modifiers` getrennt, auch wo die Felder gleich heißen: Forschung ist
etwas, das der Spieler besitzt, Druck etwas, das ihm zustößt. Der Rundenbericht muss beide
getrennt ausweisen können.

### 6. Platz in der Schrittfolge

`resolve_turn()` hat eine feste Schrittfolge, und wo die Ereignisse einsortiert werden,
entscheidet, ob sie noch die gerade gemeldete Runde beeinflussen. Zwei neue Schritte:

```
Servicegrad → Worker-Effekte → Nebeneffekte → Alignment → Einnahmen → Kosten →
Abrechnung → **Ereignisse auslösen** → **laufende Effekte altern** → Token-Preis →
Projekt-Lebenszyklus → Phase → Endbedingungen
```

**Laufender Druck wirkt sofort** (er wird von Einnahmen und Kosten gelesen, wie
`Modifiers` — kein eigener Schritt). **Neu ausgelöste Ereignisse wirken erst ab der
nächsten Runde**, ihre Sofortbuchungen stehen als eigene Zeile unter der Abrechnung.
Sonst stimmte die gemeldete Bilanz nicht mit dem gemeldeten Netto überein.

### 7. Lesbarkeit — die Bedingung, an der alles hängt

Alignment ist bewusst deterministisch, damit der Spieler die Bilanz **vor** der
Entscheidung lesen kann ([BALANCING.md](../BALANCING.md) Nr. 8). Ereignisse dürfen diese
Eigenschaft nicht durch die Hintertür kassieren:

- Jeder Effekt, der Geld, Alignment oder Einnahmen bewegt, erzeugt eine **eigene, benannte
  Zeile** im Rundenbericht. Es gibt keinen anonymen Posten.
- Das Dashboard zeigt ein Panel **„Laufende Ereignisse"** mit Restlaufzeit („Rezession —
  noch 2 Runden, Einnahmen −30 %"), damit laufender Druck vor dem Zug sichtbar ist und
  nicht erst in der Abrechnung.
- Was **noch nicht** eingetreten ist, bleibt verborgen. Freischaltung ist kein Versprechen.

## Die vier Kategorien

Alle vier aus der Spec, aber in aufsteigender Schwierigkeit umgesetzt — die Reihenfolge
unten ist auch die Baureihenfolge.

1. **KI-spezifisch** (KI-Hype, Ethik-Debatte, KI-Regulierung, KI-Skandal). Hängt an
   Agentenzahl, Agentenstufe und Alignment, braucht keine neuen Zustandsfelder und ist der
   natürliche Ort für die **Vorboten des Twists**.
2. **Markt & Wirtschaft** (Rezession, Konkurrenz, Steuererhöhung, Lieferkette). Reine
   temporäre Multiplikatoren — der Testfall für `duration`.
3. **Privater Druck** (Miete, Krankenversicherung, Auto, Urlaub, Baby). Dauerhafte
   Fixkosten, starker Ton, die härteste Geldsenke.
4. **Investoren** (Quartalsbericht, Drohung, Börsengang). Braucht als einzige Kategorie
   ein Gedächtnis über Runden hinweg: `GameState.last_net` und die Ereignisketten über
   `after_event`. Zuletzt, und notfalls auf den Quartalsbericht plus Drohung reduziert.

## Geldsenke — ja, aber nicht abschließend

M4 schließt den größten offenen Balancing-Punkt aus M3 **teilweise**: Miete,
Versicherung, Steuern und KI-Regulierung sind wiederkehrende Fixkosten, und sie wachsen
mit der Firma statt mit der Rundenzahl. Der Punkt „Geldsenke fehlt" bleibt trotzdem im
[README](./README.md) stehen, weil Ereignisse nur *eine* Antwort darauf sind — Produkte,
Büro-Ausbau, Agenten-Wartung und Investoren-Auszahlungen bleiben Kandidaten für später.

Die Zahlen werden **simuliert, nicht geraten**. Das ist die Lehre aus M3, wo die geschätzte
Verdreifachung der Technologiekosten sich als falsch erwies. Zielbild für die Kalibrierung:

- Mindestens eine **knappe Runde** in einer normal gespielten Partie, kein garantierter
  Bankrott.
- Fixkosten in der Größenordnung **eines Projekt-Nettoertrags** — wer wächst, zahlt mehr,
  aber Wachstum bleibt die richtige Antwort.
- Die reine Automatisierungsstrategie darf durch die KI-Steuer **teurer**, aber nicht
  unmöglich werden. Sie soll weiterhin in den Kontrollverlust führen, nicht in den
  Bankrott.

## Konfiguration

`src/automate_inc/data/events.json`, aufgebaut wie `technologies.json`, mit einem
`tuning`-Block obenauf (`max_events_per_turn`, globale Wahrscheinlichkeits-Skalierung,
Grund-Cooldown).

```json
{
  "id": "ai_regulation",
  "category": "AI",
  "name": "KI-Regulierung",
  "description": "Der Gesetzgeber hat von eurer Belegschaft gehört.",
  "requires": { "min_agents": 7 },
  "chance": 0.15,
  "once": true,
  "options": [
    {
      "id": "comply",
      "label": "Steuer zahlen",
      "effects": { "cost_per_agent": 10 },
      "duration": null
    },
    {
      "id": "lobby",
      "label": "Lobbyisten beauftragen (2.000 €)",
      "effects": { "money": -2000, "alignment": -5 }
    }
  ]
}
```

Der Katalog wird beim Laden validiert wie der Tech-Baum: unbekannte Effektfelder,
unbekannte Bedingungen und `after_event`-Verweise ins Leere sind ein Fehler beim Laden,
nicht ein stiller Aussetzer im Spiel.

**Alle deutschen Texte** — Name, Beschreibung, Optionslabels — stehen in `events.json`,
nicht in `strings.py`. Das ist die eine bewusste Abweichung von der Sprachkonvention: Sie
sind Katalogdaten wie Projekt- und Technologienamen, die auch schon dort stehen.
`strings.py` behält die Rahmentexte („📩 Neues Ereignis: {name}").

## Was das kostet

- **Save-Format 5**: `active_events`, `pending_decisions`, `event_history`, `last_net`.
- **`resolve_turn()` kann jetzt scheitern.** Bisher war der Rundenwechsel bedingungslos;
  künftig gibt es einen Zustand, in dem er abgelehnt wird. Das berührt `__main__.py` und
  jeden Test, der blind Runden durchdreht.
- **Die UI bekommt einen neuen Fluss**, der eine Antwort erzwingt — der erste, der nicht
  aus dem Hauptmenü kommt. `menu.end_turn()` fragt neue Entscheidungen direkt im Anschluss
  ab; ein geladener Spielstand mit offener Entscheidung fragt sie beim nächsten
  Rundenversuch ab.
- **Balancing muss neu geeicht werden**, sobald Fixkosten laufen — insbesondere die
  Technologiekosten, die in M3 genau deshalb *nicht* angefasst wurden.

## Reihenfolge

1. `core/events.py`: `Event`, `EventOption`, `EventRegistry`, `Pressure`, `aggregate` +
   Katalogvalidierung — mit Tests, ohne Anbindung
2. Bedingungs-Tabelle und `is_available()` gegen einen `EventContext` aus dem `GameState`
3. Zustand: `active_events`, `pending_decisions`, `event_history`, `last_net`,
   Save-Format 5
4. `resolve_turn()`: `_trigger_events()`, `_age_events()`, Blockade bei offener
   Entscheidung
5. `economy.py` liest `Pressure` bei Einnahmen, Kosten und Alignment
6. Aktion `answer_event()` + UI-Fluss + Dashboard-Panel „Laufende Ereignisse"
7. Katalog in vier Wellen: KI → Markt → Privat → Investoren
8. Simulation und Kalibrierung der Geldsenke
9. Doku: `BALANCING.md` Nr. 16 ff., dieses Dokument, README

## Ergebnis

Umgesetzt wie geplant, mit drei Abweichungen — Details in
[BALANCING.md](../BALANCING.md) Nr. 16–19:

- Effekte entstehen ausschließlich in `answer_event`, nie beim Auslösen (Nr. 16) —
  eine Klarstellung eines Widerspruchs zwischen Abschnitt 4 und 6 oben, keine
  Planänderung.
- `resolve_turn()` blockiert nur, während das Spiel noch läuft (Nr. 17) — sonst
  könnte eine `PendingDecision` aus der Runde, die das Spiel beendet, es für immer
  einfrieren.
- Der Katalog wurde auf 13 Ereignisse über alle vier Kategorien reduziert (Nr. 18) —
  von der Spec ausdrücklich für die Investoren-Kategorie erlaubt, hier auf alle vier
  angewendet, weil die Mechanik konfigurationsgetrieben ist.

Save-Format 5 wie geplant. `menu.end_turn()` beantwortet offene Entscheidungen vor
jedem Rundenversuch; das Dashboard zeigt laufenden Druck im Panel „Laufende
Ereignisse" mit Restlaufzeit. Die Geldsenke ist kalibriert und simuliert (Nr. 19),
nicht geraten — bewusst weiterhin nicht abschließend, siehe
[README](./README.md).

Die drei „Offenen Fragen" von oben: `max_events_per_turn: 1` beantwortet die zweite
(mehr als eine Entscheidung pro Runde wäre spielbar, aber ungetestet). Die erste
(Projekt läuft ohne Fertigstellung ab) bleibt offen, siehe README. Die dritte
(Ereignisse mit Ablaufdatum für die Antwort) bleibt bewusst außerhalb von M4.

## Testlage

`tests/test_events.py`, mit den Eigenschaften, an denen die Mechanik hängt:

- **Ein Ereignis mit unerfüllten Bedingungen löst nie aus** — über den ganzen Katalog
  parametrisiert.
- **Derselbe Seed ergibt dieselbe Ereignisfolge**, auch wenn mittendrin gespeichert und
  geladen wird.
- **Eine offene Entscheidung blockiert die Runde** und `resolve_turn()` lässt den Zustand
  byte-identisch — dieselbe Eigenschaft wie
  `test_failed_action_leaves_state_untouched`.
- **Laufende Effekte laufen nach `duration` Runden aus** und lassen keinen Rest zurück.
- **Jeder Effekt erzeugt eine benannte Zeile im Bericht** — parametrisiert über den
  Katalog. Das ist der Test gegen unerklärliches Rauschen in der Bilanz.
- **Jede Option ist wählbar**, auch bei 0 € (keine Sackgasse).
- Katalogvalidierung: unbekannte Effekte/Bedingungen fliegen beim Laden.

## Offene Fragen

- **Was passiert mit einem Projekt, das bei Ablauf nie fertig wurde?** Aus M3 übernommen.
  Ein Ereignis („Kunde klagt") wäre die naheliegende Antwort — aber es ist streng genommen
  eine Projektregel, kein externer Druck. Entscheidung beim Bauen der Kategorie „Markt".
- **Wie viele Entscheidungen pro Runde erträgt der Spielfluss?** `max_events_per_turn`
  fängt es ab, der Wert ist zu spielen, nicht zu setzen.
- **Ereignisse mit Ablaufdatum für die Antwort** (das Angebot gilt zwei Runden) sind
  bewusst nicht Teil von M4.

## Nicht Teil von M4

Produkte und Upgrades, HR-Rolle, weitere Geldsenken jenseits der Fixkosten, der Twist
selbst — und Ereignisse, die die KI *fälscht*. Der Seam dafür entsteht hier, benutzt wird
er später.
