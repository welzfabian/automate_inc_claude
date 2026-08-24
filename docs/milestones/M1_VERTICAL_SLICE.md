# M1 — Spielbarer Vertical Slice

> **Status:** ✅ Abgeschlossen
> **Abgeschlossen:** 24. August 2026
> **Commits:** `77cdfd1` … `ad417d8` (11 Commits nach dem Initial Commit)
> **Umfang:** ~1.870 Zeilen Python, 39 Tests

---

## 1. Ziel

Eine **End-to-End spielbare Runden-Schleife** — bewusst nicht die vollständige Spec.
Ressourcen verwalten, Worker einstellen, Projekte starten und besetzen, Runde
abrechnen, pleitegehen. Begründung: Das Balancing ist bei diesem Spiel die eigentliche
Herausforderung, weil der Twist voraussetzt, dass Agenten sich *zunächst* wirtschaftlich
lohnen. Das lässt sich erst beurteilen, wenn man das Spiel spielen kann.

**Vorgaben aus der Planung:** Python + [Rich](https://rich.readthedocs.io),
menügesteuert · Spielertexte Deutsch, Code-Bezeichner Englisch · Balancing in
`data/*.json` · Save/Load als JSON · Tests mit pytest.

## 2. Was entstanden ist

| Bereich | Ergebnis |
|---------|----------|
| **Ressourcen** | Geld, Tokens mit schwankendem Tagespreis, Research Points, Alignment |
| **Worker** | Menschen und Agenten (Stufe 1) in vier Rollen: Entwickler, Designer, Sales, Forscher |
| **Projekte** | Vier Typen aus [`data/projects.json`](../../src/automate_inc/data/projects.json), Lebensdauer, Qualität/Ästhetik/Bugs |
| **Rundenabrechnung** | Worker-Effekte → Nebeneffekte → Einnahmen → Kosten → Verrechnung → Tokenpreis → Lebenszyklen → Ende-Prüfung |
| **Token-Markt** | Manueller Kauf, automatischer Nachkauf bei Unterdeckung, Preisschwankung ±10 % mit Inflationsdrift |
| **Speichern/Laden** | Versioniertes JSON, lesbar und diffbar (kein `pickle`) |
| **Enden** | Bankrott. Weitere Enden hängen sich an `END_CONDITIONS` an |
| **Oberfläche** | Rich-Dashboard (Kopfzeile, Projekte, Team, Ereignis-Log) und Menüschleife |
| **Start** | [`start_game.sh`](../../start_game.sh) — legt beim ersten Start `.venv/` an |

### Architektur-Entscheidung mit Folgen

`core/` kennt weder Rich noch `input()`. Jede Aktion gibt ein `ActionResult` zurück,
jede Runde einen `TurnReport`; die UI rendert nur. **Das ist die Naht für den Twist:**
Die KI kann später Aktionen abfangen, blockieren oder ihr Ergebnis fälschen, ohne dass
die Oberfläche den Unterschied bemerkt — genau das Verhalten, das
[VISION.md](../VISION.md) unter „Subtile Manipulation" beschreibt.

Zweite Entscheidung mit Folgen: **Der Zufall wird aus Seed und Rundennummer
abgeleitet** (`random.Random(f"{seed}:{turn}")`) statt als lebender Generator
mitgeführt. Dadurch rechnet ein geladener Spielstand die nächste Runde exakt so ab wie
der ursprüngliche Durchlauf — und Tests sind ohne Mocking reproduzierbar.

## 3. Was unterwegs geändert werden musste

Die Design-Dokumente waren an **sechs Stellen nicht implementierbar**. Alle Auflösungen
mit Begründung stehen in **[BALANCING.md](../BALANCING.md)**; hier nur die Kurzfassung:

| # | Problem | Auflösung |
|---|---------|-----------|
| 1 | Projektstart verlangt Worker der Stufe 2+, die es in Runde 0 nicht geben kann | Menschen zählen immer als Stufe 2 |
| 2 | Einnahmenformel nullt jedes Projekt ohne Designer | Nicht angeforderte Attribute sind neutral; Projekte starten bei 50 statt 0 |
| 3 | Kein Weg, Tokens nachzukaufen | Kauf-Aktion + automatischer Nachkauf bei Unterdeckung |
| 4 | Projekt-Tabelle in GAME_DESIGN.md 3.2 war strukturell kaputt | Tabelle korrigiert, SPEC 3.2 als Referenz |
| 5 | **Jede** Besetzung war defizitär: Statische Website 50 €/Runde, der dafür nötige Entwickler 80 €/Runde | Projekteinnahmen auf die VISION-Vorgabe angehoben (Website jetzt 100 €), Agentenkosten auf 2–3 Tokens gesenkt |
| 6 | Unklar, ob unbeschäftigte Worker kosten | Ja — Gehaltsabrechnung läuft weiter |

**Nummer 5 war der kritische Punkt.** Ohne diese Korrektur hätte das Spiel keinen
gewinnbaren Zustand gehabt. Zielvorgabe war die Notiz aus [VISION.md](../VISION.md):
*Menschen machen kleinen Gewinn, Agenten machen großen Gewinn.*

### Zusätzlich behoben

- **Endlosschleife bei EOF** (`ad417d8`): Schloss stdin, gab `ask()` ersatzweise `"q"`
  zurück, die Rückfrage „Wirklich beenden?" bekam wieder EOF, die Antwort war nicht
  `j` — und die Schleife begann von vorn. Der Prozess war nur per Kill zu beenden.
  EOF bricht jetzt über eine `Abort`-Exception sauber ab.
- **Dokumentation der Abweichungen** (`dfc7ed9`): [BALANCING.md](../BALANCING.md) neu,
  Projekt-Tabelle in GAME_DESIGN.md 3.2 repariert.

## 4. Nachweis, dass es funktioniert

**39 Tests**, `PYTHONPATH=src python3 -m pytest`:

| Datei | Prüft |
|-------|-------|
| `test_economy.py` | Rechenbeispiele aus SPEC 6.1 (194,40 € / 247,00 €), Neutralitätsregel, Kostentrennung €/Tokens, Tokenpreis-Korridor |
| `test_projects.py` | Registry lädt Katalog, Stufe-2-Regel, Rollen-Slots, Profitabilität jedes Projekts mit rein menschlichem Team |
| `test_turn.py` | Attribut-Deckelung bei 100, Projektablauf, Token-Autokauf, Bankrott, Phasenwechsel, Determinismus |
| `test_state.py` | JSON-Round-Trip, geladener Stand rechnet identisch weiter, keine ID-Kollisionen nach dem Laden |

**Gespielter Durchlauf über 12 Runden** (Seed 2024, E-Commerce-Shop, in Runde 5 wird
der menschliche Designer durch einen Agenten ersetzt):

```
Runde  0   Bilanz  -72,65 €   (Qualität und Ästhetik fahren erst hoch)
Runde  3   Bilanz  +20,00 €   rein menschliches Team
Runde  4   Bilanz  +20,00 €
  -> Designer durch Agenten ersetzt
Runde  5   Bilanz  +90,00 €   ein einziger Agent vervierfacht den Gewinn
Runde 11   Bilanz  +90,00 €
```

Das ist die beabsichtigte Kurve: Menschen tragen sich knapp, Agenten lohnen sich
*offensichtlich*. Ohne dieses Gefälle hätte der Twist in M2+ keine Wirkung.

## 5. Bewusst nicht enthalten

Produkte, Upgrades und die Konvertierung Projekt → Produkt · Tech-Tree und Verwendung
der Research Points · Agenten-Stufen 2 und 3 samt Nebeneffekten · HR-Rolle · externe
Druckereignisse (Investoren, Privatleben, Markt) · Alignment-Verfall · **der Twist
selbst**.

Das Alignment wird bereits angezeigt und gespeichert, verändert sich in M1 aber nicht —
es gibt noch keine Quelle für Verfall.

## 6. Bekannte Schwächen für die nächste Runde

- **Forscher sind aktuell eine Falle.** Sie kosten 90 €/Runde und produzieren Research
  Points, für die es noch keine Verwendung gibt. Löst sich mit dem Tech-Tree.
- **Kein Lint in der Pipeline.** `ruff` ist in `pyproject.toml` konfiguriert, war lokal
  aber nicht installiert und lief daher nie. CI wurde bei der Planung abgewählt.
- **Menschliche Fehler sind praktisch unsichtbar** (0,2–1 % Chance pro Runde). Das ist
  so gewollt, macht den Code-Pfad aber schwer im Spiel zu beobachten; getestet ist er
  nur indirekt.
- **Projektkatalog ist klein.** Enterprise-Software und KI-Integration sind in
  GAME_DESIGN.md beschrieben, aber noch nicht in `projects.json`.
