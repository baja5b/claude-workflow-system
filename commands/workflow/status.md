# Workflow Status

Zeige den Status des aktuellen oder eines spezifischen Workflows.

## Anweisungen

Rufe den Workflow-Status aus der SQLite-Datenbank ab.

### Status-Abfrage

```sql
-- Aktueller/aktiver Workflow
SELECT * FROM active_workflows
WHERE project = '{aktuelles_verzeichnis}'
ORDER BY created_at DESC
LIMIT 1;

-- Oder spezifischer Workflow
SELECT * FROM workflow_summary
WHERE workflow_id = '$ARGUMENTS';
```

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
/workflow-start "Beschreibung der Aufgabe"

Letzte Workflows:
- WF-2025-001: "Feature X" (COMPLETED)
- WF-2025-002: "Bug Fix Y" (COMPLETED)
```

## Optionen

- Ohne Argument: Zeige aktuellen Workflow für dieses Projekt
- Mit Workflow-ID: Zeige spezifischen Workflow
- `--all`: Zeige alle aktiven Workflows
- `--history`: Zeige letzte 10 abgeschlossene Workflows
