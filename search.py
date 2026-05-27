from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

def similarity(a, b):
    # Cosine similarity - measures how similar two meanings are
    # Returns a number between 0 and 1, where 1 is identical meaning
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

verses = [
    "For God so loved the world that he gave his only Son",
    "Love your neighbor as yourself",
    "The Lord is my shepherd, I shall not want",
    "God is love",
    "In the beginning God created the heavens and the earth",
]

query = "God loves us"

query_embedding = model.encode(query)
verse_embeddings = model.encode(verses)

print(f"Query: '{query}'\n")
print("Similarity scores:")
for i, verse in enumerate(verses):
    score = similarity(query_embedding, verse_embeddings[i])
    print(f"{score:.3f} - {verse}")