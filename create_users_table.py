import sqlite3
from pathlib import Path

# Project folder
PROJECT_ROOT = Path(__file__).resolve().parent

# Existing SQLite database
DB_PATH = PROJECT_ROOT / "data" / "mumbai_safety.db"

print("Database:", DB_PATH)

# Connect to database
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# Create users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

connection.commit()
connection.close()

print("Users table created successfully!")