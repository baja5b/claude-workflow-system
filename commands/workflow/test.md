# Workflow Test (4-Augen-Prinzip)

Starte einen unabhängigen Review der Implementierung.

## Anweisungen

Das 4-Augen-Prinzip bedeutet: Eine unabhängige Prüfung der Änderungen
anhand der Original-Anforderungen UND automatisierte Tests.

### Schritt 1: Issue laden

```
Tool: jira_list_by_status
Arguments:
  statuses: ["REVIEW", "TESTING"]
```

Falls Issue-Key als Argument:
```
Tool: jira_get_issue
Arguments:
  issue_key: $ARGUMENTS
```

### Schritt 2: Transition zu TESTING

```
Tool: jira_transition
Arguments:
  issue_key: {KEY}
  status: "TESTING"
  comment: "Starte automatisierte Tests..."
```

### Schritt 3: Lokale Tests ausführen

**Pflicht vor jedem Merge:**

```bash
# Lint Check
npm run lint
# oder
ruff check . --ignore E501

# Unit Tests
npm test
# oder
pytest -v

# E2E Tests (bei größeren Änderungen)
npm run test:e2e
```

### Schritt 4: Test-Ergebnisse dokumentieren

```
Tool: jira_add_comment
Arguments:
  issue_key: {KEY}
  body: |
    [Test Results]

    **Lint:** {PASSED/FAILED}
    **Unit Tests:** {count} tests, {passed} passed
    **E2E Tests:** {status}

    {Details bei Fehlern}
```

### Schritt 5: 4-Augen Code Review

Spawne einen Task Agent für den Code Review:

```
Tool: Task
Arguments:
  subagent_type: general-purpose
  description: "Code Review for issue"
  prompt: |
    Du bist ein unabhängiger Code Reviewer.

    ORIGINAL-ANFORDERUNGEN:
    {requirements aus Jira Issue}

    GIT ÄNDERUNGEN:
    {führe git diff aus}

    Prüfe:
    1. Erfüllen die Änderungen die Anforderungen?
    2. Gibt es offensichtliche Bugs?
    3. Code-Qualität OK?

    Antworte mit: PASS oder FAIL mit Begründung.
```

### Schritt 6: Ergebnis auswerten

Bei **PASS** (alle Tests bestanden):
```
Tool: jira_transition
Arguments:
  issue_key: {KEY}
  status: "MANUAL TESTING"
  comment: "Automatische Tests bestanden. Bereit für manuelles Testing."
```

```
Tool: telegram_workflow_complete
Arguments:
  workflow_id: {issue_key}
  project: {project}
  title: {summary}
  tests_passed: {passed_count}
  tests_total: {total_count}
```

Bei **FAIL**:
```
Tool: jira_add_comment
Arguments:
  issue_key: {KEY}
  body: |
    [Tests FAILED]

    {Fehlerbeschreibung}

    Bitte beheben und erneut testen.
```

```
Tool: telegram_workflow_error
Arguments:
  workflow_id: {issue_key}
  project: {project}
  title: {summary}
  phase: "TESTING"
  error: {failed_tests_summary}
```

## Ausgabe-Format

```
=== 4-AUGEN TEST ===
Issue: MT-123

Lokale Tests:
  Lint:        PASSED
  Unit Tests:  42 passed, 0 failed
  E2E Tests:   PASSED

Code Review:
  Anforderungen erfüllt: JA
  Offensichtliche Bugs:  NEIN
  Code-Qualität:         OK

=== TEST ERGEBNIS: BESTANDEN ===

Issue wird auf MANUAL TESTING gesetzt.
User muss nun manuell testen und bestätigen.
```

## Wichtig

- Tests laufen lokal oder auf Dev-Server (NICHT Produktion!)
- Code Review ist isoliert (nur Requirements + Diff)
- Bei Fehlern: Issue bleibt in TESTING
- MANUAL TESTING erfordert User-Interaktion in Jira
