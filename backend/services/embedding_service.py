from sentence_transformers import SentenceTransformer
from core.config import settings

model = SentenceTransformer(settings.vector_store.EMBEDDING_MODEL)

def get_embedding(text: str):
    return model.encode(text)