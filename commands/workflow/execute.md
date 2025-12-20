# Workflow Execute

Führe den nächsten Task im Workflow aus.

## Anweisungen

### 1. Aktuellen Workflow und Tasks laden

```
Tool: workflow_list_active
```

Wähle den Workflow im Status `CONFIRMED` oder `EXECUTING`.

```
Tool: workflow_get
Arguments:
  workflow_id: {ID}
```

```
Tool: workflow_get_tasks
Arguments:
  workflow_id: {ID}
```

### 2. Nächsten pending Task identifizieren

Finde den ersten Task mit Status `PENDING` (niedrigste sequence).

### 3. Task starten

```
Tool: workflow_update_task
Arguments:
  task_id: {task_id}
  status: IN_PROGRESS
```

### 4. Task ausführen

1. Führe die Implementierung durch
2. Nutze TodoWrite für Fortschritt-Tracking
3. **Coding-Standards beachten:**
   - Logging hinzufügen wo sinnvoll
   - Keine Inline-Styles
   - Komponenten wiederverwenden
   - Commit-Format: `type: description (fixes #issue)`

### 5. Task abschließen

Bei Erfolg:
```
Tool: workflow_update_task
Arguments:
  task_id: {task_id}
  status: COMPLETED
  result: "{beschreibung_was_gemacht_wurde}"
```

Bei Fehler:
```
Tool: workflow_update_task
Arguments:
  task_id: {task_id}
  status: FAILED
  error_message: "{fehler_beschreibung}"
```

### 6. Nächster Task oder Abschluss

Falls weitere Tasks pending:
- Fahre automatisch mit nächstem Task fort

Falls alle Tasks completed:
```
Tool: workflow_update
Arguments:
  workflow_id: {ID}
  status: TESTING
```

Dann automatisch `/workflow:test` ausführen.

### Ausgabe-Format

```
=== TASK AUSFÜHRUNG ===
Workflow: WF-2025-XXX
Task {current}/{total}: {description}

[Implementierung hier...]

✓ Task abgeschlossen

Nächster Task: {next_task}
```

## Fehlerbehandlung

Bei Fehler:

```
=== TASK FEHLGESCHLAGEN ===
Task {current}/{total}: {description}
Fehler: {error_message}

Optionen:
1. Fehler beheben und /workflow-execute erneut ausführen
2. Task überspringen mit /workflow-execute --skip
3. Workflow abbrechen mit /workflow-status --cancel
```

## Optionen

- `--skip`: Aktuellen Task überspringen (Status = 'SKIPPED')
- `--retry`: Fehlgeschlagenen Task erneut versuchen
- `--force`: Alle pending Tasks ausführen ohne Pause

## Wichtig

- **Bestehende Strukturen nutzen:** Prüfe vor jeder Änderung ob Code wiederverwendet werden kann
- **Keine Duplikate:** Erweitere bestehende Module statt neue zu erstellen
- **Tests nicht vergessen:** Bei größeren Änderungen E2E-Tests ergänzen
