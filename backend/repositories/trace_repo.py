import json

from db.database import SessionLocal
from db.models import QueryTrace


class TraceRepository:
    def add_trace(
        self,
        user_id: str,
        session_id: str,
        question: str,
        answer: str,
        model_name: str,
        query_mode: str,
        latency_ms: int,
        sources: list,
    ):
        with SessionLocal() as db:
            trace = QueryTrace(
                user_id=user_id,
                session_id=session_id,
                question=question,
                answer=answer,
                model_name=model_name,
                query_mode=query_mode,
                latency_ms=latency_ms,
                source_count=len(sources),
                sources=json.dumps(sources, ensure_ascii=False),
            )
            db.add(trace)
            db.commit()
            db.refresh(trace)
            return self._to_dict(trace)

    def get_traces(self, user_id: str | None = None, limit: int = 100):
        with SessionLocal() as db:
            query = db.query(QueryTrace)
            if user_id:
                query = query.filter(QueryTrace.user_id == user_id)
            traces = query.order_by(QueryTrace.created_at.desc(), QueryTrace.id.desc()).limit(limit).all()
            return [self._to_dict(trace) for trace in traces]

    def _to_dict(self, trace):
        return {
            "id": trace.id,
            "user_id": trace.user_id,
            "session_id": trace.session_id,
            "question": trace.question,
            "answer": trace.answer,
            "model_name": trace.model_name,
            "query_mode": trace.query_mode,
            "latency_ms": trace.latency_ms,
            "source_count": trace.source_count,
            "created_at": trace.created_at.isoformat() if trace.created_at else None,
        }
