import os
from dotenv import load_dotenv

load_dotenv()

def _split_csv(value: str, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]

class AppConfig:
    TITLE = "Enterprise RAG System"
    VERSION = "1.0.0"
    CORS_ORIGINS = _split_csv(os.getenv("CORS_ORIGINS"), ["http://localhost:5173"])

class SecurityConfig:
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS = 24
    TOKEN_URL = "auth/login"
    SECRET_KEY = os.getenv("SECRET_KEY")

    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set in the backend environment")

class LLMConfig:
    MODEL_NAME = "llama-3.1-8b-instant"
    SYSTEM_PROMPT = "You are an intelligent assistant. Use the following context to answer the user's question. If document-only mode is enabled and the answer is not in the context, say you could not find it in the uploaded documents.\n\nDocument-only mode: {document_only}\n\nContext:\n{context}"
    HISTORY_LIMIT = 5

class VectorStoreConfig:
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    FAISS_DIMENSIONS = 384
    SEARCH_K = 3
    STORAGE_DIR = os.getenv("VECTOR_STORE_DIR", "data/faiss_index")

class UploadConfig:
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 150
    ALLOWED_EXTENSIONS = ('.txt', '.md', '.csv', '.pdf', '.docx', '.png', '.jpg', '.jpeg')

class Settings:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "mssql+pyodbc://YOUR_SERVER_ID:YOUR_PASSWORD@YOUR_SERVER_NAME/YOUR_DB_NAME?driver=ODBC+Driver+17+for+SQL+Server")
    
    app = AppConfig()
    security = SecurityConfig()
    llm = LLMConfig()
    vector_store = VectorStoreConfig()
    upload = UploadConfig()

settings = Settings()
