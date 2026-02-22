import easyocr
import re
import os
import faiss
import numpy as np
import sqlite3
import cv2
import time
from datetime import datetime
from sentence_transformers import SentenceTransformer
from collections import Counter, defaultdict


# CONFIG
INDEX_PATH = r"C:\Users\DELL\Desktop\LeafLens\books.index"
META_PATH = r"C:\Users\DELL\Desktop\LeafLens\books_meta.npy"
MPNET_EMB_PATH = r"C:\Users\DELL\Desktop\LeafLens\mpnet_embeddings.npy"
DB_PATH = r"C:\Users\DELL\Desktop\LeafLens\books.db"

OCR_CHUNK_SIZE = 450
TOP_K = 6
MAX_RERANK_PREVIEWS = 12

CONFIDENCE_THRESHOLD = 0.25
MIN_VOTE_ACCEPT = 3

MPNET_DIR = "./models/mpnet"
MINILM_DIR = "./models/minilm"

ANTHOLOGY_KEYWORDS = [
    "complete works",
    "collected works",
    "collection",
    "anthology",
    "全集"
]


# TIMESTAMP LOGGER
GLOBAL_START = time.time()

def log_stage(stage_name, stage_start):
    now = time.time()
    total_elapsed = now - GLOBAL_START
    stage_elapsed = now - stage_start

    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] "
        f"{stage_name} | "
        f"Stage: {stage_elapsed:.2f}s | "
        f"Total: {total_elapsed:.2f}s"
    )

# HELPERS
def is_anthology(title):
    return any(word in title.lower() for word in ANTHOLOGY_KEYWORDS)


def load_model_local(model_name, save_path):
    start = time.time()
    if not os.path.exists(save_path):
        model = SentenceTransformer(model_name)
        os.makedirs(save_path, exist_ok=True)
        model.save(save_path)
    model = SentenceTransformer(save_path)
    log_stage(f"Loaded model: {model_name}", start)
    return model


def is_mostly_english(text):
    letters = re.findall(r"[a-zA-Z]", text)
    return len(letters) / max(len(text), 1) > 0.6


def get_author_from_db(book_id: str) -> str:
    start = time.time()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    book_id = book_id.replace(".txt", "").lower()

    row = c.execute(
        "SELECT author FROM books WHERE LOWER(book_id)=?",
        (book_id,),
    ).fetchone()

    conn.close()

    log_stage("Database author lookup", start)

    return row[0] if row and row[0].strip() else "Unknown"

# OCR
def extract_text(image_path):
    start = time.time()

    img = cv2.imread(image_path)

    if img is None:
        return ""

    h, w = img.shape[:2]
    max_dim = 1200

    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    result = reader.readtext(img, detail=0)

    log_stage("OCR extraction", start)

    return " ".join(result)


def clean_text(text):
    start = time.time()

    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    log_stage("Text cleaning", start)

    return text.strip()


def chunk_text(text):
    start = time.time()

    chunks = [text[i:i + OCR_CHUNK_SIZE] for i in range(0, len(text), OCR_CHUNK_SIZE)]
    chunks = [c for c in chunks if len(c) > 50]

    log_stage("Text chunking", start)

    return chunks

# FAST SEARCH
def fast_search(chunks):
    start = time.time()

    emb = miniLM.encode(chunks, batch_size=8).astype("float32")
    faiss.normalize_L2(emb)

    D, I = index.search(emb, TOP_K)

    candidates = []
    for neighbors in I:
        for idx in neighbors:
            candidates.append(metadata[idx]["book"])

    log_stage("MiniLM encode + FAISS search", start)

    return candidates

# RERANK
def rerank_candidates(chunks, candidate_books):
    start = time.time()

    if not candidate_books:
        return None, 0

    emb_query = mpnet.encode(chunks, batch_size=8)
    emb_query = emb_query / np.linalg.norm(emb_query, axis=1, keepdims=True)

    scores = {}

    for book in set(candidate_books):

        preview_indices = book_to_indices.get(book, [])[:MAX_RERANK_PREVIEWS]

        if not preview_indices:
            continue

        emb_book = mpnet_embeddings[preview_indices]
        sim = np.dot(emb_query, emb_book.T)
        score = sim.mean()

        if is_anthology(book):
            score *= 0.80

        scores[book] = score

    if not scores:
        return None, 0

    best_book = max(scores, key=scores.get)

    log_stage("MPNet reranking", start)

    return best_book, scores[best_book]


# LOAD EVERYTHING
print("================================")
print("System Initializing...")
print("================================")

reader_start = time.time()
reader = easyocr.Reader(["en"], gpu=False)
log_stage("EasyOCR loaded", reader_start)

miniLM = load_model_local("all-MiniLM-L6-v2", MINILM_DIR)
mpnet = load_model_local("sentence-transformers/all-mpnet-base-v2", MPNET_DIR)

start = time.time()
index = faiss.read_index(INDEX_PATH)
log_stage("FAISS index loaded", start)

