from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = "gymtune_secret"

def get_db():
    return sqlite3.connect("database.db")

# LOGIN PAGE
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        user = cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email,password)
        ).fetchone()

        conn.close()

        if user:
            session["user_id"] = user[0]
            return redirect("/dashboard")

    return render_template("login.html")

# REGISTER PAGE
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users(name,email,password) VALUES(?,?,?)",
                (name,email,password)
            )
            conn.commit()
            conn.close()
            return redirect("/")
        except:
            conn.close()
            return "Email already registered! Go back and login."

    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    message = request.args.get("msg")

    conn = get_db()
    cursor = conn.cursor()

    # totals
    total_workouts = cursor.execute(
        "SELECT COUNT(*) FROM workouts WHERE user_id=?",
        (session["user_id"],)
    ).fetchone()[0]

    total_duration = cursor.execute(
        "SELECT SUM(duration) FROM workouts WHERE user_id=?",
        (session["user_id"],)
    ).fetchone()[0]

    total_calories = cursor.execute(
        "SELECT SUM(calories_burned) FROM workouts WHERE user_id=?",
        (session["user_id"],)
    ).fetchone()[0]

    if total_duration is None:
        total_duration = 0
    if total_calories is None:
        total_calories = 0

    # chart data
    chart_data = cursor.execute(
        "SELECT date, COUNT(*) FROM workouts WHERE user_id=? GROUP BY date",
        (session["user_id"],)
    ).fetchall()

    dates = [row[0] for row in chart_data]
    counts = [row[1] for row in chart_data]

    # quit risk prediction
    last_workout = cursor.execute(
        "SELECT date FROM workouts WHERE user_id=? ORDER BY date DESC LIMIT 1",
        (session["user_id"],)
    ).fetchone()

    risk = "LOW"
    if last_workout:
        last_date = datetime.strptime(last_workout[0], "%Y-%m-%d")
        days_gap = (datetime.now() - last_date).days

        if days_gap > 7:
            risk = "HIGH"
        elif days_gap > 3:
            risk = "MEDIUM"

    # 🔥 streak calculation
    dates_data = cursor.execute(
        "SELECT date FROM workouts WHERE user_id=? ORDER BY date DESC",
        (session["user_id"],)
    ).fetchall()

    streak = 0
    current_day = date.today()

    for row in dates_data:
        workout_day = datetime.strptime(row[0], "%Y-%m-%d").date()
        if workout_day == current_day:
            streak += 1
            current_day -= timedelta(days=1)
        else:
            break

    # 🎯 weekly goal
    week_ago = date.today() - timedelta(days=7)
    weekly_count = cursor.execute(
        "SELECT COUNT(*) FROM workouts WHERE user_id=? AND date>=?",
        (session["user_id"], str(week_ago))
    ).fetchone()[0]
    weekly_goal = 5

    # 📊 average duration (Data Science)
    avg_duration = cursor.execute(
        "SELECT AVG(duration) FROM workouts WHERE user_id=?",
        (session["user_id"],)
    ).fetchone()[0]

    if avg_duration is None:
        avg_duration = 0

    # 📊 most active day of week
    day_data = cursor.execute("""
        SELECT strftime('%w', date), COUNT(*) 
        FROM workouts 
        WHERE user_id=? 
        GROUP BY strftime('%w', date)
    """, (session["user_id"],)).fetchall()

    days_map = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
    most_active_day = "N/A"
    song_list = []

    if day_data:
        most_active_day_idx = max(day_data, key=lambda x: x[1])[0]
        most_active_day = days_map[int(most_active_day_idx)]
        
        # 🎵 get all songs
        songs_db = cursor.execute("SELECT name FROM songs").fetchall()
        song_list = [s[0] for s in songs_db]

    # 📊 Monthly calories (Now inside the function)
    month_ago = date.today() - timedelta(days=30)
    monthly_calories = cursor.execute(
        "SELECT SUM(calories_burned) FROM workouts WHERE user_id=? AND date>=?",
        (session["user_id"], str(month_ago))
    ).fetchone()[0]

    if monthly_calories is None:
        monthly_calories = 0

    # ⏱ Longest workout
    longest_workout = cursor.execute(
        "SELECT MAX(duration) FROM workouts WHERE user_id=?",
        (session["user_id"],)
    ).fetchone()[0]

    if longest_workout is None:
        longest_workout = 0

    # 📈 Consistency score (last 30 days)
    days_active = cursor.execute(
        "SELECT COUNT(DISTINCT date) FROM workouts WHERE user_id=? AND date>=?",
        (session["user_id"], str(month_ago))
    ).fetchone()[0]
    consistency = int((days_active / 30) * 100)

    conn.close()

    return render_template(
        "dashboard.html",
        workouts=total_workouts,
        duration=total_duration,
        calories=total_calories,
        risk=risk,
        dates=dates,
        counts=counts,
        message=message,
        streak=streak,
        weekly_count=weekly_count,
        weekly_goal=weekly_goal,
        avg_duration=round(avg_duration,1),
        most_active_day=most_active_day,
        songs=song_list,
        monthly_calories=monthly_calories,
        longest_workout=longest_workout,
        consistency=consistency
    )

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/start_workout")
def start_workout():
    if "user_id" not in session:
        return redirect("/")

    # save start time in session
    session["workout_start"] = datetime.now().strftime("%H:%M:%S")

    return redirect("/dashboard?msg=Workout Started! Click Stop when finished.")

@app.route("/stop_workout")
def stop_workout():
    if "user_id" not in session:
        return redirect("/")

    if "workout_start" not in session:
        return redirect("/dashboard?msg=Start workout first!")

    # get start time from session
    start_time_str = session["workout_start"]
    start_time = datetime.strptime(start_time_str, "%H:%M:%S")
    now = datetime.now()
    
    # Calculate duration by combining today's date with start time
    start_datetime = datetime.combine(date.today(), start_time.time())
    duration = int((now - start_datetime).total_seconds() / 60)

    if duration < 1:
        duration = 1

    calories = duration * 5
    today = str(date.today())

    conn = get_db()
    cursor = conn.cursor()

    # prevent multiple workouts per day
    existing = cursor.execute(
        "SELECT * FROM workouts WHERE user_id=? AND date=?",
        (session["user_id"], today)
    ).fetchone()

    if existing:
        conn.close()
        session.pop("workout_start")
        return redirect("/dashboard?msg=Workout already saved today!")

    # save workout
    cursor.execute(
        "INSERT INTO workouts(user_id,date,duration,calories_burned) VALUES(?,?,?,?)",
        (session["user_id"], today, duration, calories)
    )

    conn.commit()
    conn.close()

    session.pop("workout_start")

    return redirect("/dashboard?msg=Workout Saved Successfully!")

@app.route("/history")
def history():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    data = cursor.execute(
        "SELECT date, duration, calories_burned FROM workouts WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template("history.html", workouts=data)

@app.route("/download")
def download():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    data = cursor.execute(
        "SELECT date, duration, calories_burned FROM workouts WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    df = pd.DataFrame(data, columns=["Date","Duration","Calories"])
    df.to_excel("report.xlsx", index=False)

    return send_file("report.xlsx", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)