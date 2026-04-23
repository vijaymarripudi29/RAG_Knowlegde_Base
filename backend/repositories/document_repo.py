from datetime import datetime

from db.database import SessionLocal
from db.models import ChatSession, Document, DocumentChunk


class DocumentRepository:
    def add_document(self, user_id: str, session_id: str, filename: str, chunks: list[dict]):
        with SessionLocal() as db:
            try:
                document = Document(
                    user_id=user_id,
                    session_id=session_id,
                    filename=filename,
                    chunk_count=len(chunks),
                )
                db.add(document)
                db.flush()

                for chunk in chunks:
                    db.add(
                        DocumentChunk(
                            document_id=document.id,
                            user_id=user_id,
                            session_id=session_id,
                            filename=filename,
                            chunk_index=chunk["chunk_index"],
                            page_number=chunk.get("page_number"),
                            content=chunk["content"],
                        )
                    )

                self._touch_session(db, user_id, session_id)

                db.commit()
                db.refresh(document)
                return self._document_to_dict(document)
            except Exception as e:
                db.rollback()
                raise e

    def get_documents(self, user_id: str, session_id: str | None = None):
        with SessionLocal() as db:
            query = db.query(Document).filter(Document.user_id == user_id)
            if session_id:
                query = query.filter(Document.session_id == session_id)

            documents = query.order_by(Document.created_at.desc(), Document.id.desc()).all()
            return [self._document_to_dict(document) for document in documents]

    def delete_document(self, user_id: str, session_id: str, document_id: int):
        with SessionLocal() as db:
            try:
                document = (
                    db.query(Document)
                    .filter(
                        Document.id == document_id,
                        Document.user_id == user_id,
                        Document.session_id == session_id,
                    )
                    .first()
                )
                if not document:
                    return None

                deleted = self._document_to_dict(document)
                db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
                db.delete(document)
                self._touch_session(db, user_id, session_id)
                db.commit()
                return deleted
            except Exception as e:
                db.rollback()
                raise e

    def get_session_chunks(self, user_id: str, session_id: str):
        with SessionLocal() as db:
            chunks = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.user_id == user_id, DocumentChunk.session_id == session_id)
                .order_by(DocumentChunk.id.asc())
                .all()
            )
            return [self._chunk_to_source(chunk) for chunk in chunks]

    def clear_session_documents(self, user_id: str, session_id: str):
        with SessionLocal() as db:
            try:
                db.query(DocumentChunk).filter(
                    DocumentChunk.user_id == user_id,
                    DocumentChunk.session_id == session_id,
                ).delete()
                db.query(Document).filter(
                    Document.user_id == user_id,
                    Document.session_id == session_id,
                ).delete()
                db.commit()
            except Exception as e:
                db.rollback()
                raise e

    def get_document_chunks(self, user_id: str, session_id: str, document_id: int):
        with SessionLocal() as db:
            chunks = (
                db.query(DocumentChunk)
                .filter(
                    DocumentChunk.user_id == user_id,
                    DocumentChunk.session_id == session_id,
                    DocumentChunk.document_id == document_id,
                )
                .order_by(DocumentChunk.chunk_index.asc(), DocumentChunk.id.asc())
                .all()
            )
            return [self._chunk_to_source(chunk) for chunk in chunks]

    def _document_to_dict(self, document):
        return {
            "id": document.id,
            "session_id": document.session_id,
            "filename": document.filename,
            "chunk_count": document.chunk_count,
            "created_at": document.created_at.isoformat() if document.created_at else None,
        }

    def _chunk_to_source(self, chunk):
        return {
            "document_id": chunk.document_id,
            "filename": chunk.filename,
            "chunk_index": chunk.chunk_index,
            "page_number": chunk.page_number,
            "content": chunk.content,
        }

    def _touch_session(self, db, user_id: str, session_id: str):
        session = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id, ChatSession.id == session_id)
            .first()
        )
        if session:
            session.updated_at = datetime.utcnow()
