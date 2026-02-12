import easyocr
import re
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from collections import Counter

BOOKS_DIR = "data/books"
INDEX_PATH = "books.index"
META_PATH = "books_meta.npy"

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

print("Loading models...")

reader = easyocr.Reader(["en"], gpu=False)

miniLM = load_model_local("all-MiniLM-L6-v2", MINILM_DIR)
mpnet = load_model_local("sentence-transformers/all-mpnet-base-v2", MPNET_DIR)

# BUILD FAISS INDEX
def build_index():
    if not os.path.exists(BOOKS_DIR):
        print(f"Books folder not found: {BOOKS_DIR}")
        exit()

    files = [f for f in os.listdir(BOOKS_DIR) if f.endswith(".txt")]
    embeddings = []
    metadata = []

    print(f"Indexing {len(files)} books...")

    for i, filename in enumerate(files, 1):
        print(f"\n [{i}/{len(files)}] {filename}")
        path = os.path.join(BOOKS_DIR, filename)

        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = [text[j:j+CHUNK_SIZE] for j in range(0, len(text), CHUNK_SIZE)]
        chunk_embeddings = miniLM.encode(chunks, batch_size=32)

        for chunk, emb in zip(chunks, chunk_embeddings):
            embeddings.append(emb.astype("float32"))
            metadata.append({
                "book": filename,
                "preview": chunk[:250]
            })

    embeddings = np.array(embeddings)

    print("\n Building FAISS index...")
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)
    np.save(META_PATH, metadata)

    print("Index built!")

if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
    build_index()

# LOAD INDEX
print("Loading FAISS index...")
index = faiss.read_index(INDEX_PATH)
metadata = np.load(META_PATH, allow_pickle=True)
print(f"Loaded {len(metadata)} chunks")

# OCR
def extract_text(image_path):
    print(f"\n OCR reading: {image_path}")
    result = reader.readtext(image_path, detail=0, paragraph=True)
    print(f"OCR extracted {len(result)} text blocks")
    return " ".join(result)

# CLEAN TEXT
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# OCR CHUNKING
def chunk_text(text):
    chunks = [text[i:i+OCR_CHUNK_SIZE] for i in range(0, len(text), OCR_CHUNK_SIZE)]
    chunks = [c for c in chunks if len(c) > 50]
    print(f"Split OCR into {len(chunks)} chunks")
    return chunks

# FAST SEARCH(BATCHED)
def fast_search(chunks):
    print("\n MiniLM fast search...")

    embeddings = miniLM.encode(chunks, batch_size=16)
    D, I = index.search(np.array(embeddings).astype("float32"), TOP_K)

    candidates = []
    for chunk_i, neighbors in enumerate(I):
        for idx in neighbors:
            candidates.append(metadata[idx]["book"])
        print(f"    Chunk {chunk_i+1}/{len(chunks)} searched")

    return candidates

# RERANK(LIMITED PREVIEWS)
def rerank_candidates(chunks, candidate_books):
    if not candidate_books:
        return None, 0

    print("\n MPNet reranking...")

    candidate_texts = {}
    for m in metadata:
        if m["book"] in candidate_books:
            candidate_texts.setdefault(m["book"], []).append(m["preview"])

    for book in candidate_texts:
        candidate_texts[book] = candidate_texts[book][:MAX_RERANK_PREVIEWS]

    emb_query = mpnet.encode(chunks, batch_size=16)

    scores = {}

    for i, (book, previews) in enumerate(candidate_texts.items(), 1):
        emb_book = mpnet.encode(previews, batch_size=16)

        sim = np.dot(emb_query, emb_book.T) / (
            np.linalg.norm(emb_query, axis=1)[:, None] *
            np.linalg.norm(emb_book, axis=1)[None, :]
        )

        score = sim.mean()

        if is_anthology(book):
            score *= 0.80

        scores[book] = score
        print(f"   {i}/{len(candidate_texts)} → {book}")

    best_book = max(scores, key=scores.get)
    return best_book, scores[best_book]

def identify_book(image_path):
    raw = extract_text(image_path)
    clean = clean_text(raw)

    print("\n====== OCR PREVIEW ======")
    print(clean[:800])
    print("=========================")

    if len(clean) < 80:
        return {"status": "fail", "reason": "Not enough readable text"}

    chunks = chunk_text(clean)
    candidates = fast_search(chunks)

    if not candidates:
        return {"status": "fail", "reason": "No matches found"}

    best_book, best_score = rerank_candidates(chunks, candidates)

    votes = Counter(candidates)
    top_vote_book = votes.most_common(1)[0][0]
    top_vote_count = votes[top_vote_book]

    print("\n Candidate votes:", votes)
    print("Best rerank:", best_book, round(float(best_score), 3))
    print("Top voted:", top_vote_book, "Votes:", top_vote_count)

    FINAL_BOOK = best_book

    # Prevent anthology override
    if is_anthology(FINAL_BOOK) and not is_anthology(top_vote_book):
        FINAL_BOOK = top_vote_book

    if not is_anthology(best_book) and is_anthology(top_vote_book):
        FINAL_BOOK = best_book

    elif top_vote_count >= MIN_VOTE_ACCEPT and top_vote_book != FINAL_BOOK:
        FINAL_BOOK = top_vote_book

    # Boost if title appears in OCR
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

if __name__ == "__main__":
    image_path = input("\n Enter image path: ")
    result = identify_book(image_path)
    print("\n RESULT:", result)
