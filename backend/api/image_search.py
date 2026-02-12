import easyocr
import re
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from collections import Counter

#  CONFIG 
BOOKS_DIR = r"C:\Users\DELL\Desktop\LeafLens\data\books"
INDEX_PATH = r"C:\Users\DELL\Desktop\LeafLens\books.index"
META_PATH = r"C:\Users\DELL\Desktop\LeafLens\books_meta.npy"

CHUNK_SIZE = 800
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

#  HELPERS 
def is_anthology(title):
    return any(word in title.lower() for word in ANTHOLOGY_KEYWORDS)

def load_model_local(model_name, save_path):
    if not os.path.exists(save_path):
        print(f"Downloading {model_name}...")
        model = SentenceTransformer(model_name)
        os.makedirs(save_path, exist_ok=True)
        model.save(save_path)
        print(f"Saved at {save_path}")
    return SentenceTransformer(save_path)

def extract_text(image_path):
    result = reader.readtext(image_path, detail=0, paragraph=True)
    return " ".join(result)

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def chunk_text(text):
    chunks = [text[i:i+OCR_CHUNK_SIZE] for i in range(0, len(text), OCR_CHUNK_SIZE)]
    return [c for c in chunks if len(c) > 50]

def fast_search(chunks):
    embeddings = miniLM.encode(chunks, batch_size=16)
    D, I = index.search(np.array(embeddings).astype("float32"), TOP_K)
    candidates = []
    for neighbors in I:
        for idx in neighbors:
            candidates.append(metadata[idx]["book"])
    return candidates

def rerank_candidates(chunks, candidate_books):
    if not candidate_books:
        return None, 0

    candidate_texts = {}
    for m in metadata:
        if m["book"] in candidate_books:
            candidate_texts.setdefault(m["book"], []).append(m["preview"])

    for book in candidate_texts:
        candidate_texts[book] = candidate_texts[book][:MAX_RERANK_PREVIEWS]

    emb_query = mpnet.encode(chunks, batch_size=16)
    scores = {}
    for book, previews in candidate_texts.items():
        emb_book = mpnet.encode(previews, batch_size=16)
        sim = np.dot(emb_query, emb_book.T) / (
            np.linalg.norm(emb_query, axis=1)[:, None] *
            np.linalg.norm(emb_book, axis=1)[None, :]
        )
        score = sim.mean()
        if is_anthology(book):
            score *= 0.80
        scores[book] = score

    best_book = max(scores, key=scores.get)
    return best_book, scores[best_book]

# LOAD MODELS & INDEX
print("Loading models...")
reader = easyocr.Reader(["en"], gpu=False)
miniLM = load_model_local("all-MiniLM-L6-v2", MINILM_DIR)
mpnet = load_model_local("sentence-transformers/all-mpnet-base-v2", MPNET_DIR)

if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
    raise FileNotFoundError("FAISS index or metadata not found. Build it first!")

print("Loading FAISS index...")
index = faiss.read_index(INDEX_PATH)
metadata = np.load(META_PATH, allow_pickle=True)

# MAIN FUNCTION 
def run_image_search(image_path: str):
    raw = extract_text(image_path)
    clean = clean_text(raw)

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
    if not is_anthology(best_book) and is_anthology(top_vote_book):
        FINAL_BOOK = best_book
    elif top_vote_count >= MIN_VOTE_ACCEPT and top_vote_book != FINAL_BOOK:
        FINAL_BOOK = top_vote_book
    if FINAL_BOOK and FINAL_BOOK.lower().replace(".txt", "") in clean:
        best_score += 0.10

    if best_score >= CONFIDENCE_THRESHOLD or top_vote_count >= MIN_VOTE_ACCEPT:
        return {
            "status": "success",
            "book": FINAL_BOOK,
            "confidence": round(float(best_score), 2),
            "votes": top_vote_count
        }

    return {"status": "fail", "reason": "Low confidence"}
