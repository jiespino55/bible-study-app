import requests
import os
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

ESV_API_KEY = os.getenv("ESV_API_KEY")

app = FastAPI()

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
    # Remove the first line if it's just the reference
    if cleaned_lines and cleaned_lines[0] == data["canonical"]:
        cleaned_lines = cleaned_lines[1:]
    text = ' '.join(cleaned_lines)
    text = text.replace('\u201c', '"').replace('\u201d', '"').replace('\u2018', "'").replace('\u2019', "'")

    return {
        "reference": data["canonical"],
        "text": text
    }   

@app.get("/passage")
def passage_endpoint(q: str):
    result = get_passage(q)
    return result