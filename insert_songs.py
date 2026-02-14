import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM songs")  # clear old songs

songs = [
("Song 1","EDM","Artist"),
("Song 2","EDM","Artist"),
("Song 3","Pop","Artist"),
("Song 4","Rock","Artist"),
("Song 5","HipHop","Artist"),
("Song 6","Instrumental","Artist"),
("Song 7","Rock","Artist"),
("Song 8","Pop","Artist"),
("Song 9","EDM","Artist"),
("Song 10","HipHop","Artist")
]

cursor.executemany(
    "INSERT INTO songs(name,genre,artist) VALUES(?,?,?)",
    songs
)

conn.commit()
conn.close()

print("10 songs inserted successfully")
