import os
import time
import numpy as np
from sentence_transformers import SentenceTransformer

META_PATH = "books_meta.npy"
MPNET_DIR = "./models/mpnet"
MPNET_EMB_PATH = "mpnet_embeddings.npy"

if not os.path.exists(META_PATH):
    raise FileNotFoundError("books_meta.npy not found. Build main index first.")

print("\n==============================")
print("Building MPNet Embedding Cache")
print("==============================\n")

start_time = time.time()

print("Loading MPNet model...")
mpnet = SentenceTransformer(MPNET_DIR)

print("Loading metadata...")
metadata = np.load(META_PATH, allow_pickle=True)

previews = [m["preview"] for m in metadata]
total_previews = len(previews)

print(f"\nTotal previews to encode: {total_previews}")
print("Encoding with MPNet...\n")

embeddings = mpnet.encode(
    previews,
    batch_size=32,
    show_progress_bar=True
).astype("float32")

print("\nSaving embeddings...")
np.save(MPNET_EMB_PATH, embeddings)

elapsed = time.time() - start_time

print("\n================================")
print("✅ MPNet cache successfully built!")
print(f"Total vectors saved: {len(embeddings)}")
print(f"Saved to: {MPNET_EMB_PATH}")
print(f"Time taken: {round(elapsed, 2)} seconds")
print("================================\n")
