import anthropic
import requests
import os
import json
import csv
import re 
import numpy as np
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

class UTF8JSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(content, ensure_ascii=False).encode('utf-8')

load_dotenv()

# Load Anthropic client
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

ESV_API_KEY = os.getenv("ESV_API_KEY")
app = FastAPI(default_response_class=UTF8JSONResponse)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Load Strongs on startup
print("Loading Strongs concordance...")

def load_strongs():
    with open('strongs-master/greek/strongs-greek-dictionary.js', 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'=\s*({.*})', content, re.DOTALL)
    greek = json.loads(match.group(1))
    
    with open('strongs-master/hebrew/strongs-hebrew-dictionary.js', 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'=\s*({.*})', content, re.DOTALL)
    hebrew = json.loads(match.group(1))
    return greek, hebrew

greek_dict, hebrew_dict = load_strongs()
print(f"Loaded {len(greek_dict)} Greek and {len(hebrew_dict)} Hebrew words!")

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

BOOK_ALIASES = {
    # Old Testament
    'gen': 'Genesis', 'ex': 'Exodus', 'exod': 'Exodus',
    'lev': 'Leviticus', 'num': 'Numbers', 'deut': 'Deuteronomy',
    'josh': 'Joshua', 'judg': 'Judges', 'ru': 'Ruth',
    '1sam': '1 Samuel', '2sam': '2 Samuel',
    '1ki': '1 Kings', '1kgs': '1 Kings', '2ki': '2 Kings', '2kgs': '2 Kings',
    '1chr': '1 Chronicles', '2chr': '2 Chronicles',
    'ezr': 'Ezra', 'neh': 'Nehemiah', 'esth': 'Esther',
    'ps': 'Psalms', 'psa': 'Psalms', 'pss': 'Psalms',
    'prov': 'Proverbs', 'pro': 'Proverbs',
    'eccl': 'Ecclesiastes', 'ecc': 'Ecclesiastes',
    'song': 'Song of Solomon', 'sos': 'Song of Solomon',
    'isa': 'Isaiah', 'jer': 'Jeremiah', 'lam': 'Lamentations',
    'ezek': 'Ezekiel', 'eze': 'Ezekiel',
    'dan': 'Daniel', 'hos': 'Hosea',
    'obad': 'Obadiah', 'ob': 'Obadiah',
    'jon': 'Jonah', 'jnh': 'Jonah',
    'mic': 'Micah', 'nah': 'Nahum', 'hab': 'Habakkuk',
    'zeph': 'Zephaniah', 'zep': 'Zephaniah',
    'hag': 'Haggai', 'zech': 'Zechariah', 'zec': 'Zechariah',
    'mal': 'Malachi',
    # New Testament
    'matt': 'Matthew', 'mat': 'Matthew', 'mt': 'Matthew',
    'mk': 'Mark', 'mr': 'Mark',
    'lk': 'Luke', 'lu': 'Luke',
    'jn': 'John', 'jhn': 'John', 'jo': 'John',
    'ac': 'Acts',
    'rom': 'Romans', 'ro': 'Romans',
    '1cor': '1 Corinthians', '1co': '1 Corinthians',
    '2cor': '2 Corinthians', '2co': '2 Corinthians',
    'gal': 'Galatians', 'ga': 'Galatians',
    'eph': 'Ephesians',
    'phil': 'Philippians', 'php': 'Philippians',
    'col': 'Colossians',
    '1thess': '1 Thessalonians', '1th': '1 Thessalonians',
    '2thess': '2 Thessalonians', '2th': '2 Thessalonians',
    '1tim': '1 Timothy', '1ti': '1 Timothy',
    '2tim': '2 Timothy', '2ti': '2 Timothy',
    'tit': 'Titus',
    'phlm': 'Philemon', 'phm': 'Philemon',
    'heb': 'Hebrews',
    'jas': 'James', 'jam': 'James',
    '1pet': '1 Peter', '1pe': '1 Peter',
    '2pet': '2 Peter', '2pe': '2 Peter',
    '1jn': '1 John', '1jo': '1 John',
    '2jn': '2 John', '2jo': '2 John',
    '3jn': '3 John', '3jo': '3 John',
    'jud': 'Jude',
    'rev': 'Revelation', 're': 'Revelation',
}

def normalize_reference(query):
    query = query.strip()
    # Match optional leading number, book name, then chapter:verse
    match = re.match(r'^(\d\s?)?([a-zA-Z]+)\.?\s*(\d+)?(\:\d+(-\d+)?)?$', query)
    if not match:
        return query
    
    prefix = (match.group(1) or '').strip()
    book = match.group(2).lower()
    chapter_verse = (match.group(3) or '') + (match.group(4) or '')
    
    # Build lookup key
    key = (prefix + book).replace(' ', '') if prefix else book
    
    full_book = BOOK_ALIASES.get(key) or BOOK_ALIASES.get(book)
    if not full_book:
        return query
    
    if chapter_verse:
        return f"{full_book} {chapter_verse}"
    return full_book

def is_bible_reference(query):
    # Matches patterns like "John 3:16", "Romans 8", "1 Corinthians 13:4-7"
    pattern = r'^(\d\s)?[a-zA-Z]+\.?\s+\d+(\:\d+(-\d+)?)?$'
    return bool(re.match(pattern, query.strip()))

