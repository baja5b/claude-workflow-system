# Workflow Document

Generiere automatisch Dokumentation für den abgeschlossenen Workflow.

## Anweisungen

### 1. Workflow-Daten laden

```
Tool: workflow_list_active
```

Wähle den Workflow im Status `TESTING` oder `COMPLETED`.

```
Tool: workflow_get
Arguments:
  workflow_id: {ID}
```

```
Tool: workflow_get_tasks
Arguments:
  workflow_id: {ID}
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

```
Tool: workflow_update
Arguments:
  workflow_id: {ID}
  status: COMPLETED
```

### 6. Telegram-Benachrichtigung

```
Tool: telegram_workflow_complete
Arguments:
  workflow_id: {workflow_id}
  project: {project}
  title: {title}
  duration_minutes: {duration_minutes}
```

### 7. PR erstellen (falls auf Feature-Branch)

```bash
# Prüfe ob auf Feature-Branch
git branch --show-current

# Falls nicht main/develop, erstelle PR
gh pr create --base develop --title "{title}" --body "$(cat <<'EOF'
## Summary
{changelog_entry}

## Test plan
- [x] Lokale Tests bestanden
- [x] Dev-Server Tests bestanden
- [x] 4-Augen Review bestanden

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
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
