import requests
import os
import json
import csv
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

# Load cross references on startup
print("Loading cross references...")

def parse_reference(ref):
    book_map = {
        'Gen': 'Genesis', 'Exod': 'Exodus', 'Lev': 'Leviticus',
        'Num': 'Numbers', 'Deut': 'Deuteronomy', 'Josh': 'Joshua',
        'Judg': 'Judges', 'Ruth': 'Ruth', '1Sam': '1 Samuel',
        '2Sam': '2 Samuel', '1Kgs': '1 Kings', '2Kgs': '2 Kings',
        '1Chr': '1 Chronicles', '2Chr': '2 Chronicles', 'Ezra': 'Ezra',
        'Neh': 'Nehemiah', 'Esth': 'Esther', 'Job': 'Job',
        'Ps': 'Psalms', 'Prov': 'Proverbs', 'Eccl': 'Ecclesiastes',
        'Song': 'Song of Solomon', 'Isa': 'Isaiah', 'Jer': 'Jeremiah',
        'Lam': 'Lamentations', 'Ezek': 'Ezekiel', 'Dan': 'Daniel',
        'Hos': 'Hosea', 'Joel': 'Joel', 'Amos': 'Amos', 'Obad': 'Obadiah',
        'Jonah': 'Jonah', 'Mic': 'Micah', 'Nah': 'Nahum', 'Hab': 'Habakkuk',
        'Zeph': 'Zephaniah', 'Hag': 'Haggai', 'Zech': 'Zechariah',
        'Mal': 'Malachi', 'Matt': 'Matthew', 'Mark': 'Mark', 'Luke': 'Luke',
        'John': 'John', 'Acts': 'Acts', 'Rom': 'Romans', '1Cor': '1 Corinthians',
        '2Cor': '2 Corinthians', 'Gal': 'Galatians', 'Eph': 'Ephesians',
        'Phil': 'Philippians', 'Col': 'Colossians', '1Thess': '1 Thessalonians',
        '2Thess': '2 Thessalonians', '1Tim': '1 Timothy', '2Tim': '2 Timothy',
        'Titus': 'Titus', 'Phlm': 'Philemon', 'Heb': 'Hebrews', 'Jas': 'James',
        '1Pet': '1 Peter', '2Pet': '2 Peter', '1John': '1 John', '2John': '2 John',
        '3John': '3 John', 'Jude': 'Jude', 'Rev': 'Revelation'
    }
    ref = ref.split('-')[0]
    parts = ref.split('.')
    if len(parts) < 3:
        return None
    book_name = book_map.get(parts[0])
    if not book_name:
        return None
    return f"{book_name} {parts[1]}:{parts[2]}"

cross_refs = {}
with open('cross_references.txt', 'r') as f:
    reader = csv.reader(f, delimiter='\t')
    next(reader)
    for row in reader:
        if len(row) < 3:
            continue
        from_verse = parse_reference(row[0])
        to_verse = parse_reference(row[1])
        votes = int(row[2]) if row[2].isdigit() else 0
        if not from_verse or not to_verse:
            continue
        if from_verse not in cross_refs:
            cross_refs[from_verse] = []
        cross_refs[from_verse].append({
            "reference": to_verse,
            "votes": votes
        })

for verse in cross_refs:
    cross_refs[verse].sort(key=lambda x: x['votes'], reverse=True)

print(f"Loaded cross references for {len(cross_refs)} verses!")

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

@app.get("/crossreferences")
def cross_references_endpoint(q: str):
    refs = cross_refs.get(q, [])[:10]
    return {"verse": q, "cross_references": refs}