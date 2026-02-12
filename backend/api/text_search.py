import sqlite3
import hashlib
import re
from collections import defaultdict, Counter


DB_PATH = r"C:\Users\DELL\Desktop\LeafLens\books.db"
print("Using DB at:", DB_PATH)

WINDOW_SIZES = [6, 7, 8]
STEP = 1

BASE_MIN_ALIGNED = 8
BASE_MIN_DOMINANCE = 0.6
MIN_TOTAL_VOTES = 12


def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fingerprint_query(text, window_size):
    words = text.split()
    for i in range(0, len(words) - window_size + 1, STEP):
        window = " ".join(words[i:i + window_size])
        h = hashlib.md5(window.encode("utf-8")).hexdigest()[:16]
        yield h, i


def run_text_search(query: str):
    """
    Perform text-based book identification.
    
    Args:
        query (str): Text from a book page.

    Returns:
        dict: Result including match status, title, author, and confidence info.
    """
    query = normalize_text(query)
    word_count = len(query.split())

    MIN_ALIGNED = BASE_MIN_ALIGNED if word_count < 80 else BASE_MIN_ALIGNED + 4
    MIN_DOMINANCE = 0.45 if word_count < 80 else BASE_MIN_DOMINANCE

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    offset_votes = defaultdict(list)

    for w in WINDOW_SIZES:
        for h, q_pos in fingerprint_query(query, w):
            rows = c.execute(
                "SELECT book_id, position FROM fingerprints WHERE hash=?",
                (h,)
            ).fetchall()

            for book_id, b_pos in rows:
                offset = int(b_pos) - int(q_pos)
                if -1_000_000 < offset < 1_000_000:
                    offset_votes[book_id].append(offset)

    book_titles = {
        row[0]: normalize_text(row[1])
        for row in c.execute("SELECT book_id, title FROM books")
    }

    collapsed_votes = defaultdict(list)
    for book_id, offsets in offset_votes.items():
        title_key = book_titles.get(book_id, book_id)
        collapsed_votes[title_key].extend(offsets)

    results = []

    for title_key, offsets in collapsed_votes.items():
        if len(offsets) < MIN_TOTAL_VOTES:
            continue

        counter = Counter(offsets)
        best_offset, aligned = counter.most_common(1)[0]
        dominance = aligned / len(offsets)

        if aligned < 3:
            continue

        results.append((title_key, aligned, dominance, len(offsets)))

    results.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)

    if not results:
        conn.close()
        return {"status": "fail", "reason": "No match found"}

    best = results[0]
    title_key, aligned, dominance, total = best

    if aligned >= MIN_ALIGNED and dominance >= MIN_DOMINANCE:
        row = c.execute(
            "SELECT title, author FROM books WHERE LOWER(title)=?",
            (title_key,)
        ).fetchone()

        title, author = row if row else (title_key, "Unknown")

        conn.close()
        return {
            "status": "success",
            "title": title,
            "author": author,
            "aligned": aligned,
            "dominance": round(dominance, 2),
            "votes": total,
            "top_candidates": [
                {"title": r[0], "aligned": r[1], "dominance": round(r[2], 2), "votes": r[3]}
                for r in results[:5]
            ]
        }
    else:
        conn.close()
        return {"status": "fail", "reason": "Low confidence"}
