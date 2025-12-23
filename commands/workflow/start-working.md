# Start Working - Claude Code als intelligenter Workflow Worker

Arbeite alle Jira Issues im aktuellen Repo so weit wie moeglich durch den Workflow.

## Kernprinzip

**DU (Claude Code) bist der Worker.** Du analysierst jedes Issue im Kontext des Repos und bewegst Issues durch den Workflow.

## WICHTIG: Zwei-Phasen-Workflow

**Phase 1: Planung (TO DO → PLANNED)**
- Codebase analysieren (NUR LESEN!)
- Plan in Jira dokumentieren
- Status auf PLANNED setzen
- **KEINE Code-Aenderungen!**
- **WARTEN auf User-Review!**

**Phase 2: Implementierung (PLANNED AND CONFIRMED → IN PROGRESS)**
- Erst wenn User nach PLANNED AND CONFIRMED verschoben hat
- Dann Code implementieren
- Commits erstellen
- Status weiter bewegen

## Workflow mit User-Approval-Gates

```
TO DO → [Claude plant] → PLANNED → [USER] → PLANNED AND CONFIRMED → [Claude implementiert] → IN PROGRESS → [Claude] → REVIEW → [USER] → TESTING → [Claude] → MANUAL TESTING → [USER] → DOCUMENTATION → [Claude] → DONE
```

**User verschiebt manuell (3 Gates):**
1. **PLANNED → PLANNED AND CONFIRMED** (User prüft Plan)
2. **REVIEW → TESTING** (User prüft Code Review)
3. **MANUAL TESTING → DOCUMENTATION** (User bestätigt manuelle Tests)

**Claude verschiebt automatisch:**
- TO DO → PLANNED (Plan erstellen)
- PLANNED AND CONFIRMED → IN PROGRESS (Implementierung starten)
- IN PROGRESS → REVIEW (Implementierung fertig)
- TESTING → MANUAL TESTING (Auto-Tests bestanden)
- DOCUMENTATION → DONE (Doku erstellt)

## Anweisungen

### 1. Konfiguration laden

Lade `.claude-workflow.json` aus dem aktuellen Repo:
- `jira.project_key` - Jira Projekt
- `github.base_branch` - Basis-Branch fuer PRs

Falls nicht vorhanden: Zeige Fehler und beende.

### 2. Jira Issues abrufen

Pruefe ob Jira MCP-Tools verfuegbar sind:
- `jira_list_by_status`
- `jira_get_workable`
- `jira_process_issue`

Falls nicht: Zeige Anleitung zur MCP-Server Konfiguration.

Hole alle offenen Issues:
```
Tool: jira_list_by_status
Arguments:
  statuses: ["to do", "PLANNED", "PLANNED AND CONFIRMED", "In progress"]
```

### 3. Issues nach Prioritaet sortieren

Zeige Uebersicht:
```
=== WORKFLOW SESSION: {project_key} ===

Gefunden: {count} Issues

TO DO (Planung erforderlich):
  - MUS-XX: Titel...

PLANNED AND CONFIRMED (Bereit zur Implementierung):
  - MUS-YY: Titel...

IN PROGRESS (In Arbeit):
  - MUS-ZZ: Titel...

Starte Verarbeitung...
```

### 4. TO DO Issues → PLANNED (NUR PLANEN, NICHT IMPLEMENTIEREN!)

**WICHTIG: Bei TO DO Issues wird NUR ein Plan erstellt! KEINE Code-Aenderungen!**

Fuer jedes Issue im Status "TO DO":

**a) Issue-Details lesen:**
```
Tool: jira_get_issue
Arguments:
  issue_key: {key}
```

**b) Codebase analysieren (NUR LESEN!):**
- Suche relevante Dateien basierend auf Issue-Titel/Beschreibung
- Verstehe die aktuelle Implementierung
- Identifiziere betroffene Komponenten
- **KEINE DATEIEN AENDERN!**

**c) Konkreten Plan erstellen:**
Basierend auf der Codebase-Analyse, dokumentiere:
- Welche Dateien muessen geaendert werden?
- Was genau muss implementiert werden?
- Welche Tests sind noetig?

**d) Jira mit Plan aktualisieren:**
```
Tool: jira_update_issue
Arguments:
  issue_key: {key}
  fields:
    description: |
      **Urspruengliche Anforderung**
      {original_description}

      **Analyse**
      {deine_analyse_der_codebase}

      **Implementierungsplan**
      1. {konkreter_schritt_1}
      2. {konkreter_schritt_2}
      ...

      **Betroffene Dateien**
      - path/to/file1.py
      - path/to/file2.ts

      **Naechste Schritte**
      - Plan pruefen
      - Nach PLANNED AND CONFIRMED verschieben wenn OK
```

**e) Status auf PLANNED setzen (NICHT PLANNED AND CONFIRMED!):**
```
Tool: jira_transition
Arguments:
  issue_key: {key}
  transition_name: "Geplant"
```

**STOP! Warte auf User-Bestaetigung bevor du weitermachst!**

### 5. PLANNED AND CONFIRMED → IN PROGRESS → REVIEW

Fuer jedes Issue im Status "PLANNED AND CONFIRMED":

**a) Plan aus Issue lesen**

**b) Implementierung durchfuehren:**
- Erstelle/aendere die identifizierten Dateien
- Schreibe Tests
- Fuehre Tests aus

**c) Fortschritt in Jira dokumentieren:**
```
Tool: jira_add_comment
Arguments:
  issue_key: {key}
  comment: |
    [Fortschritt]
    - ✅ Datei X geaendert
    - ✅ Tests geschrieben
    - 🔄 Code Review ausstehend
```

**d) Bei Fertigstellung:**
- Commit erstellen
- PR erstellen (falls konfiguriert)
- Status → REVIEW

### 6. REVIEW → TESTING

Fuer Issues in REVIEW:
- Pruefe ob PR gemerged
- Fuehre finale Tests aus
- Status → TESTING → DONE

### 7. Zusammenfassung

```
=== SESSION ABGESCHLOSSEN ===

Verarbeitet:
- MUS-XX: TO DO → PLANNED (Plan erstellt)
- MUS-YY: PLANNED AND CONFIRMED → IN PROGRESS (Implementierung gestartet)
- MUS-ZZ: IN PROGRESS → REVIEW (PR erstellt)

Naechste Schritte:
- MUS-XX: Plan in Jira pruefen, dann nach "PLANNED AND CONFIRMED" verschieben
- MUS-YY: Implementierung fortsetzen mit /workflow:start-working
```

## Wichtige Regeln

1. **Immer Codebase analysieren** - Keine generischen Plaene!
2. **Konkrete Dateipfade nennen** - Welche Files werden geaendert?
3. **Kleine Commits** - Ein Commit pro logische Aenderung
4. **Tests schreiben** - Keine Implementierung ohne Tests
5. **Jira aktuell halten** - Fortschritt dokumentieren

## Fallback ohne Jira MCP

Falls Jira MCP nicht verfuegbar:
1. Zeige Anleitung zur Installation
2. Biete Alternative: GitHub Issues verwenden
3. Oder: Manuell Jira-Key angeben fuer direkten API-Aufruf
