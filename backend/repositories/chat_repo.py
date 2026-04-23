import uuid
from datetime import datetime

from db.database import SessionLocal
from db.models import ChatMessage, ChatSession, Log


class ChatRepository:
    def create_session(self, user_id: str, title: str = "New chat"):
        with SessionLocal() as db:
            session = ChatSession(id=str(uuid.uuid4()), user_id=user_id, title=title)
            db.add(session)
            db.commit()
            db.refresh(session)
            return self._session_to_dict(session)

    def get_sessions(self, user_id: str):
        with SessionLocal() as db:
            sessions = (
                db.query(ChatSession)
                .filter(ChatSession.user_id == user_id)
                .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
                .all()
            )
            if not sessions:
                self._import_legacy_logs(db, user_id)
                sessions = (
                    db.query(ChatSession)
                    .filter(ChatSession.user_id == user_id)
                    .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
                    .all()
                )
            return [self._session_to_dict(session) for session in sessions]

    def get_session(self, user_id: str, session_id: str):
        with SessionLocal() as db:
            session = (
                db.query(ChatSession)
                .filter(ChatSession.user_id == user_id, ChatSession.id == session_id)
                .first()
            )
            return self._session_to_dict(session) if session else None

    def rename_session(self, user_id: str, session_id: str, title: str):
        clean_title = " ".join(title.strip().split())[:255]
        if not clean_title:
            clean_title = "New chat"

        with SessionLocal() as db:
            session = (
                db.query(ChatSession)
                .filter(ChatSession.user_id == user_id, ChatSession.id == session_id)
                .first()
            )
            if not session:
                return None

            session.title = clean_title
            session.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(session)
            return self._session_to_dict(session)

    def delete_session(self, user_id: str, session_id: str):
        with SessionLocal() as db:
            session = (
                db.query(ChatSession)
                .filter(ChatSession.user_id == user_id, ChatSession.id == session_id)
                .first()
            )
            if not session:
                return None
            deleted = self._session_to_dict(session)
            db.query(ChatMessage).filter(ChatMessage.user_id == user_id, ChatMessage.session_id == session_id).delete()
            db.delete(session)
            db.commit()
            return deleted

    def ensure_session(self, user_id: str, session_id: str | None, first_question: str):
        if session_id:
            existing = self.get_session(user_id, session_id)
            if existing:
                return existing

        title = self._title_from_question(first_question)
        return self.create_session(user_id, title)

    def add_message(self, user_id: str, session_id: str, question: str, answer: str):
        with SessionLocal() as db:
            message = ChatMessage(
                user_id=user_id,
                session_id=session_id,
                question=question,
                answer=answer,
            )
            db.add(message)

            session = (
                db.query(ChatSession)
                .filter(ChatSession.user_id == user_id, ChatSession.id == session_id)
                .first()
            )
            if session:
                if session.title in ("New chat", "New RAG chat"):
                    session.title = self._title_from_question(question)
                session.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(message)
            return self._message_to_dict(message)

    def get_messages(self, user_id: str, session_id: str, newest_first: bool = False):
        with SessionLocal() as db:
            query = db.query(ChatMessage).filter(
                ChatMessage.user_id == user_id,
                ChatMessage.session_id == session_id,
            )
            order = ChatMessage.timestamp.desc() if newest_first else ChatMessage.timestamp.asc()
            messages = query.order_by(order, ChatMessage.id.asc()).all()
            return [self._message_to_dict(message) for message in messages]

    def _title_from_question(self, question: str):
        title = " ".join(question.strip().split())
        return title[:60] or "New chat"

    def _import_legacy_logs(self, db, user_id: str):
        logs = (
            db.query(Log)
            .filter(Log.user_id == user_id)
            .order_by(Log.timestamp.asc(), Log.id.asc())
            .all()
        )
        if not logs:
            return

        session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title="Previous chat",
        )
        db.add(session)
        db.flush()

        for log in logs:
            db.add(
                ChatMessage(
                    user_id=user_id,
                    session_id=session.id,
                    question=log.question,
                    answer=log.answer,
                )
            )
        db.commit()

    def _session_to_dict(self, session):
        return {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        }

    def _message_to_dict(self, message):
        return {
            "id": message.id,
            "session_id": message.session_id,
            "question": message.question,
            "answer": message.answer,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None,
        }
