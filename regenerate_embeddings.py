import json
import numpy as np
import google.generativeai as genai
import os
import time
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

print("Loading verses...")
with open('verses.json', 'r') as f:
    verses = json.load(f)

print(f"Loaded {len(verses)} verses")
print("Generating embeddings with Google Gemini...")
print("This will take about 35-40 minutes due to free tier rate limits...")

texts = [v['text'] for v in verses]
all_embeddings = []
batch_size = 50
total_batches = len(texts) // batch_size + 1
requests_this_minute = 0
minute_start = time.time()

for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    batch_num = i//batch_size + 1

    # Rate limiting - max 90 requests per minute (buffer below 100)
    requests_this_minute += 1
    if requests_this_minute >= 90:
        elapsed = time.time() - minute_start
        if elapsed < 60:
            wait = 60 - elapsed + 2
            print(f"Rate limit pause: waiting {wait:.0f} seconds...")
            time.sleep(wait)
        requests_this_minute = 0
        minute_start = time.time()

    try:
        result = genai.embed_content(
            model='models/gemini-embedding-001',
            content=batch,
            task_type='retrieval_document'
        )
        all_embeddings.extend(result['embedding'])
        print(f"Batch {batch_num}/{total_batches} done ({len(all_embeddings)} verses so far)")
    except Exception as e:
        print(f"Error on batch {batch_num}: {e}")
        print("Waiting 60 seconds...")
        time.sleep(60)
        requests_this_minute = 0
        minute_start = time.time()
        try:
            result = genai.embed_content(
                model='models/gemini-embedding-001',
                content=batch,
                task_type='retrieval_document'
            )
            all_embeddings.extend(result['embedding'])
            print(f"Batch {batch_num}/{total_batches} done (after retry)")
        except Exception as e2:
            print(f"Failed again: {e2}, skipping batch")

embeddings = np.array(all_embeddings)
np.save('embeddings.npy', embeddings)
print(f"Done! Shape: {embeddings.shape}")
print("Saved to embeddings.npy")