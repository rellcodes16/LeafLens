import easyocr
import re
import os
import faiss
import numpy as np
import sqlite3
import cv2
from sentence_transformers import SentenceTransformer
from collections import Counter


# PATHS
BOOKS_DIR = "data/books"
INDEX_PATH = "books.index"
META_PATH = "books_meta.npy"
MPNET_EMB_PATH = "mpnet_embeddings.npy"
DB_PATH = "books.db"

CHUNK_SIZE = 800
OCR_CHUNK_SIZE = 600
TOP_K = 6
MAX_RERANK_BOOKS = 4
MAX_RERANK_PREVIEWS = 8
CONFIDENCE_THRESHOLD = 0.25
MIN_VOTE_ACCEPT = 3

MINILM_DIR = "./models/minilm"
MPNET_DIR = "./models/mpnet"

ANTHOLOGY_KEYWORDS = [
    "complete works",
    "collected works",
    "collection",
    "anthology",
    "全集"
]

# UTIL
def is_anthology(title):
    return any(word in title.lower() for word in ANTHOLOGY_KEYWORDS)

def load_model_local(model_name, save_path):
    if not os.path.exists(save_path):
        model = SentenceTransformer(model_name)
        os.makedirs(save_path, exist_ok=True)
        model.save(save_path)
    return SentenceTransformer(save_path)

print("Loading models (CPU)...")

reader = easyocr.Reader(["en"], gpu=False)

miniLM = load_model_local("all-MiniLM-L6-v2", MINILM_DIR)
mpnet = load_model_local("sentence-transformers/all-mpnet-base-v2", MPNET_DIR)

# BUILD INDEX (MiniLM ONLY)
def build_index():

    files = [f for f in os.listdir(BOOKS_DIR) if f.endswith(".txt")]

    embeddings = []
    metadata = []

    print(f"Indexing {len(files)} books...")

    for filename in files:

        path = os.path.join(BOOKS_DIR, filename)

        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = [
            text[i:i+CHUNK_SIZE]
            for i in range(0, len(text), CHUNK_SIZE)
        ]

        mini_emb = miniLM.encode(
            chunks,
            batch_size=32,
            show_progress_bar=False
        ).astype("float32")

        for chunk, emb in zip(chunks, mini_emb):

            embeddings.append(emb)
            metadata.append({
                "book": filename,
                "preview": chunk[:250]
            })

    embeddings = np.array(embeddings)

    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)
    np.save(META_PATH, metadata)

    print("MiniLM index built successfully!")

if not os.path.exists(INDEX_PATH):
    build_index()

# LOAD INDEX + MPNet CACHE
print("Loading FAISS index...")
index = faiss.read_index(INDEX_PATH)

print("Loading metadata...")
metadata = np.load(META_PATH, allow_pickle=True)

print("Loading MPNet cache...")
mpnet_meta = np.load(MPNET_EMB_PATH)

book_to_indices = {}
for i, m in enumerate(metadata):
    book_to_indices.setdefault(m["book"], []).append(i)

print("System ready.")

# AUTHOR LOOKUP
def get_author_from_db(filename):

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    title_guess = filename.replace(".txt", "").lower()

    row = c.execute(
        "SELECT author FROM books WHERE LOWER(title)=?",
        (title_guess,)
    ).fetchone()

    conn.close()

    return row[0] if row and row[0] else "Unknown"


# OCR
def extract_text(image_path):

    img = cv2.imread(image_path)

    if img is None:
        return ""

    h, w = img.shape[:2]

    if w > 1200:
        scale = 1200 / w
        img = cv2.resize(img, None, fx=scale, fy=scale)

    result = reader.readtext(
        img,
        detail=0,
        paragraph=False
    )

    return " ".join(result)

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def chunk_text(text):
    chunks = [
        text[i:i+OCR_CHUNK_SIZE]
        for i in range(0, len(text), OCR_CHUNK_SIZE)
    ]
    return [c for c in chunks if len(c) > 80]


# FAST RETRIEVAL (MiniLM)
def fast_search(chunks):

    emb = miniLM.encode(
        chunks,
        batch_size=32
    ).astype("float32")

    faiss.normalize_L2(emb)

    D, I = index.search(emb, TOP_K)

    candidates = []

    for neighbors in I:
        for idx in neighbors:
            candidates.append(metadata[idx]["book"])

    return candidates

# RERANK (MPNet - PRECOMPUTED)
def rerank_candidates(chunks, candidate_books):

    vote_counter = Counter(candidate_books)
    top_books = [b for b, _ in vote_counter.most_common(MAX_RERANK_BOOKS)]

    emb_query = mpnet.encode(
        chunks,
        batch_size=16
    ).astype("float32")

    emb_query /= np.linalg.norm(emb_query, axis=1, keepdims=True)

    scores = {}

    for book in top_books:

        indices = book_to_indices[book][:MAX_RERANK_PREVIEWS]
        emb_book = mpnet_meta[indices]

        emb_book = emb_book / np.linalg.norm(
            emb_book,
            axis=1,
            keepdims=True
        )

        sim = np.dot(emb_query, emb_book.T)
        score = float(sim.mean())

        if is_anthology(book):
            score *= 0.85

        scores[book] = score

    best_book = max(scores, key=scores.get)
    return best_book, scores[best_book], vote_counter

# IDENTIFY BOOK
def identify_book(image_path):

    raw = extract_text(image_path)
    clean = clean_text(raw)

    if len(clean) < 100:
        return {"status": "fail", "reason": "Not enough readable text"}

    chunks = chunk_text(clean)

    if not chunks:
        return {"status": "fail", "reason": "No usable text detected"}

    candidates = fast_search(chunks)

    if not candidates:
        return {"status": "fail", "reason": "No matches found"}

    best_book, best_score, votes = rerank_candidates(chunks, candidates)

    top_vote_book = votes.most_common(1)[0][0]
    top_vote_count = votes[top_vote_book]

    final_book = best_book

    if top_vote_count >= MIN_VOTE_ACCEPT:
        final_book = top_vote_book

    if best_score >= CONFIDENCE_THRESHOLD or top_vote_count >= MIN_VOTE_ACCEPT:

        author = get_author_from_db(final_book)

        return {
            "status": "success",
            "book": final_book,
            "author": author,
            "confidence": round(float(best_score), 3),
            "votes": top_vote_count
        }

    return {"status": "fail", "reason": "Low confidence"}

# MAIN
if __name__ == "__main__":

    image_path = input("Enter image path: ")

    result = identify_book(image_path)

    print("\nRESULT:")
    print(result)
