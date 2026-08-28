DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    required_notifications BOOLEAN NOT NULL CHECK (required_notifications IN (0, 1))
);

DROP TABLE IF EXISTS net_usage;
CREATE TABLE net_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    mb_used INTEGER NOT NULL DEFAULT 0
);
