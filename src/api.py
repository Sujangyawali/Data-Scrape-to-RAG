from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import yaml
import os
import json
import requests
from dotenv import load_dotenv

app = FastAPI()
load_dotenv()

# Load config and model
with open('/app/sample_config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load FAISS index and metadata
index = faiss.read_index("/app/data/vector_index.faiss")
with open("/app/data/metadata.json", 'r', encoding='utf-8') as f:
    metadata = json.load(f)

# Load texts from silver directory (for embedding lookup)
silver_dir = "/app/data/silver"
text_files = [os.path.join(silver_dir, f) for f in os.listdir(silver_dir) if f.endswith('.txt')]
texts = []
for file_path in text_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        texts.append(f.read())

@app.post("/ask")
async def ask_question(question: str):
    # Generate query embedding
    query_embedding = model.encode([question])
    
    # Retrieve top 3 similar documents
    distances, indices = index.search(query_embedding, k=3)
    retrieved_indices = indices[0]
    retrieved_context = " ".join([texts[i] for i in retrieved_indices if i < len(texts)])
    
    # Query Ollama
    ollama_url = "http://ollama:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "llama3",  # Adjust based on your Ollama model
        "prompt": f"Based on this context: {retrieved_context}\n\nQuestion: {question}",
        "stream": False
    }
    response = requests.post(ollama_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        return {"question": question, "answer": result.get("response", "No response"), "sources": [metadata.get(str(i), "Unknown") for i in retrieved_indices if i < len(texts)]}
    else:
        return {"question": question, "error": f"Ollama Error: {response.status_code} - {response.text}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)