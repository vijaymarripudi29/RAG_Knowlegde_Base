import uuid
from db.database import SessionLocal
from db.models import User

class UserRepository:
    def create_user(self, username: str, password_hash: str) -> str:
        with SessionLocal() as db:
            user_id = str(uuid.uuid4())
            try:
                new_user = User(id=user_id, username=username, password_hash=password_hash)
                db.add(new_user)
                db.commit()
                return user_id
            except Exception as e:
                db.rollback()
                raise e

    def get_user_by_username(self, username: str) -> dict:
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == username).first()
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "password_hash": user.password_hash,
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": user.role,
                }
            return None

    def get_user_by_id(self, user_id: str) -> dict:
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": user.role,
                }
            return None

    def update_user(self, user_id: str, updates: dict) -> dict:
        with SessionLocal() as db:
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return None

                for field, value in updates.items():
                    setattr(user, field, value)

                db.commit()
                db.refresh(user)
                return {
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": user.role,
                }
            except Exception as e:
                db.rollback()
                raise e

    def get_users(self):
        with SessionLocal() as db:
            users = db.query(User).order_by(User.username.asc()).all()
            return [
                {
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": user.role,
                }
                for user in users
            ]
