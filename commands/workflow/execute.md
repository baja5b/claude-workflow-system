# Workflow Execute

Führe den nächsten Task im Workflow aus.

## Anweisungen

### 1. Aktuellen Task laden

```sql
SELECT * FROM tasks
WHERE workflow_id = '{workflow_id}'
AND status = 'PENDING'
ORDER BY sequence ASC
LIMIT 1;
```

### 2. Task ausführen

1. Setze Task-Status auf 'IN_PROGRESS'
2. Führe die Implementierung durch
3. Nutze TodoWrite für Fortschritt-Tracking
4. Bei Erfolg: Status = 'COMPLETED'
5. Bei Fehler: Status = 'FAILED', error_message speichern

### 3. Progress-Update

Nach jedem Task:

```sql
UPDATE tasks
SET status = 'COMPLETED',
    completed_at = CURRENT_TIMESTAMP,
    result = '{json_result}'
WHERE workflow_id = '{workflow_id}'
AND sequence = {current_sequence};
```

### 4. Nächster Task oder Abschluss

Falls weitere Tasks pending:
- Fahre automatisch mit nächstem Task fort

Falls alle Tasks completed:
- Setze Workflow-Status auf 'TESTING'
- Führe /workflow-test aus

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
