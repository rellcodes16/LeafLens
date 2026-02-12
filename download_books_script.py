import os
import requests
import time
import re

OUTPUT_DIR = "data/books"
TIMEOUT = 15
SLEEP_BETWEEN = 2

BOOKS = {
    580: "The Pickwick Papers",
    564: "The Mystery of Edwin Drood",
    675: "Nicholas Nickleby",
}

URL_PATTERNS = [
    "https://www.gutenberg.org/files/{id}/{id}-0.txt",
    "https://www.gutenberg.org/files/{id}/{id}.txt",
    "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt",
]


os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_title(title):
    title = title.lower()
    title = re.sub(r"[^a-z0-9]+", "_", title)
    return title.strip("_")

def download_book(book_id, title):
    filename = f"{clean_title(title)}.txt"
    path = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(path):
        print(f"Skipping (already exists): {title}")
        return True

    for url in URL_PATTERNS:
        try:
            final_url = url.format(id=book_id)
            print(f"Trying: {final_url}")
            r = requests.get(final_url, timeout=TIMEOUT)

            if r.status_code == 200 and len(r.text) > 5000:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(r.text)

                print(f"{title}")
                return True

        except Exception:
            pass

    print(f"Failed: {title}")
    return False


if __name__ == "__main__":
    success = 0

    for book_id, title in BOOKS.items():
        print(f"\n {title} (ID: {book_id})")
        if download_book(book_id, title):
            success += 1
        time.sleep(SLEEP_BETWEEN)

    print(f"\n Done. {success}/{len(BOOKS)} books downloaded.")
