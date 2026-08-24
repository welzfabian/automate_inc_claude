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
