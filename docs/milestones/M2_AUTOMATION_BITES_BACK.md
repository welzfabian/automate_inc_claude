# M2 — Automatisierung beißt zurück

**Status:** 🔄 in Arbeit
**Geplant:** 24. August 2026
**Abgeschlossen:** —

## Ziel

M1 hat ein spielbares, aber harmloses Spiel geliefert. Agenten der Stufe 1 haben
definitionsgemäß keine Nebeneffekte, `alignment` steht unbewegt auf 100, `Project.bugs`
wird in der Einnahmenformel gelesen, aber von nichts erhöht, und Research Points sammeln
sich an, ohne dass man sie ausgeben kann — der Forscher ist in M1 eine reine Kostenfalle.

M2 schließt diesen Kreis mit drei Systemen, die einzeln wenig und zusammen viel ergeben:

1. **Forschung** gibt Research Points eine Funktion (`core/tech.py`, `data/technologies.json`)
2. **Agenten-Stufen 2 und 3** werden dadurch freigeschaltet — deutlich effizienter,
   aber mit Nebeneffekten (Bugs, Klagen, generisch werdende Designs)
3. **Alignment** wird zur lebenden Mechanik: es sinkt durch Agenten, steigt durch
   Menschen und Technologie, und beendet unter 20 das Spiel

Der Spieler soll zum ersten Mal spüren, dass Automatisierung einen Preis hat, ohne schon
entmachtet zu werden. **Die Entmachtung ist der Twist und bleibt für M3+ reserviert.**

## Abgestimmte Entscheidungen

- Alignment wirkt nur **weich**: Ton, Nachfragen, Warnungen. Jede Spieleraktion wird
  weiterhin ausgeführt.
- **Keine HR-Rolle** in M2.
- Der Tech-Tree deckt **alle vier Kategorien** ab: Stufen-Freischaltung,
  Nebeneffekt-Dämpfer, Wirtschafts-Techs, gefährliche Techs.
- Die gefährlichen Technologien sind sichtbar und erforschbar, aber **noch ohne
  Twist-Folgen** — sie sind die Verlockung, die M3 einlöst.

## Ausdrücklich nicht Teil von M2

Produkte und Upgrades, Projekt→Produkt-Konvertierung, externe Druckereignisse, die
HR-Rolle, der Twist selbst. Ebenfalls nicht: `ruff` zum Laufen bringen, CI, die
fehlenden Projekttypen (Enterprise-Software, KI-Integration) in `projects.json`.

## Neue Design-Entscheidungen

Drei weitere Widersprüche zwischen den Spec-Dokumenten mussten aufgelöst werden; sie
stehen als **Nr. 7–9 in [BALANCING.md](../BALANCING.md)** und werden hier nicht
wiederholt. Kurzform: Alignment-Decay hängt nur an der Agenten-Stufe, es gibt keinen
zufälligen Basis-Decay, und Menschen geben +1 statt +5 Alignment pro Runde.

## Ergebnis

*Wird beim Abschluss ergänzt.*

## Testlage

*Wird beim Abschluss ergänzt.*
