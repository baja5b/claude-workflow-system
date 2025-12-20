# Workflow Test (4-Augen-Prinzip)

Starte einen unabhängigen Review der Implementierung.

## Anweisungen

Das 4-Augen-Prinzip bedeutet: Eine unabhängige Prüfung der Änderungen
anhand der Original-Anforderungen UND automatisierte Tests auf dem Dev-Server.

### Schritt 1: Aktuellen Workflow laden

```
Tool: workflow_list_active
```

Wähle den Workflow im Status `EXECUTING` oder `TESTING`.

```
Tool: workflow_get
Arguments:
  workflow_id: {ID}
```

### Schritt 2: Status auf TESTING setzen

```
Tool: workflow_update
Arguments:
  workflow_id: {ID}
  status: TESTING
```

### Schritt 3: Deployment prüfen

Prüfe ob das Deployment erfolgreich war:
```
Tool: test_check_deployment
Arguments:
  environment: dev
```

### Schritt 4: Lokale Tests ausführen (vor Merge)

**Pflicht vor jedem Merge:**

```bash
# Lint Check
docker-compose exec backend ruff check . --ignore E501
docker-compose exec frontend npm run lint

# Unit Tests
docker-compose exec backend pytest -v
docker-compose exec frontend npm test

# E2E Tests (bei größeren Änderungen)
docker-compose exec frontend npm run test:smoke
```

### Schritt 5: Comprehensive Tests auf Dev-Server

Führe automatisierte Tests auf dem Dev-Server aus:
```
Tool: test_comprehensive
Arguments:
  environment: dev
  include_smoke_tests: false
```

Dies prüft:
- Health Check (API erreichbar)
- Container Status (alle Container laufen)
- API Endpoints (kritische Endpoints funktionieren)

### Schritt 5b: API Tests

Prüfe kritische API-Endpoints:
```
Tool: test_api_endpoint
Arguments:
  environment: dev
  endpoint: /api/health
  method: GET
```

```
Tool: test_api_endpoint
Arguments:
  environment: dev
  endpoint: /api/songs
  method: GET
```

```
Tool: test_api_endpoint
Arguments:
  environment: dev
  endpoint: /api/events
  method: GET
```

### Schritt 6: Test-Ergebnisse speichern

Für jeden Test-Typ:
```
Tool: workflow_add_test_result
Arguments:
  workflow_id: {ID}
  test_type: "health" | "api" | "container"
  test_name: {Name des Tests}
  passed: true/false
  output: {Test-Output}
```

### Schritt 7: 4-Augen Code Review

Spawne einen Task Agent für den Code Review:

```
Tool: Task
Arguments:
  subagent_type: general-purpose
  description: "Code Review for workflow"
  prompt: |
    Du bist ein unabhängiger Code Reviewer.

    ORIGINAL-ANFORDERUNGEN:
    {requirements aus workflow}

    GIT ÄNDERUNGEN:
    {führe git diff aus}

    Prüfe:
    1. Erfüllen die Änderungen die Anforderungen?
    2. Gibt es offensichtliche Bugs?
    3. Code-Qualität OK?

    Antworte mit: PASS oder FAIL mit Begründung.
```

### Schritt 8: Ergebnis auswerten

Bei **PASS** (alle Tests bestanden):
```
Tool: workflow_update
Arguments:
  workflow_id: {ID}
  status: COMPLETED
```

```
Tool: telegram_send
Arguments:
  message: |
    ✅ *4-Augen Test bestanden*

    *ID:* `{workflow_id}`
    *Titel:* {title}

    ✅ Health Check
    ✅ Container Status
    ✅ API Endpoints
    ✅ Code Review

    Workflow abgeschlossen!
```

Bei **FAIL**:
```
Tool: telegram_send
Arguments:
  message: |
    ❌ *Test fehlgeschlagen*

    *ID:* `{workflow_id}`
    *Fehler:* {failed_tests}

    Bitte prüfen und beheben.
```

### Schritt 9: Optional - Smoke Tests

Falls kritische Änderungen:
```
Tool: test_run_smoke_tests
Arguments:
  environment: dev
  project_path: {Pfad zum MusicTracker Projekt}
```

## Ausgabe-Format

```
=== 4-AUGEN TEST ===
Workflow: WF-2025-XXX

🔍 Lokale Tests (vor Merge):
✅ Lint: ruff + eslint OK
✅ Unit Tests: pytest + jest OK
✅ E2E Tests: Playwright OK

🔍 Dev-Server Tests:
✅ Health Check: API erreichbar
✅ Container: 6/6 running
✅ API Endpoints: /health, /songs, /events OK

🔍 Code Review:
✅ Anforderungen erfüllt
✅ Keine offensichtlichen Bugs
✅ Code-Qualität akzeptabel
✅ Logging vorhanden
✅ Keine Inline-Styles

=== TEST ERGEBNIS: BESTANDEN ===

Workflow wird als COMPLETED markiert.
```

## Wichtig

- Der Test läuft auf dem DEV-Server (NICHT Produktion!)
- Code Review ist isoliert (nur Requirements + Diff)
- Bei Fehlern: Workflow bleibt in TESTING
