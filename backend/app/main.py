from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.routers import auth, assessment, learning, investments, chatbot, recommendations
from app.routers import podcast, portfolio, goals

app = FastAPI(
    title="FinSakhi API",
    description="Financial Literacy Platform for Bharat",
    version="1.0.0"
)

# CORS - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve podcast audio files as static content
PODCAST_STATIC_DIR = Path(__file__).resolve().parent.parent / "data" / "podcasts"
PODCAST_STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static/podcasts", StaticFiles(directory=str(PODCAST_STATIC_DIR)), name="podcasts-static")

# Include routers
app.include_router(auth.router)
app.include_router(assessment.router)
app.include_router(learning.router)
app.include_router(investments.router)
app.include_router(chatbot.router)
app.include_router(recommendations.router)
app.include_router(podcast.router)
app.include_router(portfolio.router)
app.include_router(goals.router)

@app.get("/")
def read_root():
    return {
        "message": "FinSakhi API is running! 🌾",
        "status": "healthy",
        "database": "SQLite (offline-ready)"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}