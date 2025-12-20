# Workflow Status

Zeige den Status des aktuellen oder eines spezifischen Workflows.

## Anweisungen

### Status-Abfrage

**Alle aktiven Workflows:**
```
Tool: workflow_list_active
```

**Spezifischer Workflow (falls ID angegeben):**
```
Tool: workflow_get
Arguments:
  workflow_id: $ARGUMENTS
```

**Tasks des Workflows:**
```
Tool: workflow_get_tasks
Arguments:
  workflow_id: {ID}
```

**Telegram-Aufträge prüfen (noch nicht bearbeitet):**
Prüfe ob es via Telegram erstellte Workflows gibt die noch nicht gestartet wurden.

### Ausgabe-Format

```
=== WORKFLOW STATUS ===
ID: WF-2025-XXX
Projekt: {project}
Titel: {title}
Status: {status}
Erstellt: {created_at}

=== TASKS ({completed}/{total}) ===
[✓] 1. Task 1 - COMPLETED
[→] 2. Task 2 - IN_PROGRESS
[ ] 3. Task 3 - PENDING

=== TESTS ===
Gesamt: {total_tests} | Bestanden: {passed_tests}

=== LETZTE AKTIVITÄT ===
{updated_at}: {letzte Aktion}
```

### Status-Bedeutung

| Status | Bedeutung | Nächster Schritt |
|--------|-----------|------------------|
| PLANNING | Plan wird erstellt | /workflow-confirm |
| CONFIRMED | Plan bestätigt | Automatische Ausführung |
| EXECUTING | Tasks werden ausgeführt | Warten |
| TESTING | 4-Augen Test läuft | Warten |
| DOCUMENTING | Doku wird erstellt | Warten |
| COMPLETED | Erfolgreich abgeschlossen | - |
| REJECTED | Plan abgelehnt | /workflow-start |
| FAILED | Fehler aufgetreten | Fehler beheben |

### Kein Workflow gefunden

Falls kein aktiver Workflow existiert:

```
=== KEIN AKTIVER WORKFLOW ===

Starte einen neuen Workflow mit:
/workflow:start "Beschreibung der Aufgabe"

Oder prüfe Telegram-Aufträge:
/workflow:status --pending
```

## Optionen

- Ohne Argument: Zeige aktuellen Workflow für dieses Projekt
- Mit Workflow-ID: Zeige spezifischen Workflow
- `--all`: Zeige alle aktiven Workflows
- `--pending`: Zeige Telegram-Aufträge die noch nicht bearbeitet wurden
- `--history`: Zeige letzte 10 abgeschlossene Workflows

## Nächste Schritte je nach Status

| Status | Nächster Befehl |
|--------|-----------------|
| PLANNING | `/workflow:confirm` |
| CONFIRMED | `/workflow:execute` |
| EXECUTING | Warten oder `/workflow:execute` |
| TESTING | `/workflow:test` |
| COMPLETED | `/workflow:document` oder `/workflow:cleanup` |
| FAILED | Fehler beheben, dann `/workflow:execute --retry` |
