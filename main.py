import requests
import os
from dotenv import load_dotenv

load_dotenv()

ESV_API_KEY = os.getenv("ESV_API_KEY")

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
    
    return {
        "reference": data["canonical"],
        "text": data["passages"][0].strip()
    }

# Test it
result = get_passage("Lamentations 3:22-23")
print(f"Reference: {result['reference']}")
print(f"Text: {result['text']}")