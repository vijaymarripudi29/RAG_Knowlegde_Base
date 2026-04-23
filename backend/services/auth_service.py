from fastapi import HTTPException, status
from core.security import verify_password, get_password_hash, create_token
from repositories.user_repo import UserRepository

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register(self, username: str, password: str):
        self._validate_password_strength(password)
        existing_user = self.user_repo.get_user_by_username(username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        hashed_password = get_password_hash(password)
        user_id = self.user_repo.create_user(username, hashed_password)
        return {"id": user_id, "username": username}

    def authenticate(self, username: str, password: str):
        user = self.user_repo.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        
        if not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        
        token = create_token(user["id"])
        return {"access_token": token, "token_type": "bearer"}

    def get_me(self, user_id: str):
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def update_profile(self, user_id: str, username=None, full_name=None, email=None, password=None):
        updates = {}
        if username:
            existing_user = self.user_repo.get_user_by_username(username)
            if existing_user and existing_user["id"] != user_id:
                raise HTTPException(status_code=400, detail="Username already registered")
            updates["username"] = username
        if full_name is not None:
            updates["full_name"] = full_name
        if email is not None:
            updates["email"] = email
        if password:
            self._validate_password_strength(password)
            updates["password_hash"] = get_password_hash(password)

        if not updates:
            return self.get_me(user_id)

        user = self.user_repo.update_user(user_id, updates)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def change_password(self, user_id: str, current_password: str, new_password: str):
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user_with_hash = self.user_repo.get_user_by_username(user["username"])
        if not verify_password(current_password, user_with_hash["password_hash"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

        self._validate_password_strength(new_password)
        return self.user_repo.update_user(user_id, {"password_hash": get_password_hash(new_password)})

    def _validate_password_strength(self, password: str):
        errors = []
        if len(password) < 8:
            errors.append("at least 8 characters")
        if not any(ch.isupper() for ch in password):
            errors.append("one uppercase letter")
        if not any(ch.islower() for ch in password):
            errors.append("one lowercase letter")
        if not any(ch.isdigit() for ch in password):
            errors.append("one number")
        if not any(not ch.isalnum() for ch in password):
            errors.append("one special character")

        if errors:
            raise HTTPException(
                status_code=400,
                detail=f"Password must contain {', '.join(errors)}.",
            )
