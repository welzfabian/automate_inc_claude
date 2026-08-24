# M3 — Servicegrad und Instandhaltung

**Status:** ✅ Abgeschlossen
**Geplant:** 24. August 2026
**Abgeschlossen:** 24. August 2026

## Warum

Beim Nachrechnen der Projektmechanik nach M2 kam heraus, dass **ein unbesetztes Projekt
die profitabelste Besetzung ist**. Es bringt Einnahmen (Qualität und Ästhetik starten bei
50) und kostet kein Gehalt. Eine Partie „einen Menschen einstellen, vier Web-Apps starten,
niemanden zuweisen, zwanzig Runden nichts tun" ergibt **+110 €/Runde, dauerhaft, bei
Alignment 100**.

Das unterläuft die Prämisse des Spiels. Wenn Nichtstun profitabel ist, gibt es keinen
Grund zu automatisieren — und damit auch keinen Twist, der greifen könnte.

Die Ursache ist eine fehlende Achse. Die bestehenden Attribute beantworten *wie gut ist
das Ding* (Qualität, Ästhetik), aber nichts beantwortet *existiert es überhaupt schon*.
`BALANCING.md` Nr. 2 hat diese Lücke in M1 mit dem Startwert 50 überbrückt.

Zwei weitere Befunde derselben Rechnung:

- **Die Sales-Stelle zahlt sich nicht.** 60 €/Runde Gehalt für +10 % Sichtbarkeit —
  bei der Kunden-App rund 24 €. Die Stelle leer zu lassen ist besser, als sie zu besetzen.
  Die `+22 €` in der M1-Balancing-Tabelle sind also nicht das Optimum, sondern eine
  Fehlbesetzung.
- **Jedes Projekt bringt gleich viel.** Menschliches Team: +20 €/Runde bei der statischen
  Website wie bei der Web-App. Die Projektwahl ist mechanisch bedeutungslos. Dazu laufen
  große Projekte **kürzer** als kleine (Web-App 12 Runden, statische Website 20) — genau
  invertiert.

## Ziel

Projekte werden zu **Investitionen mit laufender Instandhaltung** statt zu Mietobjekten.
Ein Projekt kostet erst Geld, dann trägt es; und es trägt nur, solange jemand daran
arbeitet. Größere Projekte kosten mehr, laufen länger und bringen deutlich mehr.

Dazu lösen sich die Spielphasen von der Rundenzahl und richten sich nach dem, was der
Spieler tatsächlich getan hat.

## Die Mechanik

### 1. `Project.service_level` — was bekommt der Kunde gerade?

