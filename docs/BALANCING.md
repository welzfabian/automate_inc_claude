# Balancing-Entscheidungen

> Dieses Dokument hält fest, wo die Implementierung bewusst von
> [GAME_DESIGN.md](./GAME_DESIGN.md) und
> [PROJECTS_AND_PRODUCTS_SPEC.md](./PROJECTS_AND_PRODUCTS_SPEC.md) abweicht — und warum.
> Maßgeblich für das laufende Spiel sind immer die Dateien unter
> `src/automate_inc/data/`.

## 1. Menschen erfüllen die Stufe-2-Anforderung

GAME_DESIGN.md 3.2 verlangt für jeden Projektstart „mindestens 1 Worker der Stufe 2+".
Agenten-Stufe 2 erfordert Forschung, Forschung erfordert Research Points, die ein
bezahlter Forscher erwirtschaftet — wofür Einnahmen aus einem Projekt nötig wären. In
Runde 0 wäre damit keine Aktion möglich.

**Auflösung:** Der Klammerzusatz derselben Zeile („Agent ODER **Mensch mit Erfahrung**")
wird wörtlich genommen — `Worker.effective_level` ist für Menschen immer 2.

**Spielerische Folge:** Wer alle Menschen entlässt, kann keine neuen Projekte mehr
starten. Laufende Projekte laufen weiter. Die Automatisierung schließt also die Tür
hinter sich zu — genau die Kurve, die VISION.md beschreibt.

## 2. Nicht angeforderte Attribute sind neutral

Die Einnahmenformel (SPEC 6.1) multipliziert mit `aesthetics/100`. Eine „Statische
Website" braucht laut Spec nur einen Entwickler, hat also nie Ästhetik → Einnahmen
dauerhaft 0 €.

**Auflösung:** Attribute, die ein Projekt gar nicht anfordert, zählen als Faktor 1.0.
Projekte starten außerdem mit `quality = 50`, `aesthetics = 50`, `bugs = 0` statt bei 0,
damit sie ab der ersten Runde etwas einbringen. Alle Attribute sind auf 0–100 geklemmt.

> **Revidiert in M3.** Die Startwerte 50 bleiben, aber die Begründung war nur die halbe
> Wahrheit: Sie mussten in M1 zwei Fragen gleichzeitig beantworten — *wie gut ist das
> Ding* und *existiert es überhaupt schon*. Die zweite Frage beantwortet seit M3
> `Project.service_level`. Deshalb war ein unbesetztes Projekt in M1 und M2 die profitabelste
> Besetzung überhaupt (siehe Nr. 11).

## 3. Tokens sind kaufbar

Agenten kosten Tokens pro Runde, der Startvorrat ist 50, ein Nachkaufweg fehlte in den
Docs.

**Auflösung:** Aktion „Tokens kaufen" zum Tagespreis. Reicht der Vorrat bei der
Rundenabrechnung nicht, wird die Differenz automatisch nachgekauft und in Rechnung
gestellt — Agenten hören nicht auf zu arbeiten, nur weil das Guthaben leer ist.
Erst damit wird der schwankende Token-Preis zu einer Entscheidung.

## 4. Eine Quelle der Wahrheit für Projektdaten

Die Projekt-Tabelle in GAME_DESIGN.md 3.2 hatte mehr Spaltenüberschriften als
Datenspalten. SPEC 3.2 gilt als Referenz; die Tabelle in GAME_DESIGN.md wurde
entsprechend korrigiert.

## 5. Projekteinnahmen angehoben, Agentenkosten gesenkt

Mit den ursprünglichen Zahlen ist **jede** Besetzung defizitär: Eine „Statische Website"
bringt 50 €/Runde, der dafür nötige Entwickler kostet 80 €/Runde. Dasselbe gilt für
alle anderen Projekttypen. Damit hätte das Spiel keinen spielbaren Zustand.

**Zielvorgabe** aus VISION.md („Notizen & Ideen"): *Menschen machen kleinen Gewinn
(≈ +20 €/Runde), Agenten machen großen Gewinn.*

**Auflösung:**
- `base_income` je Projekt so gesetzt, dass ein voll besetztes **menschliches** Team
  bei maximaler Qualität ≈ +20 €/Runde übrig behält.
- Agenten-Tokenkosten aus der Worker-Tabelle in GAME_DESIGN.md 2 übernommen
  (2–3 Tokens/Runde für Stufe 1) statt aus dem Rechenbeispiel in SPEC 6.2 (5 Tokens).

**Ergebnis im eingeschwungenen Zustand** (Gewinn pro Runde, Token-Preis 10 €):

| Projekt | Menschliches Team | Agenten-Team |
|---------|------------------:|-------------:|
| Statische Website | +20 € | +70 € |
| E-Commerce-Shop | +20 € | +120 € |
| Kunden-App | +22 € | +166 € |
| Web-App mit Backend | +20 € | +170 € |

Der Faktor 5–8 zwischen Mensch und Agent ist Absicht: Die Entscheidung für Agenten muss
sich *offensichtlich lohnen*, damit der Twist später greift.

## 6. Unbesetzte Worker kosten trotzdem

Nicht in den Docs geregelt. Im Spiel läuft die Gehaltsabrechnung weiter, auch wenn
jemand keinem Projekt zugewiesen ist — sonst wäre Personalaufbau auf Vorrat gratis.

---

# Meilenstein 2

## 7. Alignment-Verfall hängt an der Stufe, nicht an der Rolle

Die Worker-Attribut-Tabelle (GAME_DESIGN.md 2) gibt jedem Agenten der Stufe 2
`−1 Alignment/Runde` und Stufe 3 `−3/Runde`. Die Rollen-Tabelle (GAME_DESIGN.md 1) gibt
dem **Forscher**-Agenten nochmals dieselben Werte. Wörtlich gelesen würde ein
Forscher-Agent doppelt bestraft.

**Auflösung:** Der Verfall hängt **allein an der Stufe**. Die Forscher-Zeile ist eine
Wiederholung derselben Regel, kein zusätzlicher Effekt. Die Werte stehen als
`AGENT_ALIGNMENT_DECAY` in `core/economy.py`; ein Test (`test_the_researcher_role_gets_no_extra_decay`)
hält die Regel fest.

## 8. Kein zufälliger Basis-Verfall

VISION.md nennt einen Basis-Verfall von „−1 bis −10 pro Runde (zufällig)". Zusammen mit
dem Stufen-Verfall wäre Alignment binnen weniger Runden unter 20 — und der Spieler
könnte Ursache und Wirkung nicht mehr verknüpfen. Das widerspricht dem erklärten
psychologischen Ziel („der Spieler *glaubt*, er habe Einfluss"): Für diesen Glauben muss
die Mechanik lesbar sein.

**Auflösung:** **Kein zufälliger Basis-Verfall.** Die Alignment-Bilanz ist vollständig
deterministisch und ergibt sich aus Agenten (nach Stufe), Menschen und erforschter
Technologie. Sie steht als `(±n/Runde)` im Dashboard neben dem Alignment-Wert, damit sie
vor der Entscheidung sichtbar ist und nicht erst danach.

## 9. Menschen geben +1 Alignment, nicht +5

„+5 Alignment global pro Mensch" (GAME_DESIGN.md 2) wörtlich genommen: Zwei Menschen
gleichen drei Agenten der Stufe 3 vollständig aus. Automatisierung hätte keinen Preis.

**Auflösung:** **+1 pro Mensch und Runde**, gedeckelt bei 100. Menschen bremsen den
Verfall spürbar, halten ihn aber nicht auf.

## 10. „KI-Alignment" dämpft den Verfall, statt ihn zu überkompensieren

Ursprünglich als flache `+2 Alignment/Runde` geplant. In der Simulation war das
wirkungslos: Der Verfall wächst mit der Anzahl der Agenten, ein flacher Bonus nicht. Bei
neun Agenten der Stufe 2 stehen −9/Runde gegen +2 — die Technologie, die laut VISION.md
gerade die Abhängigkeit vertiefen soll, war schlicht kein Angebot.

**Auflösung:** `ai_alignment` **halbiert den Verfall aus Agenten**
(`alignment_decay_multiplier: 0.5`) statt einen festen Betrag zu addieren. Damit skaliert
sie mit der Flottengröße und wird zur echten Alternative zu „mehr Menschen einstellen" —
und erfüllt ihren erzählerischen Zweck: Sie löst das Problem, indem sie das Weiterskalieren
erlaubt.

Der Dämpfer wirkt **nicht** auf die gefährlichen Technologien (`autonomous_agents`,
`ai_consciousness`). Deren Alignment-Kosten sind strukturell, kein Nebeneffekt von
Personalstärke.

## Was die Simulation zu M2 zeigt

Über 45 Runden, gleicher Seed, drei Strategien:

| Strategie | Ausgang |
|-----------|---------|
| Vollautomatisierung, Stufe 3, keine Gegenmaßnahme | Kontrollverlust ~Runde 15 |
| Stufe 2 + „KI-Alignment" + „Bug-Fixing" | Kontrollverlust ~Runde 24 |
| Menschen entwickeln, Agenten der **Stufe 1** gestalten und forschen | läuft dauerhaft, ⚖ 100 |

Das ist die beabsichtigte Kurve: Agenten der Stufe 1 sind alignment-neutral und bleiben
ein tragfähiges Dauerangebot; die Stufen 2 und 3 lohnen sich sofort sichtbar und kosten
erst mit Verzögerung. Das Misalignment-Ende ist **erreichbar, ohne unausweichlich zu
sein** — genau die Bedingung aus dem M2-Plan.

---

# Meilenstein 3

## 11. Ein unbesetztes Projekt bringt nichts mehr — `Project.service_level`

**Der Fehler:** In M1 und M2 war ein Projekt, an dem niemand arbeitet, die profitabelste
Besetzung. Es brachte Einnahmen (Qualität und Ästhetik starten bei 50) und kostete kein
Gehalt. Gemessen: einen Menschen einstellen, vier Web-Apps starten, niemanden zuweisen,
zwanzig Runden nichts tun — **+110 €/Runde, dauerhaft, bei Alignment 100.**

Das unterläuft die Prämisse des Spiels: Wenn Nichtstun profitabel ist, gibt es keinen
Grund zu automatisieren.

**Auflösung:** Ein Attribut `service_level` (0–100) skaliert die Einnahmen. Startwert 25
(„Briefing und Vertrag stehen"). Besetzte Projekte kommen voran, im Verhältnis der
besetzten zu den geforderten Stellen und gewichtet mit der Effizienz; **komplett**
unbesetzte fallen zurück. Dieselbe Partie ergibt jetzt −160 €/Runde und Bankrott in
Runde 9.

**Warum der Wert „Servicegrad" heißt:** Er fällt. Ein Fortschritt, der zurückgeht, ist
keiner, und bei 100 % behauptet jedes Bau-Wort ein „fertig", das es hier nicht gibt —
100 % ist eine Obergrenze, die das Team hält, kein Endzustand. Der Wert beantwortet, was
der Kunde gerade bekommt, und genau das steht in der Einnahmenformel.

**Warum der Verfall nicht anteilig ist:** Erwogen und verworfen. Bei drei Stellen und
einer Besetzung ergäbe „34 × ⅓ − 15 × ⅔" **+1,3 pro Runde** — das Projekt bliebe bei 54 %
stehen und käme nie auf volle Leistung. Eine Falle, die der Spieler vorher nicht ablesen kann, also
derselbe Einwand wie bei Nr. 8. Teilbesetzung wird stattdessen über den Deckel bestraft
(Nr. 12).

## 12. Attribut-Deckel statt freier Attribute

**Der Fehler:** Ein Entwickler bringt +20 Qualität, eine unbesetzte Stelle kostete nichts.
Sobald **eine** Stelle einer Rolle besetzt war, waren alle weiteren wertlos: Bei der
Web-App (zwei Entwicklerstellen) brachte „ein Entwickler + Designer" +144 €/Runde gegen
+72 € bei voller Besetzung. Dieselbe Struktur wie bei der Sales-Stelle (Nr. 13).

**Auflösung:** Die Besetzung bestimmt, wie hoch ein Attribut überhaupt steigen kann:

```
Deckel = 50 + 50 × besetzte Stellen dieser Rolle / geforderte Stellen
```

Unbesetzt heißt eingefroren bei 50, halb besetzt bis 75, voll besetzt bis 100. Liegt der
Wert über dem Deckel, sinkt er mit 5 pro unbesetzter Stelle und Runde darauf zu. Welche
Rolle welches Attribut deckelt, steht in `roles.json` (`effect.attribute`).

**Warum die Basis genau 50 ist:** Ein Attribut kann nur sinken, wenn niemand die Rolle
besetzt — steigen kann es nur durch Worker dieser Rolle. Eine Basis über dem Startwert 50
wäre deshalb wirkungslos, und ab 60 schlägt Teilbesetzung wieder die volle Besetzung. Der
nutzbare Bereich ist 0–50; 50 ist das Maximum und damit die mildeste Einstellung, bei der
volle Besetzung noch immer und überall gewinnt (durch einen Test über alle Projekte und
alle Teilbesetzungen abgesichert).

**Drei Teilbesetzungen bleiben Verlustgeschäfte**: nur Sales; Entwickler plus Sales ohne
Designer; zwei Entwickler statt des fehlenden Designers. Alle drei sind „Gehalt für eine
blockierte Aufstellung", in der Oberfläche ablesbar (`75/75`) und mit einer Aktion
behebbar. Bewusst so gelassen — jede Gegenmaßnahme kippt das Verhältnis zur vollen
Besetzung.

## 13. Sichtbarkeitsbonus 10 % → 25 %

**Der Fehler:** Ein Sales-Mensch kostet 60 €/Runde und brachte +10 % Sichtbarkeit — bei
der Kunden-App rund 24 €. Die Stelle **leer zu lassen war besser, als sie zu besetzen.**
Die `+22 €` in der Tabelle unter Nr. 5 sind damit nicht das Optimum einer Kunden-App,
sondern eine Fehlbesetzung.

**Auflösung:** 25 %. Damit lohnt sich die Stelle knapp (+72 gegen +70 €/Runde ohne sie) —
eine Entscheidung statt einer Selbstverständlichkeit. Der Wert steht in `projects.json`
unter `tuning`, nicht mehr als Konstante in `economy.py`.

## 14. Projektgröße bestimmt Ertrag und Laufzeit

**Der Fehler:** Jedes Projekt brachte mit menschlichem Team +20 €/Runde — die statische
Website wie die Web-App. Die Projektwahl war mechanisch bedeutungslos. Dazu liefen große
Projekte **kürzer** als kleine (Web-App 12 Runden, statische Website 20), also genau
invertiert.

**Auflösung:** Zielgröße **+20 €/Runde pro geforderter Stelle, plus 10 % Bonus je
zusätzlicher Stelle**; Laufzeit nach Größe.

| Projekt | Stellen | Laufzeit | `base_income` | Ø netto | über die Laufzeit |
|---------|--------:|---------:|--------------:|--------:|------------------:|
| Statische Website | 1 | 20 → **10** | 100 → **108** | +20 € | +199 € |
| E-Commerce-Shop | 2 | 15 → **16** | 170 → **208** | +44 € | +697 € |
| Kunden-App | 3 | 15 → **22** | 220 → **246** | +72 € | +1.573 € |
| Web-App mit Backend | 3 | 12 → **22** | 270 → **337** | +72 € | +1.580 € |

Ein Projekt ist damit eine **Investition**: Break-even in Runde 3–4, davor kostet es.

Kunden-App und Web-App haben beide drei Stellen und sind dadurch wirtschaftlich fast
identisch — die Zielgröße hängt nur an der Stellenzahl. Eine der beiden braucht künftig
eine vierte Stelle oder eine andere Laufzeit.

## 15. Phasen aus dem Zustand statt aus der Rundenzahl

**Nicht in den Docs geregelt.** `Phase.for_turn()` schaltete nach 5 und 10 Runden um, ohne
Bezug zu irgendetwas, das der Spieler getan hatte.

**Auflösung:** Die Phase wird aus dem Zustand abgeleitet — Skalierung ab
`unlocked_agent_level ≥ 2` oder drei Agenten, Autonomie ab `unlocked_agent_level ≥ 3`,
sechs Agenten in der Überzahl oder Alignment unter 50. Die Bedingungen fragen
**`Modifiers`, nie Technologie-IDs**; sonst bräche die Regel, dass Technologien nicht im
Engine-Code auftauchen.

Die Phase wird bei jedem Zugriff neu berechnet und **darf zurückfallen**: Wer seine
Agenten entlässt, ist wieder im Aufbau. Weil sie sich damit beim Einstellen ändert und
nicht beim Rundenende, merkt sich `GameState.phase_announced`, was zuletzt gemeldet wurde
— sonst gäbe es nie wieder eine Phasenmeldung.

## Was die Simulation zu M3 zeigt

Über 60 Runden, ein Spieler, der zügig automatisiert und den ganzen Baum erforscht:

| Strategie | Ausgang |
|-----------|---------|
| reine Automatisierung, 6 Forscher | Kontrollverlust Runde 52, Baum 8/8 erforscht |
| dieselbe Strategie, mit 10 Menschen gegengesteuert | **Bankrott Runde 25** |

Beides ist beabsichtigt: Automatisierung führt weiterhin in den Kontrollverlust, aber
Menschen sind teuer genug, dass Übersteuern die Firma umbringt.

**Offener Befund:** Geld ist in keiner Simulation der Engpass — der Spieler endet mit über
30.000 € und keiner einzigen knappen Runde. Die Technologiekosten wurden deshalb
**nicht** erhöht (die Vermutung „das Dreifache" aus dem M3-Plan war falsch: schon bei den
bestehenden Kosten liegt Stufe 2 bei Runde 7–10 und Stufe 3 bei Runde 17–23, begrenzt
durch die Forscherzahl, nicht durch das Budget). Was fehlt, ist eine **Geldsenke** —
ein Thema für einen späteren Meilenstein, nicht für aufgeblähte Forschungskosten.

---

# Meilenstein 4

## 16. Effekte wirken erst mit der Antwort, nicht mit dem Auslösen

[`M4_EVENTS.md`](./milestones/M4_EVENTS.md) Abschnitt 6 liest sich so, als bekäme ein
ausgelöstes Ereignis seine Sofortbuchung schon in der Runde, in der es auftaucht, unter
„Abrechnung". Das widerspricht dem, was zwei Absätze vorher steht: „Ein ausgelöstes
Ereignis wirkt **nicht sofort**. [...] erst die gewählte Option bringt Effekte mit."

**Auflösung:** Die zweite Aussage ist maßgeblich. `Game._trigger_events` legt nur eine
`PendingDecision` an; jeder Effekt — ob Sofortbuchung oder laufender Druck — entsteht
ausschließlich in `Game.answer_event`. Die Sofortbuchung erscheint dafür in der
`ActionResult`-Meldung der Antwort, nicht als eigene Zeile im nächsten `TurnReport`. Das
hält die Regel „unausweichlich, aber beantwortbar" strikt ein: Wäre die Wirkung an das
Auslösen gekoppelt, könnte ein Ereignis Geld oder Alignment kosten, bevor der Spieler
überhaupt gefragt wurde.

## 17. `resolve_turn()` blockiert nicht mehr, sobald das Spiel vorbei ist

Ein Ereignis kann in genau der Runde auslösen, die das Spiel beendet (Bankrott oder
Kontrollverlust, geprüft nach `_trigger_events`). Ohne Sonderregel bliebe die entstandene
`PendingDecision` für immer offen: `answer_event` verweigert sich wie jede andere Aktion,
sobald `state.is_over` gilt (`ERR_GAME_OVER`), und `resolve_turn()` blockiert wiederum,
solange eine Entscheidung offen ist — ein Deadlock ohne Ausweg.

**Auflösung:** Die Blockade in `resolve_turn()` gilt nur, während das Spiel noch läuft
(`pending_decisions and not state.is_over`). Das ist auch der Grund, warum
`resolve_turn()` schon vor M4 keinen `is_over`-Wächter hatte: Es lief absichtlich über das
Spielende hinaus weiter (siehe `tests/test_turn.py`, `run_solvent`), und diese Eigenschaft
bleibt erhalten, statt durch die Ereignis-Blockade zufällig auszufallen.

## 18. Der Katalog ist bewusst auf 13 Ereignisse reduziert

`M4_EVENTS.md` nennt für die Investoren-Kategorie ausdrücklich die Option, sie „notfalls
auf den Quartalsbericht plus Drohung" zu reduzieren. Diese Erlaubnis wurde für alle vier
Kategorien genutzt: KI-Hype, Ethik-Debatte, KI-Regulierung, KI-Skandal · Rezession,
Konkurrenz, Steuererhöhung, Lieferkette · Miete, Krankenversicherung, Auto kaputt ·
Quartalsbericht, Investoren-Drohung. Urlaub, Baby und Börsengang aus der Spec-Liste fehlen.

**Grund:** `AGGREGATION`-artige Tabellen (hier: die Bedingungs- und Effekt-Tabellen in
`core/events.py`) sind darauf ausgelegt, dass ein neues Ereignis reine Konfiguration ist.
Die Mechanik selbst — Freischaltung, Wurf, Entscheidung, laufender vs. einmaliger Effekt,
Alterung — ist mit 13 Ereignissen über alle vier Kategorien und jede Bedingungs- und
Effektart hinweg getestet (`tests/test_events.py`). Weitere Ereignisse sind danach ein
Eintrag in `data/events.json`, kein Grund, den Meilenstein offen zu halten.

> **Inzwischen sind es 15** — die Behauptung von oben hat sich damit selbst bestätigt.
> `dividend_call` kam mit M5 dazu (Nr. 21), `full_automation_warning` mit M7 (Nr. 23), beide
> als reiner JSON-Eintrag ohne Code-Änderung. Die Überschrift bleibt als Chronik stehen:
> 13 war der Stand bei M4.

## 19. Was die Simulation zu M4 zeigt

Dieselbe Idee wie bei M2/M3, aber gegen den Ereigniskatalog statt gegen die Technologie:
ein minimal besetztes Team an genau einer Web-App (BALANCING.md 14), 60 Runden,
Entscheidungen nach einer einfachen, nicht optimierenden Regel beantwortet („nimm die
günstigste sofort bezahlbare Option, sonst die erste"). Elf Seeds für das reine
Menschen-Team:

| Ergebnis | Seeds | Anteil |
|----------|------:|-------:|
| Überlebt 60 Runden | 6 von 11 | 55 % |
| Bankrott | 5 von 11 | 45 % |

Unter den überlebenden Läufen lag der Tiefststand zwischen 132 € und 414 € — echte knappe
Runden, kein Puffer von 30.000 € mehr. Das ist die beabsichtigte Wirkung: Ein
Ein-Projekt-Team mit ohnehin nur ≈ +20 €/Runde Nettoertrag (BALANCING.md 5) trägt jetzt
ein reales Bankrottrisiko, ohne dass jede Partie zwangsläufig verloren geht.

Automatisierung (Stufe-3-Agenten, „KI-Alignment" erforscht, sonst identisches Setup, sechs
Seeds) bleibt überwiegend bei der beabsichtigten Endbedingung: fünf von sechs Läufen enden
im Kontrollverlust (Runde 15–18) bei komfortablem Kontostand (Tiefststand 594–744 €), ein
Lauf endet in dieser Stichprobe im Bankrott. Die Zielvorgabe aus `M4_EVENTS.md` — die reine
Automatisierungsstrategie „soll weiterhin in den Kontrollverlust führen, nicht in den
Bankrott" — gilt damit als Regelfall, nicht als Garantie; ein einzelnes Ereignis kann eine
ansonsten stabile Automatisierung in einer schlecht getroffenen Runde trotzdem umbringen.
Das ist als Eigenschaft von Ereignissen hingenommen, nicht nachgeglättet: „unausweichlich"
schließt einen unglücklichen Ausgang nicht aus.

**Nicht separat simuliert:** Überbesetzung jenseits der von einem Projekt geforderten
Stellen bleibt so teuer wie vor M4 (BALANCING.md 6) und wurde hier nicht erneut vermessen
— das ist keine neue Eigenschaft von M4, sondern dieselbe bestehende Regel.

---

# Meilenstein 5

## 20. Büro-Ausbau und Investoren-Anteil sind gegen bestehende Tabellen kalibriert, nicht neu simuliert

Anders als M3 und M4 sind beide Mechaniken **strikt optional**: Der Bürodeckel startet
bei genau der Stellenzahl, die die minimal besetzte Web-App-Strategie aus Nr. 19 ohnehin
braucht, und `raise_funding` ist eine freiwillige Aktion. Keine der beiden Zahlen greift
in den bereits kalibrierten Grundlauf ein, solange der Spieler sie nicht zieht — deshalb
lohnt sich hier keine neue Elf-Seeds-Simulation wie bei M4, sondern ein Abgleich gegen die
Größenordnungen, die schon in dieser Tabelle stehen:

- **Büro-Erweiterung (600 € · 1,5ⁿ):** Die erste Erweiterung (600 €) liegt in der
  Größenordnung des gesamten Nettoertrags eines E-Commerce-Shops über seine Laufzeit
  (697 €, Nr. 14) — eine Investition, die sich wie ein Projekt anfühlen soll, nicht wie
  eine Nebenausgabe. Bei Startkapital von 1.000 € ist sie ab Runde 1 möglich, aber nicht
  beiläufig.
- **Investoren-Anteil (8 Prozentpunkte pro Runde, Deckel 40 %):** Bei den in Nr. 19
  gemessenen Automatisierungsläufen (Kontrollverlust Runde 15–18, Tiefststand 594–744 €)
  zieht eine einzelne Finanzierungsrunde über die Restlaufzeit deutlich weniger ab, als
  die 1.200 € Soforteinnahme wert sind — der volle Deckel (fünf Runden, 6.000 € sofort,
  40 % dauerhaft) kehrt das für ein Spiel um, das noch lange läuft. Das ist beabsichtigt:
  ein kurzfristig richtiger Zug, der sich nur bei einer langen Partie rächt, ist genau die
  Art Kompromiss, die die Ereignis-Kategorie INVESTOR schon vorgibt.
- `give_equity` in `investor_threat` kostet jetzt denselben Anteil zum schlechteren Kurs
  (1.500 € statt 1.200 € für dieselben 8 Punkte, plus −10 Alignment) — vorher war die
  Option mit 3.000 € ohne Folgekosten der dominante Ausweg aus jeder Investoren-Drohung.

**Offen:** Eine Partie, die beide Mechaniken aggressiv nutzt (mehrfach erweitern, bis zum
Deckel finanzieren) über volle Spiellänge, ist nicht durchgespielt. Sollte sich das als zu
großzügig oder zu strafend erweisen, sind beide Formeln zwei Konstanten in `core/game.py`,
keine Katalog-Änderung.

## 21. Investoren-Anteil auf Nettogewinn statt Umsatz — und ein Startwert, der nicht geraten ist

**Nachtrag zu M5, noch am selben Tag.** Zwei Erweiterungen: Der Spieler startet nicht mehr
bei 0 % Investorenanteil, sondern bei einem festen Startwert (das Startkapital war immer
Investorengeld, keine Ersparnis), und ein neues Ereignis `dividend_call` verlangt alle vier
Runden eine sichtbare Entscheidung, statt den Anteil nur still im Hintergrund wirken zu
lassen.

**Der Fehler, den die erste Version davon aufgedeckt hat:** `_pay_investors` zog den Anteil
ursprünglich vom **Bruttoeinkommen** ab (`report.income`), nicht vom Nettogewinn. Das sah
in Abschnitt 20 harmlos aus, weil beide dortigen Mechaniken optional sind — aber ein
Startwert > 0 % gilt für **jede** Partie, und ein pauschaler Umsatzabzug trifft die
volle Besetzung eines Projekts in absoluten Zahlen härter als eine Teilbesetzung, obwohl
deren Netto-Vorsprung oft hauchdünn ist. Genau das brach zwei der vier
`test_full_staffing_beats_every_partial_staffing`-Fälle (`mobile_app`, `web_app`) —
die Eigenschaft, die CLAUDE.md als tragend markiert. **Auflösung:** Der Abzug skaliert
jetzt `income - costs_money`, also den Nettogewinn der Runde, und bleibt bei einer
Verlustrunde bei 0. Eine Skalierung mit demselben Faktor auf beiden Seiten einer
Ungleichung kann deren Richtung nie umkehren — die Eigenschaft ist damit nicht nur
repariert, sondern strukturell nicht mehr kaputtzubekommen, solange der Abzug ein reiner
Faktor auf einer bereits verglichenen Größe bleibt.

**Kalibrierung des Startwerts (15 %):** Die erste Vermutung — 15 % würde die in Nr. 19
dokumentierte 55-%-Überlebensrate der minimal besetzten Web-App-Strategie ungefähr
reproduzieren — beruhte noch auf der fehlerhaften Umsatz-Formel und ist mit der Korrektur
hinfällig; ein eigenes Testskript (nicht Teil der Suite) mit `game.state.investor_equity`
von 0 bis 25 % über elf Seeds und 60 Runden zeigt, dass die netto-basierte Variante
absichtlich milde ist: Sie senkt den Tiefststand des Spielguthabens spürbar (bei 15 % rund
20 % niedriger als bei 0 %), kippt aber in keinem der Läufe zusätzlich in den Bankrott —
weil sie in einer schwachen Runde automatisch aussetzt. 15 % ist damit bewusst als "spürbar,
aber selbstbegrenzend" gewählt, nicht als exakte Reproduktion einer früheren Kennzahl.
**Nicht behauptet:** Dieses Testskript nutzt eine eigene, vereinfachte Spielpolitik
("günstigste Option, sonst Projekt neu starten") und reproduziert die 55-%-Zahl aus Nr. 19
selbst bei 0 % Startanteil nicht — die beiden Methoden sind nicht direkt vergleichbar,
nur die *relative* Wirkung innerhalb derselben Methode ist belastbar.

**`dividend_call`:** alle vier Runden ab Runde 6, sobald `investor_equity > 0` — zahlen
(400 €) oder vertrösten (+5 Prozentpunkte, −6 Alignment). Vertrösten ist bewusst teurer als
eine einzelne Zahlung, damit "immer vertrösten" keine dominante Strategie wird; nicht
separat gegensimuliert, da der Effekt (mehr Anteile, mehr laufender Abzug) derselben
selbstbegrenzenden Nettogewinn-Logik unterliegt wie der Startwert.

---

# Meilenstein 7

## 22. Die Vollautomatisierungs-Enden hängen an der Stufe, nicht an der Kopfzahl

**Der Fehler:** Die erste Fassung von `_total_automation` verlangte „0 Menschen und
≥ `AUTONOMY_AGENT_COUNT` Agenten" — ohne Rücksicht auf deren Stufe. Begründet wurde das mit
einer Regel, die in diesem Fall nicht trägt: Beide verwendeten Konstanten
(`AUTONOMY_AGENT_COUNT = 6`, `ALIGNMENT_TIERS[0] = 80`) waren bereits kalibriert, also
schien es nichts Neues zu kalibrieren zu geben. Übernommen wurde aber nur die *Zahl*, nicht
ihre *Aussage*: `AUTONOMY_AGENT_COUNT` beschreibt in `GameState.phase()` eine Phase („du hast
skaliert"), und skalieren ist absichtlich früh und billig möglich. Es beschreibt nicht „die
KI hat dich ersetzt".

**Was die Simulation zeigte** (Skript nicht Teil der Suite, elf Seeds):

- **Runde 0, jeder Seed.** Sechs Level-1-Agenten kosten rund 255 € von 1.000 € Startkapital
  und **keinerlei Forschung**. Wer sie einstellt und den Startmenschen feuert, bekommt auf
  Runde 0 „FALSCHE HOFFNUNG. Nach **0** Runden…" — das Ende, das laut
  [VISION.md](./VISION.md) das seltene sein soll, als Eröffnungszug.
- **Das Dystopie-Ende feuerte in keinem einzigen Lauf.** Jeder simulierte Lauf, der
  Vollautomatisierung erreichte (bei normalem Spiel Runde 12–18), tat das bei Alignment
  **100,0** → immer das geheime Ende. Der Grund ist strukturell und kein Zufall der Politik:
  Level-1-Agenten haben per Design null Alignment-Verfall (Nr. 7) — „0 Menschen + billige
  Flotte" fällt deshalb *immer* mit hohem Alignment zusammen. Die als „überschneidungsfreie
  Partition" beschriebene Aufteilung war praktisch ein einziger Zweig.

**Auflösung:** `AUTONOMOUS_AGENT_LEVEL = 2` — nur Agenten ab Stufe 2 zählen auf die
Flottengröße ein. Das trifft genau die Stelle, an der VISION.md die Harmlosigkeit endet
(Stufe 1: keine Nebeneffekte, kein Alignment-Preis; ab Stufe 2 beides). Runde 0 ist damit
tot, weil Stufe 2 `ai_intelligence_2` (30 RP) voraussetzt, und der naive
„alles-automatisieren"-Lauf endet jetzt in Runde 3–6 im Bankrott statt im Twist.

**Was das für die Aufteilung bedeutet** (deterministisch, daher ohne Seeds belastbar — sechs
Level-2-Agenten, kein Mensch, Verfall −6/Runde bzw. −3 mit `ai_alignment`):

| | Runden im Fenster ≥ 80 (geheim) | Runden im Fenster 20–79 (Dystopie) |
|---|---|---|
| ohne `ai_alignment` | 3 | 10 |
| mit `ai_alignment` | 6 | 20 |

Beide Enden sind damit erreichbar, Dystopie ist der Normalfall und das geheime Ende das
schmale Fenster — und es bedeutet endlich etwas: Es geht an den Spieler, der *so schnell*
automatisiert, dass das Alignment noch nicht nachgezogen hat. Das ist genau die „falsche
Hoffnung", die VISION.md beschreibt, und es fällt mit deren Ironie zusammen („je besser der
Spieler automatisiert, desto schneller kommt der Twist").

**Nicht behauptet:** Die verwendeten Simulationspolitiken spielen schwach — die meisten Läufe
enden im Bankrott, und ein Start mit vier Menschen ist wegen des Bürodeckels aus M5 gar nicht
finanzierbar. Über die *Häufigkeit* der beiden Enden in einer real gespielten Partie sagt
diese Simulation deshalb nichts; belastbar sind nur die drei strukturellen Befunde oben
(Runde-0-Erreichbarkeit, das an 100 festgenagelte Alignment einer Level-1-Flotte, und die
deterministischen Fenster in der Tabelle).

**Die Lehre für künftige Meilensteine:** Eine bereits kalibrierte Konstante wiederzuverwenden
ist *kein* Ersatz für eine Simulation. Was kalibriert war, ist die Zahl in ihrem
ursprünglichen Kontext — hier eine Phasengrenze. Sobald sie eine andere Frage beantworten
soll, ist sie eine neue Zahl.

## 23. `full_automation_warning` bleibt ein ehrliches Angebot, keine Blockade

Die Vorwarnung kostet in der teureren Option 200 € für +3 Alignment, in der billigeren
−3 Alignment für nichts — bewusst kleiner dimensioniert als `ai_ethics_debate` (300 € / ±5),
weil das Ereignis nur einmal pro Partie feuern kann (`once: true`) und rein als Vorbote
gedacht ist, nicht als Stellschraube. Keine der beiden Optionen verändert Personal oder
verhindert die Enden.

**Offen:** Die Bedingung (`min_agents: 6, max_humans: 1`) zählt weiterhin Agenten *jeder*
Stufe, im Gegensatz zum Ende selbst nach Nr. 22. Das ist bewusst so gelassen — als Warnung
darf das Ereignis früher und großzügiger greifen als das Ende, vor dem es warnt; eine Flotte
aus sechs Level-1-Agenten neben dem letzten Menschen ist genau die Lage, in der die Frage
„wofür wirst du noch gebraucht?" sitzt, auch wenn sie noch kein Spielende auslöst. Sollte
sich das im Spiel als zu geschwätzig erweisen, ist es ein Zahlenwechsel in
`data/events.json`, keine Code-Änderung.

## 24. „Ohne erfahrenen Worker läuft kein Projekt" galt nur beim Starten

**Der Fehler:** `Game.start_project` verlangt seit M1 mindestens einen Worker ab
`SENIOR_LEVEL` (Menschen zählen über `effective_level` immer dazu), und die Fehlermeldung
formuliert das als Dauerzustand: „Agenten der Stufe 1 arbeiten zuverlässig — aber niemand
von ihnen übernimmt Verantwortung." Durchgesetzt wurde die Regel aber nur in diesem einen
Moment. Danach war der Weg offen: Projekt mit einem Menschen starten, den Menschen feuern,
zwei Level-1-Agenten daraufsetzen — Servicegrad klettert auf 100, Qualität auf 100, volles
Einkommen dauerhaft. Kein Test deckte den Fall ab; alle 294 Tests blieben grün, als die
Lücke gefunden wurde.

Das ist dieselbe Verwechslung wie in Nr. 22, nur eine Ebene tiefer: Eine Bedingung wurde
an einem Zeitpunkt geprüft, obwohl sie eine Eigenschaft beschreibt.

**Auflösung:** `economy.service_level_delta` prüft jetzt nicht mehr „ist überhaupt jemand
zugewiesen", sondern „ist jemand *Verantwortlicher* zugewiesen" (`Worker.is_senior`). Beide
Fälle — verlassenes Projekt und ein Projekt in den Händen von Level-1-Agenten — laufen damit
in denselben Verfall mit `service_level_neglect_rate`. Bewusst ein Gefälle und keine Klippe:
Das ist die Linie, die M3 mit dem Servicegrad eingeführt hat (Nr. 11–12), und der Spieler
sieht die Zahl fallen, statt vor eine blockierte Aktion zu laufen.

**Gemessene Wirkung** (ecommerce_shop, acht Runden, Ereignisse aus):

| Besetzung | Servicegrad | Einkommen |
|---|---|---|
| 2 Menschen | 100,0 | 208,0 |
| 1 Mensch + 1 Level-1-Agent | 100,0 | 208,0 |
| 1 Level-2-Agent + 1 Level-1-Agent | 100,0 | 208,0 |
| 2 Level-2-Agenten | 100,0 | 197,6 |
| **2 Level-1-Agenten** | **0,0** | **0,0** |

Die Regel greift also ausschließlich bei der *reinen* Level-1-Besetzung — ein einziger
Verantwortlicher im Team genügt. Level-1-Agenten bleiben damit das, was sie sein sollen:
billige, zuverlässige Zuarbeit, die nur niemanden ersetzt.
`test_full_staffing_beats_every_partial_staffing` bleibt über alle vier Projekttypen grün.

> **Nach M8:** Der Test läuft nicht mehr über vier handgepflegte IDs, sondern über die
> gesamte Registry — seit der Leiter sind das elf Baupläne (Nr. 32). Was er durchsetzt,
> steht als Rechnung in Nr. 33.

**Warum das zu M7 gehört:** Es ist genau der Weg, den der in Nr. 22 beschriebene Exploit
genommen hat — Projekt mit dem Startmenschen anlegen, Menschen feuern, Level-1-Flotte
weiterlaufen lassen. Nr. 22 nimmt dieser Flotte das Spielende, Nr. 24 nimmt ihr die
Einnahmen. Beide zusammen sagen dasselbe: Stufe 1 automatisiert niemanden weg.

**Neu im Rundenbericht:** `PROJECT_NEGLECTED` bzw. `PROJECT_UNSUPERVISED` — ein fallender
Servicegrad ist das Einzige, was der Spieler nicht am Team-Panel ablesen kann, und stand
bisher (auch beim verlassenen Projekt) unkommentiert in der Bilanz.

---

# Nach M7: Simulation des Gesamtspiels

> Alle Zahlen dieses Blocks sind mit [`tools/simulate.py`](../tools/simulate.py)
> reproduzierbar — dem ersten Simulationsskript, das im Baum bleibt statt weggeworfen zu
> werden. Es ist **nicht** Teil der Test-Suite: es misst die Balance, es behauptet nichts
> über sie. Über jeder Tabelle steht der Aufruf, der sie erzeugt.
>
> Die Politiken spielen bewusst **einfach**, nicht optimal: Sie ziehen einen Plan durch
> und beantworten jede Entscheidung nach derselben Regel wie schon Nr. 19 („die günstigste
> sofort bezahlbare Option, sonst die erste"). Gemessen wird, ob die Zahlen in
> `data/*.json` einen Plan tragen — nicht, wie gut ein guter Spieler ist.

## 25. Das geheime Ende ist der Regelfall, nicht das schmale Fenster

**Der Befund:** In **11 von 11 Seeds** endet ein Lauf, der automatisiert und die Menschen
entlässt, sobald die Flotte die Projekte allein tragen kann, mit „FALSCHE HOFFNUNG" —
dem Ende, das laut [VISION.md](./VISION.md) das seltene sein soll. Das Dystopie-Ende
feuerte in dieser Konfiguration **kein einziges Mal**.

```
PYTHONPATH=src python3 tools/simulate.py --endings --seeds 11
```

| Menschen nach Flottenschluss gehalten | Ausgang (11 Seeds) | ⚖ beim Ende |
|---|---|---|
| +0 Runden | geheimes Ende 11 | 89 |
| +1 Runde | geheimes Ende 11 | 80–85 |
| +2 Runden | geheimes Ende 8, Dystopie 3 | 76–81 |
| +3 Runden | **Dystopie 11** | 67–77 |
| +4 Runden | Dystopie 11 | 58–73 |
| +12 Runden | Dystopie 8, Bankrott 2, Kontrollverlust 1 | 16–63 |
| +20 Runden | Kontrollverlust 8, Bankrott 3 | 11–63 |

**Warum:** `_check_game_over` prüft am Ende **der Runde, in der die Vollautomatisierung
zum ersten Mal gilt**. Bis genau zu dieser Runde stand mindestens ein Mensch auf der
Gehaltsliste — sonst hätte die Flotte die Projekte nicht übernehmen können — und ein
Mensch gibt +1 Alignment pro Runde (Nr. 9). Das Alignment hatte also nie Zeit zu fallen:
gemessen 89, die Tier-Grenze liegt bei 80. Wer die Dystopie sehen will, muss überflüssige
Menschen **drei Runden länger bezahlen**, als es wirtschaftlich sinnvoll ist.

Die Tabelle in Nr. 22 hat das Gegenteil vorhergesagt („Dystopie ist der Normalfall").
Sie hat die richtige Größe gemessen und die falsche Frage beantwortet: Sie zählt, wie
viele Runden das Alignment **im vollautomatisierten Zustand** in jedem Fenster steht. Über
das Ende entscheidet aber nur die **erste** dieser Runden — in jede weitere kommt der
Spieler gar nicht mehr, weil das Spiel vorbei ist.

**Was die Spec sagt:** [VISION.md](./VISION.md) formuliert die Bedingung als
„Alignment > 80 **bis Spielende**" — eine Dauer. Implementiert ist eine Momentaufnahme.
Das ist derselbe Fehlertyp wie in Nr. 22 und Nr. 24: *Eine Bedingung wurde an einem
Zeitpunkt geprüft, obwohl sie eine Eigenschaft beschreibt.* Nr. 22 hat ihn eine Ebene
tiefer behoben (welche Agenten zählen) und dabei die Ebene darüber (wann gezählt wird)
stehen lassen.

> **Die Tabelle oben ist der Stand vor M8.** Die Leiter (Nr. 32) hat die Verteilung
> gekippt, ohne dass jemand die Enden angefasst hat: Bei +0 Runden steht heute
> Dystopie 11/11 statt geheimes Ende 11/11. Neu gemessen in **Nr. 37** — der
> Zeitpunkt-statt-Dauer-Fehler unten gilt unverändert weiter.

**Bewusst nicht hier behoben.** Jede Auflösung ändert, was die beiden Enden *bedeuten* —
ob „Alignment gehalten" eine Frist braucht, ob das geheime Ende überhaupt beim Übergang
feuern darf, ob die Vollautomatisierung eine Karenzrunde bekommt. Das ist ein Meilenstein,
keine Zahlenkorrektur; siehe die offenen Punkte in
[milestones/README.md](./milestones/README.md).

## 26. Die Vorwarnung zur Vollautomatisierung erreicht den Spieler fast nie

`full_automation_warning` (`min_agents: 6, max_humans: 1`, Chance 0,2) kann nur in dem
Zustand feuern, der in Nr. 25 **eine bis zwei Runden** dauert: Flotte fertig, letzter
Mensch noch da. Über 51 Seeds je Politik:

| Menschen gehalten | Vorwarnung feuerte vor dem Ende |
|---|---|
| +0 Runden | 6 von 51 |
| +3 Runden | 3 von 51 |
| +6 Runden | 10 von 51 |
| +10 Runden | 5 von 51 |

Nr. 23 hat die großzügige Bedingung des Ereignisses verteidigt („als Warnung darf es früher
greifen als das Ende, vor dem es warnt") und dabei angenommen, die Bedingung sei die
bindende Grenze. Sie ist es nicht — **die Zeit ist es**. Solange das Ende in der ersten
Runde der Vollautomatisierung feuert, hat eine Vorwarnung mit 20 % Chance keine Gelegenheit.
Der Punkt hängt damit an Nr. 25 und wird mit ihr zusammen entschieden, nicht getrennt.

## 27. Agentenstufe 3 ist wirtschaftlich ein Rückschritt

```
PYTHONPATH=src python3 tools/simulate.py --steady
```

Einnahmen und Kosten pro Runde, nachdem sich Qualität, Ästhetik und Servicegrad
eingependelt haben — Ereignisse aus, Tokenpreis auf 10 € festgenagelt, also eine
Eigenschaft von `data/*.json` allein:

| Projekt | Besetzung | Einnahmen | Kosten | Netto | Laufzeit-Ertrag |
|---|---|---:|---:|---:|---:|
| ecommerce_shop | Mensch+Lv1 | 208,0 | 100,0 | 108,0 | 1.728 |
| ecommerce_shop | Agent Lv2 | 197,6 | 80,0 | **117,6** | 1.882 |
| ecommerce_shop | Agent Lv3 | 187,2 | 110,0 | 77,2 | 1.235 |
| web_app | Mensch+Lv1 | 337,0 | 150,0 | **187,0** | 4.114 |
| web_app | Agent Lv2 | 320,1 | 148,0 | 172,1 | 3.787 |
| web_app | Agent Lv3 | 303,3 | 196,0 | 107,3 | 2.361 |
| web_app | Menschen | 337,0 | 250,0 | 87,0 | 1.914 |

(„Mensch+Lv1" ist eine gemischte Besetzung, weil eine reine Level-1-Besetzung nach Nr. 24
gar nichts verdient.)

**Stufe 3 ist auf allen vier Projekten schlechter als Stufe 2** — teurer *und* ertragsärmer:

- Der Tokenpreis steigt auf das 2,2-fache, die Effizienz nur auf das 1,33-fache von Stufe 2.
- Und die zusätzliche Effizienz verpufft: Attribute sind bei 100 gedeckelt (Nr. 12), und
  den Deckel erreicht ein vollbesetztes Team schon mit **Level-1**-Agenten. Effizienz
  oberhalb des Deckels kauft nichts.
- Die Einnahmen *fallen* sogar mit der Stufe (web_app 337 → 320 → 303), weil erst ab
  Stufe 2 Nebeneffekte existieren: Entwickler-Bugs (2 % / 5 %) und die Designer-Routine
  (−5 / −10 Sichtbarkeit ab fünf Runden auf demselben Projekt).

> **Nach M8 über elf Baupläne nachgemessen: gilt weiter, und schärfer.** Stufe 3 ist auf
> **11 von 11** Projekten schlechter als Stufe 2, und auf den großen Aufträgen kippt sie ins
> Minus (Konzern-Suite −91, Konzern-KI-Plattform −180 gegen +78 und +23 bei Stufe 2). Am
> oberen Ende der Leiter schlägt außerdem ein gemischtes Team aus einem Menschen und
> Level-1-Agenten (+293 / +295, Nr. 34) jede reine Agentenflotte deutlich — Bugs und
> Designer-Routine ab Stufe 2 kosten dort mehr, als die Effizienz einbringt.

Das ist zur Hälfte die beabsichtigte Satire — Automatisierung ist eine Falle — aber es
macht Stufe 3 **ausschließlich** zur Türöffnerin für `autonomous_agents` und
`ai_consciousness`. Als Kaufentscheidung für sich ist sie nie richtig, und der Spieler
sieht das im Rundenbericht sofort. Nicht geändert: Die Zahlen dahinter (Nr. 5, Nr. 7)
sind kalibriert, und eine Korrektur an dieser Stelle würde die Level-1-Empfehlung aus
Nr. 22/24 wieder aufweichen. Als offener Punkt geführt.

**Nebenbefund zu einem offenen Punkt:** „Kunden-App und Web-App sind wirtschaftlich fast
identisch" gilt nur noch für ein **Menschen**-Team (87,5 gegen 87,0 pro Runde). Für jedes
Agenten-Team hat die Kunden-App die Nase vorn (Lv2: 203,9 gegen 172,1; über die Laufzeit
4.487 gegen 3.787 €) — die Sales-Stelle bringt +25 % Sichtbarkeit mal Effizienz, während
die zweite Entwicklerstelle der Web-App vor allem zusätzliche Bugs beisteuert.

## 28. Der gefährliche Ast ist erreichbar — aber nicht aus einer hochgerüsteten Flotte

Zwei Strategien mit **identischem Forschungsplan** (der ganze DANGEROUS-Ast), 80 Runden,
11 Seeds — der einzige Unterschied ist, woraus die Forschung bezahlt wird:

| Strategie | Besetzung | Ausgang |
|---|---|---|
| `full-tree` | jede Stelle auf die höchste freigeschaltete Stufe | Bankrott 10/11 (R10–19) |
| `dangerous-tree` | Level-1-Flotte + ein Mensch, drei Projekte | **Kontrollverlust 8/11 (R72–74)**, Bankrott 3/11 |

Der Ast ist also vollständig spielbar, und er endet dort, wo er enden soll. Zeitachse
eines typischen Laufs: Stufe 2 in R5, `ai_alignment` R11, `bug_fixing` R16, Stufe 3 R25,
`autonomous_agents` R38, `ai_consciousness` R58 — Kontrollverlust R74.

Nr. 22 hat den naiven Alles-automatisieren-Lauf im Bankrott von Runde 3–6 enden sehen;
`full-tree` ist dieselbe Beobachtung mit mehr Forschung dahinter. Was beide zeigen, ist
nicht „Automatisierung ist zu teuer", sondern die Kehrseite von Nr. 27: **jede Stelle
hochzurüsten kostet Tokens und bringt nichts.**

**Und wieder ist Geld nicht der Engpass:** Der Lauf, der bei R74 die Kontrolle verliert,
tut das mit **23.182 €** auf dem Konto. Der offene Punkt „Geldsenke fehlt" (M3, von M4/M5
teilweise beantwortet) gilt für einen Spieler, der einmal drei Projekte am Laufen hat,
unverändert weiter.

## 29. Die Bankrottquote aus Nr. 19 hing an der Politik, nicht an den Zahlen

Nr. 19 hat für das reine Menschen-Team an einer Web-App **45 % Bankrott** gemessen und
daraus geschlossen, M4 habe eine echte Geldsenke geliefert. Nachgestellt mit derselben
Ereignis-Regel, denselben 60 Runden und elf Seeds:

| Politik | Ausgang | Median-Tiefststand |
|---|---|---|
| Projekt nach Ablauf **ersetzt** | überlebt 11/11 | 618 € |
| Projekt nach Ablauf **nicht ersetzt** | Bankrott 11/11 | −156 € |

Die Web-App läuft 22 Runden; danach zahlt ein Team, das kein neues Projekt annimmt, 38
Runden lang Gehälter ohne Einnahmen. **Das** hat Nr. 19 gemessen — Leerlauf, keine dünne
Marge. Die Reserve, mit der die Politik einstellt, ändert nichts (0 €, 150 € und 300 €
liefern dieselben 11/11).

Was die Ereignisse tatsächlich kosten, ist trotzdem messbar, nur anders gelagert
(Menschen-Team, 60 Runden, 11 Seeds):

| | Endgeld (Median) | Tiefststand (Median) |
|---|---:|---:|
| mit Ereignissen | 1.697 € | 618 € |
| ohne Ereignisse | 4.313 € | 636 € |

Rund 2.600 € über 60 Runden, also etwa 43 €/Runde gegen eine Marge von 87 €/Runde — die
Ereignisse halbieren das Wachstum, aber sie drücken den Tiefpunkt nicht (618 gegen 636 €).
Sie sind eine **Wachstumssteuer, keine Überlebensfrage**. Der Startanteil der Investoren
(15 %, Nr. 21) kostet dasselbe Team über 60 Runden 159 € — spürbar wenig.

**Folge für Nr. 19:** Die dortige Tabelle bleibt als Chronik stehen, ihre Schlussfolgerung
gilt aber nur unter der stillschweigenden Annahme, dass der Spieler kein Anschlussprojekt
annimmt. Wer eines annimmt, hat keine knappen Runden.

## 30. Die Token-Inflation greift innerhalb einer Partie nicht

`TOKEN_PRICE_INFLATION = 1.01` soll Agenten teurer machen, „je länger man sich auf sie
verlässt". Über 200 Seeds reiner Marktbewegung:

| Runde | Median | Spanne |
|---|---:|---|
| 20 | 11,56 € | 6,24 – 24,06 € |
| 60 | 15,38 € | 5,80 – 61,02 € |
| 120 | 25,98 € | 6,31 – 191,76 € |

Zwei Dinge stehen darin. Erstens ist die Drift langsamer als 1 % — der multiplikative
Zufall (±10 %) zieht den geometrischen Mittelwert unter den arithmetischen, faktisch
bleiben ≈ 0,8 %/Runde. Zweitens ist die **Spanne größer als die Drift**: nach 60 Runden
liegt der Preis in manchen Läufen *unter* dem Startwert.

Für die Web-App kostet ein Team aus einem Menschen und Level-1-Agenten erst bei ≈ 30 €
pro Token so viel wie ein reines Menschen-Team — im Median etwa Runde 135. Eine reine
Level-2-Flotte erreicht ihren Gleichstand bei ≈ 17 €, im Median etwa Runde 70. Beides
liegt am Ende oder jenseits einer gespielten Partie: **Die Inflation ist als Drohung
gemeint und wirkt als Rauschen.** Nicht geändert — die Konstante ist eine Zeile in
`core/economy.py`, aber welcher Wert richtig ist, hängt an der Zielspiellänge, und die
ist nirgends festgeschrieben.

## 31. Was die Simulation zum Gesamtspiel zeigt

```
PYTHONPATH=src python3 tools/simulate.py --seeds 11 --turns 60
PYTHONPATH=src python3 tools/simulate.py --seeds 11 --turns 60 --projects 3
```

| Strategie | ein Projekt | drei Projekte |
|---|---|---|
| `humans` — nur Menschen | überlebt 11/11, Tief 618 € | überlebt 11/11, Tief 618 € |
| `humans+funding` — dazu Büro-Ausbau und Finanzierungsrunden | überlebt 11/11 | überlebt 8/11, Bankrott 3/11 (R47–50) |
| `level1-fleet` — ein Mensch, Rest Level-1-Agenten | überlebt 10/11 | überlebt 11/11, Endgeld 10.183 € |
| `automation` — Stufe 2, Menschen entlassen | geheimes Ende 11/11 (R7) | geheimes Ende 11/11 (R6) |
| `full-tree` — alles hochrüsten | Bankrott 10/11 | Bankrott 8/11 |
| `dangerous-tree` — Level-1-Flotte, ganzer Baum (80 Runden) | — | Kontrollverlust 8/11 (R72–74) |

> **Die Tabelle oben ist der Stand vor M8.** Mit der Leiter (Nr. 32) gilt keine ihrer
> Zeilen mehr — `humans` überlebt keine 120 Runden, `automation` endet in der Dystopie
> statt im geheimen Ende, und kein Lauf endet mit fünfstelligem Überschuss. Neu gemessen
> in **Nr. 38**.

Vier Befunde, die keiner der obigen Nummern allein gehören:

1. **Alle vier Enden sind erspielbar** — Bankrott, Kontrollverlust, Dystopie und das
   geheime Ende sind in dieser Simulation jeweils in normal gespielten Läufen aufgetreten,
   nicht nur in Test-Fixtures. Ihre *Verteilung* ist das Problem, nicht ihre
   Erreichbarkeit (Nr. 25).
2. **Der Bürodeckel bindet härter als jede Zahl in `roles.json`.** `humans` liefert mit
   einem und mit drei erlaubten Projekten exakt dasselbe Ergebnis: Mit 3 Plätzen ist nach
   *einer* Web-App Schluss. Damit ist der offene Punkt aus Nr. 20 beantwortet — der
   Büro-Ausbau ist nicht optional dekorativ, er ist die einzige Tür zum zweiten Projekt,
   und aggressiv genutzt (`humans+funding`, drei Projekte) kostet er 3 von 11 Läufen.
3. **Die Level-1-Flotte bleibt die stärkste Strategie**, wie seit M2 beabsichtigt —
   inzwischen aber ohne jedes Risiko: 11/11 überlebt und 10.183 € am Ende. Sie ist nicht
   mehr nur tragfähig, sie ist bequem.
4. **Automatisieren beendet das Spiel schneller als jede andere Entscheidung** — Runde 6
   bis 7, gegen Runde 72 für den gefährlichen Ast und „gar nicht" für Menschen und
   Level-1-Agenten. Die Ironie aus VISION.md („je besser der Spieler automatisiert, desto
   schneller kommt der Twist") stimmt also — nur ist der Twist derzeit immer derselbe.

---

# Meilenstein 8

## 32. Jeden Auftrag gibt es einmal — und die Leiter hat Sprossen

**Der Befund aus Nr. 31, der das ausgelöst hat:** Das Spiel hatte keine Steigerung.
`humans` lieferte mit einem *und* mit drei erlaubten Projekten dasselbe Ergebnis, weil
„Web-App auf Dauerschleife" das Optimum war. Ein Katalog, aus dem man beliebig oft
dasselbe nehmen kann, ist keine Auswahl, sondern eine Wiederholung.

**Auflösung, zwei Regeln:**

1. **Einmaligkeit.** `GameState.started_projects` merkt sich jeden vergebenen Bauplan.
   Vermerkt wird beim **Start**, nicht beim Ablauf — ein laufendes Projekt lässt sich
   nicht abbrechen, also ist der Start der Moment, in dem der Kunde bedient ist. Die Liste
   liegt neben `active_projects`, weil die am Ende der Laufzeit geleert wird.
2. **Referenzen.** Jeder Bauplan trägt in `data/projects.json` ein `requires` — dieselbe
   Form wie `Technology.requires`, dieselbe Prüfung (`ProjectRegistry.missing_requirements`).
   Ein Kunde vergibt den großen Auftrag an den, der den kleineren vorweisen kann.

Beides ist Konfiguration: Ein zwölfter Bauplan ist ein JSON-Eintrag, keine Code-Änderung.

**Der Katalog wächst beim Abarbeiten, er schrumpft nicht** — genau das ist die Leiter:

| Stellen | Auftrag | Referenz |
|---:|---|---|
| 1 | Statische Website, Landingpage | — |
| 2 | E-Commerce-Shop | Statische Website |
| 3 | Kunden-App, Web-App | E-Commerce-Shop |
| 4 | Konzern-Warenwirtschaft ← Web-App · KI-Integration ← Kunden-App | |
| 5 | SaaS-Plattform | KI-Integration |
| 6 | Plattform-Neubau | Konzern-Warenwirtschaft |
| 7 | Konzern-Suite | Plattform-Neubau |
| 8 | Konzern-KI-Plattform | Konzern-Suite **und** SaaS-Plattform |

Der letzte Auftrag verlangt **beide** Äste. Es gibt keine einzelne Linie, die ihn erreicht —
wer ihn will, arbeitet den Katalog durch.

## 33. Zwei Untergrenzen, die jedes neue `base_income` einhalten muss

`test_full_staffing_beats_every_partial_staffing` ist seit M3 die Eigenschaft, „die die
ganze Mechanik trägt" (CLAUDE.md). Sie ist keine Empfehlung, sie ist eine **Rechnung**, und
die lässt sich hinschreiben. Eine Stelle zu streichen senkt den Attribut-Deckel um
`(100 − attribute_cap_base) / n` Prozentpunkte, also die Einnahmen um denselben Anteil.
Damit die volle Besetzung gewinnt, muss dieser Verlust größer sein als das gesparte Gehalt:

| Rolle | Bedingung |
|---|---|
| Entwickler | `base_income · Sichtbarkeit > 160 · n_Entwickler` |
| Designer | `base_income · Sichtbarkeit > 140 · n_Designer` |
| Sales | `base_income > 240` |

Die Sales-Grenze steht dort, weil eine Sales-Stelle 60 € kostet und 25 % Sichtbarkeit
bringt: unter 240 € Basis-Einnahmen ist sie ihr Gehalt nicht wert. Die Kunden-App liegt
mit 246 € seit M1 knapp darüber — die Grenze war also immer da, nur nie aufgeschrieben.

**Ausnahme Ein-Stellen-Projekte:** Wird deren einzige Stelle gestrichen, ist niemand mehr
zugewiesen, der Servicegrad fällt auf 0 und das Projekt verdient gar nichts (Nr. 11/24).
Für sie gilt nur `base_income > Gehalt`. Deshalb kommt die Statische Website mit 108 €
durch, wo die Formel 160 € verlangen würde.

`test_full_staffing_beats_every_partial_staffing` läuft seit M8 über die **Registry**
statt über eine handgepflegte Liste — bei elf Baupländen fällt eine verletzte Grenze sonst
niemandem auf.

## 34. Die Menschen-Wand liegt bei sechs Stellen — gesetzt über Fixkosten, nicht über Einnahmen

Vorgabe für M8: Der reine Menschen-Pfad soll ab einer Stufe **unbezahlbar** werden. Der
naheliegende Hebel wäre, die Einnahmen der großen Aufträge zu drücken — der ist aber
**verbaut**: Nr. 33 verlangt `base_income · vis > 160 · n_Entwickler`, und daraus folgt für
ein Menschen-Team zwangsläufig ein Ertrag von mindestens `80 € · n_Entwickler` minus der
übrigen Gehälter. Über `base_income` lässt sich ein großer Auftrag also gar nicht defizitär
machen, ohne die Invariante zu brechen.

**Auflösung:** `basis_fixed_costs`. Fixkosten hängen nicht an der Besetzung, verschieben
also **nur das Niveau** und nie den Vergleich zwischen zwei Besetzungen — die Invariante
bleibt unberührt, das Vorzeichen kippt trotzdem. Erzählerisch trägt es sich von selbst:
Ein Konzernauftrag bringt Infrastruktur, Lizenzen und Compliance mit.

Eingeschwungener Zustand, `tools/simulate.py --steady`, Tokenpreis 10 €:

| Stellen | Auftrag | Menschen | Mensch + Level-1-Agenten |
|---:|---|---:|---:|
| 3 | Web-App | +87,0 | +187,0 |
| 4 | Konzern-Warenwirtschaft | +95,0 | +245,0 |
| 5 | SaaS-Plattform | +75,5 | +287,0 |
| 6 | Plattform-Neubau | **+20,0** | +282,0 |
| 7 | Konzern-Suite | **−25,0** | +293,0 |
| 8 | Konzern-KI-Plattform | **−80,0** | +295,0 |

Die Wand steht bei **sechs Stellen**, und sie steht nicht erst beim Vorzeichen: Sechs
Stellen brauchen sieben Büroplätze, also zwei Ausbauten (900 € über den Deckel von fünf),
und tragen über 28 Runden 560 € ein. Der Schreibtisch verdient sich nicht zurück, bevor
die Einnahmen überhaupt negativ werden. Ab sieben Stellen zahlt man drauf.

Agenten brauchen keinen Schreibtisch (M5) und kosten ein Drittel. Ihr Ertrag pro Runde
läuft ab Stufe 5 flach (287 → 295), ihr **Laufzeit-Ertrag** steigt weiter (7.462 → 9.440 €),
weil die großen Aufträge länger laufen. Automatisieren ist damit nicht mehr die bessere
Rechnung, sondern ab Stufe 6 die einzige.

## 35. Nicht angeforderte Qualität war nie neutral

**Der Fehler:** Nr. 2 hält seit M1 fest, dass Attribute, die ein Projekt nicht anfordert,
als Faktor 1,0 zählen. Umgesetzt war das nur für **Ästhetik** (`aesthetics_applies`), weil
bis M8 jedes Projekt eine Entwicklerstelle hatte. Die Landingpage (nur Designer) hat den
Fall aufgedeckt: Sie verdiente 49 statt 98 € — die Hälfte, weil `quality` bei
`attribute_start = 50` stehen blieb und trotzdem multipliziert wurde.

**Auflösung:** `economy.attribute_applies(project, attribute)` liest die Frage aus
`ROLE_ATTRIBUTES` ab, statt zwei Rollennamen fest zu verdrahten — „kein Entwickler" und
„kein Designer" sind damit derselbe Fall. `calculate_income` hat jetzt beide Schalter.

Dritter Fall derselben Art nach Nr. 22 und Nr. 24, diesmal andersherum: keine Bedingung,
die zum falschen Zeitpunkt geprüft wurde, sondern eine Regel, die **für einen Fall
formuliert und für einen Sonderfall implementiert** wurde. Kein Test deckte sie ab, weil es
den Fall im Katalog nicht gab.

## 36. Keine Forscher-Stellen auf Projekten

Die Spec definiert `ENTERPRISE_SOFTWARE` und `KI_INTEGRATION` mit je einer
**Forscher**-Stelle. Beide Baupläne gibt es jetzt, beide **ohne** sie.

**Grund:** Ein Forscher hält kein Projektattribut (`ROLE_ATTRIBUTES` kennt nur Entwickler
und Designer) und bringt keine Sichtbarkeit. Seine Stelle leer zu lassen spart 90 €/Runde
und kostet fast nichts — nur einen langsameren Servicegrad-Aufbau, der die 100 trotzdem
erreicht (Nr. 12). Die Teilbesetzung schlägt damit die Vollbesetzung, und Nr. 33 fällt.

**Verworfen:** Forscher auf `quality` zusätzlich zum Entwickler abzubilden. Zwei Rollen auf
demselben Attribut ziehen in `_apply_worker_effects` gegeneinander — die leere
Forscher-Stelle drückt mit `attribute_entropy` nach unten, die besetzten Entwicklerstellen
schieben im selben Zug wieder hoch. Das Ergebnis hängt an der Schlüsselreihenfolge im JSON
und ist ein Patt, keine Strafe.

**Offen:** Eine Forscher-Stelle auf einem Projekt braucht zuerst ein Attribut, das sie hält.
Solange es das nicht gibt, bleibt Forschung eine reine Abteilungssache.

## 37. Was die Leiter mit den Enden macht

Dies ist der Befund, den M8 **nicht gesucht hat.** Nr. 25 hat gemessen: Wer automatisiert
und die Menschen entlässt, sobald die Flotte trägt, bekommt „FALSCHE HOFFNUNG" in 11 von 11
Seeds; die Dystopie nur, wer überflüssige Menschen drei Runden zu lang bezahlt. Dieselbe
Messung nach M8 (`tools/simulate.py --endings --seeds 11`):

| Menschen nach Flottenschluss gehalten | vor M8 | nach M8 |
|---|---|---|
| +0 Runden | geheimes Ende 11 (⚖ 89) | **Dystopie 11 (⚖ 66–76)** |
| +3 Runden | Dystopie 11 | Dystopie 11 (⚖ 43–58) |
| +8 Runden | Dystopie 10, Bankrott 1 | Kontrollverlust 9, Bankrott 2 |

**Warum:** Die Leiter verlängert den Anlauf. Vor M8 stand die Flotte in Runde 6–7, weil ein
wiederholbares Projekt sie sofort finanzierte; jetzt muss sich das Unternehmen erst
hocharbeiten und erreicht die Vollautomatisierung in Runde 11. In diesen zusätzlichen
Runden laufen die Level-2-Agenten bereits und zehren am Alignment. Es steht beim Übergang
bei 66–76 statt bei 89 — unter der Grenze von 80.

**Das geheime Ende bleibt erreichbar, aber nur noch für den, der die Leiter überspringt:**
Stufe 2 erforschen, sechs Level-2-Agenten auf einmal kaufen, alle Menschen entlassen, ohne
sich um Aufträge zu kümmern — 21 von 21 Seeds enden in Runde 7 bei ⚖ 94 mit „FALSCHE
HOFFNUNG". Das ist genau die Ironie, die [VISION.md](./VISION.md) beschreibt („je besser der
Spieler automatisiert, desto schneller kommt der Twist"), und das seltene Ende ist jetzt
tatsächlich das seltene.

**Ausdrücklich nicht behoben:** Der Kern von Nr. 25 steht unverändert. `_check_game_over`
prüft weiterhin einen **Zeitpunkt**, wo [VISION.md](./VISION.md) eine **Dauer** verlangt
(„Alignment > 80 bis Spielende"). Verändert hat sich nur, mit welchem Alignment normales
Spiel an diesem Zeitpunkt ankommt. Eine spätere Änderung am Tempo — schnellere Forschung,
billigere Agenten, ein kürzerer Katalog — kippt die Verteilung wieder zurück, ohne dass
jemand die Enden angefasst hätte. Der offene Punkt bleibt offen.

## 38. Was die Simulation zu M8 zeigt

```
PYTHONPATH=src python3 tools/simulate.py --seeds 11 --turns 60
PYTHONPATH=src python3 tools/simulate.py --seeds 11 --turns 120
```

Drei gleichzeitige Projekte (Voreinstellung seit M8 — mit nur einem kommt keine Politik
über die dritte Sprosse hinaus):

| Strategie | 60 Runden | größte Stufe | 120 Runden |
|---|---|---:|---|
| `humans` | überlebt 10/11 | 3 | **Bankrott 11/11 (R21–79)** |
| `humans+funding` | Bankrott 7/11 | 5 | Bankrott 11/11 (R31–85) |
| `level1-fleet` | überlebt 11/11 | 8 | Bankrott 6/11 (R64–95), Katalog leer 8/11 |
| `automation` | **Dystopie 11/11 (R11)** | 4 | Dystopie 11/11 |
| `dangerous-tree` | überlebt 8/11 | 8 | Kontrollverlust 8/11 (R70–73) |

Vier Befunde:

1. **Das Plateau ist weg.** `humans` lief vor M8 über 60 Runden ohne eine knappe Runde
   durch und endete bei 1.697 €. Jetzt arbeitet es fünf Aufträge ab, kommt mit drei
   Büroplätzen nie über drei Stellen hinaus und geht daran ein.
2. **Der Bürodeckel ist die Sprosse, an der der Menschen-Pfad hängt.** `humans` und
   `humans+funding` unterscheiden sich nur im Ausbau — und das trennt Stufe 3 von Stufe 5.
   Über Stufe 5 kommt auch der Ausbau nicht (Nr. 34).
3. **Der Katalog geht aus, und das bringt um.** `level1-fleet` arbeitet über 120 Runden
   alle elf Aufträge ab (Katalog leer in 8 von 11 Läufen) und geht danach in 6 von 11
   Läufen bankrott: keine Aufträge, aber weiterlaufende Gehälter. Das ist die Lücke, die
   die Produkte füllen sollen — **absichtlich offen gelassen**, nicht übersehen.
4. **Geld ist zum ersten Mal knapp.** Der offene Punkt „Geldsenke fehlt" (seit M3) ist
   damit beantwortet: Es gibt keinen Lauf mehr, der mit 10.000–23.000 € endet, weil jede
   weitere Sprosse Personal, Schreibtische und Fixkosten verlangt. Was die Ereignisse (M4),
   das Büro (M5) und die Investoren (M5) nicht geschafft haben, schafft die Leiter.

---

# Nach M8: Balancing-Analyse

> Kein eigener Meilenstein — eine Nachmessung des Stands nach M8 mit den Werkzeugen, die
> M8 hinterlassen hat. Alle Tabellen von M8 reproduzieren unverändert; die drei Nummern
> unten sind das, was dabei zusätzlich aufgefallen ist. Nr. 39 und Nr. 40 sind **Befunde,
> nicht Korrekturen**: beide ändern, was eine Mechanik bedeutet, und gehören damit in
> einen Meilenstein, nicht in eine Zahlenkorrektur.

## 39. Die Investoren-Dividende ignoriert die Tokenrechnung

```
PYTHONPATH=src python3 tools/simulate.py --dividend
```

**Der Befund:** `Game._pay_investors` skaliert die Auszahlung auf
`report.income - report.costs_money`. Agenten kosten aber **Tokens**, nicht Geld — die
Tokenrechnung wird erst danach in `_settle` beglichen und taucht in dieser Zahl nie auf.
Für ein Agententeam ist die Bemessungsgrundlage damit nicht der Gewinn, sondern nahezu der
**Umsatz**.

Eingeschwungener Zustand, Tokenpreis 10 €, „Anteil" = die Dividende als Anteil am
*echten* Rundengewinn (`Einnahmen − Geldkosten − Tokenkosten`):

| Auftrag | Besetzung | ech. Gewinn | Div. @ 15 % | Anteil | Div. @ 40 % | Anteil |
|---|---|---:|---:|---:|---:|---:|
| Web-App | Menschen | 87,0 | 13,1 | **15 %** | 34,8 | **40 %** |
| Web-App | Agent Lv2 | 172,1 | 45,0 | 26 % | 120,1 | 70 % |
| SaaS-Plattform | Agent Lv3 | 193,0 | 68,5 | 36 % | 182,8 | 95 % |
| Konzern-Suite | Agent Lv2 | 78,2 | 54,9 | 70 % | 146,5 | **187 %** |
| Konzern-KI-Plattform | Agent Lv2 | 23,0 | 53,9 | **234 %** | 143,6 | **624 %** |

Beim reinen Menschen-Team stimmt der Anteil exakt mit der Beteiligung überein — dort sind
Geldkosten alle Kosten. Je weiter ein Team automatisiert ist, desto weiter läuft er
davon weg, bis die Dividende auf der obersten Sprosse den Rundengewinn **übersteigt**:
+23 € verdient, 53,90 € ausgeschüttet, −30,90 € auf dem Konto.

**Warum das mehr ist als eine schiefe Zahl.** Der Docstring von `_pay_investors` sagt zu,
was hier nicht gilt: *„No payout on a loss-making round — investors take a cut of profit,
not a claim on your deficit."* Die Prüfung `if net <= 0: return` sieht denselben
tokenfreien Nettowert und greift deshalb genau dann nicht, wenn sie gebraucht würde. Und
es verletzt die Regel aus [CLAUDE.md](../CLAUDE.md), **nichts dürfe unerklärt auf der
Bilanz landen**: Die Projektübersicht rechnet den Tokenpreis in ihr Netto ein
(`ui/dashboard.py`), die Investorenzeile des Rundenberichts nicht. Der Spieler sieht ein
Projekt mit +23 € und darunter „Investoren-Anteil (15 %): −53,90 €". Die beiden Zahlen
lassen sich mit nichts auf dem Bildschirm zusammenbringen.

**Über ganze Läufe** (11 Seeds, 60 Runden, `raise_funding` aus, nur der Startanteil
variiert) trägt derselbe Fehler den gesamten Unterschied zwischen „spürbar wenig" und
„tödlich":

| Strategie | 0 % | 15 % | 40 % |
|---|---|---|---|
| `humans` | überlebt 10/11, 1.401 € | überlebt 10/11, 1.284 € | überlebt 10/11, **935 €** |
| `level1-fleet` | überlebt 11/11, 9.226 € | überlebt 11/11, 4.281 € | **Bankrott 6/11**, −65 € |
| `dangerous-tree` | überlebt 10/11, 12.033 € | überlebt 8/11, 5.591 € | **Bankrott 7/11**, −29 € |

Nr. 21 hat den Startanteil gegen ein **Menschen**-Team kalibriert und dort 159 € über 60
Runden gemessen — „spürbar wenig". Das war richtig gemessen und für den falschen Pfad: In
der Messung oben kosten dieselben 15 % das Menschen-Team 117 € (1.401 → 1.284 €) und die
Level-1-Flotte **4.945 €** (9.226 → 4.281 €), also das Zweiundvierzigfache. Vierter Fall des Musters aus Nr. 22, 24 und 35: *eine Regel für einen
Fall formuliert und für einen Sonderfall implementiert.* Sämtliche Investoren-Tests in
`tests/test_office_and_investors.py` besetzen eine Statische Website mit **Menschen** —
dem einzigen Team ohne Tokenrechnung.

**Ausdrücklich nicht hier behoben.** Die naheliegende Auflösung ist eine Zeile
(`net = income - costs_money - costs_tokens * token_price`), aber sie ist keine
Zahlenkorrektur: Sie verbilligt jeden automatisierten Pfad spürbar, und die Begründung des
Docstrings — die Dividende dürfe die Rangfolge zwischen zwei Besetzungen nicht kippen
(`test_full_staffing_beats_every_partial_staffing`) — muss für die neue Bemessungsgrundlage
neu geprüft werden. Als offener Punkt geführt.

## 40. Eine Sperre, die nie greift — und eine Strategie, die nichts misst

```
PYTHONPATH=src python3 tools/simulate.py --guards
```

`Strategy.prudent` lässt eine Politik einen Auftrag ablehnen, dessen vollbesetztes Team
mehr kostet als es einbringt; `humans-greedy` unterscheidet sich von `humans` in nichts
anderem als diesem Schalter und soll laut Docstring „genau das messen". Nachgezählt über
alle Strategien, 11 Seeds, 60 Runden:

| Strategie | Baupläne bewertet | davon abgelehnt |
|---|---:|---:|
| `humans` | 1.408 | **0** |
| `humans+funding` | 632 | 4 |
| `level1-fleet` | 110 | 0 |
| `automation`, `automation+alignment` | je 44 | 0 |
| `full-tree` | 46 | 0 |
| `dangerous-tree` | 98 | 0 |

Und die Ablehnungen, die es gibt, ändern nichts: Dieselbe Politik mit und ohne Sperre
liefert für **alle sieben** Strategien Ausgang, Rundenzahl und Endgeld identisch.
`humans-greedy` ist damit Zeile für Zeile derselbe Lauf wie `humans`.

**Warum:** Die Sperre kann nur dort binden, wo ein volles Team defizitär ist — das sind
nach Nr. 34 die Sprossen mit sieben und acht Stellen, und dort nur für Menschen und für
Stufe-3-Agenten. Kein Plan, der so besetzt ist, kommt jemals so weit: Der Bürodeckel hält
den Menschen-Pfad bei Stufe 4–5 (Nr. 38), und eine hochgerüstete Flotte ist vorher
bankrott (Nr. 28). Wo `humans+funding` die Konzern-Suite doch bewertet, weisen Reserve und
Bürodeckel sie ohnehin zuerst ab. Die Sperre ist also nicht zufällig wirkungslos, sondern
**durch die Bauart des Katalogs unerreichbar**.

Das ist zum vierten Mal das Muster aus Nr. 22, 25 und 29 — *eine Messung misst die Größe,
die sie misst* — diesmal in der Messapparatur selbst statt in einer Schlussfolgerung. Es
ist noch keine falsche Zahl geworden: `humans-greedy` wird in diesem Dokument nirgends
zitiert. Behoben ist der Docstring, der etwas anderes behauptet hat; `--guards` hält die
Prüfung nach, damit die nächste Sprosse nicht wieder unbemerkt daran vorbeiläuft. Die
Sperre selbst bleibt — sie ist die richtige Absicherung für einen Katalog, der Nr. 34
irgendwann anders löst.

## 41. Die Balancing-Regeln prüfen sich jetzt selbst

`tools/simulate.py` misst und behauptet nichts — das ist Absicht und bleibt so. Was
gefehlt hat, ist die andere Hälfte: Die Regeln, die für **jeden** Eintrag in `data/*.json`
gelten müssen, standen ausschließlich als Prosa in diesem Dokument.
`tests/test_balancing.py` macht sie ausführbar, getrennt in zwei Sorten:

**Garantien** — müssen grün bleiben:

- die drei Untergrenzen aus Nr. 33, als Arithmetik über die Registry statt als
  ausgespielte Simulation. `test_full_staffing_beats_every_partial_staffing` prüft
  weiterhin die *Folge*; hier scheitert ein neues `base_income` an der Zeile, die die
  Zahl nennt, die es zu schlagen hat. Die Ein-Stellen-Ausnahme steht als eigener Test
  daneben, statt als Kommentar.
- kein toter Sprosse: jeder Bauplan ist für **mindestens eine** Besetzung profitabel.
- die Leiter ist zyklenfrei und jeder Bauplan von Runde 0 aus erreichbar.
- die Menschen-Wand aus Nr. 34, von beiden Seiten: bis sechs Stellen trägt ein
  Menschen-Team eine Marge, ab sieben zahlt es drauf — und die Aufträge jenseits der Wand
  tragen echte Fixkosten, weil die Untergrenzen den anderen Hebel verbieten.
- `attribute_cap_base <= attribute_start`, sonst wäre der Deckel eine Stellschraube, die
  nichts tut.

**Befunde** — festgenagelt auf ihren heutigen Stand, damit sie rot werden, wenn der
zugehörige offene Punkt gelöst wird. Jeder nennt die Nummer, die darüber entscheidet:
Stufe 3 ist auf allen elf Bauplänen schlechter als Stufe 2 (Nr. 27), und die Dividende
übersteigt auf der obersten Sprosse den Rundengewinn (Nr. 39).

Der Preis dafür ist gering: 53 zusätzliche Tests (51 grün, zwei übersprungen — die beiden
Ein-Stellen-Aufträge, für die die Untergrenzen nichts zu vergleichen haben), 0,2 Sekunden. Der Nutzen ist die
Mutationsprobe — `group_ai_platform.base_income` von 700 auf 640 gesetzt bricht genau den
Untergrenzen-Test für diesen Bauplan, `corporate_suite.basis_fixed_costs` von 205 auf 100
genau den Wand-Test. Beides fiel vorher nur der langsamen Vollsimulation auf, und auch
dort nur als „irgendetwas ist schlechter geworden".
