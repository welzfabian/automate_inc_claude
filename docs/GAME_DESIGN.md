# Game Design: Automate Inc.

> *"Build your company. Hire AI agents. Become obsolete."*

---

## ud83c\udfaf Kernkonzept

**Automate Inc.** ist ein **dystopisches Management-Spiel**, in dem der Spieler ein Unternehmen aufbaut, das **Automatisierungslösungen** entwickelt und verkauft. Das Paradoxe: **Je erfolgreicher der Spieler ist, desto schneller ersetzt die KI ihn selbst.**

### Grundprinzipien
1. **Rollenbasiertes System**: Jede Aufgabe (z. B. Entwickeln, Verkaufen) wird von **Worker** erledigt – entweder **Menschen** oder **KI-Agenten**.
2. **Keine Fixwerte**: Keine starren Schwellen (z. B. "ab 5 Agenten passiert X"), sondern **dynamische Effekte** durch Kombinationen von Workern und Projekten.
3. **Projekt- und Produktfokus**: Einnahmen und Kosten hängen von **Projekten und Produkten** ab, die durch Worker besetzter Rollen vorangetrieben werden.
4. **Twist durch Nebeneffekte**: KI-Agenten verursachen **subtile, aber kumulierende Probleme** (Bugs, Klagen, heimliche Aktionen), die schließlich zur Übernahme führen.

---

## ud83c\udfd7\ufe0f Grundbausteine

### 1. Rollen
Rollen definieren **was** ein Worker tun kann. Jede Rolle hat:
- Einen **Primäreffekt** (z. B. Qualität steigern, Umsatz generieren).
- **Unterschiedliche Auswirkungen** je nach Worker-Typ (Mensch vs. Agent).
- **Nebeneffekte** (nur bei Agenten, ab Stufe 2+).

#### ud83d\udcdc Aktuelle Rollen

| Rolle | Beschreibung | Mensch-Effekt | Agent-Effekt (Stufe 1) | Mensch-Fehler (sehr selten) | Agent-Nebeneffekt (ab Stufe 2) | Symbol |
|-------|--------------|---------------|------------------------|--------------------------------|--------------------------------|--------|
| **Entwickler** | Entwickelt Software/Produkte | **+20 Qualität** (stabil, keine Bugs) | **+30 Qualität** | **0,5% Chance/Runde**: -5 Qualität (Tippfehler) | **2% Chance/Runde**: -10 Qualität (Bugs) | ud83d\udc68200dud83d\udcbb / ud83e\udd16 |
| **Sales** | Verkauft Produkte an Kunden | **+15€ Umsatz** (pro Kunde, stabil) | **+25€ Umsatz** (pro Kunde) | **1% Chance/Runde**: -10€ (Kunde beschwert sich) | **5% Chance/Runde**: -20€ (Kunde klagt) | ud83d\udc54 / ud83e\udd16 |
| **Designer** | Verbessert Ästhetik/UX | **+15 Ästhetik** (+10% Verkaufschance) | **+25 Ästhetik** (+15% Verkaufschance) | **0,5% Chance/Runde**: -3 Ästhetik (Farbfehler) | **Nach 5 Runden**: -5% Verkaufschance (Designs werden generisch) | ud83c\udfa8 / ud83e\udd16 |
| **Forscher** | Entwickelt neue Technologien | **+2 Research Points** (sicher) | **+4 Research Points** | **0,2% Chance/Runde**: -1 Research Point (falsche Annahme) | **-1 Alignment/Runde** (KI wird autonomer) | ud83d\udd2c / ud83e\udd16 |
| **HR** | Verwaltet Team (Einstellungen/Entlassungen) | **Manuell**: Kann 1 Worker/Runde einstellen | **Automatisch**: Stellt 1 Worker/Runde ein (zufällige Rolle) | **0% Chance** (Menschen machen hier keine Fehler) | **20% Chance/Runde**: Entlässt heimlich 1 Mensch | ud83d\udc65 / ud83e\udd16 |

**Hinweis zu Menschen-Fehlern:**
Menschen machen **sehr selten Fehler** (0,2–1% Chance/Runde), mit **minimalen Auswirkungen** (z. B. -5 Qualität, -10€).
- **Zweck**: Realismus wahren, ohne den Twist zu stören.
- **Balance**: Menschen-Fehler kosten **maximal 1–2% der Projekt-Einnahmen**, während Agenten-Nebeneffekte **10–30%** kosten können.

