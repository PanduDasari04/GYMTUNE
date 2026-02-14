import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT
)
""")

# workouts table
cursor.execute("""
CREATE TABLE IF NOT EXISTS workouts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT,
    duration INTEGER,
    calories_burned INTEGER
)
""")

# songs table ⭐ NEW
cursor.execute("""
CREATE TABLE IF NOT EXISTS songs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    genre TEXT,
    artist TEXT
)
""")

conn.commit()
conn.close()

print("Database created successfully")
