# Workflow Document

Generiere automatisch Dokumentation für den abgeschlossenen Workflow.

## Anweisungen

### 1. Workflow-Daten laden

```sql
SELECT w.*,
       GROUP_CONCAT(t.description, '; ') as tasks_completed
FROM workflows w
JOIN tasks t ON w.workflow_id = t.workflow_id
WHERE w.workflow_id = '{workflow_id}'
AND t.status = 'COMPLETED';
```

### 2. Git History analysieren

```bash
git log --oneline HEAD~{commit_count}..HEAD
git diff --stat HEAD~{commit_count}..HEAD
```

### 3. Dokumentation erstellen

**Changelog-Eintrag:**
```markdown
## [{version}] - {date}

### Added
- {neue Features}

### Changed
- {Änderungen}

### Fixed
- {Bug Fixes}

### Technical
- Files modified: {file_list}
- Tests: {test_count} added/modified
```

**Commit-Zusammenfassung:**
- Erstelle aussagekräftige Commit-Message
- Referenziere Workflow-ID und GitHub Issue

### 4. README/Docs updaten (falls nötig)

- Prüfe ob neue Features dokumentiert werden müssen
- Update API-Dokumentation
- Update Setup-Anweisungen

### 5. Workflow finalisieren

```sql
UPDATE workflows
SET status = 'COMPLETED',
    completed_at = CURRENT_TIMESTAMP
WHERE workflow_id = '{workflow_id}';
```

### 6. Notification

```
✅ Workflow abgeschlossen
Projekt: {project}
Workflow: {workflow_id}
Dauer: {duration}
Tasks: {completed_tasks}/{total_tasks}
Tests: {passed_tests}/{total_tests}
```

## Ausgabe-Format

```
=== DOKUMENTATION ERSTELLT ===
Workflow: WF-2025-XXX

=== CHANGELOG ===
{changelog_entry}

=== COMMIT ===
{suggested_commit_message}

=== STATISTIKEN ===
- Dateien geändert: {files_changed}
- Zeilen hinzugefügt: {lines_added}
- Zeilen entfernt: {lines_removed}
- Dauer: {duration}

=== WORKFLOW ABGESCHLOSSEN ===
```

## Optionen

- `--no-changelog`: Changelog-Update überspringen
- `--dry-run`: Zeige nur was dokumentiert würde
- `--commit`: Erstelle direkt einen Commit
