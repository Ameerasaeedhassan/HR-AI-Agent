from pathlib import Path
import json

import numpy as np
from sentence_transformers import SentenceTransformer

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Read the chunks we already created.
chunks = json.loads(
    (DATA_DIR / "policy_chunks.json").read_text(encoding="utf-8")
)

if not chunks:
    raise ValueError("No chunks found. Run build_chunks.py first.")

texts = [chunk["text"] for chunk in chunks]

# Download the pretrained model on the first run.
# CPU mode works without a dedicated graphics card.
model = SentenceTransformer(MODEL_NAME, device="cpu")

# Check that no passage exceeds the model's input limit.
tokenized = model.tokenizer(
    texts,
    truncation=False,
    padding=False,
    add_special_tokens=True,
)

lengths = [len(ids) for ids in tokenized["input_ids"]]

too_long = [
    f"{chunk['id']}: {length} tokens"
    for chunk, length in zip(chunks, lengths)
    if length > model.max_seq_length
]

print(f"Longest chunk: {max(lengths)} tokens")
print(f"Model input limit: {model.max_seq_length} tokens")

if too_long:
    raise ValueError(
        "These chunks need splitting before embedding:\n"
        + "\n".join(too_long)
    )

# Convert each passage into a normalized vector.
embeddings = model.encode(
    texts,
    batch_size=16,
    show_progress_bar=True,
    normalize_embeddings=True,
    convert_to_numpy=True,
)

np.save(DATA_DIR / "policy_embeddings.npy", embeddings)

# Preserve the row order and model identity for later retrieval.
manifest = {
    "model_name": MODEL_NAME,
    "normalize_embeddings": True,
    "dimensions": int(embeddings.shape[1]),
    "chunk_ids": [chunk["id"] for chunk in chunks],
}

(DATA_DIR / "embedding_manifest.json").write_text(
    json.dumps(manifest, indent=2),
    encoding="utf-8",
)

print(f"\nEmbedding shape: {embeddings.shape}")
print("Saved policy_embeddings.npy and embedding_manifest.json")