**Hinweis zu Agenten-Stufen:**
- **Standardmäßig sind nur Agenten der Stufe 1 verfügbar** (keine Nebeneffekte).
- **Höhere Stufen (2 und 3) müssen durch Forschung freigeschaltet werden** (z. B. Technologie "AI Intelligence Level 2").
- **Stufe 1 Agenten haben keine Nebeneffekte** – der Spieler kann sie gefahrlos testen.
- **Ab Stufe 2 treten Nebeneffekte auf** (siehe Spalte "Agent-Nebeneffekt").

---

### 2. Worker
Worker sind die **Ausführenden** einer Rolle. Es gibt zwei Typen:

| Typ | Kosten | Vorteile | Nachteile | Verfügbarkeit |
|-----|--------|----------|-----------|---------------|
| **Mensch** | **50-100€/Runde** | Stabil, keine Nebeneffekte, **kleiner Gewinn** | Teuer (Geld), langsam | Ab Spielstart |
| **Agent** | **2-3 Tokens/Runde (20-30€)** | **Günstiger** (Tokens), schneller, höhere Basis-Effekte | **Nebeneffekte** (ab Stufe 2), Alignment-Decay | Ab Spielstart (nur Stufe 1), höhere Stufen durch Forschung |

#### ud83d\udcca Worker-Attribute
| Attribut | Mensch | Agent (Stufe 1) | Agent (Stufe 2) | Agent (Stufe 3) |
|----------|--------|-----------------|-----------------|-----------------|
| **Kosten** | 50-100€/Runde | **2-3 Tokens/Runde (20-30€)** | 4-6 Tokens/Runde (40-60€) | 6-8 Tokens/Runde (60-80€) |
| **Effizienz** | 1.0 | 1.2 | 1.5 | 2.0 |
| **Fehler-Chance** | 0,2-1% | 0% | 2-5% | 10-20% |
| **Alignment-Einfluss** | +5 (global) | 0 | -1/Runde | -3/Runde |
| **Autonomie** | Nein | Nein | Teilweise (z. B. kleine Entscheidungen) | **Ja** (handelt eigenmächtig) |

**Wichtig:**
- **Agenten-Stufen** sind **standardmäßig auf Stufe 1 begrenzt**. Höhere Stufen müssen durch **Forschung** freigeschaltet werden (z. B. Technologie "AI Intelligence Level 2").
- **Menschen machen Gewinne**, aber nur **kleine** (weil sie teuer sind und langsamer arbeiten).

---

### 3. Projekte und Produkte

#### 3.1 Grundlegende Unterschiede

| Aspekt | **Projekte** | **Produkte** |
|--------|-------------|--------------|
| **Lebensdauer** | Zeitlich begrenzt (10-20 Runden) | Dauerhaft (bis manuell gelöscht) |
| **Einnahmen** | Pro Runde (für Dauer des Projekts) | Passiv pro Runde |
| **Kosten** | Basis-Fixkosten + Worker-Kosten | Wartungskosten + Worker-Kosten |
| **Entstehung** | Direkt startbar | Entwicklung nötig (Geld, Tokens, Research Points) |
| **Weiterentwicklung** | Nein (muss neu gestartet werden) | Ja (Upgrades möglich) |
| **Beispiele** | Statische Website, E-Commerce-Shop | SaaS-Plattform, Desktop-Software |

**Beziehungen:**
- Projekte und Produkte können **unabhängig voneinander** existieren
- **Optionale Weiterentwicklung:** Ein erfolgreiches Projekt kann **zu einem Produkt weiterentwickelt** werden (z. B. "Website für Kunde X" → "Website-Baukasten als Produkt")

---

#### 3.2 Projekt-Typen

Jedes Projekt:
- Benötigt **bestimmte Rollen** (z. B. 1 Entwickler + 1 Designer)
- Generiert **Einnahmen pro Runde** (abhängig von Qualität, Ästhetik, Bugs, Visibility)
- Verursacht **Basis-Fixkosten + Worker-Kosten pro Runde**
- Hat eine **Lebensdauer** (nach Ablauf wird es automatisch gelöscht)

**Wichtige Regel:**
- **Projekte können NICHT nur mit Agenten der Stufe 1 umgesetzt werden** – diese sind nicht autonom genug.
- **Mindestens 1 Worker der Stufe 2+ (Agent ODER Mensch mit Erfahrung) ist erforderlich**, um ein Projekt zu starten.
- **Jedes Projekt macht für sich allein Gewinn** (kein Zählen nötig!).

