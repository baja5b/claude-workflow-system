# Workflow Confirm

Bestätige den aktuellen Workflow-Plan und starte die Ausführung.

## Anweisungen

### Schritt 1: Aktiven Workflow laden

Hole den aktiven Workflow mit dem MCP-Tool:
```
Tool: workflow_list_active
```

Wähle den neuesten Workflow im Status `PLANNING`.

### Schritt 2: Workflow-Details anzeigen

```
Tool: workflow_get
Arguments:
  workflow_id: {ID aus Schritt 1}
```

### Schritt 3: Plan zusammenfassen

Zeige dem User:
```
=== WORKFLOW BESTÄTIGUNG ===
ID: {workflow_id}
Titel: {title}

=== PLAN ===
{plan als lesbare Liste}

=== TASKS ({anzahl}) ===
1. {task_1}
2. {task_2}
...

Implementierung bestätigen? (Der User hat bereits bestätigt durch Aufruf dieses Skills)
```

### Schritt 4: Status auf CONFIRMED setzen

```
Tool: workflow_update
Arguments:
  workflow_id: {ID}
  status: CONFIRMED
```

### Schritt 5: Telegram-Benachrichtigung

```
Tool: telegram_send
Arguments:
  message: |
    ✅ *Plan bestätigt*

    *ID:* `{workflow_id}`
    *Projekt:* {project}
    *Tasks:* {task_count}

    Starte Implementierung...
```

### Schritt 6: Ersten Task starten

Setze Status auf EXECUTING und starte den ersten Task:

```
Tool: workflow_update
Arguments:
  workflow_id: {ID}
  status: EXECUTING
```

Hole die Tasks:
```
Tool: workflow_get_tasks
Arguments:
  workflow_id: {ID}
```

Setze ersten Task auf IN_PROGRESS:
```
Tool: workflow_update_task
Arguments:
  task_id: {erste task_id}
  status: IN_PROGRESS
```

### Schritt 7: Implementierung durchführen

Führe nun die eigentliche Implementierung durch:
1. Bearbeite jeden Task in Reihenfolge
2. Nutze TodoWrite für Fortschritt-Tracking
3. Nach jedem Task: Status auf COMPLETED setzen
4. Bei Fehler: Status auf FAILED mit error_message

**Coding-Standards beachten:**
- Logging hinzufügen wo sinnvoll
- Keine Inline-Styles (zentrales UX-Design)
- Komponenten wiederverwenden
- Security beachten (keine Secrets im Code, OWASP Top 10)
- Commit-Format: `type: description (fixes #issue)`

## Ausgabe-Format

```
=== PLAN BESTÄTIGT ===
Workflow: WF-2025-XXX

Starte Ausführung von {total_tasks} Tasks...

[1/{total}] {task_1}...
```

## Bei Ablehnung

Falls der User den Plan ablehnt:
```
Tool: workflow_update
Arguments:
  workflow_id: {ID}
  status: REJECTED
```

## Workflow-Flow

`PLANNING` → `CONFIRMED` → `EXECUTING` → `TESTING` → `COMPLETED`
