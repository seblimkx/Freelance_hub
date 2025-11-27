"""Search engine for freelance posts using semantic similarity"""
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

class SearchQuery:
    def __init__(self, items):
        self.items = items
        self.text = [f"TITLE: {item.title}. DESCRIPTION: {item.description}. SELLER'S RESUME: {item.resume or ''}" for item in items]

    def search(self, query):
        query_embedding = model.encode(query, normalize_embeddings=True)
        text_embedding = model.encode(self.text, normalize_embeddings=True)
        if text_embedding is None or len(text_embedding) == 0:
            print("DEBUG: No text embeddings available.")
            return []
        similarities = cosine_similarity([query_embedding], text_embedding)[0]
        # Sorted expects key to be a function
        # reverse = True because we want top cosine similarity value first
        ranked = sorted(
            zip(self.items, similarities), key=lambda x: x[1], reverse=True
        )
        return ranked
