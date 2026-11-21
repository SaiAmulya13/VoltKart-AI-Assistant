
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.db import initialize_database

from backend.api.upload import router as upload_router
from backend.api.chat import router as chat_router


# Initialize database when application starts
@asynccontextmanager
async def lifespan(app: FastAPI):

    initialize_database()

    yield


# Create FastAPI application
app = FastAPI(
    title="VoltKart AI Assistant",
    description="Multi-Source AI Chat Assistant API",
    version="1.0.0",
    lifespan=lifespan
)


# Allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Register API routers
app.include_router(upload_router)
app.include_router(chat_router)


# Health check
@app.get("/")
def home():

    return {
        "message": "Welcome to VoltKart AI Assistant",
        "status": "Backend is running"
    }


@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "application": "VoltKart AI Assistant"
    }
