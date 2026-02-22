import sqlite3
import hashlib
import re
from collections import defaultdict, Counter

DB_PATH = "books.db"
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


query = input("\n Paste text from a book page:\n")
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


# Map book_id -> normalized title
book_titles = {
    row[0]: normalize_text(row[1])
    for row in c.execute("SELECT book_id, title FROM books")
}

# Collapse votes by title
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

    # ✅ Find the book_id with the most offsets for this title_key
    book_ids_for_title = [
        bid for bid, t_key in book_titles.items() if t_key == title_key
    ]
    book_id_votes = {bid: len(offset_votes[bid]) for bid in book_ids_for_title}
    winning_book_id = max(book_id_votes, key=book_id_votes.get)

    results.append((title_key, aligned, dominance, len(offsets), winning_book_id))

results.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)

# OUTPUT
if not results:
    print("\n No match found.")
    conn.close()
    exit()

print("\n Top candidates:")
for r in results[:5]:
    print(f"- {r[0]} | aligned={r[1]} | dominance={r[2]:.2f} | votes={r[3]}")

best = results[0]
title_key, aligned, dominance, total, winning_book_id = best

row = c.execute(
    "SELECT title, author FROM books WHERE book_id=?",
    (winning_book_id,)
).fetchone()

title, author = row if row else (title_key, "Unknown")

if aligned >= MIN_ALIGNED and dominance >= MIN_DOMINANCE:
    print("\n MATCH FOUND")
else:
    print("\n LOW CONFIDENCE MATCH")

print(f"Title: {title}")
print(f"Author: {author if author and author.strip() else 'Unknown'}")
print(f"Aligned matches: {aligned}")
print(f"Offset dominance: {dominance:.2f}")
print(f"Total votes: {total}")

conn.close()