from fastapi import APIRouter, Depends, HTTPException

from core.security import get_current_user
from repositories.chat_repo import ChatRepository
from repositories.document_repo import DocumentRepository
from repositories.trace_repo import TraceRepository
from repositories.user_repo import UserRepository


router = APIRouter()
user_repo = UserRepository()
chat_repo = ChatRepository()
document_repo = DocumentRepository()
trace_repo = TraceRepository()


APP_REGISTRY = [
    {
        "id": "rag",
        "name": "RAG Knowledge Base",
        "description": "Chat with session-specific document knowledge bases.",
        "icon": "database",
        "route": "rag",
        "required_role": "user",
    }
]


@router.get("/apps")
def list_apps(user_id: str = Depends(get_current_user)):
    return APP_REGISTRY


def require_admin(user_id: str):
    user = user_repo.get_user_by_id(user_id)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/admin/users")
def list_users(user_id: str = Depends(get_current_user)):
    require_admin(user_id)
    return user_repo.get_users()


@router.get("/admin/traces")
def list_traces(user_id: str = Depends(get_current_user)):
    require_admin(user_id)
    return trace_repo.get_traces(limit=200)


@router.get("/admin/summary")
def admin_summary(user_id: str = Depends(get_current_user)):
    require_admin(user_id)
    users = user_repo.get_users()
    traces = trace_repo.get_traces(limit=1000)
    return {
        "users": len(users),
        "recent_queries": len(traces),
        "apps": len(APP_REGISTRY),
    }