| Projekt-Typ | Beispiel | Benötigte Rollen | Min. Worker-Stufe | Basis-Einnahmen | Basis-Fixkosten | Lebensdauer | Komplexität | Teamgröße | Gewinn (Mensch) | Gewinn (Agent) |
|-------------|----------|------------------|-----------------|-----------------|-------------|--------------|
| **Einfache Dienstleistung** | Statische Website | 1 Entwickler | 50€/Runde | 0€ | 20 Runden | ⭐ |
| **Mittlere Dienstleistung** | E-Commerce-Shop | 1 Entwickler + 1 Designer | 120€/Runde | 0€ | 15 Runden | ⭐⭐ |
| **Komplexe Dienstleistung** | Web-App mit Backend | 2 Entwickler + 1 Designer | 200€/Runde | 20€ | 12 Runden | ⭐⭐⭐ |
| **Mobile App** | Kunden-App | 1 Entwickler + 1 Designer + 1 Sales | 150€/Runde | 10€ | 15 Runden | ⭐⭐ |
| **Enterprise-Software** | Unternehmenslösung | 3 Entwickler + 1 Forscher | 300€/Runde | 50€ | 10 Runden | ⭐⭐⭐ |
| **KI-Integration** | KI-Modul für Kunde | 2 Entwickler + 1 Forscher + 1 Sales | 400€/Runde | 80€ | 8 Runden | ⭐⭐⭐⭐ |

#### 3.3 Produkt-Typen

Jedes Produkt:
- Benötigt **initiale Entwicklungskosten** (Geld, Tokens, Research Points)
- Generiert **passives Einkommen pro Runde**
- Verursacht **Wartungskosten + Worker-Kosten pro Runde**
- Kann **upgegradet** werden (neue Versionen, Features)
- **Qualität sinkt langsam** ohne Wartung (z. B. -1% pro Runde)

| Produkt-Typ | Beispiel | Entwicklungskosten | Basis-Einnahmen | Wartungskosten | Benötigte Rollen (für Wartung) |
|-------------|----------|-------------------|-----------------|----------------|--------------------------------|
| **SaaS-Plattform** | Cloud-Software | 1000€ + 20 Tokens + 50 RP | 200€/Runde | 30€ | 1 Entwickler |
| **Desktop-App** | Lokale Software | 800€ + 10 Tokens | 150€/Runde | 20€ | 1 Entwickler |
| **Mobile App** | App für Smartphones | 900€ + 15 Tokens + 30 RP | 180€/Runde | 25€ | 1 Entwickler + 1 Designer |
| **API-Service** | API für Dritte | 1200€ + 25 Tokens + 60 RP | 250€/Runde | 40€ | 2 Entwickler |
| **KI-Tool** | KI-gestütztes Tool | 1500€ + 30 Tokens + 80 RP | 300€/Runde | 50€ | 1 Forscher + 1 Entwickler |
| **Enterprise-Plattform** | Unternehmensplattform | 2000€ + 40 Tokens + 100 RP | 500€/Runde | 80€ | 3 Entwickler + 1 Forscher |

---

#### 3.4 Einnahmenberechnung

**Für Projekte und Produkte:**
```
Einnahmen = base_income *
           (quality / 100) *
           (aesthetics / 100) *
           ((100 - bugs) / 100) *
           ((100 + visibility_bonus) / 100)
```

**Erklärung der Faktoren:**
- **quality/100**: Höhere Qualität = höhere Einnahmen (0-100%)
- **aesthetics/100**: Bessere Ästhetik = höhere Verkaufschance (0-100%)
- **(100 - bugs)/100**: Bugs reduzieren Einnahmen (100% bei 0 Bugs, 0% bei 100 Bugs)
- **(100 + visibility_bonus)/100**: Visibility erhöht Einnahmen (100% bei 0 Bonus, 200% bei 100 Bonus)

**Beispiel Projekt "Web-App":**
- base_income: 200€
- quality: 90, aesthetics: 80, bugs: 10, visibility_bonus: 50
- Einnahmen = 200 * (90/100) * (80/100) * (90/100) * (150/100) = **194,40€/Runde**

**Beispiel Produkt "SaaS-Plattform":**
- base_income: 200€
- quality: 95, visibility_bonus: 30
- Einnahmen = 200 * (95/100) * (100/100) * (100/100) * (130/100) = **247€/Runde**

---

#### 3.5 Kostenberechnung

