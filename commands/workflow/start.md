# Workflow Start

Starte einen neuen AI-gesteuerten Entwicklungs-Workflow.

## Anweisungen

Du startest jetzt einen strukturierten Workflow für: **$ARGUMENTS**

### Phase 1: Requirements Planning

1. **Analysiere die Anforderung**:
   - Was genau soll implementiert werden?
   - Welche Dateien/Komponenten sind betroffen?
   - Gibt es Abhängigkeiten zu beachten?

2. **Stelle Klärungsfragen** (falls nötig):
   - Nutze AskUserQuestion für unklare Anforderungen
   - Frage nach Präferenzen bei mehreren Lösungsansätzen
   - Kläre Edge Cases und Fehlerbehandlung

3. **Erstelle einen Plan**:
   - Liste konkrete Tasks auf (nummeriert)
   - Schätze Komplexität pro Task
   - Identifiziere kritische Pfade

### Phase 2: Workflow-Tracking

Speichere den Workflow in der SQLite-Datenbank:

```sql
-- Generiere Workflow-ID: WF-{YYYY}-{NNN}
INSERT INTO workflows (workflow_id, project, project_path, title, status, requirements)
VALUES (?, ?, ?, ?, 'PLANNING', ?);
```

### Phase 3: GitHub Issue (Optional)

Falls ein GitHub-Repository vorhanden ist:
- Erstelle ein Issue mit dem Plan
- Verlinke Issue-Nummer im Workflow

### Phase 4: Notification

Sende Telegram-Benachrichtigung:
```
🚀 Workflow gestartet
Projekt: {project}
Task: {title}
Status: Planning
```

### Ausgabe-Format

Zeige dem User:

```
=== WORKFLOW GESTARTET ===
ID: WF-2025-XXX
Projekt: {aktuelles Verzeichnis}
Titel: $ARGUMENTS

=== REQUIREMENTS PLANNING ===

[Deine Analyse und Fragen hier]

=== VORGESCHLAGENER PLAN ===

Tasks:
1. [Task 1]
2. [Task 2]
...

Bestätige mit /workflow-confirm oder passe den Plan an.
```

## Wichtig

- Warte auf User-Bestätigung bevor du implementierst
- Dokumentiere alle Entscheidungen
- Halte den Plan konkret und umsetzbar