Ein Wert von 0 bis 100, der die Einnahmen skaliert. Startwert **25** („Briefing und
Vertrag stehen"). Pro Runde:

```
besetzt:    progress += 34 × (Σ Effizienz der Zugewiesenen / geforderte Stellen)
unbesetzt:  progress -= 15
```

Voll mit Menschen besetzt also drei bis vier Runden bis zur Fertigstellung, mit
Stufe-3-Agenten zwei. **Der Verfall greift nur bei komplett unbesetzten Projekten** —
Teilbesetzung wird über den Deckel bestraft, nicht über den Fortschritt. Die
anteilige Variante wurde verworfen: Bei drei Stellen und einer Besetzung ergäbe sie
34 × ⅓ − 15 × ⅔ = **+1,3/Runde**, das Projekt bliebe bei 54 % stehen und würde nie
fertig — eine Falle, die der Spieler vorher nicht ablesen kann. Dasselbe
Lesbarkeitsargument wie bei `BALANCING.md` Nr. 8.

### 2. Attribut-Deckel — wie gut *kann* es werden?

Die Besetzung bestimmt, wie hoch ein Attribut überhaupt steigen kann:

```
Deckel = 50 + 50 × besetzte Stellen dieser Rolle / geforderte Stellen
```

Unbesetzt heißt eingefroren bei 50, halb besetzt bis 75, voll besetzt bis 100. Liegt der
Wert über dem Deckel, sinkt er mit **5 pro unbesetzter Stelle und Runde** darauf zu.

Welche Rolle welches Attribut deckelt, steht schon in `roles.json` (`effect.attribute`) —
Entwickler → Qualität, Designer → Ästhetik. Sales deckelt nichts; die Rolle verliert bei
Nichtbesetzung ihren Sichtbarkeitsbonus, das ist ihre Strafe.

Der Basiswert 50 ist gehaltvoller, als er aussieht: Ein Attribut kann nur *sinken*, wenn
niemand die Rolle besetzt — steigen kann es nur durch Worker dieser Rolle. Ein Deckel
über 50 wäre deshalb wirkungslos (der Startwert ist 50), und ab Basis 60 schlägt
Teilbesetzung die volle Besetzung. Der konfigurierbare Bereich ist **0 bis 50**.

### 3. Neue Projektzahlen

| Projekt | Stellen | Laufzeit | `base_income` | Ø netto | gesamt | Kapitalbedarf |
|---------|--------:|---------:|--------------:|--------:|-------:|--------------:|
| Statische Website | 1 | 20 → **10** | 100 → **108** | +20 € | +200 € | −35 € |
| E-Commerce-Shop | 2 | 15 → **16** | 170 → **208** | +44 € | +704 € | −104 € |
| Kunden-App | 3 | 15 → **22** | 220 → **246** | +72 € | +1.584 € | −152 € |
| Web-App mit Backend | 3 | 12 → **22** | 270 → **337** | +72 € | +1.590 € | −134 € |

Zielgröße: **+20 €/Runde pro geforderter Stelle, plus 10 % Bonus je zusätzlicher Stelle.**
Break-even in Runde 3–4.

### 4. Sichtbarkeitsbonus 10 % → 25 %

Damit lohnt sich die Sales-Stelle knapp (+72 gegen +70 €/Runde ohne sie) — eine
Entscheidung statt einer Selbstverständlichkeit.

### 5. Phasen aus dem Zustand statt aus der Rundenzahl

`Phase.for_turn()` weicht einer Liste nach dem Vorbild von `END_CONDITIONS`. Die
Bedingungen fragen **`Modifiers`, nicht Technologie-IDs** — sonst bräche die Regel aus
`CLAUDE.md`, dass Technologien nie im Engine-Code auftauchen:

- **Skalierung**: `unlocked_agent_level ≥ 2` oder mindestens drei Agenten
- **Autonomie**: `unlocked_agent_level ≥ 3` oder Agenten in der Überzahl oder Alignment < 50
- sonst **Aufbau**

Die Phase wird wie bisher bei jedem Zugriff berechnet (`GameState.phase` bleibt eine
`@property`, kein gespeichertes Feld) und **darf zurückfallen**, wenn der Spieler Agenten
entlässt. Dafür braucht es eine eigene Meldung — „Neue Phase: Aufbau" liest sich falsch.

## Was das kostet

- **`BALANCING.md` Nr. 2 wird revidiert.** Die Startwerte 50 bleiben, bekommen aber eine
  neue Begründung: `progress` übernimmt die Rolle, für die sie in M1 herhalten mussten.
- **Save-Format 3**: `Project.progress` kommt dazu.
- **Die M1-Einnahmentests müssen nachgezogen werden** — sie prüfen Beträge, die sich
  verschieben. `test_every_catalog_project_is_profitable_with_humans` bleibt inhaltlich
  gleich, die Zahlen darin nicht.
- **M2 muss nachgeeicht werden.** Eine Kunden-App trägt künftig 1.584 € statt rund 300 €
  über ihre Laufzeit. Forschung wird dadurch deutlich leichter bezahlbar, und der
  Alignment-Druck aus M2 verschiebt sich. Die Technologiekosten steigen voraussichtlich
  auf etwa das Dreifache — **diese Zahl ist zu simulieren, nicht zu raten.**
- Eine Laufzeit von 22 Runden spannt über eine ganze Partie. Wie lang ein Spiel dauern
  soll, wird damit zur offenen Frage.

## Konfiguration

Die neuen Stellschrauben (`progress`-Aufbau, Verfall, Startwert, Deckel-Basis, Entropie)
gehören nach `data/projects.json` als Block auf oberster Ebene — Balancing-Zahlen stehen
nie im Code. Ein späterer Override je Projekt bleibt damit offen.

## Ergebnis

Umgesetzt wie geplant, mit zwei Abweichungen, die erst die Simulation gezeigt hat.

**Die Technologiekosten wurden nicht erhöht.** Der Plan sagte „voraussichtlich das
Dreifache" — mit dem Vermerk, dass die Zahl zu simulieren und nicht zu raten sei. Genau
das hat sie widerlegt: Geld ist in keiner Partie der Engpass, die Forschungsgeschwindigkeit
hängt fast ausschließlich an der Forscherzahl. Bei den bestehenden Kosten liegt Stufe 2 bei
Runde 7–10 und Stufe 3 bei Runde 17–23 — ein brauchbarer Bogen. Eine Verdreifachung hätte
Stufe 2 auf Runde 41 geschoben. Der eigentliche Befund ist ein anderer und steht in
[BALANCING.md](../BALANCING.md): **es fehlt eine Geldsenke.**

**Die Autonomie-Schwelle wurde angehoben.** „Agenten in der Überzahl" ließ die Phase in
Runde 0 auf Autonomie springen, sobald drei Agenten neben einem Gründer standen. Jetzt
braucht es sechs — doppelt so viele wie für die Skalierung.

Die Balancing-Entscheidungen im Einzelnen stehen als **Nr. 11–15 in
[BALANCING.md](../BALANCING.md)**; Nr. 2 aus M1 wurde dort revidiert statt gelöscht.

## Testlage

**128 Tests grün** (107 vorher, 21 neu), davon in `tests/test_progress.py`:

- Ein unbesetztes Projekt fällt auf 0 % und verdient nichts — der Test, der das ganze
  Loch abdeckt.
- **Volle Besetzung schlägt jede Teilbesetzung**, über alle vier Projekte und alle
  Kombinationen parametrisiert. Das ist die Eigenschaft, an der die Mechanik hängt.
- Deckel bei 100 / 75 / 50 je nach Besetzung; der Verfall ist schrittweise, nicht abrupt.
- Teilbesetzung wird trotzdem irgendwann fertig — kein Stillstand.
- Agenten bauen schneller als Menschen.
- Große Projekte bringen mehr **und** laufen länger.

Die Phasen-Tests aus M1 (`Phase.for_turn`) wurden durch acht neue ersetzt, die die
Zustandsbedingungen prüfen, inklusive Rückfall.

## Offene Fragen

- **Kunden-App und Web-App haben beide drei Stellen** und werden dadurch wirtschaftlich
  identisch, weil die Zielgröße nur an der Stellenzahl hängt. Eine der beiden braucht eine
  vierte Stelle oder eine andere Laufzeit.
- **Drei von dreizehn Teilbesetzungen bleiben Verlustgeschäfte** (nur Sales; Entwickler
  plus Sales ohne Designer; zwei Entwickler statt des fehlenden Designers). Alle drei sind
  „Gehalt für eine blockierte Aufstellung", in der Oberfläche ablesbar und mit einer
  Aktion behebbar. Bewusst so gelassen — jede Gegenmaßnahme kippt das Verhältnis zur
  vollen Besetzung.
- Was passiert mit einem Projekt, das bei Ablauf nie fertig wurde? Heute nichts.
  Naheliegender Anknüpfungspunkt für die Zufallsereignisse (M4).
- **Es fehlt eine Geldsenke.** Der Spieler endet mit über 30.000 € und keiner knappen
  Runde. Das ist der größte offene Balancing-Punkt nach M3.

## Reihenfolge

1. `Project.progress` + Einnahmenformel + Save-Format 3
2. Attribut-Deckel und Entropie in `economy.py`
3. Neue Zahlen in `projects.json` (Laufzeiten, `base_income`, Tuning-Block), Sichtbarkeit 25 %
4. Phasen aus `Modifiers`
5. Technologiekosten neu eichen (simuliert, nicht geraten)
6. UI: Fortschrittsbalken, Deckel-Anzeige („Qualität max. 75 %"), Phasenmeldung
7. Doku: `BALANCING.md` Nr. 2 revidiert, Nr. 11 ff. neu, dieses Dokument, README

## Nicht Teil von M3

Zufallsereignisse (M4), Produkte und Upgrades, HR-Rolle, der Twist.
