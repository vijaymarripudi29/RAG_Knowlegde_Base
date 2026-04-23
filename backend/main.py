from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.controller import app_controller, auth_controller, query_controller, upload_controller
from db.database import engine, Base
import db.models
from core.config import settings

app = FastAPI(
    title=settings.app.TITLE,
    version=settings.app.VERSION
)

# Initialize database
Base.metadata.create_all(bind=engine)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_controller.router)
app.include_router(app_controller.router)
app.include_router(query_controller.router)
app.include_router(upload_controller.router)

@app.get("/health")
def health():
    return {"status": "ok"}
