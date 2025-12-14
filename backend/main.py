"""
FastAPI Backend for HaUI Assistant Chatbot
Provides REST API endpoints for chat functionality.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import chat, data

app = FastAPI(
    title="HaUI Assistant API",
    version="1.0.0",
    description="Backend API for HaUI AI chatbot with RAG capabilities"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",  # Chainlit default
        "http://localhost:8501",  # Streamlit (for testing)
        "http://localhost:3000",  # React (if needed later)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(data.router, prefix="/api/data", tags=["data"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HaUI Assistant API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
