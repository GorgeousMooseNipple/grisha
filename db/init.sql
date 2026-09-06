CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    name TEXT NOT NULL,
    notify BOOLEAN NOT NULL CHECK (notify IN (0, 1)),
    was_notified BOOLEAN NOT NULL CHECK (was_notified IN (0, 1)),
    threshold INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS net_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year_month TEXT NOT NULL,
    quota REAL NOT NULL DEFAULT 0,
    used REAL NOT NULL DEFAULT 0
);
