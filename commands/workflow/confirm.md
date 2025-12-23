# Workflow Confirm

Bestätige den Plan eines Jira-Issues und starte die Implementierung.

## Anweisungen

### Schritt 1: Issue laden

Hole das Issue im Status PLANNED:
```
Tool: jira_list_by_status
Arguments:
  statuses: ["PLANNED"]
```

Falls Issue-Key als Argument:
```
Tool: jira_get_issue
Arguments:
  issue_key: $ARGUMENTS
```

### Schritt 2: Plan anzeigen

Hole die Kommentare (enthält den Auto-Plan):
```
Tool: jira_get_comments
Arguments:
  issue_key: {KEY}
```

Zeige dem User:
```
=== PLAN BESTÄTIGUNG ===
Issue: {key}
Titel: {summary}

=== PLAN ===
{Plan aus den Kommentaren}

Bestätigen und Implementierung starten?
```

### Schritt 3: Transition zu PLANNED AND CONFIRMED

```
Tool: jira_transition
Arguments:
  issue_key: {KEY}
  status: "PLANNED AND CONFIRMED"
  comment: "Plan bestätigt durch User. Starte Implementierung..."
```

### Schritt 4: Telegram-Benachrichtigung

```
Tool: telegram_workflow_start
Arguments:
  workflow_id: {issue_key}
  project: {project_key}
  title: {summary}
```

### Schritt 5: Automatische Verarbeitung starten

Der Worker wird das Issue automatisch auf IN PROGRESS setzen.
Alternativ manuell:
```
Tool: jira_process_issue
Arguments:
  issue_key: {KEY}
```

### Schritt 6: Implementierung durchführen

Führe nun die eigentliche Implementierung durch:
1. Analysiere die Anforderungen
2. Implementiere die Änderungen
3. Nutze TodoWrite für Fortschritt-Tracking
4. Bei Fertigstellung: Transition zu REVIEW

**Coding-Standards beachten:**
- Logging hinzufügen wo sinnvoll
- Keine Inline-Styles (zentrales UX-Design)
- Komponenten wiederverwenden
- Security beachten (keine Secrets im Code, OWASP Top 10)
- Commit-Format: `type: description (PROJ-123)`

## Ausgabe-Format

```
=== PLAN BESTÄTIGT ===
Issue: MT-123
Status: PLANNED → PLANNED AND CONFIRMED

Implementierung wird gestartet...
```

## Bei Ablehnung

Falls der User den Plan ablehnt, füge einen Kommentar hinzu:
```
Tool: jira_add_comment
Arguments:
  issue_key: {KEY}
  body: "Plan abgelehnt. Grund: {user_feedback}"
```

## Workflow-Flow

```
PLANNED → PLANNED AND CONFIRMED → IN PROGRESS → REVIEW → TESTING → MANUAL TESTING → DOCUMENTATION → DONE
```
