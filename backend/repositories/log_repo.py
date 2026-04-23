from db.database import SessionLocal
from db.models import Log

class LogRepository:
    def add_log(self, user_id: str, question: str, answer: str):
        with SessionLocal() as db:
            try:
                new_log = Log(user_id=user_id, question=question, answer=answer)
                db.add(new_log)
                db.commit()
            except Exception as e:
                db.rollback()
                raise e

    def get_logs(self, user_id: str):
        with SessionLocal() as db:
            logs = db.query(Log).filter(Log.user_id == user_id).order_by(Log.timestamp.desc()).all()
            return [
                {
                    "id": log.id,
                    "question": log.question,
                    "answer": log.answer,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None
                }
                for log in logs
            ]

    def clear_logs(self, user_id: str):
        with SessionLocal() as db:
            try:
                db.query(Log).filter(Log.user_id == user_id).delete()
                db.commit()
            except Exception as e:
                db.rollback()
                raise e
