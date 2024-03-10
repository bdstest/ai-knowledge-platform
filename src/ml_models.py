"""Machine Learning models for knowledge retrieval and incident prediction."""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """Enhanced knowledge retrieval using TF-IDF and semantic search."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 3)
        )
        self.document_vectors = None
        self.documents = []
        
    def index_documents(self, documents: List[Dict[str, str]]):
        """Index documents for similarity search."""
        self.documents = documents
        texts = [doc['content'] for doc in documents]
        self.document_vectors = self.vectorizer.fit_transform(texts)
        logger.info(f"Indexed {len(documents)} documents")
        
    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict, float]]:
        """Search for relevant documents."""
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.document_vectors)[0]
        
        # Get top-k most similar documents
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Minimum similarity threshold
                results.append((self.documents[idx], float(similarities[idx])))
                
        return results


class IncidentPredictor:
    """Predict incident severity and resolution time."""
    
    def __init__(self):
        self.severity_patterns = {
            'critical': ['down', 'outage', 'crash', 'failed', 'emergency'],
            'high': ['error', 'slow', 'timeout', 'blocked', 'urgent'],
            'medium': ['warning', 'delay', 'issue', 'problem'],
            'low': ['minor', 'cosmetic', 'typo', 'enhancement']
        }
        
    def predict_severity(self, description: str) -> str:
        """Predict incident severity based on description."""
        description_lower = description.lower()
        
        for severity, patterns in self.severity_patterns.items():
            if any(pattern in description_lower for pattern in patterns):
                return severity
                
        return 'medium'  # Default severity
        
    def estimate_resolution_time(self, severity: str, category: str) -> int:
        """Estimate resolution time in minutes."""
        base_times = {
            'critical': 30,
            'high': 60,
            'medium': 120,
            'low': 240
        }
        
        category_multipliers = {
            'infrastructure': 1.5,
            'application': 1.0,
            'security': 2.0,
            'database': 1.3,
            'network': 1.4
        }
        
        base_time = base_times.get(severity, 120)
        multiplier = category_multipliers.get(category, 1.0)
        
        return int(base_time * multiplier)