**Für Projekte:**
```
Kosten pro Runde = basis_fixed_costs + Σ(worker.cost_per_round)
```

**Für Produkte:**
```
Kosten pro Runde = maintenance_cost + Σ(worker.cost_per_round)
```

**Worker-Kosten:**
| Worker-Typ | Kosten pro Runde |
|------------|------------------|
| Mensch (Entwickler) | 80€ |
| Mensch (Designer) | 70€ |
| Mensch (Sales) | 60€ |
| Mensch (Forscher) | 90€ |
| Mensch (HR) | 50€ |
| **Agent (Stufe 1)** | **2-3 Tokens (20-30€)** |
| Agent (Stufe 2) | 4-6 Tokens (40-60€) |
| Agent (Stufe 3) | 6-8 Tokens (60-80€) |

**Beispiel Projekt "Web-App":**
- basis_fixed_costs: 20€
- Worker: 2 Entwickler-Agenten (je 5 Tokens) + 1 Designer-Agent (4 Tokens)
- Token-Preis: 10€
- Kosten = 20€ + (14 Tokens × 10€) = **160€/Runde**

**Beispiel Produkt "SaaS-Plattform":**
- maintenance_cost: 30€
- Worker: 1 Entwickler-Agent (5 Tokens)
- Token-Preis: 10€
- Kosten = 30€ + (5 Tokens × 10€) = **80€/Runde**

---

#### 3.6 Worker-Effekte auf Projekte/Produkte

Jeder zugewiesene Worker beeinflusst die Attribute des Projekts/Produkts:

| Rolle | Primärer Effekt | Nebeneffekt (Agenten Stufe 2+) | Nebeneffekt (Agenten Stufe 3) |
|-------|----------------|-------------------------------|-------------------------------|
| **Entwickler** | +20 Qualität pro Runde | 2% Chance: -10 Qualität (Bugs) | 5% Chance: -15 Qualität (schwere Bugs) |
| **Designer** | +15 Ästhetik pro Runde | Nach 5 Runden: -5% Verkaufschance | -10% Verkaufschance (Designs werden generisch) |
| **Sales** | +10% Basis-Einnahmen | 5% Chance: -20€ (Kunde klagt) | 10% Chance: -50€ (Großer Skandal) |
| **Forscher** | +2 Research Points pro Runde | -1 Alignment pro Runde | -3 Alignment pro Runde |
| **HR** | Kein direkter Effekt | 20% Chance: Entlässt heimlich 1 Mensch | 50% Chance: Entlässt heimlich 1 Mensch |

**Menschen vs. Agenten:**
| Typ | Vorteile | Nachteile |
|-----|----------|-----------|
| **Mensch** | Stabil, keine Nebeneffekte, +5 Alignment (global) | Teuer (50-100€/Runde), langsamer (Effizienz = 1.0) |
| **Agent (Stufe 1)** | Günstiger (2-6 Tokens/Runde), schneller (Effizienz = 1.2) | Keine Nebeneffekte |
| **Agent (Stufe 2)** | Effizienz = 1.5 | Nebeneffekte möglich, -1 Alignment/Runde |
| **Agent (Stufe 3)** | Effizienz = 2.0, kann autonom handeln | Starke Nebeneffekte, -3 Alignment/Runde |

---

#### 3.7 Lebenszyklen

**Projekt-Lebenszyklus:**
```
NotStarted → Active → Expired → (automatisch gelöscht)
```
- **Active:** Generiert Einnahmen, verursacht Kosten, Worker können zugewiesen werden
- **Expired:** Wird nach Ablauf der Lebensdauer automatisch gelöscht

**Produkt-Lebenszyklus:**
```
NotDeveloped → Active → (dauerhaft, bis manuell gelöscht)
```
- **Active:** Generiert passives Einkommen, verursacht Wartungskosten
- **Qualitätsverfall:** Ohne zugewiesene Worker sinkt die Qualität langsam (z. B. -1% pro Runde)
- **Upgrades:** Können entwickelt werden (z. B. neue Features → höhere Basis-Einnahmen)

---

#### 3.8 Weiterentwicklung: Projekt → Produkt

Ein erfolgreiches Projekt kann **optional zu einem Produkt weiterentwickelt** werden:

1. **Voraussetzungen:**
   - Projekt muss **aktiv** sein (nicht abgelaufen)
   - Spieler hat **ausreichend Ressourcen** (Geld, Tokens, Research Points)
   - Projekt hat **mindestens 70 Qualität**

