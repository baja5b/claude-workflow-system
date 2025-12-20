# Workflow Start

Starte einen neuen AI-gesteuerten Entwicklungs-Workflow.

## Anweisungen

Du startest jetzt einen strukturierten Workflow für: **$ARGUMENTS**

### Schritt 0: GitHub Issue prüfen/erstellen

**Pflicht:** Jede Änderung braucht ein GitHub Issue.

1. **Prüfe ob Issue existiert:**
   ```bash
   gh issue list --search "$ARGUMENTS" --state open
   ```

2. **Falls kein Issue existiert, erstelle eines:**
   ```bash
   gh issue create --title "feat: $ARGUMENTS" --body "..." --label "feature-request"
   ```

3. **Erstelle Feature-Branch:**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/issue-{nummer}-{kurzbeschreibung}
   ```

### Schritt 1: Workflow erstellen

Nutze den `workflow_create` MCP-Tool um den Workflow anzulegen:

```
Tool: workflow_create
Arguments:
  project: {name des aktuellen Projekts}
  project_path: {vollständiger Pfad zum Projekt}
  title: $ARGUMENTS
```

### Schritt 2: Bestehende Strukturen analysieren (Duplikate vermeiden!)

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

### Schritt 3: Requirements analysieren

1. **Analysiere die Anforderung**:
   - Was genau soll implementiert werden?
   - Welche Dateien/Komponenten sind betroffen?
   - Gibt es Abhängigkeiten zu beachten?
   - **Welche bestehenden Module können erweitert werden?**

2. **Stelle Klärungsfragen** (falls nötig):
   - Nutze AskUserQuestion für unklare Anforderungen
   - Frage nach Präferenzen bei mehreren Lösungsansätzen
   - Kläre Edge Cases und Fehlerbehandlung

### Schritt 4: Plan erstellen und speichern

Erstelle einen konkreten Implementierungsplan:
- Liste konkrete Tasks auf (nummeriert)
- Identifiziere betroffene Dateien
- Definiere Akzeptanzkriterien

Speichere den Plan mit `workflow_update`:
```
Tool: workflow_update
Arguments:
  workflow_id: {die generierte ID}
  requirements: {JSON-String mit den Anforderungen}
  plan: {JSON-String mit dem Plan}
```

### Schritt 5: Tasks hinzufügen

Für jeden Task im Plan:
```
Tool: workflow_add_task
Arguments:
  workflow_id: {ID}
  sequence: {1, 2, 3, ...}
  description: {Task-Beschreibung}
```

### Schritt 6: Telegram-Benachrichtigung

Sende Notification mit `telegram_send_message`:
```
Tool: telegram_send_message
Arguments:
  message: |
    🚀 *Workflow gestartet*

    *ID:* {workflow_id}
    *Projekt:* {project}
    *Task:* {title}
    *Status:* PLANNING

    Tasks: {anzahl}
```

### Ausgabe-Format

Zeige dem User:

```
=== WORKFLOW GESTARTET ===
ID: WF-2025-XXX
Projekt: {aktuelles Verzeichnis}
Titel: $ARGUMENTS
Branch: feature/issue-{nummer}-{kurzbeschreibung}

=== STRUKTUR-ANALYSE ===

Wiederverwendbare Komponenten gefunden:
- {komponente_1}: {beschreibung}
- {komponente_2}: {beschreibung}

Empfehlung: {Erweiterung/Neuerstellung} weil {begründung}

=== REQUIREMENTS PLANNING ===

[Deine Analyse hier]

=== VORGESCHLAGENER PLAN ===

Tasks:
1. [Task 1]
2. [Task 2]
...

Bestätige mit /workflow:confirm oder passe den Plan an.
```

## Workflow-Status

Nach dem Start ist der Workflow im Status `PLANNING`.
Nächster Schritt: `/workflow:confirm` um die Implementierung zu starten.

## Wichtig

- Warte auf User-Bestätigung bevor du implementierst
- Dokumentiere alle Entscheidungen
- Halte den Plan konkret und umsetzbar
- Nutze die MCP-Tools für alle Workflow-Operationen
- **KEINE DUPLIKATE:** Immer bestehende Strukturen erweitern statt neue erstellen
- **Code lesen vor schreiben:** Verstehe was existiert bevor du änderst
