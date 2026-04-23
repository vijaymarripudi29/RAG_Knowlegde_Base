from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from repositories.vector_repo import VectorRepo
from services.embedding_service import get_embedding
from services.file_parser_service import FileParserService
from core.security import get_current_user
from core.config import settings
from api.controller.query_controller import vector_repo
from repositories.chat_repo import ChatRepository
from repositories.document_repo import DocumentRepository

router = APIRouter(prefix="/upload")
file_parser = FileParserService()
document_repo = DocumentRepository()
chat_repo = ChatRepository()

def chunk_text(text: str, chunk_size: int = settings.upload.CHUNK_SIZE):
    chunks = []
    step = max(1, chunk_size - settings.upload.CHUNK_OVERLAP)
    for i in range(0, len(text), step):
        chunks.append(text[i:i+chunk_size])
    return chunks

def build_chunks(text: str):
    return [
        {"content": chunk, "chunk_index": index, "page_number": None}
        for index, chunk in enumerate(chunk_text(text))
        if chunk.strip()
    ]

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    user_id: str = Depends(get_current_user),
):
    session = chat_repo.get_session(user_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    if not file.filename.lower().endswith(settings.upload.ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail=f"Unsupported file format. Supported extensions: {settings.upload.ALLOWED_EXTENSIONS}")
    
    content = await file.read()
    
    try:
        text = file_parser.parse_file(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse file: {str(e)}")
        
    stored_chunks = build_chunks(text)
    document = document_repo.add_document(user_id, session_id, file.filename, stored_chunks)

    for chunk in stored_chunks:
        source = {
            "document_id": document["id"],
            "filename": file.filename,
            "chunk_index": chunk["chunk_index"],
            "page_number": chunk.get("page_number"),
            "content": chunk["content"],
        }
        embedding = get_embedding(chunk["content"])
        vector_repo.add(user_id, embedding, source, session_id=session_id)
        
    return {
        "message": f"Successfully processed and stored {len(stored_chunks)} chunks.",
        "document": document,
    }

@router.get("/documents")
def list_documents(session_id: str | None = None, user_id: str = Depends(get_current_user)):
    return document_repo.get_documents(user_id, session_id)

@router.get("/documents/{document_id}/chunks")
def preview_document(document_id: int, session_id: str, user_id: str = Depends(get_current_user)):
    chunks = document_repo.get_document_chunks(user_id, session_id, document_id)
    if not chunks:
        raise HTTPException(status_code=404, detail="Document chunks not found")
    return chunks

@router.post("/documents/{document_id}/reindex")
def reindex_document(document_id: int, session_id: str, user_id: str = Depends(get_current_user)):
    chunks = document_repo.get_session_chunks(user_id, session_id)
    if not chunks:
        vector_repo.clear(user_id, session_id=session_id)
        return {"message": "No chunks found. Cleared vector index."}
    embedded_chunks = [(get_embedding(chunk["content"]), chunk) for chunk in chunks]
    vector_repo.replace(user_id, embedded_chunks, session_id=session_id)
    return {"message": "Re-indexed this chat knowledge base."}

@router.delete("/documents/{document_id}")
def delete_document(document_id: int, session_id: str, user_id: str = Depends(get_current_user)):
    deleted = document_repo.delete_document(user_id, session_id, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    remaining_chunks = document_repo.get_session_chunks(user_id, session_id)
    embedded_chunks = [(get_embedding(chunk["content"]), chunk) for chunk in remaining_chunks]
    vector_repo.replace(user_id, embedded_chunks, session_id=session_id)

    return {
        "message": "Document removed from this chat knowledge base.",
        "document": deleted,
    }
