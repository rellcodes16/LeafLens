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
OCR_CHUNK_SIZE = 400

TOP_K = 5

CONFIDENCE_THRESHOLD = 0.25
MIN_VOTE_ACCEPT = 3

MPNET_DIR = "./models/mpnet"
MINILM_DIR = "./models/minilm"

# ================= ANTHOLOGY DETECTION =================
ANTHOLOGY_KEYWORDS = [
    "complete works",
    "collected works",
    "collection",
    "anthology",
    "全集"
]

def is_anthology(title):
    title = title.lower()
    return any(word in title for word in ANTHOLOGY_KEYWORDS)

# ================= MODEL LOADER =================
def load_model_local(model_name, save_path):
    if not os.path.exists(save_path):
        print(f" {model_name} not found locally. Downloading...")
        model = SentenceTransformer(model_name)
        os.makedirs(save_path, exist_ok=True)
        model.save(save_path)
        print(f" {model_name} saved locally at {save_path}")
    return SentenceTransformer(save_path)

print("Loading models...")

reader = easyocr.Reader(["en"], gpu=False)

miniLM = load_model_local("all-MiniLM-L6-v2", MINILM_DIR)
mpnet = load_model_local("sentence-transformers/all-mpnet-base-v2", MPNET_DIR)

# ================= BUILD FAISS INDEX =================
def build_index():
    if not os.path.exists(BOOKS_DIR):
        print(f"Books folder not found: {BOOKS_DIR}")
        exit()

    files = [f for f in os.listdir(BOOKS_DIR) if f.endswith(".txt")]
    total_files = len(files)

    print(f"Building MiniLM index from {total_files} books...")

    embeddings = []
    metadata = []
    processed_chunks = 0

    for file_i, filename in enumerate(files, start=1):
        path = os.path.join(BOOKS_DIR, filename)

        print(f"\n📖 [{file_i}/{total_files}] Processing: {filename}")

        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
        print(f"    {len(chunks)} chunks")

        for chunk_i, chunk in enumerate(chunks, start=1):
            emb = miniLM.encode(chunk).astype("float32")
            embeddings.append(emb)
            metadata.append({
                "book": filename,
                "preview": chunk[:250]
            })

            processed_chunks += 1
            if chunk_i % 10 == 0 or chunk_i == len(chunks):
                print(f"       Embedded {chunk_i}/{len(chunks)} chunks")

    embeddings = np.array(embeddings)
    print(f"\n Total chunks embedded: {processed_chunks}")

    print("Building FAISS index...")
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)
    np.save(META_PATH, metadata)

    print("MiniLM index built successfully!")

if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
    build_index()

# ================= LOAD INDEX =================
print("Loading FAISS index...")
index = faiss.read_index(INDEX_PATH)
metadata = np.load(META_PATH, allow_pickle=True)
print(f"Loaded {len(metadata)} chunks")

# ================= OCR =================
def extract_text(image_path):
    print(f"\n OCR reading: {image_path}")
    result = reader.readtext(image_path, detail=0)
    print(f"OCR extracted {len(result)} text lines")
    return " ".join(result)

# ================= TEXT CLEANING =================
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ================= OCR CHUNKING =================
def chunk_text(text, size=OCR_CHUNK_SIZE):
    chunks = [text[i:i+size] for i in range(0, len(text), size)]
    print(f"Split OCR text into {len(chunks)} chunks")
    return chunks

# ================= FAST SEARCH =================
def fast_search(chunks):
    print("\n Running MiniLM fast search...")
    candidates = []

    for i, chunk in enumerate(chunks, start=1):
        emb = miniLM.encode(chunk).astype("float32")
        D, I = index.search(np.array([emb]), TOP_K)

        for idx in I[0]:
            candidates.append(metadata[idx]["book"])

        print(f"    Chunk {i}/{len(chunks)} searched")

    return candidates

# ================= RERANK =================
def rerank_candidates(chunks, candidate_books):
    if not candidate_books:
        return None, 0

    print("\n Reranking with MPNet...")

    candidate_texts = {}
    for m in metadata:
        if m["book"] in candidate_books:
            candidate_texts.setdefault(m["book"], []).append(m["preview"])

    scores = {}
    emb_query = mpnet.encode(chunks, batch_size=8)

    total_books = len(candidate_texts)

    for i, (book, previews) in enumerate(candidate_texts.items(), start=1):
        emb_book = mpnet.encode(previews, batch_size=8)

        sim = np.dot(emb_query, emb_book.T) / (
            np.linalg.norm(emb_query, axis=1)[:, None] *
            np.linalg.norm(emb_book, axis=1)[None, :]
        )

        score = sim.mean()

        # Penalize anthologies
        if is_anthology(book):
            score *= 0.80  

        scores[book] = score
        print(f"   Reranked {i}/{total_books}: {book}")

    best_book = max(scores, key=scores.get)
    best_score = scores[best_book]

    return best_book, best_score

# ================= FINAL DECISION =================
def identify_book(image_path):
    raw = extract_text(image_path)
    clean = clean_text(raw)

    print("\n====== OCR PREVIEW ======")
    print(clean[:800])
    print("=========================\n")

    if len(clean) < 60:
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
    print(" Best rerank:", best_book, "Score:", round(float(best_score), 3))
    print(" Top voted:", top_vote_book, "Votes:", top_vote_count)

    FINAL_BOOK = best_book

    # ================= CORE RULE =================

    # 1️⃣ Prefer specific over anthology ALWAYS
    if is_anthology(FINAL_BOOK) and not is_anthology(top_vote_book):
        print(" Switching from anthology to specific book")
        FINAL_BOOK = top_vote_book

    # 2️⃣ Block anthology from overriding a specific rerank match
    if not is_anthology(best_book) and is_anthology(top_vote_book):
        print(" Blocking anthology override — keeping specific rerank result")
        FINAL_BOOK = best_book

    # 3️⃣ Allow vote override only when both are same type
    elif top_vote_count >= MIN_VOTE_ACCEPT and top_vote_book != FINAL_BOOK:
        print(" Overriding rerank with vote consensus")
        FINAL_BOOK = top_vote_book

    # Boost score if OCR contains book title
    if FINAL_BOOK and FINAL_BOOK.lower().replace(".txt", "") in clean:
        best_score += 0.10

    # Accept if rerank OR votes confident
    if best_score >= CONFIDENCE_THRESHOLD or top_vote_count >= MIN_VOTE_ACCEPT:
        return {
            "status": "success",
            "book": FINAL_BOOK,
            "confidence": round(float(best_score), 2),
            "votes": top_vote_count
        }

    return {"status": "fail", "reason": "Low confidence"}

# ================= RUN =================
if __name__ == "__main__":
    image_path = input("\n Enter image path: ")
    result = identify_book(image_path)
    print("\n RESULT:", result)
