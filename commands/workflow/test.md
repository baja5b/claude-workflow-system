# Workflow Test (4-Augen-Prinzip)

Starte einen unabhängigen Review der Implementierung.

## Anweisungen

Das 4-Augen-Prinzip bedeutet: Eine unabhängige Instanz prüft die Änderungen
nur anhand der Original-Anforderungen, OHNE den Implementierungsplan zu kennen.

### 1. Daten sammeln

```sql
-- Nur Requirements laden (NICHT den Plan!)
SELECT workflow_id, title, requirements
FROM workflows
WHERE workflow_id = '{workflow_id}';
```

### 2. Git Diff holen

```bash
git diff HEAD~{commit_count}..HEAD
# oder
git diff {base_branch}..HEAD
```

### 3. Task Agent spawnen

Spawne einen neuen Task Agent mit isoliertem Kontext:

```
Du bist ein Code Reviewer.

ANFORDERUNGEN:
{requirements}

ÄNDERUNGEN:
{git_diff}

Prüfe:
1. Erfüllen die Änderungen die Anforderungen vollständig?
2. Gibt es offensichtliche Bugs oder Probleme?
3. Sind Tests vorhanden und sinnvoll?

Führe aus:
- npm test / pytest (je nach Projekt)
- Linting checks

Bewerte: PASS oder FAIL mit Begründung.
```

### 4. Tests ausführen

Der Agent führt automatisch aus:
- Unit Tests
- Lint Checks
- Type Checks (falls vorhanden)

### 5. Ergebnisse speichern

```sql
INSERT INTO test_results (workflow_id, test_type, test_name, passed, output)
VALUES
    ('{workflow_id}', 'review', 'requirements_check', true/false, '{output}'),
    ('{workflow_id}', 'unit', 'npm_test', true/false, '{output}'),
    ('{workflow_id}', 'lint', 'eslint', true/false, '{output}');
```

### 6. Notification

Bei Erfolg:
```
✅ 4-Augen Test bestanden
Workflow: {workflow_id}
Tests: {passed}/{total}
```

Bei Fehler:
```
❌ 4-Augen Test fehlgeschlagen
Workflow: {workflow_id}
Fehler: {failed_tests}
```

## Ausgabe-Format

```
=== 4-AUGEN TEST ===
Workflow: WF-2025-XXX

Unabhängiger Review (nur Requirements bekannt):

Anforderungen:
- {requirement_1}
- {requirement_2}

Prüfung:
[PASS] Anforderung 1 erfüllt
[PASS] Anforderung 2 erfüllt
[PASS] Unit Tests: 24/24
[PASS] Lint: keine Fehler

=== TEST ERGEBNIS: BESTANDEN ===

Workflow wird als COMPLETED markiert.
```

## Wichtig

- Der Test-Agent sieht NUR: Requirements + Git Diff + Testbefehle
- NICHT: Implementierungsplan, Kommentare, Notizen
- Dies simuliert einen unabhängigen Code Review
