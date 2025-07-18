from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import json
import requests
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
load_dotenv()

# Enable CORS to allow Streamlit (port 8501) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a Pydantic model for the request body
class QuestionRequest(BaseModel):
    question: str

# Load Together AI API key
api_key = os.getenv("TOGETHER_API_KEY")
if not api_key:
    raise ValueError("TOGETHER_API_KEY not found in .env file")

# Load precomputed index and metadata
index = faiss.read_index("data/vector_index.faiss")
with open("data/metadata.json", 'r', encoding='utf-8') as f:
    metadata = json.load(f)

# Load model for query embedding
model = SentenceTransformer('all-MiniLM-L6-v2')

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    question = request.question
    print("Received question:", question)  # Debug print
    if not question.strip():
        return {"question": question, "error": "Question cannot be empty."}
    
    # Generate query embedding and retrieve context
    query_embedding = model.encode([question])
    distances, indices = index.search(query_embedding, k=3)  # Retrieve top 2 chunks
    retrieved_indices = indices[0]
    
    # Construct context from chunks
    with open("data/chunked_texts.json", "r", encoding="utf-8") as f:
        texts = json.load(f)
    context = " ".join([texts[i] for i in retrieved_indices if i < len(texts)])
    
    # Define system prompt and context separately
    system_prompt = """Role: You are an expert document assistant.
                       Knowledge Source: Only use information from the user-provided context below.
                       Core Instructions:
                       - Context is Truth: Base every response EXCLUSIVELY on the provided context. Never use external knowledge.
                       - Unanswerable Questions: If the context lacks information, respond: "The document doesn't specify" or "I cannot determine from the provided context."
                       - Precision: Prioritize direct quotes/phrases from the context. Never add interpretations not explicitly supported.
                       - Acknowledge document limitations.
                       - Citation: When possible, reference section titles/page numbers from the context metadata.
                       - Brevity: Keep responses concise unless complexity requires elaboration.
                       - No need to mentioned "Limited context" or "Based on the limited context" or " provided context" repeatedly. Single mention is sufficient.
                       You must strictly follow these instructions. Any deviation will result in an invalid response."""

    # Structure messages to enforce context usage
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Context: {context}"},  # Separate context message
        {"role": "user", "content": question}
    ]
    
    # Query Together AI with chat/completions endpoint
    together_url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.7
    }
    print("Sending to Together AI:", payload)  # Debug print
    response = requests.post(together_url, headers=headers, json=payload, timeout=60)
    print("Together AI response status:", response.status_code)  # Debug print
    print("Together AI response text:", response.text)  # Debug print
    
    if response.status_code == 200:
        result = response.json()
        answer = result.get("choices", [{}])[0].get("message", {}).get("content", "No response")
        sources = [metadata.get(str(i), "Unknown") for i in retrieved_indices if i < len(texts)]
        return {"question": question, "answer": answer, "sources": sources}
    else:
        return {"question": question, "error": f"Together AI Error: {response.status_code} - {response.text}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)