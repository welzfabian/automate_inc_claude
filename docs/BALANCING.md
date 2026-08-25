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

## 22. Die beiden neuen Enden führen keinen eigenen Schwellenwert ein

`_total_automation` (0 Menschen, Agentenflotte ≥ `AUTONOMY_AGENT_COUNT`) und die Aufteilung
in "Dystopie" gegen "Geheimes Ende" bei `ALIGNMENT_TIERS[0]` (80.0) verwenden ausschließlich
Konstanten, die schon vor M7 kalibriert waren: `AUTONOMY_AGENT_COUNT = 6` bestimmt seit M1/M2
die Autonomie-Phase (`GameState.phase()`), und `ALIGNMENT_TIERS[0]` ist die Schwelle, unter
der `ALIGNMENT_WARNINGS` überhaupt zum ersten Mal etwas anzeigt. M7 führt deshalb keine neue
Elf-Seeds-Simulation wie M2–M4 — es gibt keine neue Zahl zu kalibrieren, nur eine neue
Kombination zweier bestehender. Wie M5 (Eintrag 20) für seine beiden optionalen Mechaniken
begründet: Ein Abgleich gegen die bereits belegten Größenordnungen genügt, wenn der Eingriff
selbst keine neuen Parameter mitbringt.

**Worauf das Ergebnis empfindlich reagiert und worauf nicht:** Da `_total_automation`
`AUTONOMY_AGENT_COUNT` unverändert wiederverwendet, tritt eines der beiden neuen Enden nie
früher ein als die Autonomie-Phase selbst schon erreichbar ist (siehe M2s Simulation:
Runde 7–10 für Stufe 2, 17–23 für Stufe 3) — ein Vollautomatisierungs-Ende vor Runde ~7 ist
mit der aktuellen Fleet-Ökonomie nicht erreichbar. Die Aufteilung bei Alignment 80 ist streng
deterministisch (kein RNG, BALANCING.md 8) und bewusst *nicht* symmetrisch gewählt: Da Level-2-
Agenten schon −1/Runde und Level-3-Agenten −3/Runde kosten (Nr. 7), braucht eine Sechs-Agenten-
Flotte aktives Gegensteuern (Menschen, `ai_alignment`-Forschung, das neue
`full_automation_warning`), um überhaupt bei ≥ 80 anzukommen — das "Geheime Ende" ist damit die
seltenere, nicht die leichtere der beiden Varianten.

## 23. `full_automation_warning` bleibt ein ehrliches Angebot, keine Blockade

Die Vorwarnung (6 Agenten, höchstens 1 Mensch) kostet in der teureren Option 200 € für
+3 Alignment, in der billigeren −3 Alignment für nichts — bewusst kleiner dimensioniert als
`ai_ethics_debate` (300 € / ±5, Nr. siehe `data/events.json`), weil das Ereignis nur einmal pro
Partie feuern kann (`once: true`) und rein als Vorbote gedacht ist, nicht als Stellschraube.
Keine der beiden Optionen verändert Personal oder verhindert die Enden — wer danach trotzdem
den letzten Menschen feuert, bekommt eines der beiden neuen Enden wie vorgesehen. Nicht separat
simuliert: Der Effekt ist zu klein, um die Alignment-Schwelle 80 in der Praxis zu verschieben
(±3 gegen einen laufenden Verfall von −1 bis −3/Runde bei sechs Agenten).
