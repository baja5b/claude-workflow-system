# Workflow Confirm

Bestätige den aktuellen Workflow-Plan und starte die Ausführung.

## Anweisungen

Der User hat den Plan bestätigt. Führe folgende Schritte aus:

### 1. Status-Update

```sql
UPDATE workflows
SET status = 'CONFIRMED', updated_at = CURRENT_TIMESTAMP
WHERE workflow_id = '{current_workflow_id}'
AND status = 'PLANNING';
```

### 2. Tasks erstellen

Falls noch nicht vorhanden, erstelle Tasks aus dem Plan:

```sql
INSERT INTO tasks (workflow_id, sequence, description, status)
VALUES
    ('{workflow_id}', 1, '{task_1}', 'PENDING'),
    ('{workflow_id}', 2, '{task_2}', 'PENDING'),
    ...;
```

### 3. Notification

```
✅ Plan bestätigt
Workflow: {workflow_id}
Tasks: {total_tasks}
Starte Ausführung...
```

### 4. Ausführung starten

- Setze Status auf 'EXECUTING'
- Starte mit Task 1
- Führe /workflow-execute automatisch aus

## Ausgabe-Format

```
=== PLAN BESTÄTIGT ===
Workflow: WF-2025-XXX

Starte Ausführung von {total_tasks} Tasks...

[1/{total}] {task_1}...
```

## Abbruch-Option

Falls der User den Plan ablehnt (z.B. "nein", "abbrechen"):

```sql
UPDATE workflows
SET status = 'REJECTED', updated_at = CURRENT_TIMESTAMP
WHERE workflow_id = '{workflow_id}';
```

```
=== WORKFLOW ABGELEHNT ===
Der Plan wurde nicht bestätigt.

Starte erneut mit:
/workflow-start "Neue Beschreibung"
```
