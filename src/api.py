from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import faiss
import json
import numpy as np
from ollama import Client
from pyspark.sql import SparkSession
import yaml
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
model = SentenceTransformer('all-MiniLM-L6-v2')
index = faiss.read_index("vector_index.faiss")
with open("metadata.json", "r") as f:
    metadata = json.load(f)

# Initialize Ollama client
ollama_client = Client(host='http://ollama:11434')

# Load Spark for accessing Gold layer
with open('sample_config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)
spark = SparkSession.builder.appName("RAG").getOrCreate()
gold_df = spark.read.format("delta").load(f"s3a://{config['minio']['bucket_gold']}/gold")

@app.get("/ask")
async def ask(query: str):
    # Find relevant documents using FAISS
    query_embedding = model.encode([query])[0]
    _, indices = index.search(np.array([query_embedding]), k=2)
    
    # Retrieve text from Gold layer
    results = []
    for i in indices[0]:
        source = metadata[str(i)]
        # Query Spark to get the full text for the source
        text_row = gold_df.filter(f"source = '{source}'").select("text").collect()
        text = text_row[0]["text"] if text_row else "Text not found"
        results.append({"source": source, "text": text[:500]})  # Truncate for brevity
    
    # Generate answer using Ollama
    context = "\n".join([r["text"] for r in results])
    prompt = f"Based on the following context, answer the query: {query}\n\nContext:\n{context}"
    response = ollama_client.generate(model='mistral', prompt=prompt)
    
    return {
        "query": query,
        "answer": response['response'],
        "sources": [r["source"] for r in results]
    }