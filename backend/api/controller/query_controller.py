import json
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from schemas.query import ChatSessionCreate, ChatSessionUpdate, QueryRequest
from services.rag_service import RAGService
from repositories.vector_repo import VectorRepo
from repositories.chat_repo import ChatRepository
from repositories.document_repo import DocumentRepository
from repositories.trace_repo import TraceRepository
from services.llm_service import LLMService
from services.embedding_service import get_embedding
from core.security import get_current_user
from langchain_core.messages import HumanMessage, AIMessage
from core.config import settings

router = APIRouter()

vector_repo = VectorRepo()
chat_repo = ChatRepository()
document_repo = DocumentRepository()
trace_repo = TraceRepository()
llm_service = LLMService()
rag_service = RAGService(vector_repo, llm_service)

@router.get("/chats")
def get_chats(user_id: str = Depends(get_current_user)):
    return chat_repo.get_sessions(user_id)

@router.post("/chats")
def create_chat(req: ChatSessionCreate, user_id: str = Depends(get_current_user)):
    return chat_repo.create_session(user_id, req.title)

@router.patch("/chats/{session_id}")
def rename_chat(session_id: str, req: ChatSessionUpdate, user_id: str = Depends(get_current_user)):
    session = chat_repo.rename_session(user_id, session_id, req.title)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session

@router.delete("/chats/{session_id}")
def delete_chat(session_id: str, user_id: str = Depends(get_current_user)):
    session = chat_repo.delete_session(user_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    vector_repo.clear(user_id, session_id=session_id)
    document_repo.clear_session_documents(user_id, session_id)
    return {"message": "Chat deleted.", "session": session}

@router.get("/chats/{session_id}/messages")
def get_chat_messages(session_id: str, user_id: str = Depends(get_current_user)):
    return chat_repo.get_messages(user_id, session_id)

@router.post("/query")
def query(req: QueryRequest, user_id: str = Depends(get_current_user)):
    started_at = time.perf_counter()
    session = chat_repo.ensure_session(user_id, req.session_id, req.question)
    raw_logs = chat_repo.get_messages(user_id, session["id"], newest_first=True)
    raw_logs = raw_logs[:settings.llm.HISTORY_LIMIT]
    raw_logs.reverse()
    
    chat_history = []
    for log in raw_logs:
        chat_history.append(HumanMessage(content=log["question"]))
        chat_history.append(AIMessage(content=log["answer"]))

    result = rag_service.query(
        user_id=user_id,
        question=req.question,
        embedding_fn=get_embedding,
        chat_history=chat_history,
        session_id=session["id"],
        query_mode=req.query_mode,
    )
    
    chat_repo.add_message(user_id, session["id"], req.question, result["answer"])
    session = chat_repo.get_session(user_id, session["id"])
    trace_repo.add_trace(
        user_id=user_id,
        session_id=session["id"],
        question=req.question,
        answer=result["answer"],
        model_name=settings.llm.MODEL_NAME,
        query_mode=req.query_mode,
        latency_ms=int((time.perf_counter() - started_at) * 1000),
        sources=result["sources"],
    )
    result["session"] = session

    return result

@router.post("/query/stream")
def query_stream(req: QueryRequest, user_id: str = Depends(get_current_user)):
    session = chat_repo.ensure_session(user_id, req.session_id, req.question)
    raw_logs = chat_repo.get_messages(user_id, session["id"], newest_first=True)[:settings.llm.HISTORY_LIMIT]
    raw_logs.reverse()
    chat_history = []
    for log in raw_logs:
        chat_history.append(HumanMessage(content=log["question"]))
        chat_history.append(AIMessage(content=log["answer"]))

    query_emb = get_embedding(req.question)
    docs = vector_repo.search(user_id, query_emb, session_id=session["id"])

    def events():
        answer_parts = []
        if req.query_mode == "document_only" and not docs:
            text = "I could not find relevant information in the uploaded documents for this chat."
            answer_parts.append(text)
            yield f"data: {json.dumps({'type': 'token', 'content': text})}\n\n"
        else:
            for token in llm_service.stream(req.question, docs, chat_history, document_only=req.query_mode == "document_only"):
                answer_parts.append(token)
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        answer = "".join(answer_parts)
        chat_repo.add_message(user_id, session["id"], req.question, answer)
        updated_session = chat_repo.get_session(user_id, session["id"])
        yield f"data: {json.dumps({'type': 'done', 'answer': answer, 'sources': docs, 'session': updated_session})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
