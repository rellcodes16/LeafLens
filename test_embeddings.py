import sqlite3, numpy as np

conn = sqlite3.connect("books.db")
c = conn.cursor()
row = c.execute("SELECT embedding FROM chunks LIMIT 1").fetchone()[0]

dim = 384
emb = np.frombuffer(row, dtype=np.float16)
print("len:", len(emb))
print("dim:", dim)
print("reshape works?", len(emb) == dim)
