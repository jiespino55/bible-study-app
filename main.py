import requests
import os
import json
import numpy as np
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

ESV_API_KEY = os.getenv("ESV_API_KEY")
app = FastAPI()

# Load search engine on startup
print("Loading search engine...")
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = np.load('embeddings.npy')
with open('verses.json', 'r') as f:
    verses = json.load(f)
print("Search engine ready!")

def get_passage(passage):
    url = "https://api.esv.org/v3/passage/text/"
    headers = {"Authorization": f"Token {ESV_API_KEY}"}
    params = {
        "q": passage,
        "include-headings": False,
        "include-footnotes": False,
        "include-verse-numbers": True,
        "include-short-copyright": False,
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    lines = data["passages"][0].strip().split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    if cleaned_lines and cleaned_lines[0] == data["canonical"]:
        cleaned_lines = cleaned_lines[1:]
    text = ' '.join(cleaned_lines)
    text = text.replace('\u201c', '"').replace('\u201d', '"').replace('\u2018', "'").replace('\u2019', "'")
    return {
        "reference": data["canonical"],
        "text": text
    }

def search_verses(query, top_k=5):
    query_embedding = model.encode(query)
    similarities = np.dot(embeddings, query_embedding) / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    top_indices = np.argsort(similarities)[::-1][:top_k]
    results = []
    for idx in top_indices:
        results.append({
            "reference": verses[idx]['reference'],
            "text": verses[idx]['text'],
            "score": float(similarities[idx])
        })
    return results

@app.get("/passage")
def passage_endpoint(q: str):
    return get_passage(q)

@app.get("/search")
def search_endpoint(q: str):
    return {"query": q, "results": search_verses(q)}