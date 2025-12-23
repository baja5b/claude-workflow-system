# Workflow Document

Generiere automatisch Dokumentation für das abgeschlossene Issue.

## Anweisungen

### 1. Issue laden

```
Tool: jira_list_by_status
Arguments:
  statuses: ["DOCUMENTATION"]
```

Falls Issue-Key als Argument:
```
Tool: jira_get_issue
Arguments:
  issue_key: $ARGUMENTS
```

```
Tool: jira_get_comments
Arguments:
  issue_key: {KEY}
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
- Jira: {issue_key}
```

### 4. Jira-Kommentar mit Dokumentation

```
Tool: jira_add_comment
Arguments:
  issue_key: {KEY}
  body: |
    [Documentation Complete]

    **Summary:**
    {Was wurde implementiert}

    **Changes:**
    {Liste der Änderungen}

    **Files Modified:**
    {Dateiliste}

    **Testing:**
    - Unit Tests: {count}
    - E2E Tests: {count}

    **Commits:**
    {commit_list}
```

### 5. README/Docs updaten (falls nötig)

- Prüfe ob neue Features dokumentiert werden müssen
- Update API-Dokumentation
- Update Setup-Anweisungen

### 6. Issue abschließen

```
Tool: jira_transition
Arguments:
  issue_key: {KEY}
  status: "DONE"
  comment: "Issue vollständig dokumentiert und abgeschlossen."
```

### 7. Telegram-Benachrichtigung

```
Tool: telegram_workflow_complete
Arguments:
  workflow_id: {issue_key}
  project: {project}
  title: {summary}
  duration_minutes: {duration}
```

### 8. PR erstellen (falls auf Feature-Branch)

```bash
# Prüfe ob auf Feature-Branch
git branch --show-current

# Falls nicht main/develop, erstelle PR
gh pr create --base develop --title "{issue_key}: {summary}" --body "$(cat <<'EOF'
## Summary
{changelog_entry}

## Test plan
- [x] Lokale Tests bestanden
- [x] Automatische Tests bestanden
- [x] Manuelles Testing bestanden
- [x] 4-Augen Review bestanden

Closes #{github_issue_number}
Jira: {issue_key}

Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

## Ausgabe-Format

```
=== DOKUMENTATION ERSTELLT ===
Issue: MT-123

=== CHANGELOG ===
{changelog_entry}

=== STATISTIKEN ===
- Dateien geändert: {files_changed}
- Zeilen hinzugefügt: {lines_added}
- Zeilen entfernt: {lines_removed}
- Dauer: {duration}

=== ISSUE ABGESCHLOSSEN ===
Status: DOCUMENTATION → DONE
```

## Optionen

- `--no-changelog`: Changelog-Update überspringen
- `--dry-run`: Zeige nur was dokumentiert würde
- `--commit`: Erstelle direkt einen Commit
- `--pr`: Erstelle Pull Request
