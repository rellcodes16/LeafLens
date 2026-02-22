import sqlite3

conn = sqlite3.connect("books.db")
c = conn.cursor()

rows = c.execute("SELECT book_id FROM books LIMIT 30").fetchall()

for r in rows:
    print(r[0])

conn.close()
