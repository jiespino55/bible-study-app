import json
import numpy as np
from sentence_transformers import SentenceTransformer

# Load everything
print("Loading...")
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = np.load('embeddings.npy')
with open('verses.json', 'r') as f:
    verses = json.load(f)
print("Ready!")

def search(query, top_k=5):
    query_embedding = model.encode(query)
    
    # Calculate similarity between query and all verses
    similarities = np.dot(embeddings, query_embedding) / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    
    # Get top results
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        results.append({
            "reference": verses[idx]['reference'],
            "text": verses[idx]['text'],
            "score": float(similarities[idx])
        })
    
    return results

# Test it
results = search("the armor of God")
print("\nResults for 'the armor of God':")
for r in results:
    print(f"\n{r['reference']} (score: {r['score']:.3f})")
    print(f"{r['text']}")