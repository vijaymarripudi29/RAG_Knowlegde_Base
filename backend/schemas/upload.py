from pydantic import BaseModel


class UploadedDocument(BaseModel):
    id: int
    session_id: str | None = None
    filename: str
    chunk_count: int
    created_at: str | None = None


class UploadResponse(BaseModel):
    message: str
    document: UploadedDocument
