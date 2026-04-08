import numpy as np
import os
from vertexai.language_models import TextEmbeddingModel
from db.database import get_all_modules

def embed_text(text: str) -> np.ndarray:
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    response = model.get_embeddings([text])
    return np.array(response[0].values, dtype=np.float32)

def serialize_vector(vector: np.ndarray) -> bytes:
    return vector.tobytes()

def deserialize_vector(blob: bytes) -> np.ndarray:
    if not blob:
        return np.array([], dtype=np.float32)
    return np.frombuffer(blob, dtype=np.float32)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or b.size == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def search_related_modules(repo_url: str, query: str, top_k: int = 5):
    query_vector = embed_text(query)
    modules = get_all_modules(repo_url)
    
    scored_modules = []
    for mod in modules:
        if not mod.get('vector_blob'):
            continue
        mod_vector = deserialize_vector(mod['vector_blob'])
        score = cosine_similarity(query_vector, mod_vector)
        scored_modules.append((score, mod['path'], mod['summary']))
        
    scored_modules.sort(key=lambda x: x[0], reverse=True)
    return scored_modules[:top_k]
