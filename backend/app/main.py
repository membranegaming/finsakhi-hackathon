from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, assessment, learning, investments, chatbot

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

# Include routers
app.include_router(auth.router)
app.include_router(assessment.router)
app.include_router(learning.router)
app.include_router(investments.router)
app.include_router(chatbot.router)

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