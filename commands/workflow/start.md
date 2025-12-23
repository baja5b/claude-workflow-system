# Workflow Start

Starte einen neuen AI-gesteuerten Entwicklungs-Workflow mit Jira-Integration.

## Anweisungen

Du startest jetzt einen strukturierten Workflow für: **$ARGUMENTS**

### Schritt 0: Jira Issue prüfen/erstellen

**Pflicht:** Jede Änderung braucht ein Jira Issue.

1. **Prüfe ob Issue existiert:**
   ```
   Tool: jira_list_issues
   Arguments:
     jql: "project = {PROJECT_KEY} AND summary ~ \"$ARGUMENTS\" AND status != Done"
   ```

2. **Falls kein Issue existiert, erstelle eines:**
   ```
   Tool: jira_create_issue
   Arguments:
     summary: $ARGUMENTS
     description: "Workflow gestartet von Claude Code"
     issue_type: "Task"
   ```

3. **Erstelle Feature-Branch:**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/{ISSUE_KEY}-{kurzbeschreibung}
   ```

### Schritt 1: Bestehende Strukturen analysieren (Duplikate vermeiden!)

**Pflicht:** Vor jeder Implementierung prüfen ob wiederverwendbare Strukturen existieren.

1. **Dokumentation lesen:**
   ```
   Tool: Read
   Arguments:
     file_path: {projekt}/CLAUDE.md
   ```
   ```
   Tool: Read
   Arguments:
     file_path: {projekt}/README.md
   ```

2. **Bestehende Module/Komponenten suchen:**
   ```
   Tool: Task
   Arguments:
     subagent_type: Explore
     description: "Find reusable components"
     prompt: |
       Suche nach bestehenden Modulen, Funktionen und Komponenten die für
       "$ARGUMENTS" wiederverwendet werden können.

       Prüfe:
       - Gibt es ähnliche Funktionalität bereits?
       - Welche UI-Komponenten existieren (components/ui/)?
       - Welche Services/Hooks können erweitert werden?
       - Gibt es zentrale Styles/Themes?

       Ziel: Keine Duplikate erstellen, bestehenden Code erweitern.
   ```

3. **Ergebnis dokumentieren:**
   - Gefundene wiederverwendbare Strukturen auflisten
   - Vorschlagen ob Erweiterung oder Neuerstellung sinnvoller ist

### Schritt 2: Requirements analysieren

1. **Analysiere die Anforderung**:
   - Was genau soll implementiert werden?
   - Welche Dateien/Komponenten sind betroffen?
   - Gibt es Abhängigkeiten zu beachten?
   - **Welche bestehenden Module können erweitert werden?**

2. **Stelle Klärungsfragen** (falls nötig):
   - Nutze AskUserQuestion für unklare Anforderungen
   - Frage nach Präferenzen bei mehreren Lösungsansätzen
   - Kläre Edge Cases und Fehlerbehandlung

### Schritt 3: Plan erstellen und als Jira-Kommentar speichern

Erstelle einen konkreten Implementierungsplan:
- Liste konkrete Tasks auf (nummeriert)
- Identifiziere betroffene Dateien
- Definiere Akzeptanzkriterien

Speichere den Plan als Jira-Kommentar:
```
Tool: jira_add_comment
Arguments:
  issue_key: {ISSUE_KEY}
  body: |
    [Implementation Plan]

    **Requirements:**
    {requirements_summary}

    **Affected Files:**
    {file_list}

    **Tasks:**
    1. {task_1}
    2. {task_2}
    3. {task_3}

    **Acceptance Criteria:**
    - {criterion_1}
    - {criterion_2}

    Warte auf Bestätigung...
```

### Schritt 4: Issue auf PLANNED setzen

```
Tool: jira_transition
Arguments:
  issue_key: {ISSUE_KEY}
  status: "PLANNED"
```

### Schritt 5: Telegram-Benachrichtigung

```
Tool: telegram_workflow_start
Arguments:
  workflow_id: {ISSUE_KEY}
  project: {project}
  title: {summary}
```

### Ausgabe-Format

Zeige dem User:

```
=== WORKFLOW GESTARTET ===
Issue: {ISSUE_KEY}
Projekt: {aktuelles Verzeichnis}
Titel: $ARGUMENTS
Branch: feature/{ISSUE_KEY}-{kurzbeschreibung}

=== STRUKTUR-ANALYSE ===

Wiederverwendbare Komponenten gefunden:
- {komponente_1}: {beschreibung}
- {komponente_2}: {beschreibung}

Empfehlung: {Erweiterung/Neuerstellung} weil {begründung}

=== REQUIREMENTS ===

[Deine Analyse hier]

=== VORGESCHLAGENER PLAN ===

Tasks:
1. [Task 1]
2. [Task 2]
...

=== NÄCHSTER SCHRITT ===
Prüfe den Plan in Jira und verschiebe das Issue zu "PLANNED AND CONFIRMED"
oder nutze: /workflow:confirm {ISSUE_KEY}
```

## Workflow-Status

Nach dem Start ist das Issue im Status `PLANNED`.
Nächster Schritt: Issue in Jira auf `PLANNED AND CONFIRMED` verschieben
oder `/workflow:confirm` um die Implementierung zu starten.

## Wichtig

- Warte auf User-Bestätigung bevor du implementierst
- Dokumentiere alle Entscheidungen als Jira-Kommentare
- Halte den Plan konkret und umsetzbar
- Nutze die Jira-MCP-Tools für alle Workflow-Operationen
- **KEINE DUPLIKATE:** Immer bestehende Strukturen erweitern statt neue erstellen
- **Code lesen vor schreiben:** Verstehe was existiert bevor du änderst
