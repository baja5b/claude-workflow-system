# Workflow Plan

AI Brainstorming für Requirements und Implementierungsplan.

## Anweisungen

Führe eine tiefgehende Analyse durch und erstelle einen detaillierten Plan.

### 1. Kontext verstehen

- Analysiere das aktuelle Projekt (package.json, requirements.txt, etc.)
- Identifiziere verwendete Technologien und Patterns
- Prüfe bestehende Code-Struktur

### 2. Requirements Brainstorming

Stelle systematisch Fragen:

**Funktionale Anforderungen:**
- Was genau soll die Funktion/Feature tun?
- Welche Eingaben werden erwartet?
- Welche Ausgaben sollen erzeugt werden?
- Gibt es Edge Cases zu beachten?

**Nicht-funktionale Anforderungen:**
- Performance-Anforderungen?
- Sicherheitsaspekte?
- Accessibility?
- Kompatibilität?

**Technische Constraints:**
- Welche APIs/Libraries sollen verwendet werden?
- Gibt es Code-Style-Vorgaben?
- Test-Anforderungen?

### 3. Plan erstellen

Strukturiere den Plan in:

1. **Vorbereitung**: Research, Dependency-Check
2. **Implementierung**: Kernlogik, UI, API
3. **Testing**: Unit, Integration, E2E
4. **Dokumentation**: Code-Kommentare, README-Updates
5. **Cleanup**: Unused Code, Refactoring

### 4. Plan speichern

```sql
UPDATE workflows
SET plan = '{json_plan}',
    updated_at = CURRENT_TIMESTAMP
WHERE workflow_id = '{workflow_id}';
```

## Ausgabe-Format

```
=== AI BRAINSTORMING ===
Workflow: WF-2025-XXX

Projekt-Analyse:
- Framework: {detected_framework}
- Sprache: {language}
- Test-Framework: {test_framework}

=== KLÄRUNGSFRAGEN ===

1. {Frage 1}
   Optionen: A) ... B) ... C) ...

2. {Frage 2}
   ...

=== VORGESCHLAGENER PLAN ===

Phase 1: Vorbereitung
- [ ] Dependency X installieren
- [ ] Bestehende Implementierung verstehen

Phase 2: Implementierung
- [ ] {Task 1}
- [ ] {Task 2}
- [ ] {Task 3}

Phase 3: Testing
- [ ] Unit Tests schreiben
- [ ] Integration Tests

Phase 4: Dokumentation
- [ ] Code dokumentieren
- [ ] README updaten

Geschätzte Komplexität: {niedrig/mittel/hoch}

Bestätige mit /workflow-confirm oder passe an.
```

## Tipps

- Nutze AskUserQuestion für wichtige Entscheidungen
- Halte Tasks klein und spezifisch (max 30 min pro Task)
- Identifiziere Risiken und plane Alternativen
