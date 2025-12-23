# Start Working

Starte den Jira-Worker und arbeite kontinuierlich an Issues.

## Beschreibung

Dieser Command startet eine Arbeits-Session, die Jira nach Issues pollt und diese automatisch verarbeitet. Der Worker durchläuft den kompletten Workflow:

```
TO DO → PLANNED → PLANNED AND CONFIRMED → IN PROGRESS → REVIEW → TESTING → MANUAL TESTING → DOCUMENTATION → DONE
```

## Anweisungen

### Schritt 1: Jira-Verbindung prüfen

Prüfe ob Jira konfiguriert ist:
```
Tool: jira_list_by_status
Arguments:
  statuses: ["TO DO"]
```

Falls Fehler: Zeige Hinweis zur Konfiguration.

### Schritt 2: Workable Issues abrufen

Hole alle Issues die bearbeitet werden können:
```
Tool: jira_get_workable
```

### Schritt 3: Übersicht anzeigen

```
=== JIRA WORKFLOW SESSION ===

Projekt: {JIRA_PROJECT_KEY}
Gefundene Issues: {count}

=== ISSUES ZUM BEARBEITEN ===
{Für jedes Issue:}
[{status}] {key}: {summary}

Starte automatische Verarbeitung...
```

### Schritt 4: Issues verarbeiten

Für jedes Issue:
```
Tool: jira_process_issue
Arguments:
  issue_key: {key}
```

Zeige Fortschritt:
```
[{index}/{total}] {key}: {status} → {result}
```

### Schritt 5: Polling-Loop (optional)

Falls der User kontinuierliches Polling wünscht:
```
Tool: jira_poll_once
```

Wiederhole alle 30 Sekunden.

### Schritt 6: Telegram-Benachrichtigung

Bei wichtigen Status-Änderungen:
```
Tool: telegram_workflow_start
Arguments:
  workflow_id: {issue_key}
  project: {project}
  title: {summary}
```

## Status-Aktionen

| Jira Status | Automatische Aktion |
|-------------|---------------------|
| TO DO | Plan erstellen → PLANNED |
| PLANNED | Warten auf User-Feedback |
| PLANNED AND CONFIRMED | Arbeit starten → IN PROGRESS |
| IN PROGRESS | Arbeit fortsetzen, bei Blockern: Telegram |
| REVIEW | Code-Review → TESTING |
| TESTING | Tests ausführen → MANUAL TESTING |
| MANUAL TESTING | Warten auf User-Bestätigung |
| DOCUMENTATION | Doku erstellen → DONE |

## Ausgabe-Format

```
=== SESSION GESTARTET ===
Verarbeite {count} Issues...

[1/3] MT-1: TO DO → PLANNED (Plan erstellt)
[2/3] MT-2: PLANNED AND CONFIRMED → IN PROGRESS (Arbeit gestartet)
[3/3] MT-3: REVIEW → TESTING (Tests laufen)

=== SESSION ABGESCHLOSSEN ===
Verarbeitet: 3 Issues
Nächster Poll in 30s oder beenden mit Ctrl+C
```

## Verwendung

```bash
/workflow:start-working           # Einmaliger Durchlauf
/workflow:start-working --loop    # Kontinuierliches Polling
/workflow:start-working MT-123    # Spezifisches Issue bearbeiten
```

## Voraussetzungen

1. Jira-Konfiguration in `.env`:
   - JIRA_BASE_URL
   - JIRA_USERNAME
   - JIRA_API_TOKEN
   - JIRA_PROJECT_KEY

2. Jira-Board mit korrekten Status-Spalten

## Hinweise

- Der Worker verarbeitet nur Issues im konfigurierten Projekt
- MANUAL TESTING erfordert User-Interaktion
- Bei Fehlern wird ein Kommentar im Issue erstellt
- Telegram-Benachrichtigungen bei Blockern und Abschluss
