import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# get all users
users = cursor.execute("SELECT id FROM users").fetchall()

today = datetime.now()

for user in users:
    user_id = user[0]

    for i in range(30):   # 30 workouts per user
        days_ago = random.randint(0, 30)
        date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        duration = random.randint(20, 60)
        calories = duration * 5

        cursor.execute(
            "INSERT INTO workouts(user_id,date,duration,calories_burned) VALUES(?,?,?,?)",
            (user_id, date, duration, calories)
        )

conn.commit()
conn.close()

print("Demo data generated for all users")