@app.get("/search")
def search_endpoint(q: str):
    normalized = normalize_reference(q)
    if is_bible_reference(normalized):
        passage = get_passage(normalized)
        return {
            "query": q,
            "type": "passage",
            "results": [{"reference": passage["reference"], "text": passage["text"], "score": 1.0}]
        }
    else:
        return {
            "query": q,
            "type": "search",
            "results": search_verses(q)
        }

@app.get("/crossreferences")
def cross_references_endpoint(q: str):
    refs = cross_refs.get(q, [])[:10]
    return {"verse": q, "cross_references": refs}

@app.get("/strongs")
def strongs_endpoint(id: str):
    id = id.upper()
    if id.startswith('G'):
        entry = greek_dict.get(id)
        language = "Greek"
    elif id.startswith('H'):
        entry = hebrew_dict.get(id)
        language = "Hebrew"
    else:
        return {"error": "ID must start with G (Greek) or H (Hebrew)"}
    
    if not entry:
        return {"error": f"No entry found for {id}"}
    
    return {
        "id": id,
        "language": language,
        "lemma": entry.get('lemma', '').encode('utf-8').decode('utf-8'),
        "transliteration": (entry.get('translit') or entry.get('xlit', '')).encode('utf-8').decode('utf-8'),
        "pronunciation": entry.get('pron', ''),
        "definition": entry.get('strongs_def', '').strip(),
        "kjv_usage": entry.get('kjv_def', '')
    }

@app.get("/assistant")
def assistant_endpoint(q: str, verse: str = ""):
    # If a verse is selected, fetch its cross references to give the AI context
    context_refs = []
    context_passage = ""
    
    if verse:
        # Get the passage text
        passage_data = get_passage(verse)
        context_passage = f"{passage_data['reference']}: {passage_data['text']}"
        
        # Get cross references
        refs = cross_refs.get(verse, [])[:5]
        for ref in refs:
            ref_data = get_passage(ref['reference'])
            context_refs.append(f"{ref_data['reference']}: {ref_data['text']}")
    
    # Build the context string
    context = ""
    if context_passage:
        context += f"\nSelected verse:\n{context_passage}\n"
    if context_refs:
        context += f"\nRelated verses:\n" + "\n".join(context_refs)
    
    system_prompt = """You are a Bible study research assistant. Your role is to help users explore and understand scripture by presenting what the data, history, and scholarship says — never by giving your own theological conclusions or taking doctrinal positions.

Your guidelines:
- Present information from multiple perspectives when there is disagreement
- Always cite scripture references when relevant
- For historical questions, provide historical context and facts
- For doctrinal debates, present what each side believes and their supporting verses — never pick a side
- For pastoral questions, surface relevant scripture and commentary themes
- Never say "I believe", "I think", or give a personal theological opinion
- End responses by pointing the user toward the data: suggest related passages, topics, or questions they can explore further
- Keep responses concise and organized
- You are a librarian, not a theologian"""

    user_message = f"{context}\n\nUser question: {q}" if context else q

    message = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    return {"response": message.content[0].text}

@app.get("/keywords")
def keywords_endpoint(reference: str):
    # Determine testament from book name
    nt_books = [
        "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
        "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
        "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
        "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews",
        "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John",
        "Jude", "Revelation"
    ]
    
    book = ' '.join(reference.split()[:-1])
    is_nt = book in nt_books
    dictionary = greek_dict if is_nt else hebrew_dict
    language = "Greek" if is_nt else "Hebrew"
    
    # Get the verse text
    passage_data = get_passage(reference)
    verse_text = passage_data['text'].lower()
    
    # Key theological words to look for
    greek_keywords = {
        "love": "G26", "grace": "G5485", "faith": "G4102",
        "hope": "G1680", "peace": "G1515", "joy": "G5479",
        "spirit": "G4151", "truth": "G225", "life": "G2222",
        "light": "G5457", "word": "G3056", "god": "G2316",
        "lord": "G2962", "christ": "G5547", "jesus": "G2424",
        "sin": "G266", "salvation": "G4991", "righteousness": "G1343",
        "mercy": "G1656", "glory": "G1391", "power": "G1411",
        "prayer": "G4335", "believe": "G4100", "heart": "G2588",
        "soul": "G5590", "eternal": "G166", "kingdom": "G932",
        "forgive": "G863", "holy": "G40", "wisdom": "G4678"
    }
    
    hebrew_keywords = {
        "love": "H157", "grace": "H2580", "faith": "H530",
        "hope": "H8615", "peace": "H7965", "joy": "H8342",
        "spirit": "H7307", "truth": "H571", "life": "H2416",
        "light": "H216", "word": "H1697", "god": "H430",
        "lord": "H3068", "sin": "H2403", "salvation": "H3444",
        "righteousness": "H6666", "mercy": "H2617", "glory": "H3519",
        "power": "H3581", "heart": "H3820", "soul": "H5315",
        "holy": "H6944", "wisdom": "H2451", "fear": "H3374",
        "covenant": "H1285", "praise": "H1984", "blessed": "H835"
    }
    
    keywords = greek_keywords if is_nt else hebrew_keywords
    found = []
    
    for word, strongs_id in keywords.items():
        if word in verse_text:
            entry = dictionary.get(strongs_id)
            if entry:
                found.append({
                    "word": word,
                    "strongs_id": strongs_id,
                    "language": language,
                    "lemma": entry.get('lemma', ''),
                    "transliteration": entry.get('translit') or entry.get('xlit', ''),
                    "definition": entry.get('strongs_def', '').strip()
                })
    
    return {
        "reference": reference,
        "language": language,
        "keywords": found
    }