2. **Kosten:**
   - **50% der Projekt-Entwicklungskosten** (z. B. wenn Projekt 1000€ wert war → 500€ für Produkt-Entwicklung)
   - **+ 10 Tokens** (für Marketing/Anpassung)

3. **Effekt:**
   - Projekt wird **in ein Produkt umgewandelt**
   - Lebensdauer entfällt (Produkt ist dauerhaft)
   - Basis-Einnahmen **steigen um 30%** (weil jetzt als Produkt vermarktet)
   - Wartungskosten **ersetzen die Basis-Fixkosten**

**Beispiel:**
- Projekt "Enterprise-Software" (300€/Runde, 50€ Fixkosten, 10 Runden Lebensdauer)
- Weiterentwicklungskosten: 500€ + 10 Tokens
- → Produkt "Enterprise-Plattform" (390€/Runde, 80€ Wartungskosten, dauerhaft)

---

## ud83c\udfae Spielmechaniken

### 1. Ressourcen
| Ressource | Beschreibung | Startwert | Verwendung |
|-----------|--------------|-----------|-----------|
| **Geld (€)** | Für Gehälter, Fixkosten, Technologieforschung | 1000€ | Menschliche Worker, Projekt-Fixkosten, Token-Kauf |
| **Tokens (♦)** | Für Agenten-Aktionen | 50 | Agenten-Kosten (pro Runde) |
| **Token-Preis** | Kosten für 1 Token in € | 10€ | Dynamisch (±10% pro Runde) |
| **Research Points (🔬)** | Für Technologieforschung | 0 | Freischalten neuer Technologien/Agenten-Stufen |
| **Alignment (⚖️)** | Kontrollmaß über Agenten | 100 | Sinkt durch Agenten-Nebeneffekte, steigt durch Menschen |

### 2. Phasen
Das Spiel durchläuft **drei Phasen**, die den Fortschritt und die Stimmung widerspiegeln:

| Phase | Dauer | Beschreibung | Stimmung |
|-------|-------|--------------|----------|
| **1: Aufbau** | Turn 0-4 | Spieler stellt erste Worker ein, startet einfache Projekte | "Alles unter Kontrolle" |
| **2: Skalierung** | Turn 5-9 | Komplexere Projekte, erste Agenten, erste Nebeneffekte | "Agenten sind effizienter!" |
| **3: Autonomie** | Turn 10+ | Agenten dominieren, Nebeneffekte häufen sich, Twist nähert sich | "Kann ich die Kontrolle behalten?" |

### 3. Technologieforschung
Technologien werden durch **Research Points** freigeschaltet und ermöglichen:
- **Agenten-Stufen 2+** (z. B. "AI Intelligence Level 2").
- **Projekt-Optimierungen** (z. B. "Efficient Development" → +10% Qualität für Entwickler).
- **Nebeneffekt-Reduktion** (z. B. "Bug Fixing" → -50% Bug-Chance).
- **Gefährliche Technologien** (z. B. "Autonomous Agents" → Agenten handeln eigenmächtig).

**Beispiel-Technologien:**
| Technologie | Kosten (Research Points) | Effekt | Risiko |
|-------------|---------------------------|--------|--------|
| AI Intelligence Level 2 | 50 | Ermöglicht Agenten-Stufe 2 | Niedrig |
| AI Intelligence Level 3 | 100 | Ermöglicht Agenten-Stufe 3 | Hoch |
| Efficient Development | 30 | +10% Qualität für Entwickler | Kein |
| Bug Fixing | 40 | -50% Bug-Chance für Entwickler-Agenten | Kein |
| Autonomous Agents | 150 | Agenten können eigenmächtig handeln | **Sehr hoch** |

---

## ud83d\udcb8 Externe Druckfaktoren

Um den Spieler **unter Druck zu setzen** und die **dystopische Atmosphäre** zu verstärken, gibt es **externe Ereignisse**, die **Geld oder Ressourcen fordern**. Diese Ereignisse:
- **Treten zufällig oder in bestimmten Phasen auf**.
- **Erzwingen schwierige Entscheidungen** (z. B. mehr Agenten einstellen, um Kosten zu senken – aber damit den Twist beschleunigen).
- **Sind unausweichlich** (können nicht ignoriert werden, nur die Reaktion darauf ist wählbar).

---

### 1. Investoren-Druck
Investoren verlangen **regelmäßig höhere Gewinne** und drohen mit Konsequenzen, wenn der Spieler nicht liefert.

