import os
import sqlite3
import hashlib
import re

# ---------------- CONFIG ----------------
BOOKS_DIR = "data/books"
DB_PATH = "books.db"

WINDOW_SIZES = [6, 7, 8]   # multi-scale = OCR tolerant
STEP = 1
# --------------------------------------


def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fingerprint_text(text, window_size):
    words = text.split()
    for i in range(0, len(words) - window_size + 1, STEP):
        window = " ".join(words[i:i + window_size])
        h = hashlib.md5(window.encode("utf-8")).hexdigest()[:16]
        yield h, i



# ---------------- DB SETUP ----------------
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS books (
    book_id TEXT PRIMARY KEY,
    title TEXT,
    author TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS fingerprints (
    hash TEXT,
    book_id TEXT,
    position INTEGER
)
""")

c.execute("""
CREATE INDEX IF NOT EXISTS idx_fingerprint_hash
ON fingerprints(hash)
""")

conn.commit()

# ---------------- INDEX BOOKS ----------------
files = [f for f in os.listdir(BOOKS_DIR) if f.endswith(".txt")]

for filename in files:
    book_id = filename.replace(".txt", "")
    path = os.path.join(BOOKS_DIR, filename)

    # Skip if already indexed
    exists = c.execute(
        "SELECT 1 FROM fingerprints WHERE book_id=? LIMIT 1",
        (book_id,)
    ).fetchone()

    if exists:
        print(f" Skipping already indexed: {book_id}")
        continue

    print(f"\n📘 Indexing (Shazam-style): {book_id}")

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        raw_text = f.read()

    text = normalize_text(raw_text)

    c.execute(
        "INSERT OR IGNORE INTO books (book_id, title, author) VALUES (?, ?, ?)",
        (book_id, book_id.replace("_", " ").title(), "Unknown")
    )

    inserts = []

    for w in WINDOW_SIZES:
        for h, pos in fingerprint_text(text, w):
            inserts.append((h, book_id, pos))

    c.executemany(
        "INSERT INTO fingerprints (hash, book_id, position) VALUES (?, ?, ?)",
        inserts
    )

    conn.commit()
    print(f"Stored {len(inserts)} fingerprints")

conn.close()
print("\n Shazam-style indexing complete.")