start = time.time()
metadata = np.load(META_PATH, allow_pickle=True)
log_stage("Metadata loaded", start)

start = time.time()
mpnet_embeddings = np.load(MPNET_EMB_PATH)
mpnet_embeddings = mpnet_embeddings / np.linalg.norm(
    mpnet_embeddings, axis=1, keepdims=True
)
log_stage("MPNet embeddings loaded + normalized", start)

start = time.time()
book_to_indices = defaultdict(list)
for i, m in enumerate(metadata):
    book_to_indices[m["book"]].append(i)
log_stage("Book preview index map built", start)

print("================================")
print("System ready.")
print("================================")

# MAIN SEARCH
def run_image_search(image_path: str):
    pipeline_start = time.time()

    raw = extract_text(image_path)
    if not raw.strip():
        return {"status": "fail", "reason": "No readable text detected"}
    if not is_mostly_english(raw):
        return {"status": "fail", "reason": "Only English books supported"}

    clean = clean_text(raw)
    if len(clean.split()) < 10:
        return {"status": "fail", "reason": "Too little readable text"}
    if len(clean) < 80:
        return {"status": "fail", "reason": "Not enough readable text"}

    chunks = chunk_text(clean)

    candidates = fast_search(chunks)
    if not candidates:
        return {"status": "fail", "reason": "No matches found"}

    best_book, best_score = rerank_candidates(chunks, candidates)

    votes = Counter(candidates)
    top_vote_book, top_vote_count = votes.most_common(1)[0]

    FINAL_BOOK = best_book

    if is_anthology(FINAL_BOOK):
        if not is_anthology(top_vote_book) and top_vote_count >= MIN_VOTE_ACCEPT:
            FINAL_BOOK = top_vote_book
        elif top_vote_count >= MIN_VOTE_ACCEPT:
            FINAL_BOOK = top_vote_book

    if FINAL_BOOK:
        book_keywords = FINAL_BOOK.lower().replace(".txt","").split("_")
        matches = sum(1 for word in book_keywords if word in clean)
        best_score += 0.05 * matches

        vote_boost = min(top_vote_count / TOP_K, 1.0) * 0.2
        best_score += vote_boost

        text_words = set(clean.split())
        coverage = len(text_words & set(book_keywords)) / max(len(book_keywords), 1)
        best_score += min(coverage, 0.2)

    if FINAL_BOOK and FINAL_BOOK.lower().replace(".txt", "") in clean:
        best_score += 0.05

    best_score = min(best_score, 1.0)
    best_score = round(float(best_score), 2)

    if best_score >= CONFIDENCE_THRESHOLD or top_vote_count >= MIN_VOTE_ACCEPT:
        author = get_author_from_db(FINAL_BOOK)
        log_stage("Total search pipeline", pipeline_start)
        return {
            "status": "success",
            "book": FINAL_BOOK,
            "author": author,
            "confidence": best_score,
            "votes": top_vote_count,
        }

    log_stage("Total search pipeline", pipeline_start)
    return {"status": "fail", "reason": "Low confidence"}

    pipeline_start = time.time()

    raw = extract_text(image_path)

    if not raw.strip():
        return {"status": "fail", "reason": "No readable text detected"}

    if not is_mostly_english(raw):
        return {"status": "fail", "reason": "Only English books supported"}

    clean = clean_text(raw)

    if len(clean.split()) < 10:
        return {"status": "fail", "reason": "Too little readable text"}

    if len(clean) < 80:
        return {"status": "fail", "reason": "Not enough readable text"}

    chunks = chunk_text(clean)

    candidates = fast_search(chunks)

    if not candidates:
        return {"status": "fail", "reason": "No matches found"}

    best_book, best_score = rerank_candidates(chunks, candidates)

    votes = Counter(candidates)
    top_vote_book, top_vote_count = votes.most_common(1)[0]

    FINAL_BOOK = best_book

    if is_anthology(FINAL_BOOK) and not is_anthology(top_vote_book):
        FINAL_BOOK = top_vote_book
    elif top_vote_count >= MIN_VOTE_ACCEPT:
        FINAL_BOOK = top_vote_book

    if FINAL_BOOK and FINAL_BOOK.lower().replace(".txt", "") in clean:
        best_score += 0.10

    if best_score >= CONFIDENCE_THRESHOLD or top_vote_count >= MIN_VOTE_ACCEPT:
        author = get_author_from_db(FINAL_BOOK)

        log_stage("Total search pipeline", pipeline_start)

        return {
            "status": "success",
            "book": FINAL_BOOK,
            "author": author,
            "confidence": round(float(best_score), 2),
            "votes": top_vote_count,
        }

    log_stage("Total search pipeline", pipeline_start)

    return {"status": "fail", "reason": "Low confidence"}


# CLI

if __name__ == "__main__":
    print()
    image_path = input("Enter image path: ").strip().strip('"')

    if not os.path.exists(image_path):
        print("\nFile not found.")
    else:
        result = run_image_search(image_path)
        print("\nRESULT:")
        print(result)