from sentence_transformers import SentenceTransformer
from pyspark.sql import SparkSession
import faiss
import numpy as np
import yaml
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def generate_embeddings():
    spark = SparkSession.builder.appName("Embed").getOrCreate()
    
    # Load config
    with open('/opt/spark/sample_config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Define local silver directory
    silver_dir = "/opt/spark/data/silver"
    
    # Read text files from local silver directory
    text_files = [os.path.join(silver_dir, f) for f in os.listdir(silver_dir) if f.endswith('.txt')]
    texts = []
    sources = []
    for file_path in text_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            texts.append(content)
            sources.append(file_path)
    
    # Generate embeddings
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(texts)
    
    # Create and save FAISS index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, "/opt/spark/data/vector_index.faiss")
    
    # Save metadata
    metadata = {i: source for i, source in enumerate(sources)}
    with open("/opt/spark/data/metadata.json", "w", encoding='utf-8') as f:
        json.dump(metadata, f)
    
    # Example: Retrieve and query with Ollama
    query = "What is the main topic of the documents?"
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, k=3)  # Retrieve top 3 similar documents
    retrieved_context = " ".join([texts[i] for i in indices[0] if i < len(texts)])
    
    ollama_url = "http://ollama:11434/api/generate"  # Ollama API endpoint
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "llama3",  # Adjust model name based on your Ollama setup
        "prompt": f"Based on this context: {retrieved_context}\n\nQuestion: {query}",
        "stream": False
    }
    response = requests.post(ollama_url, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        print("Ollama Response:", result.get("response", "No response"))
    else:
        print("Ollama Error:", response.status_code, response.text)
    
    spark.stop()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "generate_embeddings":
        generate_embeddings()