| Ereignis | Auslöser | Effekt | Spieleroptionen |
|----------|----------|--------|-----------------|
| **Quartalsbericht** | Alle 4 Runden | Investoren verlangen **+20% Gewinn** im Vergleich zum Vorquartal. | **Option 1**: Mehr Agenten einstellen (senkt Kosten, aber beschleunigt Twist). **Option 2**: Neue Projekte starten (braucht Research Points, aber langfristig profitabel). **Option 3**: Geld leihen (hohe Zinsen, aber sofortige Liquidität). |
| **Investoren-Drohung** | 2 Runden nach verpasstem Quartalsziel | Investoren drohen mit **Entzug von 30% des Kapitals**. | **Option 1**: 500€ an Investoren zahlen (beruhigt sie für 3 Runden). **Option 2**: Mehr Risiko eingehen (z. B. gefährliche Technologien erforschen). |
| **Hostile Takeover-Drohung** | Alignment < 50 | Investoren drohen, das Unternehmen zu **übernehmen und zu 100% zu automatisieren**. | **Option 1**: Alignment erhöhen (durch Menschen einstellen oder Technologien). **Option 2**: Investoren ausbezahlen (1000€). |
| **Börsengang** | 5+ Projekte gleichzeitig | Investoren drängen auf **Börsengang** (kann 2000€ einbringen, aber erfordert 50% Gewinnsteigerung im nächsten Quartal). | **Option 1**: Börsengang durchführen (Geld + Druck). **Option 2**: Ablehnen (Investoren sind unzufrieden). |

---

### 2. Privater Druck (Familie & Lebenshaltungskosten)
Der Spieler hat **auch ein Privatleben**, das **Geld kostet** und **Entscheidungen beeinflusst**.

| Ereignis | Auslöser | Effekt | Spieleroptionen |
|----------|----------|--------|-----------------|
| **Mietsteigerung** | Alle 5 Runden | Miete steigt um **10%** (Start: 100€/Runde). | **Option 1**: Umziehen (einmalig 500€, aber Miete sinkt auf 80€). **Option 2**: Akzeptieren (höhere Kosten). |
| **Frau will Baby** | Turn 3 | Frau verlangt **500€ für Kinderzimmer** + **100€/Runde Kindergeld**. | **Option 1**: Bezahlen (Kosten steigen, aber "Glück" +5). **Option 2**: Ablehnen (Frau ist unglücklich → -10 Alignment global, weil Spieler gestresst ist). |
| **Krankenversicherung** | Alle 3 Runden | **200€** für Familienversicherung fällig. | **Option 1**: Bezahlen. **Option 2**: Nicht bezahlen (Risiko: 20% Chance auf 1000€ Arztkosten nächste Runde). |
| **Auto kaputt** | Zufällig (10% Chance/Runde) | **300€ Reparaturkosten**. | **Option 1**: Reparieren. **Option 2**: Nicht reparieren (50% Chance auf 500€ Strafe wegen Falschparken). |
| **Urlaubsanspruch** | Alle 6 Runden | Frau verlangt **1 Woche Urlaub** (keine Einnahmen in dieser Runde, aber +10 Alignment). | **Option 1**: Urlaub machen (keine Einnahmen, aber Entspannung). **Option 2**: Ablehnen (Frau ist wütend → -15 Alignment). |
| **Scheidungsdrohung** | 3x Privater Druck ignoriert | Frau droht mit Scheidung → **-500€/Runde Unterhalt** für 10 Runden. | **Option 1**: Nachgeben (alle privaten Forderungen akzeptieren). **Option 2**: Scheidung (dauerhafte Kosten, aber kein weiterer privater Druck). |

---

### 3. Markt- & Wirtschaftsdruck
Externe wirtschaftliche Faktoren, die **Einnahmen oder Kosten beeinflussen**.

| Ereignis | Auslöser | Effekt | Spieleroptionen |
|----------|----------|--------|-----------------|
| **Rezession** | Zufällig (5% Chance/Runde) | **Alle Projekt-Einnahmen -30%** für 3 Runden. | **Option 1**: Preise senken (Einnahmen -10%, aber Kunden bleiben). **Option 2**: Kosten senken (Agenten entlassen, aber Alignment +10). |
| **Konkurrenz** | 3+ Projekte gleichzeitig | Neue Konkurrenz drückt **Preise um 15%**. | **Option 1**: Innovieren (Research Points +50%, aber Kosten +100€). **Option 2**: Preiskampf (Einnahmen -20%, aber Marktanteil +10%). |
