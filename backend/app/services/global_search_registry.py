# Minimal path-only search registry entries.
# Each entry describes searchable columns and possible navigation paths.

REGISTRY = [
    {
        "table": "case",
        "columns": ["case_number"],
        "boost": 3.0,
        "routes": [
            {"path": "/cases/{case.case_number}/core/intake", "priority": 1.0}
        ]
    },
    {
        "table": "task",
        "columns": ["title"],
        "boost": 1.5,
        "routes": [
            {"path": "/cases/{case.case_number}/tasks/{task.id}", "priority": 2.0},
            {"path": "/cases/{case.case_number}/tasks", "priority": 1.0}
        ]
    },
    {
        "table": "message",
        "columns": ["message"],
        "boost": 1.5,
        "routes": [
            {"path": "/cases/{case.case_number}/tasks/{message.task_id}", "when": "message.task_id IS NOT NULL", "priority": 2.0},
            {"path": "/cases/{case.case_number}/messages", "priority": 1.0}
        ]
    },
]
