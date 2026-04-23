from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    session_id: str | None = None
    query_mode: str = "hybrid"

class ChatSessionCreate(BaseModel):
    title: str = "New chat"

class ChatSessionUpdate(BaseModel):
    title: str
