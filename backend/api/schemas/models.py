"""
Pydantic models for API request/response schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    question: str = Field(..., description="User's question")
    chat_history: List[Dict[str, str]] = Field(
        default=[],
        description="Previous conversation history"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "SICT có những ngành nào?",
                "chat_history": [
                    {"role": "user", "content": "Xin chào"},
                    {"role": "assistant", "content": "Chào bạn!"}
                ]
            }
        }

class Source(BaseModel):
    """Source citation model"""
    title: str
    url: str
    category: str

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    answer: str = Field(..., description="AI's answer")
    sources: List[Source] = Field(default=[], description="Source citations")
    suggestions: List[str] = Field(default=[], description="Follow-up suggestions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "SICT đào tạo 6 ngành...",
                "sources": [
                    {
                        "title": "Giới thiệu ngành",
                        "url": "https://sict.haui.edu.vn/...",
                        "category": "Tin tức"
                    }
                ],
                "suggestions": ["Học phí?", "Điều kiện?"]
            }
        }

class DataStats(BaseModel):
    """Data statistics model"""
    total_articles: int
    total_chunks: int
    last_updated: str
    categories: Dict[str, int]
