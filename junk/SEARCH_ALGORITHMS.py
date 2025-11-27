"""
Alternative Search Algorithms for FreelanceHub
Choose one and copy it to src/utils/search_engine.py
"""

# ==========================================
# OPTION 1: Simple Keyword Search (Fast, No AI)
# ==========================================
class KeywordSearchQuery:
    """Fast keyword-based search without AI"""
    def __init__(self, items):
        self.items = items
    
    def search(self, query):
        query_lower = query.lower()
        results = []
        
        for item in self.items:
            score = 0
            # Search in title (weighted higher)
            if query_lower in item.title.lower():
                score += 10
            # Search in description
            if query_lower in item.description.lower():
                score += 5
            # Search in resume
            if item.resume and query_lower in item.resume.lower():
                score += 3
            
            if score > 0:
                results.append((item, score))
        
        # Sort by score
        return sorted(results, key=lambda x: x[1], reverse=True)


# ==========================================
# OPTION 2: Semantic Search with Price Filter
# ==========================================
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

class FilteredSemanticSearch:
    """Semantic search with price filtering"""
    def __init__(self, items):
        self.items = items
        self.text = [f"TITLE: {item.title}. DESCRIPTION: {item.description}." for item in items]
    
    def search(self, query, min_price=None, max_price=None, category=None):
        # Filter by price and category first
        filtered_items = []
        filtered_text = []
        
        for i, item in enumerate(self.items):
            # Apply filters
            if min_price and item.price < min_price:
                continue
            if max_price and item.price > max_price:
                continue
            if category and hasattr(item, 'tag') and item.tag != category:
                continue
            
            filtered_items.append(item)
            filtered_text.append(self.text[i])
        
        if not filtered_items:
            return []
        
        # Semantic search on filtered results
        query_embedding = model.encode(query, normalize_embeddings=True)
        text_embedding = model.encode(filtered_text, normalize_embeddings=True)
        similarities = cosine_similarity([query_embedding], text_embedding)[0]
        
        ranked = sorted(
            zip(filtered_items, similarities), 
            key=lambda x: x[1], 
            reverse=True
        )
        return ranked


# ==========================================
# OPTION 3: Hybrid Search (Keywords + AI)
# ==========================================
class HybridSearch:
    """Combines keyword matching with semantic search"""
    def __init__(self, items):
        self.items = items
        self.text = [f"{item.title} {item.description}" for item in items]
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
    
    def search(self, query):
        query_lower = query.lower()
        
        # Get semantic scores
        query_embedding = self.model.encode(query, normalize_embeddings=True)
        text_embedding = self.model.encode(self.text, normalize_embeddings=True)
        semantic_scores = cosine_similarity([query_embedding], text_embedding)[0]
        
        # Calculate keyword scores
        keyword_scores = []
        for item in self.items:
            score = 0
            if query_lower in item.title.lower():
                score += 0.5  # Exact match bonus
            if query_lower in item.description.lower():
                score += 0.3
            keyword_scores.append(score)
        
        # Combine scores (70% semantic, 30% keyword)
        combined_scores = [
            0.7 * sem + 0.3 * key 
            for sem, key in zip(semantic_scores, keyword_scores)
        ]
        
        ranked = sorted(
            zip(self.items, combined_scores), 
            key=lambda x: x[1], 
            reverse=True
        )
        return ranked


# ==========================================
# OPTION 4: TF-IDF Search (Traditional ML)
# ==========================================
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TfidfSearch:
    """Traditional TF-IDF based search"""
    def __init__(self, items):
        self.items = items
        self.texts = [f"{item.title} {item.description}" for item in items]
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.vectorizer.fit_transform(self.texts)
    
    def search(self, query):
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]
        
        ranked = sorted(
            zip(self.items, similarities), 
            key=lambda x: x[1], 
            reverse=True
        )
        return ranked


# ==========================================
# OPTION 5: Fuzzy Matching Search
# ==========================================
from difflib import SequenceMatcher

class FuzzySearch:
    """Fuzzy string matching for typo tolerance"""
    def __init__(self, items):
        self.items = items
    
    def search(self, query):
        query_lower = query.lower()
        results = []
        
        for item in self.items:
            # Calculate fuzzy match ratio
            title_ratio = SequenceMatcher(None, query_lower, item.title.lower()).ratio()
            desc_ratio = SequenceMatcher(None, query_lower, item.description.lower()).ratio()
            
            # Combined score
            score = max(title_ratio * 2, desc_ratio)  # Title weighted higher
            results.append((item, score))
        
        return sorted(results, key=lambda x: x[1], reverse=True)
