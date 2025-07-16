from sentence_transformers import SentenceTransformer
from pyspark.sql import SparkSession
import faiss
import numpy as np
import yaml
import os
import json
from dotenv import load_dotenv

load_dotenv()

def generate_embeddings():
    spark = SparkSession.builder.appName("Embed").getOrCreate()
    with open('sample_config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    df = spark.read.format("delta").load(f"s3a://{config['minio']['bucket_gold']}/gold")
    texts = df.select("text", "source").collect()
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode([row.text for row in texts])
    
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, "vector_index.faiss")
    
    with open("metadata.json", "w") as f:
        json.dump({i: row.source for i, row in enumerate(texts)}, f)
    
    spark.stop()