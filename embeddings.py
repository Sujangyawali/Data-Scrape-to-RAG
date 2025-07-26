# embeddings.py
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import json
from dotenv import load_dotenv
from minio import Minio
import pandas as pd
import io

# Load environment variables
load_dotenv()

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize MinIO client
client = Minio(
    'localhost:9000',
    access_key=os.getenv('MINIO_ACCESS_KEY'),
    secret_key=os.getenv('MINIO_SECRET_KEY'),
    secure=False
)

# Gold bucket and folder details
gold_bucket = "gold"
books_folder = "books"

# List all CSV files in the books folder
try:
    objects = client.list_objects(gold_bucket, prefix=f"{books_folder}/", recursive=True)
    csv_files = [obj.object_name for obj in objects if obj.object_name.endswith('.csv')]
    if not csv_files:
        raise ValueError(f"No CSV files found in {gold_bucket}/{books_folder}/")
except Exception as e:
    raise ValueError(f"Failed to list objects in MinIO: {e}")

# Chunking parameters
chunk_size = 500  
chunk_overlap = 50 

# Load and chunk documents from all CSV files
texts = []
sources = []
text_urls = []
for csv_file in csv_files:
    try:
        response = client.get_object(gold_bucket, csv_file)
        csv_data = response.read()
        response.close()
        df = pd.read_csv(io.BytesIO(csv_data))
        
        for index, row in df.iterrows():
            content = str(row['content']).strip()
            if content:
                words = content.split()
                for i in range(0, len(words) - chunk_size + 1, chunk_size - chunk_overlap):
                    chunk = " ".join(words[i:i + chunk_size])
                    texts.append(chunk)
                    sources.append(f"{os.path.basename(csv_file).replace('.csv', '')}_chunk_{i//(chunk_size - chunk_overlap)}")
                    text_urls.append(row['text_url'])
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")
        continue

if not texts:
    raise ValueError("No valid (non-empty) content found in CSV files from MinIO gold bucket.")

# Save chunked texts
os.makedirs("data", exist_ok=True)
with open("data/chunked_texts.json", "w", encoding="utf-8") as f:
    json.dump(texts, f)

# Generate and save embeddings
embeddings = model.encode(texts)
if embeddings.shape[0] == 0:
    raise ValueError("Failed to generate embeddings. Ensure content contains valid text.")
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)
faiss.write_index(index, "data/vector_index.faiss")

# Save metadata including text_url
metadata = {i: {"source": source, "text_url": text_url} for i, (source, text_url) in enumerate(zip(sources, text_urls))}
with open("data/metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f)

print("Embedding process completed. Index, metadata, and chunked texts saved.")