"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

class AnalysisRequest(BaseModel):
    """Request model for sentiment analysis."""
    text: str = Field(..., min_length=1, max_length=1000)
    deployment: str = Field(default="lambda", description="Target deployment: 'lambda' or 'kubernetes'")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "I love this product!",
                "deployment": "lambda"
            }
        }

class AnalysisResponse(BaseModel):
    """Response model for sentiment analysis."""
    text: str
    sentiment: str
    confidence: float  
    scores: Optional[Dict[str, float]] = None  # Optional detailed scores
    deployment: str
    retry_attempts: int  
    response_time_ms: float  
    timestamp: str

    class Config:
        json_schema_extra = {
            "example": {
                "text": "I love this!",
                "sentiment": "POSITIVE",
                "confidence": 0.9995,
                "scores": {"positive": 0.9995, "negative": 0.0005},
                "deployment": "lambda",
                "retry_attempts": 0,
                "response_time_ms": 150.25,
                "timestamp": "2025-11-15T23:50:00"
            }
        }

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    lambda_endpoint: Optional[str]
    kubernetes_endpoint: Optional[str]
    timestamp: str

class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    detail: str
    timestamp: str
