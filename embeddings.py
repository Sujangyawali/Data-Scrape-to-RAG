# embeddings.py
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Directory for input documents
silver_dir = "data/silver/books"
if not os.path.exists(silver_dir):
    os.makedirs(silver_dir, exist_ok=True)
    raise ValueError(f"Directory {silver_dir} does not exist. Please create it and add .txt files.")

# Chunking parameters
chunk_size = 500  
chunk_overlap = 50 

# Load and chunk documents
texts = []
sources = []
for file_path in os.listdir(silver_dir):
    if file_path.endswith('.txt'):
        with open(os.path.join(silver_dir, file_path), 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                words = content.split()
                for i in range(0, len(words) - chunk_size + 1, chunk_size - chunk_overlap):
                    chunk = " ".join(words[i:i + chunk_size])
                    texts.append(chunk)
                    sources.append(f"{file_path}_chunk_{i//(chunk_size - chunk_overlap)}")

if not texts:
    raise ValueError("No valid (non-empty) text files found in data/silver/books directory.")

# Save chunked texts
os.makedirs("data", exist_ok=True)
with open("data/chunked_texts.json", "w", encoding="utf-8") as f:
    json.dump(texts, f)

# Generate and save embeddings
embeddings = model.encode(texts)
if embeddings.shape[0] == 0:
    raise ValueError("Failed to generate embeddings. Ensure text files contain valid content.")
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)
faiss.write_index(index, "data/vector_index.faiss")

# Save metadata
metadata = {i: source for i, source in enumerate(sources)}
with open("data/metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f)

print("Embedding process completed. Index, metadata, and chunked texts saved.")