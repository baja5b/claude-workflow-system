-- Claude Workflow System - SQLite Schema
-- Version: 1.0.0

-- Workflows table - main workflow tracking
CREATE TABLE IF NOT EXISTS workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT UNIQUE NOT NULL,           -- Format: WF-YYYY-NNN
    project TEXT NOT NULL,                       -- Project directory name
    project_path TEXT,                           -- Full path to project
    title TEXT NOT NULL,                         -- Workflow title/description
    status TEXT NOT NULL DEFAULT 'PLANNING',     -- Current status
    requirements TEXT,                           -- JSON: Original requirements
    plan TEXT,                                   -- JSON: Implementation plan
    github_issue_number INTEGER,                 -- Linked GitHub issue
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,                         -- When execution started
    completed_at DATETIME,                       -- When workflow completed

    CHECK (status IN ('PLANNING', 'CONFIRMED', 'EXECUTING', 'TESTING', 'DOCUMENTING', 'COMPLETED', 'REJECTED', 'FAILED'))
);

-- Tasks table - individual tasks within a workflow
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL,                   -- Reference to workflows.workflow_id
    sequence INTEGER NOT NULL,                   -- Order of execution (1, 2, 3...)
    description TEXT NOT NULL,                   -- What this task does
    status TEXT NOT NULL DEFAULT 'PENDING',      -- Current status
    result TEXT,                                 -- JSON: Task result/output
    error_message TEXT,                          -- Error if failed
    started_at DATETIME,
    completed_at DATETIME,

    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'SKIPPED')),
    UNIQUE (workflow_id, sequence)
);

-- Notifications table - track sent notifications
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL,                   -- Reference to workflows.workflow_id
    notification_type TEXT NOT NULL,             -- Type: start, end, error, decision
    channel TEXT NOT NULL DEFAULT 'telegram',    -- telegram, signal, etc.
    message TEXT NOT NULL,                       -- Message content
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    delivered BOOLEAN DEFAULT FALSE,             -- Confirmed delivery

    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    CHECK (notification_type IN ('start', 'end', 'error', 'decision', 'progress'))
);

-- Test results table - 4-eyes test results
CREATE TABLE IF NOT EXISTS test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL,                   -- Reference to workflows.workflow_id
    test_type TEXT NOT NULL,                     -- unit, integration, e2e, review
    test_name TEXT NOT NULL,                     -- Name of the test
    passed BOOLEAN NOT NULL,                     -- Pass/fail
    output TEXT,                                 -- Test output/logs
    executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_project ON workflows(project);
CREATE INDEX IF NOT EXISTS idx_workflows_created ON workflows(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_workflow ON tasks(workflow_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_notifications_workflow ON notifications(workflow_id);
CREATE INDEX IF NOT EXISTS idx_test_results_workflow ON test_results(workflow_id);

-- Trigger to update updated_at on workflow changes
CREATE TRIGGER IF NOT EXISTS update_workflow_timestamp
    AFTER UPDATE ON workflows
    FOR EACH ROW
BEGIN
    UPDATE workflows SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- View for active workflows
CREATE VIEW IF NOT EXISTS active_workflows AS
SELECT
    w.*,
    COUNT(t.id) as total_tasks,
    SUM(CASE WHEN t.status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_tasks,
    SUM(CASE WHEN t.status = 'FAILED' THEN 1 ELSE 0 END) as failed_tasks
FROM workflows w
LEFT JOIN tasks t ON w.workflow_id = t.workflow_id
WHERE w.status NOT IN ('COMPLETED', 'REJECTED', 'FAILED')
GROUP BY w.id;

-- View for workflow summary
CREATE VIEW IF NOT EXISTS workflow_summary AS
SELECT
    w.workflow_id,
    w.project,
    w.title,
    w.status,
    w.created_at,
    w.completed_at,
    COUNT(t.id) as total_tasks,
    SUM(CASE WHEN t.status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_tasks,
    COUNT(tr.id) as total_tests,
    SUM(CASE WHEN tr.passed THEN 1 ELSE 0 END) as passed_tests
FROM workflows w
LEFT JOIN tasks t ON w.workflow_id = t.workflow_id
LEFT JOIN test_results tr ON w.workflow_id = tr.workflow_id
GROUP BY w.id
ORDER BY w.created_at DESC;
