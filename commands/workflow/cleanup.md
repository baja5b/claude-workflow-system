# Workflow Cleanup

Entferne deprecated Code, ungenutzte Dateien und bereinige das Projekt.

## Anweisungen

### 0. Aktuellen Workflow laden

```
Tool: workflow_list_active
```

Wähle den Workflow im Status `COMPLETED` oder `TESTING`.

### 1. Analyse durchführen

**Ungenutzte Exporte finden:**
```bash
# TypeScript/JavaScript
npx ts-prune
# oder
npx unimported
```

**Ungenutzte Dependencies:**
```bash
npx depcheck
# oder
pip-autoremove --list (Python)
```

**Tote Code-Pfade:**
- Suche nach `// TODO_REMOVE`, `// DEPRECATED`, `@deprecated`
- Prüfe auf auskommentierte Code-Blöcke
- Identifiziere ungenutzte Funktionen/Klassen

### 2. Cleanup-Plan erstellen

Kategorisiere Findings:

**Sicher zu entfernen:**
- Ungenutzte Imports
- Auskommentierter Code
- Leere Dateien

**Prüfung erforderlich:**
- Scheinbar ungenutzte Exporte (könnten extern genutzt werden)
- Deprecated APIs mit möglichen Abhängigkeiten

**Manuell entscheiden:**
- Feature Flags
- Experimental Code
- Legacy-Kompatibilität

### 3. User-Bestätigung

Zeige dem User was entfernt werden soll:

```
=== CLEANUP VORSCHLAG ===

Sicher zu entfernen (automatisch):
- src/utils/oldHelper.ts (ungenutzt seit 3 Monaten)
- import { unusedFn } from './lib' (10 Vorkommen)

Prüfung erforderlich:
- src/api/v1/ (alte API-Version)
- src/components/LegacyButton.tsx

Soll ich fortfahren? [Ja/Nein/Details]
```

### 4. Cleanup ausführen

Nach Bestätigung:
- Entferne toten Code
- Update Imports
- Führe Formatter aus
- Führe Tests aus zur Validierung

### 5. Cleanup dokumentieren

```
Tool: workflow_add_task
Arguments:
  workflow_id: {ID}
  sequence: {next_seq}
  description: "Cleanup: {summary}"
```

```
Tool: workflow_update_task
Arguments:
  task_id: {task_id}
  status: COMPLETED
  result: "{removed_items}"
```

### 6. Telegram-Benachrichtigung

```
Tool: telegram_send
Arguments:
  message: |
    🧹 *Cleanup abgeschlossen*

    *Workflow:* `{workflow_id}`
    *Entfernt:* {lines_removed} Zeilen
    *Dateien:* {files_deleted} gelöscht, {files_modified} modifiziert

    ✅ Tests bestanden
```

## Ausgabe-Format

```
=== CLEANUP ANALYSE ===

Gefunden:
- 5 ungenutzte Imports
- 2 deprecated Funktionen
- 1 leere Datei
- 3 auskommentierte Code-Blöcke

=== AKTIONEN ===

[✓] Entfernt: import { oldFn } from './utils' (5x)
[✓] Entfernt: src/helpers/deprecated.ts
[✓] Entfernt: auskommentierter Code in src/App.tsx (Zeilen 45-67)
[⚠] Übersprungen: LegacyAPI (noch in Nutzung)

=== VALIDIERUNG ===
[✓] Tests: 124/124 bestanden
[✓] Build: erfolgreich
[✓] Lint: keine neuen Fehler

=== CLEANUP ABGESCHLOSSEN ===
Entfernt: 234 Zeilen Code
Dateien: 3 gelöscht, 7 modifiziert
```

## Optionen

- `--dry-run`: Nur analysieren, nichts ändern
- `--aggressive`: Auch "unsichere" Items entfernen
- `--imports-only`: Nur ungenutzte Imports entfernen
- `--confirm-each`: Jede Änderung einzeln bestätigen
