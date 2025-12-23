# Workflow Status

Zeige den Status der Jira-Issues und Workflows.

## Anweisungen

### Status-Abfrage

**Alle aktiven Issues abrufen:**
```
Tool: jira_get_workable
```

**Alternativ: Issues nach Status:**
```
Tool: jira_list_by_status
Arguments:
  statuses: ["TO DO", "PLANNED", "PLANNED AND CONFIRMED", "IN PROGRESS", "REVIEW", "TESTING", "MANUAL TESTING", "DOCUMENTATION"]
```

**Spezifisches Issue (falls Key angegeben):**
```
Tool: jira_get_issue
Arguments:
  issue_key: $ARGUMENTS
```

**Kommentare des Issues:**
```
Tool: jira_get_comments
Arguments:
  issue_key: {KEY}
```

### Ausgabe-Format

```
=== JIRA WORKFLOW STATUS ===

=== BOARD ÜBERSICHT ===
TO DO:              {count}
PLANNED:            {count}
CONFIRMED:          {count}
IN PROGRESS:        {count}
REVIEW:             {count}
TESTING:            {count}
MANUAL TESTING:     {count}
DOCUMENTATION:      {count}

=== AKTIVE ISSUES ===
[IN PROGRESS] MT-123: Feature implementieren
[TESTING]     MT-122: Bug Fix validieren
[REVIEW]      MT-121: Refactoring abschließen

=== NÄCHSTE AKTIONEN ===
MT-123: Warte auf Implementierung
MT-122: Tests ausführen
MT-121: Code-Review durchführen
```

### Einzelnes Issue

Falls Issue-Key angegeben:
```
=== ISSUE DETAILS ===
Key:        {key}
Titel:      {summary}
Typ:        {issue_type}
Status:     {status}
Erstellt:   {created}

=== BESCHREIBUNG ===
{description}

=== KOMMENTARE ({count}) ===
{Für jeden Kommentar:}
[{author}] {created}:
{body}

=== VERFÜGBARE TRANSITIONS ===
{Für jede Transition:}
→ {name}
```

### Status-Bedeutung

| Status | Bedeutung | Nächster Schritt |
|--------|-----------|------------------|
| TO DO | Neu, warte auf Planung | Automatisch → PLANNED |
| PLANNED | Plan erstellt | User prüft, dann → CONFIRMED |
| PLANNED AND CONFIRMED | Plan bestätigt | Automatisch → IN PROGRESS |
| IN PROGRESS | Wird bearbeitet | Bei Fertigstellung → REVIEW |
| REVIEW | Code-Review | Automatisch → TESTING |
| TESTING | Automatische Tests | Automatisch → MANUAL TESTING |
| MANUAL TESTING | User testet | User entscheidet → DOCUMENTATION |
| DOCUMENTATION | Doku wird erstellt | Automatisch → DONE |
| DONE | Abgeschlossen | - |

### Kein Issue gefunden

Falls kein aktives Issue existiert:

```
=== KEINE AKTIVEN ISSUES ===

Alle Issues sind entweder:
- DONE (abgeschlossen)
- MANUAL TESTING (warte auf User)

Erstelle ein neues Issue in Jira oder prüfe das Board.

Oder starte mit:
/workflow:start "Beschreibung der Aufgabe"
```

## Optionen

- Ohne Argument: Zeige Board-Übersicht
- Mit Issue-Key: Zeige Issue-Details
- `--all`: Zeige alle Issues inkl. DONE
- `--comments`: Zeige Kommentare

## Nächste Schritte je nach Status

| Status | Nächster Befehl |
|--------|-----------------|
| PLANNED | Plan prüfen, dann in Jira → CONFIRMED verschieben |
| MANUAL TESTING | Testen, dann in Jira → DOCUMENTATION verschieben |
| Steckengeblieben | `/workflow:start-working` für automatische Verarbeitung |
