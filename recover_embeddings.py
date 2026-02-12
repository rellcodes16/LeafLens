import os
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_FOLDER = r"C:\Users\DELL\Desktop\LeafLens\models\all-MiniLM-L6-v2"
BOOKS_DIR = "data/books"
DB_PATH = "books.db"

CHUNK_SIZE = 280
OVERLAP = 90
BATCH_SIZE = 16


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + chunk_size]))
        i += chunk_size - overlap
    return chunks


model = SentenceTransformer(
    MODEL_FOLDER,
    device="cpu",
    backend="onnx",
    model_kwargs={"file_name": "onnx/model.onnx"}
)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

books = c.execute("SELECT book_id FROM books").fetchall()

for (book_id,) in books:
    count = c.execute(
        "SELECT COUNT(*) FROM chunks WHERE book_id=?",
        (book_id,)
    ).fetchone()[0]

    if count > 0:
        continue 

    print(f" Recovering missing chunks for: {book_id}")

    path = os.path.join(BOOKS_DIR, f"{book_id}.txt")
    if not os.path.exists(path):
        print("⚠️ File missing, skipping")
        continue

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    chunks = chunk_text(text)

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        embeddings = model.encode(batch, convert_to_numpy=True)

        for chunk, emb in zip(batch, embeddings):
            c.execute(
                "INSERT INTO chunks (book_id, chunk_text, embedding) VALUES (?, ?, ?)",
                (book_id, chunk, emb.astype("float16").tobytes())
            )

    conn.commit()
    print(" Recovered")

conn.close()
print("\n Recovery complete.")
