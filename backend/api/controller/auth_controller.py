from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from schemas.auth import ChangePasswordRequest, ProfileUpdateRequest, RegisterRequest
from services.auth_service import AuthService
from repositories.user_repo import UserRepository
from core.security import get_current_user

router = APIRouter(prefix="/auth")
user_repo = UserRepository()
auth_service = AuthService(user_repo)

@router.post("/register")
def register(req: RegisterRequest):
    return auth_service.register(req.username, req.password)

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return auth_service.authenticate(form_data.username, form_data.password)

@router.get("/me")
def get_me(user_id: str = Depends(get_current_user)):
    return auth_service.get_me(user_id)

@router.put("/me")
def update_me(req: ProfileUpdateRequest, user_id: str = Depends(get_current_user)):
    return auth_service.update_profile(
        user_id=user_id,
        username=req.username,
        full_name=req.full_name,
        email=req.email,
        password=req.password,
    )

@router.post("/change-password")
def change_password(req: ChangePasswordRequest, user_id: str = Depends(get_current_user)):
    return auth_service.change_password(user_id, req.current_password, req.new_password)
